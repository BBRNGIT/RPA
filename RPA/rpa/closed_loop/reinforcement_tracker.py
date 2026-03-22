"""
Reinforcement Tracker - Track pattern usage and reinforcement.

Provides deterministic link strength management:
- Reinforce on success (increase score)
- Decay on disuse (time-based decay)
- Flag on failure (reduce score)
- Track usage frequency

This module implements the reinforcement learning aspect of RPA,
ensuring patterns that are used successfully get stronger while
unused or failing patterns weaken over time.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import uuid
import logging
import math

from rpa.core.graph import Node

logger = logging.getLogger(__name__)


@dataclass
class ReinforcementRecord:
    """Record of a reinforcement event."""
    record_id: str
    pattern_id: str
    event_type: str  # "success", "failure", "decay", "reset"
    previous_score: float
    new_score: float
    delta: float
    reason: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "record_id": self.record_id,
            "pattern_id": self.pattern_id,
            "event_type": self.event_type,
            "previous_score": self.previous_score,
            "new_score": self.new_score,
            "delta": self.delta,
            "reason": self.reason,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class UsageStats:
    """Usage statistics for a pattern."""
    pattern_id: str
    total_uses: int = 0
    successful_uses: int = 0
    failed_uses: int = 0
    last_used: Optional[datetime] = None
    first_used: Optional[datetime] = None
    reinforcement_score: float = 1.0
    decay_events: int = 0
    boost_events: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "pattern_id": self.pattern_id,
            "total_uses": self.total_uses,
            "successful_uses": self.successful_uses,
            "failed_uses": self.failed_uses,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "first_used": self.first_used.isoformat() if self.first_used else None,
            "reinforcement_score": self.reinforcement_score,
            "decay_events": self.decay_events,
            "boost_events": self.boost_events,
        }


class ReinforcementTracker:
    """
    Track pattern reinforcement and decay.

    Manages the strength of patterns based on usage:
    - Success: Increase reinforcement score
    - Failure: Decrease reinforcement score
    - Time decay: Reduce score for unused patterns
    - Usage frequency: Track how often patterns are accessed

    The reinforcement score determines:
    - Pattern retrieval priority
    - Whether pattern needs review
    - When to consider deprecation
    """

    # Reinforcement parameters
    DEFAULT_INITIAL_SCORE = 1.0
    SUCCESS_BOOST = 0.1  # Add on success
    FAILURE_PENALTY = 0.2  # Subtract on failure
    DECAY_RATE = 0.05  # Per day decay
    DECAY_THRESHOLD_DAYS = 7  # Days before decay starts
    MIN_SCORE = 0.1  # Minimum score before flagging
    MAX_SCORE = 2.0  # Maximum score
    DEPRECATION_THRESHOLD = 0.2  # Score below which to consider deprecation

    def __init__(self):
        """Initialize the ReinforcementTracker."""
        # Usage statistics by pattern
        self._usage_stats: Dict[str, UsageStats] = {}

        # Reinforcement history
        self._reinforcement_history: Dict[str, List[ReinforcementRecord]] = []

        # Global statistics
        self._stats = {
            "total_successes": 0,
            "total_failures": 0,
            "total_decays": 0,
            "total_boosts": 0,
        }

    def record_success(
        self,
        pattern_id: str,
        context: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ReinforcementRecord:
        """
        Record a successful use of a pattern.

        Args:
            pattern_id: ID of the pattern
            context: Optional context of usage
            metadata: Optional additional metadata

        Returns:
            ReinforcementRecord with score change
        """
        self._stats["total_successes"] += 1

        stats = self._get_or_create_stats(pattern_id)
        previous_score = stats.reinforcement_score

        # Apply success boost
        boost = self.SUCCESS_BOOST
        new_score = min(self.MAX_SCORE, previous_score + boost)

        # Update stats
        stats.total_uses += 1
        stats.successful_uses += 1
        stats.last_used = datetime.now()
        stats.reinforcement_score = new_score
        stats.boost_events += 1

        if stats.first_used is None:
            stats.first_used = datetime.now()

        # Create record
        record = ReinforcementRecord(
            record_id=f"reinforce_{uuid.uuid4().hex[:8]}",
            pattern_id=pattern_id,
            event_type="success",
            previous_score=previous_score,
            new_score=new_score,
            delta=boost,
            reason=f"Successful use in context: {context or 'unknown'}",
            metadata=metadata or {},
        )

        self._add_to_history(record)
        self._stats["total_boosts"] += 1

        logger.debug(f"Pattern {pattern_id} reinforced: {previous_score:.3f} -> {new_score:.3f}")

        return record

    def record_failure(
        self,
        pattern_id: str,
        context: Optional[str] = None,
        error_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ReinforcementRecord:
        """
        Record a failed use of a pattern.

        Args:
            pattern_id: ID of the pattern
            context: Optional context of usage
            error_type: Optional type of error
            metadata: Optional additional metadata

        Returns:
            ReinforcementRecord with score change
        """
        self._stats["total_failures"] += 1

        stats = self._get_or_create_stats(pattern_id)
        previous_score = stats.reinforcement_score

        # Apply failure penalty
        penalty = self.FAILURE_PENALTY
        new_score = max(self.MIN_SCORE, previous_score - penalty)

        # Update stats
        stats.total_uses += 1
        stats.failed_uses += 1
        stats.last_used = datetime.now()
        stats.reinforcement_score = new_score

        if stats.first_used is None:
            stats.first_used = datetime.now()

        # Create record
        record = ReinforcementRecord(
            record_id=f"reinforce_{uuid.uuid4().hex[:8]}",
            pattern_id=pattern_id,
            event_type="failure",
            previous_score=previous_score,
            new_score=new_score,
            delta=-penalty,
            reason=f"Failed use: {error_type or 'unknown error'} in context: {context or 'unknown'}",
            metadata=metadata or {},
        )

        self._add_to_history(record)

        logger.debug(f"Pattern {pattern_id} penalized: {previous_score:.3f} -> {new_score:.3f}")

        return record

    def apply_decay(
        self,
        pattern_id: str,
        days_unused: Optional[int] = None,
    ) -> Optional[ReinforcementRecord]:
        """
        Apply time-based decay to a pattern.

        Args:
            pattern_id: ID of the pattern
            days_unused: Optional override for days unused

        Returns:
            ReinforcementRecord if decay was applied, None otherwise
        """
        stats = self._get_or_create_stats(pattern_id)

        # Check if decay should apply
        if stats.last_used is None:
            return None

        if days_unused is None:
            days_unused = (datetime.now() - stats.last_used).days

        if days_unused < self.DECAY_THRESHOLD_DAYS:
            return None

        # Calculate decay
        decay_days = days_unused - self.DECAY_THRESHOLD_DAYS
        decay_amount = self.DECAY_RATE * decay_days
        decay_amount = min(decay_amount, stats.reinforcement_score - self.MIN_SCORE)

        if decay_amount <= 0:
            return None

        previous_score = stats.reinforcement_score
        new_score = max(self.MIN_SCORE, previous_score - decay_amount)

        # Update stats
        stats.reinforcement_score = new_score
        stats.decay_events += 1

        # Create record
        record = ReinforcementRecord(
            record_id=f"reinforce_{uuid.uuid4().hex[:8]}",
            pattern_id=pattern_id,
            event_type="decay",
            previous_score=previous_score,
            new_score=new_score,
            delta=-decay_amount,
            reason=f"Time decay after {days_unused} days unused",
            metadata={"days_unused": days_unused},
        )

        self._add_to_history(record)
        self._stats["total_decays"] += 1

        logger.debug(f"Pattern {pattern_id} decayed: {previous_score:.3f} -> {new_score:.3f}")

        return record

    def apply_decay_batch(
        self,
        pattern_ids: List[str],
    ) -> List[ReinforcementRecord]:
        """
        Apply decay to multiple patterns.

        Args:
            pattern_ids: List of pattern IDs to check for decay

        Returns:
            List of ReinforcementRecords for patterns that decayed
        """
        records = []
        for pattern_id in pattern_ids:
            record = self.apply_decay(pattern_id)
            if record:
                records.append(record)
        return records

    def get_score(self, pattern_id: str) -> float:
        """Get current reinforcement score for a pattern."""
        stats = self._usage_stats.get(pattern_id)
        return stats.reinforcement_score if stats else self.DEFAULT_INITIAL_SCORE

    def get_usage_stats(self, pattern_id: str) -> UsageStats:
        """Get usage statistics for a pattern."""
        return self._get_or_create_stats(pattern_id)

    def should_deprecate(self, pattern_id: str) -> bool:
        """Check if a pattern should be deprecated based on score."""
        score = self.get_score(pattern_id)
        return score < self.DEPRECATION_THRESHOLD

    def needs_review(self, pattern_id: str) -> bool:
        """Check if a pattern needs review based on score."""
        score = self.get_score(pattern_id)
        return score < 0.5

    def get_weak_patterns(self, threshold: float = 0.5) -> List[str]:
        """Get patterns with reinforcement score below threshold."""
        weak = []
        for pattern_id, stats in self._usage_stats.items():
            if stats.reinforcement_score < threshold:
                weak.append(pattern_id)
        return weak

    def get_strong_patterns(self, threshold: float = 1.5) -> List[str]:
        """Get patterns with reinforcement score above threshold."""
        strong = []
        for pattern_id, stats in self._usage_stats.items():
            if stats.reinforcement_score >= threshold:
                strong.append(pattern_id)
        return strong

    def get_unused_patterns(self, days: int = 30) -> List[str]:
        """Get patterns not used in specified days."""
        cutoff = datetime.now() - timedelta(days=days)
        unused = []

        for pattern_id, stats in self._usage_stats.items():
            if stats.last_used is None or stats.last_used < cutoff:
                unused.append(pattern_id)

        return unused

    def boost_pattern(
        self,
        pattern_id: str,
        amount: float = 0.2,
        reason: str = "Manual boost",
    ) -> ReinforcementRecord:
        """
        Manually boost a pattern's score.

        Args:
            pattern_id: ID of the pattern
            amount: Amount to boost
            reason: Reason for the boost

        Returns:
            ReinforcementRecord with score change
        """
        stats = self._get_or_create_stats(pattern_id)
        previous_score = stats.reinforcement_score
        new_score = min(self.MAX_SCORE, previous_score + amount)

        stats.reinforcement_score = new_score
        stats.boost_events += 1

        record = ReinforcementRecord(
            record_id=f"reinforce_{uuid.uuid4().hex[:8]}",
            pattern_id=pattern_id,
            event_type="boost",
            previous_score=previous_score,
            new_score=new_score,
            delta=amount,
            reason=reason,
        )

        self._add_to_history(record)

        return record

    def reset_score(
        self,
        pattern_id: str,
        reason: str = "Manual reset",
    ) -> ReinforcementRecord:
        """
        Reset a pattern's score to initial value.

        Args:
            pattern_id: ID of the pattern
            reason: Reason for the reset

        Returns:
            ReinforcementRecord with score change
        """
        stats = self._get_or_create_stats(pattern_id)
        previous_score = stats.reinforcement_score
        new_score = self.DEFAULT_INITIAL_SCORE

        stats.reinforcement_score = new_score

        record = ReinforcementRecord(
            record_id=f"reinforce_{uuid.uuid4().hex[:8]}",
            pattern_id=pattern_id,
            event_type="reset",
            previous_score=previous_score,
            new_score=new_score,
            delta=new_score - previous_score,
            reason=reason,
        )

        self._add_to_history(record)

        return record

    def get_history(
        self,
        pattern_id: str,
        limit: int = 20,
    ) -> List[ReinforcementRecord]:
        """Get reinforcement history for a pattern."""
        history = self._reinforcement_history.get(pattern_id, [])
        return history[-limit:]

    def get_global_statistics(self) -> Dict[str, Any]:
        """Get global reinforcement statistics."""
        total_patterns = len(self._usage_stats)
        avg_score = 0.0

        if total_patterns > 0:
            total_score = sum(
                stats.reinforcement_score
                for stats in self._usage_stats.values()
            )
            avg_score = total_score / total_patterns

        return {
            **self._stats,
            "total_patterns_tracked": total_patterns,
            "average_score": avg_score,
            "weak_patterns": len(self.get_weak_patterns()),
            "strong_patterns": len(self.get_strong_patterns()),
            "unused_patterns_30d": len(self.get_unused_patterns(30)),
        }

    def update_node_metadata(self, node: Node) -> Node:
        """
        Update a node's metadata with reinforcement info.

        Args:
            node: The node to update

        Returns:
            The updated node
        """
        stats = self._get_or_create_stats(node.node_id)

        node.metadata["reinforcement_score"] = stats.reinforcement_score
        node.metadata["total_uses"] = stats.total_uses
        node.metadata["successful_uses"] = stats.successful_uses
        node.metadata["failed_uses"] = stats.failed_uses
        node.metadata["last_used"] = stats.last_used.isoformat() if stats.last_used else None
        node.metadata["decay_events"] = stats.decay_events
        node.metadata["boost_events"] = stats.boost_events

        return node

    def _get_or_create_stats(self, pattern_id: str) -> UsageStats:
        """Get or create usage stats for a pattern."""
        if pattern_id not in self._usage_stats:
            self._usage_stats[pattern_id] = UsageStats(pattern_id=pattern_id)
        return self._usage_stats[pattern_id]

    def _add_to_history(self, record: ReinforcementRecord) -> None:
        """Add record to history."""
        if record.pattern_id not in self._reinforcement_history:
            self._reinforcement_history[record.pattern_id] = []
        self._reinforcement_history[record.pattern_id].append(record)

    def clear_history(self) -> None:
        """Clear reinforcement history."""
        self._reinforcement_history.clear()
        self._stats = {
            "total_successes": 0,
            "total_failures": 0,
            "total_decays": 0,
            "total_boosts": 0,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Serialize tracker state to dictionary."""
        return {
            "usage_stats": {
                pid: stats.to_dict()
                for pid, stats in self._usage_stats.items()
            },
            "stats": self._stats,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReinforcementTracker":
        """Deserialize tracker from dictionary."""
        tracker = cls()

        for pid, stats_data in data.get("usage_stats", {}).items():
            stats = UsageStats(pattern_id=pid)
            stats.total_uses = stats_data.get("total_uses", 0)
            stats.successful_uses = stats_data.get("successful_uses", 0)
            stats.failed_uses = stats_data.get("failed_uses", 0)
            stats.reinforcement_score = stats_data.get("reinforcement_score", 1.0)
            stats.decay_events = stats_data.get("decay_events", 0)
            stats.boost_events = stats_data.get("boost_events", 0)

            if stats_data.get("last_used"):
                stats.last_used = datetime.fromisoformat(stats_data["last_used"])
            if stats_data.get("first_used"):
                stats.first_used = datetime.fromisoformat(stats_data["first_used"])

            tracker._usage_stats[pid] = stats

        tracker._stats = data.get("stats", tracker._stats)

        return tracker
