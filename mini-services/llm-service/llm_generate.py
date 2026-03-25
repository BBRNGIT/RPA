#!/usr/bin/env python3
"""
LLM Generate Script - Called directly from Next.js API
"""

import sys
import os
import json

# Add RPA path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'RPA', 'RPA'))

from rpa_engine.neural.tokenizer import CharacterTokenizer
from rpa_engine.neural.trainable_llm import TrainableLLM, ModelConfig
import numpy as np

def main():
    # Get input from stdin
    try:
        input_data = json.loads(sys.stdin.read())
    except:
        input_data = {}

    message = input_data.get('message', '')
    max_tokens = input_data.get('max_tokens', 50)
    temperature = input_data.get('temperature', 0.8)

    # Load model
    tokenizer = CharacterTokenizer()
    config = ModelConfig(
        vocab_size=tokenizer.vocab_size,
        d_model=32,
        num_heads=2,
        num_layers=2,
        learning_rate=0.1
    )
    model = TrainableLLM(config)

    # Generate
    prompt_ids = tokenizer.encode(message)
    if len(prompt_ids) == 0:
        prompt_ids = [0]

    input_ids = np.array([prompt_ids])
    output_ids = model.generate(input_ids, max_new_tokens=max_tokens, temperature=temperature)
    output_text = tokenizer.decode(output_ids[0].tolist())

    result = {
        'message': message,
        'response': output_text,
        'model': 'RPA Neural LLM'
    }

    print(json.dumps(result))

if __name__ == '__main__':
    main()
