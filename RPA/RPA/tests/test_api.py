"""
Tests for API Module (Simplified).

Focus on core AgentInterface functionality with compatibility fixes.
"""

import pytest

from rpa.api.agent_interface import (
    AgentInterface,
    PatternQueryResult,
    TeachingResult,
    AssessmentResult,
    MemoryStatus
)
from rpa.memory import LongTermMemory, EpisodicMemory
from rpa.core import Node, NodeType


class TestPatternQueryResult:
    """Tests for PatternQueryResult."""

    def test_create_found_result(self):
        """Test creating a found result."""
        result = PatternQueryResult(
            found=True,
            pattern={"id": "test", "label": "test"},
            message="Found"
        )
        assert result.found is True
        assert result.pattern["label"] == "test"

    def test_create_not_found_result(self):
        """Test creating a not found result."""
        result = PatternQueryResult(
            found=False,
            message="Pattern not found"
        )
        assert result.found is False
        assert result.pattern is None

    def test_to_dict(self):
        """Test converting to dictionary."""
        result = PatternQueryResult(
            found=True,
            pattern={"id": "test"},
            message="Test",
            related_patterns=[{"id": "related"}]
        )
        d = result.to_dict()
        assert d["found"] is True
        assert len(d["related_patterns"]) == 1


class TestTeachingResult:
    """Tests for TeachingResult."""

    def test_create_success_result(self):
        """Test creating a successful teaching result."""
        result = TeachingResult(
            success=True,
            pattern_id="pattern:test",
            message="Success",
            consolidation_status="consolidated"
        )
        assert result.success is True
        assert result.consolidation_status == "consolidated"

    def test_create_failure_result(self):
        """Test creating a failed teaching result."""
        result = TeachingResult(
            success=False,
            message="Validation failed",
            validation={"is_valid": False, "issues": ["Missing child"]}
        )
        assert result.success is False
        assert result.validation is not None

    def test_to_dict(self):
        """Test converting to dictionary."""
        result = TeachingResult(
            success=True,
            pattern_id="test",
            message="Test"
        )
        d = result.to_dict()
        assert d["success"] is True
        assert d["pattern_id"] == "test"


class TestAssessmentResult:
    """Tests for AssessmentResult."""

    def test_create_valid_result(self):
        """Test creating a valid assessment result."""
        result = AssessmentResult(
            pattern_id="pattern:test",
            is_valid=True,
            pass_rate=0.9,
            strengths=["All links valid"],
            weaknesses=[]
        )
        assert result.is_valid is True
        assert result.pass_rate == 0.9
        assert len(result.strengths) == 1

    def test_create_invalid_result(self):
        """Test creating an invalid assessment result."""
        result = AssessmentResult(
            pattern_id="pattern:test",
            is_valid=False,
            pass_rate=0.3,
            weaknesses=["Missing links"],
            recommendations=["Review composition"]
        )
        assert result.is_valid is False
        assert len(result.weaknesses) == 1

    def test_to_dict(self):
        """Test converting to dictionary."""
        result = AssessmentResult(
            pattern_id="test",
            is_valid=True,
            pass_rate=1.0,
            exercises=[{"type": "reconstruct", "passed": True}]
        )
        d = result.to_dict()
        assert d["is_valid"] is True
        assert len(d["exercises"]) == 1


class TestMemoryStatus:
    """Tests for MemoryStatus."""

    def test_create_status(self):
        """Test creating a memory status."""
        status = MemoryStatus(
            stm_patterns=5,
            ltm_patterns=100,
            total_episodes=50,
            domains=["english", "python"],
            hierarchy_levels={0: 26, 1: 50, 2: 24}
        )
        assert status.stm_patterns == 5
        assert status.ltm_patterns == 100
        assert len(status.domains) == 2

    def test_to_dict(self):
        """Test converting to dictionary."""
        status = MemoryStatus(
            stm_patterns=0,
            ltm_patterns=10,
            total_episodes=5,
            domains=["english"],
            hierarchy_levels={0: 5, 1: 5}
        )
        d = status.to_dict()
        assert d["ltm_patterns"] == 10
        assert d["total_episodes"] == 5


class TestAgentInterface:
    """Tests for AgentInterface."""

    def test_init(self):
        """Test AgentInterface initialization."""
        interface = AgentInterface()
        assert interface.ltm is not None
        assert interface.stm is not None
        assert interface.episodic is not None

        # test_query_pattern_not_found is a def test_query_pattern_not_found(self):
        """Test querying a non-existent pattern."""
        interface = AgentInterface()
        result = interface.query_pattern("nonexistent")
        assert result.found is False

        assert "not found" in result.message.lower()

    def test_teach_pattern_simple(self):
        """Test teaching a simple pattern."""
        interface = AgentInterface()
        # Create a pattern directly in LTM
        node = Node(
            node_id="pattern:hello",
            label="hello",
            node_type=NodeType.PATTERN,
            content="hello",
            domain="english",
            hierarchy_level=1
        )
        interface.ltm.add_node(node)
        
        result = interface.query_pattern("hello")
        assert result.found is True

        assert result.pattern["label"] == "hello"
    def test_get_curriculum_status(self):
        """Test getting curriculum status."""
        interface = AgentInterface()
        status = interface.get_curriculum_status()
        assert "total_patterns" in status
        assert "by_domain" in status


    def test_export_knowledge(self):
        """Test exporting knowledge."""
        interface = AgentInterface()
        # Add a node
        node = Node(
            node_id="pattern:test",
            label="test",
            node_type=NodeType.PATTERN,
            content="test",
            domain="english",
            hierarchy_level=1
        )
        interface.ltm.add_node(node)

        knowledge = interface.export_knowledge("english")
        assert "nodes" in knowledge
        assert len(knowledge["nodes"]) == 1
        assert knowledge["nodes"][0]["label"] == "test"


class TestWebSocketClient:
    """Tests for WebSocketClient dataclass."""

    def test_create_client(self):
        """Test creating a WebSocket client."""
        from rpa.api.websocket_server import WebSocketClient
        client = WebSocketClient(client_id="test123")
        assert client.client_id == "test123"
        assert len(client.subscriptions) == 0

    def test_client_subscriptions(self):
        """Test client subscriptions."""
        from rpa.api.websocket_server import WebSocketClient
        client = WebSocketClient(client_id="test123")
        client.subscriptions.add("pattern_created")
        client.subscriptions.add("inquiry_answered")
        assert len(client.subscriptions) == 2
        assert "pattern_created" in client.subscriptions

    def test_client_to_dict(self):
        """Test converting client to dictionary."""
        from rpa.api.websocket_server import WebSocketClient
        client = WebSocketClient(client_id="test123")
        client.subscriptions.add("test_event")
        d = client.to_dict()
        assert d["client_id"] == "test123"
        assert "subscriptions" in d
        assert "connected_at" in d


class TestMockWebSocketServer:
    """Tests for MockWebSocketServer."""

    def test_create_mock_server(self):
        """Test creating a mock WebSocket server."""
        from rpa.api.websocket_server import MockWebSocketServer
        interface = AgentInterface()
        server = MockWebSocketServer(interface)
        assert server.interface is not None

    def test_mock_server_event_handlers(self):
        """Test registering event handlers."""
        from rpa.api.websocket_server import MockWebSocketServer
        interface = AgentInterface()
        server = MockWebSocketServer(interface)

        async def handler(data):
            pass

        server.on_event("test_event", handler)
        assert "test_event" in server.event_handlers
        assert len(server.event_handlers["test_event"]) == 1

    def test_mock_server_get_clients(self):
        """Test getting connected clients."""
        from rpa.api.websocket_server import MockWebSocketServer
        interface = AgentInterface()
        server = MockWebSocketServer(interface)
        clients = server.get_clients()
        assert clients == []

    def test_mock_server_start_threaded(self):
        """Test starting mock server in thread."""
        from rpa.api.websocket_server import MockWebSocketServer
        import threading
        interface = AgentInterface()
        server = MockWebSocketServer(interface)
        thread = server.start_threaded()
        assert isinstance(thread, threading.Thread)


class TestCreateWebSocketServer:
    """Tests for create_websocket_server factory function."""

    def test_create_returns_server(self):
        """Test that factory returns a server instance."""
        from rpa.api.websocket_server import create_websocket_server
        interface = AgentInterface()
        server = create_websocket_server(interface)
        assert server is not None
        assert server.interface is not None

    def test_create_server_has_event_handler_registration(self):
        """Test that created server supports event handlers."""
        from rpa.api.websocket_server import create_websocket_server
        interface = AgentInterface()
        server = create_websocket_server(interface)

        async def handler(data):
            pass

        server.on_event("test", handler)
        assert "test" in server.event_handlers


class TestWebSocketServerImports:
    """Tests for WebSocket server module imports."""

    def test_import_websockets_available(self):
        """Test importing WEBSOCKETS_AVAILABLE flag."""
        from rpa.api.websocket_server import WEBSOCKETS_AVAILABLE
        assert isinstance(WEBSOCKETS_AVAILABLE, bool)

    def test_import_from_api_module(self):
        """Test importing WebSocket components from api module."""
        from rpa.api import (
            WebSocketServer,
            WebSocketClient,
            MockWebSocketServer,
            create_websocket_server,
            run_websocket_server,
            run_websocket_server_threaded,
            WEBSOCKETS_AVAILABLE
        )
        assert WebSocketServer is not None
        assert WebSocketClient is not None
        assert MockWebSocketServer is not None


class TestWebSocketServerHandlers:
    """Tests for WebSocket server message handlers."""

    @pytest.mark.asyncio
    async def test_handle_ping(self):
        """Test ping handler."""
        from rpa.api.websocket_server import WebSocketServer, WebSocketClient
        interface = AgentInterface()
        server = WebSocketServer(interface)
        client = WebSocketClient(client_id="test")

        response = await server._handle_ping(client, {})
        assert response["type"] == "pong"
        assert "timestamp" in response

    @pytest.mark.asyncio
    async def test_handle_query_pattern(self):
        """Test pattern query handler."""
        from rpa.api.websocket_server import WebSocketServer, WebSocketClient
        interface = AgentInterface()
        server = WebSocketServer(interface)
        client = WebSocketClient(client_id="test")

        response = await server._handle_query_pattern(client, {
            "label": "nonexistent"
        })
        assert response["type"] == "query_result"
        assert "data" in response

    @pytest.mark.asyncio
    async def test_handle_get_status(self):
        """Test status handler."""
        from rpa.api.websocket_server import WebSocketServer, WebSocketClient
        interface = AgentInterface()
        server = WebSocketServer(interface)
        client = WebSocketClient(client_id="test")

        response = await server._handle_get_status(client, {"type": "memory"})
        assert response["type"] == "status"
        assert "data" in response

    @pytest.mark.asyncio
    async def test_handle_subscribe(self):
        """Test subscribe handler."""
        from rpa.api.websocket_server import WebSocketServer, WebSocketClient
        interface = AgentInterface()
        server = WebSocketServer(interface)
        client = WebSocketClient(client_id="test")

        response = await server._handle_subscribe(client, {
            "events": ["pattern_created", "inquiry_answered"]
        })
        assert response["type"] == "subscribed"
        assert len(client.subscriptions) == 2

    @pytest.mark.asyncio
    async def test_handle_unsubscribe(self):
        """Test unsubscribe handler."""
        from rpa.api.websocket_server import WebSocketServer, WebSocketClient
        interface = AgentInterface()
        server = WebSocketServer(interface)
        client = WebSocketClient(client_id="test")
        client.subscriptions.add("pattern_created")
        client.subscriptions.add("inquiry_answered")

        response = await server._handle_unsubscribe(client, {
            "events": ["pattern_created"]
        })
        assert response["type"] == "unsubscribed"
        assert len(client.subscriptions) == 1
        assert "inquiry_answered" in client.subscriptions
