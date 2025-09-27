#!/usr/bin/env python3
"""
SDUI Web Platform Validator
Проверяет JSON-контракты на совместимость с веб-платформой
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Optional

class SDUIWebValidator:
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.component_schemas = {}
        self.layout_schemas = {}
        self.incompatible_components = []
        self.warnings = []
        self.errors = []

        # Кэш загруженных схем
        self.schema_cache = {}

    def load_schema(self, schema_path: Path) -> Dict:
        """Загружает схему компонента из файла"""
        if schema_path in self.schema_cache:
            return self.schema_cache[schema_path]

        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = json.load(f)
                self.schema_cache[schema_path] = schema
                return schema
        except Exception as e:
            print(f"Warning: Cannot load schema {schema_path}: {e}")
            return {}

    def find_component_schema(self, component_type: str) -> Optional[Path]:
        """Находит схему для компонента по его типу"""
        # Ищем в компонентах и layouts, включая специальную папку Constraint
        patterns = [
            f"SDUI/components/{component_type}/v*/{component_type}.json",
            f"SDUI/layouts/{component_type}/v*/{component_type}.json",
            f"SDUI/layouts/Constraint/v*/{component_type}.json",  # Для ConstraintWrapper
            f"SDUI/components/{component_type}/v1/{component_type}.json",
            f"SDUI/layouts/{component_type}/v1/{component_type}.json",
            f"SDUI/layouts/Constraint/v1/{component_type}.json",  # Для ConstraintWrapper v1
        ]

        for pattern in patterns:
            matches = list(self.base_path.glob(pattern))
            if matches:
                # Берем последнюю версию (сортировка по версии)
                return sorted(matches)[-1]

        return None

    def check_web_support(self, component_type: str, component_data: Dict, path: str) -> bool:
        """Проверяет поддержку компонента на веб-платформе"""
        schema_path = self.find_component_schema(component_type)

        if not schema_path:
            self.warnings.append({
                'message': f"Schema not found for component '{component_type}'",
                'path': path
            })
            return True  # Предполагаем поддержку если схема не найдена

        schema = self.load_schema(schema_path)

        # Проверяем основной releaseVersion компонента
        if 'releaseVersion' in schema:
            web_release = schema['releaseVersion'].get('web', 'released')
            if web_release in ['notReleased', 'willNotBeReleased']:
                self.errors.append({
                    'component': component_type,
                    'reason': f"web: {web_release}",
                    'path': path
                })
                return False

        # Проверяем поля компонента
        if 'properties' in schema:
            for field_name, field_value in component_data.items():
                if field_name in ['type', 'version', 'paddings', 'size', 'weight', 'hidden', 'tag']:
                    continue  # Пропускаем системные поля

                if field_name in schema['properties']:
                    field_schema = schema['properties'][field_name]

                    # Проверяем releaseVersion для конкретного поля
                    if 'releaseVersion' in field_schema:
                        field_web_release = field_schema['releaseVersion'].get('web', 'released')
                        if field_web_release in ['notReleased', 'willNotBeReleased']:
                            self.errors.append({
                                'component': component_type,
                                'field': field_name,
                                'reason': f"web: {field_web_release}",
                                'path': f"{path}.{field_name}"
                            })
                            return False

        return True

    def check_component_recursively(self, obj: Any, path: str = "") -> bool:
        """Рекурсивно проверяет все компоненты в контракте"""
        all_valid = True

        if isinstance(obj, dict):
            # Проверяем если это компонент
            if 'type' in obj and isinstance(obj['type'], str):
                component_type = obj['type']
                # Проверяем только компоненты View/Wrapper
                if component_type.endswith('View') or component_type.endswith('Wrapper') or component_type == 'Spacer':
                    if not self.check_web_support(component_type, obj, path):
                        all_valid = False
                        self.incompatible_components.append({
                            'type': component_type,
                            'path': path,
                            'data': obj
                        })

            # Рекурсивно проверяем вложенные объекты
            for key, value in obj.items():
                new_path = f"{path}.{key}" if path else key
                if not self.check_component_recursively(value, new_path):
                    all_valid = False

        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                if not self.check_component_recursively(item, f"{path}[{i}]"):
                    all_valid = False

        return all_valid

    def validate_contract(self, contract_path: str) -> bool:
        """Валидирует контракт на совместимость с веб-платформой"""
        print(f"\n{'='*60}")
        print(f"🔍 Validating contract for web platform compatibility:")
        print(f"   {contract_path}")
        print(f"{'='*60}")

        # Очищаем предыдущие результаты
        self.incompatible_components = []
        self.warnings = []
        self.errors = []
        self.contract_path = contract_path

        try:
            with open(contract_path, 'r', encoding='utf-8') as f:
                contract = json.load(f)
        except Exception as e:
            print(f"❌ Failed to load contract: {e}")
            return False

        # Проверяем все компоненты в контракте
        is_valid = self.check_component_recursively(contract)

        # Выводим результаты
        print(f"\n📊 Validation Results:")
        print(f"{'─'*60}")

        if self.warnings:
            print(f"\n⚠️  Warnings ({len(self.warnings)}):")
            print(f"{'─'*60}\n")
            for i, warning in enumerate(self.warnings[:5], 1):  # Показываем первые 5
                if isinstance(warning, dict):
                    print(f"  Warning #{i}:")
                    print(f"  📍 Location: {contract_path}:1")
                    print(f"  📝 Path: {warning['path']}")
                    print(f"  ⚠️  {warning['message']}")
                    print()
                else:
                    print(f"  {warning}")
            if len(self.warnings) > 5:
                print(f"  ... and {len(self.warnings) - 5} more warnings\n")

        if self.errors:
            print(f"\n❌ Errors ({len(self.errors)}):")
            print(f"{'─'*60}\n")
            for i, error in enumerate(self.errors[:10], 1):  # Показываем первые 10
                if isinstance(error, dict):
                    print(f"  Error #{i}:")
                    print(f"  📍 Location: {contract_path}:1")
                    print(f"  📝 Path: {error['path']}")
                    print(f"  🚫 Component: '{error['component']}'")
                    if 'field' in error:
                        print(f"  📌 Field: '{error['field']}'")
                    print(f"  ❌ Reason: Not supported on web platform ({error['reason']})")
                    print(f"  {'─'*56}")
                else:
                    print(f"  {error}")
            if len(self.errors) > 10:
                print(f"\n  ... and {len(self.errors) - 10} more errors")

        if self.incompatible_components:
            print(f"\n🚫 Incompatible Components Summary:")
            print(f"{'─'*60}")
            component_types = {}
            for comp in self.incompatible_components:
                comp_type = comp['type']
                if comp_type not in component_types:
                    component_types[comp_type] = []
                component_types[comp_type].append(comp['path'])

            for comp_type, paths in component_types.items():
                print(f"\n  • {comp_type}: {len(paths)} occurrences")
                for j, path in enumerate(paths[:3], 1):  # Показываем первые 3 пути
                    print(f"    {j}. {contract_path}:1 → {path}")
                if len(paths) > 3:
                    print(f"    ... and {len(paths) - 3} more")

        # Итоговый статус
        print(f"\n{'='*60}")
        if is_valid and not self.errors:
            print("✅ Contract is compatible with web platform!")
            return True
        else:
            print("❌ Contract has compatibility issues with web platform!")
            print(f"   Total errors: {len(self.errors)}")
            print(f"   Total warnings: {len(self.warnings)}")
            return False


def main():
    if len(sys.argv) < 2:
        print("Usage: python sdui_web_validator.py <contract.json>")
        sys.exit(1)

    contract_path = sys.argv[1]

    if not os.path.exists(contract_path):
        print(f"Error: File not found: {contract_path}")
        sys.exit(1)

    # Быстрый выход для не-JSON файлов и схем
    if not contract_path.endswith('.json'):
        sys.exit(0)

    # Пропускаем схемы - проверяем только контракты
    if '/SDUI/' in contract_path and not '/.JSON/' in contract_path:
        # Это схема, а не контракт - пропускаем
        if not any(x in contract_path for x in ['/samples/', '/examples/', '/_test_']):
            sys.exit(0)

    validator = SDUIWebValidator()
    is_valid = validator.validate_contract(contract_path)

    # VSCode integration - выводим ошибки в формате для Problem Matcher
    if not is_valid and validator.errors:
        print("\n=== VSCode Problem Matcher Output ===")
        for error in validator.errors:
            if isinstance(error, dict):
                # Формат: file:line:column: error: message
                # Пытаемся определить примерную строку по пути
                line_hint = 1
                if 'path' in error:
                    # Грубая оценка - считаем уровни вложенности
                    depth = error['path'].count('.') + error['path'].count('[')
                    line_hint = max(1, depth * 10)  # Примерная строка

                error_msg = f"Component '{error['component']}' not supported on web ({error['reason']}) at {error['path']}"
                if 'field' in error:
                    error_msg = f"Field '{error['field']}' in '{error['component']}' not supported on web ({error['reason']}) at {error['path']}"

                print(f"{contract_path}:{line_hint}:1: error: ❌ {error_msg}")
            else:
                print(f"{contract_path}:1:1: error: {error}")

    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()