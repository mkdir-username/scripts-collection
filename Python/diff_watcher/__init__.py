"""
Diff Watcher Module

Configuration module for file watching and template processing.
Provides monitoring capabilities for Jinja templates and value files.
"""

__version__ = "1.0.0"
__author__ = "Python Scripts Project"

from .constants.paths import (
    JSON_DIR,
    SALARY_LIST,
    PAYROLL,
    ENTRYPOINTS_MOCK,
    ENTRYPOINTS_GET_STEPS_UNSUBSCRIBED
)

__all__ = [
    "JSON_DIR",
    "SALARY_LIST",
    "PAYROLL",
    "ENTRYPOINTS_MOCK",
    "ENTRYPOINTS_GET_STEPS_UNSUBSCRIBED"
]