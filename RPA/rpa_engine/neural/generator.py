"""
RPA Text Generator - Autoregressive Text Generation

Generates text by:
1. Encode prompt to tokens
2. Forward pass through model
3. Sample next token from distribution
4. Append token to sequence
5. Repeat until stop condition

Supports various sampling strategies:
- Greedy: Always pick most likely token
- Top-k: Sample from top k tokens
- Top-p (nucleus): Sample from cumulative probability p
- Temperature: Control randomness
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, List, Tuple, Dict
from dataclasses import dataclass


@dataclass
class GenerationConfig:
    """Configuration for text generation."""
    
    max_new_tokens: int = 100
    temperature: float = 1.0
    top_k: int = 50
    top_p: float = 0.9
    
    # Stopping
    stop_tokens: Optional[List[int]] = None  # Token IDs to stop on
    stop_strings: Optional[List[str]] = None  # Strings to stop on
    
    # Repetition penalty
    repetition_penalty: float = 1.0
    
    # Speed optimization
    use_cache: bool = True  # Use KV cache for faster generation


class TextGenerator:
    """
    Text generator for language models.
    
    Takes a trained model and generates text autoregressively.
    """
    
    def __init__(
        self,
        model: nn.Module,
        tokenizer,
        config: Optional[GenerationConfig] = None,
        device: str = "auto",
    ):
        self.model = model
        self.tokenizer = tokenizer
        self.config = config or GenerationConfig()
        
        # Device
        if device == "auto":
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)
        
        self.model = self.model.to(self.device)
        self.model.eval()
    
    def generate(
        self,
        prompt: str,
        config: Optional[GenerationConfig] = None,
    ) -> str:
        """
        Generate text from a prompt.
        
        Args:
            prompt: Input text to continue
            config: Optional generation config (overrides default)
            
        Returns:
            Generated text (including prompt)
        """
        config = config or self.config
        
        # Encode prompt
        input_ids = self.tokenizer.encode(prompt, add_special_tokens=True)
        input_ids = torch.tensor([input_ids], dtype=torch.long, device=self.device)
        
        # Generate
        output_ids = self._generate_tokens(input_ids, config)
        
        # Decode
        output_text = self.tokenizer.decode(output_ids[0].tolist())
        
        return output_text
    
    def _generate_tokens(
        self,
        input_ids: torch.Tensor,
        config: GenerationConfig,
    ) -> torch.Tensor:
        """
        Generate token IDs.
        
        Args:
            input_ids: (1, seq_len) tensor of input token IDs
            config: Generation config
            
        Returns:
            (1, seq_len + new_tokens) tensor
        """
        # Initialize
        generated = input_ids.clone()
        past_key_values = None
        
        # Stop token IDs
        stop_ids = set(config.stop_tokens or [])
        if hasattr(self.tokenizer, 'eos_id'):
            stop_ids.add(self.tokenizer.eos_id)
        
        for _ in range(config.max_new_tokens):
            # Prepare input
            if config.use_cache and past_key_values is not None:
                # Only pass the new token
                model_input = generated[:, -1:]
            else:
                # Pass full sequence
                model_input = generated
            
            # Forward pass
            with torch.no_grad():
                output = self.model(
                    model_input,
                    kv_cache=past_key_values,
                    use_cache=config.use_cache,
                )
            
            logits = output["logits"][:, -1, :]  # (1, vocab_size)
            
            # Update cache
            if config.use_cache:
                past_key_values = output.get("kv_cache")
            
            # Apply repetition penalty
            if config.repetition_penalty > 1.0:
                logits = self._apply_repetition_penalty(
                    logits, generated, config.repetition_penalty
                )
            
            # Apply temperature
            if config.temperature != 1.0:
                logits = logits / config.temperature
            
            # Sample next token
            next_token = self._sample_token(logits, config)
            
            # Check for stop
            if next_token.item() in stop_ids:
                break
            
            # Append
            generated = torch.cat([generated, next_token.unsqueeze(0)], dim=1)
            
            # Check for stop strings
            if config.stop_strings:
                current_text = self.tokenizer.decode(generated[0].tolist())
                if any(s in current_text for s in config.stop_strings):
                    break
        
        return generated
    
    def _sample_token(
        self,
        logits: torch.Tensor,
        config: GenerationConfig,
    ) -> torch.Tensor:
        """
        Sample next token from logits.
        
        Supports:
        - Greedy (temperature=0)
        - Top-k sampling
        - Top-p (nucleus) sampling
        """
        # Greedy
        if config.temperature == 0:
            return logits.argmax(dim=-1)
        
        # Apply top-k
        if config.top_k > 0:
            top_k = min(config.top_k, logits.size(-1))
            values, _ = torch.topk(logits, top_k)
            min_value = values[:, -1].unsqueeze(-1)
            logits = torch.where(
                logits < min_value,
                torch.full_like(logits, float('-inf')),
                logits
            )
        
        # Apply top-p
        if config.top_p < 1.0:
            sorted_logits, sorted_indices = torch.sort(logits, descending=True)
            cumulative_probs = torch.cumsum(F.softmax(sorted_logits, dim=-1), dim=-1)
            
            # Remove tokens with cumulative probability above threshold
            sorted_indices_to_remove = cumulative_probs > config.top_p
            sorted_indices_to_remove[:, 1:] = sorted_indices_to_remove[:, :-1].clone()
            sorted_indices_to_remove[:, 0] = False
            
            indices_to_remove = sorted_indices_to_remove.scatter(
                1, sorted_indices, sorted_indices_to_remove
            )
            logits = logits.masked_fill(indices_to_remove, float('-inf'))
        
        # Sample from distribution
        probs = F.softmax(logits, dim=-1)
        next_token = torch.multinomial(probs, num_samples=1)
        
        return next_token.squeeze(-1)
    
    def _apply_repetition_penalty(
        self,
        logits: torch.Tensor,
        generated: torch.Tensor,
        penalty: float,
    ) -> torch.Tensor:
        """Apply repetition penalty to logits."""
        for token_id in generated[0].unique():
            if logits[0, token_id] > 0:
                logits[0, token_id] /= penalty
            else:
                logits[0, token_id] *= penalty
        return logits
    
    def generate_batch(
        self,
        prompts: List[str],
        config: Optional[GenerationConfig] = None,
    ) -> List[str]:
        """Generate text for multiple prompts."""
        # Note: This is sequential for simplicity
        # Could be parallelized with padding
        return [self.generate(p, config) for p in prompts]
    
    def chat(
        self,
        message: str,
        history: Optional[List[Dict[str, str]]] = None,
        system_prompt: Optional[str] = None,
        config: Optional[GenerationConfig] = None,
    ) -> Tuple[str, List[Dict[str, str]]]:
        """
        Chat interface with conversation history.
        
        Args:
            message: User message
            history: List of {"role": "user/assistant", "content": "..."}
            system_prompt: System prompt
            config: Generation config
            
        Returns:
            (response, updated_history)
        """
        history = history or []
        
        # Build prompt
        prompt_parts = []
        
        if system_prompt:
            prompt_parts.append(f"System: {system_prompt}\n")
        
        for turn in history:
            role = turn.get("role", "user")
            content = turn.get("content", "")
            prompt_parts.append(f"{role.capitalize()}: {content}\n")
        
        prompt_parts.append(f"User: {message}\nAssistant:")
        
        full_prompt = "".join(prompt_parts)
        
        # Generate
        response = self.generate(full_prompt, config)
        
        # Extract just the new response
        response = response[len(full_prompt):].strip()
        
        # Update history
        new_history = history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": response},
        ]
        
        return response, new_history
    
    def complete_code(
        self,
        code: str,
        language: str = "python",
        config: Optional[GenerationConfig] = None,
    ) -> str:
        """
        Complete code.
        
        Args:
            code: Partial code
            language: Programming language
            config: Generation config
            
        Returns:
            Completed code
        """
        # Add language-specific prompt
        prompt = f"# {language} code\n{code}"
        
        # Generate with code-specific settings
        code_config = config or GenerationConfig(
            max_new_tokens=200,
            temperature=0.2,  # Lower for code
            top_p=0.95,
            stop_strings=["\nclass ", "\ndef ", "\n# End"],
        )
        
        return self.generate(prompt, code_config)


def create_generator(
    model: nn.Module,
    tokenizer,
    config: Optional[GenerationConfig] = None,
    device: str = "auto",
) -> TextGenerator:
    """Create a text generator."""
    return TextGenerator(model, tokenizer, config, device)


if __name__ == "__main__":
    print("=" * 60)
    print("TEXT GENERATOR TEST")
    print("=" * 60)
    
    from .transformer import TransformerLM
    from .tokenizer import CharacterTokenizer
    
    # Create tokenizer and model
    tokenizer = CharacterTokenizer()
    
    model = TransformerLM(
        vocab_size=tokenizer.vocab_size,
        d_model=64,
        num_heads=4,
        num_layers=2,
        max_seq_len=128,
    )
    
    # Create generator
    config = GenerationConfig(
        max_new_tokens=50,
        temperature=0.8,
        top_k=40,
    )
    
    generator = create_generator(model, tokenizer, config)
    
    # Generate
    prompt = "def hello"
    output = generator.generate(prompt)
    
    print(f"\nPrompt: {prompt}")
    print(f"Generated: {output}")
    
    print("\n" + "=" * 60)
    print("TEXT GENERATOR WORKING!")
    print("=" * 60)
