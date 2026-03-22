"""
Pattern Validation Framework - Comprehensive pattern validation.

This module provides a flexible framework for validating patterns
with customizable rules and severity levels.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
from enum import Enum
import re


class RuleSeverity(Enum):
    """Severity levels for validation rules."""
    CRITICAL = "critical"  # Must pass, blocks ingestion
    ERROR = "error"        # Should pass, may block depending on config
    WARNING = "warning"    # Informational, doesn't block
    INFO = "info"          # Informational only


@dataclass
class ValidationRule:
    """A validation rule for patterns."""
    rule_id: str
    name: str
    description: str
    severity: RuleSeverity
    check_function: Callable[[Dict[str, Any]], bool]
    error_message: str = ""
    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "description": self.description,
            "severity": self.severity.value,
            "error_message": self.error_message,
            "enabled": self.enabled,
        }


@dataclass
class ValidationResult:
    """Result of validating a pattern against rules."""
    pattern_id: str
    is_valid: bool
    passed_rules: List[str] = field(default_factory=list)
    failed_rules: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    validation_time_ms: float = 0.0
    total_rules_checked: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "pattern_id": self.pattern_id,
            "is_valid": self.is_valid,
            "passed_rules": self.passed_rules,
            "failed_rules": self.failed_rules,
            "warnings": self.warnings,
            "validation_time_ms": self.validation_time_ms,
            "total_rules_checked": self.total_rules_checked,
        }


class PatternValidationFramework:
    """
    Comprehensive framework for validating patterns.

    This framework provides:
    - Built-in validation rules for common checks
    - Custom rule registration
    - Configurable severity handling
    - Validation result aggregation
    """

    def __init__(self, strict_mode: bool = True):
        """
        Initialize the validation framework.

        Args:
            strict_mode: If True, ERROR-level failures block validation.
                        If False, only CRITICAL failures block.
        """
        self.strict_mode = strict_mode
        self._rules: Dict[str, ValidationRule] = {}
        self._validation_stats: Dict[str, int] = {
            "validations_performed": 0,
            "patterns_passed": 0,
            "patterns_failed": 0,
            "rules_triggered": 0,
        }

        # Register built-in rules
        self._register_builtin_rules()

    def _register_builtin_rules(self) -> None:
        """Register built-in validation rules."""
        # Structural rules
        self.register_rule(ValidationRule(
            rule_id="struct_001",
            name="Has Content",
            description="Pattern must have non-empty content",
            severity=RuleSeverity.CRITICAL,
            check_function=lambda p: bool(p.get("content", "").strip()),
            error_message="Pattern content is empty",
        ))

        self.register_rule(ValidationRule(
            rule_id="struct_002",
            name="Has Label",
            description="Pattern should have a label",
            severity=RuleSeverity.ERROR,
            check_function=lambda p: bool(p.get("label", "").strip()),
            error_message="Pattern is missing a label",
        ))

        self.register_rule(ValidationRule(
            rule_id="struct_003",
            name="Valid Hierarchy Level",
            description="Hierarchy level must be non-negative",
            severity=RuleSeverity.ERROR,
            check_function=lambda p: p.get("hierarchy_level", 0) >= 0,
            error_message="Hierarchy level cannot be negative",
        ))

        self.register_rule(ValidationRule(
            rule_id="struct_004",
            name="Valid Difficulty",
            description="Difficulty must be between 1 and 10 if specified",
            severity=RuleSeverity.WARNING,
            check_function=lambda p: (
                p.get("difficulty") is None or
                1 <= p.get("difficulty", 1) <= 10
            ),
            error_message="Difficulty should be between 1 and 10",
        ))

        # Content rules
        self.register_rule(ValidationRule(
            rule_id="content_001",
            name="No Malicious Content",
            description="Content must not contain script tags",
            severity=RuleSeverity.CRITICAL,
            check_function=lambda p: not bool(
                re.search(r"<script.*?>", p.get("content", ""), re.IGNORECASE)
            ),
            error_message="Content contains potentially malicious script tags",
        ))

        self.register_rule(ValidationRule(
            rule_id="content_002",
            name="Reasonable Length",
            description="Content should be within reasonable bounds",
            severity=RuleSeverity.WARNING,
            check_function=lambda p: (
                0 < len(p.get("content", "")) <= 100000
            ),
            error_message="Content length is outside recommended bounds",
        ))

        self.register_rule(ValidationRule(
            rule_id="content_003",
            name="Valid Composition",
            description="Composition must be a list if specified",
            severity=RuleSeverity.ERROR,
            check_function=lambda p: (
                "composition" not in p or
                isinstance(p.get("composition"), list)
            ),
            error_message="Composition must be a list",
        ))

        self.register_rule(ValidationRule(
            rule_id="content_004",
            name="Non-empty Composition",
            description="Composition elements should not be empty",
            severity=RuleSeverity.WARNING,
            check_function=lambda p: (
                "composition" not in p or
                all(bool(c) for c in p.get("composition", []))
            ),
            error_message="Composition contains empty elements",
        ))

        # Reference rules
        self.register_rule(ValidationRule(
            rule_id="ref_001",
            name="Valid Related Patterns",
            description="Related patterns must be a list if specified",
            severity=RuleSeverity.ERROR,
            check_function=lambda p: (
                "related_patterns" not in p or
                isinstance(p.get("related_patterns"), list)
            ),
            error_message="Related patterns must be a list",
        ))

        self.register_rule(ValidationRule(
            rule_id="ref_002",
            name="Non-empty Related Patterns",
            description="Related pattern references should not be empty strings",
            severity=RuleSeverity.WARNING,
            check_function=lambda p: (
                "related_patterns" not in p or
                all(bool(r) for r in p.get("related_patterns", []))
            ),
            error_message="Related patterns contains empty references",
        ))

        # Metadata rules
        self.register_rule(ValidationRule(
            rule_id="meta_001",
            name="Valid Metadata",
            description="Metadata must be a dict if specified",
            severity=RuleSeverity.ERROR,
            check_function=lambda p: (
                "metadata" not in p or
                isinstance(p.get("metadata"), dict)
            ),
            error_message="Metadata must be a dictionary",
        ))

    def register_rule(self, rule: ValidationRule) -> None:
        """
        Register a validation rule.

        Args:
            rule: The validation rule to register.
        """
        self._rules[rule.rule_id] = rule

    def unregister_rule(self, rule_id: str) -> bool:
        """
        Unregister a validation rule.

        Args:
            rule_id: ID of the rule to remove.

        Returns:
            True if rule was removed, False if not found.
        """
        if rule_id in self._rules:
            del self._rules[rule_id]
            return True
        return False

    def enable_rule(self, rule_id: str) -> bool:
        """Enable a validation rule."""
        if rule_id in self._rules:
            self._rules[rule_id].enabled = True
            return True
        return False

    def disable_rule(self, rule_id: str) -> bool:
        """Disable a validation rule."""
        if rule_id in self._rules:
            self._rules[rule_id].enabled = False
            return True
        return False

    def validate_pattern(self, pattern: Dict[str, Any]) -> ValidationResult:
        """
        Validate a pattern against all registered rules.

        Args:
            pattern: The pattern to validate.

        Returns:
            ValidationResult with validation details.
        """
        start_time = datetime.now()
        passed_rules = []
        failed_rules = []
        warnings = []

        pattern_id = pattern.get("id", pattern.get("label", "unknown"))

        for rule_id, rule in self._rules.items():
            if not rule.enabled:
                continue

            try:
                if rule.check_function(pattern):
                    passed_rules.append(rule_id)
                else:
                    failure = {
                        "rule_id": rule_id,
                        "rule_name": rule.name,
                        "severity": rule.severity.value,
                        "message": rule.error_message,
                    }
                    failed_rules.append(failure)

                    # Collect warnings
                    if rule.severity == RuleSeverity.WARNING:
                        warnings.append(f"{rule.name}: {rule.error_message}")

            except Exception as e:
                failed_rules.append({
                    "rule_id": rule_id,
                    "rule_name": rule.name,
                    "severity": "error",
                    "message": f"Rule check failed: {str(e)}",
                })

        # Determine if pattern is valid
        critical_failures = [
            f for f in failed_rules
            if f.get("severity") == RuleSeverity.CRITICAL.value
        ]
        error_failures = [
            f for f in failed_rules
            if f.get("severity") == RuleSeverity.ERROR.value
        ]

        is_valid = len(critical_failures) == 0
        if self.strict_mode:
            is_valid = len(error_failures) == 0 and is_valid

        validation_time = (datetime.now() - start_time).total_seconds() * 1000

        # Update stats
        self._validation_stats["validations_performed"] += 1
        self._validation_stats["rules_triggered"] += len(failed_rules)
        if is_valid:
            self._validation_stats["patterns_passed"] += 1
        else:
            self._validation_stats["patterns_failed"] += 1

        return ValidationResult(
            pattern_id=pattern_id,
            is_valid=is_valid,
            passed_rules=passed_rules,
            failed_rules=failed_rules,
            warnings=warnings,
            validation_time_ms=validation_time,
            total_rules_checked=len(passed_rules) + len(failed_rules),
        )

    def validate_batch(self, patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate a batch of patterns.

        Args:
            patterns: List of patterns to validate.

        Returns:
            Dict with batch validation results.
        """
        results = []
        valid_count = 0
        invalid_count = 0

        for pattern in patterns:
            result = self.validate_pattern(pattern)
            results.append(result.to_dict())

            if result.is_valid:
                valid_count += 1
            else:
                invalid_count += 1

        return {
            "total_patterns": len(patterns),
            "valid_count": valid_count,
            "invalid_count": invalid_count,
            "results": results,
        }

    def validate_with_custom_rules(
        self,
        pattern: Dict[str, Any],
        custom_rules: List[ValidationRule],
    ) -> ValidationResult:
        """
        Validate a pattern with additional custom rules.

        Args:
            pattern: The pattern to validate.
            custom_rules: Additional rules to apply.

        Returns:
            ValidationResult with combined validation details.
        """
        # Temporarily add custom rules
        added_ids = []
        for rule in custom_rules:
            if rule.rule_id not in self._rules:
                self._rules[rule.rule_id] = rule
                added_ids.append(rule.rule_id)

        # Validate
        result = self.validate_pattern(pattern)

        # Remove temporary rules
        for rule_id in added_ids:
            del self._rules[rule_id]

        return result

    def get_rule(self, rule_id: str) -> Optional[ValidationRule]:
        """Get a validation rule by ID."""
        return self._rules.get(rule_id)

    def get_all_rules(self) -> List[ValidationRule]:
        """Get all registered rules."""
        return list(self._rules.values())

    def get_rules_by_severity(self, severity: RuleSeverity) -> List[ValidationRule]:
        """Get rules filtered by severity."""
        return [r for r in self._rules.values() if r.severity == severity]

    def get_enabled_rules(self) -> List[ValidationRule]:
        """Get all enabled rules."""
        return [r for r in self._rules.values() if r.enabled]

    def get_stats(self) -> Dict[str, Any]:
        """Get validation statistics."""
        return {
            **self._validation_stats,
            "total_rules": len(self._rules),
            "enabled_rules": len([r for r in self._rules.values() if r.enabled]),
        }

    def reset_stats(self) -> None:
        """Reset validation statistics."""
        self._validation_stats = {
            "validations_performed": 0,
            "patterns_passed": 0,
            "patterns_failed": 0,
            "rules_triggered": 0,
        }

    def create_custom_rule(
        self,
        rule_id: str,
        name: str,
        description: str,
        severity: RuleSeverity,
        check_function: Callable[[Dict[str, Any]], bool],
        error_message: str = "",
    ) -> ValidationRule:
        """
        Create and register a custom validation rule.

        Args:
            rule_id: Unique identifier for the rule.
            name: Human-readable name.
            description: Detailed description.
            severity: Rule severity level.
            check_function: Function that takes a pattern and returns bool.
            error_message: Message to display on failure.

        Returns:
            The created ValidationRule.
        """
        rule = ValidationRule(
            rule_id=rule_id,
            name=name,
            description=description,
            severity=severity,
            check_function=check_function,
            error_message=error_message,
        )
        self.register_rule(rule)
        return rule
