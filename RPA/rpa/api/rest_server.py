"""
REST API Server - HTTP endpoints for RPA.

Provides RESTful endpoints for:
- Pattern management (CRUD)
- Assessment
- Inquiry handling
- System status

Uses Flask for HTTP handling (with fallback to simple HTTP server).
"""

from typing import Dict, Any, Optional, List
import json
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading

from .agent_interface import AgentInterface

logger = logging.getLogger(__name__)

# Try to import Flask, fall back to basic HTTP if not available
try:
    from flask import Flask, request, jsonify
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    Flask = None


def create_flask_app(interface: AgentInterface) -> "Flask":
    """
    Create a Flask application for the RPA API.

    Args:
        interface: AgentInterface instance

    Returns:
        Flask application
    """
    if not FLASK_AVAILABLE:
        raise ImportError("Flask is not installed. Install with: pip install flask")

    app = Flask("rpa_api")

    @app.route("/health", methods=["GET"])
    def health():
        """Health check endpoint."""
        return jsonify({"status": "healthy", "service": "rpa_api"})

    @app.route("/pattern/<label>", methods=["GET"])
    def get_pattern(label: str):
        """Query a pattern by label."""
        domain = request.args.get("domain")
        result = interface.query_pattern(label, domain)
        return jsonify(result.to_dict())

    @app.route("/pattern", methods=["POST"])
    def create_pattern():
        """Teach a new pattern."""
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        content = data.get("content")
        domain = data.get("domain")

        if not content or not domain:
            return jsonify({"error": "content and domain are required"}), 400

        result = interface.teach_pattern(
            content=content,
            domain=domain,
            hierarchy_level=data.get("hierarchy_level", 1),
            composition=data.get("composition")
        )

        status_code = 201 if result.success else 400
        return jsonify(result.to_dict()), status_code

    @app.route("/pattern/<label>/assess", methods=["GET"])
    def assess_pattern(label: str):
        """Assess a pattern."""
        domain = request.args.get("domain")
        result = interface.assess_pattern(label, domain)
        return jsonify(result.to_dict())

    @app.route("/pattern/search", methods=["GET"])
    def search_patterns():
        """Search for patterns."""
        query = request.args.get("q", "")
        domain = request.args.get("domain")
        limit = request.args.get("limit", 10, type=int)

        results = interface.search_patterns(query, domain, limit)
        return jsonify({"results": results, "count": len(results)})

    @app.route("/pattern/batch", methods=["POST"])
    def batch_teach():
        """Teach multiple patterns at once."""
        data = request.get_json()
        if not data or "patterns" not in data:
            return jsonify({"error": "patterns array is required"}), 400

        results = interface.batch_teach(data["patterns"])
        successes = sum(1 for r in results if r.success)
        return jsonify({
            "total": len(results),
            "successful": successes,
            "failed": len(results) - successes,
            "results": [r.to_dict() for r in results]
        })

    @app.route("/inquiries", methods=["GET"])
    def get_inquiries():
        """Get pending inquiries."""
        domain = request.args.get("domain")
        inquiries = interface.get_inquiries(domain)
        return jsonify({"inquiries": inquiries, "count": len(inquiries)})

    @app.route("/inquiries/<inquiry_id>/answer", methods=["POST"])
    def answer_inquiry(inquiry_id: str):
        """Answer an inquiry."""
        data = request.get_json()
        if not data or "response" not in data:
            return jsonify({"error": "response is required"}), 400

        result = interface.answer_inquiry(inquiry_id, data["response"])
        return jsonify(result)

    @app.route("/status/curriculum", methods=["GET"])
    def curriculum_status():
        """Get curriculum status."""
        status = interface.get_curriculum_status()
        return jsonify(status)

    @app.route("/status/memory", methods=["GET"])
    def memory_status():
        """Get memory status."""
        status = interface.get_memory_status()
        return jsonify(status.to_dict())

    @app.route("/knowledge/export", methods=["GET"])
    def export_knowledge():
        """Export all knowledge."""
        domain = request.args.get("domain")
        knowledge = interface.export_knowledge(domain)
        return jsonify(knowledge)

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Internal server error"}), 500

    return app


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    """Simple HTTP request handler for basic API without Flask."""

    interface: AgentInterface = None

    def log_message(self, format, *args):
        """Override to use our logger."""
        logger.info(format, *args)

    def _send_json_response(self, data: Dict[str, Any], status: int = 200):
        """Send a JSON response."""
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def _parse_path(self) -> tuple:
        """Parse the request path and query string."""
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        return path, query

    def do_GET(self):
        """Handle GET requests."""
        path, query = self._parse_path()

        # Health check
        if path == "/health":
            self._send_json_response({"status": "healthy", "service": "rpa_api"})
            return

        # Get pattern
        if path.startswith("/pattern/") and not path.endswith("/assess"):
            label = path.split("/pattern/")[1].split("/")[0]
            domain = query.get("domain", [None])[0]
            result = self.interface.query_pattern(label, domain)
            self._send_json_response(result.to_dict())
            return

        # Assess pattern
        if path.endswith("/assess"):
            label = path.split("/pattern/")[1].split("/assess")[0]
            domain = query.get("domain", [None])[0]
            result = self.interface.assess_pattern(label, domain)
            self._send_json_response(result.to_dict())
            return

        # Search patterns
        if path == "/pattern/search":
            search_query = query.get("q", [""])[0]
            domain = query.get("domain", [None])[0]
            limit = int(query.get("limit", [10])[0])
            results = self.interface.search_patterns(search_query, domain, limit)
            self._send_json_response({"results": results, "count": len(results)})
            return

        # Get inquiries
        if path == "/inquiries":
            domain = query.get("domain", [None])[0]
            inquiries = self.interface.get_inquiries(domain)
            self._send_json_response({"inquiries": inquiries, "count": len(inquiries)})
            return

        # Curriculum status
        if path == "/status/curriculum":
            status = self.interface.get_curriculum_status()
            self._send_json_response(status)
            return

        # Memory status
        if path == "/status/memory":
            status = self.interface.get_memory_status()
            self._send_json_response(status.to_dict())
            return

        # Export knowledge
        if path == "/knowledge/export":
            domain = query.get("domain", [None])[0]
            knowledge = self.interface.export_knowledge(domain)
            self._send_json_response(knowledge)
            return

        # Not found
        self._send_json_response({"error": "Not found"}, 404)

    def do_POST(self):
        """Handle POST requests."""
        path, query = self._parse_path()

        # Read request body
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")

        try:
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            self._send_json_response({"error": "Invalid JSON"}, 400)
            return

        # Create pattern
        if path == "/pattern":
            content = data.get("content")
            domain = data.get("domain")

            if not content or not domain:
                self._send_json_response({"error": "content and domain are required"}, 400)
                return

            result = self.interface.teach_pattern(
                content=content,
                domain=domain,
                hierarchy_level=data.get("hierarchy_level", 1),
                composition=data.get("composition")
            )

            status = 201 if result.success else 400
            self._send_json_response(result.to_dict(), status)
            return

        # Batch teach
        if path == "/pattern/batch":
            if "patterns" not in data:
                self._send_json_response({"error": "patterns array is required"}, 400)
                return

            results = self.interface.batch_teach(data["patterns"])
            successes = sum(1 for r in results if r.success)
            self._send_json_response({
                "total": len(results),
                "successful": successes,
                "failed": len(results) - successes,
                "results": [r.to_dict() for r in results]
            })
            return

        # Answer inquiry
        if "/inquiries/" in path and "/answer" in path:
            inquiry_id = path.split("/inquiries/")[1].split("/answer")[0]

            if "response" not in data:
                self._send_json_response({"error": "response is required"}, 400)
                return

            result = self.interface.answer_inquiry(inquiry_id, data["response"])
            self._send_json_response(result)
            return

        # Not found
        self._send_json_response({"error": "Not found"}, 404)


def run_server(
    interface: AgentInterface,
    host: str = "0.0.0.0",
    port: int = 8000,
    use_flask: bool = True
) -> None:
    """
    Run the RPA API server.

    Args:
        interface: AgentInterface instance
        host: Host to bind to
        port: Port to listen on
        use_flask: Whether to use Flask (falls back to basic HTTP if not available)
    """
    if use_flask and FLASK_AVAILABLE:
        app = create_flask_app(interface)
        logger.info(f"Starting Flask server on {host}:{port}")
        app.run(host=host, port=port)
    else:
        # Use basic HTTP server
        SimpleHTTPRequestHandler.interface = interface
        server = HTTPServer((host, port), SimpleHTTPRequestHandler)
        logger.info(f"Starting HTTP server on {host}:{port}")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            logger.info("Server stopped")
            server.shutdown()


def run_server_threaded(
    interface: AgentInterface,
    host: str = "0.0.0.0",
    port: int = 8000
) -> threading.Thread:
    """
    Run the API server in a background thread.

    Args:
        interface: AgentInterface instance
        host: Host to bind to
        port: Port to listen on

    Returns:
        Thread running the server
    """
    thread = threading.Thread(
        target=run_server,
        args=(interface, host, port, True),
        daemon=True
    )
    thread.start()
    return thread
