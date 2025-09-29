#!/usr/bin/env python3
"""
SDUI Jinja2 Extensions
Кастомные расширения и фильтры для поддержки SDUI функций в Jinja2
"""

from datetime import datetime, timedelta
from typing import Any, List, Dict, Optional, Union
import json
import math
import re
from jinja2 import nodes
from jinja2.ext import Extension


class SDUIConditionalExtension(Extension):
    """Расширение для поддержки SDUI условных выражений"""

    tags = {'sdui_if'}

    def parse(self, parser):
        """Парсинг SDUI условных блоков"""
        lineno = next(parser.stream).lineno

        # Парсим условие
        condition = parser.parse_expression()

        # Парсим then блок
        parser.stream.expect('name:then')
        then_body = parser.parse_statements(['name:else', 'name:endsdui_if'], drop_needle=False)

        # Парсим else блок если есть
        else_body = []
        if parser.stream.current.test('name:else'):
            next(parser.stream)
            else_body = parser.parse_statements(['name:endsdui_if'], drop_needle=False)

        parser.stream.expect('name:endsdui_if')

        # Создаём условный узел
        return nodes.If(condition, then_body, [], else_body, lineno=lineno)


class SDUILoopExtension(Extension):
    """Расширение для поддержки SDUI циклов"""

    tags = {'sdui_for'}

    def parse(self, parser):
        """Парсинг SDUI циклов"""
        lineno = next(parser.stream).lineno

        # Парсим переменную цикла
        target = parser.parse_assign_target(name_only=True)

        parser.stream.expect('name:in')

        # Парсим итерируемый объект
        iter_obj = parser.parse_expression()

        # Парсим тело цикла
        body = parser.parse_statements(['name:endsdui_for'], drop_needle=False)
        parser.stream.expect('name:endsdui_for')

        # Создаём узел цикла
        return nodes.For(target, iter_obj, body, [], None, False, lineno=lineno)


def create_sdui_filters():
    """Создание словаря кастомных фильтров для SDUI"""

    filters = {}

    # Строковые фильтры
    def sdui_concat(*args):
        """Конкатенация строк"""
        return ''.join(str(arg) for arg in args if arg is not None)

    def sdui_substring(value, start=0, end=None):
        """Получение подстроки"""
        if value is None:
            return ''
        str_val = str(value)
        if end is None:
            return str_val[start:]
        return str_val[start:end]

    def sdui_pad_start(value, length, fill_char=' '):
        """Дополнение строки слева"""
        if value is None:
            return ''
        str_val = str(value)
        if len(str_val) >= length:
            return str_val
        return str_val.rjust(length, fill_char)

    def sdui_pad_end(value, length, fill_char=' '):
        """Дополнение строки справа"""
        if value is None:
            return ''
        str_val = str(value)
        if len(str_val) >= length:
            return str_val
        return str_val.ljust(length, fill_char)

    def sdui_split(value, separator=','):
        """Разделение строки"""
        if value is None:
            return []
        return str(value).split(separator)

    # Математические фильтры
    def sdui_ceil(value):
        """Округление вверх"""
        try:
            return math.ceil(float(value))
        except (TypeError, ValueError):
            return 0

    def sdui_floor(value):
        """Округление вниз"""
        try:
            return math.floor(float(value))
        except (TypeError, ValueError):
            return 0

    def sdui_min(*args):
        """Минимальное значение"""
        try:
            return min(float(arg) for arg in args if arg is not None)
        except (TypeError, ValueError):
            return 0

    def sdui_max(*args):
        """Максимальное значение"""
        try:
            return max(float(arg) for arg in args if arg is not None)
        except (TypeError, ValueError):
            return 0

    def sdui_clamp(value, min_val, max_val):
        """Ограничение значения в диапазоне"""
        try:
            val = float(value)
            return max(min_val, min(val, max_val))
        except (TypeError, ValueError):
            return min_val

    def sdui_percentage(value, total):
        """Вычисление процента"""
        try:
            if total == 0:
                return 0
            return (float(value) / float(total)) * 100
        except (TypeError, ValueError, ZeroDivisionError):
            return 0

    # Фильтры для массивов
    def sdui_flatten(value):
        """Сглаживание вложенных массивов"""
        if not isinstance(value, (list, tuple)):
            return [value]

        result = []
        for item in value:
            if isinstance(item, (list, tuple)):
                result.extend(sdui_flatten(item))
            else:
                result.append(item)
        return result

    def sdui_chunk(value, size):
        """Разделение массива на части"""
        if not isinstance(value, (list, tuple)):
            return []

        chunks = []
        for i in range(0, len(value), size):
            chunks.append(list(value[i:i+size]))
        return chunks

    def sdui_group_by(value, key):
        """Группировка элементов по ключу"""
        if not isinstance(value, (list, tuple)):
            return {}

        groups = {}
        for item in value:
            if isinstance(item, dict):
                group_key = item.get(key)
                if group_key not in groups:
                    groups[group_key] = []
                groups[group_key].append(item)
        return groups

    def sdui_pluck(value, key):
        """Извлечение значений по ключу из массива объектов"""
        if not isinstance(value, (list, tuple)):
            return []

        result = []
        for item in value:
            if isinstance(item, dict) and key in item:
                result.append(item[key])
        return result

    def sdui_find(value, condition_key, condition_value):
        """Поиск первого элемента по условию"""
        if not isinstance(value, (list, tuple)):
            return None

        for item in value:
            if isinstance(item, dict) and item.get(condition_key) == condition_value:
                return item
        return None

    def sdui_find_index(value, condition_key, condition_value):
        """Поиск индекса элемента по условию"""
        if not isinstance(value, (list, tuple)):
            return -1

        for i, item in enumerate(value):
            if isinstance(item, dict) and item.get(condition_key) == condition_value:
                return i
        return -1

    def sdui_every(value, condition_key, condition_value):
        """Проверка, что все элементы удовлетворяют условию"""
        if not isinstance(value, (list, tuple)):
            return False

        if not value:
            return True

        for item in value:
            if not isinstance(item, dict) or item.get(condition_key) != condition_value:
                return False
        return True

    def sdui_some(value, condition_key, condition_value):
        """Проверка, что хотя бы один элемент удовлетворяет условию"""
        if not isinstance(value, (list, tuple)):
            return False

        for item in value:
            if isinstance(item, dict) and item.get(condition_key) == condition_value:
                return True
        return False

    # Фильтры для дат
    def sdui_date_now():
        """Текущая дата и время"""
        return datetime.now()

    def sdui_date_add(value, days=0, hours=0, minutes=0, seconds=0):
        """Добавление времени к дате"""
        try:
            if isinstance(value, str):
                dt = datetime.fromisoformat(value)
            elif isinstance(value, datetime):
                dt = value
            else:
                return value

            delta = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
            return dt + delta
        except:
            return value

    def sdui_date_subtract(value, days=0, hours=0, minutes=0, seconds=0):
        """Вычитание времени из даты"""
        try:
            if isinstance(value, str):
                dt = datetime.fromisoformat(value)
            elif isinstance(value, datetime):
                dt = value
            else:
                return value

            delta = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
            return dt - delta
        except:
            return value

    def sdui_date_diff(date1, date2, unit='days'):
        """Разница между датами"""
        try:
            if isinstance(date1, str):
                dt1 = datetime.fromisoformat(date1)
            else:
                dt1 = date1

            if isinstance(date2, str):
                dt2 = datetime.fromisoformat(date2)
            else:
                dt2 = date2

            diff = dt1 - dt2

            if unit == 'seconds':
                return int(diff.total_seconds())
            elif unit == 'minutes':
                return int(diff.total_seconds() / 60)
            elif unit == 'hours':
                return int(diff.total_seconds() / 3600)
            elif unit == 'days':
                return diff.days
            else:
                return diff.days
        except:
            return 0

    def sdui_date_format(value, format='%Y-%m-%d %H:%M:%S'):
        """Форматирование даты"""
        try:
            if isinstance(value, str):
                dt = datetime.fromisoformat(value)
            elif isinstance(value, datetime):
                dt = value
            else:
                return value

            return dt.strftime(format)
        except:
            return value

    # Фильтры для объектов
    def sdui_merge(*objects):
        """Объединение объектов"""
        result = {}
        for obj in objects:
            if isinstance(obj, dict):
                result.update(obj)
        return result

    def sdui_pick(obj, *keys):
        """Выбор определённых ключей из объекта"""
        if not isinstance(obj, dict):
            return {}

        return {k: v for k, v in obj.items() if k in keys}

    def sdui_omit(obj, *keys):
        """Исключение определённых ключей из объекта"""
        if not isinstance(obj, dict):
            return {}

        return {k: v for k, v in obj.items() if k not in keys}

    def sdui_invert(obj):
        """Инверсия ключей и значений объекта"""
        if not isinstance(obj, dict):
            return {}

        return {str(v): k for k, v in obj.items()}

    # Логические фильтры
    def sdui_coalesce(*values):
        """Возвращает первое не-null значение"""
        for value in values:
            if value is not None:
                return value
        return None

    def sdui_is_empty(value):
        """Проверка на пустоту"""
        if value is None:
            return True
        if isinstance(value, (str, list, tuple, dict)):
            return len(value) == 0
        return False

    def sdui_is_not_empty(value):
        """Проверка на непустоту"""
        return not sdui_is_empty(value)

    def sdui_type_of(value):
        """Получение типа значения"""
        if value is None:
            return 'null'
        elif isinstance(value, bool):
            return 'boolean'
        elif isinstance(value, int):
            return 'integer'
        elif isinstance(value, float):
            return 'float'
        elif isinstance(value, str):
            return 'string'
        elif isinstance(value, list):
            return 'array'
        elif isinstance(value, dict):
            return 'object'
        else:
            return 'unknown'

    # Фильтры для преобразования типов
    def sdui_to_string(value):
        """Преобразование в строку"""
        if value is None:
            return ''
        elif isinstance(value, bool):
            return 'true' if value else 'false'
        else:
            return str(value)

    def sdui_to_number(value):
        """Преобразование в число"""
        if value is None:
            return 0
        try:
            if isinstance(value, bool):
                return 1 if value else 0
            elif isinstance(value, str):
                if '.' in value:
                    return float(value)
                else:
                    return int(value)
            else:
                return float(value)
        except (TypeError, ValueError):
            return 0

    def sdui_to_boolean(value):
        """Преобразование в булево значение"""
        if value is None:
            return False
        elif isinstance(value, bool):
            return value
        elif isinstance(value, (int, float)):
            return value != 0
        elif isinstance(value, str):
            return value.lower() not in ('', 'false', '0', 'null', 'none')
        else:
            return bool(value)

    def sdui_to_json(value, indent=None):
        """Преобразование в JSON строку"""
        try:
            return json.dumps(value, ensure_ascii=False, indent=indent)
        except (TypeError, ValueError):
            return '{}'

    def sdui_from_json(value):
        """Парсинг JSON строки"""
        if not isinstance(value, str):
            return value
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return None

    # Регистрация фильтров
    filters['sdui_concat'] = sdui_concat
    filters['sdui_substring'] = sdui_substring
    filters['sdui_pad_start'] = sdui_pad_start
    filters['sdui_pad_end'] = sdui_pad_end
    filters['sdui_split'] = sdui_split

    filters['sdui_ceil'] = sdui_ceil
    filters['sdui_floor'] = sdui_floor
    filters['sdui_min'] = sdui_min
    filters['sdui_max'] = sdui_max
    filters['sdui_clamp'] = sdui_clamp
    filters['sdui_percentage'] = sdui_percentage

    filters['sdui_flatten'] = sdui_flatten
    filters['sdui_chunk'] = sdui_chunk
    filters['sdui_group_by'] = sdui_group_by
    filters['sdui_pluck'] = sdui_pluck
    filters['sdui_find'] = sdui_find
    filters['sdui_find_index'] = sdui_find_index
    filters['sdui_every'] = sdui_every
    filters['sdui_some'] = sdui_some

    filters['sdui_date_now'] = sdui_date_now
    filters['sdui_date_add'] = sdui_date_add
    filters['sdui_date_subtract'] = sdui_date_subtract
    filters['sdui_date_diff'] = sdui_date_diff
    filters['sdui_date_format'] = sdui_date_format
    filters['date_add'] = sdui_date_add  # Алиас для совместимости
    filters['format_date'] = sdui_date_format  # Алиас для совместимости

    filters['sdui_merge'] = sdui_merge
    filters['sdui_pick'] = sdui_pick
    filters['sdui_omit'] = sdui_omit
    filters['sdui_invert'] = sdui_invert

    filters['sdui_coalesce'] = sdui_coalesce
    filters['sdui_is_empty'] = sdui_is_empty
    filters['sdui_is_not_empty'] = sdui_is_not_empty
    filters['sdui_type_of'] = sdui_type_of

    filters['sdui_to_string'] = sdui_to_string
    filters['sdui_to_number'] = sdui_to_number
    filters['sdui_to_boolean'] = sdui_to_boolean
    filters['sdui_to_json'] = sdui_to_json
    filters['sdui_from_json'] = sdui_from_json

    # Алиасы для совместимости
    filters['safe_get'] = lambda obj, key, default=None: obj.get(key, default) if isinstance(obj, dict) else default
    filters['fromjson'] = sdui_from_json
    filters['tojson'] = sdui_to_json

    return filters


def create_sdui_tests():
    """Создание словаря кастомных тестов для SDUI"""

    tests = {}

    def is_sdui_empty(value):
        """Тест на пустоту"""
        if value is None:
            return True
        if isinstance(value, (str, list, tuple, dict)):
            return len(value) == 0
        return False

    def is_sdui_not_empty(value):
        """Тест на непустоту"""
        return not is_sdui_empty(value)

    def is_sdui_null(value):
        """Тест на null"""
        return value is None

    def is_sdui_not_null(value):
        """Тест на не-null"""
        return value is not None

    def is_sdui_number(value):
        """Тест на число"""
        return isinstance(value, (int, float)) and not isinstance(value, bool)

    def is_sdui_string(value):
        """Тест на строку"""
        return isinstance(value, str)

    def is_sdui_boolean(value):
        """Тест на булево значение"""
        return isinstance(value, bool)

    def is_sdui_array(value):
        """Тест на массив"""
        return isinstance(value, (list, tuple))

    def is_sdui_object(value):
        """Тест на объект"""
        return isinstance(value, dict)

    # Регистрация тестов
    tests['sdui_empty'] = is_sdui_empty
    tests['sdui_not_empty'] = is_sdui_not_empty
    tests['sdui_null'] = is_sdui_null
    tests['sdui_not_null'] = is_sdui_not_null
    tests['sdui_number'] = is_sdui_number
    tests['sdui_string'] = is_sdui_string
    tests['sdui_boolean'] = is_sdui_boolean
    tests['sdui_array'] = is_sdui_array
    tests['sdui_object'] = is_sdui_object

    return tests


def create_sdui_globals():
    """Создание словаря глобальных функций для SDUI"""

    globals_dict = {}

    # Глобальные функции
    globals_dict['now'] = datetime.now
    globals_dict['range'] = range
    globals_dict['len'] = len
    globals_dict['int'] = int
    globals_dict['float'] = float
    globals_dict['str'] = str
    globals_dict['bool'] = bool
    globals_dict['list'] = list
    globals_dict['dict'] = dict
    globals_dict['abs'] = abs
    globals_dict['min'] = min
    globals_dict['max'] = max
    globals_dict['sum'] = sum
    globals_dict['round'] = round
    globals_dict['sorted'] = sorted
    globals_dict['reversed'] = reversed

    return globals_dict