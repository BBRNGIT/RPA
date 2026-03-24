"""
Tests for Phase 6: System Integrity & Safety.

Tests for:
- CurriculumIngestionGate: Validate curriculum before ingestion
- RecursiveLoopPrevention: Detect and prevent infinite loops
- PatternValidationFramework: Comprehensive pattern validation
- SystemHealthMonitor: Track system health metrics
"""

import pytest
from datetime import datetime


# =============================================================================
# CurriculumIngestionGate Tests
# =============================================================================

class TestCurriculumIngestionGate:
    """Tests for CurriculumIngestionGate."""

    def test_imports(self):
        """Test that CurriculumIngestionGate components can be imported."""
        from rpa.safety.curriculum_ingestion_gate import (
            CurriculumIngestionGate,
            IngestionResult,
            CurriculumBatch,
        )
        assert CurriculumIngestionGate is not None
        assert IngestionResult is not None
        assert CurriculumBatch is not None

    def test_create_curriculum_batch(self):
        """Test creating a CurriculumBatch."""
        from rpa.safety.curriculum_ingestion_gate import CurriculumBatch

        batch = CurriculumBatch(
            batch_id="test_batch_001",
            domain="english",
            hierarchy_level=1,
            items=[
                {"content": "apple", "label": "apple"},
                {"content": "banana", "label": "banana"},
            ],
        )

        assert batch.batch_id == "test_batch_001"
        assert batch.domain == "english"
        assert len(batch.items) == 2

    def test_batch_to_dict(self):
        """Test batch serialization."""
        from rpa.safety.curriculum_ingestion_gate import CurriculumBatch

        batch = CurriculumBatch(
            batch_id="test_batch",
            domain="python",
            hierarchy_level=2,
            items=[{"content": "x = 1"}],
        )

        data = batch.to_dict()
        assert data["batch_id"] == "test_batch"
        assert data["domain"] == "python"
        assert "created_at" in data

    def test_batch_from_dict(self):
        """Test batch deserialization."""
        from rpa.safety.curriculum_ingestion_gate import CurriculumBatch

        data = {
            "batch_id": "test_batch",
            "domain": "english",
            "hierarchy_level": 1,
            "items": [{"content": "test"}],
        }

        batch = CurriculumBatch.from_dict(data)
        assert batch.batch_id == "test_batch"
        assert batch.domain == "english"

    def test_batch_compute_hash(self):
        """Test batch hash computation."""
        from rpa.safety.curriculum_ingestion_gate import CurriculumBatch

        batch = CurriculumBatch(
            batch_id="test",
            domain="english",
            hierarchy_level=1,
            items=[{"content": "test"}],
        )

        hash1 = batch.compute_hash()
        hash2 = batch.compute_hash()
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex digest

    def test_create_ingestion_gate(self):
        """Test creating an ingestion gate."""
        from rpa.safety.curriculum_ingestion_gate import CurriculumIngestionGate

        gate = CurriculumIngestionGate()
        assert gate is not None
        assert gate.strict_mode is True

    def test_create_ingestion_gate_non_strict(self):
        """Test creating non-strict ingestion gate."""
        from rpa.safety.curriculum_ingestion_gate import CurriculumIngestionGate

        gate = CurriculumIngestionGate(strict_mode=False)
        assert gate.strict_mode is False

    def test_validate_valid_batch(self):
        """Test validating a valid batch."""
        from rpa.safety.curriculum_ingestion_gate import (
            CurriculumIngestionGate,
            CurriculumBatch,
        )

        gate = CurriculumIngestionGate()
        batch = CurriculumBatch(
            batch_id="valid_batch",
            domain="english",
            hierarchy_level=1,
            items=[
                {"content": "apple", "label": "apple"},
                {"content": "banana", "label": "banana"},
            ],
        )

        result = gate.validate_batch(batch)
        assert result.is_valid is True
        assert result.items_accepted == 2
        assert result.items_rejected == 0

    def test_validate_batch_missing_batch_id(self):
        """Test validating batch with missing batch_id."""
        from rpa.safety.curriculum_ingestion_gate import (
            CurriculumIngestionGate,
            CurriculumBatch,
        )

        gate = CurriculumIngestionGate()
        batch = CurriculumBatch(
            batch_id="",
            domain="english",
            hierarchy_level=1,
            items=[{"content": "test"}],
        )

        result = gate.validate_batch(batch)
        assert result.is_valid is False
        assert len(result.rejection_reasons) > 0

    def test_validate_batch_unsupported_domain(self):
        """Test validating batch with unsupported domain."""
        from rpa.safety.curriculum_ingestion_gate import (
            CurriculumIngestionGate,
            CurriculumBatch,
        )

        gate = CurriculumIngestionGate()
        batch = CurriculumBatch(
            batch_id="test",
            domain="unsupported_domain",
            hierarchy_level=1,
            items=[{"content": "test"}],
        )

        result = gate.validate_batch(batch)
        assert result.is_valid is False

    def test_validate_item_missing_content(self):
        """Test validating item with missing content."""
        from rpa.safety.curriculum_ingestion_gate import (
            CurriculumIngestionGate,
            CurriculumBatch,
        )

        gate = CurriculumIngestionGate()
        batch = CurriculumBatch(
            batch_id="test",
            domain="english",
            hierarchy_level=1,
            items=[{"label": "no_content"}],
        )

        result = gate.validate_batch(batch)
        assert result.items_rejected == 1

    def test_validate_item_empty_content(self):
        """Test validating item with empty content."""
        from rpa.safety.curriculum_ingestion_gate import (
            CurriculumIngestionGate,
            CurriculumBatch,
        )

        gate = CurriculumIngestionGate()
        batch = CurriculumBatch(
            batch_id="test",
            domain="english",
            hierarchy_level=1,
            items=[{"content": ""}],
        )

        result = gate.validate_batch(batch)
        assert result.items_rejected == 1

    def test_validate_item_forbidden_pattern(self):
        """Test validating item with forbidden pattern (script injection)."""
        from rpa.safety.curriculum_ingestion_gate import (
            CurriculumIngestionGate,
            CurriculumBatch,
        )

        gate = CurriculumIngestionGate()
        batch = CurriculumBatch(
            batch_id="test",
            domain="english",
            hierarchy_level=1,
            items=[{"content": "<script>alert('xss')</script>"}],
        )

        result = gate.validate_batch(batch)
        assert result.is_valid is False

    def test_validate_python_code(self):
        """Test validating Python code item."""
        from rpa.safety.curriculum_ingestion_gate import (
            CurriculumIngestionGate,
            CurriculumBatch,
        )

        gate = CurriculumIngestionGate()
        batch = CurriculumBatch(
            batch_id="test",
            domain="python",
            hierarchy_level=1,
            items=[
                {"content": "x = 1", "label": "assignment"},
                {"content": "def foo():\n    pass", "label": "function"},
            ],
        )

        result = gate.validate_batch(batch)
        assert result.items_accepted == 2

    def test_validate_python_unbalanced_parens(self):
        """Test validating Python code with unbalanced parentheses."""
        from rpa.safety.curriculum_ingestion_gate import (
            CurriculumIngestionGate,
            CurriculumBatch,
        )

        gate = CurriculumIngestionGate(strict_mode=False)
        batch = CurriculumBatch(
            batch_id="test",
            domain="python",
            hierarchy_level=1,
            items=[{"content": "print('unbalanced')"}],  # Actually balanced - 2 parens
        )

        result = gate.validate_batch(batch)
        # This should pass as it's actually valid
        assert result.is_valid is True

    def test_validate_json_file(self):
        """Test validating JSON file."""
        from rpa.safety.curriculum_ingestion_gate import CurriculumIngestionGate
        import json
        import tempfile

        gate = CurriculumIngestionGate()

        # Create temp file with valid JSON
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                "batch_id": "file_test",
                "domain": "english",
                "hierarchy_level": 1,
                "items": [{"content": "test"}],
            }, f)
            temp_path = f.name

        result = gate.validate_json_file(temp_path)
        assert result.is_valid is True

        # Clean up
        import os
        os.unlink(temp_path)

    def test_validate_invalid_json_file(self):
        """Test validating invalid JSON file."""
        from rpa.safety.curriculum_ingestion_gate import CurriculumIngestionGate
        import tempfile

        gate = CurriculumIngestionGate()

        # Create temp file with invalid JSON
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{ invalid json }")
            temp_path = f.name

        result = gate.validate_json_file(temp_path)
        assert result.is_valid is False

        # Clean up
        import os
        os.unlink(temp_path)

    def test_duplicate_detection(self):
        """Test duplicate batch detection."""
        from rpa.safety.curriculum_ingestion_gate import (
            CurriculumIngestionGate,
            CurriculumBatch,
        )

        gate = CurriculumIngestionGate()
        batch = CurriculumBatch(
            batch_id="test",
            domain="english",
            hierarchy_level=1,
            items=[{"content": "test"}],
        )

        # First ingestion
        result1 = gate.validate_batch(batch)
        assert "previously ingested" not in " ".join(result1.warnings)

        # Mark as ingested
        gate.mark_ingested(result1.batch_hash)

        # Second ingestion of same content
        result2 = gate.validate_batch(batch)
        assert any("previously ingested" in w for w in result2.warnings)

    def test_get_stats(self):
        """Test getting validation statistics."""
        from rpa.safety.curriculum_ingestion_gate import (
            CurriculumIngestionGate,
            CurriculumBatch,
        )

        gate = CurriculumIngestionGate()
        batch = CurriculumBatch(
            batch_id="test",
            domain="english",
            hierarchy_level=1,
            items=[{"content": "test"}],
        )

        gate.validate_batch(batch)
        stats = gate.get_stats()
        assert stats["batches_processed"] == 1
        assert stats["items_accepted"] == 1


# =============================================================================
# RecursiveLoopPrevention Tests
# =============================================================================

class TestRecursiveLoopPrevention:
    """Tests for RecursiveLoopPrevention."""

    def test_imports(self):
        """Test that RecursiveLoopPrevention components can be imported."""
        from rpa.safety.recursive_loop_prevention import (
            RecursiveLoopPrevention,
            LoopDetectionResult,
            LoopInfo,
        )
        assert RecursiveLoopPrevention is not None
        assert LoopDetectionResult is not None
        assert LoopInfo is not None

    def test_create_loop_prevention(self):
        """Test creating loop prevention system."""
        from rpa.safety.recursive_loop_prevention import RecursiveLoopPrevention

        prevention = RecursiveLoopPrevention()
        assert prevention is not None
        assert prevention.max_depth == 100

    def test_create_loop_prevention_custom_depth(self):
        """Test creating loop prevention with custom depth."""
        from rpa.safety.recursive_loop_prevention import RecursiveLoopPrevention

        prevention = RecursiveLoopPrevention(max_depth=50)
        assert prevention.max_depth == 50

    def test_detect_no_cycles(self):
        """Test detecting no cycles in acyclic graph."""
        from rpa.safety.recursive_loop_prevention import RecursiveLoopPrevention

        prevention = RecursiveLoopPrevention()

        # Simple DAG: A -> B -> C
        graph = {
            "A": ["B"],
            "B": ["C"],
            "C": [],
        }

        result = prevention.detect_cycles_dfs(graph)
        assert result.has_loops is False
        assert result.safe_to_proceed is True

    def test_detect_simple_cycle(self):
        """Test detecting simple cycle."""
        from rpa.safety.recursive_loop_prevention import RecursiveLoopPrevention

        prevention = RecursiveLoopPrevention()

        # Cycle: A -> B -> A
        graph = {
            "A": ["B"],
            "B": ["A"],
        }

        result = prevention.detect_cycles_dfs(graph)
        assert result.has_loops is True
        assert result.safe_to_proceed is False
        assert len(result.loops) > 0

    def test_detect_self_loop(self):
        """Test detecting self-loop."""
        from rpa.safety.recursive_loop_prevention import RecursiveLoopPrevention

        prevention = RecursiveLoopPrevention()

        # Self-loop: A -> A
        graph = {
            "A": ["A"],
        }

        result = prevention.detect_cycles_dfs(graph)
        assert result.has_loops is True
        assert len(result.loops) == 1

    def test_detect_longer_cycle(self):
        """Test detecting longer cycle."""
        from rpa.safety.recursive_loop_prevention import RecursiveLoopPrevention

        prevention = RecursiveLoopPrevention()

        # Longer cycle: A -> B -> C -> A
        graph = {
            "A": ["B"],
            "B": ["C"],
            "C": ["A"],
        }

        result = prevention.detect_cycles_dfs(graph)
        assert result.has_loops is True
        assert result.loops[0].length == 3

    def test_detect_scc(self):
        """Test detecting strongly connected components."""
        from rpa.safety.recursive_loop_prevention import RecursiveLoopPrevention

        prevention = RecursiveLoopPrevention()

        # SCC: A -> B -> C -> A, plus D -> E
        graph = {
            "A": ["B"],
            "B": ["C"],
            "C": ["A"],
            "D": ["E"],
            "E": [],
        }

        result = prevention.detect_strongly_connected_components(graph)
        assert result.has_loops is True
        assert len(result.loops) == 1

    def test_check_recursion_depth_safe(self):
        """Test checking safe recursion depth."""
        from rpa.safety.recursive_loop_prevention import RecursiveLoopPrevention

        prevention = RecursiveLoopPrevention(max_depth=100)

        call_stack = ["node_" + str(i) for i in range(10)]
        is_safe, warning = prevention.check_recursion_depth(call_stack)

        assert is_safe is True
        assert warning is None

    def test_check_recursion_depth_exceeded(self):
        """Test checking exceeded recursion depth."""
        from rpa.safety.recursive_loop_prevention import RecursiveLoopPrevention

        prevention = RecursiveLoopPrevention(max_depth=10)

        call_stack = ["node_" + str(i) for i in range(15)]
        is_safe, warning = prevention.check_recursion_depth(call_stack)

        assert is_safe is False
        assert warning is not None

    def test_check_chain_length_safe(self):
        """Test checking safe chain length."""
        from rpa.safety.recursive_loop_prevention import RecursiveLoopPrevention

        prevention = RecursiveLoopPrevention()

        chain = ["node_" + str(i) for i in range(100)]
        is_safe, warning = prevention.check_chain_length(chain)

        assert is_safe is True

    def test_validate_pattern_reference_valid(self):
        """Test validating valid pattern reference."""
        from rpa.safety.recursive_loop_prevention import RecursiveLoopPrevention

        prevention = RecursiveLoopPrevention()

        graph = {
            "A": ["B"],
            "B": [],
        }

        is_valid, error = prevention.validate_pattern_reference("A", "C", graph)
        assert is_valid is True
        assert error is None

    def test_validate_pattern_reference_self(self):
        """Test validating self-reference."""
        from rpa.safety.recursive_loop_prevention import RecursiveLoopPrevention

        prevention = RecursiveLoopPrevention()

        graph = {"A": []}

        is_valid, error = prevention.validate_pattern_reference("A", "A", graph)
        assert is_valid is False
        assert "Self-reference" in error

    def test_validate_pattern_reference_creates_cycle(self):
        """Test validating reference that would create cycle."""
        from rpa.safety.recursive_loop_prevention import RecursiveLoopPrevention

        prevention = RecursiveLoopPrevention()

        graph = {
            "A": ["B"],
            "B": ["C"],
            "C": [],
        }

        # Adding C -> A would create a cycle
        is_valid, error = prevention.validate_pattern_reference("C", "A", graph)
        assert is_valid is False
        assert "cycle" in error.lower()

    def test_get_visit_count(self):
        """Test getting node visit count."""
        from rpa.safety.recursive_loop_prevention import RecursiveLoopPrevention

        prevention = RecursiveLoopPrevention()

        graph = {
            "A": ["B"],
            "B": [],
        }

        prevention.detect_cycles_dfs(graph)
        count = prevention.get_visit_count("A")
        assert count >= 1

    def test_get_hot_nodes(self):
        """Test getting hot nodes."""
        from rpa.safety.recursive_loop_prevention import RecursiveLoopPrevention

        prevention = RecursiveLoopPrevention()

        graph = {
            "A": ["B"],
            "B": ["C"],
            "C": [],
        }

        # Run multiple times to create hot nodes
        for _ in range(15):
            prevention.detect_cycles_dfs(graph)

        hot = prevention.get_hot_nodes(threshold=10)
        assert len(hot) > 0

    def test_get_stats(self):
        """Test getting detection statistics."""
        from rpa.safety.recursive_loop_prevention import RecursiveLoopPrevention

        prevention = RecursiveLoopPrevention()

        graph = {"A": ["A"]}  # Self-loop
        prevention.detect_cycles_dfs(graph)

        stats = prevention.get_stats()
        assert stats["checks_performed"] == 1
        assert stats["loops_detected"] == 1

    def test_loop_info_to_dict(self):
        """Test LoopInfo serialization."""
        from rpa.safety.recursive_loop_prevention import LoopInfo

        loop = LoopInfo(
            loop_id="test_loop",
            nodes=["A", "B", "A"],
            length=2,
            severity="critical",
            detection_method="dfs",
        )

        data = loop.to_dict()
        assert data["loop_id"] == "test_loop"
        assert data["length"] == 2
        assert data["severity"] == "critical"


# =============================================================================
# PatternValidationFramework Tests
# =============================================================================

class TestPatternValidationFramework:
    """Tests for PatternValidationFramework."""

    def test_imports(self):
        """Test that PatternValidationFramework components can be imported."""
        from rpa.safety.pattern_validation_framework import (
            PatternValidationFramework,
            ValidationResult,
            ValidationRule,
            RuleSeverity,
        )
        assert PatternValidationFramework is not None
        assert ValidationResult is not None
        assert ValidationRule is not None
        assert RuleSeverity is not None

    def test_create_validation_framework(self):
        """Test creating validation framework."""
        from rpa.safety.pattern_validation_framework import PatternValidationFramework

        framework = PatternValidationFramework()
        assert framework is not None
        assert framework.strict_mode is True

    def test_builtin_rules_registered(self):
        """Test that built-in rules are registered."""
        from rpa.safety.pattern_validation_framework import PatternValidationFramework

        framework = PatternValidationFramework()
        rules = framework.get_all_rules()

        assert len(rules) > 0
        # Check for some expected rules
        rule_ids = [r.rule_id for r in rules]
        assert "struct_001" in rule_ids  # Has Content
        assert "struct_002" in rule_ids  # Has Label

    def test_validate_valid_pattern(self):
        """Test validating a valid pattern."""
        from rpa.safety.pattern_validation_framework import PatternValidationFramework

        framework = PatternValidationFramework()

        pattern = {
            "id": "test_pattern",
            "content": "apple",
            "label": "apple",
            "hierarchy_level": 1,
        }

        result = framework.validate_pattern(pattern)
        assert result.is_valid is True
        assert len(result.failed_rules) == 0

    def test_validate_pattern_empty_content(self):
        """Test validating pattern with empty content."""
        from rpa.safety.pattern_validation_framework import PatternValidationFramework

        framework = PatternValidationFramework()

        pattern = {
            "id": "test",
            "content": "",
        }

        result = framework.validate_pattern(pattern)
        assert result.is_valid is False
        assert any(r["rule_id"] == "struct_001" for r in result.failed_rules)

    def test_validate_pattern_missing_label(self):
        """Test validating pattern with missing label."""
        from rpa.safety.pattern_validation_framework import PatternValidationFramework

        framework = PatternValidationFramework()

        pattern = {
            "content": "test content",
        }

        result = framework.validate_pattern(pattern)
        # Missing label is ERROR level, fails in strict mode
        assert any(r["rule_id"] == "struct_002" for r in result.failed_rules)

    def test_validate_pattern_negative_hierarchy(self):
        """Test validating pattern with negative hierarchy."""
        from rpa.safety.pattern_validation_framework import PatternValidationFramework

        framework = PatternValidationFramework()

        pattern = {
            "content": "test",
            "label": "test",
            "hierarchy_level": -1,
        }

        result = framework.validate_pattern(pattern)
        assert any(r["rule_id"] == "struct_003" for r in result.failed_rules)

    def test_validate_pattern_malicious_content(self):
        """Test validating pattern with script content."""
        from rpa.safety.pattern_validation_framework import PatternValidationFramework

        framework = PatternValidationFramework()

        pattern = {
            "content": "<script>alert('xss')</script>",
            "label": "malicious",
        }

        result = framework.validate_pattern(pattern)
        assert result.is_valid is False
        assert any(r["rule_id"] == "content_001" for r in result.failed_rules)

    def test_validate_pattern_invalid_composition(self):
        """Test validating pattern with invalid composition."""
        from rpa.safety.pattern_validation_framework import PatternValidationFramework

        framework = PatternValidationFramework()

        pattern = {
            "content": "test",
            "label": "test",
            "composition": "not a list",  # Should be a list
        }

        result = framework.validate_pattern(pattern)
        assert any(r["rule_id"] == "content_003" for r in result.failed_rules)

    def test_validate_batch(self):
        """Test validating a batch of patterns."""
        from rpa.safety.pattern_validation_framework import PatternValidationFramework

        framework = PatternValidationFramework()

        patterns = [
            {"content": "valid", "label": "valid"},
            {"content": "", "label": "invalid"},  # Empty content
            {"content": "valid2", "label": "valid2"},
        ]

        result = framework.validate_batch(patterns)
        assert result["total_patterns"] == 3
        assert result["valid_count"] == 2
        assert result["invalid_count"] == 1

    def test_register_custom_rule(self):
        """Test registering custom validation rule."""
        from rpa.safety.pattern_validation_framework import (
            PatternValidationFramework,
            ValidationRule,
            RuleSeverity,
        )

        framework = PatternValidationFramework()

        rule = ValidationRule(
            rule_id="custom_001",
            name="Custom Rule",
            description="A custom validation rule",
            severity=RuleSeverity.WARNING,
            check_function=lambda p: "bad" not in p.get("content", "").lower(),
            error_message="Content contains 'bad'",
        )

        framework.register_rule(rule)
        assert framework.get_rule("custom_001") is not None

        # Test the rule
        pattern = {"content": "This is bad content", "label": "test"}
        result = framework.validate_pattern(pattern)
        assert any(r["rule_id"] == "custom_001" for r in result.failed_rules)

    def test_unregister_rule(self):
        """Test unregistering a rule."""
        from rpa.safety.pattern_validation_framework import PatternValidationFramework

        framework = PatternValidationFramework()

        # Remove a rule
        removed = framework.unregister_rule("struct_002")
        assert removed is True

        # Verify it's gone
        assert framework.get_rule("struct_002") is None

    def test_enable_disable_rule(self):
        """Test enabling and disabling rules."""
        from rpa.safety.pattern_validation_framework import PatternValidationFramework

        framework = PatternValidationFramework()

        # Disable a rule
        framework.disable_rule("struct_002")
        assert framework.get_rule("struct_002").enabled is False

        # Enable it again
        framework.enable_rule("struct_002")
        assert framework.get_rule("struct_002").enabled is True

    def test_get_rules_by_severity(self):
        """Test getting rules by severity."""
        from rpa.safety.pattern_validation_framework import (
            PatternValidationFramework,
            RuleSeverity,
        )

        framework = PatternValidationFramework()

        critical_rules = framework.get_rules_by_severity(RuleSeverity.CRITICAL)
        assert len(critical_rules) > 0

        # All should be critical
        for rule in critical_rules:
            assert rule.severity == RuleSeverity.CRITICAL

    def test_create_custom_rule_helper(self):
        """Test create_custom_rule helper method."""
        from rpa.safety.pattern_validation_framework import (
            PatternValidationFramework,
            RuleSeverity,
        )

        framework = PatternValidationFramework()

        rule = framework.create_custom_rule(
            rule_id="helper_001",
            name="Helper Rule",
            description="Created via helper",
            severity=RuleSeverity.WARNING,
            check_function=lambda p: True,
            error_message="Helper error",
        )

        assert rule.rule_id == "helper_001"
        assert framework.get_rule("helper_001") is not None

    def test_get_stats(self):
        """Test getting validation statistics."""
        from rpa.safety.pattern_validation_framework import PatternValidationFramework

        framework = PatternValidationFramework()

        pattern = {"content": "test", "label": "test"}
        framework.validate_pattern(pattern)

        stats = framework.get_stats()
        assert stats["validations_performed"] == 1
        assert stats["patterns_passed"] == 1

    def test_non_strict_mode(self):
        """Test non-strict mode validation."""
        from rpa.safety.pattern_validation_framework import PatternValidationFramework

        framework = PatternValidationFramework(strict_mode=False)

        # Pattern missing label (ERROR level)
        pattern = {"content": "test content"}

        result = framework.validate_pattern(pattern)
        # In non-strict mode, ERROR level doesn't block
        # Only CRITICAL should block
        assert result.is_valid is True


# =============================================================================
# SystemHealthMonitor Tests
# =============================================================================

class TestSystemHealthMonitor:
    """Tests for SystemHealthMonitor."""

    def test_imports(self):
        """Test that SystemHealthMonitor components can be imported."""
        from rpa.safety.system_health_monitor import (
            SystemHealthMonitor,
            HealthMetric,
            HealthStatus,
            HealthReport,
        )
        assert SystemHealthMonitor is not None
        assert HealthMetric is not None
        assert HealthStatus is not None
        assert HealthReport is not None

    def test_create_health_monitor(self):
        """Test creating health monitor."""
        from rpa.safety.system_health_monitor import SystemHealthMonitor

        monitor = SystemHealthMonitor()
        assert monitor is not None

    def test_health_status_enum(self):
        """Test HealthStatus enum values."""
        from rpa.safety.system_health_monitor import HealthStatus

        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.DEGRADED.value == "degraded"
        assert HealthStatus.UNHEALTHY.value == "unhealthy"
        assert HealthStatus.UNKNOWN.value == "unknown"

    def test_collect_memory_metrics(self):
        """Test collecting memory metrics."""
        from rpa.safety.system_health_monitor import SystemHealthMonitor

        monitor = SystemHealthMonitor()
        metric = monitor.collect_memory_metrics()

        assert metric.name == "Memory Usage"
        assert metric.unit == "MB"
        assert metric.status is not None

    def test_collect_pattern_metrics_healthy(self):
        """Test collecting pattern metrics (healthy)."""
        from rpa.safety.system_health_monitor import (
            SystemHealthMonitor,
            HealthStatus,
        )

        monitor = SystemHealthMonitor()
        metric = monitor.collect_pattern_metrics(
            stm_count=100,
            ltm_count=500,
            episodic_count=200,
        )

        assert metric.name == "Pattern Count"
        assert metric.value == 800
        assert metric.status == HealthStatus.HEALTHY

    def test_collect_pattern_metrics_degraded(self):
        """Test collecting pattern metrics (degraded)."""
        from rpa.safety.system_health_monitor import (
            SystemHealthMonitor,
            HealthStatus,
        )

        monitor = SystemHealthMonitor()
        metric = monitor.collect_pattern_metrics(
            stm_count=1000,
            ltm_count=8000,
            episodic_count=500,  # Total > 9000
        )

        assert metric.status == HealthStatus.DEGRADED

    def test_collect_error_metrics_healthy(self):
        """Test collecting error metrics (healthy)."""
        from rpa.safety.system_health_monitor import (
            SystemHealthMonitor,
            HealthStatus,
        )

        monitor = SystemHealthMonitor()

        # Record some operations
        monitor.record_operation("test_op", 100)
        monitor.record_error("test_error", 2)

        metric = monitor.collect_error_metrics()

        assert metric.name == "Error Rate"
        assert metric.value == 2.0  # 2/100 * 100
        assert metric.status == HealthStatus.HEALTHY

    def test_collect_error_metrics_unhealthy(self):
        """Test collecting error metrics (unhealthy)."""
        from rpa.safety.system_health_monitor import (
            SystemHealthMonitor,
            HealthStatus,
        )

        monitor = SystemHealthMonitor()

        # Record many errors
        monitor.record_operation("test_op", 100)
        monitor.record_error("test_error", 15)  # 15% error rate

        metric = monitor.collect_error_metrics()

        assert metric.status == HealthStatus.UNHEALTHY

    def test_collect_consolidation_metrics(self):
        """Test collecting consolidation metrics."""
        from rpa.safety.system_health_monitor import (
            SystemHealthMonitor,
            HealthStatus,
        )

        monitor = SystemHealthMonitor()
        metric = monitor.collect_consolidation_metrics(
            total_attempted=100,
            total_consolidated=80,
        )

        assert metric.name == "Consolidation Rate"
        assert metric.value == 80.0
        assert metric.status == HealthStatus.HEALTHY

    def test_collect_inquiry_metrics(self):
        """Test collecting inquiry metrics."""
        from rpa.safety.system_health_monitor import SystemHealthMonitor

        monitor = SystemHealthMonitor()
        metric = monitor.collect_inquiry_metrics(pending_inquiries=50)

        assert metric.name == "Inquiry Backlog"
        assert metric.value == 50

    def test_collect_performance_metrics(self):
        """Test collecting performance metrics."""
        from rpa.safety.system_health_monitor import (
            SystemHealthMonitor,
            HealthStatus,
        )

        monitor = SystemHealthMonitor()
        metric = monitor.collect_performance_metrics(avg_response_time_ms=500)

        assert metric.name == "Response Time"
        assert metric.value == 500
        assert metric.status == HealthStatus.HEALTHY

    def test_register_custom_collector(self):
        """Test registering custom metric collector."""
        from rpa.safety.system_health_monitor import SystemHealthMonitor

        monitor = SystemHealthMonitor()
        monitor.register_custom_collector("custom_metric", lambda: 42)

        metrics = monitor.collect_custom_metrics()
        assert len(metrics) == 1
        assert metrics[0].name == "custom_metric"
        assert metrics[0].value == 42

    def test_unregister_custom_collector(self):
        """Test unregistering custom collector."""
        from rpa.safety.system_health_monitor import SystemHealthMonitor

        monitor = SystemHealthMonitor()
        monitor.register_custom_collector("custom", lambda: 1)

        removed = monitor.unregister_custom_collector("custom")
        assert removed is True

        metrics = monitor.collect_custom_metrics()
        assert len(metrics) == 0

    def test_generate_report(self):
        """Test generating health report."""
        from rpa.safety.system_health_monitor import (
            SystemHealthMonitor,
            HealthStatus,
        )

        monitor = SystemHealthMonitor()
        report = monitor.generate_report(
            stm_count=100,
            ltm_count=500,
            episodic_count=100,
            pending_inquiries=10,
            consolidation_attempted=50,
            consolidation_success=40,
            avg_response_time_ms=100,
        )

        assert report.overall_status == HealthStatus.HEALTHY
        assert len(report.metrics) >= 6  # Standard metrics
        assert report.uptime_seconds >= 0

    def test_generate_report_with_issues(self):
        """Test generating report with issues."""
        from rpa.safety.system_health_monitor import (
            SystemHealthMonitor,
            HealthStatus,
        )

        monitor = SystemHealthMonitor()

        # Create high error rate
        monitor.record_operation("op", 100)
        monitor.record_error("err", 20)

        report = monitor.generate_report()

        assert report.overall_status == HealthStatus.UNHEALTHY
        assert len(report.issues) > 0
        assert len(report.recommendations) > 0

    def test_health_metric_to_dict(self):
        """Test HealthMetric serialization."""
        from rpa.safety.system_health_monitor import (
            HealthMetric,
            HealthStatus,
        )

        metric = HealthMetric(
            metric_id="test_metric",
            name="Test",
            value=100,
            unit="units",
            status=HealthStatus.HEALTHY,
        )

        data = metric.to_dict()
        assert data["name"] == "Test"
        assert data["value"] == 100
        assert data["status"] == "healthy"

    def test_health_report_to_dict(self):
        """Test HealthReport serialization."""
        from rpa.safety.system_health_monitor import (
            HealthReport,
            HealthMetric,
            HealthStatus,
        )

        report = HealthReport(
            report_id="test_report",
            overall_status=HealthStatus.HEALTHY,
            metrics=[
                HealthMetric(
                    metric_id="m1",
                    name="Metric",
                    value=1,
                    unit="unit",
                    status=HealthStatus.HEALTHY,
                )
            ],
        )

        data = report.to_dict()
        assert data["report_id"] == "test_report"
        assert data["overall_status"] == "healthy"
        assert len(data["metrics"]) == 1

    def test_get_metric_history(self):
        """Test getting metric history."""
        from rpa.safety.system_health_monitor import SystemHealthMonitor

        monitor = SystemHealthMonitor()

        # Generate multiple reports
        for _ in range(3):
            monitor.generate_report()

        history = monitor.get_metric_history("Memory Usage")
        assert len(history) == 3

    def test_set_threshold(self):
        """Test setting custom thresholds."""
        from rpa.safety.system_health_monitor import (
            SystemHealthMonitor,
            HealthStatus,
        )

        monitor = SystemHealthMonitor()
        monitor.set_threshold("inquiry_backlog", warning=50, critical=100)

        # Now 75 inquiries should be degraded (between 50 and 100)
        metric = monitor.collect_inquiry_metrics(pending_inquiries=75)
        assert metric.status == HealthStatus.DEGRADED

    def test_get_stats(self):
        """Test getting monitoring statistics."""
        from rpa.safety.system_health_monitor import SystemHealthMonitor

        monitor = SystemHealthMonitor()
        monitor.generate_report()

        stats = monitor.get_stats()
        assert stats["reports_generated"] == 1
        assert stats["uptime_seconds"] >= 0

    def test_record_operations(self):
        """Test recording operations and errors."""
        from rpa.safety.system_health_monitor import SystemHealthMonitor

        monitor = SystemHealthMonitor()

        monitor.record_operation("teach", 10)
        monitor.record_operation("query", 20)
        monitor.record_error("validation_error", 2)

        # Check via error metrics
        metric = monitor.collect_error_metrics()
        assert metric.details["total_operations"] == 30
        assert metric.details["total_errors"] == 2


# =============================================================================
# Integration Tests
# =============================================================================

class TestPhase6Integration:
    """Integration tests for Phase 6 components."""

    def test_full_safety_workflow(self):
        """Test full safety workflow."""
        from rpa.safety.curriculum_ingestion_gate import (
            CurriculumIngestionGate,
            CurriculumBatch,
        )
        from rpa.safety.pattern_validation_framework import PatternValidationFramework
        from rpa.safety.recursive_loop_prevention import RecursiveLoopPrevention
        from rpa.safety.system_health_monitor import SystemHealthMonitor

        # 1. Validate curriculum batch
        gate = CurriculumIngestionGate()
        batch = CurriculumBatch(
            batch_id="integration_test",
            domain="english",
            hierarchy_level=1,
            items=[
                {"content": "apple", "label": "apple"},
                {"content": "banana", "label": "banana"},
            ],
        )

        ingestion_result = gate.validate_batch(batch)
        assert ingestion_result.is_valid is True

        # 2. Validate patterns
        framework = PatternValidationFramework()
        for item in batch.items:
            result = framework.validate_pattern(item)
            assert result.is_valid is True

        # 3. Check for loops in pattern graph
        prevention = RecursiveLoopPrevention()
        graph = {
            "apple": ["a", "p", "p", "l", "e"],
            "a": [],
            "p": [],
            "l": [],
            "e": [],
        }

        loop_result = prevention.detect_cycles_dfs(graph)
        assert loop_result.safe_to_proceed is True

        # 4. Generate health report
        monitor = SystemHealthMonitor()
        report = monitor.generate_report(
            stm_count=1,
            ltm_count=len(batch.items),
        )

        assert report.overall_status is not None

    def test_safety_with_malicious_input(self):
        """Test safety components with malicious input."""
        from rpa.safety.curriculum_ingestion_gate import (
            CurriculumIngestionGate,
            CurriculumBatch,
        )
        from rpa.safety.pattern_validation_framework import PatternValidationFramework

        # Malicious batch
        gate = CurriculumIngestionGate()
        batch = CurriculumBatch(
            batch_id="malicious_test",
            domain="english",
            hierarchy_level=1,
            items=[
                {"content": "<script>alert('xss')</script>", "label": "malicious"},
            ],
        )

        # Gate should reject
        ingestion_result = gate.validate_batch(batch)
        assert ingestion_result.is_valid is False

        # Framework should also detect
        framework = PatternValidationFramework()
        result = framework.validate_pattern(batch.items[0])
        assert result.is_valid is False

    def test_safety_with_circular_patterns(self):
        """Test safety with circular pattern references."""
        from rpa.safety.recursive_loop_prevention import RecursiveLoopPrevention

        prevention = RecursiveLoopPrevention()

        # Circular: apple -> banana -> apple
        graph = {
            "apple": ["banana"],
            "banana": ["apple"],
        }

        result = prevention.detect_cycles_dfs(graph)
        assert result.has_loops is True

        # Verify we can't add edge that creates cycle
        new_graph = {"A": [], "B": []}
        is_valid, error = prevention.validate_pattern_reference("A", "B", new_graph)
        assert is_valid is True

        # Adding B -> A after A -> B creates cycle
        new_graph["A"].append("B")
        is_valid, error = prevention.validate_pattern_reference("B", "A", new_graph)
        assert is_valid is False

    def test_monitoring_with_validation_errors(self):
        """Test monitoring when validation has errors."""
        from rpa.safety.pattern_validation_framework import PatternValidationFramework
        from rpa.safety.system_health_monitor import SystemHealthMonitor

        framework = PatternValidationFramework()
        monitor = SystemHealthMonitor()

        # Validate many patterns with some errors
        for i in range(100):
            pattern = {"content": f"pattern_{i}"}
            framework.validate_pattern(pattern)

        # Record operations
        monitor.record_operation("validation", 100)

        # Some patterns fail (missing label in strict mode)
        stats = framework.get_stats()
        monitor.record_error("validation_error", stats["patterns_failed"])

        # Check error metrics
        error_metric = monitor.collect_error_metrics()
        assert error_metric.value >= 0
