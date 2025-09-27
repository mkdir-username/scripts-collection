#!/usr/bin/env python3
"""
SDUI Schema Enhanced Resolver - улучшенная версия для интеграции с агентами
Добавлены: валидация метасхемы, Truth Score, StateAware паттерны, API интерфейс
"""

import json
import hashlib
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import argparse
from copy import deepcopy
from collections import Counter
import re


# ============== Configuration ==============

@dataclass
class ResolverConfig:
    """Конфигурация резолвера"""
    base_path: Path
    metaschema_path: Optional[Path] = None
    web_only: bool = False
    max_depth: int = 50
    verbose: bool = False
    truth_score_threshold: float = 0.95
    enable_api: bool = False
    api_port: int = 8080
    batch_size: int = 10
    
    def __post_init__(self):
        self.base_path = Path(self.base_path)
        if self.metaschema_path:
            self.metaschema_path = Path(self.metaschema_path)


class ValidationLevel(Enum):
    """Уровни валидации"""
    NONE = "none"
    BASIC = "basic"
    STRICT = "strict"
    METASCHEMA = "metaschema"


# ============== Tracking Classes ==============

@dataclass
class ComponentMetrics:
    """Метрики компонента для расчета Truth Score"""
    name: str
    occurrences: int = 0
    resolved_refs: int = 0
    validation_errors: int = 0
    missing_fields: List[str] = field(default_factory=list)
    web_released: bool = True
    has_required_fields: bool = True
    stateaware_patterns: List[str] = field(default_factory=list)
    
    def calculate_score(self) -> float:
        """Расчет Truth Score компонента"""
        score = 1.0
        
        # Штрафы за ошибки
        if self.validation_errors > 0:
            score -= 0.1 * self.validation_errors
        
        # Штраф за отсутствующие required поля  
        if self.missing_fields:
            score -= 0.05 * len(self.missing_fields)
            
        # Штраф за отсутствие web release
        if not self.web_released:
            score -= 0.2
            
        # Бонус за StateAware паттерны
        if self.stateaware_patterns:
            score += 0.05 * len(self.stateaware_patterns)
            
        return max(0.0, min(1.0, score))


@dataclass 
class ComponentTracker:
    """Расширенное отслеживание компонентов"""
    first_occurrences: Dict[str, str] = field(default_factory=dict)
    occurrences_count: Dict[str, int] = field(default_factory=dict)
    component_metrics: Dict[str, ComponentMetrics] = field(default_factory=dict)
    stateaware_components: Set[str] = field(default_factory=set)
    
    def register_component(self, name: str, path: str, schema: Dict = None) -> Tuple[bool, Optional[str]]:
        """Регистрация компонента с расширенными метриками"""
        if name not in self.component_metrics:
            self.component_metrics[name] = ComponentMetrics(name=name)
            
        metrics = self.component_metrics[name]
        metrics.occurrences += 1
        
        # Детекция StateAware паттернов
        if schema:
            patterns = self._detect_stateaware_patterns(schema)
            metrics.stateaware_patterns.extend(patterns)
            if patterns:
                self.stateaware_components.add(name)
        
        if name not in self.first_occurrences:
            self.first_occurrences[name] = path
            self.occurrences_count[name] = 1
            return True, None
        else:
            self.occurrences_count[name] += 1
            
            # Адаптивные лимиты для разных типов
            if name in self.stateaware_components:
                max_copies = 2  # StateAware компоненты чаще циклические
            elif name in ["LayoutElement", "LayoutElementContent", "Action"]:
                max_copies = 2
            else:
                max_copies = 3
                
            if self.occurrences_count[name] <= max_copies:
                return True, None
            else:
                return False, self.first_occurrences[name]
    
    def _detect_stateaware_patterns(self, schema: Dict) -> List[str]:
        """Обнаружение StateAware паттернов в схеме"""
        patterns = []
        schema_str = json.dumps(schema)
        
        # Паттерны для поиска
        stateaware_patterns = [
            (r'Control<\w+>', 'Control'),
            (r'Focus<\w+>', 'Focus'), 
            (r'Selection<\w+>', 'Selection'),
            (r'StateRef<\w+>', 'StateRef'),
            (r'Binding<\w+>', 'Binding')
        ]
        
        for pattern, name in stateaware_patterns:
            if re.search(pattern, schema_str):
                patterns.append(name)
                
        return patterns
    
    def get_truth_score(self, component_name: str) -> float:
        """Получить Truth Score для компонента"""
        if component_name in self.component_metrics:
            return self.component_metrics[component_name].calculate_score()
        return 0.0


@dataclass
class ResolveContext:
    """Расширенный контекст разрешения"""
    max_depth: int = 50
    web_only: bool = False
    validation_level: ValidationLevel = ValidationLevel.BASIC
    
    # Tracking
    depth: int = 0
    path_stack: List[str] = field(default_factory=list)
    tracker: ComponentTracker = field(default_factory=ComponentTracker)
    resolved_cache: Dict[str, Any] = field(default_factory=dict)
    
    # Statistics
    total_resolutions: int = 0
    stub_count: int = 0
    validation_errors: List[str] = field(default_factory=list)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    
    def get_current_path(self) -> str:
        """Получить текущий путь в документе"""
        return ".".join(self.path_stack)
    
    def add_validation_error(self, error: str):
        """Добавить ошибку валидации"""
        full_error = f"[{self.get_current_path()}] {error}"
        self.validation_errors.append(full_error)


# ============== Main Resolver Class ==============

class SDUIEnhancedResolver:
    """Улучшенный SDUI резолвер с расширенным функционалом"""
    
    def __init__(self, config: ResolverConfig):
        self.config = config
        self.base_path = config.base_path
        self.warnings: List[str] = []
        self.errors: List[str] = []
        
        # Настройка логирования
        self._setup_logging()
        
        # Загрузка метасхемы если указана
        self.metaschema = None
        if config.metaschema_path:
            self.metaschema = self.load_json_file(config.metaschema_path)
    
    def _setup_logging(self):
        """Настройка системы логирования"""
        level = logging.DEBUG if self.config.verbose else logging.INFO
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def log(self, message: str, level: str = "INFO"):
        """Логирование с поддержкой уровней"""
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        log_method(message)
    
    def load_json_file(self, file_path: Path) -> Optional[Dict]:
        """Загрузка JSON файла с валидацией"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.log(f"Loaded {file_path}", "DEBUG")
                return data
        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON in {file_path}: {e}")
            self.log(f"JSON decode error in {file_path}: {e}", "ERROR")
        except Exception as e:
            self.errors.append(f"Cannot load {file_path}: {e}")
            self.log(f"Failed to load {file_path}: {e}", "ERROR")
        return None
    
    # ============== Validation Methods ==============
    
    def validate_against_metaschema(self, contract: Dict, metaschema_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Валидация контракта против метасхемы
        
        Args:
            contract: SDUI контракт для валидации
            metaschema_path: Путь к метасхеме (опционально)
            
        Returns:
            Dict с результатами валидации
        """
        metaschema = self.metaschema
        if metaschema_path:
            metaschema = self.load_json_file(metaschema_path)
            
        if not metaschema:
            return {
                "valid": False,
                "errors": ["No metaschema available for validation"],
                "warnings": []
            }
        
        errors = []
        warnings = []
        
        # Проверка required полей из метасхемы
        required_fields = metaschema.get("required", [])
        for field in required_fields:
            if field not in contract:
                errors.append(f"Missing required field: {field}")
        
        # Проверка типов полей
        properties = metaschema.get("properties", {})
        for field, value in contract.items():
            if field in properties:
                expected_type = properties[field].get("type")
                if not self._check_type(value, expected_type):
                    errors.append(f"Type mismatch for {field}: expected {expected_type}")
        
        # Проверка additionalProperties
        if not metaschema.get("additionalProperties", True):
            extra_fields = set(contract.keys()) - set(properties.keys())
            if extra_fields:
                warnings.append(f"Additional properties found: {extra_fields}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "checked_at": datetime.now().isoformat()
        }
    
    def _check_type(self, value: Any, expected_type: Optional[str]) -> bool:
        """Проверка соответствия типа"""
        if not expected_type:
            return True
            
        type_map = {
            "string": str,
            "number": (int, float),
            "integer": int,
            "boolean": bool,
            "array": list,
            "object": dict,
            "null": type(None)
        }
        
        expected = type_map.get(expected_type)
        if expected:
            return isinstance(value, expected)
        return True
    
    def calculate_truth_score(self, contract: Dict, schema: Optional[Dict] = None) -> float:
        """
        Расчет Truth Score для контракта (детерминистическая метрика)
        
        Args:
            contract: SDUI контракт
            schema: Опциональная схема для сравнения
            
        Returns:
            Truth Score от 0.0 до 1.0
        """
        score = 1.0
        
        # Проверка наличия ключевых полей
        required_fields = ["type", "name"]
        for field in required_fields:
            if field not in contract:
                score -= 0.1
        
        # Проверка валидации против метасхемы
        if self.metaschema:
            validation_result = self.validate_against_metaschema(contract)
            if not validation_result["valid"]:
                score -= 0.05 * len(validation_result["errors"])
        
        # Проверка web release status
        if not self.check_web_released_status(contract):
            score -= 0.15
        
        # Проверка StateAware паттернов
        patterns = self.extract_stateaware_patterns(contract)
        if patterns:
            score += 0.05 * min(len(patterns), 3)  # Бонус за StateAware
        
        # Проверка на наличие заглушек
        stub_count = self._count_stubs(contract)
        if stub_count > 0:
            score -= 0.02 * stub_count
        
        return max(0.0, min(1.0, score))
    
    def _count_stubs(self, obj: Any) -> int:
        """Подсчет количества заглушек в объекте"""
        count = 0
        
        if isinstance(obj, dict):
            if obj.get("_ref_stub"):
                count += 1
            for value in obj.values():
                count += self._count_stubs(value)
        elif isinstance(obj, list):
            for item in obj:
                count += self._count_stubs(item)
                
        return count
    
    # ============== Web Release Methods ==============
    
    def check_web_released_status(self, component: Dict) -> bool:
        """
        Проверка статуса web release компонента
        
        Args:
            component: Компонент для проверки
            
        Returns:
            True если компонент released для web
        """
        if not isinstance(component, dict):
            return True
            
        release = component.get("releaseVersion", {})
        if not release:
            return True  # Если нет информации о release, считаем released
            
        web_status = release.get("web", "notReleased")
        
        # Проверяем различные форматы статуса
        if web_status == "released":
            return True
        if isinstance(web_status, str) and web_status[0:1].isdigit():
            return True  # Версионированный release (например "1.0.0")
        if web_status in ["beta", "alpha", "rc"]:
            return True  # Pre-release версии тоже допускаем
            
        return False
    
    # ============== StateAware Pattern Methods ==============
    
    def extract_stateaware_patterns(self, contract: Dict) -> List[Dict[str, Any]]:
        """
        Извлечение StateAware паттернов из контракта
        
        Args:
            contract: SDUI контракт
            
        Returns:
            Список найденных StateAware паттернов
        """
        patterns = []
        
        def traverse(obj: Any, path: str = ""):
            if isinstance(obj, dict):
                # Проверка на StateAware типы
                if "type" in obj:
                    type_str = str(obj["type"])
                    if any(pattern in type_str for pattern in ["Control", "Focus", "Selection", "StateRef", "Binding"]):
                        patterns.append({
                            "path": path,
                            "type": type_str,
                            "pattern": self._extract_pattern_type(type_str),
                            "details": obj
                        })
                
                # Рекурсивный обход
                for key, value in obj.items():
                    new_path = f"{path}.{key}" if path else key
                    traverse(value, new_path)
                    
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    traverse(item, f"{path}[{i}]")
        
        traverse(contract)
        return patterns
    
    def _extract_pattern_type(self, type_str: str) -> str:
        """Извлечение типа StateAware паттерна"""
        patterns = {
            "Control": r'Control<(\w+)>',
            "Focus": r'Focus<(\w+)>',
            "Selection": r'Selection<(\w+)>',
            "StateRef": r'StateRef<(\w+)>',
            "Binding": r'Binding<(\w+)>'
        }
        
        for name, pattern in patterns.items():
            if re.search(pattern, type_str):
                return name
                
        return "Unknown"
    
    # ============== Component Map Generation ==============
    
    def generate_component_map(self, contract: Dict) -> Dict[str, Any]:
        """
        Генерация карты компонентов с их связями
        
        Args:
            contract: SDUI контракт
            
        Returns:
            Карта компонентов и их взаимосвязей
        """
        component_map = {
            "components": {},
            "references": [],
            "hierarchy": {},
            "statistics": {}
        }
        
        def traverse(obj: Any, path: str = "", parent: str = None):
            if isinstance(obj, dict):
                # Регистрация компонента
                if "name" in obj:
                    name = obj["name"]
                    if name not in component_map["components"]:
                        component_map["components"][name] = {
                            "paths": [],
                            "type": obj.get("type"),
                            "refs": [],
                            "children": []
                        }
                    
                    component_map["components"][name]["paths"].append(path)
                    
                    # Добавление в иерархию
                    if parent:
                        if parent not in component_map["hierarchy"]:
                            component_map["hierarchy"][parent] = []
                        component_map["hierarchy"][parent].append(name)
                    
                    parent = name
                
                # Обработка ссылок
                if "$ref" in obj:
                    ref_info = {
                        "from": path,
                        "to": obj["$ref"],
                        "parent": parent
                    }
                    component_map["references"].append(ref_info)
                
                # Рекурсия
                for key, value in obj.items():
                    if key not in ["$ref"]:
                        new_path = f"{path}.{key}" if path else key
                        traverse(value, new_path, parent)
                        
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    traverse(item, f"{path}[{i}]", parent)
        
        traverse(contract)
        
        # Статистика
        component_map["statistics"] = {
            "total_components": len(component_map["components"]),
            "total_references": len(component_map["references"]),
            "max_depth": self._calculate_max_depth(component_map["hierarchy"])
        }
        
        return component_map
    
    def _calculate_max_depth(self, hierarchy: Dict) -> int:
        """Расчет максимальной глубины иерархии"""
        if not hierarchy:
            return 0
            
        def get_depth(node: str, visited: Set[str] = None) -> int:
            if visited is None:
                visited = set()
                
            if node in visited:
                return 0  # Цикл
                
            visited.add(node)
            
            if node not in hierarchy:
                return 1
                
            max_child_depth = 0
            for child in hierarchy[node]:
                child_depth = get_depth(child, visited.copy())
                max_child_depth = max(max_child_depth, child_depth)
                
            return 1 + max_child_depth
        
        max_depth = 0
        for root in hierarchy:
            depth = get_depth(root)
            max_depth = max(max_depth, depth)
            
        return max_depth
    
    # ============== Required Fields Validation ==============
    
    def validate_required_fields(self, contract: Dict, schema: Dict) -> Dict[str, Any]:
        """
        Валидация required полей контракта против схемы
        
        Args:
            contract: SDUI контракт
            schema: Схема для валидации
            
        Returns:
            Результат валидации
        """
        results = {
            "valid": True,
            "missing_fields": [],
            "type_mismatches": [],
            "extra_fields": []
        }
        
        # Проверка required полей
        required = schema.get("required", [])
        for field in required:
            if field not in contract:
                results["missing_fields"].append(field)
                results["valid"] = False
        
        # Проверка типов
        properties = schema.get("properties", {})
        for field, value in contract.items():
            if field in properties:
                expected = properties[field]
                if "type" in expected:
                    if not self._check_type(value, expected["type"]):
                        results["type_mismatches"].append({
                            "field": field,
                            "expected": expected["type"],
                            "actual": type(value).__name__
                        })
                        results["valid"] = False
        
        # Проверка лишних полей
        if not schema.get("additionalProperties", True):
            schema_fields = set(properties.keys())
            contract_fields = set(contract.keys())
            extra = contract_fields - schema_fields
            if extra:
                results["extra_fields"] = list(extra)
                
        return results
    
    # ============== Original Resolution Methods (Enhanced) ==============
    
    def resolve_ref_path(self, ref: str, current_file: Path) -> Tuple[Path, Optional[str]]:
        """Преобразование $ref в путь к файлу и фрагмент"""
        if ref.startswith("#/"):
            return current_file, ref
        
        parts = ref.split("#")
        file_ref = parts[0]
        fragment = "#" + parts[1] if len(parts) > 1 else None
        
        if not file_ref:
            return current_file, fragment
        
        if not file_ref.endswith(".json"):
            file_ref = f"{file_ref}.json"
        
        resolved_path = (current_file.parent / file_ref).resolve()
        return resolved_path, fragment
    
    def resolve_internal_ref(self, schema: Dict, ref_path: str) -> Optional[Dict]:
        """Разрешение внутренней ссылки #/definitions/..."""
        if not ref_path.startswith("#/"):
            return None
        
        parts = ref_path[2:].split("/")
        current = schema
        
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                self.log(f"Cannot resolve internal ref: {ref_path}", "WARNING")
                return None
        
        return current
    
    def create_internal_stub(self, ref: str, name: str, first_path: str, reason: str = "duplicate") -> Dict:
        """Создание заглушки с внутренней ссылкой"""
        return {
            "_ref_stub": True,
            "_original_ref": ref,
            "_component_name": name,
            "_first_occurrence_path": first_path,
            "_reason": reason,
            "type": "object",
            "description": f"See {first_path} for full definition"
        }
    
    def resolve_reference(self, ref: str, current_file: Path, parent_schema: Dict, context: ResolveContext) -> Any:
        """Разрешение $ref с расширенной функциональностью"""
        context.total_resolutions += 1
        
        # Проверка глубины
        if context.depth >= context.max_depth:
            context.stub_count += 1
            self.log(f"Max depth reached for {ref}", "WARNING")
            return {
                "_ref_stub": True,
                "_original_ref": ref,
                "_reason": "max_depth_reached",
                "type": "object",
                "description": "Maximum depth reached"
            }
        
        # Кеш проверка
        cache_key = f"{current_file}:{ref}"
        if cache_key in context.resolved_cache:
            self.log(f"Using cached resolution for {ref}", "DEBUG")
            return context.resolved_cache[cache_key]
        
        # Парсинг ссылки
        target_file, fragment = self.resolve_ref_path(ref, current_file)
        
        # Внутренняя ссылка
        if ref.startswith("#/") and parent_schema:
            resolved = self.resolve_internal_ref(parent_schema, ref)
            if resolved:
                result = self.resolve_schema(resolved, current_file, parent_schema, context)
                context.resolved_cache[cache_key] = result
                return result
            context.add_validation_error(f"Cannot resolve {ref}")
            return {"_error": f"Cannot resolve {ref}"}
        
        # Загрузка внешнего файла
        target_schema = self.load_json_file(target_file)
        if not target_schema:
            context.stub_count += 1
            return {
                "_ref_stub": True,
                "_original_ref": ref,
                "_reason": "file_not_found",
                "type": "object"
            }
        
        # Проверка web release
        if context.web_only and not self.check_web_released_status(target_schema):
            context.stub_count += 1
            self.log(f"Component {ref} not web released", "INFO")
            return {
                "_ref_stub": True,
                "_original_ref": ref,
                "_reason": "not_web_released",
                "type": "object"
            }
        
        # Получение имени компонента
        component_name = target_schema.get("name", str(target_file.stem))
        current_path = context.get_current_path()
        
        # Регистрация с метриками
        should_expand, first_path = context.tracker.register_component(
            component_name, current_path, target_schema
        )
        
        if not should_expand and first_path:
            context.stub_count += 1
            return self.create_internal_stub(
                ref, component_name, first_path,
                f"duplicate_limit_reached_{component_name}"
            )
        
        # Резолв фрагмента
        if fragment:
            resolved = self.resolve_internal_ref(target_schema, fragment)
            if resolved:
                result = self.resolve_schema(resolved, target_file, target_schema, context)
                context.resolved_cache[cache_key] = result
                return result
        
        # Полный резолв схемы
        result = self.resolve_schema(target_schema, target_file, target_schema, context)
        context.resolved_cache[cache_key] = result
        return result
    
    def resolve_schema(self, schema: Any, current_file: Path, root_schema: Dict, context: ResolveContext) -> Any:
        """Рекурсивное разрешение схемы с расширенной обработкой"""
        context.depth += 1
        
        try:
            if isinstance(schema, dict):
                # Обработка $ref
                if "$ref" in schema:
                    ref = schema["$ref"]
                    resolved = self.resolve_reference(ref, current_file, root_schema, context)
                    
                    # Слияние с оригинальными полями
                    if isinstance(resolved, dict) and not resolved.get("_ref_stub"):
                        result = deepcopy(resolved)
                        for key in ["required", "description", "default", "minItems", "maxItems"]:
                            if key in schema and key not in result:
                                result[key] = schema[key]
                        return result
                    
                    # Добавление оригинальных полей к заглушке
                    if isinstance(resolved, dict) and resolved.get("_ref_stub"):
                        for key in ["required", "description", "default"]:
                            if key in schema:
                                resolved[key] = schema[key]
                    
                    return resolved
                
                # Обработка композиций
                for key in ["oneOf", "anyOf", "allOf"]:
                    if key in schema:
                        context.path_stack.append(key)
                        schema[key] = [
                            self.resolve_schema(item, current_file, root_schema, context)
                            for item in schema[key]
                        ]
                        context.path_stack.pop()
                
                # Рекурсивная обработка
                for key, value in list(schema.items()):
                    if key not in ["$ref", "oneOf", "anyOf", "allOf"]:
                        context.path_stack.append(key)
                        schema[key] = self.resolve_schema(value, current_file, root_schema, context)
                        context.path_stack.pop()
                
            elif isinstance(schema, list):
                result = []
                for i, item in enumerate(schema):
                    context.path_stack.append(f"[{i}]")
                    result.append(self.resolve_schema(item, current_file, root_schema, context))
                    context.path_stack.pop()
                return result
                
        finally:
            context.depth -= 1
        
        return schema
    
    def create_navigation_index(self, schema: Any, path: str = "") -> Dict[str, List[str]]:
        """Создание расширенного навигационного индекса"""
        index = {}
        
        def traverse(obj: Any, current_path: str):
            if isinstance(obj, dict):
                # Индексирование компонента
                if "name" in obj and not obj.get("_ref_stub"):
                    name = obj["name"]
                    if not isinstance(name, str):
                        return
                    if name not in index:
                        index[name] = []
                    index[name].append(current_path)
                
                # Рекурсивный обход
                for key, value in obj.items():
                    new_path = f"{current_path}.{key}" if current_path else key
                    traverse(value, new_path)
                    
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    new_path = f"{current_path}[{i}]"
                    traverse(item, new_path)
        
        traverse(schema, "")
        return index
    
    # ============== Main Resolution Method ==============
    
    def resolve_file(self, file_path: str, context: Optional[ResolveContext] = None) -> Dict:
        """
        Главная функция разрешения файла с расширенными метриками
        
        Args:
            file_path: Путь к входному файлу
            context: Опциональный контекст (создается автоматически если не указан)
            
        Returns:
            Разрешенная схема с метаданными
        """
        input_file = Path(file_path).resolve()
        start_time = datetime.now()
        
        self.log(f"Starting enhanced resolution of {input_file}")
        
        # Загрузка схемы
        schema = self.load_json_file(input_file)
        if not schema:
            raise ValueError(f"Cannot load input file: {input_file}")
        
        # Создание контекста
        if context is None:
            context = ResolveContext(
                max_depth=self.config.max_depth,
                web_only=self.config.web_only,
                validation_level=ValidationLevel.STRICT
            )
        
        # Разрешение схемы
        resolved = self.resolve_schema(schema, input_file, schema, context)
        
        # Создание навигационного индекса
        navigation_index = self.create_navigation_index(resolved)
        
        # Расчет Truth Score
        truth_score = self.calculate_truth_score(resolved)
        
        # Валидация против метасхемы
        validation_result = None
        if self.metaschema:
            validation_result = self.validate_against_metaschema(resolved)
        
        # Извлечение StateAware паттернов
        stateaware_patterns = self.extract_stateaware_patterns(resolved)
        
        # Генерация карты компонентов
        component_map = self.generate_component_map(resolved)
        
        # Время обработки
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Добавление расширенных метаданных
        resolved["_metadata"] = {
            "original_file": str(input_file),
            "processing_time": processing_time,
            "truth_score": truth_score,
            "total_resolutions": context.total_resolutions,
            "total_stubs": context.stub_count,
            "unique_components": len(context.tracker.first_occurrences),
            "component_stats": dict(context.tracker.occurrences_count),
            "stateaware_components": list(context.tracker.stateaware_components),
            "stateaware_patterns": stateaware_patterns,
            "validation_errors": context.validation_errors,
            "validation_result": validation_result,
            "component_map": component_map,
            "navigation_index": {
                name: {
                    "count": len(paths),
                    "first_path": paths[0] if paths else None,
                    "truth_score": context.tracker.get_truth_score(name)
                }
                for name, paths in navigation_index.items()
            },
            "performance": {
                "cache_hits": len(context.resolved_cache),
                "processing_time_ms": processing_time * 1000
            }
        }
        
        self.log(f"Resolution completed with Truth Score: {truth_score:.2f}")
        
        return resolved
    
    # ============== Batch Processing ==============
    
    def batch_resolve(self, file_paths: List[str]) -> List[Dict]:
        """
        Пакетная обработка нескольких файлов
        
        Args:
            file_paths: Список путей к файлам
            
        Returns:
            Список разрешенных схем
        """
        results = []
        total = len(file_paths)
        
        self.log(f"Starting batch resolution of {total} files")
        
        for i, file_path in enumerate(file_paths, 1):
            self.log(f"Processing {i}/{total}: {file_path}")
            try:
                resolved = self.resolve_file(file_path)
                results.append({
                    "file": file_path,
                    "success": True,
                    "data": resolved
                })
            except Exception as e:
                self.log(f"Error processing {file_path}: {e}", "ERROR")
                results.append({
                    "file": file_path,
                    "success": False,
                    "error": str(e)
                })
        
        self.log(f"Batch processing completed: {len(results)} files processed")
        return results


# ============== API Interface ==============

class SDUIResolverAPI:
    """API интерфейс для интеграции с агентами"""
    
    def __init__(self, resolver: SDUIEnhancedResolver):
        self.resolver = resolver
    
    def process_request(self, request: Dict) -> Dict:
        """
        Обработка API запроса
        
        Args:
            request: Запрос в формате JSON-RPC или REST
            
        Returns:
            Результат обработки
        """
        action = request.get("action", "resolve")
        
        if action == "resolve":
            return self._handle_resolve(request)
        elif action == "validate":
            return self._handle_validate(request)
        elif action == "calculate_score":
            return self._handle_score(request)
        elif action == "extract_patterns":
            return self._handle_patterns(request)
        elif action == "batch":
            return self._handle_batch(request)
        else:
            return {"error": f"Unknown action: {action}"}
    
    def _handle_resolve(self, request: Dict) -> Dict:
        """Обработка запроса на разрешение"""
        file_path = request.get("file_path")
        if not file_path:
            return {"error": "file_path is required"}
        
        try:
            resolved = self.resolver.resolve_file(file_path)
            return {"success": True, "data": resolved}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _handle_validate(self, request: Dict) -> Dict:
        """Обработка запроса на валидацию"""
        contract = request.get("contract")
        if not contract:
            return {"error": "contract is required"}
        
        result = self.resolver.validate_against_metaschema(contract)
        return {"success": True, "validation": result}
    
    def _handle_score(self, request: Dict) -> Dict:
        """Обработка запроса на расчет Truth Score"""
        contract = request.get("contract")
        if not contract:
            return {"error": "contract is required"}
        
        score = self.resolver.calculate_truth_score(contract)
        return {"success": True, "truth_score": score}
    
    def _handle_patterns(self, request: Dict) -> Dict:
        """Обработка запроса на извлечение паттернов"""
        contract = request.get("contract")
        if not contract:
            return {"error": "contract is required"}
        
        patterns = self.resolver.extract_stateaware_patterns(contract)
        return {"success": True, "patterns": patterns}
    
    def _handle_batch(self, request: Dict) -> Dict:
        """Обработка пакетного запроса"""
        file_paths = request.get("file_paths", [])
        if not file_paths:
            return {"error": "file_paths is required"}
        
        results = self.resolver.batch_resolve(file_paths)
        return {"success": True, "results": results}


# ============== CLI Interface ==============

def main():
    parser = argparse.ArgumentParser(
        description="SDUI Enhanced Resolver - Advanced version for agent integration"
    )
    parser.add_argument("input_file", help="Input SDUI schema JSON file")
    parser.add_argument("-o", "--output", help="Output file path")
    parser.add_argument("--base-path", help="Base path for SDUI schemas")
    parser.add_argument("--metaschema", help="Path to metaschema for validation")
    parser.add_argument("--web-only", action="store_true", help="Filter web-only elements")
    parser.add_argument("--max-depth", type=int, default=50, help="Maximum recursion depth")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--pretty", action="store_true", help="Pretty print output")
    parser.add_argument("--validate", action="store_true", help="Run validation")
    parser.add_argument("--score", action="store_true", help="Calculate and show Truth Score")
    parser.add_argument("--patterns", action="store_true", help="Extract StateAware patterns")
    parser.add_argument("--api", action="store_true", help="Enable API mode")
    parser.add_argument("--api-port", type=int, default=8080, help="API port")
    
    args = parser.parse_args()
    
    # Определение base path
    input_path = Path(args.input_file).resolve()
    base_path = args.base_path or str(input_path.parent)
    
    # Поиск SDUI директории
    for parent in input_path.parents:
        if parent.name == "SDUI":
            base_path = str(parent)
            break
    
    # Создание конфигурации
    config = ResolverConfig(
        base_path=base_path,
        metaschema_path=Path(args.metaschema) if args.metaschema else None,
        web_only=args.web_only,
        max_depth=args.max_depth,
        verbose=args.verbose,
        enable_api=args.api,
        api_port=args.api_port
    )
    
    # Создание resolver
    resolver = SDUIEnhancedResolver(config)
    
    try:
        # Разрешение схемы
        resolved = resolver.resolve_file(args.input_file)
        
        # Дополнительные операции
        if args.validate and config.metaschema_path:
            validation = resolver.validate_against_metaschema(resolved)
            print(f"\\n✅ Validation: {'PASSED' if validation['valid'] else 'FAILED'}")
            if not validation['valid']:
                for error in validation['errors']:
                    print(f"  ❌ {error}")
        
        if args.score:
            score = resolver.calculate_truth_score(resolved)
            print(f"\\n📊 Truth Score: {score:.2%}")
            if score < config.truth_score_threshold:
                print(f"  ⚠️ Score below threshold ({config.truth_score_threshold:.2%})")
        
        if args.patterns:
            patterns = resolver.extract_stateaware_patterns(resolved)
            if patterns:
                print(f"\\n🎯 Found {len(patterns)} StateAware patterns:")
                for pattern in patterns[:5]:  # Показываем первые 5
                    print(f"  - {pattern['pattern']} at {pattern['path']}")
        
        # Сохранение результата
        output_file = args.output or f"{input_path.stem}_enhanced.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            if args.pretty:
                json.dump(resolved, f, ensure_ascii=False, indent=2)
            else:
                json.dump(resolved, f, ensure_ascii=False)
        
        print(f"\\n✅ Successfully resolved to: {output_file}")
        
        # Статистика
        metadata = resolved.get("_metadata", {})
        print(f"\\n📊 Statistics:")
        print(f"  - Truth Score: {metadata.get('truth_score', 0):.2%}")
        print(f"  - Total resolutions: {metadata.get('total_resolutions', 0)}")
        print(f"  - Total stubs: {metadata.get('total_stubs', 0)}")
        print(f"  - Unique components: {metadata.get('unique_components', 0)}")
        print(f"  - StateAware components: {len(metadata.get('stateaware_components', []))}")
        print(f"  - Processing time: {metadata.get('processing_time', 0):.3f}s")
        
        # API режим
        if args.api:
            print(f"\\n🚀 Starting API server on port {args.api_port}...")
            api = SDUIResolverAPI(resolver)
            # Здесь можно добавить реальный HTTP сервер (Flask, FastAPI и т.д.)
            print("API server started (mock mode)")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())