#!/usr/bin/env python3
"""
Исправляет битые ссылки, находя правильные пути к файлам
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import defaultdict


class BrokenRefFixer:
    """Исправляет битые ссылки, находя правильные файлы"""

    def __init__(self, base_path: Path, dry_run: bool = False):
        self.base_path = base_path.resolve()
        self.dry_run = dry_run

        # Статистика
        self.total_fixed = 0
        self.files_modified = 0

        # Кеш найденных файлов для быстрого поиска
        self.file_index: Dict[str, List[Path]] = defaultdict(list)
        self._build_file_index()

        # Известные перемещения
        self.known_moves = {
            "file:///Users/username/Documents/front-middle-schema/SDUI/components/BannerWrapper/v1/TextContent.json":
                "file:///Users/username/Documents/front-middle-schema/SDUI/atoms/Text/v1/TextContent.json",
        }

    def _build_file_index(self):
        """Строит индекс всех JSON файлов"""
        print("📚 Индексирую все JSON файлы...")

        for json_file in self.base_path.glob("**/*.json"):
            # Пропускаем служебные
            if any(part.startswith('.') for part in json_file.parts):
                continue

            filename = json_file.name
            self.file_index[filename].append(json_file)

        print(f"  ✅ Проиндексировано {sum(len(v) for v in self.file_index.values())} файлов")

    def find_correct_path(self, broken_ref: str) -> Optional[str]:
        """Пытается найти правильный путь для битой ссылки"""

        # Проверяем известные перемещения
        if broken_ref in self.known_moves:
            return self.known_moves[broken_ref]

        # Извлекаем имя файла из битой ссылки
        if broken_ref.startswith("file:///"):
            path_str = broken_ref[8:]  # Убираем file:///
        elif broken_ref.startswith("file://"):
            path_str = broken_ref[7:]  # Убираем file://
        else:
            return None

        filename = Path(path_str).name

        # Ищем файл в индексе
        if filename in self.file_index:
            candidates = self.file_index[filename]

            if len(candidates) == 1:
                # Только один кандидат - используем его
                correct_path = candidates[0]
                return f"file:///{correct_path.as_posix()}"

            elif len(candidates) > 1:
                # Несколько кандидатов - пытаемся выбрать наиболее подходящий
                broken_parts = Path(path_str).parts

                # Ищем максимальное совпадение путей
                best_match = None
                max_common = 0

                for candidate in candidates:
                    candidate_parts = candidate.parts

                    # Считаем общие части пути с конца
                    common = 0
                    for i in range(1, min(len(broken_parts), len(candidate_parts)) + 1):
                        if broken_parts[-i] == candidate_parts[-i]:
                            common += 1
                        else:
                            break

                    if common > max_common:
                        max_common = common
                        best_match = candidate

                if best_match and max_common >= 2:  # Минимум 2 общих компонента
                    return f"file:///{best_match.as_posix()}"

        return None

    def fix_file(self, file_path: Path) -> int:
        """Исправляет битые ссылки в файле"""
        fixed_count = 0

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                data = json.loads(content)

            def fix_refs_recursive(obj):
                nonlocal fixed_count

                if isinstance(obj, dict):
                    for key, value in list(obj.items()):
                        if key == "$ref" and isinstance(value, str):
                            if value.startswith("file://"):
                                # Проверяем существование
                                test_path = value[8:] if value.startswith("file:///") else value[7:]

                                if not Path(test_path).exists():
                                    # Пытаемся найти правильный путь
                                    correct_ref = self.find_correct_path(value)

                                    if correct_ref and correct_ref != value:
                                        obj[key] = correct_ref
                                        fixed_count += 1

                                        if not self.dry_run:
                                            print(f"    🔧 {value}")
                                            print(f"       → {correct_ref}")
                        else:
                            fix_refs_recursive(value)

                elif isinstance(obj, list):
                    for item in obj:
                        fix_refs_recursive(item)

            fix_refs_recursive(data)

            if fixed_count > 0 and not self.dry_run:
                # Сохраняем исправленный файл
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                    f.write('\n')

                self.total_fixed += fixed_count
                self.files_modified += 1

        except Exception as e:
            print(f"  ❌ Ошибка в {file_path}: {e}")

        return fixed_count

    def scan_and_fix(self):
        """Сканирует все файлы и исправляет битые ссылки"""

        print(f"\n🔍 {'PREVIEW' if self.dry_run else 'ИСПРАВЛЕНИЕ'} битых ссылок...")

        # Сначала найдём все файлы с проблемами
        files_with_issues = []

        for json_file in self.base_path.glob("**/*.json"):
            # Пропускаем служебные
            if any(part.startswith('.') for part in json_file.parts):
                continue

            # Быстрая проверка на наличие битых ссылок
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Простой поиск file:// ссылок
                if '"file://' in content:
                    data = json.loads(content)

                    def has_broken_refs(obj):
                        if isinstance(obj, dict):
                            for key, value in obj.items():
                                if key == "$ref" and isinstance(value, str):
                                    if value.startswith("file://"):
                                        test_path = value[8:] if value.startswith("file:///") else value[7:]
                                        if not Path(test_path).exists():
                                            return True
                                else:
                                    if has_broken_refs(value):
                                        return True
                        elif isinstance(obj, list):
                            for item in obj:
                                if has_broken_refs(item):
                                    return True
                        return False

                    if has_broken_refs(data):
                        files_with_issues.append(json_file)

            except:
                continue

        if not files_with_issues:
            print("✅ Битых ссылок не найдено!")
            return

        print(f"📋 Найдено файлов с битыми ссылками: {len(files_with_issues)}")

        # Исправляем
        for json_file in files_with_issues:
            rel_path = json_file.relative_to(self.base_path)
            fixed = self.fix_file(json_file)

            if fixed > 0:
                if self.dry_run:
                    print(f"  🔍 {rel_path}: найдено {fixed} битых ссылок")
                else:
                    print(f"  ✅ {rel_path}: исправлено {fixed} ссылок")

        # Итоги
        print(f"\n📊 Итоги:")
        if self.dry_run:
            print(f"  • Найдено битых ссылок: {self.total_fixed}")
            print(f"  • Файлов с проблемами: {self.files_modified}")
            print(f"\n💡 Запустите без --dry-run для исправления")
        else:
            print(f"  • Исправлено ссылок: {self.total_fixed}")
            print(f"  • Модифицировано файлов: {self.files_modified}")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Исправляет битые $ref ссылки, находя правильные пути"
    )
    parser.add_argument(
        "path",
        nargs='?',
        default=".",
        help="Путь к проекту front-middle-schema"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Только показать что будет исправлено"
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

    # Создаём исправитель
    fixer = BrokenRefFixer(base_path, dry_run=args.dry_run)

    # Запускаем исправление
    fixer.scan_and_fix()


if __name__ == "__main__":
    main()