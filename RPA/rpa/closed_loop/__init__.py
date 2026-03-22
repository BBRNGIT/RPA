"""
Closed-Loop Intelligence Engine for RPA.

This module provides the feedback and self-improvement layer that makes
RPA a learning organism rather than a static knowledge store.

Components:
- OutcomeEvaluator: Unified outcome classification
- ReinforcementTracker: Usage tracking and reinforcement signals
- PatternMutator: Pattern versioning and mutation
- SelfQuestioningGate: Pre-output validation
- RetryEngine: Goal-driven retry loop
- MemoryEvolution: Pattern evolution tracking
- AbstractionCompressor: Pattern clustering and abstraction
"""

from .outcome_evaluator import (
    OutcomeEvaluator,
    Outcome,
    OutcomeType,
    OutcomeRecord,
)
from .reinforcement_tracker import (
    ReinforcementTracker,
    ReinforcementRecord,
)
from .pattern_mutator import (
    PatternMutator,
    MutationRecord,
    MutationType,
)
from .self_questioning_gate import (
    SelfQuestioningGate,
    QuestioningResult,
)
from .retry_engine import (
    RetryEngine,
    RetryRecord,
    RetryStatus,
)

__all__ = [
    # Outcome Evaluator
    "OutcomeEvaluator",
    "Outcome",
    "OutcomeType",
    "OutcomeRecord",
    # Reinforcement Tracker
    "ReinforcementTracker",
    "ReinforcementRecord",
    # Pattern Mutator
    "PatternMutator",
    "MutationRecord",
    "MutationType",
    # Self Questioning Gate
    "SelfQuestioningGate",
    "QuestioningResult",
    # Retry Engine
    "RetryEngine",
    "RetryRecord",
    "RetryStatus",
]
