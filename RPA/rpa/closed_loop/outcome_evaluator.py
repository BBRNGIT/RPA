"""
Outcome Evaluator - Unified outcome scoring for closed-loop learning.

Evaluates every action result and classifies it for learning feedback.
This is the foundation of the self-improving system - every outcome
is scored, recorded, and used to drive pattern mutation.

Outcome Types:
- SUCCESS: Pattern worked correctly
- FAILURE: Pattern failed but was recoverable
- GAP: Missing knowledge detected
- ERROR: Unrecoverable error occurred
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set
import uuid
import logging

from rpa.learning.error_classifier import ErrorClassifier, ClassifiedError
from rpa.validation.validator import Validator, ValidationResult
from rpa.assessment.engine import SelfAssessmentEngine

logger = logging.getLogger(__name__)


class OutcomeType(Enum):
    """Types of outcomes from pattern application."""
    SUCCESS = "success"           # Pattern worked correctly
    FAILURE = "failure"           # Pattern failed but recoverable
    GAP = "gap"                   # Missing knowledge detected
    ERROR = "error"               # Unrecoverable error
    PARTIAL = "partial"           # Partially successful
    UNCERTAIN = "uncertain"       # Outcome unclear - needs review


class OutcomeSeverity(Enum):
    """Severity levels for outcomes."""
    CRITICAL = "critical"         # System-breaking, needs immediate attention
    HIGH = "high"                 # Significant impact
    MEDIUM = "medium"             # Moderate impact
    LOW = "low"                   # Minor impact
    INFO = "info"                 # Informational only


@dataclass
class Outcome:
    """
    Represents the outcome of a pattern application.
    
    This is the core unit of feedback for the closed-loop system.
    Every time a pattern is used, an Outcome is created and recorded.
    """
    outcome_id: str
    outcome_type: OutcomeType
    severity: OutcomeSeverity
    pattern_id: str
    domain: str
    
    # Scoring
    success_score: float = 0.0      # 0.0-1.0 how successful was the outcome
    confidence_score: float = 0.0   # 0.0-1.0 how confident are we in the outcome
    learning_value: float = 0.0     # 0.0-1.0 how much can be learned from this
    
    # Context
    action: str = ""                # What action was attempted
    context: Dict[str, Any] = field(default_factory=dict)
    result: Optional[str] = None    # What actually happened
    
    # Error information (if applicable)
    error: Optional[ClassifiedError] = None
    validation: Optional[ValidationResult] = None
    
    # Feedback sources
    sandbox_result: Optional[Dict[str, Any]] = None
    user_rating: Optional[int] = None  # 1-5 stars or -1 for negative
    self_assessment: Optional[Dict[str, Any]] = None
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    session_id: str = ""
    retry_count: int = 0
    previous_outcome_id: Optional[str] = None  # Link to previous attempt if retry
    
    # Learning signals
    should_mutate: bool = False
    should_deprecate: bool = False
    should_reinforce: bool = False
    suggested_fixes: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "outcome_id": self.outcome_id,
            "outcome_type": self.outcome_type.value,
            "severity": self.severity.value,
            "pattern_id": self.pattern_id,
            "domain": self.domain,
            "success_score": self.success_score,
            "confidence_score": self.confidence_score,
            "learning_value": self.learning_value,
            "action": self.action,
            "context": self.context,
            "result": self.result,
            "error": self.error.to_dict() if self.error else None,
            "validation": self.validation.to_dict() if self.validation else None,
            "sandbox_result": self.sandbox_result,
            "user_rating": self.user_rating,
            "self_assessment": self.self_assessment,
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id,
            "retry_count": self.retry_count,
            "previous_outcome_id": self.previous_outcome_id,
            "should_mutate": self.should_mutate,
            "should_deprecate": self.should_deprecate,
            "should_reinforce": self.should_reinforce,
            "suggested_fixes": self.suggested_fixes,
        }


class OutcomeEvaluator:
    """
    Unified outcome evaluation system.
    
    Evaluates every action result and produces a standardized Outcome
    that can be used for:
    - Pattern mutation decisions
    - Reinforcement signals
    - Gap detection
    - Learning prioritization
    
    Integrates three feedback sources:
    1. Sandbox execution result
    2. User explicit rating
    3. RPA's own SelfAssessmentEngine
    """
    
    def __init__(
        self,
        error_classifier: Optional[ErrorClassifier] = None,
        validator: Optional[Validator] = None,
        assessment_engine: Optional[SelfAssessmentEngine] = None,
    ):
        """Initialize the OutcomeEvaluator."""
        self.error_classifier = error_classifier or ErrorClassifier()
        self.validator = validator or Validator()
        self.assessment_engine = assessment_engine or SelfAssessmentEngine()
        
        # Outcome history for pattern tracking
        self._outcome_history: Dict[str, List[Outcome]] = {}  # pattern_id -> outcomes
        self._all_outcomes: List[Outcome] = []
        self._max_history_per_pattern = 100
        self._max_total_history = 10000
        
        # Statistics
        self._stats = {
            "total_evaluated": 0,
            "by_type": {t.value: 0 for t in OutcomeType},
            "by_severity": {s.value: 0 for s in OutcomeSeverity},
            "by_domain": {},
            "mutations_triggered": 0,
            "deprecations_triggered": 0,
            "reinforcements_triggered": 0,
        }
    
    def evaluate(
        self,
        pattern_id: str,
        domain: str,
        action: str,
        result: str,
        sandbox_result: Optional[Dict[str, Any]] = None,
        user_rating: Optional[int] = None,
        self_assessment: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        error_type: Optional[str] = None,
        code_context: Optional[str] = None,
        session_id: str = "",
        retry_count: int = 0,
        previous_outcome_id: Optional[str] = None,
    ) -> Outcome:
        """
        Evaluate the outcome of a pattern application.
        
        Args:
            pattern_id: ID of the pattern that was used
            domain: Domain of the pattern (python, rust, english, etc.)
            action: What action was attempted
            result: What actually happened
            sandbox_result: Result from sandbox execution (if any)
            user_rating: User's explicit rating (1-5 or -1 for negative)
            self_assessment: RPA's self-assessment result
            error_message: Error message if failure occurred
            error_type: Type of error if known
            code_context: Code context for error classification
            session_id: Current session ID
            retry_count: Number of retries attempted
            previous_outcome_id: ID of previous outcome if this is a retry
            
        Returns:
            Outcome with complete evaluation and learning signals
        """
        outcome_id = f"outcome_{uuid.uuid4().hex[:8]}"
        
        # Initialize outcome
        outcome = Outcome(
            outcome_id=outcome_id,
            outcome_type=OutcomeType.SUCCESS,  # Default, will be refined
            severity=OutcomeSeverity.INFO,
            pattern_id=pattern_id,
            domain=domain,
            action=action,
            result=result,
            sandbox_result=sandbox_result,
            user_rating=user_rating,
            self_assessment=self_assessment,
            session_id=session_id,
            retry_count=retry_count,
            previous_outcome_id=previous_outcome_id,
        )
        
        # Step 1: Classify error if present
        if error_message:
            outcome.error = self.error_classifier.classify(
                error_message=error_message,
                error_type=error_type,
                code_context=code_context,
            )
            outcome.learning_value = outcome.error.learning_value
            outcome.suggested_fixes = outcome.error.suggestions
        
        # Step 2: Determine outcome type from multiple sources
        outcome.outcome_type = self._determine_outcome_type(
            sandbox_result=sandbox_result,
            user_rating=user_rating,
            self_assessment=self_assessment,
            error=outcome.error,
            result=result,
        )
        
        # Step 3: Determine severity
        outcome.severity = self._determine_severity(
            outcome_type=outcome.outcome_type,
            error=outcome.error,
            user_rating=user_rating,
        )
        
        # Step 4: Calculate scores
        outcome.success_score = self._calculate_success_score(
            outcome_type=outcome.outcome_type,
            sandbox_result=sandbox_result,
            user_rating=user_rating,
            self_assessment=self_assessment,
        )
        
        outcome.confidence_score = self._calculate_confidence_score(
            sandbox_result=sandbox_result,
            user_rating=user_rating,
            self_assessment=self_assessment,
        )
        
        # Step 5: Determine learning signals
        outcome.should_mutate = self._should_mutate(outcome)
        outcome.should_deprecate = self._should_deprecate(outcome)
        outcome.should_reinforce = self._should_reinforce(outcome)
        
        # Step 6: Update learning value if not set
        if outcome.learning_value == 0.0:
            outcome.learning_value = self._calculate_learning_value(outcome)
        
        # Record outcome
        self._record_outcome(outcome)
        
        # Update statistics
        self._update_stats(outcome)
        
        return outcome
    
    def _determine_outcome_type(
        self,
        sandbox_result: Optional[Dict[str, Any]],
        user_rating: Optional[int],
        self_assessment: Optional[Dict[str, Any]],
        error: Optional[ClassifiedError],
        result: str,
    ) -> OutcomeType:
        """Determine the outcome type from multiple sources."""
        
        # Check for explicit failure signals
        if error:
            if error.severity == "critical":
                return OutcomeType.ERROR
            return OutcomeType.FAILURE
        
        # Check sandbox result
        if sandbox_result:
            if sandbox_result.get("success") is False:
                if sandbox_result.get("error_type") == "gap":
                    return OutcomeType.GAP
                return OutcomeType.FAILURE
            elif sandbox_result.get("partial_success"):
                return OutcomeType.PARTIAL
        
        # Check user rating
        if user_rating is not None:
            if user_rating < 0:
                return OutcomeType.ERROR
            elif user_rating < 2:
                return OutcomeType.FAILURE
            elif user_rating < 3:
                return OutcomeType.PARTIAL
            elif user_rating >= 4:
                return OutcomeType.SUCCESS
        
        # Check self-assessment
        if self_assessment:
            if self_assessment.get("gap_detected"):
                return OutcomeType.GAP
            if self_assessment.get("uncertain"):
                return OutcomeType.UNCERTAIN
            if self_assessment.get("passed") is False:
                return OutcomeType.FAILURE
            if self_assessment.get("confidence", 0) < 0.5:
                return OutcomeType.UNCERTAIN
        
        # Check result string for clues
        result_lower = result.lower()
        if "error" in result_lower or "failed" in result_lower:
            return OutcomeType.FAILURE
        if "gap" in result_lower or "missing" in result_lower:
            return OutcomeType.GAP
        if "success" in result_lower or "completed" in result_lower:
            return OutcomeType.SUCCESS
        
        # Default to success if no negative signals
        return OutcomeType.SUCCESS
    
    def _determine_severity(
        self,
        outcome_type: OutcomeType,
        error: Optional[ClassifiedError],
        user_rating: Optional[int],
    ) -> OutcomeSeverity:
        """Determine the severity of an outcome."""
        
        # Map outcome type to base severity
        type_severity = {
            OutcomeType.ERROR: OutcomeSeverity.CRITICAL,
            OutcomeType.FAILURE: OutcomeSeverity.HIGH,
            OutcomeType.GAP: OutcomeSeverity.MEDIUM,
            OutcomeType.PARTIAL: OutcomeSeverity.MEDIUM,
            OutcomeType.UNCERTAIN: OutcomeSeverity.LOW,
            OutcomeType.SUCCESS: OutcomeSeverity.INFO,
        }
        
        severity = type_severity.get(outcome_type, OutcomeSeverity.INFO)
        
        # Adjust based on error severity
        if error:
            error_severity_map = {
                "critical": OutcomeSeverity.CRITICAL,
                "high": OutcomeSeverity.HIGH,
                "medium": OutcomeSeverity.MEDIUM,
                "low": OutcomeSeverity.LOW,
            }
            error_severity = error_severity_map.get(error.severity, OutcomeSeverity.MEDIUM)
            if error_severity.value > severity.value:
                severity = error_severity
        
        # Adjust based on user rating
        if user_rating is not None:
            if user_rating < 0:
                return OutcomeSeverity.CRITICAL
            elif user_rating < 2 and severity.value < OutcomeSeverity.HIGH.value:
                return OutcomeSeverity.HIGH
        
        return severity
    
    def _calculate_success_score(
        self,
        outcome_type: OutcomeType,
        sandbox_result: Optional[Dict[str, Any]],
        user_rating: Optional[int],
        self_assessment: Optional[Dict[str, Any]],
    ) -> float:
        """Calculate the success score (0.0-1.0)."""
        
        scores = []
        
        # Base score from outcome type
        type_scores = {
            OutcomeType.SUCCESS: 1.0,
            OutcomeType.PARTIAL: 0.6,
            OutcomeType.UNCERTAIN: 0.4,
            OutcomeType.GAP: 0.2,
            OutcomeType.FAILURE: 0.1,
            OutcomeType.ERROR: 0.0,
        }
        scores.append(type_scores.get(outcome_type, 0.5))
        
        # Sandbox score
        if sandbox_result:
            if sandbox_result.get("success"):
                scores.append(1.0)
            elif sandbox_result.get("partial_success"):
                scores.append(0.5)
            else:
                scores.append(0.0)
        
        # User rating score
        if user_rating is not None:
            if user_rating > 0:
                scores.append(user_rating / 5.0)
            else:
                scores.append(0.0)
        
        # Self-assessment score
        if self_assessment:
            scores.append(self_assessment.get("confidence", 0.5))
        
        return sum(scores) / len(scores) if scores else 0.5
    
    def _calculate_confidence_score(
        self,
        sandbox_result: Optional[Dict[str, Any]],
        user_rating: Optional[int],
        self_assessment: Optional[Dict[str, Any]],
    ) -> float:
        """Calculate confidence in the outcome assessment."""
        
        confidence = 0.5  # Base confidence
        
        # More feedback sources = higher confidence
        sources = 0
        if sandbox_result:
            sources += 1
            confidence += 0.1
        if user_rating is not None:
            sources += 1
            confidence += 0.15  # User feedback is valuable
        if self_assessment:
            sources += 1
            confidence += 0.1
        
        # Adjust based on source agreement
        if sources >= 2:
            confidence += 0.1  # Multiple sources agreeing
        
        return min(confidence, 1.0)
    
    def _calculate_learning_value(self, outcome: Outcome) -> float:
        """Calculate how much can be learned from this outcome."""
        
        # Failures have high learning value
        if outcome.outcome_type == OutcomeType.FAILURE:
            return 0.8 + (outcome.error.learning_value * 0.2 if outcome.error else 0)
        
        # Errors have very high learning value
        if outcome.outcome_type == OutcomeType.ERROR:
            return 0.9
        
        # Gaps indicate missing knowledge
        if outcome.outcome_type == OutcomeType.GAP:
            return 0.7
        
        # Partial successes have learning value
        if outcome.outcome_type == OutcomeType.PARTIAL:
            return 0.5
        
        # Uncertain outcomes need review
        if outcome.outcome_type == OutcomeType.UNCERTAIN:
            return 0.4
        
        # Successes have low learning value (but still valuable for reinforcement)
        if outcome.outcome_type == OutcomeType.SUCCESS:
            return 0.2
        
        return 0.3
    
    def _should_mutate(self, outcome: Outcome) -> bool:
        """Determine if the pattern should be mutated based on this outcome."""
        
        # Don't mutate successful patterns
        if outcome.outcome_type == OutcomeType.SUCCESS:
            return False
        
        # Always mutate on failure if we have suggestions
        if outcome.outcome_type == OutcomeType.FAILURE:
            return len(outcome.suggested_fixes) > 0 or outcome.error is not None
        
        # Mutate on error
        if outcome.outcome_type == OutcomeType.ERROR:
            return True
        
        # Mutate on gap if it reveals missing knowledge
        if outcome.outcome_type == OutcomeType.GAP:
            return True
        
        # Consider mutating partial successes after multiple attempts
        if outcome.outcome_type == OutcomeType.PARTIAL and outcome.retry_count >= 2:
            return True
        
        return False
    
    def _should_deprecate(self, outcome: Outcome) -> bool:
        """Determine if the pattern should be deprecated."""
        
        # Deprecate on critical errors
        if outcome.severity == OutcomeSeverity.CRITICAL:
            return True
        
        # Deprecate on repeated failures
        if outcome.outcome_type == OutcomeType.FAILURE:
            pattern_outcomes = self._outcome_history.get(outcome.pattern_id, [])
            recent_failures = sum(
                1 for o in pattern_outcomes[-5:]
                if o.outcome_type == OutcomeType.FAILURE
            )
            if recent_failures >= 3:
                return True
        
        # Deprecate if error is unrecoverable
        if outcome.error and outcome.error.severity == "critical":
            return True
        
        return False
    
    def _should_reinforce(self, outcome: Outcome) -> bool:
        """Determine if the pattern should be reinforced."""
        
        # Reinforce on clear success
        if outcome.outcome_type == OutcomeType.SUCCESS:
            # Higher reinforcement for high-confidence successes
            if outcome.confidence_score >= 0.8:
                return True
            # Reinforce if user rated highly
            if outcome.user_rating and outcome.user_rating >= 4:
                return True
            # Reinforce if sandbox and self-assessment both passed
            if (outcome.sandbox_result and outcome.sandbox_result.get("success") and
                outcome.self_assessment and outcome.self_assessment.get("passed")):
                return True
        
        return False
    
    def _record_outcome(self, outcome: Outcome) -> None:
        """Record outcome in history."""
        
        # Add to pattern-specific history
        if outcome.pattern_id not in self._outcome_history:
            self._outcome_history[outcome.pattern_id] = []
        
        self._outcome_history[outcome.pattern_id].append(outcome)
        
        # Trim if needed
        if len(self._outcome_history[outcome.pattern_id]) > self._max_history_per_pattern:
            self._outcome_history[outcome.pattern_id].pop(0)
        
        # Add to total history
        self._all_outcomes.append(outcome)
        if len(self._all_outcomes) > self._max_total_history:
            self._all_outcomes.pop(0)
    
    def _update_stats(self, outcome: Outcome) -> None:
        """Update statistics."""
        self._stats["total_evaluated"] += 1
        self._stats["by_type"][outcome.outcome_type.value] += 1
        self._stats["by_severity"][outcome.severity.value] += 1
        
        if outcome.domain not in self._stats["by_domain"]:
            self._stats["by_domain"][outcome.domain] = {"total": 0, "by_type": {}}
        self._stats["by_domain"][outcome.domain]["total"] += 1
        
        type_key = outcome.outcome_type.value
        if type_key not in self._stats["by_domain"][outcome.domain]["by_type"]:
            self._stats["by_domain"][outcome.domain]["by_type"][type_key] = 0
        self._stats["by_domain"][outcome.domain]["by_type"][type_key] += 1
        
        if outcome.should_mutate:
            self._stats["mutations_triggered"] += 1
        if outcome.should_deprecate:
            self._stats["deprecations_triggered"] += 1
        if outcome.should_reinforce:
            self._stats["reinforcements_triggered"] += 1
    
    def get_pattern_outcomes(self, pattern_id: str) -> List[Outcome]:
        """Get all outcomes for a specific pattern."""
        return self._outcome_history.get(pattern_id, [])
    
    def get_pattern_success_rate(self, pattern_id: str) -> float:
        """Calculate success rate for a pattern."""
        outcomes = self._outcome_history.get(pattern_id, [])
        if not outcomes:
            return 0.0
        
        successes = sum(1 for o in outcomes if o.outcome_type == OutcomeType.SUCCESS)
        return successes / len(outcomes)
    
    def get_pattern_learning_trend(self, pattern_id: str) -> str:
        """Analyze learning trend for a pattern."""
        outcomes = self._outcome_history.get(pattern_id, [])
        if len(outcomes) < 3:
            return "insufficient_data"
        
        # Compare recent vs earlier outcomes
        recent = outcomes[-3:]
        earlier = outcomes[:-3]
        
        recent_success = sum(1 for o in recent if o.outcome_type == OutcomeType.SUCCESS)
        earlier_success = sum(1 for o in earlier if o.outcome_type == OutcomeType.SUCCESS)
        
        recent_rate = recent_success / len(recent)
        earlier_rate = earlier_success / len(earlier) if earlier else 0.5
        
        if recent_rate > earlier_rate + 0.2:
            return "improving"
        elif recent_rate < earlier_rate - 0.2:
            return "declining"
        else:
            return "stable"
    
    def get_stats(self) -> Dict[str, Any]:
        """Get evaluator statistics."""
        return {
            **self._stats,
            "unique_patterns_tracked": len(self._outcome_history),
            "recent_outcomes": len(self._all_outcomes[-100:]),
        }
    
    def get_high_learning_outcomes(self, limit: int = 20) -> List[Outcome]:
        """Get outcomes with highest learning value."""
        sorted_outcomes = sorted(
            self._all_outcomes,
            key=lambda o: -o.learning_value
        )
        return sorted_outcomes[:limit]
    
    def get_patterns_needing_attention(self) -> List[Dict[str, Any]]:
        """Get patterns that need attention (high failure rate, declining trend)."""
        attention_needed = []
        
        for pattern_id, outcomes in self._outcome_history.items():
            if len(outcomes) < 3:
                continue
            
            success_rate = self.get_pattern_success_rate(pattern_id)
            trend = self.get_pattern_learning_trend(pattern_id)
            
            if success_rate < 0.5 or trend == "declining":
                attention_needed.append({
                    "pattern_id": pattern_id,
                    "success_rate": success_rate,
                    "trend": trend,
                    "total_outcomes": len(outcomes),
                    "last_outcome": outcomes[-1].to_dict() if outcomes else None,
                })
        
        return sorted(attention_needed, key=lambda x: x["success_rate"])
