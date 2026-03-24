"""
RPA Closed-Loop Intelligence Engine

This package provides the closed-loop learning components that enable
the RPA system to improve itself based on real-world outcomes.

Components:
- OutcomeEvaluator: Unified outcome scoring and evaluation
- ReinforcementTracker: Pattern strength, decay, and reinforcement
- PatternMutator: Version, fix, and deprecate patterns
- SelfQuestioningGate: Pre-output confidence checks
- RetryEngine: Goal-driven retry with mutation loop
- MemoryEvolution: Pattern origin, version, failure, and lineage tracking

The closed-loop works as follows:
1. Pattern is used → Outcome is generated
2. OutcomeEvaluator scores the outcome
3. ReinforcementTracker updates pattern strength
4. PatternMutator creates new versions or deprecates as needed
5. SelfQuestioningGate checks confidence before next use
6. RetryEngine executes Attempt → Sandbox → Evaluate → Mutate → Retry loop
7. MemoryEvolution tracks complete pattern history
8. Updated patterns feed back into the system

This creates a self-improving organism, not just a static knowledge store.
"""

from rpa.closed_loop.outcome_evaluator import (
    OutcomeEvaluator,
    Outcome,
    OutcomeType,
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
    PatternVersion,
)
from rpa.closed_loop.self_questioning_gate import (
    SelfQuestioningGate,
    SelfQuestioningResult,
    QuestionResult,
    QuestionType,
    ConfidenceLevel,
)
from rpa.closed_loop.retry_engine import (
    RetryEngine,
    RetryChain,
    RetryAttempt,
    RetryStrategy,
    RetryTrigger,
    RetryConfig,
)
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

__all__ = [
    # Outcome Evaluator
    "OutcomeEvaluator",
    "Outcome",
    "OutcomeType",
    # Reinforcement Tracker
    "ReinforcementTracker",
    "ReinforcementSignal",
    "ReinforcementRecord",
    "PatternStrength",
    # Pattern Mutator
    "PatternMutator",
    "MutationType",
    "PatternVersion",
    # Self Questioning Gate
    "SelfQuestioningGate",
    "SelfQuestioningResult",
    "QuestionResult",
    "QuestionType",
    "ConfidenceLevel",
    # Retry Engine
    "RetryEngine",
    "RetryChain",
    "RetryAttempt",
    "RetryStrategy",
    "RetryTrigger",
    "RetryConfig",
    # Memory Evolution
    "MemoryEvolution",
    "PatternOrigin",
    "VersionRecord",
    "FailureRecord",
    "UsageSnapshot",
    "PatternLineage",
    "EvolutionEvent",
    "OriginType",
]
