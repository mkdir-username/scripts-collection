#!/usr/bin/env python3
"""
Jinja2 Hot Reload Script v3.11.0
================================
Modular architecture with computed validation.

Features:
- [JJ_FULL_<platform>] output: Fully assembled Jinja template
- Native {% include %} support (relative & absolute paths)  
- {% from '...' import ... %} macro imports
- {# Jinja comments #} handling
- // JSON comments removal
- MAP/FULL dual output system
- Module imports via // [name](file:///)
- Smart watch mode with dependency tracking
- NEW: Computed section validation

Usage:
    python jinja_hot_reload.py --template path/to/template.java --data path/to/data.json
    python jinja_hot_reload.py --template path/to/template.java --data path/to/data.json --smart
    python jinja_hot_reload.py --template path/to/template.java --data path/to/data.json --no-validate
"""

import sys
import os
import time
import argparse

# Add parent directory to path for package import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sdui_tools import (
    VERSION,
    generate_output_paths,
    get_max_mtime,
    render_template,
)
from sdui_tools.config import DEFAULT_TEMPLATE_PATH, DEFAULT_DATA_PATH


def print_banner():
    """Print startup banner with version and config info."""
    print("=" * 70)
    print(f"Jinja2 Hot Reload v{VERSION} - Modular Architecture")
    print("=" * 70)


def print_config(template_path, data_path, jj_full_path, map_path, full_path):
    """Print current configuration."""
    print(f"📄 Template:     {os.path.basename(template_path)}")
    print(f"💾 Data:         {os.path.basename(data_path)}")
    print(f"📋 JJ_FULL Out:  {os.path.basename(jj_full_path)}")
    print(f"🗺️  MAP Output:   {os.path.basename(map_path)}")
    print(f"✨ FULL Output:  {os.path.basename(full_path)}")
    print("=" * 70)


def run_watch_mode(template_path, data_path, jj_full_path, map_path, full_path,
                   validate_computed=True, verbose_validation=False):
    """
    Run in smart watch mode - monitors file changes and re-renders.
    """
    print("👀 Smart mode enabled. Watching for file changes...\n")

    success, watched_files = render_template(
        template_path, data_path, jj_full_path, map_path, full_path,
        validate_computed=validate_computed,
        verbose_validation=verbose_validation
    )

    last_mtime, _ = get_max_mtime(watched_files)

    while True:
        try:
            current_mtime, changed_file = get_max_mtime(watched_files)

            if current_mtime > last_mtime:
                if changed_file:
                    basename = os.path.basename(changed_file)
                    
                    # Determine file type
                    if changed_file == os.path.abspath(template_path):
                        file_type = "📄 Template"
                    elif changed_file == os.path.abspath(data_path):
                        file_type = "💾 Data"
                    else:
                        file_type = "📦 Module"

                    print(
                        f"\n[{time.strftime('%H:%M:%S')}] 📝 Change detected in {file_type}: {basename}"
                    )

                time.sleep(0.1)

                success, watched_files = render_template(
                    template_path, data_path, jj_full_path, map_path, full_path,
                    validate_computed=validate_computed,
                    verbose_validation=verbose_validation
                )

                last_mtime, _ = get_max_mtime(watched_files)

            time.sleep(1)

        except KeyboardInterrupt:
            print("\n🛑 Stopping watcher.")
            break
        except Exception as e:
            print(f"❌ Error in watch loop: {e}")
            time.sleep(2)


def main():
    parser = argparse.ArgumentParser(
        description=f"Jinja2 Hot Reload Script v{VERSION} - Modular with validation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --template my_template.java --data my_data.json
  %(prog)s --template my_template.java --data my_data.json --smart
  %(prog)s --template my_template.java --data my_data.json --no-validate
  %(prog)s --template my_template.java --data my_data.json --smart --verbose
        """
    )
    
    parser.add_argument(
        "--template", "-t",
        type=str,
        default=DEFAULT_TEMPLATE_PATH,
        help="Path to main .j2 template file",
    )
    parser.add_argument(
        "--data", "-d",
        type=str,
        default=DEFAULT_DATA_PATH,
        help="Path to data JSON file",
    )
    parser.add_argument(
        "--smart", "-s",
        action="store_true",
        help="Enable smart watch mode (monitors file changes)",
    )
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Disable computed section validation",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose validation output (show all computed keys)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {VERSION}",
    )

    args = parser.parse_args()

    template_path = os.path.abspath(args.template)
    data_path = os.path.abspath(args.data)

    jj_full_path, map_path, full_path = generate_output_paths(template_path)

    # Print startup info
    print_banner()
    print_config(template_path, data_path, jj_full_path, map_path, full_path)

    # Validate template exists
    if not os.path.exists(template_path):
        print(f"❌ Template file not found: {template_path}")
        sys.exit(1)

    # Run
    validate_computed = not args.no_validate
    
    if args.smart:
        run_watch_mode(
            template_path, data_path, jj_full_path, map_path, full_path,
            validate_computed=validate_computed,
            verbose_validation=args.verbose
        )
    else:
        success, _ = render_template(
            template_path, data_path, jj_full_path, map_path, full_path,
            validate_computed=validate_computed,
            verbose_validation=args.verbose
        )
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
