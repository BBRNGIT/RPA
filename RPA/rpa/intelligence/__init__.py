"""
RPA Intelligence Module - Closed-Loop Learning Engine.

This module provides the self-improving intelligence layer for RPA:
- OutcomeEvaluator: Classify every action result
- ReinforcementTracker: Track pattern usage and decay
- PatternMutator: Version, fix, and deprecate patterns
- SelfQuestioningGate: Pre-output validation
- RetryEngine: Goal-driven retry loop
- MemoryEvolution: Track pattern evolution
- AbstractionCompressor: Cluster similar patterns
"""

from .outcome_evaluator import OutcomeEvaluator, Outcome, OutcomeType
from .reinforcement_tracker import ReinforcementTracker, ReinforcementRecord
from .pattern_mutator import PatternMutator, PatternVersion, MutationType

__all__ = [
    "OutcomeEvaluator",
    "Outcome",
    "OutcomeType",
    "ReinforcementTracker",
    "ReinforcementRecord",
    "PatternMutator",
    "PatternVersion",
    "MutationType",
]
