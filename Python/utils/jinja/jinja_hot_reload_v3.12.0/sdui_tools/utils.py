"""
SDUI Tools Utilities
====================
Вспомогательные функции: JSON-обработка, работа с файлами.
"""

import os
import re
import json


def json_finalize(thing):
    """
    Custom finalize function for Jinja2.
    Конвертирует Python-типы в валидные JSON-значения.
    
    - None → "null"
    - True/False → "true"/"false"  
    - dict/list → JSON string
    """
    if thing is None:
        return "null"
    if isinstance(thing, bool):
        return "true" if thing else "false"
    if isinstance(thing, (dict, list)):
        return json.dumps(thing, ensure_ascii=False)
    return thing


def remove_json_comments(content):
    """
    Удаляет комментарии из JSON-контента:
    1. {# Jinja2 block comments #}
    2. // line comments (сохраняя URLs типа http://)
    3. Trailing commas перед закрывающими скобками
    
    Args:
        content: Строка с JSON + комментариями
        
    Returns:
        Чистый JSON без комментариев
    """
    # Step 1: Remove {# Jinja2 comments #}
    content = re.sub(r"\{#.*?#\}", "", content, flags=re.DOTALL)

    # Step 2: Remove // comments (line by line)
    lines = content.split("\n")
    result = []

    for line in lines:
        stripped = line.lstrip()
        
        # Skip full-line comments
        if stripped.startswith("//"):
            continue

        # Check for inline // comments (preserve URLs)
        if "//" in line:
            idx = line.find("//")
            if idx > 0:
                prefix = line[:idx]
                # Don't remove if it's part of a URL
                if not (prefix.endswith("http:") or prefix.endswith("https:")):
                    line = prefix.rstrip()

        result.append(line)

    content = "\n".join(result)

    # Step 3: Remove trailing commas
    content = re.sub(r",(\s*[}\]])", r"\1", content)

    return content


def resolve_include_path(file_path, template_dir):
    """
    Резолвит путь include/from в абсолютный путь.
    
    Пробует:
    1. Абсолютный путь (если уже абсолютный)
    2. Относительно template_dir
    3. Относительно родительской директории template_dir
    
    Args:
        file_path: Путь из include/from statement
        template_dir: Директория текущего шаблона
        
    Returns:
        str or None: Абсолютный путь или None если не найден
    """
    if os.path.isabs(file_path):
        return file_path if os.path.exists(file_path) else None

    candidates = [
        os.path.join(template_dir, file_path),
        os.path.join(os.path.dirname(template_dir), file_path),
        os.path.normpath(os.path.join(template_dir, file_path)),
    ]

    for candidate in candidates:
        if os.path.exists(candidate):
            return os.path.abspath(candidate)

    return None


def get_max_mtime(files):
    """
    Находит максимальное время модификации среди файлов.
    Используется для watch mode.
    
    Args:
        files: Iterable путей к файлам
        
    Returns:
        tuple: (max_mtime, changed_file_path or None)
    """
    max_mtime = 0
    changed_file = None

    for f in files:
        if os.path.exists(f):
            mtime = os.path.getmtime(f)
            if mtime > max_mtime:
                max_mtime = mtime
                changed_file = f

    return max_mtime, changed_file


def safe_read_file(file_path, encoding="utf-8"):
    """
    Безопасное чтение файла с обработкой ошибок.
    
    Returns:
        tuple: (content or None, error_message or None)
    """
    try:
        with open(file_path, "r", encoding=encoding) as f:
            return f.read(), None
    except FileNotFoundError:
        return None, f"File not found: {file_path}"
    except PermissionError:
        return None, f"Permission denied: {file_path}"
    except Exception as e:
        return None, f"Error reading {file_path}: {e}"


def safe_write_file(file_path, content, encoding="utf-8"):
    """
    Безопасная запись файла с созданием директорий.
    
    Returns:
        tuple: (success: bool, error_message or None)
    """
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding=encoding) as f:
            f.write(content)
        return True, None
    except PermissionError:
        return False, f"Permission denied: {file_path}"
    except Exception as e:
        return False, f"Error writing {file_path}: {e}"
