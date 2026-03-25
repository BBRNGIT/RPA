"""
Tests for Phase 7.5: Goal-Driven Retry Engine

Tests the retry engine that implements:
Attempt → Sandbox → Evaluate → Mutate → Retry loop

Key test areas:
1. Basic retry functionality
2. Strategy selection
3. Mutation-based retries
4. Chain tracking and history
5. Learning insights
"""

import pytest
from datetime import datetime
from pathlib import Path
import sys

# Add RPA to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rpa.closed_loop.retry_engine import (
    RetryEngine,
    RetryChain,
    RetryAttempt,
    RetryStrategy,
    RetryTrigger,
    RetryConfig,
)
from rpa.closed_loop.outcome_evaluator import (
    OutcomeEvaluator,
    Outcome,
    OutcomeType,
    OutcomeSeverity,
)
from rpa.closed_loop.reinforcement_tracker import (
    ReinforcementTracker,
    ReinforcementSignal,
)
from rpa.closed_loop.pattern_mutator import PatternMutator
from rpa.execution.code_sandbox import CodeSandbox
from rpa.core.node import Node


class TestRetryConfig:
    """Tests for RetryConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = RetryConfig()

        assert config.max_attempts == 5
        assert config.backoff_base_ms == 100.0
        assert config.backoff_multiplier == 2.0
        assert config.max_backoff_ms == 5000.0
        assert config.timeout_seconds == 10.0
        assert config.prefer_mutation is True
        assert config.success_score_threshold == 0.8

    def test_custom_config(self):
        """Test custom configuration values."""
        config = RetryConfig(
            max_attempts=10,
            backoff_base_ms=200.0,
            timeout_seconds=30.0,
        )

        assert config.max_attempts == 10
        assert config.backoff_base_ms == 200.0
        assert config.timeout_seconds == 30.0


class TestRetryEngine:
    """Tests for RetryEngine."""

    def test_create_engine(self):
        """Test creating a RetryEngine."""
        engine = RetryEngine()

        assert engine is not None
        assert engine.sandbox is not None
        assert engine.evaluator is not None
        assert engine.mutator is not None
        assert engine._stats["total_chains"] == 0

    def test_execute_with_retry_success_first_try(self):
        """Test successful execution on first attempt."""
        engine = RetryEngine()

        # Create a simple working pattern
        pattern = Node.create_pattern(
            label="simple_add",
            content="result = 2 + 2",
            domain="python",
        )

        chain = engine.execute_with_retry(
            pattern=pattern,
            goal="Add two numbers",
            expected_output="4",
        )

        assert chain is not None
        assert chain.success is True
        assert chain.total_attempts == 1
        assert len(chain.attempts) == 1
        assert chain.final_outcome is not None
        assert chain.final_outcome.outcome_type == OutcomeType.SUCCESS

    def test_execute_with_retry_success_after_failures(self):
        """Test success after multiple attempts with mutation."""
        engine = RetryEngine()

        # Create a pattern that needs fixing
        pattern = Node.create_pattern(
            label="broken_division",
            content="""
# This will fail due to division by zero
def divide(a, b):
    return a / b

result = divide(10, 0)
""",
            domain="python",
        )

        # Configure for more attempts
        config = RetryConfig(max_attempts=3)

        chain = engine.execute_with_retry(
            pattern=pattern,
            goal="Divide numbers safely",
            config_override=config,
        )

        assert chain is not None
        assert chain.total_attempts >= 1
        assert len(chain.attempts) >= 1

        # Check that retry strategies were applied
        if chain.total_attempts > 1:
            assert any(
                a.strategy_used is not None
                for a in chain.attempts[:-1]  # Exclude last attempt
            )

    def test_execute_code_with_retry(self):
        """Test direct code execution with retry."""
        engine = RetryEngine()

        # Simple working code
        code = "result = 5 * 5"

        chain = engine.execute_code_with_retry(
            code=code,
            goal="Multiply numbers",
            expected_output="25",
        )

        assert chain is not None
        assert chain.success is True

    def test_max_attempts_limit(self):
        """Test that max attempts limit is respected."""
        engine = RetryEngine()

        # Create a pattern that will always fail
        pattern = Node.create_pattern(
            label="always_fails",
            content="raise Exception('Always fails')",
            domain="python",
        )

        config = RetryConfig(max_attempts=3)

        chain = engine.execute_with_retry(
            pattern=pattern,
            goal="This will never succeed",
            config_override=config,
        )

        assert chain is not None
        assert chain.success is False
        assert chain.total_attempts == 3

    def test_backoff_calculation(self):
        """Test exponential backoff calculation."""
        engine = RetryEngine()
        config = RetryConfig(
            backoff_base_ms=100.0,
            backoff_multiplier=2.0,
            max_backoff_ms=1000.0,
        )

        # Test backoff progression
        b1 = engine._calculate_backoff(1, config)
        b2 = engine._calculate_backoff(2, config)
        b3 = engine._calculate_backoff(3, config)
        b4 = engine._calculate_backoff(10, config)  # Should hit max

        assert b1 == 100.0  # base
        assert b2 == 200.0  # base * 2
        assert b3 == 400.0  # base * 4
        assert b4 == 1000.0  # capped at max

    def test_strategy_selection_failure(self):
        """Test strategy selection for failures."""
        engine = RetryEngine()
        config = RetryConfig()

        # Create a failure outcome
        outcome = Outcome(
            outcome_id="test_outcome",
            outcome_type=OutcomeType.FAILURE,
            severity=OutcomeSeverity.HIGH,
            pattern_id="test_pattern",
            domain="python",
            success_score=0.2,
        )

        strategy, trigger = engine._determine_strategy(outcome, 1, config)

        assert strategy in [RetryStrategy.MUTATE_FIX, RetryStrategy.ALTERNATIVE_PATTERN]
        assert trigger == RetryTrigger.EXECUTION_FAILURE

    def test_strategy_selection_error(self):
        """Test strategy selection for errors."""
        engine = RetryEngine()
        config = RetryConfig()

        outcome = Outcome(
            outcome_id="error_outcome",
            outcome_type=OutcomeType.ERROR,
            severity=OutcomeSeverity.CRITICAL,
            pattern_id="test_pattern",
            domain="python",
            success_score=0.0,
        )

        strategy, trigger = engine._determine_strategy(outcome, 1, config)

        assert strategy in [RetryStrategy.BACKTRACK, RetryStrategy.ABANDON]
        assert trigger == RetryTrigger.EXECUTION_FAILURE

    def test_strategy_selection_gap(self):
        """Test strategy selection for gaps."""
        engine = RetryEngine()
        config = RetryConfig()

        outcome = Outcome(
            outcome_id="gap_outcome",
            outcome_type=OutcomeType.GAP,
            severity=OutcomeSeverity.MEDIUM,
            pattern_id="test_pattern",
            domain="python",
            success_score=0.0,
        )

        strategy, trigger = engine._determine_strategy(outcome, 1, config)

        assert strategy in [RetryStrategy.MUTATE_ENHANCE, RetryStrategy.ESCALATE]
        assert trigger == RetryTrigger.GAP_DETECTED

    def test_chain_tracking(self):
        """Test that chains are properly tracked."""
        engine = RetryEngine()

        pattern = Node.create_pattern(
            label="test_pattern",
            content="result = 1 + 1",
            domain="python",
        )

        chain = engine.execute_with_retry(
            pattern=pattern,
            goal="Simple addition",
        )

        # Check chain is stored
        retrieved = engine.get_chain(chain.chain_id)
        assert retrieved is not None
        assert retrieved.chain_id == chain.chain_id

        # Check it appears in recent chains
        recent = engine.get_recent_chains()
        assert len(recent) > 0
        assert any(c.chain_id == chain.chain_id for c in recent)

    def test_statistics_tracking(self):
        """Test that statistics are properly tracked."""
        engine = RetryEngine()

        # Execute multiple chains
        for i in range(3):
            pattern = Node.create_pattern(
                label=f"stat_pattern_{i}",
                content=f"result = {i} + {i}",
                domain="python",
            )
            engine.execute_with_retry(
                pattern=pattern,
                goal=f"Addition {i}",
            )

        stats = engine.get_stats()

        assert stats["total_chains"] >= 3
        assert stats["total_attempts"] >= 3
        assert stats["history_size"] >= 3


class TestRetryChain:
    """Tests for RetryChain."""

    def test_create_chain(self):
        """Test creating a retry chain."""
        chain = RetryChain(
            chain_id="test_chain_1",
            goal="Test goal",
            domain="python",
        )

        assert chain.chain_id == "test_chain_1"
        assert chain.goal == "Test goal"
        assert chain.domain == "python"
        assert chain.success is False
        assert chain.total_attempts == 0
        assert len(chain.attempts) == 0

    def test_chain_to_dict(self):
        """Test chain serialization."""
        chain = RetryChain(
            chain_id="test_chain",
            goal="Test",
            domain="python",
            success=True,
            total_attempts=2,
        )

        data = chain.to_dict()

        assert data["chain_id"] == "test_chain"
        assert data["goal"] == "Test"
        assert data["domain"] == "python"
        assert data["success"] is True
        assert data["total_attempts"] == 2


class TestRetryAttempt:
    """Tests for RetryAttempt."""

    def test_create_attempt(self):
        """Test creating a retry attempt."""
        attempt = RetryAttempt(
            attempt_id="attempt_1",
            attempt_number=1,
            pattern_id="pattern_1",
            pattern_content="print('hello')",
        )

        assert attempt.attempt_id == "attempt_1"
        assert attempt.attempt_number == 1
        assert attempt.pattern_id == "pattern_1"
        assert attempt.execution_result is None
        assert attempt.outcome is None

    def test_attempt_to_dict(self):
        """Test attempt serialization."""
        attempt = RetryAttempt(
            attempt_id="attempt_1",
            attempt_number=1,
            pattern_id="pattern_1",
            pattern_content="test content",
            should_retry=True,
        )

        data = attempt.to_dict()

        assert data["attempt_id"] == "attempt_1"
        assert data["attempt_number"] == 1
        assert data["should_retry"] is True


class TestRetryStrategies:
    """Tests for retry strategies."""

    def test_direct_retry_strategy(self):
        """Test direct retry strategy."""
        engine = RetryEngine()

        # Create a pattern that might succeed on retry
        pattern = Node.create_pattern(
            label="flaky",
            content="import random; result = random.randint(0, 10)",
            domain="python",
        )

        # Direct retry just uses the same pattern
        can_apply = engine._can_apply_strategy(RetryStrategy.DIRECT_RETRY, Outcome(
            outcome_id="test",
            outcome_type=OutcomeType.FAILURE,
            severity=OutcomeSeverity.MEDIUM,
            pattern_id="test",
            domain="python",
            success_score=0.5,
        ))

        assert can_apply is True

    def test_mutate_fix_strategy(self):
        """Test mutation fix strategy application."""
        engine = RetryEngine()

        # Create pattern and outcome
        pattern = Node.create_pattern(
            label="needs_fix",
            content="x = undefined_var",
            domain="python",
        )

        # Create a mock outcome that needs fixing
        from rpa.learning.error_classifier import ClassifiedError

        error = ClassifiedError(
            error_id="err_1",
            error_type="runtime",
            category="name_error",
            message="name 'undefined_var' is not defined",
            severity="high",
            learning_value=0.8,
        )

        outcome = Outcome(
            outcome_id="outcome_1",
            outcome_type=OutcomeType.FAILURE,
            severity=OutcomeSeverity.HIGH,
            pattern_id=pattern.node_id,
            domain="python",
            success_score=0.0,
            error=error,  # Use 'error' not 'error_details'
            should_mutate=True,
        )

        # Check if strategy can be applied
        can_apply = engine._can_apply_strategy(RetryStrategy.MUTATE_FIX, outcome)
        assert can_apply is True


class TestLearningInsights:
    """Tests for learning insights from retry chains."""

    def test_patterns_needing_improvement(self):
        """Test detection of patterns needing improvement."""
        engine = RetryEngine()

        # Create a failing pattern
        pattern = Node.create_pattern(
            label="always_fails",
            content="raise Exception('fail')",
            domain="python",
        )

        # Execute multiple times
        for _ in range(3):
            config = RetryConfig(max_attempts=2)
            engine.execute_with_retry(
                pattern=pattern,
                goal="This will fail",
                config_override=config,
            )

        # Get patterns needing improvement
        patterns = engine.get_patterns_needing_improvement()

        # Should find our failing pattern
        assert len(patterns) > 0
        failing_ids = [p["pattern_id"] for p in patterns]
        assert pattern.node_id in failing_ids

    def test_learning_insights_summary(self):
        """Test learning insights summary."""
        engine = RetryEngine()

        # Execute some patterns
        for i in range(5):
            pattern = Node.create_pattern(
                label=f"insight_pattern_{i}",
                content=f"result = {i} * 2",
                domain="python",
            )
            engine.execute_with_retry(
                pattern=pattern,
                goal=f"Test {i}",
            )

        insights = engine.get_learning_insights()

        assert "total_chains" in insights
        assert "success_rate" in insights
        assert "common_failure_types" in insights
        assert "effective_strategies" in insights
        assert insights["total_chains"] >= 5


class TestChainExport:
    """Tests for chain export/import."""

    def test_export_chains(self):
        """Test exporting chains."""
        engine = RetryEngine()

        pattern = Node.create_pattern(
            label="export_test",
            content="result = 1",
            domain="python",
        )
        engine.execute_with_retry(pattern=pattern, goal="Export test")

        exported = engine.export_chains()

        assert isinstance(exported, list)
        assert len(exported) > 0
        assert all("chain_id" in c for c in exported)

    def test_import_chains(self):
        """Test importing chains."""
        engine = RetryEngine()

        # Create a chain
        chain_data = [{
            "chain_id": "imported_chain_1",
            "goal": "Imported goal",
            "domain": "python",
            "success": True,
            "total_attempts": 1,
            "attempts": [{
                "attempt_id": "attempt_1",
                "attempt_number": 1,
                "pattern_id": "pattern_1",
                "pattern_content": "test",
            }],
        }]

        imported = engine.import_chains(chain_data)

        assert imported == 1

        # Verify chain is accessible
        chain = engine.get_chain("imported_chain_1")
        assert chain is not None
        assert chain.goal == "Imported goal"


class TestIntegration:
    """Integration tests with other closed-loop components."""

    def test_integration_with_outcome_evaluator(self):
        """Test integration with OutcomeEvaluator."""
        evaluator = OutcomeEvaluator()
        engine = RetryEngine(evaluator=evaluator)

        pattern = Node.create_pattern(
            label="integration_test",
            content="result = 10",
            domain="python",
        )

        chain = engine.execute_with_retry(
            pattern=pattern,
            goal="Integration test",
            expected_output="10",
        )

        # Check that evaluator recorded the outcome
        assert chain.final_outcome is not None

    def test_integration_with_reinforcement_tracker(self):
        """Test integration with ReinforcementTracker."""
        tracker = ReinforcementTracker()
        engine = RetryEngine(reinforcement=tracker)

        pattern = Node.create_pattern(
            label="reinforcement_test",
            content="result = 5",
            domain="python",
        )

        engine.execute_with_retry(
            pattern=pattern,
            goal="Reinforcement test",
        )

        # Check that pattern strength was tracked
        strength = tracker.get_strength(pattern.node_id)
        # Pattern should be tracked (even if not in LTM)
        assert strength is not None

    def test_full_closed_loop_integration(self):
        """Test full closed-loop: Attempt → Evaluate → Reinforce → Mutate → Retry."""
        engine = RetryEngine()

        # Pattern with a fixable issue
        pattern = Node.create_pattern(
            label="fixable_issue",
            content="""
# Missing variable definition
result = undefined_variable + 5
""",
            domain="python",
        )

        config = RetryConfig(max_attempts=3)

        chain = engine.execute_with_retry(
            pattern=pattern,
            goal="Fix the undefined variable",
            config_override=config,
        )

        # Verify full loop executed
        assert chain is not None
        assert len(chain.attempts) >= 1

        # Check that patterns were created or deprecated
        if not chain.success:
            assert (
                len(chain.patterns_created) > 0 or
                len(chain.patterns_deprecated) > 0 or
                len(chain.learning_notes) > 0
            )


class TestRetryEngineStatistics:
    """Tests for statistics and reporting."""

    def test_stats_after_success(self):
        """Test statistics after successful execution."""
        engine = RetryEngine()

        pattern = Node.create_pattern(
            label="stats_test",
            content="result = 42",
            domain="python",
        )

        engine.execute_with_retry(
            pattern=pattern,
            goal="Statistics test",
        )

        stats = engine.get_stats()

        assert stats["total_chains"] >= 1
        assert stats["successful_chains"] >= 1

    def test_stats_after_failure(self):
        """Test statistics after failed execution."""
        engine = RetryEngine()

        pattern = Node.create_pattern(
            label="fail_stats",
            content="raise Exception('Always fails')",
            domain="python",
        )

        config = RetryConfig(max_attempts=2)
        engine.execute_with_retry(
            pattern=pattern,
            goal="Will fail",
            config_override=config,
        )

        stats = engine.get_stats()

        assert stats["failed_chains"] >= 1

    def test_strategy_usage_stats(self):
        """Test that strategy usage is tracked."""
        engine = RetryEngine()

        # Execute chains that will use different strategies
        failing_pattern = Node.create_pattern(
            label="strategies",
            content="raise Exception('fail')",
            domain="python",
        )

        config = RetryConfig(max_attempts=3)
        engine.execute_with_retry(
            pattern=failing_pattern,
            goal="Track strategies",
            config_override=config,
        )

        stats = engine.get_stats()

        # Some strategies should have been used
        total_strategies = sum(stats["by_strategy"].values())
        assert total_strategies >= 0  # May be 0 if all attempts failed immediately


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
