"""
Dataset Loader - Load datasets from Hugging Face Hub and local sources.

Supports:
- Hugging Face datasets (via datasets library)
- Local datasets (CSV, JSON, Parquet, text files)
- Schema validation
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Union
from pathlib import Path
import json
import csv
import logging

logger = logging.getLogger(__name__)

# Optional import for Hugging Face datasets
try:
    from datasets import Dataset, load_dataset
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False
    Dataset = None
    load_dataset = None


@dataclass
class DatasetConfig:
    """Configuration for dataset loading and interpretation."""
    dataset_name: str
    domain: str  # "english", "python", "javascript", etc.
    split: str = "train"
    text_field: str = "text"
    metadata_fields: List[str] = field(default_factory=list)
    min_length: int = 1
    max_length: int = 1000
    sample_size: Optional[int] = None
    deduplication: bool = True
    language_filter: Optional[str] = None
    quality_threshold: float = 0.5

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "dataset_name": self.dataset_name,
            "domain": self.domain,
            "split": self.split,
            "text_field": self.text_field,
            "metadata_fields": self.metadata_fields,
            "min_length": self.min_length,
            "max_length": self.max_length,
            "sample_size": self.sample_size,
            "deduplication": self.deduplication,
            "language_filter": self.language_filter,
            "quality_threshold": self.quality_threshold
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DatasetConfig":
        """Create config from dictionary."""
        return cls(**data)


class DatasetLoader:
    """
    Load datasets from Hugging Face Hub and local sources.

    Provides a unified interface for loading various data sources
    into a format suitable for curriculum generation.
    """

    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize DatasetLoader.

        Args:
            cache_dir: Optional directory for caching downloaded datasets
        """
        self.cache_dir = cache_dir
        self._loaded_datasets: Dict[str, Any] = {}

    def load_huggingface_dataset(
        self,
        dataset_name: str,
        split: str = "train",
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Load a dataset from Hugging Face Hub.

        Args:
            dataset_name: Name of the dataset (e.g., "wikitext", "openwebtext")
            split: Dataset split to load ("train", "validation", "test")
            **kwargs: Additional arguments for load_dataset

        Returns:
            List of samples as dictionaries

        Raises:
            ImportError: If datasets library is not installed
            ValueError: If dataset cannot be loaded
        """
        if not HF_AVAILABLE:
            raise ImportError(
                "Hugging Face datasets library not installed. "
                "Install with: pip install datasets"
            )

        cache_key = f"{dataset_name}:{split}"

        # Check cache
        if cache_key in self._loaded_datasets:
            return self._loaded_datasets[cache_key]

        try:
            logger.info(f"Loading dataset '{dataset_name}' split '{split}'...")
            dataset = load_dataset(dataset_name, split=split, **kwargs)

            # Convert to list of dicts
            samples = [dict(item) for item in dataset]
            self._loaded_datasets[cache_key] = samples

            logger.info(f"Loaded {len(samples)} samples from {dataset_name}")
            return samples

        except Exception as e:
            raise ValueError(f"Failed to load dataset '{dataset_name}': {e}")

    def load_local_dataset(
        self,
        path: str,
        format: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Load a dataset from local file.

        Args:
            path: Path to the dataset file
            format: File format (csv, json, jsonl, txt, parquet).
                   Auto-detected from extension if not provided.

        Returns:
            List of samples as dictionaries

        Raises:
            FileNotFoundError: If file does not exist
            ValueError: If format is not supported
        """
        file_path = Path(path)

        if not file_path.exists():
            raise FileNotFoundError(f"Dataset file not found: {path}")

        # Auto-detect format
        if format is None:
            format = file_path.suffix.lstrip(".").lower()

        # Load based on format
        if format == "json":
            return self._load_json(file_path)
        elif format in ("jsonl", "ndjson"):
            return self._load_jsonl(file_path)
        elif format == "csv":
            return self._load_csv(file_path)
        elif format == "txt":
            return self._load_txt(file_path)
        elif format == "parquet":
            return self._load_parquet(file_path)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _load_json(self, path: Path) -> List[Dict[str, Any]]:
        """Load JSON file."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            # Try to find the main data array
            for key in ["data", "samples", "items", "records"]:
                if key in data and isinstance(data[key], list):
                    return data[key]
            # Return as single item
            return [data]
        else:
            raise ValueError(f"Unexpected JSON structure in {path}")

    def _load_jsonl(self, path: Path) -> List[Dict[str, Any]]:
        """Load JSONL (JSON Lines) file."""
        samples = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    samples.append(json.loads(line))
        return samples

    def _load_csv(self, path: Path) -> List[Dict[str, Any]]:
        """Load CSV file."""
        samples = []
        with open(path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                samples.append(dict(row))
        return samples

    def _load_txt(self, path: Path) -> List[Dict[str, Any]]:
        """Load plain text file (one sample per line or whole file)."""
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        lines = [line.strip() for line in content.split("\n") if line.strip()]

        # Return each line as a sample
        return [{"text": line} for line in lines]

    def _load_parquet(self, path: Path) -> List[Dict[str, Any]]:
        """Load Parquet file."""
        try:
            import pandas as pd
            df = pd.read_parquet(path)
            return df.to_dict("records")
        except ImportError:
            raise ImportError(
                "pandas and pyarrow required for Parquet support. "
                "Install with: pip install pandas pyarrow"
            )

    def validate_dataset_schema(
        self,
        samples: List[Dict[str, Any]],
        required_fields: List[str]
    ) -> Dict[str, Any]:
        """
        Validate that dataset has required fields.

        Args:
            samples: List of dataset samples
            required_fields: List of required field names

        Returns:
            Validation result with:
            - is_valid: bool
            - missing_fields: List[str]
            - present_fields: List[str]
            - sample_count: int
        """
        if not samples:
            return {
                "is_valid": False,
                "missing_fields": required_fields,
                "present_fields": [],
                "sample_count": 0,
                "error": "Dataset is empty"
            }

        # Get all fields from samples
        all_fields = set()
        for sample in samples:
            all_fields.update(sample.keys())

        # Check required fields
        missing = [f for f in required_fields if f not in all_fields]
        present = [f for f in required_fields if f in all_fields]

        return {
            "is_valid": len(missing) == 0,
            "missing_fields": missing,
            "present_fields": present,
            "sample_count": len(samples),
            "all_fields": list(all_fields)
        }

    def apply_config_filters(
        self,
        samples: List[Dict[str, Any]],
        config: DatasetConfig
    ) -> List[Dict[str, Any]]:
        """
        Apply filters from DatasetConfig to samples.

        Args:
            samples: List of dataset samples
            config: DatasetConfig with filter settings

        Returns:
            Filtered list of samples
        """
        filtered = []

        for sample in samples:
            # Get text field
            text = sample.get(config.text_field, "")
            if not text:
                continue

            # Length filter
            text_len = len(text)
            if text_len < config.min_length or text_len > config.max_length:
                continue

            # Language filter
            if config.language_filter:
                lang = sample.get("language", sample.get("lang", ""))
                if lang and lang != config.language_filter:
                    continue

            filtered.append(sample)

        # Sample size limit
        if config.sample_size and len(filtered) > config.sample_size:
            filtered = filtered[:config.sample_size]

        # Deduplication
        if config.deduplication:
            seen = set()
            unique = []
            for sample in filtered:
                text = sample.get(config.text_field, "")
                if text not in seen:
                    seen.add(text)
                    unique.append(sample)
            filtered = unique

        return filtered

    def get_dataset_statistics(
        self,
        samples: List[Dict[str, Any]],
        text_field: str = "text"
    ) -> Dict[str, Any]:
        """
        Get statistics about a dataset.

        Args:
            samples: List of dataset samples
            text_field: Field containing text data

        Returns:
            Statistics dictionary
        """
        if not samples:
            return {
                "sample_count": 0,
                "total_chars": 0,
                "avg_length": 0,
                "min_length": 0,
                "max_length": 0
            }

        lengths = []
        for sample in samples:
            text = sample.get(text_field, "")
            if text:
                lengths.append(len(text))

        if not lengths:
            return {
                "sample_count": len(samples),
                "total_chars": 0,
                "avg_length": 0,
                "min_length": 0,
                "max_length": 0,
                "fields": list(samples[0].keys()) if samples else []
            }

        return {
            "sample_count": len(samples),
            "total_chars": sum(lengths),
            "avg_length": sum(lengths) / len(lengths),
            "min_length": min(lengths),
            "max_length": max(lengths),
            "fields": list(samples[0].keys()) if samples else []
        }

    def clear_cache(self) -> None:
        """Clear the loaded datasets cache."""
        self._loaded_datasets.clear()
        logger.info("Dataset cache cleared")


# Pre-configured dataset examples
DATASET_CONFIGS = {
    "english_wikitext": DatasetConfig(
        dataset_name="wikitext",
        domain="english",
        split="train",
        text_field="text",
        min_length=10,
        max_length=500,
        sample_size=10000,
        deduplication=True,
        quality_threshold=0.8
    ),
    "python_code_search_net": DatasetConfig(
        dataset_name="code_search_net",
        domain="python",
        split="train",
        text_field="code",
        min_length=5,
        max_length=200,
        sample_size=5000,
        deduplication=True,
        quality_threshold=0.9
    ),
    "english_common_voice": DatasetConfig(
        dataset_name="common_voice",
        domain="english",
        split="train",
        text_field="sentence",
        min_length=5,
        max_length=100,
        sample_size=5000,
        language_filter="en",
        deduplication=True
    ),
    "python_github_code": DatasetConfig(
        dataset_name="github-code",
        domain="python",
        split="train",
        text_field="code",
        min_length=10,
        max_length=500,
        sample_size=3000,
        language_filter="Python",
        deduplication=True
    )
}
