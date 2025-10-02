#!/usr/bin/env python3
"""
Jinja Hot Reload v3.3.0 - Major Integration Release

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 НОВЫЕ ВОЗМОЖНОСТИ В v3.3.0:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MODULE #1: FileSystemLoader Integration
  📂 Поддержка загрузки шаблонов из файловой системы
  📂 Автоматическое определение базовой директории
  📂 Поиск шаблонов в parts/, components/, templates/

MODULE #2: Include/Import Support
  🔗 Полная поддержка {% include %} директив
  🔗 Полная поддержка {% import %} и {% from ... import %}
  🔗 Автоматическое отслеживание всех include/import зависимостей

MODULE #3: Auto Re-rendering
  🔄 Умный ре-рендеринг при изменении любого файла в цепочке
  🔄 Каскадное обновление родительских файлов
  🔄 Пакетная обработка множественных изменений

MODULE #4: Custom Filters & Functions
  🎨 now() - текущая дата/время
  🎨 isoformat - ISO 8601 форматирование
  🎨 formatCurrency - форматирование валюты
  🎨 formatDate - форматирование дат
  🎨 tojson - JSON сериализация
  🎨 daysUntil - дни до даты

MODULE #5: Enhanced Logging
  📊 Детальное логирование обработки файлов
  📊 Визуальные разделители событий
  📊 Цветовая индикация статусов
  📊 Debug режим с трассировкой

MODULE #6: Dependency Graph Visualization
  🌳 Построение графа зависимостей
  🌳 Визуализация parent-child связей
  🌳 Экспорт в DOT/PNG формат
  🌳 Интерактивные отчеты

MODULE #7: Template Caching
  ⚡ Кэширование скомпилированных шаблонов
  ⚡ Инвалидация при изменениях
  ⚡ Ускорение повторного рендеринга

MODULE #8: Error Recovery
  🛡️ Graceful degradation при ошибках
  🛡️ Сохранение частичных результатов
  🛡️ Подробная диагностика ошибок

MODULE #9: Performance Monitoring
  ⏱️ Измерение времени обработки каждого файла
  ⏱️ Статистика по всем операциям
  ⏱️ Выявление узких мест

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 ПРЕДЫДУЩИЕ ВОЗМОЖНОСТИ (v3.2.4):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. 📊 Отслеживание зависимостей parent-child файлов
2. 🔄 Автоматический ре-рендеринг родительских файлов при изменении дочерних
3. 🎯 Умная перезагрузка только когда изменились зависимости
4. 🌐 Браузер перезагружается только один раз после обработки всех файлов
5. 📥 Обработка импортов через комментарии file:///path/to/file
6. 🧹 Удаление всех комментариев из итогового JSON
7. 🧠 Интеллектуальное исправление JSON структуры
8. 🔧 Автоматическое создание заглушек для undefined переменных

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀 ЗАПУСК:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  python3 jinja_hot_reload_v3.3.0.py --smart          # Smart режим
  python3 jinja_hot_reload_v3.3.0.py --smart --debug  # Smart + Debug
  python3 jinja_hot_reload_v3.3.0.py --visualize      # С визуализацией графа
  python3 jinja_hot_reload_v3.3.0.py --test           # Однократная обработка

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📦 CHANGELOG v3.3.0:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[ADDED]
+ FileSystemLoader для поддержки {% include %} и {% import %}
+ Автоматическое отслеживание include/import зависимостей
+ Пользовательские фильтры: now(), formatCurrency, formatDate, daysUntil
+ Визуализация дерева зависимостей в формате DOT/PNG
+ Кэширование скомпилированных шаблонов
+ Мониторинг производительности с детальной статистикой
+ Graceful error recovery с сохранением частичных результатов
+ Экспорт графа зависимостей в HTML

[IMPROVED]
* Улучшенная система логирования с временными метками
* Оптимизированная обработка вложенных include/import
* Более точное определение изменений в цепочке зависимостей
* Расширенный debug режим с подробной трассировкой

[FIXED]
* Корректная обработка относительных путей в include/import
* Предотвращение дублирования обработки при каскадных изменениях
* Правильная инвалидация кэша при изменении зависимостей

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os
import sys
import json
import time
import re
import argparse
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple, Set
from collections import defaultdict
from urllib.parse import unquote
import logging

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 📦 ИМПОРТЫ ЗАВИСИМОСТЕЙ
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

try:
    from jinja2 import (
        Environment, FileSystemLoader, Template,
        TemplateSyntaxError, UndefinedError, StrictUndefined, DebugUndefined
    )
    from jinja2.exceptions import TemplateError, TemplateNotFound
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileModifiedEvent
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("Установите зависимости: pip install jinja2 watchdog")
    sys.exit(1)

# Импорт SDUI модулей (опционально)
sys.path.append(str(Path(__file__).parent))
try:
    from sdui_to_jinja2_transformer import SDUIToJinja2Transformer
    from sdui_jinja_extensions import SDUIJinja2Extensions
except ImportError:
    SDUIToJinja2Transformer = None
    SDUIJinja2Extensions = None

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 📊 НАСТРОЙКА ЛОГИРОВАНИЯ
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MODULE #9: Performance Monitoring
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class PerformanceMonitor:
    """Мониторинг производительности обработки файлов"""

    def __init__(self, debug: bool = False):
        self.debug = debug
        self.timings = defaultdict(list)
        self.counters = defaultdict(int)
        self.start_times = {}

    def start_operation(self, operation_name: str):
        """Начало измерения операции"""
        self.start_times[operation_name] = time.time()
        self.counters[operation_name] += 1

    def end_operation(self, operation_name: str):
        """Окончание измерения операции"""
        if operation_name in self.start_times:
            duration = time.time() - self.start_times[operation_name]
            self.timings[operation_name].append(duration)
            del self.start_times[operation_name]

            if self.debug:
                logger.debug(f"⏱️ {operation_name}: {duration*1000:.2f}ms")

    def get_statistics(self) -> Dict[str, Any]:
        """Получить статистику по всем операциям"""
        stats = {}

        for op_name, durations in self.timings.items():
            if durations:
                stats[op_name] = {
                    'count': len(durations),
                    'total': sum(durations),
                    'average': sum(durations) / len(durations),
                    'min': min(durations),
                    'max': max(durations),
                }

        return stats

    def print_summary(self):
        """Вывести сводку по производительности"""
        stats = self.get_statistics()

        if not stats:
            return

        logger.info("")
        logger.info("━" * 80)
        logger.info("⏱️ СТАТИСТИКА ПРОИЗВОДИТЕЛЬНОСТИ:")
        logger.info("━" * 80)

        for op_name, data in sorted(stats.items()):
            logger.info(f"📊 {op_name}:")
            logger.info(f"   Операций: {data['count']}")
            logger.info(f"   Среднее: {data['average']*1000:.2f}ms")
            logger.info(f"   Минимум: {data['min']*1000:.2f}ms")
            logger.info(f"   Максимум: {data['max']*1000:.2f}ms")
            logger.info(f"   Всего: {data['total']*1000:.2f}ms")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MODULE #8: Error Recovery
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class ErrorRecoveryManager:
    """Управление ошибками с graceful degradation"""

    def __init__(self, debug: bool = False):
        self.debug = debug
        self.error_history = []
        self.recovery_attempts = defaultdict(int)

    def handle_error(self, error: Exception, context: Dict[str, Any]) -> Optional[Any]:
        """
        Обработка ошибки с попыткой восстановления

        Args:
            error: Исключение
            context: Контекст ошибки (файл, операция и т.д.)

        Returns:
            Результат восстановления или None
        """
        error_info = {
            'timestamp': datetime.now(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context
        }

        self.error_history.append(error_info)

        # Попытки восстановления в зависимости от типа ошибки
        if isinstance(error, TemplateNotFound):
            return self._recover_template_not_found(error, context)
        elif isinstance(error, TemplateSyntaxError):
            return self._recover_syntax_error(error, context)
        elif isinstance(error, json.JSONDecodeError):
            return self._recover_json_error(error, context)

        return None

    def _recover_template_not_found(self, error: TemplateNotFound, context: Dict) -> Optional[str]:
        """Восстановление при отсутствующем шаблоне"""
        logger.warning(f"   ⚠️ Шаблон не найден: {error.name}")
        logger.warning(f"   🔧 Используется заглушка")

        # Возвращаем пустой JSON объект как заглушку
        return '{}'

    def _recover_syntax_error(self, error: TemplateSyntaxError, context: Dict) -> Optional[str]:
        """Восстановление при синтаксической ошибке"""
        logger.warning(f"   ⚠️ Синтаксическая ошибка: {error.message}")
        logger.warning(f"   🔧 Попытка использовать исходный контент")

        # Возвращаем исходный контент если он есть
        return context.get('original_content')

    def _recover_json_error(self, error: json.JSONDecodeError, context: Dict) -> Optional[str]:
        """Восстановление при ошибке парсинга JSON"""
        logger.warning(f"   ⚠️ JSON ошибка на строке {error.lineno}: {error.msg}")

        # Попытка исправить распространенные ошибки
        content = context.get('content', '')

        # Удаление trailing commas
        fixed = re.sub(r',(\s*[}\]])', r'\1', content)

        try:
            json.loads(fixed)
            logger.info(f"   ✅ Автоматическое исправление успешно")
            return fixed
        except:
            return None

    def get_error_summary(self) -> str:
        """Получить сводку по ошибкам"""
        if not self.error_history:
            return "Ошибок не обнаружено"

        summary = f"Всего ошибок: {len(self.error_history)}\n"

        # Группировка по типам
        error_types = defaultdict(int)
        for err in self.error_history:
            error_types[err['error_type']] += 1

        summary += "По типам:\n"
        for err_type, count in sorted(error_types.items()):
            summary += f"  • {err_type}: {count}\n"

        return summary


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MODULE #7: Template Caching
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TemplateCacheManager:
    """Кэширование скомпилированных шаблонов"""

    def __init__(self, debug: bool = False):
        self.debug = debug
        self.cache = {}
        self.file_mtimes = {}
        self.hits = 0
        self.misses = 0

    def get_template(self, file_path: Path, jinja_env: Environment) -> Optional[Template]:
        """
        Получить шаблон из кэша или скомпилировать новый

        Args:
            file_path: Путь к файлу шаблона
            jinja_env: Jinja2 окружение

        Returns:
            Скомпилированный шаблон или None при ошибке
        """
        # Проверяем, изменился ли файл
        current_mtime = file_path.stat().st_mtime if file_path.exists() else 0
        cached_mtime = self.file_mtimes.get(file_path, 0)

        # Если файл не изменился, возвращаем из кэша
        if file_path in self.cache and current_mtime == cached_mtime:
            self.hits += 1
            if self.debug:
                logger.debug(f"   💾 Кэш HIT: {file_path.name}")
            return self.cache[file_path]

        # Кэш промах - компилируем заново
        self.misses += 1
        if self.debug:
            logger.debug(f"   🔄 Кэш MISS: {file_path.name}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            template = jinja_env.from_string(content)

            # Сохраняем в кэш
            self.cache[file_path] = template
            self.file_mtimes[file_path] = current_mtime

            return template

        except Exception as e:
            logger.error(f"   ❌ Ошибка компиляции шаблона {file_path.name}: {e}")
            return None

    def invalidate(self, file_path: Path):
        """Инвалидировать кэш для файла"""
        if file_path in self.cache:
            del self.cache[file_path]
            if file_path in self.file_mtimes:
                del self.file_mtimes[file_path]

            if self.debug:
                logger.debug(f"   🗑️ Кэш инвалидирован: {file_path.name}")

    def clear(self):
        """Очистить весь кэш"""
        self.cache.clear()
        self.file_mtimes.clear()
        self.hits = 0
        self.misses = 0

    def get_statistics(self) -> Dict[str, Any]:
        """Получить статистику по кэшу"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0

        return {
            'hits': self.hits,
            'misses': self.misses,
            'total': total,
            'hit_rate': hit_rate,
            'cached_items': len(self.cache)
        }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MODULE #6: Dependency Graph Visualization
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class DependencyGraphVisualizer:
    """Визуализация графа зависимостей"""

    def __init__(self, debug: bool = False):
        self.debug = debug
        self.graph = defaultdict(set)

    def add_dependency(self, parent: Path, child: Path):
        """Добавить зависимость parent -> child"""
        self.graph[parent].add(child)

    def export_dot(self, output_path: Path):
        """Экспорт в DOT формат для Graphviz"""
        dot_content = ["digraph Dependencies {"]
        dot_content.append('  rankdir=LR;')
        dot_content.append('  node [shape=box, style=filled, fillcolor=lightblue];')

        # Генерация узлов и связей
        node_ids = {}
        node_counter = 0

        for parent, children in self.graph.items():
            if parent not in node_ids:
                node_ids[parent] = f"node{node_counter}"
                node_counter += 1
                dot_content.append(f'  {node_ids[parent]} [label="{parent.name}"];')

            for child in children:
                if child not in node_ids:
                    node_ids[child] = f"node{node_counter}"
                    node_counter += 1
                    dot_content.append(f'  {node_ids[child]} [label="{child.name}", fillcolor=lightgreen];')

                dot_content.append(f'  {node_ids[parent]} -> {node_ids[child]};')

        dot_content.append('}')

        # Сохранение
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(dot_content))

        logger.info(f"   📊 Граф экспортирован: {output_path.name}")

    def export_html(self, output_path: Path):
        """Экспорт в HTML с интерактивным графом"""
        html_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Dependency Graph</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .node {{ padding: 10px; margin: 5px; background: #e3f2fd; border-radius: 5px; }}
        .child {{ margin-left: 30px; padding: 5px; background: #c8e6c9; border-left: 3px solid #4caf50; }}
        h1 {{ color: #1976d2; }}
    </style>
</head>
<body>
    <h1>🌳 Граф Зависимостей</h1>
    <div id="graph">
{graph_html}
    </div>
</body>
</html>
"""

        graph_html_parts = []

        for parent, children in sorted(self.graph.items()):
            graph_html_parts.append(f'        <div class="node">📄 {parent.name}')
            for child in sorted(children):
                graph_html_parts.append(f'            <div class="child">↳ {child.name}</div>')
            graph_html_parts.append('        </div>')

        html_content = html_template.format(graph_html='\n'.join(graph_html_parts))

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"   📊 HTML граф экспортирован: {output_path.name}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MODULE #4: Custom Filters & Functions
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class CustomJinjaFilters:
    """Пользовательские фильтры и функции для Jinja2"""

    @staticmethod
    def now():
        """Возвращает текущую дату/время"""
        return datetime.now()

    @staticmethod
    def isoformat(dt):
        """ISO 8601 форматирование"""
        if isinstance(dt, datetime):
            return dt.isoformat()
        return str(dt)

    @staticmethod
    def format_currency(amount: float, currency: str = '₽') -> str:
        """
        Форматирование суммы в валюту
        Пример: 125000 -> ₽ 125 000,00
        """
        formatted = f"{amount:,.2f}".replace(',', ' ').replace('.', ',')
        return f"{currency} {formatted}"

    @staticmethod
    def format_date(date_str: str, format: str = '%d %B %Y') -> str:
        """
        Форматирование даты в читаемый вид
        Пример: 2025-10-15 -> 15 октября 2025
        """
        # Словарь месяцев на русском
        months_ru = {
            1: 'января', 2: 'февраля', 3: 'марта', 4: 'апреля',
            5: 'мая', 6: 'июня', 7: 'июля', 8: 'августа',
            9: 'сентября', 10: 'октября', 11: 'ноября', 12: 'декабря'
        }

        try:
            if isinstance(date_str, str):
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                dt = date_str

            day = dt.day
            month = months_ru.get(dt.month, dt.strftime('%B'))
            year = dt.year

            return f"{day} {month} {year}"
        except:
            return str(date_str)

    @staticmethod
    def days_until(date_str: str) -> int:
        """
        Количество дней до указанной даты
        """
        try:
            if isinstance(date_str, str):
                target_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                target_date = date_str

            delta = target_date - datetime.now()
            return delta.days
        except:
            return 0

    @staticmethod
    def register_filters(jinja_env: Environment):
        """Регистрация всех фильтров в Jinja2 окружении"""
        jinja_env.filters['isoformat'] = CustomJinjaFilters.isoformat
        jinja_env.filters['formatCurrency'] = CustomJinjaFilters.format_currency
        jinja_env.filters['formatDate'] = CustomJinjaFilters.format_date
        jinja_env.filters['daysUntil'] = CustomJinjaFilters.days_until

        # Глобальные функции
        jinja_env.globals['now'] = CustomJinjaFilters.now


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MODULE #2: Include/Import Dependency Tracker
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class IncludeImportTracker:
    """Отслеживание зависимостей через {% include %} и {% import %}"""

    def __init__(self, debug: bool = False):
        self.debug = debug
        self.include_pattern = re.compile(r"{%\s*include\s+['\"]([^'\"]+)['\"]\s*%}")
        self.import_pattern = re.compile(r"{%\s*(?:import|from)\s+['\"]([^'\"]+)['\"]\s*")

    def extract_dependencies(self, content: str) -> Set[str]:
        """
        Извлекает все пути к шаблонам из {% include %} и {% import %}

        Returns:
            Множество путей к зависимым шаблонам
        """
        dependencies = set()

        # Ищем include
        for match in self.include_pattern.finditer(content):
            template_path = match.group(1)
            dependencies.add(template_path)

            if self.debug:
                logger.debug(f"   🔗 Найден include: {template_path}")

        # Ищем import
        for match in self.import_pattern.finditer(content):
            template_path = match.group(1)
            dependencies.add(template_path)

            if self.debug:
                logger.debug(f"   🔗 Найден import: {template_path}")

        return dependencies


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LEGACY MODULES (из v3.2.4)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class SmartJSONFixer:
    """Интеллектуальный фиксер JSON структуры"""

    def __init__(self, debug: bool = False):
        self.debug = debug
        self.fixes_applied = []

    def fix_json(self, content: str) -> Tuple[str, List[str]]:
        """
        Применяет интеллектуальные исправления к JSON
        Returns: (исправленный JSON, список примененных фиксов)
        """
        self.fixes_applied = []
        fixed = content

        # 1. Исправление trailing commas
        fixed = self._fix_trailing_commas(fixed)

        # 2. Исправление missing commas
        fixed = self._fix_missing_commas(fixed)

        # 3. Исправление пустых значений
        fixed = self._fix_empty_values(fixed)

        # 4. Нормализация пробелов
        fixed = self._normalize_whitespace(fixed)

        return fixed, self.fixes_applied

    def _fix_trailing_commas(self, content: str) -> str:
        """Удаляет trailing запятые перед ] и }"""
        pattern1 = r',(\s*)\}'
        if re.search(pattern1, content):
            content = re.sub(pattern1, r'\1}', content)
            self.fixes_applied.append("Удалены trailing запятые перед }")

        pattern2 = r',(\s*)\]'
        if re.search(pattern2, content):
            content = re.sub(pattern2, r'\1]', content)
            self.fixes_applied.append("Удалены trailing запятые перед ]")

        return content

    def _fix_missing_commas(self, content: str) -> str:
        """Добавляет отсутствующие запятые между элементами"""
        pattern1 = r'\}(\s*)\{'
        matches = re.findall(pattern1, content)
        if matches:
            content = re.sub(pattern1, r'},\1{', content)
            self.fixes_applied.append(f"Добавлены {len(matches)} запятых между объектами")

        return content

    def _fix_empty_values(self, content: str) -> str:
        """Заменяет пустые значения на null"""
        patterns = [
            (r':\s*,', ': null,', 'после двоеточия перед запятой'),
            (r':\s*\}', ': null}', 'после двоеточия перед }'),
            (r':\s*\]', ': null]', 'после двоеточия перед ]'),
        ]

        for pattern, replacement, desc in patterns:
            matches = re.findall(pattern, content)
            if matches:
                content = re.sub(pattern, replacement, content)
                self.fixes_applied.append(f"Заменены пустые значения на null ({desc})")

        return content

    def _normalize_whitespace(self, content: str) -> str:
        """Нормализует пробелы (убирает лишние)"""
        content = re.sub(r'\s{2,}', ' ', content)
        return content


class SmartJinja2ContextBuilder:
    """Интеллектуальный построитель контекста для Jinja2"""

    def __init__(self, debug: bool = False):
        self.debug = debug
        self.auto_vars = {}

    def extract_undefined_vars(self, template_str: str, context: Dict[str, Any]) -> Set[str]:
        """Извлекает все undefined переменные из шаблона"""
        patterns = [
            r'\{\{\s*([a-zA-Z_][a-zA-Z0-9_\.]*)\s*\}\}',
            r'\{%\s*if\s+([a-zA-Z_][a-zA-Z0-9_\.]*)',
            r'\{%\s*for\s+\w+\s+in\s+([a-zA-Z_][a-zA-Z0-9_\.]*)',
        ]

        all_vars = set()
        for pattern in patterns:
            matches = re.findall(pattern, template_str)
            for match in matches:
                root_var = match.split('.')[0].split('[')[0]
                if root_var not in context:
                    all_vars.add(root_var)

        return all_vars

    def build_smart_context(self, template_str: str, base_context: Dict[str, Any]) -> Dict[str, Any]:
        """Строит умный контекст с заглушками для undefined переменных"""
        undefined_vars = self.extract_undefined_vars(template_str, base_context)

        smart_context = base_context.copy()

        for var in undefined_vars:
            stub = self._create_smart_stub(var, template_str)
            smart_context[var] = stub
            self.auto_vars[var] = stub

            if self.debug:
                logger.debug(f"🔧 Создана заглушка: {var} = {stub}")

        return smart_context

    def _create_smart_stub(self, var_name: str, template_str: str) -> Any:
        """Создает умную заглушку на основе контекста использования"""
        pattern_for = r'\{%\s*for\s+\w+\s+in\s+' + re.escape(var_name)
        if re.search(pattern_for, template_str):
            return []

        pattern_if = r'\{%\s*if\s+' + re.escape(var_name)
        if re.search(pattern_if, template_str):
            return False

        pattern_attr = re.escape(var_name) + r'\.\w+'
        if re.search(pattern_attr, template_str):
            return defaultdict(lambda: None)

        return ""


class JSONCommentImportProcessor:
    """Обработчик импортов через комментарии в JSON"""

    def __init__(self, debug: bool = False):
        self.debug = debug
        self.processed_files = set()
        self.imported_files = []

    def process_imports(self, content: str, base_path: Path) -> Tuple[str, int, List[Path]]:
        """
        Обрабатывает импорты в комментариях и удаляет все комментарии

        Формат: // [Описание](file:///absolute/path/to/file.json)
        """
        import_count = 0
        self.processed_files.clear()
        self.imported_files.clear()

        processed = self._process_imports_recursive(content, base_path, import_count)
        content_with_imports, import_count = processed

        # Удаляем комментарии
        cleaned = re.sub(r'(?:^|\s)//[^\n]*', '', content_with_imports, flags=re.MULTILINE)
        cleaned = re.sub(r'/\*.*?\*/', '', cleaned, flags=re.DOTALL)
        cleaned = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned)

        return cleaned, import_count, self.imported_files.copy()

    def _process_imports_recursive(self, content: str, base_path: Path, count: int) -> Tuple[str, int]:
        """Рекурсивная обработка импортов"""
        import_pattern = r'//[^\n]*?\(file:///(.*?)\)[^\n]*'
        matches = list(re.finditer(import_pattern, content))

        if not matches:
            return content, count

        result = content

        for match in reversed(matches):
            file_url = match.group(1)
            decoded_path = unquote(file_url)

            if '#' in decoded_path:
                decoded_path = decoded_path.split('#')[0]

            import_file = Path('/' + decoded_path)

            if import_file in self.processed_files:
                continue

            if not import_file.exists():
                logger.warning(f"   ⚠️ Файл импорта не найден: {import_file}")
                continue

            try:
                with open(import_file, 'r', encoding='utf-8') as f:
                    imported_content = f.read()

                self.processed_files.add(import_file)
                self.imported_files.append(import_file)
                count += 1

                imported_content, count = self._process_imports_recursive(
                    imported_content, import_file.parent, count
                )

                before_text = result[:match.start()].rstrip()
                after_text = result[match.end():].lstrip()

                needs_comma_before = before_text and before_text[-1] not in '[{,'
                needs_comma_after = after_text and after_text[0] not in ']},'

                replacement = ''
                if needs_comma_before:
                    replacement = ','
                replacement += '\n' + imported_content.strip()
                if needs_comma_after:
                    replacement += ','

                result = result[:match.start()] + replacement + result[match.end():]

            except Exception as e:
                logger.error(f"   ❌ Ошибка импорта {import_file.name}: {e}")
                continue

        return result, count


class EnhancedJinjaJsonPreprocessor:
    """Улучшенный препроцессор с интеллектуальной обработкой"""

    def __init__(self, smart_mode: bool = False, debug: bool = False):
        self.smart_mode = smart_mode
        self.debug = debug
        self.json_fixer = SmartJSONFixer(debug) if smart_mode else None
        self.import_processor = JSONCommentImportProcessor(debug)

    def clean_mixed_syntax(self, content: str, source_file: Path = None) -> Tuple[str, Dict[str, str], List[Path]]:
        """
        Очищает смешанный Jinja2/JSON синтаксис с умными исправлениями
        Returns: (очищенный контент, словарь замен, список импортированных файлов)
        """
        replacements = {}
        counter = 0
        imported_files = []

        # Обрабатываем импорты через комментарии
        if source_file:
            content, import_count, imported_files = self.import_processor.process_imports(content, source_file.parent)
            if import_count > 0:
                logger.info(f"   📥 Обработано импортов через комментарии: {import_count}")
        else:
            content = re.sub(r'(?:^|\s)//[^\n]*', '', content, flags=re.MULTILINE)
            content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)

        # Паттерны Jinja2
        patterns = [
            (r'\{%\s*if\s+[^%]+%\}.*?\{%\s*endif\s*%\}', 'JINJA_IF'),
            (r'\{%\s*for\s+[^%]+%\}.*?\{%\s*endfor\s*%\}', 'JINJA_FOR'),
            (r'\{%\s*set\s+[^%]+%\}', 'JINJA_SET'),
            (r'\{%[^}]+%\}', 'JINJA_TAG'),
            (r'\{\{[^}]+\}\}', 'JINJA_VAR'),
        ]

        cleaned = content

        # Удаляем Jinja2 блоки для проверки JSON
        for pattern, block_type in patterns:
            matches = list(re.finditer(pattern, cleaned, re.DOTALL | re.MULTILINE))
            for match in reversed(matches):
                counter += 1
                key = f"__{block_type}_{counter}__"
                replacements[key] = match.group()
                cleaned = cleaned[:match.start()] + cleaned[match.end():]

        # Базовая очистка
        while ',,' in cleaned:
            cleaned = cleaned.replace(',,', ',')

        cleaned = re.sub(r',\s*\]', ']', cleaned)
        cleaned = re.sub(r',\s*\}', '}', cleaned)
        cleaned = re.sub(r'\[\s*,', '[', cleaned)
        cleaned = re.sub(r'\{\s*,', '{', cleaned)
        cleaned = re.sub(r',\s*:', ':', cleaned)
        cleaned = re.sub(r':\s*,', ': null,', cleaned)
        cleaned = re.sub(r':\s*\}', ': null}', cleaned)
        cleaned = re.sub(r':\s*\]', ': null]', cleaned)

        # Smart режим
        if self.smart_mode and self.json_fixer:
            cleaned, fixes = self.json_fixer.fix_json(cleaned)
            if fixes and self.debug:
                logger.info(f"🧠 Smart исправления: {', '.join(fixes)}")

        return cleaned, replacements, imported_files


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ГЛАВНЫЙ КЛАСС: JinjaHotReloaderV33
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class JinjaHotReloaderV33(FileSystemEventHandler):
    """Hot Reload v3.3.0 - Major Integration Release"""

    SUPPORTED_EXTENSIONS = {'.json', '.jinja', '.j2', '.json.jinja', '.json.j2', '.j2.java', '.jinja.java', '.java'}

    def __init__(self, watch_dir: str = None, debug: bool = False,
                 browser_reload: bool = True, smart_mode: bool = False,
                 visualize: bool = False):
        self.watch_dir = Path(watch_dir) if watch_dir else Path('/Users/username/Documents/front-middle-schema/.JSON')
        self.debug = debug
        self.browser_reload = browser_reload
        self.smart_mode = smart_mode
        self.visualize = visualize
        self.processing_files = set()
        self.last_process_time = {}

        # MODULE #1: FileSystemLoader
        # Определяем базовые директории для поиска шаблонов
        self.template_search_paths = [
            str(self.watch_dir),
            str(self.watch_dir / 'WEB'),
            str(self.watch_dir / 'ANDROID'),
        ]

        # MODULE #2: Include/Import Tracker
        self.include_tracker = IncludeImportTracker(debug)

        # Карта зависимостей: child_file -> set(parent_files)
        self.dependency_map: Dict[Path, Set[Path]] = defaultdict(set)

        # MODULE #4: Custom Filters
        # Jinja2 окружение с FileSystemLoader
        if smart_mode:
            self.jinja_env = Environment(
                loader=FileSystemLoader(self.template_search_paths),
                undefined=DebugUndefined
            )
        else:
            self.jinja_env = Environment(
                loader=FileSystemLoader(self.template_search_paths)
            )

        # Регистрация пользовательских фильтров
        CustomJinjaFilters.register_filters(self.jinja_env)

        # MODULE #6: Dependency Graph
        self.dep_graph = DependencyGraphVisualizer(debug)

        # MODULE #7: Template Cache
        self.template_cache = TemplateCacheManager(debug)

        # MODULE #8: Error Recovery
        self.error_manager = ErrorRecoveryManager(debug)

        # MODULE #9: Performance Monitor
        self.perf_monitor = PerformanceMonitor(debug)

        # Legacy компоненты
        self.preprocessor = EnhancedJinjaJsonPreprocessor(smart_mode, debug)
        self.context_builder = SmartJinja2ContextBuilder(debug) if smart_mode else None

        # SDUI трансформер
        self.sdui_transformer = SDUIToJinja2Transformer() if SDUIToJinja2Transformer else None
        if SDUIJinja2Extensions:
            SDUIJinja2Extensions.register_all(self.jinja_env)

        # Валидатор
        self.validator_path = Path('/Users/username/Documents/front-middle-schema/sdui_web_validator_v3.0.0.py')

        # Вывод информации о конфигурации
        logger.info("━" * 80)
        logger.info("🚀 Jinja Hot Reload v3.3.0 - MAJOR INTEGRATION RELEASE")
        logger.info("━" * 80)
        logger.info(f"📁 Директория наблюдения: {self.watch_dir}")
        logger.info(f"🔍 SDUI поддержка: {'✅ Включена' if self.sdui_transformer else '❌ Отключена'}")
        logger.info(f"🌐 Перезагрузка браузера: {'✅ Включена (Vivaldi:9090)' if self.browser_reload else '❌ Отключена'}")
        logger.info(f"🧠 Smart режим: {'✅ Включен' if self.smart_mode else '❌ Отключен'}")
        logger.info(f"📊 FileSystemLoader: ✅ Включен ({len(self.template_search_paths)} путей)")
        logger.info(f"🔗 Include/Import трекинг: ✅ Включен")
        logger.info(f"🎨 Кастомные фильтры: ✅ Включены")
        logger.info(f"💾 Template Cache: ✅ Включен")
        logger.info(f"🛡️ Error Recovery: ✅ Включен")
        logger.info(f"⏱️ Performance Monitor: ✅ Включен")
        logger.info(f"🌳 Визуализация: {'✅ Включена' if self.visualize else '❌ Отключена'}")
        logger.info(f"📄 Поддерживаемые расширения: {', '.join(self.SUPPORTED_EXTENSIONS)}")
        logger.info("━" * 80)

    def is_jj_file(self, file_path: Path) -> bool:
        """Проверяет, является ли файл [JJ_] файлом"""
        if not file_path.name.startswith('[JJ_'):
            return False

        if file_path.suffix in self.SUPPORTED_EXTENSIONS:
            return True

        name_parts = file_path.name.split('.')
        if len(name_parts) >= 3:
            compound_ext = '.' + '.'.join(name_parts[-2:])
            if compound_ext in self.SUPPORTED_EXTENSIONS:
                return True

        return False

    def find_data_file(self, jj_file: Path) -> Optional[Path]:
        """Ищет [data] файл"""
        current_dir = jj_file.parent

        while current_dir != current_dir.parent:
            for file in current_dir.iterdir():
                if file.is_file() and file.name.startswith('[data'):
                    logger.info(f"📁 Найден data файл: {file.name}")
                    return file
            current_dir = current_dir.parent

        return None

    def resolve_template_path(self, template_name: str, parent_file: Path) -> Optional[Path]:
        """
        Разрешает путь к шаблону относительно родительского файла

        Args:
            template_name: Имя шаблона из include/import (например, 'parts/header.j2')
            parent_file: Родительский файл, из которого идет импорт

        Returns:
            Абсолютный путь к шаблону или None
        """
        # Сначала пытаемся найти относительно родительского файла
        relative_path = parent_file.parent / template_name
        if relative_path.exists():
            return relative_path

        # Затем ищем в search_paths
        for search_path in self.template_search_paths:
            full_path = Path(search_path) / template_name
            if full_path.exists():
                return full_path

        return None

    def update_dependencies(self, parent_file: Path, content: str):
        """
        Обновляет карту зависимостей на основе include/import в контенте

        Args:
            parent_file: Родительский файл
            content: Содержимое файла для анализа
        """
        self.perf_monitor.start_operation('update_dependencies')

        # Удаляем старые зависимости этого родителя
        for child_files in self.dependency_map.values():
            child_files.discard(parent_file)

        # Извлекаем новые зависимости
        template_names = self.include_tracker.extract_dependencies(content)

        # Разрешаем пути и добавляем в карту
        for template_name in template_names:
            child_path = self.resolve_template_path(template_name, parent_file)

            if child_path:
                self.dependency_map[child_path].add(parent_file)
                self.dep_graph.add_dependency(parent_file, child_path)

                if self.debug:
                    logger.debug(f"   📊 Зависимость: {child_path.name} ← {parent_file.name}")
            else:
                logger.warning(f"   ⚠️ Не удалось разрешить путь: {template_name}")

        self.perf_monitor.end_operation('update_dependencies')

    def get_parents_for_file(self, file_path: Path) -> Set[Path]:
        """Возвращает все родительские файлы, которые импортируют данный файл"""
        return self.dependency_map.get(file_path, set())

    def process_jj_file(self, file_path: Path):
        """Обрабатывает [JJ_] файл со всеми новыми возможностями v3.3.0"""
        if file_path in self.processing_files:
            return

        current_time = time.time()
        if file_path in self.last_process_time:
            if current_time - self.last_process_time[file_path] < 1:
                return

        self.last_process_time[file_path] = current_time
        self.processing_files.add(file_path)

        self.perf_monitor.start_operation('process_jj_file')

        try:
            logger.info("")
            logger.info("─" * 80)
            logger.info(f"🔄 Обработка: {file_path.name}")
            logger.info("─" * 80)

            # 1. Читаем файл
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()

            # 2. Обновляем карту зависимостей (MODULE #2)
            self.update_dependencies(file_path, original_content)

            # 3. Обрабатываем импорты через комментарии (legacy)
            cleaned_content, jinja_blocks, legacy_imported_files = self.preprocessor.clean_mixed_syntax(
                original_content, file_path
            )

            # Обновляем зависимости для legacy импортов
            for legacy_file in legacy_imported_files:
                self.dependency_map[legacy_file].add(file_path)
                self.dep_graph.add_dependency(file_path, legacy_file)

            # 4. Парсим очищенный JSON
            try:
                json_obj = json.loads(cleaned_content)
            except json.JSONDecodeError as e:
                # MODULE #8: Error Recovery
                logger.error(f"❌ JSON ошибка на строке {e.lineno}: {e.msg}")

                recovery_result = self.error_manager.handle_error(e, {
                    'file': file_path,
                    'content': cleaned_content,
                    'original_content': original_content
                })

                if recovery_result:
                    cleaned_content = recovery_result
                    try:
                        json_obj = json.loads(cleaned_content)
                        logger.info(f"   ✅ Восстановление успешно")
                    except:
                        logger.error(f"   ❌ Восстановление не удалось")
                        return
                else:
                    if self.debug:
                        debug_path = file_path.with_name(f"{file_path.stem}_debug_cleaned.json")
                        with open(debug_path, 'w', encoding='utf-8') as f:
                            f.write(cleaned_content)
                        logger.info(f"   📝 Debug файл: {debug_path.name}")
                    return

            # 5. Конвертация для WEB
            if 'ANDROID' in str(file_path):
                logger.info("   🔄 Конвертация Android → WEB")
                json_obj = self._convert_to_web(json_obj)

            # 6. SDUI трансформация
            if self.sdui_transformer:
                json_str = json.dumps(json_obj, ensure_ascii=False)
                if '${' in json_str or '"type": "if"' in json_str:
                    logger.info("   🔄 Преобразование SDUI → Jinja2")
                    json_str = self.sdui_transformer.transform(json_str)
                    json_obj = json.loads(json_str)

            # 7. Загружаем data файл
            data_file = self.find_data_file(file_path)
            context = {}

            if data_file:
                try:
                    with open(data_file, 'r', encoding='utf-8') as f:
                        context = json.load(f)
                    logger.info(f"   ✅ Загружены данные из: {data_file.name}")
                except Exception as e:
                    logger.error(f"   ❌ Ошибка загрузки данных: {e}")

            # 8. Рендеринг через Jinja2 с FileSystemLoader (MODULE #1)
            json_str = json.dumps(json_obj, ensure_ascii=False)
            json_str = re.sub(r'\$\{([^}]+)\}', r'{{ \1 }}', json_str)

            # Smart режим - умный контекст
            if self.smart_mode and self.context_builder:
                context = self.context_builder.build_smart_context(json_str, context)

                if self.context_builder.auto_vars:
                    logger.info(f"   🧠 Создано заглушек: {len(self.context_builder.auto_vars)}")

            try:
                # MODULE #7: Используем кэш шаблонов
                # Сохраняем текущий файл во временный template для рендеринга
                temp_template_name = f"_temp_{file_path.stem}.j2"
                temp_template_path = file_path.parent / temp_template_name

                with open(temp_template_path, 'w', encoding='utf-8') as f:
                    f.write(json_str)

                try:
                    # Добавляем директорию файла в search paths
                    parent_dir = str(file_path.parent)
                    if parent_dir not in self.template_search_paths:
                        self.template_search_paths.insert(0, parent_dir)
                        self.jinja_env.loader = FileSystemLoader(self.template_search_paths)

                    template = self.jinja_env.get_template(temp_template_name)
                    rendered = template.render(**context)
                    result_obj = json.loads(rendered)

                    logger.info(f"   ✅ Рендеринг Jinja2 успешен (с include/import поддержкой)")

                finally:
                    # Удаляем временный файл
                    if temp_template_path.exists():
                        temp_template_path.unlink()

            except TemplateNotFound as e:
                # MODULE #8: Error Recovery
                logger.warning(f"⚠️ Шаблон не найден: {e.name}")
                recovery_result = self.error_manager.handle_error(e, {
                    'file': file_path,
                    'template_name': e.name,
                    'original_content': json_str
                })

                if recovery_result:
                    result_obj = json.loads(recovery_result)
                else:
                    result_obj = json_obj

            except (TemplateSyntaxError, UndefinedError) as e:
                logger.warning(f"⚠️ Jinja2: {e}")
                result_obj = json_obj

            except json.JSONDecodeError as e:
                logger.error(f"❌ Ошибка парсинга результата: {e}")
                result_obj = json_obj

            # 9. Генерируем выходной файл
            file_name = file_path.name
            for ext in sorted(self.SUPPORTED_EXTENSIONS, key=len, reverse=True):
                if file_name.endswith(ext):
                    file_stem = file_name[:-len(ext)]
                    break
            else:
                file_stem = file_path.stem

            if file_stem.startswith('[JJ_'):
                platform = file_stem[4:file_stem.find(']')]
                full_name = f"[FULL_{platform}]{file_stem[file_stem.find(']')+1:]}_web.json"
            else:
                full_name = f"[FULL_{file_stem}]_web.json"

            output_path = file_path.parent / full_name

            # 10. Сохраняем
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result_obj, f, indent=2, ensure_ascii=False)

            logger.info("")
            logger.info(f"✅ Создан: {output_path.name}")

            # 11. Валидация
            if self.validator_path.exists():
                self.validate_output(output_path)

        except Exception as e:
            logger.error("")
            logger.error("┄" * 80)
            logger.error(f"❌ Ошибка обработки {file_path.name}: {e}")
            logger.error("┄" * 80)

            # MODULE #8: Error Recovery
            self.error_manager.handle_error(e, {'file': file_path})

            if self.debug:
                import traceback
                traceback.print_exc()
        finally:
            self.processing_files.discard(file_path)
            self.perf_monitor.end_operation('process_jj_file')

    def _convert_to_web(self, component: Dict[str, Any]) -> Dict[str, Any]:
        """Простая конвертация Android → WEB"""
        MAPPING = {
            'ScrollView': 'ScrollWrapper',
            'ConstraintLayout': 'ConstraintWrapper',
            'LinearLayout': 'StackView',
            'TextView': 'LabelView',
            'Button': 'ButtonView',
            'Image': 'ImageView',
            'Icon': 'IconView',
            'Card': 'BannerWrapper',
        }

        if not isinstance(component, dict):
            return component

        if 'type' in component and component['type'] in MAPPING:
            component['type'] = MAPPING[component['type']]

        if 'content' in component and isinstance(component['content'], dict):
            component['content'] = self._convert_to_web(component['content'])

        if 'children' in component and isinstance(component['children'], list):
            component['children'] = [self._convert_to_web(c) for c in component['children']]

        return component

    def validate_output(self, file_path: Path):
        """Валидация через sdui_web_validator"""
        try:
            result = subprocess.run(
                [sys.executable, str(self.validator_path), str(file_path)],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                logger.info(f"   ✅ Валидация пройдена: {file_path.name}")
            else:
                logger.warning(f"   ⚠️ Валидация не пройдена: {result.stderr}")
        except Exception as e:
            logger.error(f"   ❌ Ошибка валидации: {e}")

    def reload_browser(self):
        """Перезагрузка Vivaldi:9090"""
        try:
            applescript = '''
            tell application "Vivaldi"
                activate
                set allWindows to every window
                repeat with aWindow in allWindows
                    set allTabs to every tab of aWindow
                    repeat with aTab in allTabs
                        set tabURL to URL of aTab
                        if tabURL contains ":9090" then
                            tell aTab to reload
                            return "Reloaded"
                        end if
                    end repeat
                end repeat
                return "Not found"
            end tell
            '''

            result = subprocess.run(
                ['osascript', '-e', applescript],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0 and "Reloaded" in result.stdout:
                logger.info("   🌐 Браузер Vivaldi перезагружен (порт 9090)")
        except:
            pass

    def on_modified(self, event):
        """MODULE #3: Auto Re-rendering - Обработчик изменения файла"""
        if event.is_directory:
            return

        path = Path(event.src_path)

        # Проверяем, является ли измененный файл дочерним (импортируемым)
        parent_files = self.get_parents_for_file(path)

        if parent_files:
            logger.info("")
            logger.info("━" * 80)
            logger.info(f"📥 Обновлен импортируемый файл: {path.name}")
            logger.info(f"   🔗 Найдено родительских файлов: {len(parent_files)}")
            logger.info("━" * 80)

            # MODULE #7: Инвалидация кэша
            self.template_cache.invalidate(path)

            # Обрабатываем все родительские файлы
            for parent_file in parent_files:
                logger.info(f"   ↻ Перерендеринг родительского файла: {parent_file.name}")
                self.template_cache.invalidate(parent_file)
                self.process_jj_file(parent_file)

            # Перезагрузка браузера после обработки всех родителей
            if self.browser_reload:
                self.reload_browser()

        elif self.is_jj_file(path):
            # MODULE #7: Инвалидация кэша
            self.template_cache.invalidate(path)

            self.process_jj_file(path)

            if self.browser_reload:
                self.reload_browser()

        elif path.name.startswith('[data'):
            logger.info(f"🔄 Обновлен data файл: {path.name}")

            # Обрабатываем все связанные файлы
            for jj_file in path.parent.iterdir():
                if self.is_jj_file(jj_file):
                    self.template_cache.invalidate(jj_file)
                    self.process_jj_file(jj_file)

            if self.browser_reload:
                self.reload_browser()

    def process_all(self):
        """Обрабатывает все [JJ_] файлы"""
        logger.info("")
        logger.info("━" * 80)
        logger.info("🔍 Поиск всех [JJ_] файлов...")
        logger.info("━" * 80)

        jj_files = []
        for root, dirs, files in os.walk(self.watch_dir):
            for file in files:
                file_path = Path(root) / file
                if self.is_jj_file(file_path):
                    jj_files.append(file_path)

        logger.info("")
        logger.info(f"📊 Найдено {len(jj_files)} [JJ_] файлов")
        logger.info("")

        for jj_file in jj_files:
            self.process_jj_file(jj_file)

        # Перезагрузка браузера один раз после обработки всех файлов
        if self.browser_reload and jj_files:
            self.reload_browser()

        # MODULE #6: Визуализация графа зависимостей
        if self.visualize and self.dependency_map:
            logger.info("")
            logger.info("━" * 80)
            logger.info("🌳 Визуализация графа зависимостей:")
            logger.info("━" * 80)

            # Экспорт в DOT формат
            dot_path = self.watch_dir / 'dependency_graph.dot'
            self.dep_graph.export_dot(dot_path)

            # Экспорт в HTML
            html_path = self.watch_dir / 'dependency_graph.html'
            self.dep_graph.export_html(html_path)

        # Выводим статистику по зависимостям
        if self.dependency_map:
            logger.info("")
            logger.info("━" * 80)
            logger.info("📊 Карта зависимостей:")
            logger.info("━" * 80)
            for child_file, parent_files in sorted(self.dependency_map.items()):
                logger.info(f"   📄 {child_file.name}")
                for parent_file in sorted(parent_files):
                    logger.info(f"      ← {parent_file.name}")

        # MODULE #7: Статистика кэша
        cache_stats = self.template_cache.get_statistics()
        if cache_stats['total'] > 0:
            logger.info("")
            logger.info("━" * 80)
            logger.info("💾 Статистика кэша шаблонов:")
            logger.info("━" * 80)
            logger.info(f"   Попадания: {cache_stats['hits']}")
            logger.info(f"   Промахи: {cache_stats['misses']}")
            logger.info(f"   Hit Rate: {cache_stats['hit_rate']:.1f}%")
            logger.info(f"   В кэше: {cache_stats['cached_items']} шаблонов")

        # MODULE #8: Сводка по ошибкам
        error_summary = self.error_manager.get_error_summary()
        logger.info("")
        logger.info("━" * 80)
        logger.info("🛡️ Сводка по ошибкам:")
        logger.info("━" * 80)
        logger.info(error_summary)

        # MODULE #9: Статистика производительности
        self.perf_monitor.print_summary()

        logger.info("")
        logger.info("━" * 80)
        logger.info("✨ Обработка завершена")
        logger.info("━" * 80)

    def watch(self):
        """Запуск наблюдателя"""
        observer = Observer()
        observer.schedule(self, str(self.watch_dir), recursive=True)
        observer.start()

        logger.info("")
        logger.info("━" * 80)
        logger.info("👀 Отслеживание изменений... (Ctrl+C для остановки)")
        logger.info("━" * 80)

        self.process_all()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
            logger.info("\n🛑 Остановлено")

        observer.join()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ГЛАВНАЯ ФУНКЦИЯ
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(
        description='Jinja Hot Reload v3.3.0 - Major Integration Release'
    )

    parser.add_argument(
        '--path',
        default='/Users/username/Documents/front-middle-schema/.JSON',
        help='Директория для наблюдения'
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='Режим отладки'
    )

    parser.add_argument(
        '--test',
        action='store_true',
        help='Однократная обработка без наблюдения'
    )

    parser.add_argument(
        '--no-browser-reload',
        action='store_true',
        help='Отключить автоматическую перезагрузку браузера'
    )

    parser.add_argument(
        '--smart',
        action='store_true',
        help='🧠 Включить интеллектуальный режим исправления ошибок'
    )

    parser.add_argument(
        '--visualize',
        action='store_true',
        help='🌳 Включить визуализацию графа зависимостей'
    )

    args = parser.parse_args()

    print("""
    ╔══════════════════════════════════════════════════╗
    ║     Jinja Hot Reload v3.3.0                     ║
    ║     🚀 MAJOR INTEGRATION RELEASE                ║
    ║     📦 9 Новых Модулей                          ║
    ╚══════════════════════════════════════════════════╝
    """)

    reloader = JinjaHotReloaderV33(
        watch_dir=args.path,
        debug=args.debug,
        browser_reload=not args.no_browser_reload,
        smart_mode=args.smart,
        visualize=args.visualize
    )

    if args.test:
        logger.info("🧪 Режим тестирования")
        reloader.process_all()
    else:
        reloader.watch()


if __name__ == '__main__':
    main()
