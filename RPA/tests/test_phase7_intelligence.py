"""
Tests for Phase 7: Closed-Loop Intelligence Engine.

Tests the core components:
- OutcomeEvaluator
- ReinforcementTracker  
- PatternMutator
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add RPA to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rpa.core.graph import Node, PatternGraph, NodeType
from rpa.memory import LongTermMemory, ShortTermMemory
from rpa.intelligence.outcome_evaluator import (
    OutcomeEvaluator, Outcome, OutcomeType
)
from rpa.intelligence.reinforcement_tracker import (
    ReinforcementTracker, ReinforcementRecord
)
from rpa.intelligence.pattern_mutator import (
    PatternMutator, PatternVersion, MutationType
)


class TestOutcomeEvaluator:
    """Tests for OutcomeEvaluator."""

    def test_create_evaluator(self):
        """Test evaluator creation."""
        evaluator = OutcomeEvaluator()
        assert evaluator is not None
        stats = evaluator.get_stats()
        assert stats["total_evaluations"] == 0

    def test_evaluate_success_execution(self):
        """Test evaluation of successful execution."""
        evaluator = OutcomeEvaluator()

        # Create a test pattern
        pattern = Node.create_pattern(
            label="test_pattern",
            content="def add(a, b): return a + b",
            hierarchy_level=2,
            domain="python"
        )

        # Simulate successful execution
        result = evaluator.evaluate_execution(
            pattern=pattern,
            execution_result={
                "success": True,
                "output": "5",
                "error": None,
                "execution_time": 0.001
            },
            expected_output="5"
        )

        assert result.outcome_type == OutcomeType.SUCCESS
        assert result.success_score >= 0.8
        assert result.pattern_id == pattern.node_id

    def test_evaluate_failed_execution(self):
        """Test evaluation of failed execution."""
        evaluator = OutcomeEvaluator()

        pattern = Node.create_pattern(
            label="failing_pattern",
            content="def divide(a, b): return a / b",
            hierarchy_level=2,
            domain="python"
        )

        result = evaluator.evaluate_execution(
            pattern=pattern,
            execution_result={
                "success": False,
                "output": "",
                "error": "ZeroDivisionError: division by zero",
                "execution_time": 0.001
            }
        )

        assert result.outcome_type == OutcomeType.FAILURE
        assert result.success_score < 0.5
        assert result.error_details is not None
        assert result.error_details.category == "zero_division_error"
        assert result.should_mutate or result.learning_value > 0

    def test_evaluate_user_feedback(self):
        """Test evaluation from user feedback."""
        evaluator = OutcomeEvaluator()

        pattern = Node.create_pattern(
            label="user_rated_pattern",
            content="some code",
            hierarchy_level=1,
            domain="python"
        )

        # Positive feedback
        result = evaluator.evaluate_feedback(
            pattern=pattern,
            user_rating=0.9,
            user_comment="Works great!"
        )

        assert result.outcome_type == OutcomeType.SUCCESS
        assert result.success_score == 0.9
        assert result.source == "user_feedback"

        # Negative feedback
        result2 = evaluator.evaluate_feedback(
            pattern=pattern,
            user_rating=0.2,
            user_comment="Doesn't work",
            correction="fixed code here"
        )

        assert result2.outcome_type == OutcomeType.FAILURE
        assert result2.should_mutate == True

    def test_pattern_success_rate(self):
        """Test calculating pattern success rate."""
        evaluator = OutcomeEvaluator()

        pattern = Node.create_pattern(
            label="rated_pattern",
            content="code",
            hierarchy_level=1,
            domain="python"
        )

        # Add multiple outcomes
        for score in [1.0, 0.8, 0.6, 0.9, 0.3]:
            evaluator.evaluate_feedback(
                pattern=pattern,
                user_rating=score
            )

        rate = evaluator.get_pattern_success_rate(pattern.node_id)
        assert 0.5 <= rate <= 0.8

    def test_learning_candidates(self):
        """Test getting learning candidates."""
        evaluator = OutcomeEvaluator()

        pattern = Node.create_pattern(
            label="learning_pattern",
            content="code",
            hierarchy_level=1,
            domain="python"
        )

        # Create high learning value outcome
        evaluator.evaluate_execution(
            pattern=pattern,
            execution_result={
                "success": False,
                "output": "",
                "error": "TypeError: unsupported operand",
                "execution_time": 0.01
            }
        )

        candidates = evaluator.get_learning_candidates()
        assert pattern.node_id in candidates


class TestReinforcementTracker:
    """Tests for ReinforcementTracker."""

    def test_create_tracker(self):
        """Test tracker creation."""
        tracker = ReinforcementTracker()
        assert tracker is not None
        stats = tracker.get_stats()
        assert stats["total_reinforcements"] == 0

    def test_reinforce_on_success(self):
        """Test reinforcement on success."""
        tracker = ReinforcementTracker()

        record = tracker.reinforce(
            pattern_id="test_pattern",
            domain="python",
            success=True
        )

        assert record.strength > 1.0  # Should be reinforced
        assert record.success_count == 1
        assert record.usage_count == 1

    def test_penalty_on_failure(self):
        """Test penalty on failure."""
        tracker = ReinforcementTracker()

        # First reinforce
        record = tracker.reinforce(
            pattern_id="test_pattern",
            domain="python",
            success=True
        )
        initial_strength = record.strength

        # Then fail
        record = tracker.reinforce(
            pattern_id="test_pattern",
            domain="python",
            success=False
        )

        assert record.strength < initial_strength
        assert record.failure_count == 1

    def test_decay_application(self):
        """Test decay over time."""
        tracker = ReinforcementTracker()

        # Create record with old timestamp
        record = tracker.get_or_create("old_pattern", "python")
        record.last_used = datetime.now() - timedelta(hours=48)
        record.strength = 1.5

        # Apply decay
        result = tracker.apply_decay()

        assert result["decayed_count"] > 0
        assert record.strength < 1.5
        assert record.decay_events > 0

    def test_flagging(self):
        """Test flagging for review."""
        tracker = ReinforcementTracker()

        record = tracker.get_or_create("bad_pattern", "python")

        # Simulate multiple failures
        for _ in range(5):
            tracker.reinforce("bad_pattern", "python", success=False)

        # Check if flagged
        records = tracker.get_flagged_patterns()
        assert len(records) > 0

    def test_domain_tracking(self):
        """Test domain-based tracking."""
        tracker = ReinforcementTracker()

        # Create records in different domains
        tracker.reinforce("py_pattern", "python", success=True)
        tracker.reinforce("rs_pattern", "rust", success=True)
        tracker.reinforce("go_pattern", "go", success=True)

        domains = tracker.get_domains()
        assert "python" in domains
        assert "rust" in domains
        assert "go" in domains

    def test_strength_bounds(self):
        """Test strength stays within bounds."""
        tracker = ReinforcementTracker()

        # Over-reinforce
        for _ in range(20):
            tracker.reinforce("super_pattern", "python", success=True)

        record = tracker.get_record("super_pattern")
        assert record.strength <= tracker.MAX_STRENGTH

        # Over-penalize
        for _ in range(20):
            tracker.reinforce("fail_pattern", "python", success=False)

        record = tracker.get_record("fail_pattern")
        assert record.strength >= tracker.MIN_STRENGTH


class TestPatternMutator:
    """Tests for PatternMutator."""

    def test_create_mutator(self):
        """Test mutator creation."""
        mutator = PatternMutator()
        assert mutator is not None
        stats = mutator.get_stats()
        assert stats["total_mutations"] == 0

    def test_apply_fix(self):
        """Test applying a fix to a pattern."""
        mutator = PatternMutator()

        pattern = Node.create_pattern(
            label="buggy_pattern",
            content="def foo():\n  x = 1\n  return x",
            hierarchy_level=2,
            domain="python"
        )

        new_pattern = mutator.apply_fix(
            pattern=pattern,
            fix_description="Add null check for safety",
        )

        assert new_pattern is not None
        assert new_pattern.metadata.get("mutation_type") == "fix"
        assert "parent_pattern_id" in new_pattern.metadata

    def test_version_tracking(self):
        """Test version tracking."""
        mutator = PatternMutator()

        pattern = Node.create_pattern(
            label="versioned_pattern",
            content="original content",
            hierarchy_level=1,
            domain="python"
        )

        # Apply multiple fixes
        mutator.apply_fix(pattern, "Fix 1")
        mutator.apply_fix(pattern, "Fix 2")
        mutator.apply_fix(pattern, "Fix 3")

        history = mutator.get_pattern_history(pattern.node_id)
        assert len(history) == 3
        assert history[0].version_number == 1
        assert history[2].version_number == 3

    def test_generalization(self):
        """Test pattern generalization."""
        mutator = PatternMutator()

        pattern = Node.create_pattern(
            label="specific_pattern",
            content="def sort_int_list(items): ...",
            hierarchy_level=2,
            domain="python"
        )

        generalized = mutator.generalize_pattern(
            pattern=pattern,
            abstraction="Generic sorting algorithm for any comparable type"
        )

        assert generalized is not None
        assert generalized.hierarchy_level < pattern.hierarchy_level
        assert "abstraction" in generalized.metadata

    def test_deprecation(self):
        """Test pattern deprecation."""
        ltm = LongTermMemory()
        mutator = PatternMutator(ltm=ltm)

        pattern = Node.create_pattern(
            label="old_pattern",
            content="deprecated code",
            hierarchy_level=1,
            domain="python"
        )

        ltm.add_node(pattern)

        success = mutator.deprecate_pattern(
            pattern_id=pattern.node_id,
            reason="Replaced by better implementation"
        )

        # Check LTM state
        stored = ltm.get_pattern(pattern.node_id)
        assert stored is not None
        assert stored.is_valid == False

    def test_version_comparison(self):
        """Test comparing versions."""
        mutator = PatternMutator()

        pattern = Node.create_pattern(
            label="compare_pattern",
            content="v1 content",
            hierarchy_level=1,
            domain="python"
        )

        v1 = mutator.apply_fix(pattern, "First fix")
        v2 = mutator.apply_fix(pattern, "Second fix")

        history = mutator.get_pattern_history(pattern.node_id)
        comparison = mutator.compare_versions(
            history[0].version_id,
            history[1].version_id
        )

        assert comparison["version_diff"] == 1
        assert "v1_hash" in comparison
        assert "v2_hash" in comparison


class TestClosedLoop:
    """Tests for the complete closed-loop flow."""

    def test_full_learning_cycle(self):
        """Test full learning cycle: execute -> evaluate -> reinforce -> mutate."""
        # Setup
        evaluator = OutcomeEvaluator()
        tracker = ReinforcementTracker()
        mutator = PatternMutator()

        # Create pattern
        pattern = Node.create_pattern(
            label="cycle_pattern",
            content="def risky(): pass",
            hierarchy_level=2,
            domain="python"
        )

        # 1. Execute and fail
        outcome = evaluator.evaluate_execution(
            pattern=pattern,
            execution_result={
                "success": False,
                "output": "",
                "error": "NameError: name 'x' is not defined",
                "execution_time": 0.01
            }
        )

        assert outcome.outcome_type == OutcomeType.FAILURE

        # 2. Track reinforcement
        record = tracker.reinforce(
            pattern_id=pattern.node_id,
            domain=pattern.domain,
            success=False,
            outcome_id=outcome.outcome_id
        )

        assert record.failure_count == 1

        # 3. Mutate if needed
        if outcome.should_mutate:
            new_pattern = mutator.mutate_from_outcome(pattern, outcome)
            # Version should be tracked
            history = mutator.get_pattern_history(pattern.node_id)
            assert len(history) > 0

    def test_success_reinforcement_cycle(self):
        """Test cycle with successful outcome."""
        evaluator = OutcomeEvaluator()
        tracker = ReinforcementTracker()

        pattern = Node.create_pattern(
            label="good_pattern",
            content="def reliable(): return 42",
            hierarchy_level=1,
            domain="python"
        )

        # Multiple successful executions
        for _ in range(5):
            outcome = evaluator.evaluate_execution(
                pattern=pattern,
                execution_result={
                    "success": True,
                    "output": "42",
                    "error": None,
                    "execution_time": 0.001
                },
                expected_output="42"
            )

            tracker.reinforce(
                pattern_id=pattern.node_id,
                domain=pattern.domain,
                success=True,
                outcome_id=outcome.outcome_id
            )

        record = tracker.get_record(pattern.node_id)
        assert record.success_count == 5
        assert record.strength > 1.0  # Should be reinforced

        # Pattern should not be flagged
        assert not record.is_flagged


class TestMultiDomain:
    """Tests for multi-domain support."""

    def test_cross_domain_patterns(self):
        """Test patterns across different domains."""
        evaluator = OutcomeEvaluator()
        tracker = ReinforcementTracker()

        domains = ["python", "rust", "go", "english"]

        for domain in domains:
            pattern = Node.create_pattern(
                label=f"{domain}_pattern",
                content=f"content for {domain}",
                hierarchy_level=1,
                domain=domain
            )

            outcome = evaluator.evaluate_execution(
                pattern=pattern,
                execution_result={"success": True, "output": "ok", "error": None},
            )

            tracker.reinforce(
                pattern_id=pattern.node_id,
                domain=domain,
                success=True
            )

        # Check domain tracking
        assert set(tracker.get_domains()) == set(domains)

        # Check domain-specific records
        for domain in domains:
            records = tracker.get_records_by_domain(domain)
            assert len(records) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
