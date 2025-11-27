import sys
import os
import json
import time
import re
import argparse
import subprocess
from jinja2 import Environment, FileSystemLoader, StrictUndefined

# Configuration for the specific task
TEMPLATE_PATH = '/Users/username/Documents/FMS_GIT/_JSON/WEB/payroll/1.0_main_screen/desktop/[JJ_PC]_1.0_main_screen_modular_v2.j2.java'
DATA_PATH = '/Users/username/Documents/FMS_GIT/_JSON/WEB/payroll/1.0_main_screen/[data]_1.0_main_screen.json'
BROWSER_URL = "http://localhost:8080"

def generate_output_path(template_path):
    """
    Generate output path from template path.
    [JJ_PC]_name.j2.java -> [FULL_PC]_name_web.json
    [JJ_MOB]_name.j2.java -> [FULL_MOB]_name_web.json
    """
    template_dir = os.path.dirname(template_path)
    template_file = os.path.basename(template_path)

    # Extract platform from [JJ_<PLATFORM>]
    match = re.match(r'^\[JJ_(\w+)\]_(.+)\.j2\.java$', template_file)
    if not match:
        # Fallback if pattern doesn't match
        base_name = os.path.splitext(os.path.splitext(template_file)[0])[0]
        return os.path.join(template_dir, f"{base_name}_output.json")

    platform = match.group(1)  # PC, MOB, etc.
    base_name = match.group(2)  # 1.0_main_screen_modular

    output_filename = f"[FULL_{platform}]_{base_name}_web.json"
    return os.path.join(template_dir, output_filename)

def json_finalize(thing):
    """
    Custom finalize function to ensure Python types correspond to valid JSON values.
    """
    if thing is None:
        return "null"
    if isinstance(thing, bool):
        return "true" if thing else "false"
    if isinstance(thing, (dict, list)):
        return json.dumps(thing, ensure_ascii=False)
    return thing

def reload_browser():
    """
    Reloads the browser tab at localhost:8080.
    Optimized for macOS and Vivaldi.
    """
    print(f"[{time.strftime('%H:%M:%S')}] 🔄 Reloading {BROWSER_URL}...")

    if sys.platform == 'darwin':
        # AppleScript to reload the active tab in Vivaldi
        # This avoids opening duplicate tabs
        script = """
        tell application "Vivaldi"
            if (count of windows) > 0 then
                tell active tab of window 1
                    reload
                end tell
            else
                open location \"%s\"
            end if
        end tell
        """ % BROWSER_URL

        try:
            subprocess.run(['osascript', '-e', script], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return
        except subprocess.CalledProcessError:
            pass # Fallback if Vivaldi isn't the default or script fails
            
    # Fallback: generic open (might create new tabs)
    import webbrowser
    webbrowser.open(BROWSER_URL)

def render_template(template_path, data_path, output_path):
    print(f"[{time.strftime('%H:%M:%S')}] 🔨 Processing...")
    
    # 1. Load Data
    if not os.path.exists(data_path):
        print(f"Error: Data file not found: {data_path}")
        return False

    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON data: {e}")
        return False
    except Exception as e:
        print(f"Error loading data: {e}")
        return False

    # 2. Setup Jinja2 Environment
    template_dir = os.path.dirname(template_path)
    template_file = os.path.basename(template_path)
    
    if not os.path.exists(template_path):
        print(f"Error: Template file not found: {template_path}")
        return False

    env = Environment(
        loader=FileSystemLoader(template_dir),
        finalize=json_finalize,
        autoescape=False, # We are generating JSON, not HTML
        undefined=StrictUndefined # Fail on missing variables
    )
    
    # Add support for 'null', 'true', 'false'
    env.globals['null'] = None
    env.globals['true'] = True
    env.globals['false'] = False
    
    # 3. Render
    try:
        template = env.get_template(template_file)
        # Pass null, true, false directly to the render context
        render_context = data.copy()
        render_context['null'] = None
        render_context['true'] = True
        render_context['false'] = False
        rendered = template.render(**render_context)
    except Exception as e:
        print(f"Error rendering template: {e}")
        return False

    # 4. Write Output
    try:
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(rendered)
        print(f"[{time.strftime('%H:%M:%S')}] ✅ Success! Output written to: {output_path}")
        return True
    except Exception as e:
        print(f"Error writing output: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Jinja2 Hot Reload Script v3.6.3")
    parser.add_argument("--smart", action="store_true", help="Watch for changes in template and data files")
    args = parser.parse_args()

    # Generate output path from template path
    output_path = generate_output_path(TEMPLATE_PATH)

    print(f"Input Template: {TEMPLATE_PATH}")
    print(f"Input Data:     {DATA_PATH}")
    print(f"Output File:    {output_path}")
    print("-" * 60)

    if args.smart:
        print("👀 Smart mode enabled. Watching files and reloading browser...")
        
        # Initial render
        if render_template(TEMPLATE_PATH, DATA_PATH, output_path):
            reload_browser()

        last_mtime = 0
        # Initialize last_mtime with current max to avoid immediate double render if files exist
        if os.path.exists(TEMPLATE_PATH) and os.path.exists(DATA_PATH):
            last_mtime = max(os.path.getmtime(TEMPLATE_PATH), os.path.getmtime(DATA_PATH))

        while True:
            try:
                if os.path.exists(TEMPLATE_PATH) and os.path.exists(DATA_PATH):
                    t_mtime = os.path.getmtime(TEMPLATE_PATH)
                    d_mtime = os.path.getmtime(DATA_PATH)
                    current_max_mtime = max(t_mtime, d_mtime)

                    if current_max_mtime > last_mtime:
                        # Identify what changed for log clarity
                        if t_mtime > last_mtime:
                            print(f"\n[{time.strftime('%H:%M:%S')}] 📝 Template change detected.")
                        if d_mtime > last_mtime:
                            print(f"\n[{time.strftime('%H:%M:%S')}] 💾 Data change detected.")

                        # Give a tiny buffer for file write completion
                        time.sleep(0.1)
                        
                        if render_template(TEMPLATE_PATH, DATA_PATH, output_path):
                            reload_browser()
                            
                        last_mtime = current_max_mtime
                else:
                     print("Waiting for files to exist...", end='\r')

                time.sleep(1)
            except KeyboardInterrupt:
                print("\nStopping watcher.")
                break
            except Exception as e:
                print(f"Error in watcher loop: {e}")
                time.sleep(2)
    else:
        if render_template(TEMPLATE_PATH, DATA_PATH, output_path):
            reload_browser()

if __name__ == "__main__":
    main()
