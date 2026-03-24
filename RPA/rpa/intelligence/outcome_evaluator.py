"""
Outcome Evaluator - Unified outcome scoring for closed-loop learning.

This is the foundation of the closed-loop intelligence engine. It unifies:
- ErrorClassifier: Error categorization
- Validator: Pattern validation
- Sandbox execution results
- User feedback

Into a single Outcome type that drives all downstream learning.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set
import uuid
import logging

from rpa.learning.error_classifier import ErrorClassifier, ClassifiedError
from rpa.validation.validator import Validator, ValidationResult
from rpa.core.graph import Node, PatternGraph

logger = logging.getLogger(__name__)


class OutcomeType(Enum):
    """Types of outcomes from pattern application."""
    SUCCESS = "success"           # Pattern worked correctly
    FAILURE = "failure"           # Pattern produced an error
    PARTIAL = "partial"           # Pattern worked but with issues
    GAP = "gap"                   # Missing knowledge detected
    TIMEOUT = "timeout"           # Execution timed out
    INVALID = "invalid"           # Pattern structure is invalid
    UNCERTAIN = "uncertain"       # Not enough information to judge


@dataclass
class Outcome:
    """
    Represents the outcome of a pattern application.

    This is the core feedback signal that drives learning.
    """
    outcome_id: str
    outcome_type: OutcomeType
    pattern_id: str
    domain: str

    # Core metrics
    success_score: float = 0.0       # 0.0 = complete failure, 1.0 = perfect success
    confidence: float = 0.0          # How confident in this assessment

    # Context
    input_context: Optional[str] = None
    output_context: Optional[str] = None
    error_details: Optional[ClassifiedError] = None
    validation_result: Optional[ValidationResult] = None

    # Learning signals
    learning_value: float = 0.0      # How much can be learned from this outcome
    should_mutate: bool = False      # Should pattern be mutated?
    should_deprecate: bool = False   # Should pattern be deprecated?
    retry_recommended: bool = False  # Should we try again?

    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = "execution"        # execution, user_feedback, self_assessment
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Linked outcomes (for retry chains)
    parent_outcome_id: Optional[str] = None
    retry_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "outcome_id": self.outcome_id,
            "outcome_type": self.outcome_type.value,
            "pattern_id": self.pattern_id,
            "domain": self.domain,
            "success_score": self.success_score,
            "confidence": self.confidence,
            "input_context": self.input_context[:200] if self.input_context else None,
            "output_context": self.output_context[:200] if self.output_context else None,
            "error_details": self.error_details.to_dict() if self.error_details else None,
            "learning_value": self.learning_value,
            "should_mutate": self.should_mutate,
            "should_deprecate": self.should_deprecate,
            "retry_recommended": self.retry_recommended,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "metadata": self.metadata,
            "parent_outcome_id": self.parent_outcome_id,
            "retry_count": self.retry_count,
        }


class OutcomeEvaluator:
    """
    Unified outcome evaluation system.

    Evaluates pattern applications and produces standardized outcomes
    that drive the closed-loop learning process.

    Sources of feedback:
    1. Sandbox execution results (pass/fail/error)
    2. Error classification (syntax/runtime/logic/semantic)
    3. Pattern validation (structural integrity)
    4. User explicit feedback (rating/correction)
    5. Self-assessment (internal quality checks)

    Example:
        evaluator = OutcomeEvaluator()

        # From sandbox execution
        outcome = evaluator.evaluate_execution(
            pattern=node,
            code_result=sandbox_result,
            expected_output="expected"
        )

        # From user feedback
        outcome = evaluator.evaluate_feedback(
            pattern=node,
            user_rating=0.8,
            user_comment="Works but slow"
        )
    """

    # Thresholds for decision making
    SUCCESS_THRESHOLD = 0.8
    PARTIAL_THRESHOLD = 0.5
    DEPRECATION_THRESHOLD = 0.2
    HIGH_LEARNING_VALUE_THRESHOLD = 0.7

    def __init__(
        self,
        error_classifier: Optional[ErrorClassifier] = None,
        validator: Optional[Validator] = None
    ):
        """
        Initialize the OutcomeEvaluator.

        Args:
            error_classifier: Optional ErrorClassifier instance
            validator: Optional Validator instance
        """
        self.error_classifier = error_classifier or ErrorClassifier()
        self.validator = validator or Validator()

        # Outcome history
        self._outcomes: Dict[str, Outcome] = {}
        self._pattern_outcomes: Dict[str, List[str]] = {}  # pattern_id -> outcome_ids
        self._max_history = 1000

        # Statistics
        self._stats = {
            "total_evaluations": 0,
            "by_type": {t.value: 0 for t in OutcomeType},
            "mutations_triggered": 0,
            "deprecations_triggered": 0,
        }

    def evaluate_execution(
        self,
        pattern: Node,
        execution_result: Dict[str, Any],
        expected_output: Optional[str] = None,
        input_context: Optional[str] = None,
    ) -> Outcome:
        """
        Evaluate a pattern based on sandbox execution result.

        Args:
            pattern: The pattern node that was applied
            execution_result: Result from CodeSandbox
                - success: bool
                - output: str
                - error: Optional[str]
                - execution_time: float
            expected_output: Expected output for comparison
            input_context: The input that was processed

        Returns:
            Outcome with evaluation results
        """
        outcome_id = f"outcome_{uuid.uuid4().hex[:8]}"
        success = execution_result.get("success", False)
        output = execution_result.get("output", "")
        error = execution_result.get("error")
        execution_time = execution_result.get("execution_time", 0)

        # Determine base outcome type
        if success:
            # Check if output matches expected
            if expected_output:
                match_score = self._calculate_match_score(output, expected_output)
                if match_score >= self.SUCCESS_THRESHOLD:
                    outcome_type = OutcomeType.SUCCESS
                    success_score = match_score
                elif match_score >= self.PARTIAL_THRESHOLD:
                    outcome_type = OutcomeType.PARTIAL
                    success_score = match_score
                else:
                    outcome_type = OutcomeType.FAILURE
                    success_score = match_score
            else:
                outcome_type = OutcomeType.SUCCESS
                success_score = 1.0
        else:
            outcome_type = OutcomeType.FAILURE
            success_score = 0.0

        # Classify error if present
        classified_error = None
        if error:
            classified_error = self.error_classifier.classify(
                error_message=error,
                code_context=pattern.content,
            )

        # Calculate learning value
        learning_value = self._calculate_learning_value(
            outcome_type,
            classified_error,
            success_score
        )

        # Determine actions
        should_mutate = self._should_mutate(outcome_type, classified_error, success_score)
        should_deprecate = self._should_deprecate(outcome_type, success_score)
        retry_recommended = self._should_retry(outcome_type, classified_error)

        # Create outcome
        outcome = Outcome(
            outcome_id=outcome_id,
            outcome_type=outcome_type,
            pattern_id=pattern.node_id,
            domain=pattern.domain,
            success_score=success_score,
            confidence=self._calculate_confidence(execution_result, expected_output),
            input_context=input_context,
            output_context=output[:500] if output else None,
            error_details=classified_error,
            learning_value=learning_value,
            should_mutate=should_mutate,
            should_deprecate=should_deprecate,
            retry_recommended=retry_recommended,
            source="execution",
            metadata={
                "execution_time": execution_time,
                "expected_output": expected_output[:100] if expected_output else None,
            }
        )

        # Record outcome
        self._record_outcome(outcome)

        logger.info(
            f"Evaluated pattern {pattern.node_id}: {outcome_type.value} "
            f"(score={success_score:.2f}, learn={learning_value:.2f})"
        )

        return outcome

    def evaluate_validation(
        self,
        pattern: Node,
        graph: PatternGraph,
    ) -> Outcome:
        """
        Evaluate a pattern based on structural validation.

        Args:
            pattern: The pattern node to validate
            graph: The pattern graph containing related nodes

        Returns:
            Outcome with validation results
        """
        outcome_id = f"outcome_{uuid.uuid4().hex[:8]}"

        # Run validation
        validation_result = self.validator.validate_pattern_structure(pattern, graph)

        # Determine outcome type
        if validation_result.is_valid:
            outcome_type = OutcomeType.SUCCESS
            success_score = 1.0
        elif validation_result.missing_references:
            outcome_type = OutcomeType.GAP
            success_score = 0.3
        elif validation_result.circular_deps:
            outcome_type = OutcomeType.INVALID
            success_score = 0.0
        else:
            outcome_type = OutcomeType.PARTIAL
            success_score = 0.5

        # Calculate learning value (validation issues are high learning value)
        learning_value = 0.8 if not validation_result.is_valid else 0.2

        outcome = Outcome(
            outcome_id=outcome_id,
            outcome_type=outcome_type,
            pattern_id=pattern.node_id,
            domain=pattern.domain,
            success_score=success_score,
            confidence=0.9,  # High confidence in validation
            validation_result=validation_result,
            learning_value=learning_value,
            should_mutate=not validation_result.is_valid and len(validation_result.structural_issues) > 0,
            should_deprecate=len(validation_result.circular_deps) > 0,
            retry_recommended=len(validation_result.missing_references) > 0,
            source="validation",
            metadata={
                "issues": [issue["issue_type"] for issue in validation_result.structural_issues],
                "missing_refs": validation_result.missing_references,
            }
        )

        self._record_outcome(outcome)
        return outcome

    def evaluate_feedback(
        self,
        pattern: Node,
        user_rating: float,
        user_comment: Optional[str] = None,
        correction: Optional[str] = None,
    ) -> Outcome:
        """
        Evaluate a pattern based on explicit user feedback.

        Args:
            pattern: The pattern being rated
            user_rating: User's rating (0.0 to 1.0)
            user_comment: Optional comment
            correction: Optional corrected code/content

        Returns:
            Outcome with user feedback
        """
        outcome_id = f"outcome_{uuid.uuid4().hex[:8]}"

        # Determine outcome type from rating
        if user_rating >= self.SUCCESS_THRESHOLD:
            outcome_type = OutcomeType.SUCCESS
        elif user_rating >= self.PARTIAL_THRESHOLD:
            outcome_type = OutcomeType.PARTIAL
        elif user_rating >= self.DEPRECATION_THRESHOLD:
            outcome_type = OutcomeType.FAILURE
        else:
            outcome_type = OutcomeType.INVALID

        # User feedback is high learning value
        learning_value = 0.9 if correction else 0.7

        outcome = Outcome(
            outcome_id=outcome_id,
            outcome_type=outcome_type,
            pattern_id=pattern.node_id,
            domain=pattern.domain,
            success_score=user_rating,
            confidence=1.0,  # User feedback is definitive
            learning_value=learning_value,
            should_mutate=user_rating < self.SUCCESS_THRESHOLD and bool(correction),
            should_deprecate=user_rating < self.DEPRECATION_THRESHOLD,
            retry_recommended=False,  # User already provided feedback
            source="user_feedback",
            metadata={
                "user_comment": user_comment,
                "correction_provided": bool(correction),
            }
        )

        self._record_outcome(outcome)
        return outcome

    def evaluate_gap_detection(
        self,
        pattern: Node,
        gap_description: str,
        missing_knowledge: List[str],
    ) -> Outcome:
        """
        Evaluate a pattern that triggered a gap detection.

        Args:
            pattern: The pattern that revealed the gap
            gap_description: Description of the knowledge gap
            missing_knowledge: List of missing knowledge items

        Returns:
            Outcome indicating knowledge gap
        """
        outcome_id = f"outcome_{uuid.uuid4().hex[:8]}"

        outcome = Outcome(
            outcome_id=outcome_id,
            outcome_type=OutcomeType.GAP,
            pattern_id=pattern.node_id,
            domain=pattern.domain,
            success_score=0.0,  # Gap means pattern was insufficient
            confidence=0.8,
            learning_value=0.9,  # Gaps are high learning value
            should_mutate=True,
            should_deprecate=False,
            retry_recommended=False,  # Need new knowledge first
            source="gap_detection",
            metadata={
                "gap_description": gap_description,
                "missing_knowledge": missing_knowledge,
            }
        )

        self._record_outcome(outcome)
        return outcome

    def get_pattern_outcomes(
        self,
        pattern_id: str,
        limit: int = 10
    ) -> List[Outcome]:
        """
        Get recent outcomes for a pattern.

        Args:
            pattern_id: The pattern ID
            limit: Maximum number of outcomes to return

        Returns:
            List of outcomes, most recent first
        """
        outcome_ids = self._pattern_outcomes.get(pattern_id, [])
        outcomes = [
            self._outcomes[oid]
            for oid in outcome_ids[-limit:]
            if oid in self._outcomes
        ]
        return list(reversed(outcomes))

    def get_pattern_success_rate(self, pattern_id: str) -> float:
        """
        Calculate success rate for a pattern.

        Args:
            pattern_id: The pattern ID

        Returns:
            Success rate (0.0 to 1.0)
        """
        outcomes = self.get_pattern_outcomes(pattern_id, limit=100)
        if not outcomes:
            return 0.5  # No data, assume neutral

        scores = [o.success_score for o in outcomes]
        return sum(scores) / len(scores)

    def get_learning_candidates(self) -> List[str]:
        """
        Get pattern IDs that should be prioritized for learning.

        Returns:
            List of pattern IDs with high learning value outcomes
        """
        candidates = []

        for pattern_id, outcome_ids in self._pattern_outcomes.items():
            recent_outcomes = [
                self._outcomes[oid]
                for oid in outcome_ids[-5:]
                if oid in self._outcomes
            ]

            # Check if any recent outcomes have high learning value
            if any(o.learning_value >= self.HIGH_LEARNING_VALUE_THRESHOLD for o in recent_outcomes):
                candidates.append(pattern_id)

        return candidates

    def get_stats(self) -> Dict[str, Any]:
        """Get evaluator statistics."""
        return {
            **self._stats,
            "total_outcomes": len(self._outcomes),
            "patterns_with_outcomes": len(self._pattern_outcomes),
        }

    def _calculate_match_score(self, actual: str, expected: str) -> float:
        """Calculate how well actual matches expected."""
        if not actual or not expected:
            return 0.0

        # Normalize for comparison
        actual_norm = actual.strip().lower()
        expected_norm = expected.strip().lower()

        # Exact match
        if actual_norm == expected_norm:
            return 1.0

        # Contains expected
        if expected_norm in actual_norm:
            return 0.8

        # Calculate word overlap
        actual_words = set(actual_norm.split())
        expected_words = set(expected_norm.split())

        if not expected_words:
            return 0.0

        overlap = len(actual_words & expected_words)
        return overlap / len(expected_words)

    def _calculate_learning_value(
        self,
        outcome_type: OutcomeType,
        error: Optional[ClassifiedError],
        success_score: float
    ) -> float:
        """Calculate how much can be learned from this outcome."""
        # Failures have high learning value
        if outcome_type == OutcomeType.FAILURE:
            base = 0.7
            # Higher if we have good error classification
            if error and error.learning_value:
                base = min(1.0, base + error.learning_value * 0.3)
            return base

        # Partial successes are valuable
        if outcome_type == OutcomeType.PARTIAL:
            return 0.6

        # Successes have lower learning value (we already know it works)
        if outcome_type == OutcomeType.SUCCESS:
            return 0.2

        # Gaps are very valuable
        if outcome_type == OutcomeType.GAP:
            return 0.9

        return 0.5

    def _should_mutate(
        self,
        outcome_type: OutcomeType,
        error: Optional[ClassifiedError],
        success_score: float
    ) -> bool:
        """Determine if pattern should be mutated."""
        if outcome_type == OutcomeType.SUCCESS:
            return False

        if outcome_type == OutcomeType.FAILURE:
            # Mutate if we have useful error info
            if error and error.learning_value >= 0.6:
                return True

        if success_score < self.PARTIAL_THRESHOLD:
            return True

        return False

    def _should_deprecate(self, outcome_type: OutcomeType, success_score: float) -> bool:
        """Determine if pattern should be deprecated."""
        return outcome_type == OutcomeType.INVALID or success_score < self.DEPRECATION_THRESHOLD

    def _should_retry(
        self,
        outcome_type: OutcomeType,
        error: Optional[ClassifiedError]
    ) -> bool:
        """Determine if a retry might succeed."""
        if outcome_type == OutcomeType.SUCCESS:
            return False

        # Retry on certain error types
        if error:
            # Transient errors
            if error.category in ["timeout", "memory_error", "recursion_error"]:
                return True
            # Fixable errors
            if error.category in ["index_error", "key_error", "value_error"]:
                return True

        return outcome_type in [OutcomeType.PARTIAL, OutcomeType.FAILURE]

    def _calculate_confidence(
        self,
        execution_result: Dict[str, Any],
        expected_output: Optional[str]
    ) -> float:
        """Calculate confidence in the evaluation."""
        base_confidence = 0.7

        # Higher confidence if we have expected output
        if expected_output:
            base_confidence += 0.2

        # Lower confidence if execution had issues
        if execution_result.get("timeout", False):
            base_confidence -= 0.2

        return min(1.0, max(0.0, base_confidence))

    def _record_outcome(self, outcome: Outcome) -> None:
        """Record an outcome in history."""
        # Store outcome
        self._outcomes[outcome.outcome_id] = outcome

        # Link to pattern
        if outcome.pattern_id not in self._pattern_outcomes:
            self._pattern_outcomes[outcome.pattern_id] = []
        self._pattern_outcomes[outcome.pattern_id].append(outcome.outcome_id)

        # Update stats
        self._stats["total_evaluations"] += 1
        self._stats["by_type"][outcome.outcome_type.value] += 1

        if outcome.should_mutate:
            self._stats["mutations_triggered"] += 1
        if outcome.should_deprecate:
            self._stats["deprecations_triggered"] += 1

        # Trim history if needed
        if len(self._outcomes) > self._max_history:
            self._trim_history()

    def _trim_history(self) -> None:
        """Trim old outcomes from history."""
        # Remove oldest outcomes
        sorted_ids = sorted(
            self._outcomes.keys(),
            key=lambda x: self._outcomes[x].timestamp
        )

        to_remove = sorted_ids[:-self._max_history]
        for oid in to_remove:
            del self._outcomes[oid]

            # Remove from pattern index
            for pattern_id in list(self._pattern_outcomes.keys()):
                if oid in self._pattern_outcomes[pattern_id]:
                    self._pattern_outcomes[pattern_id].remove(oid)
                if not self._pattern_outcomes[pattern_id]:
                    del self._pattern_outcomes[pattern_id]
