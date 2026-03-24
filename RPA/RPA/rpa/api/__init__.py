"""
API module - REST and WebSocket interfaces.

This module provides:
- AgentInterface: API for external agent integration
- REST server: HTTP endpoints
- WebSocket server: Real-time communication
"""

from .agent_interface import (
    AgentInterface,
    PatternQueryResult,
    TeachingResult,
    AssessmentResult,
    MemoryStatus
)
from .rest_server import (
    create_flask_app,
    run_server,
    run_server_threaded,
    SimpleHTTPRequestHandler,
    FLASK_AVAILABLE
)
from .websocket_server import (
    WebSocketServer,
    WebSocketClient,
    MockWebSocketServer,
    create_websocket_server,
    run_websocket_server,
    run_websocket_server_threaded,
    WEBSOCKETS_AVAILABLE
)

__all__ = [
    # Agent Interface
    "AgentInterface",
    "PatternQueryResult",
    "TeachingResult",
    "AssessmentResult",
    "MemoryStatus",

    # REST Server
    "create_flask_app",
    "run_server",
    "run_server_threaded",
    "SimpleHTTPRequestHandler",
    "FLASK_AVAILABLE",

    # WebSocket Server
    "WebSocketServer",
    "WebSocketClient",
    "MockWebSocketServer",
    "create_websocket_server",
    "run_websocket_server",
    "run_websocket_server_threaded",
    "WEBSOCKETS_AVAILABLE",
]
