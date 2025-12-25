"""
SDUI Tools Configuration
========================
Константы, пути по умолчанию, настройки валидации.
"""

import os

# ==================== VERSION ====================
VERSION = "3.12.0"

# ==================== PROJECT ROOT ====================
# Use FMS_GIT_ROOT env var, or current working directory
PROJECT_ROOT = os.environ.get("FMS_GIT_ROOT", os.getcwd())

# ==================== DEFAULT PATHS ====================
_TEMPLATE_REL = "_JSON/WEB/payroll/1.0_main_screen/desktop/[JJ_PC]_1.0_main_screen_modular_web.java"
_DATA_REL = "_JSON/WEB/payroll/1.0_main_screen/[data]_1.0_main_screen.json"

DEFAULT_TEMPLATE_PATH = os.path.join(PROJECT_ROOT, _TEMPLATE_REL)
DEFAULT_DATA_PATH = os.path.join(PROJECT_ROOT, _DATA_REL)

# ==================== SDUI COMPUTED TYPES ====================
# Валидные типы для секции computed (функции, не UI-компоненты)
VALID_COMPUTED_TYPES = {
    "if",
    "switch",
    "applyTemplate",
    "map",
    "filter",
    "reduce",
    "find",
    "concat",
    "merge",
    "format",
    "join",
    "split",
    "slice",
    "sort",
    "reverse",
    "keys",
    "values",
    "entries",
    "fromEntries",
    "length",
    "toString",
    "toNumber",
    "toBoolean",
}

# UI-компоненты которые ТОЧНО не должны быть в computed
KNOWN_UI_COMPONENTS = {
    # Layouts
    "StackView",
    "ScrollWrapper",
    "ConstraintWrapper",
    "BannerWrapper",
    "CardWrapper",
    "LayoutElement",
    "GridView",
    # Components
    "LabelView",
    "ButtonView",
    "ImageView",
    "IconView",
    "TagView",
    "BadgeView",
    "DividerView",
    "Spacer",
    "InputView",
    "SwitchView",
    "CheckboxView",
    "RadioView",
    "SliderView",
    "ProgressView",
    "LoaderView",
    "WebView",
    "MapView",
    "ChartView",
    # Special
    "BottomSheet",
    "Modal",
    "Tooltip",
    "Snackbar",
}

# ==================== FILE EXTENSIONS ====================
TEMPLATE_EXTENSIONS = [".json.j2", ".j2.java", ".java", ".j2"]
