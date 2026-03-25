#!/usr/bin/env python3
"""
Quick training script for demo purposes.
Trains a smaller model quickly to produce meaningful output.
"""

import sys
import os
import json
import numpy as np
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rpa_engine.neural.trainable_llm import TrainableLLM, ModelConfig


class CharTokenizer:
    def __init__(self):
        self.chars = list(' !"\'()*+,-./0123456789:;?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[]_`abcdefghijklmnopqrstuvwxyz \n\t')
        self.char_to_id = {c: i for i, c in enumerate(self.chars)}
        self.pad_id = len(self.chars)
        self.unk_id = len(self.chars) + 1
        self.chars.append('<PAD>')
        self.chars.append('<UNK>')
        self.vocab_size = len(self.chars)
        
    def encode(self, text):
        return [self.char_to_id.get(c, self.unk_id) for c in text]
    
    def decode(self, ids):
        return ''.join(self.chars[i] if 0 <= i < len(self.chars) else '' for i in ids)


def main():
    print("=" * 50)
    print("RPA LLM QUICK TRAINING")
    print("=" * 50)
    
    tokenizer = CharTokenizer()
    print(f"Vocab: {tokenizer.vocab_size} characters")
    
    # Sample training data - coding + finance
    texts = [
        # Python code
        "def hello():",
        "    return True",
        "    print('hello')",
        "class User:",
        "    def __init__(self):",
        "        self.name = name",
        "import numpy as np",
        "from typing import List",
        "def calculate(x, y):",
        "    return x + y",
        "# This is a comment",
        "for i in range(10):",
        "if x > 0:",
        "else:",
        "    pass",
        
        # Finance terms
        "stock market",
        "financial analysis",
        "revenue growth",
        "profit margin",
        "market trends",
        "investment portfolio",
        "risk management",
        "asset allocation",
        "price earnings ratio",
        "dividend yield",
        "market capitalization",
        "return on investment",
        "cash flow statement",
        "balance sheet",
        "income statement",
        
        # Q&A patterns
        "What is a variable?",
        "A variable stores data.",
        "What is a function?",
        "A function is reusable code.",
        "What is profit?",
        "Profit is revenue minus cost.",
    ]
    
    print(f"Training data: {len(texts)} samples")
    
    # Create smaller model for quick training
    config = ModelConfig(
        vocab_size=tokenizer.vocab_size,
        d_model=64,
        num_heads=2,
        num_layers=2,
        max_seq_len=32,
        learning_rate=0.05,
    )
    
    model = TrainableLLM(config)
    print(f"Model: {model.count_params():,} parameters")
    
    # Training
    print("\nTraining...")
    for epoch in range(10):
        total_loss = 0
        count = 0
        
        for text in texts:
            ids = tokenizer.encode(text)
            if len(ids) < 2:
                continue
            
            input_ids = np.array([ids[:-1]])
            target_ids = np.array([ids[1:]])
            
            loss = model.train_step(input_ids, target_ids)
            if not np.isnan(loss):
                total_loss += loss
                count += 1
        
        avg_loss = total_loss / count if count > 0 else 0
        print(f"Epoch {epoch+1}: loss = {avg_loss:.4f}")
    
    # Test
    print("\n" + "=" * 50)
    print("TEST GENERATION")
    print("=" * 50)
    
    for prompt in ["def ", "What is", "stock"]:
        ids = np.array([tokenizer.encode(prompt)])
        gen = model.generate(ids, max_new_tokens=15, temperature=0.5)
        text = tokenizer.decode(gen[0].tolist())
        print(f"'{prompt}' -> '{text}'")
    
    # Export
    print("\nExporting model...")
    output_path = Path(__file__).parent.parent / 'docs' / 'model_weights.json'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    weights = {
        'config': {
            'vocab_size': config.vocab_size,
            'd_model': config.d_model,
            'num_heads': config.num_heads,
            'num_layers': config.num_layers,
            'max_seq_len': config.max_seq_len,
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
        json.dump(weights, f)
    
    size = os.path.getsize(output_path) / 1024
    print(f"Saved to {output_path} ({size:.1f} KB)")
    
    print("\n" + "=" * 50)
    print("DONE!")
    print("=" * 50)


if __name__ == '__main__':
    main()
