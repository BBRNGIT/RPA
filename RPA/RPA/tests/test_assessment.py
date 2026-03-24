"""
Tests for RPA Assessment module.
"""

import pytest

from rpa.core.graph import Node, PatternGraph, NodeType
from rpa.assessment.criteria import AssessmentCriteria, DEFAULT_CRITERIA
from rpa.assessment.exercise_generator import ExerciseGenerator, Exercise, ExerciseType
from rpa.assessment.exercise_scorer import ExerciseScorer, ExerciseScore
from rpa.assessment.engine import SelfAssessmentEngine, AssessmentResult
from tests.fixtures import word_graph, full_english_graph


class TestAssessmentCriteria:
    """Tests for AssessmentCriteria."""
    
    def test_create_basic_criteria(self):
        """Test creating basic assessment criteria."""
        criteria = AssessmentCriteria.create_basic("test_pattern")
        
        assert criteria.pattern_id == "test_pattern"
        assert len(criteria.criteria) == 3
        assert criteria.required_pass_rate == 0.7
    
    def test_create_comprehensive_criteria(self):
        """Test creating comprehensive assessment criteria."""
        criteria = AssessmentCriteria.create_comprehensive("test_pattern")
        
        assert criteria.pattern_id == "test_pattern"
        assert len(criteria.criteria) == 9
        assert criteria.required_pass_rate == 0.8
    
    def test_create_code_criteria(self):
        """Test creating code-specific criteria."""
        criteria = AssessmentCriteria.create_for_code("test_code")
        
        assert "error_detection" in criteria.get_criteria_types()
    
    def test_criteria_weights_normalized(self):
        """Test that criteria weights are normalized."""
        # Create criteria with unnormalized weights
        criteria = AssessmentCriteria(
            pattern_id="test",
            criteria=[
                {"type": "reconstruct", "weight": 2.0},
                {"type": "recognize", "weight": 2.0},
            ],
        )
        
        total_weight = sum(c["weight"] for c in criteria.criteria)
        assert abs(total_weight - 1.0) < 0.01
    
    def test_criteria_serialization(self):
        """Test criteria serialization."""
        criteria = AssessmentCriteria.create_basic("test")
        
        data = criteria.to_dict()
        restored = AssessmentCriteria.from_dict(data)
        
        assert restored.pattern_id == criteria.pattern_id
        assert restored.required_pass_rate == criteria.required_pass_rate
    
    def test_default_criteria(self):
        """Test default criteria dictionary."""
        assert "primitive" in DEFAULT_CRITERIA
        assert "word" in DEFAULT_CRITERIA
        assert "sentence" in DEFAULT_CRITERIA
        assert "code" in DEFAULT_CRITERIA


class TestExerciseGenerator:
    """Tests for ExerciseGenerator."""
    
    def test_generate_primitive_exercises(self, word_graph: PatternGraph):
        """Test generating exercises for a primitive."""
        generator = ExerciseGenerator(seed=42)
        
        node = word_graph.get_node("primitive:a")
        exercises = generator.generate_exercises(node, word_graph)
        
        assert len(exercises) > 0
        assert all(e.pattern_id == "primitive:a" for e in exercises)
    
    def test_generate_word_exercises(self, word_graph: PatternGraph):
        """Test generating exercises for a word pattern."""
        generator = ExerciseGenerator(seed=42)
        
        node = word_graph.get_node("pattern:cat")
        exercises = generator.generate_exercises(node, word_graph, count=5)
        
        assert len(exercises) >= 5
        
        # Check exercise types
        types = [e.exercise_type for e in exercises]
        assert ExerciseType.RECONSTRUCT in types or ExerciseType.RECOGNIZE in types
    
    def test_generate_specific_exercise_types(self, word_graph: PatternGraph):
        """Test generating specific exercise types."""
        generator = ExerciseGenerator(seed=42)
        
        node = word_graph.get_node("pattern:cat")
        exercises = generator.generate_exercises(
            node, 
            word_graph,
            exercise_types=[ExerciseType.RECONSTRUCT, ExerciseType.DECOMPOSE],
            count=4,
        )
        
        types = set(e.exercise_type for e in exercises)
        assert types.issubset({ExerciseType.RECONSTRUCT, ExerciseType.DECOMPOSE})
    
    def test_reconstruct_exercise(self, word_graph: PatternGraph):
        """Test reconstruct exercise generation."""
        generator = ExerciseGenerator()
        
        node = word_graph.get_node("pattern:cat")
        exercise = generator._generate_reconstruct(node, word_graph)
        
        assert exercise is not None
        assert exercise.exercise_type == ExerciseType.RECONSTRUCT
        assert exercise.expected_answer == "cat"
    
    def test_recognize_exercise(self, word_graph: PatternGraph):
        """Test recognize exercise generation."""
        generator = ExerciseGenerator()
        
        node = word_graph.get_node("pattern:cat")
        exercise = generator._generate_recognize(node, word_graph)
        
        assert exercise is not None
        assert exercise.exercise_type == ExerciseType.RECOGNIZE
        assert exercise.expected_answer == "cat"
        assert len(exercise.options) == 4  # Multiple choice
        assert "cat" in exercise.options
    
    def test_decompose_exercise(self, word_graph: PatternGraph):
        """Test decompose exercise generation."""
        generator = ExerciseGenerator()
        
        node = word_graph.get_node("pattern:cat")
        exercise = generator._generate_decompose(node, word_graph)
        
        assert exercise is not None
        assert exercise.exercise_type == ExerciseType.DECOMPOSE
        # Should list the component characters
        assert "c" in exercise.expected_answer.lower()
    
    def test_exercise_serialization(self):
        """Test exercise serialization."""
        exercise = Exercise(
            exercise_id="test_ex",
            exercise_type=ExerciseType.RECONSTRUCT,
            pattern_id="test_pattern",
            prompt="Test prompt",
            expected_answer="test",
        )
        
        data = exercise.to_dict()
        restored = Exercise.from_dict(data)
        
        assert restored.exercise_id == exercise.exercise_id
        assert restored.exercise_type == exercise.exercise_type


class TestExerciseScorer:
    """Tests for ExerciseScorer."""
    
    def test_score_correct_answer(self):
        """Test scoring a correct answer."""
        scorer = ExerciseScorer()
        
        exercise = Exercise(
            exercise_id="test",
            exercise_type=ExerciseType.RECONSTRUCT,
            pattern_id="test",
            prompt="Test",
            expected_answer="cat",
        )
        
        score = scorer.score_exercise(exercise, "cat")
        
        assert score.is_correct is True
        assert score.score == 1.0
    
    def test_score_incorrect_answer(self):
        """Test scoring an incorrect answer."""
        scorer = ExerciseScorer()
        
        exercise = Exercise(
            exercise_id="test",
            exercise_type=ExerciseType.RECONSTRUCT,
            pattern_id="test",
            prompt="Test",
            expected_answer="cat",
        )
        
        score = scorer.score_exercise(exercise, "dog")
        
        assert score.is_correct is False
        assert score.score < 1.0
    
    def test_score_partial_answer(self):
        """Test scoring a partially correct answer."""
        scorer = ExerciseScorer()
        
        exercise = Exercise(
            exercise_id="test",
            exercise_type=ExerciseType.RECONSTRUCT,
            pattern_id="test",
            prompt="Test",
            expected_answer="cat",
        )
        
        score = scorer.score_exercise(exercise, "ca")  # Missing one letter
        
        assert score.score > 0
        assert len(score.issues) > 0
    
    def test_score_case_insensitive(self):
        """Test case-insensitive scoring."""
        scorer = ExerciseScorer(case_sensitive=False)
        
        exercise = Exercise(
            exercise_id="test",
            exercise_type=ExerciseType.RECONSTRUCT,
            pattern_id="test",
            prompt="Test",
            expected_answer="Cat",
        )
        
        score = scorer.score_exercise(exercise, "cat")
        
        assert score.is_correct is True
    
    def test_score_composition_exercise(self):
        """Test scoring a composition exercise."""
        scorer = ExerciseScorer()
        
        exercise = Exercise(
            exercise_id="test",
            exercise_type=ExerciseType.COMPOSE,
            pattern_id="test",
            prompt="Test",
            expected_answer="a, b, c",
        )
        
        # Correct components, different order
        score = scorer.score_exercise(exercise, "c, b, a")
        
        assert score.is_correct is True
        assert score.score >= 0.9
    
    def test_aggregate_scores(self):
        """Test aggregating multiple scores."""
        scorer = ExerciseScorer()
        
        scores = [
            ExerciseScore(
                exercise_id="ex1",
                exercise_type=ExerciseType.RECONSTRUCT,
                is_correct=True,
                score=1.0,
                expected="a",
                provided="a",
                feedback="",
            ),
            ExerciseScore(
                exercise_id="ex2",
                exercise_type=ExerciseType.RECOGNIZE,
                is_correct=True,
                score=1.0,
                expected="a",
                provided="a",
                feedback="",
            ),
            ExerciseScore(
                exercise_id="ex3",
                exercise_type=ExerciseType.DECOMPOSE,
                is_correct=False,
                score=0.5,
                expected="a, b",
                provided="a",
                feedback="",
            ),
        ]
        
        aggregated = scorer.aggregate_exercise_scores(scores)
        
        assert aggregated["correct_count"] == 2
        assert aggregated["total_exercises"] == 3
        assert aggregated["overall_score"] > 0.5
        assert len(aggregated["strengths"]) >= 0
    
    def test_aggregate_with_weights(self):
        """Test aggregating scores with custom weights."""
        scorer = ExerciseScorer()
        
        scores = [
            ExerciseScore(
                exercise_id="ex1",
                exercise_type=ExerciseType.RECONSTRUCT,
                is_correct=True,
                score=1.0,
                expected="a",
                provided="a",
                feedback="",
            ),
            ExerciseScore(
                exercise_id="ex2",
                exercise_type=ExerciseType.RECOGNIZE,
                is_correct=False,
                score=0.0,
                expected="a",
                provided="b",
                feedback="",
            ),
        ]
        
        weights = {
            "reconstruct": 0.7,  # Higher weight
            "recognize": 0.3,
        }
        
        aggregated = scorer.aggregate_exercise_scores(scores, weights)
        
        # Reconstruct (correct, weight 0.7) should dominate
        assert aggregated["overall_score"] > 0.5


class TestSelfAssessmentEngine:
    """Tests for SelfAssessmentEngine."""
    
    def test_assess_primitive(self, word_graph: PatternGraph):
        """Test assessing a primitive pattern."""
        engine = SelfAssessmentEngine()
        
        node = word_graph.get_node("primitive:a")
        result = engine.assess_pattern(node, word_graph)
        
        assert result.node_id == "primitive:a"
        assert result.recursive_depth == 0
    
    def test_assess_word_pattern(self, word_graph: PatternGraph):
        """Test assessing a word pattern."""
        engine = SelfAssessmentEngine()
        
        node = word_graph.get_node("pattern:cat")
        result = engine.assess_pattern(node, word_graph, num_exercises=5)
        
        assert result.node_id == "pattern:cat"
        assert len(result.exercises) >= 5
        assert result.pass_rate >= 0.0
        assert result.recursive_depth >= 1
    
    def test_assess_with_custom_criteria(self, word_graph: PatternGraph):
        """Test assessment with custom criteria."""
        engine = SelfAssessmentEngine()
        
        criteria = AssessmentCriteria.create_basic("pattern:cat")
        node = word_graph.get_node("pattern:cat")
        
        result = engine.assess_pattern(node, word_graph, criteria=criteria)
        
        assert result is not None
    
    def test_assess_batch(self, word_graph: PatternGraph):
        """Test batch assessment."""
        engine = SelfAssessmentEngine()
        
        node_ids = ["primitive:a", "primitive:b", "pattern:cat"]
        
        results = engine.assess_batch(node_ids, word_graph)
        
        assert results["total"] == 3
        assert results["passed"] >= 0
        assert "average_score" in results
    
    def test_assessment_history(self, word_graph: PatternGraph):
        """Test assessment history tracking."""
        engine = SelfAssessmentEngine()
        
        node = word_graph.get_node("pattern:cat")
        
        # Assess multiple times
        engine.assess_pattern(node, word_graph)
        engine.assess_pattern(node, word_graph)
        
        history = engine.get_assessment_history("pattern:cat")
        
        assert len(history) == 2
    
    def test_get_latest_assessment(self, word_graph: PatternGraph):
        """Test getting latest assessment."""
        engine = SelfAssessmentEngine()
        
        node = word_graph.get_node("pattern:cat")
        result1 = engine.assess_pattern(node, word_graph)
        result2 = engine.assess_pattern(node, word_graph)
        
        latest = engine.get_latest_assessment("pattern:cat")
        
        assert latest.result_id == result2.result_id
    
    def test_assessment_result_serialization(self, word_graph: PatternGraph):
        """Test assessment result serialization."""
        engine = SelfAssessmentEngine()
        
        node = word_graph.get_node("pattern:cat")
        result = engine.assess_pattern(node, word_graph)
        
        data = result.to_dict()
        
        assert "result_id" in data
        assert "node_id" in data
        assert "is_valid" in data
        assert "pass_rate" in data
    
    def test_clear_history(self, word_graph: PatternGraph):
        """Test clearing assessment history."""
        engine = SelfAssessmentEngine()
        
        node = word_graph.get_node("pattern:cat")
        engine.assess_pattern(node, word_graph)
        
        engine.clear_history()
        
        history = engine.get_assessment_history("pattern:cat")
        assert len(history) == 0
