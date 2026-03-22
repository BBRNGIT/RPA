"""
Long-Term Memory (LTM) for the RPA system.

LTM provides persistent storage for validated patterns that have
been consolidated from Short-Term Memory.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import json
import uuid

from rpa.core.graph import Node, Edge, PatternGraph, NodeType, EdgeType


@dataclass
class ConsolidationRecord:
    """Record of a pattern consolidation from STM to LTM."""
    record_id: str
    node_id: str
    session_id: str
    consolidated_at: datetime = field(default_factory=datetime.now)
    validation_score: float = 0.0
    source: str = ""
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "record_id": self.record_id,
            "node_id": self.node_id,
            "session_id": self.session_id,
            "consolidated_at": self.consolidated_at.isoformat(),
            "validation_score": self.validation_score,
            "source": self.source,
            "notes": self.notes,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConsolidationRecord":
        """Deserialize from dictionary."""
        return cls(
            record_id=data["record_id"],
            node_id=data["node_id"],
            session_id=data["session_id"],
            consolidated_at=datetime.fromisoformat(data["consolidated_at"]),
            validation_score=data.get("validation_score", 0.0),
            source=data.get("source", ""),
            notes=data.get("notes", ""),
        )


class LongTermMemory:
    """
    Long-Term Memory for persistent pattern storage.
    
    LTM stores validated patterns that have been consolidated
    from STM. It provides efficient querying, indexing, and
    persistence capabilities.
    """
    
    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize LTM.
        
        Args:
            storage_path: Optional path for persistent storage
        """
        self.storage_path = storage_path
        
        # Internal graph for pattern storage
        self._graph = PatternGraph(domain="ltm")
        
        # Indices for fast lookup
        self._label_index: Dict[str, Set[str]] = {}  # label -> node_ids
        self._domain_index: Dict[str, Set[str]] = {}  # domain -> node_ids
        self._content_index: Dict[str, Set[str]] = {}  # content -> node_ids
        
        # Consolidation records
        self._consolidation_records: Dict[str, ConsolidationRecord] = {}
        self._node_consolidation: Dict[str, str] = {}  # node_id -> record_id
        
        # Pattern versioning
        self._pattern_versions: Dict[str, List[str]] = {}  # node_id -> list of version_ids
        self._current_version: Dict[str, str] = {}  # node_id -> current version_id
        
        # Statistics
        self._stats = {
            "patterns_consolidated": 0,
            "patterns_deprecated": 0,
            "patterns_restored": 0,
            "queries_total": 0,
        }
    
    # === Pattern Operations ===
    
    def consolidate(self, node: Node, session_id: str = "", 
                    validation_score: float = 0.0,
                    source: str = "", notes: str = "") -> Node:
        """
        Consolidate a pattern from STM into LTM.
        
        Args:
            node: The pattern node to consolidate
            session_id: Session ID from STM
            validation_score: Score from validation
            source: Source of the pattern
            notes: Additional notes
            
        Returns:
            The consolidated node
        """
        # Mark as consolidated
        node.is_consolidated = True
        node.is_valid = True
        node.session_id = session_id
        
        # Add to graph
        if self._graph.has_node(node.node_id):
            self._graph.update_node(node)
        else:
            self._graph.add_node(node)
        
        # Update indices
        self._index_node(node)
        
        # Create consolidation record
        record_id = f"cons_{uuid.uuid4().hex[:8]}"
        record = ConsolidationRecord(
            record_id=record_id,
            node_id=node.node_id,
            session_id=session_id,
            validation_score=validation_score,
            source=source,
            notes=notes,
        )
        self._consolidation_records[record_id] = record
        self._node_consolidation[node.node_id] = record_id
        
        # Initialize versioning
        if node.node_id not in self._pattern_versions:
            self._pattern_versions[node.node_id] = []
            self._current_version[node.node_id] = node.node_id
        
        self._stats["patterns_consolidated"] += 1
        
        return node
    
    def get_pattern(self, node_id: str) -> Optional[Node]:
        """Get a pattern by ID."""
        self._stats["queries_total"] += 1
        return self._graph.get_node(node_id)
    
    def has_pattern(self, node_id: str) -> bool:
        """Check if a pattern exists."""
        return self._graph.has_node(node_id)
    
    def update_pattern(self, node: Node, reason: str = "") -> Node:
        """
        Update an existing pattern.
        
        Creates a new version of the pattern.
        
        Args:
            node: The updated pattern node
            reason: Reason for the update
            
        Returns:
            The updated node
        """
        if not self._graph.has_node(node.node_id):
            raise ValueError(f"Pattern {node.node_id} does not exist in LTM")
        
        old_node = self._graph.get_node(node.node_id)
        
        # Update indices if changed
        if old_node.label != node.label:
            self._label_index.get(old_node.label, set()).discard(node.node_id)
            self._index_node(node)
        
        if old_node.content != node.content:
            self._content_index.get(old_node.content, set()).discard(node.node_id)
            self._index_node(node)
        
        # Update graph
        self._graph.update_node(node)
        
        return node
    
    def deprecate_pattern(self, node_id: str, reason: str = "") -> bool:
        """
        Deprecate a pattern (soft delete).
        
        Args:
            node_id: Pattern to deprecate
            reason: Reason for deprecation
            
        Returns:
            True if successful
        """
        node = self._graph.get_node(node_id)
        if not node:
            return False
        
        node.is_valid = False
        node.metadata["deprecated"] = True
        node.metadata["deprecation_reason"] = reason
        node.metadata["deprecated_at"] = datetime.now().isoformat()
        
        self._graph.update_node(node)
        
        # Remove from indices
        self._label_index.get(node.label, set()).discard(node_id)
        self._content_index.get(node.content, set()).discard(node_id)
        
        self._stats["patterns_deprecated"] += 1
        
        return True
    
    def restore_pattern(self, node_id: str) -> bool:
        """
        Restore a deprecated pattern.
        
        Args:
            node_id: Pattern to restore
            
        Returns:
            True if successful
        """
        node = self._graph.get_node(node_id)
        if not node:
            return False
        
        node.is_valid = True
        node.metadata["deprecated"] = False
        node.metadata["restored_at"] = datetime.now().isoformat()
        
        self._graph.update_node(node)
        self._index_node(node)
        
        self._stats["patterns_restored"] += 1
        
        return True
    
    def delete_pattern(self, node_id: str) -> bool:
        """
        Permanently delete a pattern.
        
        Args:
            node_id: Pattern to delete
            
        Returns:
            True if successful
        """
        if not self._graph.has_node(node_id):
            return False
        
        node = self._graph.get_node(node_id)
        
        # Remove from indices
        self._label_index.get(node.label, set()).discard(node_id)
        self._content_index.get(node.content, set()).discard(node_id)
        self._domain_index.get(node.domain, set()).discard(node_id)
        
        # Remove consolidation records
        record_id = self._node_consolidation.pop(node_id, None)
        if record_id:
            del self._consolidation_records[record_id]
        
        # Remove versioning
        self._pattern_versions.pop(node_id, None)
        self._current_version.pop(node_id, None)
        
        # Remove from graph
        return self._graph.delete_node(node_id)
    
    # === Edge Operations ===
    
    def add_edge(self, edge: Edge) -> Edge:
        """Add an edge to LTM."""
        return self._graph.add_edge(edge)
    
    def get_edge(self, edge_id: str) -> Optional[Edge]:
        """Get an edge by ID."""
        return self._graph.get_edge(edge_id)
    
    def delete_edge(self, edge_id: str) -> bool:
        """Delete an edge."""
        return self._graph.delete_edge(edge_id)
    
    # === Query Operations ===
    
    def find_by_label(self, label: str) -> List[Node]:
        """Find patterns by label."""
        self._stats["queries_total"] += 1
        node_ids = self._label_index.get(label, set())
        return [self._graph.get_node(nid) for nid in node_ids if self._graph.has_node(nid)]
    
    def find_by_content(self, content: str) -> List[Node]:
        """Find patterns by content."""
        self._stats["queries_total"] += 1
        node_ids = self._content_index.get(content, set())
        return [self._graph.get_node(nid) for nid in node_ids if self._graph.has_node(nid)]
    
    def find_by_domain(self, domain: str) -> List[Node]:
        """Find patterns by domain."""
        self._stats["queries_total"] += 1
        node_ids = self._domain_index.get(domain, set())
        return [self._graph.get_node(nid) for nid in node_ids if self._graph.has_node(nid)]
    
    def find_by_type(self, node_type: NodeType) -> List[Node]:
        """Find patterns by type."""
        self._stats["queries_total"] += 1
        return self._graph.get_nodes_by_type(node_type)
    
    def find_by_level(self, level: int) -> List[Node]:
        """Find patterns by hierarchy level."""
        self._stats["queries_total"] += 1
        return self._graph.get_nodes_by_level(level)
    
    def find_uncertain_patterns(self) -> List[Node]:
        """Find patterns flagged as uncertain."""
        self._stats["queries_total"] += 1
        return [n for n in self._graph._nodes.values() if n.is_uncertain]
    
    def find_orphaned_patterns(self) -> List[Node]:
        """Find patterns not referenced by any parent."""
        self._stats["queries_total"] += 1
        orphans = []
        for node in self._graph.nodes.values():
            if node.node_type == NodeType.PRIMITIVE:
                continue
            parents = self._graph.get_parents(node.node_id)
            if not parents and node.hierarchy_level > 0:
                orphans.append(node)
        return orphans
    
    def find_incomplete_patterns(self) -> List[Dict[str, Any]]:
        """Find patterns with missing child references."""
        self._stats["queries_total"] += 1
        incomplete = []
        
        for node in self._graph.nodes.values():
            if node.node_type == NodeType.PRIMITIVE:
                continue
            
            missing_children = []
            for child_id in node.children:
                if not self._graph.has_node(child_id):
                    missing_children.append(child_id)
            
            if missing_children:
                incomplete.append({
                    "node_id": node.node_id,
                    "missing_children": missing_children,
                    "severity": "high" if len(missing_children) > 1 else "medium",
                })
        
        return incomplete
    
    def search(self, query: str, limit: int = 10) -> List[Node]:
        """
        Search for patterns matching a query.
        
        Searches in labels and content.
        """
        self._stats["queries_total"] += 1
        query_lower = query.lower()
        results = []
        
        for node in self._graph.nodes.values():
            if query_lower in node.label.lower() or query_lower in node.content.lower():
                results.append(node)
                if len(results) >= limit:
                    break
        
        return results
    
    # === Indexing ===
    
    def _index_node(self, node: Node) -> None:
        """Add node to indices."""
        # Label index
        if node.label not in self._label_index:
            self._label_index[node.label] = set()
        self._label_index[node.label].add(node.node_id)
        
        # Content index
        if node.content not in self._content_index:
            self._content_index[node.content] = set()
        self._content_index[node.content].add(node.node_id)
        
        # Domain index
        if node.domain not in self._domain_index:
            self._domain_index[node.domain] = set()
        self._domain_index[node.domain].add(node.node_id)
    
    def rebuild_indices(self) -> None:
        """Rebuild all indices from scratch."""
        self._label_index.clear()
        self._content_index.clear()
        self._domain_index.clear()
        
        for node in self._graph.nodes.values():
            self._index_node(node)
    
    # === Consolidation Records ===
    
    def get_consolidation_record(self, node_id: str) -> Optional[ConsolidationRecord]:
        """Get the consolidation record for a pattern."""
        record_id = self._node_consolidation.get(node_id)
        if record_id:
            return self._consolidation_records.get(record_id)
        return None
    
    def get_all_consolidation_records(self) -> List[ConsolidationRecord]:
        """Get all consolidation records."""
        return list(self._consolidation_records.values())
    
    # === Statistics ===
    
    def get_stats(self) -> Dict[str, Any]:
        """Get LTM statistics."""
        return {
            **self._stats,
            "total_patterns": len(self._graph),
            "total_edges": len(self._graph.edges),
            "domains": list(self._domain_index.keys()),
            "patterns_by_domain": {
                domain: len(nodes) 
                for domain, nodes in self._domain_index.items()
            },
            "hierarchy_levels": {
                level: len(nodes)
                for level, nodes in self._graph._hierarchy_index.items()
            },
            "graph_stats": self._graph.get_stats(),
        }
    
    # === Persistence ===
    
    def save(self, path: Optional[Path] = None) -> None:
        """Save LTM to disk."""
        path = path or self.storage_path
        if not path:
            raise ValueError("No storage path specified")
        
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        
        # Save graph
        graph_path = path / "graph.json"
        with open(graph_path, "w") as f:
            json.dump(self._graph.to_dict(), f, indent=2)
        
        # Save consolidation records
        records_path = path / "consolidation_records.json"
        with open(records_path, "w") as f:
            json.dump({
                rid: r.to_dict() 
                for rid, r in self._consolidation_records.items()
            }, f, indent=2)
        
        # Save metadata
        meta_path = path / "metadata.json"
        with open(meta_path, "w") as f:
            json.dump({
                "stats": self._stats,
                "node_to_record": self._node_consolidation,
            }, f, indent=2)
    
    def load(self, path: Optional[Path] = None) -> None:
        """Load LTM from disk."""
        path = path or self.storage_path
        if not path:
            raise ValueError("No storage path specified")
        
        path = Path(path)
        
        # Load graph
        graph_path = path / "graph.json"
        if graph_path.exists():
            with open(graph_path) as f:
                self._graph = PatternGraph.from_dict(json.load(f))
        
        # Load consolidation records
        records_path = path / "consolidation_records.json"
        if records_path.exists():
            with open(records_path) as f:
                records_data = json.load(f)
                self._consolidation_records = {
                    rid: ConsolidationRecord.from_dict(r)
                    for rid, r in records_data.items()
                }
        
        # Load metadata
        meta_path = path / "metadata.json"
        if meta_path.exists():
            with open(meta_path) as f:
                meta = json.load(f)
                self._stats = meta.get("stats", self._stats)
                self._node_consolidation = meta.get("node_to_record", {})
        
        # Rebuild indices
        self.rebuild_indices()
    
    # === Serialization ===
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize LTM to dictionary."""
        return {
            "graph": self._graph.to_dict(),
            "consolidation_records": {
                rid: r.to_dict() 
                for rid, r in self._consolidation_records.items()
            },
            "node_consolidation": self._node_consolidation,
            "stats": self._stats,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LongTermMemory":
        """Deserialize LTM from dictionary."""
        ltm = cls()
        
        ltm._graph = PatternGraph.from_dict(data["graph"])
        
        for rid, rdata in data.get("consolidation_records", {}).items():
            ltm._consolidation_records[rid] = ConsolidationRecord.from_dict(rdata)
        
        ltm._node_consolidation = data.get("node_consolidation", {})
        ltm._stats = data.get("stats", ltm._stats)
        
        ltm.rebuild_indices()
        
        return ltm
    
    def __len__(self) -> int:
        """Return the number of patterns in LTM."""
        return len(self._graph)
    
    def __contains__(self, node_id: str) -> bool:
        """Check if a pattern exists in LTM."""
        return self._graph.has_node(node_id)
    
    def __repr__(self) -> str:
        return f"LongTermMemory(patterns={len(self._graph)}, domains={len(self._domain_index)})"
    
    # === Convenience Methods for New Modules ===
    
    def add_node(self, node: Node) -> Node:
        """
        Add a node directly to LTM.
        
        Convenience method for adding nodes without full consolidation.
        
        Args:
            node: Node to add
            
        Returns:
            The added node
        """
        if self._graph.has_node(node.node_id):
            self._graph.update_node(node)
        else:
            self._graph.add_node(node)
        
        self._index_node(node)
        return node
    
    def get_node(self, node_id: str) -> Optional[Node]:
        """
        Get a node by ID.
        
        Alias for get_pattern() for convenience.
        
        Args:
            node_id: ID of the node
            
        Returns:
            Node if found, None otherwise
        """
        return self.get_pattern(node_id)
    
    @property
    def _nodes(self) -> Dict[str, Node]:
        """Direct access to nodes dictionary."""
        return self._graph.nodes
    
    @property  
    def _edges(self) -> Dict[str, Edge]:
        """Direct access to edges dictionary."""
        return self._graph.edges
    
    def get_edges_from(self, node_id: str, edge_type: Optional[EdgeType] = None) -> List[Edge]:
        """Get all edges originating from a node."""
        return self._graph.get_outgoing_edges(node_id, edge_type)
    
    def get_edges_to(self, node_id: str, edge_type: Optional[EdgeType] = None) -> List[Edge]:
        """Get all edges pointing to a node."""
        return self._graph.get_incoming_edges(node_id, edge_type)
