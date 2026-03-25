#!/usr/bin/env python3
"""
RPA LLM Full Training Pipeline

Features:
- Scaled architecture (500K params)
- All curriculum data loading
- 100+ epochs with LR scheduler
- Temperature and top-k sampling
- Model weight export for JS
- Backend API ready
"""

import sys
import os
import json
import glob
import time
import math
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rpa_engine.neural.trainable_llm import TrainableLLM, ModelConfig


# ============================================================================
# ENHANCED TOKENIZER
# ============================================================================

class CharTokenizer:
    """Character-level tokenizer - NO word-piece!"""
    
    def __init__(self):
        # Full printable ASCII + common unicode + special
        self.chars = list(
            ' !"#$%&\'()*+,-./0123456789:;<=>?@'
            'ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`'
            'abcdefghijklmnopqrstuvwxyz{|}~'
            '\n\r\t'
        )
        self.char_to_id = {c: i for i, c in enumerate(self.chars)}
        self.pad_id = len(self.chars)
        self.unk_id = len(self.chars) + 1
        self.chars.append('<PAD>')
        self.chars.append('<UNK>')
        self.vocab_size = len(self.chars)
        
    def encode(self, text: str) -> List[int]:
        return [self.char_to_id.get(c, self.unk_id) for c in text]
    
    def decode(self, ids: List[int]) -> str:
        return ''.join(
            self.chars[i] if 0 <= i < len(self.chars) else '' 
            for i in ids
        )


# ============================================================================
# CURRICULUM DATA LOADER
# ============================================================================

def load_all_curriculum(curriculum_dir: str) -> List[str]:
    """Load ALL curriculum data from all domains."""
    texts = []
    curriculum_path = Path(curriculum_dir)
    
    domains = [
        'coding', 'finance', 'python', 'english', 'reasoning',
        'health', 'medicine', 'skills', 'generated', 'tracks'
    ]
    
    print(f"\n📚 Loading curriculum from: {curriculum_path}")
    total_files = 0
    
    for domain in domains:
        domain_path = curriculum_path / domain
        if not domain_path.exists():
            continue
        
        json_files = list(domain_path.glob('**/*.json'))
        if not json_files:
            continue
            
        domain_count = 0
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                extracted = extract_text_from_json(data)
                texts.extend(extracted)
                domain_count += len(extracted)
                total_files += 1
                
            except Exception as e:
                pass  # Skip problematic files
        
        if domain_count > 0:
            print(f"  {domain}: {domain_count} samples from {len(json_files)} files")
    
    print(f"\n✅ Total: {len(texts)} text samples from {total_files} files")
    return texts


def extract_text_from_json(data) -> List[str]:
    """Extract all text content from various JSON structures."""
    texts = []
    
    if isinstance(data, list):
        for item in data:
            texts.extend(extract_text_from_json(item))
    elif isinstance(data, dict):
        # Known text fields
        text_keys = ['pattern', 'text', 'question', 'answer', 'code', 
                     'example', 'word', 'definition', 'description',
                     'title', 'content', 'prompt', 'response',
                     'statement', 'explanation', 'concept', 'term']
        
        for key in text_keys:
            if key in data and isinstance(data[key], str):
                texts.append(data[key])
        
        # Recurse into nested structures
        for value in data.values():
            texts.extend(extract_text_from_json(value))
    
    return texts


# ============================================================================
# TRAINING UTILITIES
# ============================================================================

def create_batches(
    texts: List[str],
    tokenizer: CharTokenizer,
    seq_len: int = 64,
    batch_size: int = 1
) -> List[Tuple[np.ndarray, np.ndarray]]:
    """Create training batches from texts."""
    batches = []
    
    for text in texts:
        if len(text) < 2:
            continue
        
        ids = tokenizer.encode(text)
        
        # Split into overlapping sequences
        for i in range(0, len(ids) - seq_len, seq_len // 2):
            seq = ids[i:i + seq_len + 1]
            if len(seq) < 2:
                continue
            
            input_ids = np.array([seq[:-1]])
            target_ids = np.array([seq[1:]])
            batches.append((input_ids, target_ids))
    
    return batches


def get_lr(step: int, warmup: int, max_lr: float, min_lr: float, total_steps: int) -> float:
    """Cosine learning rate schedule with warmup."""
    if step < warmup:
        return max_lr * step / warmup
    
    progress = (step - warmup) / (total_steps - warmup)
    return min_lr + 0.5 * (max_lr - min_lr) * (1 + math.cos(math.pi * progress))


# ============================================================================
# ENHANCED MODEL WITH TOP-K SAMPLING
# ============================================================================

def generate_with_sampling(
    model: TrainableLLM,
    tokenizer: CharTokenizer,
    prompt: str,
    max_new_tokens: int = 50,
    temperature: float = 0.8,
    top_k: int = 40,
) -> str:
    """Generate with temperature and top-k sampling."""
    tokens = tokenizer.encode(prompt)
    
    for _ in range(max_new_tokens):
        # Truncate to max context
        context = tokens[-model.config.max_seq_len:]
        input_ids = np.array([context])
        
        # Forward pass
        logits = model.forward(input_ids)
        last_logits = logits[0, -1, :]
        
        # Apply temperature
        scaled = last_logits / temperature
        
        # Top-k filtering
        if top_k > 0 and top_k < len(scaled):
            indices = np.argsort(scaled)[::-1]
            threshold = scaled[indices[top_k]]
            scaled = np.where(scaled < threshold, -float('inf'), scaled)
        
        # Softmax
        exp_logits = np.exp(scaled - np.max(scaled))
        probs = exp_logits / exp_logits.sum()
        
        # Sample
        next_token = np.random.choice(len(probs), p=probs)
        tokens.append(int(next_token))
    
    return tokenizer.decode(tokens)


# ============================================================================
# MODEL EXPORT
# ============================================================================

def export_model(
    model: TrainableLLM,
    tokenizer: CharTokenizer,
    output_path: str,
    training_stats: dict = None
):
    """Export model weights to JSON for JS inference."""
    print(f"\n💾 Exporting model to {output_path}...")
    
    weights = {
        'config': {
            'vocab_size': model.config.vocab_size,
            'd_model': model.config.d_model,
            'num_heads': model.config.num_heads,
            'num_layers': model.config.num_layers,
            'max_seq_len': model.config.max_seq_len,
        },
        'tokenizer': {
            'chars': tokenizer.chars,
            'vocab_size': tokenizer.vocab_size,
        },
        'embedding': {
            'weight': model.embedding.weight.tolist(),
            'pos_weight': model.embedding.pos_weight.tolist(),
        },
        'blocks': [],
        'ln_f': {
            'gamma': model.ln_f.gamma.tolist(),
            'beta': model.ln_f.beta.tolist(),
        },
        'training_stats': training_stats or {},
    }
    
    for block in model.blocks:
        weights['blocks'].append({
            'attention': {
                'W_q': block.attention.W_q.tolist(),
                'W_k': block.attention.W_k.tolist(),
                'W_v': block.attention.W_v.tolist(),
                'W_o': block.attention.W_o.tolist(),
            },
            'ffn': {
                'W1': block.ffn.W1.tolist(),
                'W2': block.ffn.W2.tolist(),
            },
            'ln1': {
                'gamma': block.ln1.gamma.tolist(),
                'beta': block.ln1.beta.tolist(),
            },
            'ln2': {
                'gamma': block.ln2.gamma.tolist(),
                'beta': block.ln2.beta.tolist(),
            }
        })
    
    with open(output_path, 'w') as f:
        json.dump(weights, f, indent=2)
    
    size = os.path.getsize(output_path) / (1024 * 1024)
    print(f"  Saved {size:.2f} MB")
    
    return weights


# ============================================================================
# MAIN TRAINING PIPELINE
# ============================================================================

def main():
    print("=" * 60)
    print("🧠 RPA LLM FULL TRAINING PIPELINE")
    print("=" * 60)
    print("\n✨ Features:")
    print("  • Scaled architecture (500K params)")
    print("  • All curriculum data")
    print("  • 100+ epochs with LR scheduler")
    print("  • Temperature & top-k sampling")
    print("  • JS + Python inference ready")
    print()
    
    # Initialize tokenizer
    tokenizer = CharTokenizer()
    print(f"📝 Tokenizer: {tokenizer.vocab_size} characters")
    
    # Load all curriculum
    curriculum_dir = Path(__file__).parent / 'curriculum'
    texts = load_all_curriculum(str(curriculum_dir))
    
    # Also add core training samples
    core_samples = [
        # Python code patterns
        "def function_name(parameters):",
        "    return value",
        "class ClassName:",
        "    def __init__(self):",
        "        self.attribute = value",
        "import module_name",
        "from module import function",
        "for item in iterable:",
        "while condition:",
        "if condition:",
        "    pass",
        "else:",
        "elif condition:",
        "try:",
        "except Exception as e:",
        "finally:",
        "with open(file) as f:",
        "    data = f.read()",
        "lambda x: x * 2",
        "list comprehension",
        "[x for x in range(10)]",
        "{k: v for k, v in items}",
        "def __str__(self):",
        "def __repr__(self):",
        
        # Finance patterns
        "stock price analysis",
        "market capitalization",
        "price to earnings ratio",
        "dividend yield calculation",
        "revenue growth rate",
        "profit margin percentage",
        "return on investment",
        "asset allocation strategy",
        "risk management framework",
        "portfolio diversification",
        "financial statement analysis",
        "cash flow statement",
        "balance sheet items",
        "income statement metrics",
        "earnings per share",
        "market volatility index",
        "trading volume analysis",
        "bull market conditions",
        "bear market trends",
        "interest rate impact",
        
        # Q&A patterns
        "What is a variable?",
        "A variable stores data values.",
        "What is a function?",
        "A function is reusable code.",
        "What is profit?",
        "Profit equals revenue minus costs.",
        "How do you define a class?",
        "Use the class keyword followed by name.",
        "What is market cap?",
        "Market cap is stock price times shares.",
    ]
    
    texts.extend(core_samples)
    print(f"\n📊 Total training samples: {len(texts)}")
    
    # Create model - SCALED UP
    print("\n" + "=" * 60)
    print("🏗️  CREATING MODEL")
    print("=" * 60)
    
    config = ModelConfig(
        vocab_size=tokenizer.vocab_size,
        d_model=256,       # Scaled up
        num_heads=4,       # Scaled up
        num_layers=4,      # Scaled up
        max_seq_len=128,   # Longer context
        learning_rate=0.003,
        max_grad_norm=1.0,
    )
    
    model = TrainableLLM(config)
    params = model.count_params()
    print(f"\n📈 Model Statistics:")
    print(f"  Parameters: {params:,}")
    print(f"  d_model: {config.d_model}")
    print(f"  num_heads: {config.num_heads}")
    print(f"  num_layers: {config.num_layers}")
    print(f"  max_seq_len: {config.max_seq_len}")
    
    # Create batches
    print("\n" + "=" * 60)
    print("📦 PREPARING DATA")
    print("=" * 60)
    
    batches = create_batches(texts, tokenizer, seq_len=config.max_seq_len)
    print(f"  Training batches: {len(batches)}")
    
    if not batches:
        print("❌ No training batches!")
        sys.exit(1)
    
    # Training
    print("\n" + "=" * 60)
    print("🚀 TRAINING")
    print("=" * 60)
    
    epochs = 100
    warmup_steps = len(batches) * 2
    total_steps = epochs * len(batches)
    max_lr = 0.003
    min_lr = 0.0001
    
    print(f"\n  Epochs: {epochs}")
    print(f"  Warmup steps: {warmup_steps}")
    print(f"  Total steps: {total_steps}")
    print(f"  LR range: {min_lr} -> {max_lr} -> {min_lr}")
    
    step = 0
    losses = []
    best_loss = float('inf')
    start_time = time.time()
    
    for epoch in range(epochs):
        np.random.shuffle(batches)
        epoch_losses = []
        
        for input_ids, target_ids in batches:
            # Get learning rate
            lr = get_lr(step, warmup_steps, max_lr, min_lr, total_steps)
            
            # Training step
            loss = model.train_step(input_ids, target_ids, lr=lr)
            
            if not np.isnan(loss):
                epoch_losses.append(loss)
                losses.append(loss)
            
            step += 1
        
        # Stats
        avg_loss = np.mean(epoch_losses) if epoch_losses else float('nan')
        elapsed = time.time() - start_time
        
        if avg_loss < best_loss:
            best_loss = avg_loss
        
        if (epoch + 1) % 10 == 0 or epoch == 0:
            print(f"Epoch {epoch + 1:3d}/{epochs}: loss = {avg_loss:.4f} | best = {best_loss:.4f} | lr = {lr:.6f} | time = {elapsed:.1f}s")
            
            # Quick test
            if (epoch + 1) % 20 == 0:
                print("\n  📝 Test generation:")
                for prompt in ["def ", "What is", "stock "]:
                    output = generate_with_sampling(
                        model, tokenizer, prompt,
                        max_new_tokens=20, temperature=0.7, top_k=40
                    )
                    print(f"    '{prompt}' -> '{output}'")
                print()
    
    # Final test
    print("\n" + "=" * 60)
    print("🎯 FINAL GENERATION TEST")
    print("=" * 60)
    
    test_prompts = [
        ("def ", 30, 0.6),
        ("What is", 40, 0.7),
        ("stock ", 30, 0.7),
        ("class ", 40, 0.6),
        ("market ", 30, 0.7),
    ]
    
    for prompt, max_tokens, temp in test_prompts:
        output = generate_with_sampling(
            model, tokenizer, prompt,
            max_new_tokens=max_tokens, temperature=temp, top_k=40
        )
        print(f"\nPrompt: '{prompt}'")
        print(f"Output: '{output}'")
    
    # Save model
    print("\n" + "=" * 60)
    print("💾 SAVING MODEL")
    print("=" * 60)
    
    training_stats = {
        'epochs': epochs,
        'final_loss': float(losses[-1]) if losses else None,
        'best_loss': float(best_loss),
        'total_steps': step,
        'training_time_sec': time.time() - start_time,
        'params': params,
    }
    
    # Export to docs for GitHub Pages
    docs_path = Path(__file__).parent.parent / 'docs' / 'model_weights.json'
    docs_path.parent.mkdir(parents=True, exist_ok=True)
    export_model(model, tokenizer, str(docs_path), training_stats)
    
    # Also save to model_storage
    storage_path = Path(__file__).parent / 'model_storage' / 'trained_model' / 'model_weights.json'
    storage_path.parent.mkdir(parents=True, exist_ok=True)
    export_model(model, tokenizer, str(storage_path), training_stats)
    
    print("\n" + "=" * 60)
    print("✅ TRAINING COMPLETE!")
    print("=" * 60)
    print(f"\n📊 Final Stats:")
    print(f"  Parameters: {params:,}")
    print(f"  Final loss: {losses[-1]:.4f}")
    print(f"  Best loss: {best_loss:.4f}")
    print(f"  Training time: {(time.time() - start_time) / 60:.1f} minutes")
    print(f"\n📁 Outputs:")
    print(f"  GitHub Pages: {docs_path}")
    print(f"  Local: {storage_path}")


if __name__ == '__main__':
    main()
