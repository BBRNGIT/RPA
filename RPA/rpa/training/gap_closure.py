"""
RPA Gap Closure Loop

Connects GapDetector to self-improvement cycle for autonomous learning.
Generates learning goals from detected gaps and attempts to close them.

Ticket: SI-004
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum

from rpa.inquiry.gap_detector import GapDetector, Gap, GapType
from rpa.core.graph import PatternGraph

logger = logging.getLogger(__name__)


class LearningGoalStatus(Enum):
    """Status of a learning goal."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    DEFERRED = "deferred"


class GapClosureStrategy(Enum):
    """Strategies for closing knowledge gaps."""
    LEARN_FROM_SOURCE = "learn_from_source"
    COMPOSE_EXISTING = "compose_existing"
    GENERATE_PATTERN = "generate_pattern"
    IMPORT_FROM_DOMAIN = "import_from_domain"
    ASK_FOR_HELP = "ask_for_help"


@dataclass
class LearningGoal:
    """A learning goal generated from a detected gap."""
    goal_id: str
    source_gap_id: str
    description: str
    target_patterns: List[str]
    strategy: GapClosureStrategy
    priority: int  # 1-10, higher = more important
    status: LearningGoalStatus = LearningGoalStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    attempts: int = 0
    max_attempts: int = 3
    result: Optional[str] = None
    patterns_learned: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['strategy'] = self.strategy.value
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat()
        data['started_at'] = self.started_at.isoformat() if self.started_at else None
        data['completed_at'] = self.completed_at.isoformat() if self.completed_at else None
        return data


@dataclass
class GapClosureResult:
    """Result of a gap closure attempt."""
    goal_id: str
    gap_id: str
    success: bool
    patterns_created: int
    patterns_linked: int
    message: str
    duration_seconds: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class GapClosureLoop:
    """
    Autonomous gap detection and closure system.
    
    This class connects the GapDetector to the self-improvement cycle,
    automatically generating learning goals from detected gaps and
    attempting to close them through various strategies.
    
    Usage:
        loop = GapClosureLoop(ltm, gap_detector)
        
        # Detect gaps and generate goals
        goals = loop.detect_and_plan()
        
        # Execute closure attempts
        results = loop.execute_closure()
        
        # Get status
        status = loop.get_status()
    """
    
    def __init__(
        self,
        ltm: Any,
        gap_detector: Optional[GapDetector] = None,
        storage_path: Optional[Path] = None,
        max_goals_per_cycle: int = 10,
        auto_execute: bool = True
    ):
        """
        Initialize the gap closure loop.
        
        Args:
            ltm: Long-term memory instance
            gap_detector: GapDetector instance (created if None)
            storage_path: Path for state persistence
            max_goals_per_cycle: Maximum goals to process per cycle
            auto_execute: Whether to auto-execute closure attempts
        """
        self.ltm = ltm
        self.gap_detector = gap_detector or GapDetector()
        self.storage_path = storage_path or Path.home() / ".rpa" / "gap_closure"
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.max_goals_per_cycle = max_goals_per_cycle
        self.auto_execute = auto_execute
        
        # State
        self.learning_goals: Dict[str, LearningGoal] = {}
        self.closure_history: List[GapClosureResult] = []
        self._goal_counter = 0
        self._total_gaps_detected = 0
        self._total_goals_created = 0
        self._total_goals_completed = 0
        
        # Load existing state
        self._load_state()
    
    def detect_and_plan(
        self,
        domain: Optional[str] = None,
        min_severity: str = "medium"
    ) -> List[LearningGoal]:
        """
        Detect gaps and generate learning goals.
        
        Args:
            domain: Optional domain filter
            min_severity: Minimum severity to process ("low", "medium", "high")
            
        Returns:
            List of new learning goals created
        """
        # Get the graph from LTM
        graph = self._get_graph()
        if graph is None:
            logger.warning("No graph available for gap detection")
            return []
        
        # Detect all gaps
        gaps = self.gap_detector.detect_all_gaps(graph, domain)
        self._total_gaps_detected += len(gaps)
        
        # Filter by severity
        severity_order = {"low": 1, "medium": 2, "high": 3}
        min_level = severity_order.get(min_severity, 2)
        
        filtered_gaps = [
            g for g in gaps 
            if severity_order.get(g.severity, 1) >= min_level
        ]
        
        # Prioritize gaps
        prioritized = self.gap_detector.prioritize_gaps(filtered_gaps)
        
        # Generate learning goals
        new_goals = []
        for gap in prioritized[:self.max_goals_per_cycle]:
            # Skip if we already have a goal for this gap
            existing = [g for g in self.learning_goals.values() 
                       if g.source_gap_id == gap.gap_id and 
                       g.status in [LearningGoalStatus.PENDING, LearningGoalStatus.IN_PROGRESS]]
            
            if existing:
                continue
            
            goal = self._create_learning_goal(gap)
            if goal:
                self.learning_goals[goal.goal_id] = goal
                new_goals.append(goal)
                self._total_goals_created += 1
        
        logger.info(f"Created {len(new_goals)} new learning goals from {len(gaps)} detected gaps")
        
        # Save state
        self._save_state()
        
        return new_goals
    
    def _get_graph(self) -> Optional[PatternGraph]:
        """Get the pattern graph from LTM."""
        if hasattr(self.ltm, '_graph'):
            return self.ltm._graph
        elif hasattr(self.ltm, 'graph'):
            return self.ltm.graph
        return None
    
    def _create_learning_goal(self, gap: Gap) -> Optional[LearningGoal]:
        """Create a learning goal from a detected gap."""
        self._goal_counter += 1
        goal_id = f"goal_{self._goal_counter:04d}"
        
        # Determine best strategy
        strategy = self._select_strategy(gap)
        
        # Calculate priority
        priority = self._calculate_priority(gap)
        
        # Create description
        description = self._generate_description(gap, strategy)
        
        # Target patterns
        target_patterns = gap.affected_nodes.copy()
        
        goal = LearningGoal(
            goal_id=goal_id,
            source_gap_id=gap.gap_id,
            description=description,
            target_patterns=target_patterns,
            strategy=strategy,
            priority=priority,
            metadata={
                'gap_type': gap.gap_type.value,
                'gap_severity': gap.severity,
                'gap_metadata': gap.metadata
            }
        )
        
        return goal
    
    def _select_strategy(self, gap: Gap) -> GapClosureStrategy:
        """Select the best strategy for closing a gap."""
        gap_type = gap.gap_type
        
        # Strategy mapping based on gap type
        strategy_map = {
            GapType.UNRESOLVED_REFERENCE: GapClosureStrategy.LEARN_FROM_SOURCE,
            GapType.INCOMPLETE_COMPOSITION: GapClosureStrategy.COMPOSE_EXISTING,
            GapType.MISSING_PRIMITIVE: GapClosureStrategy.LEARN_FROM_SOURCE,
            GapType.UNCERTAIN_PATTERN: GapClosureStrategy.GENERATE_PATTERN,
            GapType.HIERARCHY_GAP: GapClosureStrategy.COMPOSE_EXISTING,
            GapType.ORPHANED_PATTERN: GapClosureStrategy.COMPOSE_EXISTING,
            GapType.CROSS_DOMAIN: GapClosureStrategy.IMPORT_FROM_DOMAIN,
        }
        
        return strategy_map.get(gap_type, GapClosureStrategy.LEARN_FROM_SOURCE)
    
    def _calculate_priority(self, gap: Gap) -> int:
        """Calculate priority score for a gap."""
        severity_scores = {"high": 9, "medium": 6, "low": 3}
        base = severity_scores.get(gap.severity, 5)
        
        # Adjust for gap type
        type_multipliers = {
            GapType.UNRESOLVED_REFERENCE: 1.2,
            GapType.INCOMPLETE_COMPOSITION: 1.1,
            GapType.MISSING_PRIMITIVE: 1.0,
            GapType.UNCERTAIN_PATTERN: 0.9,
            GapType.HIERARCHY_GAP: 0.8,
            GapType.ORPHANED_PATTERN: 0.7,
            GapType.CROSS_DOMAIN: 0.6,
        }
        
        multiplier = type_multipliers.get(gap.gap_type, 1.0)
        return min(10, int(base * multiplier))
    
    def _generate_description(self, gap: Gap, strategy: GapClosureStrategy) -> str:
        """Generate a human-readable goal description."""
        strategy_names = {
            GapClosureStrategy.LEARN_FROM_SOURCE: "Learn from source",
            GapClosureStrategy.COMPOSE_EXISTING: "Compose from existing patterns",
            GapClosureStrategy.GENERATE_PATTERN: "Generate new pattern",
            GapClosureStrategy.IMPORT_FROM_DOMAIN: "Import from another domain",
            GapClosureStrategy.ASK_FOR_HELP: "Request external help",
        }
        
        return f"{strategy_names[strategy]}: {gap.description}"
    
    def execute_closure(
        self,
        goal_ids: Optional[List[str]] = None,
        max_attempts: int = 5
    ) -> List[GapClosureResult]:
        """
        Execute closure attempts for pending goals.
        
        Args:
            goal_ids: Specific goal IDs to execute (None = all pending)
            max_attempts: Maximum attempts per goal
            
        Returns:
            List of closure results
        """
        results = []
        
        # Get goals to process
        if goal_ids:
            goals = [self.learning_goals[gid] for gid in goal_ids if gid in self.learning_goals]
        else:
            goals = [g for g in self.learning_goals.values() 
                    if g.status == LearningGoalStatus.PENDING]
        
        # Sort by priority
        goals.sort(key=lambda g: g.priority, reverse=True)
        
        for goal in goals[:max_attempts]:
            result = self._execute_single_closure(goal)
            results.append(result)
            
            if result.success:
                self._total_goals_completed += 1
        
        # Save state
        self._save_state()
        
        return results
    
    def _execute_single_closure(self, goal: LearningGoal) -> GapClosureResult:
        """Execute a single closure attempt."""
        import time
        start_time = time.time()
        
        goal.status = LearningGoalStatus.IN_PROGRESS
        goal.started_at = datetime.now()
        goal.attempts += 1
        
        patterns_created = 0
        patterns_linked = 0
        success = False
        message = ""
        
        try:
            if goal.strategy == GapClosureStrategy.COMPOSE_EXISTING:
                patterns_created, patterns_linked, message = self._compose_existing(goal)
            elif goal.strategy == GapClosureStrategy.LEARN_FROM_SOURCE:
                patterns_created, patterns_linked, message = self._learn_from_source(goal)
            elif goal.strategy == GapClosureStrategy.GENERATE_PATTERN:
                patterns_created, patterns_linked, message = self._generate_pattern(goal)
            elif goal.strategy == GapClosureStrategy.IMPORT_FROM_DOMAIN:
                patterns_created, patterns_linked, message = self._import_from_domain(goal)
            else:
                message = f"Unknown strategy: {goal.strategy}"
            
            success = patterns_created > 0 or patterns_linked > 0
            
            if success:
                goal.status = LearningGoalStatus.COMPLETED
                goal.completed_at = datetime.now()
                goal.result = "success"
            elif goal.attempts >= goal.max_attempts:
                goal.status = LearningGoalStatus.FAILED
                goal.result = "max_attempts_reached"
            else:
                goal.status = LearningGoalStatus.PENDING
        
        except Exception as e:
            message = f"Error during closure: {str(e)}"
            goal.status = LearningGoalStatus.FAILED
            goal.result = f"error: {str(e)}"
            logger.error(f"Gap closure error for {goal.goal_id}: {e}")
        
        duration = time.time() - start_time
        
        result = GapClosureResult(
            goal_id=goal.goal_id,
            gap_id=goal.source_gap_id,
            success=success,
            patterns_created=patterns_created,
            patterns_linked=patterns_linked,
            message=message,
            duration_seconds=duration
        )
        
        self.closure_history.append(result)
        
        return result
    
    def _compose_existing(self, goal: LearningGoal) -> Tuple[int, int, str]:
        """
        Compose a new pattern from existing ones.
        
        Strategy: Find existing patterns that could be composed to fill the gap.
        """
        graph = self._get_graph()
        if graph is None:
            return 0, 0, "No graph available"
        
        patterns_created = 0
        patterns_linked = 0
        
        # Get metadata about the gap
        gap_meta = goal.metadata.get('gap_metadata', {})
        
        if 'missing_children' in gap_meta:
            # Try to find existing patterns that match the missing references
            missing = gap_meta['missing_children']
            
            for missing_id in missing:
                # Check if pattern exists with similar content
                # This is a simplified implementation
                pass
        
        # For hierarchy gaps, compose higher-level patterns
        if goal.metadata.get('gap_type') == 'hierarchy':
            missing_levels = gap_meta.get('missing_levels', [])
            domain = gap_meta.get('domain', 'general')
            
            # Would create intermediate patterns here
            message = f"Hierarchy gap identified in {domain}, levels {missing_levels}"
        
        return patterns_created, patterns_linked, "Composition attempted"
    
    def _learn_from_source(self, goal: LearningGoal) -> Tuple[int, int, str]:
        """
        Learn patterns from external sources.
        
        Strategy: Use training data or curriculum to fill gaps.
        """
        # This would integrate with the training pipeline
        # For now, return placeholder
        return 0, 0, "Source learning requires training integration"
    
    def _generate_pattern(self, goal: LearningGoal) -> Tuple[int, int, str]:
        """
        Generate a new pattern algorithmically.
        
        Strategy: Create patterns based on detected structure.
        """
        # This would use pattern generation logic
        return 0, 0, "Pattern generation not yet implemented"
    
    def _import_from_domain(self, goal: LearningGoal) -> Tuple[int, int, str]:
        """
        Import patterns from another domain.
        
        Strategy: Find analogous patterns in other domains.
        """
        graph = self._get_graph()
        if graph is None:
            return 0, 0, "No graph available"
        
        domains = goal.metadata.get('gap_metadata', {}).get('domains', [])
        content = goal.metadata.get('gap_metadata', {}).get('content', '')
        
        # Would create cross-domain links here
        
        return 0, 0, f"Cross-domain import from {domains}"
    
    def get_pending_goals(self) -> List[LearningGoal]:
        """Get all pending learning goals."""
        return [g for g in self.learning_goals.values() 
                if g.status == LearningGoalStatus.PENDING]
    
    def get_in_progress_goals(self) -> List[LearningGoal]:
        """Get all in-progress learning goals."""
        return [g for g in self.learning_goals.values() 
                if g.status == LearningGoalStatus.IN_PROGRESS]
    
    def get_completed_goals(self) -> List[LearningGoal]:
        """Get all completed learning goals."""
        return [g for g in self.learning_goals.values() 
                if g.status == LearningGoalStatus.COMPLETED]
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status of the gap closure system."""
        return {
            'total_gaps_detected': self._total_gaps_detected,
            'total_goals_created': self._total_goals_created,
            'total_goals_completed': self._total_goals_completed,
            'pending_goals': len(self.get_pending_goals()),
            'in_progress_goals': len(self.get_in_progress_goals()),
            'completed_goals': len(self.get_completed_goals()),
            'total_closure_attempts': len(self.closure_history),
            'successful_closures': sum(1 for r in self.closure_history if r.success),
            'recent_results': [r.to_dict() for r in self.closure_history[-5:]]
        }
    
    def _load_state(self):
        """Load persisted state from file."""
        state_file = self.storage_path / "gap_closure_state.json"
        
        if state_file.exists():
            try:
                with open(state_file, 'r') as f:
                    state = json.load(f)
                
                self._goal_counter = state.get('goal_counter', 0)
                self._total_gaps_detected = state.get('total_gaps_detected', 0)
                self._total_goals_created = state.get('total_goals_created', 0)
                self._total_goals_completed = state.get('total_goals_completed', 0)
                
                logger.info(f"Loaded gap closure state: {self._total_goals_completed} goals completed")
                
            except Exception as e:
                logger.warning(f"Could not load gap closure state: {e}")
    
    def _save_state(self):
        """Save current state to file."""
        state_file = self.storage_path / "gap_closure_state.json"
        
        try:
            state = {
                'goal_counter': self._goal_counter,
                'total_gaps_detected': self._total_gaps_detected,
                'total_goals_created': self._total_goals_created,
                'total_goals_completed': self._total_goals_completed,
                'last_updated': datetime.now().isoformat(),
                'learning_goals': {gid: goal.to_dict() for gid, goal in self.learning_goals.items()}
            }
            
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)
                
        except Exception as e:
            logger.warning(f"Could not save gap closure state: {e}")
    
    def run_full_cycle(
        self,
        domain: Optional[str] = None,
        min_severity: str = "medium"
    ) -> Dict[str, Any]:
        """
        Run a complete detect-plan-execute cycle.
        
        This is the main entry point for the gap closure loop.
        
        Args:
            domain: Optional domain filter
            min_severity: Minimum severity to process
            
        Returns:
            Dict with cycle results
        """
        # Phase 1: Detect and plan
        new_goals = self.detect_and_plan(domain, min_severity)
        
        # Phase 2: Execute closure
        results = []
        if self.auto_execute:
            results = self.execute_closure()
        
        # Compile results
        status = self.get_status()
        
        return {
            'new_goals_created': len(new_goals),
            'closure_attempts': len(results),
            'successful_closures': sum(1 for r in results if r.success),
            'status': status
        }
    
    def __repr__(self) -> str:
        return (
            f"GapClosureLoop("
            f"goals={len(self.learning_goals)}, "
            f"completed={self._total_goals_completed})"
        )
