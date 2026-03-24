"""
Tests for Phase 5: Multi-Agent System.

Tests for:
- BaseAgent: Core agent functionality
- CodingAgent: Code generation and analysis
- LanguageAgent: Natural language understanding
- AgentRegistry: Agent management
- Orchestrator: Task delegation
- SharedKnowledge: Cross-agent learning
- AgentMessenger: Inter-agent communication
"""

import pytest
from datetime import datetime


# =============================================================================
# BaseAgent Tests
# =============================================================================

class TestBaseAgent:
    """Tests for BaseAgent."""

    def test_imports(self):
        """Test that BaseAgent components can be imported."""
        from rpa.agents.base_agent import (
            BaseAgent,
            AgentStatus,
            Inquiry,
        )
        assert BaseAgent is not None
        assert AgentStatus is not None
        assert Inquiry is not None

    def test_create_agent(self):
        """Test creating a BaseAgent."""
        from rpa.agents.base_agent import BaseAgent
        agent = BaseAgent(domain="test")
        assert agent.domain == "test"
        assert agent.agent_id.startswith("agent_test_")

    def test_create_agent_with_id(self):
        """Test creating agent with specific ID."""
        from rpa.agents.base_agent import BaseAgent
        agent = BaseAgent(domain="test", agent_id="custom_agent_123")
        assert agent.agent_id == "custom_agent_123"

    def test_query(self):
        """Test querying an agent."""
        from rpa.agents.base_agent import BaseAgent
        agent = BaseAgent(domain="test")

        # Teach something first
        agent.teach({"content": "test pattern", "label": "test"})

        # Query should find it
        response = agent.query("test")
        assert "test" in response.lower()

    def test_teach(self):
        """Test teaching an agent."""
        from rpa.agents.base_agent import BaseAgent
        agent = BaseAgent(domain="test")

        result = agent.teach({
            "content": "apple is a fruit",
            "label": "apple",
            "hierarchy_level": 1,
        })

        assert result["success"] is True
        assert "pattern_id" in result
        assert agent._status.patterns_learned == 1

    def test_assess(self):
        """Test assessing a pattern."""
        from rpa.agents.base_agent import BaseAgent
        agent = BaseAgent(domain="test")

        # Teach a pattern
        result = agent.teach({"content": "test content"})
        pattern_id = result["pattern_id"]

        # Assess it
        assessment = agent.assess(pattern_id)
        assert assessment["success"] is True
        assert "is_valid" in assessment
        assert "score" in assessment

    def test_assess_nonexistent(self):
        """Test assessing a nonexistent pattern."""
        from rpa.agents.base_agent import BaseAgent
        agent = BaseAgent(domain="test")

        assessment = agent.assess("nonexistent_pattern")
        assert assessment["success"] is False
        assert "not found" in assessment["message"].lower()

    def test_ask_inquiry(self):
        """Test asking an inquiry."""
        from rpa.agents.base_agent import BaseAgent
        agent = BaseAgent(domain="test")

        inquiry = agent.ask_inquiry(
            question="What is this?",
            inquiry_type="general",
            priority="high",
        )

        assert inquiry.inquiry_id is not None
        assert inquiry.question == "What is this?"
        assert inquiry.priority == "high"
        assert inquiry.answered is False

    def test_answer_inquiry(self):
        """Test answering an inquiry."""
        from rpa.agents.base_agent import BaseAgent
        agent = BaseAgent(domain="test")

        inquiry = agent.ask_inquiry("Test question?")
        result = agent.answer_inquiry(inquiry.inquiry_id, "Test answer")

        assert result["success"] is True
        assert inquiry.answered is True
        assert inquiry.answer == "Test answer"

    def test_get_pending_inquiries(self):
        """Test getting pending inquiries."""
        from rpa.agents.base_agent import BaseAgent
        agent = BaseAgent(domain="test")

        agent.ask_inquiry("Question 1?")
        agent.ask_inquiry("Question 2?")

        pending = agent.get_pending_inquiries()
        assert len(pending) == 2

    def test_get_status(self):
        """Test getting agent status."""
        from rpa.agents.base_agent import BaseAgent
        agent = BaseAgent(domain="test")

        status = agent.get_status()
        assert status["agent_id"] == agent.agent_id
        assert status["domain"] == "test"
        assert "patterns_learned" in status

    def test_get_capabilities(self):
        """Test getting agent capabilities."""
        from rpa.agents.base_agent import BaseAgent
        agent = BaseAgent(domain="test")

        caps = agent.get_capabilities()
        assert "capabilities" in caps
        assert "query" in caps["capabilities"]
        assert "teach" in caps["capabilities"]

    def test_to_dict_and_from_dict(self):
        """Test serialization and deserialization."""
        from rpa.agents.base_agent import BaseAgent
        agent = BaseAgent(domain="test")
        agent.teach({"content": "test"})

        # Serialize
        data = agent.to_dict()
        assert data["domain"] == "test"

        # Deserialize
        agent2 = BaseAgent.from_dict(data)
        assert agent2.domain == "test"
        assert agent2.agent_id == agent.agent_id


# =============================================================================
# CodingAgent Tests
# =============================================================================

class TestCodingAgent:
    """Tests for CodingAgent."""

    def test_imports(self):
        """Test that CodingAgent components can be imported."""
        from rpa.agents.coding_agent import (
            CodingAgent,
            CodeReview,
            CodePattern,
        )
        assert CodingAgent is not None
        assert CodeReview is not None
        assert CodePattern is not None

    def test_create_coding_agent(self):
        """Test creating a CodingAgent."""
        from rpa.agents.coding_agent import CodingAgent
        agent = CodingAgent(language="python")
        assert agent.language == "python"
        assert "coding_python" in agent.domain

    def test_generate_code_for_loop(self):
        """Test generating for loop code."""
        from rpa.agents.coding_agent import CodingAgent
        agent = CodingAgent(language="python")

        result = agent.generate_code("create a for loop from 0 to 5")
        assert result["success"] is True
        assert "for" in result["code"].lower()
        assert "range" in result["code"].lower()

    def test_generate_code_if_statement(self):
        """Test generating if statement code."""
        from rpa.agents.coding_agent import CodingAgent
        agent = CodingAgent(language="python")

        result = agent.generate_code("create an if statement")
        assert result["success"] is True
        assert "if" in result["code"].lower()

    def test_refactor_code(self):
        """Test refactoring code."""
        from rpa.agents.coding_agent import CodingAgent
        agent = CodingAgent(language="python")

        code = "x=1\ty=2"  # with tabs
        result = agent.refactor_code(code)

        assert result["success"] is True
        assert "refactored_code" in result
        assert "suggestions" in result

    def test_review_code(self):
        """Test reviewing code."""
        from rpa.agents.coding_agent import CodingAgent
        agent = CodingAgent(language="python")

        code = "def foo():\n    pass\n"
        review = agent.review_code(code)

        assert review.review_id is not None
        assert review.score >= 0
        assert isinstance(review.issues, list)

    def test_debug_code_name_error(self):
        """Test debugging NameError."""
        from rpa.agents.coding_agent import CodingAgent
        agent = CodingAgent(language="python")

        result = agent.debug_code(
            code="print(undefined_var)",
            error="NameError: name 'undefined_var' is not defined",
        )

        assert result["success"] is True
        assert len(result["suggestions"]) > 0
        assert "undefined_var" in result["suggestions"][0]

    def test_debug_code_syntax_error(self):
        """Test debugging SyntaxError."""
        from rpa.agents.coding_agent import CodingAgent
        agent = CodingAgent(language="python")

        result = agent.debug_code(
            code="print('missing quote",
            error="SyntaxError: EOL while scanning string literal",
        )

        assert result["success"] is True
        assert len(result["suggestions"]) > 0

    def test_execute_code(self):
        """Test executing code in sandbox."""
        from rpa.agents.coding_agent import CodingAgent
        agent = CodingAgent(language="python")

        result = agent.execute_code("x = 1 + 1\nprint(x)")
        assert result.success is True
        assert "2" in result.output

    def test_execute_code_with_error(self):
        """Test executing code with error."""
        from rpa.agents.coding_agent import CodingAgent
        agent = CodingAgent(language="python")

        result = agent.execute_code("1 / 0")
        assert result.success is False
        assert "ZeroDivisionError" in result.error_type

    def test_recognize_pattern(self):
        """Test recognizing code patterns."""
        from rpa.agents.coding_agent import CodingAgent
        agent = CodingAgent(language="python")

        code = "def hello():\n    print('world')\nfor i in range(10):\n    pass"
        patterns = agent.recognize_pattern(code)

        assert len(patterns) >= 1
        # Should find function or for loop pattern

    def test_get_capabilities(self):
        """Test getting coding agent capabilities."""
        from rpa.agents.coding_agent import CodingAgent
        agent = CodingAgent()

        caps = agent.get_capabilities()
        assert "generate_code" in caps["domain_specific"]
        assert "review_code" in caps["domain_specific"]


# =============================================================================
# LanguageAgent Tests
# =============================================================================

class TestLanguageAgent:
    """Tests for LanguageAgent."""

    def test_imports(self):
        """Test that LanguageAgent components can be imported."""
        from rpa.agents.language_agent import (
            LanguageAgent,
            ParsedSentence,
            Concept,
        )
        assert LanguageAgent is not None
        assert ParsedSentence is not None
        assert Concept is not None

    def test_create_language_agent(self):
        """Test creating a LanguageAgent."""
        from rpa.agents.language_agent import LanguageAgent
        agent = LanguageAgent(language="english")
        assert agent.language == "english"
        assert "language_english" in agent.domain

    def test_parse_sentence(self):
        """Test parsing a sentence."""
        from rpa.agents.language_agent import LanguageAgent
        agent = LanguageAgent()

        parsed = agent.parse_sentence("The cat sat on the mat.")

        assert parsed.parse_id is not None
        assert len(parsed.words) >= 4
        assert "structure" in parsed.to_dict()

    def test_generate_sentence(self):
        """Test generating a sentence."""
        from rpa.agents.language_agent import LanguageAgent
        agent = LanguageAgent()

        result = agent.generate_sentence({
            "subject": "The dog",
            "verb": "ran",
            "object": "quickly",
        })

        assert result["success"] is True
        assert "dog" in result["sentence"].lower()
        assert "ran" in result["sentence"].lower()

    def test_explain_concept_known(self):
        """Test explaining a known concept."""
        from rpa.agents.language_agent import LanguageAgent
        agent = LanguageAgent()

        result = agent.explain_concept("noun")

        assert result["success"] is True
        assert "definition" in result
        assert "examples" in result

    def test_explain_concept_unknown(self):
        """Test explaining an unknown concept."""
        from rpa.agents.language_agent import LanguageAgent
        agent = LanguageAgent()

        result = agent.explain_concept("xyzzy123nonexistent")

        assert result["success"] is False

    def test_translate_concept(self):
        """Test translating concept between domains."""
        from rpa.agents.language_agent import LanguageAgent
        agent = LanguageAgent()

        result = agent.translate_concept(
            concept="if",
            from_domain="english",
            to_domain="python",
        )

        assert result["success"] is True
        assert "translation" in result

    def test_analyze_grammar(self):
        """Test analyzing grammar."""
        from rpa.agents.language_agent import LanguageAgent
        agent = LanguageAgent()

        analysis = agent.analyze_grammar("The cat sat. The dog ran.")

        assert analysis["sentence_count"] == 2
        assert analysis["word_count"] >= 6

    def test_add_concept(self):
        """Test adding a concept."""
        from rpa.agents.language_agent import LanguageAgent
        agent = LanguageAgent()

        concept = agent.add_concept(
            name="test_concept",
            category="test",
            definition="A test concept",
            examples=["example 1", "example 2"],
        )

        assert concept.concept_id is not None
        assert concept.name == "test_concept"


# =============================================================================
# AgentRegistry Tests
# =============================================================================

class TestAgentRegistry:
    """Tests for AgentRegistry."""

    def test_imports(self):
        """Test that AgentRegistry components can be imported."""
        from rpa.agents.agent_registry import (
            AgentRegistry,
            RegistryEntry,
        )
        assert AgentRegistry is not None
        assert RegistryEntry is not None

    def test_create_registry(self):
        """Test creating an AgentRegistry."""
        from rpa.agents.agent_registry import AgentRegistry
        registry = AgentRegistry()
        assert registry is not None
        assert len(registry) == 0

    def test_register_agent(self):
        """Test registering an agent."""
        from rpa.agents.agent_registry import AgentRegistry
        from rpa.agents.base_agent import BaseAgent

        registry = AgentRegistry()
        agent = BaseAgent(domain="test")

        agent_id = registry.register_agent(agent)
        assert agent_id == agent.agent_id
        assert len(registry) == 1

    def test_deregister_agent(self):
        """Test deregistering an agent."""
        from rpa.agents.agent_registry import AgentRegistry
        from rpa.agents.base_agent import BaseAgent

        registry = AgentRegistry()
        agent = BaseAgent(domain="test")

        registry.register_agent(agent)
        result = registry.deregister_agent(agent.agent_id)

        assert result is True
        assert len(registry) == 0

    def test_get_agent(self):
        """Test getting an agent by ID."""
        from rpa.agents.agent_registry import AgentRegistry
        from rpa.agents.base_agent import BaseAgent

        registry = AgentRegistry()
        agent = BaseAgent(domain="test")
        registry.register_agent(agent)

        retrieved = registry.get_agent(agent.agent_id)
        assert retrieved is agent

    def test_list_agents(self):
        """Test listing agents."""
        from rpa.agents.agent_registry import AgentRegistry
        from rpa.agents.base_agent import BaseAgent

        registry = AgentRegistry()
        registry.register_agent(BaseAgent(domain="domain1"))
        registry.register_agent(BaseAgent(domain="domain2"))

        agents = registry.list_agents()
        assert len(agents) == 2

    def test_list_agents_by_domain(self):
        """Test listing agents by domain."""
        from rpa.agents.agent_registry import AgentRegistry
        from rpa.agents.base_agent import BaseAgent

        registry = AgentRegistry()
        registry.register_agent(BaseAgent(domain="domain1"))
        registry.register_agent(BaseAgent(domain="domain2"))
        registry.register_agent(BaseAgent(domain="domain1"))

        agents = registry.list_agents(domain="domain1")
        assert len(agents) == 2

    def test_get_agent_capabilities(self):
        """Test getting agent capabilities."""
        from rpa.agents.agent_registry import AgentRegistry
        from rpa.agents.coding_agent import CodingAgent

        registry = AgentRegistry()
        agent = CodingAgent()
        registry.register_agent(agent)

        caps = registry.get_agent_capabilities(agent.agent_id)
        assert caps is not None
        assert "generate_code" in caps.get("domain_specific", [])

    def test_find_agents_by_capability(self):
        """Test finding agents by capability."""
        from rpa.agents.agent_registry import AgentRegistry
        from rpa.agents.coding_agent import CodingAgent
        from rpa.agents.language_agent import LanguageAgent

        registry = AgentRegistry()
        registry.register_agent(CodingAgent())
        registry.register_agent(LanguageAgent())

        coders = registry.find_agents_by_capability("generate_code")
        assert len(coders) >= 1

    def test_get_registry_stats(self):
        """Test getting registry stats."""
        from rpa.agents.agent_registry import AgentRegistry
        from rpa.agents.base_agent import BaseAgent

        registry = AgentRegistry()
        registry.register_agent(BaseAgent(domain="domain1"))
        registry.register_agent(BaseAgent(domain="domain2"))

        stats = registry.get_registry_stats()
        assert stats["total_agents"] == 2
        assert len(stats["domains"]) == 2


# =============================================================================
# Orchestrator Tests
# =============================================================================

class TestOrchestrator:
    """Tests for Orchestrator."""

    def test_imports(self):
        """Test that Orchestrator components can be imported."""
        from rpa.agents.orchestrator import (
            Orchestrator,
            Task,
            Subtask,
        )
        assert Orchestrator is not None
        assert Task is not None
        assert Subtask is not None

    def test_create_orchestrator(self):
        """Test creating an Orchestrator."""
        from rpa.agents.orchestrator import Orchestrator
        orchestrator = Orchestrator()
        assert orchestrator is not None

    def test_create_task(self):
        """Test creating a task."""
        from rpa.agents.orchestrator import Orchestrator
        orchestrator = Orchestrator()

        task = orchestrator.create_task(
            description="Test task",
            task_type="general",
            priority="high",
        )

        assert task.task_id is not None
        assert task.description == "Test task"
        assert task.status == "pending"

    def test_decompose_task_code(self):
        """Test decomposing a code task."""
        from rpa.agents.orchestrator import Orchestrator
        orchestrator = Orchestrator()

        task = orchestrator.create_task(
            description="Generate and review code",
            task_type="code",
        )

        subtasks = orchestrator.decompose_task(task)
        assert len(subtasks) >= 1

    def test_decompose_task_language(self):
        """Test decomposing a language task."""
        from rpa.agents.orchestrator import Orchestrator
        orchestrator = Orchestrator()

        task = orchestrator.create_task(
            description="Parse the sentence",
            task_type="language",
        )

        subtasks = orchestrator.decompose_task(task)
        assert len(subtasks) >= 1

    def test_assign_subtask(self):
        """Test assigning a subtask."""
        from rpa.agents.orchestrator import Orchestrator, Subtask
        from rpa.agents.agent_registry import AgentRegistry
        from rpa.agents.coding_agent import CodingAgent

        registry = AgentRegistry()
        registry.register_agent(CodingAgent())

        orchestrator = Orchestrator(registry=registry)
        subtask = Subtask(
            subtask_id="sub_test",
            parent_task_id="task_test",
            description="Test",
            required_capability="generate_code",
        )

        agent_id = orchestrator.assign_subtask(subtask)
        assert agent_id is not None

    def test_get_task(self):
        """Test getting a task by ID."""
        from rpa.agents.orchestrator import Orchestrator
        orchestrator = Orchestrator()

        task = orchestrator.create_task("Test task")
        retrieved = orchestrator.get_task(task.task_id)

        assert retrieved is task

    def test_get_stats(self):
        """Test getting orchestrator stats."""
        from rpa.agents.orchestrator import Orchestrator
        orchestrator = Orchestrator()

        orchestrator.create_task("Task 1")
        orchestrator.create_task("Task 2")

        stats = orchestrator.get_stats()
        assert stats["total_tasks"] == 2


# =============================================================================
# SharedKnowledge Tests
# =============================================================================

class TestSharedKnowledge:
    """Tests for SharedKnowledge."""

    def test_imports(self):
        """Test that SharedKnowledge components can be imported."""
        from rpa.agents.shared_knowledge import (
            SharedKnowledge,
            KnowledgeTransfer,
            CrossDomainLink,
        )
        assert SharedKnowledge is not None
        assert KnowledgeTransfer is not None
        assert CrossDomainLink is not None

    def test_create_shared_knowledge(self):
        """Test creating SharedKnowledge."""
        from rpa.agents.shared_knowledge import SharedKnowledge
        sk = SharedKnowledge()
        assert sk is not None

    def test_share_pattern(self):
        """Test sharing a pattern between agents."""
        from rpa.agents.shared_knowledge import SharedKnowledge
        from rpa.agents.base_agent import BaseAgent

        sk = SharedKnowledge()
        agent1 = BaseAgent(domain="domain1")
        agent2 = BaseAgent(domain="domain2")

        # Teach agent1 a pattern
        result = agent1.teach({"content": "shared knowledge", "label": "test"})
        pattern_id = result["pattern_id"]

        # Share with agent2
        share_result = sk.share_pattern(
            pattern_id=pattern_id,
            from_agent=agent1,
            to_agents=[agent2],
        )

        assert share_result["success_count"] >= 1

    def test_link_cross_domain_patterns(self):
        """Test linking cross-domain patterns."""
        from rpa.agents.shared_knowledge import SharedKnowledge

        sk = SharedKnowledge()
        link = sk.link_cross_domain_patterns(
            pattern_id_1="pattern_1",
            agent_id_1="agent_1",
            pattern_id_2="pattern_2",
            agent_id_2="agent_2",
            link_type="equivalent",
        )

        assert link.link_id is not None
        assert link.link_type == "equivalent"

    def test_get_cross_domain_links(self):
        """Test getting cross-domain links."""
        from rpa.agents.shared_knowledge import SharedKnowledge

        sk = SharedKnowledge()
        sk.link_cross_domain_patterns(
            "p1", "a1", "p2", "a2", "equivalent"
        )

        links = sk.get_cross_domain_links(agent_id="a1")
        assert len(links) == 1

    def test_find_equivalent_patterns(self):
        """Test finding equivalent patterns."""
        from rpa.agents.shared_knowledge import SharedKnowledge

        sk = SharedKnowledge()
        sk.link_cross_domain_patterns(
            "p1", "a1", "p2", "a2", "equivalent"
        )

        equivalents = sk.find_equivalent_patterns("p1", "a1")
        assert len(equivalents) == 1
        assert equivalents[0]["pattern_id"] == "p2"

    def test_get_knowledge_stats(self):
        """Test getting knowledge stats."""
        from rpa.agents.shared_knowledge import SharedKnowledge

        sk = SharedKnowledge()
        sk.link_cross_domain_patterns(
            "p1", "a1", "p2", "a2", "equivalent"
        )

        stats = sk.get_knowledge_stats()
        assert stats["cross_domain_links"] == 1


# =============================================================================
# AgentMessenger Tests
# =============================================================================

class TestAgentMessenger:
    """Tests for AgentMessenger."""

    def test_imports(self):
        """Test that AgentMessenger components can be imported."""
        from rpa.agents.agent_messenger import (
            AgentMessenger,
            Message,
        )
        assert AgentMessenger is not None
        assert Message is not None

    def test_create_messenger(self):
        """Test creating AgentMessenger."""
        from rpa.agents.agent_messenger import AgentMessenger
        messenger = AgentMessenger()
        assert messenger is not None

    def test_send_query(self):
        """Test sending a query between agents."""
        from rpa.agents.agent_messenger import AgentMessenger
        from rpa.agents.agent_registry import AgentRegistry
        from rpa.agents.base_agent import BaseAgent

        registry = AgentRegistry()
        agent1 = BaseAgent(domain="domain1")
        agent2 = BaseAgent(domain="domain2")
        agent2.teach({"content": "test knowledge", "label": "test"})

        registry.register_agent(agent1)
        registry.register_agent(agent2)

        messenger = AgentMessenger(registry=registry)
        msg_id, response = messenger.send_query(
            from_agent_id=agent1.agent_id,
            to_agent_id=agent2.agent_id,
            query="test",
        )

        assert msg_id is not None
        assert response is not None

    def test_send_teaching(self):
        """Test sending teaching between agents."""
        from rpa.agents.agent_messenger import AgentMessenger
        from rpa.agents.agent_registry import AgentRegistry
        from rpa.agents.base_agent import BaseAgent

        registry = AgentRegistry()
        agent1 = BaseAgent(domain="domain1")
        agent2 = BaseAgent(domain="domain2")

        registry.register_agent(agent1)
        registry.register_agent(agent2)

        messenger = AgentMessenger(registry=registry)
        msg_id, result = messenger.send_teaching(
            from_agent_id=agent1.agent_id,
            to_agent_id=agent2.agent_id,
            lesson={"content": "new knowledge", "label": "test"},
        )

        assert msg_id is not None
        assert result is not None
        assert result["success"] is True

    def test_broadcast_inquiry(self):
        """Test broadcasting an inquiry."""
        from rpa.agents.agent_messenger import AgentMessenger
        from rpa.agents.agent_registry import AgentRegistry
        from rpa.agents.base_agent import BaseAgent

        registry = AgentRegistry()
        agent1 = BaseAgent(domain="domain1")
        agent2 = BaseAgent(domain="domain2")

        registry.register_agent(agent1)
        registry.register_agent(agent2)

        messenger = AgentMessenger(registry=registry)
        results = messenger.broadcast_inquiry(
            inquiry="What do you know?",
            domains=["domain1", "domain2"],
        )

        assert len(results) == 2

    def test_coordinate_task(self):
        """Test coordinating a task."""
        from rpa.agents.agent_messenger import AgentMessenger
        from rpa.agents.agent_registry import AgentRegistry
        from rpa.agents.base_agent import BaseAgent

        registry = AgentRegistry()
        agent1 = BaseAgent(domain="domain1")
        agent2 = BaseAgent(domain="domain2")

        registry.register_agent(agent1)
        registry.register_agent(agent2)

        messenger = AgentMessenger(registry=registry)
        result = messenger.coordinate_task(
            task="Test coordination",
            agent_ids=[agent1.agent_id, agent2.agent_id],
        )

        assert result["agent_count"] == 2
        assert "responses" in result

    def test_get_message(self):
        """Test getting a message by ID."""
        from rpa.agents.agent_messenger import AgentMessenger
        from rpa.agents.agent_registry import AgentRegistry
        from rpa.agents.base_agent import BaseAgent

        registry = AgentRegistry()
        agent1 = BaseAgent(domain="domain1")
        agent2 = BaseAgent(domain="domain2")

        registry.register_agent(agent1)
        registry.register_agent(agent2)

        messenger = AgentMessenger(registry=registry)
        msg_id, _ = messenger.send_query(
            from_agent_id=agent1.agent_id,
            to_agent_id=agent2.agent_id,
            query="test",
        )

        message = messenger.get_message(msg_id)
        assert message is not None
        assert message.message_id == msg_id

    def test_get_stats(self):
        """Test getting messenger stats."""
        from rpa.agents.agent_messenger import AgentMessenger
        from rpa.agents.agent_registry import AgentRegistry
        from rpa.agents.base_agent import BaseAgent

        registry = AgentRegistry()
        agent1 = BaseAgent(domain="domain1")
        agent2 = BaseAgent(domain="domain2")

        registry.register_agent(agent1)
        registry.register_agent(agent2)

        messenger = AgentMessenger(registry=registry)
        messenger.send_query(agent1.agent_id, agent2.agent_id, "test")

        stats = messenger.get_stats()
        assert stats["total_messages"] >= 1


# =============================================================================
# Integration Tests
# =============================================================================

class TestPhase5Integration:
    """Integration tests for Phase 5 components."""

    def test_full_agent_workflow(self):
        """Test full agent workflow."""
        from rpa.agents.coding_agent import CodingAgent
        from rpa.agents.agent_registry import AgentRegistry
        from rpa.agents.orchestrator import Orchestrator

        # Create agents
        coder = CodingAgent(language="python")

        # Register
        registry = AgentRegistry()
        registry.register_agent(coder)

        # Create task
        orchestrator = Orchestrator(registry=registry)
        task = orchestrator.create_task(
            description="Generate a for loop",
            task_type="code",
        )

        # Decompose and check
        subtasks = orchestrator.decompose_task(task)
        assert len(subtasks) >= 1

    def test_multi_agent_collaboration(self):
        """Test multi-agent collaboration."""
        from rpa.agents.coding_agent import CodingAgent
        from rpa.agents.language_agent import LanguageAgent
        from rpa.agents.agent_registry import AgentRegistry
        from rpa.agents.agent_messenger import AgentMessenger

        # Create agents
        coder = CodingAgent()
        linguist = LanguageAgent()

        # Register
        registry = AgentRegistry()
        registry.register_agent(coder)
        registry.register_agent(linguist)

        # Communication
        messenger = AgentMessenger(registry=registry)

        # Send teaching from language agent to coding agent
        msg_id, result = messenger.send_teaching(
            from_agent_id=linguist.agent_id,
            to_agent_id=coder.agent_id,
            lesson={"content": "if means conditional", "label": "if_concept"},
        )

        assert result["success"] is True

    def test_knowledge_sharing_workflow(self):
        """Test knowledge sharing workflow."""
        from rpa.agents.base_agent import BaseAgent
        from rpa.agents.shared_knowledge import SharedKnowledge

        # Create agents
        agent1 = BaseAgent(domain="domain1")
        agent2 = BaseAgent(domain="domain2")

        # Teach agent1
        result = agent1.teach({"content": "shared concept", "label": "concept"})
        pattern_id = result["pattern_id"]

        # Share knowledge
        sk = SharedKnowledge()
        share_result = sk.share_pattern(
            pattern_id=pattern_id,
            from_agent=agent1,
            to_agents=[agent2],
        )

        assert share_result["success_count"] == 1

        # Create cross-domain link
        link = sk.link_cross_domain_patterns(
            pattern_id_1=pattern_id,
            agent_id_1=agent1.agent_id,
            pattern_id_2="equivalent_concept",
            agent_id_2=agent2.agent_id,
            link_type="equivalent",
        )

        assert link.link_id is not None
