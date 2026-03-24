"""
Self-Questioning Gate - Pre-output confidence checks.

Before the system outputs a response, this gate performs self-questioning
to ensure confidence and completeness. If the system doesn't know → it
exposes the gap rather than guessing.

Key questions:
1. Have I seen this pattern fail before?
2. Is the pattern complete (all children resolved)?
3. Do I have sufficient confidence?
4. Are there known edge cases I should warn about?

This implements the Epic requirement: "The system must be treated as a
recursive intelligent organism. If the system doesn't know → it exposes the gap."
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set
import uuid
import logging

from rpa.memory.ltm import LongTermMemory
from rpa.closed_loop.outcome_evaluator import OutcomeEvaluator, OutcomeType
from rpa.closed_loop.reinforcement_tracker import ReinforcementTracker, ReinforcementSignal
from rpa.closed_loop.pattern_mutator import PatternMutator, MutationType
from rpa.inquiry.gap_detector import GapDetector

logger = logging.getLogger(__name__)


class ConfidenceLevel(Enum):
    """Confidence levels for self-questioning results."""
    HIGH = "high"           # > 0.8 - Confident to proceed
    MEDIUM = "medium"       # 0.5-0.8 - Proceed with caveats
    LOW = "low"             # 0.3-0.5 - Needs review
    INSUFFICIENT = "insufficient"  # < 0.3 - Cannot proceed, expose gap


class QuestionType(Enum):
    """Types of self-questioning."""
    FAILURE_HISTORY = "failure_history"         # Has this failed before?
    COMPLETENESS = "completeness"               # Are all children resolved?
    CONFIDENCE = "confidence"                   # Is confidence sufficient?
    EDGE_CASES = "edge_cases"                   # Known edge cases?
    DOMAIN_MATCH = "domain_match"               # Is domain appropriate?
    RECENT_SUCCESS = "recent_success"           # Has it worked recently?
    VERSION_CHECK = "version_check"             # Is this the latest version?
    SIMILAR_FAILURES = "similar_failures"       # Have similar patterns failed?


@dataclass
class QuestionResult:
    """Result of a single self-question."""
    question_type: QuestionType
    passed: bool
    confidence: float
    details: str = ""
    warnings: List[str] = field(default_factory=list)
    related_pattern_ids: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "question_type": self.question_type.value,
            "passed": self.passed,
            "confidence": self.confidence,
            "details": self.details,
            "warnings": self.warnings,
            "related_pattern_ids": self.related_pattern_ids,
        }


@dataclass
class SelfQuestioningResult:
    """
    Complete result of self-questioning gate.
    
    This is what determines if the system can output confidently or
    must expose a gap.
    """
    result_id: str
    pattern_id: str
    domain: str
    
    # Overall assessment
    confidence_level: ConfidenceLevel
    overall_confidence: float
    can_proceed: bool
    
    # Individual questions
    questions: List[QuestionResult] = field(default_factory=list)
    
    # Issues found
    gaps_detected: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    # Context
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "result_id": self.result_id,
            "pattern_id": self.pattern_id,
            "domain": self.domain,
            "confidence_level": self.confidence_level.value,
            "overall_confidence": self.overall_confidence,
            "can_proceed": self.can_proceed,
            "questions": [q.to_dict() for q in self.questions],
            "gaps_detected": self.gaps_detected,
            "warnings": self.warnings,
            "recommendations": self.recommendations,
            "context": self.context,
            "timestamp": self.timestamp.isoformat(),
        }


class SelfQuestioningGate:
    """
    Pre-output confidence gate for self-questioning.
    
    Before any pattern is used to generate output, this gate runs
    a series of self-questions to determine:
    1. Can the system proceed confidently?
    2. Are there known issues to warn about?
    3. Should the gap be exposed instead?
    
    The gate is deterministic - it checks actual history and state,
    no heuristics pretending to be reasoning.
    """
    
    # Confidence thresholds
    HIGH_THRESHOLD = 0.8
    MEDIUM_THRESHOLD = 0.5
    LOW_THRESHOLD = 0.3
    
    # Failure tolerance
    MAX_RECENT_FAILURES = 2
    MIN_SUCCESS_RATE = 0.5
    
    def __init__(
        self,
        ltm: Optional[LongTermMemory] = None,
        outcome_evaluator: Optional[OutcomeEvaluator] = None,
        reinforcement_tracker: Optional[ReinforcementTracker] = None,
        pattern_mutator: Optional[PatternMutator] = None,
        gap_detector: Optional[GapDetector] = None,
    ):
        """
        Initialize SelfQuestioningGate.
        
        Args:
            ltm: LongTermMemory instance
            outcome_evaluator: OutcomeEvaluator instance
            reinforcement_tracker: ReinforcementTracker instance
            pattern_mutator: PatternMutator instance
            gap_detector: GapDetector instance
        """
        self.ltm = ltm
        self.outcome_evaluator = outcome_evaluator or OutcomeEvaluator()
        self.reinforcement_tracker = reinforcement_tracker or ReinforcementTracker()
        self.pattern_mutator = pattern_mutator or PatternMutator()
        self.gap_detector = gap_detector or GapDetector()
        
        # Question history for learning
        self._question_history: List[SelfQuestioningResult] = []
        self._max_history = 1000
        
        # Statistics
        self._stats = {
            "total_questions": 0,
            "passed": 0,
            "blocked": 0,
            "warnings_issued": 0,
            "gaps_exposed": 0,
            "by_confidence_level": {level.value: 0 for level in ConfidenceLevel},
        }
    
    def question(
        self,
        pattern_id: str,
        domain: str,
        context: Optional[Dict[str, Any]] = None,
        skip_questions: Optional[List[QuestionType]] = None,
    ) -> SelfQuestioningResult:
        """
        Run self-questioning gate on a pattern.
        
        This is the main entry point - before using a pattern,
        question its readiness.
        
        Args:
            pattern_id: Pattern to question
            domain: Domain context
            context: Additional context for questioning
            skip_questions: Questions to skip (for performance)
            
        Returns:
            SelfQuestioningResult with complete assessment
        """
        result_id = f"sq_{uuid.uuid4().hex[:8]}"
        skip_questions = skip_questions or []
        
        questions = []
        gaps = []
        warnings = []
        recommendations = []
        
        # Run all questions
        for question_type in QuestionType:
            if question_type in skip_questions:
                continue
            
            if question_type == QuestionType.FAILURE_HISTORY:
                q_result = self._question_failure_history(pattern_id, domain)
            elif question_type == QuestionType.COMPLETENESS:
                q_result = self._question_completeness(pattern_id, domain)
            elif question_type == QuestionType.CONFIDENCE:
                q_result = self._question_confidence(pattern_id, domain)
            elif question_type == QuestionType.EDGE_CASES:
                q_result = self._question_edge_cases(pattern_id, domain)
            elif question_type == QuestionType.DOMAIN_MATCH:
                q_result = self._question_domain_match(pattern_id, domain)
            elif question_type == QuestionType.RECENT_SUCCESS:
                q_result = self._question_recent_success(pattern_id, domain)
            elif question_type == QuestionType.VERSION_CHECK:
                q_result = self._question_version_check(pattern_id, domain)
            elif question_type == QuestionType.SIMILAR_FAILURES:
                q_result = self._question_similar_failures(pattern_id, domain)
            else:
                continue
            
            questions.append(q_result)
            
            # Collect gaps and warnings
            if not q_result.passed:
                if "gap" in q_result.details.lower() or "missing" in q_result.details.lower():
                    gaps.append(q_result.details)
                else:
                    warnings.append(q_result.details)
            
            warnings.extend(q_result.warnings)
        
        # Calculate overall confidence
        confidence_scores = [q.confidence for q in questions]
        overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.5
        
        # Determine confidence level
        if overall_confidence >= self.HIGH_THRESHOLD:
            confidence_level = ConfidenceLevel.HIGH
        elif overall_confidence >= self.MEDIUM_THRESHOLD:
            confidence_level = ConfidenceLevel.MEDIUM
        elif overall_confidence >= self.LOW_THRESHOLD:
            confidence_level = ConfidenceLevel.LOW
        else:
            confidence_level = ConfidenceLevel.INSUFFICIENT
        
        # Determine if can proceed
        critical_failures = sum(1 for q in questions if not q.passed and q.confidence < 0.3)
        can_proceed = confidence_level != ConfidenceLevel.INSUFFICIENT and critical_failures == 0
        
        # Generate recommendations
        if not can_proceed:
            recommendations.append("Expose gap to user instead of proceeding")
            recommendations.append("Consider alternative patterns")
        elif confidence_level == ConfidenceLevel.LOW:
            recommendations.append("Proceed with caution and user confirmation")
        elif confidence_level == ConfidenceLevel.MEDIUM:
            recommendations.append("Proceed but note caveats")
        
        if gaps:
            recommendations.append("Address detected gaps before proceeding")
        
        # Create result
        result = SelfQuestioningResult(
            result_id=result_id,
            pattern_id=pattern_id,
            domain=domain,
            confidence_level=confidence_level,
            overall_confidence=overall_confidence,
            can_proceed=can_proceed,
            questions=questions,
            gaps_detected=gaps,
            warnings=warnings,
            recommendations=recommendations,
            context=context or {},
        )
        
        # Record history
        self._question_history.append(result)
        if len(self._question_history) > self._max_history:
            self._question_history.pop(0)
        
        # Update statistics
        self._update_stats(result)
        
        return result
    
    def _question_failure_history(
        self,
        pattern_id: str,
        domain: str,
    ) -> QuestionResult:
        """Question: Has this pattern failed recently?"""
        
        # Get outcomes from evaluator
        outcomes = self.outcome_evaluator.get_pattern_outcomes(pattern_id)
        
        if not outcomes:
            return QuestionResult(
                question_type=QuestionType.FAILURE_HISTORY,
                passed=True,
                confidence=0.7,  # Neutral - no history
                details="No failure history available",
            )
        
        # Check recent failures
        recent = outcomes[-10:]  # Last 10 outcomes
        failures = [o for o in recent if o.outcome_type in (OutcomeType.FAILURE, OutcomeType.ERROR)]
        
        if len(failures) > self.MAX_RECENT_FAILURES:
            return QuestionResult(
                question_type=QuestionType.FAILURE_HISTORY,
                passed=False,
                confidence=0.3,
                details=f"Pattern has {len(failures)} recent failures",
                warnings=[f"Recent failure rate: {len(failures)}/{len(recent)}"],
            )
        
        # Check success rate
        if len(recent) >= 3:
            successes = sum(1 for o in recent if o.outcome_type == OutcomeType.SUCCESS)
            success_rate = successes / len(recent)
            
            if success_rate < self.MIN_SUCCESS_RATE:
                return QuestionResult(
                    question_type=QuestionType.FAILURE_HISTORY,
                    passed=False,
                    confidence=success_rate,
                    details=f"Success rate below threshold: {success_rate:.1%}",
                    warnings=[f"Consider using alternative pattern"],
                )
            
            return QuestionResult(
                question_type=QuestionType.FAILURE_HISTORY,
                passed=True,
                confidence=success_rate,
                details=f"Acceptable success rate: {success_rate:.1%}",
            )
        
        return QuestionResult(
            question_type=QuestionType.FAILURE_HISTORY,
            passed=True,
            confidence=0.8,
            details="Insufficient history for failure analysis",
        )
    
    def _question_completeness(
        self,
        pattern_id: str,
        domain: str,
    ) -> QuestionResult:
        """Question: Is the pattern complete (all children resolved)?"""
        
        if not self.ltm:
            return QuestionResult(
                question_type=QuestionType.COMPLETENESS,
                passed=True,
                confidence=0.6,
                details="No LTM available for completeness check",
            )
        
        pattern = self.ltm.get_pattern(pattern_id)
        if not pattern:
            return QuestionResult(
                question_type=QuestionType.COMPLETENESS,
                passed=False,
                confidence=0.2,
                details="Pattern not found in LTM",
                warnings=["Pattern may not be consolidated"],
            )
        
        # Check if pattern has unresolved children
        # Note: This would require graph traversal in full implementation
        # For now, check if pattern is marked as valid
        if not pattern.is_valid:
            return QuestionResult(
                question_type=QuestionType.COMPLETENESS,
                passed=False,
                confidence=0.3,
                details="Pattern is not marked as valid",
                warnings=[f"Validation issue: pattern marked invalid"],
            )
        
        if pattern.is_uncertain:
            return QuestionResult(
                question_type=QuestionType.COMPLETENESS,
                passed=False,
                confidence=0.4,
                details="Pattern is marked as uncertain",
                warnings=["Requires review before use"],
            )
        
        return QuestionResult(
            question_type=QuestionType.COMPLETENESS,
            passed=True,
            confidence=0.9,
            details="Pattern is complete and valid",
        )
    
    def _question_confidence(
        self,
        pattern_id: str,
        domain: str,
    ) -> QuestionResult:
        """Question: Is confidence sufficient?"""
        
        # Check reinforcement tracker
        strength = self.reinforcement_tracker.get_strength(pattern_id)
        
        if strength is None:
            return QuestionResult(
                question_type=QuestionType.CONFIDENCE,
                passed=True,
                confidence=0.5,
                details="Pattern not tracked in reinforcement system",
            )
        
        confidence = strength.strength
        
        if confidence < self.LOW_THRESHOLD:
            return QuestionResult(
                question_type=QuestionType.CONFIDENCE,
                passed=False,
                confidence=confidence,
                details=f"Pattern strength critically low: {confidence:.2f}",
                warnings=["Pattern may be near deprecation"],
            )
        
        if confidence < self.MEDIUM_THRESHOLD:
            return QuestionResult(
                question_type=QuestionType.CONFIDENCE,
                passed=True,  # Still usable but warn
                confidence=confidence,
                details=f"Pattern strength below optimal: {confidence:.2f}",
                warnings=["Consider reinforcing pattern"],
            )
        
        return QuestionResult(
            question_type=QuestionType.CONFIDENCE,
            passed=True,
            confidence=confidence,
            details=f"Pattern strength sufficient: {confidence:.2f}",
        )
    
    def _question_edge_cases(
        self,
        pattern_id: str,
        domain: str,
    ) -> QuestionResult:
        """Question: Are there known edge cases?"""
        
        # Check pattern versions for known issues
        versions = self.pattern_mutator.get_version_history(pattern_id)
        
        if not versions:
            return QuestionResult(
                question_type=QuestionType.EDGE_CASES,
                passed=True,
                confidence=0.7,
                details="No version history available",
            )
        
        # Check for deprecated versions
        deprecated = [v for v in versions if v.is_deprecated]
        
        if deprecated:
            warnings = []
            for v in deprecated[:3]:
                warnings.append(f"Previous version deprecated: {v.deprecation_reason[:50]}")
            
            return QuestionResult(
                question_type=QuestionType.EDGE_CASES,
                passed=True,  # Can still use current version
                confidence=0.7,
                details=f"Found {len(deprecated)} deprecated versions",
                warnings=warnings,
            )
        
        # Check for failure history in versions
        active = self.pattern_mutator.get_active_version(pattern_id)
        if active and active.failure_count > 0:
            return QuestionResult(
                question_type=QuestionType.EDGE_CASES,
                passed=True,
                confidence=0.6,
                details=f"Version has {active.failure_count} previous failures",
                warnings=["Pattern may have edge cases"],
            )
        
        return QuestionResult(
            question_type=QuestionType.EDGE_CASES,
            passed=True,
            confidence=0.9,
            details="No known edge cases",
        )
    
    def _question_domain_match(
        self,
        pattern_id: str,
        domain: str,
    ) -> QuestionResult:
        """Question: Is domain appropriate?"""
        
        if not self.ltm:
            return QuestionResult(
                question_type=QuestionType.DOMAIN_MATCH,
                passed=True,
                confidence=0.6,
                details="No LTM available for domain check",
            )
        
        pattern = self.ltm.get_pattern(pattern_id)
        if not pattern:
            return QuestionResult(
                question_type=QuestionType.DOMAIN_MATCH,
                passed=True,
                confidence=0.5,
                details="Pattern not found, assuming domain match",
            )
        
        if pattern.domain != domain:
            return QuestionResult(
                question_type=QuestionType.DOMAIN_MATCH,
                passed=True,  # Warning only
                confidence=0.5,
                details=f"Domain mismatch: pattern is '{pattern.domain}', context is '{domain}'",
                warnings=["Cross-domain pattern usage"],
            )
        
        return QuestionResult(
            question_type=QuestionType.DOMAIN_MATCH,
            passed=True,
            confidence=1.0,
            details=f"Domain match: {domain}",
        )
    
    def _question_recent_success(
        self,
        pattern_id: str,
        domain: str,
    ) -> QuestionResult:
        """Question: Has it worked recently?"""
        
        strength = self.reinforcement_tracker.get_strength(pattern_id)
        
        if strength is None or strength.last_success is None:
            return QuestionResult(
                question_type=QuestionType.RECENT_SUCCESS,
                passed=True,
                confidence=0.5,
                details="No recent success recorded",
            )
        
        # Check recency
        hours_since_success = (datetime.now() - strength.last_success).total_seconds() / 3600
        
        if hours_since_success < 1:
            return QuestionResult(
                question_type=QuestionType.RECENT_SUCCESS,
                passed=True,
                confidence=1.0,
                details=f"Very recent success ({hours_since_success:.1f} hours ago)",
            )
        elif hours_since_success < 24:
            return QuestionResult(
                question_type=QuestionType.RECENT_SUCCESS,
                passed=True,
                confidence=0.9,
                details=f"Recent success ({hours_since_success:.1f} hours ago)",
            )
        elif hours_since_success < 168:  # 1 week
            return QuestionResult(
                question_type=QuestionType.RECENT_SUCCESS,
                passed=True,
                confidence=0.7,
                details=f"Success within last week ({hours_since_success/24:.1f} days ago)",
            )
        else:
            return QuestionResult(
                question_type=QuestionType.RECENT_SUCCESS,
                passed=True,
                confidence=0.5,
                details=f"Stale success record ({hours_since_success/24:.1f} days ago)",
                warnings=["Pattern hasn't succeeded in over a week"],
            )
    
    def _question_version_check(
        self,
        pattern_id: str,
        domain: str,
    ) -> QuestionResult:
        """Question: Is this the latest version?"""
        
        active = self.pattern_mutator.get_active_version(pattern_id)
        
        if active is None:
            return QuestionResult(
                question_type=QuestionType.VERSION_CHECK,
                passed=True,
                confidence=0.7,
                details="No version tracking available",
            )
        
        if active.is_deprecated:
            return QuestionResult(
                question_type=QuestionType.VERSION_CHECK,
                passed=False,
                confidence=0.2,
                details="Active version is deprecated",
                warnings=["Pattern needs restoration or replacement"],
            )
        
        versions = self.pattern_mutator.get_version_history(pattern_id)
        if len(versions) > 1 and active.version_number < max(v.version_number for v in versions):
            return QuestionResult(
                question_type=QuestionType.VERSION_CHECK,
                passed=True,
                confidence=0.6,
                details="Newer version exists",
                warnings=["Consider using latest version"],
            )
        
        return QuestionResult(
            question_type=QuestionType.VERSION_CHECK,
            passed=True,
            confidence=0.9,
            details=f"Using latest version (v{active.version_number})",
        )
    
    def _question_similar_failures(
        self,
        pattern_id: str,
        domain: str,
    ) -> QuestionResult:
        """Question: Have similar patterns failed?"""
        
        if not self.ltm:
            return QuestionResult(
                question_type=QuestionType.SIMILAR_FAILURES,
                passed=True,
                confidence=0.6,
                details="No LTM for similarity check",
            )
        
        # Find patterns in same domain
        domain_patterns = self.ltm.find_by_domain(domain)
        
        # Check their success rates
        weak_patterns = []
        for p in domain_patterns[:20]:  # Limit for performance
            if p.node_id == pattern_id:
                continue
            
            strength = self.reinforcement_tracker.get_strength(p.node_id)
            if strength and strength.strength < 0.5:
                weak_patterns.append(p.node_id)
        
        if len(weak_patterns) > 3:
            return QuestionResult(
                question_type=QuestionType.SIMILAR_FAILURES,
                passed=True,
                confidence=0.6,
                details=f"Found {len(weak_patterns)} weak patterns in same domain",
                warnings=[f"Domain may have systemic issues"],
                related_pattern_ids=weak_patterns[:5],
            )
        
        return QuestionResult(
            question_type=QuestionType.SIMILAR_FAILURES,
            passed=True,
            confidence=0.9,
            details="No concerning pattern failures in domain",
        )
    
    def _update_stats(self, result: SelfQuestioningResult) -> None:
        """Update statistics."""
        self._stats["total_questions"] += 1
        self._stats["by_confidence_level"][result.confidence_level.value] += 1
        
        if result.can_proceed:
            self._stats["passed"] += 1
        else:
            self._stats["blocked"] += 1
        
        if result.warnings:
            self._stats["warnings_issued"] += 1
        
        if result.gaps_detected:
            self._stats["gaps_exposed"] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get gate statistics."""
        return {
            **self._stats,
            "history_size": len(self._question_history),
            "block_rate": self._stats["blocked"] / max(1, self._stats["total_questions"]),
        }
    
    def get_blocked_patterns(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recently blocked patterns."""
        blocked = [
            r.to_dict() for r in self._question_history
            if not r.can_proceed
        ]
        return blocked[-limit:]
    
    def get_low_confidence_patterns(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get patterns with low confidence."""
        low_conf = [
            r.to_dict() for r in self._question_history
            if r.confidence_level in (ConfidenceLevel.LOW, ConfidenceLevel.INSUFFICIENT)
        ]
        return low_conf[-limit:]
