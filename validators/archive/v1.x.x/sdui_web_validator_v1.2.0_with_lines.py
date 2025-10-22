#!/usr/bin/env python3
"""
SDUI Web Platform Validator with Line Number Detection
Проверяет JSON-контракты на совместимость с веб-платформой и определяет номера строк ошибок
"""

import json
import sys
import os
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Optional

class JSONLineMapper:
    """Класс для определения номеров строк в JSON файле"""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.line_map = {}
        self._build_line_map()

    def _build_line_map(self):
        """Строит карту соответствия путей JSON к номерам строк"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')

                # Простой парсер для поиска ключей в JSON
                current_path = []
                bracket_stack = []

                for line_num, line in enumerate(lines, 1):
                    stripped = line.strip()

                    # Ищем ключи JSON
                    key_match = re.search(r'"([^"]+)"\s*:', stripped)
                    if key_match:
                        key = key_match.group(1)

                        # Определяем уровень вложенности по отступам
                        indent = len(line) - len(line.lstrip())

                        # Формируем путь
                        if current_path and indent > 0:
                            path = '.'.join(current_path) + '.' + key
                        else:
                            path = key

                        self.line_map[path] = line_num

                        # Обрабатываем массивы
                        if '[' in stripped:
                            bracket_stack.append((key, line_num))

                    # Отслеживаем закрытие массивов
                    if ']' in stripped and bracket_stack:
                        bracket_stack.pop()

        except Exception as e:
            print(f"Warning: Could not build line map: {e}")

    def get_line_number(self, json_path: str) -> int:
        """Возвращает номер строки для заданного пути в JSON"""
        # Пробуем найти точное совпадение
        if json_path in self.line_map:
            return self.line_map[json_path]

        # Пробуем найти частичное совпадение
        path_parts = json_path.split('.')
        for i in range(len(path_parts), 0, -1):
            partial_path = '.'.join(path_parts[:i])
            if partial_path in self.line_map:
                return self.line_map[partial_path]

        # Если не нашли, возвращаем оценку на основе глубины пути
        depth = json_path.count('.') + json_path.count('[')
        return max(1, depth * 5)  # Грубая оценка


class SDUIWebValidator:
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.component_schemas = {}
        self.layout_schemas = {}
        self.incompatible_components = []
        self.warnings = []
        self.errors = []
        self.line_mapper = None
        self.contract_path = None

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
        patterns = [
            f"SDUI/components/{component_type}/v*/{component_type}.json",
            f"SDUI/layouts/{component_type}/v*/{component_type}.json",
            f"SDUI/layouts/Constraint/v*/{component_type}.json",
            f"SDUI/components/{component_type}/v1/{component_type}.json",
            f"SDUI/layouts/{component_type}/v1/{component_type}.json",
            f"SDUI/layouts/Constraint/v1/{component_type}.json",
        ]

        for pattern in patterns:
            matches = list(self.base_path.glob(pattern))
            if matches:
                return sorted(matches)[-1]

        return None

    def check_web_support(self, component_type: str, component_data: Dict, path: str) -> bool:
        """Проверяет поддержку компонента на веб-платформе"""
        schema_path = self.find_component_schema(component_type)

        if not schema_path:
            line_num = self.line_mapper.get_line_number(path) if self.line_mapper else 1
            self.warnings.append({
                'message': f"Schema not found for component '{component_type}'",
                'path': path,
                'line': line_num
            })
            return True

        schema = self.load_schema(schema_path)

        # Проверяем основной releaseVersion компонента
        if 'releaseVersion' in schema:
            web_release = schema['releaseVersion'].get('web', 'released')
            if web_release in ['notReleased', 'willNotBeReleased']:
                line_num = self.line_mapper.get_line_number(path) if self.line_mapper else 1
                self.errors.append({
                    'component': component_type,
                    'reason': f"web: {web_release}",
                    'path': path,
                    'line': line_num
                })
                return False

        # Проверяем поля компонента
        if 'properties' in schema:
            for field_name, field_value in component_data.items():
                if field_name in ['type', 'version', 'paddings', 'size', 'weight', 'hidden', 'tag']:
                    continue

                if field_name in schema['properties']:
                    field_schema = schema['properties'][field_name]

                    if 'releaseVersion' in field_schema:
                        field_web_release = field_schema['releaseVersion'].get('web', 'released')
                        if field_web_release in ['notReleased', 'willNotBeReleased']:
                            field_path = f"{path}.{field_name}"
                            line_num = self.line_mapper.get_line_number(field_path) if self.line_mapper else 1
                            self.errors.append({
                                'component': component_type,
                                'field': field_name,
                                'reason': f"web: {field_web_release}",
                                'path': field_path,
                                'line': line_num
                            })
                            return False

        return True

    def check_component_recursively(self, obj: Any, path: str = "") -> bool:
        """Рекурсивно проверяет все компоненты в контракте"""
        all_valid = True

        if isinstance(obj, dict):
            if 'type' in obj and isinstance(obj['type'], str):
                component_type = obj['type']
                if component_type.endswith('View') or component_type.endswith('Wrapper') or component_type == 'Spacer':
                    if not self.check_web_support(component_type, obj, path):
                        all_valid = False
                        self.incompatible_components.append({
                            'type': component_type,
                            'path': path,
                            'line': self.line_mapper.get_line_number(path) if self.line_mapper else 1,
                            'data': obj
                        })

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
        # Инициализация
        self.incompatible_components = []
        self.warnings = []
        self.errors = []
        self.contract_path = contract_path
        self.line_mapper = JSONLineMapper(contract_path)

        try:
            with open(contract_path, 'r', encoding='utf-8') as f:
                contract = json.load(f)
        except Exception as e:
            print(f"❌ Failed to load contract: {e}")
            return False

        # Проверяем все компоненты в контракте
        is_valid = self.check_component_recursively(contract)

        # Форматированный вывод
        print(f"\n{'═'*60}")
        print(f"📋 ВАЛИДАЦИЯ СОВМЕСТИМОСТИ С WEB")
        print(f"{'═'*60}")

        # Группируем ошибки по типам компонентов
        if self.errors or self.incompatible_components:
            component_errors = {}

            for error in self.errors:
                comp_type = error['component']
                if comp_type not in component_errors:
                    component_errors[comp_type] = {
                        'reason': error['reason'],
                        'occurrences': []
                    }
                component_errors[comp_type]['occurrences'].append({
                    'path': error['path'],
                    'line': error['line'],
                    'field': error.get('field')
                })

            # Выводим сгруппированные ошибки
            for comp_type, data in component_errors.items():
                print(f"\n❌ {comp_type} — не поддерживается ({data['reason']})")
                print(f"   Найдено: {len(data['occurrences'])} вхождений")

                for occurrence in data['occurrences']:
                    print(f"\n   📍 {contract_path}:{occurrence['line']}:1")
                    print(f"      └─ {occurrence['path']}")

        # Выводим предупреждения
        if self.warnings:
            print(f"\n⚠️  Предупреждения ({len(self.warnings)}):")
            for warning in self.warnings[:3]:
                print(f"   • {warning['message']}")
            if len(self.warnings) > 3:
                print(f"   ... и ещё {len(self.warnings) - 3}")

        # Итоговый статус
        print(f"\n{'─'*60}")
        if is_valid and not self.errors:
            print(f"ИТОГ: ✅ Контракт совместим")
        else:
            print(f"ИТОГ: ❌ Контракт несовместим (всего ошибок: {len(self.errors)})")

        print(f"{'═'*60}")

        return is_valid and not self.errors


def main():
    if len(sys.argv) < 2:
        print("Usage: python sdui_web_validator_with_lines.py <contract.json>")
        sys.exit(1)

    contract_path = sys.argv[1]

    if not os.path.exists(contract_path):
        print(f"Error: File not found: {contract_path}")
        sys.exit(1)

    # Быстрый выход для не-JSON файлов и схем
    if not contract_path.endswith('.json'):
        sys.exit(0)

    if '/SDUI/' in contract_path and not '/.JSON/' in contract_path:
        if not any(x in contract_path for x in ['/samples/', '/examples/', '/_test_']):
            sys.exit(0)

    validator = SDUIWebValidator()
    is_valid = validator.validate_contract(contract_path)

    # Убрал вывод VSCode Problem Matcher - он теперь не нужен

    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()