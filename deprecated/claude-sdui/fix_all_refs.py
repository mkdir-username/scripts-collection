#!/usr/bin/env python3
"""
Исправление ВСЕХ проблем с $ref ссылками
"""

import json
import re
from pathlib import Path
import sys


def fix_refs_in_file(file_path: Path) -> int:
    """Исправляет ссылки в файле"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            original_content = content

        data = json.loads(content)
        fixed_count = fix_refs_recursive(data, file_path)

        if fixed_count > 0:
            new_content = json.dumps(data, indent=2, ensure_ascii=False)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
                if not new_content.endswith('\n'):
                    f.write('\n')
            print(f"✅ {file_path.name}: исправлено {fixed_count} ссылок")

        return fixed_count

    except Exception as e:
        print(f"❌ {file_path.name}: {e}")
        return 0


def fix_refs_recursive(obj: any, source_file: Path, depth: int = 0) -> int:
    """Рекурсивно исправляет $ref ссылки"""
    if depth > 20:
        return 0

    fixed_count = 0

    if isinstance(obj, dict):
        for key, value in list(obj.items()):
            if key == "$ref" and isinstance(value, str):
                new_value = fix_ref(value, source_file)
                if new_value != value:
                    obj[key] = new_value
                    fixed_count += 1
            else:
                fixed_count += fix_refs_recursive(value, source_file, depth + 1)

    elif isinstance(obj, list):
        for item in obj:
            fixed_count += fix_refs_recursive(item, source_file, depth + 1)

    return fixed_count


def fix_ref(ref: str, source_file: Path) -> str:
    """Исправляет одну ссылку"""
    # Пропускаем внутренние ссылки
    if ref.startswith("#"):
        return ref

    # Пропускаем http ссылки
    if ref.startswith("http"):
        return ref

    # Добавляем .json если его нет
    if not ref.endswith('.json'):
        # Проверяем, не является ли последняя часть уже расширением
        parts = ref.split('/')
        last_part = parts[-1]

        # Если нет точки в последней части, добавляем .json
        if '.' not in last_part:
            return ref + '.json'

    return ref


def main():
    # Находим все JSON файлы с проблемными ссылками
    base_path = Path("/Users/username/Documents/FMS_GIT")

    problem_dirs = [
        "multistep",
        "widgets",
        "analytics",
        "dependentfields",
        "valuefields",
        "SDUI"
    ]

    total_fixed = 0

    for dir_name in problem_dirs:
        dir_path = base_path / dir_name
        if dir_path.exists():
            print(f"\n📁 Обрабатываю {dir_name}/...")
            for json_file in dir_path.glob("**/*.json"):
                # Пропускаем служебные директории
                if any(part.startswith('.') for part in json_file.parts):
                    continue

                fixed = fix_refs_in_file(json_file)
                total_fixed += fixed

    print(f"\n✨ Всего исправлено ссылок: {total_fixed}")


if __name__ == "__main__":
    main()