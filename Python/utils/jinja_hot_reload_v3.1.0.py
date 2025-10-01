#!/usr/bin/env python3
"""
Jinja Hot Reload v3.1.0 - Улучшенная версия с полной поддержкой SDUI и валидацией для WEB

Основные возможности:
1. Обработка смешанного Jinja2/JSON синтаксиса
2. Преобразование SDUI функций в Jinja2
3. Валидация через sdui_web_validator
4. Автоматическое исправление для WEB платформы
"""

import os
import sys
import json
import time
import re
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
import logging

# Импорт Jinja2 и watchdog
try:
    from jinja2 import Environment, Template, TemplateSyntaxError, UndefinedError
    from jinja2.exceptions import TemplateError
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileModifiedEvent
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("Установите зависимости: pip install jinja2 watchdog")
    sys.exit(1)

# Импорт модулей SDUI
sys.path.append(str(Path(__file__).parent))
try:
    from sdui_to_jinja2_transformer import SDUIToJinja2Transformer
    from sdui_jinja_extensions import SDUIJinja2Extensions
except ImportError:
    print("⚠️ SDUI модули не найдены, работа без SDUI поддержки")
    SDUIToJinja2Transformer = None
    SDUIJinja2Extensions = None

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class JinjaJsonPreprocessor:
    """Препроцессор для файлов со смешанным Jinja2/JSON синтаксисом"""

    @staticmethod
    def clean_mixed_syntax(content: str) -> Tuple[str, Dict[str, str]]:
        """
        Очищает смешанный Jinja2/JSON синтаксис
        Returns: (очищенный контент, словарь замен)
        """
        replacements = {}
        counter = 0

        # Паттерны Jinja2 которые ломают JSON (от сложных к простым)
        patterns = [
            # {% if ... %} ... {% elif %} ... {% else %} ... {% endif %}
            (r'\{%\s*if\s+[^%]+%\}.*?\{%\s*endif\s*%\}', 'JINJA_IF'),
            # {% for ... %} ... {% endfor %}
            (r'\{%\s*for\s+[^%]+%\}.*?\{%\s*endfor\s*%\}', 'JINJA_FOR'),
            # {% set ... %}
            (r'\{%\s*set\s+[^%]+%\}', 'JINJA_SET'),
            # {% ... %} (любые другие теги)
            (r'\{%[^}]+%\}', 'JINJA_TAG'),
            # {{ ... }} (переменные Jinja2)
            (r'\{\{[^}]+\}\}', 'JINJA_VAR'),
        ]

        cleaned = content

        # Удаляем Jinja2 блоки для валидного JSON
        for pattern, block_type in patterns:
            matches = list(re.finditer(pattern, cleaned, re.DOTALL | re.MULTILINE))
            for match in reversed(matches):
                counter += 1
                key = f"__{block_type}_{counter}__"
                replacements[key] = match.group()
                # Удаляем блок полностью
                cleaned = cleaned[:match.start()] + cleaned[match.end():]

        # Агрессивная очистка структурных проблем
        # 1. Удаляем множественные запятые
        while ',,' in cleaned:
            cleaned = cleaned.replace(',,', ',')

        # 2. Удаляем запятые перед закрывающими скобками
        cleaned = re.sub(r',\s*\]', ']', cleaned)
        cleaned = re.sub(r',\s*\}', '}', cleaned)

        # 3. Удаляем запятые после открывающих скобок
        cleaned = re.sub(r'\[\s*,', '[', cleaned)
        cleaned = re.sub(r'\{\s*,', '{', cleaned)

        # 4. Удаляем запятые перед двоеточием (после удаления значения)
        cleaned = re.sub(r',\s*:', ':', cleaned)

        # 5. Удаляем пустые значения после двоеточия
        cleaned = re.sub(r':\s*,', ': null,', cleaned)
        cleaned = re.sub(r':\s*\}', ': null}', cleaned)
        cleaned = re.sub(r':\s*\]', ': null]', cleaned)

        # 6. Удаляем пустые свойства
        cleaned = re.sub(r'"\w+"\s*:\s*null\s*,\s*', '', cleaned)
        cleaned = re.sub(r',\s*"\w+"\s*:\s*null\s*\}', '}', cleaned)

        return cleaned, replacements


class SDUIWebConverter:
    """Конвертер SDUI компонентов для WEB платформы"""

    # Маппинг Android компонентов на WEB аналоги
    COMPONENT_MAPPING = {
        # Android -> Web
        'ScrollView': 'ScrollWrapper',
        'ConstraintLayout': 'ConstraintWrapper',
        'LinearLayout': 'StackView',
        'TextView': 'LabelView',
        'Button': 'ButtonView',
        'Image': 'ImageView',
        'Icon': 'IconView',
        'Card': 'BannerWrapper',
    }

    @classmethod
    def convert_to_web(cls, component: Dict[str, Any]) -> Dict[str, Any]:
        """Конвертирует компонент для WEB платформы"""
        if not isinstance(component, dict):
            return component

        # Конвертируем тип компонента
        if 'type' in component:
            component_type = component['type']
            if component_type in cls.COMPONENT_MAPPING:
                component['type'] = cls.COMPONENT_MAPPING[component_type]

        # Рекурсивно обрабатываем вложенные компоненты
        if 'content' in component and isinstance(component['content'], dict):
            component['content'] = cls.convert_to_web(component['content'])

        if 'children' in component:
            if isinstance(component['children'], list):
                component['children'] = [
                    cls.convert_to_web(child) for child in component['children']
                ]

        return component


class JinjaHotReloaderV3(FileSystemEventHandler):
    """Hot Reload для Jinja2/SDUI с валидацией для WEB"""

    # Поддерживаемые расширения для [JJ_] файлов
    SUPPORTED_EXTENSIONS = {'.json', '.jinja', '.j2', '.json.jinja', '.json.j2'}

    def __init__(self, watch_dir: str = None, debug: bool = False, browser_reload: bool = True):
        self.watch_dir = Path(watch_dir) if watch_dir else Path('/Users/username/Documents/front-middle-schema/.JSON')
        self.debug = debug
        self.browser_reload = browser_reload
        self.data_cache = {}
        self.processing_files = set()
        self.last_process_time = {}

        # SDUI трансформер
        self.sdui_transformer = SDUIToJinja2Transformer() if SDUIToJinja2Transformer else None

        # Jinja2 окружение
        self.jinja_env = Environment()
        if SDUIJinja2Extensions:
            SDUIJinja2Extensions.register_all(self.jinja_env)

        # Валидатор путь
        self.validator_path = Path('/Users/username/Documents/front-middle-schema/sdui_web_validator_v3.0.0.py')

        logger.info(f"📁 Директория наблюдения: {self.watch_dir}")
        logger.info(f"🔍 SDUI поддержка: {'✅ Включена' if self.sdui_transformer else '❌ Отключена'}")
        logger.info(f"🌐 Перезагрузка браузера: {'✅ Включена (Vivaldi:9090)' if self.browser_reload else '❌ Отключена'}")
        logger.info(f"📄 Поддерживаемые расширения: {', '.join(self.SUPPORTED_EXTENSIONS)}")

    def is_jj_file(self, file_path: Path) -> bool:
        """Проверяет, является ли файл JJ_ файлом с поддерживаемым расширением"""
        if not file_path.name.startswith('[JJ_'):
            return False

        # Проверяем расширение
        # Для составных расширений типа .json.jinja проверяем последние две части
        if file_path.suffix in self.SUPPORTED_EXTENSIONS:
            return True

        # Проверка для составных расширений (.json.jinja, .json.j2)
        name_parts = file_path.name.split('.')
        if len(name_parts) >= 3:
            compound_ext = '.' + '.'.join(name_parts[-2:])
            if compound_ext in self.SUPPORTED_EXTENSIONS:
                return True

        return False

    def find_data_file(self, jj_file: Path) -> Optional[Path]:
        """Ищет [data] файл для данного [JJ_] файла"""
        current_dir = jj_file.parent

        while current_dir != current_dir.parent:
            # Ищем файлы с префиксом [data
            for file in current_dir.iterdir():
                if file.is_file() and file.name.startswith('[data'):
                    logger.info(f"📁 Найден data файл: {file.name}")
                    return file
            current_dir = current_dir.parent

        return None

    def process_jj_file(self, file_path: Path):
        """Обрабатывает [JJ_] файл"""
        if file_path in self.processing_files:
            return

        # Защита от частых обработок
        current_time = time.time()
        if file_path in self.last_process_time:
            if current_time - self.last_process_time[file_path] < 1:
                return

        self.last_process_time[file_path] = current_time
        self.processing_files.add(file_path)

        try:
            logger.info(f"🔄 Обработка: {file_path.name}")

            # 1. Читаем исходный файл
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 2. Очищаем смешанный синтаксис
            cleaned_content, jinja_blocks = JinjaJsonPreprocessor.clean_mixed_syntax(content)

            # 3. Пробуем парсить как JSON
            try:
                json_obj = json.loads(cleaned_content)
            except json.JSONDecodeError as e:
                logger.error(f"❌ Ошибка парсинга JSON на строке {e.lineno}: {e.msg}")
                logger.error(f"   Файл: {file_path.name}")
                if self.debug:
                    debug_path = file_path.with_name(f"{file_path.stem}_debug.json")
                    with open(debug_path, 'w', encoding='utf-8') as f:
                        f.write(cleaned_content)
                    logger.info(f"📝 Debug файл создан: {debug_path.name}")
                    # Показываем проблемное место
                    lines = cleaned_content.split('\n')
                    if e.lineno <= len(lines):
                        start = max(0, e.lineno - 3)
                        end = min(len(lines), e.lineno + 2)
                        logger.info(f"   Контекст ошибки (строки {start+1}-{end}):")
                        for i in range(start, end):
                            marker = " >>> " if i == e.lineno - 1 else "     "
                            logger.info(f"{marker}{i+1:4d} | {lines[i][:100]}")
                return

            # 4. Конвертируем для WEB если это Android контракт
            if 'ANDROID' in str(file_path):
                logger.info("🔄 Конвертация Android → WEB")
                json_obj = SDUIWebConverter.convert_to_web(json_obj)

            # 5. Преобразуем SDUI функции в Jinja2 если есть
            if self.sdui_transformer:
                json_str = json.dumps(json_obj, ensure_ascii=False)
                if '${' in json_str or '"type": "if"' in json_str:
                    logger.info("🔄 Преобразование SDUI → Jinja2")
                    json_str = self.sdui_transformer.transform(json_str)
                    json_obj = json.loads(json_str)

            # 6. Находим и загружаем [data] файл
            data_file = self.find_data_file(file_path)
            context = {}

            if data_file:
                try:
                    with open(data_file, 'r', encoding='utf-8') as f:
                        context = json.load(f)
                    logger.info(f"✅ Загружены данные из: {data_file.name}")
                except Exception as e:
                    logger.error(f"❌ Ошибка загрузки данных: {e}")

            # 7. Обрабатываем Jinja2 шаблоны
            json_str = json.dumps(json_obj, ensure_ascii=False)

            # Заменяем ${ на {{ для Jinja2
            json_str = re.sub(r'\$\{([^}]+)\}', r'{{ \1 }}', json_str)

            # Рендерим через Jinja2
            try:
                template = self.jinja_env.from_string(json_str)
                rendered = template.render(**context)
                result_obj = json.loads(rendered)
            except (TemplateSyntaxError, UndefinedError) as e:
                logger.warning(f"⚠️ Jinja2: {e} (используется исходный JSON)")
                result_obj = json_obj
            except json.JSONDecodeError as e:
                logger.error(f"❌ Ошибка парсинга результата: {e}")
                result_obj = json_obj

            # 8. Генерируем [FULL_] файл
            # Определяем имя выходного файла
            # Убираем все поддерживаемые расширения из имени файла
            file_name = file_path.name
            for ext in sorted(self.SUPPORTED_EXTENSIONS, key=len, reverse=True):
                if file_name.endswith(ext):
                    file_stem = file_name[:-len(ext)]
                    break
            else:
                file_stem = file_path.stem

            if file_stem.startswith('[JJ_'):
                # Заменяем JJ_ на FULL_
                platform = file_stem[4:file_stem.find(']')]
                full_name = f"[FULL_{platform}]{file_stem[file_stem.find(']')+1:]}_web.json"
            else:
                full_name = f"[FULL_{file_stem}]_web.json"

            output_path = file_path.parent / full_name

            # 9. Сохраняем результат
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result_obj, f, indent=2, ensure_ascii=False)

            logger.info(f"✅ Создан: {output_path.name}")

            # 10. Валидируем через sdui_web_validator если доступен
            if self.validator_path.exists():
                self.validate_output(output_path)

            # 11. Перезагружаем браузер Vivaldi (если включено)
            if self.browser_reload:
                self.reload_browser()

        except Exception as e:
            logger.error(f"❌ Ошибка обработки {file_path.name}: {e}")
            if self.debug:
                import traceback
                traceback.print_exc()
        finally:
            self.processing_files.discard(file_path)

    def validate_output(self, file_path: Path):
        """Валидирует выходной файл через sdui_web_validator"""
        try:
            result = subprocess.run(
                [sys.executable, str(self.validator_path), str(file_path)],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                logger.info(f"✅ Валидация пройдена: {file_path.name}")
            else:
                logger.warning(f"⚠️ Валидация не пройдена: {result.stderr}")
        except Exception as e:
            logger.error(f"❌ Ошибка валидации: {e}")

    def reload_browser(self):
        """Перезагружает страницу с портом 9090 в браузере Vivaldi"""
        try:
            # AppleScript для перезагрузки вкладки Vivaldi с портом 9090
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

            if result.returncode == 0:
                if "Reloaded" in result.stdout:
                    logger.info("🌐 Браузер Vivaldi перезагружен (порт 9090)")
                elif "Not found" in result.stdout:
                    logger.debug("ℹ️ Вкладка с портом 9090 не найдена в Vivaldi")
            else:
                logger.debug(f"⚠️ Не удалось перезагрузить браузер: {result.stderr}")

        except subprocess.TimeoutExpired:
            logger.debug("⏱️ Таймаут при попытке перезагрузки браузера")
        except Exception as e:
            logger.debug(f"ℹ️ Перезагрузка браузера недоступна: {e}")

    def on_modified(self, event):
        """Обработчик изменения файла"""
        if event.is_directory:
            return

        path = Path(event.src_path)

        # Обрабатываем только [JJ_] файлы с поддерживаемыми расширениями
        if self.is_jj_file(path):
            self.process_jj_file(path)

        # Перезагружаем data файлы
        elif path.name.startswith('[data'):
            logger.info(f"🔄 Обновлен data файл: {path.name}")
            # Переобрабатываем все [JJ_] файлы в этой директории
            for jj_file in path.parent.iterdir():
                if self.is_jj_file(jj_file):
                    self.process_jj_file(jj_file)

    def process_all(self):
        """Обрабатывает все [JJ_] файлы"""
        logger.info("🔍 Поиск всех [JJ_] файлов...")

        jj_files = []
        for root, dirs, files in os.walk(self.watch_dir):
            for file in files:
                file_path = Path(root) / file
                if self.is_jj_file(file_path):
                    jj_files.append(file_path)

        logger.info(f"📊 Найдено {len(jj_files)} [JJ_] файлов")

        for jj_file in jj_files:
            self.process_jj_file(jj_file)

        logger.info("✨ Обработка завершена")

    def watch(self):
        """Запуск наблюдателя за изменениями"""
        observer = Observer()
        observer.schedule(self, str(self.watch_dir), recursive=True)
        observer.start()

        logger.info("👀 Отслеживание изменений... (Ctrl+C для остановки)")

        # Первичная обработка
        self.process_all()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
            logger.info("\n🛑 Остановлено")

        observer.join()


def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(
        description='Jinja Hot Reload v3.1.0 - SDUI/Jinja2 обработчик с WEB валидацией'
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
        help='Отключить автоматическую перезагрузку браузера Vivaldi'
    )

    args = parser.parse_args()

    print("""
    ╔══════════════════════════════════════════════════╗
    ║     Jinja Hot Reload v3.1.0                     ║
    ║     SDUI + Jinja2 + WEB Validation              ║
    ╚══════════════════════════════════════════════════╝
    """)

    reloader = JinjaHotReloaderV3(
        watch_dir=args.path,
        debug=args.debug,
        browser_reload=not args.no_browser_reload
    )

    if args.test:
        logger.info("🧪 Режим тестирования")
        reloader.process_all()
    else:
        reloader.watch()


if __name__ == '__main__':
    main()