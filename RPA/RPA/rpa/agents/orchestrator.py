"""
Orchestrator - Task delegation and multi-agent coordination.

Provides:
- Task decomposition
- Subtask assignment
- Result aggregation
- Multi-agent coordination
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid
import logging

from rpa.agents.base_agent import BaseAgent
from rpa.agents.agent_registry import AgentRegistry

logger = logging.getLogger(__name__)


@dataclass
class Task:
    """Represents a task to be executed."""
    task_id: str
    description: str
    task_type: str  # code, language, analysis, etc.
    status: str = "pending"  # pending, in_progress, completed, failed
    priority: str = "medium"  # high, medium, low
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    assigned_agent: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "task_id": self.task_id,
            "description": self.description,
            "task_type": self.task_type,
            "status": self.status,
            "priority": self.priority,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "assigned_agent": self.assigned_agent,
            "result": self.result,
            "error": self.error,
            "metadata": self.metadata,
        }


@dataclass
class Subtask:
    """Represents a subtask of a larger task."""
    subtask_id: str
    parent_task_id: str
    description: str
    required_capability: str
    status: str = "pending"
    assigned_agent: Optional[str] = None
    result: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "subtask_id": self.subtask_id,
            "parent_task_id": self.parent_task_id,
            "description": self.description,
            "required_capability": str(self.required_capability),
            "status": self.status,
            "assigned_agent": self.assigned_agent,
            "result": self.result,
        }


class Orchestrator:
    """
    Orchestrator for task delegation and coordination.

    Provides:
    - Task decomposition into subtasks
    - Subtask assignment to appropriate agents
    - Multi-agent task execution
    - Result aggregation
    """

    # Task type to capability mapping
    TASK_CAPABILITIES = {
        "code": ["generate_code", "review_code", "debug_code"],
        "language": ["parse_sentence", "generate_sentence", "explain_concept"],
        "analysis": ["assess", "query"],
        "general": ["query", "teach"],
    }

    # Task type to domain mapping
    TASK_DOMAINS = {
        "code": "coding",
        "language": "language",
        "english": "language_english",
        "python": "coding_python",
    }

    def __init__(self, registry: Optional[AgentRegistry] = None):
        """
        Initialize the Orchestrator.

        Args:
            registry: Optional AgentRegistry instance
        """
        self.registry = registry or AgentRegistry()
        self._tasks: Dict[str, Task] = {}
        self._subtasks: Dict[str, List[Subtask]] = {}  # task_id -> subtasks

    def create_task(
        self,
        description: str,
        task_type: str = "general",
        priority: str = "medium",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Task:
        """
        Create a new task.

        Args:
            description: Task description
            task_type: Type of task
            priority: Task priority
            metadata: Optional metadata

        Returns:
            The created task
        """
        task = Task(
            task_id=f"task_{uuid.uuid4().hex[:8]}",
            description=description,
            task_type=task_type,
            priority=priority,
            metadata=metadata or {},
        )
        self._tasks[task.task_id] = task
        logger.info(f"Created task {task.task_id}: {description}")
        return task

    def decompose_task(self, task: Task) -> List[Subtask]:
        """
        Decompose a task into subtasks.

        Args:
            task: The task to decompose

        Returns:
            List of subtasks
        """
        subtasks = []

        # Simple decomposition based on task type
        task_lower = task.description.lower()

        if task.task_type == "code":
            # Code tasks might need generation and review
            if "generate" in task_lower or "create" in task_lower:
                subtasks.append(Subtask(
                    subtask_id=f"sub_{uuid.uuid4().hex[:8]}",
                    parent_task_id=task.task_id,
                    description="Generate code",
                    required_capability="generate_code",
                ))
            if "review" in task_lower or "check" in task_lower:
                subtasks.append(Subtask(
                    subtask_id=f"sub_{uuid.uuid4().hex[:8]}",
                    parent_task_id=task.task_id,
                    description="Review code",
                    required_capability="review_code",
                ))
            if not subtasks:
                subtasks.append(Subtask(
                    subtask_id=f"sub_{uuid.uuid4().hex[:8]}",
                    parent_task_id=task.task_id,
                    description="Process code task",
                    required_capability="generate_code",
                ))

        elif task.task_type == "language":
            if "parse" in task_lower:
                subtasks.append(Subtask(
                    subtask_id=f"sub_{uuid.uuid4().hex[:8]}",
                    parent_task_id=task.task_id,
                    description="Parse sentence",
                    required_capability="parse_sentence",
                ))
            if "generate" in task_lower:
                subtasks.append(Subtask(
                    subtask_id=f"sub_{uuid.uuid4().hex[:8]}",
                    parent_task_id=task.task_id,
                    description="Generate sentence",
                    required_capability="generate_sentence",
                ))
            if not subtasks:
                subtasks.append(Subtask(
                    subtask_id=f"sub_{uuid.uuid4().hex[:8]}",
                    parent_task_id=task.task_id,
                    description="Process language task",
                    required_capability="explain_concept",
                ))

        else:
            # General task
            subtasks.append(Subtask(
                subtask_id=f"sub_{uuid.uuid4().hex[:8]}",
                parent_task_id=task.task_id,
                description=task.description,
                required_capability="query",
            ))

        self._subtasks[task.task_id] = subtasks
        logger.info(f"Decomposed task {task.task_id} into {len(subtasks)} subtasks")

        return subtasks

    def assign_subtask(
        self,
        subtask: Subtask,
        agents: Optional[List[BaseAgent]] = None,
    ) -> Optional[str]:
        """
        Assign a subtask to an appropriate agent.

        Args:
            subtask: The subtask to assign
            agents: Optional list of agents to choose from

        Returns:
            Assigned agent ID, or None if no suitable agent found
        """
        # Find agents with required capability
        if agents is None:
            matching_agents = self.registry.find_agents_by_capability(
                subtask.required_capability
            )
        else:
            matching_agents = [
                a for a in agents
                if subtask.required_capability in a.get_capabilities().get(
                    "domain_specific", []
                ) or subtask.required_capability in a.get_capabilities().get(
                    "capabilities", []
                )
            ]

        if not matching_agents:
            logger.warning(f"No agents found for capability: {subtask.required_capability}")
            return None

        # Assign to first available agent
        agent = matching_agents[0]
        subtask.assigned_agent = agent.agent_id
        subtask.status = "assigned"

        logger.info(f"Assigned subtask {subtask.subtask_id} to agent {agent.agent_id}")

        return agent.agent_id

    def execute_subtask(
        self,
        subtask: Subtask,
        input_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a subtask.

        Args:
            subtask: The subtask to execute
            input_data: Optional input data

        Returns:
            Execution result
        """
        if not subtask.assigned_agent:
            return {"success": False, "error": "No agent assigned"}

        agent = self.registry.get_agent(subtask.assigned_agent)
        if not agent:
            return {"success": False, "error": "Agent not found"}

        subtask.status = "in_progress"
        result = {"success": False}

        # Execute based on capability
        try:
            capability = subtask.required_capability

            if capability == "generate_code":
                result = agent.generate_code(
                    input_data.get("task", subtask.description)
                )
            elif capability == "review_code":
                result = agent.review_code(
                    input_data.get("code", "")
                ).to_dict()
            elif capability == "parse_sentence":
                result = agent.parse_sentence(
                    input_data.get("sentence", "")
                ).to_dict()
            elif capability == "generate_sentence":
                result = agent.generate_sentence(
                    input_data.get("components", {})
                )
            elif capability == "explain_concept":
                result = agent.explain_concept(
                    input_data.get("concept", "")
                )
            elif capability == "query":
                result = {"response": agent.query(
                    input_data.get("question", subtask.description)
                )}
            else:
                # Generic execution
                result = agent.teach({
                    "content": input_data.get("content", subtask.description),
                })

            subtask.status = "completed"
            subtask.result = result

        except Exception as e:
            subtask.status = "failed"
            result = {"success": False, "error": str(e)}
            logger.error(f"Subtask {subtask.subtask_id} failed: {e}")

        return result

    def execute_orchestrated_task(
        self,
        task: Task,
        agents: Optional[List[BaseAgent]] = None,
        input_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a task with full orchestration.

        Args:
            task: The task to execute
            agents: Optional list of agents to use
            input_data: Optional input data

        Returns:
            Aggregated results
        """
        task.status = "in_progress"
        task.started_at = datetime.now()

        # Decompose task
        subtasks = self.decompose_task(task)

        # Execute each subtask
        results = []
        for subtask in subtasks:
            # Assign to agent
            agent_id = self.assign_subtask(subtask, agents)

            if agent_id:
                # Execute
                result = self.execute_subtask(subtask, input_data)
                results.append({
                    "subtask_id": subtask.subtask_id,
                    "agent_id": agent_id,
                    "result": result,
                })
            else:
                results.append({
                    "subtask_id": subtask.subtask_id,
                    "error": "No suitable agent found",
                })

        # Aggregate results
        aggregated = self.aggregate_results(results)
        task.result = aggregated
        task.status = "completed"
        task.completed_at = datetime.now()

        return aggregated

    def aggregate_results(
        self,
        results: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Aggregate results from multiple subtasks.

        Args:
            results: List of subtask results

        Returns:
            Aggregated result dictionary
        """
        successful = [r for r in results if r.get("result", {}).get("success")]
        failed = [r for r in results if not r.get("result", {}).get("success")]

        return {
            "success": len(successful) > 0,
            "total_subtasks": len(results),
            "successful": len(successful),
            "failed": len(failed),
            "results": results,
            "summary": self._create_summary(results),
        }

    def _create_summary(self, results: List[Dict[str, Any]]) -> str:
        """Create a human-readable summary of results."""
        parts = []
        for r in results:
            if r.get("result", {}).get("success"):
                parts.append(f"✓ Subtask {r['subtask_id'][:12]} completed")
            else:
                parts.append(f"✗ Subtask {r['subtask_id'][:12]} failed")
        return "\n".join(parts)

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        return self._tasks.get(task_id)

    def get_subtasks(self, task_id: str) -> List[Subtask]:
        """Get subtasks for a task."""
        return self._subtasks.get(task_id, [])

    def get_stats(self) -> Dict[str, Any]:
        """Get orchestrator statistics."""
        total = len(self._tasks)
        completed = sum(1 for t in self._tasks.values() if t.status == "completed")
        failed = sum(1 for t in self._tasks.values() if t.status == "failed")
        pending = sum(1 for t in self._tasks.values() if t.status == "pending")

        return {
            "total_tasks": total,
            "completed": completed,
            "failed": failed,
            "pending": pending,
            "success_rate": completed / total if total > 0 else 0,
        }

    def __repr__(self) -> str:
        return f"Orchestrator(tasks={len(self._tasks)})"
