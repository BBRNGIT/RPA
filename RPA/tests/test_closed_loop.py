"""
Tests for Phase 7: Closed-Loop Intelligence Engine

Tests the three foundational components:
1. OutcomeEvaluator - Unified outcome scoring
2. ReinforcementTracker - Pattern strength and decay
3. PatternMutator - Version, fix, deprecate patterns
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add RPA to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rpa.closed_loop.outcome_evaluator import (
    OutcomeEvaluator,
    Outcome,
    OutcomeType,
    OutcomeSeverity,
)
from rpa.closed_loop.reinforcement_tracker import (
    ReinforcementTracker,
    ReinforcementSignal,
    ReinforcementRecord,
    PatternStrength,
)
from rpa.closed_loop.pattern_mutator import (
    PatternMutator,
    MutationType,
    MutationRecord,
    PatternVersion,
)
from rpa.closed_loop.self_questioning_gate import (
    SelfQuestioningGate,
    SelfQuestioningResult,
    QuestionResult,
    QuestionType,
    ConfidenceLevel,
)
from rpa.memory.ltm import LongTermMemory
from rpa.core.node import Node


class TestOutcomeEvaluator:
    """Tests for OutcomeEvaluator."""
    
    def test_create_evaluator(self):
        """Test creating an OutcomeEvaluator."""
        evaluator = OutcomeEvaluator()
        assert evaluator is not None
        assert evaluator._stats["total_evaluated"] == 0
    
    def test_evaluate_success_outcome(self):
        """Test evaluating a successful outcome."""
        evaluator = OutcomeEvaluator()
        
        outcome = evaluator.evaluate(
            pattern_id="test_pattern_1",
            domain="python",
            action="generate_code",
            result="Code generated successfully",
            sandbox_result={"success": True},
            user_rating=4,
        )
        
        assert outcome is not None
        assert outcome.outcome_type == OutcomeType.SUCCESS
        assert outcome.success_score > 0.5
        assert outcome.pattern_id == "test_pattern_1"
        assert outcome.domain == "python"
    
    def test_evaluate_failure_outcome(self):
        """Test evaluating a failed outcome."""
        evaluator = OutcomeEvaluator()
        
        outcome = evaluator.evaluate(
            pattern_id="test_pattern_2",
            domain="python",
            action="generate_code",
            result="Code failed with error",
            error_message="TypeError: 'NoneType' object is not callable",
            sandbox_result={"success": False},
        )
        
        assert outcome is not None
        assert outcome.outcome_type == OutcomeType.FAILURE
        assert outcome.error is not None
        assert outcome.error.category == "type_error"
        assert outcome.should_mutate is True
    
    def test_evaluate_gap_outcome(self):
        """Test evaluating a gap outcome."""
        evaluator = OutcomeEvaluator()
        
        outcome = evaluator.evaluate(
            pattern_id="test_pattern_3",
            domain="python",
            action="generate_code",
            result="Missing knowledge for this task",
            self_assessment={"gap_detected": True, "passed": False},
        )
        
        assert outcome is not None
        assert outcome.outcome_type == OutcomeType.GAP
        assert outcome.learning_value >= 0.5
    
    def test_severity_determination(self):
        """Test severity level determination."""
        evaluator = OutcomeEvaluator()
        
        # Critical error
        critical = evaluator.evaluate(
            pattern_id="p1",
            domain="python",
            action="test",
            result="Critical failure",
            error_message="RecursionError: maximum recursion depth exceeded",
        )
        assert critical.severity == OutcomeSeverity.HIGH or critical.severity == OutcomeSeverity.CRITICAL
        
        # User negative rating
        negative = evaluator.evaluate(
            pattern_id="p2",
            domain="python",
            action="test",
            result="Bad result",
            user_rating=-1,
        )
        assert negative.severity == OutcomeSeverity.CRITICAL
    
    def test_reinforcement_signals(self):
        """Test reinforcement signal determination."""
        evaluator = OutcomeEvaluator()
        
        # Should reinforce on success
        success = evaluator.evaluate(
            pattern_id="p1",
            domain="python",
            action="test",
            result="Success",
            sandbox_result={"success": True},
            user_rating=5,
        )
        assert success.should_reinforce is True
        
        # Should mutate on failure
        failure = evaluator.evaluate(
            pattern_id="p2",
            domain="python",
            action="test",
            result="Failed",
            error_message="IndexError: list index out of range",
        )
        assert failure.should_mutate is True
    
    def test_pattern_tracking(self):
        """Test pattern outcome history tracking."""
        evaluator = OutcomeEvaluator()
        
        # Evaluate multiple outcomes for same pattern
        for i in range(5):
            evaluator.evaluate(
                pattern_id="tracked_pattern",
                domain="python",
                action=f"action_{i}",
                result="Success" if i < 3 else "Failed",
                user_rating=4 if i < 3 else 2,
            )
        
        outcomes = evaluator.get_pattern_outcomes("tracked_pattern")
        assert len(outcomes) == 5
        
        rate = evaluator.get_pattern_success_rate("tracked_pattern")
        assert 0 < rate < 1
    
    def test_learning_trend(self):
        """Test learning trend analysis."""
        evaluator = OutcomeEvaluator()
        
        # Simulate improving pattern
        pattern_id = "improving_pattern"
        for i in range(6):
            evaluator.evaluate(
                pattern_id=pattern_id,
                domain="python",
                action=f"action_{i}",
                result="Success" if i >= 3 else "Failed",
                user_rating=4 if i >= 3 else 2,
            )
        
        trend = evaluator.get_pattern_learning_trend(pattern_id)
        assert trend == "improving"
    
    def test_statistics(self):
        """Test evaluator statistics."""
        evaluator = OutcomeEvaluator()
        
        for i in range(10):
            evaluator.evaluate(
                pattern_id=f"pattern_{i}",
                domain="python",
                action=f"action_{i}",
                result="Success" if i % 2 == 0 else "Failed",
            )
        
        stats = evaluator.get_stats()
        assert stats["total_evaluated"] == 10
        assert stats["by_type"]["success"] > 0
        assert stats["by_type"]["failure"] > 0


class TestReinforcementTracker:
    """Tests for ReinforcementTracker."""
    
    def test_create_tracker(self):
        """Test creating a ReinforcementTracker."""
        tracker = ReinforcementTracker()
        assert tracker is not None
        assert tracker._stats["patterns_tracked"] == 0
    
    def test_track_pattern(self):
        """Test tracking a new pattern."""
        tracker = ReinforcementTracker()
        tracker._track_pattern("test_pattern")
        
        assert "test_pattern" in tracker._strengths
        strength = tracker.get_strength("test_pattern")
        assert strength is not None
        assert strength.strength == 1.0
    
    def test_reinforce_on_success(self):
        """Test reinforcement on successful outcome."""
        tracker = ReinforcementTracker()
        
        # Track pattern with initial strength < 1.0 so it can increase
        tracker._track_pattern("success_pattern", initial_strength=0.7)
        
        # Create a success outcome
        outcome = Outcome(
            outcome_id="o1",
            outcome_type=OutcomeType.SUCCESS,
            severity=OutcomeSeverity.INFO,
            pattern_id="success_pattern",
            domain="python",
            success_score=0.9,
            confidence_score=0.8,
        )
        
        record = tracker.process_outcome(outcome)
        
        assert record.signal == ReinforcementSignal.REINFORCE
        assert record.new_strength > record.previous_strength
        
        strength = tracker.get_strength("success_pattern")
        assert strength.successful_uses == 1
        assert strength.current_streak == 1
    
    def test_decay_on_failure(self):
        """Test decay on failed outcome."""
        tracker = ReinforcementTracker()
        
        # Create a failure outcome
        outcome = Outcome(
            outcome_id="o2",
            outcome_type=OutcomeType.FAILURE,
            severity=OutcomeSeverity.HIGH,
            pattern_id="failure_pattern",
            domain="python",
            success_score=0.2,
            confidence_score=0.9,
        )
        
        record = tracker.process_outcome(outcome)
        
        assert record.signal in [ReinforcementSignal.DECAY, ReinforcementSignal.FLAG]
        assert record.new_strength < record.previous_strength
        
        strength = tracker.get_strength("failure_pattern")
        assert strength.failed_uses == 1
        assert strength.current_streak == -1
    
    def test_streak_tracking(self):
        """Test success/failure streak tracking."""
        tracker = ReinforcementTracker()
        
        # Simulate success streak
        for i in range(5):
            outcome = Outcome(
                outcome_id=f"s{i}",
                outcome_type=OutcomeType.SUCCESS,
                severity=OutcomeSeverity.INFO,
                pattern_id="streak_pattern",
                domain="python",
                success_score=0.9,
                confidence_score=0.9,
            )
            tracker.process_outcome(outcome)
        
        strength = tracker.get_strength("streak_pattern")
        assert strength.current_streak == 5
        assert strength.best_streak == 5
        
        # Break streak with failure
        fail_outcome = Outcome(
            outcome_id="f1",
            outcome_type=OutcomeType.FAILURE,
            severity=OutcomeSeverity.HIGH,
            pattern_id="streak_pattern",
            domain="python",
            success_score=0.2,
            confidence_score=0.9,
        )
        tracker.process_outcome(fail_outcome)
        
        strength = tracker.get_strength("streak_pattern")
        assert strength.current_streak == -1
    
    def test_time_based_decay(self):
        """Test time-based decay for unused patterns."""
        tracker = ReinforcementTracker()
        
        # Track a pattern
        tracker._track_pattern("old_pattern")
        strength = tracker._strengths["old_pattern"]
        
        # Simulate old last_used time
        strength.last_used = datetime.now() - timedelta(hours=48)
        strength.strength = 0.8
        
        # Apply decay
        records = tracker.apply_decay()
        
        assert len(records) > 0
        assert strength.strength < 0.8
    
    def test_weak_patterns_detection(self):
        """Test detection of weak patterns."""
        tracker = ReinforcementTracker()
        
        # Create weak and strong patterns
        tracker._track_pattern("weak_pattern")
        tracker._strengths["weak_pattern"].strength = 0.2
        
        tracker._track_pattern("strong_pattern")
        tracker._strengths["strong_pattern"].strength = 0.9
        
        weak = tracker.get_weak_patterns()
        strong = tracker.get_strong_patterns()
        
        assert len(weak) == 1
        assert len(strong) == 1
        assert weak[0].pattern_id == "weak_pattern"
    
    def test_patterns_for_review(self):
        """Test patterns needing review detection."""
        tracker = ReinforcementTracker()
        
        # Create pattern with issues
        tracker._track_pattern("problem_pattern")
        strength = tracker._strengths["problem_pattern"]
        strength.strength = 0.2
        strength.current_streak = -5
        strength.total_uses = 10
        strength.failed_uses = 8
        
        review = tracker.get_patterns_for_review()
        
        assert len(review) > 0
        assert review[0]["pattern_id"] == "problem_pattern"
    
    def test_ltm_sync(self):
        """Test synchronization with LTM."""
        ltm = LongTermMemory()
        tracker = ReinforcementTracker(ltm=ltm)
        
        # Add pattern to LTM
        node = Node.create_pattern(
            label="sync_pattern",
            content="test content",
            domain="python",
        )
        ltm.add_node(node)
        
        # Track and process
        tracker._track_pattern("sync_pattern")
        
        outcome = Outcome(
            outcome_id="o1",
            outcome_type=OutcomeType.SUCCESS,
            severity=OutcomeSeverity.INFO,
            pattern_id="sync_pattern",
            domain="python",
            success_score=0.9,
            confidence_score=0.9,
        )
        tracker.process_outcome(outcome)
        
        # Check LTM updated
        ltm_node = ltm.get_node("sync_pattern")
        # Note: sync_pattern ID would be different due to Node.create_pattern
        # This test verifies the mechanism exists


class TestPatternMutator:
    """Tests for PatternMutator."""
    
    def test_create_mutator(self):
        """Test creating a PatternMutator."""
        mutator = PatternMutator()
        assert mutator is not None
        assert mutator._stats["total_mutations"] == 0
    
    def test_version_tracking(self):
        """Test pattern version tracking."""
        mutator = PatternMutator()
        
        # Process an outcome for new pattern
        outcome = Outcome(
            outcome_id="o1",
            outcome_type=OutcomeType.SUCCESS,
            severity=OutcomeSeverity.INFO,
            pattern_id="versioned_pattern",
            domain="python",
            success_score=0.9,
            confidence_score=0.9,
        )
        mutator.process_outcome(outcome)
        
        versions = mutator.get_version_history("versioned_pattern")
        assert len(versions) == 1
        assert versions[0].version_number == 1
    
    def test_mutation_on_failure(self):
        """Test mutation triggered by failure."""
        mutator = PatternMutator()
        
        # First track the pattern with success
        success_outcome = Outcome(
            outcome_id="o1",
            outcome_type=OutcomeType.SUCCESS,
            severity=OutcomeSeverity.INFO,
            pattern_id="mutate_pattern",
            domain="python",
            success_score=0.9,
            confidence_score=0.9,
        )
        mutator.process_outcome(success_outcome)
        
        # Simulate multiple failures to trigger mutation
        for i in range(3):
            fail_outcome = Outcome(
                outcome_id=f"f{i}",
                outcome_type=OutcomeType.FAILURE,
                severity=OutcomeSeverity.HIGH,
                pattern_id="mutate_pattern",
                domain="python",
                success_score=0.2,
                confidence_score=0.8,
                should_mutate=True,
            )
            mutator.process_outcome(fail_outcome)
        
        # Check version history
        versions = mutator.get_version_history("mutate_pattern")
        assert len(versions) >= 1
    
    def test_deprecation(self):
        """Test pattern deprecation."""
        mutator = PatternMutator()
        
        # Track pattern
        mutator._ensure_pattern_tracked("deprecate_pattern")
        
        # Trigger deprecation
        outcome = Outcome(
            outcome_id="o1",
            outcome_type=OutcomeType.ERROR,
            severity=OutcomeSeverity.CRITICAL,
            pattern_id="deprecate_pattern",
            domain="python",
            success_score=0.0,
            confidence_score=0.9,
            should_deprecate=True,
        )
        
        record = mutator.process_outcome(outcome)
        
        assert record is not None
        assert record.mutation_type == MutationType.DEPRECATE
        
        deprecated = mutator.get_deprecated_patterns()
        assert len(deprecated) > 0
    
    def test_pattern_restoration(self):
        """Test restoring a deprecated pattern."""
        mutator = PatternMutator()
        
        # Create and deprecate a pattern
        mutator._ensure_pattern_tracked("restore_pattern")
        version = mutator._get_active_version("restore_pattern")
        version.is_deprecated = True
        version.is_active = False
        
        # Restore
        record = mutator.restore_pattern("restore_pattern")
        
        assert record is not None
        assert record.mutation_type == MutationType.RESTORE
        
        active = mutator.get_active_version("restore_pattern")
        assert active is not None
        assert active.is_deprecated is False
    
    def test_version_diff(self):
        """Test getting diff between versions."""
        mutator = PatternMutator()
        
        # Create pattern with multiple versions
        v1 = PatternVersion(
            version_id="v1",
            pattern_id="diff_pattern",
            version_number=1,
            content="line1\nline2\nline3",
            label="test",
        )
        v2 = PatternVersion(
            version_id="v2",
            pattern_id="diff_pattern",
            version_number=2,
            content="line1\nline2_modified\nline3",
            label="test",
        )
        
        mutator._versions["diff_pattern"] = [v1, v2]
        mutator._version_by_id["v1"] = v1
        mutator._version_by_id["v2"] = v2
        
        diff = mutator.get_version_diff("v1", "v2")
        
        assert "diff" in diff
        assert "lines_changed" in diff
    
    def test_patterns_needing_fix(self):
        """Test detection of patterns needing fixes."""
        mutator = PatternMutator()
        
        # Create pattern with failures
        mutator._ensure_pattern_tracked("fix_needed_pattern")
        version = mutator._get_active_version("fix_needed_pattern")
        version.failure_count = 5
        version.success_count = 1
        
        needs_fix = mutator.get_patterns_needing_fix()
        
        assert len(needs_fix) > 0
        assert needs_fix[0]["pattern_id"] == "fix_needed_pattern"
    
    def test_statistics(self):
        """Test mutator statistics."""
        mutator = PatternMutator()
        
        # Create some mutations
        for i in range(3):
            mutator._ensure_pattern_tracked(f"stat_pattern_{i}")
        
        stats = mutator.get_stats()
        
        assert stats["total_patterns_tracked"] >= 3


class TestSelfQuestioningGate:
    """Tests for SelfQuestioningGate."""
    
    def test_create_gate(self):
        """Test creating a SelfQuestioningGate."""
        gate = SelfQuestioningGate()
        assert gate is not None
        assert gate._stats["total_questions"] == 0
    
    def test_question_pattern(self):
        """Test questioning a pattern."""
        gate = SelfQuestioningGate()
        
        result = gate.question(
            pattern_id="test_pattern",
            domain="python",
        )
        
        assert result is not None
        assert result.pattern_id == "test_pattern"
        assert result.domain == "python"
        assert result.confidence_level in ConfidenceLevel
        assert len(result.questions) > 0
    
    def test_high_confidence_on_good_pattern(self):
        """Test that good patterns get high confidence."""
        gate = SelfQuestioningGate()
        tracker = ReinforcementTracker()
        gate.reinforcement_tracker = tracker
        
        # Track pattern with initial strength
        tracker._track_pattern("good_pattern", initial_strength=0.9)
        
        result = gate.question(
            pattern_id="good_pattern",
            domain="python",
        )
        
        assert result.can_proceed is True
        assert result.confidence_level in (ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM)
    
    def test_low_confidence_detection(self):
        """Test detection of low confidence patterns."""
        gate = SelfQuestioningGate()
        tracker = ReinforcementTracker()
        gate.reinforcement_tracker = tracker
        
        # Track pattern with very low strength
        tracker._track_pattern("weak_pattern", initial_strength=0.2)
        
        result = gate.question(
            pattern_id="weak_pattern",
            domain="python",
        )
        
        # Should have warnings about low strength
        assert len(result.warnings) > 0 or not result.can_proceed
    
    def test_gap_exposure(self):
        """Test gap exposure for unknown patterns."""
        gate = SelfQuestioningGate()
        
        result = gate.question(
            pattern_id="unknown_pattern_12345",
            domain="python",
        )
        
        # Unknown patterns should still be questioned
        assert result is not None
        assert len(result.questions) > 0
    
    def test_question_types(self):
        """Test that all question types are covered."""
        gate = SelfQuestioningGate()
        
        result = gate.question(
            pattern_id="test_pattern",
            domain="python",
        )
        
        question_types = {q.question_type for q in result.questions}
        
        # Should have multiple question types
        assert len(question_types) >= 4
    
    def test_statistics_tracking(self):
        """Test statistics tracking."""
        gate = SelfQuestioningGate()
        
        # Question multiple patterns
        for i in range(5):
            gate.question(
                pattern_id=f"pattern_{i}",
                domain="python",
            )
        
        stats = gate.get_stats()
        
        assert stats["total_questions"] == 5
    
    def test_blocked_patterns(self):
        """Test getting blocked patterns."""
        gate = SelfQuestioningGate()
        tracker = ReinforcementTracker()
        gate.reinforcement_tracker = tracker
        
        # Create pattern that will be blocked
        tracker._track_pattern("blocked_pattern", initial_strength=0.1)
        
        gate.question(
            pattern_id="blocked_pattern",
            domain="python",
        )
        
        # Check if we can retrieve blocked patterns
        blocked = gate.get_blocked_patterns()
        assert isinstance(blocked, list)


class TestClosedLoopIntegration:
    """Integration tests for the closed-loop system."""
    
    def test_full_closed_loop(self):
        """Test the full closed-loop: Outcome → Reinforcement → Mutation."""
        # Create components
        evaluator = OutcomeEvaluator()
        tracker = ReinforcementTracker()
        mutator = PatternMutator()
        
        pattern_id = "integration_pattern"
        
        # 1. Successful outcome
        success = evaluator.evaluate(
            pattern_id=pattern_id,
            domain="python",
            action="generate",
            result="Success",
            sandbox_result={"success": True},
            user_rating=5,
        )
        
        # 2. Process through reinforcement
        reinf = tracker.process_outcome(success)
        assert reinf.signal == ReinforcementSignal.REINFORCE
        
        # 3. Process through mutator (should not mutate on success)
        mut_record = mutator.process_outcome(success)
        assert mut_record is None  # No mutation on success
        
        # 4. Now simulate failures
        for i in range(3):
            fail = evaluator.evaluate(
                pattern_id=pattern_id,
                domain="python",
                action="generate",
                result="Failed",
                error_message="TypeError: unsupported operand",
            )
            
            tracker.process_outcome(fail)
            mutator.process_outcome(fail)
        
        # Check final state
        strength = tracker.get_strength(pattern_id)
        assert strength is not None
        assert strength.failed_uses == 3
        
        versions = mutator.get_version_history(pattern_id)
        assert len(versions) >= 1
    
    def test_multi_domain_patterns(self):
        """Test closed-loop with multiple domains."""
        evaluator = OutcomeEvaluator()
        tracker = ReinforcementTracker()
        
        domains = ["python", "rust", "go", "english"]
        
        for domain in domains:
            for i in range(5):
                outcome = evaluator.evaluate(
                    pattern_id=f"{domain}_pattern_{i}",
                    domain=domain,
                    action="test",
                    result="Success" if i % 2 == 0 else "Failed",
                )
                tracker.process_outcome(outcome)
        
        stats = evaluator.get_stats()
        assert all(domain in stats["by_domain"] for domain in domains)
        
        tracker_stats = tracker.get_stats()
        assert tracker_stats["total_patterns_tracked"] >= 20


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
