"""
SDUI Tools Import Resolution
============================
Обработка кастомных модульных импортов и Jinja includes.
Jinjava compatibility transforms.
"""

import os
import re
from urllib.parse import unquote

from .utils import resolve_include_path


# ══════════════════════════════════════════════════════════════════════════════
# SDUI EL ESCAPE — решает конфликт ${{ между SDUI Expression Language и Jinja
# ══════════════════════════════════════════════════════════════════════════════

SDUI_EL_PLACEHOLDER = "__SDUI_EL_OPEN__"


def escape_sdui_el(content):
    """
    Escape ${{ + { → placeholder перед рендерингом Jinjava.

    Проблема: В паттерне ${{{ var }}.field}:
        - ${...} — SDUI Expression Language
        - {{ var }} — Jinja expression
        - Jinjava видит {{{ как {{ + { (expression + dict literal) → syntax error

    Решение: escape ${{ когда за ним следует { (т.е. паттерн ${{{)
        - ${{{ var }}.field} → __SDUI_EL_OPEN__{{ var }}.field}
        - Jinjava рендерит {{ var }} нормально
        - Post-restore: __SDUI_EL_OPEN__ → ${

    Примеры:
        ${{{ source_prefix }}.deeplink} → __SDUI_EL_OPEN__{{ source_prefix }}.deeplink}
        ${source.deeplink} → ${source.deeplink} (без изменений — нет Jinja переменных)
    """
    # Escape только паттерн ${{ + { (SDUI EL + Jinja conflict)
    # ${{{ → __SDUI_EL_OPEN__{{ (убираем ${ и первый {, оставляем Jinja {{}})
    return content.replace('${{{', SDUI_EL_PLACEHOLDER + '{{')


def restore_sdui_el(content):
    """
    Восстанавливает ${ после рендеринга Jinjava.

    Пример:
        До:    __SDUI_EL_OPEN__source.deeplink}
        После: ${source.deeplink}
    """
    return content.replace(SDUI_EL_PLACEHOLDER, '${')


# ══════════════════════════════════════════════════════════════════════════════
# JINJAVA COMPATIBILITY TRANSFORMS — модульные функции-трансформеры
# ══════════════════════════════════════════════════════════════════════════════

def _transform_macro_defaults(content):
    """Удаляет =none / =None из macro arguments (Jinjava treats missing as undefined)."""
    return re.sub(r'=\s*[Nn]one\b', '', content)


def _transform_none_checks(content):
    """Преобразует `is none` / `is not none` → `== ""` / `!= ""`."""
    content = re.sub(r'\bis\s+not\s+[Nn]one\b', '!= ""', content)
    content = re.sub(r'\bis\s+[Nn]one\b', '== ""', content)
    return content


def _transform_python_literals(content):
    """Преобразует True/False/None → true/false/null."""
    content = re.sub(r'\bTrue\b', 'true', content)
    content = re.sub(r'\bFalse\b', 'false', content)
    content = re.sub(r'\bNone\b', 'null', content)
    return content


def _transform_dict_get(content):
    """
    Преобразует .get() → bracket access + default filter.

    Примеры:
        dict.get('key')           → dict['key'] | default('')
        dict.get('key', 'value')  → dict['key'] | default('value')
        dict.get(var)             → dict[var] | default('')
    """
    def replace_get(match):
        obj = match.group(1)
        key = match.group(2)
        default = match.group(4)

        if default:
            return f"{obj}[{key}] | default({default})"
        return f"{obj}[{key}] | default('')"

    pattern = r'(\b[\w.]+(?:\[[^\]]+\])?)\s*\.\s*get\s*\(\s*([\'"][^\'"]+[\'"]|\w+)\s*(?:(,)\s*([^)]+))?\s*\)'
    return re.sub(pattern, replace_get, content)


def _transform_dict_methods(content):
    """Преобразует .items()/.keys()/.values() → | items/keys/values."""
    content = re.sub(r'\.items\s*\(\s*\)', ' | items', content)
    content = re.sub(r'\.keys\s*\(\s*\)', ' | keys', content)
    content = re.sub(r'\.values\s*\(\s*\)', ' | values', content)
    return content


def _transform_string_methods(content):
    """Преобразует string методы → Jinjava filters."""
    transforms = [
        (r'\.strip\s*\(\s*\)', ' | trim'),
        (r'\.lower\s*\(\s*\)', ' | lower'),
        (r'\.upper\s*\(\s*\)', ' | upper'),
        (r'\.title\s*\(\s*\)', ' | title'),
        (r'\.capitalize\s*\(\s*\)', ' | capitalize'),
    ]
    for pattern, replacement in transforms:
        content = re.sub(pattern, replacement, content)
    return content


# ══════════════════════════════════════════════════════════════════════════════
# MAIN COMPAT FUNCTION
# ══════════════════════════════════════════════════════════════════════════════

def jinjava_compat(content):
    """
    Преобразует Python jinja2 синтаксис в Jinjava-совместимый.

    Pipeline (порядок важен):
        1. Escape SDUI EL (${{) — избегаем конфликта с Jinjava
        2. Macro default arguments (=none → remove)
        3. None checks (is none → == "")
        4. Python literals (True → true)
        5. Dict .get() → bracket + default
        6. Dict methods (.items() → | items)
        7. String methods (.strip() → | trim)

    Note: restore_sdui_el() вызывается ПОСЛЕ рендеринга в renderer.py
    """
    # Pipeline: каждый трансформер изолирован и тестируем отдельно
    transforms = [
        escape_sdui_el,           # SDUI EL conflict fix (NEW!)
        _transform_macro_defaults,
        _transform_none_checks,
        _transform_python_literals,
        _transform_dict_get,
        _transform_dict_methods,
        _transform_string_methods,
    ]

    for transform in transforms:
        content = transform(content)

    return content


def parse_import_aliases(imports_str):
    """
    Парсит строку импортов и возвращает словарь алиасов.

    Examples:
        'click as analytics_click' → {'analytics_click': 'click'}

    Returns:
        dict: {alias: original}
    """
    aliases = {}

    # Split by comma, handle each import
    for item in imports_str.split(','):
        item = item.strip()
        if ' as ' in item:
            parts = item.split(' as ')
            if len(parts) == 2:
                original = parts[0].strip()
                alias = parts[1].strip()
                aliases[alias] = original

    return aliases


def parse_module_imports(content, base_dir, processed_files=None, collected_files=None):
    """
    Парсит и резолвит модульные импорты формата:
    // [description](file:///absolute/path/to/module.j2)
    
    Рекурсивно обрабатывает вложенные импорты.
    Детектит циклические импорты.
    
    Args:
        content: Содержимое шаблона
        base_dir: Базовая директория для относительных путей
        processed_files: Set уже обработанных файлов (для circular import detection)
        collected_files: Set для сбора всех путей (для watch mode)
        
    Returns:
        tuple: (processed_content, collected_files)
    """
    if processed_files is None:
        processed_files = set()
    if collected_files is None:
        collected_files = set()

    pattern = r"^(\s*)//\s*\[.*?\]\(file:///([^)]+)\)\s*$"

    lines = content.split("\n")
    result_lines = []

    for line in lines:
        match = re.match(pattern, line)
        if match:
            indent = match.group(1)
            file_uri = match.group(2)
            file_path = unquote(file_uri)

            # Resolve relative paths
            if not os.path.isabs(file_path):
                candidates = [
                    os.path.join(base_dir, file_path),
                    os.path.join(os.path.dirname(base_dir), file_path),
                ]

                resolved_path = None
                for candidate in candidates:
                    if os.path.exists(candidate):
                        resolved_path = candidate
                        break

                file_path = resolved_path if resolved_path else candidates[0]

            file_path = os.path.abspath(file_path)

            # Circular import detection
            if file_path in processed_files:
                result_lines.append(
                    f"{indent}// [CIRCULAR IMPORT DETECTED: {os.path.basename(file_path)}]"
                )
                print(f"⚠️  Warning: Circular import detected for {file_path}")
                continue

            # File not found
            if not os.path.exists(file_path):
                result_lines.append(f"{indent}// [MODULE NOT FOUND: {file_path}]")
                print(f"⚠️  Warning: Module not found: {file_path}")
                continue

            # Load and process module
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    module_content = f.read()

                new_processed = processed_files.copy()
                new_processed.add(file_path)
                collected_files.add(file_path)

                module_dir = os.path.dirname(file_path)
                processed_module, collected_files = parse_module_imports(
                    module_content, module_dir, new_processed, collected_files
                )

                # Indent module content
                module_lines = processed_module.split("\n")
                indented_module = "\n".join(
                    indent + line if line.strip() else line for line in module_lines
                )

                module_name = os.path.basename(file_path)
                result_lines.append(f"{indent}// ▼ START MODULE: {module_name}")
                result_lines.append(indented_module)
                result_lines.append(f"{indent}// ▲ END MODULE: {module_name}")

                print(f"    📦 Loaded module: {module_name}")

            except Exception as e:
                result_lines.append(f"{indent}// [ERROR LOADING MODULE: {e}]")
                print(f"❌ Error loading module {file_path}: {e}")
        else:
            result_lines.append(line)

    return "\n".join(result_lines), collected_files


def resolve_jinja_includes(content, template_dir, processed_files=None, collected_files=None):
    """
    Резолвит {% include '...' %} и {% from '...' import ... %} statements
    БЕЗ рендеринга Jinja переменных.
    
    Создает полностью собранный шаблон для инспекции перед подстановкой данных.
    
    Args:
        content: Содержимое шаблона
        template_dir: Базовая директория для include resolution
        processed_files: Set уже обработанных файлов (circular import prevention)
        collected_files: Set для сбора путей файлов (для watch mode)
        
    Returns:
        tuple: (content_with_includes_resolved, collected_files)
    """
    if processed_files is None:
        processed_files = set()
    if collected_files is None:
        collected_files = set()

    # Pattern for {% include 'path/to/file.j2' %}
    include_pattern = r"\{%\s*include\s+['\"]([^'\"]+)['\"]\s*%\}"

    # Pattern for {% from 'path/to/file.j2' import macro_name %}
    from_pattern = r"\{%\s*from\s+['\"]([^'\"]+)['\"]\s+import\s+([^%]+)\s*%\}"

    result = content

    # Process {% from ... import ... %} first
    from_matches = list(re.finditer(from_pattern, result))
    for match in reversed(from_matches):
        file_path = match.group(1)
        imports = match.group(2).strip()

        resolved_path = resolve_include_path(file_path, template_dir)

        if resolved_path and os.path.exists(resolved_path):
            collected_files.add(resolved_path)

            if resolved_path not in processed_files:
                try:
                    with open(resolved_path, "r", encoding="utf-8") as f:
                        macro_content = f.read()

                    new_processed = processed_files.copy()
                    new_processed.add(resolved_path)

                    macro_dir = os.path.dirname(resolved_path)
                    resolved_macro, collected_files = resolve_jinja_includes(
                        macro_content, macro_dir, new_processed, collected_files
                    )

                    macro_name = os.path.basename(resolved_path)

                    # Handle aliases via lexical replacement
                    aliases = parse_import_aliases(imports)
                    
                    replacement = f"{{# ▼ FROM: {macro_name} (import {imports}) #}}\n{resolved_macro}\n{{# ▲ END FROM: {macro_name} #}}"

                    # 1. Apply replacement of the import tag
                    result = result[: match.start()] + replacement + result[match.end():]

                    # 2. Apply alias replacements in the REST of the content (global scope)
                    # Note: This is risky if aliases conflict with other names, but necessary for Jinjava macro aliasing
                    for alias, original in aliases.items():
                        # Use word boundary to replace only whole words
                        pattern = r'\b' + re.escape(alias) + r'\b'
                        result = re.sub(pattern, original, result)

                except Exception as e:
                    print(f"⚠️  Error resolving from-import {file_path}: {e}")
            else:
                result = (
                    result[: match.start()]
                    + f"{{# CIRCULAR IMPORT: {file_path} #}}"
                    + result[match.end():]
                )
        else:
            print(f"⚠️  Warning: from-import file not found: {file_path}")


    # Process {% include ... %} statements
    include_matches = list(re.finditer(include_pattern, result))
    for match in reversed(include_matches):
        file_path = match.group(1)

        resolved_path = resolve_include_path(file_path, template_dir)

        if resolved_path and os.path.exists(resolved_path):
            collected_files.add(resolved_path)

            if resolved_path not in processed_files:
                try:
                    with open(resolved_path, "r", encoding="utf-8") as f:
                        include_content = f.read()

                    new_processed = processed_files.copy()
                    new_processed.add(resolved_path)

                    include_dir = os.path.dirname(resolved_path)
                    resolved_include, collected_files = resolve_jinja_includes(
                        include_content, include_dir, new_processed, collected_files
                    )

                    include_name = os.path.basename(resolved_path)
                    replacement = f"{{# ▼ INCLUDE: {include_name} #}}\n{resolved_include}\n{{# ▲ END INCLUDE: {include_name} #}}"

                    result = result[: match.start()] + replacement + result[match.end():]

                except Exception as e:
                    print(f"⚠️  Error resolving include {file_path}: {e}")
            else:
                result = (
                    result[: match.start()]
                    + f"{{# CIRCULAR INCLUDE: {file_path} #}}"
                    + result[match.end():]
                )
        else:
            print(f"⚠️  Warning: include file not found: {file_path}")

    return result, collected_files
