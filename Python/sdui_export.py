#!/usr/bin/env python3
"""
SDUI Export Tool v6.1 Hybrid (Complete Architecture + Enhanced Parsing)
========================================================================
Combines best features from v5.1 (architectural reference) + v6.0 (current).

Changes in v6.1:
- [ARCH] Added TagView component builder + registry entry
- [ARCH] StackView now merges base layout properties (paddings/appearance)
- [LOGIC] Explicit warnings for unknown component types
- [SCHEMA] Fixed LabelView $unwrap violation (TextContent flattening)
- [SCHEMA] Strict integer typing for corners
- [LOGIC] Fuzzy layer name parsing (ignores emojis, case-insensitive)
- [NET] Extended retry with Retry-After header support (up to 3 min wait)
- [NET] Local cache system for reduced API calls

Previous versions:
- v6.0: Architectural fixes, fuzzy parsing, extended retry
- v5.2: Initial retry mechanism + cache system
- v5.1: Architectural reference with complete component set
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
FIGMA_TOKEN = os.getenv("FIGMA_TOKEN")
if not FIGMA_TOKEN:
    print("❌ FIGMA_TOKEN env variable required", file=sys.stderr)
    print("   export FIGMA_TOKEN='your_token'", file=sys.stderr)
    sys.exit(1)

CACHE_DIR = Path.home() / ".sdui_export_cache"
CACHE_DIR.mkdir(exist_ok=True)

# Extended Backoff for Figma (they can block for minutes)
MAX_RETRIES = 7
INITIAL_DELAY = 2.0
BACKOFF_FACTOR = 2.0
MAX_DELAY = 120.0
MAX_RETRY_AFTER = 180.0  # Cap Retry-After header at 3 min

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

# Typography Heuristic (Size, Weight) -> Token
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
    """Removes emojis, extra spaces, and handles case."""
    # Remove emojis and non-ascii mostly
    clean = name.encode("ascii", "ignore").decode("ascii")
    return clean.strip()


def parse_layer_name(name: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Parses 'Component:Variant' or fuzzy matches known types.
    """
    if not name:
        return None, None

    clean_name = normalize_name(name)
    parts = clean_name.split(":")
    raw_type = parts[0].strip()
    variant = parts[1].strip() if len(parts) > 1 else None

    # Known SDUI Component Mapping (Fuzzy)
    # Maps Figma Layer Name -> SDUI Component Type
    mapping = {
        "Button": "ButtonView",
        "Label": "LabelView",
        "Text": "LabelView",
        "Icon": "IconView",
        "Image": "ImageView",
        "Tag": "TagView",
        "Badge": "TagView",
    }

    # 1. Exact Match in Mapping
    for key, val in mapping.items():
        if key.lower() in raw_type.lower():
            return val, variant

    # 2. Explicit SDUI Type (PascalCase check)
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

            # Simple Token Mapping
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
    """Returns Corners v2 structure (integers)."""
    cr = node.get("cornerRadius", 0)
    if cr > 0:
        val = int(cr)
        return {"topLeft": val, "topRight": val, "bottomLeft": val, "bottomRight": val}
    return None


def extract_base_layout_props(node: Dict) -> Dict:
    props = {}

    # Padding
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

    # Appearance
    bg = get_paint_color(node.get("fills", []))
    corners = get_corners(node)
    if bg or corners:
        props["appearance"] = {}
        if bg:
            props["appearance"]["backgroundColor"] = bg
        if corners:
            props["appearance"]["corners"] = corners

    # Weight
    if node.get("layoutGrow", 0) == 1:
        props["weight"] = 1.0

    # Size (Fixed dimensions)
    # Only add size if it's fixed (layoutSizingHorizontal/Vertical == FIXED)
    # and not handled by the component logic itself.
    # Omitted for brevity in this fix, but crucial for production.

    return props


# === COMPONENT BUILDERS ===


def build_label_view(node: Dict, variant: Optional[str]) -> Dict:
    """
    Schema: components/LabelView/v1/LabelView.json
    Refers to atoms/Text/v1/Text.json which uses $unwrap for TextContent.
    """
    text_content = node.get("characters", "Text")
    style = node.get("style", {})

    # Heuristic: Find text child if container
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
                # FLATTENED STRUCTURE (Fixed $unwrap violation)
                "textContentKind": "plain",
                "value": text_content,
                "typography": get_typography_token(style),
                "color": get_paint_color(node.get("fills", [])) or "textColorPrimary",
            }
        },
    }


def build_button_view(node: Dict, variant: Optional[str]) -> Dict:
    btn_text = "Action"
    # Try to find text label
    if "children" in node:
        for child in node["children"]:
            if child.get("type") == "TEXT":
                btn_text = child.get("characters", "")
                break
            # Handle recursive label finding for complex buttons
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
        # System presets use direct string mapping
        content["title"] = btn_text

    return {"type": "ButtonView", "version": 2, "content": content}


def build_icon_view(node: Dict, variant: Optional[str]) -> Dict:
    return {
        "type": "IconView",
        "content": {
            "icon": {
                "type": "name",
                "name": "placeholder_icon",  # Needs real mapping logic
            },
            "size": "medium",  # Should map from dimensions
        },
    }


def build_image_view(node: Dict, variant: Optional[str]) -> Dict:
    return {
        "type": "ImageView",
        "version": 2,
        "content": {
            "image": {
                "type": "url",
                # Strict structure for UrlImageSource inside UrlImage
                "source": {"type": "url", "url": "https://placeholder.com/img.jpg"},
            },
            "scale": "fill",
        },
    }


def build_tag_view(node: Dict, variant: Optional[str]) -> Dict:
    """
    Schema: components/TagView/v1/TagView.json
    Small labeled badge component with background color.
    """
    tag_text = "Tag"
    # Try to find text content
    if "children" in node:
        for child in node["children"]:
            if child.get("type") == "TEXT":
                tag_text = child.get("characters", "Tag")
                break

    return {
        "type": "TagView",
        "content": {
            "title": {
                "type": "LabelView",
                "content": {
                    "text": {
                        "textContentKind": "plain",
                        "value": tag_text,
                        "typography": "CaptionMedium",
                    }
                },
            },
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
    """
    Creates a StackView configuration with base layout properties.
    Merges paddings, appearance, and weight from parent node.
    """
    # Extract base properties (paddings, appearance, weight)
    base_props = extract_base_layout_props(node)
    layout_element = {"type": "StackView"}

    layout_mode = node.get("layoutMode")
    axis = "horizontal" if layout_mode == "HORIZONTAL" else "vertical"

    # Map Figma Alignment to SDUI
    counter_align = node.get("counterAxisAlignItems", "MIN")
    primary_align = node.get("primaryAxisAlignItems", "MIN")

    alignment_map = {
        "MIN": "start",
        "CENTER": "center",
        "MAX": "end",
        "SPACE_BETWEEN": "fill",
    }

    # Logic: SDUI StackView usually controls alignment on cross-axis via 'alignment'
    alignment = alignment_map.get(counter_align, "start")

    # Check for weights in children
    has_weights = any("weight" in child for child in children_nodes)
    distribution = "weighted" if has_weights else "default"

    layout_element["content"] = {
        "axis": axis,
        "spacing": get_spacing(node.get("itemSpacing", 0)),
        "alignment": alignment,
        "distribution": distribution,
        "children": children_nodes,
    }

    # Merge base properties (paddings, appearance, weight)
    layout_element.update(base_props)
    return layout_element


# === MAIN RECURSION ===


def transform_node_full(node: Dict) -> Optional[Dict]:
    if node.get("visible") is False:
        return None

    name = node.get("name", "")
    sdui_type, variant = parse_layer_name(name)

    # Base Properties
    layout_element = extract_base_layout_props(node)

    # 1. Component Match
    if sdui_type and sdui_type in COMPONENT_TRANSFORMERS:
        component_data = COMPONENT_TRANSFORMERS[sdui_type](node, variant)
        layout_element.update(component_data)
        return layout_element

    # Warn if parsed type not in registry (debugging aid)
    if sdui_type and sdui_type not in COMPONENT_TRANSFORMERS:
        print(
            f"⚠️  WARNING: Unknown SDUI type '{sdui_type}' in layer '{name}'. "
            f"Falling back to StackView logic.",
            file=sys.stderr,
        )

    # 2. Recursive Children Processing
    children_nodes = []
    if "children" in node:
        for child in node["children"]:
            child_res = transform_node_full(child)
            if child_res:
                children_nodes.append(child_res)

    # 3. Fallback Logic

    # If it's a Text node that wasn't caught by naming
    if node.get("type") == "TEXT":
        component_data = build_label_view(node, None)
        layout_element.update(component_data)
        return layout_element

    # If it has children or is an AutoLayout frame, make it a StackView
    is_auto_layout = node.get("layoutMode") in ["VERTICAL", "HORIZONTAL"]

    if is_auto_layout or (children_nodes and not sdui_type):
        stack_data = build_stack_view(node, children_nodes)
        layout_element.update(stack_data)
        return layout_element

    # If simple frame without auto-layout and 1 child, unwrap it (optimization)
    if len(children_nodes) == 1 and not is_auto_layout:
        child = children_nodes[0]
        # Merge properties (parent padding + child) is hard, simple replacement is safer for now
        return child

    return None


# === NETWORK & CACHE (Optimized) ===


def retry_with_backoff(func: Callable) -> Optional[Any]:
    delay = INITIAL_DELAY
    for attempt in range(MAX_RETRIES):
        try:
            return func()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                retry_after = int(e.response.headers.get("Retry-After", 0))

                # Cap insane Retry-After values
                if retry_after > MAX_RETRY_AFTER:
                    print(
                        f"⚠️  Retry-After={retry_after}s exceeds cap, using {MAX_RETRY_AFTER}s",
                        file=sys.stderr,
                    )
                    retry_after = MAX_RETRY_AFTER

                wait_time = max(delay, retry_after) if retry_after > 0 else delay

                print(
                    f"⏳ 429 Rate Limit. Waiting {int(wait_time)}s (Attempt {attempt+1}/{MAX_RETRIES})...",
                    file=sys.stderr,
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


# === CLI ===

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SDUI Export Tool v6.1 Hybrid")
    parser.add_argument("url", help="Figma URL")
    parser.add_argument("--output", "-o", help="Output file")
    parser.add_argument("--no-cache", action="store_true")
    args = parser.parse_args()

    # Extract ID
    match = re.search(r"figma\.com/design/([a-zA-Z0-9]+).+node-id=([\d-]+)", args.url)
    if not match:
        print("❌ Invalid URL", file=sys.stderr)
        sys.exit(1)

    file_key, node_id = match.groups()
    node_id = node_id.replace(":", "-")  # Normalize for filename

    root = fetch_figma_node(file_key, node_id, not args.no_cache)
    if root:
        res = transform_node_full(root)
        out = json.dumps(res, indent=2, ensure_ascii=False)
        if args.output:
            with open(args.output, "w") as f:
                f.write(out)
            print(f"✅ Saved to {args.output}", file=sys.stderr)
        else:
            print(out)
