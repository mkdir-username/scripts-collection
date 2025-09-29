#!/usr/bin/env python3
"""
SDUI Web Validator for VSCode v1.0.0
Optimized for VSCode Run on Save extension
"""

import json
import os
import sys
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import time

# Force no colors for VSCode output
class Colors:
    RED = ''
    GREEN = ''
    YELLOW = ''
    BLUE = ''
    MAGENTA = ''
    CYAN = ''
    WHITE = ''
    RESET = ''
    BOLD = ''

class ErrorType(Enum):
    """Types of validation errors"""
    SCHEMA_NOT_FOUND = "SCHEMA_NOT_FOUND"
    COMPONENT_NOT_RELEASED = "COMPONENT_NOT_RELEASED"
    REQUIRED_FIELD_MISSING = "REQUIRED_FIELD_MISSING"
    INVALID_JSON = "INVALID_JSON"
    SCHEMA_VS_CONTRACT = "SCHEMA_VS_CONTRACT"
    JINJA_SYNTAX_ERROR = "JINJA_SYNTAX_ERROR"
    UNKNOWN_COMPONENT = "UNKNOWN_COMPONENT"

@dataclass
class ValidationError:
    """Represents a validation error"""
    error_type: ErrorType
    message: str
    path: str
    line: Optional[int] = None
    suggestion: Optional[str] = None

@dataclass
class ValidationResult:
    """Result of validation"""
    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=dict)

class SchemaLoader:
    """Load and cache SDUI schemas"""

    def __init__(self, schema_base_path: str):
        self.schema_base = Path(schema_base_path)
        self.schema_cache = {}
        self.component_index = {}
        self.release_info = {}
        self._build_index()

    def _build_index(self):
        """Build index of all available schemas"""
        if not self.schema_base.exists():
            return

        # Scan for component schemas
        for schema_dir in ['components', 'layouts', 'wrappers', 'atoms']:
            dir_path = self.schema_base / schema_dir
            if dir_path.exists():
                self._scan_directory(dir_path)

    def _scan_directory(self, directory: Path):
        """Recursively scan directory for schemas"""
        for item in directory.rglob('*.json'):
            if 'samples' not in str(item) and 'presets' not in str(item):
                try:
                    with open(item, 'r', encoding='utf-8') as f:
                        schema = json.load(f)

                    component_name = schema.get('name')
                    if component_name:
                        is_web_released = False
                        if 'releaseVersion' in schema:
                            web_status = schema['releaseVersion'].get('web', 'notReleased')
                            is_web_released = (web_status == 'released')

                        if component_name not in self.component_index or is_web_released:
                            self.component_index[component_name] = str(item.relative_to(self.schema_base))

                            if 'releaseVersion' in schema:
                                self.release_info[component_name] = schema['releaseVersion']

                            self.schema_cache[component_name] = schema
                except (json.JSONDecodeError, IOError):
                    continue

    def get_schema(self, component_type: str) -> Optional[Dict]:
        """Get schema for a component type"""
        if component_type in self.schema_cache:
            return self.schema_cache[component_type]

        if component_type in self.component_index:
            schema_path = self.schema_base / self.component_index[component_type]
            try:
                with open(schema_path, 'r', encoding='utf-8') as f:
                    schema = json.load(f)
                    self.schema_cache[component_type] = schema
                    return schema
            except (json.JSONDecodeError, IOError):
                pass

        return None

    def is_component_released_for_web(self, component_type: str):
        """Check if component is released for web platform"""
        if component_type in self.release_info:
            web_status = self.release_info[component_type].get('web', 'notReleased')
            return web_status == 'released', web_status

        schema = self.get_schema(component_type)
        if schema and 'releaseVersion' in schema:
            web_status = schema['releaseVersion'].get('web', 'notReleased')
            return web_status == 'released', web_status

        return False, 'unknown'

class SDUIValidator:
    """Main SDUI contract validator"""

    def __init__(self, schema_path: str = "/Users/username/Documents/front-middle-schema/SDUI"):
        self.schema_loader = SchemaLoader(schema_path)
        self.visited_nodes = set()
        self.errors = []
        self.warnings = []
        self.stats = {}

    def validate_file(self, file_path: str) -> ValidationResult:
        """Validate a single SDUI contract file"""
        self.errors = []
        self.warnings = []
        self.visited_nodes = set()
        self.stats = {
            'total_components': 0,
            'validated_components': 0,
            'unreleased_components': 0,
            'unknown_components': 0
        }

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

        # Check for Jinja2 syntax
        if self._has_invalid_jinja(content):
            return ValidationResult(
                is_valid=False,
                errors=[ValidationError(
                    error_type=ErrorType.JINJA_SYNTAX_ERROR,
                    message="File contains Jinja2 syntax ({% %}) that breaks JSON structure",
                    path="",
                    suggestion="Use Mustache-style templates {{ }} or remove Jinja2 blocks"
                )]
            )

        # Parse JSON
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
                path=""
            ))

        return ValidationResult(
            is_valid=len(self.errors) == 0,
            errors=self.errors,
            warnings=self.warnings,
            stats=self.stats
        )

    def _has_invalid_jinja(self, content: str) -> bool:
        """Check for Jinja2 syntax that breaks JSON"""
        return bool(re.search(r'{%.*?%}', content))

    def _preprocess_templates(self, content: str) -> str:
        """Pre-process Mustache-style templates for JSON parsing"""
        content = re.sub(r'"\{\{[^}]+\}\}"', '"__TEMPLATE__"', content)
        content = re.sub(r'\{\{[^}]+\}\}', '__TEMPLATE__', content)
        content = re.sub(r'"\$\{[^}]+\}"', '"__TEMPLATE__"', content)
        content = re.sub(r'\$\{[^}]+\}', '__TEMPLATE__', content)
        return content

    def _is_schema_not_contract(self, data: Dict) -> bool:
        """Check if this is a schema definition instead of a contract"""
        schema_indicators = ['properties', 'definitions', 'releaseVersion', '$schema']

        if 'name' in data and 'properties' in data:
            return True

        indicator_count = sum(1 for ind in schema_indicators if ind in data)
        if indicator_count >= 2:
            return True

        return False

    def _validate_component(self, component: Dict, path: List[str]):
        """Recursively validate a component and its children"""
        component_id = id(component)
        if component_id in self.visited_nodes:
            return
        self.visited_nodes.add(component_id)

        component_type = component.get('type')
        if not component_type:
            self.errors.append(ValidationError(
                error_type=ErrorType.REQUIRED_FIELD_MISSING,
                message="Component missing 'type' field",
                path='.'.join(path)
            ))
            return

        self.stats['total_components'] += 1

        # Check if component is released for web
        is_released, web_status = self.schema_loader.is_component_released_for_web(component_type)
        if not is_released and web_status != 'unknown':
            self.errors.append(ValidationError(
                error_type=ErrorType.COMPONENT_NOT_RELEASED,
                message=f"Component '{component_type}' is not released for web (status: {web_status})",
                path='.'.join(path),
                suggestion=f"Use only components with releaseVersion.web = 'released'"
            ))
            self.stats['unreleased_components'] += 1

        # Get schema for validation
        schema = self.schema_loader.get_schema(component_type)
        if not schema:
            if component_type.endswith('Wrapper'):
                base_type = component_type[:-7]
                schema = self.schema_loader.get_schema(base_type)

            if not schema:
                self.warnings.append(ValidationError(
                    error_type=ErrorType.SCHEMA_NOT_FOUND,
                    message=f"Schema not found for component: {component_type}",
                    path='.'.join(path)
                ))
                self.stats['unknown_components'] += 1
        else:
            self._validate_against_schema(component, schema, path)
            self.stats['validated_components'] += 1

        # Find and validate children components
        self._validate_children(component, path)

    def _validate_against_schema(self, component: Dict, schema: Dict, path: List[str]):
        """Validate component against its schema"""
        properties = schema.get('properties', {})

        for prop_name, prop_schema in properties.items():
            if isinstance(prop_schema, dict) and prop_schema.get('required', False):
                value = component.get(prop_name)
                if value is None and 'content' in component:
                    value = component['content'].get(prop_name)

                if value is None:
                    self.errors.append(ValidationError(
                        error_type=ErrorType.REQUIRED_FIELD_MISSING,
                        message=f"Required field '{prop_name}' is missing",
                        path='.'.join(path + [prop_name]),
                        suggestion=f"Add required field '{prop_name}' to the component"
                    ))

    def _validate_children(self, component: Dict, path: List[str]):
        """Find and validate all child components"""
        children_locations = [
            ('content', 'children'),
            ('content', 'content'),
            ('content', 'items'),
            ('children',),
            ('items',),
            ('elements',),
            ('views',),
            ('content', 'leftView'),
            ('content', 'rightView'),
            ('content', 'topView'),
            ('content', 'bottomView'),
            ('wrapper',),
            ('innerWrapper',),
        ]

        for location in children_locations:
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

                elif isinstance(child_value, list):
                    for i, item in enumerate(child_value):
                        if isinstance(item, dict) and 'type' in item:
                            self._validate_component(item, child_path + [str(i)])

def print_vscode_output(result: ValidationResult, file_path: str):
    """Print results formatted for VSCode output"""
    filename = os.path.basename(file_path)

    if result.is_valid:
        print(f"✓ {filename} - VALID")
        if result.stats:
            print(f"  Components: {result.stats.get('total_components', 0)} validated")
    else:
        print(f"✗ {filename} - INVALID")

        for error in result.errors:
            line_info = f":{error.line}" if error.line else ""
            print(f"  ERROR{line_info}: {error.message}")
            if error.suggestion:
                print(f"    → {error.suggestion}")

        if result.warnings:
            for warning in result.warnings:
                print(f"  WARNING: {warning.message}")

def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: sdui_web_validator_vscode.py <contract.json>")
        sys.exit(1)

    file_path = sys.argv[1]

    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    # Only validate .json files in .JSON directory
    if not ('.JSON' in file_path and file_path.endswith('.json')):
        # Skip non-JSON contract files silently
        sys.exit(0)

    validator = SDUIValidator()
    result = validator.validate_file(file_path)
    print_vscode_output(result, file_path)

    sys.exit(0 if result.is_valid else 1)

if __name__ == "__main__":
    main()