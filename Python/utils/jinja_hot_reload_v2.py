#!/usr/bin/env python3
"""
Jinja2 JSON Template Hot Reload Monitor v2.0.0
Мониторинг и обработка Jinja2 шаблонов в JSON файлах с автоматической подстановкой данных
"""

import os
import sys
import json
import time
import logging
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Set, Tuple
from collections import defaultdict

import jinja2
from jinja2 import Template, Environment, FileSystemLoader, TemplateSyntaxError
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class JinjaJsonProcessor:
    """Процессор для обработки JSON файлов с Jinja2 шаблонами"""

    def __init__(self, base_path: str):
        """
        Инициализация процессора

        Args:
            base_path: Базовый путь для мониторинга
        """
        self.base_path = Path(base_path)
        self.processed_files: Set[str] = set()
        self.data_cache: Dict[str, Dict] = {}
        self.last_process_time: Dict[str, float] = {}

        # Настройка Jinja2 окружения
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.base_path)),
            undefined=jinja2.StrictUndefined,  # Строгий режим для undefined переменных
            trim_blocks=True,
            lstrip_blocks=True
        )

        # Добавляем кастомные фильтры
        self._setup_custom_filters()

    def _setup_custom_filters(self):
        """Настройка кастомных фильтров для Jinja2"""
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

        self.jinja_env.filters['safe_get'] = safe_get
        self.jinja_env.filters['format_date'] = format_date

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
            # Ищем все файлы с префиксом [data]
            data_files = list(current_dir.glob('[data]*.json'))

            if data_files:
                # Возвращаем первый найденный [data] файл
                logger.info(f"📁 Найден data файл: {data_files[0]}")
                return data_files[0]

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
        Рекурсивная обработка JSON объекта с Jinja2 шаблонами

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

    def generate_output_filename(self, jj_file_path: Path) -> Path:
        """
        Генерация имени выходного [FULL_] файла

        Args:
            jj_file_path: Путь к [JJ_] файлу

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
                new_filename = f'[FULL_{prefix_content}]{rest_of_name}'
            else:
                new_filename = filename.replace('[JJ_', '[FULL_')
        else:
            new_filename = f'[FULL]{filename}'

        # Возвращаем путь в той же директории
        return jj_file_path.parent / new_filename

    def process_jj_file(self, jj_file_path: Path) -> bool:
        """
        Обработка [JJ_] файла

        Args:
            jj_file_path: Путь к [JJ_] файлу

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

            # Обрабатываем JSON с Jinja2 шаблонами
            processed_json = self.process_json_with_jinja(template_json, context)

            # Генерируем путь к выходному файлу
            output_path = self.generate_output_filename(jj_file_path)

            # Сохраняем результат
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(processed_json, f, ensure_ascii=False, indent=2)

            logger.info(f"✅ Создан: {output_path.name}")

            # Добавляем в список обработанных
            self.processed_files.add(str(jj_file_path))

            return True

        except json.JSONDecodeError as e:
            logger.error(f"❌ Ошибка парсинга JSON в {jj_file_path}: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Ошибка обработки {jj_file_path}: {e}")
            logger.debug(traceback.format_exc())
            return False

    def process_all_jj_files(self):
        """Обработка всех существующих [JJ_] файлов"""
        logger.info("🔍 Поиск всех [JJ_] файлов...")

        jj_files = list(self.base_path.rglob('[JJ_*.json'))

        if not jj_files:
            logger.warning("⚠️ [JJ_] файлы не найдены")
            return

        logger.info(f"📊 Найдено {len(jj_files)} [JJ_] файлов")

        success_count = 0
        for jj_file in jj_files:
            if self.process_jj_file(jj_file):
                success_count += 1

        logger.info(f"✅ Успешно обработано: {success_count}/{len(jj_files)} файлов")


class JinjaJsonWatcher(FileSystemEventHandler):
    """Обработчик событий файловой системы для мониторинга [JJ_] файлов"""

    def __init__(self, processor: JinjaJsonProcessor):
        """
        Инициализация обработчика

        Args:
            processor: Экземпляр JinjaJsonProcessor
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

        # Находим все [JJ_] файлы в поддиректориях
        search_dir = data_file_path.parent
        jj_files = list(search_dir.rglob('[JJ_*.json'))

        if jj_files:
            logger.info(f"♻️ Переобработка {len(jj_files)} зависимых файлов...")
            for jj_file in jj_files:
                # Проверяем, что этот JJ файл действительно использует этот data файл
                if self.processor.find_data_file(jj_file) == data_file_path:
                    self.processor.process_jj_file(jj_file)


class JinjaHotReloadMonitor:
    """Главный класс для мониторинга и горячей перезагрузки"""

    def __init__(self, base_path: str):
        """
        Инициализация монитора

        Args:
            base_path: Базовый путь для мониторинга
        """
        self.base_path = Path(base_path)

        if not self.base_path.exists():
            raise ValueError(f"Путь не существует: {base_path}")

        self.processor = JinjaJsonProcessor(base_path)
        self.watcher = JinjaJsonWatcher(self.processor)
        self.observer = Observer()

    def start(self):
        """Запуск мониторинга"""
        logger.info("=" * 60)
        logger.info("🚀 Запуск Jinja JSON Hot Reload Monitor v2.0.0")
        logger.info(f"📁 Базовая директория: {self.base_path}")
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

        # Выводим статистику
        logger.info(f"📊 Обработано файлов за сессию: {len(self.processor.processed_files)}")
        logger.info(f"💾 Файлов в кэше данных: {len(self.processor.data_cache)}")
        logger.info("✅ Мониторинг остановлен")
        logger.info("=" * 60)


def main():
    """Главная функция"""
    # Базовый путь для мониторинга
    BASE_PATH = "/Users/username/Documents/front-middle-schema/.JSON"

    # Проверка наличия необходимых библиотек
    try:
        import jinja2
        from watchdog.observers import Observer
    except ImportError as e:
        logger.error(f"❌ Отсутствует необходимая библиотека: {e}")
        logger.info("📦 Установите зависимости: pip install jinja2 watchdog")
        sys.exit(1)

    try:
        # Создаём и запускаем монитор
        monitor = JinjaHotReloadMonitor(BASE_PATH)
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