"""
Tests for Phase 4: Production Hardening Components.

Tests for:
- CodeSandbox: Safe code execution
- ErrorClassifier: Error categorization
- ErrorCorrector: Error correction
- AbstractionEngine: Concept formation
- KnowledgeIntegrity: Truth management
"""

import pytest
from datetime import datetime


# =============================================================================
# CodeSandbox Tests
# =============================================================================

class TestCodeSandbox:
    """Tests for CodeSandbox."""

    def test_imports(self):
        """Test that CodeSandbox components can be imported."""
        from rpa.execution.code_sandbox import (
            CodeSandbox,
            CodeAnalyzer,
            ExecutionResult,
            SafetyViolation,
            ExecutionLogger,
            RestrictedGlobals,
        )
        assert CodeSandbox is not None
        assert CodeAnalyzer is not None
        assert ExecutionResult is not None
        assert SafetyViolation is not None

    def test_create_sandbox(self):
        """Test creating a CodeSandbox instance."""
        from rpa.execution.code_sandbox import CodeSandbox
        sandbox = CodeSandbox(timeout_seconds=5.0)
        assert sandbox.timeout == 5.0
        assert sandbox.max_output_size == 10000

    def test_execute_simple_code(self):
        """Test executing simple code."""
        from rpa.execution.code_sandbox import CodeSandbox
        sandbox = CodeSandbox()
        result = sandbox.execute("x = 1 + 1")
        assert result.success is True

    def test_execute_with_output(self):
        """Test code with output."""
        from rpa.execution.code_sandbox import CodeSandbox
        sandbox = CodeSandbox()
        result = sandbox.execute("print('Hello, World!')")
        assert result.success is True
        assert "Hello, World!" in result.output

    def test_execute_with_error(self):
        """Test code with runtime error."""
        from rpa.execution.code_sandbox import CodeSandbox
        sandbox = CodeSandbox()
        result = sandbox.execute("1 / 0")
        assert result.success is False
        assert result.error is not None
        assert "ZeroDivisionError" in result.error_type

    def test_safety_check_blocks_dangerous_import(self):
        """Test that dangerous imports are blocked."""
        from rpa.execution.code_sandbox import CodeSandbox
        sandbox = CodeSandbox(enable_safety_check=True)
        result = sandbox.execute("import os")
        assert result.success is False
        assert "Safety" in result.error or "blocked" in result.error.lower()

    def test_safety_check_blocks_eval(self):
        """Test that eval is blocked."""
        from rpa.execution.code_sandbox import CodeSandbox
        sandbox = CodeSandbox(enable_safety_check=True)
        result = sandbox.execute("eval('1+1')")
        assert result.success is False

    def test_execution_result_to_dict(self):
        """Test ExecutionResult serialization."""
        from rpa.execution.code_sandbox import ExecutionResult
        result = ExecutionResult(
            success=True,
            output="test output",
            execution_time_ms=10.5
        )
        d = result.to_dict()
        assert d["success"] is True
        assert d["output"] == "test output"
        assert d["execution_time_ms"] == 10.5

    def test_sandbox_stats(self):
        """Test sandbox statistics."""
        from rpa.execution.code_sandbox import CodeSandbox
        sandbox = CodeSandbox()
        sandbox.execute("x = 1")
        sandbox.execute("y = 2")
        stats = sandbox.get_stats()
        assert stats["total_executions"] == 2
        assert stats["successful"] == 2


class TestCodeAnalyzer:
    """Tests for CodeAnalyzer."""

    def test_create_analyzer(self):
        """Test creating a CodeAnalyzer."""
        from rpa.execution.code_sandbox import CodeAnalyzer
        analyzer = CodeAnalyzer()
        assert analyzer is not None

    def test_analyze_safe_code(self):
        """Test analyzing safe code."""
        from rpa.execution.code_sandbox import CodeAnalyzer
        analyzer = CodeAnalyzer()
        is_safe, violations = analyzer.is_safe("x = 1 + 1")
        assert is_safe is True
        assert len(violations) == 0

    def test_analyze_dangerous_import(self):
        """Test detecting dangerous import."""
        from rpa.execution.code_sandbox import CodeAnalyzer
        analyzer = CodeAnalyzer()
        is_safe, violations = analyzer.is_safe("import os")
        assert is_safe is False
        assert len(violations) > 0

    def test_analyze_blocked_call(self):
        """Test detecting blocked function call."""
        from rpa.execution.code_sandbox import CodeAnalyzer
        analyzer = CodeAnalyzer()
        is_safe, violations = analyzer.is_safe("eval('test')")
        assert is_safe is False

    def test_syntax_error_detection(self):
        """Test detecting syntax errors."""
        from rpa.execution.code_sandbox import CodeAnalyzer
        analyzer = CodeAnalyzer()
        violations = analyzer.analyze("x = ")
        assert len(violations) > 0
        assert violations[0].violation_type == "syntax_error"


class TestExecutionLogger:
    """Tests for ExecutionLogger."""

    def test_create_logger(self):
        """Test creating an ExecutionLogger."""
        from rpa.execution.code_sandbox import ExecutionLogger
        logger = ExecutionLogger()
        assert logger is not None

    def test_log_execution(self):
        """Test logging an execution."""
        from rpa.execution.code_sandbox import ExecutionLogger, ExecutionResult
        logger = ExecutionLogger()
        result = ExecutionResult(success=True, output="test")
        entry_id = logger.log_execution("x = 1", result)
        assert entry_id is not None

    def test_get_entries(self):
        """Test getting log entries."""
        from rpa.execution.code_sandbox import ExecutionLogger, ExecutionResult
        logger = ExecutionLogger()
        result = ExecutionResult(success=True, output="test")
        logger.log_execution("x = 1", result)
        entries = logger.get_entries()
        assert len(entries) == 1

    def test_error_patterns(self):
        """Test getting error patterns."""
        from rpa.execution.code_sandbox import ExecutionLogger, ExecutionResult
        logger = ExecutionLogger()
        # Log some errors
        for _ in range(3):
            result = ExecutionResult(
                success=False,
                output="",
                error="ZeroDivisionError",
                error_type="ZeroDivisionError"
            )
            logger.log_execution("1/0", result)
        patterns = logger.get_error_patterns()
        assert len(patterns) > 0


# =============================================================================
# ErrorClassifier Tests
# =============================================================================

class TestErrorClassifier:
    """Tests for ErrorClassifier."""

    def test_imports(self):
        """Test that ErrorClassifier components can be imported."""
        from rpa.learning.error_classifier import (
            ErrorClassifier,
            ClassifiedError,
            ErrorPattern,
        )
        assert ErrorClassifier is not None
        assert ClassifiedError is not None

    def test_create_classifier(self):
        """Test creating an ErrorClassifier."""
        from rpa.learning.error_classifier import ErrorClassifier
        classifier = ErrorClassifier()
        assert classifier is not None

    def test_classify_syntax_error(self):
        """Test classifying a syntax error."""
        from rpa.learning.error_classifier import ErrorClassifier
        classifier = ErrorClassifier()
        error = classifier.classify(
            "SyntaxError: invalid syntax",
            line_number=10
        )
        assert error.error_type == "syntax"
        assert error.line_number == 10

    def test_classify_name_error(self):
        """Test classifying a NameError."""
        from rpa.learning.error_classifier import ErrorClassifier
        classifier = ErrorClassifier()
        error = classifier.classify(
            "NameError: name 'undefined_var' is not defined"
        )
        assert error.category == "name_error"
        assert len(error.suggestions) > 0

    def test_classify_index_error(self):
        """Test classifying an IndexError."""
        from rpa.learning.error_classifier import ErrorClassifier
        classifier = ErrorClassifier()
        error = classifier.classify(
            "IndexError: list index out of range"
        )
        assert error.category == "index_error"

    def test_classify_key_error(self):
        """Test classifying a KeyError."""
        from rpa.learning.error_classifier import ErrorClassifier
        classifier = ErrorClassifier()
        error = classifier.classify(
            "KeyError: 'missing_key'"
        )
        assert error.category == "key_error"

    def test_classify_zero_division(self):
        """Test classifying ZeroDivisionError."""
        from rpa.learning.error_classifier import ErrorClassifier
        classifier = ErrorClassifier()
        error = classifier.classify(
            "ZeroDivisionError: division by zero"
        )
        assert error.category == "zero_division_error"
        assert error.learning_value >= 0.8

    def test_get_common_errors(self):
        """Test getting common errors."""
        from rpa.learning.error_classifier import ErrorClassifier
        classifier = ErrorClassifier()
        classifier.classify("NameError: name 'x' is not defined")
        classifier.classify("NameError: name 'y' is not defined")
        common = classifier.get_common_errors()
        assert len(common) > 0

    def test_get_learning_insights(self):
        """Test getting learning insights."""
        from rpa.learning.error_classifier import ErrorClassifier
        classifier = ErrorClassifier()
        classifier.classify("NameError: name 'x' is not defined")
        classifier.classify("IndexError: list index out of range")
        insights = classifier.get_learning_insights()
        assert insights["total_errors"] == 2
        assert len(insights["insights"]) > 0

    def test_classified_error_to_dict(self):
        """Test ClassifiedError serialization."""
        from rpa.learning.error_classifier import ClassifiedError
        error = ClassifiedError(
            error_id="test123",
            error_type="runtime",
            category="index_error",
            message="Test error",
            severity="high"
        )
        d = error.to_dict()
        assert d["error_id"] == "test123"
        assert d["error_type"] == "runtime"
        assert d["severity"] == "high"


# =============================================================================
# ErrorCorrector Tests
# =============================================================================

class TestErrorCorrector:
    """Tests for ErrorCorrector."""

    def test_imports(self):
        """Test that ErrorCorrector components can be imported."""
        from rpa.learning.error_corrector import (
            ErrorCorrector,
            Correction,
            CorrectionPattern,
            AutomatedFixer,
        )
        assert ErrorCorrector is not None
        assert Correction is not None

    def test_create_corrector(self):
        """Test creating an ErrorCorrector."""
        from rpa.learning.error_corrector import ErrorCorrector
        corrector = ErrorCorrector()
        assert corrector is not None

    def test_suggest_correction(self):
        """Test suggesting a correction."""
        from rpa.learning.error_corrector import ErrorCorrector
        from rpa.learning.error_classifier import ClassifiedError
        corrector = ErrorCorrector()

        error = ClassifiedError(
            error_id="test",
            error_type="runtime",
            category="name_error",
            message="NameError: name 'x' is not defined",
            severity="high"
        )

        correction = corrector.suggest_correction(error)
        assert correction.error_id == "test"
        assert len(correction.description) > 0

    def test_get_correction_patterns(self):
        """Test getting correction patterns."""
        from rpa.learning.error_corrector import ErrorCorrector
        corrector = ErrorCorrector()
        patterns = corrector.get_correction_patterns()
        assert len(patterns) > 0

    def test_correction_to_dict(self):
        """Test Correction serialization."""
        from rpa.learning.error_corrector import Correction
        correction = Correction(
            correction_id="corr123",
            error_id="err123",
            fix_type="code_change",
            description="Fix description"
        )
        d = correction.to_dict()
        assert d["correction_id"] == "corr123"
        assert d["fix_type"] == "code_change"

    def test_get_stats(self):
        """Test corrector statistics."""
        from rpa.learning.error_corrector import ErrorCorrector
        corrector = ErrorCorrector()
        stats = corrector.get_stats()
        assert "total_corrections" in stats
        assert "patterns_count" in stats

    def test_add_custom_pattern(self):
        """Test adding a custom correction pattern."""
        from rpa.learning.error_corrector import ErrorCorrector
        corrector = ErrorCorrector()
        pattern_id = corrector.add_custom_pattern(
            error_category="custom_error",
            detection_pattern=r"CustomError: (.+)",
            fix_template="Apply custom fix"
        )
        assert pattern_id is not None
        assert pattern_id.startswith("custom_")


class TestAutomatedFixer:
    """Tests for AutomatedFixer."""

    def test_create_fixer(self):
        """Test creating an AutomatedFixer."""
        from rpa.learning.error_corrector import ErrorCorrector, AutomatedFixer
        corrector = ErrorCorrector()
        fixer = AutomatedFixer(corrector)
        assert fixer is not None

    def test_attempt_fix_indentation(self):
        """Test attempting to fix indentation."""
        from rpa.learning.error_corrector import ErrorCorrector, AutomatedFixer
        from rpa.learning.error_classifier import ClassifiedError
        corrector = ErrorCorrector()
        fixer = AutomatedFixer(corrector)

        error = ClassifiedError(
            error_id="test",
            error_type="syntax",
            category="indentation_error",
            message="IndentationError",
            severity="medium"
        )

        code = "def foo():\n\tprint('hi')"
        fixed_code, success, msg = fixer.attempt_fix(code, error)
        # Should replace tabs with spaces
        assert "\t" not in fixed_code or success is True


# =============================================================================
# AbstractionEngine Tests
# =============================================================================

class TestAbstractionEngine:
    """Tests for AbstractionEngine."""

    def test_imports(self):
        """Test that AbstractionEngine components can be imported."""
        from rpa.learning.abstraction_engine import (
            AbstractionEngine,
            AbstractConcept,
            AbstractionRule,
            ConceptHierarchy,
        )
        assert AbstractionEngine is not None
        assert AbstractConcept is not None

    def test_create_engine(self):
        """Test creating an AbstractionEngine."""
        from rpa.learning.abstraction_engine import AbstractionEngine
        engine = AbstractionEngine()
        assert engine is not None

    def test_form_concept(self):
        """Test forming an abstract concept."""
        from rpa.learning.abstraction_engine import AbstractionEngine
        engine = AbstractionEngine()

        patterns = [
            {"id": "p1", "content": "apple", "domain": "english", "hierarchy_level": 1},
            {"id": "p2", "content": "banana", "domain": "english", "hierarchy_level": 1},
            {"id": "p3", "content": "cherry", "domain": "english", "hierarchy_level": 1},
        ]

        concept = engine.form_concept(patterns)
        assert concept.concept_id is not None
        assert len(concept.source_patterns) == 3

    def test_get_concept(self):
        """Test getting a concept by ID."""
        from rpa.learning.abstraction_engine import AbstractionEngine
        engine = AbstractionEngine()

        patterns = [
            {"id": "p1", "content": "test", "domain": "test"},
        ]
        concept = engine.form_concept(patterns)

        retrieved = engine.get_concept(concept.concept_id)
        assert retrieved is not None
        assert retrieved.concept_id == concept.concept_id

    def test_find_abstractions(self):
        """Test finding abstractions in patterns."""
        from rpa.learning.abstraction_engine import AbstractionEngine
        engine = AbstractionEngine()

        patterns = [
            {"content": "cat", "domain": "english", "hierarchy_level": 1, "type": "noun"},
            {"content": "dog", "domain": "english", "hierarchy_level": 1, "type": "noun"},
            {"content": "bird", "domain": "english", "hierarchy_level": 1, "type": "noun"},
        ]

        abstractions = engine.find_abstractions(patterns, min_similarity=0.3)
        assert len(abstractions) >= 1

    def test_refine_concept(self):
        """Test refining a concept."""
        from rpa.learning.abstraction_engine import AbstractionEngine
        engine = AbstractionEngine()

        patterns = [{"id": "p1", "content": "test", "domain": "test"}]
        concept = engine.form_concept(patterns)

        new_patterns = [{"id": "p2", "content": "test2", "domain": "test"}]
        refined = engine.refine_concept(concept.concept_id, new_patterns)

        assert refined is not None
        assert len(refined.source_patterns) == 2

    def test_abstract_concept_to_dict(self):
        """Test AbstractConcept serialization."""
        from rpa.learning.abstraction_engine import AbstractConcept
        concept = AbstractConcept(
            concept_id="c1",
            name="TestConcept",
            description="A test concept",
            abstraction_level=2
        )
        d = concept.to_dict()
        assert d["concept_id"] == "c1"
        assert d["abstraction_level"] == 2

    def test_get_stats(self):
        """Test engine statistics."""
        from rpa.learning.abstraction_engine import AbstractionEngine
        engine = AbstractionEngine()
        stats = engine.get_stats()
        assert "total_concepts" in stats
        assert "by_level" in stats

    def test_get_concepts_by_level(self):
        """Test getting concepts by abstraction level."""
        from rpa.learning.abstraction_engine import AbstractionEngine
        engine = AbstractionEngine()

        patterns = [{"id": "p1", "content": "test", "domain": "test"}]
        engine.form_concept(patterns, abstraction_level=2)

        level_2 = engine.get_concepts_by_level(2)
        assert len(level_2) >= 1


class TestConceptHierarchy:
    """Tests for ConceptHierarchy."""

    def test_create_hierarchy(self):
        """Test creating a ConceptHierarchy."""
        from rpa.learning.abstraction_engine import ConceptHierarchy
        hierarchy = ConceptHierarchy()
        assert hierarchy is not None

    def test_add_relationship(self):
        """Test adding a parent-child relationship."""
        from rpa.learning.abstraction_engine import ConceptHierarchy
        hierarchy = ConceptHierarchy()
        hierarchy.add_relationship("parent1", "child1")

        parent = hierarchy.get_parent("child1")
        assert parent == "parent1"

    def test_get_children(self):
        """Test getting children."""
        from rpa.learning.abstraction_engine import ConceptHierarchy
        hierarchy = ConceptHierarchy()
        hierarchy.add_relationship("parent1", "child1")
        hierarchy.add_relationship("parent1", "child2")

        children = hierarchy.get_children("parent1")
        assert len(children) == 2

    def test_get_ancestors(self):
        """Test getting ancestors."""
        from rpa.learning.abstraction_engine import ConceptHierarchy
        hierarchy = ConceptHierarchy()
        hierarchy.add_relationship("grandparent", "parent")
        hierarchy.add_relationship("parent", "child")

        ancestors = hierarchy.get_ancestors("child")
        assert "parent" in ancestors
        assert "grandparent" in ancestors

    def test_find_common_ancestor(self):
        """Test finding common ancestor."""
        from rpa.learning.abstraction_engine import ConceptHierarchy
        hierarchy = ConceptHierarchy()
        hierarchy.add_relationship("root", "branch1")
        hierarchy.add_relationship("root", "branch2")
        hierarchy.add_relationship("branch1", "leaf1")
        hierarchy.add_relationship("branch2", "leaf2")

        common = hierarchy.find_common_ancestor("leaf1", "leaf2")
        assert common == "root"


# =============================================================================
# KnowledgeIntegrity Tests
# =============================================================================

class TestKnowledgeIntegrity:
    """Tests for KnowledgeIntegrity."""

    def test_imports(self):
        """Test that KnowledgeIntegrity components can be imported."""
        from rpa.validation.knowledge_integrity import (
            KnowledgeIntegrity,
            Fact,
            Contradiction,
            TruthTracker,
        )
        assert KnowledgeIntegrity is not None
        assert Fact is not None
        assert Contradiction is not None

    def test_create_integrity(self):
        """Test creating a KnowledgeIntegrity instance."""
        from rpa.validation.knowledge_integrity import KnowledgeIntegrity
        integrity = KnowledgeIntegrity()
        assert integrity is not None

    def test_add_fact(self):
        """Test adding a fact."""
        from rpa.validation.knowledge_integrity import KnowledgeIntegrity
        integrity = KnowledgeIntegrity()
        fact = integrity.add_fact(
            content="The sky is blue",
            domain="general",
            truth_value=0.9
        )
        assert fact.fact_id is not None
        assert fact.truth_value == 0.9

    def test_get_fact(self):
        """Test getting a fact."""
        from rpa.validation.knowledge_integrity import KnowledgeIntegrity
        integrity = KnowledgeIntegrity()
        fact = integrity.add_fact("Test fact", "test")
        retrieved = integrity.get_fact(fact.fact_id)
        assert retrieved is not None
        assert retrieved.content == "Test fact"

    def test_query_truth(self):
        """Test querying truth value."""
        from rpa.validation.knowledge_integrity import KnowledgeIntegrity
        integrity = KnowledgeIntegrity()
        integrity.add_fact("Water boils at 100C", "science", truth_value=1.0)

        result = integrity.query_truth("water boils at 100c")
        assert result is not None
        assert result["truth_value"] >= 0.5

    def test_is_true(self):
        """Test is_true check."""
        from rpa.validation.knowledge_integrity import KnowledgeIntegrity
        integrity = KnowledgeIntegrity()
        integrity.add_fact("True fact", "test", truth_value=0.9)

        assert integrity.is_true("true fact") is True

    def test_is_false(self):
        """Test is_false check."""
        from rpa.validation.knowledge_integrity import KnowledgeIntegrity
        integrity = KnowledgeIntegrity()
        integrity.add_fact("False fact", "test", truth_value=0.1)

        assert integrity.is_false("false fact") is True

    def test_add_evidence(self):
        """Test adding evidence."""
        from rpa.validation.knowledge_integrity import KnowledgeIntegrity
        integrity = KnowledgeIntegrity()
        fact = integrity.add_fact("Test", "test", truth_value=0.5)

        integrity.add_evidence(fact.fact_id, supports=True)
        updated = integrity.get_fact(fact.fact_id)
        assert updated.evidence_for == 1

    def test_get_contradictions(self):
        """Test getting contradictions."""
        from rpa.validation.knowledge_integrity import KnowledgeIntegrity
        integrity = KnowledgeIntegrity()
        contradictions = integrity.get_contradictions()
        assert isinstance(contradictions, list)

    def test_validate_consistency(self):
        """Test validating consistency."""
        from rpa.validation.knowledge_integrity import KnowledgeIntegrity
        integrity = KnowledgeIntegrity()
        integrity.add_fact("Fact 1", "test")
        integrity.add_fact("Fact 2", "test")

        result = integrity.validate_consistency()
        assert "is_consistent" in result
        assert "consistency_score" in result

    def test_fact_to_dict(self):
        """Test Fact serialization."""
        from rpa.validation.knowledge_integrity import Fact
        fact = Fact(
            fact_id="f1",
            content="Test fact",
            domain="test",
            truth_value=0.8,
            confidence=0.9,
            source="test_source"
        )
        d = fact.to_dict()
        assert d["fact_id"] == "f1"
        assert d["truth_value"] == 0.8

    def test_get_stats(self):
        """Test integrity statistics."""
        from rpa.validation.knowledge_integrity import KnowledgeIntegrity
        integrity = KnowledgeIntegrity()
        integrity.add_fact("Fact 1", "domain1")
        integrity.add_fact("Fact 2", "domain2")

        stats = integrity.get_stats()
        assert stats["total_facts"] == 2
        assert len(stats["by_domain"]) == 2


class TestTruthTracker:
    """Tests for TruthTracker."""

    def test_create_tracker(self):
        """Test creating a TruthTracker."""
        from rpa.validation.knowledge_integrity import TruthTracker
        tracker = TruthTracker()
        assert tracker is not None

    def test_record_and_get_history(self):
        """Test recording and getting history."""
        from rpa.validation.knowledge_integrity import TruthTracker, Fact
        tracker = TruthTracker()

        fact = Fact(
            fact_id="f1",
            content="Test",
            domain="test",
            truth_value=0.5,
            confidence=0.5,
            source="test"
        )

        tracker.record(fact)
        history = tracker.get_history("f1")
        assert len(history) == 1

    def test_stability_score(self):
        """Test calculating stability score."""
        from rpa.validation.knowledge_integrity import TruthTracker, Fact
        tracker = TruthTracker()

        fact = Fact(
            fact_id="f1",
            content="Test",
            domain="test",
            truth_value=0.5,
            confidence=0.5,
            source="test"
        )

        # Record multiple times with same value
        for _ in range(3):
            tracker.record(fact)

        stability = tracker.get_stability_score("f1")
        assert stability >= 0.8  # Should be high for stable values
