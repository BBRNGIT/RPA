"""
Tests for the Pattern Encoder - the foundation of the RPA LLM.

These tests verify that the encoder can:
1. Load curriculum patterns
2. Encode text to vectors
3. Decode vectors back to similar patterns
4. Save and load the vocabulary
"""

import pytest
import math
from pathlib import Path
import tempfile
import shutil

from rpa.model import PatternEncoder, PatternVocabulary
from rpa.model.pattern_encoder import Pattern, cosine_similarity


class TestPatternVocabulary:
    """Test the PatternVocabulary class."""

    def test_create_vocabulary(self):
        """Vocabulary can be created with specified embedding dimension."""
        vocab = PatternVocabulary(embed_dim=128)
        assert vocab.embed_dim == 128
        assert len(vocab) == 0

    def test_add_pattern(self):
        """Patterns can be added to vocabulary."""
        vocab = PatternVocabulary(embed_dim=64)
        pattern = Pattern(
            pattern_id="test_1",
            text="This is a test pattern",
            domain="test",
            pattern_type="test_type"
        )

        pattern_id = vocab.add_pattern(pattern)

        assert pattern_id == "test_1"
        assert len(vocab) == 1
        assert "test_1" in vocab

    def test_embedding_created(self):
        """Adding a pattern creates an embedding vector."""
        vocab = PatternVocabulary(embed_dim=64)
        pattern = Pattern(
            pattern_id="test_1",
            text="Test pattern",
            domain="test",
            pattern_type="test"
        )
        vocab.add_pattern(pattern)

        embedding = vocab.get_embedding("test_1")

        assert embedding is not None
        assert len(embedding) == 64
        assert all(isinstance(v, float) for v in embedding)

    def test_embedding_deterministic(self):
        """Same text produces same embedding (deterministic)."""
        vocab = PatternVocabulary(embed_dim=64)

        pattern1 = Pattern("p1", "Same text here", "test", "test")
        pattern2 = Pattern("p2", "Same text here", "test", "test")

        vocab.add_pattern(pattern1)
        vocab.add_pattern(pattern2)

        emb1 = vocab.get_embedding("p1")
        emb2 = vocab.get_embedding("p2")

        # Different IDs but same text should produce same embedding
        assert emb1 == emb2

    def test_find_pattern_by_text(self):
        """Patterns can be found by text."""
        vocab = PatternVocabulary(embed_dim=64)
        pattern = Pattern("p1", "Hello world", "test", "test")
        vocab.add_pattern(pattern)

        found = vocab.find_pattern("hello world")
        assert found is not None
        assert found.pattern_id == "p1"

        # Partial match
        found = vocab.find_pattern("hello")
        assert found is not None

    def test_domain_indexing(self):
        """Patterns are indexed by domain."""
        vocab = PatternVocabulary(embed_dim=64)

        vocab.add_pattern(Pattern("p1", "Pattern 1", "english", "test"))
        vocab.add_pattern(Pattern("p2", "Pattern 2", "english", "test"))
        vocab.add_pattern(Pattern("p3", "Pattern 3", "python", "test"))

        english_patterns = vocab.get_patterns_by_domain("english")
        python_patterns = vocab.get_patterns_by_domain("python")

        assert len(english_patterns) == 2
        assert len(python_patterns) == 1

    def test_save_load(self):
        """Vocabulary can be saved and loaded."""
        vocab = PatternVocabulary(embed_dim=64)
        vocab.add_pattern(Pattern("p1", "Test pattern", "test", "test"))

        with tempfile.TemporaryDirectory() as tmpdir:
            vocab.save(Path(tmpdir))

            new_vocab = PatternVocabulary(embed_dim=64)
            new_vocab.load(Path(tmpdir))

            assert len(new_vocab) == 1
            assert "p1" in new_vocab
            assert new_vocab.get_embedding("p1") is not None


class TestPatternEncoder:
    """Test the PatternEncoder class."""

    def test_create_encoder(self):
        """Encoder can be created."""
        encoder = PatternEncoder(embed_dim=128)
        assert encoder.embed_dim == 128
        assert encoder.get_vocab_size() == 0

    def test_encode_empty_vocab(self):
        """Encoding with empty vocabulary returns zero vector."""
        encoder = PatternEncoder(embed_dim=64)
        vector = encoder.encode("Hello world")

        assert len(vector) == 64
        # Should still produce some vector (from text hash)

    def test_encode_with_vocabulary(self):
        """Encoding uses vocabulary patterns."""
        encoder = PatternEncoder(embed_dim=64)

        # Add patterns
        encoder.vocab.add_pattern(Pattern("p1", "What is a noun?", "english", "question"))
        encoder.vocab.add_pattern(Pattern("p2", "A noun is a word", "english", "definition"))

        vector = encoder.encode("What is a noun?")

        assert len(vector) == 64
        assert any(v != 0 for v in vector)  # Not all zeros

    def test_decode_finds_similar(self):
        """Decoding finds similar patterns."""
        encoder = PatternEncoder(embed_dim=64)

        encoder.vocab.add_pattern(Pattern("p1", "Python function definition", "python", "concept"))
        encoder.vocab.add_pattern(Pattern("p2", "How to cook pasta", "cooking", "tutorial"))

        # Encode a Python-related question
        vector = encoder.encode("How do I define a Python function?")
        matches = encoder.decode(vector, top_k=2)

        assert len(matches) >= 1
        # Python pattern should be more similar than cooking
        top_pattern = matches[0][0]
        assert "Python" in top_pattern.text or "function" in top_pattern.text

    def test_encode_decode_roundtrip(self):
        """Encode then decode should find the source pattern."""
        encoder = PatternEncoder(embed_dim=128)

        text = "A variable stores data in Python"
        encoder.vocab.add_pattern(Pattern("p1", text, "python", "definition"))

        vector = encoder.encode(text)
        matches = encoder.decode(vector, top_k=1)

        assert len(matches) == 1
        assert matches[0][0].text == text
        assert matches[0][1] > 0.9  # High similarity

    def test_load_curriculum(self):
        """Curriculum files can be loaded."""
        encoder = PatternEncoder(embed_dim=128)
        curriculum_path = Path(__file__).parent.parent / "curriculum"

        if not curriculum_path.exists():
            pytest.skip("Curriculum directory not found")

        patterns_loaded = encoder.load_curriculum(curriculum_path)

        assert patterns_loaded > 0
        assert encoder.get_vocab_size() > 0

    def test_stats(self):
        """Encoder provides statistics."""
        encoder = PatternEncoder(embed_dim=64)
        encoder.vocab.add_pattern(Pattern("p1", "Test", "test", "test"))

        stats = encoder.get_stats()

        assert "vocab_size" in stats
        assert "embed_dim" in stats
        assert stats["vocab_size"] == 1
        assert stats["embed_dim"] == 64

    def test_save_load_encoder(self):
        """Encoder can be saved and loaded."""
        encoder = PatternEncoder(embed_dim=64)
        encoder.vocab.add_pattern(Pattern("p1", "Test pattern", "test", "test"))

        with tempfile.TemporaryDirectory() as tmpdir:
            encoder.save(Path(tmpdir))

            new_encoder = PatternEncoder(embed_dim=64)
            new_encoder.load(Path(tmpdir))

            assert new_encoder.get_vocab_size() == 1


class TestCosineSimilarity:
    """Test the cosine similarity function."""

    def test_identical_vectors(self):
        """Identical vectors have similarity 1.0."""
        vec = [1.0, 2.0, 3.0]
        assert cosine_similarity(vec, vec) == pytest.approx(1.0, abs=1e-6)

    def test_orthogonal_vectors(self):
        """Orthogonal vectors have similarity 0.0."""
        vec1 = [1.0, 0.0]
        vec2 = [0.0, 1.0]
        assert cosine_similarity(vec1, vec2) == pytest.approx(0.0, abs=1e-6)

    def test_opposite_vectors(self):
        """Opposite vectors have similarity -1.0."""
        vec1 = [1.0, 1.0]
        vec2 = [-1.0, -1.0]
        assert cosine_similarity(vec1, vec2) == pytest.approx(-1.0, abs=1e-6)

    def test_zero_vector(self):
        """Zero vector has similarity 0.0 with any vector."""
        vec1 = [0.0, 0.0, 0.0]
        vec2 = [1.0, 2.0, 3.0]
        assert cosine_similarity(vec1, vec2) == 0.0


class TestEncoderIntegration:
    """Integration tests for the encoder."""

    @pytest.fixture
    def loaded_encoder(self):
        """Create encoder with curriculum loaded."""
        encoder = PatternEncoder(embed_dim=256)
        curriculum_path = Path(__file__).parent.parent / "curriculum"

        if curriculum_path.exists():
            encoder.load_curriculum(curriculum_path)

        return encoder

    def test_encode_real_question(self, loaded_encoder):
        """Can encode a real question and find relevant patterns."""
        if loaded_encoder.get_vocab_size() == 0:
            pytest.skip("No curriculum loaded")

        question = "What is a function in Python?"
        vector = loaded_encoder.encode(question)

        assert len(vector) == 256
        assert any(v != 0 for v in vector)

        matches = loaded_encoder.decode(vector, top_k=3)
        assert len(matches) >= 1

    def test_domain_patterns_accessible(self, loaded_encoder):
        """Domain-specific patterns are accessible."""
        if loaded_encoder.get_vocab_size() == 0:
            pytest.skip("No curriculum loaded")

        stats = loaded_encoder.get_stats()
        domains = stats.get("domains", {})

        # Should have patterns from at least some domains
        assert len(domains) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
