#!/usr/bin/env python3
"""
Examples and tests for SDUI Resolver API
Demonstrates high-level API usage for agents
"""

import asyncio
import json
import time
from pathlib import Path
from sdui_resolver_api import (
    SDUIResolverAPI,
    ValidationStatus,
    quick_resolve,
    quick_validate,
    get_component
)

async def example_basic_resolution():
    """Example: Basic contract resolution"""
    print("=== Basic Contract Resolution ===")

    # Initialize API
    api = SDUIResolverAPI(base_path="/path/to/sdui", verbose=True)

    # Resolve a contract
    result = await api.resolve_contract("Button.json")

    if result.success:
        print(f"✅ Resolution successful in {result.processing_time:.2f}s")
        print(f"Contract size: {len(json.dumps(result.contract))} bytes")
        print(f"Dependencies resolved: {result.metadata.get('dependencies_resolved', 0)}")
    else:
        print("❌ Resolution failed:")
        for error in result.errors:
            print(f"  - {error}")

async def example_schema_validation():
    """Example: Schema validation"""
    print("\n=== Schema Validation ===")

    api = SDUIResolverAPI(".")

    # Sample schema for validation
    test_schema = {
        "name": "TestComponent",
        "type": "object",
        "properties": {
            "label": {"type": "string"},
            "disabled": {"type": "boolean"}
        },
        "releaseVersion": {
            "web": "released"
        }
    }

    result = await api.validate_schema(test_schema)

    print(f"Validation status: {result.status.value}")

    if result.errors:
        print("Errors found:")
        for error in result.errors:
            print(f"  ❌ {error}")

    if result.warnings:
        print("Warnings:")
        for warning in result.warnings:
            print(f"  ⚠️ {warning}")

    if result.incompatible_elements:
        print("Incompatible elements:")
        for elem in result.incompatible_elements:
            print(f"  🚫 {elem}")

async def example_component_info():
    """Example: Get component information"""
    print("\n=== Component Information ===")

    api = SDUIResolverAPI(".")

    # Get component info (this will search for the component)
    info = await api.get_component_info("Button")

    if info:
        print(f"Component: {info.name}")
        print(f"Type: {info.type}")
        print(f"Path: {info.path}")
        print(f"Released: {'✅' if info.is_released else '❌'}")
        print(f"Release status: {info.release_status}")
        print(f"File size: {info.file_size} bytes")
        print(f"Dependencies: {len(info.dependencies)}")
        print(f"Last modified: {info.last_modified}")

        if info.dependencies:
            print("Dependencies:")
            for dep in info.dependencies:
                print(f"  - {dep}")
    else:
        print("Component not found")

async def example_streaming_large_schema():
    """Example: Stream processing of large schema"""
    print("\n=== Streaming Large Schema ===")

    api = SDUIResolverAPI(".")

    # Create a large test schema
    large_schema_path = Path("large_test_schema.json")

    # Generate large test schema
    large_schema = {
        "name": "LargeSchema",
        "type": "object",
        "properties": {}
    }

    # Add many properties to simulate large schema
    for i in range(1000):
        large_schema["properties"][f"property_{i}"] = {
            "type": "string",
            "description": f"Property number {i}",
            "default": f"value_{i}"
        }

    # Save test schema
    with open(large_schema_path, 'w') as f:
        json.dump(large_schema, f)

    print(f"Processing large schema with {len(large_schema['properties'])} properties...")

    # Stream process the schema
    async for chunk_data in api.stream_large_schema(large_schema_path, chunk_size=50):
        if 'error' in chunk_data:
            print(f"❌ Error: {chunk_data['error']}")
            break

        progress = chunk_data['progress']
        processed = chunk_data['processed']
        total = chunk_data['total']

        print(f"Progress: {progress:.1f}% ({processed}/{total} items)")

        # Process chunk data here
        chunk = chunk_data['chunk']
        print(f"  Chunk contains {len(chunk.get('items', []))} items")

        # Simulate some processing time
        await asyncio.sleep(0.1)

    # Cleanup
    large_schema_path.unlink()
    print("✅ Large schema processing completed")

async def example_batch_resolution():
    """Example: Batch resolution of multiple contracts"""
    print("\n=== Batch Contract Resolution ===")

    api = SDUIResolverAPI(".", max_concurrent=3)

    # Create some test schemas
    test_files = []
    for i in range(5):
        filename = f"test_schema_{i}.json"
        schema = {
            "name": f"TestSchema{i}",
            "type": "object",
            "properties": {
                "value": {"type": "string"}
            }
        }

        with open(filename, 'w') as f:
            json.dump(schema, f)

        test_files.append(filename)

    print(f"Batch resolving {len(test_files)} schemas...")

    # Batch resolve
    start_time = time.time()
    results = await api.batch_resolve_contracts(test_files)
    total_time = time.time() - start_time

    successful = sum(1 for r in results if r.success)
    print(f"✅ Batch resolution completed in {total_time:.2f}s")
    print(f"Success rate: {successful}/{len(results)} ({successful/len(results)*100:.1f}%)")

    for i, result in enumerate(results):
        if result.success:
            print(f"  ✅ {test_files[i]}: {result.processing_time:.3f}s")
        else:
            print(f"  ❌ {test_files[i]}: {'; '.join(result.errors)}")

    # Cleanup
    for filename in test_files:
        Path(filename).unlink()

async def example_convenience_functions():
    """Example: Using convenience functions"""
    print("\n=== Convenience Functions ===")

    # Create test schema
    test_schema = {
        "name": "ConvenienceTest",
        "type": "object",
        "properties": {
            "test": {"type": "string"}
        }
    }

    test_file = "convenience_test.json"
    with open(test_file, 'w') as f:
        json.dump(test_schema, f)

    try:
        # Quick resolve
        print("Quick resolve:")
        resolved = await quick_resolve(test_file)
        print(f"  ✅ Resolved: {resolved.get('name', 'Unknown')}")

        # Quick validate
        print("Quick validate:")
        is_valid = await quick_validate(test_schema)
        print(f"  {'✅' if is_valid else '❌'} Valid: {is_valid}")

        # Get component (will not find this test file, but shows usage)
        print("Get component info:")
        component_info = await get_component("NonExistentComponent")
        print(f"  {'✅' if component_info else '❌'} Found: {component_info is not None}")

    finally:
        # Cleanup
        Path(test_file).unlink()

async def example_error_handling():
    """Example: Error handling scenarios"""
    print("\n=== Error Handling ===")

    api = SDUIResolverAPI(".")

    # Test with non-existent file
    print("Testing non-existent file:")
    result = await api.resolve_contract("non_existent_file.json")
    print(f"  Success: {result.success}")
    if not result.success:
        print(f"  Error: {result.errors[0]}")

    # Test with invalid JSON
    print("Testing invalid schema:")
    invalid_schema = "not a valid schema"
    validation_result = await api.validate_schema(invalid_schema)
    print(f"  Status: {validation_result.status.value}")
    if validation_result.errors:
        print(f"  Error: {validation_result.errors[0]}")

    # Test with incompatible schema
    print("Testing incompatible schema:")
    incompatible_schema = {
        "name": "IncompatibleTest",
        "type": "object",
        "releaseVersion": {
            "web": "notReleased"
        }
    }

    validation_result = await api.validate_schema(incompatible_schema)
    print(f"  Status: {validation_result.status.value}")
    if validation_result.incompatible_elements:
        print(f"  Incompatible elements: {len(validation_result.incompatible_elements)}")

async def run_all_examples():
    """Run all examples"""
    print("🚀 SDUI Resolver API Examples")
    print("=" * 50)

    examples = [
        example_basic_resolution,
        example_schema_validation,
        example_component_info,
        example_streaming_large_schema,
        example_batch_resolution,
        example_convenience_functions,
        example_error_handling
    ]

    for example in examples:
        try:
            await example()
        except Exception as e:
            print(f"❌ Example {example.__name__} failed: {e}")

        await asyncio.sleep(0.5)  # Small delay between examples

    print("\n" + "=" * 50)
    print("✅ All examples completed!")

if __name__ == "__main__":
    asyncio.run(run_all_examples())