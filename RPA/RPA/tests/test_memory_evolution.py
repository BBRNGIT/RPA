"""
Tests for Phase 7.6: Memory Evolution

Tests the pattern evolution tracking system:
- Origin tracking
- Version history
- Failure and fix records
- Usage snapshots and trends
- Lineage tracking
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add RPA to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rpa.closed_loop.memory_evolution import (
    MemoryEvolution,
    PatternOrigin,
    VersionRecord,
    FailureRecord,
    UsageSnapshot,
    PatternLineage,
    EvolutionEvent,
    OriginType,
)


class TestPatternOrigin:
    """Tests for PatternOrigin."""

    def test_create_origin(self):
        """Test creating a pattern origin."""
        origin = PatternOrigin(
            pattern_id="test_pattern",
            origin_type=OriginType.LEARNED,
            source="mbpp_dataset",
        )

        assert origin.pattern_id == "test_pattern"
        assert origin.origin_type == OriginType.LEARNED
        assert origin.source == "mbpp_dataset"
        assert origin.created_at is not None

    def test_origin_to_dict(self):
        """Test origin serialization."""
        origin = PatternOrigin(
            pattern_id="test_pattern",
            origin_type=OriginType.MUTATED,
            parent_pattern_id="parent_123",
            derivation_method="fix",
        )

        data = origin.to_dict()

        assert data["pattern_id"] == "test_pattern"
        assert data["origin_type"] == "mutated"
        assert data["parent_pattern_id"] == "parent_123"
        assert data["derivation_method"] == "fix"

    def test_origin_from_dict(self):
        """Test origin deserialization."""
        data = {
            "pattern_id": "test_pattern",
            "origin_type": "learned",
            "source": "test_source",
            "created_at": datetime.now().isoformat(),
            "dataset": "mbpp",
            "sample_id": "sample_001",
        }

        origin = PatternOrigin.from_dict(data)

        assert origin.pattern_id == "test_pattern"
        assert origin.origin_type == OriginType.LEARNED
        assert origin.source == "test_source"
        assert origin.dataset == "mbpp"


class TestVersionRecord:
    """Tests for VersionRecord."""

    def test_create_version(self):
        """Test creating a version record."""
        version = VersionRecord(
            version_id="ver_001",
            pattern_id="test_pattern",
            version_number=1,
            event_type=EvolutionEvent.CREATED,
            content="print('hello')",
            label="hello_world",
        )

        assert version.version_id == "ver_001"
        assert version.version_number == 1
        assert version.event_type == EvolutionEvent.CREATED
        assert version.is_active is True

    def test_version_to_dict(self):
        """Test version serialization."""
        version = VersionRecord(
            version_id="ver_002",
            pattern_id="test_pattern",
            version_number=2,
            event_type=EvolutionEvent.FIXED,
            content="print('hello world')",
            change_summary="Added world",
        )

        data = version.to_dict()

        assert data["version_id"] == "ver_002"
        assert data["event_type"] == "fixed"
        assert data["change_summary"] == "Added world"


class TestFailureRecord:
    """Tests for FailureRecord."""

    def test_create_failure(self):
        """Test creating a failure record."""
        failure = FailureRecord(
            failure_id="fail_001",
            pattern_id="test_pattern",
            version_id="ver_001",
            error_type="TypeError",
            error_message="unsupported operand",
            error_category="runtime",
        )

        assert failure.failure_id == "fail_001"
        assert failure.error_type == "TypeError"
        assert failure.was_fixed is False

    def test_failure_fix(self):
        """Test marking a failure as fixed."""
        failure = FailureRecord(
            failure_id="fail_001",
            pattern_id="test_pattern",
            version_id="ver_001",
            error_type="TypeError",
            error_message="error",
        )

        failure.was_fixed = True
        failure.fix_version_id = "ver_002"
        failure.fix_description = "Added type check"

        assert failure.was_fixed is True
        assert failure.fix_version_id == "ver_002"


class TestUsageSnapshot:
    """Tests for UsageSnapshot."""

    def test_create_snapshot(self):
        """Test creating a usage snapshot."""
        snapshot = UsageSnapshot(
            snapshot_id="snap_001",
            pattern_id="test_pattern",
            total_uses=100,
            successful_uses=80,
            failed_uses=20,
            strength=0.85,
        )

        assert snapshot.snapshot_id == "snap_001"
        assert snapshot.total_uses == 100
        assert snapshot.success_rate == 0.8

    def test_snapshot_serialization(self):
        """Test snapshot serialization."""
        snapshot = UsageSnapshot(
            snapshot_id="snap_001",
            pattern_id="test_pattern",
            total_uses=50,
            successful_uses=40,
            failed_uses=10,
            strength=0.9,
            current_streak=5,
        )

        data = snapshot.to_dict()

        assert data["total_uses"] == 50
        assert data["success_rate"] == 0.8
        assert data["current_streak"] == 5


class TestPatternLineage:
    """Tests for PatternLineage."""

    def test_create_lineage(self):
        """Test creating a lineage."""
        lineage = PatternLineage(
            pattern_id="child_pattern",
            ancestors=["parent_pattern", "grandparent_pattern"],
            ancestor_depth=2,
            descendants=["grandchild_1", "grandchild_2"],
        )

        assert lineage.pattern_id == "child_pattern"
        assert len(lineage.ancestors) == 2
        assert len(lineage.descendants) == 2

    def test_lineage_serialization(self):
        """Test lineage serialization."""
        lineage = PatternLineage(
            pattern_id="test_pattern",
            ancestors=["parent_1"],
            descendants=["child_1", "child_2"],
            siblings=["sibling_1"],
        )

        data = lineage.to_dict()

        assert data["pattern_id"] == "test_pattern"
        assert data["ancestors"] == ["parent_1"]
        assert data["siblings"] == ["sibling_1"]


class TestMemoryEvolution:
    """Tests for MemoryEvolution."""

    def test_create_evolution(self):
        """Test creating MemoryEvolution."""
        evolution = MemoryEvolution()

        assert evolution is not None
        assert evolution._stats["total_patterns_tracked"] == 0

    def test_record_origin(self):
        """Test recording pattern origin."""
        evolution = MemoryEvolution()

        origin = evolution.record_origin(
            pattern_id="pattern_001",
            origin_type=OriginType.LEARNED,
            source="mbpp_dataset",
            dataset="mbpp",
            sample_id="mbpp_001",
        )

        assert origin is not None
        assert origin.pattern_id == "pattern_001"
        assert origin.origin_type == OriginType.LEARNED

        # Verify it was stored
        retrieved = evolution.get_origin("pattern_001")
        assert retrieved is not None
        assert retrieved.pattern_id == "pattern_001"

    def test_record_version(self):
        """Test recording pattern versions."""
        evolution = MemoryEvolution()

        # Record first version
        v1 = evolution.record_version(
            pattern_id="pattern_001",
            event_type=EvolutionEvent.CREATED,
            content="def add(a, b): return a + b",
            label="add_function",
        )

        assert v1.version_number == 1
        assert v1.event_type == EvolutionEvent.CREATED

        # Record second version
        v2 = evolution.record_version(
            pattern_id="pattern_001",
            event_type=EvolutionEvent.FIXED,
            content="def add(a, b): return a + b  # Fixed",
            label="add_function",
            change_summary="Added comment",
        )

        assert v2.version_number == 2
        assert v2.previous_version_id == v1.version_id

        # Get all versions
        versions = evolution.get_versions("pattern_001")
        assert len(versions) == 2

    def test_record_failure(self):
        """Test recording pattern failures."""
        evolution = MemoryEvolution()

        # Setup version first
        evolution.record_version(
            pattern_id="pattern_001",
            event_type=EvolutionEvent.CREATED,
            content="test content",
        )
        version = evolution.get_current_version("pattern_001")

        # Record failure
        failure = evolution.record_failure(
            pattern_id="pattern_001",
            version_id=version.version_id,
            error_type="TypeError",
            error_message="unsupported operand",
            error_category="runtime",
        )

        assert failure is not None
        assert failure.error_type == "TypeError"
        assert failure.was_fixed is False

        # Get failures
        failures = evolution.get_failures("pattern_001")
        assert len(failures) == 1

    def test_record_fix(self):
        """Test recording a fix for a failure."""
        evolution = MemoryEvolution()

        # Setup
        evolution.record_version(
            pattern_id="pattern_001",
            event_type=EvolutionEvent.CREATED,
            content="test",
        )
        version = evolution.get_current_version("pattern_001")

        failure = evolution.record_failure(
            pattern_id="pattern_001",
            version_id=version.version_id,
            error_type="TypeError",
            error_message="error",
        )

        # Record fix
        result = evolution.record_fix(
            failure_id=failure.failure_id,
            fix_version_id="ver_new",
            fix_description="Added type check",
        )

        assert result is True

        # Verify failure is marked as fixed
        failures = evolution.get_failures("pattern_001")
        assert failures[0].was_fixed is True

    def test_usage_tracking(self):
        """Test usage snapshot recording."""
        evolution = MemoryEvolution()

        snapshot = evolution.record_usage_snapshot(
            pattern_id="pattern_001",
            total_uses=100,
            successful_uses=85,
            failed_uses=15,
            strength=0.9,
            current_streak=5,
        )

        assert snapshot is not None
        assert snapshot.total_uses == 100
        assert snapshot.success_rate == 0.85

        # Get history
        history = evolution.get_usage_history("pattern_001")
        assert len(history) == 1

    def test_usage_trend_analysis(self):
        """Test usage trend analysis."""
        evolution = MemoryEvolution()

        # Record multiple snapshots showing improvement
        for i, (total, success) in enumerate([
            (10, 5),   # 50% success
            (20, 12),  # 60% success
            (30, 21),  # 70% success
            (40, 32),  # 80% success
            (50, 45),  # 90% success
        ]):
            evolution.record_usage_snapshot(
                pattern_id="pattern_001",
                total_uses=total,
                successful_uses=success,
                failed_uses=total - success,
            )

        trend = evolution.get_usage_trend("pattern_001")

        assert trend["trend"] == "improving"
        assert trend["snapshots"] == 5

    def test_lineage_tracking(self):
        """Test pattern lineage tracking."""
        evolution = MemoryEvolution()

        # Create parent pattern
        evolution.record_origin(
            pattern_id="parent_001",
            origin_type=OriginType.LEARNED,
            source="dataset",
        )

        # Create child pattern
        evolution.record_origin(
            pattern_id="child_001",
            origin_type=OriginType.MUTATED,
            parent_pattern_id="parent_001",
            derivation_method="fix",
        )

        # Get lineage
        lineage = evolution.get_lineage("child_001")

        assert lineage is not None
        assert "parent_001" in lineage.ancestors
        assert lineage.ancestor_depth == 1

        # Check parent has child as descendant
        parent_lineage = evolution.get_lineage("parent_001")
        assert "child_001" in parent_lineage.descendants

    def test_find_problematic_patterns(self):
        """Test finding patterns with many failures."""
        evolution = MemoryEvolution()

        # Create pattern with multiple failures
        evolution.record_version(
            pattern_id="problematic",
            event_type=EvolutionEvent.CREATED,
            content="test",
        )
        version = evolution.get_current_version("problematic")

        for i in range(5):
            evolution.record_failure(
                pattern_id="problematic",
                version_id=version.version_id,
                error_type="Error",
                error_message=f"Error {i}",
            )

        problematic = evolution.find_problematic_patterns(min_failures=3)

        assert len(problematic) == 1
        assert problematic[0]["pattern_id"] == "problematic"
        assert problematic[0]["total_failures"] == 5

    def test_find_patterns_by_origin(self):
        """Test finding patterns by origin type."""
        evolution = MemoryEvolution()

        # Create patterns with different origins
        evolution.record_origin(
            pattern_id="learned_1",
            origin_type=OriginType.LEARNED,
            source="dataset_a",
        )
        evolution.record_origin(
            pattern_id="learned_2",
            origin_type=OriginType.LEARNED,
            source="dataset_b",
        )
        evolution.record_origin(
            pattern_id="mutated_1",
            origin_type=OriginType.MUTATED,
            parent_pattern_id="learned_1",
        )

        learned = evolution.find_patterns_by_origin(OriginType.LEARNED)
        mutated = evolution.find_patterns_by_origin(OriginType.MUTATED)

        assert len(learned) == 2
        assert len(mutated) == 1

    def test_evolution_history(self):
        """Test getting complete evolution history."""
        evolution = MemoryEvolution()

        # Create pattern with full history
        evolution.record_origin(
            pattern_id="full_pattern",
            origin_type=OriginType.LEARNED,
            source="test_dataset",
        )

        evolution.record_version(
            pattern_id="full_pattern",
            event_type=EvolutionEvent.CREATED,
            content="version 1",
        )

        version = evolution.get_current_version("full_pattern")
        evolution.record_failure(
            pattern_id="full_pattern",
            version_id=version.version_id,
            error_type="Error",
            error_message="test error",
        )

        evolution.record_usage_snapshot(
            pattern_id="full_pattern",
            total_uses=10,
            successful_uses=8,
            failed_uses=2,
        )

        # Get history
        history = evolution.get_evolution_history("full_pattern")

        assert history["pattern_id"] == "full_pattern"
        assert history["origin"] is not None
        assert len(history["versions"]) == 1
        assert len(history["failures"]) == 1
        assert history["usage_trend"]["snapshots"] == 1

    def test_evolution_summary(self):
        """Test getting evolution summary."""
        evolution = MemoryEvolution()

        evolution.record_origin(
            pattern_id="summary_pattern",
            origin_type=OriginType.LEARNED,
            source="test",
        )

        for i in range(3):
            evolution.record_version(
                pattern_id="summary_pattern",
                event_type=EvolutionEvent.ENHANCED,
                content=f"version {i+1}",
            )

        summary = evolution.get_evolution_summary("summary_pattern")

        assert summary["pattern_id"] == "summary_pattern"
        assert summary["origin_type"] == "learned"
        assert summary["total_versions"] == 3
        assert summary["current_version"] == 3

    def test_serialization(self):
        """Test full serialization and deserialization."""
        evolution = MemoryEvolution()

        # Add data
        evolution.record_origin(
            pattern_id="test_pattern",
            origin_type=OriginType.LEARNED,
            source="test",
        )
        evolution.record_version(
            pattern_id="test_pattern",
            event_type=EvolutionEvent.CREATED,
            content="test content",
        )

        # Serialize
        data = evolution.to_dict()

        # Create new instance and deserialize
        evolution2 = MemoryEvolution()
        evolution2.from_dict(data)

        # Verify
        origin = evolution2.get_origin("test_pattern")
        assert origin is not None
        assert origin.origin_type == OriginType.LEARNED

        versions = evolution2.get_versions("test_pattern")
        assert len(versions) == 1

    def test_statistics(self):
        """Test statistics tracking."""
        evolution = MemoryEvolution()

        # Add various data
        evolution.record_origin(
            pattern_id="p1",
            origin_type=OriginType.LEARNED,
            source="test",
        )
        evolution.record_origin(
            pattern_id="p2",
            origin_type=OriginType.MUTATED,
            parent_pattern_id="p1",
        )

        evolution.record_version(
            pattern_id="p1",
            event_type=EvolutionEvent.CREATED,
            content="test",
        )
        evolution.record_version(
            pattern_id="p1",
            event_type=EvolutionEvent.FIXED,
            content="test fixed",
        )

        stats = evolution.get_stats()

        assert stats["total_patterns_tracked"] == 2
        assert stats["total_versions"] == 2
        assert stats["by_origin_type"]["learned"] == 1
        assert stats["by_origin_type"]["mutated"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
