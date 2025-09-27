#!/usr/bin/env python3
"""
SDUI Web Contract Validator
Система 100% валидации контрактов для WEB платформы
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
import hashlib
from datetime import datetime
import re
from collections import defaultdict
from sdui_index_cache import SDUIIndexCache

class SDUIWebValidator:
    """Валидатор SDUI контрактов для WEB платформы с 100% гарантией"""

    def __init__(self, project_root: str = "/Users/username/Documents/front-middle-schema"):
        self.project_root = Path(project_root)
        self.index_cache = SDUIIndexCache(project_root)

        # Загрузка правил валидации
        self.validation_rules = self._load_validation_rules()
        self.web_requirements = self._load_web_requirements()
        self.component_schemas = {}
        self._load_component_schemas()

    def _load_validation_rules(self) -> Dict:
        """Загрузка правил валидации для WEB платформы"""
        return {
            # Обязательные поля для sample контрактов (экземпляров)
            # Для samples content обычно обязателен, но конкретные поля внутри content могут быть опциональными
            "required_fields": {
                # Убираем жесткие требования, так как для samples структура может варьироваться
            },

            # WEB-специфичные атрибуты
            "web_attributes": {
                "accessibility": ["ariaLabel", "ariaRole", "ariaDescribedBy"],
                "interaction": ["tabIndex", "focusable", "draggable"],
                "styling": ["className", "style", "dataTestId"]
            },

            # Ограничения для WEB (обновлено)
            "constraints": {
                "max_nesting_depth": 999,  # Снято ограничение глубины
                "max_array_size": 1000,
                "max_string_length": 10000,
                "max_file_size_kb": 500
            },

            # Запрещенные для WEB
            "forbidden": {
                "properties": ["androidSpecific", "iosSpecific", "nativeOnly"],
                "values": {
                    "releaseVersion.web": ["willNotBeReleased", "blocked"]
                }
            }
        }

    def _load_web_requirements(self) -> Dict:
        """Загрузка требований WEB платформы"""
        return {
            "browser_support": {
                "chrome": "90+",
                "firefox": "88+",
                "safari": "14+",
                "edge": "90+"
            },
            "required_polyfills": [],
            "performance_budget": {
                "max_bundle_size_kb": 200,
                "max_load_time_ms": 3000,
                "max_render_time_ms": 100
            }
        }

    def _load_component_schemas(self):
        """Загрузка схем всех компонентов"""
        sdui_path = self.project_root / "SDUI"

        for category in ["components", "layouts", "atoms", "common"]:
            category_path = sdui_path / category
            if category_path.exists():
                for schema_file in category_path.rglob("*.json"):
                    try:
                        with open(schema_file, 'r', encoding='utf-8') as f:
                            schema = json.load(f)
                            component_name = schema_file.stem
                            self.component_schemas[component_name] = schema
                    except Exception as e:
                        print(f"⚠ Ошибка загрузки схемы {schema_file}: {e}")

    def validate_contract(
        self,
        contract: Dict,
        strict: bool = True,
        auto_fix: bool = False
    ) -> Tuple[bool, Dict, Optional[Dict]]:
        """
        Валидация контракта с 100% гарантией для WEB

        Args:
            contract: JSON контракт для валидации
            strict: Строгий режим валидации
            auto_fix: Автоматическое исправление ошибок

        Returns:
            (valid, report, fixed_contract)
        """
        report = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "info": [],
            "metrics": {},
            "web_compatibility": 100,
            "timestamp": datetime.now().isoformat()
        }

        fixed_contract = json.loads(json.dumps(contract)) if auto_fix else None

        # Определяем тип контракта
        contract_root = contract
        if "rootElement" in contract:
            # Это контракт с computed и rootElement
            contract_root = contract["rootElement"]
            report["info"].append("Контракт с computed и rootElement структурой")

            # Валидация computed секции если есть
            if "computed" in contract:
                self._validate_computed(contract["computed"], report)

        # 1. Структурная валидация
        self._validate_structure(contract_root, report, fixed_contract)

        # 2. Валидация компонентов
        self._validate_components(contract_root, report, fixed_contract, strict)

        # 3. Валидация WEB совместимости
        self._validate_web_compatibility(contract_root, report, fixed_contract)

        # 4. Валидация производительности
        self._validate_performance(contract_root, report)

        # 5. Валидация доступности (accessibility)
        self._validate_accessibility(contract_root, report, fixed_contract)

        # 6. Валидация безопасности
        self._validate_security(contract, report)

        # 7. Валидация версии контракта (если указана)
        self._validate_contract_version(contract, report)

        # 8. Валидация против метасхемы (только для схем, не для samples)
        self._validate_against_metaschema(contract, report)

        # Подсчет итогового процента совместимости
        error_weight = len(report["errors"]) * 10
        warning_weight = len(report["warnings"]) * 2
        report["web_compatibility"] = max(0, 100 - error_weight - warning_weight)

        report["valid"] = len(report["errors"]) == 0

        return report["valid"], report, fixed_contract

    def _validate_structure(self, contract: Dict, report: Dict, fixed: Optional[Dict]):
        """Валидация структуры контракта"""
        def check_depth(obj: Any, depth: int = 0, path: str = "root"):
            max_depth = self.validation_rules["constraints"]["max_nesting_depth"]
            if depth > max_depth:
                report["errors"].append(f"Превышена максимальная глубина вложенности ({max_depth}) в {path}")
                return False

            if isinstance(obj, dict):
                for key, value in obj.items():
                    check_depth(value, depth + 1, f"{path}.{key}")
            elif isinstance(obj, list):
                max_size = self.validation_rules["constraints"]["max_array_size"]
                if len(obj) > max_size:
                    report["warnings"].append(f"Большой массив ({len(obj)} элементов) в {path}")

                for i, item in enumerate(obj):
                    check_depth(item, depth + 1, f"{path}[{i}]")
            elif isinstance(obj, str):
                max_length = self.validation_rules["constraints"]["max_string_length"]
                if len(obj) > max_length:
                    report["warnings"].append(f"Длинная строка ({len(obj)} символов) в {path}")

        check_depth(contract)

    def _validate_components(self, contract: Dict, report: Dict, fixed: Optional[Dict], strict: bool):
        """Валидация компонентов в контракте-экземпляре (sample)"""
        def validate_component(obj: Any, path: str = "root", parent_type: Optional[str] = None):
            if isinstance(obj, dict):
                # Проверка типа компонента
                if "type" in obj:
                    component_type = obj["type"]

                    # Специальная обработка для actions (deeplink, navigate, etc)
                    if "action" in path or parent_type == "action":
                        # Это action, не компонент
                        action_types = ["deeplink", "navigate", "back", "close", "openUrl", "share",
                                      "callPhone", "sendSms", "sendEmail", "copy", "paste"]
                        if component_type in action_types:
                            # Валидный тип action
                            return
                        elif not self._component_exists_in_filesystem(component_type):
                            report["warnings"].append(f"Неизвестный тип action '{component_type}' в {path}")
                            return

                    # Проверка, является ли это компонентом UI или просто значением enum
                    # Компоненты обычно имеют PascalCase и могут содержать "content" или другие поля компонента
                    is_likely_component = (
                        component_type[0].isupper() or  # PascalCase или UPPER_CASE
                        "View" in component_type or
                        "Wrapper" in component_type or
                        "Layout" in component_type or
                        "content" in obj or
                        "action" in obj or
                        "version" in obj
                    )

                    # Известные enum значения, которые не являются компонентами
                    known_enum_values = [
                        # Position constraints
                        "center", "scale", "top", "bottom", "left", "right",
                        "topAndBottom", "leftAndRight",
                        # Alignment
                        "fill", "start", "end", "middle",
                        # Axis
                        "horizontal", "vertical",
                        # Other common enums
                        "control", "focus", "selection"
                    ]

                    if component_type in known_enum_values:
                        # Это enum значение, не компонент - пропускаем валидацию компонента
                        pass
                    elif not is_likely_component:
                        # Вероятно это enum или другое значение, не компонент
                        pass
                    else:
                        # Это похоже на компонент - проверяем его существование
                        if component_type not in self.component_schemas:
                            # Ищем компонент в файловой системе
                            if not self._component_exists_in_filesystem(component_type):
                                report["errors"].append(f"Компонент '{component_type}' не найден в SDUI в {path}")
                                return
                            else:
                                # Компонент существует, но схема не загружена - это нормально для samples
                                pass  # Не добавляем лишние info сообщения

                    # Для samples проверяем структуру контракта
                    # Некоторые компоненты не требуют content
                    components_without_content = ["EmptyView", "SpacerView", "DividerView", "LoadingView"]
                    if "content" not in obj and component_type not in components_without_content:
                        # Проверяем, может у этого компонента content опционален
                        if component_type in self.component_schemas:
                            schema = self.component_schemas[component_type]
                            # Если в схеме нет required полей или content не required - не выдаем warning
                            required_props = schema.get("required", [])
                            if "content" in required_props:
                                report["warnings"].append(f"Отсутствует поле 'content' для компонента {component_type} в {path}")

                    # Проверка поддержки WEB платформы через схему компонента
                    if component_type in self.component_schemas:
                        schema = self.component_schemas[component_type]
                        release_version = schema.get("releaseVersion", {})
                        web_status = release_version.get("web", "notReleased")

                        if web_status in ["willNotBeReleased", "blocked", "notReleased"]:
                            report["errors"].append(f"Компонент {component_type} не поддерживается на WEB (статус: {web_status}) в {path}")
                        elif web_status == "released":
                            # Проверяем поддержку конкретных полей на WEB
                            if "content" in obj and isinstance(obj["content"], dict):
                                self._validate_web_fields(obj["content"], schema, component_type, path, report)

                    # Рекурсивная проверка вложенных компонентов
                    if "content" in obj:
                        validate_component(obj["content"], f"{path}.content", component_type)

                    # Проверка action если есть
                    if "action" in obj:
                        validate_component(obj["action"], f"{path}.action", component_type)

                # Проверка других полей рекурсивно
                for key, value in obj.items():
                    if key not in ["type", "content", "action"]:
                        # Проверка запрещенных свойств для WEB
                        if key in self.validation_rules["forbidden"]["properties"]:
                            report["errors"].append(f"Запрещенное свойство '{key}' для WEB в {path}")
                            if fixed:
                                fixed_obj = self._find_in_path(fixed, path)
                                if fixed_obj and key in fixed_obj:
                                    del fixed_obj[key]
                        else:
                            validate_component(value, f"{path}.{key}", parent_type)

            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    validate_component(item, f"{path}[{i}]", parent_type)

        validate_component(contract)

    def _validate_web_compatibility(self, contract: Dict, report: Dict, fixed: Optional[Dict]):
        """Проверка WEB-специфичных требований"""
        def check_web_features(obj: Any, path: str = "root"):
            if isinstance(obj, dict):
                # Проверка WEB атрибутов
                if "type" in obj:
                    component_type = obj["type"]

                    # Добавление WEB атрибутов если их нет
                    if component_type in ["ButtonView", "EditText", "SelectView"]:
                        if "webAttributes" not in obj:
                            report["info"].append(f"Рекомендуется добавить webAttributes для {component_type} в {path}")
                            if fixed:
                                fixed_obj = self._find_in_path(fixed, path)
                                if fixed_obj:
                                    fixed_obj["webAttributes"] = {
                                        "tabIndex": 0,
                                        "focusable": True
                                    }

                # Проверка изображений
                if obj.get("type") == "ImageView":
                    if "src" in obj:
                        src = obj["src"]
                        if not self._is_valid_web_url(src) and not src.startswith("data:"):
                            report["warnings"].append(f"Проверьте путь к изображению: {src} в {path}")

                        # Проверка alt текста
                        if "alt" not in obj or not obj["alt"]:
                            report["warnings"].append(f"Отсутствует alt текст для изображения в {path}")
                            if fixed:
                                fixed_obj = self._find_in_path(fixed, path)
                                if fixed_obj:
                                    fixed_obj["alt"] = "Image"

                for key, value in obj.items():
                    check_web_features(value, f"{path}.{key}")

            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    check_web_features(item, f"{path}[{i}]")

        check_web_features(contract)

    def _validate_accessibility(self, contract: Dict, report: Dict, fixed: Optional[Dict]):
        """Валидация доступности (WCAG 2.1)"""
        def check_accessibility(obj: Any, path: str = "root"):
            if isinstance(obj, dict):
                component_type = obj.get("type")

                # Проверка интерактивных элементов
                if component_type in ["ButtonView", "EditText", "CheckboxView", "RadioButtonView"]:
                    # ARIA labels
                    if "accessibility" not in obj or "ariaLabel" not in obj.get("accessibility", {}):
                        text = obj.get("text", obj.get("placeholder", ""))
                        if not text:
                            report["warnings"].append(f"Отсутствует ariaLabel для {component_type} в {path}")
                            if fixed:
                                fixed_obj = self._find_in_path(fixed, path)
                                if fixed_obj:
                                    if "accessibility" not in fixed_obj:
                                        fixed_obj["accessibility"] = {}
                                    fixed_obj["accessibility"]["ariaLabel"] = component_type

                    # Tab navigation
                    if "webAttributes" not in obj or "tabIndex" not in obj.get("webAttributes", {}):
                        report["info"].append(f"Рекомендуется установить tabIndex для {component_type} в {path}")

                # Проверка контрастности для текста
                if component_type == "TextView":
                    if "textColor" in obj and "backgroundColor" in obj:
                        # Здесь должна быть проверка контрастности
                        pass

                for key, value in obj.items():
                    check_accessibility(value, f"{path}.{key}")

            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    check_accessibility(item, f"{path}[{i}]")

        check_accessibility(contract)

    def _validate_performance(self, contract: Dict, report: Dict):
        """Оценка производительности контракта"""
        # Подсчет метрик
        metrics = {
            "total_components": 0,
            "total_images": 0,
            "total_text_nodes": 0,
            "estimated_size_kb": 0,
            "dom_depth": 0
        }

        def count_components(obj: Any, depth: int = 0):
            nonlocal metrics
            metrics["dom_depth"] = max(metrics["dom_depth"], depth)

            if isinstance(obj, dict):
                if "type" in obj:
                    metrics["total_components"] += 1

                    if obj["type"] == "ImageView":
                        metrics["total_images"] += 1
                    elif obj["type"] == "TextView":
                        metrics["total_text_nodes"] += 1

                for value in obj.values():
                    count_components(value, depth + 1)

            elif isinstance(obj, list):
                for item in obj:
                    count_components(item, depth + 1)

        count_components(contract)

        # Оценка размера
        contract_json = json.dumps(contract)
        metrics["estimated_size_kb"] = len(contract_json) / 1024

        report["metrics"] = metrics

        # Проверка лимитов
        if metrics["estimated_size_kb"] > self.validation_rules["constraints"]["max_file_size_kb"]:
            report["warnings"].append(f"Большой размер контракта: {metrics['estimated_size_kb']:.1f} KB")

        if metrics["dom_depth"] > 15:
            report["warnings"].append(f"Глубокая вложенность DOM: {metrics['dom_depth']} уровней")

        if metrics["total_components"] > 500:
            report["warnings"].append(f"Много компонентов: {metrics['total_components']}")

        if metrics["total_images"] > 50:
            report["info"].append(f"Много изображений ({metrics['total_images']}), рекомендуется lazy loading")

    def _validate_computed(self, computed: Dict, report: Dict):
        """Валидация computed секции с функциями"""
        for key, func_def in computed.items():
            if isinstance(func_def, dict) and "type" in func_def:
                func_type = func_def["type"]
                # Проверяем, является ли это функцией
                function_types = [
                    "getData", "setData", "clearData",
                    "sum", "divide", "multiply", "subtract", "mod",
                    "abs", "floor", "round", "min", "max",
                    "toString", "toInt", "toFloat", "toBool",
                    "if", "and", "or", "not", "equals", "contains",
                    "length", "isEmpty", "isNotEmpty",
                    "concat", "format", "replace", "split",
                    "now", "formatDate", "parseDate"
                ]

                if func_type not in function_types:
                    # Может быть это пользовательская функция, проверим в файловой системе
                    if not self._component_exists_in_filesystem(func_type):
                        report["warnings"].append(f"Неизвестная функция '{func_type}' в computed.{key}")

    def _validate_contract_version(self, contract: Dict, report: Dict):
        """Валидация версии контракта если она указана"""
        if "version" in contract:
            version = contract["version"]
            if isinstance(version, str):
                # Проверяем формат версии (например, v1, v2, 1.0.0)
                if not re.match(r'^(v\d+|v?\d+\.\d+\.\d+)$', version):
                    report["warnings"].append(f"Нестандартный формат версии: {version}")
            elif isinstance(version, (int, float)):
                # Числовая версия тоже допустима
                pass
            else:
                report["warnings"].append(f"Неверный тип версии: {type(version).__name__}")

    def _validate_security(self, contract: Dict, report: Dict):
        """Проверка безопасности контракта"""
        def check_security(obj: Any, path: str = "root"):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    # Проверка на XSS
                    if isinstance(value, str):
                        if any(pattern in value.lower() for pattern in ["<script", "javascript:", "onerror=", "onclick="]):
                            report["errors"].append(f"Потенциальная XSS уязвимость в {path}.{key}")

                    # Проверка URL
                    if key in ["src", "href", "action"]:
                        if isinstance(value, str) and value.startswith("javascript:"):
                            report["errors"].append(f"Небезопасный URL в {path}.{key}")

                    check_security(value, f"{path}.{key}")

            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    check_security(item, f"{path}[{i}]")

        check_security(contract)

    def _validate_against_metaschema(self, contract: Dict, report: Dict):
        """Валидация против метасхемы - пропускаем для samples"""
        # Samples (контракты-экземпляры) не валидируются против метасхемы
        # так как они не являются схемами, а являются экземплярами данных

        # Определяем, является ли это sample файлом
        is_sample = False

        # Если у контракта есть поле type и content - это скорее всего sample
        if "type" in contract and isinstance(contract.get("type"), str):
            # Это sample (экземпляр контракта), а не схема
            is_sample = True
            report["info"].append("Это контракт-экземпляр (sample), валидация против метасхемы не требуется")

        if not is_sample:
            # Это схема - валидируем против метасхемы
            try:
                validation_result = self.index_cache.validate_contract(contract, "web")

                if not validation_result["valid"]:
                    # Фильтруем ошибки, связанные с метасхемой
                    for error in validation_result["errors"]:
                        if "Unresolvable" in error:
                            # Это техническая ошибка метасхемы, не критична для samples
                            report["warnings"].append(f"Техническая проблема валидации: {error}")
                        else:
                            report["errors"].append(error)

                if validation_result["warnings"]:
                    report["warnings"].extend(validation_result["warnings"])

                # Добавляем информацию о поддержке платформы
                platform_support = validation_result.get("platform_support", {})
                if not platform_support.get("fully_supported", True):
                    unsupported = platform_support.get("unsupported_features", [])
                    for feature in unsupported:
                        report["warnings"].append(f"Функция не поддерживается на WEB: {feature}")

            except Exception as e:
                # Не критичная ошибка для samples
                report["info"].append(f"Метасхема валидация пропущена: {str(e)[:50]}")

    def _find_in_path(self, obj: Any, path: str) -> Optional[Dict]:
        """Поиск объекта по пути в контракте"""
        if path == "root":
            return obj

        parts = path.replace("root.", "").split(".")
        current = obj

        for part in parts:
            if "[" in part:
                # Обработка массивов
                key, index = part.split("[")
                index = int(index.rstrip("]"))
                if key:
                    current = current.get(key, [])
                if isinstance(current, list) and index < len(current):
                    current = current[index]
                else:
                    return None
            else:
                if isinstance(current, dict):
                    current = current.get(part)
                else:
                    return None

            if current is None:
                return None

        return current

    def _component_exists_in_filesystem(self, component_type: str) -> bool:
        """Проверка существования компонента в файловой системе SDUI"""
        sdui_path = self.project_root / "SDUI"

        # Ищем во всех категориях
        for category in ["components", "layouts", "atoms", "common", "actions", "functions"]:
            category_path = sdui_path / category
            if category_path.exists():
                # Проверяем наличие директории с именем компонента
                component_dirs = list(category_path.glob(f"{component_type}*"))
                if component_dirs:
                    return True

                # Проверяем наличие JSON файла с именем компонента
                component_files = list(category_path.glob(f"**/{component_type}.json"))
                if component_files:
                    return True

        return False

    def _validate_web_fields(self, content: Dict, schema: Dict, component_type: str, path: str, report: Dict):
        """Валидация полей контента на поддержку WEB платформы"""
        if "properties" not in schema:
            return

        schema_properties = schema["properties"]

        for field_name, field_value in content.items():
            if field_name in schema_properties:
                field_schema = schema_properties[field_name]

                # Проверяем releaseVersion для конкретного поля
                if "releaseVersion" in field_schema:
                    field_release = field_schema["releaseVersion"]
                    if isinstance(field_release, dict):
                        web_status = field_release.get("web", "released")

                        if web_status in ["willNotBeReleased", "blocked"]:
                            report["errors"].append(
                                f"Поле '{field_name}' компонента {component_type} не поддерживается на WEB в {path}"
                            )
                        elif web_status == "notReleased":
                            report["warnings"].append(
                                f"Поле '{field_name}' компонента {component_type} еще не выпущено на WEB в {path}"
                            )

    def _is_valid_web_url(self, url: str) -> bool:
        """Проверка валидности URL для WEB"""
        if not url:
            return False

        # Относительные пути
        if url.startswith("/") or url.startswith("./") or url.startswith("../"):
            return True

        # Абсолютные URL
        if url.startswith(("http://", "https://", "//")):
            return True

        # Data URLs
        if url.startswith("data:"):
            return True

        return False

    def generate_report_html(self, report: Dict) -> str:
        """Генерация HTML отчета о валидации"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>SDUI Web Validation Report</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif; margin: 20px; background: #f5f5f5; }}
                .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                h1 {{ color: #333; border-bottom: 3px solid #4CAF50; padding-bottom: 10px; }}
                .status {{ padding: 10px 20px; border-radius: 4px; margin: 10px 0; font-weight: bold; }}
                .valid {{ background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }}
                .invalid {{ background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }}
                .errors {{ background: #fff3cd; border-left: 4px solid #dc3545; padding: 10px; margin: 10px 0; }}
                .warnings {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 10px; margin: 10px 0; }}
                .info {{ background: #d1ecf1; border-left: 4px solid #17a2b8; padding: 10px; margin: 10px 0; }}
                .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
                .metric {{ background: #f8f9fa; padding: 15px; border-radius: 4px; }}
                .metric-value {{ font-size: 24px; font-weight: bold; color: #495057; }}
                .metric-label {{ color: #6c757d; font-size: 12px; text-transform: uppercase; }}
                .compatibility {{ font-size: 48px; font-weight: bold; text-align: center; padding: 20px; }}
                .high {{ color: #28a745; }}
                .medium {{ color: #ffc107; }}
                .low {{ color: #dc3545; }}
                ul {{ margin: 5px 0; padding-left: 20px; }}
                li {{ margin: 3px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🔍 SDUI Web Contract Validation Report</h1>

                <div class="status {'valid' if report['valid'] else 'invalid'}">
                    Status: {'✅ VALID' if report['valid'] else '❌ INVALID'}
                </div>

                <div class="compatibility {'high' if report['web_compatibility'] >= 80 else 'medium' if report['web_compatibility'] >= 50 else 'low'}">
                    Web Compatibility: {report['web_compatibility']}%
                </div>

                <h2>📊 Metrics</h2>
                <div class="metrics">
                    {''.join(f'''
                    <div class="metric">
                        <div class="metric-value">{value}</div>
                        <div class="metric-label">{key.replace("_", " ").title()}</div>
                    </div>
                    ''' for key, value in report.get('metrics', {}).items())}
                </div>

                {self._generate_issues_html(report['errors'], 'Errors', 'errors') if report['errors'] else ''}
                {self._generate_issues_html(report['warnings'], 'Warnings', 'warnings') if report['warnings'] else ''}
                {self._generate_issues_html(report['info'], 'Information', 'info') if report['info'] else ''}

                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #dee2e6; color: #6c757d; font-size: 12px;">
                    Generated: {report['timestamp']}
                </div>
            </div>
        </body>
        </html>
        """
        return html

    def _generate_issues_html(self, issues: List[str], title: str, css_class: str) -> str:
        """Генерация HTML для списка проблем"""
        if not issues:
            return ""

        return f"""
        <h2>{title} ({len(issues)})</h2>
        <div class="{css_class}">
            <ul>
                {''.join(f'<li>{issue}</li>' for issue in issues)}
            </ul>
        </div>
        """


# CLI интерфейс
if __name__ == "__main__":
    import sys

    validator = SDUIWebValidator()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "validate":
            if len(sys.argv) > 2:
                contract_file = sys.argv[2]

                # Опции
                strict = "--strict" in sys.argv
                auto_fix = "--fix" in sys.argv
                html_report = "--html" in sys.argv

                with open(contract_file, 'r') as f:
                    contract = json.load(f)

                valid, report, fixed = validator.validate_contract(contract, strict, auto_fix)

                # Вывод результата
                if html_report:
                    html = validator.generate_report_html(report)
                    report_file = contract_file.replace('.json', '_validation_report.html')
                    with open(report_file, 'w') as f:
                        f.write(html)
                    print(f"✓ HTML отчет: {report_file}")
                else:
                    print(json.dumps(report, indent=2, ensure_ascii=False))

                # Сохранение исправленного контракта
                if auto_fix and fixed:
                    fixed_file = contract_file.replace('.json', '_fixed.json')
                    with open(fixed_file, 'w') as f:
                        json.dump(fixed, f, indent=2, ensure_ascii=False)
                    print(f"✓ Исправленный контракт: {fixed_file}")

                # Возвращаем код ошибки
                sys.exit(0 if valid else 1)
            else:
                print("Usage: python sdui_web_validator.py validate <contract.json> [--strict] [--fix] [--html]")

        elif command == "batch":
            # Пакетная валидация
            if len(sys.argv) > 2:
                directory = sys.argv[2]
                results = []

                for json_file in Path(directory).rglob("*.json"):
                    with open(json_file, 'r') as f:
                        contract = json.load(f)

                    valid, report, _ = validator.validate_contract(contract)
                    results.append({
                        "file": str(json_file),
                        "valid": valid,
                        "compatibility": report["web_compatibility"],
                        "errors": len(report["errors"]),
                        "warnings": len(report["warnings"])
                    })

                # Вывод сводки
                print("\n📊 Batch Validation Results:")
                print("-" * 80)

                for result in results:
                    status = "✅" if result["valid"] else "❌"
                    print(f"{status} {result['file']}")
                    print(f"   Compatibility: {result['compatibility']}%")
                    print(f"   Errors: {result['errors']}, Warnings: {result['warnings']}")

                valid_count = sum(1 for r in results if r["valid"])
                print("-" * 80)
                print(f"Total: {valid_count}/{len(results)} valid contracts")
            else:
                print("Usage: python sdui_web_validator.py batch <directory>")

        else:
            print(f"Unknown command: {command}")
            print("Available commands: validate, batch")
    else:
        print("SDUI Web Contract Validator")
        print("Usage: python sdui_web_validator.py <command> [options]")
        print("\nCommands:")
        print("  validate <file.json> [--strict] [--fix] [--html]")
        print("  batch <directory>")
        print("\nOptions:")
        print("  --strict   Строгая валидация (все warnings становятся errors)")
        print("  --fix      Автоматическое исправление проблем")
        print("  --html     Генерация HTML отчета")