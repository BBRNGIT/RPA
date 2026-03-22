"""
Pattern Mutator - Version, fix, and deprecate patterns on failure.

Provides pattern evolution capabilities:
- Create new versions of patterns on failure
- Link mutations to original pattern
- Track mutation reasons and history
- Deprecate failing patterns
- Restore deprecated patterns

This module enables RPA to learn from mistakes by evolving
patterns rather than simply accumulating them.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid
import logging
import hashlib

from rpa.core.graph import Node, PatternGraph, NodeType, Edge, EdgeType
from rpa.learning.error_classifier import ClassifiedError
from rpa.memory.ltm import LongTermMemory

logger = logging.getLogger(__name__)


class MutationType(Enum):
    """Types of pattern mutations."""
    FIX = "fix"                     # Fixed a bug/error
    REFINEMENT = "refinement"       # Improved pattern
    ALTERNATIVE = "alternative"     # Alternative approach
    SIMPLIFICATION = "simplification"  # Simplified pattern
    EXTENSION = "extension"         # Extended pattern
    DEPRECATION = "deprecation"     # Pattern deprecated
    RESTORATION = "restoration"     # Pattern restored


@dataclass
class MutationRecord:
    """Record of a pattern mutation."""
    record_id: str
    original_pattern_id: str
    new_pattern_id: Optional[str]
    mutation_type: MutationType
    reason: str
    error_context: Optional[str] = None
    fix_applied: Optional[str] = None
    confidence_change: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "record_id": self.record_id,
            "original_pattern_id": self.original_pattern_id,
            "new_pattern_id": self.new_pattern_id,
            "mutation_type": self.mutation_type.value,
            "reason": self.reason,
            "error_context": self.error_context,
            "fix_applied": self.fix_applied,
            "confidence_change": self.confidence_change,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class PatternVersion:
    """Version information for a pattern."""
    pattern_id: str
    version_number: int
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    deprecated: bool = False
    deprecated_at: Optional[datetime] = None
    deprecation_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "pattern_id": self.pattern_id,
            "version_number": self.version_number,
            "parent_id": self.parent_id,
            "children_ids": self.children_ids,
            "created_at": self.created_at.isoformat(),
            "deprecated": self.deprecated,
            "deprecated_at": self.deprecated_at.isoformat() if self.deprecated_at else None,
            "deprecation_reason": self.deprecation_reason,
        }


class PatternMutator:
    """
    Mutate patterns based on failure analysis.

    Provides pattern evolution:
    - Create fixed versions from failed patterns
    - Track version history
    - Deprecate consistently failing patterns
    - Restore patterns when needed
    - Link mutations to failure analysis

    Integration points:
    - ErrorClassifier: Get fix suggestions
    - RetryEngine: Apply fixes from retry attempts
    - ReinforcementTracker: Check deprecation status
    """

    # Mutation thresholds
    DEPRECATION_FAILURE_COUNT = 5
    MIN_CONFIDENCE_FOR_MUTATION = 0.3
    MAX_VERSIONS = 10  # Max versions before forcing deprecation

    def __init__(self, ltm: Optional[LongTermMemory] = None):
        """
        Initialize the PatternMutator.

        Args:
            ltm: Optional LongTermMemory instance for persistence
        """
        self.ltm = ltm

        # Version tracking
        self._versions: Dict[str, PatternVersion] = {}

        # Mutation history
        self._mutation_history: Dict[str, List[MutationRecord]] = {}

        # Statistics
        self._stats = {
            "total_mutations": 0,
            "by_type": {t.value: 0 for t in MutationType},
            "total_deprecations": 0,
            "total_restorations": 0,
        }

    def mutate_pattern(
        self,
        original: Node,
        new_content: str,
        mutation_type: MutationType,
        reason: str,
        error_context: Optional[str] = None,
        graph: Optional[PatternGraph] = None,
    ) -> Node:
        """
        Create a mutated version of a pattern.

        Args:
            original: The original pattern node
            new_content: The new content for the mutation
            mutation_type: Type of mutation
            reason: Reason for the mutation
            error_context: Optional error context that triggered mutation
            graph: Optional pattern graph for edge creation

        Returns:
            The new mutated node
        """
        self._stats["total_mutations"] += 1
        self._stats["by_type"][mutation_type.value] += 1

        # Get version info
        version_info = self._get_or_create_version(original.node_id)

        # Check version limit
        if version_info.version_number >= self.MAX_VERSIONS:
            logger.warning(
                f"Pattern {original.node_id} has reached max versions, "
                "consider deprecation"
            )

        # Create new version number
        new_version = version_info.version_number + 1

        # Create new pattern ID
        new_id = self._generate_version_id(original.node_id, new_version)

        # Create new node
        new_node = Node(
            node_id=new_id,
            label=f"{original.label}_v{new_version}",
            node_type=original.node_type,
            content=new_content,
            hierarchy_level=original.hierarchy_level,
            domain=original.domain,
            source=f"mutation:{original.node_id}",
            confidence=original.confidence,
            metadata={
                **original.metadata,
                "mutation_type": mutation_type.value,
                "mutation_reason": reason,
                "parent_pattern_id": original.node_id,
                "version": new_version,
                "mutated_at": datetime.now().isoformat(),
            },
        )

        # Update version info
        version_info.children_ids.append(new_id)

        # Create new version info for the mutation
        new_version_info = PatternVersion(
            pattern_id=new_id,
            version_number=new_version,
            parent_id=original.node_id,
        )
        self._versions[new_id] = new_version_info

        # Create mutation record
        record = MutationRecord(
            record_id=f"mut_{uuid.uuid4().hex[:8]}",
            original_pattern_id=original.node_id,
            new_pattern_id=new_id,
            mutation_type=mutation_type,
            reason=reason,
            error_context=error_context,
            confidence_change=new_node.confidence - original.confidence,
        )

        self._add_to_history(original.node_id, record)
        self._add_to_history(new_id, record)

        # Create edge in graph if provided
        if graph:
            edge = Edge(
                edge_id=f"mut_{new_id}",
                source_id=new_id,
                target_id=original.node_id,
                edge_type=EdgeType.RELATED_TO,
                weight=0.8,
                metadata={
                    "relation": "mutation",
                    "mutation_type": mutation_type.value,
                },
            )
            graph.add_edge(edge)

        # Store in LTM if provided
        if self.ltm:
            self.ltm.add_node(new_node)
            if graph:
                self.ltm.add_edge(edge)

        logger.info(
            f"Created mutation {new_id} from {original.node_id}: "
            f"{mutation_type.value}"
        )

        return new_node

    def deprecate_pattern(
        self,
        pattern_id: str,
        reason: str,
        replacement_id: Optional[str] = None,
    ) -> bool:
        """
        Deprecate a pattern.

        Args:
            pattern_id: ID of pattern to deprecate
            reason: Reason for deprecation
            replacement_id: Optional ID of replacement pattern

        Returns:
            True if deprecation was successful
        """
        version_info = self._get_or_create_version(pattern_id)

        if version_info.deprecated:
            logger.warning(f"Pattern {pattern_id} is already deprecated")
            return False

        version_info.deprecated = True
        version_info.deprecated_at = datetime.now()
        version_info.deprecation_reason = reason

        # Create mutation record
        record = MutationRecord(
            record_id=f"mut_{uuid.uuid4().hex[:8]}",
            original_pattern_id=pattern_id,
            new_pattern_id=replacement_id,
            mutation_type=MutationType.DEPRECATION,
            reason=reason,
            metadata={"replacement_id": replacement_id},
        )

        self._add_to_history(pattern_id, record)

        # Update node in LTM if available
        if self.ltm:
            node = self.ltm.get_pattern(pattern_id)
            if node:
                node.is_valid = False
                node.metadata["deprecated"] = True
                node.metadata["deprecation_reason"] = reason
                node.metadata["deprecated_at"] = datetime.now().isoformat()
                if replacement_id:
                    node.metadata["replacement_id"] = replacement_id
                self.ltm.update_pattern(node)

        self._stats["total_deprecations"] += 1

        logger.info(f"Deprecated pattern {pattern_id}: {reason}")

        return True

    def restore_pattern(
        self,
        pattern_id: str,
        reason: str,
    ) -> bool:
        """
        Restore a deprecated pattern.

        Args:
            pattern_id: ID of pattern to restore
            reason: Reason for restoration

        Returns:
            True if restoration was successful
        """
        version_info = self._versions.get(pattern_id)

        if not version_info or not version_info.deprecated:
            logger.warning(f"Pattern {pattern_id} is not deprecated")
            return False

        version_info.deprecated = False
        version_info.deprecated_at = None
        version_info.deprecation_reason = None

        # Create mutation record
        record = MutationRecord(
            record_id=f"mut_{uuid.uuid4().hex[:8]}",
            original_pattern_id=pattern_id,
            new_pattern_id=pattern_id,
            mutation_type=MutationType.RESTORATION,
            reason=reason,
        )

        self._add_to_history(pattern_id, record)

        # Update node in LTM if available
        if self.ltm:
            node = self.ltm.get_pattern(pattern_id)
            if node:
                node.is_valid = True
                node.metadata["deprecated"] = False
                node.metadata["restored_at"] = datetime.now().isoformat()
                node.metadata["restoration_reason"] = reason
                self.ltm.update_pattern(node)

        self._stats["total_restorations"] += 1

        logger.info(f"Restored pattern {pattern_id}: {reason}")

        return True

    def get_version_history(self, pattern_id: str) -> List[PatternVersion]:
        """Get version history for a pattern."""
        versions = []

        # Get current version
        current = self._versions.get(pattern_id)
        if current:
            versions.append(current)

            # Get ancestors
            parent_id = current.parent_id
            while parent_id:
                parent = self._versions.get(parent_id)
                if parent:
                    versions.append(parent)
                    parent_id = parent.parent_id
                else:
                    break

        return versions

    def get_mutation_history(
        self,
        pattern_id: str,
        limit: int = 20,
    ) -> List[MutationRecord]:
        """Get mutation history for a pattern."""
        history = self._mutation_history.get(pattern_id, [])
        return history[-limit:]

    def is_deprecated(self, pattern_id: str) -> bool:
        """Check if a pattern is deprecated."""
        version = self._versions.get(pattern_id)
        return version.deprecated if version else False

    def get_latest_version(self, pattern_id: str) -> Optional[str]:
        """Get the latest version of a pattern."""
        version = self._versions.get(pattern_id)
        if not version:
            return pattern_id

        # Check children
        if version.children_ids:
            # Get the most recent child
            latest = version.children_ids[-1]
            return self.get_latest_version(latest)

        return pattern_id

    def get_pattern_family(self, pattern_id: str) -> Dict[str, Any]:
        """Get the full family tree of a pattern."""
        version = self._versions.get(pattern_id)
        if not version:
            return {"pattern_id": pattern_id, "versions": []}

        # Get all versions
        all_versions = self.get_version_history(pattern_id)

        # Get descendants
        descendants = self._get_all_descendants(pattern_id)

        return {
            "pattern_id": pattern_id,
            "current_version": version.version_number,
            "deprecated": version.deprecated,
            "ancestors": [v.pattern_id for v in all_versions[1:]],
            "descendants": descendants,
            "total_versions": len(all_versions) + len(descendants),
        }

    def suggest_fix(
        self,
        pattern: Node,
        error: ClassifiedError,
    ) -> Optional[str]:
        """
        Suggest a fix for a pattern based on error classification.

        Args:
            pattern: The failed pattern
            error: The classified error

        Returns:
            Suggested fix content or None
        """
        # Use error suggestions as guidance
        suggestions = error.suggestions
        if not suggestions:
            return None

        # For now, return the first suggestion
        # A more sophisticated implementation would try to apply
        # the suggestion to the actual content
        return suggestions[0]

    def apply_fix(
        self,
        pattern: Node,
        fix_description: str,
        fixed_content: Optional[str] = None,
        graph: Optional[PatternGraph] = None,
    ) -> Optional[Node]:
        """
        Apply a fix to a pattern.

        Args:
            pattern: The pattern to fix
            fix_description: Description of the fix
            fixed_content: Optional fixed content (will be generated if not provided)
            graph: Optional pattern graph

        Returns:
            The new fixed pattern node
        """
        if fixed_content is None:
            # Can't apply fix without content
            logger.warning(f"No fixed content provided for {pattern.node_id}")
            return None

        return self.mutate_pattern(
            original=pattern,
            new_content=fixed_content,
            mutation_type=MutationType.FIX,
            reason=fix_description,
            error_context=pattern.content,
            graph=graph,
        )

    def get_statistics(self) -> Dict[str, Any]:
        """Get mutator statistics."""
        return {
            **self._stats,
            "total_patterns_versioned": len(self._versions),
            "deprecated_patterns": sum(
                1 for v in self._versions.values() if v.deprecated
            ),
        }

    def _get_or_create_version(self, pattern_id: str) -> PatternVersion:
        """Get or create version info for a pattern."""
        if pattern_id not in self._versions:
            self._versions[pattern_id] = PatternVersion(
                pattern_id=pattern_id,
                version_number=1,
            )
        return self._versions[pattern_id]

    def _generate_version_id(self, original_id: str, version: int) -> str:
        """Generate a new version ID."""
        return f"{original_id}_v{version}"

    def _add_to_history(self, pattern_id: str, record: MutationRecord) -> None:
        """Add record to mutation history."""
        if pattern_id not in self._mutation_history:
            self._mutation_history[pattern_id] = []
        self._mutation_history[pattern_id].append(record)

    def _get_all_descendants(self, pattern_id: str) -> List[str]:
        """Get all descendant pattern IDs."""
        version = self._versions.get(pattern_id)
        if not version or not version.children_ids:
            return []

        descendants = []
        for child_id in version.children_ids:
            descendants.append(child_id)
            descendants.extend(self._get_all_descendants(child_id))

        return descendants

    def to_dict(self) -> Dict[str, Any]:
        """Serialize mutator state to dictionary."""
        return {
            "versions": {
                pid: v.to_dict() for pid, v in self._versions.items()
            },
            "stats": self._stats,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], ltm: Optional[LongTermMemory] = None) -> "PatternMutator":
        """Deserialize mutator from dictionary."""
        mutator = cls(ltm=ltm)

        for pid, vdata in data.get("versions", {}).items():
            version = PatternVersion(pattern_id=pid)
            version.version_number = vdata.get("version_number", 1)
            version.parent_id = vdata.get("parent_id")
            version.children_ids = vdata.get("children_ids", [])
            version.deprecated = vdata.get("deprecated", False)
            version.deprecation_reason = vdata.get("deprecation_reason")

            if vdata.get("created_at"):
                version.created_at = datetime.fromisoformat(vdata["created_at"])
            if vdata.get("deprecated_at"):
                version.deprecated_at = datetime.fromisoformat(vdata["deprecated_at"])

            mutator._versions[pid] = version

        mutator._stats = data.get("stats", mutator._stats)

        return mutator
