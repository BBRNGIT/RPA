"""
Tests for the Attention Mechanism.

These tests verify:
1. Multi-head attention computes correctly
2. Attention weights sum to 1
3. Different inputs produce different outputs
4. Weights can be saved and loaded
"""

import pytest
import math
import random
from pathlib import Path
import tempfile

from rpa.model.attention import (
    MultiHeadAttention,
    SelfAttention,
    CrossAttention,
    AttentionWeights,
    softmax,
    layer_norm,
    dot_product,
)


class TestSoftmax:
    """Test softmax function."""

    def test_softmax_sums_to_one(self):
        """Softmax output sums to 1."""
        values = [1.0, 2.0, 3.0]
        result = softmax(values)
        assert sum(result) == pytest.approx(1.0, abs=1e-6)

    def test_softmax_all_positive(self):
        """Softmax outputs are all positive."""
        values = [-10.0, 0.0, 10.0]
        result = softmax(values)
        assert all(v > 0 for v in result)

    def test_softmax_preserves_order(self):
        """Larger inputs get larger outputs."""
        values = [1.0, 2.0, 3.0]
        result = softmax(values)
        assert result[2] > result[1] > result[0]

    def test_softmax_large_values(self):
        """Softmax handles large values without overflow."""
        values = [1000.0, 1001.0, 1002.0]
        result = softmax(values)
        assert sum(result) == pytest.approx(1.0, abs=1e-6)


class TestLayerNorm:
    """Test layer normalization."""

    def test_layer_norm_zero_mean(self):
        """Layer norm output has approximately zero mean."""
        x = [random.uniform(-10, 10) for _ in range(100)]
        normalized = layer_norm(x)
        mean = sum(normalized) / len(normalized)
        assert abs(mean) < 1e-6

    def test_layer_norm_unit_variance(self):
        """Layer norm output has approximately unit variance."""
        x = [random.uniform(-10, 10) for _ in range(100)]
        normalized = layer_norm(x)
        mean = sum(normalized) / len(normalized)
        variance = sum((v - mean) ** 2 for v in normalized) / len(normalized)
        assert abs(variance - 1.0) < 0.1


class TestMultiHeadAttention:
    """Test multi-head attention."""

    @pytest.fixture
    def attention(self):
        """Create attention layer for testing."""
        return MultiHeadAttention(embed_dim=64, num_heads=4, seed=42)

    @pytest.fixture
    def sample_inputs(self):
        """Create sample inputs for testing."""
        random.seed(123)
        query = [random.uniform(-0.5, 0.5) for _ in range(64)]
        context = [[random.uniform(-0.5, 0.5) for _ in range(64)] for _ in range(5)]
        return query, context

    def test_create_attention(self, attention):
        """Attention layer can be created."""
        assert attention.embed_dim == 64
        assert attention.num_heads == 4
        assert attention.head_dim == 16

    def test_attention_output_shape(self, attention, sample_inputs):
        """Attention output has correct shape."""
        query, context = sample_inputs
        output, _ = attention(query, context, context)
        assert len(output) == 64

    def test_attention_weights_shape(self, attention, sample_inputs):
        """Attention weights have correct shape."""
        query, context = sample_inputs
        _, weights = attention(query, context, context, return_weights=True)
        assert len(weights) == attention.num_heads
        assert len(weights[0]) == len(context)

    def test_attention_weights_sum_to_one(self, attention, sample_inputs):
        """Attention weights sum to 1 for each head."""
        query, context = sample_inputs
        _, weights = attention(query, context, context, return_weights=True)
        for head_weights in weights:
            assert sum(head_weights) == pytest.approx(1.0, abs=1e-6)

    def test_different_query_different_output(self, attention, sample_inputs):
        """Different queries produce different outputs."""
        _, context = sample_inputs
        query1 = [random.uniform(-0.5, 0.5) for _ in range(64)]
        query2 = [random.uniform(-0.5, 0.5) for _ in range(64)]

        output1, _ = attention(query1, context, context)
        output2, _ = attention(query2, context, context)

        # Outputs should be different
        diff = sum(abs(a - b) for a, b in zip(output1, output2))
        assert diff > 0

    def test_same_query_same_output(self, attention, sample_inputs):
        """Same query produces same output (deterministic)."""
        query, context = sample_inputs

        output1, _ = attention(query, context, context)
        output2, _ = attention(query, context, context)

        assert output1 == output2

    def test_weights_initialized(self, attention):
        """Attention weights are initialized."""
        weights = attention.get_weights()
        assert weights.Wq is not None
        assert weights.Wk is not None
        assert weights.Wv is not None
        assert weights.Wo is not None

        # Check dimensions
        assert len(weights.Wq) == 64  # embed_dim
        assert len(weights.Wq[0]) == 64

    def test_save_load_weights(self, attention, sample_inputs):
        """Attention weights can be saved and loaded."""
        query, context = sample_inputs

        # Get output before save
        output_before, _ = attention(query, context, context)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Save
            attention.save(f"{tmpdir}/attention.json")

            # Create new attention and load
            new_attention = MultiHeadAttention(embed_dim=64, num_heads=4)
            new_attention.load(f"{tmpdir}/attention.json")

            # Output should be same
            output_after, _ = new_attention(query, context, context)
            assert output_before == output_after


class TestSelfAttention:
    """Test self-attention."""

    def test_self_attention(self):
        """Self-attention works correctly."""
        attn = SelfAttention(embed_dim=64, num_heads=4, seed=42)

        x = [random.uniform(-0.5, 0.5) for _ in range(64)]
        context = [[random.uniform(-0.5, 0.5) for _ in range(64)] for _ in range(5)]

        output, weights = attn(x, context, return_weights=True)

        assert len(output) == 64
        assert len(weights) == 4


class TestCrossAttention:
    """Test cross-attention."""

    def test_cross_attention(self):
        """Cross-attention works correctly."""
        attn = CrossAttention(embed_dim=64, num_heads=4, seed=42)

        query = [random.uniform(-0.5, 0.5) for _ in range(64)]
        context = [[random.uniform(-0.5, 0.5) for _ in range(64)] for _ in range(5)]

        output, weights = attn(query, context, return_weights=True)

        assert len(output) == 64
        assert len(weights) == 4


class TestAttentionWeightsDataclass:
    """Test AttentionWeights dataclass."""

    def test_to_dict(self):
        """Weights can be converted to dict."""
        weights = AttentionWeights(
            Wq=[[1.0, 2.0], [3.0, 4.0]],
            Wk=[[5.0, 6.0], [7.0, 8.0]],
            Wv=[[9.0, 10.0], [11.0, 12.0]],
            Wo=[[13.0, 14.0], [15.0, 16.0]],
        )
        d = weights.to_dict()
        assert "Wq" in d
        assert "Wk" in d
        assert "Wv" in d
        assert "Wo" in d

    def test_from_dict(self):
        """Weights can be loaded from dict."""
        data = {
            "Wq": [[1.0, 2.0], [3.0, 4.0]],
            "Wk": [[5.0, 6.0], [7.0, 8.0]],
            "Wv": [[9.0, 10.0], [11.0, 12.0]],
            "Wo": [[13.0, 14.0], [15.0, 16.0]],
        }
        weights = AttentionWeights.from_dict(data)
        assert weights.Wq == data["Wq"]


class TestAttentionIntegration:
    """Integration tests with pattern encoder."""

    @pytest.fixture
    def encoder(self):
        """Create encoder with curriculum."""
        from rpa.model import PatternEncoder
        encoder = PatternEncoder(embed_dim=128)
        curriculum_path = Path(__file__).parent.parent / "curriculum"
        if curriculum_path.exists():
            encoder.load_curriculum(curriculum_path)
        return encoder

    def test_attention_with_encoded_patterns(self, encoder):
        """Attention can be applied to encoded patterns."""
        if encoder.get_vocab_size() == 0:
            pytest.skip("No curriculum loaded")

        attention = MultiHeadAttention(embed_dim=128, num_heads=4, seed=42)

        # Encode a question
        query = encoder.encode("What is a function in Python?")

        # Get context patterns from vocabulary
        context_patterns = list(encoder.vocab.embeddings.values())[:10]
        context_vectors = list(context_patterns)

        # Apply attention
        output, weights = attention(query, context_vectors, context_vectors, return_weights=True)

        assert len(output) == 128
        assert len(weights) == 4

        # Attention should focus on relevant patterns
        print(f"\nAttention weights for 'What is a function in Python?':")
        for i, w in enumerate(weights[0][:5]):
            print(f"  Pattern {i}: {w:.4f}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
