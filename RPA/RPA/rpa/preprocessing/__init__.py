"""
Preprocessing module - Dataset Loading and Curriculum Generation.

This module provides:
- DatasetLoader: Load datasets from HuggingFace and local sources
- DatasetInterpreter: Convert datasets to curriculum format
- DatasetCurriculumBuilder: Create curriculum batches from datasets
- DatasetConfig: Configuration for dataset processing
"""

from .dataset_loader import (
    DatasetLoader,
    DatasetConfig,
    DATASET_CONFIGS
)
from .dataset_interpreter import (
    DatasetInterpreter,
    InterpretedSequence
)
from .dataset_curriculum_builder import (
    DatasetCurriculumBuilder,
    CurriculumBatch
)

__all__ = [
    # Loader
    "DatasetLoader",
    "DatasetConfig",
    "DATASET_CONFIGS",

    # Interpreter
    "DatasetInterpreter",
    "InterpretedSequence",

    # Builder
    "DatasetCurriculumBuilder",
    "CurriculumBatch"
]
