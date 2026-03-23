"""
Tests for Self-Improvement Orchestrator (SI-001)

Tests the unified entry point for closed-loop self-improvement.
"""

import pytest
from datetime import datetime
from pathlib import Path
import tempfile
import shutil

from rpa.training.self_improvement import (
    SelfImprovementOrchestrator,
    SelfImprovementConfig,
    ImprovementCycle,
    SystemHealth,
    create_self_improvement,
    run_improvement_cycle,
)


class TestSelfImprovementConfig:
    """Tests for configuration."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = SelfImprovementConfig()
        
        assert config.confidence_threshold == 0.7
        assert config.low_confidence_threshold == 0.3
        assert config.high_confidence_threshold == 0.8
        assert config.mutation_rate == 0.1
        assert config.max_mutations_per_cycle == 10
        assert config.enable_auto_mutation is True
        assert config.reinforcement_decay == 0.05
        assert config.patterns_per_cycle == 50
        assert config.auto_save is True
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = SelfImprovementConfig(
            confidence_threshold=0.85,
            max_mutations_per_cycle=5,
            enable_auto_mutation=False
        )
        
        assert config.confidence_threshold == 0.85
        assert config.max_mutations_per_cycle == 5
        assert config.enable_auto_mutation is False


class TestImprovementCycle:
    """Tests for ImprovementCycle dataclass."""
    
    def test_cycle_creation(self):
        """Test creating an improvement cycle."""
        cycle = ImprovementCycle(
            cycle_id="test_cycle_001",
            start_time=datetime.now()
        )
        
        assert cycle.cycle_id == "test_cycle_001"
        assert cycle.start_time is not None
        assert cycle.end_time is None
        assert cycle.patterns_evaluated == 0
        assert cycle.patterns_reinforced == 0
        assert cycle.errors == []
    
    def test_cycle_to_dict(self):
        """Test serialization to dictionary."""
        cycle = ImprovementCycle(
            cycle_id="test_cycle_002",
            start_time=datetime(2024, 1, 1, 12, 0, 0),
            end_time=datetime(2024, 1, 1, 12, 0, 5),
            patterns_evaluated=10,
            patterns_reinforced=8
        )
        
        data = cycle.to_dict()
        
        assert data["cycle_id"] == "test_cycle_002"
        assert data["patterns_evaluated"] == 10
        assert data["patterns_reinforced"] == 8
        assert "start_time" in data
        assert "end_time" in data
    
    def test_cycle_duration(self):
        """Test duration calculation."""
        cycle = ImprovementCycle(
            cycle_id="test_cycle_003",
            start_time=datetime(2024, 1, 1, 12, 0, 0),
            end_time=datetime(2024, 1, 1, 12, 0, 10)
        )
        
        assert cycle.duration_seconds == 10.0
        
        # No end time
        cycle2 = ImprovementCycle(
            cycle_id="test_cycle_004",
            start_time=datetime.now()
        )
        assert cycle2.duration_seconds == 0.0


class TestSystemHealth:
    """Tests for SystemHealth dataclass."""
    
    def test_health_creation(self):
        """Test creating system health."""
        health = SystemHealth()
        
        assert health.total_patterns == 0
        assert health.strong_patterns == 0
        assert health.weak_patterns == 0
        assert health.avg_pattern_strength == 0.0
    
    def test_health_to_dict(self):
        """Test health serialization."""
        health = SystemHealth(
            total_patterns=100,
            strong_patterns=70,
            weak_patterns=10,
            recent_success_rate=0.85
        )
        
        data = health.to_dict()
        
        assert data["total_patterns"] == 100
        assert data["strong_patterns"] == 70
        assert data["weak_patterns"] == 10
        assert data["recent_success_rate"] == 0.85


class TestSelfImprovementOrchestrator:
    """Tests for the main orchestrator."""
    
    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def config(self):
        """Test configuration."""
        return SelfImprovementConfig(
            patterns_per_cycle=5,
            max_mutations_per_cycle=2,
            enable_auto_mutation=False
        )
    
    def test_orchestrator_creation(self, temp_storage, config):
        """Test creating an orchestrator."""
        orchestrator = SelfImprovementOrchestrator(
            storage_path=temp_storage,
            config=config
        )
        
        assert orchestrator.config == config
        assert orchestrator.cycle_count == 0
        assert len(orchestrator.ltm) == 0
    
    def test_orchestrator_components(self, temp_storage, config):
        """Test that all components are initialized."""
        orchestrator = SelfImprovementOrchestrator(
            storage_path=temp_storage,
            config=config
        )
        
        # Check closed-loop components
        assert orchestrator.evaluator is not None
        assert orchestrator.reinforcement is not None
        assert orchestrator.mutator is not None
        assert orchestrator.evolution is not None
        assert orchestrator.questioning_gate is not None
        assert orchestrator.retry_engine is not None
    
    def test_run_improvement_cycle(self, temp_storage, config):
        """Test running an improvement cycle."""
        orchestrator = SelfImprovementOrchestrator(
            storage_path=temp_storage,
            config=config
        )
        
        cycle = orchestrator.run_improvement_cycle()
        
        assert cycle.cycle_id is not None
        assert cycle.start_time is not None
        assert cycle.end_time is not None
        assert cycle.duration_seconds >= 0
        assert orchestrator.cycle_count == 1
    
    def test_get_system_health(self, temp_storage, config):
        """Test getting system health."""
        orchestrator = SelfImprovementOrchestrator(
            storage_path=temp_storage,
            config=config
        )
        
        health = orchestrator.get_system_health()
        
        assert isinstance(health, SystemHealth)
        assert health.total_patterns == 0
    
    def test_get_learning_priorities(self, temp_storage, config):
        """Test getting learning priorities."""
        orchestrator = SelfImprovementOrchestrator(
            storage_path=temp_storage,
            config=config
        )
        
        priorities = orchestrator.get_learning_priorities()
        
        assert "weak_patterns" in priorities
        assert "needs_fix" in priorities
        assert "problematic" in priorities
        assert "needs_attention" in priorities
        assert "gaps" in priorities
    
    def test_get_cycle_stats(self, temp_storage, config):
        """Test getting cycle statistics."""
        orchestrator = SelfImprovementOrchestrator(
            storage_path=temp_storage,
            config=config
        )
        
        # Run a few cycles
        for _ in range(3):
            orchestrator.run_improvement_cycle()
        
        stats = orchestrator.get_cycle_stats()
        
        assert stats["total_cycles"] == 3
        assert stats["analyzed_cycles"] == 3
        assert len(stats["cycle_ids"]) == 3
    
    def test_save_and_load_state(self, temp_storage, config):
        """Test state persistence."""
        orchestrator = SelfImprovementOrchestrator(
            storage_path=temp_storage,
            config=config
        )
        
        # Run some cycles
        for _ in range(5):
            orchestrator.run_improvement_cycle()
        
        # Save
        orchestrator.save()
        
        # Create new orchestrator and verify state loaded
        orchestrator2 = SelfImprovementOrchestrator(
            storage_path=temp_storage,
            config=config
        )
        
        assert orchestrator2.cycle_count == 5
    
    def test_orchestrator_repr(self, temp_storage, config):
        """Test string representation."""
        orchestrator = SelfImprovementOrchestrator(
            storage_path=temp_storage,
            config=config
        )
        
        repr_str = repr(orchestrator)
        
        assert "SelfImprovementOrchestrator" in repr_str
        assert "patterns=" in repr_str
        assert "cycles=" in repr_str


class TestConvenienceFunctions:
    """Tests for convenience functions."""
    
    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_create_self_improvement(self, temp_storage):
        """Test create_self_improvement function."""
        orchestrator = create_self_improvement(
            storage_path=temp_storage,
            confidence_threshold=0.9
        )
        
        assert isinstance(orchestrator, SelfImprovementOrchestrator)
        assert orchestrator.config.confidence_threshold == 0.9
    
    def test_run_improvement_cycle_function(self, temp_storage):
        """Test run_improvement_cycle function."""
        orchestrator = create_self_improvement(storage_path=temp_storage)
        
        cycle = run_improvement_cycle(orchestrator)
        
        assert isinstance(cycle, ImprovementCycle)
        assert orchestrator.cycle_count == 1
    
    def test_run_improvement_cycle_creates_orchestrator(self):
        """Test that run_improvement_cycle creates orchestrator if None."""
        cycle = run_improvement_cycle()
        
        assert isinstance(cycle, ImprovementCycle)


class TestCycleHistory:
    """Tests for cycle history management."""
    
    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_cycle_history_tracking(self, temp_storage):
        """Test that cycle history is tracked."""
        config = SelfImprovementConfig(patterns_per_cycle=1)
        orchestrator = SelfImprovementOrchestrator(
            storage_path=temp_storage,
            config=config
        )
        
        # Run multiple cycles
        for _ in range(5):
            orchestrator.run_improvement_cycle()
        
        assert len(orchestrator.cycle_history) == 5
        
        # Check cycle IDs are unique
        cycle_ids = [c.cycle_id for c in orchestrator.cycle_history]
        assert len(set(cycle_ids)) == 5
    
    def test_cycle_history_order(self, temp_storage):
        """Test that cycle history maintains order."""
        config = SelfImprovementConfig(patterns_per_cycle=1)
        orchestrator = SelfImprovementOrchestrator(
            storage_path=temp_storage,
            config=config
        )
        
        # Run cycles
        for i in range(3):
            orchestrator.run_improvement_cycle()
        
        # Check order
        for i, cycle in enumerate(orchestrator.cycle_history):
            assert cycle.cycle_id.endswith(f"_{i}")
