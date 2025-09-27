#!/usr/bin/env python3
"""
SDUI Enhanced Resolver - Примеры использования

Этот файл содержит практические примеры использования улучшенного SDUI резолвера
для типовых задач интеграции с агентами и обработки SDUI контрактов.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List
from sdui_resolver_enhanced import (
    SDUIEnhancedResolver, 
    ResolverConfig,
    SDUIResolverAPI,
    ValidationLevel,
    ComponentMetrics
)

# ============================================================================
# ПРИМЕР 1: Базовое использование - разрешение одного файла
# ============================================================================
def example_basic_resolution():
    """Простое разрешение SDUI схемы с минимальной конфигурацией."""
    print("\n" + "="*60)
    print("ПРИМЕР 1: Базовое разрешение схемы")
    print("="*60)
    
    # Создаем конфигурацию
    config = ResolverConfig(
        base_path="/Users/username/Documents/front-middle-schema/SDUI",
        web_only=True,  # Фильтруем только web компоненты
        verbose=False   # Тихий режим
    )
    
    # Создаем резолвер
    resolver = SDUIEnhancedResolver(config)
    
    # Разрешаем файл
    try:
        result = resolver.resolve_file("screens/salary/get-salary.json")
        
        # Выводим основную информацию
        metadata = result.get("_metadata", {})
        print(f"✅ Файл успешно обработан")
        print(f"   Truth Score: {metadata.get('truth_score', 0):.2f}")
        print(f"   Компонентов: {metadata.get('unique_components', 0)}")
        print(f"   Время: {metadata.get('processing_time', 0):.3f}с")
        
        # Сохраняем результат
        output_path = Path("resolved_salary.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"   Сохранено в: {output_path}")
        
        return result
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None


# ============================================================================
# ПРИМЕР 2: Валидация против метасхемы с Truth Score
# ============================================================================
def example_validation_with_metaschema():
    """Валидация контракта против strict_unversioned.json метасхемы."""
    print("\n" + "="*60)
    print("ПРИМЕР 2: Валидация с метасхемой и Truth Score")
    print("="*60)
    
    config = ResolverConfig(
        base_path="/Users/username/Documents/front-middle-schema/SDUI",
        metaschema_path="/Users/username/Documents/front-middle-schema/metaschemas/strict_unversioned.json",
        web_only=True,
        truth_score_threshold=0.95,  # Минимальный порог для production
        validation_level=ValidationLevel.STRICT,
        verbose=True
    )
    
    resolver = SDUIEnhancedResolver(config)
    
    # Файлы для проверки
    test_files = [
        "screens/salary/get-salary.json",
        "components/Button.json",
        "templates/form-template.json"
    ]
    
    for file_path in test_files:
        print(f"\n📋 Проверяем: {file_path}")
        try:
            # Разрешаем схему
            resolved = resolver.resolve_file(file_path)
            
            # Валидация против метасхемы
            validation = resolver.validate_against_metaschema(resolved)
            
            # Расчет Truth Score
            score = resolver.calculate_truth_score(resolved, None)
            
            # Результаты
            if validation["valid"]:
                print(f"   ✅ Валидация пройдена")
            else:
                print(f"   ❌ Ошибки валидации:")
                for error in validation["errors"][:3]:  # Первые 3 ошибки
                    print(f"      - {error}")
            
            # Truth Score анализ
            if score >= 0.95:
                print(f"   ✅ Truth Score: {score:.3f} (Production Ready)")
            elif score >= 0.80:
                print(f"   ⚠️  Truth Score: {score:.3f} (Needs Review)")
            else:
                print(f"   ❌ Truth Score: {score:.3f} (Not Ready)")
            
            # Проверка web release статуса
            if "_metadata" in resolved:
                web_released = resolved["_metadata"].get("web_released_components", [])
                if web_released:
                    print(f"   🌐 Web-released компоненты: {', '.join(web_released[:5])}")
            
        except Exception as e:
            print(f"   ❌ Ошибка обработки: {e}")


# ============================================================================
# ПРИМЕР 3: Извлечение StateAware паттернов
# ============================================================================
def example_stateaware_patterns():
    """Поиск и анализ StateAware паттернов в контракте."""
    print("\n" + "="*60)
    print("ПРИМЕР 3: Извлечение StateAware паттернов")
    print("="*60)
    
    config = ResolverConfig(
        base_path="/Users/username/Documents/front-middle-schema/SDUI",
        web_only=True,
        verbose=False
    )
    
    resolver = SDUIEnhancedResolver(config)
    
    # Создаем тестовый контракт с StateAware компонентами
    test_contract = {
        "type": "Screen",
        "title": "StateAware Example",
        "content": {
            "type": "Container",
            "children": [
                {
                    "type": "Control<Input>",
                    "id": "nameInput",
                    "stateRef": "userForm.name",
                    "validation": {"required": True}
                },
                {
                    "type": "Focus<Button>",
                    "id": "submitBtn",
                    "focusCondition": "userForm.isValid"
                },
                {
                    "type": "Selection<List>",
                    "id": "optionsList",
                    "selectionMode": "multiple",
                    "stateRef": "selectedOptions"
                },
                {
                    "type": "StateRef<Display>",
                    "binding": "userForm.summary"
                },
                {
                    "type": "Binding<Text>",
                    "dataSource": "api.response.message"
                }
            ]
        }
    }
    
    # Извлекаем StateAware паттерны
    patterns = resolver.extract_stateaware_patterns(test_contract)
    
    print(f"Найдено StateAware паттернов: {len(patterns)}")
    print("\nДетальный анализ:")
    
    # Группируем по типам
    pattern_groups = {}
    for pattern in patterns:
        pattern_type = pattern["pattern"]
        if pattern_type not in pattern_groups:
            pattern_groups[pattern_type] = []
        pattern_groups[pattern_type].append(pattern)
    
    # Выводим по группам
    for pattern_type, items in pattern_groups.items():
        print(f"\n🔹 {pattern_type}: {len(items)} компонентов")
        for item in items[:2]:  # Первые 2 примера
            print(f"   - Путь: {item['path']}")
            print(f"     Тип: {item['component_type']}")
            if 'state_ref' in item['details']:
                print(f"     State: {item['details']['state_ref']}")
    
    # Расчет влияния на Truth Score
    base_score = 1.0
    state_bonus = min(len(patterns) * 0.05, 0.15)  # Max 0.15 bonus
    final_score = min(base_score + state_bonus, 1.0)
    
    print(f"\n📊 Влияние на Truth Score:")
    print(f"   Базовый score: {base_score:.2f}")
    print(f"   StateAware бонус: +{state_bonus:.2f}")
    print(f"   Итоговый score: {final_score:.2f}")


# ============================================================================
# ПРИМЕР 4: Batch обработка множества файлов
# ============================================================================
def example_batch_processing():
    """Пакетная обработка нескольких SDUI файлов."""
    print("\n" + "="*60)
    print("ПРИМЕР 4: Batch обработка файлов")
    print("="*60)
    
    config = ResolverConfig(
        base_path="/Users/username/Documents/front-middle-schema/SDUI",
        web_only=True,
        max_parallel=3,  # Параллельная обработка
        verbose=False
    )
    
    resolver = SDUIEnhancedResolver(config)
    
    # Список файлов для обработки
    files_to_process = [
        "screens/salary/get-salary.json",
        "screens/profile/user-profile.json", 
        "components/Button.json",
        "components/Input.json",
        "components/List.json",
        "templates/form-template.json",
        "templates/card-template.json"
    ]
    
    print(f"Обрабатываем {len(files_to_process)} файлов...")
    
    # Batch обработка
    results = resolver.batch_resolve(files_to_process)
    
    # Анализ результатов
    successful = 0
    failed = 0
    total_score = 0.0
    processing_time = 0.0
    
    print("\nРезультаты обработки:")
    print("-" * 40)
    
    for result in results:
        if result["success"]:
            successful += 1
            metadata = result["data"].get("_metadata", {})
            score = metadata.get("truth_score", 0)
            time = metadata.get("processing_time", 0)
            total_score += score
            processing_time += time
            
            status = "✅" if score >= 0.95 else "⚠️" if score >= 0.80 else "❌"
            print(f"{status} {result['file']}: Score {score:.2f}, Time {time:.3f}s")
        else:
            failed += 1
            print(f"❌ {result['file']}: {result['error']}")
    
    # Статистика
    print("\n📊 Статистика:")
    print(f"   Успешно: {successful}/{len(files_to_process)}")
    print(f"   Ошибки: {failed}")
    if successful > 0:
        avg_score = total_score / successful
        print(f"   Средний Truth Score: {avg_score:.3f}")
        print(f"   Общее время: {processing_time:.2f}с")
        print(f"   Среднее время: {processing_time/successful:.3f}с")


# ============================================================================
# ПРИМЕР 5: API интерфейс для агентов
# ============================================================================
def example_api_interface():
    """Использование API интерфейса для интеграции с агентами."""
    print("\n" + "="*60)
    print("ПРИМЕР 5: API интерфейс для агентов")
    print("="*60)
    
    # Создаем API интерфейс
    api = SDUIResolverAPI(
        base_path="/Users/username/Documents/front-middle-schema/SDUI",
        metaschema_path="/Users/username/Documents/front-middle-schema/metaschemas/strict_unversioned.json"
    )
    
    # Пример запросов от агента
    agent_requests = [
        {
            "action": "resolve",
            "file_path": "screens/salary/get-salary.json"
        },
        {
            "action": "validate",
            "file_path": "components/Button.json"
        },
        {
            "action": "calculate_score",
            "file_path": "templates/form-template.json"
        },
        {
            "action": "extract_patterns",
            "file_path": "screens/profile/user-profile.json"
        },
        {
            "action": "batch",
            "files": [
                "components/Input.json",
                "components/Button.json",
                "components/Text.json"
            ]
        }
    ]
    
    print("Обработка запросов от агента:\n")
    
    for i, request in enumerate(agent_requests, 1):
        print(f"📨 Запрос {i}: {request['action']}")
        
        # Обработка запроса
        response = api.process_request(request)
        
        # Анализ ответа
        if response["success"]:
            print(f"   ✅ Успешно обработан")
            
            if "truth_score" in response:
                print(f"   Truth Score: {response['truth_score']:.3f}")
            
            if request["action"] == "validate":
                validation = response["data"]
                if validation["valid"]:
                    print(f"   Валидация пройдена")
                else:
                    print(f"   Найдено ошибок: {len(validation['errors'])}")
            
            elif request["action"] == "extract_patterns":
                patterns = response["data"]
                print(f"   Найдено StateAware паттернов: {len(patterns)}")
            
            elif request["action"] == "batch":
                results = response["data"]
                successful = sum(1 for r in results if r["success"])
                print(f"   Обработано файлов: {successful}/{len(results)}")
        else:
            print(f"   ❌ Ошибка: {response.get('error', 'Unknown')}")
        
        print()


# ============================================================================
# ПРИМЕР 6: Генерация карты компонентов
# ============================================================================  
def example_component_map():
    """Построение карты компонентов и их взаимосвязей."""
    print("\n" + "="*60)
    print("ПРИМЕР 6: Карта компонентов и связей")
    print("="*60)
    
    config = ResolverConfig(
        base_path="/Users/username/Documents/front-middle-schema/SDUI",
        web_only=True,
        verbose=False
    )
    
    resolver = SDUIEnhancedResolver(config)
    
    # Разрешаем схему
    resolved = resolver.resolve_file("screens/salary/get-salary.json")
    
    # Генерируем карту компонентов
    component_map = resolver.generate_component_map(resolved)
    
    print("📍 Карта компонентов:")
    
    # Компоненты
    components = component_map["components"]
    print(f"\nВсего уникальных компонентов: {len(components)}")
    
    # Топ-5 по использованию
    sorted_components = sorted(
        components.items(), 
        key=lambda x: x[1]["count"], 
        reverse=True
    )[:5]
    
    print("\nТоп-5 компонентов по частоте:")
    for comp_name, comp_data in sorted_components:
        print(f"   {comp_name}: {comp_data['count']} использований")
        if comp_data["paths"]:
            print(f"      Первое вхождение: {comp_data['paths'][0]}")
    
    # Связи
    references = component_map["references"]
    print(f"\nВсего связей между компонентами: {len(references)}")
    
    # Примеры связей
    if references:
        print("\nПримеры связей:")
        for ref in references[:3]:
            print(f"   {ref['from']} → {ref['to']} (тип: {ref['type']})")
    
    # Иерархия
    hierarchy = component_map["hierarchy"]
    
    def print_hierarchy(node, level=0):
        """Рекурсивная печать иерархии."""
        indent = "  " * level
        print(f"{indent}├─ {node['type']}")
        for child in node.get("children", [])[:2]:  # Первые 2 дочерних
            print_hierarchy(child, level + 1)
        if len(node.get("children", [])) > 2:
            print(f"{indent}  └─ ... еще {len(node['children']) - 2}")
    
    print("\nИерархия компонентов:")
    print_hierarchy(hierarchy)
    
    # Статистика
    stats = component_map["statistics"]
    print(f"\n📊 Статистика:")
    print(f"   Общее количество компонентов: {stats['total_components']}")
    print(f"   Уникальных компонентов: {stats['unique_types']}")
    print(f"   Максимальная глубина: {stats['max_depth']}")
    if stats['stateaware_count'] > 0:
        print(f"   StateAware компонентов: {stats['stateaware_count']}")


# ============================================================================
# ПРИМЕР 7: Проверка required полей
# ============================================================================
def example_required_fields_validation():
    """Детальная проверка обязательных полей по схеме."""
    print("\n" + "="*60)
    print("ПРИМЕР 7: Валидация required полей")
    print("="*60)
    
    config = ResolverConfig(
        base_path="/Users/username/Documents/front-middle-schema/SDUI",
        validation_level=ValidationLevel.STRICT,
        verbose=False
    )
    
    resolver = SDUIEnhancedResolver(config)
    
    # Тестовый контракт с пропущенными полями
    test_contract = {
        "type": "Button",
        "text": "Нажми меня",
        # "action" - обязательное поле отсутствует
        "style": {
            "color": "#FF0000"
            # "backgroundColor" - может быть обязательным
        }
    }
    
    # Схема компонента (упрощенная)
    button_schema = {
        "type": "object",
        "required": ["type", "text", "action"],
        "properties": {
            "type": {"type": "string"},
            "text": {"type": "string"},
            "action": {"type": "object"},
            "style": {
                "type": "object",
                "required": ["backgroundColor"],
                "properties": {
                    "color": {"type": "string"},
                    "backgroundColor": {"type": "string"}
                }
            }
        }
    }
    
    # Валидация
    validation = resolver.validate_required_fields(test_contract, button_schema)
    
    print("📋 Результат валидации required полей:")
    
    if validation["valid"]:
        print("   ✅ Все обязательные поля присутствуют")
    else:
        print("   ❌ Найдены проблемы:")
        
        if validation["missing_fields"]:
            print(f"\n   Отсутствующие обязательные поля:")
            for field in validation["missing_fields"]:
                print(f"      - {field}")
        
        if validation["type_mismatches"]:
            print(f"\n   Несоответствие типов:")
            for mismatch in validation["type_mismatches"]:
                print(f"      - {mismatch['field']}: ожидался {mismatch['expected']}, получен {mismatch['actual']}")
        
        if validation["extra_fields"]:
            print(f"\n   Лишние поля (не в схеме):")
            for field in validation["extra_fields"]:
                print(f"      - {field}")
    
    # Влияние на Truth Score
    missing_count = len(validation.get("missing_fields", []))
    type_mismatch_count = len(validation.get("type_mismatches", []))
    
    score_penalty = (missing_count * 0.1) + (type_mismatch_count * 0.05)
    final_score = max(0, 1.0 - score_penalty)
    
    print(f"\n📊 Влияние на Truth Score:")
    print(f"   Штраф за отсутствующие поля: -{missing_count * 0.1:.2f}")
    print(f"   Штраф за несоответствие типов: -{type_mismatch_count * 0.05:.2f}")
    print(f"   Итоговый Truth Score: {final_score:.2f}")


# ============================================================================
# ГЛАВНАЯ ФУНКЦИЯ - запуск всех примеров
# ============================================================================
def main():
    """Запуск примеров использования SDUI Enhanced Resolver."""
    
    print("╔" + "═"*58 + "╗")
    print("║" + " SDUI ENHANCED RESOLVER - ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ ".center(58) + "║")
    print("╚" + "═"*58 + "╝")
    
    examples = [
        ("Базовое разрешение", example_basic_resolution),
        ("Валидация с метасхемой", example_validation_with_metaschema),
        ("StateAware паттерны", example_stateaware_patterns),
        ("Batch обработка", example_batch_processing),
        ("API интерфейс", example_api_interface),
        ("Карта компонентов", example_component_map),
        ("Required поля", example_required_fields_validation)
    ]
    
    print("\nДоступные примеры:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")
    
    print("\nВыберите пример (1-7) или 'all' для запуска всех: ", end="")
    
    try:
        choice = input().strip().lower()
        
        if choice == 'all':
            for name, func in examples:
                try:
                    func()
                except Exception as e:
                    print(f"\n❌ Ошибка в примере '{name}': {e}")
        elif choice.isdigit() and 1 <= int(choice) <= len(examples):
            idx = int(choice) - 1
            name, func = examples[idx]
            func()
        else:
            print("❌ Неверный выбор")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Прервано пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {e}")
        sys.exit(1)
    
    print("\n" + "="*60)
    print("✅ Примеры выполнены успешно!")
    print("="*60)


if __name__ == "__main__":
    main()