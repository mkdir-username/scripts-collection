#!/usr/bin/env python3
"""
SDUI Export Tool v6.3 (Smart Versioning + Human-Readable Names)
========================================================================
Changes in v6.3:
- [FEAT] Smart File Naming: Uses Figma layer name for output filename
- [FEAT] Versioning: If content differs from existing file, creates a new timestamped file
- [LOGIC] Skips writing if content is identical to existing file
- [ARCH] Includes v6.2 fixes (TagView schema, directory auto-creation)

Previous versions:
- v6.2: Default paths, directory creation
- v6.1: Hybrid architecture
"""

import requests
import json
import re
import argparse
import sys
import os
import time
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple, Callable

# === CONFIGURATION ===
FIGMA_TOKEN = os.getenv("FIGMA_TOKEN", "***REMOVED***")
CACHE_DIR = Path.home() / ".sdui_export_cache"
CACHE_DIR.mkdir(exist_ok=True)

# DEFAULT OUTPUT CONFIGURATION
DEFAULT_EXPORT_DIR = Path.home() / "Scripts/Python/SDUI-export"

# Network Settings
MAX_RETRIES = 7
INITIAL_DELAY = 2.0
BACKOFF_FACTOR = 2.0
MAX_DELAY = 120.0
MAX_RETRY_AFTER = 180.0

# === CONSTANTS ===
SPACING_MAP = {
    0: "zero",
    2: "xxxs",
    4: "xxs",
    6: "xs",
    8: "s",
    10: "xss",
    12: "m",
    16: "l",
    20: "xl",
    24: "xxl",
    32: "xxl",
    40: "xxxl",
    48: "xxxxl",
    64: "xxxxxl",
}

TYPOGRAPHY_MAP = {
    (24, 700): "HeadlineSmall",
    (20, 600): "HeadlineXSmall",
    (16, 500): "ParagraphPrimaryMedium",
    (14, 400): "ParagraphPrimarySmall",
    (12, 400): "CaptionMedium",
}

# === HELPERS ===


def get_spacing(px: float) -> str:
    if px is None or px == 0:
        return "zero"
    closest = min(SPACING_MAP.keys(), key=lambda x: abs(x - px))
    return SPACING_MAP[closest]


def normalize_name(name: str) -> str:
    clean = name.encode("ascii", "ignore").decode("ascii")
    return clean.strip()


def sanitize_filename(name: str) -> str:
    """Converts Figma layer name to safe filename (e.g. 'Button / Primary' -> 'Button_Primary')"""
    # Replace separators and illegal chars with underscore
    clean = re.sub(r"[^\w\-\.]", "_", name)
    # Remove repeated underscores
    clean = re.sub(r"_{2,}", "_", clean)
    return clean.strip("_")


def parse_layer_name(name: str) -> Tuple[Optional[str], Optional[str]]:
    if not name:
        return None, None

    clean_name = normalize_name(name)
    parts = clean_name.split(":")
    raw_type = parts[0].strip()
    variant = parts[1].strip() if len(parts) > 1 else None

    mapping = {
        "Button": "ButtonView",
        "Label": "LabelView",
        "Text": "LabelView",
        "Icon": "IconView",
        "Image": "ImageView",
        "Tag": "TagView",
        "Badge": "TagView",
    }

    for key, val in mapping.items():
        if key.lower() in raw_type.lower():
            return val, variant

    if raw_type in COMPONENT_TRANSFORMERS:
        return raw_type, variant

    return None, None


def get_paint_color(fills: List[Dict]) -> Optional[str]:
    if not fills:
        return None
    for fill in fills:
        if fill.get("visible", True) and fill.get("type") == "SOLID":
            color = fill["color"]
            opacity = fill.get("opacity", 1.0)
            r, g, b = [int(c * 255) for c in [color["r"], color["g"], color["b"]]]
            hex_color = f"#{r:02x}{g:02x}{b:02x}"

            if opacity < 0.99:
                return "neutralTranslucentColor100"
            if hex_color.lower() in ["#ffffff", "#fff"]:
                return "baseBgColorPrimary"
            if hex_color.lower() in ["#000000", "#000"]:
                return "staticNeutralColor0"

            return hex_color
    return None


def get_typography_token(style: Dict) -> str:
    size = int(style.get("fontSize", 16))
    weight = int(style.get("fontWeight", 400))
    return TYPOGRAPHY_MAP.get((size, weight), "ParagraphPrimaryMedium")


def get_corners(node: Dict) -> Optional[Dict]:
    cr = node.get("cornerRadius", 0)
    if cr > 0:
        val = int(cr)
        return {"topLeft": val, "topRight": val, "bottomLeft": val, "bottomRight": val}
    return None


def extract_base_layout_props(node: Dict) -> Dict:
    props = {}
    p_top = node.get("paddingTop", 0)
    p_btm = node.get("paddingBottom", 0)
    p_left = node.get("paddingLeft", 0)
    p_right = node.get("paddingRight", 0)

    if any([p_top, p_btm, p_left, p_right]):
        props["paddings"] = {
            "top": get_spacing(p_top),
            "bottom": get_spacing(p_btm),
            "left": get_spacing(p_left),
            "right": get_spacing(p_right),
        }

    bg = get_paint_color(node.get("fills", []))
    corners = get_corners(node)
    if bg or corners:
        props["appearance"] = {}
        if bg:
            props["appearance"]["backgroundColor"] = bg
        if corners:
            props["appearance"]["corners"] = corners

    if node.get("layoutGrow", 0) == 1:
        props["weight"] = 1.0

    return props


# === COMPONENT BUILDERS ===


def build_label_view(node: Dict, variant: Optional[str]) -> Dict:
    text_content = node.get("characters", "Text")
    style = node.get("style", {})

    if "children" in node:
        for child in node["children"]:
            if child.get("type") == "TEXT":
                text_content = child.get("characters", "")
                style = child.get("style", {})
                break

    return {
        "type": "LabelView",
        "content": {
            "text": {
                "textContentKind": "plain",
                "value": text_content,
                "typography": get_typography_token(style),
                "color": get_paint_color(node.get("fills", [])) or "textColorPrimary",
            }
        },
    }


def build_button_view(node: Dict, variant: Optional[str]) -> Dict:
    btn_text = "Action"
    if "children" in node:
        for child in node["children"]:
            if child.get("type") == "TEXT":
                btn_text = child.get("characters", "")
                break
            if "children" in child:
                for sub in child["children"]:
                    if sub.get("type") == "TEXT":
                        btn_text = sub.get("characters", "")
                        break

    preset = "primaryRectangleShape"
    if variant:
        if "secondary" in variant.lower():
            preset = "secondaryRectangleShape"
        if "transparent" in variant.lower():
            preset = "transparentRectangleShape"
        if "custom" in variant.lower():
            preset = "custom"

    content = {"preset": preset}

    if preset == "custom":
        content["textLabels"] = {
            "title": {
                "type": "LabelView",
                "content": {
                    "text": {
                        "textContentKind": "plain",
                        "value": btn_text,
                        "typography": "ActionPrimaryMedium",
                    }
                },
            }
        }
    else:
        content["title"] = btn_text

    return {"type": "ButtonView", "version": 2, "content": content}


def build_icon_view(node: Dict, variant: Optional[str]) -> Dict:
    return {
        "type": "IconView",
        "content": {
            "icon": {
                "type": "name",
                "name": "placeholder_icon",
            },
            "size": "medium",
        },
    }


def build_image_view(node: Dict, variant: Optional[str]) -> Dict:
    return {
        "type": "ImageView",
        "version": 2,
        "content": {
            "image": {
                "type": "url",
                "source": {"type": "url", "url": "https://placeholder.com/img.jpg"},
            },
            "scale": "fill",
        },
    }


def build_tag_view(node: Dict, variant: Optional[str]) -> Dict:
    """
    Schema: components/TagView/v1/TagView.json
    FIXED: 'title' property requires a direct LabelView object structure.
    """
    tag_text = "Tag"
    if "children" in node:
        for child in node["children"]:
            if child.get("type") == "TEXT":
                tag_text = child.get("characters", "Tag")
                break

    label_view_object = {
        "text": {
            "textContentKind": "plain",
            "value": tag_text,
            "typography": "CaptionMedium",
            "color": "textColorPrimary",
        }
    }

    return {
        "type": "TagView",
        "content": {
            "title": label_view_object,
            "backgroundColor": get_paint_color(node.get("fills", []))
            or "neutralTranslucentColor100",
        },
    }


COMPONENT_TRANSFORMERS = {
    "LabelView": build_label_view,
    "ButtonView": build_button_view,
    "IconView": build_icon_view,
    "ImageView": build_image_view,
    "TagView": build_tag_view,
}

# === STACK BUILDER ===


def build_stack_view(node: Dict, children_nodes: List[Dict]) -> Dict:
    base_props = extract_base_layout_props(node)
    layout_element = {"type": "StackView"}

    layout_mode = node.get("layoutMode")
    axis = "horizontal" if layout_mode == "HORIZONTAL" else "vertical"

    counter_align = node.get("counterAxisAlignItems", "MIN")
    alignment_map = {
        "MIN": "start",
        "CENTER": "center",
        "MAX": "end",
        "SPACE_BETWEEN": "fill",
    }
    alignment = alignment_map.get(counter_align, "start")

    has_weights = any("weight" in child for child in children_nodes)
    distribution = "weighted" if has_weights else "default"

    layout_element["content"] = {
        "axis": axis,
        "spacing": get_spacing(node.get("itemSpacing", 0)),
        "alignment": alignment,
        "distribution": distribution,
        "children": children_nodes,
    }

    layout_element.update(base_props)
    return layout_element


# === MAIN RECURSION ===


def transform_node_full(node: Dict) -> Optional[Dict]:
    if node.get("visible") is False:
        return None

    name = node.get("name", "")
    sdui_type, variant = parse_layer_name(name)

    layout_element = extract_base_layout_props(node)

    if sdui_type and sdui_type in COMPONENT_TRANSFORMERS:
        component_data = COMPONENT_TRANSFORMERS[sdui_type](node, variant)
        layout_element.update(component_data)
        return layout_element

    children_nodes = []
    if "children" in node:
        for child in node["children"]:
            child_res = transform_node_full(child)
            if child_res:
                children_nodes.append(child_res)

    if node.get("type") == "TEXT":
        component_data = build_label_view(node, None)
        layout_element.update(component_data)
        return layout_element

    is_auto_layout = node.get("layoutMode") in ["VERTICAL", "HORIZONTAL"]

    if is_auto_layout or (children_nodes and not sdui_type):
        stack_data = build_stack_view(node, children_nodes)
        layout_element.update(stack_data)
        return layout_element

    if len(children_nodes) == 1 and not is_auto_layout:
        return children_nodes[0]

    return None


# === NETWORK & CACHE ===


def retry_with_backoff(func: Callable) -> Optional[Any]:
    delay = INITIAL_DELAY
    for attempt in range(MAX_RETRIES):
        try:
            return func()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                retry_after = int(e.response.headers.get("Retry-After", 0))
                if retry_after > MAX_RETRY_AFTER:
                    retry_after = MAX_RETRY_AFTER
                wait_time = max(delay, retry_after) if retry_after > 0 else delay
                print(
                    f"⏳ 429 Rate Limit. Waiting {int(wait_time)}s...", file=sys.stderr
                )
                time.sleep(wait_time)
                delay = min(delay * BACKOFF_FACTOR, MAX_DELAY)
            else:
                print(f"❌ HTTP Error {e.response.status_code}", file=sys.stderr)
                return None
        except Exception as e:
            print(f"❌ Network Error: {e}", file=sys.stderr)
            return None
    return None


def fetch_figma_node(file_key: str, node_id: str, use_cache: bool) -> Optional[Dict]:
    if not FIGMA_TOKEN:
        print("❌ FIGMA_TOKEN missing", file=sys.stderr)
        return None

    cache_path = CACHE_DIR / f"{file_key}_{node_id}.json"
    if use_cache and cache_path.exists():
        print(f"📦 Loaded from cache: {cache_path.name}", file=sys.stderr)
        with open(cache_path) as f:
            return json.load(f)

    def _req():
        url = f"https://api.figma.com/v1/files/{file_key}/nodes?ids={node_id.replace('-', '%3A')}"
        r = requests.get(url, headers={"X-Figma-Token": FIGMA_TOKEN})
        r.raise_for_status()
        return r.json()

    data = retry_with_backoff(_req)
    if data:
        try:
            key = list(data["nodes"].keys())[0]
            node_data = data["nodes"][key]["document"]
            if use_cache:
                with open(cache_path, "w") as f:
                    json.dump(node_data, f)
            return node_data
        except (KeyError, IndexError):
            print("❌ Error parsing Figma API response", file=sys.stderr)
    return None


# === CLI & OUTPUT LOGIC ===


def save_output(data: Dict, output_arg: Optional[str], figma_name: str) -> None:
    """
    Handles saving logic with intelligent versioning and naming.
    """
    json_output = json.dumps(data, indent=2, ensure_ascii=False)

    # Determine directory
    if output_arg:
        output_path_obj = Path(output_arg)
        # If user provided a specific file (ends in .json), use it but respect versioning logic check
        if output_path_obj.suffix.lower() == ".json":
            target_dir = output_path_obj.parent
            base_filename = output_path_obj.name
        else:
            target_dir = output_path_obj
            base_filename = f"{sanitize_filename(figma_name)}.json"
    else:
        target_dir = DEFAULT_EXPORT_DIR
        base_filename = f"{sanitize_filename(figma_name)}.json"

    # Ensure directory exists
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"❌ Failed to create directory {target_dir}: {e}", file=sys.stderr)
        sys.exit(1)

    final_path = target_dir / base_filename

    # Smart Versioning Logic
    if final_path.exists():
        try:
            with open(final_path, "r") as f:
                existing_content = f.read()

            # Normalize for comparison (load and dump to ensure formatting matches)
            # This handles cases where file might have different EOF whitespace
            try:
                if json.loads(existing_content) == data:
                    print(
                        f"✅ Content is identical to {final_path.name}. Skipping write.",
                        file=sys.stderr,
                    )
                    # Print to stdout if piped, for chaining
                    if not sys.stdout.isatty():
                        print(json_output)
                    return
            except json.JSONDecodeError:
                pass  # If existing file is corrupt, proceed to overwrite/version

            # Content is different, create versioned file
            print(f"⚠️  Content differs from {final_path.name}.", file=sys.stderr)
            timestamp = int(time.time())
            stem = final_path.stem
            final_path = target_dir / f"{stem}_v{timestamp}.json"

        except Exception as e:
            print(
                f"⚠️  Could not read existing file for comparison: {e}", file=sys.stderr
            )

    # Write file
    try:
        with open(final_path, "w") as f:
            f.write(json_output)
        print(f"✅ Saved to: {final_path}", file=sys.stderr)

        if not sys.stdout.isatty():
            print(json_output)

    except Exception as e:
        print(f"❌ Failed to write output file: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SDUI Export Tool v6.3")
    parser.add_argument("url", help="Figma URL")
    parser.add_argument("--output", "-o", help="Output file or directory")
    parser.add_argument("--no-cache", action="store_true")
    args = parser.parse_args()

    match = re.search(r"figma\.com/design/([a-zA-Z0-9]+).+node-id=([\d-]+)", args.url)
    if not match:
        print("❌ Invalid URL", file=sys.stderr)
        sys.exit(1)

    file_key, node_id = match.groups()
    node_id = node_id.replace(":", "-")

    root = fetch_figma_node(file_key, node_id, not args.no_cache)
    if root:
        res = transform_node_full(root)
        if res:
            # Extract name from root node for filename
            figma_layer_name = root.get("name", "export")
            save_output(res, args.output, figma_layer_name)
        else:
            print("❌ Transformation resulted in empty output", file=sys.stderr)
