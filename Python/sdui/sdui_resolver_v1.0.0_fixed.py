#!/usr/bin/env python3
"""
SDUI Schema Final Resolver - ИСПРАВЛЕННАЯ ВЕРСИЯ
Исправлены критические баги, найденные при валидации
"""

import json
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
import argparse
from copy import deepcopy

@dataclass
class ComponentTracker:
    """Отслеживание компонентов и их первых вхождений"""
    first_occurrences: Dict[str, str] = field(default_factory=dict)  # name -> first_path
    occurrences_count: Dict[str, int] = field(default_factory=dict)   # name -> count
    component_contexts: Dict[str, str] = field(default_factory=dict)  # path -> component_name

    def register_component(self, name: str, path: str) -> Tuple[bool, Optional[str]]:
        """
        Регистрирует компонент и возвращает (нужно_развернуть, путь_к_первому)
        """
        # Сохраняем контекст компонента для данного пути
        self.component_contexts[path] = name

        if name not in self.first_occurrences:
            # Первое вхождение - запоминаем путь
            self.first_occurrences[name] = path
            self.occurrences_count[name] = 1
            return True, None
        else:
            # Повторное вхождение
            self.occurrences_count[name] += 1

            # Специальные правила для циклических компонентов
            if name in ["LayoutElement", "LayoutElementContent", "Action"]:
                max_copies = 2
            else:
                max_copies = 3

            if self.occurrences_count[name] <= max_copies:
                return True, None
            else:
                # Возвращаем путь к первому вхождению
                return False, self.first_occurrences[name]

    def get_component_at_path(self, path: str) -> Optional[str]:
        """Получить имя компонента по пути"""
        # Ищем ближайший родительский путь с компонентом
        while path:
            if path in self.component_contexts:
                return self.component_contexts[path]
            # Удаляем последний сегмент пути
            parts = path.rsplit('.', 1)
            path = parts[0] if len(parts) > 1 else ""
        return None

@dataclass
class ResolveContext:
    """Контекст разрешения с внутренней навигацией"""
    max_depth: int = 50
    web_only: bool = False

    # Tracking
    depth: int = 0
    path_stack: List[str] = field(default_factory=list)
    tracker: ComponentTracker = field(default_factory=ComponentTracker)
    resolved_cache: Dict[str, Any] = field(default_factory=dict)
    current_component_name: Optional[str] = None  # Текущий компонент

    # Statistics
    total_resolutions: int = 0
    stub_count: int = 0

    def get_current_path(self) -> str:
        """Получить текущий путь в документе"""
        # Используем "root" для пустого пути
        return ".".join(self.path_stack) if self.path_stack else "root"

class SDUIFinalResolver:
    def __init__(self, base_path: str, verbose: bool = False):
        self.base_path = Path(base_path)
        self.verbose = verbose
        self.warnings: List[str] = []
        self.errors: List[str] = []

    def log(self, message: str, level: str = "INFO"):
        if self.verbose:
            print(f"[{level}] {message}")

    def load_json_file(self, file_path: Path) -> Optional[Dict]:
        """Загрузить JSON файл"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.errors.append(f"Cannot load {file_path}: {e}")
            return None

    def resolve_ref_path(self, ref: str, current_file: Path) -> Tuple[Path, Optional[str]]:
        """Преобразовать $ref в путь к файлу и фрагмент"""
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

    def validate_internal_ref_format(self, ref_path: str) -> bool:
        """Валидация формата внутренней ссылки"""
        if not ref_path.startswith("#/"):
            return False

        # Проверяем, что путь содержит только валидные сегменты
        parts = ref_path[2:].split("/")
        for part in parts:
            if not part:  # Пустой сегмент
                return False
            # Можно добавить дополнительные проверки
        return True

    def resolve_internal_ref(self, schema: Dict, ref_path: str) -> Optional[Dict]:
        """Разрешить внутреннюю ссылку #/definitions/..."""
        if not ref_path.startswith("#/"):
            return None

        # Валидация формата
        if not self.validate_internal_ref_format(ref_path):
            self.log(f"Invalid internal reference format: {ref_path}", "WARNING")
            return None

        parts = ref_path[2:].split("/")
        current = schema

        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None

        return current

    def check_web_release(self, schema: Dict) -> bool:
        """Проверить совместимость с web"""
        if not isinstance(schema, dict):
            return True

        release = schema.get("releaseVersion", {})
        if not release:
            return True

        web_status = release.get("web", "notReleased")
        return web_status == "released" or (isinstance(web_status, str) and web_status[0:1].isdigit())

    def create_internal_stub(self, ref: str, name: str, first_path: str, reason: str = "duplicate") -> Dict:
        """
        Создать заглушку с ВНУТРЕННЕЙ ссылкой на первое вхождение
        """
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
        """Разрешить $ref с использованием внутренних координат"""

        context.total_resolutions += 1

        # Сохраняем текущий компонент и путь
        current_path = context.get_current_path()
        current_component = context.tracker.get_component_at_path(current_path)

        # Проверка глубины
        if context.depth >= context.max_depth:
            context.stub_count += 1
            # Находим первое вхождение текущего компонента
            first_path = None
            if current_component:
                first_path = context.tracker.first_occurrences.get(current_component)

            stub = {
                "_ref_stub": True,
                "_original_ref": ref,
                "_reason": "max_depth_reached",
                "type": "object",
                "description": "Maximum depth reached"
            }

            # Добавляем информацию о компоненте и пути, если есть
            if current_component:
                stub["_component_name"] = current_component
            if first_path:
                stub["_first_occurrence_path"] = first_path
                stub["description"] = f"Maximum depth reached. See {first_path} for definition"

            return stub

        # Парсинг ссылки
        target_file, fragment = self.resolve_ref_path(ref, current_file)

        # Внутренняя ссылка
        if ref.startswith("#/") and parent_schema:
            # Проверяем формат
            if not self.validate_internal_ref_format(ref):
                return {"_error": f"Invalid reference format: {ref}"}

            resolved = self.resolve_internal_ref(parent_schema, ref)
            if resolved:
                return self.resolve_schema(resolved, current_file, parent_schema, context)
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
        if context.web_only and not self.check_web_release(target_schema):
            context.stub_count += 1
            return {
                "_ref_stub": True,
                "_original_ref": ref,
                "_reason": "not_web_released",
                "type": "object"
            }

        # Получаем имя компонента
        component_name = target_schema.get("name", str(target_file.stem))
        context.current_component_name = component_name

        # Проверяем, нужно ли разворачивать
        should_expand, first_path = context.tracker.register_component(component_name, current_path)

        if not should_expand and first_path:
            # Создаем заглушку с ВНУТРЕННЕЙ ссылкой
            context.stub_count += 1
            return self.create_internal_stub(
                ref,
                component_name,
                first_path,
                f"duplicate_limit_reached_{component_name}"
            )

        # Резолв фрагмента если есть
        if fragment:
            if not self.validate_internal_ref_format(fragment):
                return {"_error": f"Invalid fragment format: {fragment}"}

            resolved = self.resolve_internal_ref(target_schema, fragment)
            if resolved:
                return self.resolve_schema(resolved, target_file, target_schema, context)

        # Полный резолв схемы
        return self.resolve_schema(target_schema, target_file, target_schema, context)

    def resolve_schema(self, schema: Any, current_file: Path, root_schema: Dict, context: ResolveContext) -> Any:
        """Рекурсивно разрешить схему"""

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
                        for key in ["required", "description", "default"]:
                            if key in schema and key not in result:
                                result[key] = schema[key]
                        return result

                    # Если это заглушка, добавляем оригинальные поля
                    if isinstance(resolved, dict) and resolved.get("_ref_stub"):
                        for key in ["required", "description", "default"]:
                            if key in schema:
                                resolved[key] = schema[key]

                    return resolved

                # Обработка oneOf, anyOf, allOf
                for key in ["oneOf", "anyOf", "allOf"]:
                    if key in schema:
                        context.path_stack.append(key)
                        schema[key] = [
                            self.resolve_schema(item, current_file, root_schema, context)
                            for i, item in enumerate(schema[key])
                        ]
                        context.path_stack.pop()

                # Рекурсивная обработка остальных полей
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

    def create_navigation_index(self, schema: Any, path: str = "root") -> Dict[str, List[str]]:
        """Создать индекс всех компонентов с их путями"""
        index = {}

        def traverse(obj: Any, current_path: str):
            if isinstance(obj, dict):
                # Индексируем компонент (включая безымянные)
                if not obj.get("_ref_stub"):
                    # Пытаемся получить имя
                    name = None
                    if "name" in obj and isinstance(obj["name"], str):
                        name = obj["name"]
                    elif current_path == "root" and "type" in obj:
                        # Для корневого объекта без имени используем тип или "RootSchema"
                        name = "RootSchema"

                    if name:
                        if name not in index:
                            index[name] = []
                        index[name].append(current_path)

                # Рекурсивный обход
                for key, value in obj.items():
                    if not key.startswith("_"):  # Пропускаем метаданные
                        new_path = f"{current_path}.{key}" if current_path != "root" else key
                        traverse(value, new_path)

            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    new_path = f"{current_path}[{i}]"
                    traverse(item, new_path)

        traverse(schema, "root")
        return index

    def resolve_file(self, file_path: str, web_only: bool = False, max_depth: int = 50) -> Dict:
        """Главная функция разрешения файла"""
        input_file = Path(file_path).resolve()

        self.log(f"Starting final resolution of {input_file}")

        # Загрузка схемы
        schema = self.load_json_file(input_file)
        if not schema:
            raise ValueError(f"Cannot load input file: {input_file}")

        # Если у схемы нет имени, добавляем на основе файла
        if "name" not in schema:
            schema["name"] = input_file.stem

        # Создание контекста
        context = ResolveContext(
            max_depth=max_depth,
            web_only=web_only
        )

        # Регистрируем корневой компонент
        root_name = schema.get("name", "RootSchema")
        context.tracker.register_component(root_name, "root")

        # Разрешение схемы
        resolved = self.resolve_schema(schema, input_file, schema, context)

        # Создание навигационного индекса
        navigation_index = self.create_navigation_index(resolved)

        # Добавление метаданных
        resolved["_metadata"] = {
            "original_file": str(input_file),
            "total_resolutions": context.total_resolutions,
            "total_stubs": context.stub_count,
            "unique_components": len(context.tracker.first_occurrences),
            "component_stats": dict(context.tracker.occurrences_count),
            "navigation_index": {
                name: {
                    "count": len(paths),
                    "first_path": paths[0] if paths else None
                }
                for name, paths in navigation_index.items()
            }
        }

        return resolved

def main():
    parser = argparse.ArgumentParser(
        description="SDUI Final Resolver - FIXED VERSION with internal navigation coordinates"
    )
    parser.add_argument("input_file", help="Input SDUI schema JSON file")
    parser.add_argument("-o", "--output", help="Output file path")
    parser.add_argument("--web-only", action="store_true", help="Filter web-only elements")
    parser.add_argument("--max-depth", type=int, default=50, help="Maximum recursion depth")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--pretty", action="store_true", help="Pretty print output")

    args = parser.parse_args()

    # Определение base path
    input_path = Path(args.input_file).resolve()
    base_path = str(input_path.parent)
    for parent in input_path.parents:
        if parent.name == "SDUI":
            base_path = str(parent)
            break

    # Создание resolver
    resolver = SDUIFinalResolver(base_path, verbose=args.verbose)

    try:
        # Разрешение схемы
        resolved = resolver.resolve_file(
            args.input_file,
            web_only=args.web_only,
            max_depth=args.max_depth
        )

        # Вывод результата
        output_file = args.output or f"{input_path.stem}_final.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            if args.pretty:
                json.dump(resolved, f, ensure_ascii=False, indent=2)
            else:
                json.dump(resolved, f, ensure_ascii=False)

        print(f"✅ Successfully resolved to: {output_file}")

        # Статистика
        metadata = resolved.get("_metadata", {})
        print(f"\n📊 Statistics:")
        print(f"  - Total resolutions: {metadata.get('total_resolutions', 0)}")
        print(f"  - Total stubs created: {metadata.get('total_stubs', 0)}")
        print(f"  - Unique components: {metadata.get('unique_components', 0)}")

        # Показать топ дублированных компонентов
        stats = metadata.get("component_stats", {})
        if stats:
            print(f"\n  Top duplicated components:")
            for name, count in sorted(stats.items(), key=lambda x: x[1], reverse=True)[:5]:
                nav_info = metadata.get("navigation_index", {}).get(name, {})
                first_path = nav_info.get("first_path", "unknown")
                print(f"    - {name}: {count} occurrences (first at: {first_path})")

    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()