"""
RPA Self-Improvement Orchestrator

Unified entry point for the closed-loop self-improvement system.
Coordinates all learning, evaluation, mutation, and evolution components.

Ticket: SI-001
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict

# Core memory
from rpa.memory.ltm import LongTermMemory
from rpa.memory.stm import ShortTermMemory
from rpa.memory.episodic import EpisodicMemory

# Closed-loop components
from rpa.closed_loop.outcome_evaluator import (
    OutcomeEvaluator, Outcome, OutcomeType, OutcomeSeverity
)
from rpa.closed_loop.reinforcement_tracker import (
    ReinforcementTracker, ReinforcementSignal, PatternStrength
)
from rpa.closed_loop.pattern_mutator import (
    PatternMutator, MutationType, MutationRecord, PatternVersion
)
from rpa.closed_loop.self_questioning_gate import (
    SelfQuestioningGate, ConfidenceLevel, SelfQuestioningResult
)
from rpa.closed_loop.retry_engine import (
    RetryEngine, RetryConfig, RetryChain, RetryStrategy
)
from rpa.closed_loop.memory_evolution import (
    MemoryEvolution, EvolutionEvent, OriginType, PatternLineage
)

# Supporting components
from rpa.execution.code_sandbox import CodeSandbox
from rpa.inquiry.gap_detector import GapDetector
from rpa.learning.correction_analyzer import CorrectionAnalyzer
from rpa.validation.validator import Validator

logger = logging.getLogger(__name__)


@dataclass
class SelfImprovementConfig:
    """Configuration for self-improvement behavior."""
    
    # Confidence thresholds
    confidence_threshold: float = 0.7
    low_confidence_threshold: float = 0.3
    high_confidence_threshold: float = 0.8
    
    # Mutation settings
    mutation_rate: float = 0.1
    max_mutations_per_cycle: int = 10
    enable_auto_mutation: bool = True
    
    # Reinforcement settings
    reinforcement_decay: float = 0.05
    min_strength_threshold: float = 0.2
    strong_pattern_threshold: float = 0.7
    
    # Retry settings
    max_retry_attempts: int = 3
    retry_backoff_factor: float = 1.5
    
    # Cycle settings
    patterns_per_cycle: int = 50
    gap_closure_priority: bool = True
    
    # Persistence
    auto_save: bool = True
    save_interval_cycles: int = 5


@dataclass
class ImprovementCycle:
    """Record of a single self-improvement cycle."""
    
    cycle_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    
    # Stats
    patterns_evaluated: int = 0
    patterns_reinforced: int = 0
    patterns_decayed: int = 0
    patterns_mutated: int = 0
    gaps_detected: int = 0
    gaps_closed: int = 0
    
    # Outcomes
    successful_mutations: int = 0
    failed_mutations: int = 0
    confidence_improvements: int = 0
    
    # Errors
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['start_time'] = self.start_time.isoformat()
        data['end_time'] = self.end_time.isoformat() if self.end_time else None
        return data
    
    @property
    def duration_seconds(self) -> float:
        """Calculate cycle duration."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0


@dataclass
class SystemHealth:
    """Health metrics for the self-improvement system."""
    
    total_patterns: int = 0
    strong_patterns: int = 0
    weak_patterns: int = 0
    deprecated_patterns: int = 0
    
    avg_pattern_strength: float = 0.0
    avg_confidence: float = 0.0
    
    pending_mutations: int = 0
    open_gaps: int = 0
    
    recent_success_rate: float = 0.0
    learning_velocity: float = 0.0  # patterns improved per hour
    
    last_cycle_time: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        data = asdict(self)
        data['last_cycle_time'] = self.last_cycle_time.isoformat() if self.last_cycle_time else None
        return data


class SelfImprovementOrchestrator:
    """
    Unified orchestrator for the RPA self-improvement system.
    
    Coordinates:
    - Outcome evaluation
    - Pattern reinforcement and decay
    - Pattern mutation and versioning
    - Self-questioning and confidence checks
    - Retry with mutation loops
    - Memory evolution tracking
    
    Usage:
        orchestrator = SelfImprovementOrchestrator()
        
        # Run improvement cycle
        cycle = orchestrator.run_improvement_cycle()
        
        # Execute pattern with learning
        result = orchestrator.execute_and_learn(pattern, goal, domain)
        
        # Get system health
        health = orchestrator.get_system_health()
    """
    
    def __init__(
        self,
        storage_path: Optional[Path] = None,
        config: Optional[SelfImprovementConfig] = None,
        config_path: Optional[Path] = None,
        use_yaml_config: bool = True
    ):
        """
        Initialize the self-improvement orchestrator.
        
        Args:
            storage_path: Path for LTM storage
            config: Configuration settings (overrides YAML if provided)
            config_path: Path to YAML config file
            use_yaml_config: Whether to load config from YAML file
        """
        # Load configuration
        if config is not None:
            self.config = config
        elif use_yaml_config:
            try:
                from rpa.training.si_config import create_self_improvement_config_from_yaml
                self.config = create_self_improvement_config_from_yaml(config_path)
            except Exception as e:
                logger.warning(f"Could not load YAML config: {e}, using defaults")
                self.config = SelfImprovementConfig()
        else:
            self.config = SelfImprovementConfig()
        
        self.storage_path = storage_path or Path.home() / ".rpa" / "memory"
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize core memory systems
        self.ltm = LongTermMemory(self.storage_path / "ltm")
        self.stm = ShortTermMemory()
        self.episodic = EpisodicMemory()
        
        # Load existing patterns
        self.ltm.load()
        
        # Initialize supporting components
        self.sandbox = CodeSandbox()
        self.validator = Validator()
        self.gap_detector = GapDetector()  # GapDetector takes no params
        self.correction_analyzer = CorrectionAnalyzer()
        
        # Initialize closed-loop components
        self._init_closed_loop_components()
        
        # Cycle tracking
        self.cycle_count = 0
        self.cycle_history: List[ImprovementCycle] = []
        self._current_cycle: Optional[ImprovementCycle] = None
        
        # State file for persistence
        self.state_file = self.storage_path / "self_improvement_state.json"
        self._load_state()
        
        logger.info(f"SelfImprovementOrchestrator initialized with {len(self.ltm)} patterns")
    
    def _init_closed_loop_components(self):
        """Initialize all closed-loop learning components."""
        
        # Outcome evaluation
        self.evaluator = OutcomeEvaluator(
            error_classifier=None,  # Could add ErrorClassifier
            validator=self.validator,
            assessment_engine=None
        )
        
        # Reinforcement tracking
        self.reinforcement = ReinforcementTracker(ltm=self.ltm)
        self.reinforcement.load_from_ltm()
        
        # Pattern mutation
        self.mutator = PatternMutator(
            ltm=self.ltm,
            error_corrector=None,
            correction_analyzer=self.correction_analyzer
        )
        
        # Memory evolution
        self.evolution = MemoryEvolution(ltm=self.ltm)
        
        # Self-questioning gate
        self.questioning_gate = SelfQuestioningGate(
            ltm=self.ltm,
            outcome_evaluator=self.evaluator,
            reinforcement_tracker=self.reinforcement,
            pattern_mutator=self.mutator,
            gap_detector=self.gap_detector
        )
        
        # Retry engine
        retry_config = RetryConfig(
            max_attempts=self.config.max_retry_attempts,
            backoff_multiplier=self.config.retry_backoff_factor
        )
        self.retry_engine = RetryEngine(
            sandbox=self.sandbox,
            evaluator=self.evaluator,
            mutator=self.mutator,
            reinforcement=self.reinforcement,
            questioning_gate=self.questioning_gate,
            ltm=self.ltm,
            config=retry_config
        )
    
    def _load_state(self):
        """Load persisted state from file."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                self.cycle_count = state.get('cycle_count', 0)
                logger.info(f"Loaded state: {self.cycle_count} cycles completed")
            except Exception as e:
                logger.warning(f"Could not load state: {e}")
    
    def _save_state(self):
        """Save current state to file."""
        try:
            state = {
                'cycle_count': self.cycle_count,
                'last_updated': datetime.now().isoformat(),
                'total_patterns': len(self.ltm)
            }
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save state: {e}")
    
    # =====================
    # Core Improvement Cycle
    # =====================
    
    def run_improvement_cycle(
        self,
        patterns: Optional[List[Any]] = None,
        domain: Optional[str] = None
    ) -> ImprovementCycle:
        """
        Run a complete self-improvement cycle.
        
        The cycle performs:
        1. Pattern evaluation and reinforcement
        2. Time-based decay application
        3. Pattern mutation for weak patterns
        4. Gap detection and learning prioritization
        5. Memory consolidation
        
        Args:
            patterns: Specific patterns to process (None = all in LTM)
            domain: Filter by domain
            
        Returns:
            ImprovementCycle with results
        """
        cycle_id = f"cycle_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.cycle_count}"
        cycle = ImprovementCycle(
            cycle_id=cycle_id,
            start_time=datetime.now()
        )
        self._current_cycle = cycle
        
        try:
            # Get patterns to process
            if patterns is None:
                patterns = self._get_patterns_for_improvement(domain)
            
            logger.info(f"Starting improvement cycle {cycle_id} with {len(patterns)} patterns")
            
            # Phase 1: Evaluate and reinforce patterns
            cycle = self._phase_evaluate_reinforce(patterns, cycle)
            
            # Phase 2: Apply time-based decay
            cycle = self._phase_apply_decay(cycle)
            
            # Phase 3: Mutate weak patterns
            cycle = self._phase_mutate_patterns(cycle)
            
            # Phase 4: Detect and address knowledge gaps
            cycle = self._phase_detect_gaps(cycle)
            
            # Phase 5: Consolidate and cleanup
            cycle = self._phase_consolidate(cycle)
            
        except Exception as e:
            cycle.errors.append(str(e))
            logger.error(f"Error in improvement cycle: {e}")
        
        finally:
            cycle.end_time = datetime.now()
            self.cycle_count += 1
            self.cycle_history.append(cycle)
            
            # Auto-save if configured
            if self.config.auto_save and self.cycle_count % self.config.save_interval_cycles == 0:
                self._save_state()
                self.ltm.save()
            
            self._current_cycle = None
            logger.info(f"Completed cycle {cycle_id} in {cycle.duration_seconds:.2f}s")
        
        return cycle
    
    def _get_patterns_for_improvement(
        self,
        domain: Optional[str] = None
    ) -> List[Any]:
        """Get patterns prioritized for improvement."""
        
        # Get all patterns from LTM
        all_patterns = list(self.ltm._graph.nodes.values())
        
        if not all_patterns:
            return []
        
        # Prioritize patterns that need attention
        priorities = []
        
        # Get weak patterns
        weak_patterns = self.reinforcement.get_weak_patterns(
            threshold=self.config.min_strength_threshold
        )
        weak_ids = {p.pattern_id for p in weak_patterns}
        
        # Get patterns needing fix
        fix_patterns = self.mutator.get_patterns_needing_fix()
        fix_ids = {p['pattern_id'] for p in fix_patterns}
        
        # Get problematic patterns
        problematic = self.evolution.find_problematic_patterns(min_failures=2)
        problematic_ids = {p['pattern_id'] for p in problematic}
        
        # Get patterns needing attention
        attention = self.evaluator.get_patterns_needing_attention()
        attention_ids = {p['pattern_id'] for p in attention}
        
        # Combine into priority set
        priority_ids = weak_ids | fix_ids | problematic_ids | attention_ids
        
        # Sort patterns by priority
        prioritized = []
        others = []
        
        for p in all_patterns:
            pattern_id = getattr(p, 'id', str(hash(str(p))))
            if pattern_id in priority_ids:
                prioritized.append(p)
            else:
                others.append(p)
        
        # Return prioritized first, then others up to limit
        result = prioritized[:self.config.patterns_per_cycle]
        remaining = self.config.patterns_per_cycle - len(result)
        if remaining > 0:
            result.extend(others[:remaining])
        
        return result
    
    def _phase_evaluate_reinforce(
        self,
        patterns: List[Any],
        cycle: ImprovementCycle
    ) -> ImprovementCycle:
        """Phase 1: Evaluate patterns and apply reinforcement."""
        
        for pattern in patterns:
            try:
                pattern_id = getattr(pattern, 'id', str(hash(str(pattern))))
                domain = getattr(pattern, 'domain', 'general')
                
                # Get recent outcomes for this pattern
                success_rate = self.evaluator.get_pattern_success_rate(pattern_id)
                
                # Create outcome based on success rate
                if success_rate >= 0.8:
                    outcome_type = OutcomeType.SUCCESS
                elif success_rate >= 0.5:
                    outcome_type = OutcomeType.PARTIAL
                elif success_rate >= 0.2:
                    outcome_type = OutcomeType.FAILURE
                else:
                    outcome_type = OutcomeType.ERROR
                
                outcome = Outcome(
                    pattern_id=pattern_id,
                    domain=domain,
                    outcome_type=outcome_type,
                    confidence=success_rate
                )
                
                # Process through reinforcement tracker
                record = self.reinforcement.process_outcome(outcome)
                
                cycle.patterns_evaluated += 1
                
                if record and record.signal == ReinforcementSignal.REINFORCE:
                    cycle.patterns_reinforced += 1
                elif record and record.signal == ReinforcementSignal.DECAY:
                    cycle.patterns_decayed += 1
                    
            except Exception as e:
                logger.warning(f"Error evaluating pattern: {e}")
                cycle.errors.append(f"Evaluation error: {e}")
        
        return cycle
    
    def _phase_apply_decay(self, cycle: ImprovementCycle) -> ImprovementCycle:
        """Phase 2: Apply time-based decay to all patterns."""
        
        try:
            decay_records = self.reinforcement.apply_decay()
            cycle.patterns_decayed += len(decay_records)
            logger.info(f"Applied decay to {len(decay_records)} patterns")
        except Exception as e:
            logger.warning(f"Error applying decay: {e}")
            cycle.errors.append(f"Decay error: {e}")
        
        return cycle
    
    def _phase_mutate_patterns(self, cycle: ImprovementCycle) -> ImprovementCycle:
        """Phase 3: Mutate weak or failing patterns."""
        
        if not self.config.enable_auto_mutation:
            return cycle
        
        # Get patterns that need mutation
        weak_patterns = self.reinforcement.get_weak_patterns(
            threshold=self.config.min_strength_threshold
        )
        fix_patterns = self.mutator.get_patterns_needing_fix()
        
        # Combine candidates
        mutation_candidates = set()
        for p in weak_patterns[:self.config.max_mutations_per_cycle]:
            mutation_candidates.add(p.pattern_id)
        for p in fix_patterns[:self.config.max_mutations_per_cycle]:
            mutation_candidates.add(p['pattern_id'])
        
        # Attempt mutations
        for pattern_id in list(mutation_candidates)[:self.config.max_mutations_per_cycle]:
            try:
                # Get the pattern
                pattern = self.ltm.get_pattern(pattern_id)
                if not pattern:
                    continue
                
                # Create failure outcome to trigger mutation
                outcome = Outcome(
                    pattern_id=pattern_id,
                    domain=getattr(pattern, 'domain', 'general'),
                    outcome_type=OutcomeType.FAILURE,
                    confidence=0.2
                )
                
                # Process mutation
                mutation = self.mutator.process_outcome(outcome)
                
                cycle.patterns_mutated += 1
                
                if mutation:
                    cycle.successful_mutations += 1
                    
                    # Record in evolution
                    self.evolution.record_version(
                        pattern_id=pattern_id,
                        event_type=EvolutionEvent.MUTATED,
                        content=str(pattern),
                        label=f"Auto-mutation: {mutation.mutation_type.value}"
                    )
                else:
                    cycle.failed_mutations += 1
                    
            except Exception as e:
                logger.warning(f"Error mutating pattern {pattern_id}: {e}")
                cycle.errors.append(f"Mutation error: {e}")
        
        return cycle
    
    def _phase_detect_gaps(self, cycle: ImprovementCycle) -> ImprovementCycle:
        """Phase 4: Detect knowledge gaps and prioritize learning."""
        
        try:
            # Detect gaps using the LTM's internal graph
            gaps = self.gap_detector.detect_all_gaps(self.ltm._graph)
            cycle.gaps_detected = len(gaps)
            
            # For each gap, try to close it through existing knowledge
            for gap in gaps[:10]:  # Limit gap processing
                # Check if we have related patterns that could help
                # This is a simplified gap closure - real implementation
                # would involve more sophisticated reasoning
                if gap.affected_nodes:
                    # Check if any affected nodes exist in LTM
                    for node_id in gap.affected_nodes[:3]:
                        if self.ltm.has_pattern(node_id):
                            cycle.gaps_closed += 1
                            break
                    
        except Exception as e:
            logger.warning(f"Error detecting gaps: {e}")
            cycle.errors.append(f"Gap detection error: {e}")
        
        return cycle
    
    def _phase_consolidate(self, cycle: ImprovementCycle) -> ImprovementCycle:
        """Phase 5: Consolidate learning and cleanup."""
        
        try:
            # Record usage snapshots for top patterns
            strong_patterns = self.reinforcement.get_strong_patterns(
                threshold=self.config.strong_pattern_threshold
            )
            
            for p in strong_patterns[:20]:
                self.evolution.record_usage_snapshot(
                    pattern_id=p.pattern_id,
                    total_uses=p.total_uses,
                    successful_uses=p.successful_uses,
                    avg_confidence=p.current_strength
                )
            
            # Cleanup deprecated patterns
            deprecated = self.mutator.get_deprecated_patterns()
            for p in deprecated:
                # Could move to archive instead of deleting
                pass
                
        except Exception as e:
            logger.warning(f"Error in consolidation: {e}")
            cycle.errors.append(f"Consolidation error: {e}")
        
        return cycle
    
    # =====================
    # Execute and Learn
    # =====================
    
    def execute_and_learn(
        self,
        pattern: Any,
        goal: str,
        domain: str = "general",
        input_data: Optional[Dict] = None,
        expected_output: Optional[Any] = None
    ) -> Tuple[Any, RetryChain]:
        """
        Execute a pattern with full learning feedback loop.
        
        This method:
        1. Checks confidence before execution
        2. Executes with retry capability
        3. Evaluates the outcome
        4. Updates reinforcement
        5. Potentially mutates if needed
        
        Args:
            pattern: The pattern to execute
            goal: Description of the goal
            domain: Domain context
            input_data: Input for execution
            expected_output: Expected result for validation
            
        Returns:
            Tuple of (result, retry_chain)
        """
        pattern_id = getattr(pattern, 'id', str(hash(str(pattern))))
        
        # Pre-execution confidence check
        questioning_result = self.questioning_gate.question(
            pattern_id=pattern_id,
            domain=domain,
            context={'goal': goal}
        )
        
        # Check if we should proceed
        if questioning_result.confidence_level == ConfidenceLevel.INSUFFICIENT:
            logger.warning(f"Pattern {pattern_id} has insufficient confidence")
        
        # Execute with retry
        chain = self.retry_engine.execute_with_retry(
            pattern=pattern,
            goal=goal,
            domain=domain,
            input_data=input_data,
            expected_output=expected_output
        )
        
        # Record in evolution
        self.evolution.record_usage_snapshot(
            pattern_id=pattern_id,
            total_uses=1,
            successful_uses=1 if chain.success else 0,
            avg_confidence=chain.final_confidence
        )
        
        # Return result
        result = chain.final_result if chain.success else None
        return result, chain
    
    def execute_code_and_learn(
        self,
        code: str,
        goal: str,
        domain: str = "coding",
        input_data: Optional[Dict] = None,
        expected_output: Optional[Any] = None
    ) -> Tuple[Any, RetryChain]:
        """
        Execute code with full learning feedback loop.
        
        Args:
            code: Python code to execute
            goal: Description of what the code should do
            domain: Domain context
            input_data: Input variables
            expected_output: Expected result
            
        Returns:
            Tuple of (result, retry_chain)
        """
        chain = self.retry_engine.execute_code_with_retry(
            code=code,
            goal=goal,
            domain=domain,
            input_data=input_data,
            expected_output=expected_output
        )
        
        result = chain.final_result if chain.success else None
        return result, chain
    
    # =====================
    # Pattern Improvement
    # =====================
    
    def improve_pattern(
        self,
        pattern_id: str,
        strategy: Optional[MutationType] = None
    ) -> Optional[MutationRecord]:
        """
        Actively improve a specific pattern.
        
        Args:
            pattern_id: ID of pattern to improve
            strategy: Specific mutation strategy to use
            
        Returns:
            MutationRecord if improvement was made
        """
        pattern = self.ltm.get_pattern(pattern_id)
        if not pattern:
            logger.warning(f"Pattern {pattern_id} not found")
            return None
        
        # Get current state
        strength = self.reinforcement.get_strength(pattern_id)
        history = self.evaluator.get_pattern_outcomes(pattern_id, limit=10)
        
        # Determine best mutation strategy
        if strategy is None:
            success_rate = self.evaluator.get_pattern_success_rate(pattern_id)
            
            if success_rate < 0.3:
                strategy = MutationType.FIX
            elif success_rate < 0.5:
                strategy = MutationType.REFINE
            elif success_rate < 0.7:
                strategy = MutationType.ENHANCE
            else:
                # Pattern is doing well, maybe generalize
                strategy = MutationType.GENERALIZE
        
        # Create improvement outcome
        outcome = Outcome(
            pattern_id=pattern_id,
            domain=getattr(pattern, 'domain', 'general'),
            outcome_type=OutcomeType.PARTIAL,
            confidence=strength.current_strength if strength else 0.5,
            metadata={'improvement_strategy': strategy.value}
        )
        
        # Process mutation
        mutation = self.mutator.process_outcome(outcome)
        
        if mutation:
            # Record evolution
            self.evolution.record_version(
                pattern_id=pattern_id,
                event_type=EvolutionEvent.ENHANCED,
                content=str(pattern),
                label=f"Manual improvement: {strategy.value}"
            )
            
            # Reinforce the improvement
            success_outcome = Outcome(
                pattern_id=pattern_id,
                domain=getattr(pattern, 'domain', 'general'),
                outcome_type=OutcomeType.SUCCESS,
                confidence=0.8
            )
            self.reinforcement.process_outcome(success_outcome)
        
        return mutation
    
    # =====================
    # System Health & Stats
    # =====================
    
    def get_system_health(self) -> SystemHealth:
        """
        Get comprehensive health metrics for the system.
        
        Returns:
            SystemHealth with current metrics
        """
        health = SystemHealth()
        
        # Pattern counts
        health.total_patterns = len(self.ltm)
        
        # Strength distribution
        strong = self.reinforcement.get_strong_patterns(
            threshold=self.config.strong_pattern_threshold
        )
        weak = self.reinforcement.get_weak_patterns(
            threshold=self.config.min_strength_threshold
        )
        health.strong_patterns = len(strong)
        health.weak_patterns = len(weak)
        
        # Deprecated
        deprecated = self.mutator.get_deprecated_patterns()
        health.deprecated_patterns = len(deprecated)
        
        # Averages
        if strong:
            health.avg_pattern_strength = sum(
                p.current_strength for p in strong
            ) / len(strong)
        
        # Pending work
        health.pending_mutations = len(
            self.mutator.get_patterns_needing_fix()
        )
        try:
            health.open_gaps = len(self.gap_detector.detect_all_gaps(self.ltm._graph))
        except:
            health.open_gaps = 0
        
        # Success rate
        evaluator_stats = self.evaluator.get_stats()
        health.recent_success_rate = evaluator_stats.get('success_rate', 0.0)
        
        # Learning velocity
        if self.cycle_history:
            recent_cycles = self.cycle_history[-10:]
            total_improvements = sum(
                c.patterns_reinforced + c.successful_mutations
                for c in recent_cycles
            )
            total_time = sum(c.duration_seconds for c in recent_cycles)
            if total_time > 0:
                health.learning_velocity = (total_improvements / total_time) * 3600
        
        # Last cycle
        if self.cycle_history:
            health.last_cycle_time = self.cycle_history[-1].end_time
        
        return health
    
    def get_learning_priorities(self) -> Dict[str, List[Dict]]:
        """
        Get prioritized list of learning actions.
        
        Returns:
            Dict with priority categories and their items
        """
        priorities = {
            'weak_patterns': [],
            'needs_fix': [],
            'problematic': [],
            'needs_attention': [],
            'gaps': []
        }
        
        # Weak patterns
        for p in self.reinforcement.get_weak_patterns()[:10]:
            priorities['weak_patterns'].append({
                'pattern_id': p.pattern_id,
                'strength': p.current_strength,
                'trend': p.trend
            })
        
        # Needs fix
        for p in self.mutator.get_patterns_needing_fix()[:10]:
            priorities['needs_fix'].append(p)
        
        # Problematic
        for p in self.evolution.find_problematic_patterns()[:10]:
            priorities['problematic'].append(p)
        
        # Needs attention
        for p in self.evaluator.get_patterns_needing_attention()[:10]:
            priorities['needs_attention'].append(p)
        
        # Gaps - use detect_all_gaps with the LTM's graph
        try:
            gaps = self.gap_detector.detect_all_gaps(self.ltm._graph)[:10]
            for gap in gaps:
                gap_dict = {
                    'id': gap.gap_id,
                    'description': gap.description,
                    'type': gap.gap_type.value,
                    'severity': gap.severity
                }
                priorities['gaps'].append(gap_dict)
        except Exception as e:
            logger.warning(f"Error getting gaps: {e}")
        
        return priorities
    
    def get_cycle_stats(self, last_n: int = 10) -> Dict[str, Any]:
        """
        Get statistics from recent cycles.
        
        Args:
            last_n: Number of recent cycles to analyze
            
        Returns:
            Dict with cycle statistics
        """
        if not self.cycle_history:
            return {'cycles': 0, 'message': 'No cycles completed'}
        
        recent = self.cycle_history[-last_n:]
        
        stats = {
            'total_cycles': self.cycle_count,
            'analyzed_cycles': len(recent),
            'total_patterns_evaluated': sum(c.patterns_evaluated for c in recent),
            'total_patterns_reinforced': sum(c.patterns_reinforced for c in recent),
            'total_patterns_decayed': sum(c.patterns_decayed for c in recent),
            'total_patterns_mutated': sum(c.patterns_mutated for c in recent),
            'total_successful_mutations': sum(c.successful_mutations for c in recent),
            'total_gaps_detected': sum(c.gaps_detected for c in recent),
            'total_gaps_closed': sum(c.gaps_closed for c in recent),
            'total_errors': sum(len(c.errors) for c in recent),
            'avg_cycle_duration': sum(c.duration_seconds for c in recent) / len(recent),
            'cycle_ids': [c.cycle_id for c in recent]
        }
        
        return stats
    
    # =====================
    # Maintenance
    # =====================
    
    def save(self):
        """Save all state and memory."""
        self._save_state()
        self.ltm.save()
        logger.info("Self-improvement state saved")
    
    def cleanup(self):
        """Perform cleanup operations."""
        # Remove very old deprecated patterns
        deprecated = self.mutator.get_deprecated_patterns()
        for p in deprecated:
            if p.get('deprecated_days', 0) > 30:  # Older than 30 days
                pattern_id = p['pattern_id']
                # Could archive instead of delete
                logger.info(f"Archiving deprecated pattern {pattern_id}")
        
        # Compact cycle history
        if len(self.cycle_history) > 100:
            # Keep only last 100 cycles
            self.cycle_history = self.cycle_history[-100:]
            logger.info("Compacted cycle history")
    
    def __repr__(self) -> str:
        return (
            f"SelfImprovementOrchestrator("
            f"patterns={len(self.ltm)}, "
            f"cycles={self.cycle_count})"
        )


# =====================
# Convenience Functions
# =====================

def create_self_improvement(
    storage_path: Optional[Path] = None,
    **config_kwargs
) -> SelfImprovementOrchestrator:
    """
    Create a self-improvement orchestrator with optional config.
    
    Args:
        storage_path: Path for memory storage
        **config_kwargs: Configuration parameters
        
    Returns:
        Configured SelfImprovementOrchestrator
    """
    config = SelfImprovementConfig(**config_kwargs)
    return SelfImprovementOrchestrator(storage_path=storage_path, config=config)


def run_improvement_cycle(
    orchestrator: Optional[SelfImprovementOrchestrator] = None,
    **kwargs
) -> ImprovementCycle:
    """
    Run a single improvement cycle.
    
    Args:
        orchestrator: Existing orchestrator (creates new if None)
        **kwargs: Additional arguments for run_improvement_cycle
        
    Returns:
        ImprovementCycle result
    """
    if orchestrator is None:
        orchestrator = create_self_improvement()
    
    return orchestrator.run_improvement_cycle(**kwargs)


# =====================
# CLI Entry Point
# =====================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="RPA Self-Improvement System")
    parser.add_argument("--cycle", action="store_true", help="Run improvement cycle")
    parser.add_argument("--health", action="store_true", help="Show system health")
    parser.add_argument("--priorities", action="store_true", help="Show learning priorities")
    parser.add_argument("--stats", action="store_true", help="Show cycle statistics")
    parser.add_argument("--storage", type=str, help="Storage path")
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create orchestrator
    storage = Path(args.storage) if args.storage else None
    orchestrator = create_self_improvement(storage_path=storage)
    
    if args.cycle:
        cycle = orchestrator.run_improvement_cycle()
        print(f"\nCycle completed: {cycle.cycle_id}")
        print(f"  Patterns evaluated: {cycle.patterns_evaluated}")
        print(f"  Patterns reinforced: {cycle.patterns_reinforced}")
        print(f"  Patterns mutated: {cycle.patterns_mutated}")
        print(f"  Duration: {cycle.duration_seconds:.2f}s")
    
    if args.health:
        health = orchestrator.get_system_health()
        print("\n=== System Health ===")
        print(f"Total patterns: {health.total_patterns}")
        print(f"Strong patterns: {health.strong_patterns}")
        print(f"Weak patterns: {health.weak_patterns}")
        print(f"Avg strength: {health.avg_pattern_strength:.2f}")
        print(f"Pending mutations: {health.pending_mutations}")
        print(f"Open gaps: {health.open_gaps}")
        print(f"Success rate: {health.recent_success_rate:.2%}")
    
    if args.priorities:
        priorities = orchestrator.get_learning_priorities()
        print("\n=== Learning Priorities ===")
        for category, items in priorities.items():
            print(f"\n{category}: {len(items)} items")
            for item in items[:3]:
                print(f"  - {item}")
    
    if args.stats:
        stats = orchestrator.get_cycle_stats()
        print("\n=== Cycle Statistics ===")
        for key, value in stats.items():
            print(f"{key}: {value}")
    
    if not any([args.cycle, args.health, args.priorities, args.stats]):
        parser.print_help()
