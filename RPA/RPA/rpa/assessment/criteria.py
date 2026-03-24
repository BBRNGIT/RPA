"""
Assessment criteria for RPA patterns.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AssessmentCriteria:
    """
    Defines criteria for assessing pattern mastery.
    
    Attributes:
        pattern_id: ID of the pattern being assessed
        criteria: List of assessment criteria with types and weights
        required_pass_rate: Minimum pass rate for successful assessment
        structural_validation_required: Whether to require structural validation
        recursive_depth_check: Whether to check recursive depth integrity
    """
    pattern_id: str
    criteria: List[Dict[str, Any]] = field(default_factory=list)
    required_pass_rate: float = 0.8
    structural_validation_required: bool = True
    recursive_depth_check: bool = True
    
    def __post_init__(self):
        """Initialize default criteria if none provided."""
        if not self.criteria:
            self.criteria = [
                {"type": "reconstruct", "weight": 0.25},
                {"type": "recognize", "weight": 0.20},
                {"type": "compose", "weight": 0.20},
                {"type": "decompose", "weight": 0.15},
                {"type": "recursive_recall", "weight": 0.20},
            ]
        
        # Validate weights sum to 1.0
        total_weight = sum(c.get("weight", 0) for c in self.criteria)
        if abs(total_weight - 1.0) > 0.01:
            # Normalize weights
            for c in self.criteria:
                c["weight"] = c.get("weight", 0) / total_weight
    
    def get_criteria_types(self) -> List[str]:
        """Get list of criteria types."""
        return [c["type"] for c in self.criteria]
    
    def get_weight(self, criteria_type: str) -> float:
        """Get weight for a specific criteria type."""
        for c in self.criteria:
            if c["type"] == criteria_type:
                return c.get("weight", 0)
        return 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "pattern_id": self.pattern_id,
            "criteria": self.criteria,
            "required_pass_rate": self.required_pass_rate,
            "structural_validation_required": self.structural_validation_required,
            "recursive_depth_check": self.recursive_depth_check,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AssessmentCriteria":
        """Create from dictionary."""
        return cls(
            pattern_id=data["pattern_id"],
            criteria=data.get("criteria", []),
            required_pass_rate=data.get("required_pass_rate", 0.8),
            structural_validation_required=data.get("structural_validation_required", True),
            recursive_depth_check=data.get("recursive_depth_check", True),
        )
    
    @classmethod
    def create_basic(cls, pattern_id: str) -> "AssessmentCriteria":
        """Create basic assessment criteria."""
        return cls(
            pattern_id=pattern_id,
            criteria=[
                {"type": "reconstruct", "weight": 0.4},
                {"type": "recognize", "weight": 0.3},
                {"type": "recursive_recall", "weight": 0.3},
            ],
            required_pass_rate=0.7,
        )
    
    @classmethod
    def create_comprehensive(cls, pattern_id: str) -> "AssessmentCriteria":
        """Create comprehensive assessment criteria with all exercise types."""
        return cls(
            pattern_id=pattern_id,
            criteria=[
                {"type": "reconstruct", "weight": 0.15},
                {"type": "recognize", "weight": 0.10},
                {"type": "compose", "weight": 0.15},
                {"type": "decompose", "weight": 0.10},
                {"type": "recursive_recall", "weight": 0.15},
                {"type": "contextual_usage", "weight": 0.10},
                {"type": "error_detection", "weight": 0.10},
                {"type": "analogy", "weight": 0.05},
                {"type": "transformation", "weight": 0.10},
            ],
            required_pass_rate=0.8,
        )
    
    @classmethod
    def create_for_code(cls, pattern_id: str) -> "AssessmentCriteria":
        """Create assessment criteria for code patterns."""
        return cls(
            pattern_id=pattern_id,
            criteria=[
                {"type": "reconstruct", "weight": 0.20},
                {"type": "recognize", "weight": 0.15},
                {"type": "compose", "weight": 0.20},
                {"type": "decompose", "weight": 0.15},
                {"type": "recursive_recall", "weight": 0.10},
                {"type": "error_detection", "weight": 0.15},
                {"type": "transformation", "weight": 0.05},
            ],
            required_pass_rate=0.75,
        )


# Default criteria for different pattern types
DEFAULT_CRITERIA = {
    "primitive": AssessmentCriteria(
        pattern_id="default_primitive",
        criteria=[
            {"type": "recognize", "weight": 0.5},
            {"type": "reconstruct", "weight": 0.5},
        ],
        required_pass_rate=0.9,
        structural_validation_required=False,
        recursive_depth_check=False,
    ),
    "word": AssessmentCriteria.create_basic("default_word"),
    "sentence": AssessmentCriteria(
        pattern_id="default_sentence",
        criteria=[
            {"type": "reconstruct", "weight": 0.25},
            {"type": "recognize", "weight": 0.20},
            {"type": "compose", "weight": 0.25},
            {"type": "decompose", "weight": 0.15},
            {"type": "contextual_usage", "weight": 0.15},
        ],
        required_pass_rate=0.75,
    ),
    "code": AssessmentCriteria.create_for_code("default_code"),
}
