#!/usr/bin/env python3
"""
SDUI Web Platform Validator v3.0.0 - Simple and Accurate
Простой и точный валидатор, который ищет компоненты прямо в тексте файла
"""

import json
import sys
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict

class SimpleLineMapper:
    """Простой и надежный поиск строк по JSON пути"""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.lines = []
        self.json_data = None
        self._load_file()

    def _load_file(self):
        """Загружаем файл и JSON"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.lines = content.split('\n')
                self.json_data = json.loads(content)
        except Exception as e:
            print(f"Error loading file: {e}")

    def find_component_lines(self, component_type: str) -> List[Tuple[str, int]]:
        """
        Находит все вхождения компонента и возвращает пути с номерами строк
        """
        results = []

        # Ищем все строки с указанным типом компонента
        pattern = rf'"type"\s*:\s*"{component_type}"'
        component_lines = []

        for i, line in enumerate(self.lines, 1):
            if re.search(pattern, line):
                component_lines.append(i)

        # Теперь для каждой найденной строки определяем путь
        for line_num in component_lines:
            path = self._find_path_for_line(line_num, component_type)
            results.append((path, line_num))

        return results

    def _find_path_for_line(self, line_num: int, component_type: str) -> str:
        """
        Определяет JSON путь для компонента на данной строке
        """
        # Ищем родительские ключи выше по файлу
        path_parts = []
        current_indent = len(self.lines[line_num - 1]) - len(self.lines[line_num - 1].lstrip())

        # Идем вверх по файлу, собирая родительские ключи
        for i in range(line_num - 1, 0, -1):
            line = self.lines[i - 1]
            indent = len(line) - len(line.lstrip())

            # Ищем ключи с меньшим отступом (родительские)
            if indent < current_indent:
                # Проверяем, является ли это ключом объекта
                key_match = re.search(r'"([^"]+)"\s*:', line)
                if key_match:
                    key = key_match.group(1)

                    # Проверяем, не является ли это началом массива
                    if '[' in line:
                        # Это массив, нужно определить индекс
                        array_index = self._find_array_index(i, line_num)
                        path_parts.insert(0, f"{key}[{array_index}]")
                    else:
                        path_parts.insert(0, key)

                    current_indent = indent

                    # Если дошли до корня, останавливаемся
                    if indent == 0:
                        break

        # Формируем полный путь
        return '.'.join(path_parts) if path_parts else f"line_{line_num}"

    def _find_array_index(self, array_start_line: int, target_line: int) -> int:
        """
        Определяет индекс элемента в массиве
        """
        index = 0
        brace_depth = 0
        in_array = False

        for i in range(array_start_line, target_line):
            line = self.lines[i - 1]

            # Начало массива
            if '[' in line and not in_array:
                in_array = True
                if '{' in line:
                    if i >= target_line - 10:  # Близко к целевой строке
                        return index
                    index += 1
                continue

            if in_array:
                # Считаем элементы массива по открывающим скобкам
                stripped = line.strip()
                if stripped.startswith('{'):
                    if brace_depth == 0:
                        if i >= target_line - 10:  # Близко к целевой строке
                            return index
                        index += 1
                    brace_depth += stripped.count('{') - stripped.count('}')
                elif '{' in stripped:
                    brace_depth += stripped.count('{') - stripped.count('}')
                elif '}' in stripped:
                    brace_depth -= stripped.count('}')

        return index


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

        self.schema_cache = {}

    def load_schema(self, schema_path: Path) -> Dict:
        """Загружает схему компонента"""
        if schema_path in self.schema_cache:
            return self.schema_cache[schema_path]

        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = json.load(f)
                self.schema_cache[schema_path] = schema
                return schema
        except Exception as e:
            return {}

    def find_component_schema(self, component_type: str) -> Optional[Path]:
        """Находит схему для компонента"""
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

    def check_component_compatibility(self, component_type: str) -> Tuple[bool, str]:
        """Проверяет совместимость компонента с веб-платформой"""
        schema_path = self.find_component_schema(component_type)

        if not schema_path:
            return True, "Schema not found"

        schema = self.load_schema(schema_path)

        if 'releaseVersion' in schema:
            web_release = schema['releaseVersion'].get('web', 'released')
            if web_release in ['notReleased', 'willNotBeReleased']:
                return False, f"web: {web_release}"

        return True, "released"

    def validate_contract(self, contract_path: str) -> bool:
        """Валидирует контракт на совместимость с веб-платформой"""
        line_mapper = SimpleLineMapper(contract_path)

        # Собираем все типы компонентов для проверки
        component_types = set()
        pattern = r'"type"\s*:\s*"([^"]+)"'

        for line in line_mapper.lines:
            match = re.search(pattern, line)
            if match:
                comp_type = match.group(1)
                if comp_type.endswith('View') or comp_type.endswith('Wrapper'):
                    component_types.add(comp_type)

        # Проверяем каждый тип компонента
        incompatible_components = defaultdict(list)

        for comp_type in component_types:
            is_compatible, reason = self.check_component_compatibility(comp_type)

            if not is_compatible:
                # Находим все вхождения этого компонента
                occurrences = line_mapper.find_component_lines(comp_type)

                for path, line_num in occurrences:
                    incompatible_components[comp_type].append({
                        'path': path,
                        'line': line_num,
                        'reason': reason
                    })

        # Вывод результатов
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")

        print(f"\n{'═'*80}")
        print(f"📋 ВАЛИДАЦИЯ СОВМЕСТИМОСТИ С WEB v3.0 | {timestamp}")
        print(f"{'═'*80}")

        if incompatible_components:
            for comp_type, occurrences in incompatible_components.items():
                if occurrences:
                    print(f"\n❌ {comp_type} — не поддерживается ({occurrences[0]['reason']})")
                    print(f"   Найдено: {len(occurrences)} вхождений")

                    for occurrence in occurrences:
                        print(f"\n   📍 Расположение компонента:")
                        print(f"      Путь: {occurrence['path']}")
                        print(f"      → {contract_path}:{occurrence['line']}:1")
        else:
            print("\n✅ Все компоненты совместимы с веб-платформой")

        # Итог
        print(f"\n{'─'*80}")
        if not incompatible_components:
            print(f"ИТОГ: ✅ Контракт совместим с веб-платформой")
        else:
            total_errors = sum(len(v) for v in incompatible_components.values())
            print(f"ИТОГ: ❌ Контракт несовместим (всего ошибок: {total_errors})")

        print(f"{'═'*80}\n")

        return len(incompatible_components) == 0


def main():
    if len(sys.argv) < 2:
        print("Usage: python sdui_web_validator.py <contract.json>")
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