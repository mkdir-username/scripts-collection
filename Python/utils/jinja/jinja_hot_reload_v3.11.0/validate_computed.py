#!/usr/bin/env python3
"""
SDUI Computed Validator CLI
===========================
Standalone validator for SDUI JSON contracts.

Validates:
- Computed section types (no UI components in computed)
- ${computed.X} references point to valid computed functions
- $children arrays don't reference non-computed objects

Usage:
    python validate_computed.py contract.json
    python validate_computed.py contract.json --verbose
    python validate_computed.py contract.json -v
"""

import sys
import os
import argparse

# Add parent directory to path for package import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sdui_tools import VERSION
from sdui_tools.validators import validate_file


def main():
    parser = argparse.ArgumentParser(
        description="SDUI Computed Section Validator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s contract.json
  %(prog)s contract.json --verbose
  %(prog)s [FULL_PC]_main_screen.json -v

Exit codes:
  0 - Validation passed (no errors, warnings allowed)
  1 - Validation failed (errors found)
  2 - File not found or read error
        """
    )
    
    parser.add_argument(
        "file",
        type=str,
        help="Path to SDUI JSON contract file",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed validation info (all computed keys)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {VERSION}",
    )

    args = parser.parse_args()

    file_path = os.path.abspath(args.file)

    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        sys.exit(2)

    print(f"🔍 Validating: {os.path.basename(file_path)}")
    print("-" * 60)

    success = validate_file(file_path, verbose=args.verbose)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
