"""
SDUI Tools Package
==================
Modular toolkit for SDUI contract development.

Modules:
- config: Constants, default paths, validation settings
- utils: JSON processing, file operations
- paths: Output path generation
- imports: Module and Jinja include resolution
- validators: Computed section validation
- renderer: Main template rendering pipeline

Usage:
    from sdui_tools import render_template, validate_sdui_contract
    
    # Render template
    success, watched = render_template(template, data, jj_full, map_out, full_out)
    
    # Validate contract
    result = validate_sdui_contract(json_content)
    if not result.is_valid:
        print(format_validation_report(result))
"""

from .config import VERSION, VALID_COMPUTED_TYPES, KNOWN_UI_COMPONENTS
from .utils import (
    json_finalize,
    remove_json_comments,
    resolve_include_path,
    get_max_mtime,
    safe_read_file,
    safe_write_file,
)
from .paths import (
    generate_output_paths,
    get_file_type_label,
    extract_platform_from_path,
)
from .imports import (
    parse_module_imports,
    resolve_jinja_includes,
)
from .validators import (
    ValidationIssue,
    ValidationResult,
    Severity,
    validate_sdui_contract,
    validate_computed_types,
    validate_computed_references,
    format_validation_report,
    validate_file,
)
from .renderer import render_template


__version__ = VERSION
__all__ = [
    # Config
    "VERSION",
    "VALID_COMPUTED_TYPES",
    "KNOWN_UI_COMPONENTS",
    # Utils
    "json_finalize",
    "remove_json_comments",
    "resolve_include_path",
    "get_max_mtime",
    "safe_read_file",
    "safe_write_file",
    # Paths
    "generate_output_paths",
    "get_file_type_label",
    "extract_platform_from_path",
    # Imports
    "parse_module_imports",
    "resolve_jinja_includes",
    # Validators
    "ValidationIssue",
    "ValidationResult",
    "Severity",
    "validate_sdui_contract",
    "validate_computed_types",
    "validate_computed_references",
    "format_validation_report",
    "validate_file",
    # Renderer
    "render_template",
]
