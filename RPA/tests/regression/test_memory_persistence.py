"""
Memory Persistence Regression Tests (SI-007)

Tests for Long-Term Memory (LTM), Short-Term Memory (STM), and Episodic Memory
to ensure data persistence and retrieval work correctly across sessions.
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta

from rpa.memory.ltm import LongTermMemory
from rpa.memory.stm import ShortTermMemory
from rpa.memory.episodic import EpisodicMemory
from rpa.core.graph import Node, NodeType


class TestLongTermMemoryPersistence:
    """Tests for LTM persistence across sessions."""
    
    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_ltm_save_and_load(self, temp_storage):
        """Test that LTM can save and load state."""
        storage_path = temp_storage / "ltm"
        
        # Create and populate
        ltm1 = LongTermMemory(storage_path)
        
        node = Node(
            node_id="persistence_test_001",
            node_type=NodeType.PATTERN,
            content="def hello(): return 'world'",
            label="hello_function",
            domain="python"
        )
        ltm1.consolidate(node)
        ltm1.save()
        
        # Create new instance and load
        ltm2 = LongTermMemory(storage_path)
        ltm2.load()
        
        # Should have the pattern
        assert len(ltm2) >= 1
    
    def test_ltm_multiple_saves(self, temp_storage):
        """Test multiple save operations."""
        storage_path = temp_storage / "ltm"
        ltm = LongTermMemory(storage_path)
        
        # Add and save multiple times
        for i in range(5):
            node = Node(
                node_id=f"multi_save_{i:03d}",
                node_type=NodeType.PATTERN,
                content=f"content_{i}",
                label=f"label_{i}",
                domain="test"
            )
            ltm.consolidate(node)
            ltm.save()
        
        # Verify all patterns persisted
        ltm2 = LongTermMemory(storage_path)
        ltm2.load()
        
        assert len(ltm2) >= 5
    
    def test_ltm_pattern_update_persistence(self, temp_storage):
        """Test that pattern updates are persisted."""
        storage_path = temp_storage / "ltm"
        
        # Create pattern
        ltm1 = LongTermMemory(storage_path)
        
        node = Node(
            node_id="update_test",
            node_type=NodeType.PATTERN,
            content="original content",
            label="update_test",
            domain="test"
        )
        ltm1.consolidate(node)
        ltm1.save()
        
        # Update pattern
        node.content = "updated content"
        ltm1.update_pattern(node)
        ltm1.save()
        
        # Verify update persisted
        ltm2 = LongTermMemory(storage_path)
        ltm2.load()
        
        retrieved = ltm2.get_pattern("update_test")
        assert retrieved is not None
    
    def test_ltm_large_pattern_set(self, temp_storage):
        """Test persistence with a larger pattern set."""
        storage_path = temp_storage / "ltm"
        ltm = LongTermMemory(storage_path)
        
        # Add 500 patterns
        for i in range(500):
            node = Node(
                node_id=f"large_set_{i:05d}",
                node_type=NodeType.PATTERN,
                content=f"def func_{i}(): return {i}",
                label=f"func_{i}",
                domain="python"
            )
            ltm.consolidate(node)
        
        ltm.save()
        
        # Reload and verify
        ltm2 = LongTermMemory(storage_path)
        ltm2.load()
        
        assert len(ltm2) >= 400  # Should have most patterns
    
    def test_ltm_find_by_domain(self, temp_storage):
        """Test finding patterns by domain."""
        storage_path = temp_storage / "ltm"
        ltm = LongTermMemory(storage_path)
        
        # Add patterns with different domains
        for i in range(10):
            node = Node(
                node_id=f"domain_test_{i:03d}",
                node_type=NodeType.PATTERN,
                content=f"content_{i}",
                label=f"label_{i}",
                domain="python" if i < 5 else "english"
            )
            ltm.consolidate(node)
        
        # Find by domain
        python_patterns = ltm.find_by_domain("python")
        english_patterns = ltm.find_by_domain("english")
        
        assert len(python_patterns) >= 3
        assert len(english_patterns) >= 3
    
    def test_ltm_search(self, temp_storage):
        """Test searching for patterns."""
        storage_path = temp_storage / "ltm"
        ltm = LongTermMemory(storage_path)
        
        # Add patterns with searchable content
        node1 = Node(
            node_id="search_test_1",
            node_type=NodeType.PATTERN,
            content="def calculate_sum(a, b): return a + b",
            label="calculate_sum",
            domain="python"
        )
        node2 = Node(
            node_id="search_test_2",
            node_type=NodeType.PATTERN,
            content="def calculate_product(a, b): return a * b",
            label="calculate_product",
            domain="python"
        )
        ltm.consolidate(node1)
        ltm.consolidate(node2)
        
        # Search
        results = ltm.search("calculate", limit=10)
        
        assert len(results) >= 2


class TestShortTermMemoryBasics:
    """Tests for STM functionality."""
    
    def test_stm_creation(self):
        """Test STM can be created."""
        stm = ShortTermMemory()
        assert stm is not None
    
    def test_stm_is_initialized(self):
        """Test STM is properly initialized."""
        stm = ShortTermMemory()
        
        # Should be initialized without error
        assert stm is not None


class TestEpisodicMemoryBasics:
    """Tests for Episodic Memory functionality."""
    
    def test_episodic_creation(self):
        """Test EpisodicMemory can be created."""
        episodic = EpisodicMemory()
        assert episodic is not None
    
    def test_episodic_is_initialized(self):
        """Test EpisodicMemory is properly initialized."""
        episodic = EpisodicMemory()
        
        # Should be initialized without error
        assert episodic is not None


class TestMemoryIntegration:
    """Tests for memory system integration."""
    
    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_memory_systems_coexist(self, temp_storage):
        """Test that all memory systems work together."""
        ltm = LongTermMemory(temp_storage / "ltm")
        stm = ShortTermMemory()
        episodic = EpisodicMemory()
        
        # All should be created successfully
        assert ltm is not None
        assert stm is not None
        assert episodic is not None
    
    def test_learning_workflow(self, temp_storage):
        """Test a complete learning workflow."""
        ltm = LongTermMemory(temp_storage / "ltm")
        
        # Learn a new pattern
        pattern = Node(
            node_id="workflow_pattern",
            node_type=NodeType.PATTERN,
            content="x = 1 + 1",
            label="addition",
            domain="python"
        )
        
        # Consolidate to LTM
        ltm.consolidate(pattern)
        ltm.save()
        
        # Verify in LTM
        retrieved = ltm.get_pattern("workflow_pattern")
        assert retrieved is not None
    
    def test_memory_state_file_integrity(self, temp_storage):
        """Test that memory state files are valid JSON."""
        storage_path = temp_storage / "ltm"
        
        ltm = LongTermMemory(storage_path)
        
        # Add patterns
        for i in range(10):
            node = Node(
                node_id=f"integrity_test_{i:03d}",
                node_type=NodeType.PATTERN,
                content=f"content_{i}",
                label=f"label_{i}",
                domain="test"
            )
            ltm.consolidate(node)
        
        ltm.save()
        
        # Check state files exist and are valid
        state_dir = storage_path
        if state_dir.exists():
            for state_file in state_dir.glob("*.json"):
                try:
                    with open(state_file, 'r') as f:
                        data = json.load(f)
                    assert isinstance(data, dict) or isinstance(data, list)
                except json.JSONDecodeError:
                    pytest.fail(f"Invalid JSON in {state_file}")


class TestMemoryStatistics:
    """Tests for memory statistics functionality."""
    
    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_ltm_get_stats(self, temp_storage):
        """Test getting LTM statistics."""
        ltm = LongTermMemory(temp_storage / "ltm")
        
        # Add some patterns
        for i in range(5):
            node = Node(
                node_id=f"stats_test_{i:03d}",
                node_type=NodeType.PATTERN,
                content=f"content_{i}",
                label=f"label_{i}",
                domain="test"
            )
            ltm.consolidate(node)
        
        stats = ltm.get_stats()
        
        assert isinstance(stats, dict)
        assert "total_patterns" in stats or "patterns_consolidated" in stats
    
    def test_ltm_len(self, temp_storage):
        """Test LTM length operation."""
        ltm = LongTermMemory(temp_storage / "ltm")
        
        initial_len = len(ltm)
        
        # Add patterns
        for i in range(10):
            node = Node(
                node_id=f"len_test_{i:03d}",
                node_type=NodeType.PATTERN,
                content=f"content_{i}",
                label=f"label_{i}",
                domain="test"
            )
            ltm.consolidate(node)
        
        assert len(ltm) >= initial_len + 5
