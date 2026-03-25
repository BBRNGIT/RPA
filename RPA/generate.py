#!/usr/bin/env python3
"""
RPA LLM Generation Script

Usage:
    python generate.py --prompt "def " --max-tokens 50 --temperature 0.8 --top-k 40
"""

import sys
import os
import json
import argparse
import numpy as np
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rpa_engine.neural.trainable_llm import TrainableLLM, ModelConfig


class CharTokenizer:
    def __init__(self, chars=None):
        if chars is None:
            self.chars = list(
                ' !"#$%&\'()*+,-./0123456789:;<=>?@'
                'ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`'
                'abcdefghijklmnopqrstuvwxyz{|}~'
                '\n\r\t'
            )
            self.chars.extend(['<PAD>', '<UNK>'])
        else:
            self.chars = chars
        
        self.char_to_id = {c: i for i, c in enumerate(self.chars)}
        self.vocab_size = len(self.chars)
        self.unk_id = self.vocab_size - 1
    
    def encode(self, text):
        return [self.char_to_id.get(c, self.unk_id) for c in text]
    
    def decode(self, ids):
        return ''.join(
            self.chars[i] if 0 <= i < len(self.chars) else '' 
            for i in ids
        )


def load_model(weights_path):
    """Load model from weights JSON."""
    with open(weights_path, 'r') as f:
        weights = json.load(f)
    
    config = ModelConfig(
        vocab_size=weights['config']['vocab_size'],
        d_model=weights['config']['d_model'],
        num_heads=weights['config']['num_heads'],
        num_layers=weights['config']['num_layers'],
        max_seq_len=weights['config']['max_seq_len'],
    )
    
    model = TrainableLLM(config)
    
    # Load weights
    model.embedding.weight = np.array(weights['embedding']['weight'])
    model.embedding.pos_weight = np.array(weights['embedding']['pos_weight'])
    
    for i, block_weights in enumerate(weights['blocks']):
        model.blocks[i].attention.W_q = np.array(block_weights['attention']['W_q'])
        model.blocks[i].attention.W_k = np.array(block_weights['attention']['W_k'])
        model.blocks[i].attention.W_v = np.array(block_weights['attention']['W_v'])
        model.blocks[i].attention.W_o = np.array(block_weights['attention']['W_o'])
        model.blocks[i].ffn.W1 = np.array(block_weights['ffn']['W1'])
        model.blocks[i].ffn.W2 = np.array(block_weights['ffn']['W2'])
        model.blocks[i].ln1.gamma = np.array(block_weights['ln1']['gamma'])
        model.blocks[i].ln1.beta = np.array(block_weights['ln1']['beta'])
        model.blocks[i].ln2.gamma = np.array(block_weights['ln2']['gamma'])
        model.blocks[i].ln2.beta = np.array(block_weights['ln2']['beta'])
    
    model.ln_f.gamma = np.array(weights['ln_f']['gamma'])
    model.ln_f.beta = np.array(weights['ln_f']['beta'])
    
    tokenizer = CharTokenizer(chars=weights['tokenizer']['chars'])
    
    return model, tokenizer


def generate_with_sampling(
    model, tokenizer, prompt,
    max_new_tokens=50, temperature=0.8, top_k=40
):
    """Generate with temperature and top-k sampling."""
    tokens = tokenizer.encode(prompt)
    
    for _ in range(max_new_tokens):
        context = tokens[-model.config.max_seq_len:]
        input_ids = np.array([context])
        
        logits = model.forward(input_ids)
        last_logits = logits[0, -1, :]
        
        # Temperature
        scaled = last_logits / temperature
        
        # Top-k
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


def main():
    parser = argparse.ArgumentParser(description='RPA LLM Generation')
    parser.add_argument('--prompt', type=str, default='Hello', help='Input prompt')
    parser.add_argument('--max-tokens', type=int, default=50, help='Max tokens to generate')
    parser.add_argument('--temperature', type=float, default=0.8, help='Sampling temperature')
    parser.add_argument('--top-k', type=int, default=40, help='Top-k sampling')
    parser.add_argument('--weights', type=str, default=None, help='Path to weights JSON')
    
    args = parser.parse_args()
    
    # Find weights
    if args.weights:
        weights_path = args.weights
    else:
        script_dir = Path(__file__).parent
        weights_path = script_dir.parent / 'docs' / 'model_weights.json'
        if not weights_path.exists():
            weights_path = script_dir / 'model_storage' / 'trained_model' / 'model_weights.json'
    
    if not Path(weights_path).exists():
        print(f"Error: Model weights not found at {weights_path}", file=sys.stderr)
        print("Run training first: python quick_train.py", file=sys.stderr)
        sys.exit(1)
    
    # Load model
    model, tokenizer = load_model(weights_path)
    
    # Generate
    output = generate_with_sampling(
        model, tokenizer, args.prompt,
        max_new_tokens=args.max_tokens,
        temperature=args.temperature,
        top_k=args.top_k
    )
    
    print(output)


if __name__ == '__main__':
    main()
