"""
Outcome Evaluator - Unified outcome classification for RPA.

Classifies every action result into a unified outcome type:
- SUCCESS: Action completed correctly
- FAILURE: Action failed with error
- GAP: Missing knowledge detected
- PARTIAL: Partially successful, needs refinement

Integrates with:
- ErrorClassifier (runtime errors)
- Validator (structural issues)
- SelfAssessmentEngine (learning quality)
- Sandbox execution results
- User explicit ratings
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid
import logging

from rpa.learning.error_classifier import ErrorClassifier, ClassifiedError
from rpa.validation.validator import Validator, ValidationResult
from rpa.core.graph import Node, PatternGraph

logger = logging.getLogger(__name__)


class OutcomeType(Enum):
    """Types of outcomes from pattern usage."""
    SUCCESS = "success"           # Pattern worked correctly
    FAILURE = "failure"           # Pattern failed with error
    GAP = "gap"                   # Missing knowledge detected
    PARTIAL = "partial"           # Partially successful
    DEPRECATED = "deprecated"     # Pattern marked as deprecated
    UNCERTAIN = "uncertain"       # Result uncertain, needs review


@dataclass
class OutcomeRecord:
    """Record of an outcome from using a pattern."""
    record_id: str
    pattern_id: str
    outcome_type: OutcomeType
    confidence: float  # 0.0 - 1.0
    context: str  # What was being attempted
    source: str  # "sandbox", "user", "self_assessment", "validation"
    timestamp: datetime = field(default_factory=datetime.now)
    error_info: Optional[Dict[str, Any]] = None
    validation_info: Optional[Dict[str, Any]] = None
    assessment_info: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "record_id": self.record_id,
            "pattern_id": self.pattern_id,
            "outcome_type": self.outcome_type.value,
            "confidence": self.confidence,
            "context": self.context,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "error_info": self.error_info,
            "validation_info": self.validation_info,
            "assessment_info": self.assessment_info,
            "metadata": self.metadata,
        }


@dataclass
class Outcome:
    """
    Unified outcome from pattern usage.

    Combines signals from multiple sources to determine
    the overall outcome of using a pattern.
    """
    pattern_id: str
    outcome_type: OutcomeType
    confidence: float
    sources: List[str]  # Which sources contributed
    should_reinforce: bool  # Should this pattern be reinforced?
    needs_mutation: bool  # Does pattern need mutation?
    needs_deprecation: bool  # Should pattern be deprecated?
    failure_count: int = 0
    success_count: int = 0
    gap_detected: bool = False
    suggestions: List[str] = field(default_factory=list)
    records: List[OutcomeRecord] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "pattern_id": self.pattern_id,
            "outcome_type": self.outcome_type.value,
            "confidence": self.confidence,
            "sources": self.sources,
            "should_reinforce": self.should_reinforce,
            "needs_mutation": self.needs_mutation,
            "needs_deprecation": self.needs_deprecation,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "gap_detected": self.gap_detected,
            "suggestions": self.suggestions,
            "records": [r.to_dict() for r in self.records],
            "summary": self.summary,
        }


class OutcomeEvaluator:
    """
    Unified outcome evaluator for RPA.

    Integrates multiple feedback sources to classify outcomes:
    - Sandbox execution results
    - User explicit ratings
    - Self-assessment results
    - Validation checks

    Provides unified outcome classification that drives the
    reinforcement, mutation, and retry systems.
    """

    # Thresholds for outcome decisions
    FAILURE_THRESHOLD = 0.3  # Below this = failure
    SUCCESS_THRESHOLD = 0.8  # Above this = success
    DEPRECATION_FAILURE_COUNT = 5  # Failures before deprecation
    MUTATION_FAILURE_COUNT = 2  # Failures before mutation

    def __init__(
        self,
        error_classifier: Optional[ErrorClassifier] = None,
        validator: Optional[Validator] = None,
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
        self._outcome_history: Dict[str, List[OutcomeRecord]] = {}

        # Statistics
        self._stats = {
            "total_evaluations": 0,
            "by_type": {t.value: 0 for t in OutcomeType},
            "by_source": {},
        }

    def evaluate(
        self,
        pattern_id: str,
        context: str,
        sandbox_result: Optional[Dict[str, Any]] = None,
        user_rating: Optional[float] = None,
        assessment_result: Optional[Dict[str, Any]] = None,
        validation_result: Optional[Dict[str, Any]] = None,
    ) -> Outcome:
        """
        Evaluate the outcome of using a pattern.

        Args:
            pattern_id: ID of the pattern used
            context: What was being attempted
            sandbox_result: Result from sandbox execution
                - success: bool
                - error: Optional[str]
                - output: Optional[str]
            user_rating: Explicit user rating (0.0-1.0)
            assessment_result: Result from self-assessment
                - is_valid: bool
                - pass_rate: float
            validation_result: Result from validation
                - is_valid: bool
                - issues: List[str]

        Returns:
            Unified Outcome with recommendations
        """
        self._stats["total_evaluations"] += 1

        records: List[OutcomeRecord] = []
        sources: List[str] = []
        confidence_scores: List[float] = []
        failure_count = 0
        success_count = 0
        gap_detected = False
        suggestions: List[str] = []

        # Process sandbox result
        if sandbox_result is not None:
            record, confidence = self._process_sandbox_result(
                pattern_id, context, sandbox_result
            )
            records.append(record)
            sources.append("sandbox")
            confidence_scores.append(confidence)

            if sandbox_result.get("success", False):
                success_count += 1
            else:
                failure_count += 1

        # Process user rating
        if user_rating is not None:
            record, confidence = self._process_user_rating(
                pattern_id, context, user_rating
            )
            records.append(record)
            sources.append("user")
            confidence_scores.append(confidence)

            if user_rating >= self.SUCCESS_THRESHOLD:
                success_count += 1
            elif user_rating < self.FAILURE_THRESHOLD:
                failure_count += 1

        # Process assessment result
        if assessment_result is not None:
            record, confidence = self._process_assessment_result(
                pattern_id, context, assessment_result
            )
            records.append(record)
            sources.append("self_assessment")
            confidence_scores.append(confidence)

            if assessment_result.get("pass_rate", 0) < 0.5:
                gap_detected = True
                suggestions.append("Pattern knowledge gaps detected")

        # Process validation result
        if validation_result is not None:
            record, confidence = self._process_validation_result(
                pattern_id, context, validation_result
            )
            records.append(record)
            sources.append("validation")
            confidence_scores.append(confidence)

            if not validation_result.get("is_valid", True):
                suggestions.extend(validation_result.get("issues", []))

        # Determine overall outcome type
        overall_confidence = (
            sum(confidence_scores) / len(confidence_scores)
            if confidence_scores else 0.5
        )
        outcome_type = self._determine_outcome_type(
            overall_confidence, failure_count, gap_detected
        )

        # Determine actions
        should_reinforce = outcome_type == OutcomeType.SUCCESS
        needs_mutation = (
            failure_count >= self.MUTATION_FAILURE_COUNT or
            outcome_type == OutcomeType.PARTIAL
        )
        needs_deprecation = (
            failure_count >= self.DEPRECATION_FAILURE_COUNT or
            outcome_type == OutcomeType.DEPRECATED
        )

        # Generate summary
        summary = self._generate_summary(
            pattern_id, outcome_type, overall_confidence,
            success_count, failure_count, suggestions
        )

        # Create outcome
        outcome = Outcome(
            pattern_id=pattern_id,
            outcome_type=outcome_type,
            confidence=overall_confidence,
            sources=sources,
            should_reinforce=should_reinforce,
            needs_mutation=needs_mutation,
            needs_deprecation=needs_deprecation,
            failure_count=failure_count,
            success_count=success_count,
            gap_detected=gap_detected,
            suggestions=suggestions,
            records=records,
            summary=summary,
        )

        # Store records in history
        for record in records:
            if pattern_id not in self._outcome_history:
                self._outcome_history[pattern_id] = []
            self._outcome_history[pattern_id].append(record)

        # Update stats
        self._stats["by_type"][outcome_type.value] += 1
        for source in sources:
            self._stats["by_source"][source] = (
                self._stats["by_source"].get(source, 0) + 1
            )

        return outcome

    def evaluate_sandbox_execution(
        self,
        pattern_id: str,
        context: str,
        code: str,
        execution_result: Dict[str, Any],
    ) -> Outcome:
        """
        Evaluate outcome from sandbox execution.

        Args:
            pattern_id: ID of the pattern used
            context: What was being attempted
            code: Code that was executed
            execution_result: Result from CodeSandbox
                - success: bool
                - output: Optional[str]
                - error: Optional[str]
                - execution_time: Optional[float]

        Returns:
            Outcome from the execution
        """
        # Process error if present
        error_info = None
        if not execution_result.get("success", False):
            error_msg = execution_result.get("error", "Unknown error")
            classified = self.error_classifier.classify(
                error_message=error_msg,
                code_context=code,
            )
            error_info = {
                "error_message": error_msg,
                "classification": classified.to_dict(),
            }

        sandbox_result = {
            "success": execution_result.get("success", False),
            "output": execution_result.get("output"),
            "error": error_info,
            "execution_time": execution_result.get("execution_time"),
        }

        return self.evaluate(
            pattern_id=pattern_id,
            context=context,
            sandbox_result=sandbox_result,
        )

    def evaluate_user_feedback(
        self,
        pattern_id: str,
        context: str,
        rating: float,
        feedback: Optional[str] = None,
    ) -> Outcome:
        """
        Evaluate outcome from user feedback.

        Args:
            pattern_id: ID of the pattern used
            context: What was being attempted
            rating: User rating (0.0-1.0)
            feedback: Optional textual feedback

        Returns:
            Outcome from user feedback
        """
        return self.evaluate(
            pattern_id=pattern_id,
            context=context,
            user_rating=rating,
        )

    def get_outcome_history(
        self,
        pattern_id: str,
        limit: int = 20,
    ) -> List[OutcomeRecord]:
        """Get outcome history for a pattern."""
        history = self._outcome_history.get(pattern_id, [])
        return history[-limit:]

    def get_pattern_statistics(self, pattern_id: str) -> Dict[str, Any]:
        """Get outcome statistics for a pattern."""
        history = self._outcome_history.get(pattern_id, [])

        if not history:
            return {
                "pattern_id": pattern_id,
                "total_outcomes": 0,
                "success_rate": 0.0,
                "failure_rate": 0.0,
            }

        by_type = {t.value: 0 for t in OutcomeType}
        for record in history:
            by_type[record.outcome_type.value] += 1

        total = len(history)
        success_count = by_type.get(OutcomeType.SUCCESS.value, 0)
        failure_count = by_type.get(OutcomeType.FAILURE.value, 0)

        return {
            "pattern_id": pattern_id,
            "total_outcomes": total,
            "success_count": success_count,
            "failure_count": failure_count,
            "success_rate": success_count / total if total > 0 else 0,
            "failure_rate": failure_count / total if total > 0 else 0,
            "by_type": by_type,
            "last_outcome": history[-1].outcome_type.value if history else None,
        }

    def get_global_statistics(self) -> Dict[str, Any]:
        """Get global outcome statistics."""
        return {
            **self._stats,
            "patterns_tracked": len(self._outcome_history),
        }

    def _process_sandbox_result(
        self,
        pattern_id: str,
        context: str,
        result: Dict[str, Any],
    ) -> tuple[OutcomeRecord, float]:
        """Process sandbox execution result."""
        success = result.get("success", False)
        confidence = 1.0 if success else 0.0

        outcome_type = OutcomeType.SUCCESS if success else OutcomeType.FAILURE

        record = OutcomeRecord(
            record_id=f"out_{uuid.uuid4().hex[:8]}",
            pattern_id=pattern_id,
            outcome_type=outcome_type,
            confidence=confidence,
            context=context,
            source="sandbox",
            error_info=result.get("error"),
        )

        return record, confidence

    def _process_user_rating(
        self,
        pattern_id: str,
        context: str,
        rating: float,
    ) -> tuple[OutcomeRecord, float]:
        """Process user rating."""
        if rating >= self.SUCCESS_THRESHOLD:
            outcome_type = OutcomeType.SUCCESS
        elif rating >= 0.5:
            outcome_type = OutcomeType.PARTIAL
        else:
            outcome_type = OutcomeType.FAILURE

        record = OutcomeRecord(
            record_id=f"out_{uuid.uuid4().hex[:8]}",
            pattern_id=pattern_id,
            outcome_type=outcome_type,
            confidence=rating,
            context=context,
            source="user",
        )

        return record, rating

    def _process_assessment_result(
        self,
        pattern_id: str,
        context: str,
        result: Dict[str, Any],
    ) -> tuple[OutcomeRecord, float]:
        """Process self-assessment result."""
        is_valid = result.get("is_valid", False)
        pass_rate = result.get("pass_rate", 0.0)

        if is_valid and pass_rate >= self.SUCCESS_THRESHOLD:
            outcome_type = OutcomeType.SUCCESS
        elif pass_rate >= 0.5:
            outcome_type = OutcomeType.PARTIAL
        else:
            outcome_type = OutcomeType.GAP

        record = OutcomeRecord(
            record_id=f"out_{uuid.uuid4().hex[:8]}",
            pattern_id=pattern_id,
            outcome_type=outcome_type,
            confidence=pass_rate,
            context=context,
            source="self_assessment",
            assessment_info=result,
        )

        return record, pass_rate

    def _process_validation_result(
        self,
        pattern_id: str,
        context: str,
        result: Dict[str, Any],
    ) -> tuple[OutcomeRecord, float]:
        """Process validation result."""
        is_valid = result.get("is_valid", False)
        issues = result.get("issues", [])

        confidence = 1.0 if is_valid else 0.5 - (0.1 * len(issues))
        confidence = max(0.0, min(1.0, confidence))

        outcome_type = OutcomeType.SUCCESS if is_valid else OutcomeType.PARTIAL

        record = OutcomeRecord(
            record_id=f"out_{uuid.uuid4().hex[:8]}",
            pattern_id=pattern_id,
            outcome_type=outcome_type,
            confidence=confidence,
            context=context,
            source="validation",
            validation_info=result,
        )

        return record, confidence

    def _determine_outcome_type(
        self,
        confidence: float,
        failure_count: int,
        gap_detected: bool,
    ) -> OutcomeType:
        """Determine overall outcome type."""
        if gap_detected:
            return OutcomeType.GAP

        if failure_count >= self.DEPRECATION_FAILURE_COUNT:
            return OutcomeType.DEPRECATED

        if confidence >= self.SUCCESS_THRESHOLD:
            return OutcomeType.SUCCESS

        if confidence < self.FAILURE_THRESHOLD:
            return OutcomeType.FAILURE

        if confidence < 0.5:
            return OutcomeType.UNCERTAIN

        return OutcomeType.PARTIAL

    def _generate_summary(
        self,
        pattern_id: str,
        outcome_type: OutcomeType,
        confidence: float,
        success_count: int,
        failure_count: int,
        suggestions: List[str],
    ) -> str:
        """Generate human-readable summary."""
        lines = [
            f"Outcome for pattern '{pattern_id}': {outcome_type.value.upper()}",
            f"Confidence: {confidence*100:.1f}%",
            f"Successes: {success_count}, Failures: {failure_count}",
        ]

        if suggestions:
            lines.append("Suggestions:")
            for s in suggestions[:3]:
                lines.append(f"  - {s}")

        return "\n".join(lines)

    def clear_history(self) -> None:
        """Clear outcome history."""
        self._outcome_history.clear()
        self._stats = {
            "total_evaluations": 0,
            "by_type": {t.value: 0 for t in OutcomeType},
            "by_source": {},
        }
