"""
RPA Attention Mechanism - Multi-Head Self-Attention

The core of transformer models. Allows the model to:
- "Look at" different parts of the input
- Learn which tokens are related
- Build contextual representations

Scaled Dot-Product Attention:
    Attention(Q, K, V) = softmax(Q @ K^T / sqrt(d_k)) @ V

Multi-Head Attention:
    Split Q, K, V into multiple heads
    Apply attention in parallel
    Concatenate and project
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Tuple


class MultiHeadAttention(nn.Module):
    """
    Multi-Head Self-Attention.
    
    Each head can focus on different types of relationships:
    - Head 1: Syntax (subject-verb)
    - Head 2: Semantics (related concepts)
    - Head 3: Position (nearby tokens)
    - etc.
    
    Args:
        d_model: Model dimension
        num_heads: Number of attention heads
        dropout: Dropout probability
    """
    
    def __init__(
        self,
        d_model: int = 256,
        num_heads: int = 8,
        dropout: float = 0.1,
    ):
        super().__init__()
        
        assert d_model % num_heads == 0, "d_model must be divisible by num_heads"
        
        self.d_model = d_model
        self.num_heads = num_heads
        self.head_dim = d_model // num_heads
        self.scale = self.head_dim ** -0.5
        
        # Q, K, V projections
        self.q_proj = nn.Linear(d_model, d_model, bias=False)
        self.k_proj = nn.Linear(d_model, d_model, bias=False)
        self.v_proj = nn.Linear(d_model, d_model, bias=False)
        
        # Output projection
        self.out_proj = nn.Linear(d_model, d_model, bias=False)
        
        # Dropout
        self.dropout = nn.Dropout(dropout)
        
        # Initialize weights
        self._init_weights()
    
    def _init_weights(self):
        """Initialize weights."""
        nn.init.normal_(self.q_proj.weight, mean=0.0, std=0.02)
        nn.init.normal_(self.k_proj.weight, mean=0.0, std=0.02)
        nn.init.normal_(self.v_proj.weight, mean=0.0, std=0.02)
        nn.init.normal_(self.out_proj.weight, mean=0.0, std=0.02)
    
    def forward(
        self,
        x: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
        kv_cache: Optional[Tuple[torch.Tensor, torch.Tensor]] = None,
        use_cache: bool = False,
    ) -> Tuple[torch.Tensor, Optional[Tuple[torch.Tensor, torch.Tensor]]]:
        """
        Forward pass.
        
        Args:
            x: (batch_size, seq_len, d_model) input tensor
            mask: Optional attention mask
            kv_cache: Optional key-value cache for inference
            use_cache: Whether to return kv_cache
            
        Returns:
            output: (batch_size, seq_len, d_model)
            kv_cache: Optional cache for inference
        """
        batch_size, seq_len, _ = x.shape
        
        # Project to Q, K, V
        q = self.q_proj(x)
        k = self.k_proj(x)
        v = self.v_proj(x)
        
        # Use cache for inference (for autoregressive generation)
        if kv_cache is not None:
            k_cache, v_cache = kv_cache
            k = torch.cat([k_cache, k], dim=1)
            v = torch.cat([v_cache, v], dim=1)
        
        # Store new cache
        new_cache = (k, v) if use_cache else None
        
        # Reshape for multi-head attention
        # (batch, seq, d_model) -> (batch, heads, seq, head_dim)
        q = q.view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        k = k.view(batch_size, -1, self.num_heads, self.head_dim).transpose(1, 2)
        v = v.view(batch_size, -1, self.num_heads, self.head_dim).transpose(1, 2)
        
        # Compute attention scores
        # (batch, heads, seq, head_dim) @ (batch, heads, head_dim, seq) -> (batch, heads, seq, seq)
        attn_scores = torch.matmul(q, k.transpose(-2, -1)) * self.scale
        
        # Apply causal mask (for autoregressive language modeling)
        if mask is not None:
            attn_scores = attn_scores + mask
        
        # Softmax
        attn_probs = F.softmax(attn_scores, dim=-1)
        attn_probs = self.dropout(attn_probs)
        
        # Apply attention to values
        # (batch, heads, seq, seq) @ (batch, heads, seq, head_dim) -> (batch, heads, seq, head_dim)
        attn_output = torch.matmul(attn_probs, v)
        
        # Reshape back
        # (batch, heads, seq, head_dim) -> (batch, seq, d_model)
        attn_output = attn_output.transpose(1, 2).contiguous().view(batch_size, seq_len, self.d_model)
        
        # Output projection
        output = self.out_proj(attn_output)
        
        return output, new_cache


class CausalSelfAttention(nn.Module):
    """
    Causal Self-Attention for autoregressive language modeling.
    
    Each token can only attend to previous tokens (and itself).
    This is what GPT uses for next-token prediction.
    """
    
    def __init__(
        self,
        d_model: int = 256,
        num_heads: int = 8,
        max_seq_len: int = 512,
        dropout: float = 0.1,
    ):
        super().__init__()
        
        self.attention = MultiHeadAttention(d_model, num_heads, dropout)
        
        # Create causal mask
        # Lower triangular matrix: each row can only see columns to its left
        self.register_buffer(
            "causal_mask",
            torch.tril(torch.ones(max_seq_len, max_seq_len)).view(1, 1, max_seq_len, max_seq_len)
        )
    
    def forward(
        self,
        x: torch.Tensor,
        kv_cache: Optional[Tuple[torch.Tensor, torch.Tensor]] = None,
        use_cache: bool = False,
    ) -> Tuple[torch.Tensor, Optional[Tuple[torch.Tensor, torch.Tensor]]]:
        """
        Forward pass with causal masking.
        
        Args:
            x: (batch_size, seq_len, d_model) input
            kv_cache: Optional cache for inference
            use_cache: Whether to return cache
            
        Returns:
            output and optional cache
        """
        batch_size, seq_len, _ = x.shape
        
        # Get causal mask for this sequence length
        mask = self.causal_mask[:, :, :seq_len, :seq_len]
        
        # Convert to attention mask format (0 for attend, -inf for mask)
        mask = (1.0 - mask) * -1e9
        
        # Apply attention
        return self.attention(x, mask=mask, kv_cache=kv_cache, use_cache=use_cache)


class CrossAttention(nn.Module):
    """
    Cross-Attention for encoder-decoder or retrieval augmentation.
    
    Query comes from one source (decoder/query)
    Key, Value come from another source (encoder/documents)
    """
    
    def __init__(
        self,
        d_model: int = 256,
        num_heads: int = 8,
        dropout: float = 0.1,
    ):
        super().__init__()
        
        self.d_model = d_model
        self.num_heads = num_heads
        self.head_dim = d_model // num_heads
        self.scale = self.head_dim ** -0.5
        
        # Q projection (from query)
        self.q_proj = nn.Linear(d_model, d_model, bias=False)
        
        # K, V projections (from context)
        self.k_proj = nn.Linear(d_model, d_model, bias=False)
        self.v_proj = nn.Linear(d_model, d_model, bias=False)
        
        # Output projection
        self.out_proj = nn.Linear(d_model, d_model, bias=False)
        
        self.dropout = nn.Dropout(dropout)
        
        self._init_weights()
    
    def _init_weights(self):
        nn.init.normal_(self.q_proj.weight, mean=0.0, std=0.02)
        nn.init.normal_(self.k_proj.weight, mean=0.0, std=0.02)
        nn.init.normal_(self.v_proj.weight, mean=0.0, std=0.02)
        nn.init.normal_(self.out_proj.weight, mean=0.0, std=0.02)
    
    def forward(
        self,
        query: torch.Tensor,
        context: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """
        Cross-attention forward pass.
        
        Args:
            query: (batch, query_len, d_model)
            context: (batch, context_len, d_model)
            mask: Optional context mask
            
        Returns:
            (batch, query_len, d_model)
        """
        batch_size, query_len, _ = query.shape
        context_len = context.shape[1]
        
        # Project
        q = self.q_proj(query)
        k = self.k_proj(context)
        v = self.v_proj(context)
        
        # Reshape for multi-head
        q = q.view(batch_size, query_len, self.num_heads, self.head_dim).transpose(1, 2)
        k = k.view(batch_size, context_len, self.num_heads, self.head_dim).transpose(1, 2)
        v = v.view(batch_size, context_len, self.num_heads, self.head_dim).transpose(1, 2)
        
        # Attention scores
        attn_scores = torch.matmul(q, k.transpose(-2, -1)) * self.scale
        
        if mask is not None:
            attn_scores = attn_scores + mask
        
        attn_probs = F.softmax(attn_scores, dim=-1)
        attn_probs = self.dropout(attn_probs)
        
        # Apply to values
        attn_output = torch.matmul(attn_probs, v)
        
        # Reshape back
        attn_output = attn_output.transpose(1, 2).contiguous().view(batch_size, query_len, self.d_model)
        
        return self.out_proj(attn_output)


if __name__ == "__main__":
    print("=" * 60)
    print("ATTENTION MECHANISM TEST")
    print("=" * 60)
    
    # Test multi-head attention
    d_model = 64
    num_heads = 4
    batch_size = 2
    seq_len = 10
    
    attention = MultiHeadAttention(d_model, num_heads)
    
    # Random input
    x = torch.randn(batch_size, seq_len, d_model)
    
    # Forward pass
    output, _ = attention(x)
    
    print(f"Input shape: {x.shape}")
    print(f"Output shape: {output.shape}")
    print(f"Expected: ({batch_size}, {seq_len}, {d_model})")
    
    # Test causal attention
    print("\n[Causal Self-Attention]")
    causal_attn = CausalSelfAttention(d_model, num_heads, max_seq_len=20)
    output, _ = causal_attn(x)
    print(f"Output shape: {output.shape}")
    
    # Parameters
    num_params = sum(p.numel() for p in attention.parameters())
    print(f"\nParameters: {num_params:,}")
    
    print("\n" + "=" * 60)
    print("ATTENTION WORKING!")
    print("=" * 60)
