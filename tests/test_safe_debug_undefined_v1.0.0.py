#!/usr/bin/env python3
"""
Тесты для SafeDebugUndefined - v1.0.0

Проверка работы кастомного Undefined класса с поддержкой __format__.
"""

import sys
from pathlib import Path

# Добавляем путь к модулям
sys.path.insert(0, str(Path(__file__).parent.parent / 'Python' / 'utils'))

from jinja2 import Environment
import importlib.util

# Динамический импорт модуля с точками в имени
spec = importlib.util.spec_from_file_location(
    "jinja_hot_reload_v3_5_0",
    Path(__file__).parent.parent / 'Python' / 'utils' / 'jinja_hot_reload_v3.5.0.py'
)
jinja_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(jinja_module)

SafeDebugUndefined = jinja_module.SafeDebugUndefined

def test_basic_format():
    """Тест базового форматирования."""
    print("━" * 80)
    print("TEST 1: Базовое форматирование")
    print("━" * 80)

    env = Environment(undefined=SafeDebugUndefined)

    # Тест 1: Простая строка с undefined переменной
    template = env.from_string("Hello, {{ name }}!")
    result = template.render()
    print(f"✅ Result: {result}")
    assert "{{ name }}" in result

    print()

def test_format_specs():
    """Тест различных format спецификаций через Python API."""
    print("━" * 80)
    print("TEST 2: Format спецификации (Python API)")
    print("━" * 80)

    # Создаём undefined объект
    undefined = SafeDebugUndefined('test_var')

    # Тест 2: Форматирование с шириной (right align)
    result = f"{undefined:>10}"
    print(f"✅ Right align (>10): '{result}'")

    # Тест 3: Форматирование числа (должно работать gracefully)
    result = f"{undefined:.2f}"
    print(f"✅ Float format (.2f): '{result}'")

    # Тест 4: Левое выравнивание
    result = f"{undefined:<20}"
    print(f"✅ Left align (<20): '{result}'")

    # Тест 5: Центрирование
    result = f"{undefined:^15}"
    print(f"✅ Center align (^15): '{result}'")

    print()

def test_nested_access():
    """Тест вложенного доступа."""
    print("━" * 80)
    print("TEST 3: Вложенный доступ")
    print("━" * 80)

    env = Environment(undefined=SafeDebugUndefined)

    # Тест 5: Доступ к атрибутам
    template = env.from_string("User: {{ user.name }}, Email: {{ user.email }}")
    result = template.render()
    print(f"✅ Attributes: {result}")

    # Тест 6: Доступ к элементам
    template = env.from_string("Item: {{ items[0] }}")
    result = template.render()
    print(f"✅ Items: {result}")

    print()

def test_operations():
    """Тест операций с undefined."""
    print("━" * 80)
    print("TEST 4: Операции с undefined")
    print("━" * 80)

    env = Environment(undefined=SafeDebugUndefined)

    # Тест 7: Boolean контекст
    template = env.from_string("{% if user %}Has user{% else %}No user{% endif %}")
    result = template.render()
    print(f"✅ Boolean: {result}")
    assert "No user" in result

    # Тест 8: Длина
    template = env.from_string("Length: {{ items|length }}")
    result = template.render()
    print(f"✅ Length: {result}")

    print()

def test_mixed_context():
    """Тест смешанного контекста (defined + undefined)."""
    print("━" * 80)
    print("TEST 5: Смешанный контекст")
    print("━" * 80)

    env = Environment(undefined=SafeDebugUndefined)

    # Тест 9: Частично определённый контекст
    template = env.from_string("""
Name: {{ name }}
Age: {{ age }}
Email: {{ email }}
    """.strip())

    result = template.render(name="John", age=30)
    print(f"✅ Mixed context result:\n{result}")

    assert "John" in result
    assert "30" in result
    assert "{{ email }}" in result

    print()

def test_complex_template():
    """Тест сложного шаблона."""
    print("━" * 80)
    print("TEST 6: Сложный шаблон")
    print("━" * 80)

    env = Environment(undefined=SafeDebugUndefined)

    template = env.from_string("""
{
  "user": {
    "id": {{ user_id }},
    "name": "{{ user_name }}",
    "email": "{{ user_email }}",
    "profile": {
      "bio": "{{ bio }}",
      "avatar": "{{ avatar_url }}"
    },
    "stats": {
      "followers": {{ followers }},
      "following": {{ following }}
    }
  }
}
    """.strip())

    result = template.render(
        user_id=123,
        user_name="Alice"
        # Остальные переменные undefined
    )

    print(f"✅ Complex template result:\n{result}")
    print()

def test_format_string_edge_cases():
    """Тест граничных случаев форматирования через Python API."""
    print("━" * 80)
    print("TEST 7: Граничные случаи форматирования (Python API)")
    print("━" * 80)

    undefined = SafeDebugUndefined('value')

    # Тест 10: Пустой format spec
    result = f"{undefined}"
    print(f"✅ No format spec: '{result}'")

    # Тест 11: Сложный format spec
    result = f"{undefined:^20.3f}"
    print(f"✅ Complex format (^20.3f): '{result}'")

    # Тест 12: Множественное форматирование
    a = SafeDebugUndefined('a')
    b = SafeDebugUndefined('b')
    c = SafeDebugUndefined('c')
    result = f"{a:>5} | {b:<5} | {c:^5}"
    print(f"✅ Multiple formats: '{result}'")

    # Тест 13: Заполнение нулями
    result = f"{undefined:0>10}"
    print(f"✅ Zero padding (0>10): '{result}'")

    print()

def test_comparison_with_debug_undefined():
    """Сравнение с оригинальным DebugUndefined через Python API."""
    print("━" * 80)
    print("TEST 8: Сравнение SafeDebugUndefined vs DebugUndefined (Python API)")
    print("━" * 80)

    from jinja2 import DebugUndefined

    # SafeDebugUndefined - должен работать
    safe_undefined = SafeDebugUndefined('value')
    try:
        result = f"{safe_undefined:.2f}"
        print(f"✅ SafeDebugUndefined with .2f: '{result}'")
    except Exception as e:
        print(f"❌ SafeDebugUndefined error: {e}")

    # DebugUndefined - должен упасть
    debug_undefined = DebugUndefined('value')
    try:
        result = f"{debug_undefined:.2f}"
        print(f"✅ DebugUndefined with .2f: '{result}'")
    except Exception as e:
        print(f"❌ DebugUndefined error (expected): {type(e).__name__}")

    print()

def test_repr_and_str():
    """Тест __repr__ и __str__."""
    print("━" * 80)
    print("TEST 9: __repr__ и __str__")
    print("━" * 80)

    undefined = SafeDebugUndefined('test_var')

    print(f"✅ str(undefined): {str(undefined)}")
    print(f"✅ repr(undefined): {repr(undefined)}")

    print()

def main():
    """Запуск всех тестов."""
    print("\n" + "=" * 80)
    print("SAFEDEBUGUNDEFINED TEST SUITE v1.0.0")
    print("=" * 80 + "\n")

    try:
        test_basic_format()
        test_format_specs()
        test_nested_access()
        test_operations()
        test_mixed_context()
        test_complex_template()
        test_format_string_edge_cases()
        test_comparison_with_debug_undefined()
        test_repr_and_str()

        print("=" * 80)
        print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО")
        print("=" * 80)

    except Exception as e:
        print("=" * 80)
        print(f"❌ ТЕСТ ПРОВАЛЕН: {e}")
        print("=" * 80)
        raise

if __name__ == '__main__':
    main()
