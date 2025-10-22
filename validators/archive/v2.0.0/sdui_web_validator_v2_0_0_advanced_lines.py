
# Добавлено автоматически для поддержки валидаторов после миграции
import sys
from pathlib import Path
validators_path = Path('/Users/username/Scripts/validators/current')
if validators_path not in sys.path:
    sys.path.insert(0, str(validators_path))

#!/usr/bin/env python3
"""
SDUI Web Platform Validator with Advanced Line Detection
Проверяет JSON-контракты на совместимость с веб-платформой и точно определяет номера строк
"""

import json
import sys
import os
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Optional

class AdvancedJSONLineMapper:
    """Продвинутый класс для точного определения номеров строк в JSON файле"""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.line_map = {}
        self.content_lines = []
        self.json_data = None
        self._load_json_data()
        self._build_advanced_line_map()

    def _load_json_data(self):
        """Загружает JSON данные для анализа структуры"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.json_data = json.load(f)
        except:
            self.json_data = None

    def _build_advanced_line_map(self):
        """Строит детальную карту соответствия путей JSON к номерам строк"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.content_lines = f.readlines()

            # Создаем полную карту с помощью рекурсивного обхода JSON и поиска в файле
            if self.json_data:
                self._map_json_recursive(self.json_data, '')

        except Exception as e:
            # Если не удалось создать карту рекурсивным способом, используем старый метод
            self._build_line_map_from_text()

    def _map_json_recursive(self, obj, path, parent_key=''):
        """Рекурсивно строит карту путей к номерам строк"""
        if isinstance(obj, dict):
            for key, value in obj.items():
                new_path = f"{path}.{key}" if path else key
                # Ищем строку с этим ключом
                line_num = self._find_key_line(key, path)
                if line_num:
                    self.line_map[new_path] = line_num
                self._map_json_recursive(value, new_path, key)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                new_path = f"{path}[{i}]"
                # Ищем начало элемента массива
                line_num = self._find_array_element_line(path, i, parent_key)
                if line_num:
                    self.line_map[new_path] = line_num
                self._map_json_recursive(item, new_path, parent_key)

    def _find_key_line(self, key, parent_path):
        """Находит строку с определенным ключом в контексте родительского пути"""
        search_pattern = rf'"{key}"\s*:'
        context_depth = parent_path.count('.') + parent_path.count('[')

        # Ищем с учетом вложенности
        for line_num, line in enumerate(self.content_lines, 1):
            if re.search(search_pattern, line):
                # Проверяем уровень вложенности по отступам
                indent = len(line) - len(line.lstrip())
                expected_indent = context_depth * 2  # Примерная оценка

                # Принимаем строку если отступ примерно соответствует
                if abs(indent - expected_indent) <= 4:
                    return line_num
        return None

    def _find_array_element_line(self, array_path, index, parent_key):
        """Находит строку начала элемента массива"""
        # Сначала находим строку с началом массива
        if parent_key:
            array_start_pattern = rf'"{parent_key}"\s*:\s*\['
            array_start_line = None

            for line_num, line in enumerate(self.content_lines, 1):
                if re.search(array_start_pattern, line):
                    array_start_line = line_num
                    break

            if array_start_line:
                # Теперь ищем нужный элемент массива
                element_count = 0
                in_array = False
                brace_depth = 0

                for line_num in range(array_start_line, len(self.content_lines) + 1):
                    if line_num > len(self.content_lines):
                        break

                    line = self.content_lines[line_num - 1]
                    stripped = line.strip()

                    if '[' in line and not in_array:
                        in_array = True
                        continue

                    if in_array:
                        # Считаем открывающие скобки для элементов
                        if stripped.startswith('{'):
                            if brace_depth == 0 and element_count == index:
                                return line_num
                            if brace_depth == 0:
                                element_count += 1
                            brace_depth += stripped.count('{') - stripped.count('}')
                        elif '{' in stripped:
                            brace_depth += stripped.count('{') - stripped.count('}')
                        elif '}' in stripped:
                            brace_depth -= stripped.count('}')

                        if ']' in stripped and brace_depth == 0:
                            break

        return None

    def _build_line_map_from_text(self):
        """Старый метод построения карты путей (fallback)"""
        stack = []  # Стек текущего пути
        in_array = []  # Стек для отслеживания массивов
        array_indices = {}  # Счетчики элементов массивов

        for line_num, line in enumerate(self.content_lines, 1):
            stripped = line.strip()

            # Пропускаем пустые строки и комментарии
            if not stripped or stripped.startswith('//'):
                continue

            # Ищем ключи JSON с учетом кавычек
            key_match = re.match(r'^"([^"]+)"\s*:\s*(.*)$', stripped)
            if key_match:
                key = key_match.group(1)
                value_part = key_match.group(2)

                # Определяем уровень вложенности по отступам
                indent = len(line) - len(line.lstrip())

                # Управляем стеком на основе отступов
                while stack and len(stack) > indent // 2:
                    popped = stack.pop()
                    if popped in array_indices:
                        del array_indices[popped]

                # Формируем текущий путь
                if in_array and in_array[-1]:
                    # Мы внутри массива
                    parent_path = '.'.join(stack) if stack else ''
                    array_key = in_array[-1]
                    if array_key not in array_indices:
                        array_indices[array_key] = 0
                    current_index = array_indices[array_key]

                    if parent_path:
                        full_path = f"{parent_path}[{current_index}].{key}"
                    else:
                        full_path = f"{array_key}[{current_index}].{key}"
                else:
                    # Обычный объект
                    if stack:
                        full_path = '.'.join(stack) + '.' + key
                    else:
                        full_path = key

                # Сохраняем номер строки для этого пути
                self.line_map[full_path] = line_num

                # Проверяем, начинается ли объект или массив
                if value_part.startswith('{'):
                    stack.append(key)
                    in_array.append(False)
                elif value_part.startswith('['):
                    stack.append(key)
                    in_array.append(key)
                    array_indices[key] = 0

            # Обрабатываем начало элемента массива
            elif stripped.startswith('{') and in_array and in_array[-1]:
                # Новый элемент в массиве
                array_key = in_array[-1]
                if array_key in array_indices:
                    # Записываем номер строки для элемента массива
                    parent_path = '.'.join(stack[:-1]) if len(stack) > 1 else ''
                    if parent_path:
                        full_path = f"{parent_path}.{array_key}[{array_indices[array_key]}]"
                    else:
                        full_path = f"{array_key}[{array_indices[array_key]}]"
                    self.line_map[full_path] = line_num

            # Отслеживаем закрытие объектов и массивов
            if '}' in stripped:
                if stack:
                    stack.pop()
                if in_array:
                    in_array.pop()

            if ']' in stripped:
                if in_array and in_array[-1]:
                    array_key = in_array[-1]
                    if array_key in array_indices:
                        array_indices[array_key] += 1
                if in_array:
                    in_array.pop()
                if stack:
                    stack.pop()

            # Обработка запятой между элементами массива
            if stripped == ',' and in_array and in_array[-1]:
                array_key = in_array[-1]
                if array_key in array_indices:
                    array_indices[array_key] += 1


    def get_exact_line_number(self, json_path: str) -> int:
        """Возвращает точный номер строки для заданного пути в JSON"""
        # Сначала пробуем новый улучшенный метод
        line_num = self._find_line_by_path_navigation(json_path)
        if line_num and line_num > 1:
            return line_num

        # Проверяем кэш
        if json_path in self.line_map:
            return self.line_map[json_path]

        # Попытаемся найти точную строку через навигацию по JSON структуре
        line_num = self._navigate_to_path(json_path)
        if line_num:
            self.line_map[json_path] = line_num  # Кэшируем результат
            return line_num

        # Если путь не найден, пробуем найти последний элемент пути прямым поиском
        if self.json_data:
            # Навигация по пути чтобы получить значение
            try:
                current = self.json_data
                path_parts = self._parse_json_path(json_path)

                for part in path_parts:
                    if isinstance(part, int):
                        if isinstance(current, list) and part < len(current):
                            current = current[part]
                        else:
                            break
                    else:
                        if isinstance(current, dict) and part in current:
                            current = current[part]
                        else:
                            break

                # Теперь ищем точную строку с этим элементом
                if path_parts:
                    last_part = path_parts[-1]
                    if isinstance(last_part, str):
                        # Это ключ объекта, ищем его
                        line_num = self._search_key_in_context(last_part, json_path)
                        if line_num:
                            return line_num
            except:
                pass

        # Пробуем различные варианты пути
        # Убираем индексы массивов для поиска
        simplified_path = re.sub(r'\[\d+\]', '[0]', json_path)
        if simplified_path in self.line_map:
            return self.line_map[simplified_path]

        # Ищем частичные совпадения
        path_parts = json_path.split('.')
        for i in range(len(path_parts), 0, -1):
            partial_path = '.'.join(path_parts[:i])
            if partial_path in self.line_map:
                return self.line_map[partial_path]

            # Пробуем с индексами массивов
            partial_with_array = re.sub(r'\[\d+\]', '[0]', partial_path)
            if partial_with_array in self.line_map:
                return self.line_map[partial_with_array]

        # Поиск по ключевым словам пути
        for stored_path, line_num in self.line_map.items():
            if json_path.endswith(stored_path) or stored_path.endswith(json_path.split('.')[-1]):
                return line_num

        # Если ничего не нашли, возвращаем оценку
        depth = json_path.count('.') + json_path.count('[')
        return max(1, depth * 10)

    def _parse_json_path(self, path: str) -> list:
        """Разбирает JSON путь на компоненты"""
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

    def _navigate_to_path(self, json_path: str) -> Optional[int]:
        """Навигирует к JSON пути и находит точную строку"""
        if not self.json_data:
            return None

        # Разбираем путь
        path_parts = self._parse_json_path(json_path)
        if not path_parts:
            return None

        # Навигируем к целевому элементу в JSON
        current_obj = self.json_data
        current_path = []

        try:
            for i, part in enumerate(path_parts):
                current_path.append(part)

                if isinstance(part, int):
                    # Это индекс массива
                    if isinstance(current_obj, list) and part < len(current_obj):
                        current_obj = current_obj[part]
                    else:
                        break
                else:
                    # Это ключ объекта
                    if isinstance(current_obj, dict) and part in current_obj:
                        current_obj = current_obj[part]
                    else:
                        break

            # Теперь ищем строку с этим элементом
            return self._find_object_line(current_path, json_path)

        except:
            return None

    def _find_object_line(self, path_parts: list, full_path: str) -> Optional[int]:
        """Находит строку объекта по пути"""
        # Строим шаблон для поиска
        if not path_parts:
            return None

        # Оцениваем глубину вложенности
        depth = 0
        for part in path_parts[:-1]:
            if isinstance(part, str):
                depth += 1

        # Последний элемент пути
        last_part = path_parts[-1]

        if isinstance(last_part, str):
            # Ищем ключ объекта с учетом глубины
            return self._find_key_with_depth(last_part, depth, full_path)
        elif isinstance(last_part, int):
            # Ищем элемент массива
            parent_key = path_parts[-2] if len(path_parts) > 1 and isinstance(path_parts[-2], str) else None
            if parent_key:
                return self._find_array_item(parent_key, last_part, depth)

        return None

    def _find_key_with_depth(self, key: str, expected_depth: int, full_path: str) -> Optional[int]:
        """Находит ключ на определенной глубине"""
        search_pattern = rf'"{key}"\s*:'
        candidates = []

        # Собираем все вхождения ключа
        for line_num, line in enumerate(self.content_lines, 1):
            if re.search(search_pattern, line):
                indent = len(line) - len(line.lstrip())
                # Ожидаемый отступ зависит от стиля форматирования (2 или 4 пробела)
                expected_indent_2 = expected_depth * 2
                expected_indent_4 = expected_depth * 4

                # Добавляем кандидата с расчетом близости к ожидаемому отступу
                distance = min(abs(indent - expected_indent_2), abs(indent - expected_indent_4))
                candidates.append((line_num, distance, indent))

        # Выбираем наиболее подходящего кандидата
        if candidates:
            # Сортируем по близости к ожидаемому отступу
            candidates.sort(key=lambda x: (x[1], x[0]))

            # Если есть несколько кандидатов с одинаковой близостью,
            # пытаемся выбрать по контексту
            if len(candidates) > 1 and candidates[0][1] == candidates[1][1]:
                # Используем дополнительные проверки контекста
                return self._choose_best_candidate(candidates, full_path)

            return candidates[0][0]

        return None

    def _find_array_item(self, parent_key: str, index: int, depth: int) -> Optional[int]:
        """Находит элемент массива по индексу"""
        # Сначала находим начало массива
        array_pattern = rf'"{parent_key}"\s*:\s*\['
        array_start = None

        for line_num, line in enumerate(self.content_lines, 1):
            if re.search(array_pattern, line):
                indent = len(line) - len(line.lstrip())
                expected_indent = depth * 2  # или depth * 4
                if abs(indent - expected_indent) <= 4:
                    array_start = line_num
                    break

        if not array_start:
            return None

        # Теперь ищем index-ый элемент
        element_count = 0
        brace_depth = 0
        in_array = False

        for line_num in range(array_start, len(self.content_lines) + 1):
            if line_num > len(self.content_lines):
                break

            line = self.content_lines[line_num - 1]
            stripped = line.strip()

            if '[' in line and not in_array:
                in_array = True
                if '{' in line:  # Массив начинается с объекта на той же строке
                    if element_count == index:
                        return line_num
                    element_count += 1
                continue

            if in_array:
                if stripped.startswith('{'):
                    if brace_depth == 0:
                        if element_count == index:
                            return line_num
                        element_count += 1
                    brace_depth += stripped.count('{') - stripped.count('}')
                elif '}' in stripped:
                    brace_depth -= stripped.count('}')
                elif '{' in stripped:
                    brace_depth += stripped.count('{') - stripped.count('}')

                if ']' in stripped and brace_depth <= 0:
                    break

        return None

    def _choose_best_candidate(self, candidates: list, full_path: str) -> int:
        """Выбирает лучшего кандидата из нескольких по контексту"""
        # Проверяем контекст вокруг каждого кандидата
        path_parts = self._parse_json_path(full_path)

        # Если в пути есть массивы, проверяем близость к массивам
        for candidate in candidates:
            line_num = candidate[0]
            # Проверяем, есть ли массив перед этой строкой
            for i in range(max(1, line_num - 10), line_num):
                if i <= len(self.content_lines):
                    line = self.content_lines[i - 1]
                    if '[' in line:
                        # Нашли массив, это хороший кандидат
                        return line_num

        # Если не нашли контекст, возвращаем первого кандидата
        return candidates[0][0]

    def _search_key_in_context(self, key: str, full_path: str) -> Optional[int]:
        """Ищет ключ в правильном контексте на основе полного пути"""
        # Оцениваем глубину вложенности
        depth = full_path.count('.') + full_path.count('[')

        # Ищем все вхождения ключа
        candidates = []
        search_pattern = rf'"{key}"\s*:'

        for line_num, line in enumerate(self.content_lines, 1):
            if re.search(search_pattern, line):
                indent = len(line) - len(line.lstrip())
                candidates.append((line_num, indent))

        # Выбираем наиболее подходящего кандидата по глубине
        if candidates:
            # Примерная оценка ожидаемого отступа
            expected_indent = depth * 2

            # Находим ближайшего кандидата по отступу
            best_candidate = min(candidates, key=lambda x: abs(x[1] - expected_indent))
            return best_candidate[0]

        return None

    def _find_line_by_path_navigation(self, json_path: str) -> Optional[int]:
        """Улучшенный метод поиска строки через навигацию по JSON структуре"""
        if not self.json_data or not self.content_lines:
            return None

        try:
            # Разбираем путь на части
            path_parts = self._parse_json_path(json_path)
            if not path_parts:
                return None

            # Навигируем по JSON чтобы найти целевой объект
            current = self.json_data
            parent_obj = None
            parent_key = None

            # Проходим по всем частям пути кроме последней
            for i, part in enumerate(path_parts[:-1]):
                parent_obj = current
                parent_key = part

                if isinstance(part, int):
                    if isinstance(current, list) and 0 <= part < len(current):
                        current = current[part]
                    else:
                        return None
                else:
                    if isinstance(current, dict) and part in current:
                        current = current[part]
                    else:
                        return None

            # Обрабатываем последнюю часть пути
            last_part = path_parts[-1]

            if isinstance(last_part, int):
                # Это элемент массива
                if isinstance(current, list) and 0 <= last_part < len(current):
                    # Находим строку для элемента массива
                    return self._find_array_element_exact(json_path, path_parts)
            else:
                # Это ключ объекта
                if isinstance(current, dict) and last_part in current:
                    # Находим строку для ключа
                    return self._find_key_exact(json_path, path_parts)

        except Exception as e:
            pass

        return None

    def _find_array_element_exact(self, full_path: str, path_parts: list) -> Optional[int]:
        """Точный поиск элемента массива в файле"""
        # Находим родительский ключ массива
        array_key = None
        for i in range(len(path_parts) - 1, -1, -1):
            if isinstance(path_parts[i], str):
                array_key = path_parts[i]
                break

        if not array_key:
            return None

        # Получаем индекс элемента
        element_index = path_parts[-1]
        if not isinstance(element_index, int):
            return None

        # Ищем массив в файле
        array_pattern = rf'"{array_key}"\s*:\s*\['
        array_line = None

        for line_num, line in enumerate(self.content_lines, 1):
            if re.search(array_pattern, line):
                array_line = line_num
                break

        if not array_line:
            return None

        # Считаем элементы массива
        element_count = 0
        brace_depth = 0
        in_array = False

        for line_num in range(array_line, len(self.content_lines) + 1):
            if line_num > len(self.content_lines):
                break

            line = self.content_lines[line_num - 1]

            # Проверяем начало массива
            if '[' in line and not in_array:
                in_array = True
                # Проверяем есть ли элемент на той же строке
                if '{' in line:
                    if element_count == element_index:
                        return line_num
                    element_count += 1
                continue

            if in_array:
                stripped = line.strip()

                # Считаем открывающие фигурные скобки как начало элементов
                if stripped.startswith('{'):
                    if brace_depth == 0:
                        if element_count == element_index:
                            return line_num
                        element_count += 1
                    brace_depth += stripped.count('{') - stripped.count('}')
                elif '{' in stripped:
                    brace_depth += stripped.count('{') - stripped.count('}')
                elif '}' in stripped:
                    brace_depth -= stripped.count('}')

                # Проверяем конец массива
                if ']' in stripped and brace_depth <= 0:
                    break

        return None

    def _find_key_exact(self, full_path: str, path_parts: list) -> Optional[int]:
        """Точный поиск ключа объекта в файле"""
        key = path_parts[-1]
        if not isinstance(key, str):
            return None

        # Формируем паттерн поиска
        key_pattern = rf'"{key}"\s*:'

        # Оцениваем глубину вложенности
        depth = len([p for p in path_parts[:-1] if isinstance(p, str)])

        # Ищем все вхождения ключа
        candidates = []

        for line_num, line in enumerate(self.content_lines, 1):
            if re.search(key_pattern, line):
                indent = len(line) - len(line.lstrip())
                # Оцениваем соответствие глубине (2 или 4 пробела на уровень)
                score_2 = abs(indent - depth * 2)
                score_4 = abs(indent - depth * 4)
                score = min(score_2, score_4)

                # Проверяем контекст - ищем родительские ключи выше
                context_score = 0
                for i in range(max(1, line_num - 30), line_num):
                    check_line = self.content_lines[i - 1]
                    for j in range(len(path_parts) - 1):
                        if isinstance(path_parts[j], str):
                            if f'"{path_parts[j]}"' in check_line:
                                # Нашли родительский ключ - хороший признак
                                context_score += 10

                candidates.append((line_num, score - context_score))

        # Выбираем лучшего кандидата
        if candidates:
            candidates.sort(key=lambda x: x[1])
            return candidates[0][0]

        return None

    def search_in_file(self, search_term: str) -> int:
        """Ищет термин непосредственно в файле и возвращает номер строки"""
        for line_num, line in enumerate(self.content_lines, 1):
            if search_term in line:
                return line_num
        return 1


class SDUIWebValidator:
    def __init__(self):
        # Ищем путь к схемам в разных возможных местах
        possible_paths = [
            Path('/Users/username/Documents/FMS_GIT'),
            Path(__file__).parent.parent.parent.parent / 'Documents' / 'front-middle-schema',
            Path.home() / 'Documents' / 'front-middle-schema',
            Path(__file__).parent  # fallback
        ]

        self.base_path = None
        for path in possible_paths:
            if path.exists() and (path / 'SDUI').exists():
                self.base_path = path
                break

        if not self.base_path:
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
            line_num = self.line_mapper.get_exact_line_number(path) if self.line_mapper else 1
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
                line_num = self.line_mapper.get_exact_line_number(path) if self.line_mapper else 1

                # Попробуем найти точную строку где определен type компонента
                type_path = f"{path}.type"
                type_line = self.line_mapper.get_exact_line_number(type_path) if self.line_mapper else line_num

                self.errors.append({
                    'component': component_type,
                    'reason': f"web: {web_release}",
                    'path': path,
                    'line': line_num,
                    'type_line': type_line  # Строка где определен тип компонента
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
                            line_num = self.line_mapper.get_exact_line_number(field_path) if self.line_mapper else 1
                            self.errors.append({
                                'component': component_type,
                                'field': field_name,
                                'reason': f"web: {field_web_release}",
                                'path': field_path,
                                'line': line_num,
                                'type_line': line_num
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
                        line_num = self.line_mapper.get_exact_line_number(path) if self.line_mapper else 1
                        type_line = self.line_mapper.get_exact_line_number(f"{path}.type") if self.line_mapper else line_num

                        self.incompatible_components.append({
                            'type': component_type,
                            'path': path,
                            'line': line_num,
                            'type_line': type_line,
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
        # К сожалению, VS Code Output Panel не поддерживает программную очистку
        # Расширение RunOnSave должно само очищать Output перед запуском
        # или можно использовать настройку "runOnSave.clearOutputOnRun": true в settings.json

        # Инициализация
        self.incompatible_components = []
        self.warnings = []
        self.errors = []
        self.contract_path = contract_path
        self.line_mapper = AdvancedJSONLineMapper(contract_path)

        try:
            with open(contract_path, 'r', encoding='utf-8') as f:
                contract = json.load(f)
        except Exception as e:
            print(f"❌ Failed to load contract: {e}")
            return False

        # Проверяем все компоненты в контракте
        is_valid = self.check_component_recursively(contract)

        # Форматированный вывод с временной меткой
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"\n{'═'*80}")
        print(f"📋 ВАЛИДАЦИЯ СОВМЕСТИМОСТИ С WEB | {timestamp}")
        print(f"{'═'*80}")

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
                    'type_line': error.get('type_line', error['line']),
                    'field': error.get('field')
                })

            # Выводим сгруппированные ошибки
            for comp_type, data in component_errors.items():
                print(f"\n❌ {comp_type} — не поддерживается ({data['reason']})")
                print(f"   Найдено: {len(data['occurrences'])} вхождений")

                for occurrence in data['occurrences']:
                    # Получаем точный номер строки для пути
                    exact_line = self.line_mapper.get_exact_line_number(occurrence['path'])

                    # Если не нашли точную строку, используем оригинальную
                    if exact_line == occurrence['line'] or exact_line <= 1:
                        exact_line = occurrence.get('type_line', occurrence['line'])

                    print(f"\n   📍 Расположение компонента:")
                    print(f"      Путь: {occurrence['path']}")
                    print(f"      → {contract_path}:{exact_line}:1")

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

        print(f"{'═'*80}")

        # Визуальный разделитель конца лога
        print("\n")
        print("▓" * 80)
        print("█" * 80)
        print("█" * 34 + " END OF LOG " + "█" * 34)
        print("█" * 80)
        print("▓" * 80)
        print("░" * 80)
        print("\n" * 5)  # Дополнительные пустые строки для визуального разделения

        return is_valid and not self.errors


def main():
    if len(sys.argv) < 2:
        print("Usage: python sdui_web_validator_advanced.py <contract.json>")
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

    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()