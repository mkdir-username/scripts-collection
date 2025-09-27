#!/usr/bin/env python3
"""
Исправляет лишний слэш в file://// ссылках
"""

import json
import sys
from pathlib import Path
import re


def fix_file(file_path: Path) -> int:
    """Исправляет лишние слэши в одном файле"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Заменяем file://// на file:///
        new_content = re.sub(r'file:////([^"]+)', r'file:///\1', content)

        if new_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

            # Считаем количество исправлений
            count = content.count('file:////')
            return count

    except Exception as e:
        print(f"Ошибка в {file_path}: {e}")

    return 0


def main():
    base_path = Path("/Users/username/Documents/front-middle-schema")

    total_fixed = 0
    files_fixed = 0

    print("🔧 Исправляю лишние слэши в file://// ссылках...")

    # Ищем все JSON файлы
    for json_file in base_path.glob("**/*.json"):
        if any(part.startswith('.') for part in json_file.parts):
            continue

        fixed = fix_file(json_file)
        if fixed > 0:
            print(f"  ✅ {json_file.relative_to(base_path)}: исправлено {fixed} ссылок")
            total_fixed += fixed
            files_fixed += 1

    print(f"\n📊 Итого:")
    print(f"  - Исправлено ссылок: {total_fixed}")
    print(f"  - Модифицировано файлов: {files_fixed}")


if __name__ == "__main__":
    main()