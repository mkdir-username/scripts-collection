#!/usr/bin/env python3
"""
SDUI Web Platform Validator with JSONPath-based Line Detection
Использует JSONPath для точного определения позиций элементов в JSON файле
"""

import json
import sys
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from jsonpath_ng import parse as jsonpath_parse
from jsonpath_ng.ext import parse as jsonpath_ext_parse

class JSONPathLineMapper:
    """Класс для точного определения номеров строк используя JSONPath"""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.content_lines = []
        self.json_data = None
        self.json_text = ""
        self._load_file()

    def _load_file(self):
        """Загружает JSON файл и сохраняет как данные, так и текст"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.json_text = f.read()
                self.content_lines = self.json_text.splitlines()

            self.json_data = json.loads(self.json_text)
        except Exception as e:
            print(f"Error loading file: {e}")
            self.json_data = None

    def find_line_for_path(self, json_path: str) -> int:
        """
        Находит номер строки для заданного JSONPath
        Использует тот же подход, что и расширение JSON Path в VS Code
        """
        if not self.json_data:
            return 1

        try:
            # Преобразуем путь в JSONPath формат
            jsonpath_expr = self._convert_to_jsonpath(json_path)

            # Используем jsonpath_ng для поиска элемента
            parser = jsonpath_ext_parse(jsonpath_expr)
            matches = parser.find(self.json_data)

            if matches:
                # Получаем первое совпадение
                match = matches[0]

                # Теперь нужно найти этот объект в тексте
                # Используем путь и значение для точного поиска
                return self._find_object_in_text(match.full_path, match.value)
            else:
                # Если JSONPath не нашел, пробуем альтернативный метод
                return self._find_by_path_traversal(json_path)

        except Exception as e:
            print(f"JSONPath error for {json_path}: {e}")
            return self._find_by_path_traversal(json_path)

    def _convert_to_jsonpath(self, dot_path: str) -> str:
        """
        Конвертирует dot notation путь в JSONPath
        Примеры:
        data.alfaOnlyBanner.content -> $.data.alfaOnlyBanner.content
        data.children[0].content -> $.data.children[0].content
        """
        # Добавляем $ в начало если его нет
        if not dot_path.startswith('$'):
            jsonpath = '$.' + dot_path
        else:
            jsonpath = dot_path

        # JSONPath использует тот же синтаксис для массивов
        return jsonpath

    def _find_object_in_text(self, path, value) -> int:
        """
        Находит объект в тексте JSON файла
        Использует комбинацию пути и значения для точного поиска
        """
        # Получаем уникальные идентификаторы объекта
        if isinstance(value, dict):
            # Для объектов ищем уникальные ключи
            unique_keys = self._get_unique_keys(value)
            if unique_keys:
                return self._search_by_unique_keys(unique_keys, path)
        elif isinstance(value, list):
            # Для массивов ищем начало массива
            return self._search_array_start(path)

        # Fallback на поиск по пути
        return self._find_by_path_traversal(str(path))

    def _get_unique_keys(self, obj: dict) -> List[Tuple[str, Any]]:
        """Получает уникальные ключи и их значения из объекта"""
        unique_keys = []

        # Приоритетные ключи для поиска
        priority_keys = ['type', 'id', 'name', 'key', 'version']

        for key in priority_keys:
            if key in obj:
                unique_keys.append((key, obj[key]))

        # Добавляем другие ключи если нужно
        if len(unique_keys) < 2:
            for key, value in obj.items():
                if key not in priority_keys and not isinstance(value, (dict, list)):
                    unique_keys.append((key, value))
                    if len(unique_keys) >= 3:
                        break

        return unique_keys

    def _search_by_unique_keys(self, unique_keys: List[Tuple[str, Any]], path) -> int:
        """
        Ищет объект по уникальным ключам и контексту пути
        """
        if not unique_keys:
            return 1

        # Извлекаем родительские ключи из пути для контекста
        path_str = str(path)
        parent_keys = []

        # Парсим путь для получения родительских ключей
        if 'Fields' in path_str:
            # JSONPath формат
            parts = path_str.split('.')
            for part in parts:
                if 'Fields' in part:
                    # Извлекаем имя поля
                    field_name = part.split("'")[1] if "'" in part else None
                    if field_name and field_name not in ['children', 'content']:
                        parent_keys.append(field_name)
        else:
            # Простой путь
            parts = self._parse_path(path_str)
            parent_keys = [p for p in parts if isinstance(p, str) and p not in ['children', 'content']]

        # Ищем первый ключ
        first_key, first_value = unique_keys[0]

        # Формируем паттерн поиска
        if isinstance(first_value, str):
            pattern = rf'"{first_key}"\s*:\s*"{re.escape(first_value)}"'
        else:
            pattern = rf'"{first_key}"\s*:\s*{json.dumps(first_value)}'

        candidates = []

        for i, line in enumerate(self.content_lines, 1):
            if re.search(pattern, line):
                score = 0

                # Проверяем родительские ключи выше
                found_parents = set()
                for j in range(max(0, i - 100), i):
                    line_above = self.content_lines[j]
                    for parent_key in parent_keys:
                        if f'"{parent_key}"' in line_above and parent_key not in found_parents:
                            found_parents.add(parent_key)
                            # Чем ближе родитель, тем лучше
                            distance = i - j
                            score += 100 - distance

                # Штраф за отсутствующих родителей
                missing = len(parent_keys) - len(found_parents)
                score -= missing * 200

                # Проверяем остальные уникальные ключи
                context_range = 10
                for other_key, other_value in unique_keys[1:]:
                    found = False
                    for j in range(max(0, i - context_range), min(len(self.content_lines), i + context_range)):
                        if isinstance(other_value, str):
                            other_pattern = rf'"{other_key}"\s*:\s*"{re.escape(other_value)}"'
                        else:
                            other_pattern = rf'"{other_key}"\s*:\s*{json.dumps(other_value)}'

                        if re.search(other_pattern, self.content_lines[j]):
                            found = True
                            score += 10 - abs(i - j - 1)
                            break

                    if not found:
                        score -= 50

                candidates.append((i, score))

        if candidates:
            # Выбираем лучшего кандидата
            candidates.sort(key=lambda x: x[1], reverse=True)
            return candidates[0][0]

        return 1

    def _search_array_start(self, path) -> int:
        """Находит начало массива по пути"""
        path_str = str(path)
        # Извлекаем имя массива из пути
        parts = path_str.split('.')
        array_name = None

        for part in reversed(parts):
            if '[' in part:
                array_name = part.split('[')[0]
                break

        if array_name:
            pattern = rf'"{array_name}"\s*:\s*\['
            for i, line in enumerate(self.content_lines, 1):
                if re.search(pattern, line):
                    return i

        return 1

    def _find_by_path_traversal(self, json_path: str) -> int:
        """
        Fallback метод: обход JSON структуры для поиска элемента
        """
        if not self.json_data:
            return 1

        try:
            # Разбираем путь
            path_parts = self._parse_path(json_path)
            current = self.json_data

            # Навигируем к нужному элементу
            for part in path_parts:
                if isinstance(part, int):
                    if isinstance(current, list) and 0 <= part < len(current):
                        current = current[part]
                    else:
                        return 1
                else:
                    if isinstance(current, dict) and part in current:
                        current = current[part]
                    else:
                        return 1

            # Теперь ищем этот элемент в тексте
            if isinstance(current, dict) and 'type' in current:
                # Ищем по типу компонента
                pattern = rf'"type"\s*:\s*"{current["type"]}"'
                for i, line in enumerate(self.content_lines, 1):
                    if re.search(pattern, line):
                        return i

        except:
            pass

        return 1

    def _parse_path(self, path: str) -> list:
        """Разбирает путь на компоненты"""
        # Удаляем $ если есть
        if path.startswith('$.'):
            path = path[2:]
        elif path.startswith('$'):
            path = path[1:]

        parts = []
        current = ''
        i = 0

        while i < len(path):
            if path[i] == '[':
                if current:
                    parts.append(current)
                    current = ''
                # Извлекаем индекс
                j = i + 1
                while j < len(path) and path[j] != ']':
                    j += 1
                if j < len(path):
                    parts.append(int(path[i+1:j]))
                    i = j
            elif path[i] == '.':
                if current:
                    parts.append(current)
                    current = ''
            else:
                current += path[i]
            i += 1

        if current:
            parts.append(current)

        return parts


class SDUIWebValidator:
    def __init__(self):
        # Ищем путь к схемам
        possible_paths = [
            Path('/Users/username/Documents/FMS_GIT'),
            Path.home() / 'Documents' / 'front-middle-schema',
            Path(__file__).parent.parent.parent.parent / 'Documents' / 'front-middle-schema',
        ]

        self.base_path = None
        for path in possible_paths:
            if path.exists() and (path / 'SDUI').exists():
                self.base_path = path
                break

        if not self.base_path:
            self.base_path = Path(__file__).parent

        self.component_schemas = {}
        self.incompatible_components = []
        self.warnings = []
        self.errors = []
        self.line_mapper = None
        self.contract_path = None
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
            f"SDUI/components/{component_type}/v1/{component_type}.json",
            f"SDUI/layouts/{component_type}/v1/{component_type}.json",
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
            line_num = self.line_mapper.find_line_for_path(path) if self.line_mapper else 1
            self.warnings.append({
                'message': f"Schema not found for component '{component_type}'",
                'path': path,
                'line': line_num
            })
            return True

        schema = self.load_schema(schema_path)

        # Проверяем releaseVersion
        if 'releaseVersion' in schema:
            web_release = schema['releaseVersion'].get('web', 'released')
            if web_release in ['notReleased', 'willNotBeReleased']:
                line_num = self.line_mapper.find_line_for_path(path) if self.line_mapper else 1

                self.errors.append({
                    'component': component_type,
                    'reason': f"web: {web_release}",
                    'path': path,
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
                if component_type.endswith('View') or component_type.endswith('Wrapper'):
                    if not self.check_web_support(component_type, obj, path):
                        all_valid = False
                        line_num = self.line_mapper.find_line_for_path(path) if self.line_mapper else 1

                        self.incompatible_components.append({
                            'type': component_type,
                            'path': path,
                            'line': line_num,
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
        self.incompatible_components = []
        self.warnings = []
        self.errors = []
        self.contract_path = contract_path

        # Используем JSONPath mapper
        self.line_mapper = JSONPathLineMapper(contract_path)

        try:
            with open(contract_path, 'r', encoding='utf-8') as f:
                contract = json.load(f)
        except Exception as e:
            print(f"❌ Failed to load contract: {e}")
            return False

        # Проверяем все компоненты
        is_valid = self.check_component_recursively(contract)

        # Форматированный вывод
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"\n{'═'*80}")
        print(f"📋 ВАЛИДАЦИЯ СОВМЕСТИМОСТИ С WEB (JSONPath) | {timestamp}")
        print(f"{'═'*80}")

        # Группируем ошибки по типам компонентов
        if self.errors:
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
                    'line': error['line']
                })

            # Выводим сгруппированные ошибки
            for comp_type, data in component_errors.items():
                print(f"\n❌ {comp_type} — не поддерживается ({data['reason']})")
                print(f"   Найдено: {len(data['occurrences'])} вхождений")

                for occurrence in data['occurrences']:
                    print(f"\n   📍 Расположение компонента:")
                    print(f"      Путь: {occurrence['path']}")
                    print(f"      → {contract_path}:{occurrence['line']}:1")

        # Выводим предупреждения
        if self.warnings:
            print(f"\n⚠️  Предупреждения ({len(self.warnings)}):")
            for warning in self.warnings[:3]:
                print(f"   • {warning['message']}")
                print(f"     {contract_path}:{warning['line']}:1")
            if len(self.warnings) > 3:
                print(f"   ... и ещё {len(self.warnings) - 3}")

        # Итоговый статус
        print(f"\n{'─'*80}")
        if is_valid and not self.errors:
            print(f"ИТОГ: ✅ Контракт совместим с веб-платформой")
        else:
            print(f"ИТОГ: ❌ Контракт несовместим (всего ошибок: {len(self.errors)})")

        print(f"{'═'*80}\n")

        return is_valid and not self.errors


def main():
    if len(sys.argv) < 2:
        print("Usage: python sdui_web_validator_jsonpath.py <contract.json>")
        sys.exit(1)

    contract_path = sys.argv[1]

    if not os.path.exists(contract_path):
        print(f"Error: File not found: {contract_path}")
        sys.exit(1)

    # Пропускаем не-JSON файлы
    if not contract_path.endswith('.json'):
        sys.exit(0)

    validator = SDUIWebValidator()
    is_valid = validator.validate_contract(contract_path)

    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()