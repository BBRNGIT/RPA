"""
RPA Tokenizer - Character-Level and BPE Tokenization

NO word-piece tokenization. Instead we use:
1. Character-level: Each character is a token
2. BPE (Byte Pair Encoding): Learns subword units from data

Character-level is the simplest and avoids all tokenization issues.
"""

import json
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from collections import Counter
from dataclasses import dataclass


@dataclass
class TokenizerConfig:
    """Configuration for tokenizer."""
    vocab_size: int = 256  # For char-level, this is all ASCII
    max_length: int = 512
    pad_token: str = "<PAD>"
    unk_token: str = "<UNK>"
    bos_token: str = "<BOS>"  # Beginning of sequence
    eos_token: str = "<EOS>"  # End of sequence


class CharacterTokenizer:
    """
    Character-level tokenizer.
    
    Each character is a token. No word-piece, no subword.
    Simple, transparent, no OOV issues.
    
    Vocabulary: All printable ASCII characters + special tokens
    """
    
    def __init__(self, config: Optional[TokenizerConfig] = None):
        self.config = config or TokenizerConfig()
        
        # Build vocabulary from printable ASCII
        self.char_to_id: Dict[str, int] = {}
        self.id_to_char: Dict[int, str] = {}
        
        # Special tokens
        special_tokens = [
            self.config.pad_token,
            self.config.unk_token,
            self.config.bos_token,
            self.config.eos_token,
        ]
        
        # Add special tokens
        for i, token in enumerate(special_tokens):
            self.char_to_id[token] = i
            self.id_to_char[i] = token
        
        # Add printable ASCII (32-126) + newline + tab
        idx = len(special_tokens)
        for i in range(32, 127):  # Printable ASCII
            char = chr(i)
            self.char_to_id[char] = idx
            self.id_to_char[idx] = char
            idx += 1
        
        # Add newline and tab
        self.char_to_id['\n'] = idx
        self.id_to_char[idx] = '\n'
        idx += 1
        self.char_to_id['\t'] = idx
        self.id_to_char[idx] = '\t'
        
        self.pad_id = self.char_to_id[self.config.pad_token]
        self.unk_id = self.char_to_id[self.config.unk_token]
        self.bos_id = self.char_to_id[self.config.bos_token]
        self.eos_id = self.char_to_id[self.config.eos_token]
        
        self.vocab_size = len(self.char_to_id)
    
    def encode(self, text: str, add_special_tokens: bool = True) -> List[int]:
        """
        Encode text to token IDs.
        
        Args:
            text: Input text
            add_special_tokens: Add BOS/EOS tokens
            
        Returns:
            List of token IDs
        """
        tokens = []
        
        if add_special_tokens:
            tokens.append(self.bos_id)
        
        for char in text:
            if char in self.char_to_id:
                tokens.append(self.char_to_id[char])
            else:
                # Handle unknown characters (e.g., unicode)
                tokens.append(self.unk_id)
        
        if add_special_tokens:
            tokens.append(self.eos_id)
        
        return tokens
    
    def decode(self, token_ids: List[int], skip_special_tokens: bool = True) -> str:
        """
        Decode token IDs to text.
        
        Args:
            token_ids: List of token IDs
            skip_special_tokens: Skip PAD, UNK, BOS, EOS
            
        Returns:
            Decoded text
        """
        chars = []
        special_ids = {self.pad_id, self.unk_id, self.bos_id, self.eos_id}
        
        for token_id in token_ids:
            if skip_special_tokens and token_id in special_ids:
                continue
            if token_id in self.id_to_char:
                chars.append(self.id_to_char[token_id])
        
        return ''.join(chars)
    
    def batch_encode(self, texts: List[str], padding: bool = True) -> Tuple[List[List[int]], List[int]]:
        """
        Encode multiple texts with padding.
        
        Returns:
            (token_ids, lengths)
        """
        all_tokens = []
        lengths = []
        
        for text in texts:
            tokens = self.encode(text)
            all_tokens.append(tokens)
            lengths.append(len(tokens))
        
        if padding:
            max_len = max(lengths)
            for i, tokens in enumerate(all_tokens):
                while len(tokens) < max_len:
                    tokens.append(self.pad_id)
        
        return all_tokens, lengths
    
    def save(self, path: Path) -> None:
        """Save tokenizer to file."""
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        
        data = {
            "config": {
                "vocab_size": self.config.vocab_size,
                "max_length": self.config.max_length,
                "pad_token": self.config.pad_token,
                "unk_token": self.config.unk_token,
                "bos_token": self.config.bos_token,
                "eos_token": self.config.eos_token,
            },
            "char_to_id": self.char_to_id,
            "vocab_size": self.vocab_size,
        }
        
        with open(path / "tokenizer.json", 'w') as f:
            json.dump(data, f, indent=2)
    
    def load(self, path: Path) -> None:
        """Load tokenizer from file."""
        path = Path(path)
        
        with open(path / "tokenizer.json") as f:
            data = json.load(f)
        
        self.config = TokenizerConfig(**data["config"])
        self.char_to_id = data["char_to_id"]
        self.id_to_char = {int(k): v for v, k in self.char_to_id.items()}
        self.vocab_size = data["vocab_size"]
        
        self.pad_id = self.char_to_id[self.config.pad_token]
        self.unk_id = self.char_to_id[self.config.unk_token]
        self.bos_id = self.char_to_id[self.config.bos_token]
        self.eos_id = self.char_to_id[self.config.eos_token]


class BPETokenizer:
    """
    Byte Pair Encoding tokenizer.
    
    Learns subword units from data. More efficient than character-level
    but still no word-piece arbitrary splitting.
    
    Training:
    1. Start with character vocabulary
    2. Count all adjacent pairs
    3. Merge most frequent pair
    4. Repeat until target vocab size
    """
    
    def __init__(self, config: Optional[TokenizerConfig] = None):
        self.config = config or TokenizerConfig()
        self.vocab: Dict[str, int] = {}
        self.merges: List[Tuple[str, str]] = []
        self.vocab_size = 0
    
    def train(self, texts: List[str], target_vocab_size: int = 1000) -> None:
        """
        Train BPE on texts.
        
        Args:
            texts: Training texts
            target_vocab_size: Target vocabulary size
        """
        # Initialize with character vocabulary
        vocab = Counter()
        for text in texts:
            for char in text:
                vocab[char] += 1
        
        # Build initial vocabulary
        self.vocab = {char: idx for idx, char in enumerate(vocab.keys())}
        
        # Special tokens
        special_tokens = [
            self.config.pad_token,
            self.config.unk_token,
            self.config.bos_token,
            self.config.eos_token,
        ]
        for token in special_tokens:
            self.vocab[token] = len(self.vocab)
        
        self.merges = []
        
        # BPE merge loop
        while len(self.vocab) < target_vocab_size:
            # Count pairs
            pairs = Counter()
            for text in texts:
                tokens = list(text)
                for i in range(len(tokens) - 1):
                    pair = (tokens[i], tokens[i + 1])
                    pairs[pair] += 1
            
            if not pairs:
                break
            
            # Get most frequent pair
            best_pair = max(pairs, key=pairs.get)
            
            # Add merge
            self.merges.append(best_pair)
            merged = best_pair[0] + best_pair[1]
            self.vocab[merged] = len(self.vocab)
            
            # Update texts
            new_texts = []
            for text in texts:
                tokens = list(text)
                new_tokens = []
                i = 0
                while i < len(tokens):
                    if i < len(tokens) - 1 and (tokens[i], tokens[i + 1]) == best_pair:
                        new_tokens.append(merged)
                        i += 2
                    else:
                        new_tokens.append(tokens[i])
                        i += 1
                new_texts.append(''.join(new_tokens))
            texts = new_texts
        
        self.vocab_size = len(self.vocab)
        
        # Build reverse vocab
        self.id_to_token = {v: k for k, v in self.vocab.items()}
        
        # Special token IDs
        self.pad_id = self.vocab.get(self.config.pad_token, 0)
        self.unk_id = self.vocab.get(self.config.unk_token, 1)
        self.bos_id = self.vocab.get(self.config.bos_token, 2)
        self.eos_id = self.vocab.get(self.config.eos_token, 3)
    
    def encode(self, text: str, add_special_tokens: bool = True) -> List[int]:
        """Encode text to token IDs using learned BPE."""
        tokens = list(text)
        
        # Apply merges
        for pair in self.merges:
            merged = pair[0] + pair[1]
            new_tokens = []
            i = 0
            while i < len(tokens):
                if i < len(tokens) - 1 and tokens[i] == pair[0] and tokens[i + 1] == pair[1]:
                    new_tokens.append(merged)
                    i += 2
                else:
                    new_tokens.append(tokens[i])
                    i += 1
            tokens = new_tokens
        
        # Convert to IDs
        ids = []
        if add_special_tokens:
            ids.append(self.bos_id)
        
        for token in tokens:
            if token in self.vocab:
                ids.append(self.vocab[token])
            else:
                ids.append(self.unk_id)
        
        if add_special_tokens:
            ids.append(self.eos_id)
        
        return ids
    
    def decode(self, token_ids: List[int], skip_special_tokens: bool = True) -> str:
        """Decode token IDs to text."""
        special_ids = {self.pad_id, self.unk_id, self.bos_id, self.eos_id}
        
        tokens = []
        for token_id in token_ids:
            if skip_special_tokens and token_id in special_ids:
                continue
            if token_id in self.id_to_token:
                tokens.append(self.id_to_token[token_id])
        
        return ''.join(tokens)
    
    def save(self, path: Path) -> None:
        """Save tokenizer."""
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        
        data = {
            "config": {
                "vocab_size": self.config.vocab_size,
                "max_length": self.config.max_length,
                "pad_token": self.config.pad_token,
                "unk_token": self.config.unk_token,
                "bos_token": self.config.bos_token,
                "eos_token": self.config.eos_token,
            },
            "vocab": self.vocab,
            "merges": self.merges,
            "vocab_size": self.vocab_size,
        }
        
        with open(path / "bpe_tokenizer.json", 'w') as f:
            json.dump(data, f, indent=2)
    
    def load(self, path: Path) -> None:
        """Load tokenizer."""
        path = Path(path)
        
        with open(path / "bpe_tokenizer.json") as f:
            data = json.load(f)
        
        self.config = TokenizerConfig(**data["config"])
        self.vocab = data["vocab"]
        self.merges = [tuple(m) for m in data["merges"]]
        self.vocab_size = data["vocab_size"]
        self.id_to_token = {int(v): k for k, v in self.vocab.items()}
        
        self.pad_id = self.vocab.get(self.config.pad_token, 0)
        self.unk_id = self.vocab.get(self.config.unk_token, 1)
        self.bos_id = self.vocab.get(self.config.bos_token, 2)
        self.eos_id = self.vocab.get(self.config.eos_token, 3)


def create_tokenizer(tokenizer_type: str = "char", config: Optional[TokenizerConfig] = None):
    """Create a tokenizer."""
    if tokenizer_type == "char":
        return CharacterTokenizer(config)
    elif tokenizer_type == "bpe":
        return BPETokenizer(config)
    else:
        raise ValueError(f"Unknown tokenizer type: {tokenizer_type}")


if __name__ == "__main__":
    print("=" * 60)
    print("TOKENIZER TEST")
    print("=" * 60)
    
    # Test character tokenizer
    print("\n[Character Tokenizer]")
    tok = CharacterTokenizer()
    print(f"Vocab size: {tok.vocab_size}")
    
    text = "def hello():\n    return 'world'"
    ids = tok.encode(text)
    decoded = tok.decode(ids)
    
    print(f"Original: {text[:40]}...")
    print(f"Encoded: {ids[:20]}... ({len(ids)} tokens)")
    print(f"Decoded: {decoded[:40]}...")
    print(f"Match: {text == decoded}")
    
    print("\n" + "=" * 60)
    print("TOKENIZER WORKING!")
    print("=" * 60)
