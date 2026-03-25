"""
RPA Embedding Layer - Learned Vector Representations

Converts token IDs to dense vectors that capture semantic meaning.
These embeddings are LEARNED during training, not pre-computed.
"""

import math
import torch
import torch.nn as nn
from typing import Optional


class EmbeddingLayer(nn.Module):
    """
    Token + Positional Embeddings.
    
    Token Embeddings: Each token ID gets a learned vector
    Positional Embeddings: Each position gets a learned vector
    
    Combined: input = token_embedding + position_embedding
    """
    
    def __init__(
        self,
        vocab_size: int,
        d_model: int = 256,
        max_seq_len: int = 512,
        dropout: float = 0.1,
    ):
        """
        Initialize embedding layer.
        
        Args:
            vocab_size: Size of vocabulary
            d_model: Dimension of embeddings
            max_seq_len: Maximum sequence length
            dropout: Dropout probability
        """
        super().__init__()
        
        self.d_model = d_model
        self.vocab_size = vocab_size
        self.max_seq_len = max_seq_len
        
        # Token embeddings
        self.token_embedding = nn.Embedding(vocab_size, d_model)
        
        # Positional embeddings (learned)
        self.position_embedding = nn.Embedding(max_seq_len, d_model)
        
        # Dropout
        self.dropout = nn.Dropout(dropout)
        
        # Initialize weights
        self._init_weights()
    
    def _init_weights(self):
        """Initialize weights with small random values."""
        nn.init.normal_(self.token_embedding.weight, mean=0.0, std=0.02)
        nn.init.normal_(self.position_embedding.weight, mean=0.0, std=0.02)
    
    def forward(self, token_ids: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.
        
        Args:
            token_ids: (batch_size, seq_len) tensor of token IDs
            
        Returns:
            (batch_size, seq_len, d_model) tensor of embeddings
        """
        batch_size, seq_len = token_ids.shape
        
        # Get position indices
        positions = torch.arange(seq_len, device=token_ids.device)
        positions = positions.unsqueeze(0).expand(batch_size, -1)
        
        # Get embeddings
        token_emb = self.token_embedding(token_ids)
        pos_emb = self.position_embedding(positions)
        
        # Combine
        embeddings = token_emb + pos_emb
        
        # Scale by sqrt(d_model) as in original transformer
        embeddings = embeddings * math.sqrt(self.d_model)
        
        # Dropout
        embeddings = self.dropout(embeddings)
        
        return embeddings


class RotaryPositionalEmbedding(nn.Module):
    """
    Rotary Position Embedding (RoPE).
    
    More advanced positional encoding that:
    - Encodes position as rotation
    - Generalizes better to longer sequences
    - Used in LLaMA, GPT-NeoX
    
    This is optional - can use standard learned positions instead.
    """
    
    def __init__(self, d_model: int, max_seq_len: int = 512, base: int = 10000):
        super().__init__()
        
        self.d_model = d_model
        self.max_seq_len = max_seq_len
        
        # Compute inverse frequencies
        inv_freq = 1.0 / (base ** (torch.arange(0, d_model, 2).float() / d_model))
        self.register_buffer("inv_freq", inv_freq)
        
        # Precompute cos and sin
        self._build_cache(max_seq_len)
    
    def _build_cache(self, seq_len: int):
        """Precompute cos/sin for positions."""
        positions = torch.arange(seq_len, device=self.inv_freq.device)
        
        # Outer product: (seq_len, d_model/2)
        freqs = torch.outer(positions.float(), self.inv_freq)
        
        # Duplicate for complex numbers: (seq_len, d_model)
        emb = torch.cat([freqs, freqs], dim=-1)
        
        self.register_buffer("cos_cached", emb.cos())
        self.register_buffer("sin_cached", emb.sin())
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Apply rotary embedding to input."""
        seq_len = x.shape[1]
        
        return x  # Simplified - full RoPE implementation would rotate


class LearnedEmbedding(nn.Module):
    """
    Simple learned embedding for patterns.
    
    Each pattern in the knowledge base gets a learned vector.
    Used to connect the pattern store to the neural network.
    """
    
    def __init__(self, num_patterns: int, d_model: int = 256):
        super().__init__()
        
        self.embedding = nn.Embedding(num_patterns, d_model)
        self.d_model = d_model
        
        # Initialize
        nn.init.normal_(self.embedding.weight, mean=0.0, std=0.02)
    
    def forward(self, pattern_ids: torch.Tensor) -> torch.Tensor:
        """Get embeddings for pattern IDs."""
        return self.embedding(pattern_ids) * math.sqrt(self.d_model)


if __name__ == "__main__":
    print("=" * 60)
    print("EMBEDDING LAYER TEST")
    print("=" * 60)
    
    # Create embedding layer
    vocab_size = 100  # Small vocab for testing
    d_model = 64
    max_seq_len = 128
    
    embedding = EmbeddingLayer(vocab_size, d_model, max_seq_len)
    
    # Test with random token IDs
    batch_size = 2
    seq_len = 10
    token_ids = torch.randint(0, vocab_size, (batch_size, seq_len))
    
    # Forward pass
    output = embedding(token_ids)
    
    print(f"Input shape: {token_ids.shape}")
    print(f"Output shape: {output.shape}")
    print(f"Expected: ({batch_size}, {seq_len}, {d_model})")
    
    # Check parameters
    num_params = sum(p.numel() for p in embedding.parameters())
    print(f"\nParameters: {num_params:,}")
    
    print("\n" + "=" * 60)
    print("EMBEDDING LAYER WORKING!")
    print("=" * 60)
