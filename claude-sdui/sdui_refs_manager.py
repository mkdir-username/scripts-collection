#!/usr/bin/env python3
"""
Скрипт для управления $ref ссылками в JSON схемах SDUI
Поддерживает конвертацию между относительными и абсолютными путями
"""

import json
import os
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

class SDUIRefsManager:
    def __init__(self, base_path: str):
        """
        Инициализация менеджера

        Args:
            base_path: Базовый путь к SDUI директории
        """
        self.base_path = Path(base_path).resolve()
        self.changes_made = 0
        self.files_processed = 0
        self.errors = []

    def resolve_ref_path(self, ref_value: str, current_file_path: Path) -> str:
        """Преобразует относительный путь в абсолютный file:/// URI"""
        # Пропускаем внутренние ссылки
        if ref_value.startswith("#"):
            return ref_value

        # Пропускаем уже абсолютные пути
        if ref_value.startswith("file:///"):
            return ref_value

        # Получаем директорию текущего файла
        current_dir = current_file_path.parent

        # Резолвим относительный путь
        try:
            resolved_path = (current_dir / ref_value).resolve()

            # Добавляем .json если его нет
            if not str(resolved_path).endswith('.json'):
                resolved_path = Path(str(resolved_path) + '.json')

            # Конвертируем в file:/// URI
            return f"file://{resolved_path}"
        except Exception as e:
            self.errors.append(f"Error resolving {ref_value} in {current_file_path}: {e}")
            return ref_value

    def make_relative_ref(self, ref_value: str, current_file_path: Path) -> str:
        """Преобразует абсолютный путь обратно в относительный"""
        # Пропускаем внутренние ссылки
        if ref_value.startswith("#"):
            return ref_value

        # Обрабатываем только абсолютные пути
        if ref_value.startswith("file:///"):
            try:
                # Извлекаем путь из file:/// URI
                abs_path = Path(ref_value.replace("file://", ""))

                # Получаем директорию текущего файла
                current_dir = current_file_path.parent

                # Вычисляем относительный путь
                rel_path = os.path.relpath(abs_path, current_dir)

                # Убираем .json из конца если он есть
                if rel_path.endswith('.json'):
                    rel_path = rel_path[:-5]

                # Заменяем обратные слеши на прямые для совместимости
                rel_path = rel_path.replace("\\", "/")

                return rel_path
            except Exception as e:
                self.errors.append(f"Error making relative {ref_value} in {current_file_path}: {e}")
                return ref_value

        return ref_value

    def process_refs_in_dict(self, obj: Any, current_file_path: Path, mode: str) -> None:
        """
        Рекурсивно обрабатывает $ref в словаре

        Args:
            obj: Объект для обработки
            current_file_path: Путь к текущему файлу
            mode: 'absolute' или 'relative'
        """
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key == "$ref" and isinstance(value, str):
                    old_value = value
                    if mode == "absolute":
                        new_value = self.resolve_ref_path(value, current_file_path)
                    else:  # relative
                        new_value = self.make_relative_ref(value, current_file_path)

                    if old_value != new_value:
                        obj[key] = new_value
                        self.changes_made += 1
                        print(f"  Changed: {old_value} -> {new_value}")
                else:
                    self.process_refs_in_dict(value, current_file_path, mode)
        elif isinstance(obj, list):
            for item in obj:
                self.process_refs_in_dict(item, current_file_path, mode)

    def process_schema_file(self, filepath: Path, mode: str, dry_run: bool = False) -> bool:
        """
        Обрабатывает один файл схемы

        Args:
            filepath: Путь к файлу
            mode: 'absolute' или 'relative'
            dry_run: Если True, только показать изменения без записи
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                schema = json.load(f)

            # Создаем копию для сравнения
            original = json.dumps(schema, sort_keys=True)

            # Сбрасываем счетчик изменений для этого файла
            file_changes = self.changes_made

            # Обрабатываем ссылки
            self.process_refs_in_dict(schema, filepath, mode)

            # Проверяем, были ли изменения
            modified = json.dumps(schema, sort_keys=True)
            if original != modified:
                if not dry_run:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(schema, f, indent=2, ensure_ascii=False)

                changes_count = self.changes_made - file_changes
                action = "Would change" if dry_run else "Changed"
                print(f"✓ {action} {changes_count} refs in: {filepath.relative_to(self.base_path.parent)}")
                return True

        except json.JSONDecodeError as e:
            self.errors.append(f"JSON error in {filepath}: {e}")
        except Exception as e:
            self.errors.append(f"Error processing {filepath}: {e}")

        return False

    def process_directory(self, mode: str, dry_run: bool = False, pattern: str = "**/*.json") -> None:
        """
        Обрабатывает все JSON файлы в директории

        Args:
            mode: 'absolute' или 'relative'
            dry_run: Если True, только показать изменения без записи
            pattern: Glob паттерн для поиска файлов
        """
        print(f"Processing directory: {self.base_path}")
        print(f"Mode: {mode}")
        print(f"Pattern: {pattern}")
        if dry_run:
            print("DRY RUN - no files will be modified\n")
        else:
            print()

        files_changed = 0

        for filepath in self.base_path.glob(pattern):
            # Пропускаем samples если не указано обратное
            if "samples" in str(filepath) and "--include-samples" not in sys.argv:
                continue

            self.files_processed += 1
            if self.process_schema_file(filepath, mode, dry_run):
                files_changed += 1

        # Итоговая статистика
        print(f"\n📊 Статистика:")
        print(f"  Обработано файлов: {self.files_processed}")
        print(f"  Изменено файлов: {files_changed}")
        print(f"  Всего изменено refs: {self.changes_made}")

        if self.errors:
            print(f"\n⚠️ Ошибки ({len(self.errors)}):")
            for error in self.errors[:10]:  # Показываем первые 10 ошибок
                print(f"  - {error}")
            if len(self.errors) > 10:
                print(f"  ... и ещё {len(self.errors) - 10} ошибок")

def main():
    parser = argparse.ArgumentParser(
        description="Управление $ref ссылками в JSON схемах SDUI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  # Конвертировать в абсолютные пути (по умолчанию)
  python sdui_refs_manager.py /Users/username/Documents/front-middle-schema/SDUI

  # Конвертировать обратно в относительные пути
  python sdui_refs_manager.py /Users/username/Documents/front-middle-schema/SDUI --relative

  # Только показать что будет изменено (dry run)
  python sdui_refs_manager.py /Users/username/Documents/front-middle-schema/SDUI --dry-run

  # Обработать только определенные файлы
  python sdui_refs_manager.py /Users/username/Documents/front-middle-schema/SDUI --pattern "components/*/v1/*.json"

  # Включить обработку samples
  python sdui_refs_manager.py /Users/username/Documents/front-middle-schema/SDUI --include-samples
        """
    )

    parser.add_argument("path", help="Путь к SDUI директории")
    parser.add_argument("--relative", action="store_true",
                        help="Конвертировать в относительные пути (по умолчанию в абсолютные)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Только показать изменения, не изменять файлы")
    parser.add_argument("--pattern", default="**/*.json",
                        help="Glob паттерн для поиска файлов (по умолчанию '**/*.json')")
    parser.add_argument("--include-samples", action="store_true",
                        help="Включить обработку файлов в папках samples")

    args = parser.parse_args()

    # Определяем режим
    mode = "relative" if args.relative else "absolute"

    # Создаем менеджер и запускаем обработку
    manager = SDUIRefsManager(args.path)
    manager.process_directory(mode, args.dry_run, args.pattern)

if __name__ == "__main__":
    main()