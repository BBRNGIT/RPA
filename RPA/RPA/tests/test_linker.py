"""
Tests for Recursive Linker Module (Simplified).

Focus on core RecursiveLinker functionality with compatibility fixes.
"""

import pytest

from rpa.learning.recursive_linker import (
    RecursiveLinker,
    LinkResult,
    CompoundPattern,
    IntegrityReport
)
from rpa.memory import LongTermMemory
from rpa.core import Node, NodeType


class TestLinkResult:
    """Tests for LinkResult."""

    def test_create_success_result(self):
        """Test creating a successful link result."""
        result = LinkResult(
            source_id="pattern:ab",
            target_id="primitive:a",
            link_type="composition",
            success=True,
            message="Linked successfully"
        )
        assert result.success is True
        assert result.source_id == "pattern:ab"

    def test_create_failure_result(self):
        """Test creating a failed link result."""
        result = LinkResult(
            source_id="pattern:xyz",
            target_id="primitive:x",
            link_type="composition",
            success=False,
            message="Target node not found"
        )
        assert result.success is False

    def test_to_dict(self):
        """Test converting LinkResult to dictionary."""
        result = LinkResult(
            source_id="a",
            target_id="b",
            link_type="test",
            success=True,
            metadata={"key": "value"}
        )
        d = result.to_dict()
        assert d["success"] is True
        assert d["metadata"]["key"] == "value"


class TestCompoundPattern:
    """Tests for CompoundPattern."""

    def test_create_compound(self):
        """Test creating a compound pattern."""
        compound = CompoundPattern(
            pattern_id="compound:apple_tree",
            component_ids=["pattern:apple", "pattern:tree"],
            label="apple tree",
            domain="english",
            hierarchy_level=1,
            confidence=0.9
        )
        assert compound.pattern_id == "compound:apple_tree"
        assert len(compound.component_ids) == 2

    def test_to_dict(self):
        """Test converting CompoundPattern to dictionary."""
        compound = CompoundPattern(
            pattern_id="test",
            component_ids=["a", "b"],
            label="test",
            domain="english",
            hierarchy_level=1
        )
        d = compound.to_dict()
        assert d["pattern_id"] == "test"
        assert d["component_ids"] == ["a", "b"]


class TestIntegrityReport:
    """Tests for IntegrityReport."""

    def test_create_valid_report(self):
        """Test creating a valid integrity report."""
        report = IntegrityReport(
            node_id="pattern:test",
            is_valid=True,
            hierarchy_depth=2,
            total_linked_nodes=5
        )
        assert report.is_valid is True
        assert report.total_linked_nodes == 5

    def test_create_invalid_report(self):
        """Test creating an invalid integrity report."""
        report = IntegrityReport(
            node_id="pattern:test",
            is_valid=False,
            missing_links=["primitive:x"],
            orphaned_nodes=["primitive:y"]
        )
        assert report.is_valid is False
        assert len(report.missing_links) == 1
        assert len(report.orphaned_nodes) == 1

    def test_to_dict(self):
        """Test converting IntegrityReport to dictionary."""
        report = IntegrityReport(
            node_id="test",
            is_valid=True,
            hierarchy_depth=3,
            total_linked_nodes=10
        )
        d = report.to_dict()
        assert d["is_valid"] is True
        assert d["hierarchy_depth"] == 3


class TestRecursiveLinker:
    """Tests for RecursiveLinker."""

    @pytest.fixture
    def linker(self):
        """Create a RecursiveLinker instance."""
        return RecursiveLinker()

    def test_init(self, linker):
        """Test RecursiveLinker initialization."""
        assert linker._link_cache == {}
        assert linker._compound_patterns == {}

    def test_clear_cache(self, linker):
        """Test clearing the cache."""
        linker._link_cache["test"] = [LinkResult("a", "b", "test", True)]
        linker._compound_patterns["test"] = CompoundPattern(
            pattern_id="test",
            component_ids=["a", "b"],
            label="test",
            domain="english",
            hierarchy_level=1
        )
        linker.clear_cache()
        assert linker._link_cache == {}
        assert linker._compound_patterns == {}

    def test_get_hierarchy_stats(self, linker):
        """Test getting hierarchy statistics."""
        ltm = LongTermMemory()
        
        # Add some nodes
        for char in "abc":
            node = Node(
                node_id=f"primitive:{char}",
                label=char,
                node_type=NodeType.PRIMITIVE,
                content=char,
                domain="english",
                hierarchy_level=0
            )
            ltm.add_node(node)
        
        stats = linker.get_hierarchy_stats(ltm, "english")
        assert stats["total_nodes"] == 3
        assert 0 in stats["by_level"]
        assert "english" in stats["by_domain"]
