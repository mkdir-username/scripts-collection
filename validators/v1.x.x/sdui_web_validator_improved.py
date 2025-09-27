#!/usr/bin/env python3
"""
Улучшенный валидатор SDUI контрактов для WEB платформы
- Поддержка children
- Без ограничения глубины
- Автоматическая адаптация Android компонентов
"""

import json
from typing import Dict, List, Any, Tuple, Optional
from pathlib import Path
from datetime import datetime

class SDUIWebValidatorImproved:
    """Улучшенный валидатор SDUI для WEB с поддержкой Android контрактов"""

    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root or "/Users/username/Documents/front-middle-schema")

        # Маппинг Android → WEB компонентов
        self.component_mapping = {
            "LabelView": "TextView",
            "setValue": "updateState",
            "sequence": "chain",
            "AndroidButton": "ButtonView",
            "IOSButton": "ButtonView"
        }

        # WEB-совместимые компоненты (расширенный список)
        self.web_components = {
            "TextView", "ButtonView", "ImageView", "StackView", "ScrollWrapper",
            "ConstraintWrapper", "BannerWrapper", "IconView", "Spacer",
            "TextField", "TagView", "SwitchView", "StepView", "SquareWrapper",
            "SpinnerView", "Slider", "SkeletonView", "CardIconView", "CarouselWrapper"
        }

        # Действия (actions) - не компоненты
        self.actions = {
            "deeplink", "HttpAction", "updateState", "chain", "navigate",
            "openUrl", "copy", "share", "close", "back"
        }

        # Известные enum значения (не компоненты)
        self.enum_values = {
            "center", "scale", "top", "bottom", "left", "right",
            "topAndBottom", "leftAndRight", "all", "fill", "start", "end", "middle",
            "horizontal", "vertical", "control", "focus", "selection",
            "none", "small", "medium", "large", "auto", "manual",
            "zero", "xs", "s", "m", "l", "xl", "xxl"
        }

    def convert_android_to_web(self, contract: Any) -> Any:
        """Конвертация Android контракта в WEB-совместимый"""
        if isinstance(contract, dict):
            converted = {}

            for key, value in contract.items():
                # Пропускаем Android-специфичные поля на корневом уровне
                if key in ["lifecycleEvents", "state", "androidSpecific", "iosSpecific"]:
                    continue

                # Конвертируем тип компонента
                if key == "type" and isinstance(value, str):
                    if value in self.component_mapping:
                        converted[key] = self.component_mapping[value]
                        print(f"  🔄 {value} → {self.component_mapping[value]}")
                    else:
                        converted[key] = value
                # Рекурсивно обрабатываем children (поддерживаем и $children)
                elif key in ["children", "$children"] and isinstance(value, list):
                    # Всегда конвертируем $children в children для WEB
                    converted["children"] = [self.convert_android_to_web(child) for child in value]
                # Рекурсивно обрабатываем вложенные объекты
                else:
                    converted[key] = self.convert_android_to_web(value)

            return converted

        elif isinstance(contract, list):
            return [self.convert_android_to_web(item) for item in contract]

        return contract

    def validate_contract(
        self,
        contract: Dict,
        strict: bool = False,
        auto_fix: bool = False
    ) -> Tuple[bool, Dict, Optional[Dict]]:
        """Валидация контракта"""

        report = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "info": [],
            "web_compatibility": 100,
            "timestamp": datetime.now().isoformat()
        }

        # Конвертируем Android компоненты
        fixed_contract = self.convert_android_to_web(contract) if auto_fix else contract

        # Валидация структуры
        self._validate_structure(fixed_contract, report)

        # Валидация компонентов
        self._validate_components(fixed_contract, report)

        # Расчет WEB совместимости
        report["web_compatibility"] = self._calculate_web_compatibility(fixed_contract)

        # Определяем валидность
        report["valid"] = len(report["errors"]) == 0

        return report["valid"], report, fixed_contract if auto_fix else None

    def _validate_structure(self, contract: Any, report: Dict, path: str = "root"):
        """Валидация структуры контракта"""
        if isinstance(contract, dict):
            # Проверяем тип компонента
            if "type" in contract:
                comp_type = contract["type"]

                # Проверяем, что это компонент, а не enum или action
                if comp_type not in self.enum_values and comp_type not in self.actions:
                    if comp_type not in self.web_components:
                        # Проверяем, есть ли маппинг
                        if comp_type not in self.component_mapping:
                            report["errors"].append(f"{path}: Неизвестный компонент '{comp_type}'")

            # Рекурсивно проверяем children (поддерживаем и $children)
            for children_key in ["children", "$children"]:
                if children_key in contract:
                    children = contract[children_key]
                    if isinstance(children, list):
                        for i, child in enumerate(children):
                            self._validate_structure(child, report, f"{path}.{children_key}[{i}]")
                    else:
                        report["warnings"].append(f"{path}.{children_key} должно быть массивом")
                    break  # Обрабатываем только один из вариантов

            # Рекурсивно проверяем content
            if "content" in contract:
                self._validate_structure(contract["content"], report, f"{path}.content")

            # Проверяем другие вложенные объекты
            for key, value in contract.items():
                if key not in ["type", "children", "content"] and isinstance(value, (dict, list)):
                    self._validate_structure(value, report, f"{path}.{key}")

        elif isinstance(contract, list):
            for i, item in enumerate(contract):
                self._validate_structure(item, report, f"{path}[{i}]")

    def _validate_components(self, contract: Any, report: Dict):
        """Валидация использованных компонентов"""
        components_count = {}

        def count_components(node):
            if isinstance(node, dict):
                if "type" in node:
                    comp_type = node["type"]
                    # Считаем только компоненты, не enum и не actions
                    if comp_type not in self.enum_values and comp_type not in self.actions:
                        components_count[comp_type] = components_count.get(comp_type, 0) + 1

                # Обрабатываем children (поддерживаем и $children)
                for children_key in ["children", "$children"]:
                    if children_key in node and isinstance(node[children_key], list):
                        for child in node[children_key]:
                            count_components(child)
                        break

                # Обрабатываем остальные поля
                for value in node.values():
                    if isinstance(value, (dict, list)):
                        count_components(value)

            elif isinstance(node, list):
                for item in node:
                    count_components(item)

        count_components(contract)

        # Добавляем информацию о компонентах
        report["info"].append(f"Использовано компонентов: {sum(components_count.values())}")
        report["info"].append(f"Уникальных компонентов: {len(components_count)}")

    def _calculate_web_compatibility(self, contract: Any) -> int:
        """Расчет процента WEB совместимости"""
        total = 0
        compatible = 0

        def check_compatibility(node):
            nonlocal total, compatible

            if isinstance(node, dict):
                if "type" in node:
                    comp_type = node["type"]
                    # Проверяем только компоненты
                    if comp_type not in self.enum_values and comp_type not in self.actions:
                        total += 1
                        if comp_type in self.web_components:
                            compatible += 1

                # Проверяем children (поддерживаем и $children)
                for children_key in ["children", "$children"]:
                    if children_key in node and isinstance(node[children_key], list):
                        for child in node[children_key]:
                            check_compatibility(child)
                        break

                # Проверяем остальные поля
                for value in node.values():
                    if isinstance(value, (dict, list)):
                        check_compatibility(value)

            elif isinstance(node, list):
                for item in node:
                    check_compatibility(item)

        check_compatibility(contract)

        if total == 0:
            return 100

        return int((compatible / total) * 100)


def test_improved_validator():
    """Тест улучшенного валидатора"""

    print("🧪 Тестирование улучшенного валидатора\n")
    print("=" * 60)

    # Загружаем rootElement
    contract_path = '.JSON/ANDROID/main-screen/[FULL_NN]_main-screen.json'

    with open(contract_path, 'r', encoding='utf-8') as f:
        full_contract = json.load(f)

    if 'rootElement' not in full_contract:
        print("❌ rootElement не найден")
        return

    root_element = full_contract['rootElement']

    # Создаем валидатор
    validator = SDUIWebValidatorImproved()

    # Валидация с автоматической конвертацией
    print("\n📋 Валидация rootElement:")
    print("-" * 40)

    valid, report, fixed = validator.validate_contract(
        root_element,
        strict=False,
        auto_fix=True
    )

    print(f"✅ Статус: {'ВАЛИДНО' if valid else 'НЕВАЛИДНО'}")
    print(f"🌐 WEB совместимость: {report['web_compatibility']}%")
    print(f"🔴 Ошибок: {len(report['errors'])}")
    print(f"🟡 Предупреждений: {len(report['warnings'])}")

    if report['errors']:
        print("\nОшибки:")
        for error in report['errors'][:5]:
            print(f"  • {error}")

    print("\nИнформация:")
    for info in report['info']:
        print(f"  ℹ️ {info}")

    # Сохраняем результат
    if fixed:
        output_path = '.JSON/ANDROID/main-screen/root_element_improved.json'
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(fixed, f, indent=2, ensure_ascii=False)
        print(f"\n✅ Сохранена улучшенная версия: {output_path}")


if __name__ == "__main__":
    test_improved_validator()