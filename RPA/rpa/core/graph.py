"""
Pattern Graph implementation for RPA.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from .node import Node, NodeType
from .edge import Edge, EdgeType


@dataclass
class PatternGraph:
    """
    A directed graph representing patterns and their relationships.
    
    Attributes:
        nodes: Dictionary of node_id to Node
        edges: Dictionary of edge_id to Edge
        outgoing_edges: Adjacency list for outgoing edges
        incoming_edges: Adjacency list for incoming edges
        domain: Domain identifier for this graph
    """
    nodes: Dict[str, Node] = field(default_factory=dict)
    edges: Dict[str, Edge] = field(default_factory=dict)
    outgoing_edges: Dict[str, List[str]] = field(default_factory=lambda: defaultdict(list))
    incoming_edges: Dict[str, List[str]] = field(default_factory=lambda: defaultdict(list))
    domain: str = "general"
    
    # Internal indices
    _hierarchy_index: Dict[int, Set[str]] = field(default_factory=lambda: defaultdict(set))
    _type_index: Dict[NodeType, Set[str]] = field(default_factory=lambda: defaultdict(set))
    
    def add_node(self, node: Node) -> bool:
        """
        Add a node to the graph.
        
        Returns:
            True if added, False if already exists
        """
        if node.node_id in self.nodes:
            return False
        self.nodes[node.node_id] = node
        
        # Update indices
        self._hierarchy_index[node.hierarchy_level].add(node.node_id)
        self._type_index[node.node_type].add(node.node_id)
        
        return True
    
    def get_node(self, node_id: str) -> Optional[Node]:
        """Get a node by ID."""
        return self.nodes.get(node_id)
    
    def has_node(self, node_id: str) -> bool:
        """Check if a node exists."""
        return node_id in self.nodes
    
    def update_node(self, node: Node) -> bool:
        """
        Update an existing node.
        
        Returns:
            True if updated, False if not found
        """
        if node.node_id not in self.nodes:
            return False
        
        old_node = self.nodes[node.node_id]
        
        # Update indices if hierarchy level changed
        if old_node.hierarchy_level != node.hierarchy_level:
            self._hierarchy_index[old_node.hierarchy_level].discard(node.node_id)
            self._hierarchy_index[node.hierarchy_level].add(node.node_id)
        
        # Update indices if type changed
        if old_node.node_type != node.node_type:
            self._type_index[old_node.node_type].discard(node.node_id)
            self._type_index[node.node_type].add(node.node_id)
        
        self.nodes[node.node_id] = node
        return True
    
    def delete_node(self, node_id: str) -> bool:
        """
        Delete a node and all its edges.
        
        Returns:
            True if deleted, False if not found
        """
        if node_id not in self.nodes:
            return False
        
        node = self.nodes[node_id]
        
        # Remove from indices
        self._hierarchy_index[node.hierarchy_level].discard(node_id)
        self._type_index[node.node_type].discard(node_id)
        
        # Remove all edges involving this node
        edges_to_remove = (
            self.outgoing_edges.get(node_id, []) + 
            self.incoming_edges.get(node_id, [])
        )
        for edge_id in edges_to_remove:
            self.delete_edge(edge_id)
        
        # Remove from main storage
        del self.nodes[node_id]
        self.outgoing_edges.pop(node_id, None)
        self.incoming_edges.pop(node_id, None)
        
        return True
    
    def add_edge(self, edge: Edge) -> Edge:
        """
        Add an edge to the graph.
        
        Returns:
            The edge if added
        
        Raises:
            ValueError if nodes don't exist
        """
        if edge.edge_id in self.edges:
            return self.edges[edge.edge_id]
        if edge.source_id not in self.nodes:
            raise ValueError(f"Source node {edge.source_id} does not exist")
        if edge.target_id not in self.nodes:
            raise ValueError(f"Target node {edge.target_id} does not exist")
        
        self.edges[edge.edge_id] = edge
        self.outgoing_edges[edge.source_id].append(edge.edge_id)
        self.incoming_edges[edge.target_id].append(edge.edge_id)
        
        return edge
    
    def get_edge(self, edge_id: str) -> Optional[Edge]:
        """Get an edge by ID."""
        return self.edges.get(edge_id)
    
    def has_edge(self, edge_id: str) -> bool:
        """Check if an edge exists."""
        return edge_id in self.edges
    
    def delete_edge(self, edge_id: str) -> bool:
        """
        Delete an edge.
        
        Returns:
            True if deleted, False if not found
        """
        if edge_id not in self.edges:
            return False
        
        edge = self.edges[edge_id]
        
        # Remove from adjacency lists
        if edge_id in self.outgoing_edges.get(edge.source_id, []):
            self.outgoing_edges[edge.source_id].remove(edge_id)
        if edge_id in self.incoming_edges.get(edge.target_id, []):
            self.incoming_edges[edge.target_id].remove(edge_id)
        
        del self.edges[edge_id]
        return True
    
    def get_outgoing_edges(
        self, 
        node_id: str, 
        edge_type: Optional[EdgeType] = None
    ) -> List[Edge]:
        """Get all outgoing edges from a node, optionally filtered by type."""
        if node_id not in self.outgoing_edges:
            return []
        
        edges = [self.edges[eid] for eid in self.outgoing_edges[node_id] if eid in self.edges]
        
        if edge_type:
            edges = [e for e in edges if e.edge_type == edge_type]
        
        return sorted(edges, key=lambda e: e.order)
    
    def get_incoming_edges(
        self, 
        node_id: str, 
        edge_type: Optional[EdgeType] = None
    ) -> List[Edge]:
        """Get all incoming edges to a node, optionally filtered by type."""
        if node_id not in self.incoming_edges:
            return []
        
        edges = [self.edges[eid] for eid in self.incoming_edges[node_id] if eid in self.edges]
        
        if edge_type:
            edges = [e for e in edges if e.edge_type == edge_type]
        
        return sorted(edges, key=lambda e: e.order)
    
    def get_children(self, node_id: str) -> List[Node]:
        """
        Get all children of a node (nodes it is composed of).
        Returns them in composition order.
        """
        edges = self.get_outgoing_edges(node_id, EdgeType.COMPOSED_OF)
        children = []
        for edge in sorted(edges, key=lambda e: e.order):
            child = self.get_node(edge.target_id)
            if child:
                children.append(child)
        return children
    
    def get_parents(self, node_id: str) -> List[Node]:
        """Get all parent nodes (nodes that compose this node)."""
        edges = self.get_incoming_edges(node_id, EdgeType.COMPOSED_OF)
        parents = []
        for edge in edges:
            parent = self.get_node(edge.source_id)
            if parent:
                parents.append(parent)
        return parents
    
    def detect_circular_dependencies(self, node_id: str) -> List[List[str]]:
        """
        Detect circular dependencies starting from a node.
        
        Returns:
            List of cycles found (each cycle is a list of node IDs)
        """
        cycles = []
        visited = set()
        path = []
        
        def dfs(current_id: str):
            if current_id in path:
                # Found a cycle
                cycle_start = path.index(current_id)
                cycle = path[cycle_start:] + [current_id]
                cycles.append(cycle)
                return
            
            if current_id in visited:
                return
            
            visited.add(current_id)
            path.append(current_id)
            
            for edge in self.get_outgoing_edges(current_id, EdgeType.COMPOSED_OF):
                dfs(edge.target_id)
            
            path.pop()
        
        dfs(node_id)
        return cycles
    
    def calculate_hierarchy_level(self, node_id: str) -> int:
        """
        Calculate the hierarchy level of a node based on its children.
        
        Primitives have level 0, patterns composed of primitives have level 1, etc.
        """
        node = self.get_node(node_id)
        if not node:
            return -1
        
        if node.node_type == NodeType.PRIMITIVE:
            return 0
        
        children = self.get_children(node_id)
        if not children:
            return node.hierarchy_level
        
        max_child_level = max(
            self.calculate_hierarchy_level(child.node_id) 
            for child in children
        )
        return max_child_level + 1
    
    def traverse_bfs(self, start_id: str, max_depth: int = 10) -> List[Node]:
        """
        Breadth-first traversal from a node.
        
        Args:
            start_id: Starting node ID
            max_depth: Maximum traversal depth
            
        Returns:
            List of nodes in BFS order
        """
        if start_id not in self.nodes:
            return []
        
        visited = set()
        queue = [(start_id, 0)]
        result = []
        
        while queue:
            node_id, depth = queue.pop(0)
            
            if depth > max_depth:
                continue
            
            if node_id in visited:
                continue
            
            visited.add(node_id)
            node = self.get_node(node_id)
            if node:
                result.append(node)
            
            for edge in self.get_outgoing_edges(node_id):
                if edge.target_id not in visited:
                    queue.append((edge.target_id, depth + 1))
        
        return result
    
    def get_all_nodes_by_type(self, node_type: NodeType) -> List[Node]:
        """Get all nodes of a specific type."""
        return [
            self.nodes[nid] 
            for nid in self._type_index.get(node_type, set())
            if nid in self.nodes
        ]
    
    def get_nodes_by_type(self, node_type: NodeType) -> List[Node]:
        """Get all nodes of a specific type (alias for get_all_nodes_by_type)."""
        return self.get_all_nodes_by_type(node_type)
    
    def get_all_nodes_by_domain(self, domain: str) -> List[Node]:
        """Get all nodes in a specific domain."""
        return [n for n in self.nodes.values() if n.domain == domain]
    
    def get_nodes_by_level(self, level: int) -> List[Node]:
        """Get all nodes at a specific hierarchy level."""
        return [
            self.nodes[nid] 
            for nid in self._hierarchy_index.get(level, set())
            if nid in self.nodes
        ]
    
    def find_unresolved_references(self) -> List[Dict[str, str]]:
        """
        Find edges that point to non-existent nodes.
        
        Returns:
            List of dicts with edge_id and missing target_id
        """
        unresolved = []
        for edge in self.edges.values():
            if edge.target_id not in self.nodes:
                unresolved.append({
                    "edge_id": edge.edge_id,
                    "source_id": edge.source_id,
                    "missing_target": edge.target_id,
                })
        return unresolved
    
    def get_node_count(self) -> int:
        """Get total number of nodes."""
        return len(self.nodes)
    
    def get_edge_count(self) -> int:
        """Get total number of edges."""
        return len(self.edges)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get graph statistics."""
        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "nodes_by_level": {
                level: len(nodes) 
                for level, nodes in self._hierarchy_index.items()
            },
            "nodes_by_type": {
                t.value: len(nodes) 
                for t, nodes in self._type_index.items()
            },
        }
    
    def clear(self) -> None:
        """Clear all nodes and edges."""
        self.nodes.clear()
        self.edges.clear()
        self.outgoing_edges.clear()
        self.incoming_edges.clear()
        self._hierarchy_index.clear()
        self._type_index.clear()
    
    def to_dict(self) -> Dict:
        """Serialize the graph to a dictionary."""
        return {
            "domain": self.domain,
            "nodes": {nid: node.to_dict() for nid, node in self.nodes.items()},
            "edges": {eid: edge.to_dict() for eid, edge in self.edges.items()},
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "PatternGraph":
        """Deserialize a graph from a dictionary."""
        graph = cls(domain=data.get("domain", "general"))
        
        # Add nodes first
        for nid, node_data in data.get("nodes", {}).items():
            graph.add_node(Node.from_dict(node_data))
        
        # Then add edges
        for eid, edge_data in data.get("edges", {}).items():
            try:
                graph.add_edge(Edge.from_dict(edge_data))
            except ValueError:
                # Skip edges with missing nodes
                pass
        
        return graph
    
    def __len__(self) -> int:
        """Return the number of nodes."""
        return len(self.nodes)
    
    def __contains__(self, node_id: str) -> bool:
        """Check if a node exists."""
        return node_id in self.nodes
    
    def __repr__(self) -> str:
        return f"PatternGraph(nodes={len(self.nodes)}, edges={len(self.edges)})"
