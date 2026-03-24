"""
KnowledgeIntegrity - Truth management and validation for RPA.

Provides knowledge integrity capabilities:
- Contradiction detection
- Truth value tracking
- Confidence management
- Knowledge validation
- Conflict resolution
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class Fact:
    """Represents a fact in the knowledge base."""
    fact_id: str
    content: str
    domain: str
    truth_value: float  # 0.0 (false) to 1.0 (true)
    confidence: float  # How confident we are about the truth value
    source: str  # Where the fact came from
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    supporting_facts: List[str] = field(default_factory=list)
    contradicting_facts: List[str] = field(default_factory=list)
    evidence_for: int = 0
    evidence_against: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "fact_id": self.fact_id,
            "content": self.content,
            "domain": self.domain,
            "truth_value": self.truth_value,
            "confidence": self.confidence,
            "source": self.source,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "supporting_facts": self.supporting_facts,
            "contradicting_facts": self.contradicting_facts,
            "evidence_for": self.evidence_for,
            "evidence_against": self.evidence_against,
            "metadata": self.metadata,
        }


@dataclass
class Contradiction:
    """Represents a detected contradiction."""
    contradiction_id: str
    fact1_id: str
    fact2_id: str
    fact1_content: str
    fact2_content: str
    severity: str  # critical, high, medium, low
    conflict_type: str  # direct, indirect, contextual
    resolution_suggestions: List[str] = field(default_factory=list)
    resolved: bool = False
    resolution: Optional[str] = None
    detected_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "contradiction_id": self.contradiction_id,
            "fact1_id": self.fact1_id,
            "fact2_id": self.fact2_id,
            "fact1_content": self.fact1_content,
            "fact2_content": self.fact2_content,
            "severity": self.severity,
            "conflict_type": self.conflict_type,
            "resolution_suggestions": self.resolution_suggestions,
            "resolved": self.resolved,
            "resolution": self.resolution,
            "detected_at": self.detected_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "metadata": self.metadata,
        }


class KnowledgeIntegrity:
    """
    Knowledge integrity and truth management system.

    Maintains truth values, detects contradictions, and manages
    knowledge consistency.
    """

    # Truth value thresholds
    TRUTH_THRESHOLD = 0.7  # Above this = considered true
    FALSE_THRESHOLD = 0.3  # Below this = considered false
    UNCERTAIN_RANGE = (0.3, 0.7)  # Uncertain zone

    # Conflict types
    CONFLICT_DIRECT = "direct"  # Same statement with opposite truth values
    CONFLICT_INDIRECT = "indirect"  # Inferred contradictions
    CONFLICT_CONTEXTUAL = "contextual"  # Context-dependent conflicts

    def __init__(self):
        """Initialize the KnowledgeIntegrity system."""
        self._facts: Dict[str, Fact] = {}
        self._content_index: Dict[str, str] = {}  # normalized content -> fact_id
        self._domain_index: Dict[str, Set[str]] = {}  # domain -> fact_ids
        self._contradictions: Dict[str, Contradiction] = {}
        self._resolution_history: List[Dict[str, Any]] = []
        self._max_history = 200

    def add_fact(
        self,
        content: str,
        domain: str,
        truth_value: float = 1.0,
        confidence: float = 1.0,
        source: str = "unknown",
        supporting_facts: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Fact:
        """
        Add a fact to the knowledge base.

        Args:
            content: The fact content
            domain: Domain of the fact
            truth_value: Initial truth value (0.0-1.0)
            confidence: Confidence level (0.0-1.0)
            source: Source of the fact
            supporting_facts: IDs of facts that support this one
            metadata: Additional metadata

        Returns:
            The created Fact
        """
        import uuid
        fact_id = f"fact_{uuid.uuid4().hex[:8]}"

        # Normalize content for indexing
        normalized = self._normalize_content(content)

        # Check if similar fact exists
        if normalized in self._content_index:
            existing_id = self._content_index[normalized]
            # Update existing fact with new evidence
            return self._update_existing_fact(
                existing_id, truth_value, confidence, source
            )

        # Create new fact
        fact = Fact(
            fact_id=fact_id,
            content=content,
            domain=domain,
            truth_value=max(0.0, min(1.0, truth_value)),
            confidence=max(0.0, min(1.0, confidence)),
            source=source,
            supporting_facts=supporting_facts or [],
            metadata=metadata or {},
        )

        # Store fact
        self._facts[fact_id] = fact
        self._content_index[normalized] = fact_id

        # Update domain index
        if domain not in self._domain_index:
            self._domain_index[domain] = set()
        self._domain_index[domain].add(fact_id)

        # Check for contradictions
        self._check_contradictions(fact)

        return fact

    def _normalize_content(self, content: str) -> str:
        """Normalize content for comparison."""
        return content.lower().strip()

    def _update_existing_fact(
        self,
        fact_id: str,
        new_truth: float,
        new_confidence: float,
        source: str,
    ) -> Fact:
        """Update an existing fact with new evidence."""
        fact = self._facts[fact_id]

        # Update truth value using weighted average
        total_confidence = fact.confidence + new_confidence
        if total_confidence > 0:
            fact.truth_value = (
                fact.truth_value * fact.confidence +
                new_truth * new_confidence
            ) / total_confidence

        # Update confidence (increase with more sources)
        fact.confidence = min(1.0, fact.confidence + 0.1)
        fact.updated_at = datetime.now()
        fact.source = f"{fact.source},{source}"

        # Add to evidence
        if new_truth >= self.TRUTH_THRESHOLD:
            fact.evidence_for += 1
        elif new_truth <= self.FALSE_THRESHOLD:
            fact.evidence_against += 1

        return fact

    def _check_contradictions(self, new_fact: Fact) -> None:
        """Check for contradictions with existing facts."""
        # Check for direct contradictions
        self._check_direct_contradictions(new_fact)

        # Check for indirect contradictions through supporting facts
        self._check_indirect_contradictions(new_fact)

    def _check_direct_contradictions(self, fact: Fact) -> None:
        """Check for direct contradictions."""
        # Look for facts with similar content but opposite truth values
        for other_id, other in self._facts.items():
            if other_id == fact.fact_id:
                continue

            # Check if same domain
            if other.domain != fact.domain:
                continue

            # Check for semantic opposition
            if self._are_contradictory(fact, other):
                self._create_contradiction(
                    fact, other,
                    self._determine_conflict_severity(fact, other),
                    self.CONFLICT_DIRECT
                )

    def _check_indirect_contradictions(self, fact: Fact) -> None:
        """Check for indirect contradictions through supporting facts."""
        # Check if supporting facts lead to contradiction
        for support_id in fact.supporting_facts:
            if support_id not in self._facts:
                continue
            support = self._facts[support_id]

            # Check if supporting fact contradicts other facts
            for other_id, other in self._facts.items():
                if other_id == fact.fact_id or other_id == support_id:
                    continue

                if self._are_contradictory(support, other):
                    self._create_contradiction(
                        fact, other,
                        "medium",
                        self.CONFLICT_INDIRECT
                    )

    def _are_contradictory(self, fact1: Fact, fact2: Fact) -> bool:
        """Check if two facts are contradictory."""
        # Simple contradiction: opposite truth values with high confidence
        if (fact1.truth_value >= self.TRUTH_THRESHOLD and
            fact2.truth_value <= self.FALSE_THRESHOLD and
            fact1.confidence >= 0.5 and fact2.confidence >= 0.5):
            return True

        if (fact1.truth_value <= self.FALSE_THRESHOLD and
            fact2.truth_value >= self.TRUTH_THRESHOLD and
            fact1.confidence >= 0.5 and fact2.confidence >= 0.5):
            return True

        # Check for negation in content
        content1 = fact1.content.lower()
        content2 = fact2.content.lower()

        # Simple negation check
        if "not " + content1 == content2 or content1 == "not " + content2:
            return True

        return False

    def _determine_conflict_severity(self, fact1: Fact, fact2: Fact) -> str:
        """Determine the severity of a contradiction."""
        # Higher confidence = higher severity
        avg_confidence = (fact1.confidence + fact2.confidence) / 2

        if avg_confidence >= 0.9:
            return "critical"
        elif avg_confidence >= 0.7:
            return "high"
        elif avg_confidence >= 0.5:
            return "medium"
        else:
            return "low"

    def _create_contradiction(
        self,
        fact1: Fact,
        fact2: Fact,
        severity: str,
        conflict_type: str,
    ) -> Contradiction:
        """Create a contradiction record."""
        import uuid
        contradiction_id = f"contra_{uuid.uuid4().hex[:8]}"

        # Generate resolution suggestions
        suggestions = self._generate_resolution_suggestions(fact1, fact2, conflict_type)

        contradiction = Contradiction(
            contradiction_id=contradiction_id,
            fact1_id=fact1.fact1_id if hasattr(fact1, 'fact1_id') else fact1.fact_id,
            fact2_id=fact2.fact_id,
            fact1_content=fact1.content,
            fact2_content=fact2.content,
            severity=severity,
            conflict_type=conflict_type,
            resolution_suggestions=suggestions,
        )

        self._contradictions[contradiction_id] = contradiction

        # Update facts with contradiction reference
        fact1.contradicting_facts.append(fact2.fact_id)
        fact2.contradicting_facts.append(fact1.fact_id)

        return contradiction

    def _generate_resolution_suggestions(
        self,
        fact1: Fact,
        fact2: Fact,
        conflict_type: str,
    ) -> List[str]:
        """Generate suggestions for resolving a contradiction."""
        suggestions = []

        if conflict_type == self.CONFLICT_DIRECT:
            suggestions.append("Verify source reliability for both facts")
            suggestions.append("Check for context differences")
            suggestions.append("Consider temporal changes (fact may have changed)")

        elif conflict_type == self.CONFLICT_INDIRECT:
            suggestions.append("Trace chain of supporting evidence")
            suggestions.append("Verify intermediate conclusions")

        # Confidence-based suggestions
        if fact1.confidence > fact2.confidence:
            suggestions.append(f"Fact 1 has higher confidence ({fact1.confidence:.2f})")
        elif fact2.confidence > fact1.confidence:
            suggestions.append(f"Fact 2 has higher confidence ({fact2.confidence:.2f})")
        else:
            suggestions.append("Both facts have equal confidence - additional evidence needed")

        return suggestions

    def resolve_contradiction(
        self,
        contradiction_id: str,
        resolution: str,
        resolved_fact_id: str,  # The fact to keep as true
    ) -> bool:
        """
        Resolve a contradiction.

        Args:
            contradiction_id: ID of the contradiction
            resolution: Description of the resolution
            resolved_fact_id: ID of the fact that is correct

        Returns:
            True if resolution was successful
        """
        contradiction = self._contradictions.get(contradiction_id)
        if not contradiction:
            return False

        # Mark the correct fact as true
        if resolved_fact_id in self._facts:
            resolved_fact = self._facts[resolved_fact_id]
            resolved_fact.truth_value = 1.0
            resolved_fact.confidence = min(1.0, resolved_fact.confidence + 0.2)

        # Mark the other fact as false
        other_id = (
            contradiction.fact2_id
            if resolved_fact_id == contradiction.fact1_id
            else contradiction.fact1_id
        )
        if other_id in self._facts:
            other_fact = self._facts[other_id]
            other_fact.truth_value = 0.0
            other_fact.confidence = min(1.0, other_fact.confidence + 0.1)

        # Mark contradiction as resolved
        contradiction.resolved = True
        contradiction.resolution = resolution
        contradiction.resolved_at = datetime.now()

        # Record in history
        self._resolution_history.append({
            "contradiction_id": contradiction_id,
            "resolution": resolution,
            "resolved_fact_id": resolved_fact_id,
            "timestamp": datetime.now().isoformat(),
        })

        if len(self._resolution_history) > self._max_history:
            self._resolution_history.pop(0)

        return True

    def get_fact(self, fact_id: str) -> Optional[Fact]:
        """Get a fact by ID."""
        return self._facts.get(fact_id)

    def query_truth(
        self,
        content: str,
        domain: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Query the truth value of a statement.

        Args:
            content: The content to query
            domain: Optional domain filter

        Returns:
            Fact information if found
        """
        normalized = self._normalize_content(content)
        fact_id = self._content_index.get(normalized)

        if fact_id:
            fact = self._facts[fact_id]
            if domain is None or fact.domain == domain:
                return fact.to_dict()

        return None

    def is_true(self, content: str, domain: Optional[str] = None) -> bool:
        """Check if a statement is considered true."""
        result = self.query_truth(content, domain)
        if result:
            return result["truth_value"] >= self.TRUTH_THRESHOLD
        return False

    def is_false(self, content: str, domain: Optional[str] = None) -> bool:
        """Check if a statement is considered false."""
        result = self.query_truth(content, domain)
        if result:
            return result["truth_value"] <= self.FALSE_THRESHOLD
        return False

    def is_uncertain(self, content: str, domain: Optional[str] = None) -> bool:
        """Check if a statement's truth value is uncertain."""
        result = self.query_truth(content, domain)
        if result:
            return self.FALSE_THRESHOLD < result["truth_value"] < self.TRUTH_THRESHOLD
        return True  # Unknown = uncertain

    def get_contradictions(
        self,
        unresolved_only: bool = False,
        severity: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get contradictions.

        Args:
            unresolved_only: Only return unresolved contradictions
            severity: Filter by severity level

        Returns:
            List of contradiction records
        """
        contradictions = list(self._contradictions.values())

        if unresolved_only:
            contradictions = [c for c in contradictions if not c.resolved]

        if severity:
            contradictions = [c for c in contradictions if c.severity == severity]

        return [c.to_dict() for c in contradictions]

    def get_facts_by_domain(self, domain: str) -> List[Fact]:
        """Get all facts in a domain."""
        fact_ids = self._domain_index.get(domain, set())
        return [self._facts[fid] for fid in fact_ids if fid in self._facts]

    def get_facts_by_truth(
        self,
        min_truth: float = 0.0,
        max_truth: float = 1.0,
    ) -> List[Fact]:
        """Get facts within a truth value range."""
        return [
            f for f in self._facts.values()
            if min_truth <= f.truth_value <= max_truth
        ]

    def add_evidence(
        self,
        fact_id: str,
        supports: bool,
        confidence: float = 1.0,
    ) -> bool:
        """
        Add evidence for or against a fact.

        Args:
            fact_id: The fact to update
            supports: True if evidence supports, False if contradicts
            confidence: Confidence of the evidence

        Returns:
            True if fact was updated
        """
        fact = self._facts.get(fact_id)
        if not fact:
            return False

        if supports:
            fact.evidence_for += 1
            # Update truth value
            adjustment = 0.1 * confidence
            fact.truth_value = min(1.0, fact.truth_value + adjustment)
        else:
            fact.evidence_against += 1
            adjustment = 0.1 * confidence
            fact.truth_value = max(0.0, fact.truth_value - adjustment)

        # Recalculate confidence
        total_evidence = fact.evidence_for + fact.evidence_against
        if total_evidence > 0:
            agreement_ratio = max(fact.evidence_for, fact.evidence_against) / total_evidence
            fact.confidence = agreement_ratio

        fact.updated_at = datetime.now()

        # Re-check contradictions
        self._check_contradictions(fact)

        return True

    def validate_consistency(self) -> Dict[str, Any]:
        """
        Validate the consistency of the knowledge base.

        Returns:
            Validation report
        """
        total_facts = len(self._facts)
        total_contradictions = len(self._contradictions)
        unresolved = sum(1 for c in self._contradictions.values() if not c.resolved)

        # Calculate consistency score
        if total_contradictions == 0:
            consistency_score = 1.0
        else:
            consistency_score = 1.0 - (unresolved / max(1, total_facts) * 0.5)

        # Find facts with low confidence
        low_confidence = [
            f for f in self._facts.values()
            if f.confidence < 0.5
        ]

        # Find uncertain facts
        uncertain_facts = [
            f for f in self._facts.values()
            if self.FALSE_THRESHOLD < f.truth_value < self.TRUTH_THRESHOLD
        ]

        return {
            "is_consistent": unresolved == 0,
            "consistency_score": consistency_score,
            "total_facts": total_facts,
            "total_contradictions": total_contradictions,
            "unresolved_contradictions": unresolved,
            "low_confidence_facts": len(low_confidence),
            "uncertain_facts": len(uncertain_facts),
            "domains": list(self._domain_index.keys()),
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get integrity system statistics."""
        by_domain = {d: len(ids) for d, ids in self._domain_index.items()}

        truth_distribution = {
            "true": sum(1 for f in self._facts.values() if f.truth_value >= self.TRUTH_THRESHOLD),
            "false": sum(1 for f in self._facts.values() if f.truth_value <= self.FALSE_THRESHOLD),
            "uncertain": sum(1 for f in self._facts.values()
                            if self.FALSE_THRESHOLD < f.truth_value < self.TRUTH_THRESHOLD),
        }

        return {
            "total_facts": len(self._facts),
            "total_contradictions": len(self._contradictions),
            "resolved_contradictions": sum(1 for c in self._contradictions.values() if c.resolved),
            "by_domain": by_domain,
            "truth_distribution": truth_distribution,
            "avg_confidence": sum(f.confidence for f in self._facts.values()) / max(1, len(self._facts)),
        }

    def get_resolution_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get history of contradiction resolutions."""
        return self._resolution_history[-limit:]

    def clear(self) -> None:
        """Clear all facts and contradictions."""
        self._facts.clear()
        self._content_index.clear()
        self._domain_index.clear()
        self._contradictions.clear()
        self._resolution_history.clear()


class TruthTracker:
    """
    Tracks changes in truth values over time.
    """

    def __init__(self):
        """Initialize the TruthTracker."""
        self._history: Dict[str, List[Dict[str, Any]]] = {}  # fact_id -> history

    def record(self, fact: Fact) -> None:
        """Record a fact's current state."""
        if fact.fact_id not in self._history:
            self._history[fact.fact_id] = []

        self._history[fact.fact_id].append({
            "truth_value": fact.truth_value,
            "confidence": fact.confidence,
            "evidence_for": fact.evidence_for,
            "evidence_against": fact.evidence_against,
            "timestamp": datetime.now().isoformat(),
        })

    def get_history(self, fact_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get history for a fact."""
        history = self._history.get(fact_id, [])
        return history[-limit:]

    def get_truth_trajectory(self, fact_id: str) -> List[Tuple[str, float]]:
        """Get truth value changes over time."""
        history = self._history.get(fact_id, [])
        return [(h["timestamp"], h["truth_value"]) for h in history]

    def get_stability_score(self, fact_id: str) -> float:
        """
        Calculate how stable a fact's truth value has been.

        Returns:
            Stability score (1.0 = completely stable)
        """
        history = self._history.get(fact_id, [])
        if len(history) < 2:
            return 1.0

        # Calculate variance in truth values
        values = [h["truth_value"] for h in history]
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)

        # Convert to stability score (lower variance = higher stability)
        return max(0.0, 1.0 - variance * 4)
