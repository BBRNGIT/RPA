"""
Reinforcement Tracker - Track pattern usage, reinforcement, and decay.

Manages the dynamic strength of patterns over time:
- Reinforce patterns that succeed
- Decay patterns that aren't used
- Flag patterns that fail
- Track usage frequency and recency

This enables the system to "remember what works" and "forget what doesn't".
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from enum import Enum
import math
import logging

from rpa.core.node import Node
from rpa.memory.ltm import LongTermMemory
from rpa.closed_loop.outcome_evaluator import Outcome, OutcomeType

logger = logging.getLogger(__name__)


class ReinforcementSignal(Enum):
    """Types of reinforcement signals."""
    REINFORCE = "reinforce"       # Strengthen the pattern
    DECAY = "decay"               # Weaken the pattern
    FLAG = "flag"                 # Mark for review
    STABLE = "stable"             # No change needed
    PROMOTE = "promote"           # Increase hierarchy/importance
    DEMOTE = "demote"             # Decrease hierarchy/importance


@dataclass
class ReinforcementRecord:
    """Record of a reinforcement event."""
    record_id: str
    pattern_id: str
    signal: ReinforcementSignal
    previous_strength: float
    new_strength: float
    reason: str
    outcome_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "record_id": self.record_id,
            "pattern_id": self.pattern_id,
            "signal": self.signal.value,
            "previous_strength": self.previous_strength,
            "new_strength": self.new_strength,
            "reason": self.reason,
            "outcome_id": self.outcome_id,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class PatternStrength:
    """Tracks the strength of a pattern over time."""
    pattern_id: str
    strength: float = 1.0           # Current strength (0.0-1.0)
    base_strength: float = 1.0      # Starting strength
    peak_strength: float = 1.0      # Highest ever reached
    
    # Usage tracking
    total_uses: int = 0
    successful_uses: int = 0
    failed_uses: int = 0
    last_used: Optional[datetime] = None
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    
    # Reinforcement tracking
    reinforcement_count: int = 0
    decay_count: int = 0
    flag_count: int = 0
    
    # Streaks
    current_streak: int = 0         # Positive = success streak, negative = failure streak
    best_streak: int = 0
    worst_streak: int = 0
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "pattern_id": self.pattern_id,
            "strength": self.strength,
            "base_strength": self.base_strength,
            "peak_strength": self.peak_strength,
            "total_uses": self.total_uses,
            "successful_uses": self.successful_uses,
            "failed_uses": self.failed_uses,
            "success_rate": self.successful_uses / self.total_uses if self.total_uses > 0 else 0,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "last_success": self.last_success.isoformat() if self.last_success else None,
            "last_failure": self.last_failure.isoformat() if self.last_failure else None,
            "reinforcement_count": self.reinforcement_count,
            "decay_count": self.decay_count,
            "flag_count": self.flag_count,
            "current_streak": self.current_streak,
            "best_streak": self.best_streak,
            "worst_streak": self.worst_streak,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class ReinforcementTracker:
    """
    Track and manage pattern reinforcement over time.
    
    This system enables patterns to:
    - Grow stronger with successful use (reinforcement)
    - Weaken over time without use (decay)
    - Get flagged for attention on failure
    - Be promoted or demoted based on performance
    
    The reinforcement model is deterministic - no heuristics pretending
    to be reasoning. Strength changes are calculated based on actual outcomes.
    """
    
    # Reinforcement parameters
    REINFORCEMENT_RATE = 0.1        # How much to strengthen on success
    DECAY_RATE = 0.05               # Daily decay rate for unused patterns
    MIN_STRENGTH = 0.1              # Minimum strength before deprecation considered
    FLAG_THRESHOLD = 0.3            # Strength below which patterns are flagged
    PROMOTION_THRESHOLD = 0.9       # Strength for promotion consideration
    STREAK_BONUS = 0.02             # Bonus per streak step
    MAX_STREAK_BONUS = 0.2          # Maximum streak bonus
    
    # Decay timing
    DECAY_START_HOURS = 24          # Hours before decay starts
    DECAY_PERIOD_HOURS = 24         # How often decay is applied
    
    def __init__(self, ltm: Optional[LongTermMemory] = None):
        """
        Initialize ReinforcementTracker.
        
        Args:
            ltm: Optional LongTermMemory instance to sync with
        """
        self.ltm = ltm
        
        # Pattern strength tracking
        self._strengths: Dict[str, PatternStrength] = {}
        
        # Reinforcement history
        self._history: List[ReinforcementRecord] = []
        self._max_history = 10000
        
        # Statistics
        self._stats = {
            "total_reinforcements": 0,
            "total_decays": 0,
            "total_flags": 0,
            "total_promotions": 0,
            "total_demotions": 0,
            "patterns_tracked": 0,
            "patterns_deprecated": 0,
        }
    
    def process_outcome(self, outcome: Outcome) -> ReinforcementRecord:
        """
        Process an outcome and update pattern strength accordingly.
        
        This is the main entry point - every outcome triggers reinforcement
        processing for its associated pattern.
        
        Args:
            outcome: The outcome to process
            
        Returns:
            ReinforcementRecord describing what happened
        """
        pattern_id = outcome.pattern_id
        
        # Ensure pattern is tracked
        if pattern_id not in self._strengths:
            self._track_pattern(pattern_id)
        
        strength = self._strengths[pattern_id]
        previous = strength.strength
        
        # Determine signal and calculate new strength
        signal, new_strength, reason = self._calculate_reinforcement(outcome, strength)
        
        # Update strength
        strength.strength = new_strength
        strength.updated_at = datetime.now()
        strength.total_uses += 1
        
        # Update usage tracking
        if outcome.outcome_type == OutcomeType.SUCCESS:
            strength.successful_uses += 1
            strength.last_success = datetime.now()
            strength.current_streak = max(1, strength.current_streak + 1)
            strength.best_streak = max(strength.best_streak, strength.current_streak)
        elif outcome.outcome_type in (OutcomeType.FAILURE, OutcomeType.ERROR):
            strength.failed_uses += 1
            strength.last_failure = datetime.now()
            strength.current_streak = min(-1, strength.current_streak - 1)
            strength.worst_streak = min(strength.worst_streak, strength.current_streak)
        else:
            # Reset streak on uncertain/partial/gap
            if abs(strength.current_streak) > 0:
                strength.current_streak = 0
        
        strength.last_used = datetime.now()
        
        # Update peak strength
        strength.peak_strength = max(strength.peak_strength, new_strength)
        
        # Update counters
        if signal == ReinforcementSignal.REINFORCE:
            strength.reinforcement_count += 1
            self._stats["total_reinforcements"] += 1
        elif signal == ReinforcementSignal.DECAY:
            strength.decay_count += 1
            self._stats["total_decays"] += 1
        elif signal == ReinforcementSignal.FLAG:
            strength.flag_count += 1
            self._stats["total_flags"] += 1
        elif signal == ReinforcementSignal.PROMOTE:
            self._stats["total_promotions"] += 1
        elif signal == ReinforcementSignal.DEMOTE:
            self._stats["total_demotions"] += 1
        
        # Create record
        import uuid
        record = ReinforcementRecord(
            record_id=f"reinf_{uuid.uuid4().hex[:8]}",
            pattern_id=pattern_id,
            signal=signal,
            previous_strength=previous,
            new_strength=new_strength,
            reason=reason,
            outcome_id=outcome.outcome_id,
        )
        
        self._history.append(record)
        if len(self._history) > self._max_history:
            self._history.pop(0)
        
        # Sync with LTM if available
        if self.ltm:
            self._sync_to_ltm(pattern_id, strength)
        
        return record
    
    def _calculate_reinforcement(
        self,
        outcome: Outcome,
        strength: PatternStrength,
    ) -> tuple[ReinforcementSignal, float, str]:
        """
        Calculate reinforcement signal and new strength.
        
        Returns:
            Tuple of (signal, new_strength, reason)
        """
        current = strength.strength
        
        # SUCCESS: Reinforce the pattern
        if outcome.outcome_type == OutcomeType.SUCCESS:
            # Base reinforcement
            boost = self.REINFORCEMENT_RATE
            
            # Streak bonus
            streak_bonus = min(
                abs(strength.current_streak) * self.STREAK_BONUS,
                self.MAX_STREAK_BONUS
            )
            
            # Confidence multiplier
            confidence_mult = outcome.confidence_score
            
            # Calculate total boost
            total_boost = boost + streak_bonus
            total_boost *= confidence_mult
            
            new_strength = min(1.0, current + total_boost)
            
            # Check for promotion
            if new_strength >= self.PROMOTION_THRESHOLD and current < self.PROMOTION_THRESHOLD:
                return (
                    ReinforcementSignal.PROMOTE,
                    new_strength,
                    f"Pattern promoted due to consistent success (streak: {strength.current_streak})"
                )
            
            return (
                ReinforcementSignal.REINFORCE,
                new_strength,
                f"Reinforced on success (boost: {total_boost:.3f}, streak: {strength.current_streak})"
            )
        
        # FAILURE: Decay or flag
        elif outcome.outcome_type == OutcomeType.FAILURE:
            # Decay on failure
            decay = self.DECAY_RATE * 2  # Stronger decay on failure
            
            # Streak penalty
            streak_penalty = min(
                abs(strength.current_streak) * 0.02,
                0.1
            )
            
            new_strength = max(0.0, current - decay - streak_penalty)
            
            # Check for flag
            if new_strength < self.FLAG_THRESHOLD:
                return (
                    ReinforcementSignal.FLAG,
                    new_strength,
                    f"Pattern flagged due to low strength ({new_strength:.2f})"
                )
            
            return (
                ReinforcementSignal.DECAY,
                new_strength,
                f"Decayed on failure (decay: {decay + streak_penalty:.3f})"
            )
        
        # ERROR: Strong decay and flag
        elif outcome.outcome_type == OutcomeType.ERROR:
            decay = self.DECAY_RATE * 3
            new_strength = max(0.0, current - decay)
            
            return (
                ReinforcementSignal.FLAG,
                new_strength,
                f"Pattern flagged due to error (decay: {decay:.3f})"
            )
        
        # GAP: Slight decay - indicates incomplete knowledge
        elif outcome.outcome_type == OutcomeType.GAP:
            decay = self.DECAY_RATE * 0.5
            new_strength = max(0.0, current - decay)
            
            return (
                ReinforcementSignal.DECAY,
                new_strength,
                "Slight decay on gap detection"
            )
        
        # PARTIAL: Small adjustment
        elif outcome.outcome_type == OutcomeType.PARTIAL:
            # Slight decay for partial success
            new_strength = max(0.0, current - 0.02)
            return (
                ReinforcementSignal.STABLE,
                new_strength,
                "Minor adjustment for partial success"
            )
        
        # UNCERTAIN: No change but note it
        else:
            return (
                ReinforcementSignal.STABLE,
                current,
                "No change for uncertain outcome"
            )
    
    def apply_decay(self, pattern_id: Optional[str] = None) -> List[ReinforcementRecord]:
        """
        Apply time-based decay to unused patterns.
        
        Args:
            pattern_id: Optional specific pattern to decay, or all if None
            
        Returns:
            List of ReinforcementRecords for decayed patterns
        """
        records = []
        now = datetime.now()
        
        patterns_to_check = [pattern_id] if pattern_id else list(self._strengths.keys())
        
        for pid in patterns_to_check:
            if pid not in self._strengths:
                continue
            
            strength = self._strengths[pid]
            
            # Check if decay should apply
            if strength.last_used:
                hours_since_use = (now - strength.last_used).total_seconds() / 3600
            else:
                hours_since_use = (now - strength.created_at).total_seconds() / 3600
            
            if hours_since_use < self.DECAY_START_HOURS:
                continue
            
            # Calculate decay
            days_unused = hours_since_use / 24
            decay_amount = self.DECAY_RATE * (1 + 0.1 * math.log1p(days_unused))
            
            previous = strength.strength
            new_strength = max(0.0, previous - decay_amount)
            
            if new_strength < previous:
                strength.strength = new_strength
                strength.updated_at = now
                strength.decay_count += 1
                
                import uuid
                record = ReinforcementRecord(
                    record_id=f"decay_{uuid.uuid4().hex[:8]}",
                    pattern_id=pid,
                    signal=ReinforcementSignal.DECAY,
                    previous_strength=previous,
                    new_strength=new_strength,
                    reason=f"Time-based decay (unused for {days_unused:.1f} days)",
                )
                
                self._history.append(record)
                records.append(record)
                
                self._stats["total_decays"] += 1
                
                # Sync with LTM
                if self.ltm:
                    self._sync_to_ltm(pid, strength)
        
        return records
    
    def _track_pattern(self, pattern_id: str, initial_strength: float = 1.0) -> None:
        """Start tracking a pattern."""
        if pattern_id in self._strengths:
            return
        
        self._strengths[pattern_id] = PatternStrength(
            pattern_id=pattern_id,
            strength=initial_strength,
            base_strength=initial_strength,
        )
        self._stats["patterns_tracked"] += 1
    
    def _sync_to_ltm(self, pattern_id: str, strength: PatternStrength) -> None:
        """Sync strength data to LTM pattern metadata."""
        if not self.ltm:
            return
        
        node = self.ltm.get_pattern(pattern_id)
        if node:
            # Update node metadata with strength info
            node.metadata["strength"] = strength.strength
            node.metadata["total_uses"] = strength.total_uses
            node.metadata["successful_uses"] = strength.successful_uses
            node.metadata["failed_uses"] = strength.failed_uses
            node.metadata["current_streak"] = strength.current_streak
            node.metadata["reinforcement_count"] = strength.reinforcement_count
            node.metadata["decay_count"] = strength.decay_count
            node.metadata["last_used"] = strength.last_used.isoformat() if strength.last_used else None
            
            # Update confidence based on strength
            node.confidence = strength.strength
            
            # Mark deprecated if strength is too low
            if strength.strength < self.MIN_STRENGTH:
                node.is_valid = False
                node.metadata["deprecated"] = True
                node.metadata["deprecation_reason"] = f"Strength fell below {self.MIN_STRENGTH}"
                self._stats["patterns_deprecated"] += 1
    
    def get_strength(self, pattern_id: str) -> Optional[PatternStrength]:
        """Get strength info for a pattern."""
        return self._strengths.get(pattern_id)
    
    def get_patterns_by_strength(self, min_strength: float = 0.0, max_strength: float = 1.0) -> List[PatternStrength]:
        """Get patterns filtered by strength range."""
        return [
            s for s in self._strengths.values()
            if min_strength <= s.strength <= max_strength
        ]
    
    def get_weak_patterns(self, threshold: float = 0.3) -> List[PatternStrength]:
        """Get patterns below strength threshold."""
        return self.get_patterns_by_strength(max_strength=threshold)
    
    def get_strong_patterns(self, threshold: float = 0.7) -> List[PatternStrength]:
        """Get patterns above strength threshold."""
        return self.get_patterns_by_strength(min_strength=threshold)
    
    def get_patterns_for_review(self) -> List[Dict[str, Any]]:
        """Get patterns that need human review."""
        review_needed = []
        
        for strength in self._strengths.values():
            reasons = []
            
            # Low strength
            if strength.strength < self.FLAG_THRESHOLD:
                reasons.append(f"Low strength: {strength.strength:.2f}")
            
            # Negative streak
            if strength.current_streak <= -3:
                reasons.append(f"Failure streak: {strength.current_streak}")
            
            # High failure rate
            if strength.total_uses >= 5:
                failure_rate = strength.failed_uses / strength.total_uses
                if failure_rate > 0.5:
                    reasons.append(f"High failure rate: {failure_rate:.1%}")
            
            # Multiple flags
            if strength.flag_count >= 3:
                reasons.append(f"Multiple flags: {strength.flag_count}")
            
            if reasons:
                review_needed.append({
                    "pattern_id": strength.pattern_id,
                    "strength": strength.strength,
                    "reasons": reasons,
                    "details": strength.to_dict(),
                })
        
        return sorted(review_needed, key=lambda x: x["strength"])
    
    def get_reinforcement_history(self, pattern_id: Optional[str] = None, limit: int = 100) -> List[ReinforcementRecord]:
        """Get reinforcement history, optionally filtered by pattern."""
        if pattern_id:
            records = [r for r in self._history if r.pattern_id == pattern_id]
        else:
            records = self._history
        
        return records[-limit:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get reinforcement statistics."""
        strengths = list(self._strengths.values())
        
        avg_strength = sum(s.strength for s in strengths) / len(strengths) if strengths else 0
        
        return {
            **self._stats,
            "average_strength": avg_strength,
            "total_patterns_tracked": len(self._strengths),
            "history_size": len(self._history),
            "strength_distribution": {
                "weak": len([s for s in strengths if s.strength < 0.3]),
                "medium": len([s for s in strengths if 0.3 <= s.strength < 0.7]),
                "strong": len([s for s in strengths if s.strength >= 0.7]),
            },
        }
    
    def load_from_ltm(self) -> int:
        """
        Load existing patterns from LTM and initialize tracking.
        
        Returns:
            Number of patterns loaded
        """
        if not self.ltm:
            return 0
        
        loaded = 0
        for node in self.ltm._graph.nodes.values():
            if node.node_id not in self._strengths:
                # Initialize from existing metadata
                initial_strength = node.metadata.get("strength", node.confidence)
                self._track_pattern(node.node_id, initial_strength)
                
                # Load existing stats from metadata
                strength = self._strengths[node.node_id]
                strength.total_uses = node.metadata.get("total_uses", node.access_count)
                strength.successful_uses = node.metadata.get("successful_uses", 0)
                strength.failed_uses = node.metadata.get("failed_uses", 0)
                strength.current_streak = node.metadata.get("current_streak", 0)
                
                loaded += 1
        
        return loaded
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize tracker state."""
        return {
            "strengths": {pid: s.to_dict() for pid, s in self._strengths.items()},
            "stats": self._stats,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], ltm: Optional[LongTermMemory] = None) -> "ReinforcementTracker":
        """Deserialize tracker state."""
        tracker = cls(ltm=ltm)
        
        for pid, sdata in data.get("strengths", {}).items():
            strength = PatternStrength(pattern_id=pid)
            strength.strength = sdata.get("strength", 1.0)
            strength.base_strength = sdata.get("base_strength", 1.0)
            strength.peak_strength = sdata.get("peak_strength", 1.0)
            strength.total_uses = sdata.get("total_uses", 0)
            strength.successful_uses = sdata.get("successful_uses", 0)
            strength.failed_uses = sdata.get("failed_uses", 0)
            strength.reinforcement_count = sdata.get("reinforcement_count", 0)
            strength.decay_count = sdata.get("decay_count", 0)
            strength.flag_count = sdata.get("flag_count", 0)
            strength.current_streak = sdata.get("current_streak", 0)
            strength.best_streak = sdata.get("best_streak", 0)
            strength.worst_streak = sdata.get("worst_streak", 0)
            
            if sdata.get("last_used"):
                strength.last_used = datetime.fromisoformat(sdata["last_used"])
            if sdata.get("last_success"):
                strength.last_success = datetime.fromisoformat(sdata["last_success"])
            if sdata.get("last_failure"):
                strength.last_failure = datetime.fromisoformat(sdata["last_failure"])
            if sdata.get("created_at"):
                strength.created_at = datetime.fromisoformat(sdata["created_at"])
            
            tracker._strengths[pid] = strength
        
        tracker._stats = data.get("stats", tracker._stats)
        
        return tracker
