#!/usr/bin/env python3
"""
Agent Validation CLI - Команда для агентов
Простой интерфейс для валидации контрактов агентами с визуальной обратной связью
"""

import json
import sys
import argparse
from pathlib import Path
from agent_feedback_system import AgentFeedbackSystem


def validate_for_agent(contract_path: str, visual: bool = True, agent_id: str = None):
    """Валидация контракта для агента с полной обратной связью"""

    # Проверяем существование файла
    if not Path(contract_path).exists():
        print(f"❌ Файл не найден: {contract_path}")
        return False

    # Загружаем контракт
    try:
        with open(contract_path, 'r', encoding='utf-8') as f:
            contract = json.load(f)
    except Exception as e:
        print(f"❌ Ошибка чтения файла: {e}")
        return False

    # Контекст агента
    agent_context = {
        "agent_id": agent_id or "unknown_agent",
        "contract_file": contract_path,
        "timestamp": "",
        "task": "contract_validation"
    }

    # Создаем систему обратной связи
    feedback_system = AgentFeedbackSystem()

    print(f"🤖 Валидация контракта для агента: {agent_context['agent_id']}")
    print(f"📄 Файл: {contract_path}")
    print("=" * 60)

    # Выполняем валидацию
    result = feedback_system.validate_agent_contract(
        contract,
        agent_context=agent_context,
        visual_test=visual
    )

    # Отображаем результат
    print(f"\n📊 РЕЗУЛЬТАТ ВАЛИДАЦИИ")
    print(f"Оценка: {result['overall_score']}/100")
    print(f"Статус: {result['summary']['recommendation']}")

    if result['success']:
        print("✅ КОНТРАКТ ГОТОВ К ИСПОЛЬЗОВАНИЮ!")
    else:
        print("❌ КОНТРАКТ ТРЕБУЕТ ДОРАБОТКИ")

    # Показываем рекомендации
    print(f"\n💡 РЕКОМЕНДАЦИИ ДЛЯ АГЕНТА:")
    for i, rec in enumerate(result["recommendations"][:10], 1):
        print(f"  {i}. {rec}")

    # Показываем автоисправления
    if result["corrections"]["applied_fixes"]:
        print(f"\n🔧 АВТОМАТИЧЕСКИЕ ИСПРАВЛЕНИЯ:")
        for fix in result["corrections"]["applied_fixes"]:
            print(f"  • {fix}")

        # Сохраняем исправленную версию
        fixed_path = contract_path.replace('.json', '_fixed.json')
        try:
            with open(fixed_path, 'w', encoding='utf-8') as f:
                json.dump(result["corrections"]["contract"], f, indent=2, ensure_ascii=False)
            print(f"\n💾 Исправленная версия сохранена: {fixed_path}")
        except Exception as e:
            print(f"⚠️ Не удалось сохранить исправленную версию: {e}")

    # Показываем скриншоты
    visual_result = result.get("visual_feedback", {})
    screenshots = visual_result.get("screenshots", [])
    if screenshots:
        print(f"\n📸 СКРИНШОТЫ ({len(screenshots)}):")
        for screenshot in screenshots:
            if screenshot.get("success"):
                print(f"  ✅ {screenshot['scenario']}: {screenshot['screenshot_name']}")
                print(f"     Время загрузки: {screenshot['load_time']}s")
            else:
                print(f"  ❌ {screenshot['scenario']}: {screenshot.get('error', 'неизвестная ошибка')}")

    # Следующие шаги
    print(f"\n🎯 СЛЕДУЮЩИЕ ШАГИ:")
    for i, step in enumerate(result["next_steps"], 1):
        print(f"  {i}. {step}")

    print(f"\n📄 Полный отчет сохранен: {result.get('report_saved', 'не сохранен')}")

    return result['success']


def main():
    """Главная функция CLI для агентов"""
    parser = argparse.ArgumentParser(
        description='🤖 Agent Validation CLI - Валидация SDUI контрактов для агентов',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:

  # Базовая валидация
  %(prog)s contract.json

  # Валидация с указанием ID агента
  %(prog)s contract.json --agent-id my_sdui_agent

  # Валидация без визуальных тестов (быстрее)
  %(prog)s contract.json --no-visual

  # Валидация исправленной версии
  %(prog)s contract_fixed.json --agent-id agent_v2
        """
    )

    parser.add_argument(
        'contract',
        help='Путь к JSON файлу контракта'
    )

    parser.add_argument(
        '--agent-id',
        default='unknown_agent',
        help='Идентификатор агента (для статистики)'
    )

    parser.add_argument(
        '--no-visual',
        action='store_true',
        help='Отключить визуальное тестирование (быстрее)'
    )

    parser.add_argument(
        '--json-output',
        action='store_true',
        help='Вывод результата в JSON формате'
    )

    args = parser.parse_args()

    # Выполняем валидацию
    success = validate_for_agent(
        args.contract,
        visual=not args.no_visual,
        agent_id=args.agent_id
    )

    # Код возврата для агентов
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()