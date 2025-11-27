#!/usr/bin/env python3
"""
SDUI to Jinja2 Transformer
Модуль для преобразования SDUI синтаксиса в Jinja2 шаблоны
"""

import re
import json
import logging
from typing import Any, Dict, List, Optional, Union, Tuple
from pathlib import Path
from collections import OrderedDict


logger = logging.getLogger(__name__)


class SDUIToJinja2Transformer:
    """Трансформер для преобразования SDUI выражений в Jinja2"""

    def __init__(self, mapping_file: Optional[str] = None):
        """
        Инициализация трансформера

        Args:
            mapping_file: Путь к файлу с маппингом SDUI→Jinja2
        """
        self.mapping = self._load_mapping(mapping_file)
        self.transformation_cache = {}
        self.processed_nodes = set()

    def _load_mapping(self, mapping_file: Optional[str] = None) -> Dict:
        """
        Загрузка маппинга из файла

        Args:
            mapping_file: Путь к файлу маппинга

        Returns:
            Словарь с маппингом
        """
        if mapping_file is None:
            # Используем файл по умолчанию
            current_dir = Path(__file__).parent
            mapping_file = current_dir / 'sdui_mapping.json'

        try:
            with open(mapping_file, 'r', encoding='utf-8') as f:
                mapping = json.load(f)
                logger.info(f"✅ Загружен маппинг SDUI→Jinja2 v{mapping.get('version', 'unknown')}")
                return mapping
        except FileNotFoundError:
            logger.error(f"❌ Файл маппинга не найден: {mapping_file}")
            return self._get_default_mapping()
        except json.JSONDecodeError as e:
            logger.error(f"❌ Ошибка парсинга маппинга: {e}")
            return self._get_default_mapping()

    def _get_default_mapping(self) -> Dict:
        """Получение маппинга по умолчанию"""
        return {
            "patterns": {
                "variables": {
                    "simple": {
                        "pattern": r"\$\{([^}]+)\}",
                        "template": "{{ $1 }}"
                    }
                }
            }
        }

    def transform(self, content: Any) -> Any:
        """
        Главный метод преобразования SDUI в Jinja2

        Args:
            content: Контент для преобразования (строка, словарь, список)

        Returns:
            Преобразованный контент
        """
        if isinstance(content, str):
            return self._transform_string(content)
        elif isinstance(content, dict):
            return self._transform_dict(content)
        elif isinstance(content, list):
            return self._transform_list(content)
        else:
            return content

    def _transform_string(self, text: str) -> str:
        """
        Преобразование строки с SDUI выражениями в Jinja2

        Args:
            text: Исходная строка

        Returns:
            Преобразованная строка
        """
        # Проверяем кэш
        if text in self.transformation_cache:
            return self.transformation_cache[text]

        result = text

        # Применяем паттерны в порядке приоритета
        for category_path in self.mapping.get('priority_order', []):
            result = self._apply_category_patterns(result, category_path)

        # Сохраняем в кэш
        self.transformation_cache[text] = result
        return result

    def _apply_category_patterns(self, text: str, category_path: str) -> str:
        """
        Применение паттернов категории

        Args:
            text: Исходный текст
            category_path: Путь к категории паттернов

        Returns:
            Преобразованный текст
        """
        patterns = self.mapping.get('patterns', {})

        # Навигация по пути категории
        category_parts = category_path.split('.')
        current_patterns = patterns

        for part in category_parts:
            if part in current_patterns:
                current_patterns = current_patterns[part]
            else:
                return text

        # Если это словарь с паттернами, применяем их
        if isinstance(current_patterns, dict):
            if 'pattern' in current_patterns and 'template' in current_patterns:
                # Это один паттерн
                text = self._apply_single_pattern(text, current_patterns)
            else:
                # Это коллекция паттернов
                for pattern_name, pattern_config in current_patterns.items():
                    if isinstance(pattern_config, dict) and 'pattern' in pattern_config:
                        text = self._apply_single_pattern(text, pattern_config)

        return text

    def _apply_single_pattern(self, text: str, pattern_config: Dict) -> str:
        """
        Применение одного паттерна

        Args:
            text: Исходный текст
            pattern_config: Конфигурация паттерна

        Returns:
            Преобразованный текст
        """
        pattern = pattern_config.get('pattern')
        template = pattern_config.get('template')
        transform = pattern_config.get('transform')

        if not pattern or not template:
            return text

        try:
            # Компилируем регулярное выражение
            regex = re.compile(pattern, re.MULTILINE | re.DOTALL)

            def replacer(match):
                """Функция замены с поддержкой трансформаций"""
                groups = match.groups()
                result = template

                # Применяем трансформации если нужно
                if transform and transform in self.mapping.get('transformations', {}):
                    groups = self._apply_transformation(groups, transform)

                # Заменяем плейсхолдеры
                for i, group in enumerate(groups, 1):
                    placeholder = f'${i}'
                    if placeholder in result:
                        result = result.replace(placeholder, str(group) if group else '')

                return result

            # Применяем замены
            text = regex.sub(replacer, text)

        except re.error as e:
            logger.warning(f"⚠️ Ошибка в регулярном выражении: {e}")

        return text

    def _apply_transformation(self, groups: Tuple, transform_name: str) -> Tuple:
        """
        Применение трансформации к группам

        Args:
            groups: Группы из регулярного выражения
            transform_name: Имя трансформации

        Returns:
            Преобразованные группы
        """
        transformations = self.mapping.get('transformations', {})
        transform_config = transformations.get(transform_name, {})

        if not transform_config:
            return groups

        # Обработка специальных трансформаций
        if transform_name == 'join_with_and':
            if groups and groups[0]:
                values = self._parse_array_values(groups[0])
                joined = ' and '.join(values)
                return (joined,)

        elif transform_name == 'join_with_or':
            if groups and groups[0]:
                values = self._parse_array_values(groups[0])
                joined = ' or '.join(values)
                return (joined,)

        elif transform_name == 'join_with_plus':
            if groups and groups[0]:
                values = self._parse_array_values(groups[0])
                joined = ' + '.join(f'({v})' for v in values)
                return (joined,)

        elif transform_name == 'join_with_multiply':
            if groups and groups[0]:
                values = self._parse_array_values(groups[0])
                joined = ' * '.join(f'({v})' for v in values)
                return (joined,)

        elif transform_name == 'join_strings':
            if groups and groups[0]:
                values = self._parse_array_values(groups[0])
                joined = ' ~ '.join(values)
                return (joined,)

        return groups

    def _parse_array_values(self, array_str: str) -> List[str]:
        """
        Парсинг значений из строки массива

        Args:
            array_str: Строка с массивом

        Returns:
            Список значений
        """
        try:
            # Пытаемся распарсить как JSON
            values = json.loads(f'[{array_str}]')
            return [self._transform_value_to_jinja(v) for v in values]
        except:
            # Если не получилось, разбиваем по запятым
            values = []
            depth = 0
            current = []

            for char in array_str:
                if char == '{' or char == '[':
                    depth += 1
                elif char == '}' or char == ']':
                    depth -= 1
                elif char == ',' and depth == 0:
                    values.append(''.join(current).strip())
                    current = []
                    continue

                current.append(char)

            if current:
                values.append(''.join(current).strip())

            return values

    def _transform_value_to_jinja(self, value: Any) -> str:
        """
        Преобразование значения в Jinja2 синтаксис

        Args:
            value: Значение для преобразования

        Returns:
            Строка в Jinja2 синтаксисе
        """
        if isinstance(value, str):
            # Проверяем, не является ли это уже переменной
            if value.startswith('${') and value.endswith('}'):
                # Это SDUI переменная, преобразуем
                return self._transform_string(value)
            else:
                # Это обычная строка
                return f"'{value}'"
        elif isinstance(value, bool):
            return 'true' if value else 'false'
        elif value is None:
            return 'none'
        else:
            return str(value)

    def _transform_dict(self, obj: Dict) -> Dict:
        """
        Рекурсивное преобразование словаря

        Args:
            obj: Исходный словарь

        Returns:
            Преобразованный словарь
        """
        # Проверяем, не является ли это SDUI функцией
        if 'type' in obj:
            sdui_result = self._transform_sdui_function(obj)
            if sdui_result is not None:
                return sdui_result

        # Рекурсивно преобразуем ключи и значения
        result = {}
        for key, value in obj.items():
            # Преобразуем ключ если он содержит SDUI выражения
            transformed_key = self._transform_string(key) if isinstance(key, str) else key

            # Преобразуем значение
            transformed_value = self.transform(value)

            result[transformed_key] = transformed_value

        return result

    def _transform_sdui_function(self, func_obj: Dict) -> Optional[Union[str, Dict]]:
        """
        Преобразование SDUI функции в Jinja2

        Args:
            func_obj: Объект SDUI функции

        Returns:
            Преобразованная функция или None
        """
        func_type = func_obj.get('type')

        if not func_type:
            return None

        # Специальная обработка для условных выражений
        if func_type == 'if':
            condition = self.transform(func_obj.get('if', 'false'))
            then_value = self.transform(func_obj.get('then', ''))
            else_value = self.transform(func_obj.get('else', ''))

            # Возвращаем Jinja2 условное выражение
            return f"{{{{ {then_value} if {condition} else {else_value} }}}}"

        # Специальная обработка для логических операций
        elif func_type == 'and':
            values = func_obj.get('values', [])
            transformed_values = [self.transform(v) for v in values]
            joined = ' and '.join(f"({v})" for v in transformed_values)
            return f"{{{{ {joined} }}}}"

        elif func_type == 'or':
            values = func_obj.get('values', [])
            transformed_values = [self.transform(v) for v in values]
            joined = ' or '.join(f"({v})" for v in transformed_values)
            return f"{{{{ {joined} }}}}"

        elif func_type == 'not':
            value = self.transform(func_obj.get('value', 'false'))
            return f"{{{{ not ({value}) }}}}"

        # Специальная обработка для строковых функций
        elif func_type == 'concat':
            values = func_obj.get('values', [])
            transformed_values = [self.transform(v) for v in values]
            joined = ' ~ '.join(transformed_values)
            return f"{{{{ {joined} }}}}"

        elif func_type == 'uppercase':
            value = self.transform(func_obj.get('value', ''))
            return f"{{{{ ({value}) | upper }}}}"

        elif func_type == 'lowercase':
            value = self.transform(func_obj.get('value', ''))
            return f"{{{{ ({value}) | lower }}}}"

        elif func_type == 'trim':
            value = self.transform(func_obj.get('value', ''))
            return f"{{{{ ({value}) | trim }}}}"

        # Специальная обработка для математических функций
        elif func_type == 'add':
            values = func_obj.get('values', [])
            transformed_values = [self.transform(v) for v in values]
            joined = ' + '.join(f"({v})" for v in transformed_values)
            return f"{{{{ {joined} }}}}"

        elif func_type == 'subtract':
            left = self.transform(func_obj.get('left', 0))
            right = self.transform(func_obj.get('right', 0))
            return f"{{{{ ({left}) - ({right}) }}}}"

        elif func_type == 'multiply':
            values = func_obj.get('values', [])
            transformed_values = [self.transform(v) for v in values]
            joined = ' * '.join(f"({v})" for v in transformed_values)
            return f"{{{{ {joined} }}}}"

        elif func_type == 'divide':
            left = self.transform(func_obj.get('left', 1))
            right = self.transform(func_obj.get('right', 1))
            return f"{{{{ ({left}) / ({right}) }}}}"

        # Специальная обработка для массивов
        elif func_type == 'length':
            value = self.transform(func_obj.get('value', []))
            return f"{{{{ ({value}) | length }}}}"

        elif func_type == 'join':
            value = self.transform(func_obj.get('value', []))
            separator = func_obj.get('separator', ',')
            return f"{{{{ ({value}) | join('{separator}') }}}}"

        # Специальная обработка для сравнений
        elif func_type == 'equals':
            left = self.transform(func_obj.get('left'))
            right = self.transform(func_obj.get('right'))
            return f"{{{{ ({left}) == ({right}) }}}}"

        elif func_type == 'notEquals':
            left = self.transform(func_obj.get('left'))
            right = self.transform(func_obj.get('right'))
            return f"{{{{ ({left}) != ({right}) }}}}"

        elif func_type == 'greaterThan':
            left = self.transform(func_obj.get('left'))
            right = self.transform(func_obj.get('right'))
            return f"{{{{ ({left}) > ({right}) }}}}"

        elif func_type == 'lessThan':
            left = self.transform(func_obj.get('left'))
            right = self.transform(func_obj.get('right'))
            return f"{{{{ ({left}) < ({right}) }}}}"

        # Если тип функции не распознан, пробуем найти в маппинге
        else:
            # Пытаемся сериализовать объект и применить паттерны
            json_str = json.dumps(func_obj, ensure_ascii=False)
            transformed_str = self._transform_string(json_str)

            # Если строка изменилась, возвращаем её
            if transformed_str != json_str:
                return transformed_str

        return None

    def _transform_list(self, arr: List) -> List:
        """
        Рекурсивное преобразование списка

        Args:
            arr: Исходный список

        Returns:
            Преобразованный список
        """
        return [self.transform(item) for item in arr]

    def validate_transformation(self, original: Any, transformed: Any) -> Tuple[bool, List[str]]:
        """
        Валидация результата преобразования

        Args:
            original: Исходный контент
            transformed: Преобразованный контент

        Returns:
            Кортеж (успешность, список предупреждений)
        """
        warnings = []

        # Проверяем наличие непреобразованных SDUI выражений
        if isinstance(transformed, str):
            # Проверяем остатки SDUI синтаксиса
            if '${' in transformed and not '{{' in transformed:
                warnings.append(f"Возможно непреобразованное SDUI выражение: {transformed[:50]}...")

            # Проверяем корректность Jinja2 синтаксиса
            if '{{' in transformed:
                # Подсчитываем баланс скобок
                open_count = transformed.count('{{')
                close_count = transformed.count('}}')
                if open_count != close_count:
                    warnings.append(f"Несбалансированные Jinja2 скобки: открыто {open_count}, закрыто {close_count}")

        elif isinstance(transformed, dict):
            for key, value in transformed.items():
                _, value_warnings = self.validate_transformation(
                    original.get(key) if isinstance(original, dict) else None,
                    value
                )
                warnings.extend(value_warnings)

        elif isinstance(transformed, list):
            for i, item in enumerate(transformed):
                _, item_warnings = self.validate_transformation(
                    original[i] if isinstance(original, list) and i < len(original) else None,
                    item
                )
                warnings.extend(item_warnings)

        return len(warnings) == 0, warnings

    def get_statistics(self) -> Dict:
        """
        Получение статистики преобразований

        Returns:
            Словарь со статистикой
        """
        return {
            'cache_size': len(self.transformation_cache),
            'processed_nodes': len(self.processed_nodes),
            'mapping_version': self.mapping.get('version', 'unknown'),
            'pattern_categories': len(self.mapping.get('patterns', {})),
            'transformations': len(self.mapping.get('transformations', {}))
        }

    def clear_cache(self):
        """Очистка кэша преобразований"""
        self.transformation_cache.clear()
        self.processed_nodes.clear()
        logger.info("🗑️ Кэш преобразований очищен")