#!/usr/bin/env python3
"""
Исправленный валидатор контрактов без требования releaseVersion
"""

import json
import sys
import os
from pathlib import Path

def validate_json_syntax(contract_path):
    """Проверка синтаксиса JSON"""
    try:
        with open(contract_path, 'r', encoding='utf-8') as f:
            contract = json.load(f)
        return True, contract, None
    except json.JSONDecodeError as e:
        return False, None, f"Синтаксическая ошибка JSON: {e}"
    except Exception as e:
        return False, None, f"Ошибка чтения файла: {e}"

def validate_web_compatibility(contract):
    """Проверка совместимости с Web платформой"""
    errors = []
    warnings = []

    # Проверка запрещенных Android-специфичных компонентов
    forbidden_components = {
        'LabelView': 'TextView',
        'EditText': 'TextField',
        'LinearLayout': 'StackView',
        'ConstraintLayout': 'ConstraintWrapper'
    }

    # Проверка неподдерживаемых свойств для Web
    forbidden_properties = [
        'androidSpecific',
        'iosSpecific',
        'elevation',
        'rippleColor'
    ]

    def check_component(obj, path=""):
        if isinstance(obj, dict):
            component_type = obj.get('type')

            # Проверка запрещенных компонентов
            if component_type in forbidden_components:
                suggestion = forbidden_components[component_type]
                errors.append(f"Android-компонент '{component_type}' → используйте '{suggestion}' в {path}")

            # Проверка запрещенных свойств
            for prop in forbidden_properties:
                if prop in obj:
                    warnings.append(f"Свойство '{prop}' не поддерживается на Web в {path}")

            # Проверка специфичных для Android свойств
            if component_type == 'StackView':
                content = obj.get('content', {})
                if content.get('orientation') == 'vertical':
                    warnings.append(f"Используйте 'axis': 'vertical' вместо 'orientation' в {path}")

            # Рекурсивная проверка
            for key, value in obj.items():
                check_component(value, f"{path}.{key}" if path else key)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                check_component(item, f"{path}[{i}]")

    check_component(contract)

    # Проверка обязательных полей
    if 'type' not in contract:
        errors.append("Отсутствует поле 'type'")

    return errors, warnings

def suggest_fixes(contract, errors):
    """Предложение исправлений"""
    fixes = []
    fixed_contract = contract.copy()

    # Конвертация Android → Web компонентов
    component_mapping = {
        'LabelView': 'TextView',
        'EditText': 'TextField',
        'LinearLayout': 'StackView',
        'ConstraintLayout': 'ConstraintWrapper'
    }

    def convert_components(obj):
        if isinstance(obj, dict):
            if obj.get('type') in component_mapping:
                old_type = obj['type']
                new_type = component_mapping[old_type]
                obj['type'] = new_type
                fixes.append(f"{old_type} → {new_type}")

            for value in obj.values():
                if isinstance(value, (dict, list)):
                    convert_components(value)
        elif isinstance(obj, list):
            for item in obj:
                convert_components(item)

    convert_components(fixed_contract)

    return fixes, fixed_contract

def validate_contract(contract_path):
    """Основная функция валидации"""
    print(f"🔍 Валидация: {Path(contract_path).name}")

    # 1. Проверка синтаксиса
    syntax_ok, contract, syntax_error = validate_json_syntax(contract_path)

    if not syntax_ok:
        print(f"❌ {syntax_error}")
        return False

    print("✅ Синтаксис JSON корректен")

    # 2. Проверка совместимости с Web
    errors, warnings = validate_web_compatibility(contract)

    # 3. Вывод результатов
    score = 100

    if errors:
        print(f"\n❌ Ошибки ({len(errors)}):")
        for error in errors:
            print(f"  • {error}")
        score -= len(errors) * 25

    if warnings:
        print(f"\n⚠️ Предупреждения ({len(warnings)}):")
        for warning in warnings:
            print(f"  • {warning}")
        score -= len(warnings) * 10

    # 4. Предложение исправлений
    if errors:
        fixes, fixed_contract = suggest_fixes(contract, errors)

        if fixes:
            print(f"\n🔧 Предлагаемые исправления:")
            for fix in fixes:
                print(f"  • {fix}")

            # Сохранение исправленной версии
            fixed_path = contract_path.replace('.json', '_fixed.json')
            with open(fixed_path, 'w', encoding='utf-8') as f:
                json.dump(fixed_contract, f, indent=2, ensure_ascii=False)
            print(f"💾 Исправленная версия: {fixed_path}")

    # 5. Финальная оценка
    score = max(0, min(100, score))
    print(f"\n📊 Оценка: {score}/100")

    if score >= 90:
        print("🎉 Отличный контракт! Готов для Web")
        return True
    elif score >= 70:
        print("✅ Хороший контракт, незначительные доработки")
        return True
    elif score >= 50:
        print("⚠️ Контракт требует доработки")
        return False
    else:
        print("❌ Контракт содержит критические ошибки")
        return False

def main():
    if len(sys.argv) != 2:
        print("Использование: python simple_validator_fixed.py contract.json")
        sys.exit(1)

    contract_path = sys.argv[1]

    if not os.path.exists(contract_path):
        print(f"❌ Файл не найден: {contract_path}")
        sys.exit(1)

    success = validate_contract(contract_path)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()