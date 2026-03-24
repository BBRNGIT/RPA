"""
AgentMessenger - Inter-agent communication system.

Provides:
- Query delegation between agents
- Teaching/knowledge transfer
- Inquiry broadcasting
- Task coordination
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import uuid
import logging

from rpa.agents.base_agent import BaseAgent, Inquiry
from rpa.agents.agent_registry import AgentRegistry
from rpa.agents.shared_knowledge import SharedKnowledge

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Represents a message between agents."""
    message_id: str
    from_agent_id: str
    to_agent_id: str
    message_type: str  # query, teaching, inquiry, response
    content: Any
    sent_at: datetime = field(default_factory=datetime.now)
    responded_at: Optional[datetime] = None
    response: Optional[Any] = None
    status: str = "sent"  # sent, delivered, responded

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "message_id": self.message_id,
            "from_agent_id": self.from_agent_id,
            "to_agent_id": self.to_agent_id,
            "message_type": self.message_type,
            "content": self.content,
            "sent_at": self.sent_at.isoformat(),
            "responded_at": self.responded_at.isoformat() if self.responded_at else None,
            "response": self.response,
            "status": self.status,
        }


class AgentMessenger:
    """
    Inter-agent communication system.

    Provides:
    - Query delegation between agents
    - Teaching/knowledge transfer
    - Inquiry broadcasting
    - Task coordination messaging
    """

    def __init__(
        self,
        registry: Optional[AgentRegistry] = None,
        shared_knowledge: Optional[SharedKnowledge] = None,
    ):
        """
        Initialize AgentMessenger.

        Args:
            registry: Optional AgentRegistry for agent lookup
            shared_knowledge: Optional SharedKnowledge for knowledge transfer
        """
        self.registry = registry or AgentRegistry()
        self.shared_knowledge = shared_knowledge or SharedKnowledge()
        self._messages: Dict[str, Message] = {}
        self._message_log: List[str] = []  # Ordered message IDs

    def send_query(
        self,
        from_agent_id: str,
        to_agent_id: str,
        query: str,
    ) -> Tuple[str, Optional[str]]:
        """
        Send a query from one agent to another.

        Args:
            from_agent_id: Sender agent ID
            to_agent_id: Recipient agent ID
            query: The query string

        Returns:
            Tuple of (message_id, response)
        """
        message = Message(
            message_id=f"msg_{uuid.uuid4().hex[:8]}",
            from_agent_id=from_agent_id,
            to_agent_id=to_agent_id,
            message_type="query",
            content=query,
        )

        self._messages[message.message_id] = message
        self._message_log.append(message.message_id)

        # Get recipient agent
        to_agent = self.registry.get_agent(to_agent_id)

        if not to_agent:
            message.status = "failed"
            message.response = "Recipient agent not found"
            return message.message_id, None

        # Deliver query
        try:
            response = to_agent.query(query)
            message.status = "responded"
            message.response = response
            message.responded_at = datetime.now()
        except Exception as e:
            message.status = "failed"
            message.response = f"Error: {str(e)}"
            logger.error(f"Query failed: {e}")

        return message.message_id, message.response

    def send_teaching(
        self,
        from_agent_id: str,
        to_agent_id: str,
        lesson: Dict[str, Any],
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        """
        Send teaching/knowledge from one agent to another.

        Args:
            from_agent_id: Sender agent ID
            to_agent_id: Recipient agent ID
            lesson: The lesson to teach

        Returns:
            Tuple of (message_id, result)
        """
        message = Message(
            message_id=f"msg_{uuid.uuid4().hex[:8]}",
            from_agent_id=from_agent_id,
            to_agent_id=to_agent_id,
            message_type="teaching",
            content=lesson,
        )

        self._messages[message.message_id] = message
        self._message_log.append(message.message_id)

        # Get recipient agent
        to_agent = self.registry.get_agent(to_agent_id)

        if not to_agent:
            message.status = "failed"
            message.response = {"success": False, "error": "Recipient agent not found"}
            return message.message_id, None

        # Deliver teaching
        try:
            result = to_agent.teach(lesson)
            message.status = "responded"
            message.response = result
            message.responded_at = datetime.now()
        except Exception as e:
            message.status = "failed"
            message.response = {"success": False, "error": str(e)}
            logger.error(f"Teaching failed: {e}")

        return message.message_id, message.response

    def broadcast_inquiry(
        self,
        inquiry: str,
        domains: Optional[List[str]] = None,
        from_agent_id: Optional[str] = None,
    ) -> List[Tuple[str, str, Optional[str]]]:
        """
        Broadcast an inquiry to multiple agents.

        Args:
            inquiry: The inquiry to broadcast
            domains: Optional list of domains to target
            from_agent_id: Optional sender agent ID

        Returns:
            List of (message_id, agent_id, response) tuples
        """
        results = []

        # Get agents to broadcast to
        if domains:
            agents = []
            for domain in domains:
                agents.extend(self.registry.list_agents(domain=domain))
        else:
            agents = self.registry.list_agents()

        for agent in agents:
            # Don't send to self
            if from_agent_id and agent.agent_id == from_agent_id:
                continue

            message = Message(
                message_id=f"msg_{uuid.uuid4().hex[:8]}",
                from_agent_id=from_agent_id or "system",
                to_agent_id=agent.agent_id,
                message_type="inquiry",
                content=inquiry,
            )

            self._messages[message.message_id] = message
            self._message_log.append(message.message_id)

            try:
                # Create inquiry in agent
                agent_inquiry = agent.ask_inquiry(inquiry)
                message.status = "delivered"
                results.append((message.message_id, agent.agent_id, agent_inquiry.inquiry_id))
            except Exception as e:
                message.status = "failed"
                results.append((message.message_id, agent.agent_id, None))
                logger.error(f"Broadcast to {agent.agent_id} failed: {e}")

        return results

    def coordinate_task(
        self,
        task: str,
        agent_ids: List[str],
        task_type: str = "general",
    ) -> Dict[str, Any]:
        """
        Coordinate a task across multiple agents.

        Args:
            task: The task description
            agent_ids: List of agent IDs to involve
            task_type: Type of task

        Returns:
            Coordination result
        """
        coordination_id = f"coord_{uuid.uuid4().hex[:8]}"
        responses = []

        # Send task to each agent
        for agent_id in agent_ids:
            agent = self.registry.get_agent(agent_id)
            if not agent:
                continue

            message = Message(
                message_id=f"msg_{uuid.uuid4().hex[:8]}",
                from_agent_id="coordinator",
                to_agent_id=agent_id,
                message_type="task",
                content={"task": task, "task_type": task_type, "coordination_id": coordination_id},
            )

            self._messages[message.message_id] = message
            self._message_log.append(message.message_id)

            try:
                # Have agent process the task
                if task_type == "query":
                    response = agent.query(task)
                else:
                    response = agent.teach({"content": task})

                message.status = "responded"
                message.response = response
                message.responded_at = datetime.now()
                responses.append({
                    "agent_id": agent_id,
                    "response": response,
                })
            except Exception as e:
                message.status = "failed"
                responses.append({
                    "agent_id": agent_id,
                    "error": str(e),
                })

        return {
            "coordination_id": coordination_id,
            "task": task,
            "agent_count": len(agent_ids),
            "responses": responses,
            "success_count": sum(1 for r in responses if "response" in r),
        }

    def get_message(self, message_id: str) -> Optional[Message]:
        """
        Get a message by ID.

        Args:
            message_id: The message ID

        Returns:
            The message if found
        """
        return self._messages.get(message_id)

    def get_conversation(
        self,
        agent_id_1: str,
        agent_id_2: str,
        limit: int = 50,
    ) -> List[Message]:
        """
        Get conversation between two agents.

        Args:
            agent_id_1: First agent ID
            agent_id_2: Second agent ID
            limit: Maximum messages to return

        Returns:
            List of messages in conversation
        """
        messages = [
            self._messages[mid] for mid in self._message_log
            if mid in self._messages
        ]

        conversation = [
            m for m in messages
            if (m.from_agent_id == agent_id_1 and m.to_agent_id == agent_id_2) or
               (m.from_agent_id == agent_id_2 and m.to_agent_id == agent_id_1)
        ]

        return conversation[-limit:]

    def get_agent_messages(
        self,
        agent_id: str,
        direction: str = "all",  # "sent", "received", "all"
        limit: int = 50,
    ) -> List[Message]:
        """
        Get messages involving an agent.

        Args:
            agent_id: The agent ID
            direction: Message direction filter
            limit: Maximum messages to return

        Returns:
            List of messages
        """
        messages = [
            self._messages[mid] for mid in self._message_log
            if mid in self._messages
        ]

        if direction == "sent":
            filtered = [m for m in messages if m.from_agent_id == agent_id]
        elif direction == "received":
            filtered = [m for m in messages if m.to_agent_id == agent_id]
        else:
            filtered = [
                m for m in messages
                if m.from_agent_id == agent_id or m.to_agent_id == agent_id
            ]

        return filtered[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        """Get messenger statistics."""
        by_type = {}
        by_status = {}

        for message in self._messages.values():
            by_type[message.message_type] = by_type.get(message.message_type, 0) + 1
            by_status[message.status] = by_status.get(message.status, 0) + 1

        return {
            "total_messages": len(self._messages),
            "by_type": by_type,
            "by_status": by_status,
        }

    def clear_messages(self) -> None:
        """Clear all messages."""
        self._messages.clear()
        self._message_log.clear()
        logger.info("Cleared all messages")

    def __repr__(self) -> str:
        return f"AgentMessenger(messages={len(self._messages)})"
