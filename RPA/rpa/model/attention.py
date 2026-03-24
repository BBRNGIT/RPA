"""
Attention Mechanism - Multi-head attention for pattern vectors.

This implements the core attention mechanism that allows the model to:
1. Attend over patterns in the vocabulary
2. Learn which patterns are relevant for each query
3. Combine pattern information with learned weights

Unlike traditional attention over tokens, this operates on pattern embeddings.
"""

import math
import random
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field


def softmax(values: List[float]) -> List[float]:
    """Compute softmax over a list of values."""
    max_val = max(values)
    exp_vals = [math.exp(v - max_val) for v in values]
    sum_exp = sum(exp_vals)
    return [e / sum_exp for e in exp_vals]


def matrix_multiply(A: List[List[float]], B: List[List[float]]) -> List[List[float]]:
    """Multiply two matrices."""
    rows_A, cols_A = len(A), len(A[0])
    rows_B, cols_B = len(B), len(B[0])

    assert cols_A == rows_B, f"Shape mismatch: {cols_A} != {rows_B}"

    result = [[0.0 for _ in range(cols_B)] for _ in range(rows_A)]

    for i in range(rows_A):
        for j in range(cols_B):
            for k in range(cols_A):
                result[i][j] += A[i][k] * B[k][j]

    return result


def transpose(matrix: List[List[float]]) -> List[List[float]]:
    """Transpose a matrix."""
    if not matrix:
        return []
    return [[matrix[i][j] for i in range(len(matrix))] for j in range(len(matrix[0]))]


def vector_matrix_multiply(v: List[float], M: List[List[float]]) -> List[float]:
    """Multiply vector by matrix."""
    return [sum(v[j] * M[j][i] for j in range(len(v))) for i in range(len(M[0]))]


def dot_product(v1: List[float], v2: List[float]) -> float:
    """Compute dot product of two vectors."""
    return sum(a * b for a, b in zip(v1, v2))


def scale_vector(v: List[float], scalar: float) -> List[float]:
    """Scale a vector."""
    return [x * scalar for x in v]


def add_vectors(v1: List[float], v2: List[float]) -> List[float]:
    """Add two vectors."""
    return [a + b for a, b in zip(v1, v2)]


def layer_norm(x: List[float], eps: float = 1e-6) -> List[float]:
    """Apply layer normalization to a vector."""
    mean = sum(x) / len(x)
    variance = sum((xi - mean) ** 2 for xi in x) / len(x)
    std = math.sqrt(variance + eps)
    return [(xi - mean) / std for xi in x]


@dataclass
class AttentionWeights:
    """Stores learned weight matrices for attention."""
    Wq: List[List[float]]  # Query projection
    Wk: List[List[float]]  # Key projection
    Wv: List[List[float]]  # Value projection
    Wo: List[List[float]]  # Output projection

    def to_dict(self) -> Dict:
        return {
            "Wq": self.Wq,
            "Wk": self.Wk,
            "Wv": self.Wv,
            "Wo": self.Wo,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "AttentionWeights":
        return cls(
            Wq=data["Wq"],
            Wk=data["Wk"],
            Wv=data["Wv"],
            Wo=data["Wo"],
        )


class MultiHeadAttention:
    """
    Multi-head attention mechanism for pattern vectors.

    Given a query pattern and a set of context patterns, computes
    attention weights and produces an attended representation.

    Args:
        embed_dim: Dimension of input embeddings
        num_heads: Number of attention heads
        head_dim: Dimension per head (defaults to embed_dim // num_heads)
    """

    def __init__(
        self,
        embed_dim: int = 256,
        num_heads: int = 8,
        head_dim: Optional[int] = None,
        seed: Optional[int] = None
    ):
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.head_dim = head_dim or (embed_dim // num_heads)

        assert self.head_dim * num_heads == embed_dim, \
            f"embed_dim ({embed_dim}) must be divisible by num_heads ({num_heads})"

        # Initialize weights
        self._init_weights(seed)

    def _init_weights(self, seed: Optional[int] = None):
        """Initialize attention weights with Xavier initialization."""
        rng = random.Random(seed)

        def xavier_init(rows: int, cols: int) -> List[List[float]]:
            """Xavier/Glorot initialization."""
            limit = math.sqrt(6.0 / (rows + cols))
            return [[rng.uniform(-limit, limit) for _ in range(cols)] for _ in range(rows)]

        # Projection matrices
        self.weights = AttentionWeights(
            Wq=xavier_init(self.embed_dim, self.embed_dim),
            Wk=xavier_init(self.embed_dim, self.embed_dim),
            Wv=xavier_init(self.embed_dim, self.embed_dim),
            Wo=xavier_init(self.embed_dim, self.embed_dim),
        )

    def project(self, x: List[float], W: List[List[float]]) -> List[float]:
        """Project vector through weight matrix."""
        return vector_matrix_multiply(x, W)

    def split_heads(self, x: List[float]) -> List[List[float]]:
        """Split vector into multiple heads."""
        heads = []
        for i in range(self.num_heads):
            start = i * self.head_dim
            end = start + self.head_dim
            heads.append(x[start:end])
        return heads

    def merge_heads(self, heads: List[List[float]]) -> List[float]:
        """Merge multiple heads back into single vector."""
        result = []
        for head in heads:
            result.extend(head)
        return result

    def scaled_dot_product_attention(
        self,
        query: List[float],
        keys: List[List[float]],
        values: List[List[float]],
        mask: Optional[List[bool]] = None
    ) -> Tuple[List[float], List[float]]:
        """
        Compute scaled dot-product attention.

        Args:
            query: Query vector (head_dim,)
            keys: Key vectors (num_keys, head_dim)
            values: Value vectors (num_keys, head_dim)
            mask: Optional mask for positions to ignore

        Returns:
            output: Attended output (head_dim,)
            attention_weights: Attention weights (num_keys,)
        """
        # Compute attention scores: Q @ K^T / sqrt(d_k)
        scores = []
        for key in keys:
            score = dot_product(query, key) / math.sqrt(self.head_dim)
            scores.append(score)

        # Apply mask if provided
        if mask is not None:
            for i, m in enumerate(mask):
                if not m:
                    scores[i] = -1e9

        # Softmax over scores
        attention_weights = softmax(scores)

        # Weighted sum of values
        output = [0.0] * self.head_dim
        for i, (weight, value) in enumerate(zip(attention_weights, values)):
            for j in range(self.head_dim):
                output[j] += weight * value[j]

        return output, attention_weights

    def forward(
        self,
        query: List[float],
        keys: List[List[float]],
        values: List[List[float]],
        return_weights: bool = False
    ) -> Tuple[List[float], Optional[List[List[float]]]]:
        """
        Forward pass of multi-head attention.

        Args:
            query: Query pattern embedding
            keys: Key pattern embeddings
            values: Value pattern embeddings
            return_weights: Whether to return attention weights

        Returns:
            output: Attended representation
            attention_weights: Per-head attention weights (if requested)
        """
        # Project query, keys, values
        Q = self.project(query, self.weights.Wq)
        Ks = [self.project(k, self.weights.Wk) for k in keys]
        Vs = [self.project(v, self.weights.Wv) for v in values]

        # Split into heads
        Q_heads = self.split_heads(Q)
        K_heads = [self.split_heads(k) for k in Ks]
        V_heads = [self.split_heads(v) for v in Vs]

        # Compute attention for each head
        head_outputs = []
        all_attention_weights = []

        for h in range(self.num_heads):
            # Get head-specific query, keys, values
            q_h = Q_heads[h]
            k_h = [K[h] for K in K_heads]
            v_h = [V[h] for V in V_heads]

            # Compute attention
            out_h, attn_h = self.scaled_dot_product_attention(q_h, k_h, v_h)
            head_outputs.append(out_h)
            all_attention_weights.append(attn_h)

        # Merge heads
        merged = self.merge_heads(head_outputs)

        # Output projection
        output = self.project(merged, self.weights.Wo)

        if return_weights:
            return output, all_attention_weights
        return output, None

    def __call__(
        self,
        query: List[float],
        keys: List[List[float]],
        values: List[List[float]],
        return_weights: bool = False
    ) -> Tuple[List[float], Optional[List[List[float]]]]:
        """Call forward pass."""
        return self.forward(query, keys, values, return_weights)

    def get_weights(self) -> AttentionWeights:
        """Get current attention weights."""
        return self.weights

    def set_weights(self, weights: AttentionWeights) -> None:
        """Set attention weights."""
        self.weights = weights

    def save(self, path: str) -> None:
        """Save attention weights to file."""
        import json
        from pathlib import Path

        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(self.weights.to_dict(), f, indent=2)

    def load(self, path: str) -> None:
        """Load attention weights from file."""
        import json

        with open(path, 'r') as f:
            data = json.load(f)
        self.weights = AttentionWeights.from_dict(data)


class SelfAttention(MultiHeadAttention):
    """
    Self-attention where query, keys, and values are the same.

    Used in transformer layers for pattern-to-pattern attention.
    """

    def forward(
        self,
        x: List[float],
        context: List[List[float]],
        return_weights: bool = False
    ) -> Tuple[List[float], Optional[List[List[float]]]]:
        """
        Self-attention forward pass.

        Args:
            x: Query pattern
            context: Context patterns (acts as both keys and values)
            return_weights: Whether to return attention weights

        Returns:
            output: Attended representation
            attention_weights: Per-head attention weights (if requested)
        """
        return super().forward(x, context, context, return_weights)

    def __call__(
        self,
        x: List[float],
        context: List[List[float]],
        return_weights: bool = False
    ) -> Tuple[List[float], Optional[List[List[float]]]]:
        """Call forward pass."""
        return self.forward(x, context, return_weights)


class CrossAttention(MultiHeadAttention):
    """
    Cross-attention between two different sequences.

    Used for encoder-decoder attention or pattern-to-query attention.
    """

    def forward(
        self,
        query: List[float],
        context: List[List[float]],
        return_weights: bool = False
    ) -> Tuple[List[float], Optional[List[List[float]]]]:
        """
        Cross-attention forward pass.

        Args:
            query: Query from one sequence
            context: Context from another sequence
            return_weights: Whether to return attention weights

        Returns:
            output: Attended representation
            attention_weights: Per-head attention weights (if requested)
        """
        return super().forward(query, context, context, return_weights)

    def __call__(
        self,
        query: List[float],
        context: List[List[float]],
        return_weights: bool = False
    ) -> Tuple[List[float], Optional[List[List[float]]]]:
        """Call forward pass."""
        return self.forward(query, context, return_weights)


if __name__ == "__main__":
    # Test attention mechanism
    print("=" * 60)
    print("ATTENTION MECHANISM TEST")
    print("=" * 60)

    # Create attention layer
    embed_dim = 256
    num_heads = 8
    attention = MultiHeadAttention(embed_dim=embed_dim, num_heads=num_heads, seed=42)

    print(f"\nAttention layer created:")
    print(f"  Embed dim: {embed_dim}")
    print(f"  Num heads: {num_heads}")
    print(f"  Head dim: {attention.head_dim}")

    # Create test query and context
    query = [random.uniform(-0.5, 0.5) for _ in range(embed_dim)]
    context = [[random.uniform(-0.5, 0.5) for _ in range(embed_dim)] for _ in range(10)]

    print(f"\nInput shapes:")
    print(f"  Query: {len(query)}")
    print(f"  Context: {len(context)} patterns x {len(context[0])} dims")

    # Forward pass
    output, attn_weights = attention(query, context, context, return_weights=True)

    print(f"\nOutput shapes:")
    print(f"  Output: {len(output)}")
    print(f"  Attention weights: {num_heads} heads x {len(attn_weights[0])} positions")

    # Show attention weights for first head
    print(f"\nAttention weights (head 0):")
    for i, w in enumerate(attn_weights[0][:5]):
        print(f"  Pattern {i}: {w:.4f}")
    print(f"  Sum of weights: {sum(attn_weights[0]):.4f}")

    # Verify output is different from input
    diff = sum(abs(a - b) for a, b in zip(query, output))
    print(f"\nQuery-Output difference: {diff:.4f}")

    print("\n" + "=" * 60)
    print("ATTENTION MECHANISM WORKING")
    print("=" * 60)
