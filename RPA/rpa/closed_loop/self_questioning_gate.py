"""
Self-Questioning Gate - Pre-output validation for RPA.

Before the system outputs a response, it asks itself:
- Have I seen this pattern fail before?
- Is my knowledge complete for this task?
- Are there known edge cases I should warn about?
- What is my confidence level?

This module implements the self-questioning mechanism that ensures
RPA doesn't confidently output incorrect or incomplete information.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import uuid
import logging

from rpa.core.graph import Node, PatternGraph, NodeType
from rpa.memory.ltm import LongTermMemory
from rpa.validation.validator import Validator
from rpa.inquiry.gap_detector import GapDetector

logger = logging.getLogger(__name__)


class QuestionType(Enum):
    """Types of self-questions."""
    FAILURE_HISTORY = "failure_history"      # Has this failed before?
    COMPLETENESS = "completeness"            # Is knowledge complete?
    EDGE_CASES = "edge_cases"                # Are there edge cases?
    CONFIDENCE = "confidence"                # What's confidence level?
    DOMAIN_MATCH = "domain_match"            # Is domain correct?
    PREREQUISITES = "prerequisites"          # Are prerequisites met?
    ALTERNATIVES = "alternatives"            # Are there better patterns?


@dataclass
class QuestionResult:
    """Result of a self-question."""
    question_type: QuestionType
    question: str
    answer: str
    passed: bool
    confidence: float
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "question_type": self.question_type.value,
            "question": self.question,
            "answer": self.answer,
            "passed": self.passed,
            "confidence": self.confidence,
            "details": self.details,
        }


@dataclass
class QuestioningResult:
    """
    Result of the self-questioning gate.

    Contains all questions asked, overall assessment, and
    recommendations for proceeding.
    """
    result_id: str
    pattern_id: str
    context: str
    questions: List[QuestionResult] = field(default_factory=list)
    overall_passed: bool = True
    overall_confidence: float = 1.0
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    should_proceed: bool = True
    should_warn_user: bool = False
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "result_id": self.result_id,
            "pattern_id": self.pattern_id,
            "context": self.context,
            "questions": [q.to_dict() for q in self.questions],
            "overall_passed": self.overall_passed,
            "overall_confidence": self.overall_confidence,
            "warnings": self.warnings,
            "recommendations": self.recommendations,
            "should_proceed": self.should_proceed,
            "should_warn_user": self.should_warn_user,
            "timestamp": self.timestamp.isoformat(),
        }


class SelfQuestioningGate:
    """
    Pre-output self-questioning gate.

    Before outputting a response, the system questions itself
    about the quality and reliability of the knowledge being used.

    Questions include:
    - Failure history: Has this pattern failed before?
    - Completeness: Is all required knowledge present?
    - Edge cases: Are there known edge cases?
    - Confidence: What is the confidence level?
    - Domain match: Is this the right domain?
    - Prerequisites: Are prerequisite patterns known?
    """

    # Confidence thresholds
    MIN_CONFIDENCE_TO_PROCEED = 0.5
    WARN_USER_THRESHOLD = 0.7
    HIGH_CONFIDENCE_THRESHOLD = 0.9

    def __init__(
        self,
        ltm: Optional[LongTermMemory] = None,
        validator: Optional[Validator] = None,
        gap_detector: Optional[GapDetector] = None,
    ):
        """
        Initialize the SelfQuestioningGate.

        Args:
            ltm: Optional LongTermMemory for history lookup
            validator: Optional Validator for structure checks
            gap_detector: Optional GapDetector for completeness checks
        """
        self.ltm = ltm
        self.validator = validator or Validator()
        self.gap_detector = gap_detector or GapDetector()

        # Question history for analysis
        self._question_history: Dict[str, List[QuestioningResult]] = {}

        # Statistics
        self._stats = {
            "total_questioning_sessions": 0,
            "passed_sessions": 0,
            "blocked_sessions": 0,
            "warned_sessions": 0,
        }

    def question(
        self,
        pattern: Node,
        context: str,
        graph: Optional[PatternGraph] = None,
        additional_questions: Optional[List[QuestionType]] = None,
    ) -> QuestioningResult:
        """
        Run self-questioning on a pattern before output.

        Args:
            pattern: The pattern being considered for output
            context: The context in which it will be used
            graph: Optional pattern graph for validation
            additional_questions: Additional question types to ask

        Returns:
            QuestioningResult with all questions and recommendations
        """
        self._stats["total_questioning_sessions"] += 1

        result_id = f"qgate_{uuid.uuid4().hex[:8]}"
        questions: List[QuestionResult] = []
        warnings: List[str] = []
        recommendations: List[str] = []

        # Standard questions
        standard_questions = [
            QuestionType.FAILURE_HISTORY,
            QuestionType.CONFIDENCE,
            QuestionType.COMPLETENESS,
            QuestionType.DOMAIN_MATCH,
        ]

        # Add additional questions
        all_questions = standard_questions + (additional_questions or [])

        # Ask each question
        for qtype in all_questions:
            q_result = self._ask_question(qtype, pattern, context, graph)
            questions.append(q_result)

            if not q_result.passed:
                warnings.append(f"{qtype.value}: {q_result.answer}")
                recommendations.extend(self._get_recommendations(qtype, q_result))

        # Calculate overall confidence
        confidences = [q.confidence for q in questions]
        overall_confidence = sum(confidences) / len(confidences) if confidences else 1.0

        # Determine if we should proceed
        all_passed = all(q.passed for q in questions)
        overall_passed = all_passed and overall_confidence >= self.MIN_CONFIDENCE_TO_PROCEED
        should_proceed = overall_confidence >= self.MIN_CONFIDENCE_TO_PROCEED
        should_warn_user = (
            not all_passed or
            overall_confidence < self.WARN_USER_THRESHOLD
        )

        # Create result
        result = QuestioningResult(
            result_id=result_id,
            pattern_id=pattern.node_id,
            context=context,
            questions=questions,
            overall_passed=overall_passed,
            overall_confidence=overall_confidence,
            warnings=warnings,
            recommendations=recommendations,
            should_proceed=should_proceed,
            should_warn_user=should_warn_user,
        )

        # Store in history
        if pattern.node_id not in self._question_history:
            self._question_history[pattern.node_id] = []
        self._question_history[pattern.node_id].append(result)

        # Update stats
        if overall_passed:
            self._stats["passed_sessions"] += 1
        elif should_proceed:
            self._stats["warned_sessions"] += 1
        else:
            self._stats["blocked_sessions"] += 1

        return result

    def quick_check(
        self,
        pattern: Node,
        context: str,
    ) -> Tuple[bool, float, List[str]]:
        """
        Quick check without full questioning.

        Args:
            pattern: The pattern to check
            context: The context

        Returns:
            Tuple of (should_proceed, confidence, warnings)
        """
        # Check confidence
        confidence = pattern.confidence

        # Check if deprecated
        if pattern.metadata.get("deprecated", False):
            return False, 0.0, ["Pattern is deprecated"]

        # Check if uncertain
        if pattern.is_uncertain:
            return True, confidence * 0.8, ["Pattern marked as uncertain"]

        # Quick validation
        if not pattern.is_valid:
            return True, confidence * 0.9, ["Pattern has validation issues"]

        warnings = []
        should_proceed = confidence >= self.MIN_CONFIDENCE_TO_PROCEED

        if confidence < self.WARN_USER_THRESHOLD:
            warnings.append(f"Low confidence: {confidence*100:.1f}%")

        return should_proceed, confidence, warnings

    def get_questioning_history(
        self,
        pattern_id: str,
        limit: int = 10,
    ) -> List[QuestioningResult]:
        """Get questioning history for a pattern."""
        history = self._question_history.get(pattern_id, [])
        return history[-limit:]

    def get_statistics(self) -> Dict[str, Any]:
        """Get questioning statistics."""
        return {
            **self._stats,
            "patterns_questioned": len(self._question_history),
        }

    def _ask_question(
        self,
        qtype: QuestionType,
        pattern: Node,
        context: str,
        graph: Optional[PatternGraph],
    ) -> QuestionResult:
        """Ask a specific question about the pattern."""
        if qtype == QuestionType.FAILURE_HISTORY:
            return self._ask_failure_history(pattern, context)
        elif qtype == QuestionType.COMPLETENESS:
            return self._ask_completeness(pattern, context, graph)
        elif qtype == QuestionType.CONFIDENCE:
            return self._ask_confidence(pattern, context)
        elif qtype == QuestionType.DOMAIN_MATCH:
            return self._ask_domain_match(pattern, context)
        elif qtype == QuestionType.EDGE_CASES:
            return self._ask_edge_cases(pattern, context)
        elif qtype == QuestionType.PREREQUISITES:
            return self._ask_prerequisites(pattern, context, graph)
        elif qtype == QuestionType.ALTERNATIVES:
            return self._ask_alternatives(pattern, context)
        else:
            return QuestionResult(
                question_type=qtype,
                question=f"Unknown question type: {qtype.value}",
                answer="Unable to answer",
                passed=True,
                confidence=0.5,
            )

    def _ask_failure_history(
        self,
        pattern: Node,
        context: str,
    ) -> QuestionResult:
        """Ask: Has this pattern failed before?"""
        # Check pattern metadata for failure history
        failure_count = pattern.metadata.get("failure_count", 0)
        success_count = pattern.metadata.get("success_count", 0)

        question = "Has this pattern failed in similar contexts before?"

        if failure_count == 0:
            return QuestionResult(
                question_type=QuestionType.FAILURE_HISTORY,
                question=question,
                answer="No failure history found",
                passed=True,
                confidence=1.0,
                details={"failure_count": 0, "success_count": success_count},
            )

        # Calculate failure rate
        total = failure_count + success_count
        failure_rate = failure_count / total if total > 0 else 0

        passed = failure_rate < 0.3
        confidence = 1.0 - failure_rate

        answer = f"Pattern has {failure_count} failures out of {total} uses"

        return QuestionResult(
            question_type=QuestionType.FAILURE_HISTORY,
            question=question,
            answer=answer,
            passed=passed,
            confidence=confidence,
            details={
                "failure_count": failure_count,
                "success_count": success_count,
                "failure_rate": failure_rate,
            },
        )

    def _ask_completeness(
        self,
        pattern: Node,
        context: str,
        graph: Optional[PatternGraph],
    ) -> QuestionResult:
        """Ask: Is the pattern's knowledge complete?"""
        question = "Is all required knowledge present for this task?"

        # Check content length
        content_length = len(pattern.content)
        min_length = 5

        if content_length < min_length:
            return QuestionResult(
                question_type=QuestionType.COMPLETENESS,
                question=question,
                answer=f"Pattern content too short ({content_length} chars)",
                passed=False,
                confidence=0.3,
                details={"content_length": content_length},
            )

        # Check for gaps
        gap_score = 0.0
        gaps = []

        if not pattern.content.strip():
            gaps.append("Empty content")
            gap_score += 0.3

        if not pattern.label:
            gaps.append("Missing label")
            gap_score += 0.1

        # Check composition
        composition = pattern.metadata.get("composition", [])
        if not composition and pattern.hierarchy_level > 0:
            gaps.append("Missing composition")
            gap_score += 0.2

        confidence = 1.0 - gap_score
        passed = confidence >= self.MIN_CONFIDENCE_TO_PROCEED

        answer = "Pattern appears complete" if passed else f"Gaps found: {gaps}"

        return QuestionResult(
            question_type=QuestionType.COMPLETENESS,
            question=question,
            answer=answer,
            passed=passed,
            confidence=confidence,
            details={"gaps": gaps, "gap_score": gap_score},
        )

    def _ask_confidence(
        self,
        pattern: Node,
        context: str,
    ) -> QuestionResult:
        """Ask: What is the confidence level?"""
        question = "What is the confidence level for this pattern?"

        confidence = pattern.confidence

        if confidence >= self.HIGH_CONFIDENCE_THRESHOLD:
            answer = f"High confidence: {confidence*100:.1f}%"
            passed = True
        elif confidence >= self.WARN_USER_THRESHOLD:
            answer = f"Good confidence: {confidence*100:.1f}%"
            passed = True
        elif confidence >= self.MIN_CONFIDENCE_TO_PROCEED:
            answer = f"Acceptable confidence: {confidence*100:.1f}%"
            passed = True
        else:
            answer = f"Low confidence: {confidence*100:.1f}%"
            passed = False

        return QuestionResult(
            question_type=QuestionType.CONFIDENCE,
            question=question,
            answer=answer,
            passed=passed,
            confidence=confidence,
            details={"pattern_confidence": confidence},
        )

    def _ask_domain_match(
        self,
        pattern: Node,
        context: str,
    ) -> QuestionResult:
        """Ask: Is the domain appropriate?"""
        question = "Is this pattern from the correct domain?"

        # Detect domain from context
        context_lower = context.lower()
        detected_domains = []

        if any(kw in context_lower for kw in ["def ", "import ", "python", "()"]):
            detected_domains.append("python")
        if any(kw in context_lower for kw in ["fn ", "let ", "rust", "impl"]):
            detected_domains.append("rust")
        if any(kw in context_lower for kw in ["func ", "go ", "package"]):
            detected_domains.append("go")
        if any(kw in context_lower for kw in ["the ", "is ", "are ", "english"]):
            detected_domains.append("english")

        pattern_domain = pattern.domain.lower()

        # Check match
        if pattern_domain in detected_domains or not detected_domains:
            passed = True
            confidence = 1.0
            answer = f"Domain '{pattern_domain}' is appropriate"
        else:
            passed = True  # Don't block, just warn
            confidence = 0.7
            answer = f"Domain '{pattern_domain}' may not match context (detected: {detected_domains})"

        return QuestionResult(
            question_type=QuestionType.DOMAIN_MATCH,
            question=question,
            answer=answer,
            passed=passed,
            confidence=confidence,
            details={
                "pattern_domain": pattern_domain,
                "detected_domains": detected_domains,
            },
        )

    def _ask_edge_cases(
        self,
        pattern: Node,
        context: str,
    ) -> QuestionResult:
        """Ask: Are there known edge cases?"""
        question = "Are there known edge cases to consider?"

        # Check metadata for edge cases
        edge_cases = pattern.metadata.get("edge_cases", [])
        known_issues = pattern.metadata.get("known_issues", [])

        all_issues = edge_cases + known_issues

        if not all_issues:
            return QuestionResult(
                question_type=QuestionType.EDGE_CASES,
                question=question,
                answer="No known edge cases",
                passed=True,
                confidence=1.0,
                details={"edge_cases": []},
            )

        confidence = 1.0 - (0.1 * len(all_issues))
        confidence = max(0.5, confidence)
        passed = len(all_issues) < 3

        answer = f"{len(all_issues)} known edge cases"

        return QuestionResult(
            question_type=QuestionType.EDGE_CASES,
            question=question,
            answer=answer,
            passed=passed,
            confidence=confidence,
            details={"edge_cases": all_issues},
        )

    def _ask_prerequisites(
        self,
        pattern: Node,
        context: str,
        graph: Optional[PatternGraph],
    ) -> QuestionResult:
        """Ask: Are prerequisite patterns known?"""
        question = "Are all prerequisite patterns known?"

        if not graph:
            return QuestionResult(
                question_type=QuestionType.PREREQUISITES,
                question=question,
                answer="Cannot check prerequisites without graph",
                passed=True,
                confidence=0.8,
            )

        # Get children (prerequisites)
        children = graph.get_children(pattern.node_id)
        missing = []

        for child in children:
            if not child.content:
                missing.append(child.node_id)

        if not missing:
            return QuestionResult(
                question_type=QuestionType.PREREQUISITES,
                question=question,
                answer="All prerequisites present",
                passed=True,
                confidence=1.0,
                details={"prerequisite_count": len(children)},
            )

        confidence = 1.0 - (0.2 * len(missing))
        confidence = max(0.3, confidence)
        passed = len(missing) < 2

        answer = f"{len(missing)} missing prerequisites"

        return QuestionResult(
            question_type=QuestionType.PREREQUISITES,
            question=question,
            answer=answer,
            passed=passed,
            confidence=confidence,
            details={"missing_prerequisites": missing},
        )

    def _ask_alternatives(
        self,
        pattern: Node,
        context: str,
    ) -> QuestionResult:
        """Ask: Are there better alternative patterns?"""
        question = "Are there better alternative patterns available?"

        # Check metadata for alternatives
        alternatives = pattern.metadata.get("alternatives", [])
        better_versions = pattern.metadata.get("better_versions", [])

        all_alternatives = alternatives + better_versions

        if not all_alternatives:
            return QuestionResult(
                question_type=QuestionType.ALTERNATIVES,
                question=question,
                answer="No known alternatives",
                passed=True,
                confidence=1.0,
                details={"alternatives": []},
            )

        # Having alternatives is not bad, just worth noting
        answer = f"{len(all_alternatives)} alternative patterns available"

        return QuestionResult(
            question_type=QuestionType.ALTERNATIVES,
            question=question,
            answer=answer,
            passed=True,
            confidence=0.9,
            details={"alternatives": all_alternatives},
        )

    def _get_recommendations(
        self,
        qtype: QuestionType,
        result: QuestionResult,
    ) -> List[str]:
        """Get recommendations based on question result."""
        recommendations = []

        if qtype == QuestionType.FAILURE_HISTORY and not result.passed:
            recommendations.append("Consider using an alternative pattern")
            recommendations.append("Review failure reasons before proceeding")

        elif qtype == QuestionType.COMPLETENESS and not result.passed:
            recommendations.append("Complete missing pattern elements")
            recommendations.append("Add composition information")

        elif qtype == QuestionType.CONFIDENCE and not result.passed:
            recommendations.append("Find a higher-confidence pattern")
            recommendations.append("Flag pattern for review")

        elif qtype == QuestionType.DOMAIN_MATCH:
            recommendations.append("Verify domain appropriateness")

        elif qtype == QuestionType.EDGE_CASES and not result.passed:
            recommendations.append("Handle known edge cases explicitly")

        elif qtype == QuestionType.PREREQUISITES and not result.passed:
            recommendations.append("Learn missing prerequisite patterns")

        return recommendations
