#!/usr/bin/env python3
"""
Исправляет отсутствующий ведущий слэш в file:/// ссылках
Например: file:///Users/... -> file:////Users/... (неправильно)
          file:///Users/... -> file:///Users/... (правильно - ничего не меняем)
          file://Users/...  -> file:///Users/... (исправляем)
"""

import json
import re
from pathlib import Path
import sys


def fix_file(file_path: Path) -> int:
    """Исправляет ссылки в одном файле"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            original = content

        # Паттерны для исправления
        # file:///Users -> должно остаться file:///Users (3 слэша + /Users)
        # file://Users -> исправить на file:///Users (2 слэша + Users -> 3 слэша + /Users)

        # Исправляем file://Users на file:///Users (добавляем слэш перед Users)
        content = re.sub(
            r'"file://([^/][^"]+)"',  # file:// и далее НЕ слэш
            r'"file:///\1"',  # добавляем третий слэш
            content
        )

        # Исправляем file:///Users на file:////Users (если путь не начинается с /)
        content = re.sub(
            r'"file:///([^/][^"]+)"',  # file:/// и далее НЕ слэш
            r'"file:////\1"',  # добавляем четвертый слэш
            content
        )

        # Теперь исправляем file://// обратно на file:///
        content = re.sub(
            r'"file:////([^"]+)"',
            r'"file:///\1"',
            content
        )

        if content != original:
            # Считаем количество исправлений
            count = 0
            for match in re.finditer(r'"file://[^"]+', original):
                old_ref = match.group()
                if not old_ref.startswith('"file:///'):  # если не 3 слэша
                    count += 1
                elif old_ref.startswith('"file:///') and not old_ref.startswith('"file:////'):
                    # Проверяем, начинается ли путь после file:/// с /
                    path_part = old_ref[10:]  # убираем "file:///
                    if path_part and not path_part.startswith('/'):
                        count += 1

            if count > 0:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return count

    except Exception as e:
        print(f"❌ Ошибка в {file_path}: {e}")

    return 0


def main():
    base_path = Path("/Users/username/Documents/front-middle-schema")

    total_fixed = 0
    files_fixed = 0

    print("🔧 Исправляю пути в file:/// ссылках...")
    print("   Паттерн: file://Users -> file:///Users")
    print("   Паттерн: file:///Users -> file:////Users")

    # Обходим все JSON файлы
    for json_file in base_path.glob("**/*.json"):
        # Пропускаем служебные
        if any(part.startswith('.') for part in json_file.parts):
            continue

        fixed = fix_file(json_file)
        if fixed > 0:
            rel_path = json_file.relative_to(base_path)
            print(f"  ✅ {rel_path}: исправлено {fixed} ссылок")
            total_fixed += fixed
            files_fixed += 1

    print(f"\n📊 Итого:")
    print(f"  - Исправлено ссылок: {total_fixed}")
    print(f"  - Модифицировано файлов: {files_fixed}")

    if total_fixed == 0:
        print("\n✅ Все ссылки уже корректны!")


if __name__ == "__main__":
    main()