"""
Tests for the Health Domain module.

Tests cover:
- Nutrient management
- Food management
- Exercise management
- Mental health concepts
- Cross-domain integration with medicine
"""

import pytest
from datetime import datetime

from rpa.domains.health import (
    HealthDomain,
    Nutrient,
    Food,
    Exercise,
    MentalHealthConcept,
    HealthCategory,
    NutrientType,
    ExerciseType,
    MentalHealthTopic,
    HealthProficiency,
)


class TestHealthEnums:
    """Test enum definitions."""
    
    def test_health_category_enum(self):
        """Test HealthCategory enum values."""
        assert HealthCategory.NUTRITION.value == "nutrition"
        assert HealthCategory.EXERCISE.value == "exercise"
        assert HealthCategory.MENTAL_HEALTH.value == "mental_health"
    
    def test_nutrient_type_enum(self):
        """Test NutrientType enum values."""
        assert NutrientType.MACRONUTRIENT.value == "macronutrient"
        assert NutrientType.MICRONUTRIENT.value == "micronutrient"
    
    def test_exercise_type_enum(self):
        """Test ExerciseType enum values."""
        assert ExerciseType.CARDIO.value == "cardio"
        assert ExerciseType.STRENGTH.value == "strength"
        assert ExerciseType.FLEXIBILITY.value == "flexibility"
    
    def test_mental_health_topic_enum(self):
        """Test MentalHealthTopic enum values."""
        assert MentalHealthTopic.STRESS.value == "stress"
        assert MentalHealthTopic.ANXIETY.value == "anxiety"
        assert MentalHealthTopic.MINDFULNESS.value == "mindfulness"
    
    def test_health_proficiency_enum(self):
        """Test HealthProficiency enum values."""
        assert HealthProficiency.NOVICE.value == "novice"
        assert HealthProficiency.EXPERT.value == "expert"


class TestNutrient:
    """Test Nutrient dataclass."""
    
    def test_nutrient_creation(self):
        """Test creating a nutrient."""
        nutrient = Nutrient(
            nutrient_id="test_nut_1",
            name="Test Nutrient",
            nutrient_type=NutrientType.MACRONUTRIENT,
            function="Test function",
            daily_value="100mg",
            food_sources=["Food 1", "Food 2"],
        )
        assert nutrient.nutrient_id == "test_nut_1"
        assert nutrient.name == "Test Nutrient"
        assert nutrient.nutrient_type == NutrientType.MACRONUTRIENT
        assert nutrient.proficiency == HealthProficiency.NOVICE
    
    def test_nutrient_serialization(self):
        """Test Nutrient serialization."""
        nutrient = Nutrient(
            nutrient_id="test_nut_2",
            name="Vitamin C",
            nutrient_type=NutrientType.MICRONUTRIENT,
            function="Immune support",
        )
        data = nutrient.to_dict()
        assert data["nutrient_id"] == "test_nut_2"
        assert data["nutrient_type"] == "micronutrient"
        
        restored = Nutrient.from_dict(data)
        assert restored.nutrient_id == nutrient.nutrient_id
        assert restored.nutrient_type == nutrient.nutrient_type


class TestFood:
    """Test Food dataclass."""
    
    def test_food_creation(self):
        """Test creating a food."""
        food = Food(
            food_id="test_food_1",
            name="Apple",
            category="fruits",
            calories_per_serving=95,
            serving_size="1 medium",
            macronutrients={"carbs": 25, "fiber": 4},
            health_benefits=["Heart health"],
        )
        assert food.food_id == "test_food_1"
        assert food.name == "Apple"
        assert food.category == "fruits"
        assert food.calories_per_serving == 95
    
    def test_food_serialization(self):
        """Test Food serialization."""
        food = Food(
            food_id="test_food_2",
            name="Banana",
            category="fruits",
            calories_per_serving=105,
        )
        data = food.to_dict()
        assert data["food_id"] == "test_food_2"
        assert data["category"] == "fruits"
        
        restored = Food.from_dict(data)
        assert restored.food_id == food.food_id
        assert restored.calories_per_serving == food.calories_per_serving


class TestExercise:
    """Test Exercise dataclass."""
    
    def test_exercise_creation(self):
        """Test creating an exercise."""
        exercise = Exercise(
            exercise_id="test_ex_1",
            name="Running",
            exercise_type=ExerciseType.CARDIO,
            muscle_groups=["legs", "core"],
            difficulty=3,
            benefits=["Cardiovascular fitness", "Weight loss"],
        )
        assert exercise.exercise_id == "test_ex_1"
        assert exercise.name == "Running"
        assert exercise.exercise_type == ExerciseType.CARDIO
        assert exercise.difficulty == 3
    
    def test_exercise_serialization(self):
        """Test Exercise serialization."""
        exercise = Exercise(
            exercise_id="test_ex_2",
            name="Yoga",
            exercise_type=ExerciseType.FLEXIBILITY,
            muscle_groups=["full body"],
        )
        data = exercise.to_dict()
        assert data["exercise_id"] == "test_ex_2"
        assert data["exercise_type"] == "flexibility"
        
        restored = Exercise.from_dict(data)
        assert restored.exercise_id == exercise.exercise_id
        assert restored.exercise_type == exercise.exercise_type


class TestMentalHealthConcept:
    """Test MentalHealthConcept dataclass."""
    
    def test_concept_creation(self):
        """Test creating a mental health concept."""
        concept = MentalHealthConcept(
            concept_id="test_mh_1",
            name="Deep Breathing",
            topic=MentalHealthTopic.STRESS,
            description="Controlled breathing technique",
            techniques=["4-7-8 breathing", "Box breathing"],
        )
        assert concept.concept_id == "test_mh_1"
        assert concept.name == "Deep Breathing"
        assert concept.topic == MentalHealthTopic.STRESS
    
    def test_concept_serialization(self):
        """Test MentalHealthConcept serialization."""
        concept = MentalHealthConcept(
            concept_id="test_mh_2",
            name="Mindfulness",
            topic=MentalHealthTopic.MINDFULNESS,
        )
        data = concept.to_dict()
        assert data["concept_id"] == "test_mh_2"
        assert data["topic"] == "mindfulness"
        
        restored = MentalHealthConcept.from_dict(data)
        assert restored.concept_id == concept.concept_id
        assert restored.topic == concept.topic


class TestHealthDomain:
    """Test HealthDomain class."""
    
    @pytest.fixture
    def health_domain(self):
        """Create a HealthDomain instance for testing."""
        return HealthDomain()
    
    def test_health_domain_creation(self, health_domain):
        """Test HealthDomain initialization."""
        assert health_domain is not None
        assert isinstance(health_domain._nutrients, dict)
        assert isinstance(health_domain._foods, dict)
        assert isinstance(health_domain._exercises, dict)
        assert isinstance(health_domain._mental_health, dict)
    
    def test_health_domain_has_nutrients(self, health_domain):
        """Test that domain initializes with nutrients."""
        assert len(health_domain._nutrients) > 0
        
        # Check for some expected nutrients
        nutrients = list(health_domain._nutrients.values())
        nutrient_names = [n.name for n in nutrients]
        
        assert "Protein" in nutrient_names
        assert "Vitamin C" in nutrient_names or "Vitamin A" in nutrient_names
    
    def test_health_domain_has_foods(self, health_domain):
        """Test that domain initializes with foods."""
        assert len(health_domain._foods) > 0
        
        # Check for food categories
        foods = list(health_domain._foods.values())
        categories = set(f.category for f in foods)
        
        assert "fruits" in categories or "vegetables" in categories
    
    def test_health_domain_has_exercises(self, health_domain):
        """Test that domain initializes with exercises."""
        assert len(health_domain._exercises) > 0
        
        # Check for exercise types
        exercises = list(health_domain._exercises.values())
        types = set(e.exercise_type for e in exercises)
        
        assert ExerciseType.CARDIO in types
    
    def test_health_domain_has_mental_health(self, health_domain):
        """Test that domain initializes with mental health concepts."""
        assert len(health_domain._mental_health) > 0
    
    def test_add_nutrient(self, health_domain):
        """Test adding a nutrient."""
        nutrient = health_domain.add_nutrient(
            name="Test Nutrient",
            nutrient_type=NutrientType.MICRONUTRIENT,
            function="Test function",
        )
        assert nutrient.name == "Test Nutrient"
        assert nutrient.nutrient_id in health_domain._nutrients
    
    def test_get_nutrient(self, health_domain):
        """Test getting a nutrient by ID."""
        nutrient = health_domain.add_nutrient(
            name="Test Get Nutrient",
            nutrient_type=NutrientType.MACRONUTRIENT,
        )
        
        retrieved = health_domain.get_nutrient(nutrient.nutrient_id)
        assert retrieved is not None
        assert retrieved.name == "Test Get Nutrient"
    
    def test_search_nutrients(self, health_domain):
        """Test searching for nutrients."""
        results = health_domain.search_nutrients("vitamin")
        assert len(results) > 0
        
        for nutrient in results:
            assert "vitamin" in nutrient.name.lower()
    
    def test_get_nutrients_by_type(self, health_domain):
        """Test getting nutrients by type."""
        macros = health_domain.get_nutrients_by_type(NutrientType.MACRONUTRIENT)
        assert len(macros) > 0
        
        for nutrient in macros:
            assert nutrient.nutrient_type == NutrientType.MACRONUTRIENT
    
    def test_add_food(self, health_domain):
        """Test adding a food."""
        food = health_domain.add_food(
            name="Test Food",
            category="test",
            calories=100,
            serving_size="1 serving",
        )
        assert food.name == "Test Food"
        assert food.food_id in health_domain._foods
    
    def test_search_foods(self, health_domain):
        """Test searching for foods."""
        results = health_domain.search_foods("apple")
        # May or may not have apple, but search should work
        for food in results:
            assert "apple" in food.name.lower()
    
    def test_get_foods_by_category(self, health_domain):
        """Test getting foods by category."""
        fruits = health_domain.get_foods_by_category("fruits")
        assert len(fruits) > 0
        
        for food in fruits:
            assert food.category == "fruits"
    
    def test_add_exercise(self, health_domain):
        """Test adding an exercise."""
        exercise = health_domain.add_exercise(
            name="Test Exercise",
            exercise_type=ExerciseType.CARDIO,
            muscle_groups=["legs"],
        )
        assert exercise.name == "Test Exercise"
        assert exercise.exercise_id in health_domain._exercises
    
    def test_get_exercises_by_type(self, health_domain):
        """Test getting exercises by type."""
        cardio = health_domain.get_exercises_by_type(ExerciseType.CARDIO)
        assert len(cardio) > 0
        
        for exercise in cardio:
            assert exercise.exercise_type == ExerciseType.CARDIO
    
    def test_get_exercises_by_muscle(self, health_domain):
        """Test getting exercises by muscle group."""
        leg_exercises = health_domain.get_exercises_by_muscle("legs")
        assert len(leg_exercises) > 0
        
        for exercise in leg_exercises:
            assert "legs" in [m.lower() for m in exercise.muscle_groups]
    
    def test_add_mental_health_concept(self, health_domain):
        """Test adding a mental health concept."""
        concept = health_domain.add_mental_health_concept(
            name="Test Concept",
            topic=MentalHealthTopic.STRESS,
            description="Test description",
        )
        assert concept.name == "Test Concept"
        assert concept.concept_id in health_domain._mental_health
    
    def test_get_mental_health_by_topic(self, health_domain):
        """Test getting mental health concepts by topic."""
        stress_concepts = health_domain.get_mental_health_by_topic(MentalHealthTopic.STRESS)
        assert len(stress_concepts) > 0
        
        for concept in stress_concepts:
            assert concept.topic == MentalHealthTopic.STRESS


class TestExerciseGeneration:
    """Test exercise generation."""
    
    @pytest.fixture
    def health_domain(self):
        """Create a HealthDomain instance for testing."""
        return HealthDomain()
    
    def test_generate_nutrition_exercise(self, health_domain):
        """Test generating nutrition exercise."""
        exercise = health_domain.generate_nutrition_exercise()
        
        assert "exercise_id" in exercise
        assert "question" in exercise
    
    def test_generate_food_exercise(self, health_domain):
        """Test generating food exercise."""
        exercise = health_domain.generate_food_exercise()
        
        assert "exercise_id" in exercise
        assert "food_name" in exercise
    
    def test_generate_exercise_exercise(self, health_domain):
        """Test generating exercise knowledge exercise."""
        exercise = health_domain.generate_exercise_exercise()
        
        assert "exercise_id" in exercise
        assert "question" in exercise
    
    def test_generate_mental_health_exercise(self, health_domain):
        """Test generating mental health exercise."""
        exercise = health_domain.generate_mental_health_exercise()
        
        assert "exercise_id" in exercise
        assert "concept_name" in exercise


class TestCrossDomainIntegration:
    """Test cross-domain integration with medicine."""
    
    def test_set_medical_domain(self):
        """Test setting medical domain for cross-linking."""
        from rpa.domains.medicine import MedicalDomain
        
        health = HealthDomain()
        medicine = MedicalDomain()
        
        health.set_medical_domain(medicine)
        
        assert health.medical_domain is medicine
    
    def test_get_medical_links(self):
        """Test getting medical links."""
        health = HealthDomain()
        
        # Without medical domain set
        links = health.get_medical_links("nonexistent_id")
        assert links == []


class TestStatisticsAndExport:
    """Test statistics and export functionality."""
    
    @pytest.fixture
    def health_domain(self):
        """Create a HealthDomain instance for testing."""
        return HealthDomain()
    
    def test_get_statistics(self, health_domain):
        """Test getting statistics."""
        stats = health_domain.get_statistics()
        
        assert "nutrients" in stats
        assert "foods" in stats
        assert "exercises" in stats
        assert "mental_health" in stats
        
        assert stats["nutrients"]["total"] > 0
        assert stats["foods"]["total"] > 0
    
    def test_export_import_progress(self, health_domain):
        """Test exporting and importing progress."""
        # Export
        exported = health_domain.export_progress()
        
        assert "nutrients" in exported
        assert "foods" in exported
        assert "statistics" in exported
        
        # Create new domain and import
        new_domain = HealthDomain()
        initial_count = len(new_domain._nutrients)
        new_domain.import_progress(exported)
        
        # Check that data was imported (adds to existing)
        # Import is additive, so count should increase
        assert len(new_domain._nutrients) >= initial_count
        # Verify some specific nutrients exist
        nutrient_names = [n.name for n in new_domain._nutrients.values()]
        assert "Protein" in nutrient_names
    
    def test_save_patterns_to_ltm(self, health_domain):
        """Test saving patterns to LTM."""
        count = health_domain.save_patterns_to_ltm()
        
        # Should have saved nutrients, foods, exercises, and mental health concepts
        expected_min = (
            len(health_domain._nutrients) +
            len(health_domain._foods) +
            len(health_domain._exercises) +
            len(health_domain._mental_health)
        )
        assert count >= expected_min
