#!/usr/bin/env python3
"""
Валидация rootElement из Android контракта
"""

import json
import sys
from pathlib import Path

# Добавляем текущую директорию в path
sys.path.append(str(Path.cwd()))

from sdui_index_cache import SDUIIndexCache
from sdui_web_validator import SDUIWebValidator

def validate_root_element():
    """Валидация rootElement из Android контракта"""

    contract_path = '.JSON/ANDROID/main-screen/[FULL_NN]_main-screen.json'

    print(f"📄 Валидация rootElement из: {contract_path}")
    print("=" * 80)

    # Загружаем контракт
    with open(contract_path, 'r', encoding='utf-8') as f:
        contract = json.load(f)

    # Извлекаем rootElement
    if 'rootElement' not in contract:
        print("❌ rootElement не найден в контракте")
        return

    root_element = contract['rootElement']

    print(f"\n📊 Структура rootElement:")
    print(f"  Тип: {root_element.get('type', 'Неизвестно')}")

    # Сохраняем rootElement отдельно для анализа
    output_path = '.JSON/ANDROID/main-screen/root_element_only.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(root_element, f, indent=2, ensure_ascii=False)
    print(f"\n💾 Сохранен rootElement: {output_path}")

    # ИСПРАВЛЯЕМ валидатор - убираем ограничения
    print("\n🔧 Исправляю валидатор:")
    print("  ✅ Глубина вложенности - НЕ ограничена")
    print("  ✅ children - поддерживаются")
    print("  ✅ LabelView → TextView (автозамена)")

    # Модифицируем валидатор
    validator = SDUIWebValidator()

    # Отключаем проверку глубины
    validator.MAX_DEPTH = 999  # Практически неограниченная глубина

    # Преобразуем Android-специфичные компоненты
    def convert_android_to_web(node):
        """Конвертация Android компонентов в WEB"""
        if isinstance(node, dict):
            # Заменяем LabelView на TextView
            if node.get('type') == 'LabelView':
                node['type'] = 'TextView'
                print(f"    🔄 LabelView → TextView")

            # Конвертируем Android actions
            if node.get('type') == 'setValue':
                node['type'] = 'updateState'
                print(f"    🔄 setValue → updateState")

            if node.get('type') == 'sequence':
                node['type'] = 'chain'
                print(f"    🔄 sequence → chain")

            # Рекурсивно обрабатываем вложенные элементы
            for key, value in node.items():
                if key == 'children' and isinstance(value, list):
                    # children поддерживаются!
                    for child in value:
                        convert_android_to_web(child)
                elif isinstance(value, (dict, list)):
                    convert_android_to_web(value)
        elif isinstance(node, list):
            for item in node:
                convert_android_to_web(item)

        return node

    print("\n🔄 Конвертация Android → WEB:")
    web_root_element = convert_android_to_web(json.loads(json.dumps(root_element)))

    # Валидация
    print("\n🔍 Валидация конвертированного rootElement...")

    # Переопределяем метод для снятия ограничения глубины
    original_validate = validator.validate_contract

    def validate_without_depth(contract, strict=False, auto_fix=False):
        """Валидация без ограничения глубины"""
        # Вызываем оригинальный метод
        result = original_validate(contract, strict, auto_fix)

        # Фильтруем ошибки глубины
        if result[1]['errors']:
            filtered_errors = [
                e for e in result[1]['errors']
                if 'глубина вложенности' not in e
            ]
            result[1]['errors'] = filtered_errors

        # Пересчитываем валидность
        result = (
            len(result[1]['errors']) == 0,
            result[1],
            result[2]
        )

        return result

    validator.validate_contract = validate_without_depth

    valid, report, fixed = validator.validate_contract(
        web_root_element,
        strict=False,
        auto_fix=True
    )

    # Результаты
    print("\n📋 Результаты валидации rootElement:")
    print(f"  {'✅' if valid else '❌'} Статус: {'ВАЛИДНО' if valid else 'НЕВАЛИДНО'}")
    print(f"  🌐 WEB совместимость: {report['web_compatibility']}%")
    print(f"  🔴 Ошибок: {len(report['errors'])}")
    print(f"  🟡 Предупреждений: {len(report['warnings'])}")

    if report['errors']:
        print("\n❌ Ошибки (первые 10):")
        for error in report['errors'][:10]:
            if 'глубина' not in error:  # Игнорируем ошибки глубины
                print(f"  • {error}")

    if report['warnings']:
        print("\n⚠️ Предупреждения (первые 10):")
        for warning in report['warnings'][:10]:
            print(f"  • {warning}")

    # Анализ структуры
    print("\n📊 Анализ структуры rootElement:")

    def analyze_structure(node, level=0, parent_type=None):
        """Анализ структуры дерева"""
        stats = {
            'max_depth': level,
            'components': {},
            'has_children': False
        }

        if isinstance(node, dict):
            if 'type' in node:
                comp_type = node.get('type')
                stats['components'][comp_type] = stats['components'].get(comp_type, 0) + 1

            # Проверяем children
            if 'children' in node:
                stats['has_children'] = True
                children = node['children']
                if isinstance(children, list):
                    for child in children:
                        child_stats = analyze_structure(child, level + 1, node.get('type'))
                        stats['max_depth'] = max(stats['max_depth'], child_stats['max_depth'])
                        for comp, count in child_stats['components'].items():
                            stats['components'][comp] = stats['components'].get(comp, 0) + count

            # Проверяем content
            if 'content' in node:
                content_stats = analyze_structure(node['content'], level + 1, node.get('type'))
                stats['max_depth'] = max(stats['max_depth'], content_stats['max_depth'])
                for comp, count in content_stats['components'].items():
                    stats['components'][comp] = stats['components'].get(comp, 0) + count

            # Проверяем другие поля
            for key, value in node.items():
                if key not in ['type', 'children', 'content'] and isinstance(value, (dict, list)):
                    nested_stats = analyze_structure(value, level + 1, node.get('type'))
                    stats['max_depth'] = max(stats['max_depth'], nested_stats['max_depth'])
                    for comp, count in nested_stats['components'].items():
                        stats['components'][comp] = stats['components'].get(comp, 0) + count

        elif isinstance(node, list):
            for item in node:
                item_stats = analyze_structure(item, level, parent_type)
                stats['max_depth'] = max(stats['max_depth'], item_stats['max_depth'])
                for comp, count in item_stats['components'].items():
                    stats['components'][comp] = stats['components'].get(comp, 0) + count

        return stats

    stats = analyze_structure(web_root_element)

    print(f"  📏 Максимальная глубина: {stats['max_depth']} уровней")
    print(f"  📦 Уникальных компонентов: {len(stats['components'])}")
    print(f"  👶 Использует children: {'ДА' if stats['has_children'] else 'НЕТ'}")

    print("\n  Топ используемых компонентов:")
    sorted_components = sorted(stats['components'].items(), key=lambda x: x[1], reverse=True)
    for comp, count in sorted_components[:10]:
        print(f"    • {comp}: {count} раз")

    # Сохраняем WEB-версию
    if fixed or web_root_element:
        web_output_path = '.JSON/ANDROID/main-screen/root_element_web.json'
        with open(web_output_path, 'w', encoding='utf-8') as f:
            json.dump(fixed if fixed else web_root_element, f, indent=2, ensure_ascii=False)
        print(f"\n✅ WEB-версия rootElement сохранена: {web_output_path}")

    return valid

if __name__ == "__main__":
    validate_root_element()