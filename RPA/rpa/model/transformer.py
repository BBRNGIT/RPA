"""
Transformer Architecture - Complete transformer layers and model.

This implements the full transformer architecture:
1. TransformerBlock: Self-attention + Feed-forward + Layer norms
2. Transformer: Stack of transformer blocks
3. Forward pass through the full model

This is the actual neural network that processes patterns.
"""

import math
import random
import json
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
from pathlib import Path

from .attention import (
    MultiHeadAttention,
    SelfAttention,
    layer_norm,
    add_vectors,
    scale_vector,
)


def gelu(x: float) -> float:
    """Gaussian Error Linear Unit activation function."""
    return 0.5 * x * (1 + math.tanh(math.sqrt(2 / math.pi) * (x + 0.044715 * x**3)))


def relu(x: float) -> float:
    """ReLU activation function."""
    return max(0, x)


def sigmoid(x: float) -> float:
    """Sigmoid activation function."""
    if x < -20:
        return 0.0
    if x > 20:
        return 1.0
    return 1 / (1 + math.exp(-x))


@dataclass
class FeedForwardWeights:
    """Weights for feed-forward network."""
    W1: List[List[float]]  # First linear layer
    b1: List[float]  # First bias
    W2: List[List[float]]  # Second linear layer
    b2: List[float]  # Second bias

    def to_dict(self) -> Dict:
        return {
            "W1": self.W1,
            "b1": self.b1,
            "W2": self.W2,
            "b2": self.b2,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "FeedForwardWeights":
        return cls(
            W1=data["W1"],
            b1=data["b1"],
            W2=data["W2"],
            b2=data["b2"],
        )


class FeedForward:
    """
    Position-wise feed-forward network.

    FFN(x) = max(0, xW1 + b1)W2 + b2

    Args:
        embed_dim: Input and output dimension
        hidden_dim: Hidden layer dimension (typically 4 * embed_dim)
        activation: Activation function ('gelu' or 'relu')
    """

    def __init__(
        self,
        embed_dim: int = 256,
        hidden_dim: Optional[int] = None,
        activation: str = "gelu",
        seed: Optional[int] = None
    ):
        self.embed_dim = embed_dim
        self.hidden_dim = hidden_dim or (4 * embed_dim)
        self.activation = activation

        self._init_weights(seed)

    def _init_weights(self, seed: Optional[int] = None):
        """Initialize feed-forward weights."""
        rng = random.Random(seed)

        def xavier_init(rows: int, cols: int) -> List[List[float]]:
            limit = math.sqrt(6.0 / (rows + cols))
            return [[rng.uniform(-limit, limit) for _ in range(cols)] for _ in range(rows)]

        def zero_init(size: int) -> List[float]:
            return [0.0] * size

        self.weights = FeedForwardWeights(
            W1=xavier_init(self.embed_dim, self.hidden_dim),
            b1=zero_init(self.hidden_dim),
            W2=xavier_init(self.hidden_dim, self.embed_dim),
            b2=zero_init(self.embed_dim),
        )

    def forward(self, x: List[float]) -> List[float]:
        """
        Forward pass through feed-forward network.

        Args:
            x: Input vector (embed_dim,)

        Returns:
            Output vector (embed_dim,)
        """
        # First linear: x @ W1 + b1
        hidden = [0.0] * self.hidden_dim
        for j in range(self.hidden_dim):
            for i in range(self.embed_dim):
                hidden[j] += x[i] * self.weights.W1[i][j]
            hidden[j] += self.weights.b1[j]

        # Activation
        if self.activation == "gelu":
            hidden = [gelu(h) for h in hidden]
        else:
            hidden = [relu(h) for h in hidden]

        # Second linear: hidden @ W2 + b2
        output = [0.0] * self.embed_dim
        for j in range(self.embed_dim):
            for i in range(self.hidden_dim):
                output[j] += hidden[i] * self.weights.W2[i][j]
            output[j] += self.weights.b2[j]

        return output

    def __call__(self, x: List[float]) -> List[float]:
        return self.forward(x)

    def get_weights(self) -> FeedForwardWeights:
        return self.weights

    def set_weights(self, weights: FeedForwardWeights) -> None:
        self.weights = weights


class TransformerBlock:
    """
    Single transformer block.

    Structure:
        x -> LayerNorm -> Self-Attention -> Add (residual)
          -> LayerNorm -> Feed-Forward -> Add (residual)
          -> output

    Args:
        embed_dim: Embedding dimension
        num_heads: Number of attention heads
        hidden_dim: Feed-forward hidden dimension
        dropout: Dropout rate (not used in inference)
    """

    def __init__(
        self,
        embed_dim: int = 256,
        num_heads: int = 8,
        hidden_dim: Optional[int] = None,
        dropout: float = 0.0,
        seed: Optional[int] = None
    ):
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.hidden_dim = hidden_dim or (4 * embed_dim)

        # Components
        self.attention = SelfAttention(
            embed_dim=embed_dim,
            num_heads=num_heads,
            seed=seed
        )
        self.feed_forward = FeedForward(
            embed_dim=embed_dim,
            hidden_dim=self.hidden_dim,
            seed=seed + 1 if seed else None
        )

    def forward(
        self,
        x: List[float],
        context: List[List[float]],
        return_attention: bool = False
    ) -> Tuple[List[float], Optional[List[List[float]]]]:
        """
        Forward pass through transformer block.

        Args:
            x: Input query vector
            context: Context patterns for attention
            return_attention: Whether to return attention weights

        Returns:
            output: Transformed output
            attention_weights: Attention weights if requested
        """
        # Self-attention with residual connection
        attn_output, attn_weights = self.attention(x, context, return_weights=True)

        # Add & Norm
        x = layer_norm(add_vectors(x, attn_output))

        # Feed-forward with residual connection
        ff_output = self.feed_forward(x)

        # Add & Norm
        output = layer_norm(add_vectors(x, ff_output))

        if return_attention:
            return output, attn_weights
        return output, None

    def __call__(
        self,
        x: List[float],
        context: List[List[float]],
        return_attention: bool = False
    ) -> Tuple[List[float], Optional[List[List[float]]]]:
        return self.forward(x, context, return_attention)

    def get_weights(self) -> Dict:
        """Get all weights from this block."""
        return {
            "attention": self.attention.get_weights().to_dict(),
            "feed_forward": self.feed_forward.get_weights().to_dict(),
        }

    def set_weights(self, weights: Dict) -> None:
        """Set all weights for this block."""
        from .attention import AttentionWeights
        self.attention.set_weights(AttentionWeights.from_dict(weights["attention"]))
        self.feed_forward.set_weights(FeedForwardWeights.from_dict(weights["feed_forward"]))


class Transformer:
    """
    Full transformer model for pattern processing.

    A stack of transformer blocks that process input patterns
    through multiple layers of attention and feed-forward networks.

    Args:
        num_layers: Number of transformer blocks
        embed_dim: Embedding dimension
        num_heads: Number of attention heads per block
        hidden_dim: Feed-forward hidden dimension
    """

    def __init__(
        self,
        num_layers: int = 6,
        embed_dim: int = 256,
        num_heads: int = 8,
        hidden_dim: Optional[int] = None,
        seed: Optional[int] = None
    ):
        self.num_layers = num_layers
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.hidden_dim = hidden_dim or (4 * embed_dim)

        # Create transformer blocks
        self.blocks = [
            TransformerBlock(
                embed_dim=embed_dim,
                num_heads=num_heads,
                hidden_dim=self.hidden_dim,
                seed=seed + i if seed else None
            )
            for i in range(num_layers)
        ]

    def forward(
        self,
        x: List[float],
        context: List[List[float]],
        return_all_attention: bool = False
    ) -> Tuple[List[float], Optional[List[List[List[float]]]]]:
        """
        Forward pass through all transformer layers.

        Args:
            x: Input query vector
            context: Context patterns for attention
            return_all_attention: Whether to return attention from all layers

        Returns:
            output: Final output vector
            all_attention: Attention weights from all layers (if requested)
        """
        all_attention = [] if return_all_attention else None

        for block in self.blocks:
            x, attn = block(x, context, return_attention=return_all_attention)
            if return_all_attention:
                all_attention.append(attn)

        if return_all_attention:
            return x, all_attention
        return x, None

    def __call__(
        self,
        x: List[float],
        context: List[List[float]],
        return_all_attention: bool = False
    ) -> Tuple[List[float], Optional[List[List[List[float]]]]]:
        return self.forward(x, context, return_all_attention)

    def get_weights(self) -> Dict:
        """Get all weights from all layers."""
        return {
            f"layer_{i}": block.get_weights()
            for i, block in enumerate(self.blocks)
        }

    def set_weights(self, weights: Dict) -> None:
        """Set all weights for all layers."""
        for i, block in enumerate(self.blocks):
            if f"layer_{i}" in weights:
                block.set_weights(weights[f"layer_{i}"])

    def save(self, path: str) -> None:
        """Save model weights to file."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump({
                "config": {
                    "num_layers": self.num_layers,
                    "embed_dim": self.embed_dim,
                    "num_heads": self.num_heads,
                    "hidden_dim": self.hidden_dim,
                },
                "weights": self.get_weights(),
            }, f, indent=2)

    def load(self, path: str) -> None:
        """Load model weights from file."""
        with open(path, 'r') as f:
            data = json.load(f)
        self.set_weights(data["weights"])

    def count_parameters(self) -> int:
        """Count total number of parameters."""
        total = 0

        for block in self.blocks:
            # Attention weights: 4 * embed_dim * embed_dim
            total += 4 * self.embed_dim * self.embed_dim

            # Feed-forward weights: 2 * embed_dim * hidden_dim + biases
            total += 2 * self.embed_dim * self.hidden_dim
            total += self.hidden_dim + self.embed_dim

        return total


class RPAModel:
    """
    Complete RPA model combining encoder and transformer.

    This is the full AI model that:
    1. Encodes input text to vectors using PatternEncoder
    2. Retrieves relevant context patterns
    3. Processes through transformer layers
    4. Returns output for downstream tasks

    Args:
        encoder: PatternEncoder instance (with vocabulary loaded)
        num_layers: Number of transformer layers
        num_heads: Number of attention heads
    """

    def __init__(
        self,
        encoder: Optional["PatternEncoder"] = None,
        num_layers: int = 6,
        num_heads: int = 8,
        seed: Optional[int] = None
    ):
        from .pattern_encoder import PatternEncoder

        self.encoder = encoder or PatternEncoder()
        self.transformer = Transformer(
            num_layers=num_layers,
            embed_dim=self.encoder.embed_dim,
            num_heads=num_heads,
            seed=seed
        )

    def forward(
        self,
        text: str,
        max_context: int = 50,
        return_attention: bool = False
    ) -> Tuple[List[float], Optional[List[List[List[float]]]]]:
        """
        Forward pass through the full model.

        Args:
            text: Input text to process
            max_context: Maximum number of context patterns to use
            return_attention: Whether to return attention weights

        Returns:
            output: Output vector
            attention: Attention weights from all layers (if requested)
        """
        # Encode input text
        query_vector = self.encoder.encode(text)

        # Get context patterns
        matches = self.encoder.decode(query_vector, top_k=max_context)
        context_vectors = [self.encoder.vocab.get_embedding(p.pattern_id) for p, _ in matches]
        context_vectors = [v for v in context_vectors if v is not None]

        if not context_vectors:
            # No context available, return encoded query
            return query_vector, None

        # Process through transformer
        return self.transformer(query_vector, context_vectors, return_attention)

    def __call__(
        self,
        text: str,
        max_context: int = 50,
        return_attention: bool = False
    ) -> Tuple[List[float], Optional[List[List[List[float]]]]]:
        return self.forward(text, max_context, return_attention)

    def answer(self, question: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """
        Answer a question by finding similar patterns.

        Args:
            question: Question text
            top_k: Number of answers to return

        Returns:
            List of (pattern_text, similarity) tuples
        """
        output, _ = self.forward(question)
        return self.encoder.decode(output, top_k=top_k)

    def save(self, path: str) -> None:
        """Save full model to disk."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)

        # Save encoder
        self.encoder.save(Path(path) / "encoder")

        # Save transformer
        self.transformer.save(str(Path(path) / "transformer.json"))

        # Save config
        with open(Path(path) / "config.json", 'w') as f:
            json.dump({
                "num_layers": self.transformer.num_layers,
                "embed_dim": self.transformer.embed_dim,
                "num_heads": self.transformer.num_heads,
            }, f, indent=2)

    def load(self, path: str) -> None:
        """Load full model from disk."""
        self.encoder.load(Path(path) / "encoder")
        self.transformer.load(str(Path(path) / "transformer.json"))


if __name__ == "__main__":
    print("=" * 60)
    print("TRANSFORMER ARCHITECTURE TEST")
    print("=" * 60)

    # Create transformer
    embed_dim = 128
    num_layers = 4
    num_heads = 4

    model = Transformer(
        num_layers=num_layers,
        embed_dim=embed_dim,
        num_heads=num_heads,
        seed=42
    )

    print(f"\nTransformer created:")
    print(f"  Layers: {num_layers}")
    print(f"  Embed dim: {embed_dim}")
    print(f"  Heads: {num_heads}")
    print(f"  Parameters: {model.count_parameters():,}")

    # Test forward pass
    query = [random.uniform(-0.5, 0.5) for _ in range(embed_dim)]
    context = [[random.uniform(-0.5, 0.5) for _ in range(embed_dim)] for _ in range(10)]

    print(f"\nForward pass:")
    print(f"  Input: query ({len(query)}) + {len(context)} context patterns")

    output, all_attention = model(query, context, return_all_attention=True)

    print(f"  Output: {len(output)}")
    print(f"  Attention layers: {len(all_attention)}")
    print(f"  Heads per layer: {len(all_attention[0])}")

    # Test save/load
    model.save("/tmp/transformer_test.json")
    print(f"\nModel saved to /tmp/transformer_test.json")

    new_model = Transformer(num_layers=num_layers, embed_dim=embed_dim, num_heads=num_heads)
    new_model.load("/tmp/transformer_test.json")

    new_output, _ = new_model(query, context)
    diff = sum(abs(a - b) for a, b in zip(output, new_output))
    print(f"  Loaded model output difference: {diff:.6f}")

    print("\n" + "=" * 60)
    print("TRANSFORMER ARCHITECTURE WORKING")
    print("=" * 60)
