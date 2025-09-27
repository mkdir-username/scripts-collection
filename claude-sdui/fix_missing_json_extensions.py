#!/usr/bin/env python3
"""
Исправление отсутствующих расширений .json в $ref ссылках
"""

import json
import re
from pathlib import Path
import sys
import argparse


class JsonExtensionFixer:
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.fixed_count = 0
        self.files_modified = 0
        self.errors = []

    def fix_refs_in_file(self, file_path: Path) -> bool:
        """Исправляет ссылки в одном файле"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                original_content = content

            data = json.loads(content)
            modified = self._fix_refs_recursive(data, file_path)

            if modified:
                # Сохраняем с правильным форматированием
                new_content = json.dumps(data, indent=2, ensure_ascii=False)

                if new_content != original_content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                        if not new_content.endswith('\n'):
                            f.write('\n')

                    self.files_modified += 1
                    return True

        except Exception as e:
            self.errors.append(f"{file_path}: {e}")

        return False

    def _fix_refs_recursive(self, obj: any, source_file: Path, depth: int = 0) -> bool:
        """Рекурсивно исправляет $ref ссылки"""
        if depth > 20:  # Защита от бесконечной рекурсии
            return False

        modified = False

        if isinstance(obj, dict):
            for key, value in list(obj.items()):
                if key == "$ref" and isinstance(value, str):
                    new_value = self._fix_ref(value, source_file)
                    if new_value != value:
                        obj[key] = new_value
                        self.fixed_count += 1
                        modified = True
                        print(f"  ✓ Исправлено: {value} → {new_value}")
                else:
                    if self._fix_refs_recursive(value, source_file, depth + 1):
                        modified = True

        elif isinstance(obj, list):
            for item in obj:
                if self._fix_refs_recursive(item, source_file, depth + 1):
                    modified = True

        return modified

    def _fix_ref(self, ref: str, source_file: Path) -> str:
        """Исправляет одну ссылку"""
        # Пропускаем внутренние ссылки
        if ref.startswith("#"):
            return ref

        # Обрабатываем file:// ссылки
        if ref.startswith("file://"):
            path_part = ref[7:]  # Убираем file://

            # Проверяем, есть ли уже расширение
            if not path_part.endswith('.json'):
                # Проверяем существование файла
                test_path = Path(path_part + '.json')
                if test_path.exists():
                    return f"file://{path_part}.json"

                # Также проверяем без file://
                test_path2 = Path(path_part)
                if test_path2.exists() and test_path2.suffix == '':
                    # Ищем файл с расширением .json
                    json_file = test_path2.parent / f"{test_path2.name}.json"
                    if json_file.exists():
                        return f"file://{path_part}.json"

        # Обрабатываем относительные пути
        elif not ref.startswith("http"):
            if not ref.endswith('.json') and '.' not in ref.split('/')[-1]:
                # Это может быть путь без расширения
                # Пробуем найти файл относительно текущего
                if source_file:
                    base_dir = source_file.parent
                    test_path = base_dir / f"{ref}.json"

                    # Упрощаем путь
                    try:
                        test_path = test_path.resolve()
                        if test_path.exists():
                            # Конвертируем в file:// формат
                            return f"file://{test_path}"
                    except:
                        pass

        return ref

    def scan_directory(self, directory: Path) -> None:
        """Сканирует директорию и исправляет все файлы"""
        print(f"🔍 Сканирование директории: {directory}")

        json_files = list(directory.glob("**/*.json"))
        print(f"📁 Найдено JSON файлов: {len(json_files)}")

        for json_file in json_files:
            # Пропускаем файлы в .git и других служебных директориях
            if any(part.startswith('.') for part in json_file.parts):
                continue

            if self.fix_refs_in_file(json_file):
                print(f"✅ Исправлен: {json_file.relative_to(self.base_path)}")

    def print_summary(self) -> None:
        """Выводит итоговую статистику"""
        print("\n" + "="*60)
        print("📊 ИТОГИ:")
        print(f"  ✓ Исправлено ссылок: {self.fixed_count}")
        print(f"  ✓ Модифицировано файлов: {self.files_modified}")

        if self.errors:
            print(f"\n⚠️  Ошибки ({len(self.errors)}):")
            for error in self.errors[:10]:
                print(f"    - {error}")


def main():
    parser = argparse.ArgumentParser(
        description="Исправление отсутствующих расширений .json в $ref ссылках"
    )
    parser.add_argument(
        "path",
        help="Путь к директории или файлу для исправления"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Только показать, что будет исправлено, без изменений"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Подробный вывод"
    )

    args = parser.parse_args()

    target_path = Path(args.path).resolve()

    if not target_path.exists():
        print(f"❌ Путь не существует: {target_path}")
        sys.exit(1)

    fixer = JsonExtensionFixer(target_path.parent if target_path.is_file() else target_path)

    if target_path.is_file():
        print(f"🔧 Исправление файла: {target_path}")
        if fixer.fix_refs_in_file(target_path):
            print("✅ Файл исправлен")
    else:
        fixer.scan_directory(target_path)

    fixer.print_summary()


if __name__ == "__main__":
    main()