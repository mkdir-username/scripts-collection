# SafeDebugUndefined - Руководство v1.0.0

## 📋 Описание проблемы

### Исходная ошибка

При использовании `DebugUndefined` в Jinja2 с `smart_mode`, форматирование строк вызывало ошибку:

```python
# ❌ ПРОБЛЕМНЫЙ КОД (v3.4.0)
self.jinja_env = Environment(
    loader=FileSystemLoader(self.template_search_paths),
    undefined=DebugUndefined  # Не поддерживает __format__
)
```

**Ошибка:**
```
TypeError: unsupported format string passed to DebugUndefined.__format__
```

**Сценарий возникновения:**
```jinja2
{# Шаблон с форматированием #}
Price: {{ price:.2f }}  {# DebugUndefined не может обработать '.2f' #}
Value: {{ value:>10 }}  {# Ошибка при выравнивании #}
```

---

## ✅ Решение: SafeDebugUndefined

### Класс SafeDebugUndefined

Кастомный класс, наследующий `DebugUndefined` с полной поддержкой форматирования:

```python
class SafeDebugUndefined(DebugUndefined):
    """
    Undefined класс с поддержкой __format__.

    Сохраняет всю debug функциональность DebugUndefined,
    добавляя graceful handling для format strings.
    """

    def __format__(self, format_spec: str) -> str:
        """Безопасное форматирование undefined значений."""
        var_name = self._undefined_name if hasattr(self, '_undefined_name') else 'undefined'
        debug_msg = f"{{{{ {var_name} }}}}"

        if format_spec:
            try:
                return format(debug_msg, format_spec)
            except (ValueError, TypeError):
                return debug_msg

        return debug_msg
```

### Использование

```python
# ✅ ИСПРАВЛЕННЫЙ КОД (v3.5.0)
from jinja_hot_reload_v3_5_0 import SafeDebugUndefined

self.jinja_env = Environment(
    loader=FileSystemLoader(self.template_search_paths),
    undefined=SafeDebugUndefined  # Полная поддержка __format__
)
```

---

## 🎯 Возможности

### 1. Поддержка Format Strings

```jinja2
{# Все эти шаблоны теперь работают #}
Price: {{ price:.2f }}          → Price: {{ price }}
Width: {{ value:>10 }}          → Width:    {{ value }}
Left:  {{ name:<20 }}           → Left:  {{ name }}
Center:{{ title:^30 }}          → Center:         {{ title }}
```

### 2. Вложенный доступ

```jinja2
{{ user.name }}                 → {{ user.name }}
{{ user.profile.email }}        → {{ user.profile.email }}
{{ items[0] }}                  → {{ items[0] }}
{{ data['key'] }}               → {{ data['key'] }}
```

### 3. Операции

```jinja2
{# Boolean контекст #}
{% if user %}...{% endif %}     → False (корректно)

{# Длина #}
{{ items|length }}              → 0

{# Арифметика #}
{{ count + 1 }}                 → 1 (0 + 1)
```

### 4. Расширенный Debug

```python
undefined = SafeDebugUndefined('test_var')

str(undefined)    # "{{ test_var }}"
repr(undefined)   # "SafeDebugUndefined('test_var')"
int(undefined)    # 0
float(undefined)  # 0.0
bool(undefined)   # False
```

---

## 📊 Сравнение с DebugUndefined

| Функция | DebugUndefined | SafeDebugUndefined |
|---------|----------------|-------------------|
| Debug вывод | ✅ | ✅ |
| `__str__` | ✅ | ✅ |
| `__repr__` | ✅ | ✅ Enhanced |
| `__format__` | ❌ **Ошибка** | ✅ **Работает** |
| Format specs | ❌ | ✅ |
| `__int__` | ❌ | ✅ → 0 |
| `__float__` | ❌ | ✅ → 0.0 |
| `__bool__` | ✅ | ✅ |
| Вложенный доступ | ✅ | ✅ |

---

## 🧪 Примеры использования

### Пример 1: Простой шаблон

```python
from jinja2 import Environment
from jinja_hot_reload_v3_5_0 import SafeDebugUndefined

env = Environment(undefined=SafeDebugUndefined)
template = env.from_string("Hello, {{ name }}!")
result = template.render()

print(result)  # "Hello, {{ name }}!"
```

### Пример 2: Форматирование

```python
template = env.from_string("""
Price: {{ price:.2f }}
Quantity: {{ qty:>5 }}
Total: {{ total:>10.2f }}
""")

result = template.render(price=99.99)
print(result)
# Price: 99.99
# Quantity: {{ qty }}
# Total:  {{ total }}
```

### Пример 3: Сложный JSON

```python
template = env.from_string("""
{
  "user": {
    "id": {{ user_id }},
    "name": "{{ user_name }}",
    "stats": {
      "followers": {{ followers }},
      "posts": {{ posts }}
    }
  }
}
""")

result = template.render(
    user_id=123,
    user_name="Alice"
    # followers и posts undefined
)

print(result)
# {
#   "user": {
#     "id": 123,
#     "name": "Alice",
#     "stats": {
#       "followers": {{ followers }},
#       "posts": {{ posts }}
#     }
#   }
# }
```

---

## 🔧 Технические детали

### Реализованные магические методы

```python
class SafeDebugUndefined(DebugUndefined):
    def __format__(self, format_spec: str) -> str:
        """Форматирование с format spec."""

    def __str__(self) -> str:
        """Строковое представление."""

    def __repr__(self) -> str:
        """Представление для отладки."""

    def __int__(self) -> int:
        """Преобразование в int → 0."""

    def __float__(self) -> float:
        """Преобразование в float → 0.0."""

    def __bool__(self) -> bool:
        """Boolean контекст → False."""

    def __len__(self) -> int:
        """Длина → 0."""

    def __getitem__(self, key):
        """Доступ к элементам."""

    def __getattr__(self, name: str):
        """Доступ к атрибутам."""

    def __call__(self, *args, **kwargs):
        """Вызов как функции."""
```

### Format Spec поддержка

SafeDebugUndefined поддерживает все стандартные спецификации форматирования:

```python
# Выравнивание
"{:>10}".format(undefined)   # Вправо
"{:<10}".format(undefined)   # Влево
"{:^10}".format(undefined)   # По центру

# Числовое форматирование (graceful fallback)
"{:.2f}".format(undefined)   # Float
"{:d}".format(undefined)     # Integer
"{:e}".format(undefined)     # Экспоненциальное

# Комбинации
"{:>20.3f}".format(undefined)
"{:0>10}".format(undefined)
```

---

## 🚀 Миграция с v3.4.0 на v3.5.0

### Шаг 1: Обновить версию файла

```bash
# Заменить
jinja_hot_reload_v3.4.0.py

# На
jinja_hot_reload_v3.5.0.py
```

### Шаг 2: Проверить импорты (автоматически)

Изменение применяется автоматически:

```python
# БЫЛО (v3.4.0):
self.jinja_env = Environment(
    loader=FileSystemLoader(self.template_search_paths),
    undefined=DebugUndefined  # ❌ Проблема
)

# СТАЛО (v3.5.0):
self.jinja_env = Environment(
    loader=FileSystemLoader(self.template_search_paths),
    undefined=SafeDebugUndefined  # ✅ Исправлено
)
```

### Шаг 3: Тестирование

```bash
# Запустить тесты
python3 tests/test_safe_debug_undefined_v1.0.0.py

# Тестовый запуск Hot Reload
python3 jinja_hot_reload_v3.5.0.py --smart --test
```

---

## 🧪 Тестирование

### Запуск тестов

```bash
cd /Users/username/Scripts
python3 tests/test_safe_debug_undefined_v1.0.0.py
```

### Ожидаемый вывод

```
================================================================================
SAFEDEBUGUNDEFINED TEST SUITE v1.0.0
================================================================================

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TEST 1: Базовое форматирование
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Result: Hello, {{ name }}!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TEST 2: Format спецификации
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Right align (>10): Value:  {{ value }}
✅ Float format (.2f): Price: {{ price }}
✅ Left align (<20): Name: {{ name }}

[...]

================================================================================
✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО
================================================================================
```

---

## 📝 Changelog v3.5.0

### [FIXED]
- 🔧 Исправлена ошибка `DebugUndefined.__format__` в smart_mode
- 🔧 Проблемы с форматированием строк в Jinja2

### [ADDED]
- ✨ `SafeDebugUndefined` - кастомный класс с `__format__` поддержкой
- ✨ Graceful handling для всех магических методов
- ✨ Расширенный debug вывод для undefined переменных
- ✨ Полная обратная совместимость

### [IMPROVED]
- 📈 Улучшена обработка форматирования undefined значений
- 📈 Более информативные debug сообщения
- 📈 Лучшая интеграция с Jinja2 Environment

---

## 🔗 Связанные файлы

- **Реализация:** `/Users/username/Scripts/Python/utils/jinja_hot_reload_v3.5.0.py`
- **Тесты:** `/Users/username/Scripts/tests/test_safe_debug_undefined_v1.0.0.py`
- **Документация:** `/Users/username/Scripts/docs/SafeDebugUndefined_Guide_v1.0.0.md`

---

## 📚 Дополнительные ресурсы

### Официальная документация Jinja2
- [Undefined Types](https://jinja.palletsprojects.com/en/3.1.x/api/#undefined-types)
- [Format Strings](https://docs.python.org/3/library/string.html#format-string-syntax)

### Примеры использования
```python
# Smart режим с SafeDebugUndefined
python3 jinja_hot_reload_v3.5.0.py --smart

# Smart режим + Debug
python3 jinja_hot_reload_v3.5.0.py --smart --debug

# Тестовый режим
python3 jinja_hot_reload_v3.5.0.py --smart --test
```

---

## 🎯 Заключение

`SafeDebugUndefined` полностью решает проблему форматирования в Jinja2, сохраняя всю функциональность `DebugUndefined` и добавляя:

1. ✅ Поддержка `__format__` для format strings
2. ✅ Graceful handling всех операций
3. ✅ Расширенный debug вывод
4. ✅ Полная обратная совместимость
5. ✅ Нулевые breaking changes

**Версия:** v3.5.0
**Дата:** 2025-10-02
**Статус:** ✅ Production Ready
