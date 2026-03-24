"""
Gap Detection for RPA system.

Identifies knowledge gaps and areas needing attention in the pattern graph.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from collections import defaultdict

from rpa.core.graph import Node, PatternGraph, NodeType, EdgeType


class GapType(Enum):
    """Types of knowledge gaps."""
    UNCERTAIN_PATTERN = "uncertain_pattern"       # Pattern flagged for review
    INCOMPLETE_COMPOSITION = "incomplete"         # Missing child references
    ORPHANED_PATTERN = "orphaned"                 # Not referenced by parents
    UNRESOLVED_REFERENCE = "unresolved"           # Edge points to non-existent node
    HIERARCHY_GAP = "hierarchy"                   # Missing intermediate levels
    CROSS_DOMAIN = "cross_domain"                 # Potential cross-domain links
    MISSING_PRIMITIVE = "missing_primitive"       # Primitive not learned yet


@dataclass
class Gap:
    """Represents a detected knowledge gap."""
    gap_id: str
    gap_type: GapType
    severity: str  # "low", "medium", "high"
    description: str
    affected_nodes: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "gap_id": self.gap_id,
            "gap_type": self.gap_type.value,
            "severity": self.severity,
            "description": self.description,
            "affected_nodes": self.affected_nodes,
            "metadata": self.metadata,
        }


class GapDetector:
    """
    Detects knowledge gaps in the pattern graph.
    
    The GapDetector uses multiple strategies to identify areas where
    the system needs to learn more or where knowledge is incomplete.
    """
    
    def __init__(self):
        """Initialize the GapDetector."""
        self._detected_gaps: Dict[str, Gap] = {}
        self._gap_counter = 0
    
    def detect_all_gaps(
        self,
        graph: PatternGraph,
        domain: Optional[str] = None,
    ) -> List[Gap]:
        """
        Run all gap detection strategies.
        
        Args:
            graph: The pattern graph to analyze
            domain: Optional domain filter
            
        Returns:
            List of all detected gaps
        """
        gaps = []
        
        gaps.extend(self.detect_flagged_uncertain_patterns(graph, domain))
        gaps.extend(self.detect_incomplete_composition(graph, domain))
        gaps.extend(self.detect_orphaned_patterns(graph, domain))
        gaps.extend(self.detect_unresolved_references(graph))
        gaps.extend(self.detect_hierarchy_gaps(graph, domain))
        gaps.extend(self.detect_cross_domain_gaps(graph))
        
        return gaps
    
    def detect_flagged_uncertain_patterns(
        self,
        graph: PatternGraph,
        domain: Optional[str] = None,
    ) -> List[Gap]:
        """
        Find patterns marked as uncertain.
        
        Args:
            graph: The pattern graph
            domain: Optional domain filter
            
        Returns:
            List of gaps for uncertain patterns
        """
        gaps = []
        
        for node in graph.nodes.values():
            if domain and node.domain != domain:
                continue
            
            if node.is_uncertain:
                gap = self._create_gap(
                    gap_type=GapType.UNCERTAIN_PATTERN,
                    severity="medium",
                    description=f"Pattern '{node.label}' is flagged as uncertain",
                    affected_nodes=[node.node_id],
                    metadata={
                        "reason": node.metadata.get("uncertainty_reason", "Unknown"),
                        "confidence": node.confidence,
                    }
                )
                gaps.append(gap)
        
        return gaps
    
    def detect_incomplete_composition(
        self,
        graph: PatternGraph,
        domain: Optional[str] = None,
    ) -> List[Gap]:
        """
        Find patterns with missing child references.
        
        Args:
            graph: The pattern graph
            domain: Optional domain filter
            
        Returns:
            List of gaps for incomplete patterns
        """
        gaps = []
        
        for node in graph.nodes.values():
            if domain and node.domain != domain:
                continue
            
            if node.node_type == NodeType.PRIMITIVE:
                continue
            
            # Check for missing children
            missing_children = []
            outgoing = graph.get_outgoing_edges(node.node_id, EdgeType.COMPOSED_OF)
            
            for edge in outgoing:
                if not graph.has_node(edge.target_id):
                    missing_children.append(edge.target_id)
            
            if missing_children:
                severity = "high" if len(missing_children) > 1 else "medium"
                gap = self._create_gap(
                    gap_type=GapType.INCOMPLETE_COMPOSITION,
                    severity=severity,
                    description=f"Pattern '{node.label}' has {len(missing_children)} missing child reference(s)",
                    affected_nodes=[node.node_id] + missing_children,
                    metadata={
                        "missing_children": missing_children,
                    }
                )
                gaps.append(gap)
        
        return gaps
    
    def detect_orphaned_patterns(
        self,
        graph: PatternGraph,
        domain: Optional[str] = None,
    ) -> List[Gap]:
        """
        Find patterns not referenced by any parent.
        
        These are patterns that exist but aren't used in any higher-level
        composition, which might indicate isolated knowledge.
        
        Args:
            graph: The pattern graph
            domain: Optional domain filter
            
        Returns:
            List of gaps for orphaned patterns
        """
        gaps = []
        
        for node in graph.nodes.values():
            if domain and node.domain != domain:
                continue
            
            # Primitives are expected to have parents
            if node.node_type == NodeType.PRIMITIVE:
                continue
            
            # Check if pattern has any parents
            parents = graph.get_parents(node.node_id)
            
            if not parents and node.hierarchy_level > 0:
                gap = self._create_gap(
                    gap_type=GapType.ORPHANED_PATTERN,
                    severity="low",
                    description=f"Pattern '{node.label}' is not used in any higher-level patterns",
                    affected_nodes=[node.node_id],
                    metadata={
                        "hierarchy_level": node.hierarchy_level,
                    }
                )
                gaps.append(gap)
        
        return gaps
    
    def detect_unresolved_references(
        self,
        graph: PatternGraph,
    ) -> List[Gap]:
        """
        Find edges pointing to non-existent nodes.
        
        Args:
            graph: The pattern graph
            
        Returns:
            List of gaps for unresolved references
        """
        gaps = []
        
        # Track which missing nodes we've already reported
        reported_missing: Set[str] = set()
        
        for edge in graph.edges.values():
            if not graph.has_node(edge.target_id):
                if edge.target_id not in reported_missing:
                    reported_missing.add(edge.target_id)
                    
                    gap = self._create_gap(
                        gap_type=GapType.UNRESOLVED_REFERENCE,
                        severity="high",
                        description=f"Edge points to non-existent node: {edge.target_id}",
                        affected_nodes=[edge.source_id, edge.target_id],
                        metadata={
                            "edge_id": edge.edge_id,
                            "edge_type": edge.edge_type.value,
                        }
                    )
                    gaps.append(gap)
        
        return gaps
    
    def detect_hierarchy_gaps(
        self,
        graph: PatternGraph,
        domain: Optional[str] = None,
    ) -> List[Gap]:
        """
        Find missing intermediate levels in the hierarchy.
        
        For example: primitives exist, sentences exist, but no word-level patterns.
        
        Args:
            graph: The pattern graph
            domain: Optional domain filter
            
        Returns:
            List of gaps for hierarchy issues
        """
        gaps = []
        
        # Count patterns at each hierarchy level
        level_counts: Dict[int, int] = defaultdict(int)
        domains_with_levels: Dict[str, Set[int]] = defaultdict(set)
        
        for node in graph.nodes.values():
            if domain and node.domain != domain:
                continue
            
            level_counts[node.hierarchy_level] += 1
            domains_with_levels[node.domain].add(node.hierarchy_level)
        
        # Check for gaps between levels
        for node_domain, levels in domains_with_levels.items():
            if domain and node_domain != domain:
                continue
            
            sorted_levels = sorted(levels)
            
            for i in range(len(sorted_levels) - 1):
                current = sorted_levels[i]
                next_level = sorted_levels[i + 1]
                
                # If there's a gap of more than 1 level
                if next_level - current > 1:
                    missing_levels = list(range(current + 1, next_level))
                    gap = self._create_gap(
                        gap_type=GapType.HIERARCHY_GAP,
                        severity="medium",
                        description=f"Missing hierarchy levels {missing_levels} in domain '{node_domain}'",
                        affected_nodes=[],
                        metadata={
                            "domain": node_domain,
                            "missing_levels": missing_levels,
                            "existing_levels": sorted_levels,
                        }
                    )
                    gaps.append(gap)
        
        # Check for domains with only primitives
        for node_domain, levels in domains_with_levels.items():
            if domain and node_domain != domain:
                continue
            
            if levels == {0}:
                gap = self._create_gap(
                    gap_type=GapType.HIERARCHY_GAP,
                    severity="medium",
                    description=f"Domain '{node_domain}' has only primitives, no higher-level patterns",
                    affected_nodes=[],
                    metadata={
                        "domain": node_domain,
                        "has_primitives": True,
                        "has_patterns": False,
                    }
                )
                gaps.append(gap)
        
        return gaps
    
    def detect_cross_domain_gaps(
        self,
        graph: PatternGraph,
    ) -> List[Gap]:
        """
        Find patterns that could link across domains.
        
        For example: "if" in Python could relate to "conditional" in English.
        
        Args:
            graph: The pattern graph
            
        Returns:
            List of potential cross-domain link opportunities
        """
        gaps = []
        
        # Group patterns by content similarity across domains
        content_by_domain: Dict[str, Dict[str, List[str]]] = defaultdict(lambda: defaultdict(list))
        
        for node in graph.nodes.values():
            if node.node_type == NodeType.PRIMITIVE:
                continue
            
            # Normalize content for comparison
            normalized = node.content.lower().strip()
            content_by_domain[node.domain][normalized].append(node.node_id)
        
        # Find potential cross-domain matches
        domains = list(content_by_domain.keys())
        
        for i, domain1 in enumerate(domains):
            for domain2 in domains[i + 1:]:
                # Find common content
                common_content = set(content_by_domain[domain1].keys()) & set(content_by_domain[domain2].keys())
                
                for content in common_content:
                    nodes1 = content_by_domain[domain1][content]
                    nodes2 = content_by_domain[domain2][content]
                    
                    # Check if they're already linked
                    already_linked = False
                    for n1 in nodes1:
                        for edge in graph.get_outgoing_edges(n1):
                            if edge.target_id in nodes2:
                                already_linked = True
                                break
                    
                    if not already_linked:
                        gap = self._create_gap(
                            gap_type=GapType.CROSS_DOMAIN,
                            severity="low",
                            description=f"Potential cross-domain link: '{content}' between '{domain1}' and '{domain2}'",
                            affected_nodes=nodes1 + nodes2,
                            metadata={
                                "domains": [domain1, domain2],
                                "content": content,
                            }
                        )
                        gaps.append(gap)
        
        return gaps
    
    def detect_missing_primitives(
        self,
        graph: PatternGraph,
        domain: str = "english",
        required_chars: Optional[Set[str]] = None,
    ) -> List[Gap]:
        """
        Find primitive characters that haven't been learned.
        
        Args:
            graph: The pattern graph
            domain: Domain to check
            required_chars: Set of characters that should exist
            
        Returns:
            List of gaps for missing primitives
        """
        if required_chars is None:
            # Default to basic ASCII letters
            required_chars = set("abcdefghijklmnopqrstuvwxyz")
        
        # Get existing primitives
        existing_primitives = set()
        for node in graph.nodes.values():
            if node.node_type == NodeType.PRIMITIVE and node.domain == domain:
                existing_primitives.add(node.content.lower())
        
        missing = required_chars - existing_primitives
        
        gaps = []
        for char in sorted(missing):
            gap = self._create_gap(
                gap_type=GapType.MISSING_PRIMITIVE,
                severity="medium",
                description=f"Missing primitive character: '{char}'",
                affected_nodes=[f"primitive:{char}"],
                metadata={
                    "character": char,
                    "domain": domain,
                }
            )
            gaps.append(gap)
        
        return gaps
    
    def prioritize_gaps(
        self,
        gaps: List[Gap],
    ) -> List[Gap]:
        """
        Rank gaps by impact and severity.
        
        Args:
            gaps: List of gaps to prioritize
            
        Returns:
            Sorted list of gaps (highest priority first)
        """
        severity_weights = {
            "high": 3,
            "medium": 2,
            "low": 1,
        }
        
        type_weights = {
            GapType.UNRESOLVED_REFERENCE: 10,
            GapType.INCOMPLETE_COMPOSITION: 8,
            GapType.MISSING_PRIMITIVE: 7,
            GapType.UNCERTAIN_PATTERN: 5,
            GapType.HIERARCHY_GAP: 4,
            GapType.ORPHANED_PATTERN: 2,
            GapType.CROSS_DOMAIN: 1,
        }
        
        def gap_score(gap: Gap) -> int:
            severity_score = severity_weights.get(gap.severity, 1)
            type_score = type_weights.get(gap.gap_type, 1)
            return severity_score * type_score
        
        return sorted(gaps, key=gap_score, reverse=True)
    
    def get_gap(self, gap_id: str) -> Optional[Gap]:
        """Get a gap by ID."""
        return self._detected_gaps.get(gap_id)
    
    def get_gaps_by_type(self, gap_type: GapType) -> List[Gap]:
        """Get all gaps of a specific type."""
        return [g for g in self._detected_gaps.values() if g.gap_type == gap_type]
    
    def get_gaps_by_severity(self, severity: str) -> List[Gap]:
        """Get all gaps of a specific severity."""
        return [g for g in self._detected_gaps.values() if g.severity == severity]
    
    def clear_gaps(self) -> None:
        """Clear all detected gaps."""
        self._detected_gaps.clear()
        self._gap_counter = 0
    
    def _create_gap(
        self,
        gap_type: GapType,
        severity: str,
        description: str,
        affected_nodes: List[str],
        metadata: Dict[str, Any],
    ) -> Gap:
        """Create and register a new gap."""
        self._gap_counter += 1
        gap_id = f"gap_{self._gap_counter:04d}"
        
        gap = Gap(
            gap_id=gap_id,
            gap_type=gap_type,
            severity=severity,
            description=description,
            affected_nodes=affected_nodes,
            metadata=metadata,
        )
        
        self._detected_gaps[gap_id] = gap
        return gap
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of detected gaps."""
        by_type: Dict[str, int] = defaultdict(int)
        by_severity: Dict[str, int] = defaultdict(int)
        
        for gap in self._detected_gaps.values():
            by_type[gap.gap_type.value] += 1
            by_severity[gap.severity] += 1
        
        return {
            "total_gaps": len(self._detected_gaps),
            "by_type": dict(by_type),
            "by_severity": dict(by_severity),
        }
