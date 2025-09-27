#!/usr/bin/env python3
"""
Real SDUI Test Data Collection
Contains actual SDUI schema patterns for realistic testing
"""

import json
from pathlib import Path
from typing import Dict, List, Any
import tempfile


class RealSDUITestData:
    """Collection of real SDUI schema patterns for testing"""

    @staticmethod
    def create_button_component() -> Dict:
        """Real Button component schema"""
        return {
            "name": "Button",
            "type": "object",
            "releaseVersion": {
                "ios": "1.0.0",
                "android": "1.0.0",
                "web": "released"
            },
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Button text"
                },
                "action": {
                    "$ref": "Action"
                },
                "style": {
                    "type": "object",
                    "properties": {
                        "backgroundColor": {"type": "string", "default": "#007AFF"},
                        "textColor": {"type": "string", "default": "#FFFFFF"},
                        "cornerRadius": {"type": "number", "default": 8},
                        "padding": {
                            "type": "object",
                            "properties": {
                                "horizontal": {"type": "number", "default": 16},
                                "vertical": {"type": "number", "default": 12}
                            }
                        }
                    }
                },
                "disabled": {
                    "type": "boolean",
                    "default": False
                },
                "loading": {
                    "type": "boolean",
                    "default": False
                }
            },
            "required": ["title", "action"]
        }

    @staticmethod
    def create_action_component() -> Dict:
        """Real Action component schema with various types"""
        return {
            "name": "Action",
            "type": "object",
            "releaseVersion": {
                "ios": "1.0.0",
                "android": "1.0.0",
                "web": "released"
            },
            "oneOf": [
                {
                    "type": "object",
                    "properties": {
                        "type": {"const": "navigate"},
                        "destination": {"type": "string"},
                        "params": {"type": "object"}
                    },
                    "required": ["type", "destination"]
                },
                {
                    "type": "object",
                    "properties": {
                        "type": {"const": "api_call"},
                        "endpoint": {"type": "string"},
                        "method": {"enum": ["GET", "POST", "PUT", "DELETE"]},
                        "body": {"type": "object"}
                    },
                    "required": ["type", "endpoint", "method"]
                },
                {
                    "type": "object",
                    "properties": {
                        "type": {"const": "open_url"},
                        "url": {"type": "string", "format": "uri"},
                        "inApp": {"type": "boolean", "default": True}
                    },
                    "required": ["type", "url"]
                },
                {
                    "type": "object",
                    "properties": {
                        "type": {"const": "show_modal"},
                        "modalId": {"type": "string"},
                        "data": {"type": "object"}
                    },
                    "required": ["type", "modalId"]
                }
            ]
        }

    @staticmethod
    def create_layout_element() -> Dict:
        """Real LayoutElement with recursive structure"""
        return {
            "name": "LayoutElement",
            "type": "object",
            "releaseVersion": {
                "ios": "1.0.0",
                "android": "1.0.0",
                "web": "released"
            },
            "properties": {
                "type": {
                    "type": "string",
                    "enum": ["vertical", "horizontal", "stack", "grid"]
                },
                "children": {
                    "type": "array",
                    "items": {
                        "oneOf": [
                            {"$ref": "LayoutElement"},
                            {"$ref": "LayoutElementContent"}
                        ]
                    }
                },
                "spacing": {
                    "type": "number",
                    "default": 8
                },
                "padding": {
                    "type": "object",
                    "properties": {
                        "top": {"type": "number", "default": 0},
                        "right": {"type": "number", "default": 0},
                        "bottom": {"type": "number", "default": 0},
                        "left": {"type": "number", "default": 0}
                    }
                },
                "alignment": {
                    "type": "string",
                    "enum": ["start", "center", "end", "stretch"],
                    "default": "start"
                },
                "distribution": {
                    "type": "string",
                    "enum": ["start", "center", "end", "space-between", "space-around", "space-evenly"],
                    "default": "start"
                }
            },
            "required": ["type", "children"]
        }

    @staticmethod
    def create_layout_element_content() -> Dict:
        """Real LayoutElementContent that can contain various components"""
        return {
            "name": "LayoutElementContent",
            "type": "object",
            "releaseVersion": {
                "ios": "1.0.0",
                "android": "1.0.0",
                "web": "released"
            },
            "oneOf": [
                {"$ref": "Button"},
                {"$ref": "Text"},
                {"$ref": "Image"},
                {"$ref": "Card"},
                {"$ref": "Input"},
                {"$ref": "List"},
                {"$ref": "LayoutElement"}
            ]
        }

    @staticmethod
    def create_text_component() -> Dict:
        """Real Text component schema"""
        return {
            "name": "Text",
            "type": "object",
            "releaseVersion": {
                "ios": "1.0.0",
                "android": "1.0.0",
                "web": "released"
            },
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Text content"
                },
                "style": {
                    "type": "object",
                    "properties": {
                        "fontSize": {"type": "number", "default": 16},
                        "fontWeight": {"enum": ["normal", "bold", "100", "200", "300", "400", "500", "600", "700", "800", "900"]},
                        "color": {"type": "string", "default": "#000000"},
                        "textAlign": {"enum": ["left", "center", "right", "justify"], "default": "left"},
                        "lineHeight": {"type": "number"},
                        "letterSpacing": {"type": "number"}
                    }
                },
                "numberOfLines": {
                    "type": "number",
                    "description": "Maximum number of lines to display"
                }
            },
            "required": ["text"]
        }

    @staticmethod
    def create_image_component() -> Dict:
        """Real Image component schema"""
        return {
            "name": "Image",
            "type": "object",
            "releaseVersion": {
                "ios": "1.0.0",
                "android": "1.0.0",
                "web": "released"
            },
            "properties": {
                "source": {
                    "oneOf": [
                        {
                            "type": "string",
                            "format": "uri"
                        },
                        {
                            "type": "object",
                            "properties": {
                                "uri": {"type": "string", "format": "uri"},
                                "headers": {"type": "object"}
                            },
                            "required": ["uri"]
                        }
                    ]
                },
                "alt": {
                    "type": "string",
                    "description": "Alternative text for accessibility"
                },
                "aspectRatio": {
                    "type": "number",
                    "description": "Width/Height ratio"
                },
                "resizeMode": {
                    "enum": ["cover", "contain", "stretch", "center"],
                    "default": "cover"
                },
                "style": {
                    "type": "object",
                    "properties": {
                        "width": {"type": "number"},
                        "height": {"type": "number"},
                        "borderRadius": {"type": "number"},
                        "opacity": {"type": "number", "minimum": 0, "maximum": 1}
                    }
                }
            },
            "required": ["source"]
        }

    @staticmethod
    def create_card_component() -> Dict:
        """Real Card component schema"""
        return {
            "name": "Card",
            "type": "object",
            "releaseVersion": {
                "ios": "1.0.0",
                "android": "1.0.0",
                "web": "released"
            },
            "properties": {
                "header": {
                    "$ref": "LayoutElementContent"
                },
                "content": {
                    "$ref": "LayoutElementContent"
                },
                "footer": {
                    "$ref": "LayoutElementContent"
                },
                "style": {
                    "type": "object",
                    "properties": {
                        "backgroundColor": {"type": "string", "default": "#FFFFFF"},
                        "borderRadius": {"type": "number", "default": 12},
                        "shadowColor": {"type": "string", "default": "#000000"},
                        "shadowOpacity": {"type": "number", "default": 0.1},
                        "shadowRadius": {"type": "number", "default": 4},
                        "borderWidth": {"type": "number", "default": 0},
                        "borderColor": {"type": "string"}
                    }
                },
                "onPress": {
                    "$ref": "Action"
                }
            }
        }

    @staticmethod
    def create_input_component() -> Dict:
        """Real Input component schema"""
        return {
            "name": "Input",
            "type": "object",
            "releaseVersion": {
                "ios": "1.0.0",
                "android": "1.0.0",
                "web": "released"
            },
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Field name for form submission"
                },
                "type": {
                    "enum": ["text", "email", "password", "number", "tel", "url", "search"],
                    "default": "text"
                },
                "placeholder": {
                    "type": "string"
                },
                "value": {
                    "type": "string"
                },
                "validation": {
                    "type": "object",
                    "properties": {
                        "required": {"type": "boolean"},
                        "minLength": {"type": "number"},
                        "maxLength": {"type": "number"},
                        "pattern": {"type": "string"},
                        "errorMessage": {"type": "string"}
                    }
                },
                "style": {
                    "type": "object",
                    "properties": {
                        "borderColor": {"type": "string", "default": "#CCCCCC"},
                        "borderRadius": {"type": "number", "default": 4},
                        "padding": {"type": "number", "default": 10},
                        "fontSize": {"type": "number", "default": 16}
                    }
                }
            },
            "required": ["name"]
        }

    @staticmethod
    def create_list_component() -> Dict:
        """Real List component schema"""
        return {
            "name": "List",
            "type": "object",
            "releaseVersion": {
                "ios": "1.0.0",
                "android": "1.0.0",
                "web": "released"
            },
            "properties": {
                "data": {
                    "type": "array",
                    "items": {"type": "object"}
                },
                "renderItem": {
                    "$ref": "LayoutElementContent"
                },
                "keyExtractor": {
                    "type": "string",
                    "description": "Property name to use as key"
                },
                "separator": {
                    "$ref": "LayoutElementContent"
                },
                "emptyState": {
                    "$ref": "LayoutElementContent"
                },
                "onEndReached": {
                    "$ref": "Action"
                },
                "refreshing": {
                    "type": "boolean"
                },
                "onRefresh": {
                    "$ref": "Action"
                }
            },
            "required": ["data", "renderItem"]
        }

    @staticmethod
    def create_salary_list_screen() -> Dict:
        """Real complex screen: Salary List"""
        return {
            "name": "SalaryListScreen",
            "type": "object",
            "releaseVersion": {
                "ios": "3.0.0",
                "android": "3.0.0",
                "web": "released"
            },
            "properties": {
                "header": {
                    "type": "object",
                    "properties": {
                        "title": {"$ref": "Text"},
                        "subtitle": {"$ref": "Text"},
                        "actions": {
                            "type": "array",
                            "items": {"$ref": "Button"}
                        }
                    }
                },
                "content": {
                    "$ref": "LayoutElement"
                },
                "salaryCards": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "month": {"type": "string"},
                            "amount": {"type": "number"},
                            "currency": {"type": "string"},
                            "status": {"enum": ["paid", "pending", "processing"]},
                            "details": {"$ref": "Card"},
                            "actions": {
                                "type": "array",
                                "items": {"$ref": "Button"}
                            }
                        }
                    }
                },
                "footer": {
                    "$ref": "LayoutElement"
                }
            }
        }

    @staticmethod
    def create_payroll_main_screen() -> Dict:
        """Real complex screen: Payroll Main"""
        return {
            "name": "PayrollMainScreen",
            "type": "object",
            "releaseVersion": {
                "ios": "1.0.0",
                "android": "1.0.0",
                "web": "released"
            },
            "properties": {
                "navigation": {
                    "type": "object",
                    "properties": {
                        "tabs": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "string"},
                                    "title": {"$ref": "Text"},
                                    "icon": {"$ref": "Image"},
                                    "badge": {"type": "number"},
                                    "screen": {"$ref": "#/definitions/Screen"}
                                }
                            }
                        }
                    }
                },
                "dashboard": {
                    "type": "object",
                    "properties": {
                        "summary": {"$ref": "Card"},
                        "charts": {
                            "type": "array",
                            "items": {"$ref": "#/definitions/Chart"}
                        },
                        "quickActions": {
                            "type": "array",
                            "items": {"$ref": "Button"}
                        }
                    }
                },
                "notifications": {
                    "type": "array",
                    "items": {"$ref": "Card"}
                }
            },
            "definitions": {
                "Screen": {
                    "oneOf": [
                        {"$ref": "SalaryListScreen"},
                        {"$ref": "#/definitions/EmployeeScreen"},
                        {"$ref": "#/definitions/ReportsScreen"}
                    ]
                },
                "Chart": {
                    "type": "object",
                    "properties": {
                        "type": {"enum": ["line", "bar", "pie", "donut"]},
                        "data": {"type": "array"},
                        "options": {"type": "object"}
                    }
                },
                "EmployeeScreen": {
                    "type": "object",
                    "properties": {
                        "list": {"$ref": "List"},
                        "filters": {"type": "array", "items": {"$ref": "Input"}}
                    }
                },
                "ReportsScreen": {
                    "type": "object",
                    "properties": {
                        "reports": {"type": "array", "items": {"$ref": "Card"}}
                    }
                }
            }
        }

    @staticmethod
    def create_modal_component() -> Dict:
        """Real Modal component with complex state"""
        return {
            "name": "Modal",
            "type": "object",
            "releaseVersion": {
                "ios": "2.0.0",
                "android": "2.0.0",
                "web": "released"
            },
            "properties": {
                "id": {"type": "string"},
                "visible": {"type": "boolean"},
                "type": {
                    "enum": ["alert", "confirm", "custom", "bottomSheet", "fullScreen"],
                    "default": "custom"
                },
                "title": {"$ref": "Text"},
                "content": {"$ref": "LayoutElement"},
                "actions": {
                    "type": "array",
                    "items": {"$ref": "Button"}
                },
                "onClose": {"$ref": "Action"},
                "backdrop": {
                    "type": "object",
                    "properties": {
                        "color": {"type": "string", "default": "rgba(0,0,0,0.5)"},
                        "dismissible": {"type": "boolean", "default": True}
                    }
                },
                "animation": {
                    "type": "object",
                    "properties": {
                        "type": {"enum": ["fade", "slide", "scale", "none"]},
                        "duration": {"type": "number", "default": 300}
                    }
                }
            }
        }


def create_test_environment(base_dir: Path) -> Dict[str, Path]:
    """Create complete test environment with all components"""
    data_factory = RealSDUITestData()
    created_files = {}

    # Create all component files
    components = [
        ("Button", data_factory.create_button_component()),
        ("Action", data_factory.create_action_component()),
        ("LayoutElement", data_factory.create_layout_element()),
        ("LayoutElementContent", data_factory.create_layout_element_content()),
        ("Text", data_factory.create_text_component()),
        ("Image", data_factory.create_image_component()),
        ("Card", data_factory.create_card_component()),
        ("Input", data_factory.create_input_component()),
        ("List", data_factory.create_list_component()),
        ("Modal", data_factory.create_modal_component()),
        ("SalaryListScreen", data_factory.create_salary_list_screen()),
        ("PayrollMainScreen", data_factory.create_payroll_main_screen())
    ]

    for name, schema in components:
        file_path = base_dir / f"{name}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(schema, f, ensure_ascii=False, indent=2)
        created_files[name] = file_path

    return created_files


def create_stress_test_schemas(base_dir: Path) -> Dict[str, Path]:
    """Create schemas for stress testing"""
    stress_schemas = {}

    # 1. Deep nesting stress test
    def create_deep_nested(depth: int) -> Dict:
        if depth == 0:
            return {"type": "string", "value": "leaf"}
        return {
            "type": "object",
            "properties": {
                "nested": create_deep_nested(depth - 1)
            }
        }

    deep_schema = {
        "name": "DeepNested",
        "root": create_deep_nested(100)
    }
    deep_path = base_dir / "stress_deep.json"
    with open(deep_path, 'w') as f:
        json.dump(deep_schema, f)
    stress_schemas["deep"] = deep_path

    # 2. Wide schema stress test
    wide_schema = {
        "name": "WideSchema",
        "properties": {
            f"property_{i}": {"type": "string", "default": f"value_{i}"}
            for i in range(1000)
        }
    }
    wide_path = base_dir / "stress_wide.json"
    with open(wide_path, 'w') as f:
        json.dump(wide_schema, f)
    stress_schemas["wide"] = wide_path

    # 3. Many references stress test
    ref_schema = {
        "name": "ManyRefs",
        "properties": {
            f"button_{i}": {"$ref": "Button"}
            for i in range(500)
        }
    }
    ref_path = base_dir / "stress_refs.json"
    with open(ref_path, 'w') as f:
        json.dump(ref_schema, f)
    stress_schemas["refs"] = ref_path

    return stress_schemas


def create_invalid_schemas(base_dir: Path) -> Dict[str, Path]:
    """Create invalid schemas for error testing"""
    invalid_schemas = {}

    # 1. Circular reference
    circular_a = {
        "name": "CircularA",
        "properties": {"b": {"$ref": "CircularB"}}
    }
    circular_b = {
        "name": "CircularB",
        "properties": {"a": {"$ref": "CircularA"}}
    }

    circular_a_path = base_dir / "CircularA.json"
    circular_b_path = base_dir / "CircularB.json"

    with open(circular_a_path, 'w') as f:
        json.dump(circular_a, f)
    with open(circular_b_path, 'w') as f:
        json.dump(circular_b, f)

    invalid_schemas["circular_a"] = circular_a_path
    invalid_schemas["circular_b"] = circular_b_path

    # 2. Missing reference
    missing_ref = {
        "name": "MissingRef",
        "properties": {"nonexistent": {"$ref": "NonExistentComponent"}}
    }
    missing_path = base_dir / "missing_ref.json"
    with open(missing_path, 'w') as f:
        json.dump(missing_ref, f)
    invalid_schemas["missing_ref"] = missing_path

    # 3. Invalid JSON reference format
    invalid_ref = {
        "name": "InvalidRef",
        "properties": {
            "bad1": {"$ref": "///invalid///"},
            "bad2": {"$ref": ""},
            "bad3": {"$ref": None}
        }
    }
    invalid_path = base_dir / "invalid_ref.json"
    with open(invalid_path, 'w') as f:
        json.dump(invalid_ref, f)
    invalid_schemas["invalid_ref"] = invalid_path

    return invalid_schemas


if __name__ == "__main__":
    # Create temporary directory for test data
    test_dir = Path(tempfile.mkdtemp(prefix="sdui_test_data_"))

    print(f"Creating test data in: {test_dir}")

    # Create all test environments
    components = create_test_environment(test_dir)
    stress_tests = create_stress_test_schemas(test_dir)
    invalid_tests = create_invalid_schemas(test_dir)

    print(f"\nCreated {len(components)} component schemas")
    print(f"Created {len(stress_tests)} stress test schemas")
    print(f"Created {len(invalid_tests)} invalid test schemas")

    print(f"\nTotal test files created: {len(components) + len(stress_tests) + len(invalid_tests)}")
    print(f"\nTest data directory: {test_dir}")