#!/usr/bin/env python3
"""
Jinja2 Hot Reload Script v3.10.3
Base: v3.10.1 (my architecture) + resolve_jinja_includes for full JJ_FULL assembly

Features:
- [JJ_FULL_<platform>] output: Fully assembled Jinja template with ALL includes
  and macros resolved inline ({% include %}, {% from ... import %})
- Native {% include %} support (relative & absolute paths)
- {% from '...' import ... %} macro imports
- {# Jinja comments #} handling
- // JSON comments removal
- MAP/FULL dual output system
- Module imports via // [name](file:///)
- Smart watch mode with FULL dependency tracking
"""

import sys
import os
import json
import time
import re
import argparse
import tempfile
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from urllib.parse import unquote

# ==================== CONFIGURATION ====================
DEFAULT_TEMPLATE_PATH = "_JSON/WEB/payroll/1.0_main_screen/desktop/[JJ_PC]_1.0_main_screen_modular_web.java"
DEFAULT_DATA_PATH = "_JSON/WEB/payroll/1.0_main_screen/[data]_1.0_main_screen.json"

# ==================== UTILITY FUNCTIONS ====================


def generate_output_paths(template_path):
    """
    Generate MAP, FULL, and JJ_FULL output paths from template path.

    Output files:
    - [JJ_FULL_PC]_name.java - Assembled Jinja (includes resolved, vars not replaced)
    - [MAP_PC]_name.json     - Rendered with comments & module markers
    - [FULL_PC]_name.json    - Clean JSON

    Supports extensions: .json.j2, .j2.java, .java, .j2
    """
    template_dir = os.path.dirname(template_path)
    template_file = os.path.basename(template_path)

    # Pattern: [JJ_<PLATFORM>]_name.<ext>
    match = re.match(r"^\[JJ_(\w+)\]_(.+?)\.(json\.j2|j2\.java|java|j2)$", template_file)

    if match:
        platform = match.group(1)
        base_name = match.group(2)

        jj_full_filename = f"[JJ_FULL_{platform}]_{base_name}.java"
        map_filename = f"[MAP_{platform}]_{base_name}.json"
        full_filename = f"[FULL_{platform}]_{base_name}.json"

        output_dir = template_dir
    else:
        # Fallback for non-standard naming
        base_name = template_file
        for ext in [".json.j2", ".j2.java", ".java", ".j2"]:
            if base_name.endswith(ext):
                base_name = base_name[: -len(ext)]
                break

        jj_full_filename = f"{base_name}_jj_full.java"
        map_filename = f"{base_name}_map.json"
        full_filename = f"{base_name}_output.json"
        output_dir = template_dir

    jj_full_path = os.path.join(output_dir, jj_full_filename)
    map_path = os.path.join(output_dir, map_filename)
    full_path = os.path.join(output_dir, full_filename)

    return jj_full_path, map_path, full_path


def json_finalize(thing):
    """
    Custom finalize function for Jinja2 to ensure Python types
    correspond to valid JSON values.
    """
    if thing is None:
        return "null"
    if isinstance(thing, bool):
        return "true" if thing else "false"
    if isinstance(thing, (dict, list)):
        return json.dumps(thing, ensure_ascii=False)
    return thing


def remove_json_comments(content):
    """
    Remove JSON comments from rendered content:
    1. // line comments (preserving URLs like http://)
    2. {# Jinja2 block comments #}

    Also removes trailing commas before closing brackets.
    """
    # Step 1: Remove {# Jinja2 comments #}
    content = re.sub(r"\{#.*?#\}", "", content, flags=re.DOTALL)

    # Step 2: Remove // comments (line by line)
    lines = content.split("\n")
    result = []

    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("//"):
            continue

        # Check for inline // comments (but preserve URLs)
        if "//" in line:
            idx = line.find("//")
            if idx > 0:
                prefix = line[:idx]
                if not (prefix.endswith("http:") or prefix.endswith("https:")):
                    line = prefix.rstrip()

        result.append(line)

    content = "\n".join(result)

    # Step 3: Remove trailing commas
    content = re.sub(r",(\s*[}\]])", r"\1", content)

    return content


def resolve_include_path(file_path, template_dir):
    """
    Resolve an include path to an absolute path.

    Args:
        file_path: The path from the include/from statement
        template_dir: The directory of the current template

    Returns:
        str or None: Resolved absolute path, or None if not found
    """
    if os.path.isabs(file_path):
        return file_path if os.path.exists(file_path) else None

    candidates = [
        os.path.join(template_dir, file_path),
        os.path.join(os.path.dirname(template_dir), file_path),
        os.path.normpath(os.path.join(template_dir, file_path)),
    ]

    for candidate in candidates:
        if os.path.exists(candidate):
            return os.path.abspath(candidate)

    return None


def parse_module_imports(content, base_dir, processed_files=None, collected_files=None):
    """
    Parse and resolve module imports in the format:
    // [description](file:///absolute/path/to/module.j2)

    Returns:
        tuple: (processed_content, collected_files)
    """
    if processed_files is None:
        processed_files = set()
    if collected_files is None:
        collected_files = set()

    pattern = r"^(\s*)//\s*\[.*?\]\(file:///([^)]+)\)\s*$"

    lines = content.split("\n")
    result_lines = []

    for line in lines:
        match = re.match(pattern, line)
        if match:
            indent = match.group(1)
            file_uri = match.group(2)
            file_path = unquote(file_uri)

            if not os.path.isabs(file_path):
                candidates = [
                    os.path.join(base_dir, file_path),
                    os.path.join(os.path.dirname(base_dir), file_path),
                ]

                resolved_path = None
                for candidate in candidates:
                    if os.path.exists(candidate):
                        resolved_path = candidate
                        break

                file_path = resolved_path if resolved_path else candidates[0]

            file_path = os.path.abspath(file_path)

            if file_path in processed_files:
                result_lines.append(
                    f"{indent}// [CIRCULAR IMPORT DETECTED: {os.path.basename(file_path)}]"
                )
                print(f"⚠️  Warning: Circular import detected for {file_path}")
                continue

            if not os.path.exists(file_path):
                result_lines.append(f"{indent}// [MODULE NOT FOUND: {file_path}]")
                print(f"⚠️  Warning: Module not found: {file_path}")
                continue

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    module_content = f.read()

                new_processed = processed_files.copy()
                new_processed.add(file_path)
                collected_files.add(file_path)

                module_dir = os.path.dirname(file_path)
                processed_module, collected_files = parse_module_imports(
                    module_content, module_dir, new_processed, collected_files
                )

                module_lines = processed_module.split("\n")
                indented_module = "\n".join(
                    indent + line if line.strip() else line for line in module_lines
                )

                module_name = os.path.basename(file_path)
                result_lines.append(f"{indent}// ▼ START MODULE: {module_name}")
                result_lines.append(indented_module)
                result_lines.append(f"{indent}// ▲ END MODULE: {module_name}")

                print(f"    📦 Loaded module: {module_name}")

            except Exception as e:
                result_lines.append(f"{indent}// [ERROR LOADING MODULE: {e}]")
                print(f"❌ Error loading module {file_path}: {e}")
        else:
            result_lines.append(line)

    return "\n".join(result_lines), collected_files


def resolve_jinja_includes(
    content, template_dir, processed_files=None, collected_files=None
):
    """
    Resolve {% include '...' %} and {% from '...' import ... %} statements
    WITHOUT rendering Jinja variables. Creates a fully assembled template
    that can be inspected before data substitution.

    Args:
        content: Template content to process
        template_dir: Base directory for include resolution
        processed_files: Set of already processed files (circular import prevention)
        collected_files: Set to collect all resolved file paths (for watch mode)

    Returns:
        tuple: (content_with_includes_resolved, collected_files)
    """
    if processed_files is None:
        processed_files = set()
    if collected_files is None:
        collected_files = set()

    # Pattern for {% include 'path/to/file.j2' %}
    include_pattern = r"\{%\s*include\s+['\"]([^'\"]+)['\"]\s*%\}"

    # Pattern for {% from 'path/to/file.j2' import macro_name %}
    from_pattern = r"\{%\s*from\s+['\"]([^'\"]+)['\"]\s+import\s+([^%]+)\s*%\}"

    result = content

    # Process {% from ... import ... %} first
    from_matches = list(re.finditer(from_pattern, result))
    for match in reversed(from_matches):
        file_path = match.group(1)
        imports = match.group(2).strip()

        resolved_path = resolve_include_path(file_path, template_dir)

        if resolved_path and os.path.exists(resolved_path):
            collected_files.add(resolved_path)

            if resolved_path not in processed_files:
                try:
                    with open(resolved_path, "r", encoding="utf-8") as f:
                        macro_content = f.read()

                    new_processed = processed_files.copy()
                    new_processed.add(resolved_path)

                    macro_dir = os.path.dirname(resolved_path)
                    resolved_macro, collected_files = resolve_jinja_includes(
                        macro_content, macro_dir, new_processed, collected_files
                    )

                    macro_name = os.path.basename(resolved_path)
                    replacement = f"{{# ▼ FROM: {macro_name} (import {imports}) #}}\n{resolved_macro}\n{{# ▲ END FROM: {macro_name} #}}"

                    result = (
                        result[: match.start()] + replacement + result[match.end() :]
                    )

                except Exception as e:
                    print(f"⚠️  Error resolving from-import {file_path}: {e}")
            else:
                result = (
                    result[: match.start()]
                    + f"{{# CIRCULAR IMPORT: {file_path} #}}"
                    + result[match.end() :]
                )
        else:
            print(f"⚠️  Warning: from-import file not found: {file_path}")

    # Process {% include ... %} statements
    include_matches = list(re.finditer(include_pattern, result))
    for match in reversed(include_matches):
        file_path = match.group(1)

        resolved_path = resolve_include_path(file_path, template_dir)

        if resolved_path and os.path.exists(resolved_path):
            collected_files.add(resolved_path)

            if resolved_path not in processed_files:
                try:
                    with open(resolved_path, "r", encoding="utf-8") as f:
                        include_content = f.read()

                    new_processed = processed_files.copy()
                    new_processed.add(resolved_path)

                    include_dir = os.path.dirname(resolved_path)
                    resolved_include, collected_files = resolve_jinja_includes(
                        include_content, include_dir, new_processed, collected_files
                    )

                    include_name = os.path.basename(resolved_path)
                    replacement = f"{{# ▼ INCLUDE: {include_name} #}}\n{resolved_include}\n{{# ▲ END INCLUDE: {include_name} #}}"

                    result = (
                        result[: match.start()] + replacement + result[match.end() :]
                    )

                except Exception as e:
                    print(f"⚠️  Error resolving include {file_path}: {e}")
            else:
                result = (
                    result[: match.start()]
                    + f"{{# CIRCULAR INCLUDE: {file_path} #}}"
                    + result[match.end() :]
                )
        else:
            print(f"⚠️  Warning: include file not found: {file_path}")

    return result, collected_files


def get_max_mtime(files):
    """
    Get maximum modification time across all files.

    Returns:
        tuple: (max_mtime, changed_file_path or None)
    """
    max_mtime = 0
    changed_file = None

    for f in files:
        if os.path.exists(f):
            mtime = os.path.getmtime(f)
            if mtime > max_mtime:
                max_mtime = mtime
                changed_file = f

    return max_mtime, changed_file


# ==================== MAIN RENDERING FUNCTION ====================


def render_template(template_path, data_path, jj_full_path, map_path, full_path):
    """
    Main rendering function that:
    1. Loads data from JSON
    2. Processes custom module imports (// [name](file:///...))
    3. Resolves Jinja includes/imports for JJ_FULL
    4. Renders Jinja2 template
    5. Writes MAP output (with comments and markers)
    6. Writes FULL output (clean JSON)

    Returns:
        tuple: (success: bool, watched_files: set)
    """
    print(f"[{time.strftime('%H:%M:%S')}] 🔨 Processing...")

    watched_files = set()
    watched_files.add(os.path.abspath(template_path))
    watched_files.add(os.path.abspath(data_path))

    # === STEP 1: Load Data ===
    if not os.path.exists(data_path):
        print(f"❌ Error: Data file not found: {data_path}")
        return False, watched_files

    try:
        with open(data_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing JSON data: {e}")
        return False, watched_files
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return False, watched_files

    # === STEP 2: Read Template ===
    template_dir = os.path.dirname(os.path.abspath(template_path))

    if not os.path.exists(template_path):
        print(f"❌ Error: Template file not found: {template_path}")
        return False, watched_files

    try:
        with open(template_path, "r", encoding="utf-8") as f:
            template_content = f.read()

        # === STEP 3: Process Custom Module Imports ===
        print(f"[{time.strftime('%H:%M:%S')}] 📦 Processing custom module imports...")
        processed_content, module_files = parse_module_imports(
            template_content, template_dir
        )
        watched_files.update(module_files)

        # === STEP 4: Resolve Jinja Includes for JJ_FULL ===
        print(f"[{time.strftime('%H:%M:%S')}] 📄 Resolving Jinja includes/imports...")
        assembled_jinja, include_files = resolve_jinja_includes(
            processed_content, template_dir
        )
        watched_files.update(include_files)

        # === STEP 5: Write JJ_FULL Output ===
        try:
            os.makedirs(os.path.dirname(jj_full_path), exist_ok=True)

            with open(jj_full_path, "w", encoding="utf-8") as f:
                f.write(assembled_jinja)

            print(
                f"[{time.strftime('%H:%M:%S')}] 📋 JJ_FULL file written: {os.path.basename(jj_full_path)}"
            )
        except Exception as e:
            print(f"❌ Error writing JJ_FULL output: {e}")
            return False, watched_files

        # === STEP 6: Create Temp File for Jinja Rendering ===
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", suffix=".j2", delete=False
        ) as tmp:
            tmp.write(processed_content)
            tmp_path = tmp.name

        # === STEP 7: Setup Jinja2 Environment ===
        tmp_dir = os.path.dirname(tmp_path)
        tmp_file = os.path.basename(tmp_path)

        env = Environment(
            loader=FileSystemLoader([template_dir, tmp_dir]),
            finalize=json_finalize,
            autoescape=False,
            undefined=StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True,
        )

        env.globals["null"] = None
        env.globals["true"] = True
        env.globals["false"] = False

        # === STEP 8: Render Template ===
        template = env.get_template(tmp_file)
        render_context = data.copy()
        render_context["null"] = None
        render_context["true"] = True
        render_context["false"] = False

        try:
            rendered = template.render(**render_context)
            os.unlink(tmp_path)

        except Exception as render_error:
            # Don't fail - log warning and create placeholder
            print(f"⚠️  WARNING: Template rendering failed: {render_error}")
            print(f"⚠️  Generating placeholder output...")

            # Clean up temp file
            if os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except:
                    pass

            # Create noticeable placeholder JSON
            placeholder = {
                "⚠️⚠️⚠️ JINJA_RENDER_ERROR ⚠️⚠️⚠️": True,
                "error": str(render_error),
                "message": "Template rendering failed. Check data file and template for missing variables.",
                "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
                "template": os.path.basename(template_path),
                "data": os.path.basename(data_path),
                "hint": "This is a placeholder. Fix the error above to generate real output."
            }

            rendered = json.dumps(placeholder, indent=2, ensure_ascii=False)

    except Exception as e:
        print(f"❌ Error in template setup: {e}")
        if "tmp_path" in locals():
            try:
                os.unlink(tmp_path)
            except:
                pass
        return False, watched_files

    # === STEP 9: Write MAP Output ===
    try:
        os.makedirs(os.path.dirname(map_path), exist_ok=True)

        with open(map_path, "w", encoding="utf-8") as f:
            f.write(rendered)

        print(
            f"[{time.strftime('%H:%M:%S')}] 🗺️  MAP file written: {os.path.basename(map_path)}"
        )
    except Exception as e:
        print(f"❌ Error writing MAP output: {e}")
        return False, watched_files

    # === STEP 10: Remove Comments & Write FULL Output ===
    try:
        print(f"[{time.strftime('%H:%M:%S')}] 🧹 Removing comments for FULL file...")
        clean_content = remove_json_comments(rendered)

        try:
            json_obj = json.loads(clean_content)

            with open(full_path, "w", encoding="utf-8") as f:
                json.dump(json_obj, f, indent=2, ensure_ascii=False)

            print(
                f"[{time.strftime('%H:%M:%S')}] ✅ FULL file written: {os.path.basename(full_path)}"
            )

            # Show watched files with types
            print(f"[{time.strftime('%H:%M:%S')}] 👁️  Watching {len(watched_files)} file(s):")
            for wf in sorted(watched_files):
                basename = os.path.basename(wf)
                if wf == os.path.abspath(template_path):
                    print(f"     📄 Template: {basename}")
                elif wf == os.path.abspath(data_path):
                    print(f"     💾 Data:     {basename}")
                else:
                    print(f"     📦 Module:   {basename}")

            return True, watched_files

        except json.JSONDecodeError as e:
            debug_path = full_path + ".debug"
            with open(debug_path, "w", encoding="utf-8") as f:
                f.write(clean_content)

            print(f"❌ JSON validation error (line {e.lineno}, col {e.colno}): {e.msg}")
            print(f"   Debug file saved: {os.path.basename(debug_path)}")

            lines = clean_content.splitlines()
            if 0 <= e.lineno - 1 < len(lines):
                print(f"   >> {lines[e.lineno - 1].strip()}")

            return False, watched_files

    except Exception as e:
        print(f"❌ Error writing FULL output: {e}")
        return False, watched_files


# ==================== MAIN ENTRY POINT ====================


def main():
    parser = argparse.ArgumentParser(
        description="Jinja2 Hot Reload Script v3.10.3 - Full assembly + watch tracking"
    )
    parser.add_argument(
        "--template",
        type=str,
        default=DEFAULT_TEMPLATE_PATH,
        help="Path to main .j2 template file",
    )
    parser.add_argument(
        "--data", type=str, default=DEFAULT_DATA_PATH, help="Path to data JSON file"
    )
    parser.add_argument(
        "--smart",
        action="store_true",
        help="Enable smart watch mode (monitors file changes)",
    )

    args = parser.parse_args()

    template_path = os.path.abspath(args.template)
    data_path = os.path.abspath(args.data)

    jj_full_path, map_path, full_path = generate_output_paths(template_path)

    # Print configuration
    print("=" * 70)
    print("Jinja2 Hot Reload v3.10.3 - Full Assembly + Watch Tracking")
    print("=" * 70)
    print(f"📄 Template:     {os.path.basename(template_path)}")
    print(f"💾 Data:         {os.path.basename(data_path)}")
    print(f"📋 JJ_FULL Out:  {os.path.basename(jj_full_path)}")
    print(f"🗺️  MAP Output:   {os.path.basename(map_path)}")
    print(f"✨ FULL Output:  {os.path.basename(full_path)}")
    print("=" * 70)

    if not os.path.exists(template_path):
        print(f"❌ Template file not found: {template_path}")
        return

    if args.smart:
        print("👀 Smart mode enabled. Watching for file changes...\n")

        success, watched_files = render_template(
            template_path, data_path, jj_full_path, map_path, full_path
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
                        template_path, data_path, jj_full_path, map_path, full_path
                    )

                    last_mtime, _ = get_max_mtime(watched_files)

                time.sleep(1)

            except KeyboardInterrupt:
                print("\n🛑 Stopping watcher.")
                break
            except Exception as e:
                print(f"❌ Error in watch loop: {e}")
                time.sleep(2)
    else:
        render_template(template_path, data_path, jj_full_path, map_path, full_path)


if __name__ == "__main__":
    main()
