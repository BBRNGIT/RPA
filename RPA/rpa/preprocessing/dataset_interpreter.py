"""
Dataset Interpreter - Convert datasets into curriculum format.

Interprets text, code, and structured data into patterns
suitable for RPA learning.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set
from collections import Counter
import re
import logging

from .dataset_loader import DatasetConfig

logger = logging.getLogger(__name__)


@dataclass
class InterpretedSequence:
    """A sequence interpreted from a dataset, ready for curriculum packaging."""
    content: str
    sequence_type: str  # "primitive", "pattern", "sequence", "concept"
    hierarchy_level: int
    composition: List[str]
    domain: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    source: str = ""
    frequency: int = 1
    quality_score: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "content": self.content,
            "type": self.sequence_type,
            "hierarchy_level": self.hierarchy_level,
            "composition": self.composition,
            "domain": self.domain,
            "metadata": self.metadata,
            "source": self.source,
            "frequency": self.frequency,
            "quality_score": self.quality_score
        }


class DatasetInterpreter:
    """
    Interpret datasets into curriculum-ready sequences.

    Supports:
    - Text datasets (words, sentences, paragraphs)
    - Code datasets (tokens, expressions, statements)
    - Structured datasets (relationships, hierarchies)
    """

    def __init__(self):
        """Initialize DatasetInterpreter."""
        # Common English word boundaries
        self._word_pattern = re.compile(r'\b\w+\b')
        self._sentence_pattern = re.compile(r'[.!?]+\s*')

        # Code tokenization patterns
        self._code_token_patterns = {
            "python": re.compile(r'(\w+|[^\w\s]|\s+)'),
            "javascript": re.compile(r'(\w+|[^\w\s]|\s+)'),
            "default": re.compile(r'(\w+|[^\w\s]|\s+)')
        }

        # Known primitives
        self._primitives: Set[str] = set()

    def interpret_text_dataset(
        self,
        samples: List[Dict[str, Any]],
        config: DatasetConfig
    ) -> List[InterpretedSequence]:
        """
        Interpret text samples into curriculum sequences.

        Segments by hierarchy:
        - Level 0: Characters/letters (primitives)
        - Level 1: Words
        - Level 2: Sentences
        - Level 3: Paragraphs

        Args:
            samples: List of text samples
            config: Dataset configuration

        Returns:
            List of interpreted sequences
        """
        sequences = []
        seen_words: Set[str] = set()
        seen_sentences: Set[str] = set()

        text_field = config.text_field

        for sample in samples:
            text = sample.get(text_field, "")
            if not text:
                continue

            # Extract characters as primitives
            chars = set(text)
            for char in chars:
                if char.isalpha() and char not in self._primitives:
                    self._primitives.add(char.lower())

            # Extract words (hierarchy level 1)
            words = self._word_pattern.findall(text)
            for word in words:
                word_lower = word.lower()
                if word_lower not in seen_words and len(word_lower) >= config.min_length:
                    seen_words.add(word_lower)
                    sequences.append(InterpretedSequence(
                        content=word_lower,
                        sequence_type="pattern",
                        hierarchy_level=1,
                        composition=list(word_lower),
                        domain=config.domain,
                        source=config.dataset_name,
                        metadata={"original_case": word}
                    ))

            # Extract sentences (hierarchy level 2)
            sentences = self._sentence_pattern.split(text)
            for sentence in sentences:
                sentence = sentence.strip()
                if (len(sentence) >= 10 and
                    sentence not in seen_sentences and
                    len(sentence) <= config.max_length):
                    seen_sentences.add(sentence)
                    word_list = [w.lower() for w in self._word_pattern.findall(sentence)]
                    sequences.append(InterpretedSequence(
                        content=sentence,
                        sequence_type="sequence",
                        hierarchy_level=2,
                        composition=word_list,
                        domain=config.domain,
                        source=config.dataset_name,
                        metadata={"word_count": len(word_list)}
                    ))

        # Add primitives at the end (they're the foundation)
        for char in sorted(self._primitives):
            sequences.insert(0, InterpretedSequence(
                content=char,
                sequence_type="primitive",
                hierarchy_level=0,
                composition=[char],
                domain=config.domain,
                source=config.dataset_name
            ))

        logger.info(f"Interpreted {len(sequences)} sequences from text dataset")
        return sequences

    def interpret_code_dataset(
        self,
        samples: List[Dict[str, Any]],
        config: DatasetConfig,
        language: Optional[str] = None
    ) -> List[InterpretedSequence]:
        """
        Interpret code samples into curriculum sequences.

        Segments by hierarchy:
        - Level 0: Tokens/keywords (primitives)
        - Level 1: Expressions
        - Level 2: Statements
        - Level 3: Functions/blocks

        Args:
            samples: List of code samples
            config: Dataset configuration
            language: Programming language (defaults to config.domain)

        Returns:
            List of interpreted sequences
        """
        if language is None:
            language = config.domain

        sequences = []
        seen_tokens: Set[str] = set()
        seen_expressions: Set[str] = set()
        seen_statements: Set[str] = set()

        text_field = config.text_field
        token_pattern = self._code_token_patterns.get(
            language,
            self._code_token_patterns["default"]
        )

        # Common keywords for different languages
        keywords = self._get_language_keywords(language)

        for sample in samples:
            code = sample.get(text_field, "")
            if not code:
                continue

            # Extract tokens (hierarchy level 0 - primitives)
            tokens = [t.strip() for t in token_pattern.findall(code) if t.strip()]
            for token in tokens:
                if token not in seen_tokens and len(token) >= 1:
                    seen_tokens.add(token)
                    is_keyword = token in keywords
                    sequences.append(InterpretedSequence(
                        content=token,
                        sequence_type="primitive",
                        hierarchy_level=0,
                        composition=[token],
                        domain=config.domain,
                        source=config.dataset_name,
                        metadata={"is_keyword": is_keyword}
                    ))

            # Extract single-line expressions/statements
            lines = code.split("\n")
            for line in lines:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                # Simple expression detection
                if len(line) <= 50 and "=" not in line and "(" not in line:
                    if line not in seen_expressions:
                        seen_expressions.add(line)
                        expr_tokens = [t.strip() for t in token_pattern.findall(line) if t.strip()]
                        sequences.append(InterpretedSequence(
                            content=line,
                            sequence_type="pattern",
                            hierarchy_level=1,
                            composition=expr_tokens,
                            domain=config.domain,
                            source=config.dataset_name,
                            metadata={"line_type": "expression"}
                        ))

                # Statement detection (assignments, function calls)
                elif len(line) <= 100:
                    if line not in seen_statements:
                        seen_statements.add(line)
                        stmt_tokens = [t.strip() for t in token_pattern.findall(line) if t.strip()]
                        sequences.append(InterpretedSequence(
                            content=line,
                            sequence_type="sequence",
                            hierarchy_level=2,
                            composition=stmt_tokens,
                            domain=config.domain,
                            source=config.dataset_name,
                            metadata={"line_type": "statement"}
                        ))

        logger.info(f"Interpreted {len(sequences)} sequences from code dataset")
        return sequences

    def interpret_structured_dataset(
        self,
        samples: List[Dict[str, Any]],
        config: DatasetConfig
    ) -> List[InterpretedSequence]:
        """
        Interpret structured data into curriculum sequences.

        Extracts:
        - Key-value relationships
        - Hierarchies
        - Patterns from structured fields

        Args:
            samples: List of structured samples
            config: Dataset configuration

        Returns:
            List of interpreted sequences
        """
        sequences = []
        seen_keys: Set[str] = set()

        for sample in samples:
            for key, value in sample.items():
                # Track unique keys as concepts
                if key not in seen_keys:
                    seen_keys.add(key)
                    sequences.append(InterpretedSequence(
                        content=key,
                        sequence_type="concept",
                        hierarchy_level=0,
                        composition=list(key),
                        domain=config.domain,
                        source=config.dataset_name,
                        metadata={"field_type": "key"}
                    ))

                # Extract value patterns
                if isinstance(value, str) and len(value) >= config.min_length:
                    sequences.append(InterpretedSequence(
                        content=value,
                        sequence_type="pattern",
                        hierarchy_level=1,
                        composition=[value],
                        domain=config.domain,
                        source=config.dataset_name,
                        metadata={"key": key}
                    ))

        logger.info(f"Interpreted {len(sequences)} sequences from structured dataset")
        return sequences

    def filter_by_quality(
        self,
        sequences: List[InterpretedSequence],
        min_quality: float = 0.5,
        min_length: int = 1,
        max_length: int = 1000
    ) -> List[InterpretedSequence]:
        """
        Filter sequences by quality and length criteria.

        Args:
            sequences: List of sequences to filter
            min_quality: Minimum quality score (0.0-1.0)
            min_length: Minimum content length
            max_length: Maximum content length

        Returns:
            Filtered list of sequences
        """
        filtered = []

        for seq in sequences:
            # Quality filter
            if seq.quality_score < min_quality:
                continue

            # Length filter
            length = len(seq.content)
            if length < min_length or length > max_length:
                continue

            # Remove malformed content
            if not seq.content.strip():
                continue

            # Check for valid UTF-8
            try:
                seq.content.encode('utf-8').decode('utf-8')
            except UnicodeError:
                continue

            filtered.append(seq)

        return filtered

    def rank_by_frequency(
        self,
        sequences: List[InterpretedSequence]
    ) -> List[InterpretedSequence]:
        """
        Rank sequences by frequency of occurrence.

        Higher frequency sequences are prioritized for early learning.

        Args:
            sequences: List of sequences to rank

        Returns:
            Ranked list of sequences (highest frequency first)
        """
        # Count content occurrences
        content_counts: Counter = Counter()
        for seq in sequences:
            content_counts[seq.content] += 1

        # Update frequencies and sort
        for seq in sequences:
            seq.frequency = content_counts[seq.content]

        # Sort by frequency (descending), then by hierarchy level (ascending)
        return sorted(
            sequences,
            key=lambda s: (-s.frequency, s.hierarchy_level)
        )

    def deduplicate(
        self,
        sequences: List[InterpretedSequence]
    ) -> List[InterpretedSequence]:
        """
        Remove duplicate sequences, keeping the highest quality instance.

        Args:
            sequences: List of sequences

        Returns:
            Deduplicated list
        """
        seen: Dict[str, InterpretedSequence] = {}

        for seq in sequences:
            key = seq.content.lower().strip()
            if key not in seen or seq.quality_score > seen[key].quality_score:
                seen[key] = seq

        return list(seen.values())

    def _get_language_keywords(self, language: str) -> Set[str]:
        """Get keywords for a programming language."""
        keywords = {
            "python": {
                "False", "None", "True", "and", "as", "assert", "async",
                "await", "break", "class", "continue", "def", "del", "elif",
                "else", "except", "finally", "for", "from", "global", "if",
                "import", "in", "is", "lambda", "nonlocal", "not", "or",
                "pass", "raise", "return", "try", "while", "with", "yield"
            },
            "javascript": {
                "break", "case", "catch", "continue", "debugger", "default",
                "delete", "do", "else", "finally", "for", "function", "if",
                "in", "instanceof", "new", "return", "switch", "this", "throw",
                "try", "typeof", "var", "void", "while", "with", "const",
                "let", "class", "export", "extends", "import", "super",
                "yield", "await", "async"
            }
        }
        return keywords.get(language.lower(), set())

    def get_interpretation_statistics(
        self,
        sequences: List[InterpretedSequence]
    ) -> Dict[str, Any]:
        """
        Get statistics about interpreted sequences.

        Args:
            sequences: List of interpreted sequences

        Returns:
            Statistics dictionary
        """
        if not sequences:
            return {
                "total_sequences": 0,
                "by_type": {},
                "by_hierarchy": {},
                "by_domain": {}
            }

        type_counts: Counter = Counter()
        hierarchy_counts: Counter = Counter()
        domain_counts: Counter = Counter()

        for seq in sequences:
            type_counts[seq.sequence_type] += 1
            hierarchy_counts[seq.hierarchy_level] += 1
            domain_counts[seq.domain] += 1

        return {
            "total_sequences": len(sequences),
            "by_type": dict(type_counts),
            "by_hierarchy": dict(hierarchy_counts),
            "by_domain": dict(domain_counts),
            "unique_contents": len(set(s.content for s in sequences)),
            "avg_composition_length": sum(len(s.composition) for s in sequences) / len(sequences)
        }
