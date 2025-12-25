"""
SDUI Computed Validator
=======================
Валидация секции computed: проверка типов, ссылок, структуры.

Основная проблема которую решает:
"Ошибка типа вычисляемой функции. Объект по ключу ${computed.X} не является вычисляемой функцией"

Причина: в computed секции находится UI-компонент (StackView, LabelView, etc.)
вместо computed-функции (if, switch, applyTemplate, etc.)
"""

import re
import json
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Any
from enum import Enum

from .config import VALID_COMPUTED_TYPES, KNOWN_UI_COMPONENTS


class Severity(Enum):
    """Уровень серьезности проблемы"""
    ERROR = "error"      # Гарантированно сломает рендеринг
    WARNING = "warning"  # Потенциальная проблема
    INFO = "info"        # Информационное сообщение


@dataclass
class ValidationIssue:
    """Описание найденной проблемы"""
    severity: Severity
    code: str           # Уникальный код ошибки (COMP-001, REF-002, etc.)
    key: str            # Ключ в computed секции
    message: str        # Человекочитаемое сообщение
    hint: str           # Подсказка по исправлению
    found_type: Optional[str] = None
    location: Optional[str] = None  # Где найдена ссылка (если применимо)


@dataclass 
class ValidationResult:
    """Результат валидации"""
    is_valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    computed_keys: Set[str] = field(default_factory=set)
    valid_computed_keys: Set[str] = field(default_factory=set)
    invalid_computed_keys: Dict[str, str] = field(default_factory=dict)  # key → type
    
    @property
    def errors(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == Severity.ERROR]
    
    @property
    def warnings(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == Severity.WARNING]
    
    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0


def validate_computed_types(data: Dict[str, Any]) -> List[ValidationIssue]:
    """
    Проверяет что все объекты в computed секции имеют валидные computed-типы.
    
    UI-компоненты (StackView, LabelView, etc.) не должны находиться в computed.
    
    Args:
        data: Распарсенный JSON контракт
        
    Returns:
        List[ValidationIssue]: Найденные проблемы
    """
    issues = []
    computed = data.get("computed", {})
    
    for key, value in computed.items():
        if not isinstance(value, dict):
            continue
            
        obj_type = value.get("type", "")
        
        if not obj_type:
            # Нет type — возможно это просто данные, не функция
            continue
            
        # Проверка на известные UI-компоненты
        if obj_type in KNOWN_UI_COMPONENTS:
            issues.append(ValidationIssue(
                severity=Severity.ERROR,
                code="COMP-001",
                key=key,
                found_type=obj_type,
                message=f"computed.{key} имеет type='{obj_type}' — это UI-компонент, не computed-функция",
                hint=f"Перенеси '{key}' в секцию data или template. В computed используй только if/switch/applyTemplate для ссылки на него."
            ))
        elif obj_type not in VALID_COMPUTED_TYPES:
            # Неизвестный тип — может быть новый компонент
            issues.append(ValidationIssue(
                severity=Severity.WARNING,
                code="COMP-002", 
                key=key,
                found_type=obj_type,
                message=f"computed.{key} имеет неизвестный type='{obj_type}'",
                hint=f"Проверь: если это UI-компонент — перенеси в data/template. Если новая computed-функция — добавь в VALID_COMPUTED_TYPES."
            ))
    
    return issues


def find_computed_references(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Находит все ссылки ${computed.X} в JSON контракте.
    
    Args:
        data: Распарсенный JSON контракт
        
    Returns:
        List[Dict]: Список найденных ссылок с метаданными
    """
    references = []
    content_str = json.dumps(data, ensure_ascii=False)
    
    # Pattern для ${computed.keyName}
    pattern = r'\$\{computed\.(\w+)\}'
    
    for match in re.finditer(pattern, content_str):
        ref_key = match.group(1)
        # Находим контекст (несколько символов вокруг)
        start = max(0, match.start() - 50)
        end = min(len(content_str), match.end() + 50)
        context = content_str[start:end]
        
        references.append({
            "key": ref_key,
            "full_ref": match.group(0),
            "context": context,
            "position": match.start()
        })
    
    return references


def validate_computed_references(data: Dict[str, Any]) -> List[ValidationIssue]:
    """
    Проверяет что все ${computed.X} ссылки указывают на валидные computed-функции.
    
    Args:
        data: Распарсенный JSON контракт
        
    Returns:
        List[ValidationIssue]: Найденные проблемы
    """
    issues = []
    computed = data.get("computed", {})
    
    # Классифицируем computed ключи
    valid_keys = set()
    invalid_keys = {}  # key → type
    
    for key, value in computed.items():
        if isinstance(value, dict):
            obj_type = value.get("type", "")
            if obj_type in VALID_COMPUTED_TYPES:
                valid_keys.add(key)
            elif obj_type in KNOWN_UI_COMPONENTS:
                invalid_keys[key] = obj_type
            elif obj_type:
                # Неизвестный тип — помечаем как потенциально невалидный
                invalid_keys[key] = obj_type
    
    # Находим все ссылки
    references = find_computed_references(data)
    
    # Проверяем каждую ссылку
    seen_refs = set()  # Чтобы не дублировать ошибки
    
    for ref in references:
        ref_key = ref["key"]
        
        if ref_key in seen_refs:
            continue
        seen_refs.add(ref_key)
        
        if ref_key in invalid_keys:
            issues.append(ValidationIssue(
                severity=Severity.ERROR,
                code="REF-001",
                key=ref_key,
                found_type=invalid_keys[ref_key],
                message=f"${{computed.{ref_key}}} ссылается на '{invalid_keys[ref_key]}' — это не computed-функция",
                hint=f"SDUI ожидает if/switch/applyTemplate. Используй ${{data.{ref_key}}} или ${{template.{ref_key}}} вместо computed.",
                location=ref["context"][:80] + "..." if len(ref["context"]) > 80 else ref["context"]
            ))
        elif ref_key not in computed:
            issues.append(ValidationIssue(
                severity=Severity.ERROR,
                code="REF-002",
                key=ref_key,
                message=f"${{computed.{ref_key}}} ссылается на несуществующий ключ",
                hint=f"Добавь '{ref_key}' в секцию computed или исправь имя ссылки."
            ))
    
    return issues


def validate_nested_computed_calls(data: Dict[str, Any]) -> List[ValidationIssue]:
    """
    Проверяет вложенные вызовы computed в $children и других массивах.
    
    Ищет паттерн где $children содержит ${computed.X} где X — не computed-функция.
    """
    issues = []
    computed = data.get("computed", {})
    
    # Собираем невалидные ключи
    invalid_keys = {}
    for key, value in computed.items():
        if isinstance(value, dict):
            obj_type = value.get("type", "")
            if obj_type and obj_type not in VALID_COMPUTED_TYPES:
                invalid_keys[key] = obj_type
    
    # Рекурсивно ищем $children с computed ссылками
    def check_children(obj, path="root"):
        if isinstance(obj, dict):
            children = obj.get("$children", [])
            if isinstance(children, list):
                for i, child in enumerate(children):
                    if isinstance(child, str) and child.startswith("${computed."):
                        # Извлекаем ключ
                        match = re.match(r'\$\{computed\.(\w+)\}', child)
                        if match:
                            ref_key = match.group(1)
                            if ref_key in invalid_keys:
                                issues.append(ValidationIssue(
                                    severity=Severity.ERROR,
                                    code="CHILD-001",
                                    key=ref_key,
                                    found_type=invalid_keys[ref_key],
                                    message=f"$children[{i}] содержит ${{computed.{ref_key}}} типа '{invalid_keys[ref_key]}'",
                                    hint=f"В $children можно использовать только computed-функции (if/switch) или прямые компоненты.",
                                    location=path
                                ))
            
            # Рекурсия
            for k, v in obj.items():
                check_children(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                check_children(item, f"{path}[{i}]")
    
    check_children(data)
    return issues


def validate_sdui_contract(json_content: str) -> ValidationResult:
    """
    Полная валидация SDUI контракта.
    
    Проверяет:
    1. Типы в computed секции
    2. Ссылки ${computed.X}
    3. Использование в $children
    
    Args:
        json_content: JSON строка или уже распарсенный dict
        
    Returns:
        ValidationResult: Полный результат валидации
    """
    # Parse JSON if string
    if isinstance(json_content, str):
        try:
            data = json.loads(json_content)
        except json.JSONDecodeError as e:
            return ValidationResult(
                is_valid=False,
                issues=[ValidationIssue(
                    severity=Severity.ERROR,
                    code="JSON-001",
                    key="",
                    message=f"Invalid JSON: {e.msg} at line {e.lineno}",
                    hint="Fix JSON syntax first"
                )]
            )
    else:
        data = json_content
    
    # Collect all issues
    all_issues = []
    
    # Check 1: Computed types
    all_issues.extend(validate_computed_types(data))
    
    # Check 2: Computed references  
    all_issues.extend(validate_computed_references(data))
    
    # Check 3: Nested children
    all_issues.extend(validate_nested_computed_calls(data))
    
    # Build result
    computed = data.get("computed", {})
    valid_keys = set()
    invalid_keys = {}
    
    for key, value in computed.items():
        if isinstance(value, dict):
            obj_type = value.get("type", "")
            if obj_type in VALID_COMPUTED_TYPES:
                valid_keys.add(key)
            elif obj_type:
                invalid_keys[key] = obj_type
    
    return ValidationResult(
        is_valid=len([i for i in all_issues if i.severity == Severity.ERROR]) == 0,
        issues=all_issues,
        computed_keys=set(computed.keys()),
        valid_computed_keys=valid_keys,
        invalid_computed_keys=invalid_keys
    )


def format_validation_report(result: ValidationResult, verbose: bool = False) -> str:
    """
    Форматирует результат валидации в читаемый отчет.
    
    Args:
        result: Результат валидации
        verbose: Показывать ли дополнительную информацию
        
    Returns:
        str: Отформатированный отчет
    """
    lines = []
    
    if result.is_valid:
        lines.append("✅ SDUI Computed Validation: PASSED")
        if result.warnings:
            lines.append(f"   ({len(result.warnings)} warning(s))")
    else:
        lines.append("❌ SDUI Computed Validation: FAILED")
        lines.append(f"   {len(result.errors)} error(s), {len(result.warnings)} warning(s)")
    
    lines.append("")
    
    # Group by severity
    if result.errors:
        lines.append("=" * 60)
        lines.append("ERRORS (will break runtime):")
        lines.append("=" * 60)
        for issue in result.errors:
            lines.append(f"  [{issue.code}] {issue.message}")
            lines.append(f"     💡 {issue.hint}")
            if verbose and issue.location:
                lines.append(f"     📍 {issue.location}")
            lines.append("")
    
    if result.warnings:
        lines.append("-" * 60)
        lines.append("WARNINGS (potential issues):")
        lines.append("-" * 60)
        for issue in result.warnings:
            lines.append(f"  [{issue.code}] {issue.message}")
            lines.append(f"     💡 {issue.hint}")
            lines.append("")
    
    if verbose:
        lines.append("-" * 60)
        lines.append("COMPUTED SUMMARY:")
        lines.append("-" * 60)
        lines.append(f"  Total keys: {len(result.computed_keys)}")
        lines.append(f"  Valid computed-functions: {len(result.valid_computed_keys)}")
        lines.append(f"  Invalid (UI components): {len(result.invalid_computed_keys)}")
        
        if result.valid_computed_keys:
            lines.append(f"\n  ✓ Valid: {', '.join(sorted(result.valid_computed_keys))}")
        if result.invalid_computed_keys:
            lines.append(f"\n  ✗ Invalid:")
            for k, t in sorted(result.invalid_computed_keys.items()):
                lines.append(f"      {k}: {t}")
    
    return "\n".join(lines)


# ==================== CLI Interface ====================

def validate_file(file_path: str, verbose: bool = False) -> bool:
    """
    Валидирует JSON файл и выводит отчет.
    
    Args:
        file_path: Путь к JSON файлу
        verbose: Подробный вывод
        
    Returns:
        bool: True если валидация прошла без ошибок
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
        return False
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False
    
    result = validate_sdui_contract(content)
    report = format_validation_report(result, verbose=verbose)
    print(report)
    
    return result.is_valid


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python validators.py <json_file> [--verbose]")
        sys.exit(1)
    
    file_path = sys.argv[1]
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    
    success = validate_file(file_path, verbose=verbose)
    sys.exit(0 if success else 1)
