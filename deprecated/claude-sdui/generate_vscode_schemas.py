#!/usr/bin/env python3
"""
Generate VS Code json.schemas configuration for SDUI schema validation.
Scans the SDUI directory and creates fileMatch patterns for all schema files.
"""

import os
import json
import glob
from pathlib import Path
from typing import List, Dict, Set, Tuple
from collections import defaultdict

def find_schema_files(base_path: str) -> Dict[str, List[Tuple[str, str]]]:
    """
    Find all schema files in the SDUI directory structure.
    Returns a dictionary mapping schema types to (file_pattern, schema_path) tuples.
    """
    schemas = defaultdict(list)

    # Components with samples
    components_path = os.path.join(base_path, "components")
    if os.path.exists(components_path):
        for component_dir in os.listdir(components_path):
            component_path = os.path.join(components_path, component_dir)
            if os.path.isdir(component_path):
                # Find all version directories
                for version_dir in os.listdir(component_path):
                    version_path = os.path.join(component_path, version_dir)
                    if os.path.isdir(version_path) and version_dir.startswith('v'):
                        # Find main schema file
                        schema_file = os.path.join(version_path, f"{component_dir}.json")
                        if os.path.exists(schema_file):
                            # Pattern for sample files
                            sample_pattern = f"SDUI/components/{component_dir}/{version_dir}/samples/*.json"
                            schemas['components'].append((sample_pattern, schema_file))

                        # Also check for component-specific schemas (like ButtonView_web.json)
                        for schema_variant in glob.glob(os.path.join(version_path, f"{component_dir}_*.json")):
                            if 'samples' not in schema_variant:
                                variant_name = os.path.basename(schema_variant).replace(f"{component_dir}_", "").replace(".json", "")
                                sample_pattern = f"SDUI/components/{component_dir}/{version_dir}/samples/*_{variant_name}.json"
                                schemas['components'].append((sample_pattern, schema_variant))

    # Atoms
    atoms_path = os.path.join(base_path, "atoms")
    if os.path.exists(atoms_path):
        for atom_dir in os.listdir(atoms_path):
            atom_path = os.path.join(atoms_path, atom_dir)
            if os.path.isdir(atom_path):
                # Check for versioned atoms
                for version_dir in os.listdir(atom_path):
                    version_path = os.path.join(atom_path, version_dir)
                    if os.path.isdir(version_path) and version_dir.startswith('v'):
                        schema_file = os.path.join(version_path, f"{atom_dir}.json")
                        if os.path.exists(schema_file):
                            pattern = f"SDUI/atoms/{atom_dir}/{version_dir}/*.json"
                            schemas['atoms'].append((pattern, schema_file))

                # Check for non-versioned atom schema
                schema_file = os.path.join(atom_path, f"{atom_dir}.json")
                if os.path.exists(schema_file):
                    pattern = f"SDUI/atoms/{atom_dir}/*.json"
                    schemas['atoms'].append((pattern, schema_file))

    # Layouts
    layouts_path = os.path.join(base_path, "layouts")
    if os.path.exists(layouts_path):
        for layout_dir in os.listdir(layouts_path):
            layout_path = os.path.join(layouts_path, layout_dir)
            if os.path.isdir(layout_path):
                for version_dir in os.listdir(layout_path):
                    version_path = os.path.join(layout_path, version_dir)
                    if os.path.isdir(version_path) and version_dir.startswith('v'):
                        schema_file = os.path.join(version_path, f"{layout_dir}.json")
                        if os.path.exists(schema_file):
                            pattern = f"SDUI/layouts/{layout_dir}/{version_dir}/*.json"
                            schemas['layouts'].append((pattern, schema_file))
                            # Also match sample files for layouts
                            sample_pattern = f"SDUI/layouts/{layout_dir}/{version_dir}/samples/*.json"
                            schemas['layouts'].append((sample_pattern, schema_file))

    # Actions
    actions_path = os.path.join(base_path, "actions")
    if os.path.exists(actions_path):
        for action_item in os.listdir(actions_path):
            action_path = os.path.join(actions_path, action_item)

            # Direct JSON files in actions/
            if action_item.endswith('.json'):
                pattern = f"SDUI/actions/{action_item}"
                schemas['actions'].append((pattern, action_path))

            # Action subdirectories
            elif os.path.isdir(action_path):
                # Check for versioned actions
                for version_dir in os.listdir(action_path):
                    version_path = os.path.join(action_path, version_dir)
                    if os.path.isdir(version_path) and version_dir.startswith('v'):
                        schema_file = os.path.join(version_path, f"{action_item}.json")
                        if os.path.exists(schema_file):
                            pattern = f"SDUI/actions/{action_item}/{version_dir}/*.json"
                            schemas['actions'].append((pattern, schema_file))

                # Check for non-versioned action schema
                schema_file = os.path.join(action_path, f"{action_item}.json")
                if os.path.exists(schema_file):
                    pattern = f"SDUI/actions/{action_item}/*.json"
                    schemas['actions'].append((pattern, schema_file))

    # Functions
    functions_path = os.path.join(base_path, "functions")
    if os.path.exists(functions_path):
        for category_dir in os.listdir(functions_path):
            category_path = os.path.join(functions_path, category_dir)
            if os.path.isdir(category_path):
                for function_dir in os.listdir(category_path):
                    function_path = os.path.join(category_path, function_dir)
                    if os.path.isdir(function_path):
                        for version_dir in os.listdir(function_path):
                            version_path = os.path.join(function_path, version_dir)
                            if os.path.isdir(version_path) and version_dir.startswith('v'):
                                schema_file = os.path.join(version_path, f"{function_dir}.json")
                                if os.path.exists(schema_file):
                                    pattern = f"SDUI/functions/{category_dir}/{function_dir}/{version_dir}/*.json"
                                    schemas['functions'].append((pattern, schema_file))

    # Models
    models_path = os.path.join(base_path, "models")
    if os.path.exists(models_path):
        for model_dir in os.listdir(models_path):
            model_path = os.path.join(models_path, model_dir)
            if os.path.isdir(model_path):
                schema_file = os.path.join(model_path, f"{model_dir}.json")
                if os.path.exists(schema_file):
                    pattern = f"SDUI/models/{model_dir}/*.json"
                    schemas['models'].append((pattern, schema_file))

    # SDUIScreen
    sdui_screen_path = os.path.join(base_path, "SDUIScreen")
    if os.path.exists(sdui_screen_path):
        for version_dir in os.listdir(sdui_screen_path):
            version_path = os.path.join(sdui_screen_path, version_dir)
            if os.path.isdir(version_path) and version_dir.startswith('v'):
                schema_file = os.path.join(version_path, "SDUIScreen.json")
                if os.path.exists(schema_file):
                    pattern = f"SDUI/SDUIScreen/{version_dir}/*.json"
                    schemas['SDUIScreen'].append((pattern, schema_file))
                    # Also match sample files for SDUIScreen
                    sample_pattern = f"SDUI/SDUIScreen/{version_dir}/samples/*.json"
                    schemas['SDUIScreen'].append((sample_pattern, schema_file))

    # Metaschemas
    metaschemas_path = os.path.join(base_path, "metaschemas")
    if os.path.exists(metaschemas_path):
        for metaschema_file in glob.glob(os.path.join(metaschemas_path, "*.json")):
            metaschema_name = os.path.basename(metaschema_file).replace('.json', '')
            pattern = f"SDUI/metaschemas/{metaschema_name}_*.json"
            schemas['metaschemas'].append((pattern, metaschema_file))

    return schemas

def generate_vscode_schemas(base_path: str) -> List[Dict[str, str]]:
    """
    Generate VS Code json.schemas configuration.
    """
    schemas = find_schema_files(base_path)
    vscode_schemas = []
    seen_patterns = set()  # Track unique patterns to avoid duplicates

    for schema_type, schema_list in schemas.items():
        for file_pattern, schema_path in schema_list:
            # Skip if we've already added this pattern
            if file_pattern in seen_patterns:
                continue
            seen_patterns.add(file_pattern)

            # Convert to file:// URL
            schema_url = f"file://{os.path.abspath(schema_path)}"

            vscode_schemas.append({
                "fileMatch": [file_pattern],
                "url": schema_url
            })

    # Sort by fileMatch pattern for readability
    vscode_schemas.sort(key=lambda x: x['fileMatch'][0])

    return vscode_schemas

def main():
    """
    Main function to generate VS Code schemas configuration.
    """
    # Base path for SDUI directory
    base_path = "/Users/username/Documents/FMS_GIT/SDUI"

    if not os.path.exists(base_path):
        print(f"Error: SDUI directory not found at {base_path}")
        return 1

    # Generate schemas configuration
    print("Scanning SDUI directory for schema files...")
    vscode_schemas = generate_vscode_schemas(base_path)

    if not vscode_schemas:
        print("No schema files found!")
        return 1

    # Output formatted JSON
    print(f"\nFound {len(vscode_schemas)} schema configurations")
    print("\n" + "="*60)
    print("VS Code json.schemas configuration:")
    print("="*60 + "\n")

    # Pretty print JSON with proper formatting
    output = json.dumps(vscode_schemas, indent=2, ensure_ascii=False)
    print(output)

    # Also save to a file for easy copying
    output_file = "/Users/username/Scripts/Python/vscode_schemas_config.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(output)

    print(f"\n{'='*60}")
    print(f"Configuration also saved to: {output_file}")
    print("You can copy this array to your VS Code settings.json under 'json.schemas'")
    print(f"{'='*60}\n")

    # Show statistics
    print("Statistics by type:")
    schemas = find_schema_files(base_path)
    for schema_type, schema_list in sorted(schemas.items()):
        if schema_list:
            print(f"  - {schema_type}: {len(schema_list)} patterns")

    return 0

if __name__ == "__main__":
    exit(main())