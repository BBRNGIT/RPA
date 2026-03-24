"""
Exercise scoring for RPA assessment.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .exercise_generator import Exercise, ExerciseType


@dataclass
class ExerciseScore:
    """Score for a single exercise."""
    exercise_id: str
    exercise_type: ExerciseType
    is_correct: bool
    score: float
    expected: str
    provided: str
    feedback: str
    issues: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "exercise_id": self.exercise_id,
            "exercise_type": self.exercise_type.value,
            "is_correct": self.is_correct,
            "score": self.score,
            "expected": self.expected,
            "provided": self.provided,
            "feedback": self.feedback,
            "issues": self.issues,
        }


class ExerciseScorer:
    """
    Scores exercise responses and provides detailed feedback.
    
    The ExerciseScorer evaluates responses against expected answers,
    providing partial credit and actionable feedback.
    """
    
    def __init__(self, case_sensitive: bool = False):
        """
        Initialize the ExerciseScorer.
        
        Args:
            case_sensitive: Whether to use case-sensitive comparison
        """
        self.case_sensitive = case_sensitive
    
    def score_exercise(
        self,
        exercise: Exercise,
        response: str,
    ) -> ExerciseScore:
        """
        Score an exercise response.
        
        Args:
            exercise: The exercise to score
            response: The user's response
            
        Returns:
            ExerciseScore with detailed results
        """
        expected = exercise.expected_answer
        provided = response.strip()
        
        # Normalize for comparison
        if not self.case_sensitive:
            expected_normalized = expected.lower()
            provided_normalized = provided.lower()
        else:
            expected_normalized = expected
            provided_normalized = provided
        
        # Calculate base score
        is_correct, score, feedback, issues = self._evaluate_response(
            exercise.exercise_type,
            expected,
            expected_normalized,
            provided,
            provided_normalized,
        )
        
        return ExerciseScore(
            exercise_id=exercise.exercise_id,
            exercise_type=exercise.exercise_type,
            is_correct=is_correct,
            score=score,
            expected=expected,
            provided=provided,
            feedback=feedback,
            issues=issues,
        )
    
    def _evaluate_response(
        self,
        exercise_type: ExerciseType,
        expected: str,
        expected_normalized: str,
        provided: str,
        provided_normalized: str,
    ) -> tuple:
        """
        Evaluate a response based on exercise type.
        
        Returns:
            Tuple of (is_correct, score, feedback, issues)
        """
        issues = []
        
        # Exact match
        if expected_normalized == provided_normalized:
            return (
                True,
                1.0,
                "Correct! Well done.",
                [],
            )
        
        # Partial credit based on exercise type
        if exercise_type == ExerciseType.RECONSTRUCT:
            return self._score_reconstruction(
                expected, expected_normalized, provided, provided_normalized
            )
        
        elif exercise_type == ExerciseType.RECOGNIZE:
            return self._score_recognition(
                expected, expected_normalized, provided, provided_normalized
            )
        
        elif exercise_type == ExerciseType.COMPOSE:
            return self._score_composition(
                expected, expected_normalized, provided, provided_normalized
            )
        
        elif exercise_type == ExerciseType.DECOMPOSE:
            return self._score_decomposition(
                expected, expected_normalized, provided, provided_normalized
            )
        
        elif exercise_type == ExerciseType.RECURSIVE_RECALL:
            return self._score_recursive_recall(
                expected, expected_normalized, provided, provided_normalized
            )
        
        elif exercise_type == ExerciseType.CONTEXTUAL_USAGE:
            return self._score_contextual_usage(
                expected, expected_normalized, provided, provided_normalized
            )
        
        elif exercise_type == ExerciseType.ERROR_DETECTION:
            return self._score_error_detection(
                expected, expected_normalized, provided, provided_normalized
            )
        
        else:
            # Generic partial credit
            similarity = self._calculate_similarity(expected_normalized, provided_normalized)
            if similarity > 0.8:
                return (
                    True,
                    similarity,
                    f"Close! Your answer is mostly correct ({similarity*100:.0f}% match).",
                    [f"Expected: {expected}"],
                )
            else:
                return (
                    False,
                    similarity,
                    f"Incorrect. Your answer matches {similarity*100:.0f}%.",
                    [f"Expected: {expected}", f"Your answer: {provided}"],
                )
    
    def _score_reconstruction(
        self,
        expected: str,
        expected_normalized: str,
        provided: str,
        provided_normalized: str,
    ) -> tuple:
        """Score a reconstruction exercise."""
        # Check for exact match
        if expected_normalized == provided_normalized:
            return (True, 1.0, "Correct reconstruction!", [])
        
        # Check for character-level similarity
        similarity = self._calculate_similarity(expected_normalized, provided_normalized)
        
        # Check for common errors
        issues = []
        
        # Missing characters
        missing = set(expected_normalized) - set(provided_normalized)
        if missing:
            issues.append(f"Missing characters: {', '.join(sorted(missing))}")
        
        # Extra characters
        extra = set(provided_normalized) - set(expected_normalized)
        if extra:
            issues.append(f"Extra characters: {', '.join(sorted(extra))}")
        
        # Wrong order
        if sorted(expected_normalized) == sorted(provided_normalized):
            issues.append("Characters are correct but in wrong order")
            return (
                False,
                0.5,
                "Characters are correct but order is wrong.",
                issues,
            )
        
        if similarity > 0.5:
            return (
                False,
                similarity,
                f"Partially correct. {similarity*100:.0f}% match.",
                issues + [f"Expected: {expected}"],
            )
        
        return (
            False,
            similarity,
            "Incorrect reconstruction.",
            issues + [f"Expected: {expected}", f"Your answer: {provided}"],
        )
    
    def _score_recognition(
        self,
        expected: str,
        expected_normalized: str,
        provided: str,
        provided_normalized: str,
    ) -> tuple:
        """Score a recognition exercise."""
        if expected_normalized == provided_normalized:
            return (True, 1.0, "Correct recognition!", [])
        
        # Partial match
        if expected_normalized in provided_normalized or provided_normalized in expected_normalized:
            return (
                False,
                0.5,
                "Partially correct - pattern is related but not exact match.",
                [f"Expected: {expected}"],
            )
        
        return (
            False,
            0.0,
            "Incorrect pattern identified.",
            [f"Expected: {expected}", f"Your answer: {provided}"],
        )
    
    def _score_composition(
        self,
        expected: str,
        expected_normalized: str,
        provided: str,
        provided_normalized: str,
    ) -> tuple:
        """Score a composition exercise."""
        if expected_normalized == provided_normalized:
            return (True, 1.0, "Correct composition!", [])
        
        # Check if components are correct but order differs
        expected_parts = set(p.strip() for p in expected_normalized.split(","))
        provided_parts = set(p.strip() for p in provided_normalized.split(","))
        
        if expected_parts == provided_parts:
            return (
                True,
                0.9,
                "Correct components! Order may vary.",
                [],
            )
        
        # Calculate overlap
        overlap = len(expected_parts & provided_parts)
        total = max(len(expected_parts), len(provided_parts))
        score = overlap / total if total > 0 else 0
        
        missing = expected_parts - provided_parts
        extra = provided_parts - expected_parts
        
        issues = []
        if missing:
            issues.append(f"Missing components: {', '.join(missing)}")
        if extra:
            issues.append(f"Extra components: {', '.join(extra)}")
        
        return (
            False,
            score,
            f"Partially correct. {overlap}/{total} components correct.",
            issues,
        )
    
    def _score_decomposition(
        self,
        expected: str,
        expected_normalized: str,
        provided: str,
        provided_normalized: str,
    ) -> tuple:
        """Score a decomposition exercise."""
        return self._score_composition(
            expected, expected_normalized, provided, provided_normalized
        )
    
    def _score_recursive_recall(
        self,
        expected: str,
        expected_normalized: str,
        provided: str,
        provided_normalized: str,
    ) -> tuple:
        """Score a recursive recall exercise."""
        if expected_normalized == provided_normalized:
            return (True, 1.0, "Correct! All descendants recalled.", [])
        
        # Check partial recall
        expected_items = set(p.strip() for p in expected_normalized.split(","))
        provided_items = set(p.strip() for p in provided_normalized.split(","))
        
        overlap = len(expected_items & provided_items)
        total = len(expected_items)
        score = overlap / total if total > 0 else 0
        
        missing = expected_items - provided_items
        extra = provided_items - expected_items
        
        issues = []
        if missing:
            issues.append(f"Missing descendants: {', '.join(sorted(missing))}")
        if extra:
            issues.append(f"Extra items (not descendants): {', '.join(sorted(extra))}")
        
        if score > 0.8:
            return (
                True,
                score,
                f"Good recall! {overlap}/{total} descendants correct.",
                issues,
            )
        
        return (
            False,
            score,
            f"Partial recall. {overlap}/{total} descendants correct.",
            issues + [f"Expected: {expected}"],
        )
    
    def _score_contextual_usage(
        self,
        expected: str,
        expected_normalized: str,
        provided: str,
        provided_normalized: str,
    ) -> tuple:
        """Score a contextual usage exercise."""
        # Contextual usage is open-ended
        # Check if the response is non-empty and reasonably long
        if not provided_normalized:
            return (
                False,
                0.0,
                "No response provided.",
                ["Please provide an example usage."],
            )
        
        # Basic validation - response should be at least a few words
        words = provided_normalized.split()
        if len(words) < 3:
            return (
                False,
                0.3,
                "Response too short. Please provide a more complete example.",
                ["Response should be at least 3 words."],
            )
        
        # For open-ended exercises, give benefit of the doubt
        return (
            True,
            0.8,
            "Thank you for the example!",
            [],
        )
    
    def _score_error_detection(
        self,
        expected: str,
        expected_normalized: str,
        provided: str,
        provided_normalized: str,
    ) -> tuple:
        """Score an error detection exercise."""
        if expected_normalized == provided_normalized:
            return (True, 1.0, "Correct error identified!", [])
        
        # Check if key error terms are mentioned
        similarity = self._calculate_similarity(expected_normalized, provided_normalized)
        
        if similarity > 0.5:
            return (
                True,
                similarity,
                "Good error detection! Your explanation is partially correct.",
                [f"Expected answer: {expected}"],
            )
        
        return (
            False,
            similarity,
            "Error not correctly identified.",
            [f"Expected: {expected}", f"Your answer: {provided}"],
        )
    
    def _calculate_similarity(self, s1: str, s2: str) -> float:
        """
        Calculate similarity between two strings.
        
        Uses Levenshtein distance-based similarity.
        """
        if not s1 or not s2:
            return 0.0
        
        # Simple character-level similarity
        # For more accuracy, could use Levenshtein distance
        
        # Calculate Jaccard similarity on character sets
        set1 = set(s1)
        set2 = set(s2)
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        if union == 0:
            return 0.0
        
        jaccard = intersection / union
        
        # Also consider length similarity
        len_ratio = min(len(s1), len(s2)) / max(len(s1), len(s2))
        
        # Combined score
        return (jaccard + len_ratio) / 2
    
    def aggregate_exercise_scores(
        self,
        scores: List[ExerciseScore],
        weights: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """
        Aggregate scores from multiple exercises.
        
        Args:
            scores: List of exercise scores
            weights: Optional weights by exercise type
            
        Returns:
            Aggregated score summary
        """
        if not scores:
            return {
                "overall_score": 0.0,
                "by_type": {},
                "strengths": [],
                "weaknesses": [],
            }
        
        # Calculate scores by type
        by_type: Dict[str, List[float]] = {}
        for score in scores:
            type_name = score.exercise_type.value
            if type_name not in by_type:
                by_type[type_name] = []
            by_type[type_name].append(score.score)
        
        # Calculate average by type
        type_averages = {
            t: sum(s) / len(s) 
            for t, s in by_type.items()
        }
        
        # Calculate weighted overall score
        if weights:
            total_weight = 0
            weighted_sum = 0
            for type_name, avg_score in type_averages.items():
                weight = weights.get(type_name, 1.0)
                weighted_sum += avg_score * weight
                total_weight += weight
            overall = weighted_sum / total_weight if total_weight > 0 else 0
        else:
            overall = sum(score.score for score in scores) / len(scores)
        
        # Identify strengths and weaknesses
        strengths = []
        weaknesses = []
        
        for type_name, avg_score in sorted(type_averages.items(), key=lambda x: -x[1]):
            if avg_score >= 0.8:
                strengths.append(f"{type_name}: {avg_score*100:.0f}%")
            elif avg_score < 0.6:
                weaknesses.append(f"{type_name}: {avg_score*100:.0f}%")
        
        return {
            "overall_score": overall,
            "pass_rate": sum(1 for s in scores if s.is_correct) / len(scores),
            "by_type": type_averages,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "total_exercises": len(scores),
            "correct_count": sum(1 for s in scores if s.is_correct),
        }
