#!/usr/bin/env python3
"""
SDUI Schema Validation Pipeline
Enhanced validation system for SDUI contracts with quality metrics and compliance scoring.
"""

import json
import os
import sys
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import yaml
import jsonschema
from collections import defaultdict
import re


@dataclass
class ValidationError:
    """Structured validation error"""
    level: str  # 'critical', 'high', 'medium', 'low'
    category: str  # 'schema', 'platform', 'performance', 'accessibility', 'design'
    message: str
    path: str
    suggested_fix: Optional[str] = None
    confidence: float = 1.0


@dataclass
class ValidationResult:
    """Complete validation result"""
    file_path: str
    schema_compliance: float
    platform_compatibility: float
    performance_score: float
    accessibility_score: float
    design_compliance: float
    overall_score: float
    errors: List[ValidationError]
    warnings: List[ValidationError]
    suggestions: List[ValidationError]
    processing_time: float
    validation_timestamp: str


@dataclass
class QualityMetrics:
    """Quality metrics aggregation"""
    total_files: int
    passed_files: int
    failed_files: int
    critical_issues: int
    high_priority_issues: int
    average_score: float
    worst_file: Optional[str]
    best_file: Optional[str]
    performance_impact: str


class SDUIValidator:
    """Enhanced SDUI Schema Validator"""

    def __init__(self, config_path: str = ".validator.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.metaschemas = self._load_metaschemas()
        self.validation_cache = {}

        # SDUI-specific validation rules
        self.sdui_rules = self._initialize_sdui_rules()
        self.web_compatibility_rules = self._initialize_web_rules()
        self.performance_rules = self._initialize_performance_rules()
        self.accessibility_rules = self._initialize_accessibility_rules()

    def _load_config(self) -> Dict:
        """Load validator configuration"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            raise Exception(f"Failed to load config: {e}")

    def _load_metaschemas(self) -> Dict:
        """Load metaschemas for validation"""
        metaschemas = {}
        for schema_type, config in self.config.get('schemas', {}).items():
            metaschema_path = config.get('metaschema')
            if metaschema_path:
                try:
                    with open(metaschema_path, 'r', encoding='utf-8') as f:
                        metaschemas[schema_type] = json.load(f)
                except Exception as e:
                    print(f"Warning: Failed to load metaschema {metaschema_path}: {e}")
        return metaschemas

    def _initialize_sdui_rules(self) -> Dict:
        """Initialize SDUI-specific validation rules"""
        return {
            'required_fields': ['type', 'releaseVersion'],
            'forbidden_android_components': [
                'LabelView', 'EditText', 'LinearLayout', 'RelativeLayout',
                'ScrollView', 'ListView', 'GridView', 'Toolbar'
            ],
            'required_web_components': [
                'ButtonView', 'TextView', 'ImageView', 'IconView',
                'DataView', 'CustomView', 'Spacer'
            ],
            'state_aware_pattern': {
                'required_in_stateful': ['stateKey', 'defaultState'],
                'forbidden_in_stateless': ['stateKey']
            },
            'version_constraints': {
                'min_version': 1,
                'max_version': 10,
                'required_format': r'^v\d+$'
            }
        }

    def _initialize_web_rules(self) -> Dict:
        """Initialize web platform compatibility rules"""
        return {
            'release_version': {
                'web': ['released', 'beta', 'alpha'],
                'required': True
            },
            'accessibility': {
                'required_attributes': ['aria-label', 'role', 'tabindex'],
                'semantic_elements': ['button', 'input', 'label', 'heading']
            },
            'responsive_design': {
                'breakpoints': ['mobile', 'tablet', 'desktop'],
                'required_viewport': True
            },
            'performance': {
                'max_nesting_depth': 10,
                'max_children': 50,
                'forbidden_inline_styles': True
            }
        }

    def _initialize_performance_rules(self) -> Dict:
        """Initialize performance optimization rules"""
        return {
            'bundle_size': {
                'max_component_size': 50000,  # bytes
                'max_dependency_count': 20
            },
            'render_optimization': {
                'lazy_loading_threshold': 10,
                'virtualization_threshold': 100
            },
            'state_management': {
                'max_state_depth': 5,
                'avoid_circular_refs': True
            }
        }

    def _initialize_accessibility_rules(self) -> Dict:
        """Initialize accessibility compliance rules"""
        return {
            'wcag_21_aa': {
                'color_contrast': {'min_ratio': 4.5},
                'focus_management': True,
                'keyboard_navigation': True,
                'screen_reader_support': True
            },
            'semantic_markup': {
                'proper_headings': True,
                'form_labels': True,
                'alternative_text': True
            }
        }

    def validate_file(self, file_path: str) -> ValidationResult:
        """Validate a single SDUI contract file"""
        start_time = time.time()
        errors = []
        warnings = []
        suggestions = []

        # Load and parse file
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                contract = json.load(f)
        except json.JSONDecodeError as e:
            errors.append(ValidationError(
                level='critical',
                category='schema',
                message=f"Invalid JSON syntax: {e}",
                path=file_path,
                suggested_fix="Fix JSON syntax errors"
            ))
            return self._create_failed_result(file_path, errors, time.time() - start_time)
        except Exception as e:
            errors.append(ValidationError(
                level='critical',
                category='schema',
                message=f"File read error: {e}",
                path=file_path
            ))
            return self._create_failed_result(file_path, errors, time.time() - start_time)

        # Schema compliance validation
        schema_score, schema_errors = self._validate_schema_compliance(contract, file_path)
        errors.extend(schema_errors)

        # Platform compatibility validation
        platform_score, platform_errors = self._validate_platform_compatibility(contract, file_path)
        errors.extend(platform_errors)

        # Performance validation
        performance_score, perf_errors = self._validate_performance(contract, file_path)
        errors.extend(perf_errors)

        # Accessibility validation
        accessibility_score, acc_errors = self._validate_accessibility(contract, file_path)
        errors.extend(acc_errors)

        # Design compliance validation
        design_score, design_errors = self._validate_design_compliance(contract, file_path)
        errors.extend(design_errors)

        # Calculate overall score
        overall_score = self._calculate_overall_score(
            schema_score, platform_score, performance_score,
            accessibility_score, design_score, errors
        )

        # Separate errors by level
        critical_errors = [e for e in errors if e.level == 'critical']
        high_errors = [e for e in errors if e.level == 'high']
        medium_errors = [e for e in errors if e.level == 'medium']
        low_errors = [e for e in errors if e.level == 'low']

        return ValidationResult(
            file_path=file_path,
            schema_compliance=schema_score,
            platform_compatibility=platform_score,
            performance_score=performance_score,
            accessibility_score=accessibility_score,
            design_compliance=design_score,
            overall_score=overall_score,
            errors=critical_errors + high_errors,
            warnings=medium_errors,
            suggestions=low_errors,
            processing_time=time.time() - start_time,
            validation_timestamp=datetime.now().isoformat()
        )

    def _validate_schema_compliance(self, contract: Dict, file_path: str) -> Tuple[float, List[ValidationError]]:
        """Validate against metaschema"""
        errors = []
        score = 100.0

        # Determine schema type
        schema_type = self._determine_schema_type(file_path)
        if not schema_type:
            errors.append(ValidationError(
                level='high',
                category='schema',
                message="Cannot determine schema type",
                path=file_path
            ))
            return 50.0, errors

        # Validate against metaschema
        metaschema = self.metaschemas.get(schema_type)
        if metaschema:
            try:
                # This is a simplified validation - in practice you'd need proper metaschema resolution
                self._validate_basic_structure(contract, errors, file_path)
            except Exception as e:
                errors.append(ValidationError(
                    level='critical',
                    category='schema',
                    message=f"Metaschema validation failed: {e}",
                    path=file_path
                ))
                score -= 30

        # SDUI-specific rules
        self._validate_sdui_structure(contract, errors, file_path)

        # Deduct score based on errors
        critical_count = sum(1 for e in errors if e.level == 'critical')
        high_count = sum(1 for e in errors if e.level == 'high')
        score -= critical_count * 25 + high_count * 10

        return max(0, min(100, score)), errors

    def _validate_platform_compatibility(self, contract: Dict, file_path: str) -> Tuple[float, List[ValidationError]]:
        """Validate web platform compatibility"""
        errors = []
        score = 100.0

        # Release version validation
        release_version = contract.get('releaseVersion', {})
        if 'web' not in release_version:
            errors.append(ValidationError(
                level='critical',
                category='platform',
                message="Missing 'web' in releaseVersion",
                path=file_path,
                suggested_fix="Add releaseVersion.web field with 'released', 'beta', or 'alpha'"
            ))
            score -= 30
        elif release_version['web'] not in self.web_compatibility_rules['release_version']['web']:
            errors.append(ValidationError(
                level='high',
                category='platform',
                message=f"Invalid web release status: {release_version['web']}",
                path=file_path,
                suggested_fix="Use 'released', 'beta', or 'alpha' for web release status"
            ))
            score -= 15

        # Check for Android-specific components
        self._check_forbidden_components(contract, errors, file_path)

        # Check accessibility requirements
        self._check_web_accessibility(contract, errors, file_path)

        critical_count = sum(1 for e in errors if e.level == 'critical')
        high_count = sum(1 for e in errors if e.level == 'high')
        score -= critical_count * 25 + high_count * 10

        return max(0, min(100, score)), errors

    def _validate_performance(self, contract: Dict, file_path: str) -> Tuple[float, List[ValidationError]]:
        """Validate performance optimization"""
        errors = []
        score = 100.0

        # Check nesting depth
        max_depth = self._calculate_nesting_depth(contract)
        if max_depth > self.performance_rules['render_optimization']['virtualization_threshold']:
            errors.append(ValidationError(
                level='high',
                category='performance',
                message=f"Excessive nesting depth: {max_depth}",
                path=file_path,
                suggested_fix="Consider flattening component hierarchy"
            ))
            score -= 20

        # Check component count
        component_count = self._count_components(contract)
        if component_count > self.performance_rules['bundle_size']['max_dependency_count']:
            errors.append(ValidationError(
                level='medium',
                category='performance',
                message=f"High component count: {component_count}",
                path=file_path,
                suggested_fix="Consider component optimization or lazy loading"
            ))
            score -= 10

        return max(0, min(100, score)), errors

    def _validate_accessibility(self, contract: Dict, file_path: str) -> Tuple[float, List[ValidationError]]:
        """Validate accessibility compliance"""
        errors = []
        score = 100.0

        # Check for accessibility attributes
        self._check_accessibility_attributes(contract, errors, file_path)

        # Check semantic structure
        self._check_semantic_structure(contract, errors, file_path)

        critical_count = sum(1 for e in errors if e.level == 'critical')
        high_count = sum(1 for e in errors if e.level == 'high')
        score -= critical_count * 20 + high_count * 10

        return max(0, min(100, score)), errors

    def _validate_design_compliance(self, contract: Dict, file_path: str) -> Tuple[float, List[ValidationError]]:
        """Validate design system compliance"""
        errors = []
        score = 100.0

        # Check design tokens usage
        self._check_design_tokens(contract, errors, file_path)

        # Check spacing consistency
        self._check_spacing_consistency(contract, errors, file_path)

        return max(0, min(100, score)), errors

    def _determine_schema_type(self, file_path: str) -> Optional[str]:
        """Determine schema type from file path"""
        path = Path(file_path)
        if 'SDUI' in path.parts:
            return 'SDUI'
        elif 'valuefields' in path.parts:
            return 'valuefields'
        elif 'widgets' in path.parts:
            return 'widgets'
        elif 'models' in path.parts:
            return 'models'
        return None

    def _validate_basic_structure(self, contract: Dict, errors: List[ValidationError], file_path: str):
        """Validate basic contract structure"""
        for field in self.sdui_rules['required_fields']:
            if field not in contract:
                errors.append(ValidationError(
                    level='critical',
                    category='schema',
                    message=f"Missing required field: {field}",
                    path=file_path,
                    suggested_fix=f"Add required field '{field}'"
                ))

    def _validate_sdui_structure(self, contract: Dict, errors: List[ValidationError], file_path: str):
        """Validate SDUI-specific structure"""
        # Check component type
        component_type = contract.get('type')
        if component_type in self.sdui_rules['forbidden_android_components']:
            errors.append(ValidationError(
                level='high',
                category='platform',
                message=f"Android-specific component not supported on web: {component_type}",
                path=file_path,
                suggested_fix=f"Replace {component_type} with web-compatible alternative"
            ))

    def _check_forbidden_components(self, contract: Dict, errors: List[ValidationError], file_path: str):
        """Check for forbidden Android components"""
        def check_recursive(obj, path=""):
            if isinstance(obj, dict):
                if obj.get('type') in self.sdui_rules['forbidden_android_components']:
                    errors.append(ValidationError(
                        level='high',
                        category='platform',
                        message=f"Forbidden Android component: {obj.get('type')} at {path}",
                        path=file_path,
                        suggested_fix="Replace with web-compatible component"
                    ))
                for key, value in obj.items():
                    check_recursive(value, f"{path}.{key}" if path else key)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    check_recursive(item, f"{path}[{i}]")

        check_recursive(contract)

    def _check_web_accessibility(self, contract: Dict, errors: List[ValidationError], file_path: str):
        """Check web accessibility requirements"""
        # This is a simplified check - real implementation would be more comprehensive
        if contract.get('type') == 'ButtonView':
            if 'accessibility' not in contract:
                errors.append(ValidationError(
                    level='medium',
                    category='accessibility',
                    message="ButtonView missing accessibility attributes",
                    path=file_path,
                    suggested_fix="Add accessibility.label and accessibility.role"
                ))

    def _check_accessibility_attributes(self, contract: Dict, errors: List[ValidationError], file_path: str):
        """Check for accessibility attributes"""
        interactive_components = ['ButtonView', 'CustomView', 'SelectionWrapper']

        def check_recursive(obj, path=""):
            if isinstance(obj, dict):
                component_type = obj.get('type')
                if component_type in interactive_components:
                    if 'accessibility' not in obj:
                        errors.append(ValidationError(
                            level='medium',
                            category='accessibility',
                            message=f"Interactive component {component_type} missing accessibility",
                            path=f"{file_path}:{path}",
                            suggested_fix="Add accessibility attributes"
                        ))

                for key, value in obj.items():
                    check_recursive(value, f"{path}.{key}" if path else key)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    check_recursive(item, f"{path}[{i}]")

        check_recursive(contract)

    def _check_semantic_structure(self, contract: Dict, errors: List[ValidationError], file_path: str):
        """Check semantic structure"""
        pass  # Placeholder for semantic validation

    def _check_design_tokens(self, contract: Dict, errors: List[ValidationError], file_path: str):
        """Check design tokens usage"""
        pass  # Placeholder for design token validation

    def _check_spacing_consistency(self, contract: Dict, errors: List[ValidationError], file_path: str):
        """Check spacing consistency"""
        pass  # Placeholder for spacing validation

    def _calculate_nesting_depth(self, obj: Any, current_depth: int = 0) -> int:
        """Calculate maximum nesting depth"""
        if isinstance(obj, dict):
            max_child_depth = current_depth
            for value in obj.values():
                max_child_depth = max(max_child_depth, self._calculate_nesting_depth(value, current_depth + 1))
            return max_child_depth
        elif isinstance(obj, list):
            max_child_depth = current_depth
            for item in obj:
                max_child_depth = max(max_child_depth, self._calculate_nesting_depth(item, current_depth + 1))
            return max_child_depth
        return current_depth

    def _count_components(self, obj: Any) -> int:
        """Count total components"""
        count = 0
        if isinstance(obj, dict):
            if 'type' in obj:
                count += 1
            for value in obj.values():
                count += self._count_components(value)
        elif isinstance(obj, list):
            for item in obj:
                count += self._count_components(item)
        return count

    def _calculate_overall_score(self, schema: float, platform: float, performance: float,
                               accessibility: float, design: float, errors: List[ValidationError]) -> float:
        """Calculate weighted overall score"""
        weights = {
            'schema': 0.35,
            'platform': 0.25,
            'performance': 0.15,
            'accessibility': 0.15,
            'design': 0.10
        }

        weighted_score = (
            schema * weights['schema'] +
            platform * weights['platform'] +
            performance * weights['performance'] +
            accessibility * weights['accessibility'] +
            design * weights['design']
        )

        # Additional penalty for critical errors
        critical_count = sum(1 for e in errors if e.level == 'critical')
        if critical_count > 0:
            weighted_score = min(weighted_score, 60.0)  # Cap at 60 if critical errors exist

        return max(0, min(100, weighted_score))

    def _create_failed_result(self, file_path: str, errors: List[ValidationError], processing_time: float) -> ValidationResult:
        """Create result for failed validation"""
        return ValidationResult(
            file_path=file_path,
            schema_compliance=0.0,
            platform_compatibility=0.0,
            performance_score=0.0,
            accessibility_score=0.0,
            design_compliance=0.0,
            overall_score=0.0,
            errors=errors,
            warnings=[],
            suggestions=[],
            processing_time=processing_time,
            validation_timestamp=datetime.now().isoformat()
        )

    def validate_directory(self, directory: str, pattern: str = "*.json") -> List[ValidationResult]:
        """Validate all files in directory"""
        results = []
        directory_path = Path(directory)

        for file_path in directory_path.rglob(pattern):
            if file_path.is_file():
                try:
                    result = self.validate_file(str(file_path))
                    results.append(result)
                except Exception as e:
                    print(f"Error validating {file_path}: {e}")

        return results

    def generate_quality_report(self, results: List[ValidationResult]) -> QualityMetrics:
        """Generate quality metrics from validation results"""
        if not results:
            return QualityMetrics(0, 0, 0, 0, 0, 0.0, None, None, "no_data")

        total_files = len(results)
        passed_files = sum(1 for r in results if r.overall_score >= 80)
        failed_files = total_files - passed_files

        critical_issues = sum(len(r.errors) for r in results)
        high_priority_issues = sum(len(r.warnings) for r in results)

        average_score = sum(r.overall_score for r in results) / total_files

        worst_file = min(results, key=lambda r: r.overall_score).file_path if results else None
        best_file = max(results, key=lambda r: r.overall_score).file_path if results else None

        # Determine performance impact
        if average_score >= 90:
            performance_impact = "excellent"
        elif average_score >= 80:
            performance_impact = "good"
        elif average_score >= 70:
            performance_impact = "acceptable"
        elif average_score >= 60:
            performance_impact = "concerning"
        else:
            performance_impact = "critical"

        return QualityMetrics(
            total_files=total_files,
            passed_files=passed_files,
            failed_files=failed_files,
            critical_issues=critical_issues,
            high_priority_issues=high_priority_issues,
            average_score=average_score,
            worst_file=worst_file,
            best_file=best_file,
            performance_impact=performance_impact
        )

    def export_report(self, results: List[ValidationResult], metrics: QualityMetrics,
                     output_path: str = "validation_report.json"):
        """Export validation report to JSON"""
        report = {
            "validation_summary": asdict(metrics),
            "validation_timestamp": datetime.now().isoformat(),
            "results": [asdict(result) for result in results]
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"Report exported to: {output_path}")


def main():
    """Main validation pipeline"""
    if len(sys.argv) < 2:
        print("Usage: python validation_pipeline.py <file_or_directory> [--output report.json]")
        sys.exit(1)

    target_path = sys.argv[1]
    output_path = "validation_report.json"

    if "--output" in sys.argv:
        output_idx = sys.argv.index("--output")
        if output_idx + 1 < len(sys.argv):
            output_path = sys.argv[output_idx + 1]

    validator = SDUIValidator()

    print("🔍 Starting SDUI validation pipeline...")
    start_time = time.time()

    if os.path.isfile(target_path):
        results = [validator.validate_file(target_path)]
    elif os.path.isdir(target_path):
        results = validator.validate_directory(target_path)
    else:
        print(f"❌ Path not found: {target_path}")
        sys.exit(1)

    total_time = time.time() - start_time
    metrics = validator.generate_quality_report(results)

    # Print summary
    print(f"\n📊 Validation Summary (completed in {total_time:.2f}s)")
    print(f"Files processed: {metrics.total_files}")
    print(f"Passed: {metrics.passed_files} ✅")
    print(f"Failed: {metrics.failed_files} ❌")
    print(f"Critical issues: {metrics.critical_issues}")
    print(f"Average score: {metrics.average_score:.1f}/100")
    print(f"Performance impact: {metrics.performance_impact}")

    # Export report
    validator.export_report(results, metrics, output_path)

    # Exit with appropriate code
    if metrics.critical_issues > 0:
        print("\n❌ Validation failed: Critical issues found")
        sys.exit(1)
    elif metrics.average_score < 70:
        print("\n⚠️ Validation warning: Low quality score")
        sys.exit(1)
    else:
        print("\n✅ Validation passed")
        sys.exit(0)


if __name__ == "__main__":
    main()