#!/usr/bin/env python3
"""
RPA LLM Proper Training Pipeline

This script trains the neural LLM using:
1. Real backpropagation through transformer layers
2. Curriculum data from JSON files (coding + finance domains)
3. Character-level tokenization (no word-piece)
4. Model weight export for JS inference
"""

import sys
import os
import json
import glob
import time
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rpa_engine.neural.trainable_llm import TrainableLLM, ModelConfig


class CharTokenizer:
    """Character-level tokenizer - NO word-piece!"""
    
    def __init__(self):
        # Printable ASCII + special tokens
        self.chars = list(' !"\')*+,-./0123456789:;?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[]_`abcdefghijklmnopqrstuvwxyz \n\t')
        self.char_to_id = {c: i for i, c in enumerate(self.chars)}
        self.pad_id = len(self.chars)
        self.unk_id = len(self.chars) + 1
        self.chars.append('<PAD>')
        self.chars.append('<UNK>')
        self.vocab_size = len(self.chars)
        
    def encode(self, text: str) -> List[int]:
        """Convert text to token IDs."""
        ids = []
        for c in text:
            if c in self.char_to_id:
                ids.append(self.char_to_id[c])
            else:
                # Handle unknown chars
                ids.append(self.unk_id)
        return ids
    
    def decode(self, ids: List[int]) -> str:
        """Convert token IDs back to text."""
        chars = []
        for i in ids:
            if 0 <= i < len(self.chars):
                chars.append(self.chars[i])
        return ''.join(chars)


def load_curriculum_data(curriculum_dir: str, domains: List[str] = None) -> List[str]:
    """
    Load text data from curriculum JSON files.
    
    Returns list of text strings for training.
    """
    texts = []
    curriculum_path = Path(curriculum_dir)
    
    if domains is None:
        domains = ['coding', 'finance', 'python', 'english', 'reasoning']
    
    print(f"Loading curriculum from: {curriculum_path}")
    
    for domain in domains:
        domain_path = curriculum_path / domain
        if not domain_path.exists():
            continue
            
        json_files = list(domain_path.glob('*.json'))
        print(f"  {domain}: {len(json_files)} files")
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Extract text from various curriculum formats
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            # Pattern format
                            if 'pattern' in item:
                                texts.append(str(item['pattern']))
                            if 'text' in item:
                                texts.append(str(item['text']))
                            if 'question' in item:
                                texts.append(str(item['question']))
                            if 'answer' in item:
                                texts.append(str(item['answer']))
                            if 'code' in item:
                                texts.append(str(item['code']))
                            if 'example' in item:
                                texts.append(str(item['example']))
                            # Vocabulary format
                            if 'word' in item:
                                texts.append(str(item['word']))
                            if 'definition' in item:
                                texts.append(str(item['definition']))
                elif isinstance(data, dict):
                    # Handle nested structures
                    if 'patterns' in data:
                        for p in data['patterns']:
                            if isinstance(p, dict) and 'text' in p:
                                texts.append(p['text'])
                    if 'lessons' in data:
                        for lesson in data['lessons']:
                            texts.append(str(lesson))
                            
            except Exception as e:
                print(f"  Warning: Could not load {json_file}: {e}")
    
    return texts


def create_training_batches(
    texts: List[str],
    tokenizer: CharTokenizer,
    seq_len: int = 64,
    batch_size: int = 1
) -> List[Tuple[np.ndarray, np.ndarray]]:
    """
    Create training batches from texts.
    
    Returns list of (input_ids, target_ids) tuples.
    """
    batches = []
    
    for text in texts:
        if len(text) < 2:
            continue
            
        # Tokenize
        ids = tokenizer.encode(text)
        
        # Split into sequences
        for i in range(0, len(ids) - seq_len, seq_len // 2):
            seq = ids[i:i + seq_len + 1]
            if len(seq) < 2:
                continue
                
            # Input and target
            input_ids = np.array([seq[:-1]])
            target_ids = np.array([seq[1:]])
            
            batches.append((input_ids, target_ids))
    
    return batches


def train_model(
    model: TrainableLLM,
    batches: List[Tuple[np.ndarray, np.ndarray]],
    epochs: int = 10,
    lr: float = 0.01,
    print_every: int = 100
) -> List[float]:
    """
    Train the model using backpropagation.
    
    Returns list of losses.
    """
    losses = []
    step = 0
    
    print(f"\nTraining on {len(batches)} batches for {epochs} epochs...")
    start_time = time.time()
    
    for epoch in range(epochs):
        epoch_losses = []
        
        # Shuffle batches each epoch
        np.random.shuffle(batches)
        
        for input_ids, target_ids in batches:
            # Training step with backpropagation
            loss = model.train_step(input_ids, target_ids, lr=lr)
            
            if not np.isnan(loss):
                epoch_losses.append(loss)
                losses.append(loss)
            
            step += 1
            
            if step % print_every == 0:
                avg_loss = np.mean(epoch_losses[-print_every:]) if epoch_losses else 0
                print(f"  Step {step}: loss = {avg_loss:.4f}")
        
        # Epoch stats
        avg_epoch_loss = np.mean(epoch_losses) if epoch_losses else float('nan')
        elapsed = time.time() - start_time
        print(f"Epoch {epoch + 1}/{epochs}: avg_loss = {avg_epoch_loss:.4f}, time = {elapsed:.1f}s")
    
    return losses


def export_model_to_json(model: TrainableLLM, tokenizer: CharTokenizer, output_path: str):
    """
    Export model weights to JSON for JavaScript inference.
    """
    print(f"\nExporting model to {output_path}...")
    
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
        }
    }
    
    # Export each transformer block
    for i, block in enumerate(model.blocks):
        block_weights = {
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
        }
        weights['blocks'].append(block_weights)
    
    # Save
    with open(output_path, 'w') as f:
        json.dump(weights, f, indent=2)
    
    # File size
    file_size = os.path.getsize(output_path)
    print(f"  Saved {file_size / 1024:.1f} KB")
    
    return weights


def main():
    print("=" * 60)
    print("RPA LLM PROPER TRAINING PIPELINE")
    print("=" * 60)
    print("\nNO word-piece tokenization")
    print("NO memory bloat")
    print("NO hallucination - train on real data")
    print("Domains: Coding + Finance\n")
    
    # Initialize tokenizer
    tokenizer = CharTokenizer()
    print(f"Tokenizer: {tokenizer.vocab_size} characters")
    
    # Load curriculum data
    curriculum_dir = Path(__file__).parent / 'curriculum'
    texts = load_curriculum_data(str(curriculum_dir))
    
    if not texts:
        print("\nWARNING: No curriculum data found!")
        print("Creating sample training data...")
        # Create sample data for testing
        texts = [
            "def hello_world():",
            "    print('Hello, World!')",
            "    return True",
            "What is a variable?",
            "A variable stores data.",
            "What is a function?",
            "A function is reusable code.",
            "stock price increases",
            "market trends analysis",
            "financial report shows profit",
            "revenue grew by ten percent",
            "python code example",
            "function returns value",
        ]
    
    print(f"\nLoaded {len(texts)} text samples")
    
    # Show sample
    print("\nSample texts:")
    for t in texts[:5]:
        print(f"  - {t[:50]}{'...' if len(t) > 50 else ''}")
    
    # Create model - SCALED UP
    print("\n" + "=" * 60)
    print("CREATING MODEL")
    print("=" * 60)
    
    config = ModelConfig(
        vocab_size=tokenizer.vocab_size,
        d_model=128,      # Scaled up from 32
        num_heads=4,      # Scaled up from 2
        num_layers=4,     # Scaled up from 2
        max_seq_len=64,
        learning_rate=0.01,
        max_grad_norm=1.0,
    )
    
    model = TrainableLLM(config)
    params = model.count_params()
    print(f"Model parameters: {params:,}")
    print(f"  d_model: {config.d_model}")
    print(f"  num_heads: {config.num_heads}")
    print(f"  num_layers: {config.num_layers}")
    
    # Create training batches
    print("\n" + "=" * 60)
    print("PREPARING DATA")
    print("=" * 60)
    
    batches = create_training_batches(texts, tokenizer, seq_len=64, batch_size=1)
    print(f"Created {len(batches)} training batches")
    
    if not batches:
        print("ERROR: No training batches!")
        sys.exit(1)
    
    # Train
    print("\n" + "=" * 60)
    print("TRAINING WITH BACKPROPAGATION")
    print("=" * 60)
    
    losses = train_model(
        model,
        batches,
        epochs=20,
        lr=0.01,
        print_every=50
    )
    
    if losses:
        print(f"\nFinal loss: {losses[-1]:.4f}")
        print(f"Loss improvement: {losses[0]:.4f} -> {losses[-1]:.4f}")
    
    # Test generation
    print("\n" + "=" * 60)
    print("TEST GENERATION")
    print("=" * 60)
    
    test_prompts = ["def ", "What is", "stock", "market"]
    
    for prompt in test_prompts:
        prompt_ids = np.array([tokenizer.encode(prompt)])
        generated = model.generate(prompt_ids, max_new_tokens=20, temperature=0.7)
        text = tokenizer.decode(generated[0].tolist())
        print(f"\nPrompt: '{prompt}'")
        print(f"Generated: '{text}'")
    
    # Save model
    print("\n" + "=" * 60)
    print("SAVING MODEL")
    print("=" * 60)
    
    output_dir = Path(__file__).parent / 'model_storage' / 'trained_model'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Export for Python
    model_path = output_dir / 'transformer.json'
    export_model_to_json(model, tokenizer, str(model_path))
    
    # Also export to docs for GitHub Pages
    docs_path = Path(__file__).parent.parent / 'docs' / 'model_weights.json'
    docs_path.parent.mkdir(parents=True, exist_ok=True)
    export_model_to_json(model, tokenizer, str(docs_path))
    
    print("\n" + "=" * 60)
    print("TRAINING COMPLETE!")
    print("=" * 60)
    print(f"\nModel saved to: {model_path}")
    print(f"JS weights saved to: {docs_path}")
    print("\nNext steps:")
    print("1. Push changes to GitHub")
    print("2. Update llm-chat.html to load model_weights.json")
    print("3. Test on GitHub Pages")


if __name__ == '__main__':
    main()
