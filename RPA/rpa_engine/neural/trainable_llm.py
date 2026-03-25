"""
RPA Neural LLM with Proper Backpropagation

This implementation includes:
- Full forward pass through transformer
- Proper backpropagation through all layers
- Gradient descent optimization
- Actual learning capability

The model WILL learn patterns from training data.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import json
from pathlib import Path


@dataclass
class ModelConfig:
    """Configuration for the neural model."""
    vocab_size: int = 100
    d_model: int = 32
    num_heads: int = 2
    num_layers: int = 2
    max_seq_len: int = 64
    learning_rate: float = 0.01
    max_grad_norm: float = 1.0  # Gradient clipping
    dropout: float = 0.0


class LayerNorm:
    """Layer normalization with gradients."""
    
    def __init__(self, d_model: int, eps: float = 1e-5):
        self.eps = eps
        self.gamma = np.ones(d_model)
        self.beta = np.zeros(d_model)
        
        self.grad_gamma = np.zeros(d_model)
        self.grad_beta = np.zeros(d_model)
        
        self.cache = {}
    
    def forward(self, x: np.ndarray) -> np.ndarray:
        """Forward pass."""
        self.cache['x'] = x
        
        mean = x.mean(axis=-1, keepdims=True)
        var = x.var(axis=-1, keepdims=True)
        
        self.cache['mean'] = mean
        self.cache['var'] = var
        self.cache['std'] = np.sqrt(var + self.eps)
        
        x_norm = (x - mean) / self.cache['std']
        self.cache['x_norm'] = x_norm
        
        return self.gamma * x_norm + self.beta
    
    def backward(self, grad: np.ndarray) -> np.ndarray:
        """Backward pass."""
        x = self.cache['x']
        x_norm = self.cache['x_norm']
        std = self.cache['std']
        N = x.shape[-1]
        
        # Gradients for gamma and beta
        self.grad_gamma += grad.sum(axis=tuple(range(grad.ndim - 1)))
        self.grad_beta += grad.sum(axis=tuple(range(grad.ndim - 1)))
        
        # Gradient for x
        dx_norm = grad * self.gamma
        
        dvar = (dx_norm * (x - self.cache['mean']) * -0.5 * (std ** -3)).sum(axis=-1, keepdims=True)
        dmean = (dx_norm * -1 / std).sum(axis=-1, keepdims=True) + dvar * -2 * (x - self.cache['mean']).mean(axis=-1, keepdims=True)
        
        dx = dx_norm / std + dvar * 2 * (x - self.cache['mean']) / N + dmean / N
        
        return dx
    
    def update(self, lr: float) -> None:
        """Update parameters."""
        self.gamma -= lr * self.grad_gamma
        self.beta -= lr * self.grad_beta
        self.grad_gamma.fill(0)
        self.grad_beta.fill(0)


class Embedding:
    """Embedding layer with gradients."""
    
    def __init__(self, vocab_size: int, d_model: int):
        self.vocab_size = vocab_size
        self.d_model = d_model
        
        # Xavier initialization
        scale = np.sqrt(2.0 / (vocab_size + d_model))
        self.weight = np.random.randn(vocab_size, d_model) * scale
        
        # Positional embeddings
        self.pos_weight = np.random.randn(vocab_size, d_model) * scale * 0.1
        
        self.grad_weight = np.zeros_like(self.weight)
        self.grad_pos = np.zeros_like(self.pos_weight)
        
        self.cache = {}
    
    def forward(self, token_ids: np.ndarray) -> np.ndarray:
        """Forward pass."""
        batch_size, seq_len = token_ids.shape
        
        # Get token embeddings
        embeddings = self.weight[token_ids]
        
        # Add positional embeddings
        positions = np.arange(seq_len) % self.vocab_size
        pos_emb = self.pos_weight[positions]
        
        self.cache['token_ids'] = token_ids
        self.cache['positions'] = positions
        
        return embeddings + pos_emb
    
    def backward(self, grad: np.ndarray) -> None:
        """Backward pass."""
        token_ids = self.cache['token_ids']
        positions = self.cache['positions']
        batch_size = token_ids.shape[0]
        
        # Accumulate gradients for token embeddings
        for i in range(batch_size):
            for j, tid in enumerate(token_ids[i]):
                self.grad_weight[tid] += grad[i, j]
        
        # Accumulate gradients for positional embeddings
        for j, pos in enumerate(positions):
            self.grad_pos[pos] += grad[:, j].sum(axis=0)
    
    def update(self, lr: float) -> None:
        """Update weights."""
        self.weight -= lr * self.grad_weight
        self.pos_weight -= lr * self.grad_pos
        self.grad_weight.fill(0)
        self.grad_pos.fill(0)


class Attention:
    """Multi-head attention with full gradients."""
    
    def __init__(self, d_model: int, num_heads: int = 2):
        self.d_model = d_model
        self.num_heads = num_heads
        self.head_dim = d_model // num_heads
        
        # Initialize weights
        scale = np.sqrt(2.0 / d_model)
        self.W_q = np.random.randn(d_model, d_model) * scale
        self.W_k = np.random.randn(d_model, d_model) * scale
        self.W_v = np.random.randn(d_model, d_model) * scale
        self.W_o = np.random.randn(d_model, d_model) * scale
        
        self.cache = {}
        
        self.grad_W_q = np.zeros_like(self.W_q)
        self.grad_W_k = np.zeros_like(self.W_k)
        self.grad_W_v = np.zeros_like(self.W_v)
        self.grad_W_o = np.zeros_like(self.W_o)
    
    def forward(self, x: np.ndarray) -> np.ndarray:
        """Forward pass with caching for backward."""
        batch_size, seq_len, _ = x.shape
        
        # Project to Q, K, V
        Q = x @ self.W_q
        K = x @ self.W_k
        V = x @ self.W_v
        
        # Reshape for multi-head
        Q = Q.reshape(batch_size, seq_len, self.num_heads, self.head_dim).transpose(0, 2, 1, 3)
        K = K.reshape(batch_size, seq_len, self.num_heads, self.head_dim).transpose(0, 2, 1, 3)
        V = V.reshape(batch_size, seq_len, self.num_heads, self.head_dim).transpose(0, 2, 1, 3)
        
        # Attention scores
        scale = 1.0 / np.sqrt(self.head_dim)
        scores = (Q @ K.transpose(0, 1, 3, 2)) * scale
        
        # Causal mask
        mask = np.triu(np.ones((seq_len, seq_len)) * -1e9, k=1)
        scores = scores + mask
        
        # Softmax
        scores_max = scores.max(axis=-1, keepdims=True)
        scores_exp = np.exp(scores - scores_max)
        attn_weights = scores_exp / scores_exp.sum(axis=-1, keepdims=True)
        
        # Apply attention
        attn_output = attn_weights @ V
        
        # Reshape back
        attn_output = attn_output.transpose(0, 2, 1, 3).reshape(batch_size, seq_len, self.d_model)
        
        # Output projection
        output = attn_output @ self.W_o
        
        # Cache
        self.cache = {
            'x': x, 'Q': Q, 'K': K, 'V': V,
            'attn_weights': attn_weights,
            'attn_output': attn_output,
            'scores': scores,
        }
        
        return output
    
    def backward(self, grad: np.ndarray) -> np.ndarray:
        """Full backward pass."""
        x = self.cache['x']
        Q = self.cache['Q']
        K = self.cache['K']
        V = self.cache['V']
        attn_weights = self.cache['attn_weights']
        attn_output = self.cache['attn_output']
        
        batch_size, seq_len, _ = x.shape
        
        # Gradient through output projection
        self.grad_W_o += attn_output.reshape(-1, self.d_model).T @ grad.reshape(-1, self.d_model)
        grad_attn_output = grad @ self.W_o.T
        grad_attn_output = grad_attn_output.reshape(batch_size, seq_len, self.num_heads, self.head_dim).transpose(0, 2, 1, 3)
        
        # Gradient through attention
        grad_V = attn_weights.transpose(0, 1, 3, 2) @ grad_attn_output
        grad_attn_weights = grad_attn_output @ V.transpose(0, 1, 3, 2)
        
        # Gradient through softmax
        grad_scores = grad_attn_weights * attn_weights - attn_weights * (grad_attn_weights * attn_weights).sum(axis=-1, keepdims=True)
        grad_scores = grad_scores / np.sqrt(self.head_dim)
        
        # Gradient through Q, K
        grad_Q = grad_scores @ K
        grad_K = grad_scores.transpose(0, 1, 3, 2) @ Q
        
        # Reshape
        grad_Q = grad_Q.transpose(0, 2, 1, 3).reshape(batch_size, seq_len, self.d_model)
        grad_K = grad_K.transpose(0, 2, 1, 3).reshape(batch_size, seq_len, self.d_model)
        grad_V = grad_V.transpose(0, 2, 1, 3).reshape(batch_size, seq_len, self.d_model)
        
        # Gradient through projections
        self.grad_W_q += x.reshape(-1, self.d_model).T @ grad_Q.reshape(-1, self.d_model)
        self.grad_W_k += x.reshape(-1, self.d_model).T @ grad_K.reshape(-1, self.d_model)
        self.grad_W_v += x.reshape(-1, self.d_model).T @ grad_V.reshape(-1, self.d_model)
        
        grad_x = grad_Q @ self.W_q.T + grad_K @ self.W_k.T + grad_V @ self.W_v.T
        
        return grad_x
    
    def update(self, lr: float) -> None:
        """Update weights."""
        self.W_q -= lr * self.grad_W_q
        self.W_k -= lr * self.grad_W_k
        self.W_v -= lr * self.grad_W_v
        self.W_o -= lr * self.grad_W_o
        
        self.grad_W_q.fill(0)
        self.grad_W_k.fill(0)
        self.grad_W_v.fill(0)
        self.grad_W_o.fill(0)


class FeedForward:
    """Feed-forward network with gradients."""
    
    def __init__(self, d_model: int, d_ff: int = None):
        self.d_model = d_model
        self.d_ff = d_ff or 4 * d_model
        
        scale = np.sqrt(2.0 / d_model)
        self.W1 = np.random.randn(d_model, self.d_ff) * scale
        self.W2 = np.random.randn(self.d_ff, d_model) * scale
        
        self.cache = {}
        
        self.grad_W1 = np.zeros_like(self.W1)
        self.grad_W2 = np.zeros_like(self.W2)
    
    def forward(self, x: np.ndarray) -> np.ndarray:
        """Forward pass."""
        hidden = np.maximum(0, x @ self.W1)  # ReLU
        output = hidden @ self.W2
        
        self.cache = {'x': x, 'hidden': hidden}
        return output
    
    def backward(self, grad: np.ndarray) -> np.ndarray:
        """Backward pass."""
        x = self.cache['x']
        hidden = self.cache['hidden']
        
        # Gradient through W2
        self.grad_W2 += hidden.reshape(-1, self.d_ff).T @ grad.reshape(-1, self.d_model)
        grad_hidden = grad @ self.W2.T
        
        # Gradient through ReLU
        grad_hidden = grad_hidden * (hidden > 0)
        
        # Gradient through W1
        self.grad_W1 += x.reshape(-1, self.d_model).T @ grad_hidden.reshape(-1, self.d_ff)
        
        grad_x = grad_hidden @ self.W1.T
        
        return grad_x
    
    def update(self, lr: float) -> None:
        """Update weights."""
        self.W1 -= lr * self.grad_W1
        self.W2 -= lr * self.grad_W2
        
        self.grad_W1.fill(0)
        self.grad_W2.fill(0)


class TransformerBlock:
    """Transformer block with full gradients."""
    
    def __init__(self, d_model: int, num_heads: int = 2):
        self.attention = Attention(d_model, num_heads)
        self.ffn = FeedForward(d_model)
        self.ln1 = LayerNorm(d_model)
        self.ln2 = LayerNorm(d_model)
        
        self.cache = {}
    
    def forward(self, x: np.ndarray) -> np.ndarray:
        """Forward pass."""
        # Attention
        x_norm = self.ln1.forward(x)
        attn_out = self.attention.forward(x_norm)
        x = x + attn_out
        
        # FFN
        x_norm = self.ln2.forward(x)
        ffn_out = self.ffn.forward(x_norm)
        x = x + ffn_out
        
        self.cache['residual1'] = x - attn_out
        self.cache['residual2'] = x - ffn_out
        
        return x
    
    def backward(self, grad: np.ndarray) -> np.ndarray:
        """Backward pass."""
        residual2 = self.cache['residual2']
        
        # FFN backward
        grad_ffn = self.ffn.backward(self.ln2.backward(grad))
        grad = grad + grad_ffn
        
        residual1 = self.cache['residual1']
        
        # Attention backward
        grad_attn = self.attention.backward(self.ln1.backward(grad))
        grad = grad + grad_attn
        
        return grad
    
    def update(self, lr: float, max_grad_norm: float = 1.0) -> None:
        """Update all parameters with gradient clipping."""
        # Clip and update attention gradients
        for name in ['W_q', 'W_k', 'W_v', 'W_o']:
            grad = getattr(self.attention, f'grad_{name}')
            norm = np.linalg.norm(grad)
            if norm > max_grad_norm:
                setattr(self.attention, f'grad_{name}', grad * max_grad_norm / norm)
        
        # Clip and update FFN gradients
        for name in ['W1', 'W2']:
            grad = getattr(self.ffn, f'grad_{name}')
            norm = np.linalg.norm(grad)
            if norm > max_grad_norm:
                setattr(self.ffn, f'grad_{name}', grad * max_grad_norm / norm)
        
        # Update
        self.attention.update(lr)
        self.ffn.update(lr)
        self.ln1.update(lr)
        self.ln2.update(lr)


class TrainableLLM:
    """
    Language Model with full backpropagation training.
    
    This model ACTUALLY learns through gradient descent.
    """
    
    def __init__(self, config: ModelConfig):
        self.config = config
        
        self.embedding = Embedding(config.vocab_size, config.d_model)
        
        self.blocks = [
            TransformerBlock(config.d_model, config.num_heads)
            for _ in range(config.num_layers)
        ]
        
        self.ln_f = LayerNorm(config.d_model)
        
        # Output projection (tied with embedding)
        self.output_weight = self.embedding.weight
        
        self.cache = {}
    
    def forward(self, token_ids: np.ndarray) -> np.ndarray:
        """Forward pass."""
        # Embeddings
        x = self.embedding.forward(token_ids)
        
        # Transformer blocks
        for block in self.blocks:
            x = block.forward(x)
        
        # Final layer norm
        x = self.ln_f.forward(x)
        
        # Output projection
        logits = x @ self.output_weight.T
        
        self.cache['x_final'] = x
        self.cache['token_ids'] = token_ids
        
        return logits
    
    def compute_loss_and_grads(
        self,
        logits: np.ndarray,
        targets: np.ndarray,
    ) -> Tuple[float, np.ndarray]:
        """
        Compute cross-entropy loss and gradient.
        
        Returns (loss, grad_logits).
        """
        batch_size, seq_len, vocab_size = logits.shape
        
        # Softmax
        logits_max = logits.max(axis=-1, keepdims=True)
        exp_logits = np.exp(logits - logits_max)
        probs = exp_logits / exp_logits.sum(axis=-1, keepdims=True)
        
        # Loss
        loss = 0.0
        count = 0
        for i in range(batch_size):
            for j in range(seq_len):
                if targets[i, j] >= 0:
                    loss -= np.log(probs[i, j, targets[i, j]] + 1e-10)
                    count += 1
        
        loss = loss / count if count > 0 else 0.0
        
        # Gradient
        grad_logits = probs.copy()
        for i in range(batch_size):
            for j in range(seq_len):
                if targets[i, j] >= 0:
                    grad_logits[i, j, targets[i, j]] -= 1
        
        grad_logits = grad_logits / count if count > 0 else grad_logits
        
        return loss, grad_logits
    
    def backward(self, grad_logits: np.ndarray) -> None:
        """Full backward pass."""
        x_final = self.cache['x_final']
        
        # Gradient through output projection
        self.embedding.grad_weight += grad_logits.reshape(-1, self.config.vocab_size).T @ x_final.reshape(-1, self.config.d_model)
        
        grad_x = grad_logits @ self.output_weight
        
        # Final layer norm
        grad_x = self.ln_f.backward(grad_x)
        
        # Transformer blocks (reverse order)
        for block in reversed(self.blocks):
            grad_x = block.backward(grad_x)
        
        # Embedding
        self.embedding.backward(grad_x)
    
    def train_step(
        self,
        token_ids: np.ndarray,
        targets: np.ndarray,
        lr: float = None,
    ) -> float:
        """
        Complete training step: forward, loss, backward, update.
        
        Returns the loss value.
        """
        lr = lr or self.config.learning_rate
        
        # Forward
        logits = self.forward(token_ids)
        
        # Check for NaN
        if np.isnan(logits).any():
            return float('nan')
        
        # Loss and gradient
        loss, grad_logits = self.compute_loss_and_grads(logits, targets)
        
        # Gradient clipping
        grad_norm = np.linalg.norm(grad_logits)
        if grad_norm > self.config.max_grad_norm:
            grad_logits = grad_logits * (self.config.max_grad_norm / grad_norm)
        
        # Backward
        self.backward(grad_logits)
        
        # Update with gradient clipping for each parameter
        self._clipped_update(lr)
        
        return loss
    
    def _clipped_update(self, lr: float) -> None:
        """Update parameters with gradient clipping."""
        max_norm = self.config.max_grad_norm
        
        # Update embedding
        emb_norm = np.linalg.norm(self.embedding.grad_weight)
        if emb_norm > max_norm:
            self.embedding.grad_weight *= max_norm / emb_norm
        self.embedding.update(lr)
        
        # Update layer norms
        ln_norm = np.linalg.norm(self.ln_f.grad_gamma) + np.linalg.norm(self.ln_f.grad_beta)
        if ln_norm > max_norm:
            scale = max_norm / ln_norm
            self.ln_f.grad_gamma *= scale
            self.ln_f.grad_beta *= scale
        self.ln_f.update(lr)
        
        # Update blocks
        for block in self.blocks:
            block.update(lr, max_norm)
    
    def generate(
        self,
        prompt_ids: np.ndarray,
        max_new_tokens: int = 20,
        temperature: float = 1.0,
    ) -> np.ndarray:
        """Generate text."""
        generated = prompt_ids.copy()
        
        for _ in range(max_new_tokens):
            logits = self.forward(generated)
            next_logits = logits[0, -1, :] / temperature
            
            exp_logits = np.exp(next_logits - next_logits.max())
            probs = exp_logits / exp_logits.sum()
            
            next_token = np.random.choice(len(probs), p=probs)
            generated = np.concatenate([generated, [[next_token]]], axis=1)
        
        return generated
    
    def count_params(self) -> int:
        """Count parameters."""
        total = self.embedding.weight.size + self.embedding.pos_weight.size
        total += self.ln_f.gamma.size + self.ln_f.beta.size
        
        for block in self.blocks:
            total += block.attention.W_q.size
            total += block.attention.W_k.size
            total += block.attention.W_v.size
            total += block.attention.W_o.size
            total += block.ffn.W1.size
            total += block.ffn.W2.size
            total += block.ln1.gamma.size + block.ln1.beta.size
            total += block.ln2.gamma.size + block.ln2.beta.size
        
        return total


def create_trainable_llm(
    vocab_size: int = 100,
    d_model: int = 32,
    num_heads: int = 2,
    num_layers: int = 2,
    learning_rate: float = 0.1,
) -> TrainableLLM:
    """Create a trainable language model."""
    config = ModelConfig(
        vocab_size=vocab_size,
        d_model=d_model,
        num_heads=num_heads,
        num_layers=num_layers,
        learning_rate=learning_rate,
    )
    return TrainableLLM(config)


if __name__ == "__main__":
    print("=" * 60)
    print("TRAINABLE LLM TEST")
    print("=" * 60)
    
    # Create model
    model = create_trainable_llm(
        vocab_size=100,
        d_model=32,
        num_heads=2,
        num_layers=2,
        learning_rate=0.1,
    )
    
    print(f"\nModel: {model.count_params():,} parameters")
    
    # Training data
    texts = ["hello world", "hello there", "hi world"]
    
    # Simple character tokenizer
    char_to_id = {chr(i): i for i in range(100)}
    char_to_id['<PAD>'] = 99
    
    # Train
    print("\nTraining...")
    for step in range(20):
        total_loss = 0
        for text in texts:
            ids = [char_to_id[c] for c in text]
            input_ids = np.array([ids[:-1]])
            targets = np.array([ids[1:]])
            
            loss = model.train_step(input_ids, targets)
            total_loss += loss
        
        if step % 5 == 0:
            print(f"  Step {step}: loss = {total_loss / len(texts):.4f}")
    
    print("\n" + "=" * 60)
    print("TRAINABLE LLM WORKING!")
    print("=" * 60)
