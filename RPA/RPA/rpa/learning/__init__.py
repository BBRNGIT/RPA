"""
RPA Learning Module - Learning and knowledge management components.

This module provides:
- AnswerIntegrator: Integrate user answers into knowledge
- CorrectionAnalyzer: Analyze and learn from corrections
- RecursiveLinker: Link patterns hierarchically
- ErrorClassifier: Classify and categorize errors
- ErrorCorrector: Suggest and apply error corrections
- AbstractionEngine: Form abstract concepts from patterns
"""

from .answer_integrator import AnswerIntegrator
from .correction_analyzer import CorrectionAnalyzer
from .recursive_linker import RecursiveLinker, LinkResult, CompoundPattern, IntegrityReport
from .error_classifier import ErrorClassifier, ClassifiedError, ErrorPattern
from .error_corrector import ErrorCorrector, Correction, AutomatedFixer
from .abstraction_engine import (
    AbstractionEngine,
    AbstractConcept,
    ConceptHierarchy,
)

__all__ = [
    # Answer Integration
    "AnswerIntegrator",

    # Correction Analysis
    "CorrectionAnalyzer",

    # Recursive Linking
    "RecursiveLinker",
    "LinkResult",
    "CompoundPattern",
    "IntegrityReport",

    # Error Classification
    "ErrorClassifier",
    "ClassifiedError",
    "ErrorPattern",

    # Error Correction
    "ErrorCorrector",
    "Correction",
    "AutomatedFixer",

    # Abstraction
    "AbstractionEngine",
    "AbstractConcept",
    "ConceptHierarchy",
]
