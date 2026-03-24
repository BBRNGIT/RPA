"""
Tests for RPA Learning module (AnswerIntegrator, CorrectionAnalyzer).
"""

import pytest

from rpa.core.graph import Node, Edge, PatternGraph, NodeType, EdgeType
from rpa.memory.stm import ShortTermMemory
from rpa.memory.ltm import LongTermMemory
from rpa.memory.episodic import EpisodicMemory
from rpa.inquiry.gap_detector import GapType
from rpa.inquiry.question_generator import Inquiry, QuestionType, QuestionPriority
from rpa.learning.answer_integrator import AnswerIntegrator, IntegrationResult
from rpa.learning.correction_analyzer import (
    CorrectionAnalyzer, Correction, IssueType, CorrectionResult
)
from tests.fixtures import word_graph, empty_stm, empty_ltm


class TestAnswerIntegrator:
    """Tests for AnswerIntegrator."""
    
    def test_integrate_composition_answer(
        self,
        empty_stm: ShortTermMemory,
        empty_ltm: LongTermMemory,
    ):
        """Test integrating a composition answer."""
        integrator = AnswerIntegrator()
        
        # Create a pattern in STM
        node = Node.create_pattern("cat", "cat", 1)
        empty_stm.add_pattern(node, "test_session")
        
        # Create inquiry about missing components
        inquiry = Inquiry(
            inquiry_id="inquiry_1",
            question="What are the components of 'cat'?",
            question_type=QuestionType.COMPOSITION,
            gap_type=GapType.INCOMPLETE_COMPOSITION,
            priority=QuestionPriority.HIGH,
            affected_nodes=["pattern:cat"],
            metadata={"missing_children": ["c", "a", "t"]},
        )
        
        # Integrate answer
        result = integrator.integrate_composition_answer(
            inquiry, "The components are c, a, t", empty_stm, empty_ltm
        )
        
        assert result.success is True
        assert len(result.new_nodes) >= 3  # Should create primitives
    
    def test_integrate_usage_answer(
        self,
        empty_stm: ShortTermMemory,
        empty_ltm: LongTermMemory,
    ):
        """Test integrating a usage answer."""
        integrator = AnswerIntegrator()
        
        # Create a pattern
        node = Node.create_pattern("cat", "cat", 1, domain="english")
        empty_stm.add_pattern(node, "test_session")
        
        # Create inquiry about usage
        inquiry = Inquiry(
            inquiry_id="inquiry_2",
            question="How is 'cat' used?",
            question_type=QuestionType.USAGE,
            gap_type=GapType.ORPHANED_PATTERN,
            priority=QuestionPriority.LOW,
            affected_nodes=["pattern:cat"],
            metadata={"domain": "english"},
        )
        
        # Integrate answer with examples
        result = integrator.integrate_usage_answer(
            inquiry, "Examples: 'The cat sat.' 'I love my cat.'", empty_stm, empty_ltm
        )
        
        assert result.success is True
        assert len(result.new_nodes) >= 1  # Should create usage examples
    
    def test_integrate_hierarchy_answer(
        self,
        empty_stm: ShortTermMemory,
        empty_ltm: LongTermMemory,
    ):
        """Test integrating a hierarchy answer."""
        integrator = AnswerIntegrator()
        
        # Create inquiry about missing hierarchy level
        inquiry = Inquiry(
            inquiry_id="inquiry_3",
            question="What patterns fill level 1?",
            question_type=QuestionType.HIERARCHY,
            gap_type=GapType.HIERARCHY_GAP,
            priority=QuestionPriority.MEDIUM,
            affected_nodes=[],
            metadata={
                "domain": "english",
                "missing_levels": [1],
            },
        )
        
        # Integrate answer
        result = integrator.integrate_hierarchy_answer(
            inquiry, "Learn these words: 'cat', 'dog', 'run'", empty_stm, empty_ltm
        )
        
        assert result.success is True
        assert len(result.new_nodes) >= 3
    
    def test_integrate_validation_answer_affirmative(
        self,
        empty_stm: ShortTermMemory,
        empty_ltm: LongTermMemory,
    ):
        """Test integrating an affirmative validation answer."""
        integrator = AnswerIntegrator()
        
        # Create an uncertain pattern
        node = Node.create_pattern("test", "test", 1)
        node.is_uncertain = True
        empty_stm.add_pattern(node, "test_session")
        
        # Create validation inquiry
        inquiry = Inquiry(
            inquiry_id="inquiry_4",
            question="Is 'test' correct?",
            question_type=QuestionType.VALIDATION,
            gap_type=GapType.UNCERTAIN_PATTERN,
            priority=QuestionPriority.MEDIUM,
            affected_nodes=["pattern:test"],
        )
        
        # Integrate affirmative answer
        result = integrator.integrate_validation_answer(
            inquiry, "Yes, that is correct.", empty_stm, empty_ltm
        )
        
        assert result.success is True
        assert "pattern:test" in result.updated_nodes
        
        # Check node was updated
        updated = empty_stm.get_pattern("pattern:test")
        assert updated.is_uncertain is False
    
    def test_integrate_validation_answer_negative(
        self,
        empty_stm: ShortTermMemory,
        empty_ltm: LongTermMemory,
    ):
        """Test integrating a negative validation answer."""
        integrator = AnswerIntegrator()
        
        # Create an uncertain pattern
        node = Node.create_pattern("wrong", "wrong", 1)
        node.is_uncertain = True
        empty_stm.add_pattern(node, "test_session")
        
        # Create validation inquiry
        inquiry = Inquiry(
            inquiry_id="inquiry_5",
            question="Is 'wrong' correct?",
            question_type=QuestionType.VALIDATION,
            gap_type=GapType.UNCERTAIN_PATTERN,
            priority=QuestionPriority.MEDIUM,
            affected_nodes=["pattern:wrong"],
        )
        
        # Integrate negative answer
        result = integrator.integrate_validation_answer(
            inquiry, "No, that pattern is incorrect.", empty_stm, empty_ltm
        )
        
        assert result.success is True
        
        # Check node was marked invalid
        updated = empty_stm.get_pattern("pattern:wrong")
        assert updated.is_valid is False
    
    def test_extract_components(self):
        """Test extracting components from response."""
        integrator = AnswerIntegrator()
        
        components = integrator._extract_components(
            "The components are 'a', 'b', and 'c'",
            ["a", "b", "c"],
        )
        
        assert "a" in components
        assert "b" in components
        assert "c" in components
    
    def test_extract_examples(self):
        """Test extracting examples from response."""
        integrator = AnswerIntegrator()
        
        examples = integrator._extract_examples(
            "Here are some examples. The cat sat. I have a dog. We run fast."
        )
        
        assert len(examples) >= 1
        assert any("cat" in ex.lower() for ex in examples)
    
    def test_is_affirmative(self):
        """Test detecting affirmative responses."""
        integrator = AnswerIntegrator()
        
        assert integrator._is_affirmative("Yes, that's right") is True
        assert integrator._is_affirmative("Correct!") is True
        assert integrator._is_affirmative("No, that's wrong") is False
        assert integrator._is_affirmative("I'm not sure") is False
    
    def test_get_statistics(self):
        """Test getting integration statistics."""
        integrator = AnswerIntegrator()
        
        # Add some results
        integrator._integration_history["1"] = IntegrationResult(
            inquiry_id="1",
            success=True,
            new_nodes=["a", "b"],
            new_edges=["e1"],
        )
        integrator._integration_history["2"] = IntegrationResult(
            inquiry_id="2",
            success=False,
        )
        
        stats = integrator.get_statistics()
        
        assert stats["total_integrations"] == 2
        assert stats["successful"] == 1
        assert stats["nodes_created"] == 2


class TestCorrectionAnalyzer:
    """Tests for CorrectionAnalyzer."""
    
    def test_analyze_correction(self, word_graph: PatternGraph):
        """Test analyzing a correction."""
        analyzer = CorrectionAnalyzer()
        
        # Get two nodes for correction
        wrong_node = word_graph.get_node("pattern:cat")
        correct_node = word_graph.get_node("pattern:dog")
        
        if wrong_node and correct_node:
            correction = analyzer.analyze_correction(
                wrong_node_id="pattern:cat",
                correct_node_id="pattern:dog",
                feedback="The composition was wrong, should use different letters",
                graph=word_graph,
            )
            
            assert correction is not None
            assert correction.issue_type is not None
            assert correction.root_cause != ""
    
    def test_classify_issue(self):
        """Test classifying issue types."""
        analyzer = CorrectionAnalyzer()
        
        # Test structural issue
        issue = analyzer._classify_issue(None, None, "The structure is wrong")
        assert issue == IssueType.STRUCTURAL
        
        # Test compositional issue
        issue = analyzer._classify_issue(None, None, "Missing component")
        assert issue == IssueType.COMPOSITIONAL
        
        # Test usage issue
        issue = analyzer._classify_issue(None, None, "Wrong usage context")
        assert issue == IssueType.USAGE
        
        # Test order issue
        issue = analyzer._classify_issue(None, None, "Wrong order of elements")
        assert issue == IssueType.ORDER
    
    def test_identify_root_cause(self):
        """Test identifying root cause."""
        analyzer = CorrectionAnalyzer()
        
        wrong = Node.create_pattern("wrong", "abc", 1)
        correct = Node.create_pattern("correct", "xyz", 1)
        graph = PatternGraph()
        
        cause = analyzer._identify_root_cause(wrong, correct, "Test feedback", graph)
        
        assert "content mismatch" in cause.lower() or "mismatch" in cause.lower()
    
    def test_apply_correction_insights(
        self,
        empty_ltm: LongTermMemory,
    ):
        """Test applying correction insights."""
        analyzer = CorrectionAnalyzer()
        graph = PatternGraph()
        
        # Create nodes
        wrong = Node.create_pattern("wrong", "wrong", 1)
        correct = Node.create_pattern("correct", "correct", 1)
        graph.add_node(wrong)
        graph.add_node(correct)
        
        # Consolidate to LTM
        empty_ltm.consolidate(wrong)
        empty_ltm.consolidate(correct)
        
        # Create correction
        correction = Correction(
            correction_id="corr_1",
            wrong_node_id="pattern:wrong",
            correct_node_id="pattern:correct",
            feedback="Test correction",
            issue_type=IssueType.COMPOSITIONAL,
            root_cause="Wrong composition",
        )
        
        result = analyzer.apply_correction_insights(correction, graph, empty_ltm)
        
        assert result.success is True
        assert "pattern:wrong" in result.patterns_updated
    
    def test_find_similar_patterns(self, word_graph: PatternGraph):
        """Test finding similar patterns."""
        analyzer = CorrectionAnalyzer()
        
        # Add a pattern similar to existing one
        similar = Node.create_pattern("bat", "bat", 1, domain="english")
        word_graph.add_node(similar)
        
        similar_ids = analyzer._find_similar_patterns(
            "pattern:cat",
            IssueType.COMPOSITIONAL,
            word_graph,
        )
        
        # Should find some similar patterns
        assert isinstance(similar_ids, list)
    
    def test_get_corrections_by_pattern(self):
        """Test getting corrections for a pattern."""
        analyzer = CorrectionAnalyzer()
        
        # Add a correction
        correction = Correction(
            correction_id="corr_1",
            wrong_node_id="pattern:test",
            correct_node_id="pattern:correct",
            feedback="Test",
            issue_type=IssueType.COMPOSITIONAL,
        )
        analyzer._corrections["corr_1"] = correction
        
        corrections = analyzer.get_corrections_by_pattern("pattern:test")
        
        assert len(corrections) == 1
    
    def test_get_common_issues(self):
        """Test getting common issue types."""
        analyzer = CorrectionAnalyzer()
        
        # Add corrections with different issue types
        for i, issue_type in enumerate([IssueType.COMPOSITIONAL, IssueType.COMPOSITIONAL, IssueType.ORDER]):
            correction = Correction(
                correction_id=f"corr_{i}",
                wrong_node_id=f"wrong_{i}",
                correct_node_id=f"correct_{i}",
                feedback="Test",
                issue_type=issue_type,
            )
            analyzer._corrections[correction.correction_id] = correction
        
        common = analyzer.get_common_issues()
        
        assert common.get("compositional", 0) == 2
        assert common.get("order", 0) == 1
    
    def test_correction_serialization(self):
        """Test correction serialization."""
        correction = Correction(
            correction_id="test_corr",
            wrong_node_id="wrong",
            correct_node_id="correct",
            feedback="Test feedback",
            issue_type=IssueType.STRUCTURAL,
            root_cause="Test cause",
        )
        
        data = correction.to_dict()
        
        assert data["correction_id"] == "test_corr"
        assert data["issue_type"] == "structural"
    
    def test_get_statistics(self):
        """Test getting correction statistics."""
        analyzer = CorrectionAnalyzer()
        
        # Add some corrections
        for i in range(3):
            correction = Correction(
                correction_id=f"corr_{i}",
                wrong_node_id=f"wrong_{i}",
                correct_node_id=f"correct_{i}",
                feedback="Test",
                issue_type=IssueType.COMPOSITIONAL,
                applied=(i < 2),
            )
            analyzer._corrections[correction.correction_id] = correction
        
        stats = analyzer.get_statistics()
        
        assert stats["total_corrections"] == 3
        assert stats["applied"] == 2
        assert stats["pending"] == 1
