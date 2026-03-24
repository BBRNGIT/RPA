"""
WebSocket Server - Real-time communication for RPA.

Provides WebSocket endpoints for:
- Real-time pattern updates
- Streaming responses
- Event subscriptions
- Interactive sessions

Uses websockets library (with fallback to simple implementation).
"""

from typing import Dict, Any, Optional, List, Callable, Set
import json
import logging
import asyncio
import threading
from dataclasses import dataclass, field
from datetime import datetime
import uuid

from .agent_interface import AgentInterface

logger = logging.getLogger(__name__)

# Try to import websockets
try:
    import websockets
    from websockets.server import serve
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    websockets = None
    serve = None


@dataclass
class WebSocketClient:
    """Represents a connected WebSocket client."""
    client_id: str
    websocket: Any = None
    subscriptions: Set[str] = field(default_factory=set)
    connected_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "client_id": self.client_id,
            "subscriptions": list(self.subscriptions),
            "connected_at": self.connected_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
        }


class WebSocketServer:
    """
    WebSocket server for real-time RPA communication.

    Provides:
    - Real-time pattern updates
    - Event subscriptions
    - Interactive sessions
    - Streaming responses
    """

    def __init__(self, interface: AgentInterface):
        """
        Initialize the WebSocket server.

        Args:
            interface: AgentInterface instance
        """
        self.interface = interface
        self.clients: Dict[str, WebSocketClient] = {}
        self.event_handlers: Dict[str, List[Callable]] = {}
        self.server = None
        self.loop = None
        self._running = False

    async def handle_connection(self, websocket, path: str = ""):
        """
        Handle a WebSocket connection.

        Args:
            websocket: WebSocket connection
            path: Connection path
        """
        client_id = str(uuid.uuid4())[:8]
        client = WebSocketClient(client_id=client_id, websocket=websocket)
        self.clients[client_id] = client

        logger.info(f"Client {client_id} connected")

        try:
            # Send welcome message
            await self._send_message(websocket, {
                "type": "connected",
                "client_id": client_id,
                "message": "Welcome to RPA WebSocket API"
            })

            # Handle incoming messages
            async for message in websocket:
                client.last_activity = datetime.now()
                await self._handle_message(client, message)

        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client {client_id} disconnected")
        except Exception as e:
            logger.error(f"Error handling client {client_id}: {e}")
        finally:
            del self.clients[client_id]
            await self._emit_event("client_disconnected", {"client_id": client_id})

    async def _handle_message(self, client: WebSocketClient, message: str):
        """
        Handle an incoming WebSocket message.

        Args:
            client: WebSocket client
            message: Raw message string
        """
        try:
            data = json.loads(message)
            action = data.get("action")
            payload = data.get("data", {})

            handlers = {
                "ping": self._handle_ping,
                "query_pattern": self._handle_query_pattern,
                "teach_pattern": self._handle_teach_pattern,
                "assess_pattern": self._handle_assess_pattern,
                "search_patterns": self._handle_search_patterns,
                "get_inquiries": self._handle_get_inquiries,
                "answer_inquiry": self._handle_answer_inquiry,
                "get_status": self._handle_get_status,
                "subscribe": self._handle_subscribe,
                "unsubscribe": self._handle_unsubscribe,
                "batch_teach": self._handle_batch_teach,
                "export_knowledge": self._handle_export_knowledge,
            }

            handler = handlers.get(action)
            if handler:
                response = await handler(client, payload)
                response["request_id"] = data.get("request_id")
                await self._send_message(client.websocket, response)
            else:
                await self._send_message(client.websocket, {
                    "type": "error",
                    "message": f"Unknown action: {action}"
                })

        except json.JSONDecodeError:
            await self._send_message(client.websocket, {
                "type": "error",
                "message": "Invalid JSON message"
            })
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            await self._send_message(client.websocket, {
                "type": "error",
                "message": str(e)
            })

    async def _send_message(self, websocket, data: Dict[str, Any]):
        """Send a message to a WebSocket client."""
        if websocket:
            await websocket.send(json.dumps(data))

    async def _broadcast(self, data: Dict[str, Any], subscription: str = None):
        """Broadcast a message to all subscribed clients."""
        message = json.dumps(data)
        for client in self.clients.values():
            if subscription is None or subscription in client.subscriptions:
                try:
                    await client.websocket.send(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to client: {e}")

    async def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit an event to subscribed clients."""
        handlers = self.event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                await handler(data)
            except Exception as e:
                logger.error(f"Error in event handler: {e}")

        await self._broadcast({
            "type": "event",
            "event_type": event_type,
            "data": data
        }, subscription=event_type)

    # Message handlers

    async def _handle_ping(self, client: WebSocketClient, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle ping message."""
        return {"type": "pong", "timestamp": datetime.now().isoformat()}

    async def _handle_query_pattern(self, client: WebSocketClient, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle pattern query."""
        label = data.get("label")
        domain = data.get("domain")
        result = self.interface.query_pattern(label, domain)
        return {"type": "query_result", "data": result.to_dict()}

    async def _handle_teach_pattern(self, client: WebSocketClient, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle pattern teaching."""
        result = self.interface.teach_pattern(
            content=data.get("content"),
            domain=data.get("domain"),
            hierarchy_level=data.get("hierarchy_level", 1),
            composition=data.get("composition")
        )

        # Emit event for subscribers
        if result.success:
            await self._emit_event("pattern_created", {
                "label": result.label,
                "domain": data.get("domain")
            })

        return {"type": "teach_result", "data": result.to_dict()}

    async def _handle_assess_pattern(self, client: WebSocketClient, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle pattern assessment."""
        label = data.get("label")
        domain = data.get("domain")
        result = self.interface.assess_pattern(label, domain)
        return {"type": "assess_result", "data": result.to_dict()}

    async def _handle_search_patterns(self, client: WebSocketClient, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle pattern search."""
        query = data.get("query", "")
        domain = data.get("domain")
        limit = data.get("limit", 10)
        results = self.interface.search_patterns(query, domain, limit)
        return {"type": "search_result", "data": {"results": results, "count": len(results)}}

    async def _handle_get_inquiries(self, client: WebSocketClient, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get inquiries."""
        domain = data.get("domain")
        inquiries = self.interface.get_inquiries(domain)
        return {"type": "inquiries", "data": {"inquiries": inquiries, "count": len(inquiries)}}

    async def _handle_answer_inquiry(self, client: WebSocketClient, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle inquiry answer."""
        inquiry_id = data.get("inquiry_id")
        response = data.get("response")
        result = self.interface.answer_inquiry(inquiry_id, response)

        await self._emit_event("inquiry_answered", {
            "inquiry_id": inquiry_id
        })

        return {"type": "answer_result", "data": result}

    async def _handle_get_status(self, client: WebSocketClient, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle status request."""
        status_type = data.get("type", "memory")

        if status_type == "memory":
            status = self.interface.get_memory_status()
            return {"type": "status", "data": status.to_dict()}
        elif status_type == "curriculum":
            status = self.interface.get_curriculum_status()
            return {"type": "status", "data": status}
        else:
            return {"type": "error", "message": f"Unknown status type: {status_type}"}

    async def _handle_subscribe(self, client: WebSocketClient, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription request."""
        events = data.get("events", [])
        for event in events:
            client.subscriptions.add(event)

        return {
            "type": "subscribed",
            "data": {
                "subscriptions": list(client.subscriptions)
            }
        }

    async def _handle_unsubscribe(self, client: WebSocketClient, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle unsubscription request."""
        events = data.get("events", [])
        for event in events:
            client.subscriptions.discard(event)

        return {
            "type": "unsubscribed",
            "data": {
                "subscriptions": list(client.subscriptions)
            }
        }

    async def _handle_batch_teach(self, client: WebSocketClient, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle batch teaching."""
        patterns = data.get("patterns", [])
        results = self.interface.batch_teach(patterns)
        successes = sum(1 for r in results if r.success)

        # Emit event
        await self._emit_event("batch_teach_completed", {
            "total": len(results),
            "successful": successes
        })

        return {
            "type": "batch_result",
            "data": {
                "total": len(results),
                "successful": successes,
                "failed": len(results) - successes,
                "results": [r.to_dict() for r in results]
            }
        }

    async def _handle_export_knowledge(self, client: WebSocketClient, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle knowledge export."""
        domain = data.get("domain")
        knowledge = self.interface.export_knowledge(domain)
        return {"type": "knowledge_export", "data": knowledge}

    # Server control

    def on_event(self, event_type: str, handler: Callable):
        """
        Register an event handler.

        Args:
            event_type: Type of event to handle
            handler: Async function to handle the event
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)

    def get_clients(self) -> List[Dict[str, Any]]:
        """Get list of connected clients."""
        return [client.to_dict() for client in self.clients.values()]

    async def start_async(self, host: str = "0.0.0.0", port: int = 8765):
        """
        Start the WebSocket server (async).

        Args:
            host: Host to bind to
            port: Port to listen on
        """
        if not WEBSOCKETS_AVAILABLE:
            raise ImportError("websockets library not installed. Install with: pip install websockets")

        self._running = True
        logger.info(f"Starting WebSocket server on {host}:{port}")

        async with serve(self.handle_connection, host, port):
            await asyncio.Future()  # Run forever

    def start(self, host: str = "0.0.0.0", port: int = 8765):
        """
        Start the WebSocket server (blocking).

        Args:
            host: Host to bind to
            port: Port to listen on
        """
        asyncio.run(self.start_async(host, port))

    def start_threaded(self, host: str = "0.0.0.0", port: int = 8765) -> threading.Thread:
        """
        Start the WebSocket server in a background thread.

        Args:
            host: Host to bind to
            port: Port to listen on

        Returns:
            Thread running the server
        """
        thread = threading.Thread(
            target=self.start,
            args=(host, port),
            daemon=True
        )
        thread.start()
        return thread

    def stop(self):
        """Stop the WebSocket server."""
        self._running = False
        if self.loop:
            self.loop.stop()


class MockWebSocketServer:
    """
    Mock WebSocket server for testing without websockets library.
    """

    def __init__(self, interface: AgentInterface):
        """Initialize mock server."""
        self.interface = interface
        self.clients = {}
        self.event_handlers = {}

    def on_event(self, event_type: str, handler: Callable):
        """Register an event handler."""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)

    def get_clients(self) -> List[Dict[str, Any]]:
        """Get list of connected clients."""
        return []

    def start(self, host: str = "0.0.0.0", port: int = 8765):
        """Start the mock server (no-op)."""
        logger.info(f"Mock WebSocket server would start on {host}:{port}")

    def start_threaded(self, host: str = "0.0.0.0", port: int = 8765) -> threading.Thread:
        """Start the mock server in a background thread."""
        thread = threading.Thread(target=self.start, args=(host, port), daemon=True)
        thread.start()
        return thread

    def stop(self):
        """Stop the mock server."""
        pass


def create_websocket_server(interface: AgentInterface):
    """
    Create a WebSocket server instance.

    Args:
        interface: AgentInterface instance

    Returns:
        WebSocketServer or MockWebSocketServer
    """
    if WEBSOCKETS_AVAILABLE:
        return WebSocketServer(interface)
    else:
        logger.warning("websockets library not available, using mock server")
        return MockWebSocketServer(interface)


def run_websocket_server(
    interface: AgentInterface,
    host: str = "0.0.0.0",
    port: int = 8765
) -> None:
    """
    Run the WebSocket server.

    Args:
        interface: AgentInterface instance
        host: Host to bind to
        port: Port to listen on
    """
    server = create_websocket_server(interface)
    server.start(host, port)


def run_websocket_server_threaded(
    interface: AgentInterface,
    host: str = "0.0.0.0",
    port: int = 8765
) -> threading.Thread:
    """
    Run the WebSocket server in a background thread.

    Args:
        interface: AgentInterface instance
        host: Host to bind to
        port: Port to listen on

    Returns:
        Thread running the server
    """
    server = create_websocket_server(interface)
    return server.start_threaded(host, port)
