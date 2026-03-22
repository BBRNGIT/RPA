"""
Short-Term Memory (STM) for the RPA system.

STM provides temporary storage for new patterns before they are
validated and consolidated into Long-Term Memory (LTM).
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
import uuid

from rpa.core.graph import Node, Edge, PatternGraph, NodeType


@dataclass
class STMSession:
    """Represents a learning session in STM."""
    session_id: str
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    patterns_learned: List[str] = field(default_factory=list)
    patterns_validated: List[str] = field(default_factory=list)
    patterns_rejected: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def touch(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = datetime.now()


class ShortTermMemory:
    """
    Short-Term Memory for temporary pattern storage.
    
    STM holds newly learned patterns before they are validated
    and consolidated into LTM. It provides session-based isolation
    and automatic expiration of old patterns.
    """
    
    def __init__(self, ttl_hours: int = 24, max_patterns: int = 1000):
        """
        Initialize STM.
        
        Args:
            ttl_hours: Time-to-live for patterns in hours
            max_patterns: Maximum number of patterns to store
        """
        self.ttl = timedelta(hours=ttl_hours)
        self.max_patterns = max_patterns
        
        # Internal graph for pattern storage
        self._graph = PatternGraph(domain="stm")
        
        # Session management
        self._sessions: Dict[str, STMSession] = {}
        self._current_session: Optional[str] = None
        
        # Pattern tracking
        self._pattern_timestamps: Dict[str, datetime] = {}
        self._pattern_sessions: Dict[str, str] = {}
        
        # Pending validation queue
        self._pending_validation: Set[str] = set()
        
        # Statistics
        self._stats = {
            "patterns_created": 0,
            "patterns_validated": 0,
            "patterns_rejected": 0,
            "patterns_expired": 0,
        }
    
    # === Session Management ===
    
    def create_session(self, session_id: Optional[str] = None, 
                       metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a new learning session.
        
        Args:
            session_id: Optional custom session ID
            metadata: Optional session metadata
            
        Returns:
            The session ID
        """
        if session_id is None:
            session_id = f"session_{uuid.uuid4().hex[:8]}"
        
        self._sessions[session_id] = STMSession(
            session_id=session_id,
            metadata=metadata or {}
        )
        self._current_session = session_id
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[STMSession]:
        """Get a session by ID."""
        return self._sessions.get(session_id)
    
    def get_current_session(self) -> Optional[STMSession]:
        """Get the current active session."""
        if self._current_session:
            return self._sessions.get(self._current_session)
        return None
    
    def set_current_session(self, session_id: str) -> bool:
        """Set the current active session."""
        if session_id in self._sessions:
            self._current_session = session_id
            return True
        return False
    
    def end_session(self, session_id: Optional[str] = None) -> Optional[STMSession]:
        """
        End a session.
        
        Args:
            session_id: Session to end, or current session if None
            
        Returns:
            The ended session, or None if not found
        """
        if session_id is None:
            session_id = self._current_session
        
        if session_id and session_id in self._sessions:
            session = self._sessions[session_id]
            if self._current_session == session_id:
                self._current_session = None
            return session
        
        return None
    
    def list_sessions(self) -> List[STMSession]:
        """List all sessions."""
        return list(self._sessions.values())
    
    # === Pattern Operations ===
    
    def add_pattern(self, node: Node, session_id: Optional[str] = None) -> Node:
        """
        Add a pattern to STM.
        
        Args:
            node: The pattern node to add
            session_id: Session ID, uses current session if None
            
        Returns:
            The added node
        """
        # Determine session
        if session_id is None:
            session_id = self._current_session
        
        if session_id is None:
            session_id = self.create_session()
        
        # Set session on node
        node.session_id = session_id
        
        # Add to graph
        self._graph.add_node(node)
        
        # Track timestamp and session
        self._pattern_timestamps[node.node_id] = datetime.now()
        self._pattern_sessions[node.node_id] = session_id
        
        # Add to pending validation
        self._pending_validation.add(node.node_id)
        
        # Update session
        session = self._sessions.get(session_id)
        if session:
            session.patterns_learned.append(node.node_id)
            session.touch()
        
        # Update stats
        self._stats["patterns_created"] += 1
        
        # Check capacity
        self._enforce_capacity()
        
        return node
    
    def get_pattern(self, node_id: str) -> Optional[Node]:
        """Get a pattern by ID."""
        return self._graph.get_node(node_id)
    
    def has_pattern(self, node_id: str) -> bool:
        """Check if a pattern exists."""
        return self._graph.has_node(node_id)
    
    def update_pattern(self, node: Node) -> None:
        """Update an existing pattern."""
        self._graph.update_node(node)
        if node.node_id in self._pattern_timestamps:
            self._pattern_timestamps[node.node_id] = datetime.now()
    
    def remove_pattern(self, node_id: str) -> bool:
        """Remove a pattern from STM."""
        if not self._graph.has_node(node_id):
            return False
        
        # Remove from tracking
        self._pattern_timestamps.pop(node_id, None)
        session_id = self._pattern_sessions.pop(node_id, None)
        self._pending_validation.discard(node_id)
        
        # Remove from graph
        result = self._graph.delete_node(node_id)
        
        # Update session if applicable
        if session_id and session_id in self._sessions:
            session = self._sessions[session_id]
            if node_id in session.patterns_learned:
                session.patterns_learned.remove(node_id)
            if node_id in session.patterns_validated:
                session.patterns_validated.remove(node_id)
            if node_id in session.patterns_rejected:
                session.patterns_rejected.remove(node_id)
        
        return result
    
    def get_pending_patterns(self) -> List[Node]:
        """Get all patterns pending validation."""
        return [
            self._graph.get_node(nid) 
            for nid in self._pending_validation 
            if self._graph.has_node(nid)
        ]
    
    def mark_validated(self, node_id: str) -> bool:
        """Mark a pattern as validated."""
        node = self._graph.get_node(node_id)
        if not node:
            return False
        
        node.is_valid = True
        self._graph.update_node(node)
        self._pending_validation.discard(node_id)
        
        # Update session
        session_id = self._pattern_sessions.get(node_id)
        if session_id and session_id in self._sessions:
            session = self._sessions[session_id]
            if node_id not in session.patterns_validated:
                session.patterns_validated.append(node_id)
            session.touch()
        
        self._stats["patterns_validated"] += 1
        
        return True
    
    def mark_rejected(self, node_id: str) -> bool:
        """Mark a pattern as rejected."""
        node = self._graph.get_node(node_id)
        if not node:
            return False
        
        node.is_valid = False
        self._graph.update_node(node)
        self._pending_validation.discard(node_id)
        
        # Update session
        session_id = self._pattern_sessions.get(node_id)
        if session_id and session_id in self._sessions:
            session = self._sessions[session_id]
            if node_id not in session.patterns_rejected:
                session.patterns_rejected.append(node_id)
            session.touch()
        
        self._stats["patterns_rejected"] += 1
        
        return True
    
    # === Edge Operations ===
    
    def add_edge(self, edge: Edge) -> Edge:
        """Add an edge to STM."""
        return self._graph.add_edge(edge)
    
    def get_edge(self, edge_id: str) -> Optional[Edge]:
        """Get an edge by ID."""
        return self._graph.get_edge(edge_id)
    
    # === Expiration and Cleanup ===
    
    def get_expired_patterns(self) -> List[Node]:
        """Get patterns that have exceeded TTL."""
        now = datetime.now()
        expired_ids = [
            nid for nid, ts in self._pattern_timestamps.items()
            if now - ts > self.ttl
        ]
        return [
            self._graph.get_node(nid) 
            for nid in expired_ids 
            if self._graph.has_node(nid)
        ]
    
    def expire_patterns(self) -> List[str]:
        """
        Remove expired patterns.
        
        Returns:
            List of expired pattern IDs
        """
        expired = self.get_expired_patterns()
        expired_ids = []
        
        for node in expired:
            if self.remove_pattern(node.node_id):
                expired_ids.append(node.node_id)
                self._stats["patterns_expired"] += 1
        
        return expired_ids
    
    def _enforce_capacity(self) -> None:
        """Enforce maximum capacity by removing oldest patterns."""
        while len(self._graph) > self.max_patterns:
            # Find oldest pattern
            oldest_id = min(
                self._pattern_timestamps.keys(),
                key=lambda x: self._pattern_timestamps[x]
            )
            self.remove_pattern(oldest_id)
            self._stats["patterns_expired"] += 1
    
    def clear(self) -> None:
        """Clear all patterns from STM."""
        self._graph = PatternGraph(domain="stm")
        self._pattern_timestamps.clear()
        self._pattern_sessions.clear()
        self._pending_validation.clear()
    
    # === Statistics ===
    
    def get_stats(self) -> Dict[str, Any]:
        """Get STM statistics."""
        return {
            **self._stats,
            "total_patterns": len(self._graph),
            "pending_validation": len(self._pending_validation),
            "total_sessions": len(self._sessions),
            "ttl_hours": self.ttl.total_seconds() / 3600,
            "max_patterns": self.max_patterns,
            "graph_stats": self._graph.get_stats(),
        }
    
    # === Serialization ===
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize STM to dictionary."""
        return {
            "ttl_hours": self.ttl.total_seconds() / 3600,
            "max_patterns": self.max_patterns,
            "graph": self._graph.to_dict(),
            "sessions": {
                sid: {
                    "session_id": s.session_id,
                    "created_at": s.created_at.isoformat(),
                    "last_activity": s.last_activity.isoformat(),
                    "patterns_learned": s.patterns_learned,
                    "patterns_validated": s.patterns_validated,
                    "patterns_rejected": s.patterns_rejected,
                    "metadata": s.metadata,
                }
                for sid, s in self._sessions.items()
            },
            "pattern_timestamps": {
                nid: ts.isoformat() 
                for nid, ts in self._pattern_timestamps.items()
            },
            "pattern_sessions": self._pattern_sessions,
            "pending_validation": list(self._pending_validation),
            "stats": self._stats,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ShortTermMemory":
        """Deserialize STM from dictionary."""
        stm = cls(
            ttl_hours=data.get("ttl_hours", 24),
            max_patterns=data.get("max_patterns", 1000),
        )
        
        stm._graph = PatternGraph.from_dict(data["graph"])
        
        for sid, sdata in data.get("sessions", {}).items():
            stm._sessions[sid] = STMSession(
                session_id=sdata["session_id"],
                created_at=datetime.fromisoformat(sdata["created_at"]),
                last_activity=datetime.fromisoformat(sdata["last_activity"]),
                patterns_learned=sdata.get("patterns_learned", []),
                patterns_validated=sdata.get("patterns_validated", []),
                patterns_rejected=sdata.get("patterns_rejected", []),
                metadata=sdata.get("metadata", {}),
            )
        
        for nid, ts in data.get("pattern_timestamps", {}).items():
            stm._pattern_timestamps[nid] = datetime.fromisoformat(ts)
        
        stm._pattern_sessions = data.get("pattern_sessions", {})
        stm._pending_validation = set(data.get("pending_validation", []))
        stm._stats = data.get("stats", stm._stats)
        
        return stm
    
    def __len__(self) -> int:
        """Return the number of patterns in STM."""
        return len(self._graph)
    
    def __contains__(self, node_id: str) -> bool:
        """Check if a pattern exists in STM."""
        return self._graph.has_node(node_id)
    
    def __repr__(self) -> str:
        return f"ShortTermMemory(patterns={len(self._graph)}, pending={len(self._pending_validation)})"
