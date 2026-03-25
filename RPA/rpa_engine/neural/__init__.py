"""
RPA Neural LLM - Neural Network Components

This module contains neural network components for building
a real LLM. Currently using numpy for minimal dependencies.

Components:
- CharacterTokenizer: Character-level tokenization
- MinimalLLM: Neural language model with embeddings, attention, and generation
"""

# Import only numpy-based modules
from .tokenizer import CharacterTokenizer, BPETokenizer, TokenizerConfig, create_tokenizer
from .minimal_llm import (
    MinimalLLM,
    ModelConfig,
    Embedding,
    Attention,
    FeedForward,
    TransformerBlock,
    create_minimal_llm,
)

__all__ = [
    # Tokenizer
    "CharacterTokenizer",
    "BPETokenizer",
    "TokenizerConfig",
    "create_tokenizer",
    
    # Model
    "MinimalLLM",
    "ModelConfig",
    "Embedding",
    "Attention",
    "FeedForward",
    "TransformerBlock",
    "create_minimal_llm",
]
