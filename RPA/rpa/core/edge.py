"""
Edge implementation for RPA pattern graph.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional


class EdgeType(Enum):
    """Types of edges in the pattern graph."""
    COMPOSED_OF = "composed_of"       # Pattern is composed of children
    PRECEDES = "precedes"             # Sequential ordering
    FOLLOWS = "follows"               # Inverse of precedes
    IS_INSTANCE_OF = "is_instance_of" # Specific to general relationship
    RELATES_TO = "relates_to"         # General association
    CLARIFIES = "clarifies"           # Cross-domain clarification
    EXPANDS = "expands"               # Pattern expansion
    DERIVED_FROM = "derived_from"     # Pattern derivation
    SIMILAR_TO = "similar_to"         # Similarity relationship
    CORRECTS = "corrects"             # Error correction relationship
    HAS_ERROR = "has_error"           # Pattern has associated error


@dataclass
class Edge:
    """
    Represents an edge in the pattern graph.
    
    Attributes:
        edge_id: Unique identifier
        source_id: Source node ID
        target_id: Target node ID
        edge_type: Type of relationship
        order: Order for ordered relationships (e.g., composition order)
        weight: Edge weight/confidence
        created_at: Creation timestamp
        metadata: Additional properties
    """
    edge_id: str
    source_id: str
    target_id: str
    edge_type: EdgeType
    order: int = 0
    weight: float = 1.0
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate edge after initialization."""
        if not self.edge_id:
            raise ValueError("edge_id cannot be empty")
        if not self.source_id or not self.target_id:
            raise ValueError("source_id and target_id cannot be empty")
        if self.weight < 0.0 or self.weight > 1.0:
            raise ValueError("weight must be between 0.0 and 1.0")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert edge to dictionary representation."""
        return {
            "edge_id": self.edge_id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "edge_type": self.edge_type.value,
            "order": self.order,
            "weight": self.weight,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Edge":
        """Create an Edge from dictionary representation."""
        data["edge_type"] = EdgeType(data["edge_type"])
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)
    
    @classmethod
    def create_composition(
        cls,
        parent_id: str,
        child_id: str,
        order: int = 0,
    ) -> "Edge":
        """Create a COMPOSED_OF edge for pattern composition."""
        return cls(
            edge_id=f"edge:{parent_id}:composed_of:{child_id}:{order}",
            source_id=parent_id,
            target_id=child_id,
            edge_type=EdgeType.COMPOSED_OF,
            order=order,
        )
    
    @classmethod
    def create_sequence(
        cls,
        from_id: str,
        to_id: str,
        order: int = 0,
    ) -> "Edge":
        """Create a PRECEDES edge for sequential ordering."""
        return cls(
            edge_id=f"edge:{from_id}:precedes:{to_id}:{order}",
            source_id=from_id,
            target_id=to_id,
            edge_type=EdgeType.PRECEDES,
            order=order,
        )
    
    @classmethod
    def create_instance(
        cls,
        specific_id: str,
        general_id: str,
    ) -> "Edge":
        """Create an IS_INSTANCE_OF edge."""
        return cls(
            edge_id=f"edge:{specific_id}:is_instance_of:{general_id}",
            source_id=specific_id,
            target_id=general_id,
            edge_type=EdgeType.IS_INSTANCE_OF,
        )
    
    @classmethod
    def create_correction(
        cls,
        wrong_id: str,
        correct_id: str,
    ) -> "Edge":
        """Create a CORRECTS edge for error correction."""
        return cls(
            edge_id=f"edge:{correct_id}:corrects:{wrong_id}",
            source_id=correct_id,
            target_id=wrong_id,
            edge_type=EdgeType.CORRECTS,
        )
