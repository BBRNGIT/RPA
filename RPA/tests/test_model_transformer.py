"""
Tests for the Transformer Architecture.

These tests verify:
1. Feed-forward network works correctly
2. Transformer block processes inputs
3. Full transformer model works
4. Weights can be saved and loaded
5. RPAModel integrates encoder and transformer
"""

import pytest
import math
import random
from pathlib import Path
import tempfile

from rpa.model.transformer import (
    FeedForward,
    TransformerBlock,
    Transformer,
    FeedForwardWeights,
    gelu,
    relu,
)
from rpa.model import PatternEncoder


class TestActivations:
    """Test activation functions."""

    def test_gelu_positive(self):
        """GELU of positive value is approximately the value."""
        result = gelu(1.0)
        assert 0.5 < result < 1.5

    def test_gelu_negative(self):
        """GELU of negative value is approximately zero."""
        result = gelu(-5.0)
        assert abs(result) < 0.01

    def test_gelu_zero(self):
        """GELU of zero is zero."""
        result = gelu(0.0)
        assert result == 0.0

    def test_relu_positive(self):
        """ReLU of positive value is the value."""
        assert relu(5.0) == 5.0

    def test_relu_negative(self):
        """ReLU of negative value is zero."""
        assert relu(-5.0) == 0.0


class TestFeedForward:
    """Test feed-forward network."""

    @pytest.fixture
    def ff(self):
        """Create feed-forward network."""
        return FeedForward(embed_dim=64, hidden_dim=256, seed=42)

    def test_create_feedforward(self, ff):
        """Feed-forward can be created."""
        assert ff.embed_dim == 64
        assert ff.hidden_dim == 256

    def test_forward_shape(self, ff):
        """Forward output has correct shape."""
        x = [random.uniform(-0.5, 0.5) for _ in range(64)]
        output = ff(x)
        assert len(output) == 64

    def test_forward_different_input(self, ff):
        """Different inputs produce different outputs."""
        x1 = [random.uniform(-0.5, 0.5) for _ in range(64)]
        x2 = [random.uniform(-0.5, 0.5) for _ in range(64)]

        out1 = ff(x1)
        out2 = ff(x2)

        diff = sum(abs(a - b) for a, b in zip(out1, out2))
        assert diff > 0

    def test_weights_initialized(self, ff):
        """Weights are initialized."""
        weights = ff.get_weights()
        assert len(weights.W1) == 64
        assert len(weights.W1[0]) == 256
        assert len(weights.b1) == 256


class TestTransformerBlock:
    """Test transformer block."""

    @pytest.fixture
    def block(self):
        """Create transformer block."""
        return TransformerBlock(embed_dim=64, num_heads=4, seed=42)

    @pytest.fixture
    def sample_inputs(self):
        """Create sample inputs."""
        random.seed(123)
        query = [random.uniform(-0.5, 0.5) for _ in range(64)]
        context = [[random.uniform(-0.5, 0.5) for _ in range(64)] for _ in range(5)]
        return query, context

    def test_create_block(self, block):
        """Block can be created."""
        assert block.embed_dim == 64
        assert block.num_heads == 4

    def test_forward_shape(self, block, sample_inputs):
        """Forward output has correct shape."""
        query, context = sample_inputs
        output, _ = block(query, context)
        assert len(output) == 64

    def test_attention_shape(self, block, sample_inputs):
        """Attention weights have correct shape."""
        query, context = sample_inputs
        _, attn = block(query, context, return_attention=True)
        assert len(attn) == 4  # num_heads
        assert len(attn[0]) == len(context)

    def test_residual_connection(self, block, sample_inputs):
        """Output is different from input (residual applied)."""
        query, context = sample_inputs
        output, _ = block(query, context)
        # Output should be different from input due to transformations
        diff = sum(abs(a - b) for a, b in zip(query, output))
        assert diff > 0


class TestTransformer:
    """Test full transformer model."""

    @pytest.fixture
    def transformer(self):
        """Create transformer model."""
        return Transformer(num_layers=3, embed_dim=64, num_heads=4, seed=42)

    @pytest.fixture
    def sample_inputs(self):
        """Create sample inputs."""
        random.seed(456)
        query = [random.uniform(-0.5, 0.5) for _ in range(64)]
        context = [[random.uniform(-0.5, 0.5) for _ in range(64)] for _ in range(5)]
        return query, context

    def test_create_transformer(self, transformer):
        """Transformer can be created."""
        assert transformer.num_layers == 3
        assert transformer.embed_dim == 64
        assert len(transformer.blocks) == 3

    def test_forward_shape(self, transformer, sample_inputs):
        """Forward output has correct shape."""
        query, context = sample_inputs
        output, _ = transformer(query, context)
        assert len(output) == 64

    def test_all_attention_shape(self, transformer, sample_inputs):
        """All attention weights have correct shape."""
        query, context = sample_inputs
        output, all_attn = transformer(query, context, return_all_attention=True)

        assert len(all_attn) == 3  # num_layers
        for layer_attn in all_attn:
            assert len(layer_attn) == 4  # num_heads

    def test_save_load(self, transformer, sample_inputs):
        """Transformer can be saved and loaded."""
        query, context = sample_inputs
        output_before, _ = transformer(query, context)

        with tempfile.TemporaryDirectory() as tmpdir:
            transformer.save(f"{tmpdir}/transformer.json")

            new_transformer = Transformer(num_layers=3, embed_dim=64, num_heads=4)
            new_transformer.load(f"{tmpdir}/transformer.json")

            output_after, _ = new_transformer(query, context)
            diff = sum(abs(a - b) for a, b in zip(output_before, output_after))
            assert diff < 1e-10  # Should be identical

    def test_count_parameters(self, transformer):
        """Parameter count is correct."""
        count = transformer.count_parameters()
        assert count > 0
        # Rough estimate: 3 layers * (attention + ff) * params_per_layer
        assert count > 10000


class TestTransformerIntegration:
    """Integration tests with encoder."""

    @pytest.fixture
    def encoder(self):
        """Create encoder with curriculum."""
        encoder = PatternEncoder(embed_dim=128)
        curriculum_path = Path(__file__).parent.parent / "curriculum"
        if curriculum_path.exists():
            encoder.load_curriculum(curriculum_path)
        return encoder

    def test_transformer_with_encoder(self, encoder):
        """Transformer can process encoded patterns."""
        if encoder.get_vocab_size() == 0:
            pytest.skip("No curriculum loaded")

        from rpa.model.transformer import Transformer

        transformer = Transformer(
            num_layers=2,
            embed_dim=128,
            num_heads=4,
            seed=42
        )

        # Encode a question
        query = encoder.encode("What is a function?")

        # Get context
        context_patterns = list(encoder.vocab.embeddings.values())[:10]

        # Process through transformer
        output, _ = transformer(query, context_patterns)

        assert len(output) == 128

    def test_rpamodel_answer(self, encoder):
        """RPAModel can answer questions."""
        if encoder.get_vocab_size() == 0:
            pytest.skip("No curriculum loaded")

        from rpa.model.transformer import RPAModel

        model = RPAModel(
            encoder=encoder,
            num_layers=2,
            num_heads=4,
            seed=42
        )

        answers = model.answer("What is a noun?", top_k=3)

        assert len(answers) >= 1
        # Each answer is (pattern, similarity)
        for pattern, similarity in answers:
            assert hasattr(pattern, 'text')
            assert 0 <= similarity <= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
