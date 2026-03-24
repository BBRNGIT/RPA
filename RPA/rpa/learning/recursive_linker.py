"""
Recursive Linker - Link patterns across hierarchy levels.

Creates explicit links between:
- Primitives -> Words -> Sentences -> Paragraphs (text)
- Tokens -> Expressions -> Statements -> Functions (code)
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set, Tuple
from collections import defaultdict
import logging

from ..core.node import Node, NodeType
from ..core.edge import Edge, EdgeType
from ..memory.ltm import LongTermMemory

logger = logging.getLogger(__name__)


@dataclass
class LinkResult:
    """Result of a linking operation."""
    source_id: str
    target_id: str
    link_type: str
    success: bool
    message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "link_type": self.link_type,
            "success": self.success,
            "message": self.message,
            "metadata": self.metadata
        }


@dataclass
class CompoundPattern:
    """A pattern formed by combining multiple patterns."""
    pattern_id: str
    component_ids: List[str]
    label: str
    domain: str
    hierarchy_level: int
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_id": self.pattern_id,
            "component_ids": self.component_ids,
            "label": self.label,
            "domain": self.domain,
            "hierarchy_level": self.hierarchy_level,
            "confidence": self.confidence
        }


@dataclass
class IntegrityReport:
    """Report on recursive integrity of a pattern hierarchy."""
    node_id: str
    is_valid: bool
    missing_links: List[str] = field(default_factory=list)
    orphaned_nodes: List[str] = field(default_factory=list)
    circular_references: List[List[str]] = field(default_factory=list)
    hierarchy_depth: int = 0
    total_linked_nodes: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "is_valid": self.is_valid,
            "missing_links": self.missing_links,
            "orphaned_nodes": self.orphaned_nodes,
            "circular_references": self.circular_references,
            "hierarchy_depth": self.hierarchy_depth,
            "total_linked_nodes": self.total_linked_nodes
        }


class RecursiveLinker:
    """
    Link patterns across hierarchy levels for recursive learning.

    Creates explicit links between hierarchy levels:
    - Level 0 (primitives) -> Level 1 (patterns)
    - Level 1 (patterns) -> Level 2 (sequences)
    - Level 2 (sequences) -> Level 3 (concepts)

    Also handles:
    - Compound pattern identification
    - Recursive integrity verification
    - Hierarchy gap detection
    """

    def __init__(self):
        """Initialize RecursiveLinker."""
        self._link_cache: Dict[str, List[LinkResult]] = defaultdict(list)
        self._compound_patterns: Dict[str, CompoundPattern] = {}

    def link_pattern_hierarchy(
        self,
        node_id: str,
        ltm: LongTermMemory
    ) -> List[LinkResult]:
        """
        Create explicit links between hierarchy levels for a pattern.

        Args:
            node_id: ID of the pattern to link
            ltm: Long-term memory containing the pattern

        Returns:
            List of LinkResult objects
        """
        results = []
        node = ltm.get_node(node_id)

        if not node:
            results.append(LinkResult(
                source_id=node_id,
                target_id="",
                link_type="hierarchy",
                success=False,
                message=f"Node {node_id} not found in LTM"
            ))
            return results

        # Get children from existing edges (COMPOSITION type)
        children = ltm.get_edges_from(node_id)
        child_ids = [e.target_id for e in children 
                     if e.edge_type == EdgeType.COMPOSED_OF]

        # Link to children (lower level)
        for child_id in child_ids:
            child_node = ltm.get_node(child_id)
            if child_node:
                results.append(LinkResult(
                    source_id=node_id,
                    target_id=child_id,
                    link_type="composition",
                    success=True,
                    message=f"Linked {node_id} -> {child_id}",
                    metadata={"edge_type": "COMPOSITION"}
                ))
            else:
                results.append(LinkResult(
                    source_id=node_id,
                    target_id=child_id,
                    link_type="composition",
                    success=False,
                    message=f"Child node {child_id} not found"
                ))

        # Find and link to parent patterns (higher level)
        parents = self._find_parent_patterns(node_id, ltm)
        for parent_id in parents:
            # Check if edge already exists
            existing_edges = ltm.get_edges_to(node_id)
            if not any(e.source_id == parent_id for e in existing_edges):
                edge = Edge(
                    source_id=parent_id,
                    target_id=node_id,
                    edge_type=EdgeType.COMPOSED_OF,
                    weight=1.0
                )
                ltm.add_edge(edge)

            results.append(LinkResult(
                source_id=parent_id,
                target_id=node_id,
                link_type="parent_composition",
                success=True,
                message=f"Linked parent {parent_id} -> {node_id}",
                metadata={"edge_type": "COMPOSITION"}
            ))

        # Cache results
        self._link_cache[node_id].extend(results)

        return results

    def _find_parent_patterns(
        self,
        node_id: str,
        ltm: LongTermMemory
    ) -> List[str]:
        """Find patterns that contain this node in their composition."""
        parents = []

        # Get edges pointing to this node
        edges_to = ltm.get_edges_to(node_id)
        for edge in edges_to:
            if edge.edge_type == EdgeType.COMPOSED_OF:
                parents.append(edge.source_id)

        return parents

    def identify_compound_patterns(
        self,
        ltm: LongTermMemory,
        domain: Optional[str] = None
    ) -> List[CompoundPattern]:
        """
        Identify patterns that can be combined into compound patterns.

        Example: "apple" + "tree" -> "apple tree"

        Args:
            ltm: Long-term memory to search
            domain: Optional domain filter

        Returns:
            List of identified CompoundPattern opportunities
        """
        compounds = []

        # Get all patterns at hierarchy level 1 (words/basic patterns)
        patterns = []
        for node_id, node in ltm._nodes.items():
            if node.hierarchy_level == 1:
                if domain is None or node.domain == domain:
                    patterns.append((node_id, node))

        # Look for patterns that appear together in higher-level patterns
        for node_id, node in ltm._nodes.items():
            if node.hierarchy_level >= 2:
                # Get composition from edges
                edges = ltm.get_edges_from(node_id)
                composition = [e.target_id for e in edges 
                              if e.edge_type == EdgeType.COMPOSED_OF]
                
                if len(composition) >= 2:
                    # Check for consecutive pattern pairs
                    for i in range(len(composition) - 1):
                        comp1 = composition[i]
                        comp2 = composition[i + 1]

                        # Check if both components are level-1 patterns
                        node1 = ltm.get_node(comp1)
                        node2 = ltm.get_node(comp2)

                        if (node1 and node2 and
                            node1.hierarchy_level == 1 and
                            node2.hierarchy_level == 1):

                            compound_id = f"{comp1}_{comp2}"
                            if compound_id not in self._compound_patterns:
                                compound = CompoundPattern(
                                    pattern_id=compound_id,
                                    component_ids=[comp1, comp2],
                                    label=f"{node1.label} {node2.label}",
                                    domain=node1.domain,
                                    hierarchy_level=1,
                                    confidence=0.8
                                )
                                compounds.append(compound)
                                self._compound_patterns[compound_id] = compound

        logger.info(f"Identified {len(compounds)} compound pattern opportunities")
        return compounds

    def create_compound_pattern(
        self,
        component_ids: List[str],
        compound_label: str,
        ltm: LongTermMemory,
        domain: Optional[str] = None
    ) -> Tuple[Node, List[Edge]]:
        """
        Create a new compound pattern from components.

        Args:
            component_ids: IDs of component patterns
            compound_label: Label for the new compound
            ltm: Long-term memory to store the pattern
            domain: Optional domain (inferred from components)

        Returns:
            Tuple of (Node, List[Edge]) for the new pattern
        """
        # Infer domain from first component
        if domain is None:
            first_node = ltm.get_node(component_ids[0])
            domain = first_node.domain if first_node else "unknown"

        # Create compound node
        compound_id = f"compound:{compound_label.replace(' ', '_')}"
        node = Node(
            node_id=compound_id,
            label=compound_label,
            node_type=NodeType.PATTERN,
            content=compound_label,
            domain=domain,
            hierarchy_level=1
        )

        # Create composition edges
        edges = []
        for i, comp_id in enumerate(component_ids):
            edge = Edge.create_composition(
                parent_id=compound_id,
                child_id=comp_id,
                order=i
            )
            edges.append(edge)

        # Store in LTM
        ltm.add_node(node)
        for edge in edges:
            ltm.add_edge(edge)

        logger.info(f"Created compound pattern {compound_id} from {component_ids}")
        return node, edges

    def verify_recursive_integrity(
        self,
        node_id: str,
        ltm: LongTermMemory
    ) -> IntegrityReport:
        """
        Verify that all levels of a pattern are properly linked.

        Args:
            node_id: ID of the pattern to verify
            ltm: Long-term memory

        Returns:
            IntegrityReport with validation results
        """
        node = ltm.get_node(node_id)
        if not node:
            return IntegrityReport(
                node_id=node_id,
                is_valid=False,
                missing_links=[],
                orphaned_nodes=[]
            )

        missing_links = []
        orphaned_nodes = []
        circular_refs = []
        visited: Set[str] = set()
        total_linked = 0
        max_depth = 0

        # Traverse the hierarchy
        def traverse(nid: str, depth: int, path: List[str]) -> int:
            nonlocal max_depth, total_linked

            if nid in path:
                # Circular reference detected
                circular_refs.append(path + [nid])
                return depth

            if nid in visited:
                return depth

            visited.add(nid)
            max_depth = max(max_depth, depth)

            current_node = ltm.get_node(nid)
            if not current_node:
                missing_links.append(nid)
                return depth

            # Get children from edges
            edges = ltm.get_edges_from(nid)
            child_ids = [e.target_id for e in edges 
                        if e.edge_type == EdgeType.COMPOSED_OF]
            
            for child_id in child_ids:
                child_node = ltm.get_node(child_id)
                if child_node:
                    total_linked += 1
                    traverse(child_id, depth + 1, path + [nid])
                else:
                    missing_links.append(child_id)

            return depth

        traverse(node_id, 0, [])

        # Check for orphaned nodes (nodes that should be linked but aren't)
        edges_from = ltm.get_edges_from(node_id)
        for edge in edges_from:
            if edge.edge_type == EdgeType.COMPOSED_OF:
                comp_node = ltm.get_node(edge.target_id)
                if comp_node:
                    # Check if this component is linked back
                    edges_to = ltm.get_edges_to(edge.target_id)
                    edge_sources = [e.source_id for e in edges_to]
                    if node_id not in edge_sources:
                        orphaned_nodes.append(edge.target_id)

        return IntegrityReport(
            node_id=node_id,
            is_valid=len(missing_links) == 0 and len(circular_refs) == 0,
            missing_links=missing_links,
            orphaned_nodes=orphaned_nodes,
            circular_references=circular_refs,
            hierarchy_depth=max_depth,
            total_linked_nodes=total_linked
        )

    def link_all_patterns(
        self,
        ltm: LongTermMemory,
        domain: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Link all patterns in LTM recursively.

        Args:
            ltm: Long-term memory
            domain: Optional domain filter

        Returns:
            Summary of linking operations
        """
        results = {
            "total_processed": 0,
            "successful_links": 0,
            "failed_links": 0,
            "compound_patterns_identified": 0,
            "integrity_issues": []
        }

        node_ids = list(ltm._nodes.keys())

        for node_id in node_ids:
            node = ltm.get_node(node_id)
            if domain and node and node.domain != domain:
                continue

            results["total_processed"] += 1

            # Link hierarchy
            link_results = self.link_pattern_hierarchy(node_id, ltm)
            for lr in link_results:
                if lr.success:
                    results["successful_links"] += 1
                else:
                    results["failed_links"] += 1

            # Verify integrity
            integrity = self.verify_recursive_integrity(node_id, ltm)
            if not integrity.is_valid:
                results["integrity_issues"].append({
                    "node_id": node_id,
                    "missing_links": integrity.missing_links,
                    "circular_refs": integrity.circular_references
                })

        # Identify compound patterns
        compounds = self.identify_compound_patterns(ltm, domain)
        results["compound_patterns_identified"] = len(compounds)

        logger.info(f"Linking complete: {results}")
        return results

    def get_hierarchy_stats(
        self,
        ltm: LongTermMemory,
        domain: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get statistics about the pattern hierarchy.

        Args:
            ltm: Long-term memory
            domain: Optional domain filter

        Returns:
            Statistics dictionary
        """
        stats = {
            "by_level": defaultdict(int),
            "by_domain": defaultdict(int),
            "total_nodes": 0,
            "total_edges": 0,
            "unlinked_nodes": 0,
            "max_depth": 0
        }

        for node_id, node in ltm._nodes.items():
            if domain and node.domain != domain:
                continue

            stats["total_nodes"] += 1
            stats["by_level"][node.hierarchy_level] += 1
            stats["by_domain"][node.domain] += 1

            # Check if linked
            edges = ltm.get_edges_from(node_id)
            if not edges:
                stats["unlinked_nodes"] += 1

        stats["total_edges"] = len(ltm._edges)
        stats["by_level"] = dict(stats["by_level"])
        stats["by_domain"] = dict(stats["by_domain"])

        return stats

    def clear_cache(self) -> None:
        """Clear the link cache."""
        self._link_cache.clear()
        self._compound_patterns.clear()
