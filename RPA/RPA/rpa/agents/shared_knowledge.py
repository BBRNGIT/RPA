"""
SharedKnowledge - Cross-agent knowledge sharing.

Provides:
- Pattern sharing between agents
- Cross-domain pattern linking
- Knowledge flow tracking
- Knowledge synchronization
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
import uuid
import logging

from rpa.agents.base_agent import BaseAgent
from rpa.memory.ltm import LongTermMemory
from rpa.core.graph import Node, Edge, EdgeType

logger = logging.getLogger(__name__)


@dataclass
class KnowledgeTransfer:
    """Record of knowledge transfer between agents."""
    transfer_id: str
    from_agent_id: str
    to_agent_id: str
    pattern_id: str
    transferred_at: datetime = field(default_factory=datetime.now)
    status: str = "pending"  # pending, completed, failed
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "transfer_id": self.transfer_id,
            "from_agent_id": self.from_agent_id,
            "to_agent_id": self.to_agent_id,
            "pattern_id": self.pattern_id,
            "transferred_at": self.transferred_at.isoformat(),
            "status": self.status,
            "metadata": self.metadata,
        }


@dataclass
class CrossDomainLink:
    """Link between patterns in different domains."""
    link_id: str
    pattern_id_1: str
    agent_id_1: str
    pattern_id_2: str
    agent_id_2: str
    link_type: str  # "equivalent", "related", "depends_on"
    strength: float = 1.0
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "link_id": self.link_id,
            "pattern_id_1": self.pattern_id_1,
            "agent_id_1": self.agent_id_1,
            "pattern_id_2": self.pattern_id_2,
            "agent_id_2": self.agent_id_2,
            "link_type": self.link_type,
            "strength": self.strength,
            "created_at": self.created_at.isoformat(),
        }


class SharedKnowledge:
    """
    Cross-agent knowledge sharing system.

    Provides:
    - Pattern sharing between agents
    - Cross-domain pattern linking
    - Knowledge flow tracking
    - Knowledge synchronization
    """

    def __init__(self):
        """Initialize SharedKnowledge."""
        self._transfers: Dict[str, KnowledgeTransfer] = {}
        self._cross_domain_links: Dict[str, CrossDomainLink] = {}
        self._knowledge_index: Dict[str, Set[str]] = {}  # agent_id -> pattern_ids
        self._pattern_source: Dict[str, str] = {}  # pattern_id -> original agent_id

    def share_pattern(
        self,
        pattern_id: str,
        from_agent: BaseAgent,
        to_agents: List[BaseAgent],
        ltm: Optional[LongTermMemory] = None,
    ) -> Dict[str, Any]:
        """
        Share a pattern from one agent to others.

        Args:
            pattern_id: The pattern to share
            from_agent: The agent sharing the pattern
            to_agents: List of agents to share with
            ltm: Optional shared LTM

        Returns:
            Sharing result
        """
        results = {"transfers": [], "success_count": 0, "failed_count": 0}

        # Get the pattern from source agent
        pattern = from_agent.ltm.get_pattern(pattern_id)
        if not pattern:
            logger.warning(f"Pattern {pattern_id} not found in agent {from_agent.agent_id}")
            return {"success": False, "error": "Pattern not found"}

        # Record original source
        if pattern_id not in self._pattern_source:
            self._pattern_source[pattern_id] = from_agent.agent_id

        # Track knowledge for source agent
        if from_agent.agent_id not in self._knowledge_index:
            self._knowledge_index[from_agent.agent_id] = set()
        self._knowledge_index[from_agent.agent_id].add(pattern_id)

        # Share with each target agent
        for to_agent in to_agents:
            transfer = KnowledgeTransfer(
                transfer_id=f"xfer_{uuid.uuid4().hex[:8]}",
                from_agent_id=from_agent.agent_id,
                to_agent_id=to_agent.agent_id,
                pattern_id=pattern_id,
            )

            try:
                # Copy pattern to target agent's LTM
                # Create a new node with same content but new ID
                new_pattern = Node(
                    node_id=f"shared_{pattern.node_id}_{uuid.uuid4().hex[:4]}",
                    label=pattern.label,
                    content=pattern.content,
                    domain=pattern.domain,
                    node_type=pattern.node_type,
                    hierarchy_level=pattern.hierarchy_level,
                    metadata={
                        **pattern.metadata,
                        "shared_from": from_agent.agent_id,
                        "original_id": pattern_id,
                        "shared_at": datetime.now().isoformat(),
                    },
                )

                to_agent.ltm.consolidate(
                    node=new_pattern,
                    session_id=to_agent.agent_id,
                    validation_score=0.9,
                    source=f"shared:{from_agent.agent_id}",
                )

                # Track knowledge for target agent
                if to_agent.agent_id not in self._knowledge_index:
                    self._knowledge_index[to_agent.agent_id] = set()
                self._knowledge_index[to_agent.agent_id].add(new_pattern.node_id)

                transfer.status = "completed"
                transfer.metadata["new_pattern_id"] = new_pattern.node_id
                results["success_count"] += 1

            except Exception as e:
                transfer.status = "failed"
                transfer.metadata["error"] = str(e)
                results["failed_count"] += 1
                logger.error(f"Transfer failed: {e}")

            self._transfers[transfer.transfer_id] = transfer
            results["transfers"].append(transfer.to_dict())

        return results

    def link_cross_domain_patterns(
        self,
        pattern_id_1: str,
        agent_id_1: str,
        pattern_id_2: str,
        agent_id_2: str,
        link_type: str = "related",
        strength: float = 1.0,
    ) -> CrossDomainLink:
        """
        Create a cross-domain link between patterns.

        Args:
            pattern_id_1: First pattern ID
            agent_id_1: Agent owning first pattern
            pattern_id_2: Second pattern ID
            agent_id_2: Agent owning second pattern
            link_type: Type of link
            strength: Link strength (0.0 to 1.0)

        Returns:
            The created link
        """
        link = CrossDomainLink(
            link_id=f"link_{uuid.uuid4().hex[:8]}",
            pattern_id_1=pattern_id_1,
            agent_id_1=agent_id_1,
            pattern_id_2=pattern_id_2,
            agent_id_2=agent_id_2,
            link_type=link_type,
            strength=max(0.0, min(1.0, strength)),
        )

        self._cross_domain_links[link.link_id] = link
        logger.info(f"Created cross-domain link: {pattern_id_1} <-> {pattern_id_2}")

        return link

    def get_shared_patterns(
        self,
        agent_id: str,
    ) -> List[str]:
        """
        Get patterns shared with an agent.

        Args:
            agent_id: The agent ID

        Returns:
            List of pattern IDs shared with the agent
        """
        # Get patterns that were transferred to this agent
        shared = []
        for transfer in self._transfers.values():
            if transfer.to_agent_id == agent_id and transfer.status == "completed":
                if "new_pattern_id" in transfer.metadata:
                    shared.append(transfer.metadata["new_pattern_id"])

        return shared

    def get_patterns_shared_by(
        self,
        agent_id: str,
    ) -> List[str]:
        """
        Get patterns shared by an agent.

        Args:
            agent_id: The agent ID

        Returns:
            List of pattern IDs shared by the agent
        """
        shared = []
        for transfer in self._transfers.values():
            if transfer.from_agent_id == agent_id and transfer.status == "completed":
                shared.append(transfer.pattern_id)

        return shared

    def track_knowledge_flow(
        self,
        from_agent_id: str,
        to_agent_id: str,
    ) -> Dict[str, Any]:
        """
        Track knowledge flow between agents.

        Args:
            from_agent_id: Source agent ID
            to_agent_id: Target agent ID

        Returns:
            Knowledge flow information
        """
        transfers = [
            t for t in self._transfers.values()
            if t.from_agent_id == from_agent_id and t.to_agent_id == to_agent_id
        ]

        successful = [t for t in transfers if t.status == "completed"]
        failed = [t for t in transfers if t.status == "failed"]

        return {
            "from_agent": from_agent_id,
            "to_agent": to_agent_id,
            "total_transfers": len(transfers),
            "successful": len(successful),
            "failed": len(failed),
            "patterns_transferred": [t.pattern_id for t in successful],
        }

    def get_cross_domain_links(
        self,
        pattern_id: Optional[str] = None,
        agent_id: Optional[str] = None,
    ) -> List[CrossDomainLink]:
        """
        Get cross-domain links.

        Args:
            pattern_id: Filter by pattern ID
            agent_id: Filter by agent ID

        Returns:
            List of matching links
        """
        links = list(self._cross_domain_links.values())

        if pattern_id:
            links = [
                l for l in links
                if l.pattern_id_1 == pattern_id or l.pattern_id_2 == pattern_id
            ]

        if agent_id:
            links = [
                l for l in links
                if l.agent_id_1 == agent_id or l.agent_id_2 == agent_id
            ]

        return links

    def find_equivalent_patterns(
        self,
        pattern_id: str,
        agent_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Find patterns equivalent to the given one in other domains.

        Args:
            pattern_id: The pattern to find equivalents for
            agent_id: The agent owning the pattern

        Returns:
            List of equivalent patterns with their agents
        """
        equivalents = []

        for link in self._cross_domain_links.values():
            if link.link_type == "equivalent":
                if link.pattern_id_1 == pattern_id and link.agent_id_1 == agent_id:
                    equivalents.append({
                        "pattern_id": link.pattern_id_2,
                        "agent_id": link.agent_id_2,
                        "strength": link.strength,
                    })
                elif link.pattern_id_2 == pattern_id and link.agent_id_2 == agent_id:
                    equivalents.append({
                        "pattern_id": link.pattern_id_1,
                        "agent_id": link.agent_id_1,
                        "strength": link.strength,
                    })

        return equivalents

    def get_knowledge_stats(self) -> Dict[str, Any]:
        """Get knowledge sharing statistics."""
        successful_transfers = sum(
            1 for t in self._transfers.values() if t.status == "completed"
        )

        return {
            "total_transfers": len(self._transfers),
            "successful_transfers": successful_transfers,
            "failed_transfers": len(self._transfers) - successful_transfers,
            "cross_domain_links": len(self._cross_domain_links),
            "agents_with_knowledge": len(self._knowledge_index),
            "unique_patterns": len(self._pattern_source),
        }

    def clear(self) -> None:
        """Clear all shared knowledge records."""
        self._transfers.clear()
        self._cross_domain_links.clear()
        self._knowledge_index.clear()
        self._pattern_source.clear()
        logger.info("Cleared all shared knowledge records")

    def __repr__(self) -> str:
        return (
            f"SharedKnowledge(transfers={len(self._transfers)}, "
            f"links={len(self._cross_domain_links)})"
        )
