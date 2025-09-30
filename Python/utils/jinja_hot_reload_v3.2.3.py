#!/usr/bin/env python3
"""
Jinja Hot Reload v3.2.3 - Оптимизация перезагрузки браузера

Новые возможности в v3.2.3:
1. 🌐 Браузер перезагружается только один раз после обработки всех файлов
2. ⚡ Устранено мигание при пакетной обработке
3. 🎯 Перезагрузка только при изменении файлов пользователем

Предыдущие версии (v3.2.2):
1. 📥 Обработка импортов через комментарии file:///path/to/file
2. 🔗 Автоматическая подстановка содержимого импортируемых файлов
3. 🧹 Удаление всех комментариев из итогового JSON
4. 🔄 Поддержка вложенных импортов

Предыдущие версии (v3.2.1):
1. 📊 Улучшенное форматирование вывода с визуальными разделителями
2. 🎨 Чёткое разделение между файлами и событиями

Предыдущие версии (v3.2.0):
1. 🧠 Интеллектуальное исправление JSON структуры
2. 🔧 Автоматическое создание заглушек для undefined переменных

Запуск:
  python3 jinja_hot_reload_v3.2.3.py --smart          # Smart режим
  python3 jinja_hot_reload_v3.2.3.py --smart --debug  # Smart + Debug
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
from typing import Dict, Any, Optional, List, Tuple, Set
from collections import defaultdict
from urllib.parse import unquote, urlparse
import logging

# Импорт Jinja2 и watchdog
try:
    from jinja2 import Environment, Template, TemplateSyntaxError, UndefinedError
    from jinja2.exceptions import TemplateError
    from jinja2 import StrictUndefined, DebugUndefined
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

        # 4. Исправление неэкранированных кавычек
        fixed = self._fix_unescaped_quotes(fixed)

        # 5. Исправление дублирующихся ключей
        fixed = self._fix_duplicate_keys(fixed)

        # 6. Нормализация пробелов
        fixed = self._normalize_whitespace(fixed)

        return fixed, self.fixes_applied

    def _fix_trailing_commas(self, content: str) -> str:
        """Удаляет trailing запятые перед ] и }"""
        # Запятые перед }
        pattern1 = r',(\s*)\}'
        if re.search(pattern1, content):
            content = re.sub(pattern1, r'\1}', content)
            self.fixes_applied.append("Удалены trailing запятые перед }")

        # Запятые перед ]
        pattern2 = r',(\s*)\]'
        if re.search(pattern2, content):
            content = re.sub(pattern2, r'\1]', content)
            self.fixes_applied.append("Удалены trailing запятые перед ]")

        return content

    def _fix_missing_commas(self, content: str) -> str:
        """Добавляет отсутствующие запятые между элементами"""
        # Между объектами в массиве: } {
        pattern1 = r'\}(\s*)\{'
        matches = re.findall(pattern1, content)
        if matches:
            content = re.sub(pattern1, r'},\1{', content)
            self.fixes_applied.append(f"Добавлены {len(matches)} запятых между объектами")

        # Между значениями в объекте: "value" "key"
        pattern2 = r'"(\s+)"(\w+)"\s*:'
        matches = re.findall(pattern2, content)
        if matches:
            content = re.sub(pattern2, r'",\1"\2":', content)
            self.fixes_applied.append(f"Добавлены {len(matches)} запятых между свойствами")

        return content

    def _fix_empty_values(self, content: str) -> str:
        """Заменяет пустые значения на null"""
        # : , или : }
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

    def _fix_unescaped_quotes(self, content: str) -> str:
        """Экранирует неэкранированные кавычки внутри строк"""
        # Сложная задача, пока пропускаем
        return content

    def _fix_duplicate_keys(self, content: str) -> str:
        """Обнаруживает и удаляет дублирующиеся ключи"""
        # Пока пропускаем, т.к. требует парсинга
        return content

    def _normalize_whitespace(self, content: str) -> str:
        """Нормализует пробелы (убирает лишние)"""
        # Множественные пробелы между токенами
        content = re.sub(r'\s{2,}', ' ', content)
        return content


class SmartJinja2ContextBuilder:
    """Интеллектуальный построитель контекста для Jinja2"""

    def __init__(self, debug: bool = False):
        self.debug = debug
        self.auto_vars = {}

    def extract_undefined_vars(self, template_str: str, context: Dict[str, Any]) -> Set[str]:
        """Извлекает все undefined переменные из шаблона"""
        # Паттерны для поиска переменных
        patterns = [
            r'\{\{\s*([a-zA-Z_][a-zA-Z0-9_\.]*)\s*\}\}',  # {{ var }}
            r'\{%\s*if\s+([a-zA-Z_][a-zA-Z0-9_\.]*)',     # {% if var %}
            r'\{%\s*for\s+\w+\s+in\s+([a-zA-Z_][a-zA-Z0-9_\.]*)',  # {% for x in var %}
        ]

        all_vars = set()
        for pattern in patterns:
            matches = re.findall(pattern, template_str)
            for match in matches:
                # Берем только корневую переменную (до первой точки)
                root_var = match.split('.')[0].split('[')[0]
                if root_var not in context:
                    all_vars.add(root_var)

        return all_vars

    def build_smart_context(self, template_str: str, base_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Строит умный контекст с заглушками для undefined переменных
        """
        undefined_vars = self.extract_undefined_vars(template_str, base_context)

        smart_context = base_context.copy()

        for var in undefined_vars:
            # Создаем умную заглушку в зависимости от контекста использования
            stub = self._create_smart_stub(var, template_str)
            smart_context[var] = stub
            self.auto_vars[var] = stub

            if self.debug:
                logger.debug(f"🔧 Создана заглушка: {var} = {stub}")

        return smart_context

    def _create_smart_stub(self, var_name: str, template_str: str) -> Any:
        """Создает умную заглушку на основе контекста использования"""

        # Проверяем как используется переменная
        # Если в цикле - возвращаем пустой список
        pattern_for = r'\{%\s*for\s+\w+\s+in\s+' + re.escape(var_name)
        if re.search(pattern_for, template_str):
            return []

        # Если проверяется в if - возвращаем False
        pattern_if = r'\{%\s*if\s+' + re.escape(var_name)
        if re.search(pattern_if, template_str):
            return False

        # Если обращение к атрибуту - возвращаем объект с заглушками
        pattern_attr = re.escape(var_name) + r'\.\w+'
        if re.search(pattern_attr, template_str):
            return defaultdict(lambda: None)

        # По умолчанию - пустая строка
        return ""

    def get_summary(self) -> str:
        """Возвращает сводку по созданным заглушкам"""
        if not self.auto_vars:
            return "Заглушки не создавались"

        summary = f"Создано {len(self.auto_vars)} заглушек:\n"
        for var, value in self.auto_vars.items():
            value_repr = f"list[{len(value)}]" if isinstance(value, list) else repr(value)
            summary += f"  • {var} = {value_repr}\n"

        return summary


class JSONCommentImportProcessor:
    """Обработчик импортов через комментарии в JSON"""

    def __init__(self, debug: bool = False):
        self.debug = debug
        self.processed_files = set()  # Для предотвращения циклических импортов

    def process_imports(self, content: str, base_path: Path) -> Tuple[str, int]:
        """
        Обрабатывает импорты в комментариях и удаляет все комментарии

        Формат комментария с импортом:
        // [Описание](file:///absolute/path/to/file.json)

        Returns: (обработанный контент, количество импортов)
        """
        import_count = 0
        self.processed_files.clear()

        # Обрабатываем импорты рекурсивно
        processed = self._process_imports_recursive(content, base_path, import_count)
        content_with_imports, import_count = processed

        # Удаляем все комментарии (однострочные и многострочные)
        # Однострочные комментарии // (но не внутри строк)
        # Ищем только комментарии которые начинаются с начала строки или после пробелов
        cleaned = re.sub(r'(?:^|\s)//[^\n]*', '', content_with_imports, flags=re.MULTILINE)

        # Многострочные комментарии /* */
        cleaned = re.sub(r'/\*.*?\*/', '', cleaned, flags=re.DOTALL)

        # Убираем лишние пустые строки
        cleaned = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned)

        return cleaned, import_count

    def _process_imports_recursive(self, content: str, base_path: Path, count: int) -> Tuple[str, int]:
        """Рекурсивная обработка импортов"""
        # Паттерн для поиска импортов в комментариях
        # Формат: // [любой текст](file:///path/to/file)
        import_pattern = r'//[^\n]*?\(file:///(.*?)\)[^\n]*'

        matches = list(re.finditer(import_pattern, content))

        if not matches:
            return content, count

        result = content

        for match in reversed(matches):  # Обрабатываем с конца, чтобы не сбивать индексы
            file_url = match.group(1)

            # Декодируем URL (например, %5B -> [)
            decoded_path = unquote(file_url)

            # Убираем якорь (#65) если есть
            if '#' in decoded_path:
                decoded_path = decoded_path.split('#')[0]

            import_file = Path('/' + decoded_path)

            # Проверка на циклические импорты
            if import_file in self.processed_files:
                if self.debug:
                    logger.warning(f"   ⚠️ Пропущен циклический импорт: {import_file.name}")
                continue

            if not import_file.exists():
                logger.warning(f"   ⚠️ Файл импорта не найден: {import_file}")
                continue

            try:
                # Читаем импортируемый файл
                with open(import_file, 'r', encoding='utf-8') as f:
                    imported_content = f.read()

                self.processed_files.add(import_file)
                count += 1

                if self.debug:
                    logger.debug(f"   📥 Импорт: {import_file.name}")

                # Рекурсивно обрабатываем импорты внутри импортируемого файла
                imported_content, count = self._process_imports_recursive(
                    imported_content,
                    import_file.parent,
                    count
                )

                # Заменяем комментарий на содержимое файла
                # Добавляем запятую перед если нужно
                before_text = result[:match.start()].rstrip()
                after_text = result[match.end():].lstrip()

                # Определяем, нужна ли запятая
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

    def clean_mixed_syntax(self, content: str, source_file: Path = None) -> Tuple[str, Dict[str, str]]:
        """
        Очищает смешанный Jinja2/JSON синтаксис с умными исправлениями
        Returns: (очищенный контент, словарь замен)
        """
        replacements = {}
        counter = 0

        # 1. Сначала обрабатываем импорты и удаляем комментарии
        if source_file:
            content, import_count = self.import_processor.process_imports(content, source_file.parent)
            if import_count > 0:
                logger.info(f"   📥 Обработано импортов: {import_count}")
        else:
            # Если source_file не передан, просто удаляем комментарии
            content = re.sub(r'(?:^|\s)//[^\n]*', '', content, flags=re.MULTILINE)
            content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)

        # Паттерны Jinja2 (от сложных к простым)
        patterns = [
            (r'\{%\s*if\s+[^%]+%\}.*?\{%\s*endif\s*%\}', 'JINJA_IF'),
            (r'\{%\s*for\s+[^%]+%\}.*?\{%\s*endfor\s*%\}', 'JINJA_FOR'),
            (r'\{%\s*set\s+[^%]+%\}', 'JINJA_SET'),
            (r'\{%[^}]+%\}', 'JINJA_TAG'),
            (r'\{\{[^}]+\}\}', 'JINJA_VAR'),
        ]

        cleaned = content

        # Удаляем Jinja2 блоки
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

        # Smart режим - дополнительные исправления
        if self.smart_mode and self.json_fixer:
            cleaned, fixes = self.json_fixer.fix_json(cleaned)
            if fixes and self.debug:
                logger.info(f"🧠 Smart исправления: {', '.join(fixes)}")

        return cleaned, replacements


class JinjaHotReloaderV32(FileSystemEventHandler):
    """Hot Reload v3.2.3 с оптимизированной перезагрузкой браузера"""

    SUPPORTED_EXTENSIONS = {'.json', '.jinja', '.j2', '.json.jinja', '.json.j2'}

    def __init__(self, watch_dir: str = None, debug: bool = False,
                 browser_reload: bool = True, smart_mode: bool = False):
        self.watch_dir = Path(watch_dir) if watch_dir else Path('/Users/username/Documents/front-middle-schema/.JSON')
        self.debug = debug
        self.browser_reload = browser_reload
        self.smart_mode = smart_mode
        self.data_cache = {}
        self.processing_files = set()
        self.last_process_time = {}

        # Smart компоненты
        self.preprocessor = EnhancedJinjaJsonPreprocessor(smart_mode, debug)
        self.context_builder = SmartJinja2ContextBuilder(debug) if smart_mode else None

        # SDUI трансформер
        self.sdui_transformer = SDUIToJinja2Transformer() if SDUIToJinja2Transformer else None

        # Jinja2 окружение
        if smart_mode:
            # В smart режиме используем DebugUndefined для отлова ошибок
            self.jinja_env = Environment(undefined=DebugUndefined)
        else:
            self.jinja_env = Environment()

        if SDUIJinja2Extensions:
            SDUIJinja2Extensions.register_all(self.jinja_env)

        # Валидатор путь
        self.validator_path = Path('/Users/username/Documents/front-middle-schema/sdui_web_validator_v3.0.0.py')

        logger.info("━" * 80)
        logger.info(f"📁 Директория наблюдения: {self.watch_dir}")
        logger.info(f"🔍 SDUI поддержка: {'✅ Включена' if self.sdui_transformer else '❌ Отключена'}")
        logger.info(f"🌐 Перезагрузка браузера: {'✅ Включена (Vivaldi:9090)' if self.browser_reload else '❌ Отключена'}")
        logger.info(f"🧠 Smart режим: {'✅ Включен' if self.smart_mode else '❌ Отключен'}")
        logger.info(f"📄 Поддерживаемые расширения: {', '.join(self.SUPPORTED_EXTENSIONS)}")
        logger.info("━" * 80)

    def is_jj_file(self, file_path: Path) -> bool:
        """Проверяет, является ли файл JJ_ файлом"""
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

    def process_jj_file(self, file_path: Path):
        """Обрабатывает [JJ_] файл с интеллектуальными исправлениями"""
        if file_path in self.processing_files:
            return

        current_time = time.time()
        if file_path in self.last_process_time:
            if current_time - self.last_process_time[file_path] < 1:
                return

        self.last_process_time[file_path] = current_time
        self.processing_files.add(file_path)

        try:
            logger.info("")
            logger.info("─" * 80)
            logger.info(f"🔄 Обработка: {file_path.name}")
            logger.info("─" * 80)

            # 1. Читаем файл
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 2. Очищаем смешанный синтаксис (с импортами и smart фиксами)
            cleaned_content, jinja_blocks = self.preprocessor.clean_mixed_syntax(content, file_path)

            # 3. Парсим JSON
            try:
                json_obj = json.loads(cleaned_content)
            except json.JSONDecodeError as e:
                logger.error("")
                logger.error("┄" * 80)
                logger.error(f"❌ Ошибка парсинга JSON на строке {e.lineno}: {e.msg}")
                logger.error(f"   📄 Файл: {file_path.name}")
                logger.error("┄" * 80)

                if self.debug:
                    debug_path = file_path.with_name(f"{file_path.stem}_debug_cleaned.json")
                    with open(debug_path, 'w', encoding='utf-8') as f:
                        f.write(cleaned_content)
                    logger.info(f"   📝 Debug файл создан: {debug_path.name}")

                    lines = cleaned_content.split('\n')
                    if e.lineno <= len(lines):
                        start = max(0, e.lineno - 3)
                        end = min(len(lines), e.lineno + 2)
                        logger.info(f"   Контекст ошибки (строки {start+1}-{end}):")
                        for i in range(start, end):
                            marker = " >>> " if i == e.lineno - 1 else "     "
                            logger.info(f"{marker}{i+1:4d} | {lines[i][:100]}")
                return

            # 4. Конвертация для WEB
            if 'ANDROID' in str(file_path):
                logger.info("   🔄 Конвертация Android → WEB")
                json_obj = self._convert_to_web(json_obj)

            # 5. SDUI трансформация
            if self.sdui_transformer:
                json_str = json.dumps(json_obj, ensure_ascii=False)
                if '${' in json_str or '"type": "if"' in json_str:
                    logger.info("   🔄 Преобразование SDUI → Jinja2")
                    json_str = self.sdui_transformer.transform(json_str)
                    json_obj = json.loads(json_str)

            # 6. Загружаем data файл
            data_file = self.find_data_file(file_path)
            context = {}

            if data_file:
                try:
                    with open(data_file, 'r', encoding='utf-8') as f:
                        context = json.load(f)
                    logger.info(f"   ✅ Загружены данные из: {data_file.name}")
                except Exception as e:
                    logger.error(f"   ❌ Ошибка загрузки данных: {e}")

            # 7. Рендеринг Jinja2 с smart контекстом
            json_str = json.dumps(json_obj, ensure_ascii=False)
            json_str = re.sub(r'\$\{([^}]+)\}', r'{{ \1 }}', json_str)

            # Smart режим - создаем умный контекст
            if self.smart_mode and self.context_builder:
                context = self.context_builder.build_smart_context(json_str, context)

                if self.context_builder.auto_vars:
                    logger.info(f"   🧠 Создано заглушек: {len(self.context_builder.auto_vars)}")
                    if self.debug:
                        logger.debug(self.context_builder.get_summary())

            try:
                template = self.jinja_env.from_string(json_str)
                rendered = template.render(**context)
                result_obj = json.loads(rendered)
            except (TemplateSyntaxError, UndefinedError) as e:
                if self.smart_mode:
                    logger.warning(f"⚠️ Jinja2: {e} (используется исходный JSON)")
                else:
                    logger.warning(f"⚠️ Jinja2: {e} (используется исходный JSON)")
                result_obj = json_obj
            except json.JSONDecodeError as e:
                logger.error(f"❌ Ошибка парсинга результата: {e}")
                result_obj = json_obj

            # 8. Генерируем выходной файл
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

            # 9. Сохраняем
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result_obj, f, indent=2, ensure_ascii=False)

            logger.info("")
            logger.info(f"✅ Создан: {output_path.name}")

            # 10. Валидация
            if self.validator_path.exists():
                self.validate_output(output_path)

        except Exception as e:
            logger.error("")
            logger.error("┄" * 80)
            logger.error(f"❌ Ошибка обработки {file_path.name}: {e}")
            logger.error("┄" * 80)
            if self.debug:
                import traceback
                traceback.print_exc()
        finally:
            self.processing_files.discard(file_path)

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
        """Обработчик изменения файла"""
        if event.is_directory:
            return

        path = Path(event.src_path)

        if self.is_jj_file(path):
            self.process_jj_file(path)
            # Перезагрузка браузера только после обработки
            if self.browser_reload:
                self.reload_browser()
        elif path.name.startswith('[data'):
            logger.info(f"🔄 Обновлен data файл: {path.name}")
            # Обрабатываем все связанные файлы
            for jj_file in path.parent.iterdir():
                if self.is_jj_file(jj_file):
                    self.process_jj_file(jj_file)
            # Перезагрузка браузера один раз после обработки всех файлов
            if self.browser_reload:
                self.reload_browser()

    def process_all(self):
        """Обрабатывает все файлы"""
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


def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(
        description='Jinja Hot Reload v3.2.3 - Оптимизация перезагрузки браузера'
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

    args = parser.parse_args()

    print("""
    ╔══════════════════════════════════════════════════╗
    ║     Jinja Hot Reload v3.2.3                     ║
    ║     🧠 SMART MODE: Intelligent Error Fixing     ║
    ╚══════════════════════════════════════════════════╝
    """)

    reloader = JinjaHotReloaderV32(
        watch_dir=args.path,
        debug=args.debug,
        browser_reload=not args.no_browser_reload,
        smart_mode=args.smart
    )

    if args.test:
        logger.info("🧪 Режим тестирования")
        reloader.process_all()
    else:
        reloader.watch()


if __name__ == '__main__':
    main()