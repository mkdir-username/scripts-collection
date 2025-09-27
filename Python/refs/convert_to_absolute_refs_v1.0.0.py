#!/usr/bin/env python3
"""
Скрипт для преобразования относительных $ref в абсолютные file:/// пути
"""

import json
import os
from pathlib import Path

BASE_PATH = "/Users/username/Documents/front-middle-schema"

def resolve_ref_path(ref_value, current_file_path):
    """Преобразует относительный путь в абсолютный file:/// URI"""
    # Пропускаем внутренние ссылки
    if ref_value.startswith("#"):
        return ref_value

    # Пропускаем уже абсолютные пути
    if ref_value.startswith("file:///"):
        return ref_value

    # Получаем директорию текущего файла
    current_dir = Path(current_file_path).parent

    # Резолвим относительный путь
    resolved_path = (current_dir / ref_value).resolve()

    # Конвертируем в file:/// URI
    return f"file://{resolved_path}"

def fix_refs_in_dict(obj, current_file_path):
    """Рекурсивно исправляет $ref в словаре"""
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == "$ref" and isinstance(value, str):
                # Преобразуем в абсолютный путь
                obj[key] = resolve_ref_path(value, current_file_path)
            else:
                fix_refs_in_dict(value, current_file_path)
    elif isinstance(obj, list):
        for item in obj:
            fix_refs_in_dict(item, current_file_path)

def process_schema_file(filepath):
    """Обрабатывает один файл схемы"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            schema = json.load(f)

        # Создаем копию для сравнения
        original = json.dumps(schema, sort_keys=True)

        # Исправляем ссылки
        fix_refs_in_dict(schema, filepath)

        # Проверяем, были ли изменения
        modified = json.dumps(schema, sort_keys=True)
        if original != modified:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(schema, f, indent=2, ensure_ascii=False)
            print(f"✓ Преобразовано: {filepath}")
            return True
    except Exception as e:
        print(f"✗ Ошибка в {filepath}: {e}")
    return False

def main():
    sdui_path = Path("SDUI")

    # Паттерны для поиска JSON схем
    patterns = [
        "components/*/v*/*.json",
        "atoms/*/*.json",
        "common/*/*.json",
        "layouts/*/*.json",
        "actions/*/*.json",
        "functions/*/*.json",
        "models/*/*.json"
    ]

    total_files = 0
    fixed_files = 0

    for pattern in patterns:
        for filepath in sdui_path.glob(pattern):
            # Пропускаем samples
            if "samples" in str(filepath):
                continue

            total_files += 1
            if process_schema_file(filepath):
                fixed_files += 1

    print(f"\n📊 Обработано файлов: {total_files}")
    print(f"✅ Преобразовано файлов: {fixed_files}")

if __name__ == "__main__":
    main()