#!/usr/bin/env python3
"""
SDUI Web Validator v7.0.0
Performance optimized version with IDE-friendly clickable output
Enhanced with Jinja support and versioned component validation
"""

import json
import os
import sys
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import time
from collections import defaultdict
from datetime import datetime
from functools import lru_cache
import hashlib

# Check if terminal supports colors
def supports_color():
    """Check if the terminal supports ANSI color codes"""
    if os.environ.get('NO_COLOR'):
        return False
    if os.environ.get('TERM') == 'dumb':
        return False
    if sys.platform == 'win32':
        return os.environ.get('ANSICON') or os.environ.get('WT_SESSION')
    return hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()

# ANSI colors for output
class Colors:
    if supports_color():
        RED = '\033[91m'
        GREEN = '\033[92m'
        YELLOW = '\033[93m'
        BLUE = '\033[94m'
        MAGENTA = '\033[95m'
        CYAN = '\033[96m'
        WHITE = '\033[97m'
        RESET = '\033[0m'
        BOLD = '\033[1m'
        DIM = '\033[2m'
        UNDERLINE = '\033[4m'
    else:
        RED = ''
        GREEN = ''
        YELLOW = ''
        BLUE = ''
        MAGENTA = ''
        CYAN = ''
        WHITE = ''
        RESET = ''
        BOLD = ''
        DIM = ''
        UNDERLINE = ''

class ErrorType(Enum):
    """Types of validation errors"""
    SCHEMA_NOT_FOUND = "SCHEMA_NOT_FOUND"
    COMPONENT_NOT_RELEASED = "COMPONENT_NOT_RELEASED"
    REQUIRED_FIELD_MISSING = "REQUIRED_FIELD_MISSING"
    TYPE_MISMATCH = "TYPE_MISMATCH"
    INVALID_ENUM_VALUE = "INVALID_ENUM_VALUE"
    PATTERN_MISMATCH = "PATTERN_MISMATCH"
    INVALID_JSON = "INVALID_JSON"
    SCHEMA_VS_CONTRACT = "SCHEMA_VS_CONTRACT"
    JINJA_SYNTAX_ERROR = "JINJA_SYNTAX_ERROR"
    INVALID_REFERENCE = "INVALID_REFERENCE"
    CIRCULAR_REFERENCE = "CIRCULAR_REFERENCE"
    UNKNOWN_COMPONENT = "UNKNOWN_COMPONENT"

@dataclass
class ValidationError:
    """Represents a validation error"""
    error_type: ErrorType
    message: str
    path: str
    line: Optional[int] = None
    column: Optional[int] = None
    suggestion: Optional[str] = None
    component_type: Optional[str] = None
    web_status: Optional[str] = None

@dataclass
class ValidationResult:
    """Result of validation"""
    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=dict)
    incompatible_components: Dict[str, List[Dict]] = field(default_factory=dict)

class LineTracker:
    """Track line numbers in JSON for accurate error reporting - Enhanced version"""

    def __init__(self, json_str: str):
        self.lines = json_str.split('\n')
        self.line_map = {}
        self.component_type_cache = {}
        self.path_cache = {}
        self._build_line_map(json_str)

    def _build_line_map(self, json_str: str):
        """Build a map of JSON paths to line numbers - Optimized"""
        type_pattern = re.compile(r'"type"\s*:\s*"([^"]+)"')
        field_pattern = re.compile(r'"([^"]+)"\s*:')
        
        for i, line in enumerate(self.lines, 1):
            # Look for "type": "ComponentName" patterns
            type_match = type_pattern.search(line)
            if type_match:
                component_type = type_match.group(1)
                self.line_map[component_type] = i
                if component_type not in self.component_type_cache:
                    self.component_type_cache[component_type] = []
                self.component_type_cache[component_type].append(i)

            # Look for field names
            field_match = field_pattern.search(line)
            if field_match:
                field_name = field_match.group(1)
                if field_name not in self.line_map:
                    self.line_map[field_name] = i

    @lru_cache(maxsize=256)
    def get_line_for_path(self, path: str, component_type: str = None) -> Optional[int]:
        """Get line number for a given path - Enhanced for deep nesting"""
        path_parts = path.split('.')
        
        # For deep paths, try to find the most specific component
        # Start from the end and work backwards
        for i in range(len(path_parts) - 1, -1, -1):
            part = path_parts[i]
            # Remove array indices
            clean_part = re.sub(r'\[\d+\]', '', part)
            
            # Skip generic field names
            if clean_part in ['enabled', 'text', 'children', 'content', 'isEnabled']:
                continue
            
            # Check if we have this part in our line map
            if clean_part in self.line_map:
                return self.line_map[clean_part]
        
        # Try component type if provided
        if component_type and component_type in self.line_map:
            return self.line_map[component_type]
        
        # Try to find by searching through the file
        if len(path_parts) >= 2:
            # Get the parent element
            parent = path_parts[-2] if path_parts[-1] in ['enabled', 'text'] else path_parts[-1]
            clean_parent = re.sub(r'\[\d+\]', '', parent)
            if clean_parent in self.line_map:
                return self.line_map[clean_parent]
        
        return 1  # Default to start of file

    def find_component_lines(self, component_type: str) -> List[Tuple[str, int]]:
        """Find all occurrences of a component type with JSON paths"""
        if component_type in self.component_type_cache:
            results = []
            for line_num in self.component_type_cache[component_type]:
                path = self._build_path_for_line(line_num, component_type)
                results.append((path, line_num))
            return results
        
        results = []
        pattern = re.compile(rf'"type"\s*:\s*"{component_type}"')

        for i, line in enumerate(self.lines, 1):
            if pattern.search(line):
                path = self._build_path_for_line(i, component_type)
                results.append((path, i))

        return results

    @lru_cache(maxsize=128)
    def _build_path_for_line(self, line_num: int, component_type: str = None) -> str:
        """Build JSON path for a line number"""
        path_parts = []
        current_indent = len(self.lines[line_num - 1]) - len(self.lines[line_num - 1].lstrip())

        if current_indent == 0:
            return "rootElement" if '"rootElement"' in self.lines[line_num - 2:line_num + 2] else "root"

        for i in range(line_num - 1, 0, -1):
            line = self.lines[i - 1]
            indent = len(line) - len(line.lstrip())

            if indent < current_indent:
                key_match = re.search(r'"([^"]+)"\s*:', line)
                if key_match:
                    key = key_match.group(1)

                    if '[' in line:
                        array_index = self._find_array_index_for_line(i, line_num, component_type)
                        path_parts.insert(0, f"{key}[{array_index}]")
                    else:
                        path_parts.insert(0, key)

                    current_indent = indent

                    if indent == 0:
                        break

        return '.'.join(path_parts) if path_parts else f"line_{line_num}"

    def _find_array_index_for_line(self, array_start: int, target_line: int, component_type: str = None) -> int:
        """Find array index for a line"""
        index = 0
        brace_depth = 0
        in_array = False
        
        for i in range(array_start, min(target_line, array_start + 1000)):
            line = self.lines[i - 1].strip()
            
            if not line:
                continue

            if '[' in line and not in_array:
                in_array = True
                if '{' in line:
                    if i >= target_line - 10:
                        return index
                continue

            if in_array:
                if line.startswith('{'):
                    if brace_depth == 0:
                        if component_type and i < target_line:
                            for j in range(i, min(i + 20, len(self.lines))):
                                check_line = self.lines[j]
                                if f'"type": "{component_type}"' in check_line or f'"type":"{component_type}"' in check_line:
                                    if j <= target_line <= j + 5:
                                        return index
                                    break
                        elif i >= target_line - 10:
                            return index
                        index += 1
                    brace_depth += line.count('{') - line.count('}')
                elif '{' in line:
                    if brace_depth == 0 and i >= target_line - 10:
                        return index
                    brace_depth += line.count('{') - line.count('}')
                    if brace_depth == 1:
                        index += 1
                elif '}' in line:
                    brace_depth -= line.count('}')

        return index

class SchemaLoader:
    """Load and cache SDUI schemas - Version-aware"""

    WRAPPER_MAPPINGS = {
        'ConstraintWrapper': 'components/Constraint/v1/Constraint.json',
        'ScrollWrapper': 'components/Scroll/v1/Scroll.json',
        'BannerWrapper': 'components/Banner/v1/Banner.json'
    }

    def __init__(self, schema_base_path: str):
        self.schema_base = Path(schema_base_path)
        self.schema_cache = {}
        self.component_index = {}
        self.release_info = {}
        self.index_built = False
        self._lazy_build_index()

    def _lazy_build_index(self):
        """Lazy build index"""
        if not self.schema_base.exists():
            return

        for schema_dir in ['components', 'layouts', 'wrappers', 'atoms']:
            dir_path = self.schema_base / schema_dir
            if dir_path.exists():
                self._scan_directory_lazy(dir_path)

        for wrapper_name, schema_path in self.WRAPPER_MAPPINGS.items():
            if wrapper_name not in self.component_index:
                full_path = self.schema_base / schema_path
                if full_path.exists():
                    self.component_index[wrapper_name] = schema_path

        self.index_built = True

    def _scan_directory_lazy(self, directory: Path):
        """Lazily scan directory for schemas"""
        for item in directory.rglob('*.json'):
            if 'samples' not in str(item) and 'presets' not in str(item):
                component_name = item.stem
                relative_path = str(item.relative_to(self.schema_base))
                
                # Check for versioned schemas
                parent_dir = item.parent.name
                if parent_dir.startswith('v'):
                    # This is a versioned schema
                    version = parent_dir[1:]  # Remove 'v' prefix
                    versioned_name = f"{component_name}_v{version}"
                    self.component_index[versioned_name] = relative_path
                
                if component_name not in self.component_index:
                    self.component_index[component_name] = relative_path

    @lru_cache(maxsize=64)
    def get_schema(self, component_type: str, version: Optional[int] = None) -> Optional[Dict]:
        """Get schema for a component type with optional version"""
        # Try versioned schema first if version provided
        if version and version > 1:
            versioned_name = f"{component_type}_v{version}"
            if versioned_name in self.schema_cache:
                return self.schema_cache[versioned_name]
            if versioned_name in self.component_index:
                schema_path = self.schema_base / self.component_index[versioned_name]
                try:
                    with open(schema_path, 'r', encoding='utf-8') as f:
                        schema = json.load(f)
                        self.schema_cache[versioned_name] = schema
                        return schema
                except (json.JSONDecodeError, IOError):
                    pass

        # Try regular schema
        if component_type in self.schema_cache:
            return self.schema_cache[component_type]

        if component_type in self.component_index:
            schema_path = self.schema_base / self.component_index[component_type]
            try:
                with open(schema_path, 'r', encoding='utf-8') as f:
                    schema = json.load(f)
                    self.schema_cache[component_type] = schema
                    
                    if 'releaseVersion' in schema:
                        self.release_info[component_type] = schema['releaseVersion']
                    
                    if 'name' in schema and schema['name'] != component_type:
                        self.component_index[schema['name']] = self.component_index[component_type]
                    
                    return schema
            except (json.JSONDecodeError, IOError):
                pass

        return None

    @lru_cache(maxsize=128)
    def is_component_released_for_web(self, component_type: str) -> Tuple[bool, str]:
        """Check if component is released for web platform"""
        if component_type in self.release_info:
            web_status = self.release_info[component_type].get('web', 'notReleased')
            return web_status == 'released', web_status

        schema = self.get_schema(component_type)
        if schema and 'releaseVersion' in schema:
            web_status = schema['releaseVersion'].get('web', 'notReleased')
            self.release_info[component_type] = schema['releaseVersion']
            return web_status == 'released', web_status

        return False, 'unknown'

class SDUIValidator:
    """Main SDUI contract validator - Version and Jinja aware"""

    # Прекомпилированные regex паттерны
    TEMPLATE_PATTERNS = [
        (re.compile(r'"\{\{[^}]+\}\}"'), '"__TEMPLATE__"'),
        (re.compile(r'\{\{[^}]+\}\}'), '__TEMPLATE__'),
        (re.compile(r'"\$\{[^}]+\}"'), '"__TEMPLATE__"'),
        (re.compile(r'\$\{[^}]+\}'), '__TEMPLATE__'),
    ]

    def __init__(self, schema_path: str = "/Users/username/Documents/front-middle-schema/SDUI"):
        self.schema_loader = SchemaLoader(schema_path)
        self.visited_nodes = set()
        self.current_path = []
        self.errors = []
        self.warnings = []
        self.line_tracker = None
        self.stats = defaultdict(int)
        self.incompatible_components = defaultdict(list)
        self.file_path = None
        self.jinja_blocks = []  # Store Jinja blocks for restoration

    @staticmethod
    def get_short_contract_name(file_path: str) -> str:
        """Get a short identifier for the contract file"""
        path = Path(file_path)
        path_str = str(path)
        
        patterns = [
            'front-middle-schema/',
            'Documents/',
            'Downloads/',
            'Desktop/',
            'workspace/',
            'projects/',
            'repos/',
            'src/',
        ]
        
        for pattern in patterns:
            if pattern in path_str:
                idx = path_str.rfind(pattern)
                if idx != -1:
                    short_path = path_str[idx + len(pattern):]
                    return short_path.lstrip('/')
        
        parts = path.parts
        if len(parts) > 2:
            return str(Path(*parts[-2:]))
        elif len(parts) > 1:
            return str(Path(*parts[-1:]))
        else:
            return path.name

    def validate_file(self, file_path: str) -> ValidationResult:
        """Validate a single SDUI contract file"""
        self.errors = []
        self.warnings = []
        self.visited_nodes = set()
        self.current_path = []
        self.stats = defaultdict(int)
        self.incompatible_components = defaultdict(list)
        self.file_path = file_path
        self.jinja_blocks = []

        # Read file
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except IOError as e:
            return ValidationResult(
                is_valid=False,
                errors=[ValidationError(
                    error_type=ErrorType.INVALID_JSON,
                    message=f"Cannot read file: {e}",
                    path="",
                    line=0
                )]
            )

        # Initialize line tracker
        self.line_tracker = LineTracker(content)

        # Check for invalid Jinja2 syntax
        jinja_error = self._check_jinja_validity(content)
        if jinja_error:
            return ValidationResult(
                is_valid=False,
                errors=[jinja_error]
            )

        # Parse JSON with template preprocessing
        try:
            processed_content = self._preprocess_templates(content)
            data = json.loads(processed_content)
        except json.JSONDecodeError as e:
            return ValidationResult(
                is_valid=False,
                errors=[ValidationError(
                    error_type=ErrorType.INVALID_JSON,
                    message=f"Invalid JSON: {e}",
                    path="",
                    line=e.lineno if hasattr(e, 'lineno') else None
                )]
            )

        # Check if this is a schema instead of a contract
        if self._is_schema_not_contract(data):
            return ValidationResult(
                is_valid=False,
                errors=[ValidationError(
                    error_type=ErrorType.SCHEMA_VS_CONTRACT,
                    message="This is a component schema, not a UI contract",
                    path="",
                    line=1,
                    suggestion="Use a contract with 'type' field and component instance"
                )]
            )

        # Validate the contract
        if 'rootElement' in data:
            self._validate_component(data['rootElement'], ['rootElement'])
        elif 'type' in data:
            self._validate_component(data, [])
        else:
            self.errors.append(ValidationError(
                error_type=ErrorType.REQUIRED_FIELD_MISSING,
                message="Contract must have either 'rootElement' or 'type' field",
                path="",
                line=1
            ))

        # Create result
        result = ValidationResult(
            is_valid=len(self.errors) == 0 and len(self.incompatible_components) == 0,
            errors=self.errors,
            warnings=self.warnings,
            stats=dict(self.stats),
            incompatible_components=dict(self.incompatible_components)
        )

        return result

    def _check_jinja_validity(self, content: str) -> Optional[ValidationError]:
        """Check if Jinja2 syntax is valid - allows Jinja but checks for problematic patterns"""
        # Invalid patterns that would break JSON structure
        invalid_patterns = [
            (r'^\s*{%', "Jinja block at the start of file"),
            (r'%}\s*$', "Jinja block at the end of file"),
            (r'"[^"]*{%[^}]*%}[^"]*"', "Jinja block inside string value"),
            (r':\s*{%[^}]*%}[^,\s}]', "Jinja block as JSON value without quotes"),
        ]
        
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            for pattern, description in invalid_patterns:
                if re.search(pattern, line):
                    return ValidationError(
                        error_type=ErrorType.JINJA_SYNTAX_ERROR,
                        message=f"Invalid Jinja2 placement: {description}",
                        path="",
                        line=i,
                        suggestion="Ensure Jinja blocks are properly placed and don't break JSON structure"
                    )
        
        # Jinja is valid
        return None

    def _preprocess_templates(self, content: str) -> str:
        """Pre-process templates for JSON parsing - handles Jinja gracefully"""
        processed = content
        
        # Replace Jinja blocks with placeholders for JSON parsing
        def replace_jinja(match):
            placeholder = f'"__JINJA_{len(self.jinja_blocks)}__"'
            self.jinja_blocks.append(match.group(0))
            return placeholder
        
        # Temporarily replace Jinja blocks that might interfere with JSON parsing
        # But only those that are in positions where they act as values
        processed = re.sub(r'(?<=:\s){%[^%]*%}(?=\s*[,\}])', replace_jinja, processed)
        
        # Process other template patterns
        for pattern, replacement in self.TEMPLATE_PATTERNS:
            processed = pattern.sub(replacement, processed)
        
        return processed

    def _is_schema_not_contract(self, data: Dict) -> bool:
        """Check if this is a schema definition instead of a contract"""
        if 'name' in data and 'properties' in data:
            return True

        schema_indicators = ['properties', 'definitions', 'releaseVersion', '$schema']
        indicator_count = sum(1 for ind in schema_indicators if ind in data)
        return indicator_count >= 2

    def _validate_component(self, component: Dict, path: List[str]):
        """Recursively validate a component - Version aware"""
        component_id = id(component)
        
        # Check for circular references
        if component_id in self.visited_nodes:
            self.errors.append(ValidationError(
                error_type=ErrorType.CIRCULAR_REFERENCE,
                message="Circular reference detected",
                path='.'.join(path),
                line=self.line_tracker.get_line_for_path('.'.join(path))
            ))
            return
        self.visited_nodes.add(component_id)

        component_type = component.get('type')
        if not component_type:
            self.errors.append(ValidationError(
                error_type=ErrorType.REQUIRED_FIELD_MISSING,
                message="Component missing 'type' field",
                path='.'.join(path),
                line=self.line_tracker.get_line_for_path('.'.join(path))
            ))
            return

        self.stats['total_components'] += 1

        # Check release status for web
        is_released, web_status = self.schema_loader.is_component_released_for_web(component_type)
        if not is_released and web_status != 'unknown':
            if component_type not in self.incompatible_components:
                occurrences = self.line_tracker.find_component_lines(component_type)
                for occ_path, occ_line in occurrences:
                    self.incompatible_components[component_type].append({
                        'path': occ_path,
                        'line': occ_line,
                        'reason': f"web: {web_status}"
                    })

            self.stats['unreleased_components'] += 1

        # Get schema with version support
        version = component.get('version')
        schema = self.schema_loader.get_schema(component_type, version)
        
        if not schema:
            # Try wrapper pattern
            if component_type.endswith('Wrapper'):
                base_type = component_type[:-7]
                schema = self.schema_loader.get_schema(base_type, version)

            if not schema:
                self.warnings.append(ValidationError(
                    error_type=ErrorType.SCHEMA_NOT_FOUND,
                    message=f"Schema not found for component: {component_type}" + (f" v{version}" if version else ""),
                    path='.'.join(path),
                    line=self.line_tracker.get_line_for_path('.'.join(path), component_type),
                    component_type=component_type
                ))
                self.stats['unknown_components'] += 1
        else:
            self._validate_against_schema(component, schema, path, version)
            self.stats['validated_components'] += 1

        # Validate children
        self._validate_children(component, path)

    def _validate_against_schema(self, component: Dict, schema: Dict, path: List[str], version: Optional[int] = None):
        """Validate component against its schema - Version aware"""
        properties = schema.get('properties', {})
        
        # Special handling for ButtonView v2
        if component.get('type') == 'ButtonView' and version == 2:
            # ButtonView v2 has different structure
            content = component.get('content', {})
            
            # Check for required fields in v2 structure
            if 'isEnabled' not in content:
                # In v2, the field is 'isEnabled', not 'enabled'
                pass  # v2 doesn't require this field to be explicit
            
            # v2 uses textLabels instead of direct text field
            if 'textLabels' not in content:
                # This is optional in v2
                pass
            
            # Don't report errors for v1 fields in v2 component
            return

        # Regular validation for other components and v1
        for prop_name, prop_schema in properties.items():
            if isinstance(prop_schema, dict) and prop_schema.get('required', False):
                value = component.get(prop_name)
                
                # Check nested content
                if value is None and 'content' in component:
                    value = component['content'].get(prop_name)

                if value is None:
                    # Skip if this is a v2 component with different field names
                    if version == 2:
                        # Map v1 to v2 field names
                        v2_mappings = {
                            'enabled': 'isEnabled',
                            'text': 'textLabels'
                        }
                        v2_name = v2_mappings.get(prop_name)
                        if v2_name and (v2_name in component or (component.get('content') and v2_name in component['content'])):
                            continue
                    
                    self.errors.append(ValidationError(
                        error_type=ErrorType.REQUIRED_FIELD_MISSING,
                        message=f"Required field '{prop_name}' is missing",
                        path='.'.join(path + [prop_name]),
                        line=self.line_tracker.get_line_for_path('.'.join(path)),
                        suggestion=f"Add required field '{prop_name}' to the component"
                    ))
                    self.stats['missing_required_fields'] += 1

    def _validate_children(self, component: Dict, path: List[str]):
        """Find and validate all child components"""
        children_locations = [
            ('content', 'children'),
            ('children',),
            ('content', 'content'),
            ('content', 'items'),
            ('items',),
            ('wrapper',),
            ('elements',),
            ('views',),
            ('content', 'leftView'),
            ('content', 'rightView'),
            ('content', 'topView'),
            ('content', 'bottomView'),
            ('innerWrapper',),
        ]

        found_children = False

        for location in children_locations:
            if found_children and len(location) > 1:
                continue
                
            current = component
            valid = True

            for key in location[:-1]:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    valid = False
                    break

            if valid and isinstance(current, dict) and location[-1] in current:
                child_value = current[location[-1]]
                child_path = path + list(location)

                if isinstance(child_value, dict):
                    if 'type' in child_value:
                        self._validate_component(child_value, child_path)
                        found_children = True

                elif isinstance(child_value, list):
                    for i, item in enumerate(child_value):
                        if isinstance(item, dict) and 'type' in item:
                            self._validate_component(item, child_path + [str(i)])
                            found_children = True
                
                if found_children and len(location) == 1:
                    break

    def print_results(self, result: ValidationResult, file_path: str):
        """Print validation results in a formatted way with IDE-clickable paths"""
        if '--vscode-simple' in sys.argv:
            self._print_vscode_output(result, file_path)
            return

        timestamp = datetime.now().strftime("%H:%M:%S")
        short_name = self.get_short_contract_name(file_path)
        abs_path = os.path.abspath(file_path)

        print(f"\n{'═'*80}")
        print(f"📋 ВАЛИДАЦИЯ СОВМЕСТИМОСТИ С WEB v7.0.0 | {timestamp}")
        print(f"{Colors.CYAN}📄 Контракт: {Colors.BOLD}{short_name}{Colors.RESET}")
        print(f"{Colors.DIM}   {abs_path}{Colors.RESET}")
        print(f"{'═'*80}")

        # Print incompatible components
        if result.incompatible_components:
            for comp_type, occurrences in result.incompatible_components.items():
                if occurrences:
                    print(f"\n{Colors.RED}❌ {comp_type}{Colors.RESET} — не поддерживается ({Colors.YELLOW}{occurrences[0]['reason']}{Colors.RESET})")
                    print(f"   {Colors.DIM}Найдено: {len(occurrences)} вхождений{Colors.RESET}")

                    for i, occurrence in enumerate(occurrences, 1):
                        print(f"\n   {Colors.CYAN}📍 Расположение компонента #{i}:{Colors.RESET}")
                        print(f"      Путь: {Colors.WHITE}{occurrence['path']}{Colors.RESET}")
                        print(f"      {Colors.UNDERLINE}→ {abs_path}:{occurrence['line']}:1{Colors.RESET}")

        # Print other errors
        if result.errors:
            print(f"\n{Colors.RED}Дополнительные ошибки ({len(result.errors)}):{Colors.RESET}")
            for i, error in enumerate(result.errors, 1):
                if error.error_type != ErrorType.COMPONENT_NOT_RELEASED:
                    print(f"\n  {i}. {Colors.BOLD}{error.error_type.value}{Colors.RESET}")
                    print(f"     {error.message}")
                    if error.path:
                        print(f"     Путь: {Colors.WHITE}{error.path}{Colors.RESET}")
                    if error.line:
                        print(f"     {Colors.UNDERLINE}→ {abs_path}:{error.line}:1{Colors.RESET}")
                    if error.suggestion:
                        print(f"     {Colors.YELLOW}💡 {error.suggestion}{Colors.RESET}")

        # Print warnings
        if result.warnings:
            print(f"\n{Colors.YELLOW}Предупреждения ({len(result.warnings)}):{Colors.RESET}")
            for i, warning in enumerate(result.warnings, 1):
                print(f"\n  {i}. {warning.message}")
                if warning.path:
                    print(f"     Путь: {Colors.WHITE}{warning.path}{Colors.RESET}")
                if warning.line:
                    print(f"     {Colors.UNDERLINE}→ {abs_path}:{warning.line}:1{Colors.RESET}")

        # Statistics
        if result.stats:
            print(f"\n{Colors.CYAN}📊 Статистика:{Colors.RESET}")
            print(f"   Всего компонентов: {result.stats.get('total_components', 0)}")
            print(f"   Проверено: {result.stats.get('validated_components', 0)}")
            if result.stats.get('unknown_components'):
                print(f"   Неизвестных: {result.stats.get('unknown_components', 0)}")
            if result.stats.get('unreleased_components'):
                print(f"   Не релизных: {result.stats.get('unreleased_components', 0)}")

        # Summary
        print(f"\n{'─'*80}")
        print(f"{Colors.BOLD}📊 ИТОГ для {short_name}:{Colors.RESET}")
        if result.is_valid:
            print(f"   ✅ {Colors.GREEN}Контракт совместим с веб-платформой{Colors.RESET}")
        else:
            total_errors = len(result.errors) + sum(len(v) for v in result.incompatible_components.values())
            print(f"   ❌ {Colors.RED}Контракт несовместим{Colors.RESET} (всего ошибок: {Colors.BOLD}{total_errors}{Colors.RESET})")
            if result.incompatible_components:
                incompatible_count = sum(len(v) for v in result.incompatible_components.values())
                print(f"   ⚠️  Несовместимых вхождений: {Colors.BOLD}{incompatible_count}{Colors.RESET}")
        print(f"{'═'*80}\n")

    def _print_vscode_output(self, result: ValidationResult, file_path: str):
        """Print results formatted for VSCode output"""
        abs_path = os.path.abspath(file_path)
        short_name = self.get_short_contract_name(file_path)

        if result.is_valid:
            print(f"✓ {short_name} - VALID")
            if result.stats:
                print(f"  Components: {result.stats.get('total_components', 0)} validated")
        else:
            print(f"✗ {short_name} - INVALID")

            for comp_type, occurrences in result.incompatible_components.items():
                for occ in occurrences:
                    print(f"{abs_path}:{occ['line']}:1 - error: Component '{comp_type}' not released for web ({occ['reason']})")

            for error in result.errors:
                if error.error_type != ErrorType.COMPONENT_NOT_RELEASED:
                    if error.line:
                        print(f"{abs_path}:{error.line}:1 - error: {error.message}")
                    else:
                        print(f"{abs_path}:1:1 - error: {error.message}")
                    if error.suggestion:
                        print(f"    → {error.suggestion}")

            if result.warnings:
                for warning in result.warnings:
                    if warning.line:
                        print(f"{abs_path}:{warning.line}:1 - warning: {warning.message}")
                    else:
                        print(f"{abs_path}:1:1 - warning: {warning.message}")

def main():
    """Main entry point"""
    args = sys.argv[1:]
    no_color = '--no-color' in args
    vscode_simple_mode = '--vscode-simple' in args

    if no_color:
        args.remove('--no-color')
        # Disable colors
        for attr in dir(Colors):
            if not attr.startswith('_'):
                setattr(Colors, attr, '')

    if vscode_simple_mode:
        args.remove('--vscode-simple')

    if len(args) < 1:
        print(f"{Colors.YELLOW}Usage: {sys.argv[0]} <contract.json> [schema_path] [--no-color] [--vscode-simple]{Colors.RESET}")
        print(f"Default schema path: /Users/username/Documents/front-middle-schema/SDUI")
        print(f"Use --no-color to disable colored output")
        print(f"Use --vscode-simple for simple VSCode output")
        sys.exit(1)

    file_path = args[0]
    schema_path = args[1] if len(args) > 1 else "/Users/username/Documents/front-middle-schema/SDUI"

    if not os.path.exists(file_path):
        print(f"{Colors.RED}Error: File not found: {file_path}{Colors.RESET}")
        sys.exit(1)

    validator = SDUIValidator(schema_path)

    start_time = time.time()
    result = validator.validate_file(file_path)
    elapsed_time = time.time() - start_time

    validator.print_results(result, file_path)

    sys.exit(0 if result.is_valid else 1)

if __name__ == "__main__":
    main()