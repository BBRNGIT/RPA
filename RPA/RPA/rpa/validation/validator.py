"""
Pattern validation for RPA system.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from rpa.core.graph import Node, Edge, PatternGraph, NodeType, EdgeType


@dataclass
class ValidationResult:
    """Result of pattern validation."""
    node_id: str
    is_valid: bool = False
    structural_issues: List[Dict[str, Any]] = field(default_factory=list)
    missing_references: List[str] = field(default_factory=list)
    circular_deps: List[List[str]] = field(default_factory=list)
    composition_depth: int = 0
    all_children_resolved: bool = True
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "node_id": self.node_id,
            "is_valid": self.is_valid,
            "structural_issues": self.structural_issues,
            "missing_references": self.missing_references,
            "circular_deps": self.circular_deps,
            "composition_depth": self.composition_depth,
            "all_children_resolved": self.all_children_resolved,
            "warnings": self.warnings,
        }


class Validator:
    """
    Validates patterns for structural integrity and correctness.
    
    The Validator checks patterns for:
    - Structural validity (all children exist)
    - Circular dependencies
    - Composition depth consistency
    - Reference integrity
    """
    
    def __init__(self):
        """Initialize the Validator."""
        self._validation_cache: Dict[str, ValidationResult] = {}
    
    def validate_pattern_structure(
        self,
        node: Node,
        graph: PatternGraph,
        _visited: Optional[Set[str]] = None,
    ) -> ValidationResult:
        """
        Validate a pattern's structure.
        
        Args:
            node: The node to validate
            graph: The pattern graph containing related nodes
            _visited: Internal set to track visited nodes (prevents infinite recursion)
            
        Returns:
            ValidationResult with detailed breakdown
        """
        # Initialize visited set for recursion tracking
        if _visited is None:
            _visited = set()
        
        # Check cache
        if node.node_id in self._validation_cache:
            return self._validation_cache[node.node_id]
        
        # Check for cycles during traversal
        if node.node_id in _visited:
            # Return a result indicating circular dependency
            result = ValidationResult(
                node_id=node.node_id,
                is_valid=False,
                structural_issues=[{
                    "issue_type": "circular_dependency",
                    "description": f"Circular reference detected at {node.node_id}",
                    "affected_nodes": [node.node_id],
                }],
            )
            return result
        
        _visited.add(node.node_id)
        
        result = ValidationResult(node_id=node.node_id)
        
        # Primitives are always valid
        if node.node_type == NodeType.PRIMITIVE:
            result.is_valid = True
            result.composition_depth = 0
            self._validation_cache[node.node_id] = result
            return result
        
        # Get children
        children = graph.get_children(node.node_id)
        
        # Check for missing references
        outgoing_edges = graph.get_outgoing_edges(node.node_id, EdgeType.COMPOSED_OF)
        for edge in outgoing_edges:
            if not graph.has_node(edge.target_id):
                result.missing_references.append(edge.target_id)
                result.structural_issues.append({
                    "issue_type": "missing_reference",
                    "description": f"Missing child node: {edge.target_id}",
                    "affected_nodes": [edge.target_id],
                })
        
        result.all_children_resolved = len(result.missing_references) == 0
        
        # Check for circular dependencies using graph method
        cycles = graph.detect_circular_dependencies(node.node_id)
        if cycles:
            result.circular_deps = cycles
            result.structural_issues.append({
                "issue_type": "circular_dependency",
                "description": f"Found {len(cycles)} circular dependency chain(s)",
                "affected_nodes": [n for cycle in cycles for n in cycle],
            })
        
        # Calculate composition depth (with cycle protection)
        if children:
            child_depths = []
            for child in children:
                # Pass visited set to prevent infinite recursion
                child_result = self.validate_pattern_structure(child, graph, _visited.copy())
                child_depths.append(child_result.composition_depth)
            result.composition_depth = max(child_depths) + 1 if child_depths else node.hierarchy_level
        else:
            result.composition_depth = node.hierarchy_level
        
        # Check hierarchy consistency
        expected_level = result.composition_depth
        if node.hierarchy_level != expected_level:
            result.warnings.append(
                f"Hierarchy level mismatch: node has {node.hierarchy_level}, "
                f"expected {expected_level} based on composition"
            )
        
        # Determine overall validity
        result.is_valid = (
            result.all_children_resolved and
            len(result.circular_deps) == 0 and
            len(result.structural_issues) == 0
        )
        
        # Cache result
        self._validation_cache[node.node_id] = result
        
        return result
    
    def validate_pattern_structure_detailed(
        self,
        node_id: str,
        graph: PatternGraph,
    ) -> Dict[str, Any]:
        """
        Validate a pattern with detailed breakdown.
        
        Args:
            node_id: ID of the node to validate
            graph: The pattern graph
            
        Returns:
            Detailed validation result dictionary
        """
        node = graph.get_node(node_id)
        if not node:
            return {
                "node_id": node_id,
                "is_valid": False,
                "error": "Node not found",
                "structural_issues": [],
                "missing_references": [],
                "circular_deps": [],
                "composition_depth": -1,
                "all_children_resolved": False,
            }
        
        result = self.validate_pattern_structure(node, graph)
        return result.to_dict()
    
    def validate_batch(
        self,
        node_ids: List[str],
        graph: PatternGraph,
    ) -> Dict[str, Any]:
        """
        Validate a batch of patterns.
        
        Args:
            node_ids: List of node IDs to validate
            graph: The pattern graph
            
        Returns:
            Batch validation summary
        """
        results = {
            "total": len(node_ids),
            "valid": 0,
            "invalid": 0,
            "by_issue_type": {},
            "details": [],
        }
        
        for node_id in node_ids:
            result = self.validate_pattern_structure_detailed(node_id, graph)
            
            if result["is_valid"]:
                results["valid"] += 1
            else:
                results["invalid"] += 1
                
                # Count issue types
                for issue in result.get("structural_issues", []):
                    issue_type = issue.get("issue_type", "unknown")
                    results["by_issue_type"][issue_type] = (
                        results["by_issue_type"].get(issue_type, 0) + 1
                    )
            
            results["details"].append(result)
        
        return results
    
    def suggest_fixes(
        self,
        node_id: str,
        graph: PatternGraph,
    ) -> List[str]:
        """
        Suggest fixes for a pattern's issues.
        
        Args:
            node_id: ID of the node to fix
            graph: The pattern graph
            
        Returns:
            List of suggested fixes
        """
        result = self.validate_pattern_structure_detailed(node_id, graph)
        
        if result["is_valid"]:
            return ["No fixes needed - pattern is valid."]
        
        fixes = []
        
        # Suggest fixes for missing references
        for missing in result.get("missing_references", []):
            fixes.append(
                f"Create missing child node '{missing}' or remove the "
                f"COMPOSED_OF edge pointing to it."
            )
        
        # Suggest fixes for circular dependencies
        for cycle in result.get("circular_deps", []):
            cycle_str = " -> ".join(cycle)
            fixes.append(
                f"Break circular dependency cycle: {cycle_str}. "
                f"Consider restructuring the pattern hierarchy."
            )
        
        # Suggest hierarchy level fixes
        if result.get("composition_depth", 0) != graph.get_node(node_id).hierarchy_level:
            fixes.append(
                f"Update hierarchy level to {result['composition_depth']} "
                f"to match actual composition depth."
            )
        
        return fixes
    
    def clear_cache(self) -> None:
        """Clear the validation cache."""
        self._validation_cache.clear()
    
    def get_cached_result(self, node_id: str) -> Optional[ValidationResult]:
        """Get a cached validation result."""
        return self._validation_cache.get(node_id)
