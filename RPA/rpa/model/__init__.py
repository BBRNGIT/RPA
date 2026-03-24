"""
RPA Model - The actual AI components.

This module contains the neural network components that power the RPA AI:
- PatternEncoder: Converts curriculum patterns to vector representations
- Attention: Multi-head attention mechanism
- Transformer: Full transformer architecture
- Trainer: Training pipeline
- Inference: Question answering
"""

from .pattern_encoder import PatternEncoder, PatternVocabulary

__all__ = [
    "PatternEncoder",
    "PatternVocabulary",
]
