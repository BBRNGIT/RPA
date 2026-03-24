"""
Dataset Curriculum Builder - Create curriculum batches from interpreted data.

Organizes sequences into progressive batches for learning.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from pathlib import Path
import json
import uuid
import logging
from datetime import datetime

from .dataset_loader import DatasetLoader, DatasetConfig
from .dataset_interpreter import DatasetInterpreter, InterpretedSequence

logger = logging.getLogger(__name__)


@dataclass
class CurriculumBatch:
    """A batch of curriculum content ready for learning."""
    batch_id: str
    domain: str
    hierarchy_level: int
    difficulty: int
    lessons: List[Dict[str, Any]]
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "batch_id": self.batch_id,
            "domain": self.domain,
            "hierarchy_level": self.hierarchy_level,
            "difficulty": self.difficulty,
            "lessons": self.lessons,
            "metadata": self.metadata,
            "created_at": self.created_at
        }

    def save(self, path: str) -> None:
        """Save batch to JSON file."""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)


class DatasetCurriculumBuilder:
    """
    Build curriculum batches from interpreted dataset sequences.

    Organizes sequences into:
    - Progressive batches (primitives first, then patterns, then complex)
    - Difficulty levels
    - Domain-specific groupings
    """

    def __init__(
        self,
        loader: Optional[DatasetLoader] = None,
        interpreter: Optional[DatasetInterpreter] = None
    ):
        """
        Initialize CurriculumBuilder.

        Args:
            loader: Optional DatasetLoader instance
            interpreter: Optional DatasetInterpreter instance
        """
        self.loader = loader or DatasetLoader()
        self.interpreter = interpreter or DatasetInterpreter()

    def build_curriculum_from_dataset(
        self,
        samples: List[Dict[str, Any]],
        config: DatasetConfig,
        num_batches: int = 5,
        batch_size: int = 50
    ) -> List[CurriculumBatch]:
        """
        Build curriculum batches from a dataset.

        Args:
            samples: List of dataset samples
            config: Dataset configuration
            num_batches: Number of batches to create per hierarchy level
            batch_size: Number of lessons per batch

        Returns:
            List of CurriculumBatch objects
        """
        # Interpret the dataset
        if config.domain in ("python", "javascript", "java", "cpp"):
            sequences = self.interpreter.interpret_code_dataset(samples, config)
        else:
            sequences = self.interpreter.interpret_text_dataset(samples, config)

        # Apply filters
        sequences = self.interpreter.filter_by_quality(
            sequences,
            min_quality=config.quality_threshold,
            min_length=config.min_length,
            max_length=config.max_length
        )

        # Deduplicate and rank
        sequences = self.interpreter.deduplicate(sequences)
        sequences = self.interpreter.rank_by_frequency(sequences)

        # Limit sample size
        if config.sample_size:
            sequences = sequences[:config.sample_size]

        # Group by hierarchy level
        by_hierarchy: Dict[int, List[InterpretedSequence]] = {}
        for seq in sequences:
            level = seq.hierarchy_level
            if level not in by_hierarchy:
                by_hierarchy[level] = []
            by_hierarchy[level].append(seq)

        # Create batches for each hierarchy level
        batches = []
        for level in sorted(by_hierarchy.keys()):
            level_sequences = by_hierarchy[level]
            level_batches = self._create_batches_for_level(
                level_sequences,
                config.domain,
                level,
                num_batches,
                batch_size
            )
            batches.extend(level_batches)

        logger.info(f"Created {len(batches)} batches from {len(sequences)} sequences")
        return batches

    def _create_batches_for_level(
        self,
        sequences: List[InterpretedSequence],
        domain: str,
        hierarchy_level: int,
        num_batches: int,
        batch_size: int
    ) -> List[CurriculumBatch]:
        """Create batches for a specific hierarchy level."""
        batches = []

        # Split sequences into batches
        total_batches = min(num_batches, (len(sequences) + batch_size - 1) // batch_size)

        for i in range(total_batches):
            start = i * batch_size
            end = start + batch_size
            batch_sequences = sequences[start:end]

            if not batch_sequences:
                break

            # Create lessons
            lessons = []
            for idx, seq in enumerate(batch_sequences):
                lesson = {
                    "lesson_id": f"{domain[:3]}_{hierarchy_level}_{i}_{idx}",
                    "content": seq.content,
                    "type": seq.sequence_type,
                    "hierarchy_level": seq.hierarchy_level,
                    "composition": seq.composition,
                    "metadata": seq.metadata,
                    "source_dataset": seq.source,
                    "dataset_frequency": seq.frequency,
                    "difficulty": hierarchy_level + 1
                }
                lessons.append(lesson)

            # Create batch
            batch = CurriculumBatch(
                batch_id=f"{domain}_batch_{hierarchy_level}_{i}_{uuid.uuid4().hex[:8]}",
                domain=domain,
                hierarchy_level=hierarchy_level,
                difficulty=hierarchy_level + 1,
                lessons=lessons,
                metadata={
                    "sequence_count": len(lessons),
                    "avg_frequency": sum(s.frequency for s in batch_sequences) / len(batch_sequences)
                }
            )
            batches.append(batch)

        return batches

    def create_batch(
        self,
        sequences: List[InterpretedSequence],
        batch_id: str,
        hierarchy_level: int,
        difficulty: int
    ) -> CurriculumBatch:
        """
        Create a single batch from sequences.

        Args:
            sequences: List of sequences for the batch
            batch_id: Unique identifier for the batch
            hierarchy_level: Hierarchy level of the sequences
            difficulty: Difficulty rating (1-5)

        Returns:
            CurriculumBatch object
        """
        lessons = []
        domain = sequences[0].domain if sequences else "unknown"

        for idx, seq in enumerate(sequences):
            lesson = {
                "lesson_id": f"{batch_id}_{idx}",
                "content": seq.content,
                "type": seq.sequence_type,
                "hierarchy_level": seq.hierarchy_level,
                "composition": seq.composition,
                "metadata": seq.metadata,
                "source_dataset": seq.source,
                "dataset_frequency": seq.frequency,
                "difficulty": difficulty
            }
            lessons.append(lesson)

        return CurriculumBatch(
            batch_id=batch_id,
            domain=domain,
            hierarchy_level=hierarchy_level,
            difficulty=difficulty,
            lessons=lessons,
            metadata={"sequence_count": len(lessons)}
        )

    def validate_curriculum_progression(
        self,
        batches: List[CurriculumBatch]
    ) -> Dict[str, Any]:
        """
        Validate that curriculum batches form a proper progression.

        Args:
            batches: List of batches to validate

        Returns:
            Validation result with:
            - is_valid: bool
            - issues: List[str]
            - recommendations: List[str]
        """
        issues = []
        recommendations = []

        if not batches:
            return {
                "is_valid": False,
                "issues": ["No batches provided"],
                "recommendations": ["Create at least one batch"]
            }

        # Group by hierarchy level
        by_level: Dict[int, List[CurriculumBatch]] = {}
        for batch in batches:
            level = batch.hierarchy_level
            if level not in by_level:
                by_level[level] = []
            by_level[level].append(batch)

        # Check for missing levels
        levels = sorted(by_level.keys())
        if levels:
            expected = list(range(min(levels), max(levels) + 1))
            missing = set(expected) - set(levels)
            if missing:
                issues.append(f"Missing hierarchy levels: {sorted(missing)}")
                recommendations.append(
                    f"Add batches for hierarchy levels {sorted(missing)} to complete progression"
                )

        # Check for empty batches
        for batch in batches:
            if not batch.lessons:
                issues.append(f"Batch {batch.batch_id} has no lessons")

        # Check difficulty progression
        for level in levels:
            level_batches = by_level[level]
            difficulties = [b.difficulty for b in level_batches]
            if len(set(difficulties)) > 1:
                issues.append(
                    f"Inconsistent difficulties at hierarchy level {level}: {difficulties}"
                )

        # Check batch ordering
        for i, batch in enumerate(batches[:-1]):
            next_batch = batches[i + 1]
            if batch.hierarchy_level > next_batch.hierarchy_level:
                issues.append(
                    f"Batches out of order: {batch.batch_id} (level {batch.hierarchy_level}) "
                    f"before {next_batch.batch_id} (level {next_batch.hierarchy_level})"
                )
                recommendations.append("Sort batches by hierarchy level before export")

        # Check for composition references
        all_contents = set()
        for batch in batches:
            for lesson in batch.lessons:
                all_contents.add(lesson["content"])

        missing_refs = set()
        for batch in batches:
            for lesson in batch.lessons:
                for comp in lesson.get("composition", []):
                    if comp not in all_contents and len(comp) > 1:
                        missing_refs.add(comp)

        if missing_refs:
            issues.append(f"Missing composition references: {list(missing_refs)[:10]}...")
            recommendations.append(
                "Ensure primitive patterns are included before patterns that reference them"
            )

        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "recommendations": recommendations,
            "statistics": {
                "total_batches": len(batches),
                "total_lessons": sum(len(b.lessons) for b in batches),
                "hierarchy_levels": levels
            }
        }

    def export_curriculum(
        self,
        batches: List[CurriculumBatch],
        output_dir: str,
        domain: Optional[str] = None
    ) -> List[str]:
        """
        Export curriculum batches to JSON files.

        Args:
            batches: List of batches to export
            output_dir: Directory to save files
            domain: Optional domain subdirectory

        Returns:
            List of exported file paths
        """
        output_path = Path(output_dir)
        if domain:
            output_path = output_path / domain

        output_path.mkdir(parents=True, exist_ok=True)

        exported = []
        for batch in batches:
            filename = f"{batch.batch_id}.json"
            file_path = output_path / filename
            batch.save(str(file_path))
            exported.append(str(file_path))

        logger.info(f"Exported {len(exported)} batches to {output_path}")
        return exported

    def build_quick_curriculum(
        self,
        texts: List[str],
        domain: str = "english",
        batch_size: int = 50
    ) -> List[CurriculumBatch]:
        """
        Quickly build curriculum from a list of texts.

        Convenience method for simple use cases.

        Args:
            texts: List of text strings
            domain: Domain name
            batch_size: Number of lessons per batch

        Returns:
            List of CurriculumBatch objects
        """
        samples = [{"text": t} for t in texts]
        config = DatasetConfig(
            dataset_name="quick_curriculum",
            domain=domain,
            text_field="text"
        )
        return self.build_curriculum_from_dataset(
            samples,
            config,
            num_batches=10,
            batch_size=batch_size
        )

    def merge_batches(
        self,
        batches: List[CurriculumBatch],
        max_lessons: int = 100
    ) -> CurriculumBatch:
        """
        Merge multiple batches into one.

        Args:
            batches: List of batches to merge
            max_lessons: Maximum lessons in merged batch

        Returns:
            Merged CurriculumBatch
        """
        if not batches:
            raise ValueError("No batches to merge")

        all_lessons = []
        domain = batches[0].domain
        min_level = min(b.hierarchy_level for b in batches)

        for batch in batches:
            all_lessons.extend(batch.lessons)

        # Limit lessons
        all_lessons = all_lessons[:max_lessons]

        return CurriculumBatch(
            batch_id=f"{domain}_merged_{uuid.uuid4().hex[:8]}",
            domain=domain,
            hierarchy_level=min_level,
            difficulty=min(b.difficulty for b in batches),
            lessons=all_lessons,
            metadata={
                "merged_from": [b.batch_id for b in batches],
                "lesson_count": len(all_lessons)
            }
        )
