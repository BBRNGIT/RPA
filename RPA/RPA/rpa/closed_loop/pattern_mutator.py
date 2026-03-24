"""
Pattern Mutator - Version, fix, and deprecate patterns based on outcomes.

Handles pattern evolution:
- Create new versions when patterns fail
- Track mutation history and lineage
- Apply suggested fixes
- Deprecate patterns that consistently fail
- Link mutations to their originating errors

This is the core of the self-improving system - patterns don't just
stay static, they evolve based on real-world performance.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
import uuid
import difflib
import logging

from rpa.core.node import Node, NodeType
from rpa.memory.ltm import LongTermMemory
from rpa.learning.error_corrector import ErrorCorrector
from rpa.learning.correction_analyzer import CorrectionAnalyzer
from rpa.closed_loop.outcome_evaluator import Outcome, OutcomeType

logger = logging.getLogger(__name__)


class MutationType(Enum):
    """Types of pattern mutations."""
    FIX = "fix"                     # Fix based on error
    REFINE = "refine"               # Minor refinement
    GENERALIZE = "generalize"       # Make pattern more general
    SPECIALIZE = "specialize"       # Make pattern more specific
    MERGE = "merge"                 # Merge with another pattern
    SPLIT = "split"                 # Split into multiple patterns
    DEPRECATE = "deprecate"         # Mark as deprecated
    RESTORE = "restore"             # Restore from deprecated


@dataclass
class PatternVersion:
    """Represents a version of a pattern."""
    version_id: str
    pattern_id: str
    version_number: int
    content: str
    label: str
    
    # Lineage
    parent_version_id: Optional[str] = None
    mutation_type: Optional[MutationType] = None
    mutation_reason: str = ""
    source_outcome_id: Optional[str] = None
    source_error_id: Optional[str] = None
    
    # Performance tracking
    success_count: int = 0
    failure_count: int = 0
    last_outcome: Optional[datetime] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    is_deprecated: bool = False
    deprecation_reason: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "version_id": self.version_id,
            "pattern_id": self.pattern_id,
            "version_number": self.version_number,
            "content": self.content,
            "label": self.label,
            "parent_version_id": self.parent_version_id,
            "mutation_type": self.mutation_type.value if self.mutation_type else None,
            "mutation_reason": self.mutation_reason,
            "source_outcome_id": self.source_outcome_id,
            "source_error_id": self.source_error_id,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "last_outcome": self.last_outcome.isoformat() if self.last_outcome else None,
            "created_at": self.created_at.isoformat(),
            "is_active": self.is_active,
            "is_deprecated": self.is_deprecated,
            "deprecation_reason": self.deprecation_reason,
        }


@dataclass
class MutationRecord:
    """Record of a pattern mutation."""
    record_id: str
    pattern_id: str
    mutation_type: MutationType
    previous_version_id: Optional[str]
    new_version_id: Optional[str]
    reason: str
    changes: Dict[str, Any] = field(default_factory=dict)
    outcome_id: Optional[str] = None
    error_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "record_id": self.record_id,
            "pattern_id": self.pattern_id,
            "mutation_type": self.mutation_type.value,
            "previous_version_id": self.previous_version_id,
            "new_version_id": self.new_version_id,
            "reason": self.reason,
            "changes": self.changes,
            "outcome_id": self.outcome_id,
            "error_id": self.error_id,
            "timestamp": self.timestamp.isoformat(),
        }


class PatternMutator:
    """
    Mutate patterns based on outcomes and errors.
    
    This system enables patterns to evolve:
    - Create new versions when patterns fail
    - Apply fixes from ErrorCorrector
    - Track mutation lineage
    - Deprecate consistently failing patterns
    - Restore patterns if needed
    
    The mutation model is deterministic - mutations happen based on
    actual failure data, not random exploration.
    """
    
    # Mutation thresholds
    FAILURE_THRESHOLD_FOR_MUTATION = 2    # Failures before considering mutation
    FAILURE_THRESHOLD_FOR_DEPRECATION = 5 # Failures before considering deprecation
    MIN_SUCCESS_RATE_TO_KEEP = 0.3        # Minimum success rate to keep active
    
    def __init__(
        self,
        ltm: Optional[LongTermMemory] = None,
        error_corrector: Optional[ErrorCorrector] = None,
        correction_analyzer: Optional[CorrectionAnalyzer] = None,
    ):
        """
        Initialize PatternMutator.
        
        Args:
            ltm: LongTermMemory instance
            error_corrector: ErrorCorrector for generating fixes
            correction_analyzer: CorrectionAnalyzer for learning from fixes
        """
        self.ltm = ltm
        self.error_corrector = error_corrector or ErrorCorrector()
        self.correction_analyzer = correction_analyzer or CorrectionAnalyzer()
        
        # Version tracking
        self._versions: Dict[str, List[PatternVersion]] = {}  # pattern_id -> versions
        self._active_versions: Dict[str, str] = {}            # pattern_id -> active version_id
        self._version_by_id: Dict[str, PatternVersion] = {}   # version_id -> version
        
        # Mutation history
        self._mutations: List[MutationRecord] = []
        self._max_history = 10000
        
        # Statistics
        self._stats = {
            "total_mutations": 0,
            "by_type": {t.value: 0 for t in MutationType},
            "patterns_versioned": 0,
            "patterns_deprecated": 0,
            "patterns_restored": 0,
            "successful_fixes": 0,
            "failed_fixes": 0,
        }
    
    def process_outcome(self, outcome: Outcome) -> Optional[MutationRecord]:
        """
        Process an outcome and determine if mutation is needed.
        
        This is the main entry point - outcomes trigger mutation decisions.
        
        Args:
            outcome: The outcome to process
            
        Returns:
            MutationRecord if mutation occurred, None otherwise
        """
        pattern_id = outcome.pattern_id
        
        # Ensure pattern is tracked
        self._ensure_pattern_tracked(pattern_id)
        
        # Update version stats
        active_version_id = self._active_versions.get(pattern_id)
        if active_version_id:
            version = self._version_by_id.get(active_version_id)
            if version:
                if outcome.outcome_type == OutcomeType.SUCCESS:
                    version.success_count += 1
                elif outcome.outcome_type in (OutcomeType.FAILURE, OutcomeType.ERROR):
                    version.failure_count += 1
                version.last_outcome = datetime.now()
        
        # Check if mutation is needed
        if not self._should_mutate(outcome, pattern_id):
            return None
        
        # Determine mutation type
        mutation_type, reason = self._determine_mutation(outcome, pattern_id)
        
        # Execute mutation
        if mutation_type == MutationType.DEPRECATE:
            return self._deprecate_pattern(pattern_id, outcome, reason)
        elif mutation_type == MutationType.FIX:
            return self._fix_pattern(pattern_id, outcome, reason)
        else:
            return self._apply_mutation(pattern_id, mutation_type, outcome, reason)
    
    def _should_mutate(self, outcome: Outcome, pattern_id: str) -> bool:
        """Determine if a pattern should be mutated."""
        
        # Don't mutate successful patterns
        if outcome.outcome_type == OutcomeType.SUCCESS:
            return False
        
        # Always consider mutation on error
        if outcome.outcome_type == OutcomeType.ERROR:
            return True
        
        # Check failure history
        versions = self._versions.get(pattern_id, [])
        if not versions:
            return False
        
        active = self._get_active_version(pattern_id)
        if not active:
            return False
        
        # Check if failure threshold reached
        if active.failure_count >= self.FAILURE_THRESHOLD_FOR_MUTATION:
            # Check success rate
            total = active.success_count + active.failure_count
            if total > 0:
                success_rate = active.success_count / total
                if success_rate < self.MIN_SUCCESS_RATE_TO_KEEP:
                    return True
        
        # Check outcome's mutation signal
        if outcome.should_mutate:
            return True
        
        # Check for deprecation signal
        if outcome.should_deprecate:
            return True
        
        return False
    
    def _determine_mutation(self, outcome: Outcome, pattern_id: str) -> Tuple[MutationType, str]:
        """Determine the type of mutation needed."""
        
        active = self._get_active_version(pattern_id)
        
        # Check for deprecation
        if outcome.should_deprecate:
            return MutationType.DEPRECATE, "Pattern flagged for deprecation"
        
        if active and active.failure_count >= self.FAILURE_THRESHOLD_FOR_DEPRECATION:
            return MutationType.DEPRECATE, f"Failure threshold reached ({active.failure_count} failures)"
        
        # Check for fix opportunity
        if outcome.error and outcome.suggested_fixes:
            return MutationType.FIX, f"Fix for {outcome.error.category}"
        
        # Check for refinement based on partial success
        if outcome.outcome_type == OutcomeType.PARTIAL:
            return MutationType.REFINE, "Refinement for partial success pattern"
        
        # Default to fix attempt
        return MutationType.FIX, "General improvement needed"
    
    def _fix_pattern(
        self,
        pattern_id: str,
        outcome: Outcome,
        reason: str,
    ) -> Optional[MutationRecord]:
        """Create a fixed version of the pattern."""
        
        active = self._get_active_version(pattern_id)
        if not active:
            return None
        
        # Generate fix
        if outcome.error:
            correction = self.error_corrector.suggest_correction(
                error=outcome.error,
                code_context=active.content,
            )
            
            if correction and correction.corrected_code:
                new_content = correction.corrected_code
                changes = {
                    "old_content": active.content,
                    "new_content": new_content,
                    "fix_type": correction.fix_type,
                    "confidence": correction.confidence,
                }
                
                # Create new version
                new_version = self._create_version(
                    pattern_id=pattern_id,
                    content=new_content,
                    label=active.label,
                    mutation_type=MutationType.FIX,
                    mutation_reason=reason,
                    parent_version_id=active.version_id,
                    source_outcome_id=outcome.outcome_id,
                    source_error_id=outcome.error.error_id if outcome.error else None,
                )
                
                # Record mutation
                record = self._record_mutation(
                    pattern_id=pattern_id,
                    mutation_type=MutationType.FIX,
                    previous_version_id=active.version_id,
                    new_version_id=new_version.version_id,
                    reason=reason,
                    changes=changes,
                    outcome_id=outcome.outcome_id,
                    error_id=outcome.error.error_id if outcome.error else None,
                )
                
                self._stats["successful_fixes"] += 1
                
                return record
            
            # If no automatic fix, return the correction suggestion for manual review
            else:
                changes = {
                    "suggested_fix": correction.description if correction else "No fix suggestion",
                    "confidence": correction.confidence if correction else 0.0,
                    "requires_manual_fix": True,
                }
                
                record = self._record_mutation(
                    pattern_id=pattern_id,
                    mutation_type=MutationType.FIX,
                    previous_version_id=active.version_id,
                    new_version_id=None,
                    reason=reason,
                    changes=changes,
                    outcome_id=outcome.outcome_id,
                    error_id=outcome.error.error_id if outcome.error else None,
                )
                
                return record
        
        # If no automatic fix, try suggested fixes
        elif outcome.suggested_fixes:
            # Try to apply first suggested fix
            changes = {
                "suggested_fixes": outcome.suggested_fixes,
                "applied": "manual_review_needed",
            }
            
            record = self._record_mutation(
                pattern_id=pattern_id,
                mutation_type=MutationType.FIX,
                previous_version_id=active.version_id,
                new_version_id=None,  # Needs manual intervention
                reason=reason,
                changes=changes,
                outcome_id=outcome.outcome_id,
            )
            
            return record
        
        return None
    
    def _deprecate_pattern(
        self,
        pattern_id: str,
        outcome: Outcome,
        reason: str,
    ) -> MutationRecord:
        """Deprecate a pattern."""
        
        active = self._get_active_version(pattern_id)
        previous_version_id = active.version_id if active else None
        
        # Mark version as deprecated
        if active:
            active.is_active = False
            active.is_deprecated = True
            active.deprecation_reason = reason
        
        # Update LTM if available
        if self.ltm:
            node = self.ltm.get_pattern(pattern_id)
            if node:
                self.ltm.deprecate_pattern(pattern_id, reason)
        
        # Record mutation
        record = self._record_mutation(
            pattern_id=pattern_id,
            mutation_type=MutationType.DEPRECATE,
            previous_version_id=previous_version_id,
            new_version_id=None,
            reason=reason,
            changes={"deprecated": True},
            outcome_id=outcome.outcome_id,
        )
        
        self._stats["patterns_deprecated"] += 1
        
        return record
    
    def _apply_mutation(
        self,
        pattern_id: str,
        mutation_type: MutationType,
        outcome: Outcome,
        reason: str,
    ) -> Optional[MutationRecord]:
        """Apply a general mutation to a pattern."""
        
        active = self._get_active_version(pattern_id)
        if not active:
            return None
        
        # For now, create a placeholder for manual review
        # More sophisticated mutations would be implemented based on type
        
        changes = {
            "mutation_type": mutation_type.value,
            "status": "needs_implementation",
        }
        
        record = self._record_mutation(
            pattern_id=pattern_id,
            mutation_type=mutation_type,
            previous_version_id=active.version_id,
            new_version_id=None,
            reason=reason,
            changes=changes,
            outcome_id=outcome.outcome_id,
        )
        
        return record
    
    def _create_version(
        self,
        pattern_id: str,
        content: str,
        label: str,
        mutation_type: MutationType,
        mutation_reason: str,
        parent_version_id: Optional[str] = None,
        source_outcome_id: Optional[str] = None,
        source_error_id: Optional[str] = None,
    ) -> PatternVersion:
        """Create a new version of a pattern."""
        
        # Determine version number
        versions = self._versions.get(pattern_id, [])
        version_number = len(versions) + 1
        
        # Create version ID
        version_id = f"v_{pattern_id}_{version_number}_{uuid.uuid4().hex[:6]}"
        
        version = PatternVersion(
            version_id=version_id,
            pattern_id=pattern_id,
            version_number=version_number,
            content=content,
            label=label,
            parent_version_id=parent_version_id,
            mutation_type=mutation_type,
            mutation_reason=mutation_reason,
            source_outcome_id=source_outcome_id,
            source_error_id=source_error_id,
        )
        
        # Track version
        if pattern_id not in self._versions:
            self._versions[pattern_id] = []
        self._versions[pattern_id].append(version)
        self._version_by_id[version_id] = version
        
        # Set as active
        self._active_versions[pattern_id] = version_id
        
        # Update LTM if available
        if self.ltm:
            node = self.ltm.get_pattern(pattern_id)
            if node:
                node.content = content
                node.metadata["version_id"] = version_id
                node.metadata["version_number"] = version_number
                node.metadata["mutation_type"] = mutation_type.value
                node.metadata["mutation_reason"] = mutation_reason
        
        self._stats["patterns_versioned"] += 1
        
        return version
    
    def _record_mutation(
        self,
        pattern_id: str,
        mutation_type: MutationType,
        previous_version_id: Optional[str],
        new_version_id: Optional[str],
        reason: str,
        changes: Dict[str, Any],
        outcome_id: Optional[str] = None,
        error_id: Optional[str] = None,
    ) -> MutationRecord:
        """Record a mutation in history."""
        
        record = MutationRecord(
            record_id=f"mut_{uuid.uuid4().hex[:8]}",
            pattern_id=pattern_id,
            mutation_type=mutation_type,
            previous_version_id=previous_version_id,
            new_version_id=new_version_id,
            reason=reason,
            changes=changes,
            outcome_id=outcome_id,
            error_id=error_id,
        )
        
        self._mutations.append(record)
        if len(self._mutations) > self._max_history:
            self._mutations.pop(0)
        
        self._stats["total_mutations"] += 1
        self._stats["by_type"][mutation_type.value] += 1
        
        return record
    
    def _ensure_pattern_tracked(self, pattern_id: str) -> None:
        """Ensure a pattern is being tracked."""
        if pattern_id not in self._versions:
            # Get pattern content from LTM if available
            content = ""
            label = pattern_id
            
            if self.ltm:
                node = self.ltm.get_pattern(pattern_id)
                if node:
                    content = node.content
                    label = node.label
            
            # Create initial version
            version = PatternVersion(
                version_id=f"v_{pattern_id}_1_initial",
                pattern_id=pattern_id,
                version_number=1,
                content=content,
                label=label,
            )
            
            self._versions[pattern_id] = [version]
            self._version_by_id[version.version_id] = version
            self._active_versions[pattern_id] = version.version_id
    
    def _get_active_version(self, pattern_id: str) -> Optional[PatternVersion]:
        """Get the active version of a pattern."""
        version_id = self._active_versions.get(pattern_id)
        if version_id:
            return self._version_by_id.get(version_id)
        return None
    
    def restore_pattern(self, pattern_id: str, version_id: Optional[str] = None) -> Optional[MutationRecord]:
        """
        Restore a deprecated pattern.
        
        Args:
            pattern_id: Pattern to restore
            version_id: Optional specific version to restore, or latest if None
            
        Returns:
            MutationRecord if successful
        """
        versions = self._versions.get(pattern_id, [])
        if not versions:
            return None
        
        # Find version to restore
        if version_id:
            target = self._version_by_id.get(version_id)
        else:
            # Get latest non-deprecated version, or latest if all deprecated
            target = None
            for v in reversed(versions):
                if not v.is_deprecated:
                    target = v
                    break
            if not target:
                target = versions[-1]
        
        if not target:
            return None
        
        # Restore
        target.is_deprecated = False
        target.is_active = True
        self._active_versions[pattern_id] = target.version_id
        
        # Update LTM
        if self.ltm:
            self.ltm.restore_pattern(pattern_id)
        
        # Record mutation
        record = self._record_mutation(
            pattern_id=pattern_id,
            mutation_type=MutationType.RESTORE,
            previous_version_id=None,
            new_version_id=target.version_id,
            reason="Manual restoration",
            changes={"restored": True},
        )
        
        self._stats["patterns_restored"] += 1
        
        return record
    
    def get_version_history(self, pattern_id: str) -> List[PatternVersion]:
        """Get all versions of a pattern."""
        return self._versions.get(pattern_id, [])
    
    def get_active_version(self, pattern_id: str) -> Optional[PatternVersion]:
        """Get the active version of a pattern."""
        return self._get_active_version(pattern_id)
    
    def get_mutation_history(self, pattern_id: Optional[str] = None, limit: int = 100) -> List[MutationRecord]:
        """Get mutation history, optionally filtered by pattern."""
        if pattern_id:
            records = [r for r in self._mutations if r.pattern_id == pattern_id]
        else:
            records = self._mutations
        
        return records[-limit:]
    
    def get_patterns_needing_fix(self) -> List[Dict[str, Any]]:
        """Get patterns that need fixing."""
        needs_fix = []
        
        for pattern_id, versions in self._versions.items():
            active = self._get_active_version(pattern_id)
            if not active:
                continue
            
            if active.failure_count >= self.FAILURE_THRESHOLD_FOR_MUTATION:
                needs_fix.append({
                    "pattern_id": pattern_id,
                    "version_id": active.version_id,
                    "failure_count": active.failure_count,
                    "success_count": active.success_count,
                    "success_rate": active.success_count / max(1, active.success_count + active.failure_count),
                    "last_failure": active.last_outcome.isoformat() if active.last_outcome else None,
                })
        
        return sorted(needs_fix, key=lambda x: x["success_rate"])
    
    def get_deprecated_patterns(self) -> List[Dict[str, Any]]:
        """Get all deprecated patterns."""
        deprecated = []
        
        for pattern_id, versions in self._versions.items():
            for version in versions:
                if version.is_deprecated:
                    deprecated.append({
                        "pattern_id": pattern_id,
                        "version_id": version.version_id,
                        "deprecation_reason": version.deprecation_reason,
                        "created_at": version.created_at.isoformat(),
                    })
                    break  # Only include once per pattern
        
        return deprecated
    
    def get_version_diff(self, version_id1: str, version_id2: str) -> Dict[str, Any]:
        """Get diff between two versions."""
        v1 = self._version_by_id.get(version_id1)
        v2 = self._version_by_id.get(version_id2)
        
        if not v1 or not v2:
            return {"error": "Version not found"}
        
        diff = list(difflib.unified_diff(
            v1.content.splitlines(keepends=True),
            v2.content.splitlines(keepends=True),
            fromfile=f"v{v1.version_number}",
            tofile=f"v{v2.version_number}",
        ))
        
        return {
            "version1": version_id1,
            "version2": version_id2,
            "diff": "".join(diff),
            "lines_changed": len([l for l in diff if l.startswith("+") or l.startswith("-")]) - 2,
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get mutator statistics."""
        return {
            **self._stats,
            "total_patterns_tracked": len(self._versions),
            "total_versions": len(self._version_by_id),
            "mutation_history_size": len(self._mutations),
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize mutator state."""
        return {
            "versions": {
                pid: [v.to_dict() for v in vers]
                for pid, vers in self._versions.items()
            },
            "active_versions": self._active_versions,
            "mutations": [m.to_dict() for m in self._mutations],
            "stats": self._stats,
        }
    
    @classmethod
    def from_dict(
        cls,
        data: Dict[str, Any],
        ltm: Optional[LongTermMemory] = None,
    ) -> "PatternMutator":
        """Deserialize mutator state."""
        mutator = cls(ltm=ltm)
        
        for pid, versions_data in data.get("versions", {}).items():
            versions = []
            for vdata in versions_data:
                version = PatternVersion(
                    version_id=vdata["version_id"],
                    pattern_id=vdata["pattern_id"],
                    version_number=vdata["version_number"],
                    content=vdata["content"],
                    label=vdata["label"],
                    parent_version_id=vdata.get("parent_version_id"),
                    mutation_type=MutationType(vdata["mutation_type"]) if vdata.get("mutation_type") else None,
                    mutation_reason=vdata.get("mutation_reason", ""),
                    source_outcome_id=vdata.get("source_outcome_id"),
                    source_error_id=vdata.get("source_error_id"),
                    success_count=vdata.get("success_count", 0),
                    failure_count=vdata.get("failure_count", 0),
                    is_active=vdata.get("is_active", True),
                    is_deprecated=vdata.get("is_deprecated", False),
                    deprecation_reason=vdata.get("deprecation_reason", ""),
                )
                if vdata.get("created_at"):
                    version.created_at = datetime.fromisoformat(vdata["created_at"])
                if vdata.get("last_outcome"):
                    version.last_outcome = datetime.fromisoformat(vdata["last_outcome"])
                versions.append(version)
                mutator._version_by_id[version.version_id] = version
            mutator._versions[pid] = versions
        
        mutator._active_versions = data.get("active_versions", {})
        
        for mdata in data.get("mutations", []):
            record = MutationRecord(
                record_id=mdata["record_id"],
                pattern_id=mdata["pattern_id"],
                mutation_type=MutationType(mdata["mutation_type"]),
                previous_version_id=mdata.get("previous_version_id"),
                new_version_id=mdata.get("new_version_id"),
                reason=mdata["reason"],
                changes=mdata.get("changes", {}),
                outcome_id=mdata.get("outcome_id"),
                error_id=mdata.get("error_id"),
            )
            if mdata.get("timestamp"):
                record.timestamp = datetime.fromisoformat(mdata["timestamp"])
            mutator._mutations.append(record)
        
        mutator._stats = data.get("stats", mutator._stats)
        
        return mutator
