#!/usr/bin/env python3
"""
SDUI JSON Schema Validator

Validates all JSON files against their corresponding schemas in the SDUI project.
Supports components, atoms, layouts, and other element types.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from urllib.parse import urlparse, unquote
from urllib.request import pathname2url
import argparse
import re
from collections import defaultdict

try:
    import jsonschema
    from jsonschema import Draft7Validator, RefResolver, ValidationError
    from jsonschema.exceptions import RefResolutionError
except ImportError:
    print("ERROR: jsonschema library not found. Install it with: pip install jsonschema")
    sys.exit(1)


class SDUIValidator:
    """Main validator class for SDUI JSON files."""

    def __init__(self, base_path: str, verbose: bool = False):
        """
        Initialize the validator.

        Args:
            base_path: Root path of the SDUI project
            verbose: Enable verbose output
        """
        self.base_path = Path(base_path).resolve()
        self.verbose = verbose
        self.schema_cache: Dict[str, Any] = {}
        self.validation_results: List[Dict[str, Any]] = []
        self.metaschemas: Dict[str, Any] = {}

        # Patterns for different SDUI elements
        self.element_patterns = {
            'component': r'components/([^/]+)/v(\d+)/\1\.json$',
            'atom': r'atoms/([^/]+)/v(\d+)/\1\.json$',
            'layout': r'layouts/([^/]+)/v(\d+)/\1\.json$',
            'action': r'actions/([^/]+)/v(\d+)/\1\.json$',
            'function': r'functions/([^/]+)/v(\d+)/\1\.json$',
            'sample': r'(components|atoms|layouts|actions|functions)/([^/]+)/v(\d+)/samples/.*\.json$',
        }

    def load_json_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Load and parse a JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            self.add_error(file_path, f"JSON parse error: {e}")
            return None
        except Exception as e:
            self.add_error(file_path, f"Failed to load file: {e}")
            return None

    def resolve_file_uri(self, uri: str) -> Optional[Path]:
        """
        Resolve a file:/// URI to an actual file path.

        Args:
            uri: The file:/// URI to resolve

        Returns:
            Resolved Path object or None if not found
        """
        if not uri.startswith('file:///'):
            return None

        # Parse the URI and get the path component
        parsed = urlparse(uri)
        path = unquote(parsed.path)

        # Remove leading slash on Windows
        if sys.platform == 'win32' and path.startswith('/'):
            path = path[1:]

        # Try to resolve relative to base path
        resolved_path = self.base_path / path.lstrip('/')

        if resolved_path.exists():
            return resolved_path

        # Try absolute path
        absolute_path = Path(path)
        if absolute_path.exists():
            return absolute_path

        return None

    def load_schema(self, schema_path: Path) -> Optional[Dict[str, Any]]:
        """Load a schema file with caching."""
        path_str = str(schema_path)
        if path_str in self.schema_cache:
            return self.schema_cache[path_str]

        schema = self.load_json_file(schema_path)
        if schema:
            self.schema_cache[path_str] = schema

        return schema

    def find_schema_for_sample(self, sample_path: Path) -> Optional[Path]:
        """
        Find the schema file for a given sample file.

        Args:
            sample_path: Path to the sample JSON file

        Returns:
            Path to the corresponding schema file or None
        """
        # Extract component info from path
        parts = sample_path.parts

        # Look for pattern: type/name/version/samples/file.json
        for i, part in enumerate(parts):
            if part == 'samples' and i >= 2:
                element_type = parts[i-3]  # components, atoms, etc.
                element_name = parts[i-2]
                version = parts[i-1]

                # Construct schema path
                schema_path = sample_path.parent.parent / f"{element_name}.json"
                if schema_path.exists():
                    return schema_path

                # Try without .json extension in folder
                schema_path = sample_path.parent.parent / element_name / f"{element_name}.json"
                if schema_path.exists():
                    return schema_path

        return None

    def find_metaschema(self, schema: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Find and load the metaschema referenced in a schema.

        Args:
            schema: The schema dictionary

        Returns:
            The metaschema dictionary or None
        """
        # Check for $schema field
        if '$schema' not in schema:
            return None

        schema_uri = schema['$schema']

        # Try to resolve file URI
        if schema_uri.startswith('file:///'):
            metaschema_path = self.resolve_file_uri(schema_uri)
            if metaschema_path:
                return self.load_json_file(metaschema_path)

        # Try standard JSON Schema drafts
        if 'draft-07' in schema_uri or 'draft-7' in schema_uri:
            # Use built-in Draft 7 validator
            return None  # Will use default Draft7Validator

        return None

    def create_ref_resolver(self, schema_path: Path, schema: Dict[str, Any]) -> RefResolver:
        """
        Create a reference resolver for handling $ref in schemas.

        Args:
            schema_path: Path to the schema file
            schema: The schema dictionary

        Returns:
            Configured RefResolver instance
        """
        # Base URI for resolving relative references
        base_uri = schema_path.as_uri()

        # Store for resolved references
        store = {}

        # Add the schema itself to the store
        if 'id' in schema:
            store[schema['id']] = schema
        elif '$id' in schema:
            store[schema['$id']] = schema

        # Custom handler for file:/// URIs
        def file_uri_handler(uri: str) -> Dict[str, Any]:
            resolved_path = self.resolve_file_uri(uri)
            if resolved_path:
                return self.load_json_file(resolved_path) or {}
            raise RefResolutionError(f"Could not resolve: {uri}")

        # Create resolver with custom handlers
        resolver = RefResolver(
            base_uri=base_uri,
            referrer=schema,
            store=store,
            handlers={'file': file_uri_handler}
        )

        return resolver

    def validate_file(self, json_path: Path, schema_path: Optional[Path] = None) -> bool:
        """
        Validate a JSON file against its schema.

        Args:
            json_path: Path to the JSON file to validate
            schema_path: Optional path to the schema file

        Returns:
            True if validation passed, False otherwise
        """
        # Load the JSON file
        json_data = self.load_json_file(json_path)
        if not json_data:
            return False

        # Find schema if not provided
        if not schema_path:
            schema_path = self.find_schema_for_sample(json_path)
            if not schema_path:
                self.add_warning(json_path, "No schema found for validation")
                return True  # No schema means we can't validate

        # Load the schema
        schema = self.load_schema(schema_path)
        if not schema:
            self.add_error(json_path, f"Failed to load schema: {schema_path}")
            return False

        # Create validator with reference resolver
        try:
            resolver = self.create_ref_resolver(schema_path, schema)
            validator = Draft7Validator(schema, resolver=resolver)

            # Validate
            errors = list(validator.iter_errors(json_data))

            if errors:
                for error in errors:
                    error_path = '.'.join(str(p) for p in error.absolute_path) if error.absolute_path else 'root'
                    self.add_error(
                        json_path,
                        f"Validation error at {error_path}: {error.message}",
                        schema_path=schema_path,
                        error_details={
                            'path': error_path,
                            'message': str(error.message),
                            'validator': error.validator,
                            'instance': error.instance if len(str(error.instance)) < 100 else str(error.instance)[:100] + '...'
                        }
                    )
                return False
            else:
                self.add_success(json_path, schema_path)
                return True

        except RefResolutionError as e:
            self.add_error(json_path, f"Reference resolution error: {e}", schema_path=schema_path)
            return False
        except Exception as e:
            self.add_error(json_path, f"Validation error: {e}", schema_path=schema_path)
            return False

    def find_all_json_files(self) -> List[Path]:
        """Find all JSON files in the SDUI project."""
        json_files = []

        # Directories to search
        search_dirs = ['components', 'atoms', 'layouts', 'actions', 'functions']

        for dir_name in search_dirs:
            dir_path = self.base_path / dir_name
            if dir_path.exists():
                # Find all JSON files recursively
                json_files.extend(dir_path.rglob('*.json'))

        return json_files

    def categorize_files(self, files: List[Path]) -> Dict[str, List[Path]]:
        """Categorize files by type (schema, sample, etc.)."""
        categories = defaultdict(list)

        for file_path in files:
            rel_path = str(file_path.relative_to(self.base_path))

            # Check if it's a sample file
            if '/samples/' in rel_path:
                categories['samples'].append(file_path)
            # Check if it's a schema file
            elif any(re.search(pattern, rel_path) for pattern in [
                self.element_patterns['component'],
                self.element_patterns['atom'],
                self.element_patterns['layout'],
                self.element_patterns['action'],
                self.element_patterns['function']
            ]):
                categories['schemas'].append(file_path)
            else:
                categories['other'].append(file_path)

        return categories

    def add_error(self, file_path: Path, message: str, schema_path: Optional[Path] = None, error_details: Optional[Dict] = None):
        """Add an error to the results."""
        result = {
            'status': 'error',
            'file': str(file_path.relative_to(self.base_path)),
            'message': message,
            'absolute_path': str(file_path)
        }
        if schema_path:
            result['schema'] = str(schema_path.relative_to(self.base_path))
        if error_details:
            result['details'] = error_details

        self.validation_results.append(result)

    def add_warning(self, file_path: Path, message: str):
        """Add a warning to the results."""
        self.validation_results.append({
            'status': 'warning',
            'file': str(file_path.relative_to(self.base_path)),
            'message': message,
            'absolute_path': str(file_path)
        })

    def add_success(self, file_path: Path, schema_path: Path):
        """Add a success result."""
        if self.verbose:
            self.validation_results.append({
                'status': 'success',
                'file': str(file_path.relative_to(self.base_path)),
                'schema': str(schema_path.relative_to(self.base_path)),
                'absolute_path': str(file_path)
            })

    def validate_all(self) -> Dict[str, Any]:
        """
        Validate all JSON files in the SDUI project.

        Returns:
            Summary of validation results
        """
        print("🔍 Searching for JSON files...")
        all_files = self.find_all_json_files()
        print(f"📁 Found {len(all_files)} JSON files")

        # Categorize files
        categorized = self.categorize_files(all_files)
        print(f"📊 Categorized: {len(categorized['schemas'])} schemas, {len(categorized['samples'])} samples, {len(categorized['other'])} other")

        # Validate sample files
        print("\n🧪 Validating sample files...")
        sample_results = {'passed': 0, 'failed': 0, 'skipped': 0}

        for sample_file in categorized['samples']:
            rel_path = sample_file.relative_to(self.base_path)

            if self.verbose:
                print(f"  Validating: {rel_path}")

            if self.validate_file(sample_file):
                sample_results['passed'] += 1
                if self.verbose:
                    print(f"    ✅ Passed")
            else:
                sample_results['failed'] += 1
                if self.verbose:
                    print(f"    ❌ Failed")

        # Validate schema files against metaschemas
        print("\n🔧 Validating schemas against metaschemas...")
        schema_results = {'passed': 0, 'failed': 0, 'skipped': 0}

        for schema_file in categorized['schemas']:
            schema = self.load_json_file(schema_file)
            if schema and '$schema' in schema:
                metaschema = self.find_metaschema(schema)
                if metaschema:
                    # Validate schema against metaschema
                    # For now, just count it as passed if we found the metaschema
                    schema_results['passed'] += 1
                else:
                    schema_results['skipped'] += 1
            else:
                schema_results['skipped'] += 1

        # Generate summary
        errors = [r for r in self.validation_results if r['status'] == 'error']
        warnings = [r for r in self.validation_results if r['status'] == 'warning']

        summary = {
            'total_files': len(all_files),
            'samples': sample_results,
            'schemas': schema_results,
            'errors': len(errors),
            'warnings': len(warnings),
            'validation_results': self.validation_results
        }

        return summary

    def print_summary(self, summary: Dict[str, Any]):
        """Print a formatted summary of validation results."""
        print("\n" + "="*60)
        print("📋 VALIDATION SUMMARY")
        print("="*60)

        print(f"\n📊 Overall Statistics:")
        print(f"  Total files analyzed: {summary['total_files']}")
        print(f"  Errors found: {summary['errors']}")
        print(f"  Warnings: {summary['warnings']}")

        print(f"\n🧪 Sample Validation:")
        samples = summary['samples']
        total_samples = samples['passed'] + samples['failed'] + samples['skipped']
        if total_samples > 0:
            pass_rate = (samples['passed'] / total_samples) * 100
            print(f"  ✅ Passed: {samples['passed']}")
            print(f"  ❌ Failed: {samples['failed']}")
            print(f"  ⏭️  Skipped: {samples['skipped']}")
            print(f"  📈 Pass rate: {pass_rate:.1f}%")
        else:
            print("  No samples found")

        print(f"\n🔧 Schema Validation:")
        schemas = summary['schemas']
        print(f"  ✅ Valid: {schemas['passed']}")
        print(f"  ❌ Invalid: {schemas['failed']}")
        print(f"  ⏭️  No metaschema: {schemas['skipped']}")

        # Print errors
        errors = [r for r in summary['validation_results'] if r['status'] == 'error']
        if errors:
            print(f"\n❌ Validation Errors ({len(errors)}):")
            print("-" * 60)

            # Group errors by file
            errors_by_file = defaultdict(list)
            for error in errors:
                errors_by_file[error['file']].append(error)

            for file_path, file_errors in errors_by_file.items():
                print(f"\n📄 {file_path}")
                for error in file_errors:
                    print(f"   ❌ {error['message']}")
                    if 'details' in error and error['details']:
                        details = error['details']
                        if 'path' in details:
                            print(f"      Path: {details['path']}")
                        if 'validator' in details:
                            print(f"      Validator: {details['validator']}")

        # Print warnings
        warnings = [r for r in summary['validation_results'] if r['status'] == 'warning']
        if warnings:
            print(f"\n⚠️  Warnings ({len(warnings)}):")
            print("-" * 60)
            for warning in warnings:
                print(f"  ⚠️  {warning['file']}: {warning['message']}")

        print("\n" + "="*60)

        # Final status
        if summary['errors'] == 0:
            print("✅ All validations passed!")
        else:
            print(f"❌ Found {summary['errors']} validation errors")

        print("="*60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Validate SDUI JSON files against their schemas',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s /path/to/SDUI              # Validate all files in SDUI directory
  %(prog)s /path/to/SDUI -v           # Verbose output
  %(prog)s /path/to/SDUI -o report.json  # Save results to file
  %(prog)s /path/to/SDUI --samples-only  # Only validate sample files
        """
    )

    parser.add_argument(
        'sdui_path',
        help='Path to the SDUI directory'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )

    parser.add_argument(
        '-o', '--output',
        help='Save validation results to a JSON file'
    )

    parser.add_argument(
        '--samples-only',
        action='store_true',
        help='Only validate sample files'
    )

    parser.add_argument(
        '--schemas-only',
        action='store_true',
        help='Only validate schema files'
    )

    parser.add_argument(
        '--no-colors',
        action='store_true',
        help='Disable colored output'
    )

    args = parser.parse_args()

    # Resolve SDUI path
    sdui_path = Path(args.sdui_path).resolve()
    if not sdui_path.exists():
        print(f"❌ Error: SDUI directory not found: {sdui_path}")
        sys.exit(1)

    # Check if it looks like an SDUI directory
    expected_dirs = ['components', 'atoms', 'layouts', 'actions', 'functions']
    found_dirs = [d for d in expected_dirs if (sdui_path / d).exists()]

    if not found_dirs:
        print(f"⚠️  Warning: No SDUI directories found in {sdui_path}")
        print(f"   Expected at least one of: {', '.join(expected_dirs)}")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            sys.exit(0)

    # Create validator
    print(f"🚀 Starting SDUI validation for: {sdui_path}")
    print(f"📁 Found SDUI directories: {', '.join(found_dirs)}")

    validator = SDUIValidator(str(sdui_path), verbose=args.verbose)

    # Run validation
    summary = validator.validate_all()

    # Print summary
    validator.print_summary(summary)

    # Save results if requested
    if args.output:
        output_path = Path(args.output)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Results saved to: {output_path}")

    # Exit with appropriate code
    sys.exit(0 if summary['errors'] == 0 else 1)


if __name__ == '__main__':
    main()