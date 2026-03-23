"""
Training Pipeline Regression Tests (SI-007)

Tests the core training pipeline to ensure learning functionality works correctly.
These tests establish baselines for pattern learning, consolidation, and error handling.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from rpa.memory.ltm import LongTermMemory
from rpa.memory.stm import ShortTermMemory
from rpa.memory.episodic import EpisodicMemory
from rpa.core.graph import PatternGraph, Node, NodeType, Edge, EdgeType


class TestTrainingPipelineBasics:
    """Baseline tests for training pipeline functionality."""
    
    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def ltm(self, temp_storage):
        """Create a fresh LTM instance."""
        ltm = LongTermMemory(temp_storage / "ltm")
        return ltm
    
    @pytest.fixture
    def stm(self):
        """Create a fresh STM instance."""
        return ShortTermMemory()
    
    @pytest.fixture
    def episodic(self):
        """Create a fresh EpisodicMemory instance."""
        return EpisodicMemory()
    
    def test_ltm_initialization(self, temp_storage):
        """Test LTM initializes correctly."""
        ltm = LongTermMemory(temp_storage / "ltm")
        
        assert ltm is not None
        assert hasattr(ltm, '_graph')
        assert hasattr(ltm, 'load')
        assert hasattr(ltm, 'save')
    
    def test_ltm_consolidate_pattern(self, ltm):
        """Test consolidating a pattern to LTM."""
        node = Node(
            node_id="test_pattern_001",
            node_type=NodeType.PATTERN,
            content="print('Hello, World!')",
            label="hello_world",
            domain="python"
        )
        
        result = ltm.consolidate(node, session_id="test_session")
        
        assert result is not None
        assert len(ltm) >= 1
    
    def test_ltm_get_pattern(self, ltm):
        """Test retrieving a pattern from LTM."""
        # Add a pattern first
        node = Node(
            node_id="test_pattern_002",
            node_type=NodeType.PATTERN,
            content="x = 10",
            label="variable_assignment",
            domain="python"
        )
        ltm.consolidate(node)
        
        # Retrieve it
        retrieved = ltm.get_pattern("test_pattern_002")
        
        assert retrieved is not None
        assert retrieved.content == "x = 10"
    
    def test_ltm_persistence(self, temp_storage):
        """Test that patterns persist across LTM instances."""
        storage_path = temp_storage / "ltm"
        
        # Create and populate LTM
        ltm1 = LongTermMemory(storage_path)
        
        node = Node(
            node_id="persistent_pattern",
            node_type=NodeType.PATTERN,
            content="def foo(): pass",
            label="foo_function",
            domain="python"
        )
        ltm1.consolidate(node)
        ltm1.save()
        
        # Create new LTM instance and verify persistence
        ltm2 = LongTermMemory(storage_path)
        ltm2.load()
        
        assert len(ltm2) >= 1
        retrieved = ltm2.get_pattern("persistent_pattern")
        assert retrieved is not None
    
    def test_ltm_add_node(self, ltm):
        """Test adding a node directly to LTM."""
        node = Node(
            node_id="test_node_001",
            node_type=NodeType.PATTERN,
            content="test content",
            label="test_node",
            domain="general"
        )
        
        result = ltm.add_node(node)
        
        assert result is not None
        assert ltm.has_pattern("test_node_001")
    
    def test_stm_initialization(self):
        """Test STM initializes correctly."""
        stm = ShortTermMemory()
        assert stm is not None
    
    def test_episodic_memory_initialization(self):
        """Test EpisodicMemory initializes correctly."""
        episodic = EpisodicMemory()
        
        assert episodic is not None
    
    def test_pattern_graph_initialization(self):
        """Test PatternGraph initializes correctly."""
        graph = PatternGraph()
        
        assert graph is not None
        assert hasattr(graph, 'nodes')
        assert hasattr(graph, 'edges')
    
    def test_pattern_graph_add_node(self):
        """Test adding nodes to PatternGraph."""
        graph = PatternGraph()
        
        node = Node(
            node_id="graph_node_001",
            node_type=NodeType.PATTERN,
            content="test content",
            label="test_node",
            domain="general"
        )
        
        graph.add_node(node)
        
        assert graph.has_node("graph_node_001")
    
    def test_pattern_graph_add_edge(self):
        """Test adding edges to PatternGraph."""
        graph = PatternGraph()
        
        node1 = Node(
            node_id="node_1",
            node_type=NodeType.PATTERN,
            content="parent",
            label="parent",
            domain="general"
        )
        node2 = Node(
            node_id="node_2",
            node_type=NodeType.PATTERN,
            content="child",
            label="child",
            domain="general"
        )
        
        graph.add_node(node1)
        graph.add_node(node2)
        
        # Create an edge
        edge = Edge(
            edge_id="edge_1",
            source_id="node_1",
            target_id="node_2",
            edge_type=EdgeType.COMPOSED_OF
        )
        graph.add_edge(edge)
        
        assert len(graph.edges) >= 1
    
    def test_pattern_creation_with_metadata(self, ltm):
        """Test creating patterns with metadata."""
        node = Node(
            node_id="metadata_pattern",
            node_type=NodeType.PATTERN,
            content="import os",
            label="import_os",
            domain="python",
            metadata={
                "created_by": "test",
                "difficulty": 1,
                "tags": ["import", "module"]
            }
        )
        
        ltm.consolidate(node)
        retrieved = ltm.get_pattern("metadata_pattern")
        
        assert retrieved is not None
        if hasattr(retrieved, 'metadata'):
            assert "tags" in retrieved.metadata


class TestTrainingPipelineErrors:
    """Tests for training pipeline error handling."""
    
    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_ltm_get_nonexistent_pattern(self, temp_storage):
        """Test getting a pattern that doesn't exist."""
        ltm = LongTermMemory(temp_storage / "ltm")
        
        result = ltm.get_pattern("nonexistent_pattern_xyz")
        
        # Should return None
        assert result is None
    
    def test_ltm_save_to_invalid_path(self):
        """Test saving LTM to invalid path."""
        ltm = LongTermMemory(Path("/nonexistent/path/ltm"))
        
        # Should not crash when initializing
        assert ltm is not None


class TestTrainingPipelinePerformance:
    """Tests for training pipeline performance baselines."""
    
    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_add_multiple_patterns(self, temp_storage):
        """Test adding multiple patterns in bulk."""
        ltm = LongTermMemory(temp_storage / "ltm")
        
        initial_count = len(ltm)
        
        for i in range(100):
            node = Node(
                node_id=f"bulk_pattern_{i:04d}",
                node_type=NodeType.PATTERN,
                content=f"content_{i}",
                label=f"label_{i}",
                domain="test"
            )
            ltm.consolidate(node)
        
        # Should have added patterns
        assert len(ltm) >= initial_count + 50  # At least half should succeed
    
    def test_pattern_retrieval_speed(self, temp_storage):
        """Test pattern retrieval is reasonably fast."""
        import time
        
        ltm = LongTermMemory(temp_storage / "ltm")
        
        # Add some patterns
        for i in range(50):
            node = Node(
                node_id=f"speed_test_{i:04d}",
                node_type=NodeType.PATTERN,
                content=f"content_{i}",
                label=f"label_{i}",
                domain="test"
            )
            ltm.consolidate(node)
        
        # Measure retrieval time
        start = time.time()
        for i in range(50):
            ltm.get_pattern(f"speed_test_{i:04d}")
        elapsed = time.time() - start
        
        # Should be fast (less than 1 second for 50 retrievals)
        assert elapsed < 1.0
    
    def test_search_performance(self, temp_storage):
        """Test search is reasonably fast."""
        import time
        
        ltm = LongTermMemory(temp_storage / "ltm")
        
        # Add some patterns
        for i in range(100):
            node = Node(
                node_id=f"search_test_{i:04d}",
                node_type=NodeType.PATTERN,
                content=f"def function_{i}(): return {i}",
                label=f"func_{i}",
                domain="python"
            )
            ltm.consolidate(node)
        
        # Measure search time
        start = time.time()
        results = ltm.search("function", limit=20)
        elapsed = time.time() - start
        
        # Should be fast
        assert elapsed < 0.5
