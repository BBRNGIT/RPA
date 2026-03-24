"""
Node implementation for RPA pattern graph.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class NodeType(Enum):
    """Types of nodes in the pattern graph."""
    PRIMITIVE = "primitive"      # Basic characters/tokens
    PATTERN = "pattern"          # Composed patterns (words, phrases)
    SEQUENCE = "sequence"        # Ordered sequences (sentences, code blocks)
    CONCEPT = "concept"          # Abstract concepts
    ERROR = "error"              # Error patterns for learning
    UNKNOWN = "unknown"          # Unresolved patterns


@dataclass
class Node:
    """
    Represents a node in the pattern graph.
    
    Attributes:
        node_id: Unique identifier (e.g., "primitive:a", "word:apple")
        label: Human-readable label
        node_type: Type of the node
        content: The actual content (character, word, sequence)
        hierarchy_level: 0=primitive, 1=word, 2=sentence, etc.
        domain: Domain identifier (e.g., "english", "python")
        created_at: Creation timestamp
        updated_at: Last update timestamp
        is_valid: Whether the node passed validation
        is_uncertain: Flagged for review
        metadata: Additional properties
        source: Origin of the pattern (dataset, curriculum, user)
        access_count: Number of times accessed
        confidence: Confidence score (0.0-1.0)
    """
    node_id: str
    label: str
    node_type: NodeType
    content: str
    hierarchy_level: int = 0
    domain: str = "general"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    is_valid: bool = True
    is_uncertain: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    source: Optional[str] = None
    access_count: int = 0
    confidence: float = 1.0
    
    def __post_init__(self):
        """Validate node after initialization."""
        if not self.node_id:
            raise ValueError("node_id cannot be empty")
        if not self.label:
            self.label = self.content
        if self.confidence < 0.0 or self.confidence > 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
    
    def touch(self) -> None:
        """Update the accessed timestamp and increment access count."""
        self.updated_at = datetime.now()
        self.access_count += 1
    
    def mark_uncertain(self, reason: Optional[str] = None) -> None:
        """Mark the node as uncertain for review."""
        self.is_uncertain = True
        self.updated_at = datetime.now()
        if reason:
            self.metadata["uncertainty_reason"] = reason
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary representation."""
        return {
            "node_id": self.node_id,
            "label": self.label,
            "node_type": self.node_type.value,
            "content": self.content,
            "hierarchy_level": self.hierarchy_level,
            "domain": self.domain,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "is_valid": self.is_valid,
            "is_uncertain": self.is_uncertain,
            "metadata": self.metadata,
            "source": self.source,
            "access_count": self.access_count,
            "confidence": self.confidence,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Node":
        """Create a Node from dictionary representation."""
        data["node_type"] = NodeType(data["node_type"])
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        return cls(**data)
    
    @classmethod
    def create_primitive(cls, char: str, domain: str = "general") -> "Node":
        """Create a primitive node for a character."""
        if len(char) != 1:
            raise ValueError("Primitive must be a single character")
        return cls(
            node_id=f"primitive:{char}",
            label=char,
            node_type=NodeType.PRIMITIVE,
            content=char,
            hierarchy_level=0,
            domain=domain,
        )
    
    @classmethod
    def create_pattern(
        cls,
        label: str,
        content: str,
        hierarchy_level: int = 1,
        domain: str = "general",
        source: Optional[str] = None,
    ) -> "Node":
        """Create a pattern node (word, phrase, etc.)."""
        return cls(
            node_id=f"pattern:{label}",
            label=label,
            node_type=NodeType.PATTERN,
            content=content,
            hierarchy_level=hierarchy_level,
            domain=domain,
            source=source,
        )
    
    @classmethod
    def create_sequence(
        cls,
        label: str,
        content: str,
        hierarchy_level: int = 2,
        domain: str = "general",
        source: Optional[str] = None,
    ) -> "Node":
        """Create a sequence node (sentence, code block, etc.)."""
        return cls(
            node_id=f"sequence:{label}",
            label=label,
            node_type=NodeType.SEQUENCE,
            content=content,
            hierarchy_level=hierarchy_level,
            domain=domain,
            source=source,
        )
