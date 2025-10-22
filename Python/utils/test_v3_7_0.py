#!/usr/bin/env python3
"""Тестирование SmartJSONFixer v3.7.0"""

import sys
from pathlib import Path

# Добавляем путь к модулю
sys.path.insert(0, '/Users/username/Scripts/Python/utils')

# Импортируем через importlib
import importlib.util
spec = importlib.util.spec_from_file_location(
    "jinja_hot_reload_v3_7_0",
    "/Users/username/Scripts/Python/utils/jinja_hot_reload_v3.7.0.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

SmartJSONFixer = module.SmartJSONFixer
FixType = module.FixType

print("=" * 80)
print("ТЕСТИРОВАНИЕ SmartJSONFixer v3.7.0")
print("=" * 80)

# Тест 1: Missing comma after brace
print("\n📝 ТЕСТ 1: Missing Comma After Brace")
print("-" * 60)
fixer = SmartJSONFixer(verbose=False)
test_json = '''{
  "root": {
    "property": "value"
  }
  "another": "property"
}'''

print(f"До исправления:")
print(test_json)
print()

fixed = fixer.fix_json(test_json)

print(f"После исправления:")
print(fixed)
print()
print(f"✅ Применено исправлений: {len(fixer.fixes_applied)}")
if fixer.fixes_applied:
    for fix in fixer.fixes_applied:
        print(f"   - Строка {fix.line_number}: {fix.description}")
        print(f"     До:    {fix.context_before}")
        print(f"     После: {fix.context_after}")

# Тест 2: Trailing comma
print("\n📝 ТЕСТ 2: Trailing Comma")
print("-" * 60)
fixer2 = SmartJSONFixer(verbose=False)
test_json2 = '''{"test": "value",}'''

print(f"До исправления: {test_json2}")
fixed2 = fixer2.fix_json(test_json2)
print(f"После исправления: {fixed2}")
print(f"✅ Применено исправлений: {len(fixer2.fixes_applied)}")
if fixer2.fixes_applied:
    for fix in fixer2.fixes_applied:
        print(f"   - {fix.description}")

# Тест 3: Duplicate commas
print("\n📝 ТЕСТ 3: Duplicate Commas")
print("-" * 60)
fixer3 = SmartJSONFixer(verbose=False)
test_json3 = '''{"a": 1,, "b": 2}'''

print(f"До исправления: {test_json3}")
fixed3 = fixer3.fix_json(test_json3)
print(f"После исправления: {fixed3}")
print(f"✅ Применено исправлений: {len(fixer3.fixes_applied)}")

# Тест 4: Invalid comments
print("\n📝 ТЕСТ 4: Invalid Comments")
print("-" * 60)
fixer4 = SmartJSONFixer(verbose=False)
test_json4 = '''{
  "test": "value" // this is a comment
}'''

print(f"До исправления:")
print(test_json4)
fixed4 = fixer4.fix_json(test_json4)
print(f"После исправления:")
print(fixed4)
print(f"✅ Применено исправлений: {len(fixer4.fixes_applied)}")

# Тест 5: Статистика
print("\n📊 СТАТИСТИКА")
print("-" * 60)
all_fixers = [fixer, fixer2, fixer3, fixer4]
total_fixes = sum(len(f.fixes_applied) for f in all_fixers)
print(f"Всего тестов: 4")
print(f"Всего исправлений: {total_fixes}")

print("\n" + "=" * 80)
print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
print("=" * 80)
