#!/usr/bin/env python3
"""
SDUI Export Tool v7.9.1 (Text Color Fix Edition)
========================================================================
Standard: Alpha Mobile SDUI Workflow

Changes from v7.9:
- [FIX] Text color detection - uses luminance-based logic instead of opacity
- [FIX] Proper textColorPrimary/Secondary/Tertiary based on text opacity
- [FIX] Background colors use separate logic from text colors

Changes from v7.8:
- [FIX] Deep text extraction - recursively finds TEXT nodes at any depth
- [FIX] MarkdownView extracts actual text instead of "Markdown content"
- [FIX] ButtonView extracts actual title instead of "Action"
- [FIX] LabelView extracts actual value instead of "Text"
- [FIX] Filename uses Moscow time (HH-MM-SS) instead of Unix timestamp
- [FIX] Button size detection for block-width buttons

Usage:
  python3 sdui_export.py <url> --token <token>
  python3 sdui_export.py <url> --schema-path /path/to/front-middle-schema/SDUI
  python3 sdui_export.py <url> --infer-wrappers --mode layout
"""

import requests
import json
import re
import argparse
import sys
import os
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple, Callable

# === CONFIGURATION & CONSTANTS ===
CACHE_DIR = Path.home() / ".sdui_export_cache"
DEFAULT_EXPORT_DIR = Path.home() / "Scripts/Python/SDUI-export"
DEFAULT_SCHEMA_PATH = Path.home() / "Documents/front-middle-schema/SDUI"

MAX_RETRIES = 7
INITIAL_DELAY = 2.0
BACKOFF_FACTOR = 2.0
MAX_DELAY = 120.0
MAX_RETRY_AFTER = 180.0

INFER_WRAPPERS = False
EXPORT_MODE = "full"
SCHEMA_PATH: Optional[Path] = None

# Moscow timezone (UTC+3)
MSK = timezone(timedelta(hours=3))

# Extended HEX → Token mapping for common Alfa colors
HEX_TO_TOKEN = {
    "#ffffff": "baseBgColorPrimary",
    "#fff": "baseBgColorPrimary",
    "#000000": "staticNeutralColor0",
    "#000": "staticNeutralColor0",
    "#ef3124": "brandColorPrimary",  # Alfa Red
    "#121213": "baseBgColorInverse",  # Dark BG
    "#f5f5f5": "baseBgColorSecondary",
    "#e5e5e5": "neutralLineColor",
    "#d2d3d9": "neutralLineColor",  # Divider color
    "#0cc44d": "successColor",  # Green success
    "#ff0000": "errorColor",
    "#dff8e5": "successBgColor",  # Green BG
    "#ffefd9": "warningBgColor",  # Orange/Warning BG
    "#f9ebfe": "infoBgColorAlt",  # Purple light BG
    "#eeedff": "infoBgColor",  # Blue light BG
}


class SchemaLoader:
    """Loads and caches SDUI schema definitions"""

    def __init__(self, schema_root: Optional[Path] = None):
        self.schema_root = schema_root
        self._spacing_map: Optional[Dict[int, str]] = None
        self._spacing_enum: Optional[List[str]] = None
        self._typography_enum: Optional[List[str]] = None
        self._loaded = False

    def load(self) -> bool:
        if self._loaded:
            return True

        if not self.schema_root or not self.schema_root.exists():
            print(f"⚠️  Schema path not found: {self.schema_root}", file=sys.stderr)
            print("   Using fallback hardcoded values", file=sys.stderr)
            self._use_fallback()
            return False

        try:
            self._load_spacing()
            self._load_typography()
            self._loaded = True
            print(f"✅ Loaded schemas from: {self.schema_root}", file=sys.stderr)
            return True
        except Exception as e:
            print(f"⚠️  Failed to load schemas: {e}", file=sys.stderr)
            self._use_fallback()
            return False

    def _load_spacing(self):
        spacing_path = self.schema_root / "atoms" / "Spacing" / "Spacing.json"
        if not spacing_path.exists():
            raise FileNotFoundError(f"Spacing.json not found at {spacing_path}")

        with open(spacing_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self._spacing_enum = data.get("enum", [])
        description = data.get("description", "")
        self._spacing_map = self._parse_spacing_description(description)

        if not self._spacing_map:
            self._spacing_map = {
                0: "zero",
                2: "xxxs",
                4: "xxs",
                6: "xs2xs",
                8: "xs",
                10: "xss",
                12: "s",
                16: "m",
                20: "l",
                24: "xl",
                32: "xxl",
                40: "xxxl",
                48: "xxxxl",
                64: "xxxxxl",
                72: "xxxxxxl",
            }

    def _parse_spacing_description(self, description: str) -> Dict[int, str]:
        result = {}
        pattern = r"(\w+)\s*-\s*(\d+)"
        matches = re.findall(pattern, description)

        for token, px_str in matches:
            try:
                px = int(px_str)
                token = token.strip().lower()
                if token not in result.values():
                    result[px] = token
            except ValueError:
                continue
        return result

    def _load_typography(self):
        typography_path = self.schema_root / "atoms" / "Typography" / "Typography.json"
        if not typography_path.exists():
            raise FileNotFoundError(f"Typography.json not found at {typography_path}")

        with open(typography_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self._typography_enum = data.get("enum", [])

    def _use_fallback(self):
        self._spacing_map = {
            0: "zero",
            2: "xxxs",
            4: "xxs",
            6: "xs2xs",
            8: "xs",
            10: "xss",
            12: "s",
            16: "m",
            20: "l",
            24: "xl",
            32: "xxl",
            40: "xxxl",
            48: "xxxxl",
            64: "xxxxxl",
            72: "xxxxxxl",
        }
        self._spacing_enum = list(set(self._spacing_map.values()))
        self._typography_enum = [
            "HeadlineXLarge",
            "HeadlineLarge",
            "HeadlineMedium",
            "HeadlineSmall",
            "HeadlineXSmall",
            "ParagraphPrimaryLarge",
            "ParagraphPrimaryMedium",
            "ParagraphPrimarySmall",
            "ActionPrimaryLarge",
            "ActionPrimaryMedium",
            "ActionPrimarySmall",
            "CaptionPrimaryMedium",
            "CaptionSecondaryMedium",
        ]
        self._loaded = True

    def get_spacing_token(self, px: float) -> str:
        if not self._loaded:
            self.load()
        if px is None or px == 0:
            return "zero"
        px_int = int(round(px))
        if px_int in self._spacing_map:
            return self._spacing_map[px_int]
        closest = min(self._spacing_map.keys(), key=lambda x: abs(x - px_int))
        return self._spacing_map[closest]

    def get_typography(self, size: int, weight: int) -> str:
        if not self._loaded:
            self.load()

        heuristics = {
            (48, 700): "HeadlineXLarge",
            (40, 700): "HeadlineLarge",
            (32, 700): "HeadlineMedium",
            (24, 700): "HeadlineSmall",
            (20, 600): "HeadlineXSmall",
            (20, 700): "HeadlineXSmall",
            (18, 500): "ParagraphPrimaryLarge",
            (16, 500): "ParagraphPrimaryMedium",
            (14, 500): "ParagraphPrimarySmall",
            (16, 400): "ParagraphPrimaryMedium",
            (14, 400): "ParagraphPrimarySmall",
            (18, 600): "ActionPrimaryLarge",
            (16, 600): "ActionPrimaryMedium",
            (14, 600): "ActionPrimarySmall",
            (12, 500): "CaptionPrimaryMedium",
            (12, 400): "CaptionSecondaryMedium",
        }

        if (size, weight) in heuristics:
            return heuristics[(size, weight)]

        fallback = {
            48: "HeadlineXLarge",
            40: "HeadlineLarge",
            32: "HeadlineMedium",
            24: "HeadlineSmall",
            20: "HeadlineXSmall",
            18: "ParagraphPrimaryLarge",
            16: "ParagraphPrimaryMedium",
            14: "ParagraphPrimarySmall",
            12: "CaptionPrimaryMedium",
        }
        closest = min(fallback.keys(), key=lambda x: abs(x - size))
        return fallback[closest]


SCHEMA = SchemaLoader()


# === TEXT EXTRACTION UTILITIES (v7.9 FIX) ===


def find_text_node_deep(node: Dict, max_depth: int = 10) -> Optional[Dict]:
    """
    Recursively find the first TEXT node in the tree.
    Returns the TEXT node dict or None.
    """
    if max_depth <= 0:
        return None

    if node.get("type") == "TEXT":
        return node

    for child in node.get("children", []):
        result = find_text_node_deep(child, max_depth - 1)
        if result:
            return result

    return None


def extract_all_text_deep(node: Dict, max_depth: int = 10) -> List[Tuple[str, Dict]]:
    """
    Recursively find all TEXT nodes and return list of (text, style) tuples.
    """
    results = []

    if max_depth <= 0:
        return results

    if node.get("type") == "TEXT":
        text = node.get("characters", "")
        style = node.get("style", {})
        if text.strip():
            results.append((text, style))

    for child in node.get("children", []):
        results.extend(extract_all_text_deep(child, max_depth - 1))

    return results


def extract_text_and_style(node: Dict) -> Tuple[str, Dict]:
    """
    Extract text and style from a node.
    First tries direct TEXT node, then searches recursively.
    Returns (text, style) tuple.
    """
    # If node itself is TEXT
    if node.get("type") == "TEXT":
        return node.get("characters", ""), node.get("style", {})

    # Search recursively
    text_node = find_text_node_deep(node)
    if text_node:
        return text_node.get("characters", ""), text_node.get("style", {})

    return "", {}


def extract_first_text(node: Dict) -> str:
    """
    Extract first text found in node tree.
    """
    text, _ = extract_text_and_style(node)
    return text


# === UTILITY FUNCTIONS ===


def normalize_name(name: str) -> str:
    if not name:
        return ""
    return name.encode("ascii", "ignore").decode("ascii").strip()


def sanitize_filename(name: str) -> str:
    clean = re.sub(r"[^\w\-\.]", "_", name)
    return re.sub(r"_{2,}", "_", clean).strip("_")


def sanitize_test_id(name: str) -> str:
    clean = re.sub(r"[^a-zA-Z0-9]", "_", normalize_name(name))
    return re.sub(r"_{2,}", "_", clean).strip("_").lower()


def make_clickable_path(path: Path) -> str:
    abs_path = path.resolve()
    return f"\033]8;;file://{abs_path}\033\\{abs_path}\033]8;;\033\\"


def get_msk_timestamp() -> str:
    """Get current time in Moscow as HH-MM-SS string"""
    now = datetime.now(MSK)
    return now.strftime("%H-%M-%S")


def get_paint_color(fills: List[Dict], is_text: bool = False) -> Optional[str]:
    """
    Extract color from fills, mapping HEX to tokens where possible.

    Args:
        fills: List of Figma fill objects
        is_text: If True, use text color tokens instead of background tokens
    """
    if not fills:
        return None
    for fill in fills:
        if fill.get("visible", True) and fill.get("type") == "SOLID":
            color = fill["color"]
            opacity = fill.get("opacity", 1.0)
            r, g, b = [int(c * 255) for c in [color["r"], color["g"], color["b"]]]
            hex_color = f"#{r:02x}{g:02x}{b:02x}"
            hex_lower = hex_color.lower()

            if is_text:
                # Text color logic - based on luminance and opacity
                luminance = 0.299 * r + 0.587 * g + 0.114 * b

                if luminance < 50:  # Dark text (black-ish)
                    if opacity < 0.5:
                        return "textColorTertiary"
                    elif opacity < 0.75:
                        return "textColorSecondary"
                    else:
                        return "textColorPrimary"
                elif luminance > 200:  # Light text (white-ish)
                    return "textColorInverse"
                elif hex_lower in ("#ef3124", "#ff0000"):  # Red
                    return "errorColor"
                elif hex_lower in ("#0cc44d", "#00ff00"):  # Green
                    return "successColor"
                else:
                    # Try token mapping for specific colors
                    if hex_lower in HEX_TO_TOKEN:
                        return HEX_TO_TOKEN[hex_lower]
                    return "textColorPrimary"
            else:
                # Background color logic
                if opacity < 0.5:
                    return "neutralTranslucentColor100"

                # Try to map HEX to token
                if hex_lower in HEX_TO_TOKEN:
                    return HEX_TO_TOKEN[hex_lower]

                # Return raw HEX if no token mapping
                return hex_color
    return None


def get_corners_v2(node: Dict) -> Optional[Dict[str, int]]:
    radii = node.get("rectangleCornerRadii")
    if radii:
        return {
            "topLeft": int(radii[0]),
            "topRight": int(radii[1]),
            "bottomRight": int(radii[2]),
            "bottomLeft": int(radii[3]),
        }
    cr = node.get("cornerRadius", 0)
    if cr > 0:
        val = int(cr)
        return {"topLeft": val, "topRight": val, "bottomLeft": val, "bottomRight": val}
    return None


def extract_base_layout_element_props(node: Dict) -> Dict:
    props = {}
    layer_name = node.get("name", "")
    if layer_name:
        test_id = sanitize_test_id(layer_name)
        if test_id:
            props["dataTestId"] = test_id

    p_top, p_btm = node.get("paddingTop", 0), node.get("paddingBottom", 0)
    p_left, p_right = node.get("paddingLeft", 0), node.get("paddingRight", 0)

    if any([p_top, p_btm, p_left, p_right]):
        props["paddings"] = {
            "top": SCHEMA.get_spacing_token(p_top),
            "bottom": SCHEMA.get_spacing_token(p_btm),
            "left": SCHEMA.get_spacing_token(p_left),
            "right": SCHEMA.get_spacing_token(p_right),
        }

    bg = get_paint_color(node.get("fills", []))
    corners = get_corners_v2(node)
    appearance = {}
    if bg:
        appearance["backgroundColor"] = bg
    if corners:
        appearance["corners"] = corners
    if appearance:
        props["appearance"] = appearance
    if node.get("layoutGrow", 0) == 1:
        props["weight"] = 1.0
    return props


def filter_for_mode(data: Dict, mode: str) -> Dict:
    if mode == "full":
        return data
    if mode == "layout":
        return filter_layout_mode(data)
    if mode == "skeleton":
        return filter_skeleton_mode(data)
    if mode == "names":
        return filter_names_mode(data)
    return data


def filter_layout_mode(data: Dict) -> Dict:
    if not isinstance(data, dict):
        return data
    result = {}
    for key in ["type", "dataTestId", "paddings", "size"]:
        if key in data:
            result[key] = data[key]
    if "content" in data and isinstance(data["content"], dict):
        fc = {}
        for key in ["axis", "alignment"]:
            if key in data["content"]:
                fc[key] = data["content"][key]
        if "children" in data["content"]:
            fc["children"] = [
                filter_layout_mode(c) for c in data["content"]["children"]
            ]
        if "content" in data["content"] and isinstance(
            data["content"]["content"], dict
        ):
            fc["content"] = filter_layout_mode(data["content"]["content"])
        if fc:
            result["content"] = fc
    return result


def filter_skeleton_mode(data: Dict) -> Dict:
    if not isinstance(data, dict):
        return data
    result = {}
    if "type" in data:
        result["type"] = data["type"]
    if "content" in data and isinstance(data["content"], dict):
        fc = {}
        if "children" in data["content"]:
            fc["children"] = [
                filter_skeleton_mode(c) for c in data["content"]["children"]
            ]
        if "content" in data["content"] and isinstance(
            data["content"]["content"], dict
        ):
            fc["content"] = filter_skeleton_mode(data["content"]["content"])
        if fc:
            result["content"] = fc
    return result


def filter_names_mode(data: Dict) -> Dict:
    if not isinstance(data, dict):
        return data
    result = {}
    for key in ["type", "dataTestId"]:
        if key in data:
            result[key] = data[key]
    if "content" in data and isinstance(data["content"], dict):
        fc = {}
        if "children" in data["content"]:
            fc["children"] = [filter_names_mode(c) for c in data["content"]["children"]]
        if "content" in data["content"] and isinstance(
            data["content"]["content"], dict
        ):
            fc["content"] = filter_names_mode(data["content"]["content"])
        if fc:
            result["content"] = fc
    return result


def infer_component_type(node: Dict) -> Optional[str]:
    name = node.get("name", "").lower()
    if "gapvertical" in name or "gaphorizontal" in name or "spacer" in name:
        return "Spacer"
    if "markdown" in name:
        return "MarkdownView"
    if INFER_WRAPPERS:
        if "bannerwrapper" in name:
            return "BannerWrapper"
        if "scrollwrapper" in name:
            return "ScrollWrapper"
        if "constraintwrapper" in name:
            return "ConstraintWrapper"
    return None


def get_spacer_axis_from_parent(node: Dict) -> str:
    """Determine spacer axis based on parent layout or dimensions"""
    bbox = node.get("absoluteBoundingBox", {})
    h, w = bbox.get("height", 0), bbox.get("width", 0)

    # If one dimension is significantly larger, infer axis
    if h > 0 and w > 0:
        if h > w * 3:  # Much taller than wide
            return "vertical"
        if w > h * 3:  # Much wider than tall
            return "horizontal"

    # Default based on layer name
    name = node.get("name", "").lower()
    if "horizontal" in name:
        return "horizontal"
    return "vertical"


def build_spacer(node: Dict) -> Dict:
    """Build Spacer with clean size - only relevant dimension"""
    el = {"type": "Spacer"}
    name = node.get("name", "")
    if name:
        tid = sanitize_test_id(name)
        if tid:
            el["dataTestId"] = tid

    bbox = node.get("absoluteBoundingBox", {})
    h, w = bbox.get("height", 0), bbox.get("width", 0)

    # Determine axis and include only relevant dimension
    axis = get_spacer_axis_from_parent(node)
    size = {}

    if axis == "vertical" and h > 0:
        size["height"] = int(h)
        # Only include width if it's a special case (e.g., fixed-width spacer)
        if w > 0 and w != h:
            # Check if width seems intentional (not just parent width)
            parent_name = name.lower()
            if (
                "fixed" in parent_name or w < 100
            ):  # Heuristic: small width is intentional
                size["width"] = int(w)
    elif axis == "horizontal" and w > 0:
        size["width"] = int(w)
    else:
        # Fallback: include both if we can't determine
        if h > 0:
            size["height"] = int(h)
        if w > 0:
            size["width"] = int(w)

    if size:
        el["size"] = size
    el["content"] = {}
    return el


def build_spacer_from_item_spacing(px: int, axis: str) -> Optional[Dict]:
    if px <= 0:
        return None
    spacer = {"type": "Spacer", "content": {}}
    spacer["size"] = {"height": px} if axis == "vertical" else {"width": px}
    return spacer


def build_markdown_view(node: Dict) -> Dict:
    """Build MarkdownView with deep text extraction (v7.9 fix)"""
    el = {"type": "MarkdownView"}
    el.update(extract_base_layout_element_props(node))

    # v7.9: Deep text extraction instead of shallow search
    text = extract_first_text(node)

    # If still empty, use layer name as hint (but not as fallback text)
    if not text:
        # Check if node itself has characters (shouldn't for FRAME, but just in case)
        text = node.get("characters", "")

    el["content"] = {"text": text if text else "[MISSING_TEXT]"}
    return el


def build_banner_wrapper(node: Dict, children: List[Dict]) -> Dict:
    el = {"type": "BannerWrapper"}
    el.update(extract_base_layout_element_props(node))
    inner = (
        children[0]
        if len(children) == 1
        else (
            build_stack_view(node, children)
            if children
            else {
                "type": "StackView",
                "content": {"axis": "vertical", "alignment": "fill", "children": []},
            }
        )
    )
    content = {"content": inner}
    bg = get_paint_color(node.get("fills", []))
    if bg:
        content["backgroundColor"] = bg
    el["content"] = content
    return el


def build_scroll_wrapper(node: Dict, children: List[Dict]) -> Dict:
    el = {"type": "ScrollWrapper"}
    el.update(extract_base_layout_element_props(node))
    axis = "horizontal" if node.get("layoutMode") == "HORIZONTAL" else "vertical"
    inner = (
        children[0]
        if len(children) == 1
        else (
            build_stack_view(node, children)
            if children
            else {
                "type": "StackView",
                "content": {"axis": axis, "alignment": "fill", "children": []},
            }
        )
    )
    el["content"] = {"axis": axis, "content": inner}
    return el


def build_constraint_wrapper(node: Dict, children: List[Dict]) -> Dict:
    """Build ConstraintWrapper with basic constraint support"""
    el = {"type": "ConstraintWrapper"}
    el.update(extract_base_layout_element_props(node))

    # Add constraints based on child positioning
    children_with_constraints = []
    for child in children:
        # For now, just pass children through
        # Future: detect absolute positioning and add constraints
        children_with_constraints.append(child)

    el["content"] = {"children": children_with_constraints}
    return el


class ComponentMapper:
    def map(self, node: Dict, variant: Optional[str]) -> Dict:
        raise NotImplementedError


class LabelViewMapper(ComponentMapper):
    def map(self, node: Dict, variant: Optional[str]) -> Dict:
        """Map LabelView with deep text extraction (v7.9 fix)"""
        # v7.9: Use deep extraction
        text, style = extract_text_and_style(node)

        # Fallback to node's own style if no TEXT found
        if not style:
            style = node.get("style", {})

        # Get color from the TEXT node with is_text=True for proper token mapping
        text_node = find_text_node_deep(node)
        color = None
        if text_node:
            color = get_paint_color(text_node.get("fills", []), is_text=True)
        if not color:
            color = get_paint_color(node.get("fills", []), is_text=True)

        size = int(style.get("fontSize", 16))
        weight = int(style.get("fontWeight", 400))

        return {
            "type": "LabelView",
            "content": {
                "text": {
                    "textContentKind": "plain",
                    "value": text if text else "[MISSING_TEXT]",
                    "typography": SCHEMA.get_typography(size, weight),
                    "color": color or "textColorPrimary",
                }
            },
        }


def detect_button_preset(node: Dict, variant: Optional[str]) -> str:
    """Detect button preset from layer name or variant"""
    # Check variant first (from explicit :variant syntax)
    if variant:
        v = variant.lower()
        if "secondary" in v:
            return "secondaryRectangleShape"
        if "transparent" in v or "ghost" in v:
            return "transparentRectangleShape"
        if "tertiary" in v:
            return "tertiaryRectangleShape"

    # Check full layer name
    name = node.get("name", "").lower()
    if "secondary" in name:
        return "secondaryRectangleShape"
    if "transparent" in name or "ghost" in name:
        return "transparentRectangleShape"
    if "tertiary" in name:
        return "tertiaryRectangleShape"

    return "primaryRectangleShape"


def detect_button_size_mode(node: Dict) -> Optional[str]:
    """Detect if button should be block-width based on layout properties"""
    # Check layoutSizingHorizontal
    if node.get("layoutSizingHorizontal") == "FILL":
        return "block"

    # Check layoutAlign
    if node.get("layoutAlign") == "STRETCH":
        return "block"

    # Check if width seems to fill parent (heuristic)
    bbox = node.get("absoluteBoundingBox", {})
    w = bbox.get("width", 0)
    if w >= 300:  # Likely block-width
        return "block"

    return None


class ButtonViewMapper(ComponentMapper):
    def map(self, node: Dict, variant: Optional[str]) -> Dict:
        """Map ButtonView with deep text extraction (v7.9 fix)"""
        # v7.9: Use deep extraction
        text = extract_first_text(node)

        if not text:
            text = "[MISSING_TITLE]"

        # Use improved preset detection
        preset = detect_button_preset(node, variant)

        content = {"preset": preset, "title": text}

        # v7.9: Detect block-width buttons
        size_mode = detect_button_size_mode(node)
        if size_mode:
            content["sizeMode"] = size_mode

        return {
            "type": "ButtonView",
            "version": 2,
            "content": content,
        }


class ImageViewMapper(ComponentMapper):
    def map(self, node: Dict, variant: Optional[str]) -> Dict:
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


class TagViewMapper(ComponentMapper):
    def map(self, node: Dict, variant: Optional[str]) -> Dict:
        """Map TagView with deep text extraction (v7.9 fix)"""
        # v7.9: Use deep extraction
        text = extract_first_text(node)
        if not text:
            text = "[MISSING_TAG]"

        # Get text color from TEXT node
        text_node = find_text_node_deep(node)
        text_color = None
        if text_node:
            text_color = get_paint_color(text_node.get("fills", []), is_text=True)

        return {
            "type": "TagView",
            "content": {
                "title": {
                    "text": {
                        "textContentKind": "plain",
                        "value": text,
                        "typography": "CaptionPrimaryMedium",
                        "color": text_color or "textColorPrimary",
                    }
                },
                "backgroundColor": get_paint_color(node.get("fills", []), is_text=False)
                or "neutralTranslucentColor100",
            },
        }


class IconViewMapper(ComponentMapper):
    def map(self, node: Dict, variant: Optional[str]) -> Dict:
        return {
            "type": "IconView",
            "content": {
                "icon": {"type": "name", "name": "placeholder_icon"},
                "size": "medium",
            },
        }


class RectangleViewMapper(ComponentMapper):
    def map(self, node: Dict, variant: Optional[str]) -> Dict:
        """Map rectangle - add height for divider lines"""
        bg = get_paint_color(node.get("fills", [])) or "baseBgColorPrimary"
        result = {"type": "RectangleView", "content": {"backgroundColor": bg}}

        # Check if this is a divider line (thin rectangle)
        bbox = node.get("absoluteBoundingBox", {})
        h = bbox.get("height", 0)
        w = bbox.get("width", 0)

        # If height is very small (1-2px), it's likely a divider
        if 0 < h <= 2 and w > h * 10:
            result["size"] = {"height": max(1, int(h))}

        return result


MAPPERS: Dict[str, ComponentMapper] = {
    "LabelView": LabelViewMapper(),
    "ButtonView": ButtonViewMapper(),
    "ImageView": ImageViewMapper(),
    "TagView": TagViewMapper(),
    "IconView": IconViewMapper(),
    "RectangleView": RectangleViewMapper(),
}


def parse_layer_name(name: str) -> Tuple[Optional[str], Optional[str]]:
    if not name:
        return None, None
    clean = normalize_name(name)
    parts = clean.split(":")
    raw = parts[0].strip()
    variant = parts[1].strip() if len(parts) > 1 else None
    mapping = {
        "Button": "ButtonView",
        "Label": "LabelView",
        "Text": "LabelView",
        "Icon": "IconView",
        "Image": "ImageView",
        "Tag": "TagView",
        "Rect": "RectangleView",
        "Rectangle": "RectangleView",
        "Stack": "StackView",
    }
    for k, v in mapping.items():
        if k.lower() in raw.lower():
            return v, variant
    if raw in MAPPERS:
        return raw, variant
    return None, None


def build_stack_view(node: Dict, children: List[Dict]) -> Dict:
    el = {"type": "StackView"}
    el.update(extract_base_layout_element_props(node))
    axis = "horizontal" if node.get("layoutMode") == "HORIZONTAL" else "vertical"
    align_map = {
        "MIN": "start",
        "CENTER": "center",
        "MAX": "end",
        "SPACE_BETWEEN": "fill",
    }
    alignment = align_map.get(node.get("counterAxisAlignItems", "MIN"), "start")

    spacing = node.get("itemSpacing", 0)
    final = []
    if spacing > 0 and len(children) > 1:
        for i, c in enumerate(children):
            final.append(c)
            if i < len(children) - 1:
                sp = build_spacer_from_item_spacing(int(spacing), axis)
                if sp:
                    final.append(sp)
    else:
        final = children

    has_weights = any("weight" in c for c in final)
    el["content"] = {
        "axis": axis,
        "alignment": alignment,
        "distribution": "weighted" if has_weights else "default",
        "children": final,
    }
    return el


def transform_node(node: Dict) -> Optional[Dict]:
    if node.get("visible") is False:
        return None

    inferred = infer_component_type(node)
    if inferred == "Spacer":
        return build_spacer(node)
    if inferred == "MarkdownView":
        return build_markdown_view(node)

    sdui_type, variant = parse_layer_name(node.get("name", ""))
    if sdui_type and sdui_type in MAPPERS:
        el = extract_base_layout_element_props(node)
        el.update(MAPPERS[sdui_type].map(node, variant))
        return el

    children = [r for c in node.get("children", []) if (r := transform_node(c))]

    if node.get("type") == "TEXT":
        el = extract_base_layout_element_props(node)
        el.update(MAPPERS["LabelView"].map(node, None))
        return el

    if node.get("type") == "RECTANGLE" and not children:
        el = extract_base_layout_element_props(node)
        el.update(MAPPERS["RectangleView"].map(node, None))
        return el

    if inferred == "BannerWrapper":
        return build_banner_wrapper(node, children)
    if inferred == "ScrollWrapper":
        return build_scroll_wrapper(node, children)
    if inferred == "ConstraintWrapper":
        return build_constraint_wrapper(node, children)

    if node.get("layoutMode") in ["VERTICAL", "HORIZONTAL"] or (
        children and not sdui_type
    ):
        return build_stack_view(node, children)

    if len(children) == 1:
        return children[0]
    return None


def retry_with_backoff(func: Callable) -> Optional[Any]:
    delay = INITIAL_DELAY
    for attempt in range(MAX_RETRIES):
        try:
            return func()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                retry = min(
                    int(e.response.headers.get("Retry-After", 0)), MAX_RETRY_AFTER
                )
                wait = max(delay, retry) if retry else delay
                print(
                    f"⏳ 429 Rate Limit. Waiting {int(wait)}s... ({attempt+1}/{MAX_RETRIES})",
                    file=sys.stderr,
                )
                time.sleep(wait)
                delay = min(delay * BACKOFF_FACTOR, MAX_DELAY)
            else:
                print(f"❌ HTTP Error {e.response.status_code}", file=sys.stderr)
                return None
        except Exception as e:
            print(f"❌ Network Error: {e}", file=sys.stderr)
            return None
    print(f"❌ Max retries ({MAX_RETRIES}) exceeded", file=sys.stderr)
    return None


def fetch_figma_node(
    file_key: str, node_id: str, token: str, use_cache: bool
) -> Optional[Dict]:
    CACHE_DIR.mkdir(exist_ok=True)
    cache = CACHE_DIR / f"{file_key}_{node_id}.json"
    if use_cache and cache.exists():
        print(f"📦 Loaded from cache: {cache.name}", file=sys.stderr)
        with open(cache) as f:
            return json.load(f)

    def req():
        url = f"https://api.figma.com/v1/files/{file_key}/nodes?ids={node_id.replace('-', '%3A')}"
        r = requests.get(url, headers={"X-Figma-Token": token})
        r.raise_for_status()
        return r.json()

    data = retry_with_backoff(req)
    if data:
        try:
            key = list(data["nodes"].keys())[0]
            node_data = data["nodes"][key]["document"]
            if use_cache:
                with open(cache, "w") as f:
                    json.dump(node_data, f, indent=2)
                print(f"💾 Cached to: {cache.name}", file=sys.stderr)
            return node_data
        except (KeyError, IndexError) as e:
            print(f"❌ Parse error: {e}", file=sys.stderr)
    return None


def generate_output_filename(name: str, infer: bool, mode: str) -> str:
    """Generate filename with Moscow time (v7.9 fix)"""
    base = sanitize_filename(name)
    time_str = get_msk_timestamp()
    suffixes = [time_str]
    if infer:
        suffixes.append("inferred")
    if mode != "full":
        suffixes.append(mode)
    return f"{base}_{'_'.join(suffixes)}.json"


def save_output(data: Dict, output_arg: Optional[str], figma_name: str) -> None:
    json_out = json.dumps(data, indent=2, ensure_ascii=False)

    if output_arg:
        p = Path(output_arg)
        if p.suffix.lower() == ".json":
            target_dir, filename = p.parent, p.name
        else:
            target_dir = p
            filename = generate_output_filename(figma_name, INFER_WRAPPERS, EXPORT_MODE)
    else:
        target_dir = DEFAULT_EXPORT_DIR
        filename = generate_output_filename(figma_name, INFER_WRAPPERS, EXPORT_MODE)

    try:
        target_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"❌ Failed to create dir: {e}", file=sys.stderr)
        sys.exit(1)

    final = target_dir / filename

    try:
        with open(final, "w") as f:
            f.write(json_out)
        print(f"✅ Saved to: {make_clickable_path(final)}", file=sys.stderr)
        if not sys.stdout.isatty():
            print(json_out)
    except Exception as e:
        print(f"❌ Write failed: {e}", file=sys.stderr)
        sys.exit(1)


def run():
    global INFER_WRAPPERS, EXPORT_MODE, SCHEMA

    parser = argparse.ArgumentParser(
        description="SDUI Export Tool v7.9.1 - Text Color Fix Edition",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Export Modes: full | layout | skeleton | names

Examples:
  python3 sdui_export.py <url> --token <token>
  python3 sdui_export.py <url> --schema-path ~/Documents/front-middle-schema/SDUI
  python3 sdui_export.py <url> --infer-wrappers --mode layout
""",
    )
    parser.add_argument("url", help="Figma URL with node-id")
    parser.add_argument("--token", "-t", help="Figma API Token")
    parser.add_argument("--output", "-o", help="Output file/directory")
    parser.add_argument("--no-cache", action="store_true")
    parser.add_argument("--infer-wrappers", action="store_true")
    parser.add_argument(
        "--mode", choices=["full", "layout", "skeleton", "names"], default="full"
    )
    parser.add_argument(
        "--schema-path",
        type=Path,
        default=DEFAULT_SCHEMA_PATH,
        help=f"SDUI schema dir (default: {DEFAULT_SCHEMA_PATH})",
    )
    args = parser.parse_args()

    INFER_WRAPPERS = args.infer_wrappers
    EXPORT_MODE = args.mode
    SCHEMA = SchemaLoader(args.schema_path)
    SCHEMA.load()

    if INFER_WRAPPERS:
        print("🔧 Wrapper inference enabled", file=sys.stderr)
    if EXPORT_MODE != "full":
        print(f"🔧 Export mode: {EXPORT_MODE}", file=sys.stderr)

    token = args.token or os.getenv("FIGMA_ACCESS_TOKEN") or os.getenv("FIGMA_TOKEN")
    if not token:
        print("❌ Figma Token not found.", file=sys.stderr)
        sys.exit(1)

    match = re.search(r"figma\.com/design/([a-zA-Z0-9]+).+node-id=([\d-]+)", args.url)
    if not match:
        print("❌ Invalid URL.", file=sys.stderr)
        sys.exit(1)

    file_key, node_id = match.groups()
    node_id = node_id.replace(":", "-")
    print(f"🔍 Fetching node {node_id}...", file=sys.stderr)

    root = fetch_figma_node(file_key, node_id, token, not args.no_cache)
    if root:
        print("🔄 Transforming...", file=sys.stderr)
        result = transform_node(root)
        if result:
            save_output(
                filter_for_mode(result, EXPORT_MODE),
                args.output,
                root.get("name", "export"),
            )
        else:
            print("❌ Empty output", file=sys.stderr)
            sys.exit(1)
    else:
        print("❌ Failed to fetch", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    run()
