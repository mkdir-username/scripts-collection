#!/usr/bin/env python3
"""
Скрипт для исправления $ref в JSON схемах - добавляет расширение .json
"""

import json
import os
from pathlib import Path

def fix_refs_in_dict(obj, current_file_path=None):
    """Рекурсивно исправляет $ref в словаре"""
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == "$ref" and isinstance(value, str):
                # Пропускаем ссылки на внутренние определения (начинаются с #)
                if value.startswith("#"):
                    continue

                # Если не содержит .json, добавляем
                if not value.endswith(".json"):
                    # Проверяем, является ли это ссылкой на файл в той же директории
                    # (не содержит / или ..)
                    if "/" not in value and ".." not in value:
                        # Это ссылка на файл в той же директории
                        obj[key] = value + ".json"
                    else:
                        # Это путь к файлу в другой директории
                        obj[key] = value + ".json"
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
            print(f"✓ Исправлено: {filepath}")
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
    print(f"✅ Исправлено файлов: {fixed_files}")

if __name__ == "__main__":
    main()