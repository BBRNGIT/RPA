"""
Agents module - Multi-Agent System.

This module provides:
- BaseAgent: Template for specialized agents
- CodingAgent: Code generation and analysis
- LanguageAgent: Natural language understanding
- AgentRegistry: Agent management
- Orchestrator: Task delegation and coordination
- SharedKnowledge: Cross-agent knowledge sharing
- AgentMessenger: Inter-agent communication
"""

from rpa.agents.base_agent import (
    BaseAgent,
    AgentStatus,
    Inquiry,
)
from rpa.agents.coding_agent import (
    CodingAgent,
    CodeReview,
    CodePattern,
)
from rpa.agents.language_agent import (
    LanguageAgent,
    ParsedSentence,
    Concept,
)
from rpa.agents.agent_registry import (
    AgentRegistry,
    RegistryEntry,
)
from rpa.agents.orchestrator import (
    Orchestrator,
    Task,
    Subtask,
)
from rpa.agents.shared_knowledge import (
    SharedKnowledge,
    KnowledgeTransfer,
    CrossDomainLink,
)
from rpa.agents.agent_messenger import (
    AgentMessenger,
    Message,
)

__all__ = [
    # Base Agent
    "BaseAgent",
    "AgentStatus",
    "Inquiry",
    # Coding Agent
    "CodingAgent",
    "CodeReview",
    "CodePattern",
    # Language Agent
    "LanguageAgent",
    "ParsedSentence",
    "Concept",
    # Registry
    "AgentRegistry",
    "RegistryEntry",
    # Orchestrator
    "Orchestrator",
    "Task",
    "Subtask",
    # Shared Knowledge
    "SharedKnowledge",
    "KnowledgeTransfer",
    "CrossDomainLink",
    # Messenger
    "AgentMessenger",
    "Message",
]
