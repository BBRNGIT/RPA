"""
Tests for RPA Validation module.
"""

import pytest

from rpa.core.graph import Node, Edge, PatternGraph, NodeType, EdgeType
from rpa.validation.validator import Validator, ValidationResult
from rpa.validation.reporter import ConsolidationReporter
from rpa.memory.stm import ShortTermMemory
from rpa.memory.ltm import LongTermMemory
from tests.fixtures import (
    word_graph, empty_stm, stm_with_session, stm_with_patterns, empty_ltm
)


class TestValidator:
    """Tests for the Validator class."""
    
    def test_validate_primitive(self, word_graph: PatternGraph):
        """Test validating a primitive node."""
        validator = Validator()
        
        result = validator.validate_pattern_structure_detailed(
            "primitive:a", word_graph
        )
        
        assert result["is_valid"] is True
        assert result["composition_depth"] == 0
    
    def test_validate_valid_pattern(self, word_graph: PatternGraph):
        """Test validating a valid pattern."""
        validator = Validator()
        
        result = validator.validate_pattern_structure_detailed(
            "pattern:cat", word_graph
        )
        
        assert result["is_valid"] is True
        assert result["all_children_resolved"] is True
        assert len(result["missing_references"]) == 0
    
    def test_validate_missing_reference(self):
        """Test detecting missing references."""
        validator = Validator()
        graph = PatternGraph()
        
        # Create a pattern without its children
        node = Node.create_pattern("test", "test", 1)
        graph.add_node(node)
        
        # Add an edge to a non-existent child
        from rpa.core.graph import Edge, EdgeType
        edge = Edge(
            edge_id="test_edge",
            source_id="pattern:test",
            target_id="primitive:x",  # doesn't exist
            edge_type=EdgeType.COMPOSED_OF,
        )
        graph.edges[edge.edge_id] = edge
        graph.outgoing_edges["pattern:test"].append(edge.edge_id)
        
        result = validator.validate_pattern_structure_detailed(
            "pattern:test", graph
        )
        
        assert result["is_valid"] is False
        assert "primitive:x" in result["missing_references"]
    
    def test_validate_circular_dependency(self):
        """Test detecting circular dependencies."""
        validator = Validator()
        graph = PatternGraph()
        
        # Create nodes
        a = Node.create_pattern("a", "a", 1)
        b = Node.create_pattern("b", "b", 1)
        
        graph.add_node(a)
        graph.add_node(b)
        
        # Create circular reference
        graph.add_edge(Edge(
            edge_id="e1",
            source_id="pattern:a",
            target_id="pattern:b",
            edge_type=EdgeType.COMPOSED_OF,
        ))
        graph.add_edge(Edge(
            edge_id="e2",
            source_id="pattern:b",
            target_id="pattern:a",
            edge_type=EdgeType.COMPOSED_OF,
        ))
        
        result = validator.validate_pattern_structure_detailed(
            "pattern:a", graph
        )
        
        assert result["is_valid"] is False
        assert len(result["circular_deps"]) > 0
    
    def test_validate_batch(self, word_graph: PatternGraph):
        """Test validating a batch of patterns."""
        validator = Validator()
        
        node_ids = [
            "primitive:a", "primitive:b", "pattern:cat", "pattern:dog"
        ]
        
        results = validator.validate_batch(node_ids, word_graph)
        
        assert results["total"] == 4
        assert results["valid"] >= 2  # At least primitives should be valid
    
    def test_suggest_fixes_valid(self, word_graph: PatternGraph):
        """Test suggesting fixes for a valid pattern."""
        validator = Validator()
        
        fixes = validator.suggest_fixes("pattern:cat", word_graph)
        
        assert "No fixes needed" in fixes[0]
    
    def test_suggest_fixes_invalid(self):
        """Test suggesting fixes for an invalid pattern."""
        validator = Validator()
        graph = PatternGraph()
        
        node = Node.create_pattern("test", "test", 1)
        graph.add_node(node)
        
        # Manually add unresolved edge
        from rpa.core.graph import Edge, EdgeType
        edge = Edge(
            edge_id="test_edge",
            source_id="pattern:test",
            target_id="primitive:x",
            edge_type=EdgeType.COMPOSED_OF,
        )
        graph.edges[edge.edge_id] = edge
        graph.outgoing_edges["pattern:test"].append(edge.edge_id)
        
        fixes = validator.suggest_fixes("pattern:test", graph)
        
        assert len(fixes) > 0
        assert any("primitive:x" in f for f in fixes)
    
    def test_validation_cache(self, word_graph: PatternGraph):
        """Test that validation results are cached."""
        validator = Validator()
        
        # First validation
        result1 = validator.validate_pattern_structure_detailed(
            "pattern:cat", word_graph
        )
        
        # Second validation should use cache
        result2 = validator.validate_pattern_structure_detailed(
            "pattern:cat", word_graph
        )
        
        assert result1 == result2
        
        # Check cache
        cached = validator.get_cached_result("pattern:cat")
        assert cached is not None
    
    def test_clear_cache(self, word_graph: PatternGraph):
        """Test clearing the validation cache."""
        validator = Validator()
        
        validator.validate_pattern_structure_detailed("pattern:cat", word_graph)
        
        validator.clear_cache()
        
        cached = validator.get_cached_result("pattern:cat")
        assert cached is None


class TestConsolidationReporter:
    """Tests for the ConsolidationReporter class."""
    
    def test_report_consolidation(
        self,
        empty_stm: ShortTermMemory,
        empty_ltm: LongTermMemory,
    ):
        """Test generating a consolidation report."""
        reporter = ConsolidationReporter()
        
        # Create a session and add patterns
        session_id = empty_stm.create_session("test_batch")
        
        # Add primitives
        for c in "cat":
            node = Node.create_primitive(c)
            empty_stm.add_pattern(node, session_id)
        
        # Create report
        report = reporter.report_consolidation(
            batch_id="test_batch",
            session_id=session_id,
            stm=empty_stm,
            ltm=empty_ltm,
        )
        
        assert report["batch_id"] == "test_batch"
        assert report["session_id"] == session_id
        assert report["total_patterns"] == 3
    
    def test_identify_rejection_patterns(self, empty_stm: ShortTermMemory):
        """Test identifying rejection patterns."""
        reporter = ConsolidationReporter()
        
        session_id = empty_stm.create_session("test_batch")
        
        # Add and reject some patterns
        node = Node.create_primitive("x")
        empty_stm.add_pattern(node, session_id)
        empty_stm.mark_rejected(node.node_id)
        
        analysis = reporter.identify_rejection_patterns("test_batch", empty_stm)
        
        assert analysis["batch_id"] == "test_batch"
        assert analysis["total_rejections"] >= 1
    
    def test_suggest_fixes(self, word_graph: PatternGraph):
        """Test suggesting fixes through reporter."""
        reporter = ConsolidationReporter()
        
        fixes = reporter.suggest_fixes("pattern:cat", word_graph)
        
        assert len(fixes) > 0
    
    def test_export_report_json(self, empty_stm: ShortTermMemory, empty_ltm: LongTermMemory):
        """Test exporting a report as JSON."""
        reporter = ConsolidationReporter()
        
        session_id = empty_stm.create_session("test_batch")
        
        report = reporter.report_consolidation(
            "test_batch", session_id, empty_stm, empty_ltm
        )
        
        exported = reporter.export_report("test_batch_test_batch", "json")
        
        assert exported is not None
        assert "test_batch" in exported
    
    def test_export_report_text(self, empty_stm: ShortTermMemory, empty_ltm: LongTermMemory):
        """Test exporting a report as text."""
        reporter = ConsolidationReporter()
        
        session_id = empty_stm.create_session("test_batch")
        
        report = reporter.report_consolidation(
            "test_batch", session_id, empty_stm, empty_ltm
        )
        
        exported = reporter.export_report("test_batch_test_batch", "text")
        
        assert exported is not None
        assert "Consolidation Report" in exported
    
    def test_list_reports(self, empty_stm: ShortTermMemory, empty_ltm: LongTermMemory):
        """Test listing stored reports."""
        reporter = ConsolidationReporter()
        
        session_id = empty_stm.create_session("test_batch")
        reporter.report_consolidation("test_batch", session_id, empty_stm, empty_ltm)
        
        reports = reporter.list_reports()
        
        assert len(reports) >= 1
    
    def test_clear_reports(self, empty_stm: ShortTermMemory, empty_ltm: LongTermMemory):
        """Test clearing stored reports."""
        reporter = ConsolidationReporter()
        
        session_id = empty_stm.create_session("test_batch")
        reporter.report_consolidation("test_batch", session_id, empty_stm, empty_ltm)
        
        reporter.clear_reports()
        
        assert len(reporter.list_reports()) == 0
