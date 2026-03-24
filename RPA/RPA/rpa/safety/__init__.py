"""
RPA Safety Module - System Integrity & Safety Components.

This module provides safety mechanisms for the RPA system:
- CurriculumIngestionGate: Validate curriculum before ingestion
- RecursiveLoopPrevention: Detect and prevent infinite loops in pattern graphs
- PatternValidationFramework: Comprehensive pattern validation
- SystemHealthMonitor: Track system health metrics
"""

from rpa.safety.curriculum_ingestion_gate import (
    CurriculumIngestionGate,
    IngestionResult,
    CurriculumBatch,
)
from rpa.safety.recursive_loop_prevention import (
    RecursiveLoopPrevention,
    LoopDetectionResult,
    LoopInfo,
)
from rpa.safety.pattern_validation_framework import (
    PatternValidationFramework,
    ValidationResult,
    ValidationRule,
    RuleSeverity,
)
from rpa.safety.system_health_monitor import (
    SystemHealthMonitor,
    HealthMetric,
    HealthStatus,
    HealthReport,
)

__all__ = [
    # Curriculum Ingestion Gate
    "CurriculumIngestionGate",
    "IngestionResult",
    "CurriculumBatch",
    # Recursive Loop Prevention
    "RecursiveLoopPrevention",
    "LoopDetectionResult",
    "LoopInfo",
    # Pattern Validation Framework
    "PatternValidationFramework",
    "ValidationResult",
    "ValidationRule",
    "RuleSeverity",
    # System Health Monitor
    "SystemHealthMonitor",
    "HealthMetric",
    "HealthStatus",
    "HealthReport",
]
