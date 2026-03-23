"""
Tests for Self-Improvement Orchestrator (SI-001, SI-002, SI-003, SI-004)

Tests the unified entry point for closed-loop self-improvement.
"""

import pytest
from datetime import datetime
from pathlib import Path
import tempfile
import shutil
import yaml
import os

from rpa.training.self_improvement import (
    SelfImprovementOrchestrator,
    SelfImprovementConfig,
    ImprovementCycle,
    SystemHealth,
    create_self_improvement,
    run_improvement_cycle,
)

from rpa.training.si_config import (
    SIConfiguration,
    ConfidenceConfig,
    MutationConfig,
    ReinforcementConfig,
    RetryConfigData,
    CycleConfig,
    PersistenceConfig,
    GapDetectionConfig,
    MonitoringConfig,
    SafetyConfig,
    get_si_config,
    create_self_improvement_config_from_yaml,
)

from rpa.training.gap_closure import (
    GapClosureLoop,
    LearningGoal,
    LearningGoalStatus,
    GapClosureStrategy,
    GapClosureResult
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


class TestDailyTimetableIntegration:
    """Tests for SI-002: Daily Timetable Integration."""
    
    def test_self_improvement_task_type_exists(self):
        """Test that SELF_IMPROVEMENT_CYCLE task type exists."""
        from rpa.scheduling.daily_timetable import TaskType
        
        assert hasattr(TaskType, 'SELF_IMPROVEMENT_CYCLE')
        assert TaskType.SELF_IMPROVEMENT_CYCLE.value == "self_improvement_cycle"
    
    def test_scheduler_creates_si_tasks(self):
        """Test that scheduler creates self-improvement tasks."""
        from rpa.scheduling.daily_timetable import TimetableScheduler, TaskType
        
        scheduler = TimetableScheduler()
        timetable = scheduler.generate_daily_timetable()
        
        si_tasks = [t for t in timetable.tasks if t.task_type == TaskType.SELF_IMPROVEMENT_CYCLE]
        
        # Should have 3 SI cycles per day
        assert len(si_tasks) == 3
        
        # Check cycle IDs
        cycle_ids = [t.config.get('cycle_id') for t in si_tasks]
        assert 'morning' in cycle_ids
        assert 'midday' in cycle_ids
        assert 'evening' in cycle_ids
    
    def test_si_tasks_high_priority(self):
        """Test that SI tasks are high priority."""
        from rpa.scheduling.daily_timetable import TimetableScheduler, TaskType, TaskPriority
        
        scheduler = TimetableScheduler()
        timetable = scheduler.generate_daily_timetable()
        
        si_tasks = [t for t in timetable.tasks if t.task_type == TaskType.SELF_IMPROVEMENT_CYCLE]
        
        for task in si_tasks:
            assert task.priority == TaskPriority.HIGH
    
    def test_executor_has_si_orchestrator(self):
        """Test that executor has lazy-loaded SI orchestrator."""
        from rpa.scheduling.daily_timetable import DailyJobExecutor
        
        executor = DailyJobExecutor(storage_path='/tmp/test_si_executor')
        
        # Initially None
        assert executor._si_orchestrator is None
        
        # Access property to lazy load
        orchestrator = executor.si_orchestrator
        
        assert orchestrator is not None
        assert executor._si_orchestrator is not None
    
    def test_execute_si_task(self):
        """Test executing a self-improvement task."""
        from rpa.scheduling.daily_timetable import (
            DailyJobExecutor, ScheduledTask, TaskType, TaskPriority
        )
        from datetime import time
        
        executor = DailyJobExecutor(storage_path='/tmp/test_si_execute')
        
        task = ScheduledTask(
            task_id='test_si_task',
            task_type=TaskType.SELF_IMPROVEMENT_CYCLE,
            priority=TaskPriority.HIGH,
            scheduled_time=time(6, 0),
            duration_minutes=10,
            config={'cycle_id': 'test', 'patterns': 10}
        )
        
        result = executor.execute_task(task)
        
        assert result['success'] is True
        assert 'metrics' in result
        assert result['metrics']['success'] is True
        assert 'cycle_completed' in result['metrics']
    
    def test_si_config_customizable(self):
        """Test that SI config can be customized."""
        from rpa.scheduling.daily_timetable import TimetableScheduler
        
        # Custom config
        scheduler = TimetableScheduler()
        scheduler.config['self_improvement']['cycles_per_day'] = 2
        scheduler.config['self_improvement']['patterns_per_cycle'] = 100
        
        timetable = scheduler.generate_daily_timetable()
        
        from rpa.scheduling.daily_timetable import TaskType
        si_tasks = [t for t in timetable.tasks if t.task_type == TaskType.SELF_IMPROVEMENT_CYCLE]
        
        assert len(si_tasks) == 2  # Custom: 2 cycles instead of 3


class TestSIConfiguration:
    """Tests for SI-003: YAML Configuration System."""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary config directory."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_si_config_defaults(self):
        """Test SIConfiguration default values."""
        config = SIConfiguration()
        
        assert config.confidence.default_threshold == 0.7
        assert config.confidence.low_confidence_threshold == 0.3
        assert config.mutation.rate == 0.1
        assert config.reinforcement.decay_rate == 0.05
    
    def test_si_config_load_from_yaml(self, temp_config_dir):
        """Test loading configuration from YAML file."""
        config_file = temp_config_dir / "test_config.yaml"
        
        yaml_content = """
confidence:
  default_threshold: 0.85
  low_confidence_threshold: 0.4
mutation:
  rate: 0.2
  max_per_cycle: 5
"""
        config_file.write_text(yaml_content)
        
        config = SIConfiguration(config_path=config_file)
        config.load()
        
        assert config.confidence.default_threshold == 0.85
        assert config.confidence.low_confidence_threshold == 0.4
        assert config.mutation.rate == 0.2
        assert config.mutation.max_per_cycle == 5
    
    def test_si_config_missing_file_uses_defaults(self, temp_config_dir):
        """Test that missing config file uses defaults."""
        config = SIConfiguration(config_path=temp_config_dir / "nonexistent.yaml")
        result = config.load()
        
        assert result is True  # Still succeeds with defaults
        assert config.confidence.default_threshold == 0.7
    
    def test_si_config_to_dict(self):
        """Test converting config to dictionary."""
        config = SIConfiguration()
        config.load()
        
        data = config.to_dict()
        
        assert 'confidence' in data
        assert 'mutation' in data
        assert 'reinforcement' in data
        assert 'retry' in data
        assert 'cycle' in data
    
    def test_si_config_save(self, temp_config_dir):
        """Test saving configuration to file."""
        config = SIConfiguration()
        config.load()
        
        # Modify a value
        config.confidence.default_threshold = 0.9
        
        save_path = temp_config_dir / "saved_config.yaml"
        result = config.save(save_path)
        
        assert result is True
        assert save_path.exists()
        
        # Load and verify
        loaded = SIConfiguration(config_path=save_path)
        loaded.load()
        assert loaded.confidence.default_threshold == 0.9
    
    def test_si_config_update(self):
        """Test updating individual config values."""
        config = SIConfiguration()
        config.load()
        
        result = config.update('confidence', 'default_threshold', 0.95)
        
        assert result is True
        assert config.confidence.default_threshold == 0.95
    
    def test_si_config_update_invalid_section(self):
        """Test updating invalid section."""
        config = SIConfiguration()
        config.load()
        
        result = config.update('nonexistent', 'key', 'value')
        
        assert result is False
    
    def test_si_config_update_invalid_key(self):
        """Test updating invalid key."""
        config = SIConfiguration()
        config.load()
        
        result = config.update('confidence', 'nonexistent', 'value')
        
        assert result is False
    
    def test_domain_specific_config(self, temp_config_dir):
        """Test domain-specific configuration overrides."""
        config_file = temp_config_dir / "domain_config.yaml"
        
        yaml_content = """
confidence:
  default_threshold: 0.7
domains:
  python:
    confidence:
      default_threshold: 0.6
  medicine:
    confidence:
      default_threshold: 0.85
"""
        config_file.write_text(yaml_content)
        
        config = SIConfiguration(config_path=config_file)
        config.load()
        
        # Base config
        assert config.confidence.default_threshold == 0.7
        
        # Python domain override
        python_config = config.get_domain_config('python')
        assert python_config['confidence']['default_threshold'] == 0.6
        
        # Medicine domain override
        medicine_config = config.get_domain_config('medicine')
        assert medicine_config['confidence']['default_threshold'] == 0.85
    
    def test_get_si_config_singleton(self):
        """Test get_si_config returns singleton."""
        # Reset singleton
        import rpa.training.si_config as si_config_module
        si_config_module._config_instance = None
        
        config1 = get_si_config()
        config2 = get_si_config()
        
        assert config1 is config2
    
    def test_create_self_improvement_config_from_yaml(self, temp_config_dir):
        """Test creating SelfImprovementConfig from YAML."""
        config_file = temp_config_dir / "test.yaml"
        
        yaml_content = """
confidence:
  default_threshold: 0.8
mutation:
  rate: 0.15
  max_per_cycle: 20
reinforcement:
  decay_rate: 0.03
cycle:
  patterns_per_cycle: 100
"""
        config_file.write_text(yaml_content)
        
        si_config = create_self_improvement_config_from_yaml(config_file)
        
        assert si_config.confidence_threshold == 0.8
        assert si_config.mutation_rate == 0.15
        assert si_config.max_mutations_per_cycle == 20
        assert si_config.reinforcement_decay == 0.03
        assert si_config.patterns_per_cycle == 100


class TestOrchestratorWithYAMLConfig:
    """Tests for orchestrator using YAML configuration."""
    
    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def temp_config(self):
        """Create temporary config file."""
        temp_dir = tempfile.mkdtemp()
        config_file = Path(temp_dir) / "test_config.yaml"
        
        yaml_content = """
confidence:
  default_threshold: 0.75
mutation:
  rate: 0.12
  max_per_cycle: 8
cycle:
  patterns_per_cycle: 25
"""
        config_file.write_text(yaml_content)
        yield config_file
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_orchestrator_uses_yaml_config(self, temp_storage, temp_config):
        """Test that orchestrator loads YAML config by default."""
        orchestrator = SelfImprovementOrchestrator(
            storage_path=temp_storage,
            config_path=temp_config
        )
        
        assert orchestrator.config.confidence_threshold == 0.75
        assert orchestrator.config.mutation_rate == 0.12
        assert orchestrator.config.max_mutations_per_cycle == 8
        assert orchestrator.config.patterns_per_cycle == 25
    
    def test_orchestrator_explicit_config_overrides_yaml(self, temp_storage, temp_config):
        """Test that explicit config overrides YAML."""
        explicit_config = SelfImprovementConfig(
            confidence_threshold=0.99,
            mutation_rate=0.5
        )
        
        orchestrator = SelfImprovementOrchestrator(
            storage_path=temp_storage,
            config=explicit_config,
            config_path=temp_config
        )
        
        assert orchestrator.config.confidence_threshold == 0.99
        assert orchestrator.config.mutation_rate == 0.5
    
    def test_orchestrator_disable_yaml_config(self, temp_storage, temp_config):
        """Test disabling YAML config loading."""
        orchestrator = SelfImprovementOrchestrator(
            storage_path=temp_storage,
            config_path=temp_config,
            use_yaml_config=False
        )
        
        # Should use defaults
        assert orchestrator.config.confidence_threshold == 0.7
        assert orchestrator.config.mutation_rate == 0.1


class TestConfigDataclasses:
    """Tests for individual config dataclasses."""
    
    def test_confidence_config(self):
        """Test ConfidenceConfig dataclass."""
        config = ConfidenceConfig(
            default_threshold=0.9,
            low_confidence_threshold=0.4,
            failure_penalty=0.15
        )
        
        assert config.default_threshold == 0.9
        assert config.low_confidence_threshold == 0.4
        assert config.failure_penalty == 0.15
    
    def test_mutation_config(self):
        """Test MutationConfig dataclass."""
        config = MutationConfig(
            rate=0.25,
            max_per_cycle=15,
            auto_enabled=False
        )
        
        assert config.rate == 0.25
        assert config.max_per_cycle == 15
        assert config.auto_enabled is False
    
    def test_reinforcement_config(self):
        """Test ReinforcementConfig dataclass."""
        config = ReinforcementConfig(
            decay_rate=0.08,
            min_strength_threshold=0.15,
            strong_pattern_threshold=0.8
        )
        
        assert config.decay_rate == 0.08
        assert config.min_strength_threshold == 0.15
        assert config.strong_pattern_threshold == 0.8
    
    def test_cycle_config(self):
        """Test CycleConfig dataclass."""
        config = CycleConfig(
            patterns_per_cycle=100,
            cycles_per_day=5,
            schedule_morning=7,
            schedule_evening=23
        )
        
        assert config.patterns_per_cycle == 100
        assert config.cycles_per_day == 5
        assert config.schedule_morning == 7
        assert config.schedule_evening == 23
    
    def test_safety_config(self):
        """Test SafetyConfig dataclass."""
        config = SafetyConfig(
            max_daily_mutations=50,
            validate_mutations=False,
            protected_tags=['core', 'safety', 'system', 'critical']
        )
        
        assert config.max_daily_mutations == 50
        assert config.validate_mutations is False
        assert 'critical' in config.protected_tags


class TestGapClosureLoop:
    """Tests for SI-004: Gap Closure Loop."""
    
    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def mock_ltm(self, temp_storage):
        """Create a mock LTM for testing."""
        from rpa.memory.ltm import LongTermMemory
        ltm = LongTermMemory(temp_storage / "ltm")
        ltm.load()
        return ltm
    
    def test_gap_closure_loop_creation(self, mock_ltm, temp_storage):
        """Test creating a GapClosureLoop."""
        loop = GapClosureLoop(
            ltm=mock_ltm,
            storage_path=temp_storage / "gap_closure"
        )
        
        assert loop.ltm == mock_ltm
        assert loop.max_goals_per_cycle == 10
        assert loop.auto_execute is True
    
    def test_learning_goal_creation(self):
        """Test creating a LearningGoal."""
        goal = LearningGoal(
            goal_id="goal_001",
            source_gap_id="gap_001",
            description="Test goal",
            target_patterns=["pattern_1"],
            strategy=GapClosureStrategy.COMPOSE_EXISTING,
            priority=8
        )
        
        assert goal.goal_id == "goal_001"
        assert goal.status == LearningGoalStatus.PENDING
        assert goal.strategy == GapClosureStrategy.COMPOSE_EXISTING
        assert goal.priority == 8
    
    def test_learning_goal_to_dict(self):
        """Test LearningGoal serialization."""
        goal = LearningGoal(
            goal_id="goal_002",
            source_gap_id="gap_002",
            description="Serialize test",
            target_patterns=[],
            strategy=GapClosureStrategy.LEARN_FROM_SOURCE,
            priority=5
        )
        
        data = goal.to_dict()
        
        assert data["goal_id"] == "goal_002"
        assert data["strategy"] == "learn_from_source"
        assert data["status"] == "pending"
    
    def test_gap_closure_result_creation(self):
        """Test creating a GapClosureResult."""
        result = GapClosureResult(
            goal_id="goal_001",
            gap_id="gap_001",
            success=True,
            patterns_created=2,
            patterns_linked=1,
            message="Success",
            duration_seconds=0.5
        )
        
        assert result.success is True
        assert result.patterns_created == 2
        assert result.duration_seconds == 0.5
    
    def test_detect_and_plan(self, mock_ltm, temp_storage):
        """Test gap detection and planning."""
        loop = GapClosureLoop(
            ltm=mock_ltm,
            storage_path=temp_storage / "gap_closure",
            auto_execute=False
        )
        
        goals = loop.detect_and_plan()
        
        # Should return a list (may be empty if no gaps)
        assert isinstance(goals, list)
    
    def test_get_status(self, mock_ltm, temp_storage):
        """Test getting gap closure status."""
        loop = GapClosureLoop(
            ltm=mock_ltm,
            storage_path=temp_storage / "gap_closure"
        )
        
        status = loop.get_status()
        
        assert "total_gaps_detected" in status
        assert "total_goals_created" in status
        assert "total_goals_completed" in status
        assert "pending_goals" in status
    
    def test_get_pending_goals(self, mock_ltm, temp_storage):
        """Test getting pending goals."""
        loop = GapClosureLoop(
            ltm=mock_ltm,
            storage_path=temp_storage / "gap_closure"
        )
        
        pending = loop.get_pending_goals()
        
        assert isinstance(pending, list)
    
    def test_run_full_cycle(self, mock_ltm, temp_storage):
        """Test running a full gap closure cycle."""
        loop = GapClosureLoop(
            ltm=mock_ltm,
            storage_path=temp_storage / "gap_closure",
            auto_execute=False  # Don't auto-execute in tests
        )
        
        result = loop.run_full_cycle()
        
        assert "new_goals_created" in result
        assert "closure_attempts" in result
        assert "status" in result
    
    def test_strategy_selection(self, mock_ltm, temp_storage):
        """Test strategy selection for different gap types."""
        from rpa.inquiry.gap_detector import GapType, Gap
        
        loop = GapClosureLoop(
            ltm=mock_ltm,
            storage_path=temp_storage / "gap_closure"
        )
        
        # Test each gap type
        gap = Gap(
            gap_id="test_gap",
            gap_type=GapType.INCOMPLETE_COMPOSITION,
            severity="high",
            description="Test",
            affected_nodes=[]
        )
        
        strategy = loop._select_strategy(gap)
        assert strategy == GapClosureStrategy.COMPOSE_EXISTING
    
    def test_priority_calculation(self, mock_ltm, temp_storage):
        """Test priority calculation for gaps."""
        from rpa.inquiry.gap_detector import GapType, Gap
        
        loop = GapClosureLoop(
            ltm=mock_ltm,
            storage_path=temp_storage / "gap_closure"
        )
        
        # High severity gap
        high_gap = Gap(
            gap_id="high_gap",
            gap_type=GapType.UNRESOLVED_REFERENCE,
            severity="high",
            description="High priority",
            affected_nodes=[]
        )
        
        # Low severity gap
        low_gap = Gap(
            gap_id="low_gap",
            gap_type=GapType.CROSS_DOMAIN,
            severity="low",
            description="Low priority",
            affected_nodes=[]
        )
        
        high_priority = loop._calculate_priority(high_gap)
        low_priority = loop._calculate_priority(low_gap)
        
        assert high_priority > low_priority


class TestOrchestratorGapClosure:
    """Tests for orchestrator integration with gap closure."""
    
    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_orchestrator_has_gap_closure_loop(self, temp_storage):
        """Test that orchestrator has gap closure loop."""
        config = SelfImprovementConfig(patterns_per_cycle=5)
        orchestrator = SelfImprovementOrchestrator(
            storage_path=temp_storage,
            config=config
        )
        
        # Should have gap_closure_loop attribute
        assert hasattr(orchestrator, 'gap_closure_loop')
    
    def test_cycle_with_gap_closure(self, temp_storage):
        """Test improvement cycle with gap closure."""
        config = SelfImprovementConfig(
            patterns_per_cycle=5,
            enable_auto_mutation=False
        )
        orchestrator = SelfImprovementOrchestrator(
            storage_path=temp_storage,
            config=config
        )
        
        cycle = orchestrator.run_improvement_cycle()
        
        # Should have gaps_detected (may be 0)
        assert hasattr(cycle, 'gaps_detected')
        assert hasattr(cycle, 'gaps_closed')
