"""
BaseAgent - Base class for specialized RPA agents.

Provides the foundation for domain-specific agents with:
- Memory management (LTM and Episodic)
- Query and teach operations
- Inquiry handling
- Status reporting
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid
import logging

from rpa.memory.ltm import LongTermMemory
from rpa.memory.episodic import EpisodicMemory, EventType
from rpa.core.graph import Node, NodeType

logger = logging.getLogger(__name__)


@dataclass
class AgentStatus:
    """Status information for an agent."""
    agent_id: str
    domain: str
    patterns_learned: int = 0
    patterns_validated: int = 0
    inquiries_asked: int = 0
    inquiries_answered: int = 0
    sessions_completed: int = 0
    last_activity: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "agent_id": self.agent_id,
            "domain": self.domain,
            "patterns_learned": self.patterns_learned,
            "patterns_validated": self.patterns_validated,
            "inquiries_asked": self.inquiries_asked,
            "inquiries_answered": self.inquiries_answered,
            "sessions_completed": self.sessions_completed,
            "last_activity": self.last_activity.isoformat(),
        }


@dataclass
class Inquiry:
    """Represents an inquiry from an agent."""
    inquiry_id: str
    agent_id: str
    question: str
    inquiry_type: str
    priority: str = "medium"  # high, medium, low
    pattern_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    answered: bool = False
    answer: Optional[str] = None
    answered_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "inquiry_id": self.inquiry_id,
            "agent_id": self.agent_id,
            "question": self.question,
            "inquiry_type": self.inquiry_type,
            "priority": self.priority,
            "pattern_id": self.pattern_id,
            "created_at": self.created_at.isoformat(),
            "answered": self.answered,
            "answer": self.answer,
            "answered_at": self.answered_at.isoformat() if self.answered_at else None,
        }


class BaseAgent:
    """
    Base class for specialized RPA agents.

    Provides core functionality for:
    - Memory management (LTM and Episodic)
    - Pattern querying and teaching
    - Inquiry handling
    - Status reporting

    Subclasses extend with domain-specific capabilities.
    """

    def __init__(
        self,
        domain: str,
        agent_id: Optional[str] = None,
        ltm: Optional[LongTermMemory] = None,
        episodic: Optional[EpisodicMemory] = None,
    ):
        """
        Initialize a BaseAgent.

        Args:
            domain: The domain this agent operates in (e.g., "english", "python")
            agent_id: Optional agent ID (auto-generated if not provided)
            ltm: Optional LongTermMemory instance (new one created if not provided)
            episodic: Optional EpisodicMemory instance (new one created if not provided)
        """
        self.domain = domain
        self.agent_id = agent_id or f"agent_{domain}_{uuid.uuid4().hex[:8]}"
        self.ltm = ltm or LongTermMemory()
        self.episodic = episodic or EpisodicMemory()

        # Agent state
        self._status = AgentStatus(
            agent_id=self.agent_id,
            domain=self.domain,
        )
        self._inquiries: Dict[str, Inquiry] = {}
        self._pending_inquiries: List[str] = []

        # Log agent creation
        self.episodic.log_event(
            event_type=EventType.SESSION_STARTED,
            session_id=self.agent_id,
            data={"action": "agent_created", "domain": domain},
        )

    # === Core Operations ===

    def query(self, question: str) -> str:
        """
        Query the agent's knowledge.

        Args:
            question: The question to answer

        Returns:
            Answer string based on agent's knowledge
        """
        self._update_activity()

        # Search LTM for relevant patterns
        patterns = self.ltm.search(question, limit=5)

        if patterns:
            # Build answer from found patterns
            answer_parts = []
            for p in patterns:
                answer_parts.append(f"{p.label}: {p.content}")
            answer = "Found relevant patterns:\n" + "\n".join(answer_parts)
        else:
            answer = f"No relevant patterns found in {self.domain} domain for: {question}"

        self.episodic.log_event(
            event_type=EventType.SESSION_STARTED,
            session_id=self.agent_id,
            data={"action": "query", "question": question, "found": len(patterns)},
        )

        return answer

    def teach(self, lesson: Dict[str, Any]) -> Dict[str, Any]:
        """
        Teach the agent a new pattern.

        Args:
            lesson: Lesson data containing:
                - content: The pattern content
                - label: Optional label
                - hierarchy_level: Optional hierarchy level
                - metadata: Optional additional metadata

        Returns:
            Result dictionary with success status and pattern ID
        """
        self._update_activity()
        self._status.patterns_learned += 1

        content = lesson.get("content", "")
        label = lesson.get("label", content[:20] if content else "unnamed")
        hierarchy_level = lesson.get("hierarchy_level", 0)
        metadata = lesson.get("metadata", {})

        # Create pattern node
        node = Node(
            node_id=f"pattern_{uuid.uuid4().hex[:8]}",
            label=label,
            content=content,
            domain=self.domain,
            node_type=NodeType.PATTERN,
            hierarchy_level=hierarchy_level,
            metadata=metadata,
        )

        # Consolidate to LTM
        self.ltm.consolidate(
            node=node,
            session_id=self.agent_id,
            validation_score=0.8,  # Default score for taught patterns
            source="agent_teaching",
        )

        # Log event
        self.episodic.log_event(
            event_type=EventType.PATTERN_LEARNED,
            session_id=self.agent_id,
            pattern_id=node.node_id,
            data={"content": content, "label": label},
        )

        return {
            "success": True,
            "pattern_id": node.node_id,
            "message": f"Pattern '{label}' learned successfully",
        }

    def assess(self, pattern_id: str) -> Dict[str, Any]:
        """
        Assess a pattern's validity and quality.

        Args:
            pattern_id: ID of the pattern to assess

        Returns:
            Assessment result dictionary
        """
        self._update_activity()

        pattern = self.ltm.get_pattern(pattern_id)
        if not pattern:
            return {
                "success": False,
                "pattern_id": pattern_id,
                "message": "Pattern not found",
            }

        # Basic validation checks
        issues = []

        # Check if pattern has content
        if not pattern.content:
            issues.append("Pattern has no content")

        # Check children via graph edges
        children = self.ltm._graph.get_children(pattern_id)
        missing_children = []
        for child in children:
            if not self.ltm.has_pattern(child.node_id):
                missing_children.append(child.node_id)
        if missing_children:
            issues.append(f"Missing children: {missing_children}")

        # Calculate validity score
        is_valid = len(issues) == 0
        score = 1.0 if is_valid else max(0.0, 1.0 - 0.2 * len(issues))

        self._status.patterns_validated += 1

        self.episodic.log_event(
            event_type=EventType.ASSESSMENT_COMPLETED,
            session_id=self.agent_id,
            pattern_id=pattern_id,
            data={"is_valid": is_valid, "score": score, "issues": issues},
        )

        return {
            "success": True,
            "pattern_id": pattern_id,
            "is_valid": is_valid,
            "score": score,
            "issues": issues,
            "message": "Pattern is valid" if is_valid else f"Issues found: {issues}",
        }

    # === Inquiry Operations ===

    def ask_inquiry(
        self,
        question: str,
        inquiry_type: str = "general",
        priority: str = "medium",
        pattern_id: Optional[str] = None,
    ) -> Inquiry:
        """
        Create an inquiry to ask for help.

        Args:
            question: The question to ask
            inquiry_type: Type of inquiry (composition, usage, hierarchy, etc.)
            priority: Priority level (high, medium, low)
            pattern_id: Optional related pattern ID

        Returns:
            The created inquiry
        """
        self._update_activity()
        self._status.inquiries_asked += 1

        inquiry = Inquiry(
            inquiry_id=f"inq_{uuid.uuid4().hex[:8]}",
            agent_id=self.agent_id,
            question=question,
            inquiry_type=inquiry_type,
            priority=priority,
            pattern_id=pattern_id,
        )

        self._inquiries[inquiry.inquiry_id] = inquiry
        self._pending_inquiries.append(inquiry.inquiry_id)

        self.episodic.log_event(
            event_type=EventType.INQUIRY_CREATED,
            session_id=self.agent_id,
            pattern_id=pattern_id,
            data={
                "inquiry_id": inquiry.inquiry_id,
                "question": question,
                "type": inquiry_type,
            },
        )

        return inquiry

    def answer_inquiry(
        self,
        inquiry_id: str,
        response: str,
    ) -> Dict[str, Any]:
        """
        Answer a pending inquiry.

        Args:
            inquiry_id: ID of the inquiry to answer
            response: The answer/response

        Returns:
            Result dictionary
        """
        self._update_activity()

        if inquiry_id not in self._inquiries:
            return {
                "success": False,
                "message": "Inquiry not found",
            }

        inquiry = self._inquiries[inquiry_id]
        inquiry.answered = True
        inquiry.answer = response
        inquiry.answered_at = datetime.now()

        # Remove from pending
        if inquiry_id in self._pending_inquiries:
            self._pending_inquiries.remove(inquiry_id)

        self._status.inquiries_answered += 1

        self.episodic.log_event(
            event_type=EventType.INQUIRY_ANSWERED,
            session_id=self.agent_id,
            pattern_id=inquiry.pattern_id,
            data={
                "inquiry_id": inquiry_id,
                "answer": response,
            },
        )

        return {
            "success": True,
            "inquiry_id": inquiry_id,
            "message": "Inquiry answered successfully",
        }

    def get_pending_inquiries(self) -> List[Inquiry]:
        """Get all pending (unanswered) inquiries."""
        return [
            self._inquiries[iid]
            for iid in self._pending_inquiries
            if iid in self._inquiries
        ]

    # === Status Operations ===

    def get_status(self) -> Dict[str, Any]:
        """
        Get agent status.

        Returns:
            Status dictionary with agent information
        """
        return {
            **self._status.to_dict(),
            "ltm_stats": self.ltm.get_stats(),
            "episodic_stats": {
                "total_events": self.episodic.get_event_count(),
                "events_by_type": self.episodic.get_event_count_by_type(),
            },
            "pending_inquiries": len(self._pending_inquiries),
        }

    def get_capabilities(self) -> Dict[str, Any]:
        """
        Get agent capabilities.

        Returns:
            Dictionary of agent capabilities
        """
        return {
            "agent_id": self.agent_id,
            "domain": self.domain,
            "capabilities": [
                "query",
                "teach",
                "assess",
                "ask_inquiry",
                "answer_inquiry",
                "get_status",
            ],
            "domain_specific": [],  # Override in subclasses
        }

    def _update_activity(self) -> None:
        """Update last activity timestamp."""
        self._status.last_activity = datetime.now()

    # === Serialization ===

    def to_dict(self) -> Dict[str, Any]:
        """Serialize agent to dictionary."""
        return {
            "agent_id": self.agent_id,
            "domain": self.domain,
            "status": self._status.to_dict(),
            "inquiries": {
                iid: inq.to_dict() for iid, inq in self._inquiries.items()
            },
            "pending_inquiries": self._pending_inquiries,
            "ltm": self.ltm.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaseAgent":
        """Deserialize agent from dictionary."""
        agent = cls(
            domain=data["domain"],
            agent_id=data["agent_id"],
            ltm=LongTermMemory.from_dict(data.get("ltm", {})),
        )

        # Restore status
        status_data = data.get("status", {})
        agent._status.patterns_learned = status_data.get("patterns_learned", 0)
        agent._status.patterns_validated = status_data.get("patterns_validated", 0)
        agent._status.inquiries_asked = status_data.get("inquiries_asked", 0)
        agent._status.inquiries_answered = status_data.get("inquiries_answered", 0)
        agent._status.sessions_completed = status_data.get("sessions_completed", 0)

        # Restore inquiries
        for iid, inq_data in data.get("inquiries", {}).items():
            agent._inquiries[iid] = Inquiry(
                inquiry_id=inq_data["inquiry_id"],
                agent_id=inq_data["agent_id"],
                question=inq_data["question"],
                inquiry_type=inq_data["inquiry_type"],
                priority=inq_data.get("priority", "medium"),
                pattern_id=inq_data.get("pattern_id"),
                answered=inq_data.get("answered", False),
                answer=inq_data.get("answer"),
            )
        agent._pending_inquiries = data.get("pending_inquiries", [])

        return agent

    def __repr__(self) -> str:
        return f"BaseAgent(id={self.agent_id}, domain={self.domain})"
