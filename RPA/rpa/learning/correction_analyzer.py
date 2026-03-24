"""
Correction Analysis for RPA system.

Analyzes corrections and applies insights to improve pattern knowledge.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set
import difflib

from rpa.core.graph import Node, Edge, PatternGraph, NodeType, EdgeType
from rpa.memory.stm import ShortTermMemory
from rpa.memory.ltm import LongTermMemory
from rpa.memory.episodic import EpisodicMemory, EventType


class IssueType(Enum):
    """Types of correction issues."""
    STRUCTURAL = "structural"         # Pattern structure issue
    COMPOSITIONAL = "compositional"   # Wrong components
    USAGE = "usage"                   # Wrong usage context
    SEMANTIC = "semantic"             # Meaning/concept issue
    REFERENCE = "reference"           # Wrong reference/link
    ORDER = "order"                   # Wrong ordering


@dataclass
class Correction:
    """Represents a correction to a pattern."""
    correction_id: str
    wrong_node_id: str
    correct_node_id: str
    feedback: str
    issue_type: IssueType
    root_cause: str = ""
    changes: List[str] = field(default_factory=list)
    applied: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "correction_id": self.correction_id,
            "wrong_node_id": self.wrong_node_id,
            "correct_node_id": self.correct_node_id,
            "feedback": self.feedback,
            "issue_type": self.issue_type.value,
            "root_cause": self.root_cause,
            "changes": self.changes,
            "applied": self.applied,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class CorrectionResult:
    """Result of applying a correction."""
    correction_id: str
    success: bool = False
    patterns_updated: List[str] = field(default_factory=list)
    patterns_flagged: List[str] = field(default_factory=list)
    message: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "correction_id": self.correction_id,
            "success": self.success,
            "patterns_updated": self.patterns_updated,
            "patterns_flagged": self.patterns_flagged,
            "message": self.message,
        }


class CorrectionAnalyzer:
    """
    Analyzes corrections and applies insights to prevent similar errors.
    
    The CorrectionAnalyzer examines what was wrong, identifies patterns
    in similar errors, and updates related patterns to avoid repetition.
    """
    
    def __init__(
        self,
        episodic: Optional[EpisodicMemory] = None,
    ):
        """
        Initialize the CorrectionAnalyzer.
        
        Args:
            episodic: Optional episodic memory for logging
        """
        self.episodic = episodic or EpisodicMemory()
        self._corrections: Dict[str, Correction] = {}
        self._correction_counter = 0
    
    def analyze_correction(
        self,
        wrong_node_id: str,
        correct_node_id: str,
        feedback: str,
        graph: PatternGraph,
    ) -> Correction:
        """
        Analyze a correction to understand what was wrong.
        
        Args:
            wrong_node_id: ID of the incorrect pattern
            correct_node_id: ID of the correct pattern
            feedback: Explanation of the correction
            graph: The pattern graph
            
        Returns:
            Correction object with analysis
        """
        wrong_node = graph.get_node(wrong_node_id)
        correct_node = graph.get_node(correct_node_id)
        
        # Determine issue type
        issue_type = self._classify_issue(wrong_node, correct_node, feedback)
        
        # Identify root cause
        root_cause = self._identify_root_cause(wrong_node, correct_node, feedback, graph)
        
        # List specific changes
        changes = self._identify_changes(wrong_node, correct_node, graph)
        
        # Create correction record
        self._correction_counter += 1
        correction = Correction(
            correction_id=f"corr_{self._correction_counter:04d}",
            wrong_node_id=wrong_node_id,
            correct_node_id=correct_node_id,
            feedback=feedback,
            issue_type=issue_type,
            root_cause=root_cause,
            changes=changes,
        )
        
        self._corrections[correction.correction_id] = correction
        
        # Log to episodic memory
        self.episodic.log_event(
            event_type=EventType.CORRECTION_APPLIED,
            pattern_id=wrong_node_id,
            data={
                "correction_id": correction.correction_id,
                "issue_type": issue_type.value,
                "root_cause": root_cause,
            },
        )
        
        return correction
    
    def apply_correction_insights(
        self,
        correction: Correction,
        graph: PatternGraph,
        ltm: LongTermMemory,
    ) -> CorrectionResult:
        """
        Apply insights from a correction to related patterns.
        
        Args:
            correction: The correction to apply
            graph: The pattern graph
            ltm: Long-Term Memory
            
        Returns:
            CorrectionResult with details of updates
        """
        result = CorrectionResult(correction_id=correction.correction_id)
        
        # Find similar patterns that might have the same issue
        similar_patterns = self._find_similar_patterns(
            correction.wrong_node_id,
            correction.issue_type,
            graph,
        )
        
        # Create correction edge between wrong and correct patterns
        wrong_node = graph.get_node(correction.wrong_node_id)
        correct_node = graph.get_node(correction.correct_node_id)
        
        if wrong_node and correct_node:
            edge = Edge.create_correction(
                wrong_id=correction.wrong_node_id,
                correct_id=correction.correct_node_id,
            )
            edge.metadata["correction_id"] = correction.correction_id
            edge.metadata["issue_type"] = correction.issue_type.value
            graph.add_edge(edge)
        
        # Mark wrong pattern as deprecated
        if wrong_node and ltm.has_pattern(correction.wrong_node_id):
            ltm.deprecate_pattern(
                correction.wrong_node_id,
                reason=f"Corrected by {correction.correct_node_id}: {correction.feedback}",
            )
            result.patterns_updated.append(correction.wrong_node_id)
        
        # Flag similar patterns for review
        for pattern_id in similar_patterns:
            pattern = graph.get_node(pattern_id)
            if pattern:
                pattern.mark_uncertain(
                    f"Similar to corrected pattern {correction.wrong_node_id}"
                )
                pattern.metadata["related_correction"] = correction.correction_id
                
                if ltm.has_pattern(pattern_id):
                    ltm.update_pattern(pattern)
                    result.patterns_flagged.append(pattern_id)
        
        correction.applied = True
        result.success = True
        result.message = (
            f"Applied correction: {len(result.patterns_updated)} updated, "
            f"{len(result.patterns_flagged)} flagged for review"
        )
        
        return result
    
    def _classify_issue(
        self,
        wrong_node: Optional[Node],
        correct_node: Optional[Node],
        feedback: str,
    ) -> IssueType:
        """Classify the type of issue that was corrected."""
        feedback_lower = feedback.lower()
        
        # Check feedback for issue type indicators
        if any(word in feedback_lower for word in ["structure", "format", "syntax"]):
            return IssueType.STRUCTURAL
        
        if any(word in feedback_lower for word in ["component", "part", "piece", "missing"]):
            return IssueType.COMPOSITIONAL
        
        if any(word in feedback_lower for word in ["usage", "context", "use", "apply"]):
            return IssueType.USAGE
        
        if any(word in feedback_lower for word in ["meaning", "concept", "semantic", "definition"]):
            return IssueType.SEMANTIC
        
        if any(word in feedback_lower for word in ["reference", "link", "point", "connect"]):
            return IssueType.REFERENCE
        
        if any(word in feedback_lower for word in ["order", "sequence", "position", "arrange"]):
            return IssueType.ORDER
        
        # Default based on node comparison
        if wrong_node and correct_node:
            # Check if content is similar but ordered differently
            if sorted(wrong_node.content) == sorted(correct_node.content):
                return IssueType.ORDER
            
            # Check if composition is different
            wrong_children = set()
            correct_children = set()
            # Would need graph access for full comparison
        
        return IssueType.COMPOSITIONAL
    
    def _identify_root_cause(
        self,
        wrong_node: Optional[Node],
        correct_node: Optional[Node],
        feedback: str,
        graph: PatternGraph,
    ) -> str:
        """Identify the root cause of the error."""
        if not wrong_node or not correct_node:
            return "Node not found in graph"
        
        causes = []
        
        # Check for content differences
        if wrong_node.content != correct_node.content:
            # Use difflib to find differences
            diff = list(difflib.unified_diff(
                wrong_node.content,
                correct_node.content,
                lineterm="",
            ))
            causes.append(f"Content mismatch: {wrong_node.content} vs {correct_node.content}")
        
        # Check hierarchy level differences
        if wrong_node.hierarchy_level != correct_node.hierarchy_level:
            causes.append(
                f"Hierarchy level wrong: {wrong_node.hierarchy_level} vs {correct_node.hierarchy_level}"
            )
        
        # Check domain differences
        if wrong_node.domain != correct_node.domain:
            causes.append(f"Domain mismatch: {wrong_node.domain} vs {correct_node.domain}")
        
        if not causes:
            causes.append(feedback[:200])  # Use feedback as cause
        
        return "; ".join(causes)
    
    def _identify_changes(
        self,
        wrong_node: Optional[Node],
        correct_node: Optional[Node],
        graph: PatternGraph,
    ) -> List[str]:
        """Identify specific changes needed."""
        changes = []
        
        if not wrong_node or not correct_node:
            return ["Nodes not found"]
        
        # Content changes
        if wrong_node.content != correct_node.content:
            changes.append(f"content: '{wrong_node.content}' -> '{correct_node.content}'")
        
        # Label changes
        if wrong_node.label != correct_node.label:
            changes.append(f"label: '{wrong_node.label}' -> '{correct_node.label}'")
        
        # Hierarchy changes
        if wrong_node.hierarchy_level != correct_node.hierarchy_level:
            changes.append(
                f"hierarchy_level: {wrong_node.hierarchy_level} -> {correct_node.hierarchy_level}"
            )
        
        return changes if changes else ["No structural changes identified"]
    
    def _find_similar_patterns(
        self,
        wrong_node_id: str,
        issue_type: IssueType,
        graph: PatternGraph,
        similarity_threshold: float = 0.7,
    ) -> List[str]:
        """Find patterns similar to the corrected one that might have the same issue."""
        similar = []
        
        wrong_node = graph.get_node(wrong_node_id)
        if not wrong_node:
            return similar
        
        for node in graph.nodes.values():
            if node.node_id == wrong_node_id:
                continue
            
            # Check similarity based on issue type
            if issue_type == IssueType.COMPOSITIONAL:
                # Check if patterns share similar composition
                if wrong_node.content and node.content:
                    ratio = difflib.SequenceMatcher(
                        None, 
                        wrong_node.content, 
                        node.content
                    ).ratio()
                    if ratio >= similarity_threshold:
                        similar.append(node.node_id)
            
            elif issue_type == IssueType.ORDER:
                # Check if patterns have same characters but different order
                if sorted(wrong_node.content) == sorted(node.content):
                    similar.append(node.node_id)
            
            elif issue_type == IssueType.STRUCTURAL:
                # Check if patterns have same type and domain
                if (node.node_type == wrong_node.node_type and 
                    node.domain == wrong_node.domain and
                    node.hierarchy_level == wrong_node.hierarchy_level):
                    similar.append(node.node_id)
        
        return similar[:20]  # Limit to 20 similar patterns
    
    def get_correction(self, correction_id: str) -> Optional[Correction]:
        """Get a correction by ID."""
        return self._corrections.get(correction_id)
    
    def get_corrections_by_pattern(self, node_id: str) -> List[Correction]:
        """Get all corrections involving a pattern."""
        return [
            c for c in self._corrections.values()
            if c.wrong_node_id == node_id or c.correct_node_id == node_id
        ]
    
    def get_corrections_by_type(self, issue_type: IssueType) -> List[Correction]:
        """Get all corrections of a specific type."""
        return [
            c for c in self._corrections.values()
            if c.issue_type == issue_type
        ]
    
    def get_common_issues(self) -> Dict[str, int]:
        """Get frequency of each issue type."""
        counts: Dict[str, int] = {}
        for correction in self._corrections.values():
            type_name = correction.issue_type.value
            counts[type_name] = counts.get(type_name, 0) + 1
        return counts
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get correction statistics."""
        total = len(self._corrections)
        applied = sum(1 for c in self._corrections.values() if c.applied)
        
        return {
            "total_corrections": total,
            "applied": applied,
            "pending": total - applied,
            "by_issue_type": self.get_common_issues(),
        }
    
    def clear(self) -> None:
        """Clear all corrections."""
        self._corrections.clear()
        self._correction_counter = 0
