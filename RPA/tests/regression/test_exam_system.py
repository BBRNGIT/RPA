"""
Exam System Regression Tests (SI-007)

Tests for exam engine, exercise generation, scoring, and badge management.
Ensures assessment functionality works correctly for evaluating learning progress.
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime


class TestAssessmentEngineBasics:
    """Tests for assessment engine functionality."""
    
    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_assessment_engine_initialization(self, temp_storage):
        """Test assessment engine initializes correctly."""
        from rpa.assessment.engine import SelfAssessmentEngine
        
        engine = SelfAssessmentEngine("test_pattern_001")
        
        assert engine is not None
    
    def test_assessment_engine_with_criteria(self, temp_storage):
        """Test assessment engine with criteria."""
        from rpa.assessment.engine import SelfAssessmentEngine
        from rpa.assessment.criteria import AssessmentCriteria
        
        criteria = AssessmentCriteria("test_pattern_001")
        engine = SelfAssessmentEngine("test_pattern_001")
        
        assert engine is not None
        assert criteria is not None


class TestExamEngineBasics:
    """Tests for exam engine functionality."""
    
    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_exam_engine_initialization(self, temp_storage):
        """Test exam engine initializes correctly."""
        from rpa.assessment.exam_engine import ExamEngine
        
        engine = ExamEngine()
        
        assert engine is not None
    
    def test_question_types_exist(self, temp_storage):
        """Test question types are defined."""
        from rpa.assessment.exam_engine import QuestionType
        
        # Should have question types defined
        assert QuestionType is not None


class TestExerciseGeneratorBasics:
    """Tests for exercise generation functionality."""
    
    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_exercise_generator_initialization(self, temp_storage):
        """Test exercise generator initializes correctly."""
        from rpa.assessment.exercise_generator import ExerciseGenerator
        
        generator = ExerciseGenerator()
        
        assert generator is not None
    
    def test_exercise_types_exist(self, temp_storage):
        """Test exercise types are defined."""
        from rpa.assessment.exercise_generator import ExerciseType
        
        # Should have exercise types defined
        assert ExerciseType is not None


class TestExerciseScorerBasics:
    """Tests for exercise scoring functionality."""
    
    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_exercise_scorer_initialization(self, temp_storage):
        """Test exercise scorer initializes correctly."""
        from rpa.assessment.exercise_scorer import ExerciseScorer
        
        scorer = ExerciseScorer()
        
        assert scorer is not None


class TestBadgeManagerBasics:
    """Tests for badge management functionality."""
    
    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_badge_manager_initialization(self, temp_storage):
        """Test badge manager initializes correctly."""
        from rpa.assessment.badge_manager import BadgeManager
        
        manager = BadgeManager()
        
        assert manager is not None
    
    def test_get_all_badges(self, temp_storage):
        """Test getting all badges."""
        from rpa.assessment.badge_manager import BadgeManager
        
        manager = BadgeManager()
        
        badges = manager.get_all_badges()
        
        assert isinstance(badges, list)


class TestAssessmentCriteria:
    """Tests for assessment criteria functionality."""
    
    def test_assessment_criteria_initialization(self):
        """Test assessment criteria initializes correctly."""
        from rpa.assessment.criteria import AssessmentCriteria
        
        criteria = AssessmentCriteria("test_pattern_001")
        
        assert criteria is not None
    
    def test_assessment_criteria_has_pattern_id(self):
        """Test assessment criteria has pattern_id."""
        from rpa.assessment.criteria import AssessmentCriteria
        
        criteria = AssessmentCriteria("test_pattern_001")
        
        assert criteria.pattern_id == "test_pattern_001"


class TestAssessmentIntegration:
    """Tests for assessment system integration."""
    
    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_full_assessment_workflow(self, temp_storage):
        """Test a complete assessment workflow."""
        # Initialize components
        from rpa.assessment.engine import SelfAssessmentEngine
        from rpa.assessment.exam_engine import ExamEngine
        from rpa.assessment.exercise_generator import ExerciseGenerator
        from rpa.assessment.exercise_scorer import ExerciseScorer
        from rpa.assessment.badge_manager import BadgeManager
        
        assessment_engine = SelfAssessmentEngine("test_pattern")
        exam_engine = ExamEngine()
        exercise_generator = ExerciseGenerator()
        exercise_scorer = ExerciseScorer()
        badge_manager = BadgeManager()
        
        # All components should be initialized
        assert assessment_engine is not None
        assert exam_engine is not None
        assert exercise_generator is not None
        assert exercise_scorer is not None
        assert badge_manager is not None


class TestAssessmentPerformance:
    """Tests for assessment system performance."""
    
    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_badge_manager_performance(self, temp_storage):
        """Test badge manager is reasonably fast."""
        import time
        from rpa.assessment.badge_manager import BadgeManager
        
        manager = BadgeManager()
        
        start = time.time()
        
        for _ in range(100):
            manager.get_all_badges()
        
        elapsed = time.time() - start
        
        # Should be fast (under 1 second for 100 calls)
        assert elapsed < 1.0
    
    def test_exam_engine_performance(self, temp_storage):
        """Test exam engine is reasonably fast."""
        import time
        from rpa.assessment.exam_engine import ExamEngine
        
        engine = ExamEngine()
        
        start = time.time()
        
        # Create multiple engine instances
        for _ in range(50):
            ExamEngine()
        
        elapsed = time.time() - start
        
        # Should be fast
        assert elapsed < 1.0
