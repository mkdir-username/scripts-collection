#!/usr/bin/env python3
"""
SDUI Web Platform Validator v3.0.0 Optimized
Оптимизированная версия с кэшированием, параллелизмом и профилированием
"""

import json
import sys
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from functools import lru_cache
import time

# Импорт конфигурации производительности
try:
    from performance_config_v3_0_0 import get_config, profile_performance, memoize_with_ttl
    PERFORMANCE_CONFIG_AVAILABLE = True
except ImportError:
    PERFORMANCE_CONFIG_AVAILABLE = False
    def profile_performance(threshold_ms=100):
        def decorator(func):
            return func
        return decorator


class OptimizedLineMapper:
    """
    Оптимизированный поиск строк с кэшированием и индексацией

    Оптимизации:
    1. Кэширование скомпилированных регулярных выражений
    2. Индекс строк для быстрого поиска
    3. Ленивая загрузка данных
    """

    # Кэш скомпилированных регексов (class-level для переиспользования)
    _regex_cache = {}

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.lines = []
        self.json_data = None
        self._line_index = None  # Индекс для быстрого поиска
        self._loaded = False

    def _ensure_loaded(self):
        """Ленивая загрузка файла"""
        if not self._loaded:
            self._load_file()
            self._loaded = True

    @profile_performance(threshold_ms=50)
    def _load_file(self):
        """Загружаем файл и JSON"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.lines = content.split('\n')
                self.json_data = json.loads(content)
        except Exception as e:
            print(f"Error loading file: {e}")

    def _get_compiled_regex(self, pattern: str) -> re.Pattern:
        """Получает скомпилированное регулярное выражение из кэша"""
        if pattern not in self._regex_cache:
            self._regex_cache[pattern] = re.compile(pattern)
        return self._regex_cache[pattern]

    def _build_line_index(self):
        """Строит индекс строк для быстрого поиска"""
        if self._line_index is not None:
            return

        self._ensure_loaded()
        self._line_index = defaultdict(list)

        # Индексируем строки по ключевым словам
        for i, line in enumerate(self.lines, 1):
            # Индексируем по типу компонента
            if '"type"' in line:
                type_match = re.search(r'"type"\s*:\s*"([^"]+)"', line)
                if type_match:
                    comp_type = type_match.group(1)
                    self._line_index[f'type:{comp_type}'].append(i)

    @profile_performance(threshold_ms=20)
    def find_component_lines(self, component_type: str) -> List[Tuple[str, int]]:
        """
        Находит все вхождения компонента с использованием индекса
        """
        self._ensure_loaded()

        # Используем индекс если доступен
        if PERFORMANCE_CONFIG_AVAILABLE and get_config().use_line_index:
            self._build_line_index()
            component_lines = self._line_index.get(f'type:{component_type}', [])
        else:
            # Fallback на обычный поиск
            pattern = self._get_compiled_regex(rf'"type"\s*:\s*"{component_type}"')
            component_lines = []
            for i, line in enumerate(self.lines, 1):
                if pattern.search(line):
                    component_lines.append(i)

        # Определяем пути для каждой найденной строки
        results = []
        for line_num in component_lines:
            path = self._find_path_for_line(line_num, component_type)
            results.append((path, line_num))

        return results

    def _find_path_for_line(self, line_num: int, component_type: str) -> str:
        """Определяет JSON путь для компонента на данной строке"""
        path_parts = []
        current_indent = len(self.lines[line_num - 1]) - len(self.lines[line_num - 1].lstrip())

        # Идем вверх по файлу, собирая родительские ключи
        for i in range(line_num - 1, 0, -1):
            line = self.lines[i - 1]
            indent = len(line) - len(line.lstrip())

            if indent < current_indent:
                key_match = re.search(r'"([^"]+)"\s*:', line)
                if key_match:
                    key = key_match.group(1)

                    if '[' in line:
                        array_index = self._find_array_index(i, line_num)
                        path_parts.insert(0, f"{key}[{array_index}]")
                    else:
                        path_parts.insert(0, key)

                    current_indent = indent

                    if indent == 0:
                        break

        return '.'.join(path_parts) if path_parts else f"line_{line_num}"

    def _find_array_index(self, array_start_line: int, target_line: int) -> int:
        """Определяет индекс элемента в массиве"""
        index = 0
        brace_depth = 0
        in_array = False

        for i in range(array_start_line, target_line):
            line = self.lines[i - 1]

            if '[' in line and not in_array:
                in_array = True
                if '{' in line:
                    if i >= target_line - 10:
                        return index
                    index += 1
                continue

            if in_array:
                stripped = line.strip()
                if stripped.startswith('{'):
                    if brace_depth == 0:
                        if i >= target_line - 10:
                            return index
                        index += 1
                    brace_depth += stripped.count('{') - stripped.count('}')
                elif '{' in stripped:
                    brace_depth += stripped.count('{') - stripped.count('}')
                elif '}' in stripped:
                    brace_depth -= stripped.count('}')

        return index


class OptimizedSDUIWebValidator:
    """
    Оптимизированный валидатор с кэшированием и профилированием

    Оптимизации:
    1. LRU кэш для схем компонентов
    2. Кэширование результатов проверки совместимости
    3. Индексация путей к схемам
    4. Профилирование производительности
    """

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

        # Кэш схем (с ограничением размера)
        self._schema_cache_size = 256 if PERFORMANCE_CONFIG_AVAILABLE else 128
        self.schema_cache = {}

        # Кэш результатов совместимости
        self._compatibility_cache = {}

        # Индекс путей к схемам (для быстрого поиска)
        self._schema_path_index = None

    def _build_schema_index(self):
        """Строит индекс всех доступных схем"""
        if self._schema_path_index is not None:
            return

        self._schema_path_index = {}

        # Индексируем все схемы компонентов
        for pattern in ['SDUI/components/*/v*/*.json', 'SDUI/layouts/*/v*/*.json']:
            for schema_path in self.base_path.glob(pattern):
                component_name = schema_path.stem
                if component_name not in self._schema_path_index:
                    self._schema_path_index[component_name] = []
                self._schema_path_index[component_name].append(schema_path)

    @lru_cache(maxsize=256)
    def load_schema(self, schema_path: Path) -> Dict:
        """Загружает схему компонента с LRU кэшированием"""
        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}

    @profile_performance(threshold_ms=10)
    def find_component_schema(self, component_type: str) -> Optional[Path]:
        """Находит схему для компонента с использованием индекса"""

        # Используем индекс если доступен
        if PERFORMANCE_CONFIG_AVAILABLE and get_config().use_line_index:
            self._build_schema_index()
            candidates = self._schema_path_index.get(component_type, [])
        else:
            # Fallback на glob поиск
            if component_type == "ConstraintWrapper":
                patterns = [
                    f"SDUI/layouts/Constraint/v*/{component_type}.json",
                    f"SDUI/layouts/Constraint/v1/{component_type}.json",
                ]
            else:
                patterns = [
                    f"SDUI/components/{component_type}/v*/{component_type}.json",
                    f"SDUI/layouts/{component_type}/v*/{component_type}.json",
                    f"SDUI/components/{component_type}/v1/{component_type}.json",
                    f"SDUI/layouts/{component_type}/v1/{component_type}.json",
                ]

            candidates = []
            for pattern in patterns:
                candidates.extend(self.base_path.glob(pattern))

        if not candidates:
            return None

        # Выбираем схему с поддержкой WEB
        web_supported = []
        for schema_path in sorted(candidates):
            schema = self.load_schema(schema_path)
            if schema and 'releaseVersion' in schema:
                web_status = schema['releaseVersion'].get('web', 'notReleased')
                if web_status == 'released':
                    web_supported.append(schema_path)

        return web_supported[0] if web_supported else sorted(candidates)[-1]

    def check_component_compatibility(self, component_type: str) -> Tuple[bool, str]:
        """Проверяет совместимость компонента с кэшированием"""

        # Проверяем кэш
        if component_type in self._compatibility_cache:
            return self._compatibility_cache[component_type]

        schema_path = self.find_component_schema(component_type)

        if not schema_path:
            result = (True, "Schema not found")
        else:
            schema = self.load_schema(schema_path)

            if 'releaseVersion' in schema:
                web_release = schema['releaseVersion'].get('web', 'released')
                if web_release in ['notReleased', 'willNotBeReleased']:
                    result = (False, f"web: {web_release}")
                else:
                    result = (True, "released")
            else:
                result = (True, "released")

        # Сохраняем в кэш
        self._compatibility_cache[component_type] = result
        return result

    @profile_performance(threshold_ms=100)
    def validate_contract(self, contract_path: str) -> bool:
        """Валидирует контракт на совместимость с веб-платформой"""
        start_time = time.perf_counter()

        line_mapper = OptimizedLineMapper(contract_path)
        line_mapper._ensure_loaded()

        # Собираем все типы компонентов
        component_types = set()
        pattern = re.compile(r'"type"\s*:\s*"([^"]+)"')

        for line in line_mapper.lines:
            match = pattern.search(line)
            if match:
                comp_type = match.group(1)
                if comp_type.endswith('View') or comp_type.endswith('Wrapper'):
                    component_types.add(comp_type)

        # Проверяем каждый тип компонента
        incompatible_components = defaultdict(list)

        for comp_type in component_types:
            is_compatible, reason = self.check_component_compatibility(comp_type)

            if not is_compatible:
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
        duration_ms = (time.perf_counter() - start_time) * 1000

        print("\n" * 3)
        print("╔" + "═" * 78 + "╗")
        print("║" + " " * 78 + "║")
        print(f"║  📋 ВАЛИДАЦИЯ (OPTIMIZED v3.0) | {timestamp} | {duration_ms:.2f}ms" + " " * 19 + "║")
        print("║" + " " * 78 + "║")
        print("╚" + "═" * 78 + "╝")

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

        print(f"\n{'─'*80}")
        if not incompatible_components:
            print(f"ИТОГ: ✅ Контракт совместим с веб-платформой")
        else:
            total_errors = sum(len(v) for v in incompatible_components.values())
            print(f"ИТОГ: ❌ Контракт несовместим (всего ошибок: {total_errors})")

        print(f"⏱️  Время валидации: {duration_ms:.2f}ms")
        print(f"{'═'*80}\n")

        print("▓" * 80)
        print("█" * 80)
        print("█" * 34 + " END OF LOG " + "█" * 34)
        print(f"{'█' * 35 + " "}{timestamp}{" " + '█' * 35}")
        print("▓" * 80)
        print("░" * 80)
        print("\n" * 5)

        return len(incompatible_components) == 0


def main():
    if len(sys.argv) < 2:
        print("Usage: python sdui_web_validator_v3.0.0_optimized.py <contract.json>")
        sys.exit(1)

    contract_path = sys.argv[1]

    if not os.path.exists(contract_path):
        print(f"Error: File not found: {contract_path}")
        sys.exit(1)

    if not contract_path.endswith('.json'):
        sys.exit(0)

    validator = OptimizedSDUIWebValidator()
    is_valid = validator.validate_contract(contract_path)

    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()
