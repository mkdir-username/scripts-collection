
# Добавлено автоматически для поддержки валидаторов после миграции
import sys
from pathlib import Path
validators_path = Path('/Users/username/Scripts/validators/current')
if validators_path not in sys.path:
    sys.path.insert(0, str(validators_path))

#!/usr/bin/env python3
"""
Byzantine Fault-Tolerant Validator for SDUI Contract
Performs comprehensive validation with consensus checks and malicious pattern detection
"""

import json
import os
from typing import Dict, List, Any, Tuple, Optional
from enum import Enum
from collections import defaultdict
import re
from datetime import datetime

class Severity(Enum):
    CRITICAL = "CRITICAL"  # Byzantine fault detected - production blocker
    HIGH = "HIGH"         # Major compatibility issue
    MEDIUM = "MEDIUM"     # Minor compatibility concern
    LOW = "LOW"          # Best practice violation
    INFO = "INFO"        # Informational notice

class ValidationResult:
    def __init__(self):
        self.issues: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []
        self.info: List[Dict[str, Any]] = []
        self.stats: Dict[str, Any] = {}
        self.passed: bool = True

    def add_issue(self, severity: Severity, category: str, message: str,
                  component_path: str = "", details: Dict = None):
        issue = {
            "severity": severity.value,
            "category": category,
            "message": message,
            "component_path": component_path,
            "details": details or {}
        }

        if severity in [Severity.CRITICAL, Severity.HIGH]:
            self.issues.append(issue)
            self.passed = False
        elif severity == Severity.MEDIUM:
            self.warnings.append(issue)
        else:
            self.info.append(issue)

class ByzantineValidator:
    """Byzantine fault-tolerant validator for SDUI contracts"""

    def __init__(self, contract_path: str, sdui_framework_path: str):
        self.contract_path = contract_path
        self.sdui_framework_path = sdui_framework_path
        self.result = ValidationResult()
        self.supported_components = set()
        self.supported_layouts = set()
        self._load_supported_components()

    def _load_supported_components(self):
        """Load list of supported SDUI components for WEB platform"""
        # Components verified from SDUI framework
        components_path = os.path.join(self.sdui_framework_path, "components")
        layouts_path = os.path.join(self.sdui_framework_path, "layouts")

        # Load component types
        if os.path.exists(components_path):
            for item in os.listdir(components_path):
                if os.path.isdir(os.path.join(components_path, item)):
                    self.supported_components.add(item)

        # Load layout types
        if os.path.exists(layouts_path):
            for item in os.listdir(layouts_path):
                if os.path.isdir(os.path.join(layouts_path, item)):
                    self.supported_layouts.add(item)

        # Add Constraint as ConstraintWrapper alias
        if "Constraint" in self.supported_layouts:
            self.supported_layouts.add("ConstraintWrapper")

    def validate(self) -> ValidationResult:
        """Main validation entry point"""
        print("=" * 80)
        print("BYZANTINE FAULT-TOLERANT VALIDATION SYSTEM")
        print("=" * 80)
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(f"Contract: {self.contract_path}")
        print(f"Framework: {self.sdui_framework_path}")
        print("-" * 80)

        # Load contract
        try:
            with open(self.contract_path, 'r', encoding='utf-8') as f:
                contract = json.load(f)
        except Exception as e:
            self.result.add_issue(
                Severity.CRITICAL,
                "CONTRACT_INTEGRITY",
                f"Failed to load contract: {str(e)}"
            )
            return self.result

        # Phase 1: Contract Integrity Check
        print("\n[PHASE 1] CONTRACT INTEGRITY CHECK")
        self._validate_contract_structure(contract)

        # Phase 2: Byzantine Fault Detection
        print("\n[PHASE 2] BYZANTINE FAULT DETECTION")
        self._detect_byzantine_faults(contract)

        # Phase 3: WEB Platform Compatibility
        print("\n[PHASE 3] WEB PLATFORM COMPATIBILITY")
        self._validate_web_compatibility(contract)

        # Phase 4: Production Readiness
        print("\n[PHASE 4] PRODUCTION READINESS")
        self._validate_production_readiness(contract)

        return self.result

    def _validate_contract_structure(self, contract: Dict):
        """Phase 1: Validate contract structural integrity"""

        # Check required fields
        if "metadata" not in contract:
            self.result.add_issue(
                Severity.CRITICAL,
                "STRUCTURE",
                "Missing required 'metadata' field"
            )
        else:
            metadata = contract["metadata"]
            required_metadata = ["version", "platform", "timestamp", "total_components"]
            for field in required_metadata:
                if field not in metadata:
                    self.result.add_issue(
                        Severity.HIGH,
                        "METADATA",
                        f"Missing required metadata field: {field}"
                    )

            # Verify platform is WEB
            if metadata.get("platform") != "WEB":
                self.result.add_issue(
                    Severity.CRITICAL,
                    "PLATFORM",
                    f"Invalid platform: {metadata.get('platform')}. Must be 'WEB'"
                )

            # Verify component count
            if "component_types" in metadata:
                actual_count = sum(metadata["component_types"].values())
                declared_count = metadata.get("total_components", 0)
                if actual_count != declared_count:
                    self.result.add_issue(
                        Severity.HIGH,
                        "INTEGRITY",
                        f"Component count mismatch: declared={declared_count}, actual={actual_count}"
                    )

        # Check screen structure
        if "screen" not in contract:
            self.result.add_issue(
                Severity.CRITICAL,
                "STRUCTURE",
                "Missing required 'screen' field"
            )

        print(f"  ✓ Structure validation complete: {len(self.result.issues)} critical issues")

    def _detect_byzantine_faults(self, contract: Dict):
        """Phase 2: Detect malicious or erroneous patterns"""

        def check_component(component: Dict, path: str = "root"):
            """Recursively check components for Byzantine faults"""

            # Check for injection attempts in URLs
            if isinstance(component, dict):
                for key, value in component.items():
                    if key in ["url", "deeplink"]:
                        if isinstance(value, str):
                            # Check for malicious patterns
                            malicious_patterns = [
                                r"javascript:",
                                r"data:text/html",
                                r"<script",
                                r"onclick=",
                                r"onerror=",
                                r"__VAR_",  # Unresolved variables
                                r"\$\{",    # Template injection
                            ]
                            for pattern in malicious_patterns:
                                if re.search(pattern, value, re.IGNORECASE):
                                    # Special case: __VAR_ might be legitimate placeholders
                                    if pattern == r"__VAR_":
                                        self.result.add_issue(
                                            Severity.MEDIUM,
                                            "UNRESOLVED_VARIABLE",
                                            f"Unresolved variable found: {value}",
                                            path
                                        )
                                    else:
                                        self.result.add_issue(
                                            Severity.CRITICAL,
                                            "BYZANTINE_FAULT",
                                            f"Potential injection attempt detected: {pattern} in {value}",
                                            path
                                        )

                    # Check for empty/invalid values where not allowed
                    if key in ["text", "value", "url"] and value == "":
                        # Empty URLs might be placeholders
                        severity = Severity.MEDIUM if key == "url" else Severity.LOW
                        self.result.add_issue(
                            severity,
                            "EMPTY_VALUE",
                            f"Empty {key} field detected",
                            path
                        )

                    # Recursive check
                    if isinstance(value, dict):
                        check_component(value, f"{path}.{key}")
                    elif isinstance(value, list):
                        for i, item in enumerate(value):
                            if isinstance(item, dict):
                                check_component(item, f"{path}.{key}[{i}]")

        if "screen" in contract:
            check_component(contract["screen"])

        # Check for duplicate components
        component_hashes = defaultdict(list)

        def hash_component(comp: Dict, path: str = ""):
            """Create hash of component for duplicate detection"""
            if isinstance(comp, dict) and "type" in comp:
                # Create a simple hash based on type and key properties
                comp_hash = f"{comp.get('type', '')}_{comp.get('tag', '')}_{comp.get('url', '')}"
                component_hashes[comp_hash].append(path)

                # Check nested components
                if "content" in comp:
                    if isinstance(comp["content"], list):
                        for i, item in enumerate(comp["content"]):
                            hash_component(item, f"{path}.content[{i}]")
                    elif isinstance(comp["content"], dict):
                        hash_component(comp["content"], f"{path}.content")

        if "screen" in contract:
            hash_component(contract["screen"], "screen")

        # Report suspicious duplicates
        for comp_hash, paths in component_hashes.items():
            if len(paths) > 5:  # Threshold for suspicious duplication
                self.result.add_issue(
                    Severity.MEDIUM,
                    "DUPLICATION",
                    f"Suspicious duplication detected: {len(paths)} instances of similar component",
                    ", ".join(paths[:3]) + "..."
                )

        print(f"  ✓ Byzantine fault detection complete: {len([i for i in self.result.issues if i['category'] == 'BYZANTINE_FAULT'])} faults detected")

    def _validate_web_compatibility(self, contract: Dict):
        """Phase 3: Validate WEB platform compatibility"""

        unsupported_components = set()
        android_specific_features = []

        def check_component_compatibility(component: Dict, path: str = ""):
            """Check if component is supported on WEB"""
            if isinstance(component, dict) and "type" in component:
                comp_type = component["type"]

                # Check if component is supported
                if comp_type not in self.supported_components and \
                   comp_type not in self.supported_layouts:
                    unsupported_components.add(comp_type)
                    self.result.add_issue(
                        Severity.HIGH,
                        "COMPATIBILITY",
                        f"Component type '{comp_type}' not found in WEB SDUI framework",
                        path
                    )

                # Check for Android-specific features
                if "action" in component:
                    action = component["action"]
                    if isinstance(action, dict):
                        # Check for Android intents
                        if action.get("type") == "intent":
                            android_specific_features.append((path, "Android intent action"))

                        # Check for Android-specific deeplinks
                        if "url" in action and isinstance(action["url"], str):
                            if action["url"].startswith("android://"):
                                android_specific_features.append((path, "Android-specific deeplink"))

                # Validate properties based on component type
                if comp_type == "ImageView":
                    self._validate_image_view(component, path)
                elif comp_type == "LabelView":
                    self._validate_label_view(component, path)
                elif comp_type == "ButtonView":
                    self._validate_button_view(component, path)

                # Recursive validation
                if "content" in component:
                    if isinstance(component["content"], list):
                        for i, item in enumerate(component["content"]):
                            check_component_compatibility(item, f"{path}.content[{i}]")
                    elif isinstance(component["content"], dict):
                        check_component_compatibility(component["content"], f"{path}.content")

        if "screen" in contract:
            check_component_compatibility(contract["screen"], "screen")

        # Report Android-specific features
        for path, feature in android_specific_features:
            self.result.add_issue(
                Severity.CRITICAL,
                "PLATFORM_SPECIFIC",
                f"Android-specific feature detected: {feature}",
                path
            )

        print(f"  ✓ WEB compatibility check complete: {len(unsupported_components)} unsupported components")

    def _validate_image_view(self, component: Dict, path: str):
        """Validate ImageView component"""
        if "content" in component:
            content = component["content"]
            if isinstance(content, dict):
                # Check image URL validity
                if "url" in content and content["url"]:
                    url = content["url"]
                    if not url.startswith(("http://", "https://", "//")):
                        self.result.add_issue(
                            Severity.MEDIUM,
                            "RESOURCE",
                            f"Invalid image URL format: {url}",
                            path
                        )

    def _validate_label_view(self, component: Dict, path: str):
        """Validate LabelView component"""
        if "content" in component:
            content = component["content"]
            if isinstance(content, dict) and "text" in content:
                text = content["text"]
                if isinstance(text, dict):
                    # Check typography values
                    if "typography" in text:
                        valid_typography = [
                            "HeadlineSmall", "HeadlineLarge",
                            "ActionComponent", "ActionPrimaryLarge",
                            "ActionSecondaryLarge", "ActionPrimarySmall",
                            "ActionSecondarySmall",
                            "ParagraphPrimarySmall", "ParagraphSecondaryMedium",
                            "ParagraphSecondaryLarge"
                        ]
                        if text["typography"] not in valid_typography:
                            self.result.add_issue(
                                Severity.MEDIUM,
                                "STYLE",
                                f"Unknown typography value: {text['typography']}",
                                path
                            )

    def _validate_button_view(self, component: Dict, path: str):
        """Validate ButtonView component"""
        # Check version compatibility
        if "version" in component:
            version = component["version"]
            if version not in [1, 2]:
                self.result.add_issue(
                    Severity.HIGH,
                    "VERSION",
                    f"Unsupported ButtonView version: {version}",
                    path
                )

    def _validate_production_readiness(self, contract: Dict):
        """Phase 4: Validate production readiness"""

        # Check all required fields are present
        empty_fields = []
        missing_resources = []

        def check_production_ready(component: Dict, path: str = ""):
            """Check if component is production ready"""
            if isinstance(component, dict):
                for key, value in component.items():
                    # Check for placeholder values
                    if isinstance(value, str):
                        if value.startswith("__VAR_") and value.endswith("__"):
                            empty_fields.append(f"{path}.{key}: {value}")
                        elif value == "" and key in ["url", "value", "text"]:
                            empty_fields.append(f"{path}.{key}: empty")

                    # Recursive check
                    if isinstance(value, dict):
                        check_production_ready(value, f"{path}.{key}")
                    elif isinstance(value, list):
                        for i, item in enumerate(value):
                            if isinstance(item, dict):
                                check_production_ready(item, f"{path}.{key}[{i}]")

        if "screen" in contract:
            check_production_ready(contract["screen"], "screen")

        # Report issues
        if empty_fields:
            for field in empty_fields[:10]:  # Limit output
                self.result.add_issue(
                    Severity.MEDIUM,
                    "INCOMPLETE",
                    f"Empty or placeholder field: {field}",
                    field
                )
            if len(empty_fields) > 10:
                self.result.add_issue(
                    Severity.MEDIUM,
                    "INCOMPLETE",
                    f"... and {len(empty_fields) - 10} more empty fields"
                )

        # Validate navigation and deeplinks
        deeplink_count = 0

        def count_deeplinks(component: Dict):
            nonlocal deeplink_count
            if isinstance(component, dict):
                if "action" in component and isinstance(component["action"], dict):
                    if "url" in component["action"]:
                        deeplink_count += 1
                for value in component.values():
                    if isinstance(value, dict):
                        count_deeplinks(value)
                    elif isinstance(value, list):
                        for item in value:
                            if isinstance(item, dict):
                                count_deeplinks(item)

        if "screen" in contract:
            count_deeplinks(contract["screen"])

        self.result.stats["deeplink_count"] = deeplink_count
        self.result.stats["empty_fields"] = len(empty_fields)
        self.result.stats["total_components"] = contract.get("metadata", {}).get("total_components", 0)

        print(f"  ✓ Production readiness check complete: {len(empty_fields)} incomplete fields")

    def generate_report(self) -> str:
        """Generate detailed validation report"""
        report = []
        report.append("=" * 80)
        report.append("BYZANTINE FAULT-TOLERANT VALIDATION REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append("")

        # Summary
        report.append("VALIDATION SUMMARY")
        report.append("-" * 40)
        report.append(f"Status: {'✅ PASSED' if self.result.passed else '❌ FAILED'}")
        report.append(f"Critical Issues: {len([i for i in self.result.issues if i['severity'] == 'CRITICAL'])}")
        report.append(f"High Issues: {len([i for i in self.result.issues if i['severity'] == 'HIGH'])}")
        report.append(f"Medium Issues: {len([i for i in self.result.issues if i['severity'] == 'MEDIUM'])}")
        report.append(f"Warnings: {len(self.result.warnings)}")
        report.append("")

        # Statistics
        if self.result.stats:
            report.append("STATISTICS")
            report.append("-" * 40)
            for key, value in self.result.stats.items():
                report.append(f"{key}: {value}")
            report.append("")

        # Critical Issues
        critical_issues = [i for i in self.result.issues if i["severity"] == "CRITICAL"]
        if critical_issues:
            report.append("CRITICAL ISSUES (Production Blockers)")
            report.append("-" * 40)
            for issue in critical_issues:
                report.append(f"❌ [{issue['category']}] {issue['message']}")
                if issue['component_path']:
                    report.append(f"   Location: {issue['component_path']}")
            report.append("")

        # High Priority Issues
        high_issues = [i for i in self.result.issues if i["severity"] == "HIGH"]
        if high_issues:
            report.append("HIGH PRIORITY ISSUES")
            report.append("-" * 40)
            for issue in high_issues[:10]:  # Limit output
                report.append(f"⚠️  [{issue['category']}] {issue['message']}")
                if issue['component_path']:
                    report.append(f"   Location: {issue['component_path']}")
            if len(high_issues) > 10:
                report.append(f"   ... and {len(high_issues) - 10} more")
            report.append("")

        # Medium Priority Issues
        medium_issues = [i for i in self.result.issues if i["severity"] == "MEDIUM"]
        if medium_issues:
            report.append("MEDIUM PRIORITY ISSUES")
            report.append("-" * 40)
            for issue in medium_issues[:5]:  # Limit output
                report.append(f"⚡ [{issue['category']}] {issue['message']}")
            if len(medium_issues) > 5:
                report.append(f"   ... and {len(medium_issues) - 5} more")
            report.append("")

        # Warnings
        if self.result.warnings:
            report.append("WARNINGS")
            report.append("-" * 40)
            # Group warnings by category
            warning_groups = defaultdict(list)
            for warning in self.result.warnings:
                warning_groups[warning['category']].append(warning)

            for category, warnings in warning_groups.items():
                report.append(f"[{category}] - {len(warnings)} issues:")
                for warning in warnings[:3]:
                    report.append(f"  • {warning['message']}")
                    if warning.get('component_path'):
                        report.append(f"    Location: {warning['component_path']}")
                if len(warnings) > 3:
                    report.append(f"  ... and {len(warnings) - 3} more")
            report.append("")

        # Recommendations
        report.append("RECOMMENDATIONS")
        report.append("-" * 40)

        if not self.result.passed:
            report.append("1. ❌ CRITICAL: Resolve all critical issues before production deployment")
            report.append("2. ⚠️  HIGH: Address high priority compatibility issues")

        if len(empty_fields := [i for i in self.result.issues if i["category"] == "INCOMPLETE"]) > 0:
            report.append("3. 📝 Complete all placeholder and empty fields")

        if len(unresoled_vars := [i for i in self.result.issues if "UNRESOLVED_VARIABLE" in i["category"]]) > 0:
            report.append("4. 🔧 Resolve all variable placeholders (__VAR_*__)")

        report.append("")

        # Final Verdict
        report.append("FINAL VERDICT")
        report.append("-" * 40)
        if self.result.passed:
            report.append("✅ Contract is READY for production deployment")
            report.append("   All Byzantine fault checks passed")
            report.append("   WEB platform compatibility verified")
        else:
            report.append("❌ Contract is NOT ready for production")
            report.append("   Critical issues must be resolved")
            report.append("   See recommendations above for remediation steps")

        report.append("=" * 80)

        return "\n".join(report)


def main():
    """Main entry point"""
    contract_path = "/Users/username/Documents/newclick-server-driven-ui/unified_contract.json"
    sdui_framework_path = "/Users/username/Documents/FMS_GIT/SDUI"

    validator = ByzantineValidator(contract_path, sdui_framework_path)
    result = validator.validate()

    report = validator.generate_report()
    print("\n" + report)

    # Save report to file
    report_path = "/Users/username/Documents/FMS_GIT/validation_report.txt"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\nReport saved to: {report_path}")

    # Return exit code based on validation result
    return 0 if result.passed else 1


if __name__ == "__main__":
    exit(main())