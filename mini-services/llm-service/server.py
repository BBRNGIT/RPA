#!/usr/bin/env python3
"""
RPA Neural LLM Service

This service loads the trained neural LLM and provides an HTTP API
for text generation and chat interactions.
"""

import json
import sys
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import numpy as np

# Add RPA path to system path
RPA_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'RPA', 'RPA')
sys.path.insert(0, RPA_PATH)

# Import the LLM components
from rpa_engine.neural.tokenizer import CharacterTokenizer
from rpa_engine.neural.trainable_llm import TrainableLLM, ModelConfig

# Global model and tokenizer
model = None
tokenizer = None
model_loaded = False


def load_model():
    """Load or create the LLM model."""
    global model, tokenizer, model_loaded

    if model_loaded:
        return True

    print("Loading Neural LLM...")

    # Create tokenizer
    tokenizer = CharacterTokenizer()

    # Load or create model
    model_path = os.path.join(RPA_PATH, 'model_storage', 'trained_llm')

    if os.path.exists(os.path.join(model_path, 'config.json')):
        print("Loading saved model...")
        model = TrainableLLM.load(model_path)
    else:
        print("Creating new model...")
        config = ModelConfig(
            vocab_size=tokenizer.vocab_size,
            d_model=32,
            num_heads=2,
            num_layers=2,
            learning_rate=0.1
        )
        model = TrainableLLM(config)

    model_loaded = True
    print(f"Model loaded! Parameters: {model.count_params():,}")
    return True


def generate_text(prompt: str, max_tokens: int = 50, temperature: float = 0.8) -> str:
    """Generate text from a prompt."""
    global model, tokenizer

    if not model or not tokenizer:
        return "Error: Model not loaded"

    # Encode prompt
    prompt_ids = tokenizer.encode(prompt)

    if len(prompt_ids) == 0:
        prompt_ids = [0]  # Start token

    # Create input array
    input_ids = np.array([prompt_ids])

    # Generate
    try:
        output_ids = model.generate(
            input_ids,
            max_new_tokens=max_tokens,
            temperature=temperature
        )

        # Decode
        output_text = tokenizer.decode(output_ids[0].tolist())
        return output_text
    except Exception as e:
        return f"Error generating: {str(e)}"


def train_on_text(text: str, epochs: int = 5) -> dict:
    """Train the model on some text."""
    global model, tokenizer

    if not model or not tokenizer:
        return {"error": "Model not loaded"}

    try:
        # Encode text
        ids = tokenizer.encode(text)

        if len(ids) < 2:
            return {"error": "Text too short"}

        # Training
        losses = []
        input_ids = np.array([ids[:-1]])
        targets = np.array([ids[1:]])

        for epoch in range(epochs):
            loss = model.train_step(input_ids, targets)
            losses.append(float(loss))

        return {
            "status": "trained",
            "epochs": epochs,
            "final_loss": losses[-1] if losses else None,
            "losses": losses
        }
    except Exception as e:
        return {"error": str(e)}


class LLMHandler(BaseHTTPRequestHandler):
    """HTTP request handler for LLM service."""

    def _send_json(self, data: dict, status: int = 200):
        """Send JSON response."""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self._send_json({"status": "ok"})

    def do_GET(self):
        """Handle GET requests."""
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        if path == '/health':
            self._send_json({
                "status": "healthy",
                "model_loaded": model_loaded,
                "parameters": model.count_params() if model else 0
            })
        elif path == '/generate':
            prompt = params.get('prompt', [''])[0]
            max_tokens = int(params.get('max_tokens', ['50'])[0])
            temperature = float(params.get('temperature', ['0.8'])[0])

            if not prompt:
                self._send_json({"error": "No prompt provided"}, 400)
                return

            result = generate_text(prompt, max_tokens, temperature)
            self._send_json({
                "prompt": prompt,
                "generated": result
            })
        elif path == '/status':
            self._send_json({
                "model_loaded": model_loaded,
                "vocab_size": tokenizer.vocab_size if tokenizer else 0,
                "parameters": model.count_params() if model else 0,
                "config": {
                    "d_model": model.config.d_model if model else 0,
                    "num_heads": model.config.num_heads if model else 0,
                    "num_layers": model.config.num_layers if model else 0
                }
            })
        else:
            self._send_json({"error": "Unknown endpoint"}, 404)

    def do_POST(self):
        """Handle POST requests."""
        parsed = urlparse(self.path)
        path = parsed.path

        # Read body
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode() if content_length > 0 else '{}'

        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self._send_json({"error": "Invalid JSON"}, 400)
            return

        if path == '/chat':
            # Chat endpoint - takes message and returns response
            message = data.get('message', '')
            max_tokens = data.get('max_tokens', 100)
            temperature = data.get('temperature', 0.7)

            if not message:
                self._send_json({"error": "No message provided"}, 400)
                return

            # Generate response
            response = generate_text(message, max_tokens, temperature)

            self._send_json({
                "message": message,
                "response": response,
                "model": "RPA Neural LLM"
            })
        elif path == '/train':
            # Train endpoint
            text = data.get('text', '')
            epochs = data.get('epochs', 5)

            if not text:
                self._send_json({"error": "No text provided"}, 400)
                return

            result = train_on_text(text, epochs)
            self._send_json(result)
        else:
            self._send_json({"error": "Unknown endpoint"}, 404)

    def log_message(self, format, *args):
        """Override to reduce log noise."""
        print(f"[LLM Service] {args[0]}")


def main():
    """Main entry point."""
    port = 3033

    # Load model on startup
    print("=" * 50)
    print("RPA NEURAL LLM SERVICE")
    print("=" * 50)

    load_model()

    # Start server
    server = HTTPServer(('0.0.0.0', port), LLMHandler)
    print(f"\nLLM Service running on port {port}")
    print("Endpoints:")
    print("  GET  /health    - Health check")
    print("  GET  /status    - Model status")
    print("  GET  /generate  - Generate text (?prompt=...)")
    print("  POST /chat      - Chat with LLM")
    print("  POST /train     - Train on text")
    print("-" * 50)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


if __name__ == '__main__':
    main()
