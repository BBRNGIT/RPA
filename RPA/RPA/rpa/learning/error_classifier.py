"""
ErrorClassifier - Categorizes and analyzes errors for RPA learning.

Provides intelligent error classification to help the system learn from mistakes:
- Error categorization (syntax, runtime, logic, semantic)
- Severity assessment
- Pattern recognition in errors
- Learning insights extraction
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import re
import logging

logger = logging.getLogger(__name__)


@dataclass
class ClassifiedError:
    """Represents a classified error."""
    error_id: str
    error_type: str  # syntax, runtime, logic, semantic
    category: str    # Specific category within type
    message: str
    severity: str    # critical, high, medium, low
    line_number: Optional[int] = None
    column: Optional[int] = None
    context: Optional[str] = None
    suggestions: List[str] = field(default_factory=list)
    related_patterns: List[str] = field(default_factory=list)
    learning_value: float = 0.0  # 0.0-1.0, how much can be learned
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "error_id": self.error_id,
            "error_type": self.error_type,
            "category": self.category,
            "message": self.message,
            "severity": self.severity,
            "line_number": self.line_number,
            "column": self.column,
            "context": self.context,
            "suggestions": self.suggestions,
            "related_patterns": self.related_patterns,
            "learning_value": self.learning_value,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class ErrorPattern:
    """Represents a pattern in errors."""
    pattern_id: str
    pattern_type: str
    description: str
    occurrence_count: int = 0
    first_seen: datetime = field(default_factory=datetime.now)
    last_seen: datetime = field(default_factory=datetime.now)
    example_errors: List[str] = field(default_factory=list)
    solutions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "pattern_id": self.pattern_id,
            "pattern_type": self.pattern_type,
            "description": self.description,
            "occurrence_count": self.occurrence_count,
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "example_errors": self.example_errors[:5],
            "solutions": self.solutions,
        }


class ErrorClassifier:
    """
    Intelligent error classification system.

    Categorizes errors into meaningful types and extracts learning insights.
    """

    # Error type hierarchy
    ERROR_TYPES = {
        "syntax": [
            "indentation_error",
            "name_error",
            "syntax_error",
            "tab_error",
        ],
        "runtime": [
            "type_error",
            "value_error",
            "index_error",
            "key_error",
            "attribute_error",
            "zero_division_error",
            "overflow_error",
            "recursion_error",
            "memory_error",
        ],
        "logic": [
            "infinite_loop",
            "off_by_one",
            "wrong_operator",
            "missing_condition",
            "incorrect_bound",
        ],
        "semantic": [
            "misunderstanding",
            "wrong_concept",
            "incomplete_pattern",
            "context_error",
        ],
    }

    # Common error patterns and their fixes
    ERROR_PATTERNS = {
        # Python-specific patterns
        r"NameError: name '(\w+)' is not defined": {
            "category": "name_error",
            "suggestions": [
                "Check if the variable is defined before use",
                "Check for typos in variable name",
                "Ensure proper scope for the variable",
            ],
            "learning_value": 0.8,
        },
        r"TypeError: (.+) object is not (?:callable|subscriptable|iterable)": {
            "category": "type_error",
            "suggestions": [
                "Check the type of the object",
                "Ensure proper type conversion",
                "Verify the operation is valid for this type",
            ],
            "learning_value": 0.7,
        },
        r"IndexError: (?:list|tuple|string) index out of range": {
            "category": "index_error",
            "suggestions": [
                "Check the length before accessing",
                "Verify the index is within bounds",
                "Consider using negative indexing for end elements",
            ],
            "learning_value": 0.9,
        },
        r"KeyError: '?(\w+)?'?$": {
            "category": "key_error",
            "suggestions": [
                "Check if the key exists using 'in'",
                "Use .get() method with default value",
                "Verify the dictionary content",
            ],
            "learning_value": 0.8,
        },
        r"AttributeError: '(\w+)' object has no attribute '(\w+)'": {
            "category": "attribute_error",
            "suggestions": [
                "Check available attributes of the object",
                "Verify the object type",
                "Check for typos in attribute name",
            ],
            "learning_value": 0.7,
        },
        r"IndentationError: (.+)": {
            "category": "indentation_error",
            "suggestions": [
                "Check indentation consistency",
                "Use consistent spaces or tabs",
                "Verify block structure",
            ],
            "learning_value": 0.5,
        },
        r"ZeroDivisionError": {
            "category": "zero_division_error",
            "suggestions": [
                "Check divisor before division",
                "Add zero-check condition",
                "Handle edge case explicitly",
            ],
            "learning_value": 0.9,
        },
        r"ValueError: (.+)": {
            "category": "value_error",
            "suggestions": [
                "Validate input values",
                "Check expected value range",
                "Add value validation",
            ],
            "learning_value": 0.8,
        },
        r"RecursionError: maximum recursion depth exceeded": {
            "category": "recursion_error",
            "suggestions": [
                "Add base case to recursion",
                "Check for infinite recursion",
                "Consider iterative approach",
            ],
            "learning_value": 0.9,
        },
        r"SyntaxError: (.+)": {
            "category": "syntax_error",
            "suggestions": [
                "Check syntax at indicated line",
                "Verify parentheses/brackets matching",
                "Check for missing colons",
            ],
            "learning_value": 0.6,
        },
    }

    # Severity mapping
    SEVERITY_MAP = {
        "syntax_error": "high",
        "indentation_error": "medium",
        "name_error": "high",
        "type_error": "high",
        "value_error": "medium",
        "index_error": "medium",
        "key_error": "medium",
        "attribute_error": "medium",
        "zero_division_error": "high",
        "recursion_error": "critical",
        "memory_error": "critical",
        "infinite_loop": "critical",
        "off_by_one": "low",
        "wrong_operator": "medium",
        "misunderstanding": "medium",
        "wrong_concept": "high",
    }

    def __init__(self):
        """Initialize the ErrorClassifier."""
        self._patterns: Dict[str, ErrorPattern] = {}
        self._error_history: List[ClassifiedError] = []
        self._max_history = 500

    def classify(
        self,
        error_message: str,
        error_type: Optional[str] = None,
        code_context: Optional[str] = None,
        line_number: Optional[int] = None,
    ) -> ClassifiedError:
        """
        Classify an error.

        Args:
            error_message: The error message
            error_type: Optional known error type (from exception)
            code_context: Optional code that caused the error
            line_number: Optional line number where error occurred

        Returns:
            ClassifiedError with detailed classification
        """
        import uuid
        error_id = str(uuid.uuid4())[:8]

        # Determine error type and category
        detected_type, category = self._detect_error_type(error_message, error_type)
        
        # Get severity
        severity = self.SEVERITY_MAP.get(category, "medium")

        # Find matching pattern
        pattern_info = self._match_error_pattern(error_message)
        
        # Extract suggestions
        suggestions = pattern_info.get("suggestions", []) if pattern_info else []
        learning_value = pattern_info.get("learning_value", 0.5) if pattern_info else 0.5

        # Add generic suggestions if none found
        if not suggestions:
            suggestions = self._generate_generic_suggestions(category)

        # Create classified error
        classified = ClassifiedError(
            error_id=error_id,
            error_type=detected_type,
            category=category,
            message=error_message,
            severity=severity,
            line_number=line_number,
            context=code_context[:200] if code_context else None,
            suggestions=suggestions,
            learning_value=learning_value,
        )

        # Store in history
        self._error_history.append(classified)
        if len(self._error_history) > self._max_history:
            self._error_history.pop(0)

        # Update patterns
        self._update_patterns(classified)

        return classified

    def _detect_error_type(
        self,
        error_message: str,
        known_type: Optional[str] = None
    ) -> Tuple[str, str]:
        """Detect the error type and category."""
        message_lower = error_message.lower()

        # Check each error type
        for err_type, categories in self.ERROR_TYPES.items():
            for category in categories:
                if category.replace("_", " ") in message_lower:
                    return err_type, category
                if category.replace("_", "") in message_lower.replace(" ", ""):
                    return err_type, category

        # Check known type
        if known_type:
            known_lower = known_type.lower().replace("error", "")
            for err_type, categories in self.ERROR_TYPES.items():
                for category in categories:
                    if known_lower in category:
                        return err_type, category

        # Default classification
        return "runtime", "unknown_error"

    def _match_error_pattern(self, error_message: str) -> Optional[Dict[str, Any]]:
        """Match error against known patterns."""
        for pattern, info in self.ERROR_PATTERNS.items():
            if re.search(pattern, error_message, re.IGNORECASE):
                return info
        return None

    def _generate_generic_suggestions(self, category: str) -> List[str]:
        """Generate generic suggestions for unknown errors."""
        generic = {
            "syntax_error": ["Check syntax and punctuation"],
            "runtime_error": ["Check for runtime conditions"],
            "type_error": ["Verify types of operands"],
            "value_error": ["Check value ranges and validity"],
            "unknown_error": ["Analyze the error message for clues"],
        }
        return generic.get(category, ["Debug the code step by step"])

    def _update_patterns(self, error: ClassifiedError) -> None:
        """Update error patterns with new error."""
        pattern_key = f"{error.error_type}:{error.category}"
        
        if pattern_key not in self._patterns:
            self._patterns[pattern_key] = ErrorPattern(
                pattern_id=pattern_key,
                pattern_type=error.error_type,
                description=f"Pattern of {error.category} errors",
            )

        pattern = self._patterns[pattern_key]
        pattern.occurrence_count += 1
        pattern.last_seen = datetime.now()
        
        if error.message not in pattern.example_errors:
            pattern.example_errors.append(error.message)

    def get_error_patterns(self) -> List[Dict[str, Any]]:
        """Get all detected error patterns."""
        return [p.to_dict() for p in self._patterns.values()]

    def get_common_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most common error types."""
        patterns = sorted(
            self._patterns.values(),
            key=lambda x: -x.occurrence_count
        )
        return [p.to_dict() for p in patterns[:limit]]

    def get_learning_insights(self) -> Dict[str, Any]:
        """Get insights about errors for learning."""
        if not self._error_history:
            return {"total_errors": 0, "insights": []}

        # Group by type
        by_type: Dict[str, int] = {}
        by_category: Dict[str, int] = {}
        high_learning_value: List[Dict] = []

        for error in self._error_history:
            by_type[error.error_type] = by_type.get(error.error_type, 0) + 1
            by_category[error.category] = by_category.get(error.category, 0) + 1
            if error.learning_value >= 0.8:
                high_learning_value.append(error.to_dict())

        # Generate insights
        insights = []
        
        # Most common error type
        if by_type:
            most_common_type = max(by_type.items(), key=lambda x: x[1])
            insights.append({
                "type": "common_error_type",
                "message": f"Most common error type: {most_common_type[0]} ({most_common_type[1]} occurrences)",
                "recommendation": f"Focus learning on preventing {most_common_type[0]} errors",
            })

        # High learning value errors
        if high_learning_value:
            insights.append({
                "type": "high_value_learning",
                "message": f"{len(high_learning_value)} errors have high learning value",
                "recommendation": "Review these errors for pattern improvement",
            })

        return {
            "total_errors": len(self._error_history),
            "by_type": by_type,
            "by_category": by_category,
            "high_learning_value_count": len(high_learning_value),
            "insights": insights,
        }

    def suggest_fix(self, error: ClassifiedError) -> Dict[str, Any]:
        """
        Suggest a fix for a classified error.

        Args:
            error: The classified error

        Returns:
            Fix suggestion with details
        """
        suggestions = {
            "error_id": error.error_id,
            "category": error.category,
            "fixes": error.suggestions,
            "difficulty": self._estimate_fix_difficulty(error),
            "priority": self._calculate_fix_priority(error),
        }

        # Add pattern-based solutions if available
        pattern_key = f"{error.error_type}:{error.category}"
        if pattern_key in self._patterns:
            pattern = self._patterns[pattern_key]
            if pattern.solutions:
                suggestions["proven_solutions"] = pattern.solutions

        return suggestions

    def _estimate_fix_difficulty(self, error: ClassifiedError) -> str:
        """Estimate the difficulty of fixing an error."""
        severity_weights = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        type_weights = {"syntax": 1, "runtime": 2, "logic": 3, "semantic": 4}

        severity_score = severity_weights.get(error.severity, 2)
        type_score = type_weights.get(error.error_type, 2)

        total = severity_score + type_score

        if total <= 3:
            return "easy"
        elif total <= 5:
            return "medium"
        elif total <= 7:
            return "hard"
        else:
            return "very_hard"

    def _calculate_fix_priority(self, error: ClassifiedError) -> str:
        """Calculate the priority of fixing an error."""
        if error.severity == "critical":
            return "immediate"
        elif error.severity == "high":
            return "high"
        elif error.learning_value >= 0.8:
            return "high"
        elif error.severity == "medium":
            return "medium"
        else:
            return "low"

    def record_solution(
        self,
        error_category: str,
        solution: str,
        successful: bool = True
    ) -> None:
        """
        Record a solution that was applied to fix an error.

        Args:
            error_category: The error category
            solution: The solution that was applied
            successful: Whether the solution worked
        """
        for pattern in self._patterns.values():
            if pattern.pattern_type in error_category or error_category in pattern.pattern_id:
                if successful and solution not in pattern.solutions:
                    pattern.solutions.append(solution)

    def get_stats(self) -> Dict[str, Any]:
        """Get classifier statistics."""
        return {
            "total_errors_classified": len(self._error_history),
            "unique_patterns": len(self._patterns),
            "by_severity": self._count_by_field("severity"),
            "by_type": self._count_by_field("error_type"),
            "by_category": self._count_by_field("category"),
        }

    def _count_by_field(self, field: str) -> Dict[str, int]:
        """Count errors by a specific field."""
        counts: Dict[str, int] = {}
        for error in self._error_history:
            value = getattr(error, field, "unknown")
            counts[value] = counts.get(value, 0) + 1
        return counts

    def clear_history(self) -> None:
        """Clear error history."""
        self._error_history.clear()
        self._patterns.clear()
