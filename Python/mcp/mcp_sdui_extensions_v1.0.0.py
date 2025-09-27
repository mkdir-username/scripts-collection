#!/usr/bin/env python3
"""
MCP SDUI Resolver Extensions - Advanced features and utilities
"""

import json
import hashlib
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import asyncio
import re

# Schema Templates
SCHEMA_TEMPLATES = {
    "login_form": {
        "type": "object",
        "properties": {
            "username": {
                "type": "string",
                "minLength": 3,
                "maxLength": 50,
                "pattern": "^[a-zA-Z0-9_]+$"
            },
            "password": {
                "type": "string",
                "minLength": 8,
                "format": "password"
            },
            "remember_me": {
                "type": "boolean",
                "default": False
            }
        },
        "required": ["username", "password"]
    },
    "user_profile": {
        "type": "object",
        "properties": {
            "id": {"type": "string", "format": "uuid"},
            "email": {"type": "string", "format": "email"},
            "name": {"type": "string"},
            "avatar": {"type": "string", "format": "uri"},
            "bio": {"type": "string", "maxLength": 500},
            "settings": {
                "type": "object",
                "properties": {
                    "theme": {"type": "string", "enum": ["light", "dark", "auto"]},
                    "notifications": {"type": "boolean"},
                    "language": {"type": "string"}
                }
            }
        },
        "required": ["id", "email", "name"]
    },
    "data_table": {
        "type": "object",
        "properties": {
            "columns": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "key": {"type": "string"},
                        "label": {"type": "string"},
                        "type": {"type": "string"},
                        "sortable": {"type": "boolean"},
                        "filterable": {"type": "boolean"}
                    },
                    "required": ["key", "label"]
                }
            },
            "rows": {
                "type": "array",
                "items": {"type": "object"}
            },
            "pagination": {
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "minimum": 1},
                    "pageSize": {"type": "integer", "minimum": 1},
                    "total": {"type": "integer", "minimum": 0}
                }
            }
        },
        "required": ["columns", "rows"]
    }
}

@dataclass
class SchemaCache:
    """Advanced caching for SDUI schemas"""
    max_size: int = 100
    ttl_seconds: int = 3600
    cache: Dict[str, Tuple[Any, datetime]] = field(default_factory=dict)
    access_count: Dict[str, int] = field(default_factory=dict)

    def get(self, key: str) -> Optional[Any]:
        """Get item from cache if not expired"""
        if key in self.cache:
            value, timestamp = self.cache[key]
            if datetime.now() - timestamp < timedelta(seconds=self.ttl_seconds):
                self.access_count[key] = self.access_count.get(key, 0) + 1
                return value
            else:
                del self.cache[key]
        return None

    def set(self, key: str, value: Any):
        """Set item in cache with TTL"""
        # Implement LRU if cache is full
        if len(self.cache) >= self.max_size:
            # Remove least recently used item
            lru_key = min(self.access_count.keys(),
                         key=lambda k: self.access_count.get(k, 0))
            del self.cache[lru_key]
            del self.access_count[lru_key]

        self.cache[key] = (value, datetime.now())
        self.access_count[key] = 0

    def clear(self):
        """Clear the cache"""
        self.cache.clear()
        self.access_count.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "ttl": self.ttl_seconds,
            "hit_rate": self._calculate_hit_rate(),
            "most_accessed": self._get_most_accessed()
        }

    def _calculate_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        total_accesses = sum(self.access_count.values())
        if total_accesses == 0:
            return 0.0
        return len(self.cache) / self.max_size

    def _get_most_accessed(self, top_n: int = 5) -> List[Tuple[str, int]]:
        """Get most accessed cache keys"""
        sorted_items = sorted(self.access_count.items(),
                            key=lambda x: x[1], reverse=True)
        return sorted_items[:top_n]

class SchemaTransformer:
    """Transform and manipulate SDUI schemas"""

    @staticmethod
    def merge_schemas(base: Dict[str, Any], *overlays: Dict[str, Any]) -> Dict[str, Any]:
        """Merge multiple schemas with priority"""
        result = base.copy()

        for overlay in overlays:
            result = SchemaTransformer._deep_merge(result, overlay)

        return result

    @staticmethod
    def _deep_merge(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries"""
        result = dict1.copy()

        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = SchemaTransformer._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    @staticmethod
    def filter_schema_by_permissions(
        schema: Dict[str, Any],
        permissions: Set[str]
    ) -> Dict[str, Any]:
        """Filter schema based on user permissions"""
        filtered = schema.copy()
        properties = filtered.get("properties", {})

        # Remove fields that require permissions not granted
        for field_name, field_def in list(properties.items()):
            required_permission = field_def.get("x-permission")
            if required_permission and required_permission not in permissions:
                del properties[field_name]
                # Remove from required list if present
                if "required" in filtered and field_name in filtered["required"]:
                    filtered["required"].remove(field_name)

        return filtered

    @staticmethod
    def add_validation_rules(
        schema: Dict[str, Any],
        rules: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Add custom validation rules to schema"""
        enhanced = schema.copy()
        properties = enhanced.get("properties", {})

        for field_name, field_rules in rules.items():
            if field_name in properties:
                properties[field_name].update(field_rules)

        return enhanced

    @staticmethod
    def generate_mock_data(schema: Dict[str, Any]) -> Dict[str, Any]:
        """Generate mock data based on schema"""
        import random
        import string
        import uuid

        result = {}
        properties = schema.get("properties", {})

        for field_name, field_def in properties.items():
            field_type = field_def.get("type", "string")

            if field_type == "string":
                if field_def.get("format") == "email":
                    result[field_name] = f"user{random.randint(1, 1000)}@example.com"
                elif field_def.get("format") == "uuid":
                    result[field_name] = str(uuid.uuid4())
                elif field_def.get("format") == "uri":
                    result[field_name] = f"https://example.com/{random.randint(1, 1000)}"
                elif "enum" in field_def:
                    result[field_name] = random.choice(field_def["enum"])
                else:
                    min_len = field_def.get("minLength", 5)
                    max_len = field_def.get("maxLength", 20)
                    length = random.randint(min_len, min(max_len, 20))
                    result[field_name] = ''.join(
                        random.choices(string.ascii_letters, k=length)
                    )

            elif field_type == "number" or field_type == "integer":
                minimum = field_def.get("minimum", 0)
                maximum = field_def.get("maximum", 100)
                if field_type == "integer":
                    result[field_name] = random.randint(int(minimum), int(maximum))
                else:
                    result[field_name] = random.uniform(minimum, maximum)

            elif field_type == "boolean":
                result[field_name] = random.choice([True, False])

            elif field_type == "array":
                item_schema = field_def.get("items", {"type": "string"})
                min_items = field_def.get("minItems", 0)
                max_items = field_def.get("maxItems", 5)
                num_items = random.randint(min_items, max_items)

                result[field_name] = [
                    SchemaTransformer.generate_mock_data({"properties": {"item": item_schema}})["item"]
                    for _ in range(num_items)
                ]

            elif field_type == "object":
                result[field_name] = SchemaTransformer.generate_mock_data(field_def)

        return result

class SchemaVersionManager:
    """Manage schema versions and migrations"""

    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path("/tmp/sdui_schemas")
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def save_version(
        self,
        schema_id: str,
        schema: Dict[str, Any],
        version: Optional[str] = None
    ) -> str:
        """Save a schema version"""
        if not version:
            version = datetime.now().strftime("%Y%m%d_%H%M%S")

        version_data = {
            "schema": schema,
            "version": version,
            "timestamp": datetime.now().isoformat(),
            "checksum": self._calculate_checksum(schema)
        }

        file_path = self.storage_path / f"{schema_id}_{version}.json"
        with open(file_path, "w") as f:
            json.dump(version_data, f, indent=2)

        return version

    def get_version(self, schema_id: str, version: str) -> Optional[Dict[str, Any]]:
        """Get a specific schema version"""
        file_path = self.storage_path / f"{schema_id}_{version}.json"
        if file_path.exists():
            with open(file_path, "r") as f:
                data = json.load(f)
                return data["schema"]
        return None

    def list_versions(self, schema_id: str) -> List[Dict[str, Any]]:
        """List all versions of a schema"""
        versions = []
        pattern = f"{schema_id}_*.json"

        for file_path in self.storage_path.glob(pattern):
            with open(file_path, "r") as f:
                data = json.load(f)
                versions.append({
                    "version": data["version"],
                    "timestamp": data["timestamp"],
                    "checksum": data["checksum"]
                })

        return sorted(versions, key=lambda x: x["timestamp"], reverse=True)

    def migrate_schema(
        self,
        schema: Dict[str, Any],
        from_version: str,
        to_version: str,
        migration_rules: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Migrate schema from one version to another"""
        migrated = schema.copy()

        # Apply migration rules
        for rule_type, rule_data in migration_rules.items():
            if rule_type == "rename_fields":
                for old_name, new_name in rule_data.items():
                    if old_name in migrated.get("properties", {}):
                        properties = migrated["properties"]
                        properties[new_name] = properties.pop(old_name)

            elif rule_type == "add_fields":
                properties = migrated.setdefault("properties", {})
                properties.update(rule_data)

            elif rule_type == "remove_fields":
                properties = migrated.get("properties", {})
                for field in rule_data:
                    properties.pop(field, None)

            elif rule_type == "transform_types":
                properties = migrated.get("properties", {})
                for field, new_type in rule_data.items():
                    if field in properties:
                        properties[field]["type"] = new_type

        # Update version metadata
        migrated["x-version"] = to_version
        migrated["x-migrated-from"] = from_version
        migrated["x-migration-date"] = datetime.now().isoformat()

        return migrated

    @staticmethod
    def _calculate_checksum(schema: Dict[str, Any]) -> str:
        """Calculate checksum for schema"""
        schema_str = json.dumps(schema, sort_keys=True)
        return hashlib.sha256(schema_str.encode()).hexdigest()

class SchemaValidator:
    """Advanced schema validation"""

    @staticmethod
    async def validate_with_rules(
        data: Dict[str, Any],
        schema: Dict[str, Any],
        custom_rules: Optional[List[callable]] = None
    ) -> Tuple[bool, List[str]]:
        """Validate data against schema with custom rules"""
        errors = []

        # Basic type validation
        type_errors = SchemaValidator._validate_types(data, schema)
        errors.extend(type_errors)

        # Required fields validation
        required_errors = SchemaValidator._validate_required(data, schema)
        errors.extend(required_errors)

        # Format validation
        format_errors = SchemaValidator._validate_formats(data, schema)
        errors.extend(format_errors)

        # Custom rules
        if custom_rules:
            for rule in custom_rules:
                rule_errors = await rule(data, schema)
                if rule_errors:
                    errors.extend(rule_errors)

        return len(errors) == 0, errors

    @staticmethod
    def _validate_types(data: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
        """Validate data types"""
        errors = []
        properties = schema.get("properties", {})

        for field_name, field_value in data.items():
            if field_name in properties:
                expected_type = properties[field_name].get("type")
                if expected_type and not SchemaValidator._check_type(field_value, expected_type):
                    errors.append(
                        f"Field '{field_name}' has incorrect type. Expected {expected_type}"
                    )

        return errors

    @staticmethod
    def _validate_required(data: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
        """Validate required fields"""
        errors = []
        required = schema.get("required", [])

        for field_name in required:
            if field_name not in data:
                errors.append(f"Required field '{field_name}' is missing")

        return errors

    @staticmethod
    def _validate_formats(data: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
        """Validate string formats"""
        errors = []
        properties = schema.get("properties", {})

        format_patterns = {
            "email": r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            "uri": r'^https?://[^\s/$.?#].[^\s]*$',
            "uuid": r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
            "date": r'^\d{4}-\d{2}-\d{2}$',
            "time": r'^\d{2}:\d{2}:\d{2}$',
            "datetime": r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'
        }

        for field_name, field_value in data.items():
            if field_name in properties:
                field_def = properties[field_name]
                format_type = field_def.get("format")

                if format_type and format_type in format_patterns:
                    pattern = format_patterns[format_type]
                    if isinstance(field_value, str) and not re.match(pattern, field_value):
                        errors.append(
                            f"Field '{field_name}' has invalid format. Expected {format_type}"
                        )

                # Pattern validation
                pattern = field_def.get("pattern")
                if pattern and isinstance(field_value, str):
                    if not re.match(pattern, field_value):
                        errors.append(
                            f"Field '{field_name}' does not match pattern {pattern}"
                        )

        return errors

    @staticmethod
    def _check_type(value: Any, expected_type: str) -> bool:
        """Check if value matches expected type"""
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
        return isinstance(value, expected) if expected else False

# Example usage functions
async def example_usage():
    """Example usage of extensions"""

    # Cache usage
    cache = SchemaCache(max_size=50, ttl_seconds=1800)
    cache.set("user_schema", SCHEMA_TEMPLATES["user_profile"])
    cached_schema = cache.get("user_schema")
    print("Cache stats:", cache.get_stats())

    # Schema transformation
    transformer = SchemaTransformer()

    # Merge schemas
    base_schema = SCHEMA_TEMPLATES["login_form"]
    overlay = {
        "properties": {
            "captcha": {"type": "string", "minLength": 6}
        }
    }
    merged = transformer.merge_schemas(base_schema, overlay)

    # Filter by permissions
    user_permissions = {"read", "write"}
    schema_with_perms = {
        "properties": {
            "public_field": {"type": "string"},
            "admin_field": {"type": "string", "x-permission": "admin"}
        }
    }
    filtered = transformer.filter_schema_by_permissions(schema_with_perms, user_permissions)

    # Generate mock data
    mock_data = transformer.generate_mock_data(SCHEMA_TEMPLATES["user_profile"])
    print("Mock data:", json.dumps(mock_data, indent=2))

    # Version management
    version_manager = SchemaVersionManager()
    version = version_manager.save_version("user_schema", SCHEMA_TEMPLATES["user_profile"])
    versions = version_manager.list_versions("user_schema")

    # Schema validation
    validator = SchemaValidator()
    test_data = {
        "username": "john_doe",
        "password": "securepass123"
    }
    is_valid, errors = await validator.validate_with_rules(
        test_data,
        SCHEMA_TEMPLATES["login_form"]
    )
    print(f"Validation result: {is_valid}, Errors: {errors}")

if __name__ == "__main__":
    asyncio.run(example_usage())