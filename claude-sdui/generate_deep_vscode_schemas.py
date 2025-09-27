#!/usr/bin/env python3
"""
Генератор конфигурации VS Code для ГЛУБОКОЙ валидации SDUI схем.
Обеспечивает полную иерархию валидации включая все вложенные схемы и атомарные типы.
"""

import json
from pathlib import Path
import sys
from typing import Dict, List, Set, Optional
import argparse
from collections import defaultdict

class SDUIDeepSchemaGenerator:
    """Генератор схем с поддержкой глубокой иерархии валидации"""

    def __init__(self, sdui_path: Path):
        self.sdui_path = sdui_path
        self.schemas = []
        self.processed_refs = set()
        self.atomic_types = {}
        self.schema_dependencies = defaultdict(set)

    def scan_directory(self) -> None:
        """Сканирование всей директории SDUI"""
        print("🔍 Сканирование SDUI директории для глубокого анализа...")

        # 1. Собираем ВСЕ атомарные типы
        self._collect_atomic_types()

        # 2. Компоненты с полной иерархией
        self._process_components_deep()

        # 3. Атомы
        self._process_atoms()

        # 4. Layouts
        self._process_layouts_deep()

        # 5. Actions
        self._process_actions_deep()

        # 6. Functions
        self._process_functions_deep()

        # 7. Models
        self._process_models()

        # 8. SDUIScreen
        self._process_sdui_screen()

        # 9. Common
        self._process_common()

        # 10. Специальные схемы для вложенных типов
        self._process_nested_schemas()

        # 11. Метасхема
        self._add_metaschema_configs()

    def _collect_atomic_types(self) -> None:
        """Собираем все атомарные типы для глубокой валидации"""
        print("  📦 Собираю атомарные типы...")

        # Атомы
        atoms_path = self.sdui_path / "atoms"
        if atoms_path.exists():
            for atom_dir in atoms_path.iterdir():
                if atom_dir.is_dir():
                    self._scan_atomic_schemas(atom_dir)

        # Специальные типы в компонентах (Shape, Size и т.д.)
        components_path = self.sdui_path / "components"
        if components_path.exists():
            for comp_dir in components_path.glob("*/v*"):
                for schema_file in comp_dir.glob("*.json"):
                    if not schema_file.name.startswith(comp_dir.parent.name):
                        # Это вспомогательная схема (напр. IconViewShape.json)
                        self._register_atomic_type(schema_file)

    def _scan_atomic_schemas(self, atom_dir: Path) -> None:
        """Сканирование атомарных схем"""
        for schema_file in atom_dir.glob("**/*.json"):
            if not any(p.name == "samples" for p in schema_file.parents):
                self._register_atomic_type(schema_file)

    def _register_atomic_type(self, schema_file: Path) -> None:
        """Регистрация атомарного типа"""
        try:
            with open(schema_file, 'r', encoding='utf-8') as f:
                schema_data = json.load(f)
                name = schema_data.get('name', schema_file.stem)
                self.atomic_types[name] = schema_file

                # Добавляем схему для этого типа
                pattern = f"**/{name}.json"
                self.schemas.append({
                    "fileMatch": [f"**/SDUI/**/{pattern}"],
                    "url": f"file://{schema_file.absolute()}"
                })
        except:
            pass

    def _process_components_deep(self) -> None:
        """Обработка компонентов с глубокой иерархией"""
        print("  🧩 Обрабатываю компоненты с полной иерархией...")

        components_path = self.sdui_path / "components"
        if not components_path.exists():
            return

        for comp_dir in sorted(components_path.iterdir()):
            if not comp_dir.is_dir():
                continue

            comp_name = comp_dir.name

            # Обрабатываем каждую версию
            for version_dir in sorted(comp_dir.iterdir()):
                if not version_dir.is_dir() or not version_dir.name.startswith('v'):
                    continue

                version = version_dir.name
                schema_file = version_dir / f"{comp_name}.json"

                if schema_file.exists():
                    # Основная схема компонента
                    self.schemas.append({
                        "fileMatch": [
                            f"**/SDUI/components/{comp_name}/{version}/samples/*.json",
                            f"**/SDUI/components/{comp_name}/{version}/test*.json",
                            f"**/{comp_name}_*.json",
                            f"**/*_{comp_name}.json"
                        ],
                        "url": f"file://{schema_file.absolute()}"
                    })

                    # Анализируем зависимости схемы
                    self._analyze_schema_dependencies(schema_file)

                    # Вспомогательные схемы в той же директории
                    for aux_schema in version_dir.glob("*.json"):
                        if aux_schema.name != f"{comp_name}.json":
                            # Это вспомогательная схема (напр. IconViewShape.json)
                            aux_name = aux_schema.stem
                            self.schemas.append({
                                "fileMatch": [
                                    f"**/{aux_name}*.json",
                                    f"**/*{aux_name}.json"
                                ],
                                "url": f"file://{aux_schema.absolute()}"
                            })

                    # Presets
                    presets_dir = version_dir / "presets"
                    if presets_dir.exists():
                        self._process_presets_deep(presets_dir, comp_name)

    def _process_presets_deep(self, presets_dir: Path, comp_name: str) -> None:
        """Обработка пресетов с глубокой иерархией"""
        for preset_file in presets_dir.glob("**/*.json"):
            preset_name = preset_file.stem
            relative_path = preset_file.relative_to(presets_dir)

            # Создаём паттерны для разных уровней вложенности
            patterns = [
                f"**/presets/**/{preset_name}.json",
                f"**/{comp_name}/**/{preset_name}.json",
                f"**/{preset_name}.json"
            ]

            self.schemas.append({
                "fileMatch": patterns,
                "url": f"file://{preset_file.absolute()}"
            })

    def _analyze_schema_dependencies(self, schema_file: Path) -> None:
        """Анализ зависимостей схемы для построения полной иерархии"""
        try:
            with open(schema_file, 'r', encoding='utf-8') as f:
                schema_data = json.load(f)
                self._extract_refs_recursive(schema_data, schema_file)
        except:
            pass

    def _extract_refs_recursive(self, obj: any, source_file: Path, depth: int = 0) -> None:
        """Рекурсивное извлечение всех $ref ссылок"""
        if depth > 10:  # Защита от бесконечной рекурсии
            return

        if isinstance(obj, dict):
            for key, value in obj.items():
                if key == "$ref" and isinstance(value, str):
                    if value.startswith("file://"):
                        ref_path = Path(value.replace("file://", ""))
                        if ref_path.exists():
                            self.schema_dependencies[source_file].add(ref_path)
                            # Рекурсивно анализируем зависимую схему
                            if ref_path not in self.processed_refs:
                                self.processed_refs.add(ref_path)
                                self._analyze_schema_dependencies(ref_path)
                else:
                    self._extract_refs_recursive(value, source_file, depth + 1)
        elif isinstance(obj, list):
            for item in obj:
                self._extract_refs_recursive(item, source_file, depth + 1)

    def _process_atoms(self) -> None:
        """Обработка атомов"""
        print("  ⚛️ Обрабатываю атомы...")

        atoms_path = self.sdui_path / "atoms"
        if not atoms_path.exists():
            return

        for atom_dir in sorted(atoms_path.iterdir()):
            if not atom_dir.is_dir():
                continue

            atom_name = atom_dir.name

            # Версионные атомы
            for version_dir in atom_dir.glob("v*"):
                if version_dir.is_dir():
                    for schema_file in version_dir.glob("*.json"):
                        self.schemas.append({
                            "fileMatch": [
                                f"**/atoms/{atom_name}/{version_dir.name}/**/*.json",
                                f"**/{schema_file.stem}*.json"
                            ],
                            "url": f"file://{schema_file.absolute()}"
                        })

            # Неверсионные атомы
            main_schema = atom_dir / f"{atom_name}.json"
            if main_schema.exists():
                self.schemas.append({
                    "fileMatch": [
                        f"**/atoms/{atom_name}/**/*.json",
                        f"**/{atom_name}*.json",
                        f"**/*_{atom_name}.json"
                    ],
                    "url": f"file://{main_schema.absolute()}"
                })

    def _process_layouts_deep(self) -> None:
        """Обработка layouts с глубокой иерархией"""
        print("  📐 Обрабатываю layouts...")

        layouts_path = self.sdui_path / "layouts"
        if not layouts_path.exists():
            return

        for layout_dir in sorted(layouts_path.iterdir()):
            if not layout_dir.is_dir():
                continue

            layout_name = layout_dir.name

            for version_dir in sorted(layout_dir.iterdir()):
                if not version_dir.is_dir() or not version_dir.name.startswith('v'):
                    continue

                version = version_dir.name
                schema_file = version_dir / f"{layout_name}.json"

                if schema_file.exists():
                    self.schemas.append({
                        "fileMatch": [
                            f"**/layouts/{layout_name}/{version}/**/*.json",
                            f"**/{layout_name}_*.json"
                        ],
                        "url": f"file://{schema_file.absolute()}"
                    })

                    # Вспомогательные схемы
                    for aux_schema in version_dir.glob("*.json"):
                        if aux_schema != schema_file:
                            self.schemas.append({
                                "fileMatch": [f"**/{aux_schema.stem}*.json"],
                                "url": f"file://{aux_schema.absolute()}"
                            })

    def _process_actions_deep(self) -> None:
        """Обработка actions с глубокой иерархией"""
        print("  ⚡ Обрабатываю actions...")

        actions_path = self.sdui_path / "actions"
        if not actions_path.exists():
            return

        for action_dir in sorted(actions_path.iterdir()):
            if not action_dir.is_dir():
                continue

            # Ищем главную схему действия
            for schema_file in action_dir.glob("*.json"):
                action_name = schema_file.stem
                self.schemas.append({
                    "fileMatch": [
                        f"**/actions/{action_dir.name}/**/*.json",
                        f"**/{action_name}*.json"
                    ],
                    "url": f"file://{schema_file.absolute()}"
                })

            # Версионные действия
            for version_dir in action_dir.glob("v*"):
                if version_dir.is_dir():
                    for schema_file in version_dir.glob("*.json"):
                        self.schemas.append({
                            "fileMatch": [
                                f"**/actions/{action_dir.name}/{version_dir.name}/**/*.json",
                                f"**/{schema_file.stem}*.json"
                            ],
                            "url": f"file://{schema_file.absolute()}"
                        })

    def _process_functions_deep(self) -> None:
        """Обработка functions с глубокой иерархией"""
        print("  🔧 Обрабатываю functions...")

        functions_path = self.sdui_path / "functions"
        if not functions_path.exists():
            return

        # Обрабатываем каждую категорию функций
        for category_dir in sorted(functions_path.iterdir()):
            if not category_dir.is_dir():
                continue

            category = category_dir.name

            # Обрабатываем каждую функцию в категории
            for func_dir in sorted(category_dir.iterdir()):
                if not func_dir.is_dir():
                    continue

                # Версионные функции
                for version_dir in func_dir.glob("v*"):
                    if version_dir.is_dir():
                        for schema_file in version_dir.glob("*.json"):
                            func_name = schema_file.stem
                            self.schemas.append({
                                "fileMatch": [
                                    f"**/functions/{category}/{func_dir.name}/{version_dir.name}/**/*.json",
                                    f"**/{func_name}*.json"
                                ],
                                "url": f"file://{schema_file.absolute()}"
                            })

    def _process_models(self) -> None:
        """Обработка models"""
        print("  📊 Обрабатываю models...")

        models_path = self.sdui_path / "models"
        if not models_path.exists():
            return

        for model_file in models_path.glob("**/*.json"):
            if not any(p.name == "samples" for p in model_file.parents):
                model_name = model_file.stem
                self.schemas.append({
                    "fileMatch": [
                        f"**/models/**/{model_name}.json",
                        f"**/{model_name}*.json"
                    ],
                    "url": f"file://{model_file.absolute()}"
                })

    def _process_sdui_screen(self) -> None:
        """Обработка SDUIScreen"""
        print("  📱 Обрабатываю SDUIScreen...")

        screen_path = self.sdui_path / "SDUIScreen"
        if not screen_path.exists():
            return

        for version_dir in screen_path.glob("v*"):
            if version_dir.is_dir():
                for schema_file in version_dir.glob("*.json"):
                    schema_name = schema_file.stem
                    self.schemas.append({
                        "fileMatch": [
                            f"**/SDUIScreen/{version_dir.name}/**/{schema_name}.json",
                            f"**/{schema_name}*.json"
                        ],
                        "url": f"file://{schema_file.absolute()}"
                    })

    def _process_common(self) -> None:
        """Обработка common"""
        print("  🔗 Обрабатываю common...")

        common_path = self.sdui_path / "common"
        if not common_path.exists():
            return

        for common_dir in sorted(common_path.iterdir()):
            if not common_dir.is_dir():
                continue

            for schema_file in common_dir.glob("**/*.json"):
                if not any(p.name == "samples" for p in schema_file.parents):
                    schema_name = schema_file.stem
                    self.schemas.append({
                        "fileMatch": [
                            f"**/common/**/{schema_name}.json",
                            f"**/{schema_name}*.json"
                        ],
                        "url": f"file://{schema_file.absolute()}"
                    })

    def _process_nested_schemas(self) -> None:
        """Создание специальных схем для вложенных типов"""
        print("  🔄 Создаю схемы для вложенных типов...")

        # Для каждого компонента создаём дополнительные паттерны
        for schema_entry in list(self.schemas):
            if "components" in schema_entry["url"]:
                # Добавляем паттерны для вложенных объектов
                base_patterns = schema_entry.get("fileMatch", [])
                extended_patterns = []

                for pattern in base_patterns:
                    # Добавляем паттерны для частичных файлов
                    if "samples" in pattern:
                        comp_match = pattern.split("/components/")[1].split("/")[0]
                        extended_patterns.extend([
                            f"**/{comp_match}_partial*.json",
                            f"**/test_{comp_match}*.json",
                            f"**/{comp_match.lower()}*.json"
                        ])

                if extended_patterns:
                    schema_entry["fileMatch"].extend(extended_patterns)

    def _add_metaschema_configs(self) -> None:
        """Добавление конфигурации метасхемы"""
        print("  📋 Добавляю метасхемы...")

        metaschema_path = self.sdui_path.parent / "metaschema" / "schema" / "strict_unversioned.json"

        if metaschema_path.exists():
            # Конфигурация для контрактов
            self.schemas.append({
                "fileMatch": [
                    "**/SDUI/**/*contract*.json",
                    "**/SDUI/**/*Contract*.json"
                ],
                "url": f"file://{metaschema_path.absolute()}"
            })

            # Конфигурация для тестовых файлов
            self.schemas.append({
                "fileMatch": [
                    "**/SDUI/**/samples/*.json",
                    "**/SDUI/**/test*.json",
                    "**/SDUI/**/tests/*.json"
                ],
                "url": f"file://{metaschema_path.absolute()}"
            })

    def generate_config(self) -> Dict:
        """Генерация финальной конфигурации"""
        print(f"\n✨ Сгенерировано {len(self.schemas)} конфигураций схем")

        # Сортируем для стабильности
        self.schemas.sort(key=lambda x: x["url"])

        # Удаляем дубликаты
        unique_schemas = []
        seen_urls = set()

        for schema in self.schemas:
            url = schema["url"]
            if url not in seen_urls:
                seen_urls.add(url)
                unique_schemas.append(schema)

        print(f"📦 После дедупликации: {len(unique_schemas)} схем")

        return {
            "json.schemas": unique_schemas
        }

    def save_config(self, output_path: Path) -> None:
        """Сохранение конфигурации в файл"""
        config = self.generate_config()

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Конфигурация сохранена в: {output_path}")

    def print_statistics(self) -> None:
        """Вывод статистики"""
        print("\n📊 Статистика глубокой валидации:")
        print(f"  - Всего схем: {len(self.schemas)}")
        print(f"  - Атомарных типов: {len(self.atomic_types)}")
        print(f"  - Схем с зависимостями: {len(self.schema_dependencies)}")

        # Топ-5 схем по количеству зависимостей
        if self.schema_dependencies:
            sorted_deps = sorted(
                self.schema_dependencies.items(),
                key=lambda x: len(x[1]),
                reverse=True
            )[:5]

            print("\n  📈 Топ-5 схем по зависимостям:")
            for schema, deps in sorted_deps:
                print(f"    - {schema.name}: {len(deps)} зависимостей")


def main():
    parser = argparse.ArgumentParser(
        description="Генератор конфигурации VS Code для ГЛУБОКОЙ валидации SDUI схем"
    )
    parser.add_argument(
        "sdui_path",
        help="Путь к SDUI директории"
    )
    parser.add_argument(
        "-o", "--output",
        default="vscode_deep_schemas_config.json",
        help="Выходной файл конфигурации (по умолчанию: vscode_deep_schemas_config.json)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Подробный вывод"
    )

    args = parser.parse_args()

    sdui_path = Path(args.sdui_path).resolve()
    if not sdui_path.exists():
        print(f"❌ Путь не существует: {sdui_path}")
        sys.exit(1)

    if not sdui_path.is_dir():
        print(f"❌ Путь не является директорией: {sdui_path}")
        sys.exit(1)

    print(f"🚀 Генерация конфигурации для глубокой валидации SDUI схем")
    print(f"📁 SDUI путь: {sdui_path}")

    generator = SDUIDeepSchemaGenerator(sdui_path)
    generator.scan_directory()

    output_path = Path(args.output)
    generator.save_config(output_path)
    generator.print_statistics()

    print("\n✅ Готово! Для применения конфигурации:")
    print(f"1. Откройте VS Code settings.json")
    print(f"2. Найдите или создайте секцию 'json.schemas'")
    print(f"3. Замените её содержимым из {output_path}")
    print("\n💡 Подсказка: Перезагрузите VS Code после применения конфигурации")


if __name__ == "__main__":
    main()