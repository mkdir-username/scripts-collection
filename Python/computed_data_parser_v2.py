#!/usr/bin/env python3
"""
Enhanced JSON Contract Parser v2.0
===================================

Автоматический парсер для разрешения сложных JSON-контрактов с:
- Computed выражениями (условия if-then-else)
- Подстановками ${computed.xxx}, ${data.xxx}, ${state.xxx}
- Специальными полями $children, $if, $then, $else
- Интеграцией моковых данных

Основные возможности:
1. Рекурсивное разрешение всех ссылок и подстановок
2. Вычисление условных выражений
3. Интеграция данных из внешнего файла
4. Защита от циклических зависимостей
5. Подробное логирование процесса
"""

import json
import re
import logging
from typing import Any, Dict, List, Union, Optional
from copy import deepcopy
from pathlib import Path


# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class ResolutionError(Exception):
    """Ошибка при разрешении значения."""
    pass


class CircularDependencyError(Exception):
    """Ошибка циклической зависимости."""
    pass


class JSONContractParser:
    """
    Парсер для разрешения сложных JSON-контрактов.
    
    Архитектура:
    -----------
    1. Загрузка контракта и данных
    2. Интеграция моковых данных
    3. Рекурсивное разрешение rootElement
    4. Обработка computed, data, state ссылок
    5. Вычисление условных выражений
    6. Развертывание $children массивов
    """
    
    def __init__(self, contract_file: str, data_file: str, verbose: bool = False):
        """
        Инициализация парсера.
        
        Args:
            contract_file: Путь к файлу с основным контрактом
            data_file: Путь к файлу с моковыми данными
            verbose: Включить подробное логирование
        """
        self.verbose = verbose
        if verbose:
            logger.setLevel(logging.DEBUG)
        
        logger.info(f"📂 Загрузка контракта: {contract_file}")
        with open(contract_file, 'r', encoding='utf-8') as f:
            self.contract = json.load(f)
        
        logger.info(f"📂 Загрузка моковых данных: {data_file}")
        with open(data_file, 'r', encoding='utf-8') as f:
            self.mock_data = json.load(f)
        
        # Извлекаем секции
        self.computed = self.contract.get('computed', {})
        self.data = self.contract.get('data', {})
        self.state = self.contract.get('state', {})
        self.root_element = self.contract.get('rootElement', {})
        
        logger.info(f"✅ Загружено: {len(self.computed)} computed, {len(self.data)} data, {len(self.state)} state")
        
        # Кэш для разрешенных computed значений
        self.computed_cache: Dict[str, Any] = {}
        
        # Стек вызовов для отслеживания циклов
        self.resolution_stack: List[str] = []
        
        # Статистика
        self.stats = {
            'computed_resolved': 0,
            'substitutions': 0,
            'if_expressions': 0,
            'children_expanded': 0
        }
    
    def parse(self) -> Dict[str, Any]:
        """
        Основной метод парсинга.
        
        Returns:
            Полностью распарсенный JSON с единственным ключом rootElement
        """
        logger.info("🚀 Начало парсинга контракта...")
        
        # Шаг 1: Интегрируем моковые данные
        logger.info("📊 Интеграция моковых данных...")
        self._integrate_mock_data()
        
        # Шаг 2: Разрешаем rootElement
        logger.info("🔧 Разрешение rootElement...")
        try:
            resolved_root = self._resolve_value(self.root_element, 'rootElement')
        except Exception as e:
            logger.error(f"❌ Ошибка при разрешении rootElement: {e}")
            raise
        
        # Выводим статистику
        logger.info("📈 Статистика парсинга:")
        logger.info(f"  - Computed разрешено: {self.stats['computed_resolved']}")
        logger.info(f"  - Подстановок выполнено: {self.stats['substitutions']}")
        logger.info(f"  - IF-выражений обработано: {self.stats['if_expressions']}")
        logger.info(f"  - $children развернуто: {self.stats['children_expanded']}")
        
        logger.info("✅ Парсинг завершен успешно!")
        
        return {"rootElement": resolved_root}
    
    def _integrate_mock_data(self):
        """Интегрирует моковые данные в state."""
        integrated_count = 0
        for key, value in self.mock_data.items():
            if key not in self.state:
                self.state[key] = value
                integrated_count += 1
                logger.debug(f"  + Добавлено в state: {key}")
        
        logger.info(f"  ✓ Интегрировано полей: {integrated_count}")
    
    def _resolve_value(self, value: Any, path: str = "") -> Any:
        """
        Рекурсивно разрешает значение.
        
        Args:
            value: Значение для разрешения
            path: Путь для отладки и обнаружения циклов
            
        Returns:
            Разрешенное значение
        """
        # Проверка на циклы
        if path in self.resolution_stack:
            raise CircularDependencyError(
                f"Обнаружена циклическая зависимость: {' -> '.join(self.resolution_stack + [path])}"
            )
        
        self.resolution_stack.append(path)
        
        try:
            # Строки - проверяем на подстановки
            if isinstance(value, str):
                result = self._resolve_string(value, path)
                return result
            
            # Списки - обрабатываем каждый элемент
            elif isinstance(value, list):
                return [self._resolve_value(item, f"{path}[{i}]") for i, item in enumerate(value)]
            
            # Словари - обрабатываем специальные случаи
            elif isinstance(value, dict):
                return self._resolve_dict(value, path)
            
            # Остальные типы возвращаем как есть
            else:
                return value
                
        finally:
            self.resolution_stack.pop()
    
    def _resolve_string(self, string: str, path: str = "") -> Any:
        """
        Разрешает строковые подстановки вида ${...}.
        
        Args:
            string: Строка для обработки
            path: Путь для логирования
            
        Returns:
            Разрешенное значение (может быть не строкой)
        """
        # Случай 1: Полная подстановка "${...}"
        full_match = re.match(r'^\$\{(.+)\}$', string)
        if full_match:
            ref_path = full_match.group(1)
            logger.debug(f"  🔗 Подстановка: {path} -> {ref_path}")
            self.stats['substitutions'] += 1
            return self._resolve_reference(ref_path)
        
        # Случай 2: Частичная подстановка "text ${...} text"
        if '${' in string:
            logger.debug(f"  🔗 Частичная подстановка в: {path}")
            
            def replacer(match):
                ref_path = match.group(1)
                resolved = self._resolve_reference(ref_path)
                self.stats['substitutions'] += 1
                return str(resolved) if resolved is not None else ''
            
            result = re.sub(r'\$\{([^}]+)\}', replacer, string)
            return result
        
        # Случай 3: Обычная строка
        return string
    
    def _resolve_reference(self, ref: str) -> Any:
        """
        Разрешает ссылку вида 'computed.xxx', 'data.xxx', 'state.xxx'.
        
        Args:
            ref: Ссылка для разрешения
            
        Returns:
            Значение по ссылке
        """
        parts = ref.split('.', 1)
        if len(parts) < 2:
            raise ResolutionError(f"Некорректная ссылка (нет точки): {ref}")
        
        namespace = parts[0]
        key_path = parts[1]
        
        if namespace == 'computed':
            return self._resolve_computed(key_path)
        
        elif namespace == 'data':
            return self._get_nested_value(self.data, key_path, 'data')
        
        elif namespace == 'state':
            return self._get_nested_value(self.state, key_path, 'state')
        
        else:
            raise ResolutionError(f"Неизвестный namespace: {namespace} (в ссылке {ref})")
    
    def _resolve_computed(self, key: str) -> Any:
        """
        Разрешает computed выражение по ключу.
        
        Args:
            key: Ключ computed выражения
            
        Returns:
            Разрешенное значение
        """
        # Проверяем кэш
        if key in self.computed_cache:
            logger.debug(f"  💾 Взято из кэша: computed.{key}")
            return self.computed_cache[key]
        
        if key not in self.computed:
            raise ResolutionError(f"Computed ключ не найден: {key}")
        
        logger.debug(f"  ⚙️  Вычисление computed.{key}...")
        computed_value = self.computed[key]
        
        # Обрабатываем условные выражения (if-then-else)
        if isinstance(computed_value, dict) and computed_value.get('type') == 'if':
            result = self._resolve_if_expression(computed_value, f"computed.{key}")
        else:
            result = self._resolve_value(computed_value, f"computed.{key}")
        
        # Кэшируем результат
        self.computed_cache[key] = result
        self.stats['computed_resolved'] += 1
        
        return result
    
    def _resolve_if_expression(self, expr: Dict[str, Any], path: str = "") -> Any:
        """
        Разрешает условное выражение:
        {
            "type": "if",
            "if": <condition>,
            "$then": <value_if_true>,
            "$else": <value_if_false>,
            "$if": <alternative_condition_notation>
        }
        
        Args:
            expr: Словарь с условным выражением
            path: Путь для логирования
            
        Returns:
            Результат вычисления условия
        """
        self.stats['if_expressions'] += 1
        
        # Получаем условие (может быть в 'if' или '$if')
        condition = expr.get('if') if 'if' in expr else expr.get('$if')
        then_value = expr.get('$then')
        else_value = expr.get('$else')
        
        # Разрешаем условие
        if isinstance(condition, str):
            resolved_condition = self._resolve_string(condition, f"{path}.if")
        else:
            resolved_condition = condition
        
        logger.debug(f"  ❓ IF({resolved_condition}) at {path}")
        
        # Выбираем ветку
        if resolved_condition:
            logger.debug(f"    ✓ THEN ветка")
            return self._resolve_value(then_value, f"{path}.$then") if then_value is not None else {}
        else:
            logger.debug(f"    ✗ ELSE ветка")
            return self._resolve_value(else_value, f"{path}.$else") if else_value is not None else {}
    
    def _resolve_dict(self, obj: Dict[str, Any], path: str = "") -> Dict[str, Any]:
        """
        Разрешает словарь, обрабатывая специальные ключи.
        
        Args:
            obj: Словарь для обработки
            path: Путь для логирования
            
        Returns:
            Разрешенный словарь
        """
        # Проверяем на условное выражение
        if obj.get('type') == 'if':
            return self._resolve_if_expression(obj, path)
        
        result = {}
        
        for key, value in obj.items():
            # Обрабатываем $children - специальный массив с подстановками
            if key == '$children':
                children = self._resolve_value(value, f"{path}.$children")
                if isinstance(children, list):
                    result['children'] = children
                    self.stats['children_expanded'] += 1
                    logger.debug(f"  📦 $children развернуто в {len(children)} элементов")
                else:
                    result['children'] = [children]
            
            # Служебные ключи для условий - пропускаем
            elif key in ('$if', '$then', '$else', 'type') and obj.get('type') == 'if':
                continue
            
            # Обычные ключи
            else:
                result[key] = self._resolve_value(value, f"{path}.{key}")
        
        return result
    
    def _get_nested_value(self, obj: Dict[str, Any], path: str, namespace: str = "") -> Any:
        """
        Получает вложенное значение по пути с точками.
        
        Args:
            obj: Объект для поиска
            path: Путь вида 'key1.key2.key3'
            namespace: Namespace для сообщений об ошибках
            
        Returns:
            Значение по пути
        """
        keys = path.split('.')
        current = obj
        
        for i, key in enumerate(keys):
            if isinstance(current, dict):
                if key in current:
                    current = current[key]
                else:
                    available_keys = list(current.keys())[:5]
                    raise ResolutionError(
                        f"Ключ '{key}' не найден в {namespace}.{'.'.join(keys[:i])}\n"
                        f"Доступные ключи: {available_keys}..."
                    )
            elif isinstance(current, list):
                # Обработка индексов массива
                try:
                    index = int(key)
                    current = current[index]
                except (ValueError, IndexError) as e:
                    raise ResolutionError(
                        f"Не удалось получить элемент массива [{key}] в {namespace}.{'.'.join(keys[:i])}: {e}"
                    )
            else:
                raise ResolutionError(
                    f"Невозможно получить '{key}' из {type(current).__name__} в {namespace}.{'.'.join(keys[:i])}"
                )
        
        return current


def save_pretty_json(data: Dict[str, Any], filepath: str):
    """Сохраняет JSON с красивым форматированием."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    """Основная функция для запуска парсера."""
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(
        description='JSON Contract Parser - разрешает computed выражения и подстановки',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python parser.py contract.json data.json
  python parser.py contract.json data.json -o result.json
  python parser.py contract.json data.json -v
        """
    )
    
    parser.add_argument('contract', help='Файл с JSON-контрактом')
    parser.add_argument('data', help='Файл с моковыми данными')
    parser.add_argument('-o', '--output', default='parsed_output.json', 
                       help='Файл для сохранения результата (по умолчанию: parsed_output.json)')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Подробное логирование')
    
    args = parser.parse_args()
    
    try:
        # Проверяем наличие файлов
        if not Path(args.contract).exists():
            logger.error(f"❌ Файл не найден: {args.contract}")
            sys.exit(1)
        
        if not Path(args.data).exists():
            logger.error(f"❌ Файл не найден: {args.data}")
            sys.exit(1)
        
        # Создаем парсер и выполняем парсинг
        contract_parser = JSONContractParser(args.contract, args.data, verbose=args.verbose)
        result = contract_parser.parse()
        
        # Сохраняем результат
        save_pretty_json(result, args.output)
        
        # Выводим итоговую информацию
        result_size = len(json.dumps(result))
        logger.info(f"")
        logger.info(f"✨ Парсинг успешно завершен!")
        logger.info(f"📄 Результат сохранен в: {args.output}")
        logger.info(f"📊 Размер: {result_size:,} символов ({result_size / 1024:.1f} KB)")
        
    except CircularDependencyError as e:
        logger.error(f"🔄 Обнаружена циклическая зависимость:\n{e}")
        sys.exit(1)
    
    except ResolutionError as e:
        logger.error(f"❌ Ошибка разрешения:\n{e}")
        sys.exit(1)
    
    except Exception as e:
        logger.error(f"❌ Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
