#!/usr/bin/env python3
"""
Universal JSON Schema $ref Converter
Преобразует ВСЕ относительные $ref в абсолютные file:/// пути
для ВСЕГО проекта front-middle-schema
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Set
import argparse
from datetime import datetime
import shutil


class UniversalRefConverter:
    """Универсальный конвертер для преобразования всех $ref в абсолютные пути"""

    def __init__(self, base_path: Path, verbose: bool = False, dry_run: bool = False):
        self.base_path = base_path.resolve()
        self.verbose = verbose
        self.dry_run = dry_run
        self.converted_count = 0
        self.files_modified = 0
        self.errors = []
        self.processed_files: Set[Path] = set()

    def convert_refs_in_file(self, file_path: Path) -> bool:
        """Конвертирует все ref'ы в одном файле"""
        try:
            # Читаем файл
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                original_content = content

            # Парсим JSON
            try:
                data = json.loads(content)
            except json.JSONDecodeError as e:
                if self.verbose:
                    print(f"  ⚠️  Пропускаю {file_path.name}: не валидный JSON - {e}")
                return False

            # Конвертируем ref'ы
            file_modified = self._convert_refs_recursive(data, file_path)

            # Если файл изменился, сохраняем
            if file_modified and not self.dry_run:
                new_content = json.dumps(data, indent=2, ensure_ascii=False)

                # Сохраняем с резервной копией
                backup_path = file_path.with_suffix('.json.backup')
                shutil.copy2(file_path, backup_path)

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                    if not new_content.endswith('\n'):
                        f.write('\n')

                # Удаляем резервную копию если всё прошло успешно
                backup_path.unlink()

                self.files_modified += 1
                return True

        except Exception as e:
            self.errors.append(f"{file_path}: {e}")
            if self.verbose:
                print(f"  ❌ Ошибка в {file_path.name}: {e}")

        return False

    def _convert_refs_recursive(self, obj: Any, source_file: Path, depth: int = 0) -> bool:
        """Рекурсивно конвертирует все $ref в объекте"""
        if depth > 50:  # Защита от бесконечной рекурсии
            return False

        modified = False

        if isinstance(obj, dict):
            for key, value in list(obj.items()):
                if key == "$ref" and isinstance(value, str):
                    new_ref = self._convert_ref(value, source_file)
                    if new_ref != value:
                        obj[key] = new_ref
                        self.converted_count += 1
                        modified = True
                        if self.verbose:
                            print(f"    ✓ {value} → file:///{Path(new_ref[8:]).as_posix()}")
                else:
                    if self._convert_refs_recursive(value, source_file, depth + 1):
                        modified = True

        elif isinstance(obj, list):
            for item in obj:
                if self._convert_refs_recursive(item, source_file, depth + 1):
                    modified = True

        return modified

    def _convert_ref(self, ref: str, source_file: Path) -> str:
        """Конвертирует одну $ref ссылку в абсолютный путь"""

        # Пропускаем уже абсолютные file:/// пути
        if ref.startswith("file:///"):
            return ref

        # Пропускаем внутренние ссылки (#/definitions/...)
        if ref.startswith("#"):
            return ref

        # Пропускаем HTTP/HTTPS ссылки
        if ref.startswith("http://") or ref.startswith("https://"):
            return ref

        # Обрабатываем относительные пути
        try:
            # Убираем file:// если есть (но не file:///)
            if ref.startswith("file://") and not ref.startswith("file:///"):
                ref = ref[7:]

            # Создаём Path объект
            if ref.startswith("/"):
                # Абсолютный путь от корня системы
                ref_path = Path(ref)
            else:
                # Относительный путь от текущего файла
                ref_path = (source_file.parent / ref).resolve()

            # Проверяем существование файла
            if not ref_path.exists():
                # Если файл не найден, возвращаем оригинальную ссылку
                if self.verbose:
                    print(f"    ⚠️  Файл не найден: {ref_path}")
                return ref

            # Конвертируем в file:/// URI
            # Убираем лидирующий слэш для POSIX путей
            posix_path = ref_path.as_posix()
            if posix_path.startswith('/'):
                absolute_uri = f"file://{posix_path}"
            else:
                absolute_uri = f"file:///{posix_path}"
            return absolute_uri

        except Exception as e:
            if self.verbose:
                print(f"    ⚠️  Не могу конвертировать: {ref} - {e}")
            return ref

    def process_directory(self, directory: Path, pattern: str = "**/*.json") -> None:
        """Обрабатывает все JSON файлы в директории"""
        print(f"\n📁 Обрабатываю директорию: {directory.name}")

        json_files = list(directory.glob(pattern))
        total_files = len(json_files)

        if total_files == 0:
            print(f"  ℹ️  Нет JSON файлов")
            return

        print(f"  📄 Найдено файлов: {total_files}")

        converted_in_dir = 0
        for i, json_file in enumerate(json_files, 1):
            # Пропускаем служебные файлы
            if any(part.startswith('.') for part in json_file.parts):
                continue

            # Пропускаем уже обработанные файлы
            if json_file in self.processed_files:
                continue

            self.processed_files.add(json_file)

            # Показываем прогресс
            if self.verbose or (i % 100 == 0):
                print(f"  [{i}/{total_files}] {json_file.name}...")

            # Конвертируем ref'ы
            if self.convert_refs_in_file(json_file):
                converted_in_dir += 1
                if not self.verbose:
                    print(f"  ✅ {json_file.relative_to(self.base_path)}")

        if converted_in_dir > 0:
            print(f"  ✨ Модифицировано файлов в {directory.name}: {converted_in_dir}")

    def process_all(self) -> None:
        """Обрабатывает ВСЕ директории в front-middle-schema"""

        # Список основных директорий для обработки
        main_dirs = [
            "SDUI",
            "widgets",
            "multistep",
            "valuefields",
            "dependentfields",
            "analytics",
            "metaschema",
            "api",
            "documentation"
        ]

        print(f"\n🚀 Начинаю обработку проекта: {self.base_path}")
        print(f"   Режим: {'DRY RUN (без изменений)' if self.dry_run else 'ОБНОВЛЕНИЕ ФАЙЛОВ'}")

        # Обрабатываем каждую директорию
        for dir_name in main_dirs:
            dir_path = self.base_path / dir_name
            if dir_path.exists() and dir_path.is_dir():
                self.process_directory(dir_path)

        # Обрабатываем корневые JSON файлы
        root_json_files = list(self.base_path.glob("*.json"))
        if root_json_files:
            print(f"\n📁 Корневые JSON файлы")
            for json_file in root_json_files:
                if json_file not in self.processed_files:
                    self.processed_files.add(json_file)
                    if self.convert_refs_in_file(json_file):
                        print(f"  ✅ {json_file.name}")

    def print_summary(self) -> None:
        """Выводит итоговую статистику"""
        print("\n" + "="*60)
        print("📊 ИТОГОВАЯ СТАТИСТИКА:")
        print(f"  📁 Обработано файлов: {len(self.processed_files)}")
        print(f"  ✏️  Модифицировано файлов: {self.files_modified}")
        print(f"  🔗 Конвертировано ссылок: {self.converted_count}")

        if self.errors:
            print(f"\n⚠️  Ошибки ({len(self.errors)}):")
            for error in self.errors[:10]:
                print(f"    - {error}")
            if len(self.errors) > 10:
                print(f"    ... и ещё {len(self.errors) - 10} ошибок")

        if self.dry_run:
            print("\n📌 Это был DRY RUN - файлы НЕ были изменены")
            print("   Запустите без флага --dry-run для применения изменений")


def main():
    parser = argparse.ArgumentParser(
        description="Универсальный конвертер $ref в абсолютные file:/// пути"
    )
    parser.add_argument(
        "path",
        nargs='?',
        default=".",
        help="Путь к проекту front-middle-schema (по умолчанию: текущая директория)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Только показать, что будет изменено, без реальных изменений"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Подробный вывод"
    )
    parser.add_argument(
        "-d", "--directory",
        help="Обработать только указанную директорию"
    )

    args = parser.parse_args()

    # Определяем базовый путь
    base_path = Path(args.path).resolve()

    # Ищем корень проекта front-middle-schema
    if base_path.name != "front-middle-schema":
        # Пытаемся найти front-middle-schema в родительских директориях
        for parent in base_path.parents:
            if parent.name == "front-middle-schema":
                base_path = parent
                break
        else:
            # Или в дочерних
            potential = base_path / "front-middle-schema"
            if potential.exists():
                base_path = potential

    if not base_path.exists():
        print(f"❌ Путь не существует: {base_path}")
        sys.exit(1)

    print(f"🎯 Базовый путь проекта: {base_path}")

    # Создаём конвертер
    converter = UniversalRefConverter(
        base_path=base_path,
        verbose=args.verbose,
        dry_run=args.dry_run
    )

    # Обрабатываем
    if args.directory:
        # Обработка конкретной директории
        target_dir = base_path / args.directory
        if not target_dir.exists():
            print(f"❌ Директория не существует: {target_dir}")
            sys.exit(1)
        converter.process_directory(target_dir)
    else:
        # Обработка всего проекта
        converter.process_all()

    # Выводим статистику
    converter.print_summary()


if __name__ == "__main__":
    main()