#!/usr/bin/env python3
"""
Demo script for SDUI Resolver API
Demonstrates the key features for agents
"""

import asyncio
import json
import tempfile
from pathlib import Path
from sdui_resolver_api import (
    SDUIResolverAPI, ValidationStatus, quick_resolve, quick_validate
)

async def create_test_schemas():
    """Create test schemas for demonstration"""
    test_dir = Path(tempfile.mkdtemp(prefix="sdui_test_"))

    # Base component schema
    base_schema = {
        "name": "BaseComponent",
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "className": {"type": "string"}
        },
        "releaseVersion": {
            "web": "released"
        }
    }

    # Button component that references base
    button_schema = {
        "name": "Button",
        "type": "object",
        "allOf": [
            {"$ref": "BaseComponent.json"},
            {
                "properties": {
                    "label": {"type": "string"},
                    "disabled": {"type": "boolean"},
                    "onClick": {"type": "string"}
                }
            }
        ],
        "releaseVersion": {
            "web": "released"
        }
    }

    # Unreleased component
    unreleased_schema = {
        "name": "UnreleasedComponent",
        "type": "object",
        "properties": {
            "experimental": {"type": "boolean"}
        },
        "releaseVersion": {
            "web": "notReleased"
        }
    }

    # Save schemas
    with open(test_dir / "BaseComponent.json", 'w') as f:
        json.dump(base_schema, f, indent=2)

    with open(test_dir / "Button.json", 'w') as f:
        json.dump(button_schema, f, indent=2)

    with open(test_dir / "UnreleasedComponent.json", 'w') as f:
        json.dump(unreleased_schema, f, indent=2)

    return test_dir

async def demo_contract_resolution(api, test_dir):
    """Demonstrate contract resolution"""
    print("🚀 === CONTRACT RESOLUTION DEMO ===")

    button_path = test_dir / "Button.json"
    result = await api.resolve_contract(button_path)

    if result.success:
        print(f"✅ Button contract resolved in {result.processing_time:.3f}s")
        print(f"📊 Contract size: {len(json.dumps(result.contract))} bytes")
        print(f"🔗 Dependencies resolved: {result.metadata.get('dependencies_resolved', 0)}")

        # Show resolved contract structure
        contract = result.contract
        print(f"📦 Resolved component: {contract.get('name', 'Unknown')}")

        if 'properties' in contract:
            props = list(contract['properties'].keys())
            print(f"🏷️ Properties: {', '.join(props[:5])}{'...' if len(props) > 5 else ''}")

    else:
        print("❌ Resolution failed:")
        for error in result.errors:
            print(f"  - {error}")

async def demo_schema_validation(api, test_dir):
    """Demonstrate schema validation"""
    print("\n🔍 === SCHEMA VALIDATION DEMO ===")

    schemas_to_test = [
        ("Button.json", "Valid released component"),
        ("UnreleasedComponent.json", "Unreleased component"),
    ]

    for filename, description in schemas_to_test:
        print(f"\n📋 Testing: {description}")

        result = await api.validate_schema(test_dir / filename)

        status_emoji = {
            ValidationStatus.VALID: "✅",
            ValidationStatus.WARNING: "⚠️",
            ValidationStatus.INCOMPATIBLE: "🚫",
            ValidationStatus.INVALID: "❌"
        }

        print(f"{status_emoji.get(result.status, '❓')} Status: {result.status.value}")

        if result.errors:
            print("❌ Errors:")
            for error in result.errors:
                print(f"  - {error}")

        if result.warnings:
            print("⚠️ Warnings:")
            for warning in result.warnings:
                print(f"  - {warning}")

        if result.incompatible_elements:
            print("🚫 Incompatible elements:")
            for elem in result.incompatible_elements:
                print(f"  - {elem.get('element', 'unknown')}: {elem.get('status', 'unknown')}")

async def demo_component_info(api, test_dir):
    """Demonstrate component information retrieval"""
    print("\n📦 === COMPONENT INFO DEMO ===")

    components = ["Button", "BaseComponent", "UnreleasedComponent"]

    for component_name in components:
        print(f"\n🔍 Component: {component_name}")

        info = await api.get_component_info(component_name)

        if info:
            print(f"📁 Path: {Path(info.path).name}")
            print(f"🏷️ Type: {info.type}")
            print(f"🚀 Released: {'✅' if info.is_released else '❌'} ({info.release_status})")
            print(f"📊 File size: {info.file_size} bytes")
            print(f"🔗 Dependencies: {len(info.dependencies)}")

            if info.dependencies:
                print("  Dependencies:")
                for dep in info.dependencies:
                    print(f"    - {dep}")
        else:
            print("❌ Component not found")

async def demo_streaming(api, test_dir):
    """Demonstrate streaming for large schemas"""
    print("\n📡 === STREAMING DEMO ===")

    # Create a larger test schema
    large_schema = {
        "name": "LargeComponent",
        "type": "object",
        "properties": {}
    }

    # Add many properties
    for i in range(100):
        large_schema["properties"][f"prop_{i}"] = {
            "type": "string",
            "description": f"Property {i}",
            "default": f"value_{i}"
        }

    large_file = test_dir / "LargeComponent.json"
    with open(large_file, 'w') as f:
        json.dump(large_schema, f)

    print(f"📊 Processing schema with {len(large_schema['properties'])} properties...")

    chunk_count = 0
    async for chunk_data in api.stream_large_schema(large_file, chunk_size=20):
        if 'error' in chunk_data:
            print(f"❌ Error: {chunk_data['error']}")
            break

        chunk_count += 1
        progress = chunk_data['progress']
        processed = chunk_data['processed']
        total = chunk_data['total']

        print(f"📈 Progress: {progress:.1f}% ({processed}/{total}) - Chunk {chunk_count}")

        if chunk_count >= 3:  # Limit output for demo
            print("  ... (stopping demo early)")
            break

async def demo_batch_processing(api, test_dir):
    """Demonstrate batch processing"""
    print("\n⚡ === BATCH PROCESSING DEMO ===")

    schema_files = [
        test_dir / "Button.json",
        test_dir / "BaseComponent.json",
        test_dir / "UnreleasedComponent.json"
    ]

    print(f"🔄 Batch processing {len(schema_files)} schemas...")

    results = await api.batch_resolve_contracts(schema_files)

    successful = sum(1 for r in results if r.success)
    print(f"📊 Results: {successful}/{len(results)} successful")

    for i, result in enumerate(results):
        filename = schema_files[i].name
        if result.success:
            print(f"  ✅ {filename}: {result.processing_time:.3f}s")
        else:
            print(f"  ❌ {filename}: {'; '.join(result.errors[:1])}")

async def demo_convenience_functions(test_dir):
    """Demonstrate convenience functions"""
    print("\n🎯 === CONVENIENCE FUNCTIONS DEMO ===")

    button_file = test_dir / "Button.json"

    # Quick resolve
    print("⚡ Quick resolve:")
    try:
        contract = await quick_resolve(str(button_file), str(test_dir))
        print(f"  ✅ Resolved: {contract.get('name', 'Unknown')}")
    except Exception as e:
        print(f"  ❌ Error: {e}")

    # Quick validate
    print("⚡ Quick validate:")
    with open(button_file) as f:
        schema = json.load(f)

    is_valid = await quick_validate(schema)
    print(f"  {'✅' if is_valid else '❌'} Valid: {is_valid}")

async def cleanup_test_data(test_dir):
    """Clean up test data"""
    import shutil
    shutil.rmtree(test_dir)
    print(f"\n🧹 Cleaned up test directory: {test_dir}")

async def main():
    """Main demo function"""
    print("🎬 SDUI Resolver API Demo")
    print("=" * 50)

    # Create test schemas
    test_dir = await create_test_schemas()
    print(f"📁 Created test schemas in: {test_dir}")

    # Initialize API
    api = SDUIResolverAPI(base_path=str(test_dir), verbose=False, max_concurrent=3)

    try:
        # Run all demos
        await demo_contract_resolution(api, test_dir)
        await demo_schema_validation(api, test_dir)
        await demo_component_info(api, test_dir)
        await demo_streaming(api, test_dir)
        await demo_batch_processing(api, test_dir)
        await demo_convenience_functions(test_dir)

    finally:
        # Cleanup
        await cleanup_test_data(test_dir)

    print("\n" + "=" * 50)
    print("🎉 Demo completed successfully!")
    print("\n📚 Key takeaways:")
    print("  • Async/await support for high performance")
    print("  • Comprehensive validation with detailed feedback")
    print("  • Streaming support for large schemas")
    print("  • Batch processing for multiple schemas")
    print("  • Rich component metadata")
    print("  • Convenient helper functions")

if __name__ == "__main__":
    asyncio.run(main())