"""
Question Generation for RPA system.

Generates context-aware questions based on detected knowledge gaps.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid

from rpa.core.graph import Node, PatternGraph
from .gap_detector import Gap, GapType


class QuestionType(Enum):
    """Types of inquiry questions."""
    COMPOSITION = "composition"           # About pattern composition
    USAGE = "usage"                       # About pattern usage
    HIERARCHY = "hierarchy"               # About hierarchy levels
    CROSS_DOMAIN = "cross_domain"         # About cross-domain links
    VALIDATION = "validation"             # About pattern validation
    CLARIFICATION = "clarification"       # General clarification


class QuestionPriority(Enum):
    """Priority levels for questions."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Inquiry:
    """Represents an inquiry/question."""
    inquiry_id: str
    question: str
    question_type: QuestionType
    gap_type: GapType
    priority: QuestionPriority
    affected_nodes: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    answered: bool = False
    answer: Optional[str] = None
    answered_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "inquiry_id": self.inquiry_id,
            "question": self.question,
            "question_type": self.question_type.value,
            "gap_type": self.gap_type.value,
            "priority": self.priority.value,
            "affected_nodes": self.affected_nodes,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "answered": self.answered,
            "answer": self.answer,
            "answered_at": self.answered_at.isoformat() if self.answered_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Inquiry":
        """Create from dictionary."""
        return cls(
            inquiry_id=data["inquiry_id"],
            question=data["question"],
            question_type=QuestionType(data["question_type"]),
            gap_type=GapType(data["gap_type"]),
            priority=QuestionPriority(data["priority"]),
            affected_nodes=data.get("affected_nodes", []),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            answered=data.get("answered", False),
            answer=data.get("answer"),
            answered_at=datetime.fromisoformat(data["answered_at"]) if data.get("answered_at") else None,
        )


class QuestionGenerator:
    """
    Generates context-aware questions based on knowledge gaps.
    
    The QuestionGenerator creates questions that help the system learn
    by asking for clarification, validation, or additional information.
    """
    
    def __init__(self):
        """Initialize the QuestionGenerator."""
        self._inquiries: Dict[str, Inquiry] = {}
        self._pending_inquiries: List[str] = []
    
    def generate_questions(
        self,
        gaps: List[Gap],
        graph: PatternGraph,
        limit: int = 10,
    ) -> List[Inquiry]:
        """
        Generate questions for a list of gaps.
        
        Args:
            gaps: List of detected gaps
            graph: The pattern graph for context
            limit: Maximum number of questions to generate
            
        Returns:
            List of generated inquiries
        """
        inquiries = []
        
        # Sort gaps by severity
        severity_order = {"high": 0, "medium": 1, "low": 2}
        sorted_gaps = sorted(gaps, key=lambda g: severity_order.get(g.severity, 3))
        
        for gap in sorted_gaps:
            if len(inquiries) >= limit:
                break
            
            inquiry = self._generate_question_for_gap(gap, graph)
            if inquiry:
                inquiries.append(inquiry)
                self._inquiries[inquiry.inquiry_id] = inquiry
                self._pending_inquiries.append(inquiry.inquiry_id)
        
        return inquiries
    
    def _generate_question_for_gap(
        self,
        gap: Gap,
        graph: PatternGraph,
    ) -> Optional[Inquiry]:
        """Generate a question for a specific gap type."""
        
        generators = {
            GapType.UNCERTAIN_PATTERN: self._generate_uncertain_question,
            GapType.INCOMPLETE_COMPOSITION: self._generate_composition_question,
            GapType.ORPHANED_PATTERN: self._generate_usage_question,
            GapType.UNRESOLVED_REFERENCE: self._generate_resolution_question,
            GapType.HIERARCHY_GAP: self._generate_hierarchy_question,
            GapType.CROSS_DOMAIN: self._generate_cross_domain_question,
            GapType.MISSING_PRIMITIVE: self._generate_primitive_question,
        }
        
        generator = generators.get(gap.gap_type)
        if generator:
            return generator(gap, graph)
        return None
    
    def _generate_uncertain_question(
        self,
        gap: Gap,
        graph: PatternGraph,
    ) -> Inquiry:
        """Generate question for uncertain pattern."""
        node_id = gap.affected_nodes[0] if gap.affected_nodes else "unknown"
        node = graph.get_node(node_id)
        label = node.label if node else node_id
        reason = gap.metadata.get("reason", "unknown reasons")
        
        question = (
            f"I'm uncertain about the pattern '{label}'. "
            f"The reason given was: '{reason}'. "
            f"Can you help me understand if this pattern is correct, "
            f"or what I should change about it?"
        )
        
        return self._create_inquiry(
            question=question,
            question_type=QuestionType.VALIDATION,
            gap_type=gap.gap_type,
            priority=QuestionPriority.MEDIUM,
            affected_nodes=gap.affected_nodes,
            metadata={"gap_id": gap.gap_id, "confidence": gap.metadata.get("confidence", 0.5)},
        )
    
    def _generate_composition_question(
        self,
        gap: Gap,
        graph: PatternGraph,
    ) -> Inquiry:
        """Generate question for incomplete composition."""
        node_id = gap.affected_nodes[0] if gap.affected_nodes else "unknown"
        node = graph.get_node(node_id)
        label = node.label if node else node_id
        missing = gap.metadata.get("missing_children", [])
        
        missing_str = ", ".join(missing[:3])
        if len(missing) > 3:
            missing_str += f", and {len(missing) - 3} more"
        
        question = (
            f"I learned the pattern '{label}', but I'm missing some of its components: "
            f"[{missing_str}]. "
            f"Can you teach me these missing pieces so I can fully understand '{label}'?"
        )
        
        return self._create_inquiry(
            question=question,
            question_type=QuestionType.COMPOSITION,
            gap_type=gap.gap_type,
            priority=QuestionPriority.HIGH,
            affected_nodes=gap.affected_nodes,
            metadata={"gap_id": gap.gap_id, "missing_children": missing},
        )
    
    def _generate_usage_question(
        self,
        gap: Gap,
        graph: PatternGraph,
    ) -> Inquiry:
        """Generate question for orphaned pattern."""
        node_id = gap.affected_nodes[0] if gap.affected_nodes else "unknown"
        node = graph.get_node(node_id)
        label = node.label if node else node_id
        
        question = (
            f"I know the pattern '{label}', but I haven't learned how it's used "
            f"in larger contexts. Can you show me some examples of how '{label}' "
            f"is used in sentences or higher-level patterns?"
        )
        
        return self._create_inquiry(
            question=question,
            question_type=QuestionType.USAGE,
            gap_type=gap.gap_type,
            priority=QuestionPriority.LOW,
            affected_nodes=gap.affected_nodes,
            metadata={"gap_id": gap.gap_id, "hierarchy_level": gap.metadata.get("hierarchy_level", 1)},
        )
    
    def _generate_resolution_question(
        self,
        gap: Gap,
        graph: PatternGraph,
    ) -> Inquiry:
        """Generate question for unresolved reference."""
        missing_node = gap.metadata.get("edge_id", "").split(":")[-1] if gap.metadata.get("edge_id") else "unknown"
        source_id = gap.affected_nodes[0] if gap.affected_nodes else "unknown"
        source = graph.get_node(source_id)
        label = source.label if source else source_id
        
        question = (
            f"I have a reference to '{missing_node}' from the pattern '{label}', "
            f"but '{missing_node}' doesn't exist in my knowledge. "
            f"Should I create this missing pattern, or is this reference incorrect?"
        )
        
        return self._create_inquiry(
            question=question,
            question_type=QuestionType.VALIDATION,
            gap_type=gap.gap_type,
            priority=QuestionPriority.HIGH,
            affected_nodes=gap.affected_nodes,
            metadata={"gap_id": gap.gap_id},
        )
    
    def _generate_hierarchy_question(
        self,
        gap: Gap,
        graph: PatternGraph,
    ) -> Inquiry:
        """Generate question for hierarchy gap."""
        domain = gap.metadata.get("domain", "this domain")
        missing_levels = gap.metadata.get("missing_levels", [])
        existing_levels = gap.metadata.get("existing_levels", [])
        
        missing_str = ", ".join(map(str, missing_levels))
        
        if gap.metadata.get("has_primitives") and not gap.metadata.get("has_patterns"):
            question = (
                f"I've learned primitives in '{domain}', but I haven't learned "
                f"any higher-level patterns yet. What patterns should I learn next "
                f"to build up from these primitives?"
            )
        else:
            question = (
                f"I notice there are gaps in the hierarchy for '{domain}': "
                f"I have patterns at levels {existing_levels}, but I'm missing "
                f"level(s) {missing_str}. What patterns should I learn to fill these gaps?"
            )
        
        return self._create_inquiry(
            question=question,
            question_type=QuestionType.HIERARCHY,
            gap_type=gap.gap_type,
            priority=QuestionPriority.MEDIUM,
            affected_nodes=gap.affected_nodes,
            metadata={"gap_id": gap.gap_id, "missing_levels": missing_levels, "domain": domain},
        )
    
    def _generate_cross_domain_question(
        self,
        gap: Gap,
        graph: PatternGraph,
    ) -> Inquiry:
        """Generate question for cross-domain link opportunity."""
        domains = gap.metadata.get("domains", [])
        content = gap.metadata.get("content", "this pattern")
        
        domain_str = " and ".join(domains)
        
        question = (
            f"I notice the pattern '{content}' appears in both '{domains[0]}' and '{domains[1]}' "
            f"domains. Is there a conceptual connection I should learn between "
            f"these two versions? How are they related?"
        )
        
        return self._create_inquiry(
            question=question,
            question_type=QuestionType.CROSS_DOMAIN,
            gap_type=gap.gap_type,
            priority=QuestionPriority.LOW,
            affected_nodes=gap.affected_nodes,
            metadata={"gap_id": gap.gap_id, "domains": domains, "content": content},
        )
    
    def _generate_primitive_question(
        self,
        gap: Gap,
        graph: PatternGraph,
    ) -> Inquiry:
        """Generate question for missing primitive."""
        char = gap.metadata.get("character", "?")
        domain = gap.metadata.get("domain", "general")
        
        question = (
            f"I haven't learned the primitive character '{char}' yet "
            f"(domain: {domain}). Should I add this character to my knowledge?"
        )
        
        return self._create_inquiry(
            question=question,
            question_type=QuestionType.COMPOSITION,
            gap_type=gap.gap_type,
            priority=QuestionPriority.MEDIUM,
            affected_nodes=gap.affected_nodes,
            metadata={"gap_id": gap.gap_id, "character": char, "domain": domain},
        )
    
    def generate_batch_questions(
        self,
        gaps: List[Gap],
        graph: PatternGraph,
        batch_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Generate a batch of questions for processing.
        
        Args:
            gaps: List of detected gaps
            graph: The pattern graph
            batch_id: Identifier for this batch
            
        Returns:
            List of question dictionaries
        """
        inquiries = self.generate_questions(gaps, graph)
        
        return [
            {
                "inquiry_id": inquiry.inquiry_id,
                "question": inquiry.question,
                "type": inquiry.question_type.value,
                "gap_type": inquiry.gap_type.value,
                "priority": inquiry.priority.value,
                "batch_id": batch_id,
            }
            for inquiry in inquiries
        ]
    
    def get_pending_inquiries(self) -> List[Inquiry]:
        """Get all pending (unanswered) inquiries."""
        return [
            self._inquiries[iid] 
            for iid in self._pending_inquiries 
            if iid in self._inquiries and not self._inquiries[iid].answered
        ]
    
    def get_inquiry(self, inquiry_id: str) -> Optional[Inquiry]:
        """Get an inquiry by ID."""
        return self._inquiries.get(inquiry_id)
    
    def answer_inquiry(
        self,
        inquiry_id: str,
        answer: str,
    ) -> Optional[Inquiry]:
        """
        Record an answer to an inquiry.
        
        Args:
            inquiry_id: ID of the inquiry
            answer: The answer provided
            
        Returns:
            The updated inquiry, or None if not found
        """
        inquiry = self._inquiries.get(inquiry_id)
        if not inquiry:
            return None
        
        inquiry.answered = True
        inquiry.answer = answer
        inquiry.answered_at = datetime.now()
        
        # Remove from pending
        if inquiry_id in self._pending_inquiries:
            self._pending_inquiries.remove(inquiry_id)
        
        return inquiry
    
    def _create_inquiry(
        self,
        question: str,
        question_type: QuestionType,
        gap_type: GapType,
        priority: QuestionPriority,
        affected_nodes: List[str],
        metadata: Dict[str, Any],
    ) -> Inquiry:
        """Create and register a new inquiry."""
        inquiry_id = f"inquiry_{uuid.uuid4().hex[:8]}"
        
        return Inquiry(
            inquiry_id=inquiry_id,
            question=question,
            question_type=question_type,
            gap_type=gap_type,
            priority=priority,
            affected_nodes=affected_nodes,
            metadata=metadata,
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get inquiry statistics."""
        total = len(self._inquiries)
        answered = sum(1 for i in self._inquiries.values() if i.answered)
        
        by_type: Dict[str, int] = {}
        for inquiry in self._inquiries.values():
            type_name = inquiry.question_type.value
            by_type[type_name] = by_type.get(type_name, 0) + 1
        
        return {
            "total_inquiries": total,
            "answered": answered,
            "pending": total - answered,
            "by_type": by_type,
        }
    
    def clear(self) -> None:
        """Clear all inquiries."""
        self._inquiries.clear()
        self._pending_inquiries.clear()
