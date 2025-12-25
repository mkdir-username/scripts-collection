"""
SDUI Tools Import Resolution
============================
Обработка кастомных модульных импортов и Jinja includes.
"""

import os
import re
from urllib.parse import unquote

from .utils import resolve_include_path


def parse_import_aliases(imports_str):
    """
    Парсит строку импортов и возвращает {% set %} statements для алиасов.

    Examples:
        'click as analytics_click' → '{% set analytics_click = click %}'
        'click as analytics_click, lifecycle_events' → '{% set analytics_click = click %}'
        'foo, bar as baz' → '{% set baz = bar %}'

    Returns:
        str: Jinja set statements для алиасов (может быть пустой строкой)
    """
    aliases = []

    # Split by comma, handle each import
    for item in imports_str.split(','):
        item = item.strip()
        if ' as ' in item:
            parts = item.split(' as ')
            if len(parts) == 2:
                original = parts[0].strip()
                alias = parts[1].strip()
                aliases.append(f"{{% set {alias} = {original} %}}")

    return '\n'.join(aliases)


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

            # Circular import detection — HARD FAIL
            if file_path in processed_files:
                raise ImportError(f"Circular import detected: {file_path}")

            # File not found — HARD FAIL
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Module not found: {file_path}")

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

                    # Generate {% set %} for aliases (e.g., 'click as analytics_click')
                    alias_statements = parse_import_aliases(imports)
                    alias_block = f"\n{alias_statements}" if alias_statements else ""

                    replacement = f"{{# ▼ FROM: {macro_name} (import {imports}) #}}\n{resolved_macro}{alias_block}\n{{# ▲ END FROM: {macro_name} #}}"

                    result = result[: match.start()] + replacement + result[match.end():]

                except Exception as e:
                    raise RuntimeError(f"Error resolving from-import {file_path}: {e}")
            else:
                raise ImportError(f"Circular from-import detected: {file_path}")
        else:
            raise FileNotFoundError(f"From-import file not found: {file_path}")

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
                    raise RuntimeError(f"Error resolving include {file_path}: {e}")
            else:
                raise ImportError(f"Circular include detected: {file_path}")
        else:
            raise FileNotFoundError(f"Include file not found: {file_path}")

    return result, collected_files
