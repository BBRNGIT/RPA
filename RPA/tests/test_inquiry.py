"""
Tests for RPA Inquiry module (GapDetector, QuestionGenerator).
"""

import pytest

from rpa.core.graph import Node, Edge, PatternGraph, NodeType, EdgeType
from rpa.inquiry.gap_detector import GapDetector, Gap, GapType
from rpa.inquiry.question_generator import (
    QuestionGenerator, Inquiry, QuestionType, QuestionPriority
)
from tests.fixtures import word_graph, full_english_graph


class TestGapDetector:
    """Tests for GapDetector."""
    
    def test_detect_uncertain_patterns(self, word_graph: PatternGraph):
        """Test detecting uncertain patterns."""
        detector = GapDetector()
        
        # Mark a pattern as uncertain
        node = word_graph.get_node("pattern:cat")
        if node:
            node.mark_uncertain("testing")
        
        gaps = detector.detect_flagged_uncertain_patterns(word_graph)
        
        assert len(gaps) >= 1
        assert gaps[0].gap_type == GapType.UNCERTAIN_PATTERN
    
    def test_detect_incomplete_composition(self):
        """Test detecting patterns with missing children."""
        detector = GapDetector()
        graph = PatternGraph()
        
        # Create a pattern without its children
        node = Node.create_pattern("test", "test", 1)
        graph.add_node(node)
        
        # Manually add an edge to non-existent child
        edge = Edge(
            edge_id="test_edge",
            source_id="pattern:test",
            target_id="primitive:x",
            edge_type=EdgeType.COMPOSED_OF,
        )
        graph.edges[edge.edge_id] = edge
        graph.outgoing_edges["pattern:test"].append(edge.edge_id)
        
        gaps = detector.detect_incomplete_composition(graph)
        
        assert len(gaps) >= 1
        assert gaps[0].gap_type == GapType.INCOMPLETE_COMPOSITION
        assert "primitive:x" in gaps[0].metadata.get("missing_children", [])
    
    def test_detect_orphaned_patterns(self, word_graph: PatternGraph):
        """Test detecting orphaned patterns."""
        detector = GapDetector()
        
        # Create an orphaned pattern (no parents)
        orphan = Node.create_pattern("orphan", "orphan", 1)
        word_graph.add_node(orphan)
        
        gaps = detector.detect_orphaned_patterns(word_graph)
        
        # Should find at least the orphan
        orphan_gaps = [g for g in gaps if "orphan" in g.description]
        assert len(orphan_gaps) >= 1
    
    def test_detect_unresolved_references(self):
        """Test detecting unresolved references."""
        detector = GapDetector()
        graph = PatternGraph()
        
        # Create nodes
        a = Node.create_primitive("a")
        b = Node.create_primitive("b")
        graph.add_node(a)
        graph.add_node(b)
        
        # Add edge to non-existent node
        edge = Edge(
            edge_id="bad_edge",
            source_id="primitive:a",
            target_id="primitive:z",  # doesn't exist
            edge_type=EdgeType.RELATES_TO,
        )
        graph.edges[edge.edge_id] = edge
        graph.outgoing_edges["primitive:a"].append(edge.edge_id)
        
        gaps = detector.detect_unresolved_references(graph)
        
        assert len(gaps) >= 1
        assert gaps[0].gap_type == GapType.UNRESOLVED_REFERENCE
    
    def test_detect_hierarchy_gaps(self):
        """Test detecting hierarchy gaps."""
        detector = GapDetector()
        graph = PatternGraph()
        
        # Add primitives (level 0)
        for c in "abc":
            graph.add_node(Node.create_primitive(c))
        
        # Add sentences (level 2) but no words (level 1)
        sent = Node.create_sequence("test_sent", "A test.", 2)
        graph.add_node(sent)
        
        gaps = detector.detect_hierarchy_gaps(graph)
        
        # Should detect missing level 1
        hierarchy_gaps = [g for g in gaps if g.gap_type == GapType.HIERARCHY_GAP]
        assert len(hierarchy_gaps) >= 1
    
    def test_detect_all_gaps(self, word_graph: PatternGraph):
        """Test running all detection strategies."""
        detector = GapDetector()
        
        gaps = detector.detect_all_gaps(word_graph)
        
        assert isinstance(gaps, list)
        # All gaps should have proper structure
        for gap in gaps:
            assert gap.gap_id is not None
            assert gap.gap_type is not None
            assert gap.severity in ["low", "medium", "high"]
    
    def test_prioritize_gaps(self):
        """Test gap prioritization."""
        detector = GapDetector()
        
        # Create gaps with different severities
        gap_high = Gap(
            gap_id="gap_1",
            gap_type=GapType.UNRESOLVED_REFERENCE,
            severity="high",
            description="High priority",
        )
        gap_low = Gap(
            gap_id="gap_2",
            gap_type=GapType.CROSS_DOMAIN,
            severity="low",
            description="Low priority",
        )
        gap_medium = Gap(
            gap_id="gap_3",
            gap_type=GapType.UNCERTAIN_PATTERN,
            severity="medium",
            description="Medium priority",
        )
        
        prioritized = detector.prioritize_gaps([gap_low, gap_medium, gap_high])
        
        # High severity unresolved reference should be first
        assert prioritized[0].gap_id == "gap_1"
    
    def test_get_summary(self, word_graph: PatternGraph):
        """Test getting gap summary."""
        detector = GapDetector()
        detector.detect_all_gaps(word_graph)
        
        summary = detector.get_summary()
        
        assert "total_gaps" in summary
        assert "by_type" in summary
        assert "by_severity" in summary


class TestQuestionGenerator:
    """Tests for QuestionGenerator."""
    
    def test_generate_questions_from_gaps(self, word_graph: PatternGraph):
        """Test generating questions from gaps."""
        generator = QuestionGenerator()
        detector = GapDetector()
        
        gaps = detector.detect_all_gaps(word_graph)
        inquiries = generator.generate_questions(gaps, word_graph, limit=5)
        
        assert len(inquiries) <= 5
        for inquiry in inquiries:
            assert inquiry.question is not None
            assert inquiry.question_type is not None
    
    def test_generate_composition_question(self):
        """Test generating composition question."""
        generator = QuestionGenerator()
        
        gap = Gap(
            gap_id="gap_1",
            gap_type=GapType.INCOMPLETE_COMPOSITION,
            severity="high",
            description="Missing components",
            affected_nodes=["pattern:test"],
            metadata={"missing_children": ["x", "y"]},
        )
        
        graph = PatternGraph()
        node = Node.create_pattern("test", "test", 1)
        graph.add_node(node)
        
        inquiry = generator._generate_composition_question(gap, graph)
        
        assert inquiry is not None
        assert inquiry.question_type == QuestionType.COMPOSITION
        assert "test" in inquiry.question.lower()
    
    def test_generate_usage_question(self):
        """Test generating usage question."""
        generator = QuestionGenerator()
        
        gap = Gap(
            gap_id="gap_1",
            gap_type=GapType.ORPHANED_PATTERN,
            severity="low",
            description="Orphaned pattern",
            affected_nodes=["pattern:apple"],
            metadata={},
        )
        
        graph = PatternGraph()
        node = Node.create_pattern("apple", "apple", 1)
        graph.add_node(node)
        
        inquiry = generator._generate_usage_question(gap, graph)
        
        assert inquiry is not None
        assert inquiry.question_type == QuestionType.USAGE
        assert "apple" in inquiry.question.lower()
    
    def test_generate_hierarchy_question(self):
        """Test generating hierarchy question."""
        generator = QuestionGenerator()
        
        gap = Gap(
            gap_id="gap_1",
            gap_type=GapType.HIERARCHY_GAP,
            severity="medium",
            description="Missing level",
            metadata={
                "domain": "english",
                "missing_levels": [1],
                "existing_levels": [0, 2],
            },
        )
        
        graph = PatternGraph()
        
        inquiry = generator._generate_hierarchy_question(gap, graph)
        
        assert inquiry is not None
        assert inquiry.question_type == QuestionType.HIERARCHY
    
    def test_generate_cross_domain_question(self):
        """Test generating cross-domain question."""
        generator = QuestionGenerator()
        
        gap = Gap(
            gap_id="gap_1",
            gap_type=GapType.CROSS_DOMAIN,
            severity="low",
            description="Cross-domain opportunity",
            affected_nodes=["pattern:if_py", "pattern:if_en"],
            metadata={
                "domains": ["python", "english"],
                "content": "if",
            },
        )
        
        graph = PatternGraph()
        
        inquiry = generator._generate_cross_domain_question(gap, graph)
        
        assert inquiry is not None
        assert inquiry.question_type == QuestionType.CROSS_DOMAIN
        assert "python" in inquiry.question.lower()
    
    def test_answer_inquiry(self):
        """Test answering an inquiry."""
        generator = QuestionGenerator()
        
        # Create and register an inquiry
        inquiry = Inquiry(
            inquiry_id="test_inquiry",
            question="Test question?",
            question_type=QuestionType.VALIDATION,
            gap_type=GapType.UNCERTAIN_PATTERN,
            priority=QuestionPriority.MEDIUM,
        )
        
        generator._inquiries[inquiry.inquiry_id] = inquiry
        generator._pending_inquiries.append(inquiry.inquiry_id)
        
        # Answer it
        result = generator.answer_inquiry("test_inquiry", "Yes, that's correct.")
        
        assert result is not None
        assert result.answered is True
        assert result.answer == "Yes, that's correct."
    
    def test_get_pending_inquiries(self):
        """Test getting pending inquiries."""
        generator = QuestionGenerator()
        
        # Create pending and answered inquiries
        pending = Inquiry(
            inquiry_id="pending_1",
            question="Pending?",
            question_type=QuestionType.VALIDATION,
            gap_type=GapType.UNCERTAIN_PATTERN,
            priority=QuestionPriority.MEDIUM,
        )
        
        answered = Inquiry(
            inquiry_id="answered_1",
            question="Answered?",
            question_type=QuestionType.VALIDATION,
            gap_type=GapType.UNCERTAIN_PATTERN,
            priority=QuestionPriority.MEDIUM,
            answered=True,
            answer="Yes",
        )
        
        generator._inquiries["pending_1"] = pending
        generator._inquiries["answered_1"] = answered
        generator._pending_inquiries.append("pending_1")
        
        pending_list = generator.get_pending_inquiries()
        
        assert len(pending_list) == 1
        assert pending_list[0].inquiry_id == "pending_1"
    
    def test_inquiry_serialization(self):
        """Test inquiry serialization."""
        inquiry = Inquiry(
            inquiry_id="test",
            question="Test?",
            question_type=QuestionType.COMPOSITION,
            gap_type=GapType.INCOMPLETE_COMPOSITION,
            priority=QuestionPriority.HIGH,
        )
        
        data = inquiry.to_dict()
        restored = Inquiry.from_dict(data)
        
        assert restored.inquiry_id == inquiry.inquiry_id
        assert restored.question == inquiry.question
        assert restored.question_type == inquiry.question_type
    
    def test_get_statistics(self):
        """Test getting inquiry statistics."""
        generator = QuestionGenerator()
        
        # Add some inquiries
        for i in range(3):
            inquiry = Inquiry(
                inquiry_id=f"inquiry_{i}",
                question=f"Question {i}?",
                question_type=QuestionType.VALIDATION,
                gap_type=GapType.UNCERTAIN_PATTERN,
                priority=QuestionPriority.MEDIUM,
                answered=(i == 0),
            )
            generator._inquiries[inquiry.inquiry_id] = inquiry
        
        stats = generator.get_statistics()
        
        assert stats["total_inquiries"] == 3
        assert stats["answered"] == 1
        assert stats["pending"] == 2
