"""
ErrorCorrector - Corrects errors and applies fixes for RPA learning.

Provides intelligent error correction capabilities:
- Automated fix suggestions
- Pattern-based corrections
- Fix validation
- Learning from successful corrections
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Callable
from datetime import datetime
import re
import logging

from .error_classifier import ClassifiedError, ErrorClassifier

logger = logging.getLogger(__name__)


@dataclass
class Correction:
    """Represents an error correction."""
    correction_id: str
    error_id: str
    fix_type: str  # code_change, parameter_adjustment, logic_fix
    description: str
    original_code: Optional[str] = None
    corrected_code: Optional[str] = None
    confidence: float = 0.0  # 0.0-1.0
    applied: bool = False
    successful: bool = False
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "correction_id": self.correction_id,
            "error_id": self.error_id,
            "fix_type": self.fix_type,
            "description": self.description,
            "original_code": self.original_code,
            "corrected_code": self.corrected_code,
            "confidence": self.confidence,
            "applied": self.applied,
            "successful": self.successful,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class CorrectionPattern:
    """Pattern for applying corrections."""
    pattern_id: str
    error_category: str
    detection_pattern: str  # Regex to detect error pattern
    fix_template: str  # Template for the fix
    confidence: float = 0.5
    success_count: int = 0
    failure_count: int = 0
    examples: List[Dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "pattern_id": self.pattern_id,
            "error_category": self.error_category,
            "detection_pattern": self.detection_pattern,
            "fix_template": self.fix_template,
            "confidence": self.confidence,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": self.success_count / max(1, self.success_count + self.failure_count),
        }


class ErrorCorrector:
    """
    Intelligent error correction system.

    Analyzes errors and applies corrections with learning capabilities.
    """

    # Predefined correction patterns
    CORRECTION_PATTERNS = [
        # NameError corrections
        {
            "pattern_id": "undefined_variable",
            "error_category": "name_error",
            "detection_pattern": r"NameError: name '(\w+)' is not defined",
            "fix_template": "Define variable '{var}' before use or check for typos",
            "fixes": [
                "Add variable definition before this line",
                "Check if variable name is misspelled",
                "Verify variable scope",
            ],
        },
        # IndexError corrections
        {
            "pattern_id": "index_out_of_range",
            "error_category": "index_error",
            "detection_pattern": r"IndexError: (?:list|tuple|string) index out of range",
            "fix_template": "Check index bounds: len({container}) > {index}",
            "fixes": [
                "Add bounds check before indexing",
                "Use try-except for safer access",
                "Check if the sequence is empty",
            ],
        },
        # KeyError corrections
        {
            "pattern_id": "missing_key",
            "error_category": "key_error",
            "detection_pattern": r"KeyError: '?(\w+)?'?$",
            "fix_template": "Check if key '{key}' exists before access",
            "fixes": [
                "Use dict.get('{key}', default) instead",
                "Add 'if '{key}' in dict:' check",
                "Verify dictionary content",
            ],
        },
        # TypeError corrections
        {
            "pattern_id": "type_mismatch",
            "error_category": "type_error",
            "detection_pattern": r"TypeError: (.+)",
            "fix_template": "Type conversion or check needed",
            "fixes": [
                "Add type check with isinstance()",
                "Convert to correct type",
                "Verify operation compatibility",
            ],
        },
        # ZeroDivisionError corrections
        {
            "pattern_id": "division_by_zero",
            "error_category": "zero_division_error",
            "detection_pattern": r"ZeroDivisionError",
            "fix_template": "Add zero check before division",
            "fixes": [
                "Add 'if divisor != 0:' check",
                "Use try-except for ZeroDivisionError",
                "Return default value for zero divisor",
            ],
        },
        # IndentationError corrections
        {
            "pattern_id": "indentation_issue",
            "error_category": "indentation_error",
            "detection_pattern": r"IndentationError: (.+)",
            "fix_template": "Fix indentation",
            "fixes": [
                "Use consistent indentation (4 spaces)",
                "Check for mixed tabs and spaces",
                "Verify block structure alignment",
            ],
        },
    ]

    def __init__(self, error_classifier: Optional[ErrorClassifier] = None):
        """
        Initialize the ErrorCorrector.

        Args:
            error_classifier: Optional ErrorClassifier instance
        """
        self.classifier = error_classifier or ErrorClassifier()
        self._corrections: List[Correction] = []
        self._patterns: Dict[str, CorrectionPattern] = {}
        self._max_history = 500

        # Initialize with predefined patterns
        self._initialize_patterns()

    def _initialize_patterns(self) -> None:
        """Initialize correction patterns from predefined list."""
        for pattern_data in self.CORRECTION_PATTERNS:
            pattern = CorrectionPattern(
                pattern_id=pattern_data["pattern_id"],
                error_category=pattern_data["error_category"],
                detection_pattern=pattern_data["detection_pattern"],
                fix_template=pattern_data["fix_template"],
                confidence=0.7,
            )
            self._patterns[pattern.pattern_id] = pattern

    def suggest_correction(
        self,
        error: ClassifiedError,
        code_context: Optional[str] = None,
    ) -> Correction:
        """
        Suggest a correction for a classified error.

        Args:
            error: The classified error
            code_context: Optional code context for the error

        Returns:
            Correction with suggested fix
        """
        import uuid
        correction_id = str(uuid.uuid4())[:8]

        # Find matching pattern
        pattern = self._find_matching_pattern(error)
        
        if pattern:
            fix = self._apply_pattern_fix(pattern, error, code_context)
            confidence = pattern.confidence
        else:
            fix = self._generate_generic_fix(error)
            confidence = 0.3

        correction = Correction(
            correction_id=correction_id,
            error_id=error.error_id,
            fix_type=self._determine_fix_type(error),
            description=fix,
            original_code=code_context[:200] if code_context else None,
            confidence=confidence,
        )

        # Store correction
        self._corrections.append(correction)
        if len(self._corrections) > self._max_history:
            self._corrections.pop(0)

        return correction

    def _find_matching_pattern(self, error: ClassifiedError) -> Optional[CorrectionPattern]:
        """Find a correction pattern matching the error."""
        # First check by category
        for pattern in self._patterns.values():
            if pattern.error_category == error.category:
                # Try to match detection pattern
                try:
                    if re.search(pattern.detection_pattern, error.message, re.IGNORECASE):
                        return pattern
                except re.error:
                    pass

        # Fallback to error type matching
        for pattern in self._patterns.values():
            if pattern.error_category.replace("_", "") in error.category.replace("_", ""):
                return pattern

        return None

    def _apply_pattern_fix(
        self,
        pattern: CorrectionPattern,
        error: ClassifiedError,
        code_context: Optional[str],
    ) -> str:
        """Apply a pattern to generate a fix."""
        fix = pattern.fix_template

        # Extract variables from error message
        try:
            match = re.search(pattern.detection_pattern, error.message)
            if match:
                groups = match.groups()
                for i, group in enumerate(groups):
                    if group:
                        fix = fix.replace(f"{{var}}", group)
                        fix = fix.replace(f"{{key}}", group)
                        fix = fix.replace(f"{{index}}", group)
        except re.error:
            pass

        return fix

    def _generate_generic_fix(self, error: ClassifiedError) -> str:
        """Generate a generic fix description."""
        fixes = {
            "syntax_error": f"Fix syntax error: {error.message}",
            "name_error": f"Define or check variable reference",
            "type_error": f"Check type compatibility",
            "value_error": f"Validate input values",
            "index_error": f"Check index bounds",
            "key_error": f"Verify key exists in dictionary",
            "attribute_error": f"Check attribute exists on object",
            "zero_division_error": f"Add zero check before division",
            "indentation_error": f"Fix code indentation",
            "recursion_error": f"Add base case to recursive function",
        }
        return fixes.get(error.category, f"Review and fix error: {error.message}")

    def _determine_fix_type(self, error: ClassifiedError) -> str:
        """Determine the type of fix needed."""
        type_mapping = {
            "syntax": "code_change",
            "indentation_error": "code_change",
            "name_error": "code_change",
            "type_error": "parameter_adjustment",
            "value_error": "parameter_adjustment",
            "index_error": "logic_fix",
            "key_error": "logic_fix",
            "attribute_error": "code_change",
            "zero_division_error": "logic_fix",
            "recursion_error": "logic_fix",
        }
        return type_mapping.get(error.category, "code_change")

    def apply_correction(
        self,
        correction: Correction,
        code: str,
        validate: bool = True,
    ) -> Tuple[str, bool, Optional[str]]:
        """
        Apply a correction to code.

        Args:
            correction: The correction to apply
            code: The original code
            validate: Whether to validate the result

        Returns:
            Tuple of (corrected_code, success, error_message)
        """
        corrected_code = code
        success = False
        error_msg = None

        # Apply correction based on fix type
        if correction.fix_type == "code_change":
            corrected_code, success = self._apply_code_change(correction, code)
        elif correction.fix_type == "logic_fix":
            corrected_code, success = self._apply_logic_fix(correction, code)
        elif correction.fix_type == "parameter_adjustment":
            corrected_code, success = self._apply_parameter_adjustment(correction, code)

        # Update correction status
        correction.applied = True
        correction.corrected_code = corrected_code

        if success:
            correction.successful = True
        else:
            error_msg = "Could not automatically apply correction"
            correction.successful = False

        return corrected_code, success, error_msg

    def _apply_code_change(
        self,
        correction: Correction,
        code: str,
    ) -> Tuple[str, bool]:
        """Apply a code change fix."""
        # This is a simplified implementation
        # Real implementation would need more sophisticated code manipulation
        return code, False  # Cannot auto-apply without more context

    def _apply_logic_fix(
        self,
        correction: Correction,
        code: str,
    ) -> Tuple[str, bool]:
        """Apply a logic fix."""
        # Simplified implementation
        return code, False

    def _apply_parameter_adjustment(
        self,
        correction: Correction,
        code: str,
    ) -> Tuple[str, bool]:
        """Apply a parameter adjustment fix."""
        # Simplified implementation
        return code, False

    def learn_from_correction(
        self,
        correction: Correction,
        successful: bool,
        actual_fix: Optional[str] = None,
    ) -> None:
        """
        Learn from a correction attempt.

        Args:
            correction: The correction that was attempted
            successful: Whether it was successful
            actual_fix: The actual fix that worked (if different)
        """
        # Find related pattern
        for pattern in self._patterns.values():
            if pattern.error_category in correction.description.lower():
                if successful:
                    pattern.success_count += 1
                    # Update confidence based on success rate
                    total = pattern.success_count + pattern.failure_count
                    pattern.confidence = pattern.success_count / total

                    # Store example
                    if actual_fix and len(pattern.examples) < 10:
                        pattern.examples.append({
                            "error": correction.description,
                            "fix": actual_fix,
                        })
                else:
                    pattern.failure_count += 1

                break

    def get_correction_patterns(self) -> List[Dict[str, Any]]:
        """Get all correction patterns."""
        return [p.to_dict() for p in self._patterns.values()]

    def add_custom_pattern(
        self,
        error_category: str,
        detection_pattern: str,
        fix_template: str,
        confidence: float = 0.5,
    ) -> str:
        """
        Add a custom correction pattern.

        Args:
            error_category: Category of errors this fixes
            detection_pattern: Regex to detect the error
            fix_template: Template for the fix
            confidence: Initial confidence level

        Returns:
            Pattern ID
        """
        import uuid
        pattern_id = f"custom_{uuid.uuid4().hex[:8]}"

        pattern = CorrectionPattern(
            pattern_id=pattern_id,
            error_category=error_category,
            detection_pattern=detection_pattern,
            fix_template=fix_template,
            confidence=confidence,
        )

        self._patterns[pattern_id] = pattern
        return pattern_id

    def get_correction_history(
        self,
        error_id: Optional[str] = None,
        successful_only: bool = False,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Get correction history.

        Args:
            error_id: Filter by error ID
            successful_only: Only return successful corrections
            limit: Maximum number of results

        Returns:
            List of correction records
        """
        corrections = self._corrections

        if error_id:
            corrections = [c for c in corrections if c.error_id == error_id]
        if successful_only:
            corrections = [c for c in corrections if c.successful]

        return [c.to_dict() for c in corrections[-limit:]]

    def get_stats(self) -> Dict[str, Any]:
        """Get corrector statistics."""
        total = len(self._corrections)
        applied = sum(1 for c in self._corrections if c.applied)
        successful = sum(1 for c in self._corrections if c.successful)

        return {
            "total_corrections": total,
            "applied": applied,
            "successful": successful,
            "success_rate": successful / max(1, applied),
            "patterns_count": len(self._patterns),
            "avg_confidence": sum(c.confidence for c in self._corrections) / max(1, total),
        }

    def get_most_effective_patterns(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the most effective correction patterns."""
        patterns = sorted(
            self._patterns.values(),
            key=lambda x: -x.confidence
        )
        return [p.to_dict() for p in patterns[:limit]]

    def clear_history(self) -> None:
        """Clear correction history."""
        self._corrections.clear()


class AutomatedFixer:
    """
    Automated fix application system.

    Attempts to automatically apply fixes based on learned patterns.
    """

    def __init__(self, corrector: ErrorCorrector):
        """
        Initialize the AutomatedFixer.

        Args:
            corrector: ErrorCorrector instance
        """
        self.corrector = corrector
        self._fix_handlers: Dict[str, Callable] = {}
        self._register_default_handlers()

    def _register_default_handlers(self) -> None:
        """Register default fix handlers."""
        self._fix_handlers = {
            "indentation_error": self._fix_indentation,
            "name_error": self._fix_name_error,
            "zero_division_error": self._fix_zero_division,
        }

    def register_handler(
        self,
        error_category: str,
        handler: Callable[[str, Dict], Tuple[str, bool]],
    ) -> None:
        """
        Register a custom fix handler.

        Args:
            error_category: Category of errors to handle
            handler: Function that takes (code, context) and returns (fixed_code, success)
        """
        self._fix_handlers[error_category] = handler

    def attempt_fix(
        self,
        code: str,
        error: ClassifiedError,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, bool, str]:
        """
        Attempt to automatically fix an error.

        Args:
            code: The code with the error
            error: The classified error
            context: Optional context for the fix

        Returns:
            Tuple of (fixed_code, success, message)
        """
        handler = self._fix_handlers.get(error.category)
        
        if handler:
            try:
                fixed_code, success = handler(code, context or {})
                if success:
                    return fixed_code, True, "Fix applied successfully"
                else:
                    return code, False, "Could not apply automatic fix"
            except Exception as e:
                return code, False, f"Fix handler error: {e}"

        return code, False, f"No automatic fix available for {error.category}"

    def _fix_indentation(
        self,
        code: str,
        context: Dict,
    ) -> Tuple[str, bool]:
        """Attempt to fix indentation issues."""
        lines = code.split("\n")
        fixed_lines = []
        
        for line in lines:
            # Replace tabs with spaces
            if "\t" in line:
                line = line.replace("\t", "    ")
            fixed_lines.append(line)

        return "\n".join(fixed_lines), True

    def _fix_name_error(
        self,
        code: str,
        context: Dict,
    ) -> Tuple[str, bool]:
        """Attempt to fix name errors."""
        # This would need more sophisticated implementation
        # For now, return unchanged
        return code, False

    def _fix_zero_division(
        self,
        code: str,
        context: Dict,
    ) -> Tuple[str, bool]:
        """Attempt to fix division by zero."""
        # This would need AST manipulation
        # For now, return unchanged
        return code, False
