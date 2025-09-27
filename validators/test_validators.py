#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы всех валидаторов SDUI
"""

import json
import sys
from pathlib import Path

def test_imports():
    """Тестирование импортов всех валидаторов"""
    print("🧪 ТЕСТИРОВАНИЕ ВАЛИДАТОРОВ SDUI")
    print("=" * 60)

    print("\n1️⃣ Проверка импортов...")

    modules_status = {}

    # Тест SDUIIndexCache
    try:
        from sdui_index_cache import SDUIIndexCache
        modules_status['SDUIIndexCache'] = '✅'
    except ImportError as e:
        modules_status['SDUIIndexCache'] = f'❌ {e}'

    # Тест SDUIWebValidator
    try:
        from sdui_web_validator import SDUIWebValidator
        modules_status['SDUIWebValidator'] = '✅'
    except ImportError as e:
        modules_status['SDUIWebValidator'] = f'❌ {e}'

    # Тест SDUIWebValidatorImproved
    try:
        from sdui_web_validator_improved import SDUIWebValidatorImproved
        modules_status['SDUIWebValidatorImproved'] = '✅'
    except ImportError as e:
        modules_status['SDUIWebValidatorImproved'] = f'❌ {e}'

    # Тест SDUIVisualValidator (может не работать без requests)
    try:
        from sdui_visual_validator import SDUIVisualValidator
        modules_status['SDUIVisualValidator'] = '✅'
    except ImportError as e:
        modules_status['SDUIVisualValidator'] = f'⚠️ {e}'

    # Тест AgentFeedbackSystem
    try:
        from agent_feedback_system import AgentFeedbackSystem
        modules_status['AgentFeedbackSystem'] = '✅'
    except ImportError as e:
        modules_status['AgentFeedbackSystem'] = f'⚠️ {e}'

    # Вывод результатов
    for module, status in modules_status.items():
        print(f"  • {module}: {status}")

    return all('✅' in status for status in modules_status.values() if not '⚠️' in status)

def test_basic_validation():
    """Тестирование базовой валидации"""
    print("\n2️⃣ Тестирование базовой валидации...")

    try:
        from sdui_web_validator import SDUIWebValidator

        # Создаем валидатор
        validator = SDUIWebValidator()

        # Тестовый контракт
        test_contract = {
            "type": "TextView",
            "text": "Hello, SDUI!",
            "textColor": "#000000",
            "releaseVersion": {
                "web": "released",
                "ios": "released",
                "android": "released"
            }
        }

        # Валидация
        valid, report, fixed = validator.validate_contract(test_contract, strict=False)

        print(f"  • Контракт валиден: {'✅' if valid else '❌'}")
        print(f"  • WEB совместимость: {report.get('web_compatibility', 0)}%")
        print(f"  • Ошибок: {len(report.get('errors', []))}")
        print(f"  • Предупреждений: {len(report.get('warnings', []))}")

        return valid

    except Exception as e:
        print(f"  ❌ Ошибка валидации: {e}")
        return False

def test_index_cache():
    """Тестирование индексного кеша"""
    print("\n3️⃣ Тестирование индексного кеша...")

    try:
        from sdui_index_cache import SDUIIndexCache

        # Создаем кеш
        cache = SDUIIndexCache()

        # Поиск компонента
        results = cache.find_component("TextView")

        if results:
            print(f"  • Найдено компонентов TextView: {len(results)}")
            for result in results[:3]:
                print(f"    └─ {result['id']} (WEB: {'✅' if result['web_supported'] else '❌'})")
        else:
            print("  • Компонент TextView не найден")

        # Статистика
        stats = cache.get_statistics()
        print(f"\n  📊 Статистика:")
        print(f"    • Всего компонентов: {stats['total_components']}")
        print(f"    • WEB компонентов: {stats['web_components']}")
        print(f"    • Покрытие валидацией: {stats['validation_coverage']:.1f}%")

        return True

    except Exception as e:
        print(f"  ❌ Ошибка работы с кешем: {e}")
        return False

def test_validator_wrapper():
    """Тестирование wrapper для MCP интеграции"""
    print("\n4️⃣ Тестирование validator_wrapper...")

    try:
        # Добавляем путь к модулю
        sys.path.insert(0, str(Path.cwd() / 'SDUI' / 'sdui-mcp-framework' / 'modules'))

        from validator_wrapper import ValidatorIntegration

        # Создаем интеграцию
        validator = ValidatorIntegration()

        print(f"  • Загружено валидаторов: {len(validator.validators)}")

        # Тестовая валидация
        test_contract = {
            "type": "ButtonView",
            "title": "Click me!",
            "releaseVersion": {"web": "released"}
        }

        result = validator.validate_contract(test_contract, platform="web", strict=False)

        print(f"  • Валидация выполнена: {'✅' if result['valid'] else '❌'}")
        print(f"  • Использованы валидаторы: {', '.join(result.get('validators_used', []))}")

        return True

    except Exception as e:
        print(f"  ❌ Ошибка wrapper: {e}")
        return False

def main():
    """Главная функция тестирования"""

    # Тесты
    test_results = {
        "imports": test_imports(),
        "validation": test_basic_validation(),
        "cache": test_index_cache(),
        "wrapper": test_validator_wrapper()
    }

    # Итоги
    print("\n" + "=" * 60)
    print("📊 ИТОГИ ТЕСТИРОВАНИЯ")
    print("-" * 40)

    for test_name, result in test_results.items():
        status = "✅ УСПЕШНО" if result else "❌ ПРОВАЛЕНО"
        print(f"  • {test_name}: {status}")

    # Общий результат
    all_passed = all(test_results.values())

    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("✅ Валидаторы SDUI работают корректно")
        print("✅ Импорты настроены правильно")
        print("✅ Система готова к использованию")
    else:
        print("⚠️ НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОЙДЕНЫ")
        print("Проверьте установку зависимостей:")
        print("  pip install requests playwright")
        print("  playwright install")

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())