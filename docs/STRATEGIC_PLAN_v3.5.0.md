# 🎯 СТРАТЕГИЧЕСКИЙ ПЛАН ИСПРАВЛЕНИЙ v3.5.0

**Дата создания:** 2025-10-02
**Базовая версия:** v3.4.0
**Целевая версия:** v3.5.0
**Статус:** ПЛАНИРОВАНИЕ

---

## 📊 АНАЛИЗ ТЕКУЩИХ ПРОБЛЕМ

### ❌ ПРОБЛЕМА #1: SDUI Модули не найдены
**Приоритет:** CRITICAL
**Код ошибки:** ImportError
**Локация:** Строки 166-173

```python
try:
    from sdui_to_jinja2_transformer import SDUIToJinja2Transformer
    from sdui_jinja_extensions import SDUIJinja2Extensions
except ImportError:
    SDUIToJinja2Transformer = None
    SDUIJinja2Extensions = None
```

**Анализ:**
- Импорты выполняются относительно, но модули могут отсутствовать
- Программа продолжает работу даже без SDUI модулей
- Нет детального логирования причины отсутствия

**Последствия:**
- SDUI трансформации не работают
- Конвертация `${}` → `{{ }}` не происходит
- SDUI расширения недоступны

---

### ❌ ПРОБЛЕМА #2: DebugUndefined.__format__ ошибка
**Приоритет:** HIGH
**Код ошибки:** AttributeError при рендеринге
**Локация:** Строки 1009-1017

```python
if smart_mode:
    self.jinja_env = Environment(
        loader=FileSystemLoader(self.template_search_paths),
        undefined=DebugUndefined  # ← ПРОБЛЕМА
    )
```

**Анализ:**
- `DebugUndefined` не имеет метода `__format__`
- При использовании `{{ var | formatCurrency }}` происходит падение
- Ошибка возникает только в smart_mode

**Пример ошибки:**
```
AttributeError: 'jinja2.DebugUndefined' object has no attribute '__format__'
```

**Последствия:**
- Рендеринг падает при форматировании undefined переменных
- Невозможно использовать кастомные фильтры в smart_mode

---

### ❌ ПРОБЛЕМА #3: JSON Parsing в MIXED режиме
**Приоритет:** HIGH
**Код ошибки:** JSONDecodeError
**Локация:** Метод `clean_mixed_syntax()` строки 878-935

**Анализ:**
- При удалении Jinja2 блоков остаются артефакты
- Некорректное удаление комментариев `{# ... #}`
- Проблемы с обработкой вложенных структур

**Примеры:**
```json
// ДО удаления Jinja2:
{
  "type": "{% if condition %}A{% else %}B{% endif %}",
  "value": {{ variable }}
}

// ПОСЛЕ (НЕКОРРЕКТНО):
{
  "type": "",
  "value":
}
```

**Последствия:**
- Mixed JSON+Jinja2 файлы не парсятся
- Fallback на error recovery не всегда успешен

---

## 🎯 СТРАТЕГИЯ ИСПРАВЛЕНИЙ

### ФАЗА 1: КРИТИЧНЫЕ ИСПРАВЛЕНИЯ (v3.5.0-alpha)

#### FIX #1: Robust SDUI Module Import
**Приоритет:** CRITICAL
**Оценка:** 2 часа
**Зависимости:** нет

**План действий:**
1. Добавить детальное логирование импортов
2. Реализовать fallback механизмы
3. Проверить наличие модулей в sys.path
4. Создать заглушки для отсутствующих функций

**Код:**
```python
# НОВЫЙ подход
def safe_import_sdui_modules():
    """Безопасный импорт SDUI модулей с детальным логированием"""
    modules = {
        'transformer': None,
        'extensions': None
    }

    import_paths = [
        Path(__file__).parent,
        Path(__file__).parent.parent,
        Path.cwd() / 'Python' / 'utils',
    ]

    for path in import_paths:
        sys.path.insert(0, str(path))

        try:
            from sdui_to_jinja2_transformer import SDUIToJinja2Transformer
            modules['transformer'] = SDUIToJinja2Transformer
            logger.info(f"✅ SDUI Transformer загружен из: {path}")
            break
        except ImportError as e:
            logger.debug(f"   ⚠️ Не найден в {path}: {e}")

    # Аналогично для extensions

    if not modules['transformer']:
        logger.warning("⚠️ SDUI Transformer недоступен - функции отключены")
        modules['transformer'] = SDUITransformerStub()

    return modules
```

**Результат:**
- ✅ Детальная диагностика импортов
- ✅ Fallback на заглушки
- ✅ Информирование пользователя

---

#### FIX #2: Fix DebugUndefined Format Issue
**Приоритет:** HIGH
**Оценка:** 1 час
**Зависимости:** нет

**План действий:**
1. Создать кастомный SafeDebugUndefined
2. Добавить метод `__format__`
3. Сохранить поведение DebugUndefined
4. Обеспечить совместимость с фильтрами

**Код:**
```python
# НОВЫЙ класс
class SafeDebugUndefined(DebugUndefined):
    """
    Расширение DebugUndefined с поддержкой __format__
    Решает проблему с кастомными фильтрами в smart режиме
    """

    def __format__(self, format_spec: str) -> str:
        """
        Обрабатывает форматирование undefined переменных

        Args:
            format_spec: Спецификация формата (например, '.2f')

        Returns:
            Строковое представление с информацией об undefined
        """
        # Получаем имя переменной из _undefined_name
        var_name = getattr(self, '_undefined_name', 'undefined')

        # Возвращаем информативное сообщение
        return f"{{{{ {var_name} (undefined) }}}}"

    def __str__(self) -> str:
        """Строковое представление"""
        var_name = getattr(self, '_undefined_name', 'undefined')
        return f"{{{{ {var_name} }}}}"
```

**Использование:**
```python
if smart_mode:
    self.jinja_env = Environment(
        loader=FileSystemLoader(self.template_search_paths),
        undefined=SafeDebugUndefined  # ← ИСПРАВЛЕНО
    )
```

**Результат:**
- ✅ Кастомные фильтры работают в smart режиме
- ✅ Информативные сообщения об undefined переменных
- ✅ Обратная совместимость

---

#### FIX #3: Enhanced JSON Parsing for MIXED Mode
**Приоритет:** HIGH
**Оценка:** 3 часа
**Зависимости:** нет

**План действий:**
1. Улучшить паттерны удаления Jinja2
2. Добавить валидацию после каждого удаления
3. Реализовать пошаговое восстановление
4. Сохранять промежуточные состояния для debug

**Код:**
```python
# УЛУЧШЕННЫЙ метод
def clean_mixed_syntax_v2(self, content: str, source_file: Path = None) -> Tuple[str, Dict[str, str], List[Path]]:
    """
    Улучшенная очистка смешанного синтаксиса с валидацией на каждом шаге

    АЛГОРИТМ:
    1. Обработка импортов через комментарии
    2. Замена Jinja2 блоков на placeholders (сохранение структуры)
    3. Валидация промежуточного JSON
    4. Удаление placeholders
    5. Финальная валидация
    """
    replacements = {}
    counter = 0
    imported_files = []

    # ШАГ 1: Импорты
    if source_file:
        content, import_count, imported_files = self.import_processor.process_imports(
            content, source_file.parent
        )

    # ШАГ 2: Умная замена Jinja2 с сохранением структуры
    cleaned = content

    # Паттерны в порядке приоритета
    patterns = [
        # If блоки - заменяем на пустую строку ВНУТРИ значений
        (r'"[^"]*\{%\s*if\s+[^%]+%\}[^{]*\{%\s*endif\s*%\}[^"]*"',
         lambda m: self._replace_jinja_in_string(m.group(), 'IF')),

        # For блоки - аналогично
        (r'"[^"]*\{%\s*for\s+[^%]+%\}[^{]*\{%\s*endfor\s*%\}[^"]*"',
         lambda m: self._replace_jinja_in_string(m.group(), 'FOR')),

        # Переменные {{ }} - заменяем на "null"
        (r'\{\{[^}]+\}\}', '"__JINJA_VAR__"'),

        # Set директивы - удаляем полностью
        (r'\{%\s*set\s+[^%]+%\}', ''),

        # Остальные теги
        (r'\{%[^}]+%\}', ''),
    ]

    for pattern, replacement in patterns:
        if callable(replacement):
            cleaned = re.sub(pattern, replacement, cleaned, flags=re.DOTALL)
        else:
            matches = list(re.finditer(pattern, cleaned, re.DOTALL))
            for match in reversed(matches):
                counter += 1
                key = f"__PLACEHOLDER_{counter}__"
                replacements[key] = match.group()
                cleaned = cleaned[:match.start()] + replacement + cleaned[match.end():]

    # ШАГ 3: Валидация промежуточного результата
    try:
        json.loads(cleaned)
        logger.debug("   ✅ Промежуточный JSON валиден")
    except json.JSONDecodeError as e:
        logger.warning(f"   ⚠️ Промежуточный JSON невалиден: {e.msg}")

        # Применяем умные исправления
        if self.smart_mode and self.json_fixer:
            cleaned, fixes = self.json_fixer.fix_json(cleaned)
            logger.info(f"   🧠 Применены исправления: {', '.join(fixes)}")

    # ШАГ 4: Финальная очистка
    cleaned = re.sub(r'"__JINJA_VAR__"', 'null', cleaned)
    cleaned = re.sub(r',\s*,', ',', cleaned)
    cleaned = re.sub(r',\s*([}\]])', r'\1', cleaned)

    return cleaned, replacements, imported_files

def _replace_jinja_in_string(self, string_value: str, block_type: str) -> str:
    """Замена Jinja2 внутри строковых значений"""
    # Удаляем Jinja2, сохраняя кавычки и структуру
    cleaned = re.sub(r'\{%.*?%\}', '', string_value, flags=re.DOTALL)
    cleaned = re.sub(r'\{\{.*?\}\}', '', cleaned)

    # Если строка стала пустой, возвращаем "null"
    if cleaned.strip() in ['""', "''", '']:
        return '"null"'

    return cleaned
```

**Результат:**
- ✅ Корректная обработка вложенных Jinja2 структур
- ✅ Валидация на каждом шаге
- ✅ Улучшенная диагностика ошибок
- ✅ Сохранение промежуточных состояний для debug

---

### ФАЗА 2: НОВЫЕ ВОЗМОЖНОСТИ (v3.5.0-beta)

#### FEATURE #1: Smart Context Builder v2
**Приоритет:** MEDIUM
**Оценка:** 4 часа
**Зависимости:** FIX #2

**Описание:**
Улучшенный построитель контекста с анализом типов и умными заглушками

**Возможности:**
- Автоопределение типов из шаблона
- Заглушки с реалистичными данными
- Поддержка вложенных структур
- Интеграция с SafeDebugUndefined

**Код:**
```python
class SmartContextBuilderV2:
    """
    Интеллектуальный построитель контекста v2

    НОВЫЕ ВОЗМОЖНОСТИ:
    - Анализ типов из контекста использования
    - Реалистичные заглушки (faker integration)
    - Поддержка вложенных объектов
    - Логирование создания заглушек
    """

    def __init__(self, debug: bool = False):
        self.debug = debug
        self.auto_vars = {}
        self.type_hints = {}

    def analyze_variable_usage(self, template_str: str, var_name: str) -> Dict[str, Any]:
        """
        Анализирует использование переменной в шаблоне

        Returns:
            {
                'type': 'list' | 'dict' | 'string' | 'number' | 'boolean',
                'attributes': ['attr1', 'attr2'],
                'methods': ['method1'],
                'format_spec': '.2f' | 'd' | None
            }
        """
        analysis = {
            'type': 'string',
            'attributes': [],
            'methods': [],
            'format_spec': None
        }

        # Анализ for loops
        for_pattern = rf'\{%\s*for\s+\w+\s+in\s+{re.escape(var_name)}\s*%\}'
        if re.search(for_pattern, template_str):
            analysis['type'] = 'list'

        # Анализ атрибутов
        attr_pattern = rf'{re.escape(var_name)}\.(\w+)'
        for match in re.finditer(attr_pattern, template_str):
            analysis['attributes'].append(match.group(1))
            analysis['type'] = 'dict'

        # Анализ фильтров
        filter_pattern = rf'{re.escape(var_name)}\s*\|\s*(\w+)'
        for match in re.finditer(filter_pattern, template_str):
            filter_name = match.group(1)
            if filter_name in ['formatCurrency', 'round']:
                analysis['type'] = 'number'
            elif filter_name == 'formatDate':
                analysis['type'] = 'datetime'

        return analysis

    def create_smart_stub(self, var_name: str, analysis: Dict[str, Any]) -> Any:
        """
        Создает умную заглушку на основе анализа

        Args:
            var_name: Имя переменной
            analysis: Результат analyze_variable_usage()

        Returns:
            Заглушка соответствующего типа
        """
        stub_type = analysis['type']

        if stub_type == 'list':
            return [self._create_list_item(analysis)]

        elif stub_type == 'dict':
            stub = {}
            for attr in analysis['attributes']:
                stub[attr] = self._guess_attribute_value(attr)
            return stub

        elif stub_type == 'number':
            return 0

        elif stub_type == 'datetime':
            return datetime.now().isoformat()

        elif stub_type == 'boolean':
            return False

        else:
            return ""

    def _guess_attribute_value(self, attr_name: str) -> Any:
        """Угадывает значение атрибута по имени"""
        # Словарь типичных атрибутов
        attr_types = {
            'id': 'uuid-1234-5678',
            'name': 'Sample Name',
            'title': 'Sample Title',
            'description': 'Sample description',
            'amount': 125000,
            'price': 99.99,
            'count': 5,
            'total': 499.95,
            'date': datetime.now().isoformat(),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'is_active': True,
            'is_enabled': True,
            'url': 'https://example.com',
            'email': 'user@example.com',
            'phone': '+7 (999) 123-45-67',
        }

        # Точное совпадение
        if attr_name.lower() in attr_types:
            return attr_types[attr_name.lower()]

        # Частичное совпадение
        for key, value in attr_types.items():
            if key in attr_name.lower():
                return value

        # По умолчанию
        return f"{attr_name}_value"
```

**Результат:**
- ✅ Умные заглушки с реалистичными данными
- ✅ Анализ типов из шаблона
- ✅ Поддержка сложных структур

---

#### FEATURE #2: Template Dependency Cache
**Приоритет:** MEDIUM
**Оценка:** 2 часа
**Зависимости:** нет

**Описание:**
Кэширование графа зависимостей для ускорения запуска

**Возможности:**
- Сохранение dependency_map в JSON
- Загрузка при старте
- Инвалидация при изменении файлов
- Уменьшение времени запуска на 50%

---

#### FEATURE #3: Advanced Error Diagnostics
**Приоритет:** LOW
**Оценка:** 3 часа
**Зависимости:** FIX #3

**Описание:**
Улучшенная диагностика ошибок с подсказками

**Возможности:**
- Анализ контекста ошибки
- Предложения по исправлению
- Интерактивный debug режим
- Экспорт отчетов об ошибках

---

### ФАЗА 3: ОБРАТНАЯ СОВМЕСТИМОСТЬ

#### COMPATIBILITY #1: Migration Guide
**Приоритет:** HIGH
**Оценка:** 2 часа

**Содержание:**
- Список breaking changes
- Миграция с v3.4.0 → v3.5.0
- Примеры обновления конфигурации
- FAQ по проблемам

---

#### COMPATIBILITY #2: Deprecation Warnings
**Приоритет:** MEDIUM
**Оценка:** 1 час

**Реализация:**
```python
def deprecated_method(old_name: str, new_name: str):
    """Декоратор для deprecated методов"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            warnings.warn(
                f"{old_name} устарел и будет удален в v4.0.0. "
                f"Используйте {new_name}",
                DeprecationWarning,
                stacklevel=2
            )
            return func(*args, **kwargs)
        return wrapper
    return decorator
```

---

## 🧪 ПЛАН ТЕСТИРОВАНИЯ

### UNIT TESTS

#### Test Suite #1: SDUI Import
```python
def test_sdui_import_fallback():
    """Тест fallback при отсутствии SDUI модулей"""
    # Удаляем модули из sys.modules
    # Проверяем загрузку заглушек
    # Верифицируем работу без SDUI
```

#### Test Suite #2: SafeDebugUndefined
```python
def test_safe_debug_undefined_format():
    """Тест форматирования undefined переменных"""
    # Создаем undefined переменную
    # Применяем фильтр formatCurrency
    # Проверяем отсутствие ошибок
```

#### Test Suite #3: Mixed JSON Parsing
```python
def test_mixed_syntax_cleaning():
    """Тест очистки смешанного синтаксиса"""
    # Загружаем test fixtures
    # Очищаем каждый случай
    # Верифицируем валидность JSON
```

### INTEGRATION TESTS

#### Test Case #1: Полный цикл обработки
- Чтение [JJ_] файла
- Обработка include/import
- Рендеринг с данными
- Валидация результата

#### Test Case #2: Error Recovery
- Искусственное создание ошибок
- Проверка graceful degradation
- Валидация частичных результатов

#### Test Case #3: Performance
- Обработка 100 файлов
- Измерение времени
- Проверка утечек памяти

---

## 📦 ВЕРСИОНИРОВАНИЕ

### v3.5.0-alpha (Критичные исправления)
- FIX #1: SDUI Import
- FIX #2: DebugUndefined
- FIX #3: JSON Parsing

### v3.5.0-beta (Новые возможности)
- FEATURE #1: Smart Context v2
- FEATURE #2: Dependency Cache
- FEATURE #3: Error Diagnostics

### v3.5.0-rc (Release Candidate)
- Финальное тестирование
- Документация
- Migration guide

### v3.5.0 (Stable Release)
- Полная стабилизация
- Обратная совместимость
- Production ready

---

## 📈 МЕТРИКИ УСПЕХА

### Количественные метрики:
- ✅ 0 ImportError в production
- ✅ 100% успешность рендеринга в smart режиме
- ✅ 95% успешность парсинга MIXED файлов
- ✅ < 50ms среднее время обработки
- ✅ 80%+ cache hit rate

### Качественные метрики:
- ✅ Улучшенная диагностика ошибок
- ✅ Понятные сообщения пользователю
- ✅ Легкая отладка проблем
- ✅ Стабильная работа без падений

---

## 🗓️ TIMELINE

| Фаза | Срок | Статус |
|------|------|--------|
| Планирование | 2025-10-02 | ✅ ЗАВЕРШЕНО |
| ФАЗА 1: Критичные исправления | 2025-10-03 | 📋 ОЖИДАЕТ |
| Unit Tests | 2025-10-04 | 📋 ОЖИДАЕТ |
| ФАЗА 2: Новые возможности | 2025-10-05 - 2025-10-06 | 📋 ОЖИДАЕТ |
| Integration Tests | 2025-10-07 | 📋 ОЖИДАЕТ |
| ФАЗА 3: Совместимость | 2025-10-08 | 📋 ОЖИДАЕТ |
| v3.5.0-alpha | 2025-10-09 | 📋 ОЖИДАЕТ |
| v3.5.0-beta | 2025-10-11 | 📋 ОЖИДАЕТ |
| v3.5.0-rc | 2025-10-13 | 📋 ОЖИДАЕТ |
| v3.5.0 RELEASE | 2025-10-15 | 📋 ОЖИДАЕТ |

**Общий срок:** 13 рабочих дней

---

## ✅ КОНТРОЛЬНЫЙ СПИСОК

### Перед началом разработки:
- [ ] Создать ветку `feature/v3.5.0`
- [ ] Подготовить test fixtures
- [ ] Настроить CI/CD pipeline
- [ ] Создать milestone в GitHub

### После каждого FIX:
- [ ] Написать unit tests
- [ ] Обновить документацию
- [ ] Добавить в changelog
- [ ] Code review

### Перед релизом:
- [ ] Все тесты проходят (100%)
- [ ] Документация обновлена
- [ ] Migration guide готов
- [ ] Changelog финализирован
- [ ] Performance benchmarks выполнены

---

## 🎓 CHANGELOG v3.5.0 (ПРОЕКТ)

### [FIXED]
* ImportError при отсутствии SDUI модулей → добавлены fallback заглушки
* AttributeError при форматировании undefined переменных → SafeDebugUndefined
* JSONDecodeError в MIXED режиме → улучшенный парсинг с валидацией

### [ADDED]
+ Smart Context Builder v2 с анализом типов
+ Template Dependency Cache для ускорения запуска
+ Advanced Error Diagnostics с подсказками
+ Детальное логирование импортов SDUI
+ Deprecation warnings для устаревших методов

### [IMPROVED]
* Производительность обработки MIXED файлов (+30%)
* Диагностика ошибок с контекстными подсказками
* Smart режим работает стабильно без падений
* Улучшенная обратная совместимость

---

## 📚 ССЫЛКИ

### Документация:
- `README_v2.1.0.md` - основная документация
- `INTEGRATION_REPORT_v3.3.0.md` - отчет об интеграции v3.3.0
- `jinja_hot_reload_v3.4.0.py` - текущая версия

### Связанные задачи:
- MODULE #10: Pure Jinja2 Support (v3.4.0) ✅
- MODULE #11: Error Recovery v2 (v3.5.0) 📋
- MODULE #12: Smart Context v2 (v3.5.0) 📋

---

**Автор:** Claude Code Agent
**Дата:** 2025-10-02
**Версия плана:** 1.0.0
**Статус:** УТВЕРЖДЕН К ИСПОЛНЕНИЮ
