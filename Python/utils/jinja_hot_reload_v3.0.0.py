#!/usr/bin/env python3
"""
Jinja2 JSON Template Hot Reload Monitor v3.0.0
Мониторинг и обработка Jinja2 шаблонов в JSON файлах с поддержкой SDUI преобразований
"""

import os
import sys
import json
import time
import logging
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Set, Tuple, List
from collections import defaultdict
from enum import Enum

import jinja2
from jinja2 import Template, Environment, FileSystemLoader, TemplateSyntaxError
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent

# Импорт SDUI модулей
from sdui_to_jinja2_transformer import SDUIToJinja2Transformer
from sdui_jinja_extensions import (
    SDUIConditionalExtension,
    SDUILoopExtension,
    create_sdui_filters,
    create_sdui_tests,
    create_sdui_globals
)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class ProcessingMode(Enum):
    """Режимы обработки файлов"""
    JINJA_ONLY = "jinja_only"  # Только Jinja2 обработка
    SDUI_ONLY = "sdui_only"    # Только SDUI преобразование
    SDUI_THEN_JINJA = "sdui_then_jinja"  # Сначала SDUI, потом Jinja2
    AUTO_DETECT = "auto_detect"  # Автоопределение


class SDUIJinjaJsonProcessor:
    """Процессор для обработки JSON файлов с SDUI и Jinja2 шаблонами"""

    def __init__(self, base_path: str, sdui_mapping_file: Optional[str] = None):
        """
        Инициализация процессора

        Args:
            base_path: Базовый путь для мониторинга
            sdui_mapping_file: Путь к файлу маппинга SDUI→Jinja2
        """
        self.base_path = Path(base_path)
        self.processed_files: Set[str] = set()
        self.data_cache: Dict[str, Dict] = {}
        self.last_process_time: Dict[str, float] = {}
        self.processing_stats: Dict[str, Dict] = defaultdict(lambda: {
            'sdui_transformations': 0,
            'jinja_renders': 0,
            'errors': 0,
            'warnings': []
        })

        # Инициализация SDUI трансформера
        self.sdui_transformer = SDUIToJinja2Transformer(sdui_mapping_file)

        # Настройка Jinja2 окружения с SDUI расширениями
        self.jinja_env = self._setup_jinja_environment()

    def _setup_jinja_environment(self) -> Environment:
        """Настройка Jinja2 окружения с SDUI расширениями"""
        env = Environment(
            loader=FileSystemLoader(str(self.base_path)),
            undefined=jinja2.StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True,
            extensions=[SDUIConditionalExtension, SDUILoopExtension]
        )

        # Добавляем SDUI фильтры
        sdui_filters = create_sdui_filters()
        for name, filter_func in sdui_filters.items():
            env.filters[name] = filter_func

        # Добавляем SDUI тесты
        sdui_tests = create_sdui_tests()
        for name, test_func in sdui_tests.items():
            env.tests[name] = test_func

        # Добавляем SDUI глобальные функции
        sdui_globals = create_sdui_globals()
        for name, global_func in sdui_globals.items():
            env.globals[name] = global_func

        # Добавляем базовые фильтры для совместимости
        self._setup_basic_filters(env)

        return env

    def _setup_basic_filters(self, env: Environment):
        """Настройка базовых фильтров для Jinja2"""
        # Фильтр для безопасного доступа к вложенным полям
        def safe_get(obj, key, default=None):
            try:
                return obj.get(key, default) if isinstance(obj, dict) else default
            except:
                return default

        # Фильтр для форматирования дат
        def format_date(value, format='%Y-%m-%d'):
            try:
                if isinstance(value, str):
                    dt = datetime.fromisoformat(value)
                else:
                    dt = value
                return dt.strftime(format)
            except:
                return value

        env.filters['safe_get'] = safe_get
        env.filters['format_date'] = format_date

    def detect_processing_mode(self, content: Any) -> ProcessingMode:
        """
        Автоопределение режима обработки

        Args:
            content: Контент для анализа

        Returns:
            Режим обработки
        """
        has_sdui = False
        has_jinja = False

        def check_content(obj):
            nonlocal has_sdui, has_jinja

            if isinstance(obj, str):
                # Проверяем SDUI синтаксис
                if '${' in obj or (isinstance(obj, str) and obj.startswith('$')):
                    has_sdui = True
                # Проверяем Jinja2 синтаксис
                if '{{' in obj or '{%' in obj:
                    has_jinja = True

            elif isinstance(obj, dict):
                # Проверяем SDUI функции
                if 'type' in obj and isinstance(obj.get('type'), str):
                    sdui_types = ['if', 'and', 'or', 'not', 'concat', 'uppercase',
                                  'add', 'subtract', 'equals', 'length', 'join']
                    if obj['type'] in sdui_types:
                        has_sdui = True

                # Рекурсивно проверяем значения
                for value in obj.values():
                    check_content(value)

            elif isinstance(obj, list):
                for item in obj:
                    check_content(item)

        check_content(content)

        # Определяем режим
        if has_sdui and has_jinja:
            return ProcessingMode.SDUI_THEN_JINJA
        elif has_sdui:
            return ProcessingMode.SDUI_ONLY
        elif has_jinja:
            return ProcessingMode.JINJA_ONLY
        else:
            return ProcessingMode.JINJA_ONLY  # По умолчанию

    def find_data_file(self, jj_file_path: Path) -> Optional[Path]:
        """
        Поиск [data] файла в родительских директориях

        Args:
            jj_file_path: Путь к [JJ_] файлу

        Returns:
            Path к [data] файлу или None
        """
        current_dir = jj_file_path.parent

        # Поднимаемся вверх по директориям для поиска [data] файла
        while current_dir >= self.base_path.parent:
            # Используем os.listdir для поиска файлов с квадратными скобками
            try:
                files = os.listdir(current_dir)
                data_files = [
                    current_dir / f for f in files
                    if f.startswith('[data]') and f.endswith('.json')
                ]

                if data_files:
                    # Возвращаем первый найденный [data] файл
                    logger.info(f"📁 Найден data файл: {data_files[0]}")
                    return data_files[0]
            except Exception as e:
                logger.debug(f"Ошибка при поиске в {current_dir}: {e}")

            # Переходим к родительской директории
            current_dir = current_dir.parent

        logger.warning(f"⚠️ [data] файл не найден для: {jj_file_path}")
        return None

    def load_data_file(self, data_file_path: Path) -> Dict[str, Any]:
        """
        Загрузка данных из [data] файла с кэшированием

        Args:
            data_file_path: Путь к [data] файлу

        Returns:
            Словарь с данными
        """
        str_path = str(data_file_path)

        # Проверяем кэш
        if str_path in self.data_cache:
            file_mtime = data_file_path.stat().st_mtime
            if file_mtime <= self.last_process_time.get(str_path, 0):
                logger.debug(f"💾 Используем кэшированные данные: {data_file_path.name}")
                return self.data_cache[str_path]

        try:
            with open(data_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Обновляем кэш
            self.data_cache[str_path] = data
            self.last_process_time[str_path] = time.time()

            logger.info(f"✅ Загружены данные из: {data_file_path.name}")
            return data

        except json.JSONDecodeError as e:
            logger.error(f"❌ Ошибка парсинга JSON в {data_file_path}: {e}")
            return {}
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки {data_file_path}: {e}")
            return {}

    def process_sdui_transformation(self, content: Any, file_path: Path) -> Tuple[Any, List[str]]:
        """
        Этап 1: Преобразование SDUI в Jinja2

        Args:
            content: Контент для преобразования
            file_path: Путь к файлу (для логирования)

        Returns:
            Кортеж (преобразованный контент, список предупреждений)
        """
        logger.info(f"🔄 Этап 1: Преобразование SDUI→Jinja2 для {file_path.name}")

        try:
            # Преобразуем SDUI в Jinja2
            transformed = self.sdui_transformer.transform(content)

            # Валидируем результат
            is_valid, warnings = self.sdui_transformer.validate_transformation(content, transformed)

            if warnings:
                for warning in warnings:
                    logger.warning(f"⚠️ {warning}")
                self.processing_stats[str(file_path)]['warnings'].extend(warnings)

            self.processing_stats[str(file_path)]['sdui_transformations'] += 1

            if is_valid:
                logger.info(f"✅ SDUI преобразование успешно")
            else:
                logger.warning(f"⚠️ SDUI преобразование с предупреждениями")

            return transformed, warnings

        except Exception as e:
            logger.error(f"❌ Ошибка SDUI преобразования: {e}")
            self.processing_stats[str(file_path)]['errors'] += 1
            return content, [f"Ошибка преобразования: {e}"]

    def process_jinja_template(self, template_str: str, context: Dict[str, Any]) -> str:
        """
        Обработка Jinja2 шаблона в строке

        Args:
            template_str: Строка с Jinja2 шаблоном
            context: Контекст для подстановки

        Returns:
            Обработанная строка
        """
        try:
            template = Template(template_str)
            return template.render(**context)
        except TemplateSyntaxError as e:
            logger.error(f"❌ Синтаксическая ошибка в шаблоне: {e}")
            return template_str
        except Exception as e:
            logger.error(f"❌ Ошибка обработки шаблона: {e}")
            return template_str

    def process_json_with_jinja(self, json_obj: Any, context: Dict[str, Any]) -> Any:
        """
        Этап 2: Рекурсивная обработка JSON объекта с Jinja2 шаблонами

        Args:
            json_obj: JSON объект для обработки
            context: Контекст для подстановки

        Returns:
            Обработанный JSON объект
        """
        if isinstance(json_obj, dict):
            result = {}
            for key, value in json_obj.items():
                # Обрабатываем ключ
                processed_key = self.process_jinja_template(key, context) if isinstance(key, str) else key
                # Рекурсивно обрабатываем значение
                result[processed_key] = self.process_json_with_jinja(value, context)
            return result

        elif isinstance(json_obj, list):
            return [self.process_json_with_jinja(item, context) for item in json_obj]

        elif isinstance(json_obj, str):
            # Обрабатываем строку как потенциальный шаблон
            if '{{' in json_obj or '{%' in json_obj:
                processed = self.process_jinja_template(json_obj, context)

                # Пытаемся преобразовать результат в правильный тип
                if processed.lower() in ('true', 'false'):
                    return processed.lower() == 'true'
                elif processed.replace('.', '', 1).replace('-', '', 1).isdigit():
                    try:
                        return int(processed) if '.' not in processed else float(processed)
                    except:
                        return processed
                else:
                    return processed
            return json_obj

        else:
            return json_obj

    def generate_output_filename(self, jj_file_path: Path, suffix: str = '') -> Path:
        """
        Генерация имени выходного файла

        Args:
            jj_file_path: Путь к [JJ_] файлу
            suffix: Дополнительный суффикс для имени

        Returns:
            Path к выходному файлу
        """
        filename = jj_file_path.name

        # Заменяем префикс [JJ_*] на [FULL_*]
        if filename.startswith('[JJ_'):
            # Находим закрывающую скобку
            close_bracket = filename.find(']')
            if close_bracket != -1:
                # Извлекаем суффикс после JJ_
                prefix_content = filename[4:close_bracket]
                rest_of_name = filename[close_bracket + 1:]

                if suffix:
                    new_filename = f'[FULL_{prefix_content}_{suffix}]{rest_of_name}'
                else:
                    new_filename = f'[FULL_{prefix_content}]{rest_of_name}'
            else:
                new_filename = filename.replace('[JJ_', '[FULL_')
        else:
            prefix = f'[FULL_{suffix}]' if suffix else '[FULL]'
            new_filename = f'{prefix}{filename}'

        # Возвращаем путь в той же директории
        return jj_file_path.parent / new_filename

    def process_jj_file(self, jj_file_path: Path, mode: ProcessingMode = ProcessingMode.AUTO_DETECT) -> bool:
        """
        Обработка [JJ_] файла с поддержкой SDUI

        Args:
            jj_file_path: Путь к [JJ_] файлу
            mode: Режим обработки

        Returns:
            True если обработка успешна
        """
        logger.info(f"🔄 Обработка: {jj_file_path.name}")

        # Находим [data] файл
        data_file_path = self.find_data_file(jj_file_path)
        if not data_file_path:
            logger.error(f"❌ Не найден [data] файл для: {jj_file_path}")
            return False

        # Загружаем данные
        context = self.load_data_file(data_file_path)
        if not context:
            logger.warning(f"⚠️ Пустой контекст данных для: {jj_file_path}")

        try:
            # Загружаем шаблон JSON
            with open(jj_file_path, 'r', encoding='utf-8') as f:
                template_json = json.load(f)

            # Определяем режим обработки
            if mode == ProcessingMode.AUTO_DETECT:
                mode = self.detect_processing_mode(template_json)
                logger.info(f"🎯 Режим обработки: {mode.value}")

            processed_json = template_json
            warnings = []

            # Обрабатываем в зависимости от режима
            if mode == ProcessingMode.SDUI_THEN_JINJA:
                # Этап 1: SDUI → Jinja2
                processed_json, warnings = self.process_sdui_transformation(processed_json, jj_file_path)

                # Сохраняем промежуточный результат (для отладки)
                if logger.level <= logging.DEBUG:
                    debug_path = self.generate_output_filename(jj_file_path, 'SDUI')
                    with open(debug_path, 'w', encoding='utf-8') as f:
                        json.dump(processed_json, f, ensure_ascii=False, indent=2)
                    logger.debug(f"💾 Промежуточный SDUI результат: {debug_path.name}")

                # Этап 2: Jinja2 обработка
                logger.info(f"🔄 Этап 2: Обработка Jinja2 шаблонов")
                processed_json = self.process_json_with_jinja(processed_json, context)
                self.processing_stats[str(jj_file_path)]['jinja_renders'] += 1

            elif mode == ProcessingMode.SDUI_ONLY:
                # Только SDUI преобразование
                processed_json, warnings = self.process_sdui_transformation(processed_json, jj_file_path)

            elif mode == ProcessingMode.JINJA_ONLY:
                # Только Jinja2 обработка
                processed_json = self.process_json_with_jinja(processed_json, context)
                self.processing_stats[str(jj_file_path)]['jinja_renders'] += 1

            # Генерируем путь к выходному файлу
            output_path = self.generate_output_filename(jj_file_path)

            # Сохраняем результат
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(processed_json, f, ensure_ascii=False, indent=2)

            logger.info(f"✅ Создан: {output_path.name}")

            # Выводим статистику обработки
            if warnings:
                logger.info(f"⚠️ Обработка завершена с {len(warnings)} предупреждениями")

            # Добавляем в список обработанных
            self.processed_files.add(str(jj_file_path))

            return True

        except json.JSONDecodeError as e:
            logger.error(f"❌ Ошибка парсинга JSON в {jj_file_path}: {e}")
            self.processing_stats[str(jj_file_path)]['errors'] += 1
            return False
        except Exception as e:
            logger.error(f"❌ Ошибка обработки {jj_file_path}: {e}")
            logger.debug(traceback.format_exc())
            self.processing_stats[str(jj_file_path)]['errors'] += 1
            return False

    def process_all_jj_files(self):
        """Обработка всех существующих [JJ_] файлов"""
        logger.info("🔍 Поиск всех [JJ_] файлов...")

        # Используем os.walk для рекурсивного поиска файлов с квадратными скобками
        jj_files = []
        for root, dirs, files in os.walk(self.base_path):
            for file in files:
                if file.startswith('[JJ_') and file.endswith('.json'):
                    jj_files.append(Path(root) / file)

        if not jj_files:
            logger.warning("⚠️ [JJ_] файлы не найдены")
            return

        logger.info(f"📊 Найдено {len(jj_files)} [JJ_] файлов")

        success_count = 0
        for jj_file in jj_files:
            if self.process_jj_file(jj_file):
                success_count += 1

        logger.info(f"✅ Успешно обработано: {success_count}/{len(jj_files)} файлов")
        self.print_processing_statistics()

    def print_processing_statistics(self):
        """Вывод статистики обработки"""
        logger.info("=" * 60)
        logger.info("📊 СТАТИСТИКА ОБРАБОТКИ")
        logger.info("-" * 60)

        total_sdui = 0
        total_jinja = 0
        total_errors = 0
        total_warnings = 0

        for file_path, stats in self.processing_stats.items():
            if stats['sdui_transformations'] > 0 or stats['jinja_renders'] > 0 or stats['errors'] > 0:
                file_name = Path(file_path).name
                logger.info(f"📄 {file_name}:")
                logger.info(f"   SDUI преобразований: {stats['sdui_transformations']}")
                logger.info(f"   Jinja2 рендеров: {stats['jinja_renders']}")
                logger.info(f"   Ошибок: {stats['errors']}")
                logger.info(f"   Предупреждений: {len(stats['warnings'])}")

                total_sdui += stats['sdui_transformations']
                total_jinja += stats['jinja_renders']
                total_errors += stats['errors']
                total_warnings += len(stats['warnings'])

        logger.info("-" * 60)
        logger.info(f"ИТОГО:")
        logger.info(f"   SDUI преобразований: {total_sdui}")
        logger.info(f"   Jinja2 рендеров: {total_jinja}")
        logger.info(f"   Ошибок: {total_errors}")
        logger.info(f"   Предупреждений: {total_warnings}")

        # Статистика трансформера
        transformer_stats = self.sdui_transformer.get_statistics()
        logger.info(f"   Кэш трансформера: {transformer_stats['cache_size']} элементов")
        logger.info(f"   Версия маппинга: {transformer_stats['mapping_version']}")
        logger.info("=" * 60)


class SDUIJinjaJsonWatcher(FileSystemEventHandler):
    """Обработчик событий файловой системы для мониторинга [JJ_] файлов"""

    def __init__(self, processor: SDUIJinjaJsonProcessor):
        """
        Инициализация обработчика

        Args:
            processor: Экземпляр SDUIJinjaJsonProcessor
        """
        self.processor = processor
        self.last_event_time: Dict[str, float] = {}
        self.debounce_delay = 0.5  # Задержка для предотвращения множественных событий

    def _should_process(self, file_path: Path) -> bool:
        """
        Проверка, нужно ли обрабатывать файл

        Args:
            file_path: Путь к файлу

        Returns:
            True если файл нужно обработать
        """
        # Проверяем, что это JSON файл с префиксом [JJ_
        if not file_path.name.endswith('.json'):
            return False

        if not file_path.name.startswith('[JJ_'):
            return False

        # Debounce проверка
        str_path = str(file_path)
        current_time = time.time()

        if str_path in self.last_event_time:
            if current_time - self.last_event_time[str_path] < self.debounce_delay:
                return False

        self.last_event_time[str_path] = current_time
        return True

    def on_modified(self, event):
        """Обработка события изменения файла"""
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Проверяем [JJ_] файлы
        if self._should_process(file_path):
            logger.info(f"📝 Изменён файл: {file_path.name}")
            self.processor.process_jj_file(file_path)

        # Проверяем изменения [data] файлов
        elif file_path.name.startswith('[data]') and file_path.name.endswith('.json'):
            logger.info(f"📝 Изменён data файл: {file_path.name}")
            self._reprocess_dependent_files(file_path)

        # Проверяем изменения маппинга SDUI
        elif file_path.name == 'sdui_mapping.json':
            logger.info(f"🔄 Изменён маппинг SDUI: {file_path.name}")
            # Перезагружаем маппинг
            self.processor.sdui_transformer = SDUIToJinja2Transformer(str(file_path))
            logger.info(f"✅ Маппинг SDUI перезагружен")

    def on_created(self, event):
        """Обработка события создания файла"""
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        if self._should_process(file_path):
            logger.info(f"✨ Создан новый файл: {file_path.name}")
            # Небольшая задержка для завершения записи файла
            time.sleep(0.2)
            self.processor.process_jj_file(file_path)

    def _reprocess_dependent_files(self, data_file_path: Path):
        """
        Переобработка всех [JJ_] файлов, зависящих от изменённого [data] файла

        Args:
            data_file_path: Путь к изменённому [data] файлу
        """
        # Очищаем кэш для этого data файла
        str_path = str(data_file_path)
        if str_path in self.processor.data_cache:
            del self.processor.data_cache[str_path]

        # Очищаем кэш трансформера для новых преобразований
        self.processor.sdui_transformer.clear_cache()

        # Находим все [JJ_] файлы в поддиректориях
        search_dir = data_file_path.parent
        jj_files = list(search_dir.rglob('[JJ_*.json'))

        if jj_files:
            logger.info(f"♻️ Переобработка {len(jj_files)} зависимых файлов...")
            for jj_file in jj_files:
                # Проверяем, что этот JJ файл действительно использует этот data файл
                if self.processor.find_data_file(jj_file) == data_file_path:
                    self.processor.process_jj_file(jj_file)


class SDUIJinjaHotReloadMonitor:
    """Главный класс для мониторинга и горячей перезагрузки с поддержкой SDUI"""

    def __init__(self, base_path: str, sdui_mapping_file: Optional[str] = None):
        """
        Инициализация монитора

        Args:
            base_path: Базовый путь для мониторинга
            sdui_mapping_file: Путь к файлу маппинга SDUI→Jinja2
        """
        self.base_path = Path(base_path)

        if not self.base_path.exists():
            raise ValueError(f"Путь не существует: {base_path}")

        self.processor = SDUIJinjaJsonProcessor(base_path, sdui_mapping_file)
        self.watcher = SDUIJinjaJsonWatcher(self.processor)
        self.observer = Observer()

    def start(self):
        """Запуск мониторинга"""
        logger.info("=" * 60)
        logger.info("🚀 Запуск SDUI+Jinja JSON Hot Reload Monitor v3.0.0")
        logger.info(f"📁 Базовая директория: {self.base_path}")
        logger.info("🎯 Поддержка: SDUI преобразования + Jinja2 шаблоны")
        logger.info("=" * 60)

        # Обрабатываем существующие файлы
        self.processor.process_all_jj_files()

        # Настраиваем и запускаем observer
        self.observer.schedule(self.watcher, str(self.base_path), recursive=True)
        self.observer.start()

        logger.info("👀 Мониторинг запущен. Нажмите Ctrl+C для остановки.")
        logger.info("-" * 60)

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        """Остановка мониторинга"""
        logger.info("\n" + "=" * 60)
        logger.info("🛑 Остановка мониторинга...")

        self.observer.stop()
        self.observer.join()

        # Выводим финальную статистику
        logger.info(f"📊 Обработано файлов за сессию: {len(self.processor.processed_files)}")
        logger.info(f"💾 Файлов в кэше данных: {len(self.processor.data_cache)}")

        # Статистика трансформера
        transformer_stats = self.processor.sdui_transformer.get_statistics()
        logger.info(f"🔄 SDUI статистика:")
        logger.info(f"   Кэш преобразований: {transformer_stats['cache_size']} элементов")
        logger.info(f"   Обработано узлов: {transformer_stats['processed_nodes']}")
        logger.info(f"   Версия маппинга: {transformer_stats['mapping_version']}")

        logger.info("✅ Мониторинг остановлен")
        logger.info("=" * 60)


def main():
    """Главная функция"""
    import argparse

    # Парсинг аргументов командной строки
    parser = argparse.ArgumentParser(
        description='SDUI+Jinja2 JSON Template Hot Reload Monitor v3.0.0',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  %(prog)s                                     # Мониторинг директории по умолчанию
  %(prog)s --path /path/to/json               # Мониторинг указанной директории
  %(prog)s --mapping /path/to/mapping.json    # Использование кастомного маппинга SDUI
  %(prog)s --debug                            # Включение отладочного вывода
  %(prog)s --test                             # Однократная обработка без мониторинга
        """
    )

    parser.add_argument(
        '--path', '-p',
        default="/Users/username/Documents/front-middle-schema/.JSON",
        help='Базовая директория для мониторинга (по умолчанию: /Users/username/Documents/front-middle-schema/.JSON)'
    )

    parser.add_argument(
        '--mapping', '-m',
        default=None,
        help='Путь к файлу маппинга SDUI→Jinja2 (по умолчанию: sdui_mapping.json в директории скрипта)'
    )

    parser.add_argument(
        '--debug', '-d',
        action='store_true',
        help='Включить отладочный вывод'
    )

    parser.add_argument(
        '--test', '-t',
        action='store_true',
        help='Режим тестирования: однократная обработка без мониторинга'
    )

    args = parser.parse_args()

    # Настройка уровня логирования
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("🐛 Включён отладочный режим")

    # Проверка наличия необходимых библиотек
    try:
        import jinja2
        from watchdog.observers import Observer
    except ImportError as e:
        logger.error(f"❌ Отсутствует необходимая библиотека: {e}")
        logger.info("📦 Установите зависимости: pip install jinja2 watchdog")
        sys.exit(1)

    # Определяем путь к маппингу
    if args.mapping:
        mapping_file = Path(args.mapping)
        if not mapping_file.exists():
            logger.error(f"❌ Файл маппинга не найден: {args.mapping}")
            sys.exit(1)
    else:
        # Используем маппинг в директории скрипта
        script_dir = Path(__file__).parent
        mapping_file = script_dir / 'sdui_mapping.json'

    try:
        # Создаём монитор
        monitor = SDUIJinjaHotReloadMonitor(args.path, str(mapping_file))

        if args.test:
            # Режим тестирования: только обработка без мониторинга
            logger.info("🧪 Режим тестирования: однократная обработка")
            monitor.processor.process_all_jj_files()
            logger.info("✅ Тестирование завершено")
        else:
            # Обычный режим с мониторингом
            monitor.start()

    except ValueError as e:
        logger.error(f"❌ Ошибка конфигурации: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        logger.debug(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()