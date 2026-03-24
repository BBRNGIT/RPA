"""
Reinforcement Tracker - Track pattern usage and reinforcement.

Implements deterministic reinforcement learning for pattern strength:
- Reinforce on success (strengthen pattern)
- Decay on disuse (weaken forgotten patterns)
- Flag on failure (mark for review/mutation)

This is NOT heuristic-based - it uses explicit outcome signals.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
import math
import logging

from rpa.core.graph import Node

logger = logging.getLogger(__name__)


@dataclass
class ReinforcementRecord:
    """
    Tracks reinforcement history for a pattern.

    This is the "memory trace" of how well a pattern has performed.
    """
    pattern_id: str
    domain: str

    # Core metrics
    strength: float = 1.0              # Current strength (0.0 to 2.0, starts at 1.0)
    usage_count: int = 0               # Total times used
    success_count: int = 0             # Times succeeded
    failure_count: int = 0             # Times failed

    # Decay tracking
    last_used: datetime = field(default_factory=datetime.now)
    last_reinforced: datetime = field(default_factory=datetime.now)
    decay_events: int = 0              # Times decayed

    # Flagging
    is_flagged: bool = False           # Flagged for review
    flag_reason: Optional[str] = None

    # Reinforcement history (last N events)
    reinforcement_history: List[Dict[str, Any]] = field(default_factory=list)
    max_history: int = 50

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "pattern_id": self.pattern_id,
            "domain": self.domain,
            "strength": self.strength,
            "usage_count": self.usage_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": self.success_count / max(1, self.usage_count),
            "last_used": self.last_used.isoformat(),
            "last_reinforced": self.last_reinforced.isoformat(),
            "decay_events": self.decay_events,
            "is_flagged": self.is_flagged,
            "flag_reason": self.flag_reason,
        }

    def add_reinforcement_event(
        self,
        event_type: str,
        delta: float,
        reason: str,
        outcome_id: Optional[str] = None
    ) -> None:
        """Add a reinforcement event to history."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "delta": delta,
            "reason": reason,
            "strength_after": self.strength,
            "outcome_id": outcome_id,
        }
        self.reinforcement_history.append(event)

        # Trim history
        if len(self.reinforcement_history) > self.max_history:
            self.reinforcement_history = self.reinforcement_history[-self.max_history:]


class ReinforcementTracker:
    """
    Tracks pattern reinforcement and decay.

    The reinforcement model is deterministic:
    - SUCCESS: strength += reinforcement_rate * (2.0 - strength)
    - FAILURE: strength -= penalty_rate * strength
    - DECAY: strength *= decay_factor (based on time since last use)

    Strength is bounded: 0.0 (deprecate) to 2.0 (highly reinforced)

    Example:
        tracker = ReinforcementTracker()

        # On successful outcome
        tracker.reinforce(pattern_id, success=True)

        # On failure
        tracker.reinforce(pattern_id, success=False)

        # Periodic decay check
        tracker.apply_decay()
    """

    # Configuration
    DEFAULT_REINFORCEMENT_RATE = 0.1   # How much to strengthen on success
    DEFAULT_PENALTY_RATE = 0.2         # How much to weaken on failure
    DEFAULT_DECAY_FACTOR = 0.95        # Decay multiplier
    DECAY_INTERVAL_HOURS = 24          # Apply decay every N hours
    FLAG_THRESHOLD = 0.3               # Flag for review below this
    DEPRECATE_THRESHOLD = 0.1          # Deprecate below this
    MAX_STRENGTH = 2.0                 # Maximum strength
    MIN_STRENGTH = 0.0                 # Minimum strength

    # Domain-specific adjustments
    DOMAIN_CONFIGS = {
        "python": {"reinforcement_rate": 0.12, "penalty_rate": 0.18},
        "rust": {"reinforcement_rate": 0.10, "penalty_rate": 0.20},
        "go": {"reinforcement_rate": 0.10, "penalty_rate": 0.20},
        "english": {"reinforcement_rate": 0.15, "penalty_rate": 0.15},
        "general": {"reinforcement_rate": 0.10, "penalty_rate": 0.20},
    }

    def __init__(self):
        """Initialize the ReinforcementTracker."""
        self._records: Dict[str, ReinforcementRecord] = {}
        self._domain_records: Dict[str, Set[str]] = {}  # domain -> pattern_ids

        # Statistics
        self._stats = {
            "total_reinforcements": 0,
            "total_penalties": 0,
            "total_decays": 0,
            "patterns_flagged": 0,
            "patterns_deprecated": 0,
        }

        # Last decay run
        self._last_decay_time: Optional[datetime] = None

    def record_usage(
        self,
        pattern: Node,
        success: bool,
        outcome_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ReinforcementRecord:
        """
        Record pattern usage and apply reinforcement.

        Args:
            pattern: The pattern node that was used
            success: Whether the usage was successful
            outcome_id: Optional linked outcome ID
            metadata: Optional additional metadata

        Returns:
            Updated ReinforcementRecord
        """
        pattern_id = pattern.node_id
        domain = pattern.domain

        # Get or create record
        if pattern_id not in self._records:
            self._create_record(pattern_id, domain)

        record = self._records[pattern_id]

        # Update usage counts
        record.usage_count += 1
        record.last_used = datetime.now()

        # Apply reinforcement or penalty
        if success:
            self._apply_reinforcement(record, outcome_id)
            record.success_count += 1
        else:
            self._apply_penalty(record, outcome_id)
            record.failure_count += 1

        # Check for flagging
        self._check_flag(record)

        # Update domain index
        if domain not in self._domain_records:
            self._domain_records[domain] = set()
        self._domain_records[domain].add(pattern_id)

        # Update pattern metadata
        pattern.metadata["strength"] = record.strength
        pattern.metadata["usage_count"] = record.usage_count
        pattern.metadata["success_rate"] = record.success_count / max(1, record.usage_count)

        logger.debug(
            f"Recorded usage for {pattern_id}: success={success}, "
            f"strength={record.strength:.3f}"
        )

        return record

    def reinforce(
        self,
        pattern_id: str,
        domain: str = "general",
        success: bool = True,
        outcome_id: Optional[str] = None,
        amount: Optional[float] = None
    ) -> ReinforcementRecord:
        """
        Record pattern usage and apply reinforcement or penalty.

        Args:
            pattern_id: The pattern ID
            domain: The pattern domain
            success: Whether the usage was successful (True=reinforce, False=penalize)
            outcome_id: Optional linked outcome ID
            amount: Optional custom reinforcement/penalty amount

        Returns:
            Updated ReinforcementRecord
        """
        if pattern_id not in self._records:
            self._create_record(pattern_id, domain)

        record = self._records[pattern_id]

        # Update usage counts
        record.usage_count += 1
        record.last_used = datetime.now()

        if success:
            self._apply_reinforcement(record, outcome_id, amount)
            record.success_count += 1
        else:
            self._apply_penalty(record, outcome_id, amount)
            record.failure_count += 1
            self._check_flag(record)

        return record

    def penalize(
        self,
        pattern_id: str,
        domain: str = "general",
        amount: Optional[float] = None
    ) -> ReinforcementRecord:
        """
        Explicitly penalize a pattern.

        Args:
            pattern_id: The pattern ID
            domain: The pattern domain
            amount: Optional custom penalty amount

        Returns:
            Updated ReinforcementRecord
        """
        if pattern_id not in self._records:
            self._create_record(pattern_id, domain)

        record = self._records[pattern_id]
        self._apply_penalty(record, None, amount)

        self._check_flag(record)

        return record

    def apply_decay(self, force: bool = False) -> Dict[str, Any]:
        """
        Apply time-based decay to all patterns.

        Decay is applied based on time since last use.
        Patterns used recently are not decayed.

        Args:
            force: Force decay even if interval hasn't passed

        Returns:
            Decay summary statistics
        """
        now = datetime.now()

        # Check if decay interval has passed
        if not force and self._last_decay_time:
            hours_since = (now - self._last_decay_time).total_seconds() / 3600
            if hours_since < self.DECAY_INTERVAL_HOURS:
                return {"skipped": True, "reason": "interval_not_elapsed"}

        decayed_count = 0
        flagged_count = 0
        deprecated_count = 0

        for record in self._records.values():
            # Calculate hours since last use
            hours_since_use = (now - record.last_used).total_seconds() / 3600

            # Apply decay based on time
            if hours_since_use > 24:  # Decay after 24 hours of non-use
                decay_factor = self.DEFAULT_DECAY_FACTOR ** (hours_since_use / 24)
                old_strength = record.strength
                record.strength *= decay_factor
                record.decay_events += 1

                record.add_reinforcement_event(
                    event_type="decay",
                    delta=record.strength - old_strength,
                    reason=f"Decay after {hours_since_use:.1f} hours"
                )

                decayed_count += 1

            # Check flagging after decay
            if record.strength < self.FLAG_THRESHOLD and not record.is_flagged:
                record.is_flagged = True
                record.flag_reason = f"Low strength: {record.strength:.3f}"
                flagged_count += 1
                self._stats["patterns_flagged"] += 1

            # Check deprecation
            if record.strength < self.DEPRECATE_THRESHOLD:
                deprecated_count += 1
                self._stats["patterns_deprecated"] += 1

        self._last_decay_time = now
        self._stats["total_decays"] += decayed_count

        logger.info(
            f"Applied decay: {decayed_count} patterns decayed, "
            f"{flagged_count} flagged, {deprecated_count} deprecated"
        )

        return {
            "decayed_count": decayed_count,
            "flagged_count": flagged_count,
            "deprecated_count": deprecated_count,
            "timestamp": now.isoformat(),
        }

    def get_record(self, pattern_id: str) -> Optional[ReinforcementRecord]:
        """Get reinforcement record for a pattern."""
        return self._records.get(pattern_id)

    def get_or_create(self, pattern_id: str, domain: str = "general") -> ReinforcementRecord:
        """
        Get or create a reinforcement record.

        Args:
            pattern_id: The pattern ID
            domain: The pattern domain

        Returns:
            ReinforcementRecord (existing or new)
        """
        if pattern_id not in self._records:
            self._create_record(pattern_id, domain)
        return self._records[pattern_id]

    def get_records_by_domain(self, domain: str) -> List[ReinforcementRecord]:
        """
        Get all records for a specific domain.

        Args:
            domain: The domain to filter by

        Returns:
            List of ReinforcementRecords in that domain
        """
        pattern_ids = self._domain_records.get(domain, set())
        return [self._records[pid] for pid in pattern_ids if pid in self._records]

    def get_domains(self) -> List[str]:
        """Get list of all tracked domains."""
        return list(self._domain_records.keys())

    def get_strength(self, pattern_id: str) -> float:
        """Get current strength for a pattern."""
        record = self._records.get(pattern_id)
        return record.strength if record else 1.0

    def get_flagged_patterns(self, domain: Optional[str] = None) -> List[str]:
        """
        Get patterns flagged for review.

        Args:
            domain: Optional domain filter

        Returns:
            List of flagged pattern IDs
        """
        flagged = []

        for pattern_id, record in self._records.items():
            if record.is_flagged:
                if domain is None or record.domain == domain:
                    flagged.append(pattern_id)

        return flagged

    def get_weak_patterns(self, threshold: float = 0.5) -> List[str]:
        """
        Get patterns below a strength threshold.

        Args:
            threshold: Strength threshold

        Returns:
            List of weak pattern IDs
        """
        return [
            pid for pid, record in self._records.items()
            if record.strength < threshold
        ]

    def get_strong_patterns(self, threshold: float = 1.5) -> List[str]:
        """
        Get patterns above a strength threshold.

        Args:
            threshold: Strength threshold

        Returns:
            List of strong pattern IDs
        """
        return [
            pid for pid, record in self._records.items()
            if record.strength >= threshold
        ]

    def get_domain_stats(self, domain: str) -> Dict[str, Any]:
        """Get statistics for a specific domain."""
        pattern_ids = self._domain_records.get(domain, set())
        records = [self._records[pid] for pid in pattern_ids if pid in self._records]

        if not records:
            return {"domain": domain, "pattern_count": 0}

        strengths = [r.strength for r in records]
        usage_counts = [r.usage_count for r in records]

        return {
            "domain": domain,
            "pattern_count": len(records),
            "avg_strength": sum(strengths) / len(strengths),
            "min_strength": min(strengths),
            "max_strength": max(strengths),
            "total_usage": sum(usage_counts),
            "flagged_count": sum(1 for r in records if r.is_flagged),
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get overall tracker statistics."""
        strengths = [r.strength for r in self._records.values()]

        return {
            **self._stats,
            "total_patterns": len(self._records),
            "domains": list(self._domain_records.keys()),
            "avg_strength": sum(strengths) / len(strengths) if strengths else 1.0,
            "flagged_count": sum(1 for r in self._records.values() if r.is_flagged),
        }

    def clear_flag(self, pattern_id: str) -> bool:
        """Clear the flag on a pattern."""
        record = self._records.get(pattern_id)
        if record:
            record.is_flagged = False
            record.flag_reason = None
            return True
        return False

    def _create_record(self, pattern_id: str, domain: str) -> ReinforcementRecord:
        """Create a new reinforcement record."""
        record = ReinforcementRecord(
            pattern_id=pattern_id,
            domain=domain
        )
        self._records[pattern_id] = record

        if domain not in self._domain_records:
            self._domain_records[domain] = set()
        self._domain_records[domain].add(pattern_id)

        return record

    def _apply_reinforcement(
        self,
        record: ReinforcementRecord,
        outcome_id: Optional[str] = None,
        amount: Optional[float] = None
    ) -> None:
        """Apply reinforcement to a record."""
        domain_config = self.DOMAIN_CONFIGS.get(record.domain, self.DOMAIN_CONFIGS["general"])
        rate = amount if amount is not None else domain_config["reinforcement_rate"]

        # Reinforcement formula: strength += rate * (max - strength)
        # This gives diminishing returns as strength approaches MAX_STRENGTH
        delta = rate * (self.MAX_STRENGTH - record.strength)
        record.strength = min(self.MAX_STRENGTH, record.strength + delta)
        record.last_reinforced = datetime.now()

        record.add_reinforcement_event(
            event_type="reinforcement",
            delta=delta,
            reason="success",
            outcome_id=outcome_id
        )

        self._stats["total_reinforcements"] += 1

    def _apply_penalty(
        self,
        record: ReinforcementRecord,
        outcome_id: Optional[str] = None,
        amount: Optional[float] = None
    ) -> None:
        """Apply penalty to a record."""
        domain_config = self.DOMAIN_CONFIGS.get(record.domain, self.DOMAIN_CONFIGS["general"])
        rate = amount if amount is not None else domain_config["penalty_rate"]

        # Penalty formula: strength -= rate * strength
        # This is proportional to current strength
        delta = -rate * record.strength
        record.strength = max(self.MIN_STRENGTH, record.strength + delta)

        record.add_reinforcement_event(
            event_type="penalty",
            delta=delta,
            reason="failure",
            outcome_id=outcome_id
        )

        self._stats["total_penalties"] += 1

    def _check_flag(self, record: ReinforcementRecord) -> None:
        """Check if record should be flagged."""
        if record.strength < self.FLAG_THRESHOLD and not record.is_flagged:
            record.is_flagged = True
            record.flag_reason = f"Low strength after failures: {record.strength:.3f}"
            self._stats["patterns_flagged"] += 1

        # Also flag on high failure rate
        if record.usage_count >= 5:
            failure_rate = record.failure_count / record.usage_count
            if failure_rate > 0.5 and not record.is_flagged:
                record.is_flagged = True
                record.flag_reason = f"High failure rate: {failure_rate:.1%}"
                self._stats["patterns_flagged"] += 1

    def export_records(self) -> List[Dict[str, Any]]:
        """Export all records as dictionaries."""
        return [r.to_dict() for r in self._records.values()]

    def import_records(self, records: List[Dict[str, Any]]) -> int:
        """
        Import records from dictionaries.

        Args:
            records: List of record dictionaries

        Returns:
            Number of records imported
        """
        imported = 0

        for data in records:
            pattern_id = data.get("pattern_id")
            domain = data.get("domain", "general")

            if pattern_id:
                record = ReinforcementRecord(
                    pattern_id=pattern_id,
                    domain=domain,
                    strength=data.get("strength", 1.0),
                    usage_count=data.get("usage_count", 0),
                    success_count=data.get("success_count", 0),
                    failure_count=data.get("failure_count", 0),
                    is_flagged=data.get("is_flagged", False),
                    flag_reason=data.get("flag_reason"),
                )

                # Parse timestamps
                if "last_used" in data:
                    record.last_used = datetime.fromisoformat(data["last_used"])
                if "last_reinforced" in data:
                    record.last_reinforced = datetime.fromisoformat(data["last_reinforced"])

                self._records[pattern_id] = record

                if domain not in self._domain_records:
                    self._domain_records[domain] = set()
                self._domain_records[domain].add(pattern_id)

                imported += 1

        return imported
