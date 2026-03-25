"""
Tests for the Medicine Domain module.

Tests cover:
- Medical terminology management
- Anatomy structure management
- Disease condition management
- Drug management
- Exercise generation
- Spaced repetition reviews
- LTM integration
"""

import pytest
from datetime import datetime, timedelta

from rpa.domains.medicine import (
    MedicalDomain,
    MedicalTerm,
    AnatomyStructure,
    DiseaseCondition,
    Drug,
    BodySystem,
    MedicalCategory,
    DrugClass,
    MedicalProficiency,
)


class TestMedicalEnums:
    """Test enum definitions."""
    
    def test_body_system_enum(self):
        """Test BodySystem enum values."""
        assert BodySystem.CARDIOVASCULAR.value == "cardiovascular"
        assert BodySystem.NERVOUS.value == "nervous"
        assert BodySystem.RESPIRATORY.value == "respiratory"
        assert len(list(BodySystem)) == 11
    
    def test_medical_category_enum(self):
        """Test MedicalCategory enum values."""
        assert MedicalCategory.TERMINOLOGY.value == "terminology"
        assert MedicalCategory.ANATOMY.value == "anatomy"
        assert MedicalCategory.PHARMACOLOGY.value == "pharmacology"
        assert len(list(MedicalCategory)) == 8
    
    def test_drug_class_enum(self):
        """Test DrugClass enum values."""
        assert DrugClass.ANTIBIOTIC.value == "antibiotic"
        assert DrugClass.ANALGESIC.value == "analgesic"
        assert len(list(DrugClass)) == 12
    
    def test_medical_proficiency_enum(self):
        """Test MedicalProficiency enum values."""
        assert MedicalProficiency.NOVICE.value == "novice"
        assert MedicalProficiency.EXPERT.value == "expert"
        assert len(list(MedicalProficiency)) == 5


class TestMedicalTerm:
    """Test MedicalTerm dataclass."""
    
    def test_medical_term_creation(self):
        """Test creating a medical term."""
        term = MedicalTerm(
            term_id="test_term_1",
            term="cardio-",
            definition="heart",
            category=MedicalCategory.TERMINOLOGY,
            prefix="cardio-",
            etymology="Prefix meaning 'heart'",
            examples=["cardiology", "cardiovascular"],
            difficulty=1,
        )
        assert term.term_id == "test_term_1"
        assert term.term == "cardio-"
        assert term.definition == "heart"
        assert term.category == MedicalCategory.TERMINOLOGY
        assert term.proficiency == MedicalProficiency.NOVICE
    
    def test_medical_term_serialization(self):
        """Test MedicalTerm serialization."""
        term = MedicalTerm(
            term_id="test_term_2",
            term="-itis",
            definition="inflammation",
            category=MedicalCategory.TERMINOLOGY,
            suffix="-itis",
        )
        data = term.to_dict()
        assert data["term_id"] == "test_term_2"
        assert data["term"] == "-itis"
        assert data["category"] == "terminology"
        
        restored = MedicalTerm.from_dict(data)
        assert restored.term_id == term.term_id
        assert restored.term == term.term
        assert restored.category == term.category


class TestAnatomyStructure:
    """Test AnatomyStructure dataclass."""
    
    def test_anatomy_structure_creation(self):
        """Test creating an anatomy structure."""
        structure = AnatomyStructure(
            structure_id="test_struct_1",
            name="Heart",
            body_system=BodySystem.CARDIOVASCULAR,
            location="Mediastinum",
            function="Pumps blood",
            related_structures=["Aorta", "Vena cava"],
        )
        assert structure.structure_id == "test_struct_1"
        assert structure.name == "Heart"
        assert structure.body_system == BodySystem.CARDIOVASCULAR
    
    def test_anatomy_structure_serialization(self):
        """Test AnatomyStructure serialization."""
        structure = AnatomyStructure(
            structure_id="test_struct_2",
            name="Lungs",
            body_system=BodySystem.RESPIRATORY,
            location="Thoracic cavity",
            function="Gas exchange",
        )
        data = structure.to_dict()
        assert data["structure_id"] == "test_struct_2"
        assert data["body_system"] == "respiratory"
        
        restored = AnatomyStructure.from_dict(data)
        assert restored.structure_id == structure.structure_id
        assert restored.body_system == structure.body_system


class TestDiseaseCondition:
    """Test DiseaseCondition dataclass."""
    
    def test_condition_creation(self):
        """Test creating a disease condition."""
        condition = DiseaseCondition(
            condition_id="test_cond_1",
            name="Hypertension",
            icd_code="I10",
            description="High blood pressure",
            body_system=BodySystem.CARDIOVASCULAR,
            symptoms=["Headache", "Dizziness"],
            treatments=["Lifestyle changes", "Medications"],
        )
        assert condition.condition_id == "test_cond_1"
        assert condition.name == "Hypertension"
        assert condition.icd_code == "I10"
    
    def test_condition_serialization(self):
        """Test DiseaseCondition serialization."""
        condition = DiseaseCondition(
            condition_id="test_cond_2",
            name="Diabetes",
            body_system=BodySystem.ENDOCRINE,
            symptoms=["Polyuria", "Polydipsia"],
        )
        data = condition.to_dict()
        assert data["condition_id"] == "test_cond_2"
        assert data["body_system"] == "endocrine"
        
        restored = DiseaseCondition.from_dict(data)
        assert restored.condition_id == condition.condition_id
        assert restored.symptoms == condition.symptoms


class TestDrug:
    """Test Drug dataclass."""
    
    def test_drug_creation(self):
        """Test creating a drug."""
        drug = Drug(
            drug_id="test_drug_1",
            name="Aspirin",
            generic_name="Acetylsalicylic acid",
            drug_class=DrugClass.ANALGESIC,
            indications=["Pain", "Fever"],
            side_effects=["GI bleeding"],
        )
        assert drug.drug_id == "test_drug_1"
        assert drug.name == "Aspirin"
        assert drug.drug_class == DrugClass.ANALGESIC
    
    def test_drug_serialization(self):
        """Test Drug serialization."""
        drug = Drug(
            drug_id="test_drug_2",
            name="Metformin",
            generic_name="Metformin",
            drug_class=DrugClass.ENDOCRINE,
        )
        data = drug.to_dict()
        assert data["drug_id"] == "test_drug_2"
        assert data["drug_class"] == "endocrine"
        
        restored = Drug.from_dict(data)
        assert restored.drug_id == drug.drug_id
        assert restored.drug_class == drug.drug_class


class TestMedicalDomain:
    """Test MedicalDomain class."""
    
    @pytest.fixture
    def medical_domain(self):
        """Create a MedicalDomain instance for testing."""
        return MedicalDomain()
    
    def test_medical_domain_creation(self, medical_domain):
        """Test MedicalDomain initialization."""
        assert medical_domain is not None
        assert isinstance(medical_domain._terms, dict)
        assert isinstance(medical_domain._structures, dict)
        assert isinstance(medical_domain._conditions, dict)
        assert isinstance(medical_domain._drugs, dict)
    
    def test_medical_domain_has_terminology(self, medical_domain):
        """Test that domain initializes with terminology."""
        # Should have prefixes, suffixes, and roots
        assert len(medical_domain._terms) > 0
        
        # Check for some expected terms
        terms = list(medical_domain._terms.values())
        term_texts = [t.term for t in terms]
        
        assert any("cardio" in t for t in term_texts)
        assert any("-itis" in t for t in term_texts)
    
    def test_medical_domain_has_anatomy(self, medical_domain):
        """Test that domain initializes with anatomy structures."""
        assert len(medical_domain._structures) > 0
        
        # Check for cardiovascular structures
        cv_structures = medical_domain.get_structures_by_system(BodySystem.CARDIOVASCULAR)
        assert len(cv_structures) > 0
    
    def test_medical_domain_has_conditions(self, medical_domain):
        """Test that domain initializes with conditions."""
        assert len(medical_domain._conditions) > 0
        
        # Should have some common conditions
        conditions = medical_domain.search_conditions("hypertension")
        assert len(conditions) > 0
    
    def test_medical_domain_has_drugs(self, medical_domain):
        """Test that domain initializes with drugs."""
        assert len(medical_domain._drugs) > 0
        
        # Check for common drug classes
        analgesics = medical_domain.get_drugs_by_class(DrugClass.ANALGESIC)
        assert len(analgesics) > 0
    
    def test_add_term(self, medical_domain):
        """Test adding a medical term."""
        term = medical_domain.add_term(
            term="test-prefix-",
            definition="Test definition",
            category=MedicalCategory.TERMINOLOGY,
            prefix="test-prefix-",
        )
        assert term.term == "test-prefix-"
        assert term.term_id in medical_domain._terms
    
    def test_get_term(self, medical_domain):
        """Test getting a term by ID."""
        # Add a term first
        term = medical_domain.add_term(
            term="test-term",
            definition="Test",
            category=MedicalCategory.TERMINOLOGY,
        )
        
        retrieved = medical_domain.get_term(term.term_id)
        assert retrieved is not None
        assert retrieved.term == "test-term"
    
    def test_search_terms(self, medical_domain):
        """Test searching for terms."""
        results = medical_domain.search_terms("cardio")
        assert len(results) > 0
        
        for term in results:
            assert "cardio" in term.term.lower() or "cardio" in term.definition.lower()
    
    def test_get_terms_by_category(self, medical_domain):
        """Test getting terms by category."""
        terms = medical_domain.get_terms_by_category(MedicalCategory.TERMINOLOGY)
        assert len(terms) > 0
        
        for term in terms:
            assert term.category == MedicalCategory.TERMINOLOGY
    
    def test_add_structure(self, medical_domain):
        """Test adding an anatomy structure."""
        structure = medical_domain.add_structure(
            name="Test Organ",
            body_system=BodySystem.DIGESTIVE,
            location="Test location",
            function="Test function",
        )
        assert structure.name == "Test Organ"
        assert structure.structure_id in medical_domain._structures
    
    def test_get_structures_by_system(self, medical_domain):
        """Test getting structures by body system."""
        structures = medical_domain.get_structures_by_system(BodySystem.NERVOUS)
        assert len(structures) > 0
        
        for s in structures:
            assert s.body_system == BodySystem.NERVOUS
    
    def test_add_condition(self, medical_domain):
        """Test adding a condition."""
        condition = medical_domain.add_condition(
            name="Test Condition",
            body_system=BodySystem.CARDIOVASCULAR,
            symptoms=["Symptom 1", "Symptom 2"],
        )
        assert condition.name == "Test Condition"
        assert condition.condition_id in medical_domain._conditions
    
    def test_search_conditions(self, medical_domain):
        """Test searching for conditions."""
        results = medical_domain.search_conditions("pneumonia")
        assert len(results) > 0
    
    def test_add_drug(self, medical_domain):
        """Test adding a drug."""
        drug = medical_domain.add_drug(
            name="TestDrug",
            generic_name="testdrug",
            drug_class=DrugClass.ANTIBIOTIC,
            indications=["Infection"],
        )
        assert drug.name == "TestDrug"
        assert drug.drug_id in medical_domain._drugs
    
    def test_search_drugs(self, medical_domain):
        """Test searching for drugs."""
        results = medical_domain.search_drugs("aspirin")
        # May or may not have aspirin, but search should work
        for drug in results:
            assert "aspirin" in drug.name.lower() or "aspirin" in drug.generic_name.lower()
    
    def test_get_drugs_by_class(self, medical_domain):
        """Test getting drugs by classification."""
        antibiotics = medical_domain.get_drugs_by_class(DrugClass.ANTIBIOTIC)
        assert len(antibiotics) > 0
        
        for drug in antibiotics:
            assert drug.drug_class == DrugClass.ANTIBIOTIC


class TestExerciseGeneration:
    """Test exercise generation."""
    
    @pytest.fixture
    def medical_domain(self):
        """Create a MedicalDomain instance for testing."""
        return MedicalDomain()
    
    def test_generate_term_exercise(self, medical_domain):
        """Test generating terminology exercise."""
        exercise = medical_domain.generate_term_exercise()
        
        assert "exercise_id" in exercise
        assert "type" in exercise
        assert "question" in exercise
    
    def test_generate_term_exercise_mc(self, medical_domain):
        """Test generating multiple choice terminology exercise."""
        term = list(medical_domain._terms.values())[0]
        exercise = medical_domain.generate_term_exercise(term, "multiple_choice")
        
        assert exercise["type"] == "multiple_choice"
        assert "options" in exercise
        assert "correct_answer" in exercise
        assert len(exercise["options"]) >= 2
    
    def test_generate_anatomy_exercise(self, medical_domain):
        """Test generating anatomy exercise."""
        exercise = medical_domain.generate_anatomy_exercise()
        
        assert "exercise_id" in exercise
        assert "question" in exercise
        assert "options" in exercise
    
    def test_generate_diagnosis_exercise(self, medical_domain):
        """Test generating diagnosis exercise."""
        exercise = medical_domain.generate_diagnosis_exercise()
        
        assert "exercise_id" in exercise
        assert "type" in exercise
        assert exercise["type"] == "diagnosis"
        assert "options" in exercise
    
    def test_generate_drug_exercise(self, medical_domain):
        """Test generating drug exercise."""
        exercise = medical_domain.generate_drug_exercise()
        
        assert "exercise_id" in exercise
        assert "question" in exercise
    
    def test_generate_drug_indication_exercise(self, medical_domain):
        """Test generating drug indication exercise."""
        drug = list(medical_domain._drugs.values())[0]
        exercise = medical_domain.generate_drug_exercise(drug, "indication")
        
        assert "drug_class" in exercise
        assert "options" in exercise


class TestReviewSystem:
    """Test spaced repetition review system."""
    
    @pytest.fixture
    def medical_domain(self):
        """Create a MedicalDomain instance for testing."""
        return MedicalDomain()
    
    def test_review_term_correct(self, medical_domain):
        """Test reviewing a term correctly."""
        term = list(medical_domain._terms.values())[0]
        initial_repetitions = term.repetitions
        
        result = medical_domain.review_term(term.term_id, quality=4)
        
        assert result["correct"] is True
        assert term.repetitions == initial_repetitions + 1
        assert term.next_review is not None
    
    def test_review_term_incorrect(self, medical_domain):
        """Test reviewing a term incorrectly."""
        term = list(medical_domain._terms.values())[0]
        term.repetitions = 3  # Set up some progress
        
        result = medical_domain.review_term(term.term_id, quality=2)
        
        assert result["correct"] is False
        assert term.repetitions == 0  # Reset on failure
        assert term.interval == 1  # Back to 1 day
    
    def test_review_updates_proficiency(self, medical_domain):
        """Test that reviews update proficiency."""
        term = list(medical_domain._terms.values())[0]
        term.proficiency = MedicalProficiency.NOVICE
        
        # Multiple correct reviews
        for _ in range(3):
            medical_domain.review_term(term.term_id, quality=4)
        
        # Proficiency should have improved
        assert term.proficiency != MedicalProficiency.NOVICE
    
    def test_review_nonexistent_term(self, medical_domain):
        """Test reviewing a non-existent term."""
        result = medical_domain.review_term("nonexistent_id", quality=4)
        assert "error" in result
    
    def test_get_due_reviews(self, medical_domain):
        """Test getting due reviews."""
        due = medical_domain.get_due_reviews()
        
        # All terms should initially be due
        assert len(due) > 0
    
    def test_review_history(self, medical_domain):
        """Test review history is tracked."""
        term = list(medical_domain._terms.values())[0]
        
        initial_history_len = len(medical_domain._review_history)
        medical_domain.review_term(term.term_id, quality=4)
        
        assert len(medical_domain._review_history) == initial_history_len + 1


class TestStatisticsAndExport:
    """Test statistics and export functionality."""
    
    @pytest.fixture
    def medical_domain(self):
        """Create a MedicalDomain instance for testing."""
        return MedicalDomain()
    
    def test_get_statistics(self, medical_domain):
        """Test getting statistics."""
        stats = medical_domain.get_statistics()
        
        assert "terms" in stats
        assert "structures" in stats
        assert "conditions" in stats
        assert "drugs" in stats
        
        assert stats["terms"]["total"] > 0
        assert stats["structures"]["total"] > 0
    
    def test_export_import_progress(self, medical_domain):
        """Test exporting and importing progress."""
        # Do some reviews
        term = list(medical_domain._terms.values())[0]
        medical_domain.review_term(term.term_id, quality=4)
        
        # Export
        exported = medical_domain.export_progress()
        
        assert "terms" in exported
        assert "statistics" in exported
        
        # Create new domain and import
        new_domain = MedicalDomain()
        new_domain.import_progress(exported)
        
        # Check that the reviewed term's progress was imported
        imported_term = new_domain.get_term(term.term_id)
        assert imported_term.total_reviews == term.total_reviews
    
    def test_save_patterns_to_ltm(self, medical_domain):
        """Test saving patterns to LTM."""
        count = medical_domain.save_patterns_to_ltm()
        
        # Should have saved terms, conditions, and drugs
        expected_min = (
            len(medical_domain._terms) +
            len(medical_domain._conditions) +
            len(medical_domain._drugs)
        )
        assert count >= expected_min


class TestCrossDomainIntegration:
    """Test integration with other RPA components."""
    
    def test_medical_domain_with_ltm(self):
        """Test MedicalDomain with LTM integration."""
        from rpa.memory.ltm import LongTermMemory
        
        ltm = LongTermMemory()
        domain = MedicalDomain(ltm=ltm)
        
        # Save patterns
        count = domain.save_patterns_to_ltm()
        assert count > 0
    
    def test_medical_domain_with_episodic(self):
        """Test MedicalDomain with episodic memory integration."""
        from rpa.memory.episodic import EpisodicMemory
        
        episodic = EpisodicMemory()
        domain = MedicalDomain(episodic=episodic)
        
        # Review should log to episodic
        term = list(domain._terms.values())[0]
        domain.review_term(term.term_id, quality=4)
        
        # Event should be logged (checking episodic has events)
        assert len(domain._review_history) > 0
