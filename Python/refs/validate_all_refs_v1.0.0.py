#!/usr/bin/env python3
"""
Валидатор всех $ref ссылок в JSON схемах
Проверяет корректность и доступность всех локальных ссылок
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
import argparse
from collections import defaultdict
from datetime import datetime
import re


class RefValidator:
    """Валидатор для проверки всех $ref ссылок"""

    def __init__(self, base_path: Path, verbose: bool = False, fix: bool = False):
        self.base_path = base_path.resolve()
        self.verbose = verbose
        self.fix = fix

        # Статистика
        self.total_refs = 0
        self.valid_refs = 0
        self.invalid_refs = 0
        self.internal_refs = 0
        self.fixed_refs = 0

        # Детальные отчёты
        self.broken_refs: Dict[Path, List[Tuple[str, str]]] = defaultdict(list)
        self.missing_extensions: Dict[Path, List[str]] = defaultdict(list)
        self.invalid_format: Dict[Path, List[str]] = defaultdict(list)
        self.circular_refs: Set[Tuple[Path, Path]] = set()
        self.processed_files: Set[Path] = set()

    def validate_file(self, file_path: Path) -> Dict[str, Any]:
        """Валидирует все ссылки в одном файле"""
        result = {
            'file': file_path,
            'total_refs': 0,
            'valid_refs': 0,
            'invalid_refs': 0,
            'errors': []
        }

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            try:
                data = json.loads(content)
            except json.JSONDecodeError as e:
                result['errors'].append(f"JSON parse error: {e}")
                return result

            # Валидируем все ref'ы
            self._validate_refs_recursive(data, file_path, result)

            # Если нужно исправить и есть ошибки
            if self.fix and result['invalid_refs'] > 0:
                self._fix_refs_in_file(file_path, data)

        except Exception as e:
            result['errors'].append(f"Error reading file: {e}")

        return result

    def _validate_refs_recursive(self, obj: Any, source_file: Path, result: Dict,
                                depth: int = 0, visited: Set[str] = None) -> None:
        """Рекурсивно валидирует все $ref в объекте"""
        if depth > 50:  # Защита от бесконечной рекурсии
            return

        if visited is None:
            visited = set()

        if isinstance(obj, dict):
            for key, value in obj.items():
                if key == "$ref" and isinstance(value, str):
                    result['total_refs'] += 1
                    self.total_refs += 1

                    validation = self._validate_single_ref(value, source_file, visited)

                    if validation['valid']:
                        result['valid_refs'] += 1
                        self.valid_refs += 1
                    else:
                        result['invalid_refs'] += 1
                        self.invalid_refs += 1
                        result['errors'].append(validation['error'])

                        # Категоризируем ошибку
                        if validation['category'] == 'broken':
                            self.broken_refs[source_file].append((value, validation['error']))
                        elif validation['category'] == 'missing_extension':
                            self.missing_extensions[source_file].append(value)
                        elif validation['category'] == 'invalid_format':
                            self.invalid_format[source_file].append(value)
                else:
                    self._validate_refs_recursive(value, source_file, result, depth + 1, visited)

        elif isinstance(obj, list):
            for item in obj:
                self._validate_refs_recursive(item, source_file, result, depth + 1, visited)

    def _validate_single_ref(self, ref: str, source_file: Path, visited: Set[str]) -> Dict:
        """Валидирует одну $ref ссылку"""

        # Внутренние ссылки (#/definitions/...)
        if ref.startswith("#"):
            self.internal_refs += 1
            return {'valid': True, 'category': 'internal'}

        # HTTP/HTTPS ссылки
        if ref.startswith("http://") or ref.startswith("https://"):
            return {'valid': True, 'category': 'external'}

        # file:/// ссылки
        if ref.startswith("file:///"):
            # Проверяем формат (должно быть 3 слэша, не 4)
            if ref.startswith("file:////"):
                return {
                    'valid': False,
                    'category': 'invalid_format',
                    'error': f"Invalid format (4 slashes): {ref}"
                }

            # Извлекаем путь
            path_str = ref[7:]  # Убираем file:// (7 символов)

            # Проверяем расширение
            if not path_str.endswith('.json'):
                return {
                    'valid': False,
                    'category': 'missing_extension',
                    'error': f"Missing .json extension: {ref}"
                }

            # Проверяем существование файла
            target_path = Path(path_str)
            if not target_path.exists():
                return {
                    'valid': False,
                    'category': 'broken',
                    'error': f"File not found: {path_str}"
                }

            # Не открываем файл, просто проверяем существование
            # Циклические зависимости не проверяем без открытия файлов

            return {'valid': True, 'category': 'local'}

        # Относительные пути (не должны быть в финальной версии)
        if "../" in ref or "./" in ref or not ref.startswith("file://"):
            return {
                'valid': False,
                'category': 'invalid_format',
                'error': f"Relative path should be absolute: {ref}"
            }

        return {
            'valid': False,
            'category': 'unknown',
            'error': f"Unknown reference format: {ref}"
        }

    def _fix_refs_in_file(self, file_path: Path, data: Any) -> bool:
        """Пытается исправить проблемные ссылки"""
        fixed = False

        def fix_recursive(obj: Any) -> bool:
            nonlocal fixed

            if isinstance(obj, dict):
                for key, value in list(obj.items()):
                    if key == "$ref" and isinstance(value, str):
                        new_ref = self._try_fix_ref(value, file_path)
                        if new_ref != value:
                            obj[key] = new_ref
                            fixed = True
                            self.fixed_refs += 1
                            if self.verbose:
                                print(f"  🔧 Fixed: {value} → {new_ref}")
                    else:
                        fix_recursive(value)
            elif isinstance(obj, list):
                for item in obj:
                    fix_recursive(item)

            return fixed

        if fix_recursive(data):
            # Сохраняем исправленный файл
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.write('\n')
            return True

        return False

    def _try_fix_ref(self, ref: str, source_file: Path) -> str:
        """Пытается исправить проблемную ссылку"""

        # Исправляем 4 слэша на 3
        if ref.startswith("file:////"):
            ref = "file:///" + ref[9:]

        # Добавляем .json если отсутствует
        if ref.startswith("file:///") and not ref.endswith('.json'):
            test_path = ref + '.json'
            if Path(test_path[8:]).exists():
                return test_path

        # Конвертируем относительные пути в абсолютные
        if not ref.startswith("file:///") and not ref.startswith("#") and not ref.startswith("http"):
            if ref.startswith("../") or ref.startswith("./"):
                try:
                    target = (source_file.parent / ref).resolve()
                    if target.exists():
                        return f"file:///{target.as_posix()}"
                except:
                    pass

        return ref

    def scan_directory(self, directory: Path, pattern: str = "**/*.json") -> None:
        """Сканирует директорию и валидирует все JSON файлы"""
        print(f"\n🔍 Сканирование: {directory.relative_to(self.base_path)}")

        json_files = list(directory.glob(pattern))
        total = len(json_files)

        if total == 0:
            print("  ℹ️  Нет JSON файлов")
            return

        print(f"  📄 Найдено файлов: {total}")

        errors_in_dir = 0
        for i, json_file in enumerate(json_files, 1):
            # Пропускаем служебные файлы
            if any(part.startswith('.') for part in json_file.parts):
                continue

            if json_file in self.processed_files:
                continue

            self.processed_files.add(json_file)

            # Прогресс
            if i % 100 == 0 or self.verbose:
                print(f"  [{i}/{total}] {json_file.name}...")

            # Валидируем файл
            result = self.validate_file(json_file)

            if result['invalid_refs'] > 0:
                errors_in_dir += 1
                if not self.verbose:
                    rel_path = json_file.relative_to(self.base_path)
                    print(f"  ❌ {rel_path}: {result['invalid_refs']} invalid refs")

        if errors_in_dir > 0:
            print(f"  ⚠️  Файлов с ошибками: {errors_in_dir}")

    def scan_all(self) -> None:
        """Сканирует весь проект"""

        directories = [
            "SDUI",
            "widgets",
            "multistep",
            "valuefields",
            "dependentfields",
            "analytics",
            "metaschema"
        ]

        for dir_name in directories:
            dir_path = self.base_path / dir_name
            if dir_path.exists():
                self.scan_directory(dir_path)

    def print_report(self) -> None:
        """Выводит подробный отчёт"""
        print("\n" + "="*60)
        print("📊 ОТЧЁТ ВАЛИДАЦИИ")
        print("="*60)

        # Общая статистика
        print(f"\n📈 Общая статистика:")
        print(f"  • Всего файлов проверено: {len(self.processed_files)}")
        print(f"  • Всего ссылок: {self.total_refs}")
        print(f"  • ✅ Валидных: {self.valid_refs}")
        print(f"  • ❌ Невалидных: {self.invalid_refs}")
        print(f"  • 🔗 Внутренних (#): {self.internal_refs}")

        if self.fix:
            print(f"  • 🔧 Исправлено: {self.fixed_refs}")

        # Детализация ошибок
        if self.broken_refs:
            print(f"\n❌ БИТЫЕ ССЫЛКИ ({sum(len(v) for v in self.broken_refs.values())} total):")
            for file, refs in list(self.broken_refs.items())[:10]:
                print(f"\n  📄 {file.relative_to(self.base_path)}:")
                for ref, error in refs[:3]:
                    print(f"    • {ref}")
                    print(f"      {error}")
                if len(refs) > 3:
                    print(f"    ... и ещё {len(refs) - 3}")

        if self.missing_extensions:
            print(f"\n⚠️  БЕЗ РАСШИРЕНИЯ .json ({sum(len(v) for v in self.missing_extensions.values())} total):")
            for file, refs in list(self.missing_extensions.items())[:5]:
                print(f"  📄 {file.relative_to(self.base_path)}:")
                for ref in refs[:3]:
                    print(f"    • {ref}")

        if self.invalid_format:
            print(f"\n⚠️  НЕВЕРНЫЙ ФОРМАТ ({sum(len(v) for v in self.invalid_format.values())} total):")
            for file, refs in list(self.invalid_format.items())[:5]:
                print(f"  📄 {file.relative_to(self.base_path)}:")
                for ref in refs[:3]:
                    print(f"    • {ref}")

        if self.circular_refs:
            print(f"\n🔄 ЦИКЛИЧЕСКИЕ ЗАВИСИМОСТИ ({len(self.circular_refs)} total):")
            for source, target in list(self.circular_refs)[:5]:
                print(f"  • {source.name} → {target.name}")

        # Результат
        if self.invalid_refs == 0:
            print("\n✅ ВСЕ ССЫЛКИ КОРРЕКТНЫ!")
        else:
            print(f"\n❌ НАЙДЕНО ПРОБЛЕМ: {self.invalid_refs}")
            if not self.fix:
                print("   Используйте --fix для автоматического исправления")


def main():
    parser = argparse.ArgumentParser(
        description="Валидатор всех $ref ссылок в JSON схемах"
    )
    parser.add_argument(
        "path",
        nargs='?',
        default=".",
        help="Путь к проекту front-middle-schema"
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Автоматически исправить проблемы где возможно"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Подробный вывод"
    )
    parser.add_argument(
        "-d", "--directory",
        help="Проверить только указанную директорию"
    )
    parser.add_argument(
        "-f", "--file",
        help="Проверить только указанный файл"
    )

    args = parser.parse_args()

    # Определяем базовый путь
    base_path = Path(args.path).resolve()

    # Ищем корень проекта
    if base_path.name != "front-middle-schema":
        for parent in base_path.parents:
            if parent.name == "front-middle-schema":
                base_path = parent
                break
        else:
            potential = base_path / "front-middle-schema"
            if potential.exists():
                base_path = potential

    if not base_path.exists():
        print(f"❌ Путь не существует: {base_path}")
        sys.exit(1)

    print(f"🎯 Проект: {base_path}")
    print(f"📋 Режим: {'ИСПРАВЛЕНИЕ' if args.fix else 'ПРОВЕРКА'}")

    # Создаём валидатор
    validator = RefValidator(
        base_path=base_path,
        verbose=args.verbose,
        fix=args.fix
    )

    # Запускаем проверку
    start_time = datetime.now()

    if args.file:
        # Проверка одного файла
        file_path = Path(args.file).resolve()
        if not file_path.exists():
            print(f"❌ Файл не найден: {file_path}")
            sys.exit(1)
        result = validator.validate_file(file_path)
        print(f"\n📄 {file_path.name}:")
        print(f"  • Всего ссылок: {result['total_refs']}")
        print(f"  • ✅ Валидных: {result['valid_refs']}")
        print(f"  • ❌ Невалидных: {result['invalid_refs']}")
        if result['errors']:
            print(f"  • Ошибки:")
            for error in result['errors']:
                print(f"    - {error}")

    elif args.directory:
        # Проверка директории
        target_dir = base_path / args.directory
        if not target_dir.exists():
            print(f"❌ Директория не найдена: {target_dir}")
            sys.exit(1)
        validator.scan_directory(target_dir)
        validator.print_report()

    else:
        # Проверка всего проекта
        validator.scan_all()
        validator.print_report()

    # Время выполнения
    elapsed = datetime.now() - start_time
    print(f"\n⏱️  Время выполнения: {elapsed.total_seconds():.2f} сек")

    # Код выхода
    sys.exit(0 if validator.invalid_refs == 0 else 1)


if __name__ == "__main__":
    main()