"""
Goal-Driven Retry Engine - Attempt → Sandbox → Evaluate → Mutate → Retry loop.

This is the core execution engine for the closed-loop intelligence system.
It implements the iterative improvement cycle:

1. ATTEMPT: Try to execute a pattern or solve a problem
2. SANDBOX: Execute safely in isolated environment
3. EVALUATE: Assess the outcome using OutcomeEvaluator
4. MUTATE: If failed, generate mutations using PatternMutator
5. RETRY: Try again with mutated pattern

Key features:
- Configurable max retries
- Retry strategies based on failure types
- Chain tracking for learning
- Exponential backoff
- Goal-driven (target outcome drives retries)

This implements the Epic requirement: "Goal-Driven Retry Engine: 
Attempt → Sandbox → Evaluate → Mutate → Retry loop."
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Set
import uuid
import logging
import time
import math

from rpa.core.graph import Node, PatternGraph
from rpa.core.node import NodeType
from rpa.memory.ltm import LongTermMemory
from rpa.execution.code_sandbox import CodeSandbox, ExecutionResult
from rpa.closed_loop.outcome_evaluator import (
    OutcomeEvaluator,
    Outcome,
    OutcomeType,
)
from rpa.closed_loop.reinforcement_tracker import (
    ReinforcementTracker,
    ReinforcementSignal,
    ReinforcementRecord,
)
from rpa.closed_loop.pattern_mutator import (
    PatternMutator,
    MutationType,
    PatternVersion,
)
from rpa.closed_loop.self_questioning_gate import (
    SelfQuestioningGate,
    SelfQuestioningResult,
    ConfidenceLevel,
)

logger = logging.getLogger(__name__)


class RetryStrategy(Enum):
    """Strategies for retrying failed executions."""
    DIRECT_RETRY = "direct_retry"           # Try same pattern again
    MUTATE_FIX = "mutate_fix"               # Apply fix mutation
    MUTATE_ENHANCE = "mutate_enhance"       # Apply enhancement mutation
    ALTERNATIVE_PATTERN = "alternative"     # Try alternative pattern
    BACKTRACK = "backtrack"                 # Go back to previous version
    ESCALATE = "escalate"                   # Escalate to human/system
    ABANDON = "abandon"                     # Stop retrying


class RetryTrigger(Enum):
    """What triggers a retry."""
    EXECUTION_FAILURE = "execution_failure"
    VALIDATION_FAILURE = "validation_failure"
    LOW_CONFIDENCE = "low_confidence"
    GAP_DETECTED = "gap_detected"
    USER_REJECTION = "user_rejection"
    TIMEOUT = "timeout"


@dataclass
class RetryAttempt:
    """Represents a single retry attempt in the chain."""
    attempt_id: str
    attempt_number: int
    pattern_id: str
    pattern_content: str

    # Execution
    execution_result: Optional[ExecutionResult] = None
    outcome: Optional[Outcome] = None

    # Decision
    strategy_used: Optional[RetryStrategy] = None
    trigger: Optional[RetryTrigger] = None
    should_retry: bool = False

    # Timing
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    execution_time_ms: float = 0.0

    # Mutation info
    mutation_applied: Optional[str] = None
    mutated_pattern_id: Optional[str] = None

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "attempt_id": self.attempt_id,
            "attempt_number": self.attempt_number,
            "pattern_id": self.pattern_id,
            "pattern_content": self.pattern_content[:200] if self.pattern_content else None,
            "execution_result": self.execution_result.to_dict() if self.execution_result else None,
            "outcome": self.outcome.to_dict() if self.outcome else None,
            "strategy_used": self.strategy_used.value if self.strategy_used else None,
            "trigger": self.trigger.value if self.trigger else None,
            "should_retry": self.should_retry,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "execution_time_ms": self.execution_time_ms,
            "mutation_applied": self.mutation_applied,
            "mutated_pattern_id": self.mutated_pattern_id,
            "metadata": self.metadata,
        }


@dataclass
class RetryChain:
    """
    Represents a complete retry chain for a goal.

    Tracks all attempts, strategies used, and final outcome.
    """
    chain_id: str
    goal: str
    domain: str

    # Initial state
    initial_pattern_id: Optional[str] = None
    expected_output: Optional[str] = None

    # Attempts
    attempts: List[RetryAttempt] = field(default_factory=list)

    # Final state
    final_outcome: Optional[Outcome] = None
    success: bool = False
    total_attempts: int = 0

    # Timing
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    total_time_ms: float = 0.0

    # Learning
    patterns_created: List[str] = field(default_factory=list)
    patterns_deprecated: List[str] = field(default_factory=list)
    learning_notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "chain_id": self.chain_id,
            "goal": self.goal,
            "domain": self.domain,
            "initial_pattern_id": self.initial_pattern_id,
            "expected_output": self.expected_output,
            "attempts": [a.to_dict() for a in self.attempts],
            "final_outcome": self.final_outcome.to_dict() if self.final_outcome else None,
            "success": self.success,
            "total_attempts": self.total_attempts,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "total_time_ms": self.total_time_ms,
            "patterns_created": self.patterns_created,
            "patterns_deprecated": self.patterns_deprecated,
            "learning_notes": self.learning_notes,
        }


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_attempts: int = 5
    backoff_base_ms: float = 100.0
    backoff_multiplier: float = 2.0
    max_backoff_ms: float = 5000.0
    timeout_seconds: float = 10.0

    # Strategy preferences
    prefer_mutation: bool = True
    allow_backtrack: bool = True
    allow_alternatives: bool = True

    # Success thresholds
    success_score_threshold: float = 0.8
    confidence_threshold: float = 0.5

    # Early termination
    stop_on_deprecation: bool = True
    stop_on_gap: bool = False  # Gaps might be fillable


class RetryEngine:
    """
    Goal-Driven Retry Engine for closed-loop learning.

    This engine implements the core retry loop that enables
    self-improvement through iterative attempts.

    The flow:
    1. Define a goal (expected outcome)
    2. Attempt to achieve it with a pattern
    3. Execute in sandbox
    4. Evaluate the outcome
    5. If failed and retries available:
       a. Determine retry strategy
       b. Apply mutation if needed
       c. Retry with new approach
    6. Learn from the chain

    Example:
        engine = RetryEngine(
            sandbox=code_sandbox,
            evaluator=outcome_evaluator,
            mutator=pattern_mutator,
        )

        result = engine.execute_with_retry(
            pattern=my_pattern,
            goal="Return the sum of two numbers",
            input_data={"a": 5, "b": 3},
            expected_output="8",
        )

        if result.success:
            print(f"Succeeded after {result.total_attempts} attempts")
        else:
            print(f"Failed after {result.total_attempts} attempts")
    """

    # Strategy selection based on outcome
    OUTCOME_STRATEGIES = {
        OutcomeType.FAILURE: [RetryStrategy.MUTATE_FIX, RetryStrategy.ALTERNATIVE_PATTERN],
        OutcomeType.PARTIAL: [RetryStrategy.MUTATE_ENHANCE, RetryStrategy.DIRECT_RETRY],
        OutcomeType.GAP: [RetryStrategy.MUTATE_ENHANCE, RetryStrategy.ESCALATE],
        OutcomeType.ERROR: [RetryStrategy.BACKTRACK, RetryStrategy.ABANDON],  # Unrecoverable errors
        OutcomeType.UNCERTAIN: [RetryStrategy.DIRECT_RETRY, RetryStrategy.ESCALATE],
    }

    def __init__(
        self,
        sandbox: Optional[CodeSandbox] = None,
        evaluator: Optional[OutcomeEvaluator] = None,
        mutator: Optional[PatternMutator] = None,
        reinforcement: Optional[ReinforcementTracker] = None,
        questioning_gate: Optional[SelfQuestioningGate] = None,
        ltm: Optional[LongTermMemory] = None,
        config: Optional[RetryConfig] = None,
    ):
        """
        Initialize the RetryEngine.

        Args:
            sandbox: CodeSandbox for safe execution
            evaluator: OutcomeEvaluator for assessing results
            mutator: PatternMutator for creating mutations
            reinforcement: ReinforcementTracker for strength updates
            questioning_gate: SelfQuestioningGate for pre-checks
            ltm: LongTermMemory for pattern storage
            config: RetryConfig for behavior settings
        """
        self.sandbox = sandbox or CodeSandbox()
        self.evaluator = evaluator or OutcomeEvaluator()
        self.mutator = mutator or PatternMutator(ltm=ltm)
        self.reinforcement = reinforcement or ReinforcementTracker(ltm=ltm)
        self.questioning_gate = questioning_gate or SelfQuestioningGate(
            ltm=ltm,
            outcome_evaluator=self.evaluator,
            reinforcement_tracker=self.reinforcement,
            pattern_mutator=self.mutator,
        )
        self.ltm = ltm
        self.config = config or RetryConfig()

        # Chain history
        self._chains: Dict[str, RetryChain] = {}
        self._active_chains: Set[str] = set()
        self._max_history = 500

        # Statistics
        self._stats = {
            "total_chains": 0,
            "successful_chains": 0,
            "failed_chains": 0,
            "total_attempts": 0,
            "by_strategy": {s.value: 0 for s in RetryStrategy},
            "avg_attempts_success": 0.0,
            "avg_attempts_failure": 0.0,
            "mutations_applied": 0,
            "patterns_created": 0,
        }

    def execute_with_retry(
        self,
        pattern: Node,
        goal: str,
        domain: Optional[str] = None,
        input_data: Optional[Dict[str, Any]] = None,
        expected_output: Optional[str] = None,
        input_context: Optional[str] = None,
        config_override: Optional[RetryConfig] = None,
        on_attempt: Optional[Callable[[RetryAttempt], None]] = None,
    ) -> RetryChain:
        """
        Execute a pattern with automatic retry on failure.

        This is the main entry point for the retry engine.

        Args:
            pattern: The pattern to execute
            goal: The goal/outcome we're trying to achieve
            domain: Domain context (defaults to pattern.domain)
            input_data: Input data for execution
            expected_output: Expected output for comparison
            input_context: Context string describing the input
            config_override: Override default config for this execution
            on_attempt: Optional callback after each attempt

        Returns:
            RetryChain with complete history and final outcome
        """
        config = config_override or self.config
        domain = domain or pattern.domain

        # Create chain
        chain_id = f"chain_{uuid.uuid4().hex[:8]}"
        chain = RetryChain(
            chain_id=chain_id,
            goal=goal,
            domain=domain,
            initial_pattern_id=pattern.node_id,
            expected_output=expected_output,
        )

        self._chains[chain_id] = chain
        self._active_chains.add(chain_id)
        self._stats["total_chains"] += 1

        logger.info(f"Starting retry chain {chain_id} for goal: {goal[:50]}...")

        current_pattern = pattern
        attempt_number = 0

        while attempt_number < config.max_attempts:
            attempt_number += 1

            # Create attempt record
            attempt = RetryAttempt(
                attempt_id=f"attempt_{chain_id}_{attempt_number}",
                attempt_number=attempt_number,
                pattern_id=current_pattern.node_id,
                pattern_content=current_pattern.content,
            )

            chain.attempts.append(attempt)
            self._stats["total_attempts"] += 1

            # Pre-check with self-questioning gate
            if attempt_number > 1:  # Skip on first attempt (already checked)
                gate_result = self.questioning_gate.question(
                    pattern_id=current_pattern.node_id,
                    domain=domain,
                    context={"goal": goal, "attempt": attempt_number},
                )

                if not gate_result.can_proceed:
                    logger.warning(
                        f"Attempt {attempt_number}: Self-questioning gate blocked execution"
                    )
                    attempt.should_retry = False
                    attempt.trigger = RetryTrigger.LOW_CONFIDENCE
                    attempt.metadata["gate_result"] = gate_result.to_dict()

                    # Try to find alternative if allowed
                    if config.allow_alternatives and attempt_number < config.max_attempts:
                        alt_pattern = self._find_alternative_pattern(
                            current_pattern, domain, goal
                        )
                        if alt_pattern:
                            current_pattern = alt_pattern
                            attempt.should_retry = True
                            attempt.strategy_used = RetryStrategy.ALTERNATIVE_PATTERN
                            attempt.metadata["alternative_pattern_id"] = alt_pattern.node_id
                            continue

                    break

            # Execute in sandbox
            attempt.started_at = datetime.now()

            try:
                execution_result = self._execute_pattern(
                    current_pattern,
                    input_data,
                    config.timeout_seconds,
                )
                attempt.execution_result = execution_result
            except Exception as e:
                logger.error(f"Attempt {attempt_number}: Execution error: {e}")
                execution_result = ExecutionResult(
                    success=False,
                    output="",
                    error=str(e),
                    error_type=type(e).__name__,
                )
                attempt.execution_result = execution_result

            attempt.completed_at = datetime.now()
            attempt.execution_time_ms = (
                attempt.completed_at - attempt.started_at
            ).total_seconds() * 1000

            # Evaluate outcome using closed_loop OutcomeEvaluator interface
            outcome = self.evaluator.evaluate(
                pattern_id=current_pattern.node_id,
                domain=domain,
                action="execute",
                result=execution_result.output if execution_result.success else execution_result.error or "Execution failed",
                sandbox_result={
                    "success": execution_result.success,
                    "output": execution_result.output,
                    "error": execution_result.error,
                    "error_type": execution_result.error_type,
                },
                error_message=execution_result.error if not execution_result.success else None,
                error_type=execution_result.error_type if not execution_result.success else None,
                code_context=current_pattern.content,
                retry_count=attempt_number - 1,
            )
            attempt.outcome = outcome

            # Update reinforcement
            self.reinforcement.process_outcome(outcome)

            # Check if we succeeded
            if outcome.outcome_type == OutcomeType.SUCCESS:
                chain.success = True
                chain.final_outcome = outcome
                attempt.should_retry = False
                self._stats["successful_chains"] += 1
                logger.info(
                    f"Chain {chain_id} succeeded on attempt {attempt_number}"
                )
                break

            # Determine retry strategy
            strategy, trigger = self._determine_strategy(
                outcome, attempt_number, config
            )
            attempt.strategy_used = strategy
            attempt.trigger = trigger

            # Check if we should stop
            if strategy == RetryStrategy.ABANDON:
                attempt.should_retry = False
                logger.info(f"Chain {chain_id}: Abandoning after attempt {attempt_number}")
                break

            if strategy == RetryStrategy.ESCALATE:
                attempt.should_retry = False
                chain.learning_notes.append("Escalation required")
                logger.info(f"Chain {chain_id}: Escalating after attempt {attempt_number}")
                break

            # Check deprecation
            if config.stop_on_deprecation and outcome.should_deprecate:
                attempt.should_retry = False
                chain.patterns_deprecated.append(current_pattern.node_id)
                # Let the mutator handle deprecation through process_outcome
                self.mutator.process_outcome(outcome)
                chain.learning_notes.append(f"Pattern {current_pattern.node_id} deprecated")
                logger.info(f"Chain {chain_id}: Pattern deprecated")
                break

            # Check if max attempts reached
            if attempt_number >= config.max_attempts:
                attempt.should_retry = False
                logger.info(f"Chain {chain_id}: Max attempts ({config.max_attempts}) reached")
                break

            # Apply retry strategy
            next_pattern = self._apply_strategy(
                strategy=strategy,
                pattern=current_pattern,
                outcome=outcome,
                attempt=attempt,
                chain=chain,
            )

            if next_pattern:
                attempt.should_retry = True
                attempt.mutated_pattern_id = next_pattern.node_id
                current_pattern = next_pattern
                self._stats["mutations_applied"] += 1

                # Backoff before next attempt
                backoff_ms = self._calculate_backoff(attempt_number, config)
                if backoff_ms > 0:
                    time.sleep(backoff_ms / 1000.0)
            else:
                attempt.should_retry = False
                logger.warning(
                    f"Chain {chain_id}: Could not apply strategy {strategy.value}"
                )
                break

            # Callback if provided
            if on_attempt:
                on_attempt(attempt)

        # Finalize chain
        chain.total_attempts = attempt_number
        chain.completed_at = datetime.now()
        chain.total_time_ms = (
            chain.completed_at - chain.started_at
        ).total_seconds() * 1000

        if not chain.success:
            chain.final_outcome = chain.attempts[-1].outcome if chain.attempts else None
            self._stats["failed_chains"] += 1

        # Update statistics
        self._update_stats(chain)

        # Cleanup
        self._active_chains.discard(chain_id)

        # Trim history
        if len(self._chains) > self._max_history:
            self._trim_history()

        return chain

    def execute_code_with_retry(
        self,
        code: str,
        goal: str,
        domain: str = "coding",
        input_data: Optional[Dict[str, Any]] = None,
        expected_output: Optional[str] = None,
        config_override: Optional[RetryConfig] = None,
    ) -> RetryChain:
        """
        Execute code with retry, creating a temporary pattern.

        Convenience method for executing code directly without
        an existing pattern node.

        Args:
            code: The code to execute
            goal: The goal we're trying to achieve
            domain: Domain context
            input_data: Input data for execution
            expected_output: Expected output
            config_override: Override default config

        Returns:
            RetryChain with complete history
        """
        # Create a temporary pattern node
        temp_pattern = Node.create_pattern(
            label=f"temp_{uuid.uuid4().hex[:8]}",
            content=code,
            hierarchy_level=1,
            domain=domain,
        )
        temp_pattern.metadata["temporary"] = True

        return self.execute_with_retry(
            pattern=temp_pattern,
            goal=goal,
            domain=domain,
            input_data=input_data,
            expected_output=expected_output,
            config_override=config_override,
        )

    def _execute_pattern(
        self,
        pattern: Node,
        input_data: Optional[Dict[str, Any]],
        timeout: float,
    ) -> ExecutionResult:
        """Execute a pattern in the sandbox."""
        code = pattern.content

        # Wrap execution with input data if provided
        if input_data:
            # Create wrapper that injects input
            input_setup = "\n".join(
                f"{k} = {repr(v)}"
                for k, v in input_data.items()
            )
            code = f"{input_setup}\n\n{code}"

        return self.sandbox.execute(code, timeout_override=timeout)

    def _determine_strategy(
        self,
        outcome: Outcome,
        attempt_number: int,
        config: RetryConfig,
    ) -> tuple[RetryStrategy, RetryTrigger]:
        """
        Determine the retry strategy based on outcome.

        Returns:
            Tuple of (strategy, trigger)
        """
        outcome_type = outcome.outcome_type

        # Determine trigger
        if outcome_type == OutcomeType.FAILURE:
            trigger = RetryTrigger.EXECUTION_FAILURE
        elif outcome_type == OutcomeType.ERROR:
            trigger = RetryTrigger.EXECUTION_FAILURE  # Map ERROR to execution failure
        elif outcome_type == OutcomeType.GAP:
            trigger = RetryTrigger.GAP_DETECTED
        elif outcome_type == OutcomeType.UNCERTAIN:
            trigger = RetryTrigger.LOW_CONFIDENCE
        else:
            trigger = RetryTrigger.EXECUTION_FAILURE

        # Get strategies for this outcome type
        strategies = self.OUTCOME_STRATEGIES.get(
            outcome_type,
            [RetryStrategy.MUTATE_FIX, RetryStrategy.ABANDON]
        )

        # Filter based on config and attempt number
        if not config.prefer_mutation and RetryStrategy.MUTATE_FIX in strategies:
            strategies = [s for s in strategies if s != RetryStrategy.MUTATE_FIX]

        if not config.allow_backtrack and RetryStrategy.BACKTRACK in strategies:
            strategies = [s for s in strategies if s != RetryStrategy.BACKTRACK]

        if not config.allow_alternatives and RetryStrategy.ALTERNATIVE_PATTERN in strategies:
            strategies = [s for s in strategies if s != RetryStrategy.ALTERNATIVE_PATTERN]

        # On later attempts, prefer more aggressive strategies
        if attempt_number >= config.max_attempts - 1:
            if RetryStrategy.ESCALATE not in strategies:
                strategies.append(RetryStrategy.ESCALATE)

        # Select first viable strategy
        for strategy in strategies:
            if self._can_apply_strategy(strategy, outcome):
                return strategy, trigger

        # Fallback
        return RetryStrategy.ABANDON, trigger

    def _can_apply_strategy(self, strategy: RetryStrategy, outcome: Outcome) -> bool:
        """Check if a strategy can be applied."""
        if strategy == RetryStrategy.DIRECT_RETRY:
            return True  # Always possible

        if strategy == RetryStrategy.MUTATE_FIX:
            return outcome.should_mutate and outcome.error is not None

        if strategy == RetryStrategy.MUTATE_ENHANCE:
            return outcome.should_mutate

        if strategy == RetryStrategy.BACKTRACK:
            # Check if there's a previous version
            return True  # Will return None if no previous version

        if strategy == RetryStrategy.ALTERNATIVE_PATTERN:
            return True  # Will return None if no alternative found

        if strategy in (RetryStrategy.ESCALATE, RetryStrategy.ABANDON):
            return True

        return False

    def _apply_strategy(
        self,
        strategy: RetryStrategy,
        pattern: Node,
        outcome: Outcome,
        attempt: RetryAttempt,
        chain: RetryChain,
    ) -> Optional[Node]:
        """
        Apply a retry strategy to get a new pattern.

        Returns:
            New pattern to try, or None if strategy couldn't be applied
        """
        self._stats["by_strategy"][strategy.value] += 1

        if strategy == RetryStrategy.DIRECT_RETRY:
            # Just try the same pattern again
            attempt.mutation_applied = "direct_retry"
            return pattern

        if strategy == RetryStrategy.MUTATE_FIX:
            # Apply fix mutation via process_outcome
            mutation_record = self.mutator.process_outcome(outcome)
            if mutation_record:
                attempt.mutation_applied = "fix"
                attempt.mutated_pattern_id = outcome.pattern_id
                chain.patterns_created.append(outcome.pattern_id)
                self._stats["patterns_created"] += 1
                chain.learning_notes.append(
                    f"Applied fix mutation: {mutation_record.mutation_type.value}"
                )
                # Return the same pattern since mutation updates the version in place
                return pattern
            return None

        if strategy == RetryStrategy.MUTATE_ENHANCE:
            # Apply enhancement mutation
            enhancement = self._suggest_enhancement(outcome, pattern)
            if enhancement:
                # For enhancement, we try process_outcome which will handle the mutation
                attempt.mutation_applied = "enhancement"
                chain.learning_notes.append(f"Suggested enhancement: {enhancement}")
                # Return same pattern with enhancement suggestion in metadata
                pattern.metadata["enhancement_suggestion"] = enhancement
                return pattern
            return None

        if strategy == RetryStrategy.BACKTRACK:
            # Try previous version
            history = self.mutator.get_version_history(pattern.node_id)
            if len(history) > 1:
                # Get second-to-last version
                prev_version = history[-2]
                prev_pattern = Node.create_pattern(
                    label=prev_version.label,
                    content=prev_version.content,
                    hierarchy_level=pattern.hierarchy_level,
                    domain=pattern.domain,
                )
                prev_pattern.node_id = prev_version.pattern_id
                attempt.mutation_applied = "backtrack"
                chain.learning_notes.append(
                    f"Backtracked to version {prev_version.version_number}"
                )
                return prev_pattern
            return None

        if strategy == RetryStrategy.ALTERNATIVE_PATTERN:
            # Find alternative pattern
            alt = self._find_alternative_pattern(pattern, chain.domain, chain.goal)
            if alt:
                attempt.mutation_applied = "alternative"
                chain.learning_notes.append(
                    f"Using alternative pattern: {alt.node_id}"
                )
            return alt

        return None

    def _find_alternative_pattern(
        self,
        pattern: Node,
        domain: str,
        goal: str,
    ) -> Optional[Node]:
        """Find an alternative pattern that might work better."""
        if not self.ltm:
            return None

        # Find patterns in the same domain
        domain_patterns = self.ltm.find_by_domain(domain)

        # Filter out the current pattern and deprecated ones
        alternatives = [
            p for p in domain_patterns
            if p.node_id != pattern.node_id
            and not p.metadata.get("deprecated", False)
        ]

        # Sort by strength/success rate
        alternatives.sort(
            key=lambda p: self.reinforcement.get_strength(p.node_id).strength
            if self.reinforcement.get_strength(p.node_id) else 0,
            reverse=True,
        )

        # Return the strongest alternative
        return alternatives[0] if alternatives else None

    def _suggest_enhancement(self, outcome: Outcome, pattern: Node) -> Optional[str]:
        """Suggest an enhancement based on the outcome."""
        if outcome.outcome_type == OutcomeType.PARTIAL:
            return "Handle edge cases and improve output quality"

        if outcome.outcome_type == OutcomeType.GAP:
            missing = outcome.metadata.get("missing_knowledge", [])
            if missing:
                return f"Add handling for: {', '.join(missing[:3])}"
            return "Add missing knowledge handling"

        if outcome.outcome_type == OutcomeType.TIMEOUT:
            return "Optimize for performance"

        return "General improvement"

    def _calculate_backoff(self, attempt_number: int, config: RetryConfig) -> float:
        """Calculate backoff time in milliseconds."""
        backoff = config.backoff_base_ms * (
            config.backoff_multiplier ** (attempt_number - 1)
        )
        return min(backoff, config.max_backoff_ms)

    def _update_stats(self, chain: RetryChain) -> None:
        """Update statistics after a chain completes."""
        if chain.success:
            # Update average attempts for success
            total_success = self._stats["successful_chains"]
            old_avg = self._stats["avg_attempts_success"]
            self._stats["avg_attempts_success"] = (
                (old_avg * (total_success - 1) + chain.total_attempts) / total_success
            )
        else:
            # Update average attempts for failure
            total_failure = self._stats["failed_chains"]
            old_avg = self._stats["avg_attempts_failure"]
            self._stats["avg_attempts_failure"] = (
                (old_avg * (total_failure - 1) + chain.total_attempts) / total_failure
            )

    def _trim_history(self) -> None:
        """Trim old chains from history."""
        # Keep most recent chains
        sorted_ids = sorted(
            self._chains.keys(),
            key=lambda x: self._chains[x].started_at,
        )
        to_remove = sorted_ids[:-self._max_history]

        for chain_id in to_remove:
            del self._chains[chain_id]

    def get_chain(self, chain_id: str) -> Optional[RetryChain]:
        """Get a specific retry chain."""
        return self._chains.get(chain_id)

    def get_recent_chains(self, limit: int = 20) -> List[RetryChain]:
        """Get recent retry chains."""
        chains = sorted(
            self._chains.values(),
            key=lambda c: c.started_at,
            reverse=True,
        )
        return chains[:limit]

    def get_successful_chains(self, limit: int = 20) -> List[RetryChain]:
        """Get successful retry chains."""
        chains = [c for c in self._chains.values() if c.success]
        chains.sort(key=lambda c: c.started_at, reverse=True)
        return chains[:limit]

    def get_failed_chains(self, limit: int = 20) -> List[RetryChain]:
        """Get failed retry chains."""
        chains = [c for c in self._chains.values() if not c.success]
        chains.sort(key=lambda c: c.started_at, reverse=True)
        return chains[:limit]

    def get_patterns_needing_improvement(self) -> List[Dict[str, Any]]:
        """
        Get patterns that frequently fail in retry chains.

        Returns:
            List of patterns with failure statistics
        """
        pattern_failures: Dict[str, Dict[str, Any]] = {}

        for chain in self._chains.values():
            for attempt in chain.attempts:
                pid = attempt.pattern_id
                if pid not in pattern_failures:
                    pattern_failures[pid] = {
                        "pattern_id": pid,
                        "total_attempts": 0,
                        "failures": 0,
                        "chain_ids": [],
                    }

                pattern_failures[pid]["total_attempts"] += 1
                if attempt.outcome and attempt.outcome.outcome_type != OutcomeType.SUCCESS:
                    pattern_failures[pid]["failures"] += 1
                    if chain.chain_id not in pattern_failures[pid]["chain_ids"]:
                        pattern_failures[pid]["chain_ids"].append(chain.chain_id)

        # Calculate failure rates and filter
        results = []
        for data in pattern_failures.values():
            if data["total_attempts"] >= 2:  # At least 2 attempts
                data["failure_rate"] = data["failures"] / data["total_attempts"]
                if data["failure_rate"] > 0.5:  # More than 50% failure
                    results.append(data)

        # Sort by failure rate
        results.sort(key=lambda x: x["failure_rate"], reverse=True)
        return results

    def get_learning_insights(self) -> Dict[str, Any]:
        """
        Get insights about learning from retry chains.

        Returns:
            Dictionary with learning insights
        """
        insights = {
            "total_chains": len(self._chains),
            "success_rate": 0.0,
            "common_failure_types": {},
            "effective_strategies": {},
            "patterns_created": 0,
            "patterns_deprecated": 0,
        }

        if not self._chains:
            return insights

        # Calculate success rate
        successful = sum(1 for c in self._chains.values() if c.success)
        insights["success_rate"] = successful / len(self._chains)

        # Count failure types
        for chain in self._chains.values():
            for attempt in chain.attempts:
                if attempt.trigger:
                    trigger = attempt.trigger.value
                    insights["common_failure_types"][trigger] = (
                        insights["common_failure_types"].get(trigger, 0) + 1
                    )

        # Count effective strategies (strategies that led to success)
        for chain in self._chains.values():
            if chain.success and len(chain.attempts) > 1:
                # The strategy that led to success
                last_strategy = chain.attempts[-2].strategy_used  # Second to last
                if last_strategy:
                    insights["effective_strategies"][last_strategy.value] = (
                        insights["effective_strategies"].get(last_strategy.value, 0) + 1
                    )

        # Count patterns
        for chain in self._chains.values():
            insights["patterns_created"] += len(chain.patterns_created)
            insights["patterns_deprecated"] += len(chain.patterns_deprecated)

        return insights

    def get_stats(self) -> Dict[str, Any]:
        """Get retry engine statistics."""
        return {
            **self._stats,
            "active_chains": len(self._active_chains),
            "history_size": len(self._chains),
            "success_rate": (
                self._stats["successful_chains"] / max(1, self._stats["total_chains"])
            ),
        }

    def export_chains(self) -> List[Dict[str, Any]]:
        """Export all chains as dictionaries."""
        return [c.to_dict() for c in self._chains.values()]

    def import_chains(self, chains: List[Dict[str, Any]]) -> int:
        """
        Import chains from dictionaries.

        Returns:
            Number of chains imported
        """
        imported = 0

        for data in chains:
            chain = RetryChain(
                chain_id=data["chain_id"],
                goal=data["goal"],
                domain=data["domain"],
                initial_pattern_id=data.get("initial_pattern_id"),
                expected_output=data.get("expected_output"),
                success=data.get("success", False),
                total_attempts=data.get("total_attempts", 0),
                total_time_ms=data.get("total_time_ms", 0),
                patterns_created=data.get("patterns_created", []),
                patterns_deprecated=data.get("patterns_deprecated", []),
                learning_notes=data.get("learning_notes", []),
            )

            # Parse timestamps
            if data.get("started_at"):
                chain.started_at = datetime.fromisoformat(data["started_at"])
            if data.get("completed_at"):
                chain.completed_at = datetime.fromisoformat(data["completed_at"])

            # Parse attempts
            for attempt_data in data.get("attempts", []):
                attempt = RetryAttempt(
                    attempt_id=attempt_data["attempt_id"],
                    attempt_number=attempt_data["attempt_number"],
                    pattern_id=attempt_data["pattern_id"],
                    pattern_content=attempt_data.get("pattern_content", ""),
                    should_retry=attempt_data.get("should_retry", False),
                    metadata=attempt_data.get("metadata", {}),
                )

                if attempt_data.get("strategy_used"):
                    attempt.strategy_used = RetryStrategy(attempt_data["strategy_used"])
                if attempt_data.get("trigger"):
                    attempt.trigger = RetryTrigger(attempt_data["trigger"])
                if attempt_data.get("mutation_applied"):
                    attempt.mutation_applied = attempt_data["mutation_applied"]
                if attempt_data.get("mutated_pattern_id"):
                    attempt.mutated_pattern_id = attempt_data["mutated_pattern_id"]

                if attempt_data.get("started_at"):
                    attempt.started_at = datetime.fromisoformat(attempt_data["started_at"])
                if attempt_data.get("completed_at"):
                    attempt.completed_at = datetime.fromisoformat(attempt_data["completed_at"])
                if attempt_data.get("execution_time_ms"):
                    attempt.execution_time_ms = attempt_data["execution_time_ms"]

                chain.attempts.append(attempt)

            self._chains[chain.chain_id] = chain
            imported += 1

        return imported
