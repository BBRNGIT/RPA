"""
RPA Validation Module - Consolidation reporting, validation, and knowledge integrity.

This module provides:
- ConsolidationReporter: Detailed validation reporting
- Validator: Pattern structure validation
- KnowledgeIntegrity: Truth management and contradiction detection
- TruthTracker: Track truth value changes over time
"""

from .reporter import ConsolidationReporter
from .validator import Validator, ValidationResult
from .knowledge_integrity import (
    KnowledgeIntegrity,
    Fact,
    Contradiction,
    TruthTracker,
)

__all__ = [
    # Reporting
    "ConsolidationReporter",

    # Validation
    "Validator",
    "ValidationResult",

    # Knowledge Integrity
    "KnowledgeIntegrity",
    "Fact",
    "Contradiction",
    "TruthTracker",
]
