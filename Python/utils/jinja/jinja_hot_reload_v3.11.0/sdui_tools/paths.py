"""
SDUI Tools Path Management
==========================
Генерация выходных путей, работа с именами файлов.
"""

import os
import re

from .config import TEMPLATE_EXTENSIONS


def generate_output_paths(template_path):
    """
    Генерирует пути для MAP, FULL и JJ_FULL файлов из пути шаблона.
    
    Naming convention:
    - [JJ_<PLATFORM>]_name.<ext>  →  Input template
    - [JJ_FULL_<PLATFORM>]_name.java  →  Assembled Jinja (includes resolved)
    - [MAP_<PLATFORM>]_name.json  →  Rendered with comments & markers
    - [FULL_<PLATFORM>]_name.json  →  Clean JSON output
    
    Supported extensions: .json.j2, .j2.java, .java, .j2
    
    Args:
        template_path: Путь к исходному шаблону
        
    Returns:
        tuple: (jj_full_path, map_path, full_path)
    """
    template_dir = os.path.dirname(template_path)
    template_file = os.path.basename(template_path)

    # Pattern: [JJ_<PLATFORM>]_name.<ext>
    match = re.match(r"^\[JJ_(\w+)\]_(.+?)\.(json\.j2|j2\.java|java|j2)$", template_file)

    if match:
        platform = match.group(1)
        base_name = match.group(2)

        jj_full_filename = f"[JJ_FULL_{platform}]_{base_name}.java"
        map_filename = f"[MAP_{platform}]_{base_name}.json"
        full_filename = f"[FULL_{platform}]_{base_name}.json"

        output_dir = template_dir
    else:
        # Fallback for non-standard naming
        base_name = template_file
        for ext in TEMPLATE_EXTENSIONS:
            if base_name.endswith(ext):
                base_name = base_name[: -len(ext)]
                break

        jj_full_filename = f"{base_name}_jj_full.java"
        map_filename = f"{base_name}_map.json"
        full_filename = f"{base_name}_output.json"
        output_dir = template_dir

    jj_full_path = os.path.join(output_dir, jj_full_filename)
    map_path = os.path.join(output_dir, map_filename)
    full_path = os.path.join(output_dir, full_filename)

    return jj_full_path, map_path, full_path


def get_file_type_label(file_path, template_path, data_path):
    """
    Определяет тип файла для отображения в логах.
    
    Returns:
        tuple: (emoji, label) например ("📄", "Template")
    """
    abs_path = os.path.abspath(file_path)
    
    if abs_path == os.path.abspath(template_path):
        return "📄", "Template"
    elif abs_path == os.path.abspath(data_path):
        return "💾", "Data"
    else:
        return "📦", "Module"


def extract_platform_from_path(template_path):
    """
    Извлекает платформу из имени шаблона.
    
    [JJ_PC]_name.java → "PC"
    [JJ_MOBILE]_name.java → "MOBILE"
    
    Returns:
        str or None: Название платформы
    """
    template_file = os.path.basename(template_path)
    match = re.match(r"^\[JJ_(\w+)\]_", template_file)
    
    if match:
        return match.group(1)
    return None
