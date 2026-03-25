"""
Training Pipeline - Loss, Optimizer, and Training Loop.

This is where the model actually LEARNS:
1. Loss function: Measures how wrong the model is
2. Optimizer: Updates weights to reduce loss
3. Training loop: Forward pass → Loss → Backward pass → Weight update

The training process:
- Input: Question/pattern from curriculum
- Target: Expected answer/pattern from curriculum
- Loss: Distance between model output and target
- Update: Adjust weights to minimize loss
"""

import math
import random
import json
from typing import List, Dict, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime


def dot_product(v1: List[float], v2: List[float]) -> float:
    """Compute dot product of two vectors."""
    return sum(a * b for a, b in zip(v1, v2))


def vector_subtract(v1: List[float], v2: List[float]) -> List[float]:
    """Subtract two vectors."""
    return [a - b for a, b in zip(v1, v2)]


def vector_multiply(v: List[float], scalar: float) -> List[float]:
    """Multiply vector by scalar."""
    return [x * scalar for x in v]


def vector_add(v1: List[float], v2: List[float]) -> List[float]:
    """Add two vectors."""
    return [a + b for a, b in zip(v1, v2)]


def vector_norm(v: List[float]) -> float:
    """Compute L2 norm of vector."""
    return math.sqrt(sum(x * x for x in v))


def matrix_multiply_scalar(M: List[List[float]], s: float) -> List[List[float]]:
    """Multiply matrix by scalar."""
    return [[x * s for x in row] for row in M]


def matrix_add(M1: List[List[float]], M2: List[List[float]]) -> List[List[float]]:
    """Add two matrices."""
    return [[a + b for a, b in zip(row1, row2)] for row1, row2 in zip(M1, M2)]


def outer_product(v1: List[float], v2: List[float]) -> List[List[float]]:
    """Compute outer product of two vectors."""
    return [[a * b for b in v2] for a in v1]


@dataclass
class TrainingConfig:
    """Configuration for training."""
    learning_rate: float = 0.001
    batch_size: int = 1
    epochs: int = 10
    warmup_steps: int = 100
    max_grad_norm: float = 1.0
    save_every: int = 100
    log_every: int = 10

    def to_dict(self) -> Dict:
        return {
            "learning_rate": self.learning_rate,
            "batch_size": self.batch_size,
            "epochs": self.epochs,
            "warmup_steps": self.warmup_steps,
            "max_grad_norm": self.max_grad_norm,
            "save_every": self.save_every,
            "log_every": self.log_every,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "TrainingConfig":
        return cls(**{k: v for k, v in data.items() if hasattr(cls, k)})


@dataclass
class TrainingState:
    """State tracking during training."""
    epoch: int = 0
    step: int = 0
    total_loss: float = 0.0
    best_loss: float = float('inf')
    losses: List[float] = field(default_factory=list)
    start_time: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict:
        return {
            "epoch": self.epoch,
            "step": self.step,
            "total_loss": self.total_loss,
            "best_loss": self.best_loss,
            "losses": self.losses[-100:],  # Keep last 100
            "start_time": self.start_time,
        }


class PatternLoss:
    """
    Loss function for pattern learning.

    Measures the distance between model output and target pattern.
    Uses cosine similarity loss: 1 - cos(output, target)

    Also supports:
    - MSE loss: Mean squared error between vectors
    - Combined loss: Weighted combination
    """

    def __init__(self, loss_type: str = "cosine"):
        self.loss_type = loss_type

    def cosine_loss(self, output: List[float], target: List[float]) -> float:
        """
        Cosine similarity loss.

        Loss = 1 - cos(output, target)
        Range: [0, 2] where 0 = identical, 2 = opposite
        """
        norm_out = vector_norm(output)
        norm_tgt = vector_norm(target)

        if norm_out == 0 or norm_tgt == 0:
            return 1.0

        cos_sim = dot_product(output, target) / (norm_out * norm_tgt)
        # Clamp to [-1, 1] to handle numerical issues
        cos_sim = max(-1.0, min(1.0, cos_sim))

        return 1.0 - cos_sim

    def mse_loss(self, output: List[float], target: List[float]) -> float:
        """Mean squared error loss."""
        diff = vector_subtract(output, target)
        return sum(d * d for d in diff) / len(diff)

    def forward(self, output: List[float], target: List[float]) -> float:
        """
        Compute loss between output and target.

        Args:
            output: Model output vector
            target: Target pattern vector

        Returns:
            Loss value
        """
        if self.loss_type == "cosine":
            return self.cosine_loss(output, target)
        elif self.loss_type == "mse":
            return self.mse_loss(output, target)
        else:
            # Combined: 0.5 * cosine + 0.5 * mse
            return 0.5 * self.cosine_loss(output, target) + 0.5 * self.mse_loss(output, target)

    def __call__(self, output: List[float], target: List[float]) -> float:
        return self.forward(output, target)


class SGDOptimizer:
    """
    Stochastic Gradient Descent optimizer with momentum.

    Updates weights using:
        v = momentum * v - lr * gradient
        w = w + v

    Also supports weight decay (L2 regularization).
    """

    def __init__(
        self,
        learning_rate: float = 0.001,
        momentum: float = 0.9,
        weight_decay: float = 0.0,
    ):
        self.lr = learning_rate
        self.momentum = momentum
        self.weight_decay = weight_decay

        # Velocity storage for momentum
        self.velocities: Dict[str, Any] = {}

    def _get_velocity(self, name: str, shape: Any) -> Any:
        """Get or create velocity tensor."""
        if name not in self.velocities:
            if isinstance(shape, list) and isinstance(shape[0], list):
                # Matrix
                self.velocities[name] = [[0.0 for _ in row] for row in shape]
            else:
                # Vector
                self.velocities[name] = [0.0] * len(shape)
        return self.velocities[name]

    def update_matrix(self, name: str, weights: List[List[float]], grad: List[List[float]]) -> List[List[float]]:
        """Update a weight matrix."""
        v = self._get_velocity(name, weights)

        for i in range(len(weights)):
            for j in range(len(weights[0])):
                # Apply weight decay
                if self.weight_decay > 0:
                    grad[i][j] += self.weight_decay * weights[i][j]

                # Update velocity
                v[i][j] = self.momentum * v[i][j] - self.lr * grad[i][j]

                # Update weight
                weights[i][j] += v[i][j]

        return weights

    def update_vector(self, name: str, weights: List[float], grad: List[float]) -> List[float]:
        """Update a weight vector."""
        v = self._get_velocity(name, weights)

        for i in range(len(weights)):
            # Apply weight decay
            if self.weight_decay > 0:
                grad[i] += self.weight_decay * weights[i]

            # Update velocity
            v[i] = self.momentum * v[i] - self.lr * grad[i]

            # Update weight
            weights[i] += v[i]

        return weights


class AdamOptimizer:
    """
    Adam optimizer.

    Adaptive Moment Estimation - combines momentum and RMSprop.
    Updates weights using:
        m = beta1 * m + (1 - beta1) * grad
        v = beta2 * v + (1 - beta2) * grad^2
        w = w - lr * m / (sqrt(v) + eps)
    """

    def __init__(
        self,
        learning_rate: float = 0.001,
        beta1: float = 0.9,
        beta2: float = 0.999,
        eps: float = 1e-8,
        weight_decay: float = 0.0,
    ):
        self.lr = learning_rate
        self.beta1 = beta1
        self.beta2 = beta2
        self.eps = eps
        self.weight_decay = weight_decay

        # Moment storage
        self.m: Dict[str, Any] = {}  # First moment
        self.v: Dict[str, Any] = {}  # Second moment
        self.t: int = 0  # Time step

    def _get_moments(self, name: str, shape: Any) -> Tuple[Any, Any]:
        """Get or create moment tensors."""
        if name not in self.m:
            if isinstance(shape, list) and isinstance(shape[0], list):
                self.m[name] = [[0.0 for _ in row] for row in shape]
                self.v[name] = [[0.0 for _ in row] for row in shape]
            else:
                self.m[name] = [0.0] * len(shape)
                self.v[name] = [0.0] * len(shape)
        return self.m[name], self.v[name]

    def update_matrix(self, name: str, weights: List[List[float]], grad: List[List[float]]) -> List[List[float]]:
        """Update a weight matrix."""
        m, v = self._get_moments(name, weights)
        self.t += 1

        for i in range(len(weights)):
            for j in range(len(weights[0])):
                g = grad[i][j]

                # Apply weight decay
                if self.weight_decay > 0:
                    g += self.weight_decay * weights[i][j]

                # Update moments
                m[i][j] = self.beta1 * m[i][j] + (1 - self.beta1) * g
                v[i][j] = self.beta2 * v[i][j] + (1 - self.beta2) * g * g

                # Bias correction
                m_hat = m[i][j] / (1 - self.beta1 ** self.t)
                v_hat = v[i][j] / (1 - self.beta2 ** self.t)

                # Update weight
                weights[i][j] -= self.lr * m_hat / (math.sqrt(v_hat) + self.eps)

        return weights

    def update_vector(self, name: str, weights: List[float], grad: List[float]) -> List[float]:
        """Update a weight vector."""
        m, v = self._get_moments(name, weights)
        self.t += 1

        # Pre-compute bias correction factors
        bias_correction1 = 1 - self.beta1 ** self.t
        bias_correction2 = 1 - self.beta2 ** self.t

        for i in range(len(weights)):
            g = grad[i]

            # Apply weight decay
            if self.weight_decay > 0:
                g += self.weight_decay * weights[i]

            # Update moments
            m[i] = self.beta1 * m[i] + (1 - self.beta1) * g
            v[i] = self.beta2 * v[i] + (1 - self.beta2) * g * g

            # Bias correction
            m_hat = m[i] / bias_correction1 if bias_correction1 > 0 else m[i]
            v_hat = v[i] / bias_correction2 if bias_correction2 > 0 else v[i]

            # Update weight
            weights[i] -= self.lr * m_hat / (math.sqrt(v_hat) + self.eps)

        return weights


class Trainer:
    """
    Training pipeline for RPA model.

    Handles the full training loop:
    1. Load training data from curriculum
    2. Forward pass through model
    3. Compute loss
    4. Backward pass (gradient computation)
    5. Update weights

    Args:
        model: The RPAModel to train
        config: Training configuration
    """

    def __init__(
        self,
        model: "RPAModel",
        config: Optional[TrainingConfig] = None,
        optimizer_type: str = "adam"
    ):
        from .transformer import RPAModel
        self.model = model
        self.config = config or TrainingConfig()
        self.loss_fn = PatternLoss(loss_type="cosine")

        # Create optimizer
        if optimizer_type == "adam":
            self.optimizer = AdamOptimizer(learning_rate=self.config.learning_rate)
        else:
            self.optimizer = SGDOptimizer(learning_rate=self.config.learning_rate)

        self.state = TrainingState()

    def get_training_pairs(self) -> List[Tuple[str, str]]:
        """
        Extract question-answer pairs from curriculum.

        Returns list of (question, answer) tuples.
        """
        pairs = []
        vocab = self.model.encoder.vocab

        for pattern_id, pattern in vocab.patterns.items():
            # Extract potential Q&A pairs from pattern metadata
            metadata = pattern.metadata
            original = metadata.get("original_item", {})

            # Look for Q&A structure
            if "question" in original and "answer" in original:
                pairs.append((original["question"], original["answer"]))
            elif "instruction" in original and "examples" in original:
                # Use instruction as question, first example as answer
                examples = original["examples"]
                if examples and isinstance(examples, list):
                    pairs.append((original["instruction"], str(examples[0])))
            elif "concept" in original and "instruction" in original:
                # Concept question, instruction answer
                pairs.append((f"What is {original['concept']}?", original["instruction"]))

        # If no structured pairs, create pattern-to-pattern pairs
        if not pairs:
            patterns = list(vocab.patterns.values())
            for i in range(min(100, len(patterns) - 1)):
                # Use consecutive patterns as pairs
                pairs.append((patterns[i].text, patterns[i + 1].text))

        return pairs

    def compute_gradients(
        self,
        query: List[float],
        context: List[List[float]],
        target: List[float]
    ) -> Dict[str, Any]:
        """
        Compute gradients for model weights.

        Uses numerical gradient approximation:
            grad ≈ (loss(w + eps) - loss(w - eps)) / (2 * eps)

        This is slow but works without automatic differentiation.
        """
        gradients = {"attention": [], "feed_forward": []}
        eps = 1e-5

        # Get current output
        output, _ = self.model.transformer(query, context)
        base_loss = self.loss_fn(output, target)

        # For efficiency, we only compute gradients for a subset of weights
        # In a real implementation, this would use backpropagation

        # This is a simplified gradient computation
        # We'll perturb the output and see how loss changes
        grad_output = []
        for i in range(len(output)):
            # Perturb output[i]
            output_plus = output.copy()
            output_plus[i] += eps
            loss_plus = self.loss_fn(output_plus, target)

            # Numerical gradient
            grad = (loss_plus - base_loss) / eps
            grad_output.append(grad)

        return {
            "output_gradient": grad_output,
            "loss": base_loss,
        }

    def train_step(
        self,
        question: str,
        answer: str
    ) -> float:
        """
        Single training step.

        Args:
            question: Input question
            answer: Target answer

        Returns:
            Loss value for this step
        """
        # Encode question and answer
        query = self.model.encoder.encode(question)
        target = self.model.encoder.encode(answer)

        # Get context
        matches = self.model.encoder.decode(query, top_k=10)
        context_vectors = [
            self.model.encoder.vocab.get_embedding(p.pattern_id)
            for p, _ in matches
        ]
        context_vectors = [v for v in context_vectors if v is not None]

        if not context_vectors:
            return 0.0

        # Forward pass
        output, _ = self.model.transformer(query, context_vectors)

        # Compute loss
        loss = self.loss_fn(output, target)

        # Compute gradients and update (simplified)
        # In practice, this would use backpropagation
        self._update_weights_simple(query, context_vectors, target)

        return loss

    def _update_weights_simple(
        self,
        query: List[float],
        context: List[List[float]],
        target: List[float]
    ) -> None:
        """
        Simplified weight update using gradient approximation.

        This moves weights in the direction that reduces loss.
        """
        eps = 0.01  # Perturbation size

        # Get current output
        output, _ = self.model.transformer(query, context)
        current_loss = self.loss_fn(output, target)

        # Update each transformer block
        for block_idx, block in enumerate(self.model.transformer.blocks):
            # Update attention weights (simplified)
            attn_weights = block.attention.get_weights()

            # Perturb Wq slightly in direction that might help
            for i in range(min(10, len(attn_weights.Wq))):
                for j in range(min(10, len(attn_weights.Wq[0]))):
                    # Try small perturbation
                    old_val = attn_weights.Wq[i][j]

                    # Try positive perturbation
                    attn_weights.Wq[i][j] = old_val + eps
                    output_plus, _ = self.model.transformer(query, context)
                    loss_plus = self.loss_fn(output_plus, target)

                    # Try negative perturbation
                    attn_weights.Wq[i][j] = old_val - eps
                    output_minus, _ = self.model.transformer(query, context)
                    loss_minus = self.loss_fn(output_minus, target)

                    # Compute gradient
                    grad = (loss_plus - loss_minus) / (2 * eps)

                    # Update weight
                    attn_weights.Wq[i][j] = old_val - self.config.learning_rate * grad

            block.attention.set_weights(attn_weights)

        self.state.step += 1

    def train(
        self,
        epochs: Optional[int] = None,
        save_path: Optional[str] = None,
        callback: Optional[Callable[[int, float], None]] = None
    ) -> List[float]:
        """
        Full training loop.

        Args:
            epochs: Number of epochs to train
            save_path: Path to save model checkpoints
            callback: Optional callback(epoch, loss)

        Returns:
            List of loss values
        """
        epochs = epochs or self.config.epochs

        # Get training pairs
        pairs = self.get_training_pairs()
        if not pairs:
            print("No training pairs found!")
            return []

        print(f"Training on {len(pairs)} pairs for {epochs} epochs")

        all_losses = []

        for epoch in range(epochs):
            self.state.epoch = epoch
            epoch_loss = 0.0

            # Shuffle pairs
            random.shuffle(pairs)

            for i, (question, answer) in enumerate(pairs):
                loss = self.train_step(question, answer)
                epoch_loss += loss

                # Log progress
                if (i + 1) % self.config.log_every == 0:
                    avg_loss = epoch_loss / (i + 1)
                    print(f"  Step {i+1}/{len(pairs)}, Loss: {avg_loss:.4f}")

            # Average loss for epoch
            avg_epoch_loss = epoch_loss / len(pairs)
            all_losses.append(avg_epoch_loss)
            self.state.losses.append(avg_epoch_loss)

            # Update best loss
            if avg_epoch_loss < self.state.best_loss:
                self.state.best_loss = avg_epoch_loss
                if save_path:
                    self.model.save(save_path)
                    print(f"  New best loss! Model saved to {save_path}")

            # Callback
            if callback:
                callback(epoch, avg_epoch_loss)

            print(f"Epoch {epoch + 1}/{epochs}, Loss: {avg_epoch_loss:.4f}")

        return all_losses

    def save_state(self, path: str) -> None:
        """Save training state."""
        with open(path, 'w') as f:
            json.dump({
                "config": self.config.to_dict(),
                "state": self.state.to_dict(),
            }, f, indent=2)

    def load_state(self, path: str) -> None:
        """Load training state."""
        with open(path, 'r') as f:
            data = json.load(f)
        self.config = TrainingConfig.from_dict(data["config"])
        self.state = TrainingState(**{
            k: v for k, v in data["state"].items()
            if hasattr(self.state, k)
        })


if __name__ == "__main__":
    print("=" * 60)
    print("TRAINING PIPELINE TEST")
    print("=" * 60)

    from rpa.model import PatternEncoder
    from rpa.model.transformer import RPAModel
    from pathlib import Path

    # Create encoder
    encoder = PatternEncoder(embed_dim=128)
    curriculum_path = Path(__file__).parent.parent.parent / "curriculum"

    if curriculum_path.exists():
        print(f"Loading curriculum from: {curriculum_path}")
        encoder.load_curriculum(curriculum_path)
        print(f"Loaded {encoder.get_vocab_size()} patterns")
    else:
        print("Creating sample patterns...")
        for i in range(10):
            encoder.vocab.add_pattern(
                type("Pattern", (), {
                    "pattern_id": f"p{i}",
                    "text": f"Sample pattern {i}",
                    "domain": "test",
                    "pattern_type": "test",
                    "metadata": {}
                })()
            )

    # Create model
    model = RPAModel(encoder=encoder, num_layers=2, num_heads=4, seed=42)
    print(f"\nModel created with {model.transformer.count_parameters():,} parameters")

    # Create trainer
    config = TrainingConfig(epochs=2, learning_rate=0.001, log_every=5)
    trainer = Trainer(model, config)

    # Get training pairs
    pairs = trainer.get_training_pairs()
    print(f"Found {len(pairs)} training pairs")

    if pairs:
        print("\nSample pairs:")
        for i, (q, a) in enumerate(pairs[:3]):
            print(f"  Q: {q[:50]}...")
            print(f"  A: {a[:50]}...")
            print()

    # Train
    print("Starting training...")
    losses = trainer.train(epochs=2)

    print("\n" + "=" * 60)
    print(f"TRAINING COMPLETE")
    print(f"Final loss: {losses[-1]:.4f}")
    print(f"Best loss: {trainer.state.best_loss:.4f}")
    print("=" * 60)
