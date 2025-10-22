#!/usr/bin/env python3
"""
Breaking Change Detector
Detects breaking changes in SDUI schema modifications
"""

import json
import sys
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Set
from dataclasses import dataclass
from enum import Enum


class ChangeType(Enum):
    BREAKING = "breaking"
    NON_BREAKING = "non_breaking"
    COMPATIBLE = "compatible"


@dataclass
class SchemaChange:
    change_type: ChangeType
    severity: str  # 'critical', 'major', 'minor'
    field_path: str
    old_value: Any
    new_value: Any
    description: str
    impact: str
    migration_guide: Optional[str] = None


class BreakingChangeDetector:
    """Detects breaking changes in SDUI schema modifications"""

    def __init__(self):
        self.breaking_change_rules = self._initialize_breaking_change_rules()
        self.compatibility_matrix = self._initialize_compatibility_matrix()

    def _initialize_breaking_change_rules(self) -> Dict:
        """Initialize rules for detecting breaking changes"""
        return {
            'field_removal': {
                'breaking': True,
                'severity': 'critical',
                'description': 'Field removal breaks existing implementations'
            },
            'type_change': {
                'breaking': True,
                'severity': 'critical',
                'description': 'Type changes break compatibility'
            },
            'required_field_addition': {
                'breaking': True,
                'severity': 'major',
                'description': 'Adding required fields breaks existing contracts'
            },
            'enum_value_removal': {
                'breaking': True,
                'severity': 'major',
                'description': 'Removing enum values breaks existing usage'
            },
            'property_constraint_tightening': {
                'breaking': True,
                'severity': 'major',
                'description': 'Tightening constraints may invalidate existing data'
            },
            'component_deprecation': {
                'breaking': False,
                'severity': 'minor',
                'description': 'Component deprecation with migration path'
            },
            'optional_field_addition': {
                'breaking': False,
                'severity': 'minor',
                'description': 'Adding optional fields is backward compatible'
            },
            'enum_value_addition': {
                'breaking': False,
                'severity': 'minor',
                'description': 'Adding enum values maintains compatibility'
            }
        }

    def _initialize_compatibility_matrix(self) -> Dict:
        """Initialize platform compatibility matrix"""
        return {
            'web': {
                'supported_components': [
                    'ButtonView', 'TextView', 'ImageView', 'IconView',
                    'DataView', 'DataStackView', 'CustomView', 'Spacer',
                    'ProgressBarView', 'AlertView', 'MarkdownView'
                ],
                'forbidden_components': [
                    'LabelView', 'EditText', 'LinearLayout', 'ScrollView'
                ]
            },
            'android': {
                'supported_components': 'all',
                'forbidden_components': []
            },
            'ios': {
                'supported_components': [
                    'ButtonView', 'TextView', 'ImageView', 'IconView',
                    'DataView', 'DataStackView', 'CustomView', 'Spacer'
                ],
                'forbidden_components': []
            }
        }

    def detect_changes(self, old_schema_path: str, new_schema_path: str) -> List[SchemaChange]:
        """Detect changes between two schema versions"""
        try:
            with open(old_schema_path, 'r', encoding='utf-8') as f:
                old_schema = json.load(f)
            with open(new_schema_path, 'r', encoding='utf-8') as f:
                new_schema = json.load(f)
        except Exception as e:
            raise Exception(f"Failed to load schemas: {e}")

        changes = []
        self._compare_schemas(old_schema, new_schema, "", changes)
        return self._categorize_and_prioritize_changes(changes)

    def detect_git_changes(self, file_path: str, base_branch: str = "master") -> List[SchemaChange]:
        """Detect changes using git diff"""
        try:
            # Get the file content from base branch
            cmd = ["git", "show", f"{base_branch}:{file_path}"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            old_content = result.stdout

            # Get current file content
            with open(file_path, 'r', encoding='utf-8') as f:
                new_content = f.read()

            # Parse JSON
            old_schema = json.loads(old_content)
            new_schema = json.loads(new_content)

            changes = []
            self._compare_schemas(old_schema, new_schema, "", changes)
            return self._categorize_and_prioritize_changes(changes)

        except subprocess.CalledProcessError:
            # File doesn't exist in base branch - it's a new file
            return self._analyze_new_file(file_path)
        except Exception as e:
            raise Exception(f"Failed to analyze git changes: {e}")

    def _compare_schemas(self, old: Any, new: Any, path: str, changes: List[SchemaChange]):
        """Recursively compare schema structures"""

        if type(old) != type(new):
            changes.append(SchemaChange(
                change_type=ChangeType.BREAKING,
                severity='critical',
                field_path=path,
                old_value=old,
                new_value=new,
                description=f"Type changed from {type(old).__name__} to {type(new).__name__}",
                impact="Breaking change: type compatibility lost"
            ))
            return

        if isinstance(old, dict) and isinstance(new, dict):
            # Check for removed fields
            for key in old:
                if key not in new:
                    severity = self._determine_removal_severity(key, old[key], path)
                    changes.append(SchemaChange(
                        change_type=ChangeType.BREAKING,
                        severity=severity,
                        field_path=f"{path}.{key}" if path else key,
                        old_value=old[key],
                        new_value=None,
                        description=f"Field '{key}' removed",
                        impact=f"Breaking change: field no longer available",
                        migration_guide=self._generate_removal_migration(key, old[key])
                    ))

            # Check for added fields
            for key in new:
                if key not in old:
                    is_breaking = self._is_field_addition_breaking(key, new[key], new)
                    severity = 'major' if is_breaking else 'minor'
                    change_type = ChangeType.BREAKING if is_breaking else ChangeType.COMPATIBLE
                    changes.append(SchemaChange(
                        change_type=change_type,
                        severity=severity,
                        field_path=f"{path}.{key}" if path else key,
                        old_value=None,
                        new_value=new[key],
                        description=f"Field '{key}' added",
                        impact="Required field addition" if is_breaking else "Optional field addition"
                    ))

            # Check for modified fields
            for key in old:
                if key in new:
                    new_path = f"{path}.{key}" if path else key
                    self._compare_schemas(old[key], new[key], new_path, changes)

        elif isinstance(old, list) and isinstance(new, list):
            # Compare array contents
            if len(old) != len(new):
                changes.append(SchemaChange(
                    change_type=ChangeType.NON_BREAKING,
                    severity='minor',
                    field_path=path,
                    old_value=len(old),
                    new_value=len(new),
                    description=f"Array length changed from {len(old)} to {len(new)}",
                    impact="Array size change"
                ))

            # Compare common elements
            for i in range(min(len(old), len(new))):
                self._compare_schemas(old[i], new[i], f"{path}[{i}]", changes)

        elif old != new:
            # Value change
            severity = self._determine_value_change_severity(path, old, new)
            change_type = ChangeType.BREAKING if severity in ['critical', 'major'] else ChangeType.NON_BREAKING
            changes.append(SchemaChange(
                change_type=change_type,
                severity=severity,
                field_path=path,
                old_value=old,
                new_value=new,
                description=f"Value changed from '{old}' to '{new}'",
                impact=self._analyze_value_change_impact(path, old, new)
            ))

    def _determine_removal_severity(self, field_name: str, field_value: Any, path: str) -> str:
        """Determine severity of field removal"""
        critical_fields = ['type', 'releaseVersion', 'version']
        major_fields = ['accessibility', 'text', 'src', 'name']

        if field_name in critical_fields:
            return 'critical'
        elif field_name in major_fields:
            return 'major'
        else:
            return 'minor'

    def _is_field_addition_breaking(self, field_name: str, field_value: Any, parent: Dict) -> bool:
        """Check if field addition is breaking"""
        # Check if it's marked as required
        if isinstance(parent, dict):
            required_fields = parent.get('required', [])
            if field_name in required_fields:
                return True

        # Check critical field patterns
        critical_patterns = ['required', 'mandatory', 'must']
        return any(pattern in field_name.lower() for pattern in critical_patterns)

    def _determine_value_change_severity(self, path: str, old_value: Any, new_value: Any) -> str:
        """Determine severity of value change"""
        # Component type changes are critical
        if 'type' in path:
            return 'critical'

        # Release version changes
        if 'releaseVersion' in path:
            if old_value == 'released' and new_value != 'released':
                return 'major'
            elif new_value == 'released' and old_value != 'released':
                return 'minor'

        # Version changes
        if 'version' in path:
            return 'major'

        return 'minor'

    def _analyze_value_change_impact(self, path: str, old_value: Any, new_value: Any) -> str:
        """Analyze impact of value changes"""
        if 'type' in path:
            return f"Component type change affects rendering and behavior"
        elif 'releaseVersion' in path:
            return f"Release status change affects availability"
        elif 'version' in path:
            return f"Version change may affect compatibility"
        else:
            return f"Value change may affect behavior"

    def _generate_removal_migration(self, field_name: str, field_value: Any) -> Optional[str]:
        """Generate migration guide for removed fields"""
        migration_guides = {
            'text': "Use 'content' or 'label' field instead",
            'src': "Use 'source' or 'url' field instead",
            'color': "Use theme-based styling instead",
            'size': "Use responsive sizing units"
        }
        return migration_guides.get(field_name)

    def _categorize_and_prioritize_changes(self, changes: List[SchemaChange]) -> List[SchemaChange]:
        """Categorize and prioritize changes"""
        # Sort by severity and type
        severity_order = {'critical': 0, 'major': 1, 'minor': 2}
        type_order = {ChangeType.BREAKING: 0, ChangeType.NON_BREAKING: 1, ChangeType.COMPATIBLE: 2}

        return sorted(changes, key=lambda c: (
            severity_order.get(c.severity, 3),
            type_order.get(c.change_type, 3)
        ))

    def _analyze_new_file(self, file_path: str) -> List[SchemaChange]:
        """Analyze new file for potential issues"""
        changes = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                schema = json.load(f)

            # Check for web compatibility
            self._check_new_file_web_compatibility(schema, file_path, changes)

            # Check for version requirements
            self._check_new_file_versions(schema, file_path, changes)

        except Exception as e:
            changes.append(SchemaChange(
                change_type=ChangeType.BREAKING,
                severity='critical',
                field_path=file_path,
                old_value=None,
                new_value=None,
                description=f"New file has validation errors: {e}",
                impact="File cannot be processed"
            ))

        return changes

    def _check_new_file_web_compatibility(self, schema: Dict, file_path: str, changes: List[SchemaChange]):
        """Check web compatibility for new files"""
        component_type = schema.get('type')
        web_forbidden = self.compatibility_matrix['web']['forbidden_components']

        if component_type in web_forbidden:
            changes.append(SchemaChange(
                change_type=ChangeType.BREAKING,
                severity='major',
                field_path='type',
                old_value=None,
                new_value=component_type,
                description=f"New component '{component_type}' not compatible with web platform",
                impact="Web platform compatibility broken",
                migration_guide=f"Consider using web-compatible alternative"
            ))

    def _check_new_file_versions(self, schema: Dict, file_path: str, changes: List[SchemaChange]):
        """Check version requirements for new files"""
        release_version = schema.get('releaseVersion', {})

        if 'web' not in release_version:
            changes.append(SchemaChange(
                change_type=ChangeType.BREAKING,
                severity='major',
                field_path='releaseVersion.web',
                old_value=None,
                new_value=None,
                description="New component missing web release version",
                impact="Web compatibility unknown",
                migration_guide="Add releaseVersion.web field"
            ))

    def analyze_platform_impact(self, changes: List[SchemaChange]) -> Dict[str, List[str]]:
        """Analyze impact on different platforms"""
        impact = {
            'web': [],
            'android': [],
            'ios': []
        }

        for change in changes:
            if change.change_type == ChangeType.BREAKING:
                # Analyze which platforms are affected
                if 'type' in change.field_path and change.new_value:
                    component_type = change.new_value
                    for platform, config in self.compatibility_matrix.items():
                        if component_type in config.get('forbidden_components', []):
                            impact[platform].append(f"Component '{component_type}' not supported")

                if 'releaseVersion' in change.field_path:
                    platform = change.field_path.split('.')[-1]
                    if platform in impact:
                        impact[platform].append(f"Release status change: {change.description}")

        return impact

    def generate_migration_report(self, changes: List[SchemaChange], output_file: str = None) -> str:
        """Generate detailed migration report"""
        report_lines = []
        report_lines.append("# Breaking Change Analysis Report")
        report_lines.append(f"Generated on: {os.popen('date').read().strip()}")
        report_lines.append("")

        # Summary
        breaking_count = sum(1 for c in changes if c.change_type == ChangeType.BREAKING)
        critical_count = sum(1 for c in changes if c.severity == 'critical')
        major_count = sum(1 for c in changes if c.severity == 'major')

        report_lines.append("## Summary")
        report_lines.append(f"- Breaking changes: {breaking_count}")
        report_lines.append(f"- Critical issues: {critical_count}")
        report_lines.append(f"- Major issues: {major_count}")
        report_lines.append("")

        # Breaking changes
        if breaking_count > 0:
            report_lines.append("## Breaking Changes")
            for change in changes:
                if change.change_type == ChangeType.BREAKING:
                    report_lines.append(f"### {change.field_path}")
                    report_lines.append(f"**Severity:** {change.severity}")
                    report_lines.append(f"**Description:** {change.description}")
                    report_lines.append(f"**Impact:** {change.impact}")
                    if change.migration_guide:
                        report_lines.append(f"**Migration:** {change.migration_guide}")
                    report_lines.append("")

        # Platform impact
        platform_impact = self.analyze_platform_impact(changes)
        if any(platform_impact.values()):
            report_lines.append("## Platform Impact")
            for platform, issues in platform_impact.items():
                if issues:
                    report_lines.append(f"### {platform.title()}")
                    for issue in issues:
                        report_lines.append(f"- {issue}")
                    report_lines.append("")

        report_content = "\n".join(report_lines)

        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_content)

        return report_content


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python breaking_change_detector.py <file_path> [--base-branch <branch>] [--report <output_file>]")
        sys.exit(1)

    file_path = sys.argv[1]
    base_branch = "master"
    report_file = None

    # Parse arguments
    if "--base-branch" in sys.argv:
        idx = sys.argv.index("--base-branch")
        if idx + 1 < len(sys.argv):
            base_branch = sys.argv[idx + 1]

    if "--report" in sys.argv:
        idx = sys.argv.index("--report")
        if idx + 1 < len(sys.argv):
            report_file = sys.argv[idx + 1]

    detector = BreakingChangeDetector()

    try:
        changes = detector.detect_git_changes(file_path, base_branch)

        # Generate report
        report = detector.generate_migration_report(changes, report_file)

        # Print summary
        breaking_count = sum(1 for c in changes if c.change_type == ChangeType.BREAKING)
        critical_count = sum(1 for c in changes if c.severity == 'critical')

        print(f"🔍 Breaking Change Analysis: {file_path}")
        print(f"Breaking changes: {breaking_count}")
        print(f"Critical issues: {critical_count}")

        if critical_count > 0:
            print("\n❌ Critical breaking changes detected!")
            for change in changes:
                if change.severity == 'critical':
                    print(f"  • {change.description}")
            sys.exit(1)
        elif breaking_count > 0:
            print("\n⚠️ Breaking changes detected!")
            for change in changes:
                if change.change_type == ChangeType.BREAKING:
                    print(f"  • {change.description}")
            sys.exit(1)
        else:
            print("\n✅ No breaking changes detected")
            sys.exit(0)

    except Exception as e:
        print(f"❌ Error analyzing changes: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()