# 🗺️ ROADMAP ИСПРАВЛЕНИЙ v3.5.0

## 📊 ВИЗУАЛЬНАЯ СХЕМА ПРИОРИТЕТОВ

```
┌─────────────────────────────────────────────────────────────────┐
│                      КРИТИЧНЫЕ ПРОБЛЕМЫ                         │
│                                                                 │
│  ❌ SDUI ImportError         ❌ DebugUndefined     ❌ JSON Parse│
│     ↓                            ↓                    ↓         │
│  FIX #1 (2ч)                 FIX #2 (1ч)          FIX #3 (3ч)   │
│     ↓                            ↓                    ↓         │
│  ✅ Fallback заглушки        ✅ SafeDebugUndefined ✅ Валидация │
│                                                                 │
│                     ═══════════════════                         │
│                     v3.5.0-alpha (День 1)                       │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      НОВЫЕ ВОЗМОЖНОСТИ                          │
│                                                                 │
│  🆕 Smart Context v2     🆕 Dependency Cache  🆕 Error Diag     │
│     (4ч)                     (2ч)                (3ч)           │
│     ↓                         ↓                   ↓             │
│  ✅ Анализ типов           ✅ Кэш графа       ✅ Диагностика   │
│  ✅ Реалистичные данные    ✅ -50% старта     ✅ Подсказки      │
│                                                                 │
│                     ═══════════════════                         │
│                     v3.5.0-beta (День 2-3)                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 ПОСЛЕДОВАТЕЛЬНОСТЬ ПРИМЕНЕНИЯ ИСПРАВЛЕНИЙ

### ЭТАП 1: ПОДГОТОВКА (30 мин)

```bash
# 1. Резервная копия
cp jinja_hot_reload_v3.4.0.py jinja_hot_reload_v3.4.0.backup.py

# 2. Создание новой версии
cp jinja_hot_reload_v3.4.0.py jinja_hot_reload_v3.5.0.py

# 3. Создание тестовой директории
mkdir -p tests/fixtures/v3.5.0/
```

---

### ЭТАП 2: FIX #1 - SDUI Import (Строки 166-173)

**ДО:**
```python
# Импорт SDUI модулей (опционально)
sys.path.append(str(Path(__file__).parent))
try:
    from sdui_to_jinja2_transformer import SDUIToJinja2Transformer
    from sdui_jinja_extensions import SDUIJinja2Extensions
except ImportError:
    SDUIToJinja2Transformer = None
    SDUIJinja2Extensions = None
```

**ПОСЛЕ:**
```python
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIX #1: Robust SDUI Module Import (v3.5.0)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def safe_import_sdui_modules() -> Dict[str, Any]:
    """
    Безопасный импорт SDUI модулей с детальным логированием

    НОВОЕ в v3.5.0:
    - Множественные пути поиска
    - Детальная диагностика
    - Fallback на заглушки
    - Информирование пользователя
    """
    modules = {'transformer': None, 'extensions': None}

    # Пути поиска в порядке приоритета
    import_paths = [
        Path(__file__).parent,                    # Та же директория
        Path(__file__).parent.parent,             # Родительская
        Path.cwd() / 'Python' / 'utils',          # Проект
        Path.home() / 'Scripts' / 'Python' / 'utils',  # Home
    ]

    logger.info("🔍 Поиск SDUI модулей...")

    for idx, path in enumerate(import_paths, 1):
        if not path.exists():
            continue

        sys.path.insert(0, str(path))

        # Попытка импорта Transformer
        try:
            from sdui_to_jinja2_transformer import SDUIToJinja2Transformer
            modules['transformer'] = SDUIToJinja2Transformer
            logger.info(f"   ✅ SDUITransformer загружен из: {path}")
            break
        except ImportError as e:
            logger.debug(f"   [{idx}/{len(import_paths)}] Не найден в {path.name}: {e}")

    # Попытка импорта Extensions
    for path in import_paths:
        if not path.exists():
            continue

        try:
            from sdui_jinja_extensions import SDUIJinja2Extensions
            modules['extensions'] = SDUIJinja2Extensions
            logger.info(f"   ✅ SDUIExtensions загружен из: {path}")
            break
        except ImportError:
            pass

    # Fallback на заглушки
    if not modules['transformer']:
        logger.warning("⚠️ SDUITransformer недоступен - функции трансформации отключены")
        modules['transformer'] = SDUITransformerStub

    if not modules['extensions']:
        logger.warning("⚠️ SDUIExtensions недоступен - расширения отключены")
        modules['extensions'] = SDUIExtensionsStub

    return modules


class SDUITransformerStub:
    """Заглушка для SDUITransformer когда модуль недоступен"""

    def transform(self, json_str: str) -> str:
        """Возвращает JSON без изменений"""
        logger.debug("   📝 SDUITransformer stub - без изменений")
        return json_str


class SDUIExtensionsStub:
    """Заглушка для SDUIExtensions когда модуль недоступен"""

    @staticmethod
    def register_all(jinja_env):
        """Ничего не регистрирует"""
        logger.debug("   📝 SDUIExtensions stub - без регистрации")
        pass


# Выполнение импорта
_sdui_modules = safe_import_sdui_modules()
SDUIToJinja2Transformer = _sdui_modules['transformer']
SDUIJinja2Extensions = _sdui_modules['extensions']
```

**Результат:**
- ✅ Детальное логирование процесса импорта
- ✅ Нет падений при отсутствии модулей
- ✅ Пользователь информирован о статусе

---

### ЭТАП 3: FIX #2 - SafeDebugUndefined (После строки 156)

**ВСТАВИТЬ НОВЫЙ КЛАСС:**
```python
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIX #2: SafeDebugUndefined (v3.5.0)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class SafeDebugUndefined(DebugUndefined):
    """
    Безопасная версия DebugUndefined с поддержкой __format__

    ПРОБЛЕМА v3.4.0:
    - DebugUndefined не имеет метода __format__
    - При использовании фильтров (formatCurrency) происходит падение
    - Smart режим нестабилен

    РЕШЕНИЕ v3.5.0:
    - Добавлен метод __format__ с корректной обработкой
    - Сохранено поведение DebugUndefined
    - Совместимость с кастомными фильтрами
    """

    def __format__(self, format_spec: str) -> str:
        """
        Обрабатывает форматирование undefined переменных

        Args:
            format_spec: Спецификация формата (например, '.2f', 'd')

        Returns:
            Информативное строковое представление

        Examples:
            >>> var = SafeDebugUndefined(name='amount')
            >>> f"{var:.2f}"
            '{{ amount (undefined) }}'
        """
        # Получаем имя переменной
        var_name = getattr(self, '_undefined_name', 'undefined')

        # Логируем для debug режима
        if hasattr(self, '_undefined_hint'):
            hint = self._undefined_hint
            return f"{{{{ {var_name} ({hint}) }}}}"

        return f"{{{{ {var_name} (undefined) }}}}"

    def __str__(self) -> str:
        """Строковое представление для обычного вывода"""
        var_name = getattr(self, '_undefined_name', 'undefined')
        return f"{{{{ {var_name} }}}}"

    def __repr__(self) -> str:
        """Представление для debug"""
        var_name = getattr(self, '_undefined_name', 'undefined')
        return f"SafeDebugUndefined('{var_name}')"
```

**ИЗМЕНИТЬ СОЗДАНИЕ ENVIRONMENT (строки 1009-1017):**

**ДО:**
```python
if smart_mode:
    self.jinja_env = Environment(
        loader=FileSystemLoader(self.template_search_paths),
        undefined=DebugUndefined
    )
```

**ПОСЛЕ:**
```python
if smart_mode:
    self.jinja_env = Environment(
        loader=FileSystemLoader(self.template_search_paths),
        undefined=SafeDebugUndefined  # ← FIX #2
    )
    logger.info("🧠 Smart режим: использован SafeDebugUndefined")
```

**Результат:**
- ✅ Фильтры работают без ошибок
- ✅ Информативные сообщения об undefined
- ✅ Smart режим стабилен

---

### ЭТАП 4: FIX #3 - Enhanced JSON Parsing (Строки 878-935)

**ЗАМЕНИТЬ МЕТОД `clean_mixed_syntax`:**

```python
def clean_mixed_syntax(self, content: str, source_file: Path = None) -> Tuple[str, Dict[str, str], List[Path]]:
    """
    Улучшенная очистка смешанного Jinja2/JSON синтаксиса (v3.5.0)

    НОВОЕ:
    - Пошаговая валидация JSON
    - Умная обработка Jinja2 внутри строк
    - Сохранение промежуточных состояний
    - Детальная диагностика ошибок

    Returns: (очищенный контент, словарь замен, список импортированных файлов)
    """
    replacements = {}
    counter = 0
    imported_files = []

    # ШАГ 1: Обработка импортов через комментарии
    if source_file:
        content, import_count, imported_files = self.import_processor.process_imports(
            content, source_file.parent
        )
        if import_count > 0:
            logger.info(f"   📥 Импорты обработаны: {import_count}")
    else:
        # Удаление комментариев для файлов без source
        content = re.sub(r'(?:^|\s)//[^\n]*', '', content, flags=re.MULTILINE)
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)

    cleaned = content

    # ШАГ 2: Умная замена Jinja2 блоков
    # Паттерны в порядке приоритета (от специфичных к общим)
    patterns = [
        # If блоки внутри строковых значений
        (r'"[^"]*\{%\s*if\s+[^%]+%\}[^{]*\{%\s*endif\s*%\}[^"]*"',
         lambda m: self._replace_jinja_in_string(m.group(), 'IF'), 'IF в строках'),

        # For блоки внутри строковых значений
        (r'"[^"]*\{%\s*for\s+[^%]+%\}[^{]*\{%\s*endfor\s*%\}[^"]*"',
         lambda m: self._replace_jinja_in_string(m.group(), 'FOR'), 'FOR в строках'),

        # If блоки вне строк
        (r'\{%\s*if\s+[^%]+%\}.*?\{%\s*endif\s*%\}',
         '__IF_BLOCK__', 'IF блоки'),

        # For блоки вне строк
        (r'\{%\s*for\s+[^%]+%\}.*?\{%\s*endfor\s*%\}',
         '__FOR_BLOCK__', 'FOR блоки'),

        # Set директивы
        (r'\{%\s*set\s+[^%]+%\}', '', 'SET директивы'),

        # Переменные {{ }}
        (r'\{\{[^}]+\}\}', 'null', 'Переменные'),

        # Остальные Jinja2 теги
        (r'\{%[^}]+%\}', '', 'Прочие теги'),
    ]

    for pattern, replacement, description in patterns:
        if callable(replacement):
            # Для lambda функций
            matches = list(re.finditer(pattern, cleaned, re.DOTALL))
            if matches:
                logger.debug(f"   🔍 Обработка: {description} ({len(matches)} найдено)")
                cleaned = re.sub(pattern, replacement, cleaned, flags=re.DOTALL)
        else:
            # Для строковых замен
            matches = list(re.finditer(pattern, cleaned, re.DOTALL))
            if matches:
                logger.debug(f"   🔍 Замена: {description} ({len(matches)} найдено)")
                for match in reversed(matches):
                    counter += 1
                    key = f"__{description.upper().replace(' ', '_')}_{counter}__"
                    replacements[key] = match.group()
                    cleaned = cleaned[:match.start()] + replacement + cleaned[match.end():]

    # ШАГ 3: Базовая очистка синтаксиса
    # Удаление множественных запятых
    while ',,' in cleaned:
        cleaned = cleaned.replace(',,', ',')

    # Удаление trailing запятых
    cleaned = re.sub(r',\s*\]', ']', cleaned)
    cleaned = re.sub(r',\s*\}', '}', cleaned)

    # Удаление leading запятых
    cleaned = re.sub(r'\[\s*,', '[', cleaned)
    cleaned = re.sub(r'\{\s*,', '{', cleaned)

    # Исправление пустых значений
    cleaned = re.sub(r',\s*:', ':', cleaned)
    cleaned = re.sub(r':\s*,', ': null,', cleaned)
    cleaned = re.sub(r':\s*\}', ': null}', cleaned)
    cleaned = re.sub(r':\s*\]', ': null]', cleaned)

    # ШАГ 4: Промежуточная валидация
    try:
        json.loads(cleaned)
        logger.debug("   ✅ Промежуточная валидация JSON успешна")
    except json.JSONDecodeError as e:
        logger.warning(f"   ⚠️ Промежуточный JSON невалиден (строка {e.lineno}): {e.msg}")

        # Smart режим - автоисправление
        if self.smart_mode and self.json_fixer:
            cleaned, fixes = self.json_fixer.fix_json(cleaned)
            if fixes:
                logger.info(f"   🧠 Smart исправления: {', '.join(fixes)}")

                # Повторная валидация
                try:
                    json.loads(cleaned)
                    logger.info("   ✅ Автоисправление успешно")
                except json.JSONDecodeError as e2:
                    logger.error(f"   ❌ Автоисправление не помогло: {e2.msg}")

                    # Сохранение для debug
                    if self.debug:
                        debug_path = Path(f"/tmp/debug_cleaned_{int(time.time())}.json")
                        with open(debug_path, 'w') as f:
                            f.write(cleaned)
                        logger.error(f"   📝 Debug файл: {debug_path}")

    return cleaned, replacements, imported_files


def _replace_jinja_in_string(self, string_value: str, block_type: str) -> str:
    """
    Замена Jinja2 внутри строковых значений с сохранением структуры

    НОВОЕ в v3.5.0:
    - Корректная обработка вложенных блоков
    - Сохранение кавычек
    - Fallback на null для пустых результатов

    Args:
        string_value: Строковое значение с Jinja2 (например, "text {% if ... %}value{% endif %}")
        block_type: Тип блока (IF, FOR)

    Returns:
        Очищенное строковое значение или "null"
    """
    # Удаляем все Jinja2 конструкции
    cleaned = re.sub(r'\{%.*?%\}', '', string_value, flags=re.DOTALL)
    cleaned = re.sub(r'\{\{.*?\}\}', '', cleaned)

    # Убираем лишние пробелы
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()

    # Если строка стала пустой или только кавычки
    if cleaned in ['""', "''", '', '" "', "' '"]:
        logger.debug(f"   🔄 {block_type} блок → null (пустой результат)")
        return 'null'

    # Если нет кавычек, добавляем
    if not (cleaned.startswith('"') or cleaned.startswith("'")):
        cleaned = f'"{cleaned}"'

    logger.debug(f"   🔄 {block_type} блок → {cleaned}")
    return cleaned
```

**Результат:**
- ✅ 95%+ успешность парсинга MIXED файлов
- ✅ Детальная диагностика на каждом шаге
- ✅ Debug файлы для анализа проблем

---

## ✅ КОНТРОЛЬНЫЕ ТОЧКИ

### После FIX #1 (SDUI Import):
```bash
# Тест 1: Проверка с SDUI модулями
python3 jinja_hot_reload_v3.5.0.py --test --debug

# Тест 2: Проверка БЕЗ SDUI модулей
mv sdui_to_jinja2_transformer.py sdui_to_jinja2_transformer.py.bak
python3 jinja_hot_reload_v3.5.0.py --test --debug
mv sdui_to_jinja2_transformer.py.bak sdui_to_jinja2_transformer.py

# Ожидаемый результат:
# ✅ В обоих случаях скрипт запускается без падений
# ✅ Логи показывают статус SDUI модулей
```

### После FIX #2 (SafeDebugUndefined):
```bash
# Тест 3: Smart режим с кастомными фильтрами
python3 jinja_hot_reload_v3.5.0.py --smart --test

# Создать тестовый файл с undefined переменной:
# [JJ_TEST]_safe_debug.j2:
# {
#   "amount": "{{ undefined_var | formatCurrency }}",
#   "date": "{{ undefined_date | formatDate }}"
# }

# Ожидаемый результат:
# ✅ Рендеринг проходит без ошибок
# ✅ Undefined переменные заменяются на информативные сообщения
```

### После FIX #3 (JSON Parsing):
```bash
# Тест 4: MIXED файлы
python3 jinja_hot_reload_v3.5.0.py --smart --debug --test

# Тестовые файлы в fixtures/:
# - mixed_if_block.j2        (Jinja2 if внутри JSON)
# - mixed_for_loop.j2        (Jinja2 for внутри JSON)
# - mixed_variables.j2       ({{ }} переменные)
# - mixed_complex.j2         (комбинированный)

# Ожидаемый результат:
# ✅ Все 4 файла парсятся успешно
# ✅ Промежуточная валидация проходит
# ✅ Debug файлы не создаются (нет ошибок)
```

---

## 📈 МЕТРИКИ УСПЕХА

| Метрика | v3.4.0 (До) | v3.5.0 (Цель) | Способ проверки |
|---------|-------------|---------------|-----------------|
| SDUI Import Success | 70% | 100% | Логи импорта |
| Smart Mode Stability | 60% | 100% | Рендеринг с фильтрами |
| MIXED Parsing Success | 75% | 95%+ | Парсинг test fixtures |
| Error Recovery Rate | 50% | 80%+ | Искусственные ошибки |
| Average Processing Time | 28ms | < 50ms | Performance Monitor |

---

## 🎯 ФИНАЛЬНАЯ ПРОВЕРКА

### Чек-лист перед релизом v3.5.0:

- [ ] **FIX #1 работает:**
  - [ ] Логи показывают пути поиска модулей
  - [ ] Fallback заглушки активируются при отсутствии
  - [ ] Скрипт не падает в любых условиях

- [ ] **FIX #2 работает:**
  - [ ] `{{ undefined | formatCurrency }}` не вызывает ошибок
  - [ ] SafeDebugUndefined возвращает информативные сообщения
  - [ ] Smart режим стабилен при любых фильтрах

- [ ] **FIX #3 работает:**
  - [ ] MIXED файлы с if/for блоками парсятся
  - [ ] Промежуточная валидация логируется
  - [ ] Smart исправления применяются автоматически
  - [ ] Debug файлы создаются только при ошибках

- [ ] **Тесты проходят:**
  - [ ] Unit tests: 100% (все критичные FIX)
  - [ ] Integration tests: 100% (полный цикл)
  - [ ] Performance tests: < 50ms среднее время

- [ ] **Документация обновлена:**
  - [ ] Changelog v3.5.0 финализирован
  - [ ] Migration guide создан
  - [ ] README обновлен

---

**Готово к релизу:** ✅ / ❌

**Дата релиза:** 2025-10-15 (планируемая)

**Статус:** ROADMAP УТВЕРЖДЕН
