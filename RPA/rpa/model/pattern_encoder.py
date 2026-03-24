"""
Pattern Encoder - Converts curriculum patterns to vector representations.

This is the foundation of the RPA LLM. Instead of tokenization, we use
pattern-based encoding where each unique pattern from curriculum becomes
a learnable vector representation.

Key concepts:
- Pattern: Any piece of knowledge from curriculum (concept, instruction, code, etc.)
- Vocabulary: Set of all unique patterns extracted from curriculum
- Embedding: Vector representation of a pattern
- Encoding: Converting text to vectors using pattern matching
- Decoding: Finding most similar patterns from vectors
"""

import json
import math
import hashlib
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
import random


@dataclass
class Pattern:
    """A single pattern from curriculum."""
    pattern_id: str
    text: str
    domain: str
    pattern_type: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "pattern_id": self.pattern_id,
            "text": self.text,
            "domain": self.domain,
            "pattern_type": self.pattern_type,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Pattern":
        return cls(
            pattern_id=data["pattern_id"],
            text=data["text"],
            domain=data.get("domain", "general"),
            pattern_type=data.get("pattern_type", "unknown"),
            metadata=data.get("metadata", {}),
        )


class PatternVocabulary:
    """
    Vocabulary of patterns extracted from curriculum.

    This replaces tokenization in traditional LLMs. Instead of splitting
    text into tokens, we match against known patterns from curriculum.
    """

    def __init__(self, embed_dim: int = 256):
        self.embed_dim = embed_dim
        self.patterns: Dict[str, Pattern] = {}  # pattern_id -> Pattern
        self.text_to_id: Dict[str, str] = {}  # normalized text -> pattern_id
        self.embeddings: Dict[str, List[float]] = {}  # pattern_id -> vector
        self.domain_patterns: Dict[str, List[str]] = {}  # domain -> pattern_ids

    def add_pattern(self, pattern: Pattern) -> str:
        """Add a pattern to vocabulary and create its embedding."""
        if pattern.pattern_id in self.patterns:
            return pattern.pattern_id

        self.patterns[pattern.pattern_id] = pattern
        self.text_to_id[self._normalize(pattern.text)] = pattern.pattern_id

        # Initialize embedding with deterministic random values
        embedding = self._create_embedding(pattern.text)
        self.embeddings[pattern.pattern_id] = embedding

        # Index by domain
        if pattern.domain not in self.domain_patterns:
            self.domain_patterns[pattern.domain] = []
        self.domain_patterns[pattern.domain].append(pattern.pattern_id)

        return pattern.pattern_id

    def _normalize(self, text: str) -> str:
        """Normalize text for matching."""
        return re.sub(r'\s+', ' ', text.lower().strip())

    def _create_embedding(self, text: str) -> List[float]:
        """
        Create initial embedding for a pattern.

        Uses hash-based initialization for reproducibility.
        The embedding will be refined during training.
        """
        # Use hash to get deterministic random seed
        hash_bytes = hashlib.sha256(text.encode()).digest()
        seed = int.from_bytes(hash_bytes[:4], 'big')
        rng = random.Random(seed)

        # Create vector with values in [-0.5, 0.5]
        embedding = [rng.uniform(-0.5, 0.5) for _ in range(self.embed_dim)]

        return embedding

    def get_embedding(self, pattern_id: str) -> Optional[List[float]]:
        """Get embedding for a pattern."""
        return self.embeddings.get(pattern_id)

    def find_pattern(self, text: str) -> Optional[Pattern]:
        """Find pattern by exact or partial text match."""
        normalized = self._normalize(text)

        # Try exact match
        if normalized in self.text_to_id:
            return self.patterns[self.text_to_id[normalized]]

        # Try partial match (find pattern whose text contains query)
        for pattern in self.patterns.values():
            if normalized in self._normalize(pattern.text):
                return pattern
            if self._normalize(pattern.text) in normalized:
                return pattern

        return None

    def get_patterns_by_domain(self, domain: str) -> List[Pattern]:
        """Get all patterns for a domain."""
        pattern_ids = self.domain_patterns.get(domain, [])
        return [self.patterns[pid] for pid in pattern_ids]

    def save(self, path: Path) -> None:
        """Save vocabulary to disk."""
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)

        # Save patterns
        patterns_data = {pid: p.to_dict() for pid, p in self.patterns.items()}
        with open(path / "patterns.json", "w") as f:
            json.dump(patterns_data, f, indent=2)

        # Save embeddings
        with open(path / "embeddings.json", "w") as f:
            json.dump(self.embeddings, f, indent=2)

        # Save metadata
        with open(path / "vocab_meta.json", "w") as f:
            json.dump({
                "embed_dim": self.embed_dim,
                "total_patterns": len(self.patterns),
                "domains": list(self.domain_patterns.keys()),
            }, f, indent=2)

    def load(self, path: Path) -> None:
        """Load vocabulary from disk."""
        path = Path(path)

        # Load patterns
        patterns_path = path / "patterns.json"
        if patterns_path.exists():
            with open(patterns_path) as f:
                patterns_data = json.load(f)
            for pid, pdata in patterns_data.items():
                self.add_pattern(Pattern.from_dict(pdata))

    def __len__(self) -> int:
        return len(self.patterns)

    def __contains__(self, pattern_id: str) -> bool:
        return pattern_id in self.patterns


class PatternEncoder:
    """
    Encodes text to vectors using pattern vocabulary.

    This is the INPUT layer of the RPA LLM. It converts any text into
    vector representations by:
    1. Finding matching patterns from vocabulary
    2. Combining pattern embeddings (attention-style)
    3. Producing a fixed-size vector representation
    """

    def __init__(self, embed_dim: int = 256, vocab_path: Optional[Path] = None):
        self.embed_dim = embed_dim
        self.vocab = PatternVocabulary(embed_dim=embed_dim)

        if vocab_path:
            self.vocab.load(vocab_path)

    def load_curriculum(self, curriculum_dir: Path) -> int:
        """
        Load all curriculum files and build vocabulary.

        Returns number of patterns loaded.
        """
        curriculum_dir = Path(curriculum_dir)
        patterns_loaded = 0

        # Find all JSON files in curriculum directory
        for json_file in curriculum_dir.rglob("*.json"):
            try:
                patterns = self._extract_patterns_from_file(json_file)
                for pattern in patterns:
                    self.vocab.add_pattern(pattern)
                    patterns_loaded += 1
            except Exception as e:
                print(f"Warning: Could not load {json_file}: {e}")

        return patterns_loaded

    def _extract_patterns_from_file(self, filepath: Path) -> List[Pattern]:
        """Extract patterns from a curriculum JSON file."""
        with open(filepath) as f:
            data = json.load(f)

        patterns = []
        domain = filepath.parent.name

        # Handle different curriculum formats
        items = []
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            items = data.get("items", data.get("lessons", data.get("patterns", data.get("curriculum", []))))
            if not items and "skill_name" in data:
                # Single skill file with items
                items = data.get("items", [])
            if not items:
                # Maybe it's a single item
                items = [data]

        for i, item in enumerate(items):
            if not isinstance(item, dict):
                continue

            # Extract text from various possible fields
            text = (
                item.get("content") or
                item.get("text") or
                item.get("instruction") or
                item.get("concept") or
                item.get("pattern") or
                item.get("code") or
                item.get("description") or
                ""
            )

            # For items with instruction + examples
            if not text and item.get("instruction"):
                parts = [item["instruction"]]
                if item.get("concept"):
                    parts.insert(0, f"Concept: {item['concept']}")
                if item.get("examples"):
                    examples = item["examples"]
                    if isinstance(examples, list):
                        parts.append(f"Examples: {' | '.join(str(e) for e in examples[:3])}")
                text = " ".join(parts)

            if not text or len(str(text).strip()) < 5:
                continue

            # Create pattern
            pattern_id = item.get("id", item.get("pattern_id", item.get("item_id", f"pat_{hashlib.md5(str(text).encode()).hexdigest()[:8]}")))
            pattern_type = item.get("type", item.get("category", "pattern"))

            pattern = Pattern(
                pattern_id=str(pattern_id),
                text=str(text),
                domain=item.get("domain", domain),
                pattern_type=pattern_type,
                metadata={
                    "source_file": filepath.name,
                    "original_item": {k: v for k, v in item.items() if k not in ["content", "text", "instruction"]},
                }
            )
            patterns.append(pattern)

        return patterns

    def encode(self, text: str) -> List[float]:
        """
        Encode text to a vector.

        Finds matching patterns and combines their embeddings.
        """
        if not self.vocab.patterns:
            # No vocabulary loaded - return zero vector
            return [0.0] * self.embed_dim

        # Find matching patterns
        matching_patterns = self._find_matching_patterns(text)

        if not matching_patterns:
            # No matches - create embedding from text hash
            return self.vocab._create_embedding(text)

        # Combine embeddings (weighted average by match score)
        combined = [0.0] * self.embed_dim
        total_weight = 0.0

        for pattern, score in matching_patterns:
            embedding = self.vocab.get_embedding(pattern.pattern_id)
            if embedding:
                for i in range(self.embed_dim):
                    combined[i] += embedding[i] * score
                total_weight += score

        # Normalize
        if total_weight > 0:
            combined = [v / total_weight for v in combined]

        return combined

    def _find_matching_patterns(self, text: str, max_matches: int = 5) -> List[Tuple[Pattern, float]]:
        """Find patterns matching the text and return with match scores."""
        text_lower = text.lower()
        text_words = set(re.findall(r'\w+', text_lower))
        matches = []

        for pattern in self.vocab.patterns.values():
            pattern_lower = pattern.text.lower()
            pattern_words = set(re.findall(r'\w+', pattern_lower))

            # Calculate match score
            score = 0.0

            # Word overlap
            if text_words and pattern_words:
                overlap = len(text_words & pattern_words)
                score += overlap / max(len(text_words), len(pattern_words))

            # Substring match bonus
            if text_lower in pattern_lower:
                score += 0.5
            elif pattern_lower in text_lower:
                score += 0.3

            # Keyword matching
            keywords = pattern.metadata.get("original_item", {}).get("keywords", [])
            if keywords:
                keyword_matches = sum(1 for k in keywords if k.lower() in text_lower)
                score += 0.2 * keyword_matches / len(keywords)

            if score > 0:
                matches.append((pattern, score))

        # Sort by score and return top matches
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[:max_matches]

    def decode(self, vector: List[float], top_k: int = 5) -> List[Tuple[Pattern, float]]:
        """
        Find patterns most similar to the given vector.

        Returns list of (pattern, similarity_score) tuples.
        """
        if not self.vocab.patterns:
            return []

        similarities = []

        for pattern_id, embedding in self.vocab.embeddings.items():
            # Cosine similarity
            dot_product = sum(v * e for v, e in zip(vector, embedding))
            norm_v = math.sqrt(sum(v * v for v in vector))
            norm_e = math.sqrt(sum(e * e for e in embedding))

            if norm_v > 0 and norm_e > 0:
                similarity = dot_product / (norm_v * norm_e)
            else:
                similarity = 0.0

            similarities.append((self.vocab.patterns[pattern_id], similarity))

        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

    def encode_dataset(self, texts: List[str]) -> List[List[float]]:
        """Encode multiple texts to vectors."""
        return [self.encode(text) for text in texts]

    def save(self, path: Path) -> None:
        """Save encoder to disk."""
        self.vocab.save(path)

    def load(self, path: Path) -> None:
        """Load encoder from disk."""
        self.vocab.load(path)

    def get_vocab_size(self) -> int:
        """Return vocabulary size."""
        return len(self.vocab)

    def get_stats(self) -> Dict[str, Any]:
        """Get encoder statistics."""
        domain_counts = {d: len(pids) for d, pids in self.vocab.domain_patterns.items()}
        return {
            "vocab_size": len(self.vocab),
            "embed_dim": self.embed_dim,
            "domains": domain_counts,
        }


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    dot = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))
    if norm1 > 0 and norm2 > 0:
        return dot / (norm1 * norm2)
    return 0.0


if __name__ == "__main__":
    # Demo/test when run directly
    print("=" * 60)
    print("PATTERN ENCODER TEST")
    print("=" * 60)

    # Create encoder
    encoder = PatternEncoder(embed_dim=256)

    # Load curriculum
    curriculum_path = Path(__file__).parent.parent.parent / "curriculum"
    if curriculum_path.exists():
        print(f"\nLoading curriculum from: {curriculum_path}")
        patterns_loaded = encoder.load_curriculum(curriculum_path)
        print(f"Loaded {patterns_loaded} patterns")
    else:
        print(f"Curriculum path not found: {curriculum_path}")
        print("Creating sample patterns for testing...")

        # Add some sample patterns for testing
        sample_patterns = [
            Pattern("noun_def", "A noun is a word that represents a person, place, thing, or idea", "english", "definition"),
            Pattern("verb_def", "A verb is a word that expresses an action or state of being", "english", "definition"),
            Pattern("python_func", "A function in Python is defined using the def keyword followed by the function name and parameters", "python", "definition"),
            Pattern("for_loop", "A for loop iterates over a sequence and executes code for each item", "python", "definition"),
        ]
        for p in sample_patterns:
            encoder.vocab.add_pattern(p)

    print(f"\nVocabulary size: {encoder.get_vocab_size()}")
    print(f"Embedding dimension: {encoder.embed_dim}")

    # Test encoding
    test_questions = [
        "What is a noun?",
        "How do I create a function in Python?",
        "What is the capital of France?",
    ]

    print("\n" + "=" * 60)
    print("ENCODING TESTS")
    print("=" * 60)

    for question in test_questions:
        print(f"\nQuestion: {question}")
        vector = encoder.encode(question)
        print(f"Vector shape: {len(vector)}")
        print(f"Vector sample: [{', '.join(f'{v:.3f}' for v in vector[:5])}, ...]")

        # Test decoding
        matches = encoder.decode(vector, top_k=3)
        print("Top matches:")
        for pattern, score in matches:
            print(f"  [{score:.3f}] {pattern.text[:60]}...")

    print("\n" + "=" * 60)
    print("ENCODER READY FOR TRAINING")
    print("=" * 60)
