"""
Domain-specific learning modules for RPA.

This package contains specialized learning modules for different domains:
- english: English language learning (vocabulary, grammar, reading, writing)
- coding: Programming language learning (Python, JavaScript, etc.)
- medicine: Medical knowledge (terminology, anatomy, conditions, pharmacology)
- health: Health and wellness (nutrition, exercise, mental health, preventive care)
- finance: Finance and economics (terminology, investing, accounting, indicators)
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

from rpa.domains.health import (
    HealthDomain,
    Nutrient,
    Food,
    Exercise,
    MentalHealthConcept,
    HealthCategory,
    NutrientType,
    ExerciseType,
    MentalHealthTopic,
    HealthProficiency,
)

from rpa.domains.finance import (
    FinanceDomain,
    FinancialTerm,
    FinancialRatio,
    InvestmentConcept,
    EconomicIndicator,
    FinancialCategory,
    FinancialRatioType,
    AssetClass,
    EconomicIndicatorType,
    FinanceProficiency,
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
    # Health Domain
    "HealthDomain",
    "Nutrient",
    "Food",
    "Exercise",
    "MentalHealthConcept",
    "HealthCategory",
    "NutrientType",
    "ExerciseType",
    "MentalHealthTopic",
    "HealthProficiency",
    # Finance Domain
    "FinanceDomain",
    "FinancialTerm",
    "FinancialRatio",
    "InvestmentConcept",
    "EconomicIndicator",
    "FinancialCategory",
    "FinancialRatioType",
    "AssetClass",
    "EconomicIndicatorType",
    "FinanceProficiency",
]
