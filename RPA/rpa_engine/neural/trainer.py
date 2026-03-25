"""
RPA Trainer - Training Pipeline for Language Models

Handles:
- Training loop
- Optimization
- Learning rate scheduling
- Gradient clipping
- Checkpointing
- Logging

Standard training procedure:
1. Forward pass: Get logits and loss
2. Backward pass: Compute gradients
3. Optimizer step: Update weights
4. Repeat
"""

import math
import time
import json
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR, LinearLR, SequentialLR


@dataclass
class TrainingConfig:
    """Configuration for training."""
    
    # Model
    vocab_size: int = 100
    d_model: int = 256
    num_heads: int = 8
    num_layers: int = 6
    max_seq_len: int = 512
    dropout: float = 0.1
    
    # Training
    batch_size: int = 8
    learning_rate: float = 3e-4
    weight_decay: float = 0.01
    num_epochs: int = 10
    max_steps: int = -1  # -1 for epoch-based, else step-based
    warmup_steps: int = 100
    gradient_accumulation_steps: int = 1
    max_grad_norm: float = 1.0
    
    # Checkpointing
    save_dir: str = "./checkpoints"
    save_every: int = 1000
    eval_every: int = 500
    
    # Logging
    log_every: int = 10
    use_wandb: bool = False
    
    # Device
    device: str = "auto"  # auto, cpu, cuda, mps


class TextDataset(Dataset):
    """
    Dataset for text data.
    
    Takes tokenized text and creates input/label pairs
    for next-token prediction.
    """
    
    def __init__(
        self,
        token_ids: List[int],
        seq_len: int = 128,
        overlap: int = 0,
    ):
        self.token_ids = token_ids
        self.seq_len = seq_len
        self.overlap = overlap
        
        # Calculate number of samples
        stride = seq_len - overlap if overlap > 0 else seq_len
        self.num_samples = (len(token_ids) - seq_len) // stride + 1
    
    def __len__(self) -> int:
        return self.num_samples
    
    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        stride = self.seq_len - self.overlap if self.overlap > 0 else self.seq_len
        start = idx * stride
        end = start + self.seq_len + 1  # +1 for label
        
        chunk = self.token_ids[start:end]
        
        # Pad if needed
        while len(chunk) < self.seq_len + 1:
            chunk.append(0)  # Pad token
        
        return {
            "input_ids": torch.tensor(chunk[:-1], dtype=torch.long),
            "labels": torch.tensor(chunk[1:], dtype=torch.long),
        }


class Trainer:
    """
    Training pipeline for language models.
    
    Handles the full training loop with:
    - Gradient accumulation
    - Learning rate scheduling
    - Checkpointing
    - Evaluation
    """
    
    def __init__(
        self,
        model: nn.Module,
        config: TrainingConfig,
        train_dataset: Optional[Dataset] = None,
        eval_dataset: Optional[Dataset] = None,
    ):
        self.config = config
        self.model = model
        
        # Device
        if config.device == "auto":
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(config.device)
        
        self.model = self.model.to(self.device)
        
        # DataLoaders
        self.train_loader = None
        self.eval_loader = None
        
        if train_dataset:
            self.train_loader = DataLoader(
                train_dataset,
                batch_size=config.batch_size,
                shuffle=True,
                num_workers=0,
                pin_memory=True,
            )
        
        if eval_dataset:
            self.eval_loader = DataLoader(
                eval_dataset,
                batch_size=config.batch_size,
                shuffle=False,
                num_workers=0,
            )
        
        # Optimizer
        self.optimizer = AdamW(
            model.parameters(),
            lr=config.learning_rate,
            weight_decay=config.weight_decay,
            betas=(0.9, 0.95),
        )
        
        # Learning rate scheduler
        self.scheduler = self._create_scheduler()
        
        # Training state
        self.global_step = 0
        self.epoch = 0
        self.best_loss = float('inf')
        
        # Save directory
        self.save_dir = Path(config.save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)
    
    def _create_scheduler(self):
        """Create learning rate scheduler with warmup."""
        total_steps = self.config.max_steps
        
        if total_steps < 0:
            # Estimate from epochs
            if self.train_loader:
                total_steps = len(self.train_loader) * self.config.num_epochs
            else:
                total_steps = 10000
        
        # Warmup scheduler
        warmup_scheduler = LinearLR(
            self.optimizer,
            start_factor=0.1,
            end_factor=1.0,
            total_iters=self.config.warmup_steps,
        )
        
        # Main scheduler
        main_scheduler = CosineAnnealingLR(
            self.optimizer,
            T_max=total_steps - self.config.warmup_steps,
            eta_min=self.config.learning_rate * 0.1,
        )
        
        # Combine
        return SequentialLR(
            self.optimizer,
            schedulers=[warmup_scheduler, main_scheduler],
            milestones=[self.config.warmup_steps],
        )
    
    def train(self, num_epochs: Optional[int] = None) -> Dict:
        """
        Run training loop.
        
        Returns training statistics.
        """
        if not self.train_loader:
            raise ValueError("No training dataset provided")
        
        num_epochs = num_epochs or self.config.num_epochs
        
        stats = {
            "train_loss": [],
            "eval_loss": [],
            "learning_rate": [],
            "steps": [],
        }
        
        start_time = time.time()
        
        for epoch in range(num_epochs):
            self.epoch = epoch
            epoch_loss = 0.0
            num_batches = 0
            
            for batch_idx, batch in enumerate(self.train_loader):
                # Move batch to device
                input_ids = batch["input_ids"].to(self.device)
                labels = batch["labels"].to(self.device)
                
                # Forward pass
                output = self.model(input_ids, labels=labels)
                loss = output["loss"]
                
                # Scale loss for gradient accumulation
                scaled_loss = loss / self.config.gradient_accumulation_steps
                
                # Backward pass
                scaled_loss.backward()
                
                # Gradient accumulation
                if (batch_idx + 1) % self.config.gradient_accumulation_steps == 0:
                    # Clip gradients
                    torch.nn.utils.clip_grad_norm_(
                        self.model.parameters(),
                        self.config.max_grad_norm,
                    )
                    
                    # Optimizer step
                    self.optimizer.step()
                    self.optimizer.zero_grad()
                    
                    # Scheduler step
                    self.scheduler.step()
                    
                    self.global_step += 1
                    epoch_loss += loss.item()
                    num_batches += 1
                    
                    # Logging
                    if self.global_step % self.config.log_every == 0:
                        lr = self.optimizer.param_groups[0]['lr']
                        elapsed = time.time() - start_time
                        
                        print(
                            f"Step {self.global_step} | "
                            f"Epoch {epoch + 1}/{num_epochs} | "
                            f"Loss: {loss.item():.4f} | "
                            f"LR: {lr:.2e} | "
                            f"Time: {elapsed:.1f}s"
                        )
                        
                        stats["train_loss"].append(loss.item())
                        stats["learning_rate"].append(lr)
                        stats["steps"].append(self.global_step)
                    
                    # Evaluation
                    if self.eval_loader and self.global_step % self.config.eval_every == 0:
                        eval_loss = self.evaluate()
                        stats["eval_loss"].append(eval_loss)
                        
                        print(f"Evaluation loss: {eval_loss:.4f}")
                        
                        # Save best model
                        if eval_loss < self.best_loss:
                            self.best_loss = eval_loss
                            self.save("best_model.pt")
                    
                    # Checkpoint
                    if self.global_step % self.config.save_every == 0:
                        self.save(f"checkpoint_{self.global_step}.pt")
                    
                    # Early stopping if max_steps reached
                    if self.config.max_steps > 0 and self.global_step >= self.config.max_steps:
                        print(f"Reached max steps ({self.config.max_steps})")
                        return stats
        
        # Final save
        self.save("final_model.pt")
        
        total_time = time.time() - start_time
        print(f"\nTraining completed in {total_time:.1f}s")
        print(f"Final loss: {epoch_loss / num_batches:.4f}")
        
        return stats
    
    def evaluate(self) -> float:
        """Evaluate model on validation set."""
        self.model.eval()
        total_loss = 0.0
        num_batches = 0
        
        with torch.no_grad():
            for batch in self.eval_loader:
                input_ids = batch["input_ids"].to(self.device)
                labels = batch["labels"].to(self.device)
                
                output = self.model(input_ids, labels=labels)
                total_loss += output["loss"].item()
                num_batches += 1
        
        self.model.train()
        return total_loss / num_batches if num_batches > 0 else 0.0
    
    def save(self, filename: str) -> None:
        """Save checkpoint."""
        checkpoint = {
            "model_state_dict": self.model.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "scheduler_state_dict": self.scheduler.state_dict(),
            "global_step": self.global_step,
            "epoch": self.epoch,
            "best_loss": self.best_loss,
            "config": self.config.__dict__,
        }
        
        torch.save(checkpoint, self.save_dir / filename)
        print(f"Saved checkpoint: {filename}")
    
    def load(self, filename: str) -> None:
        """Load checkpoint."""
        checkpoint = torch.load(self.save_dir / filename, map_location=self.device)
        
        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        self.scheduler.load_state_dict(checkpoint["scheduler_state_dict"])
        self.global_step = checkpoint["global_step"]
        self.epoch = checkpoint["epoch"]
        self.best_loss = checkpoint["best_loss"]
        
        print(f"Loaded checkpoint: {filename} (step {self.global_step})")


def create_trainer(
    model: nn.Module,
    config: TrainingConfig,
    train_texts: Optional[List[str]] = None,
    eval_texts: Optional[List[str]] = None,
    tokenizer=None,
) -> Trainer:
    """Create a trainer with datasets."""
    
    # Create datasets if texts provided
    train_dataset = None
    eval_dataset = None
    
    if train_texts and tokenizer:
        # Tokenize texts
        all_tokens = []
        for text in train_texts:
            all_tokens.extend(tokenizer.encode(text, add_special_tokens=True))
        
        train_dataset = TextDataset(all_tokens, seq_len=config.max_seq_len)
    
    if eval_texts and tokenizer:
        all_tokens = []
        for text in eval_texts:
            all_tokens.extend(tokenizer.encode(text, add_special_tokens=True))
        
        eval_dataset = TextDataset(all_tokens, seq_len=config.max_seq_len)
    
    return Trainer(model, config, train_dataset, eval_dataset)


if __name__ == "__main__":
    print("=" * 60)
    print("TRAINER TEST")
    print("=" * 60)
    
    from .transformer import TransformerLM
    from .tokenizer import CharacterTokenizer
    
    # Create tokenizer
    tokenizer = CharacterTokenizer()
    
    # Create model
    config = TrainingConfig(
        vocab_size=tokenizer.vocab_size,
        d_model=64,
        num_heads=4,
        num_layers=2,
        max_seq_len=64,
        batch_size=2,
        num_epochs=1,
        max_steps=20,
    )
    
    model = TransformerLM(
        vocab_size=config.vocab_size,
        d_model=config.d_model,
        num_heads=config.num_heads,
        num_layers=config.num_layers,
        max_seq_len=config.max_seq_len,
    )
    
    # Sample texts
    texts = [
        "def hello():\n    return 'world'\n",
        "class Dog:\n    def bark(self):\n        print('woof')\n",
        "x = 10\ny = 20\nprint(x + y)\n",
    ]
    
    # Create trainer
    trainer = create_trainer(
        model=model,
        config=config,
        train_texts=texts,
        tokenizer=tokenizer,
    )
    
    # Train
    stats = trainer.train()
    
    print(f"\nTraining stats: {len(stats['train_loss'])} loss points recorded")
    print(f"Final loss: {stats['train_loss'][-1]:.4f}")
    
    print("\n" + "=" * 60)
    print("TRAINER WORKING!")
    print("=" * 60)
