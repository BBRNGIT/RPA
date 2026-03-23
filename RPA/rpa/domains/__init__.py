"""
Domain-specific learning modules for RPA.

This package contains specialized learning modules for different domains:
- english: English language learning (vocabulary, grammar, reading, writing)
- coding: Programming language learning (Python, JavaScript, etc.)
- medicine: Medical knowledge (terminology, anatomy, conditions, pharmacology)
"""

from rpa.domains.english import (
    EnglishDomain,
    VocabularyTrainer,
    GrammarEngine,
    ReadingComprehension,
    WritingAssessor,
)

from rpa.domains.medicine import (
    MedicalDomain,
    MedicalTerm,
    AnatomyStructure,
    DiseaseCondition,
    Drug,
    BodySystem,
    MedicalCategory,
    DrugClass,
    MedicalProficiency,
)

__all__ = [
    # English Domain
    "EnglishDomain",
    "VocabularyTrainer",
    "GrammarEngine",
    "ReadingComprehension",
    "WritingAssessor",
    # Medicine Domain
    "MedicalDomain",
    "MedicalTerm",
    "AnatomyStructure",
    "DiseaseCondition",
    "Drug",
    "BodySystem",
    "MedicalCategory",
    "DrugClass",
    "MedicalProficiency",
]
