"""
AgentRegistry - Central registry for agent management.

Provides:
- Agent registration and deregistration
- Agent discovery by domain
- Capability querying
- Agent lifecycle management
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Type
import uuid
import logging

from rpa.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


@dataclass
class RegistryEntry:
    """Entry in the agent registry."""
    agent_id: str
    agent: BaseAgent
    domain: str
    registered_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary (without agent object)."""
        return {
            "agent_id": self.agent_id,
            "domain": self.domain,
            "registered_at": self.registered_at.isoformat(),
            "last_active": self.last_active.isoformat(),
            "metadata": self.metadata,
        }


class AgentRegistry:
    """
    Central registry for managing agents.

    Provides:
    - Agent registration and deregistration
    - Agent lookup by ID or domain
    - Capability querying
    - Activity tracking
    """

    def __init__(self):
        """Initialize the AgentRegistry."""
        self._agents: Dict[str, RegistryEntry] = {}
        self._domain_index: Dict[str, List[str]] = {}  # domain -> agent_ids

    def register_agent(
        self,
        agent: BaseAgent,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Register an agent.

        Args:
            agent: The agent to register
            metadata: Optional metadata about the agent

        Returns:
            The agent ID
        """
        if agent.agent_id in self._agents:
            logger.warning(f"Agent {agent.agent_id} already registered, updating")

        # Create entry
        entry = RegistryEntry(
            agent_id=agent.agent_id,
            agent=agent,
            domain=agent.domain,
            metadata=metadata or {},
        )

        self._agents[agent.agent_id] = entry

        # Update domain index
        if agent.domain not in self._domain_index:
            self._domain_index[agent.domain] = []
        if agent.agent_id not in self._domain_index[agent.domain]:
            self._domain_index[agent.domain].append(agent.agent_id)

        logger.info(f"Registered agent {agent.agent_id} in domain {agent.domain}")

        return agent.agent_id

    def deregister_agent(self, agent_id: str) -> bool:
        """
        Deregister an agent.

        Args:
            agent_id: ID of the agent to deregister

        Returns:
            True if successful, False if agent not found
        """
        if agent_id not in self._agents:
            return False

        entry = self._agents[agent_id]

        # Remove from domain index
        if entry.domain in self._domain_index:
            if agent_id in self._domain_index[entry.domain]:
                self._domain_index[entry.domain].remove(agent_id)
            if not self._domain_index[entry.domain]:
                del self._domain_index[entry.domain]

        # Remove agent
        del self._agents[agent_id]

        logger.info(f"Deregistered agent {agent_id}")

        return True

    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """
        Get an agent by ID.

        Args:
            agent_id: The agent ID

        Returns:
            The agent if found, None otherwise
        """
        entry = self._agents.get(agent_id)
        if entry:
            entry.last_active = datetime.now()
            return entry.agent
        return None

    def list_agents(
        self,
        domain: Optional[str] = None,
        active_only: bool = False,
    ) -> List[BaseAgent]:
        """
        List agents, optionally filtered by domain.

        Args:
            domain: Optional domain filter
            active_only: Only return recently active agents

        Returns:
            List of agents
        """
        if domain:
            agent_ids = self._domain_index.get(domain, [])
            return [
                self._agents[aid].agent
                for aid in agent_ids
                if aid in self._agents
            ]

        return [entry.agent for entry in self._agents.values()]

    def list_agent_ids(self, domain: Optional[str] = None) -> List[str]:
        """
        List agent IDs, optionally filtered by domain.

        Args:
            domain: Optional domain filter

        Returns:
            List of agent IDs
        """
        if domain:
            return self._domain_index.get(domain, [])
        return list(self._agents.keys())

    def get_agent_capabilities(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get an agent's capabilities.

        Args:
            agent_id: The agent ID

        Returns:
            Capabilities dictionary if agent found, None otherwise
        """
        agent = self.get_agent(agent_id)
        if agent:
            return agent.get_capabilities()
        return None

    def has_agent(self, agent_id: str) -> bool:
        """Check if an agent is registered."""
        return agent_id in self._agents

    def get_domains(self) -> List[str]:
        """Get list of all registered domains."""
        return list(self._domain_index.keys())

    def get_agent_count(self, domain: Optional[str] = None) -> int:
        """
        Get count of registered agents.

        Args:
            domain: Optional domain to filter by

        Returns:
            Number of agents
        """
        if domain:
            return len(self._domain_index.get(domain, []))
        return len(self._agents)

    def update_agent_activity(self, agent_id: str) -> None:
        """Update an agent's last activity timestamp."""
        entry = self._agents.get(agent_id)
        if entry:
            entry.last_active = datetime.now()

    def get_registry_stats(self) -> Dict[str, Any]:
        """Get registry statistics."""
        return {
            "total_agents": len(self._agents),
            "domains": self.get_domains(),
            "agents_by_domain": {
                domain: len(aids) for domain, aids in self._domain_index.items()
            },
        }

    def find_agents_by_capability(
        self,
        capability: str,
        domain: Optional[str] = None,
    ) -> List[BaseAgent]:
        """
        Find agents with a specific capability.

        Args:
            capability: The capability to search for
            domain: Optional domain filter

        Returns:
            List of agents with the capability
        """
        agents = self.list_agents(domain)
        matching = []

        for agent in agents:
            caps = agent.get_capabilities()
            if capability in caps.get("capabilities", []):
                matching.append(agent)
            if capability in caps.get("domain_specific", []):
                matching.append(agent)

        return matching

    def clear(self) -> None:
        """Clear all registered agents."""
        self._agents.clear()
        self._domain_index.clear()
        logger.info("Cleared all agents from registry")

    def __len__(self) -> int:
        """Return number of registered agents."""
        return len(self._agents)

    def __contains__(self, agent_id: str) -> bool:
        """Check if an agent is registered."""
        return agent_id in self._agents

    def __repr__(self) -> str:
        return f"AgentRegistry(agents={len(self._agents)}, domains={len(self._domain_index)})"
