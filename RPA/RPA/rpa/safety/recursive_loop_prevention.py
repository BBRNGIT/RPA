"""
Recursive Loop Prevention - Detect and prevent infinite loops in pattern graphs.

This module provides mechanisms to detect and prevent circular dependencies
and infinite recursion in the pattern graph structure.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Set, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict
import hashlib


@dataclass
class LoopInfo:
    """Information about a detected loop."""
    loop_id: str
    nodes: List[str]
    length: int
    severity: str  # "critical", "warning", "info"
    detection_method: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "loop_id": self.loop_id,
            "nodes": self.nodes,
            "length": self.length,
            "severity": self.severity,
            "detection_method": self.detection_method,
            "timestamp": self.timestamp,
        }


@dataclass
class LoopDetectionResult:
    """Result of loop detection on a pattern graph."""
    has_loops: bool
    loops: List[LoopInfo]
    total_nodes_checked: int
    total_edges_checked: int
    detection_time_ms: float = 0.0
    safe_to_proceed: bool = True
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "has_loops": self.has_loops,
            "loops": [loop.to_dict() for loop in self.loops],
            "total_nodes_checked": self.total_nodes_checked,
            "total_edges_checked": self.total_edges_checked,
            "detection_time_ms": self.detection_time_ms,
            "safe_to_proceed": self.safe_to_proceed,
            "recommendations": self.recommendations,
        }


class RecursiveLoopPrevention:
    """
    Detect and prevent recursive loops in pattern graphs.

    This class provides multiple detection strategies:
    - Depth-first search for cycles
    - Tarjan's algorithm for strongly connected components
    - Recursion depth monitoring
    - Pattern reference validation
    """

    # Maximum allowed recursion depth
    MAX_RECURSION_DEPTH = 100

    # Maximum allowed pattern chain length
    MAX_CHAIN_LENGTH = 1000

    # Severity thresholds
    CRITICAL_LOOP_LENGTH = 2  # Self-referencing or immediate loops
    WARNING_LOOP_LENGTH = 10  # Longer loops that might cause issues

    def __init__(self, max_depth: Optional[int] = None):
        """
        Initialize the loop prevention system.

        Args:
            max_depth: Maximum allowed recursion depth. Defaults to MAX_RECURSION_DEPTH.
        """
        self.max_depth = max_depth or self.MAX_RECURSION_DEPTH
        self._detected_loops: Dict[str, LoopInfo] = {}
        self._node_visit_counts: Dict[str, int] = defaultdict(int)
        self._detection_stats: Dict[str, int] = {
            "checks_performed": 0,
            "loops_detected": 0,
            "loops_prevented": 0,
        }

    def detect_cycles_dfs(self, graph: Dict[str, List[str]]) -> LoopDetectionResult:
        """
        Detect cycles using depth-first search.

        Args:
            graph: Adjacency list representation of the graph.
                  Keys are node IDs, values are lists of connected node IDs.

        Returns:
            LoopDetectionResult with detected cycles.
        """
        start_time = datetime.now()
        loops = []
        visited = set()
        rec_stack = set()
        path = []

        def dfs(node: str) -> Optional[List[str]]:
            """DFS helper to find cycles."""
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            # Track visit counts
            self._node_visit_counts[node] += 1

            # Check recursion depth
            if len(path) > self.max_depth:
                return path  # Depth exceeded

            # Visit neighbors
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    cycle = dfs(neighbor)
                    if cycle:
                        return cycle
                elif neighbor in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(neighbor)
                    return path[cycle_start:]

            path.pop()
            rec_stack.remove(node)
            return None

        # Check each node
        total_edges = sum(len(neighbors) for neighbors in graph.values())

        for node in graph:
            if node not in visited:
                path.clear()
                rec_stack.clear()

                cycle = dfs(node)
                if cycle:
                    loop_id = self._compute_loop_id(cycle)
                    severity = self._determine_severity(len(cycle))

                    loops.append(LoopInfo(
                        loop_id=loop_id,
                        nodes=cycle,
                        length=len(cycle),
                        severity=severity,
                        detection_method="dfs_cycle_detection",
                    ))

                    self._detected_loops[loop_id] = loops[-1]

        detection_time = (datetime.now() - start_time).total_seconds() * 1000

        # Update stats
        self._detection_stats["checks_performed"] += 1
        self._detection_stats["loops_detected"] += len(loops)

        return LoopDetectionResult(
            has_loops=len(loops) > 0,
            loops=loops,
            total_nodes_checked=len(graph),
            total_edges_checked=total_edges,
            detection_time_ms=detection_time,
            safe_to_proceed=len(loops) == 0,
            recommendations=self._generate_recommendations(loops),
        )

    def detect_strongly_connected_components(self, graph: Dict[str, List[str]]) -> LoopDetectionResult:
        """
        Detect strongly connected components using Tarjan's algorithm.

        Args:
            graph: Adjacency list representation of the graph.

        Returns:
            LoopDetectionResult with detected SCCs that form cycles.
        """
        start_time = datetime.now()
        loops = []

        index_counter = [0]
        stack = []
        lowlinks = {}
        index = {}
        on_stack = {}
        sccs = []

        def strongconnect(node: str):
            """Tarjan's algorithm helper."""
            index[node] = index_counter[0]
            lowlinks[node] = index_counter[0]
            index_counter[0] += 1
            stack.append(node)
            on_stack[node] = True

            for successor in graph.get(node, []):
                if successor not in index:
                    strongconnect(successor)
                    lowlinks[node] = min(lowlinks[node], lowlinks[successor])
                elif on_stack.get(successor, False):
                    lowlinks[node] = min(lowlinks[node], index[successor])

            # If node is a root node, pop the stack and generate SCC
            if lowlinks[node] == index[node]:
                scc = []
                while True:
                    w = stack.pop()
                    on_stack[w] = False
                    scc.append(w)
                    if w == node:
                        break

                if len(scc) > 1:  # SCC with multiple nodes = cycle
                    sccs.append(scc)
                elif len(scc) == 1 and scc[0] in graph.get(scc[0], []):
                    # Self-loop
                    sccs.append(scc)

        # Run Tarjan's algorithm
        for node in graph:
            if node not in index:
                strongconnect(node)

        total_edges = sum(len(neighbors) for neighbors in graph.values())

        # Convert SCCs to LoopInfo
        for scc in sccs:
            loop_id = self._compute_loop_id(scc)
            severity = self._determine_severity(len(scc))

            loops.append(LoopInfo(
                loop_id=loop_id,
                nodes=scc,
                length=len(scc),
                severity=severity,
                detection_method="tarjan_scc",
            ))

            self._detected_loops[loop_id] = loops[-1]

        detection_time = (datetime.now() - start_time).total_seconds() * 1000

        # Update stats
        self._detection_stats["checks_performed"] += 1
        self._detection_stats["loops_detected"] += len(loops)

        return LoopDetectionResult(
            has_loops=len(loops) > 0,
            loops=loops,
            total_nodes_checked=len(graph),
            total_edges_checked=total_edges,
            detection_time_ms=detection_time,
            safe_to_proceed=len(loops) == 0,
            recommendations=self._generate_recommendations(loops),
        )

    def check_recursion_depth(self, call_stack: List[str]) -> Tuple[bool, Optional[str]]:
        """
        Check if the current recursion depth exceeds limits.

        Args:
            call_stack: Current call stack as list of node IDs.

        Returns:
            Tuple of (is_safe, warning_message).
        """
        depth = len(call_stack)

        if depth > self.max_depth:
            self._detection_stats["loops_prevented"] += 1
            return False, f"Recursion depth {depth} exceeds maximum {self.max_depth}"

        if depth > self.max_depth * 0.8:
            return True, f"Recursion depth {depth} approaching limit {self.max_depth}"

        return True, None

    def check_chain_length(self, chain: List[str]) -> Tuple[bool, Optional[str]]:
        """
        Check if a pattern chain is too long.

        Args:
            chain: Pattern chain as list of node IDs.

        Returns:
            Tuple of (is_safe, warning_message).
        """
        length = len(chain)

        if length > self.MAX_CHAIN_LENGTH:
            self._detection_stats["loops_prevented"] += 1
            return False, f"Chain length {length} exceeds maximum {self.MAX_CHAIN_LENGTH}"

        if length > self.MAX_CHAIN_LENGTH * 0.8:
            return True, f"Chain length {length} approaching limit {self.MAX_CHAIN_LENGTH}"

        return True, None

    def validate_pattern_reference(
        self,
        source_id: str,
        target_id: str,
        existing_graph: Dict[str, List[str]],
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate that adding a pattern reference won't create a loop.

        Args:
            source_id: Source pattern ID.
            target_id: Target pattern ID to reference.
            existing_graph: Existing pattern graph.

        Returns:
            Tuple of (is_valid, error_message).
        """
        # Check self-reference
        if source_id == target_id:
            self._detection_stats["loops_prevented"] += 1
            return False, f"Self-reference not allowed: {source_id}"

        # Simulate adding the edge
        test_graph = {k: list(v) for k, v in existing_graph.items()}
        if source_id not in test_graph:
            test_graph[source_id] = []
        test_graph[source_id].append(target_id)

        # Check for cycles
        result = self.detect_cycles_dfs(test_graph)

        if result.has_loops:
            self._detection_stats["loops_prevented"] += 1
            return False, f"Adding edge {source_id} -> {target_id} would create a cycle"

        return True, None

    def get_visit_count(self, node_id: str) -> int:
        """Get the number of times a node has been visited during checks."""
        return self._node_visit_counts.get(node_id, 0)

    def get_hot_nodes(self, threshold: int = 10) -> List[Tuple[str, int]]:
        """
        Get nodes that are visited frequently (potential hotspots).

        Args:
            threshold: Minimum visit count to be considered hot.

        Returns:
            List of (node_id, visit_count) tuples.
        """
        return [
            (node, count)
            for node, count in self._node_visit_counts.items()
            if count >= threshold
        ]

    def get_detected_loop(self, loop_id: str) -> Optional[LoopInfo]:
        """Get a detected loop by ID."""
        return self._detected_loops.get(loop_id)

    def get_all_detected_loops(self) -> List[LoopInfo]:
        """Get all detected loops."""
        return list(self._detected_loops.values())

    def clear_detected_loops(self) -> None:
        """Clear the detected loops cache."""
        self._detected_loops.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get detection statistics."""
        return {
            **self._detection_stats,
            "unique_loops_found": len(self._detected_loops),
            "max_depth_configured": self.max_depth,
        }

    def reset_stats(self) -> None:
        """Reset detection statistics."""
        self._detection_stats = {
            "checks_performed": 0,
            "loops_detected": 0,
            "loops_prevented": 0,
        }
        self._node_visit_counts.clear()
        self._detected_loops.clear()

    def _compute_loop_id(self, nodes: List[str]) -> str:
        """Compute a unique ID for a loop."""
        # Sort to create a canonical representation
        canonical = "|".join(sorted(nodes))
        return hashlib.md5(canonical.encode()).hexdigest()[:12]

    def _determine_severity(self, loop_length: int) -> str:
        """Determine the severity of a loop based on its length."""
        if loop_length <= self.CRITICAL_LOOP_LENGTH:
            return "critical"
        elif loop_length <= self.WARNING_LOOP_LENGTH:
            return "warning"
        return "info"

    def _generate_recommendations(self, loops: List[LoopInfo]) -> List[str]:
        """Generate recommendations based on detected loops."""
        recommendations = []

        if not loops:
            recommendations.append("No loops detected. Graph structure is safe.")
            return recommendations

        critical_count = sum(1 for l in loops if l.severity == "critical")
        warning_count = sum(1 for l in loops if l.severity == "warning")

        if critical_count > 0:
            recommendations.append(
                f"Critical: {critical_count} immediate loops detected. "
                "These must be resolved before proceeding."
            )

        if warning_count > 0:
            recommendations.append(
                f"Warning: {warning_count} longer loops detected. "
                "Consider restructuring to avoid potential issues."
            )

        recommendations.append(
            "Review pattern composition to ensure hierarchical structure without cycles."
        )

        return recommendations
