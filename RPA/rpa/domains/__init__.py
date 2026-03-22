"""
Domain-specific learning modules for RPA.

This package contains specialized learning modules for different domains:
- english: English language learning (vocabulary, grammar, reading, writing)
- coding: Programming language learning (Python, JavaScript, etc.)
"""

from rpa.domains.english import (
    EnglishDomain,
    VocabularyTrainer,
    GrammarEngine,
    ReadingComprehension,
    WritingAssessor,
)

__all__ = [
    "EnglishDomain",
    "VocabularyTrainer",
    "GrammarEngine",
    "ReadingComprehension",
    "WritingAssessor",
]
