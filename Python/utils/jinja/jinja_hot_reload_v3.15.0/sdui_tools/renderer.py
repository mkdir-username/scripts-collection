"""
SDUI Tools Renderer
===================
Основная функция рендеринга Jinja2 шаблонов в SDUI JSON контракты.
"""

import os
import json
import time
import tempfile
import subprocess

from .config import JINJAVA_JAR_PATH
from .utils import json_finalize, remove_json_comments, safe_write_file
from .imports import parse_module_imports, resolve_jinja_includes, jinjava_compat, restore_sdui_el
from .validators import validate_sdui_contract, format_validation_report


def render_template(template_path, data_path, jj_full_path, map_path, full_path, 
                   validate_computed=True, verbose_validation=False):
    """
    Main rendering function.
    
    Pipeline:
    1. Load data from JSON
    2. Process custom module imports (// [name](file:///...))
    3. Resolve Jinja includes/imports for JJ_FULL
    4. Render Jinja2 template
    5. Write MAP output (with comments and markers)
    6. Validate computed section (NEW!)
    7. Write FULL output (clean JSON)
    
    Args:
        template_path: Path to main .j2 template file
        data_path: Path to data JSON file
        jj_full_path: Output path for assembled Jinja
        map_path: Output path for rendered with comments
        full_path: Output path for clean JSON
        validate_computed: Whether to run computed validation
        verbose_validation: Show detailed validation info
        
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

        # === STEP 4.5: Jinjava Compatibility Transform ===
        assembled_jinja = jinjava_compat(assembled_jinja)

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
        # FIX: Pass assembled_jinja (inlined includes) to Jinjava to avoid include resolution issues
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", suffix=".j2", delete=False
        ) as tmp:
            tmp.write(assembled_jinja)
            tmp_path = tmp.name

        # === STEP 7: Render via Jinjava (Java) ===
        print(f"[{time.strftime('%H:%M:%S')}] ☕ Rendering via Jinjava...")
        
        jar_path = JINJAVA_JAR_PATH

        # Create temp data file with injected globals for backward compatibility
        # Mimics Python's env.globals behavior
        data_with_globals = data.copy()
        data_with_globals["null"] = None
        data_with_globals["none"] = None  # Python keyword compatibility
        data_with_globals["true"] = True
        data_with_globals["false"] = False

        tmp_data_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", suffix=".json", delete=False
            ) as tmp_data:
                json.dump(data_with_globals, tmp_data, ensure_ascii=False)
                tmp_data_path = tmp_data.name

            cmd = ['java', '-jar', jar_path, tmp_path, tmp_data_path]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                encoding='utf-8'
            )
            
            # Clean up temp files
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            if tmp_data_path and os.path.exists(tmp_data_path):
                os.unlink(tmp_data_path)

            if result.returncode != 0:
                error_msg = result.stderr.strip() if result.stderr else "Unknown Java error"
                print(f"❌ Template rendering failed\n  - {error_msg}")
                raise Exception(error_msg)
            
            rendered = result.stdout

            # Restore SDUI EL placeholders: __SDUI_DOLLAR__ → $
            rendered = restore_sdui_el(rendered)

        except Exception as render_error:
            # Clean up temp data file if error occurred before cleanup
            if 'tmp_data_path' in locals() and tmp_data_path and os.path.exists(tmp_data_path):
                try:
                    os.unlink(tmp_data_path)
                except:
                    pass

            # Don't fail - log warning and create placeholder
            print(f"⚠️  WARNING: Template rendering failed: {render_error}")
            print(f"⚠️  Generating placeholder output...")

            # Clean up temp file (if not already done)
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

    # === STEP 10: Remove Comments & Parse JSON ===
    try:
        print(f"[{time.strftime('%H:%M:%S')}] 🧹 Removing comments for FULL file...")
        clean_content = remove_json_comments(rendered)

        try:
            json_obj = json.loads(clean_content)

            # === STEP 11: Validate Computed Section (NEW!) ===
            if validate_computed:
                print(f"[{time.strftime('%H:%M:%S')}] 🔍 Validating computed section...")
                validation_result = validate_sdui_contract(json_obj)
                
                if not validation_result.is_valid or validation_result.warnings:
                    print()  # Empty line before report
                    report = format_validation_report(
                        validation_result, 
                        verbose=verbose_validation
                    )
                    print(report)
                    print()  # Empty line after report
                else:
                    print(f"[{time.strftime('%H:%M:%S')}] ✓ Computed validation passed")

            # === STEP 12: Write FULL Output ===
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
