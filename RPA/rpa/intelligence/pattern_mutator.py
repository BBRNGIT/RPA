"""
Pattern Mutator - Version, fix, and deprecate patterns.

Handles pattern evolution through:
- Versioning: Track pattern changes over time
- Fixing: Apply corrections from error analysis
- Deprecation: Mark patterns as obsolete
- Linkage: Connect mutations to outcomes
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set
import uuid
import logging
import hashlib

from rpa.core.graph import Node, PatternGraph, NodeType
from rpa.memory import LongTermMemory
from rpa.learning.error_corrector import ErrorCorrector
from .outcome_evaluator import Outcome, OutcomeType

logger = logging.getLogger(__name__)


class MutationType(Enum):
    """Types of pattern mutations."""
    CREATION = "creation"           # Initial pattern creation
    FIX = "fix"                     # Bug fix
    ENHANCEMENT = "enhancement"     # Improvement without fixing
    REFACTOR = "refactor"           # Structural change
    GENERALIZATION = "generalization"  # Make more abstract
    SPECIALIZATION = "specialization"  # Make more specific
    DEPRECATION = "deprecation"     # Mark as obsolete
    RESTORATION = "restoration"     # Restore deprecated pattern


@dataclass
class PatternVersion:
    """
    Represents a version of a pattern.

    Tracks the evolution of a pattern over time.
    """
    version_id: str
    pattern_id: str
    version_number: int
    mutation_type: MutationType

    # Content at this version
    content: str
    label: str

    # Change tracking
    changed_from: Optional[str] = None      # Previous version ID
    change_reason: Optional[str] = None
    change_details: Dict[str, Any] = field(default_factory=dict)

    # Outcome linkage
    triggering_outcome_id: Optional[str] = None
    triggering_error: Optional[str] = None

    # Timing
    created_at: datetime = field(default_factory=datetime.now)

    # Hash for quick comparison
    content_hash: str = ""

    def __post_init__(self):
        """Generate hash after initialization."""
        if not self.content_hash:
            self.content_hash = hashlib.md5(self.content.encode()).hexdigest()[:12]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "version_id": self.version_id,
            "pattern_id": self.pattern_id,
            "version_number": self.version_number,
            "mutation_type": self.mutation_type.value,
            "content": self.content,
            "label": self.label,
            "changed_from": self.changed_from,
            "change_reason": self.change_reason,
            "change_details": self.change_details,
            "triggering_outcome_id": self.triggering_outcome_id,
            "triggering_error": self.triggering_error,
            "created_at": self.created_at.isoformat(),
            "content_hash": self.content_hash,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PatternVersion":
        """Create from dictionary."""
        data["mutation_type"] = MutationType(data["mutation_type"])
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)


class PatternMutator:
    """
    Handles pattern mutation and evolution.

    The mutator is the "repair mechanism" of the closed-loop system.
    When a pattern fails, the mutator:
    1. Analyzes the failure
    2. Generates a fix
    3. Creates a new version
    4. Links to the original pattern

    Example:
        mutator = PatternMutator(ltm)

        # Mutate based on outcome
        new_pattern = mutator.mutate_from_outcome(
            pattern=failing_pattern,
            outcome=failure_outcome
        )

        # Direct fix
        new_pattern = mutator.apply_fix(
            pattern=pattern,
            fix="Add null check before access"
        )
    """

    def __init__(
        self,
        ltm: Optional[LongTermMemory] = None,
        error_corrector: Optional[ErrorCorrector] = None
    ):
        """
        Initialize PatternMutator.

        Args:
            ltm: LongTermMemory instance for pattern storage
            error_corrector: Optional ErrorCorrector for fix generation
        """
        self.ltm = ltm
        self.error_corrector = error_corrector or ErrorCorrector()

        # Version tracking
        self._versions: Dict[str, List[PatternVersion]] = {}  # pattern_id -> versions
        self._version_index: Dict[str, PatternVersion] = {}    # version_id -> version

        # Mutation history
        self._mutations: List[Dict[str, Any]] = []
        self._max_history = 500

        # Statistics
        self._stats = {
            "total_mutations": 0,
            "by_type": {t.value: 0 for t in MutationType},
            "successful_fixes": 0,
            "failed_fixes": 0,
            "deprecations": 0,
            "restorations": 0,
        }

    def mutate_from_outcome(
        self,
        pattern: Node,
        outcome: Outcome,
        suggested_fix: Optional[str] = None,
    ) -> Optional[Node]:
        """
        Create a mutated pattern based on an outcome.

        Args:
            pattern: The pattern that failed
            outcome: The outcome describing the failure
            suggested_fix: Optional fix suggestion

        Returns:
            New mutated pattern, or None if mutation failed
        """
        if outcome.outcome_type == OutcomeType.SUCCESS:
            logger.info(f"Pattern {pattern.node_id} succeeded, no mutation needed")
            return None

        # Generate fix if not provided
        if not suggested_fix:
            suggested_fix = self._generate_fix(pattern, outcome)

        if not suggested_fix:
            logger.warning(f"Could not generate fix for pattern {pattern.node_id}")
            return None

        # Apply the fix
        return self.apply_fix(
            pattern=pattern,
            fix_description=suggested_fix,
            outcome_id=outcome.outcome_id,
            error_message=outcome.error_details.message if outcome.error_details else None
        )

    def apply_fix(
        self,
        pattern: Node,
        fix_description: str,
        outcome_id: Optional[str] = None,
        error_message: Optional[str] = None,
        new_content: Optional[str] = None,
    ) -> Optional[Node]:
        """
        Apply a fix to a pattern.

        Args:
            pattern: The pattern to fix
            fix_description: Description of the fix
            outcome_id: ID of outcome that triggered the fix
            error_message: The error message that prompted the fix
            new_content: Optional new content (if None, will generate)

        Returns:
            New mutated pattern
        """
        # Generate new content if not provided
        if not new_content:
            new_content = self._apply_fix_to_content(pattern.content, fix_description)

        if not new_content:
            return None

        # Create new version
        version_number = self._get_next_version_number(pattern.node_id)
        version_id = f"ver_{pattern.node_id}_{version_number}"

        version = PatternVersion(
            version_id=version_id,
            pattern_id=pattern.node_id,
            version_number=version_number,
            mutation_type=MutationType.FIX,
            content=new_content,
            label=f"{pattern.label}_v{version_number}",
            changed_from=self._get_latest_version_id(pattern.node_id),
            change_reason=fix_description,
            triggering_outcome_id=outcome_id,
            triggering_error=error_message,
        )

        # Create new pattern node
        new_pattern = Node.create_pattern(
            label=version.label,
            content=new_content,
            hierarchy_level=pattern.hierarchy_level,
            domain=pattern.domain,
        )
        new_pattern.metadata = {
            **pattern.metadata,
            "version_id": version_id,
            "parent_pattern_id": pattern.node_id,
            "mutation_type": MutationType.FIX.value,
            "fix_description": fix_description,
            "created_from_outcome": outcome_id,
        }

        # Track version
        self._add_version(pattern.node_id, version)

        # Store in LTM if available
        if self.ltm:
            self.ltm.add_node(new_pattern)

        self._stats["total_mutations"] += 1
        self._stats["by_type"][MutationType.FIX.value] += 1

        logger.info(
            f"Created mutation {version_id} for pattern {pattern.node_id}: {fix_description[:50]}..."
        )

        return new_pattern

    def deprecate_pattern(
        self,
        pattern_id: str,
        reason: str,
        replacement_id: Optional[str] = None
    ) -> bool:
        """
        Deprecate a pattern.

        Args:
            pattern_id: ID of pattern to deprecate
            reason: Reason for deprecation
            replacement_id: Optional ID of replacement pattern

        Returns:
            True if deprecation successful
        """
        if not self.ltm:
            logger.warning("No LTM available for deprecation")
            return False

        pattern = self.ltm.get_pattern(pattern_id)
        if not pattern:
            return False

        # Create deprecation version
        version_number = self._get_next_version_number(pattern_id)
        version = PatternVersion(
            version_id=f"ver_{pattern_id}_{version_number}",
            pattern_id=pattern_id,
            version_number=version_number,
            mutation_type=MutationType.DEPRECATION,
            content=pattern.content,
            label=f"{pattern.label}_deprecated",
            changed_from=self._get_latest_version_id(pattern_id),
            change_reason=reason,
        )

        self._add_version(pattern_id, version)

        # Apply deprecation
        success = self.ltm.deprecate_pattern(pattern_id, reason)

        if success:
            pattern.metadata["replacement_id"] = replacement_id
            self._stats["deprecations"] += 1
            self._stats["by_type"][MutationType.DEPRECATION.value] += 1
            logger.info(f"Deprecated pattern {pattern_id}: {reason}")

        return success

    def restore_pattern(self, pattern_id: str, reason: str = "") -> bool:
        """
        Restore a deprecated pattern.

        Args:
            pattern_id: ID of pattern to restore
            reason: Reason for restoration

        Returns:
            True if restoration successful
        """
        if not self.ltm:
            return False

        success = self.ltm.restore_pattern(pattern_id)

        if success:
            version_number = self._get_next_version_number(pattern_id)
            version = PatternVersion(
                version_id=f"ver_{pattern_id}_{version_number}",
                pattern_id=pattern_id,
                version_number=version_number,
                mutation_type=MutationType.RESTORATION,
                content="",  # Will be filled from LTM
                label=f"restored",
                change_reason=reason,
            )

            pattern = self.ltm.get_pattern(pattern_id)
            if pattern:
                version.content = pattern.content
                version.label = pattern.label

            self._add_version(pattern_id, version)
            self._stats["restorations"] += 1
            self._stats["by_type"][MutationType.RESTORATION.value] += 1
            logger.info(f"Restored pattern {pattern_id}: {reason}")

        return success

    def generalize_pattern(
        self,
        pattern: Node,
        abstraction: str,
    ) -> Optional[Node]:
        """
        Create a generalized version of a pattern.

        Args:
            pattern: The pattern to generalize
            abstraction: Description of the abstraction

        Returns:
            New generalized pattern
        """
        version_number = self._get_next_version_number(pattern.node_id)
        version_id = f"ver_{pattern.node_id}_{version_number}"

        # Create generalized content (abstract out specifics)
        generalized_content = self._create_generalized_content(
            pattern.content, abstraction
        )

        version = PatternVersion(
            version_id=version_id,
            pattern_id=pattern.node_id,
            version_number=version_number,
            mutation_type=MutationType.GENERALIZATION,
            content=generalized_content,
            label=f"{pattern.label}_generalized",
            changed_from=self._get_latest_version_id(pattern.node_id),
            change_reason=abstraction,
        )

        # Create new pattern
        new_pattern = Node.create_pattern(
            label=version.label,
            content=generalized_content,
            hierarchy_level=pattern.hierarchy_level - 1,  # Higher abstraction
            domain=pattern.domain,
        )
        new_pattern.metadata = {
            "version_id": version_id,
            "parent_pattern_id": pattern.node_id,
            "mutation_type": MutationType.GENERALIZATION.value,
            "abstraction": abstraction,
        }

        self._add_version(pattern.node_id, version)

        if self.ltm:
            self.ltm.add_node(new_pattern)

        self._stats["total_mutations"] += 1
        self._stats["by_type"][MutationType.GENERALIZATION.value] += 1

        return new_pattern

    def get_pattern_history(self, pattern_id: str) -> List[PatternVersion]:
        """
        Get version history for a pattern.

        Args:
            pattern_id: The pattern ID

        Returns:
            List of versions, oldest first
        """
        return self._versions.get(pattern_id, [])

    def get_latest_version(self, pattern_id: str) -> Optional[PatternVersion]:
        """Get the latest version of a pattern."""
        versions = self._versions.get(pattern_id, [])
        return versions[-1] if versions else None

    def get_version(self, version_id: str) -> Optional[PatternVersion]:
        """Get a specific version."""
        return self._version_index.get(version_id)

    def compare_versions(
        self,
        version_id1: str,
        version_id2: str
    ) -> Dict[str, Any]:
        """
        Compare two versions of a pattern.

        Returns:
            Comparison details
        """
        v1 = self._version_index.get(version_id1)
        v2 = self._version_index.get(version_id2)

        if not v1 or not v2:
            return {"error": "Version not found"}

        return {
            "version1": version_id1,
            "version2": version_id2,
            "v1_type": v1.mutation_type.value,
            "v2_type": v2.mutation_type.value,
            "v1_hash": v1.content_hash,
            "v2_hash": v2.content_hash,
            "content_changed": v1.content_hash != v2.content_hash,
            "v1_length": len(v1.content),
            "v2_length": len(v2.content),
            "version_diff": v2.version_number - v1.version_number,
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get mutator statistics."""
        return {
            **self._stats,
            "total_versions": len(self._version_index),
            "patterns_with_versions": len(self._versions),
        }

    def _generate_fix(self, pattern: Node, outcome: Outcome) -> Optional[str]:
        """Generate a fix description from an outcome."""
        if not outcome.error_details:
            return self._infer_fix_from_outcome_type(outcome)

        error = outcome.error_details

        # Use suggestions from error classification
        if error.suggestions:
            return error.suggestions[0]

        # Use error corrector
        correction = self.error_corrector.suggest_correction(
            error=error,
            code_context=pattern.content
        )

        if correction:
            return correction.description

        return None

    def _infer_fix_from_outcome_type(self, outcome: Outcome) -> Optional[str]:
        """Infer fix from outcome type when no error details."""
        fixes = {
            OutcomeType.GAP: "Add missing knowledge pattern",
            OutcomeType.INVALID: "Fix structural issues",
            OutcomeType.TIMEOUT: "Optimize for performance",
            OutcomeType.PARTIAL: "Handle edge cases",
        }
        return fixes.get(outcome.outcome_type)

    def _apply_fix_to_content(self, content: str, fix_description: str) -> Optional[str]:
        """Apply a fix to pattern content."""
        # Simple fix application strategies

        # Check for common fix patterns
        fix_lower = fix_description.lower()

        if "null check" in fix_lower or "none check" in fix_lower:
            return self._add_null_check(content)

        if "add" in fix_lower and "import" in fix_lower:
            return self._add_import(content, fix_description)

        if "fix" in fix_lower and "indentation" in fix_lower:
            return self._fix_indentation(content)

        # Default: add fix as comment
        return f"# Fixed: {fix_description}\n{content}"

    def _add_null_check(self, content: str) -> str:
        """Add null check to content."""
        lines = content.split("\n")
        new_lines = []

        for line in lines:
            new_lines.append(line)
            # Add null check after variable assignment
            if "=" in line and not line.strip().startswith("#"):
                var_name = line.split("=")[0].strip()
                if var_name and not var_name.startswith("self."):
                    indent = len(line) - len(line.lstrip())
                    new_lines.append(" " * indent + f"if {var_name} is None: return None")

        return "\n".join(new_lines)

    def _add_import(self, content: str, fix: str) -> str:
        """Add import statement."""
        # Extract module name from fix
        import re
        match = re.search(r"import\s+(\w+)", fix)
        if match:
            module = match.group(1)
            return f"import {module}\n{content}"
        return content

    def _fix_indentation(self, content: str) -> str:
        """Fix indentation issues."""
        lines = content.split("\n")
        fixed_lines = []
        indent_level = 0

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            # Decrease indent for dedent keywords
            if stripped.startswith(("return", "pass", "break", "continue", "else:", "elif ", "except", "finally:")):
                indent_level = max(0, indent_level - 1)

            fixed_lines.append("    " * indent_level + stripped)

            # Increase indent after colon
            if stripped.endswith(":"):
                indent_level += 1

        return "\n".join(fixed_lines)

    def _create_generalized_content(self, content: str, abstraction: str) -> str:
        """Create generalized version of content."""
        # Simple generalization: add abstraction as docstring
        return f'"""\nGeneralization: {abstraction}\n"""\n{content}'

    def _get_next_version_number(self, pattern_id: str) -> int:
        """Get next version number for a pattern."""
        versions = self._versions.get(pattern_id, [])
        return len(versions) + 1

    def _get_latest_version_id(self, pattern_id: str) -> Optional[str]:
        """Get ID of latest version."""
        versions = self._versions.get(pattern_id, [])
        return versions[-1].version_id if versions else None

    def _add_version(self, pattern_id: str, version: PatternVersion) -> None:
        """Add a version to tracking."""
        if pattern_id not in self._versions:
            self._versions[pattern_id] = []
        self._versions[pattern_id].append(version)
        self._version_index[version.version_id] = version

        # Record in history
        self._mutations.append({
            "pattern_id": pattern_id,
            "version_id": version.version_id,
            "mutation_type": version.mutation_type.value,
            "timestamp": version.created_at.isoformat(),
        })

        # Trim history
        if len(self._mutations) > self._max_history:
            self._mutations = self._mutations[-self._max_history:]

    def export_versions(self) -> List[Dict[str, Any]]:
        """Export all versions as dictionaries."""
        return [v.to_dict() for v in self._version_index.values()]

    def import_versions(self, versions: List[Dict[str, Any]]) -> int:
        """
        Import versions from dictionaries.

        Returns:
            Number of versions imported
        """
        imported = 0

        for data in versions:
            version = PatternVersion.from_dict(data)

            if version.pattern_id not in self._versions:
                self._versions[version.pattern_id] = []

            self._versions[version.pattern_id].append(version)
            self._version_index[version.version_id] = version
            imported += 1

        # Sort versions by number for each pattern
        for pattern_id in self._versions:
            self._versions[pattern_id].sort(key=lambda v: v.version_number)

        return imported
