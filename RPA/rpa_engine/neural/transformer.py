"""
RPA Transformer - Full Transformer Architecture

Combines all components into a complete language model:
- Embedding layer
- Multiple transformer blocks (attention + FFN)
- Output layer (language model head)

This is a GPT-style decoder-only transformer for text generation.
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Tuple, List, Dict

from .embeddings import EmbeddingLayer
from .attention import CausalSelfAttention


class FeedForward(nn.Module):
    """
    Position-wise Feed-Forward Network.
    
    Two linear layers with activation in between.
    Expands dimension then compresses back.
    
    FFN(x) = W2(activation(W1(x)))
    
    Standard: d_model -> 4*d_model -> d_model
    """
    
    def __init__(
        self,
        d_model: int = 256,
        d_ff: Optional[int] = None,
        dropout: float = 0.1,
        activation: str = "gelu",
    ):
        super().__init__()
        
        d_ff = d_ff or 4 * d_model
        
        self.w1 = nn.Linear(d_model, d_ff, bias=False)
        self.w2 = nn.Linear(d_ff, d_model, bias=False)
        self.dropout = nn.Dropout(dropout)
        
        # Activation function
        if activation == "gelu":
            self.activation = F.gelu
        elif activation == "relu":
            self.activation = F.relu
        elif activation == "silu" or activation == "swish":
            self.activation = F.silu
        else:
            self.activation = F.gelu
        
        self._init_weights()
    
    def _init_weights(self):
        nn.init.normal_(self.w1.weight, mean=0.0, std=0.02)
        nn.init.normal_(self.w2.weight, mean=0.0, std=0.02)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass."""
        x = self.w1(x)
        x = self.activation(x)
        x = self.dropout(x)
        x = self.w2(x)
        return x


class TransformerBlock(nn.Module):
    """
    Single Transformer Block.
    
    Structure (Pre-LN, as in GPT-2):
    1. LayerNorm -> Self-Attention -> Residual
    2. LayerNorm -> Feed-Forward -> Residual
    
    Pre-LN is more stable for training than Post-LN.
    """
    
    def __init__(
        self,
        d_model: int = 256,
        num_heads: int = 8,
        d_ff: Optional[int] = None,
        max_seq_len: int = 512,
        dropout: float = 0.1,
        activation: str = "gelu",
    ):
        super().__init__()
        
        # Layer norms
        self.ln1 = nn.LayerNorm(d_model)
        self.ln2 = nn.LayerNorm(d_model)
        
        # Attention
        self.attention = CausalSelfAttention(d_model, num_heads, max_seq_len, dropout)
        
        # Feed-forward
        self.ffn = FeedForward(d_model, d_ff, dropout, activation)
        
        # Dropout for residuals
        self.dropout = nn.Dropout(dropout)
    
    def forward(
        self,
        x: torch.Tensor,
        kv_cache: Optional[Tuple[torch.Tensor, torch.Tensor]] = None,
        use_cache: bool = False,
    ) -> Tuple[torch.Tensor, Optional[Tuple[torch.Tensor, torch.Tensor]]]:
        """
        Forward pass.
        
        Args:
            x: (batch, seq, d_model)
            kv_cache: Optional cache for inference
            use_cache: Whether to return cache
            
        Returns:
            output and optional cache
        """
        # Pre-LN + Attention + Residual
        residual = x
        x = self.ln1(x)
        x, cache = self.attention(x, kv_cache, use_cache)
        x = self.dropout(x)
        x = residual + x
        
        # Pre-LN + FFN + Residual
        residual = x
        x = self.ln2(x)
        x = self.ffn(x)
        x = self.dropout(x)
        x = residual + x
        
        return x, cache


class TransformerLM(nn.Module):
    """
    Complete Transformer Language Model.
    
    GPT-style decoder-only transformer for text generation.
    
    Architecture:
    - Token + Position Embeddings
    - N Transformer Blocks
    - Final LayerNorm
    - Language Model Head (project to vocab)
    
    Training: Predict next token
    Inference: Generate text autoregressively
    """
    
    def __init__(
        self,
        vocab_size: int = 100,
        d_model: int = 256,
        num_heads: int = 8,
        num_layers: int = 6,
        d_ff: Optional[int] = None,
        max_seq_len: int = 512,
        dropout: float = 0.1,
        activation: str = "gelu",
    ):
        super().__init__()
        
        self.vocab_size = vocab_size
        self.d_model = d_model
        self.num_heads = num_heads
        self.num_layers = num_layers
        self.max_seq_len = max_seq_len
        
        # Embedding layer
        self.embedding = EmbeddingLayer(vocab_size, d_model, max_seq_len, dropout)
        
        # Transformer blocks
        self.blocks = nn.ModuleList([
            TransformerBlock(d_model, num_heads, d_ff, max_seq_len, dropout, activation)
            for _ in range(num_layers)
        ])
        
        # Final layer norm
        self.ln_f = nn.LayerNorm(d_model)
        
        # Language model head
        self.lm_head = nn.Linear(d_model, vocab_size, bias=False)
        
        # Tie weights (embedding and output share weights)
        self.lm_head.weight = self.embedding.token_embedding.weight
        
        # Initialize weights
        self.apply(self._init_weights)
        
        # Print model info
        self._print_info()
    
    def _init_weights(self, module):
        """Initialize weights."""
        if isinstance(module, nn.Linear):
            nn.init.normal_(module.weight, mean=0.0, std=0.02)
            if module.bias is not None:
                nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            nn.init.normal_(module.weight, mean=0.0, std=0.02)
        elif isinstance(module, nn.LayerNorm):
            nn.init.ones_(module.weight)
            nn.init.zeros_(module.bias)
    
    def _print_info(self):
        """Print model information."""
        num_params = sum(p.numel() for p in self.parameters())
        num_trainable = sum(p.numel() for p in self.parameters() if p.requires_grad)
        
        print(f"[TransformerLM] Initialized:")
        print(f"  Vocab size: {self.vocab_size}")
        print(f"  d_model: {self.d_model}")
        print(f"  num_heads: {self.num_heads}")
        print(f"  num_layers: {self.num_layers}")
        print(f"  max_seq_len: {self.max_seq_len}")
        print(f"  Parameters: {num_params:,} ({num_params / 1e6:.2f}M)")
    
    def forward(
        self,
        input_ids: torch.Tensor,
        labels: Optional[torch.Tensor] = None,
        kv_cache: Optional[List[Tuple[torch.Tensor, torch.Tensor]]] = None,
        use_cache: bool = False,
    ) -> Dict[str, torch.Tensor]:
        """
        Forward pass.
        
        Args:
            input_ids: (batch, seq) token IDs
            labels: Optional (batch, seq) labels for loss computation
            kv_cache: Optional list of caches for each layer
            use_cache: Whether to return caches
            
        Returns:
            Dict with 'logits' and optionally 'loss' and 'kv_cache'
        """
        batch_size, seq_len = input_ids.shape
        
        # Get embeddings
        x = self.embedding(input_ids)
        
        # Apply transformer blocks
        new_cache = [] if use_cache else None
        
        for i, block in enumerate(self.blocks):
            block_cache = kv_cache[i] if kv_cache else None
            x, block_new_cache = block(x, block_cache, use_cache)
            
            if use_cache:
                new_cache.append(block_new_cache)
        
        # Final layer norm
        x = self.ln_f(x)
        
        # Language model head
        logits = self.lm_head(x)
        
        # Prepare output
        output = {"logits": logits}
        
        # Compute loss if labels provided
        if labels is not None:
            # Shift logits and labels for next token prediction
            shift_logits = logits[:, :-1, :].contiguous()
            shift_labels = labels[:, 1:].contiguous()
            
            # Cross entropy loss
            loss = F.cross_entropy(
                shift_logits.view(-1, self.vocab_size),
                shift_labels.view(-1),
                ignore_index=-100,  # Ignore padding
            )
            output["loss"] = loss
        
        if use_cache:
            output["kv_cache"] = new_cache
        
        return output
    
    def get_num_params(self) -> int:
        """Get total number of parameters."""
        return sum(p.numel() for p in self.parameters())
    
    def get_num_trainable_params(self) -> int:
        """Get number of trainable parameters."""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)
    
    def estimate_memory(self, batch_size: int = 1, seq_len: int = 128) -> Dict[str, float]:
        """
        Estimate memory usage.
        
        Returns memory in MB.
        """
        # Parameters
        param_memory = self.get_num_params() * 4 / 1e6  # float32
        
        # Activations (rough estimate)
        activation_memory = batch_size * seq_len * self.d_model * self.num_layers * 4 / 1e6
        
        # Gradients (same as parameters)
        gradient_memory = param_memory
        
        return {
            "parameters_mb": param_memory,
            "activations_mb": activation_memory,
            "gradients_mb": gradient_memory,
            "total_mb": param_memory + activation_memory + gradient_memory,
        }


def create_model(
    vocab_size: int,
    d_model: int = 256,
    num_heads: int = 8,
    num_layers: int = 6,
    max_seq_len: int = 512,
    dropout: float = 0.1,
) -> TransformerLM:
    """Create a transformer language model."""
    return TransformerLM(
        vocab_size=vocab_size,
        d_model=d_model,
        num_heads=num_heads,
        num_layers=num_layers,
        max_seq_len=max_seq_len,
        dropout=dropout,
    )


if __name__ == "__main__":
    print("=" * 60)
    print("TRANSFORMER MODEL TEST")
    print("=" * 60)
    
    # Create model
    vocab_size = 100
    d_model = 64
    num_heads = 4
    num_layers = 2
    
    model = TransformerLM(
        vocab_size=vocab_size,
        d_model=d_model,
        num_heads=num_heads,
        num_layers=num_layers,
        max_seq_len=128,
    )
    
    # Test forward pass
    batch_size = 2
    seq_len = 10
    input_ids = torch.randint(0, vocab_size, (batch_size, seq_len))
    labels = input_ids.clone()
    
    output = model(input_ids, labels=labels)
    
    print(f"\nInput shape: {input_ids.shape}")
    print(f"Logits shape: {output['logits'].shape}")
    print(f"Loss: {output['loss'].item():.4f}")
    
    # Memory estimate
    memory = model.estimate_memory(batch_size=4, seq_len=256)
    print(f"\nMemory estimate (batch=4, seq=256):")
    print(f"  Parameters: {memory['parameters_mb']:.1f} MB")
    print(f"  Total: {memory['total_mb']:.1f} MB")
    
    print("\n" + "=" * 60)
    print("TRANSFORMER MODEL WORKING!")
    print("=" * 60)
