#!/usr/bin/env python3
"""
Test suite for MCP SDUI Resolver
"""

import asyncio
import json
import unittest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
import sys
import os

# Add the script directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_sdui_resolver import (
    SDUIResolver,
    SchemaType,
    ValidationLevel,
    SchemaMetadata,
    ValidationResult,
    NavigationNode
)

from mcp_sdui_extensions import (
    SchemaCache,
    SchemaTransformer,
    SchemaVersionManager,
    SchemaValidator,
    SCHEMA_TEMPLATES
)

class TestSDUIResolver(unittest.TestCase):
    """Test cases for SDUI Resolver"""

    def setUp(self):
        """Set up test fixtures"""
        self.resolver = SDUIResolver()

    def tearDown(self):
        """Clean up after tests"""
        asyncio.run(self.resolver.cleanup())

    def test_resolver_initialization(self):
        """Test resolver initialization"""
        self.assertIsNotNone(self.resolver)
        self.assertEqual(self.resolver.base_url, "https://api.sdui.example.com")
        self.assertIsInstance(self.resolver.cache, dict)

    async def async_test_resolve_schema(self):
        """Test schema resolution"""
        schema_id = "test_form"
        context = {"user_role": "admin"}

        schema = await self.resolver.resolve_schema(
            schema_id=schema_id,
            context=context,
            include_metadata=True
        )

        self.assertIsNotNone(schema)
        self.assertEqual(schema["id"], schema_id)
        self.assertIn("metadata", schema)
        self.assertIn("context", schema)
        self.assertEqual(schema["context"]["user_role"], "admin")

    def test_resolve_schema(self):
        """Wrapper for async test"""
        asyncio.run(self.async_test_resolve_schema())

    async def async_test_validate_contract(self):
        """Test contract validation"""
        schema = {
            "id": "test_schema",
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            },
            "required": ["name"]
        }

        # Valid data
        valid_data = {"name": "John", "age": 30}
        result = await self.resolver.validate_contract(schema, valid_data)

        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.errors), 0)

        # Invalid data (missing required field)
        invalid_data = {"age": 30}
        result = await self.resolver.validate_contract(schema, invalid_data)

        self.assertFalse(result.is_valid)
        self.assertGreater(len(result.errors), 0)

    def test_validate_contract(self):
        """Wrapper for async test"""
        asyncio.run(self.async_test_validate_contract())

    async def async_test_get_navigation(self):
        """Test navigation structure generation"""
        context = {"user_role": "user"}
        navigation = await self.resolver.get_navigation(context=context, depth=2)

        self.assertIsInstance(navigation, list)
        self.assertGreater(len(navigation), 0)

        # Check navigation structure
        for node in navigation:
            self.assertIsInstance(node, NavigationNode)
            self.assertIsNotNone(node.id)
            self.assertIsNotNone(node.label)
            self.assertIsNotNone(node.path)

        # Admin context should have different navigation
        admin_context = {"user_role": "admin"}
        admin_navigation = await self.resolver.get_navigation(context=admin_context)

        # Check that settings node exists for admin
        settings_exists = any(node.id == "settings" for node in admin_navigation)
        self.assertTrue(settings_exists)

    def test_get_navigation(self):
        """Wrapper for async test"""
        asyncio.run(self.async_test_get_navigation())

class TestSchemaCache(unittest.TestCase):
    """Test cases for Schema Cache"""

    def setUp(self):
        """Set up test fixtures"""
        self.cache = SchemaCache(max_size=10, ttl_seconds=5)

    def test_cache_set_and_get(self):
        """Test cache set and get operations"""
        key = "test_key"
        value = {"test": "data"}

        self.cache.set(key, value)
        retrieved = self.cache.get(key)

        self.assertEqual(retrieved, value)

    def test_cache_expiration(self):
        """Test cache TTL expiration"""
        import time

        key = "expiring_key"
        value = {"test": "data"}

        # Set TTL to 1 second for testing
        self.cache.ttl_seconds = 1
        self.cache.set(key, value)

        # Should retrieve immediately
        self.assertIsNotNone(self.cache.get(key))

        # Wait for expiration
        time.sleep(2)

        # Should be expired
        self.assertIsNone(self.cache.get(key))

    def test_cache_lru_eviction(self):
        """Test LRU eviction when cache is full"""
        # Set small cache size
        cache = SchemaCache(max_size=3, ttl_seconds=3600)

        # Fill cache
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        # Access key1 and key2 to make them more recently used
        cache.get("key1")
        cache.get("key2")

        # Add new item, should evict key3 (least recently used)
        cache.set("key4", "value4")

        self.assertIsNotNone(cache.get("key1"))
        self.assertIsNotNone(cache.get("key2"))
        self.assertIsNotNone(cache.get("key4"))
        self.assertIsNone(cache.get("key3"))  # Should be evicted

    def test_cache_stats(self):
        """Test cache statistics"""
        self.cache.set("key1", "value1")
        self.cache.get("key1")
        self.cache.get("key1")

        stats = self.cache.get_stats()

        self.assertEqual(stats["size"], 1)
        self.assertEqual(stats["max_size"], 10)
        self.assertIn("hit_rate", stats)
        self.assertIn("most_accessed", stats)

class TestSchemaTransformer(unittest.TestCase):
    """Test cases for Schema Transformer"""

    def setUp(self):
        """Set up test fixtures"""
        self.transformer = SchemaTransformer()

    def test_merge_schemas(self):
        """Test schema merging"""
        base = {
            "type": "object",
            "properties": {
                "field1": {"type": "string"}
            }
        }

        overlay = {
            "properties": {
                "field2": {"type": "number"}
            }
        }

        merged = self.transformer.merge_schemas(base, overlay)

        self.assertIn("field1", merged["properties"])
        self.assertIn("field2", merged["properties"])

    def test_filter_by_permissions(self):
        """Test permission-based filtering"""
        schema = {
            "properties": {
                "public": {"type": "string"},
                "admin_only": {"type": "string", "x-permission": "admin"},
                "user_field": {"type": "string", "x-permission": "user"}
            },
            "required": ["public", "admin_only"]
        }

        permissions = {"user"}
        filtered = self.transformer.filter_schema_by_permissions(schema, permissions)

        self.assertIn("public", filtered["properties"])
        self.assertIn("user_field", filtered["properties"])
        self.assertNotIn("admin_only", filtered["properties"])
        self.assertNotIn("admin_only", filtered.get("required", []))

    def test_generate_mock_data(self):
        """Test mock data generation"""
        schema = SCHEMA_TEMPLATES["login_form"]
        mock_data = self.transformer.generate_mock_data(schema)

        self.assertIn("username", mock_data)
        self.assertIn("password", mock_data)
        self.assertIsInstance(mock_data["username"], str)
        self.assertIsInstance(mock_data["password"], str)

        # Check constraints
        self.assertGreaterEqual(len(mock_data["username"]), 3)
        self.assertLessEqual(len(mock_data["username"]), 50)
        self.assertGreaterEqual(len(mock_data["password"]), 8)

class TestSchemaValidator(unittest.TestCase):
    """Test cases for Schema Validator"""

    def setUp(self):
        """Set up test fixtures"""
        self.validator = SchemaValidator()

    async def async_test_validate_with_rules(self):
        """Test validation with custom rules"""
        schema = {
            "properties": {
                "email": {"type": "string", "format": "email"},
                "age": {"type": "integer"}
            },
            "required": ["email"]
        }

        # Valid data
        valid_data = {"email": "test@example.com", "age": 25}
        is_valid, errors = await self.validator.validate_with_rules(valid_data, schema)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

        # Invalid email format
        invalid_data = {"email": "invalid-email", "age": 25}
        is_valid, errors = await self.validator.validate_with_rules(invalid_data, schema)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)

        # Missing required field
        missing_data = {"age": 25}
        is_valid, errors = await self.validator.validate_with_rules(missing_data, schema)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)

    def test_validate_with_rules(self):
        """Wrapper for async test"""
        asyncio.run(self.async_test_validate_with_rules())

    def test_type_validation(self):
        """Test type validation"""
        errors = self.validator._validate_types(
            {"field1": "string", "field2": 123},
            {
                "properties": {
                    "field1": {"type": "string"},
                    "field2": {"type": "string"}
                }
            }
        )

        self.assertEqual(len(errors), 1)
        self.assertIn("field2", errors[0])

    def test_format_validation(self):
        """Test format validation"""
        errors = self.validator._validate_formats(
            {"email": "not-an-email", "uuid": "not-a-uuid"},
            {
                "properties": {
                    "email": {"type": "string", "format": "email"},
                    "uuid": {"type": "string", "format": "uuid"}
                }
            }
        )

        self.assertEqual(len(errors), 2)

class TestIntegration(unittest.TestCase):
    """Integration tests"""

    async def async_test_full_workflow(self):
        """Test complete workflow"""
        # Initialize components
        resolver = SDUIResolver()
        cache = SchemaCache()
        transformer = SchemaTransformer()
        validator = SchemaValidator()

        # Resolve schema
        schema = await resolver.resolve_schema(
            schema_id="user_form",
            context={"user_role": "admin"}
        )

        # Cache it
        cache.set("user_form", schema)

        # Transform it
        permissions = {"read", "write"}
        filtered_schema = transformer.filter_schema_by_permissions(
            schema, permissions
        )

        # Generate mock data
        mock_data = transformer.generate_mock_data(filtered_schema)

        # Validate the mock data
        is_valid, errors = await validator.validate_with_rules(
            mock_data, filtered_schema
        )

        # Assertions
        self.assertIsNotNone(schema)
        self.assertIsNotNone(cache.get("user_form"))
        self.assertIsNotNone(filtered_schema)
        self.assertIsNotNone(mock_data)

        # Cleanup
        await resolver.cleanup()

    def test_full_workflow(self):
        """Wrapper for async test"""
        asyncio.run(self.async_test_full_workflow())

def run_tests():
    """Run all tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test cases
    suite.addTests(loader.loadTestsFromTestCase(TestSDUIResolver))
    suite.addTests(loader.loadTestsFromTestCase(TestSchemaCache))
    suite.addTests(loader.loadTestsFromTestCase(TestSchemaTransformer))
    suite.addTests(loader.loadTestsFromTestCase(TestSchemaValidator))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Return success status
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)