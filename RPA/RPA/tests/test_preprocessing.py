"""
Tests for Preprocessing Module.

Tests for:
- DatasetLoader
- DatasetInterpreter
- DatasetCurriculumBuilder
"""

import pytest
import tempfile
import json
from pathlib import Path

from rpa.preprocessing import (
    DatasetLoader,
    DatasetConfig,
    DatasetInterpreter,
    InterpretedSequence,
    DatasetCurriculumBuilder,
    CurriculumBatch,
    DATASET_CONFIGS
)


class TestDatasetLoader:
    """Tests for DatasetLoader."""

    def test_init(self):
        """Test DatasetLoader initialization."""
        loader = DatasetLoader()
        assert loader.cache_dir is None
        assert loader._loaded_datasets == {}

    def test_init_with_cache(self):
        """Test DatasetLoader initialization with cache directory."""
        loader = DatasetLoader(cache_dir="/tmp/cache")
        assert loader.cache_dir == "/tmp/cache"

    def test_load_local_json(self):
        """Test loading a local JSON file."""
        loader = DatasetLoader()

        # Create temp JSON file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"data": [{"text": "hello"}, {"text": "world"}]}, f)
            f.flush()

            samples = loader.load_local_dataset(f.name, format="json")
            assert len(samples) == 2
            assert samples[0]["text"] == "hello"

    def test_load_local_jsonl(self):
        """Test loading a local JSONL file."""
        loader = DatasetLoader()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('{"text": "line1"}\n{"text": "line2"}\n')
            f.flush()

            samples = loader.load_local_dataset(f.name)
            assert len(samples) == 2
            assert samples[0]["text"] == "line1"

    def test_load_local_csv(self):
        """Test loading a local CSV file."""
        loader = DatasetLoader()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("text,label\nhello,positive\nworld,neutral\n")
            f.flush()

            samples = loader.load_local_dataset(f.name)
            assert len(samples) == 2
            assert samples[0]["text"] == "hello"
            assert samples[0]["label"] == "positive"

    def test_load_local_txt(self):
        """Test loading a local text file."""
        loader = DatasetLoader()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("line one\nline two\nline three\n")
            f.flush()

            samples = loader.load_local_dataset(f.name)
            assert len(samples) == 3
            assert samples[0]["text"] == "line one"

    def test_load_nonexistent_file(self):
        """Test loading a non-existent file."""
        loader = DatasetLoader()

        with pytest.raises(FileNotFoundError):
            loader.load_local_dataset("/nonexistent/path/file.json")

    def test_validate_dataset_schema_valid(self):
        """Test schema validation with valid data."""
        loader = DatasetLoader()
        samples = [
            {"text": "hello", "label": "greeting"},
            {"text": "world", "label": "noun"}
        ]

        result = loader.validate_dataset_schema(samples, ["text", "label"])
        assert result["is_valid"] is True
        assert len(result["missing_fields"]) == 0

    def test_validate_dataset_schema_missing(self):
        """Test schema validation with missing fields."""
        loader = DatasetLoader()
        samples = [{"text": "hello"}]

        result = loader.validate_dataset_schema(samples, ["text", "label"])
        assert result["is_valid"] is False
        assert "label" in result["missing_fields"]

    def test_validate_empty_dataset(self):
        """Test validation of empty dataset."""
        loader = DatasetLoader()

        result = loader.validate_dataset_schema([], ["text"])
        assert result["is_valid"] is False
        assert result["sample_count"] == 0

    def test_apply_config_filters(self):
        """Test applying config filters."""
        loader = DatasetLoader()
        samples = [
            {"text": "short"},
            {"text": "this is a longer text"},
            {"text": "short"},
            {"text": "another longer text here"}
        ]

        config = DatasetConfig(
            dataset_name="test",
            domain="english",
            min_length=10,
            deduplication=True
        )

        filtered = loader.apply_config_filters(samples, config)
        assert len(filtered) == 2  # Two unique longer texts

    def test_get_dataset_statistics(self):
        """Test getting dataset statistics."""
        loader = DatasetLoader()
        samples = [
            {"text": "hello"},
            {"text": "world"},
            {"text": "testing"}
        ]

        stats = loader.get_dataset_statistics(samples)
        assert stats["sample_count"] == 3
        assert stats["min_length"] == 5
        assert stats["max_length"] == 7

    def test_clear_cache(self):
        """Test clearing the cache."""
        loader = DatasetLoader()
        loader._loaded_datasets["test"] = [{"data": "value"}]

        loader.clear_cache()
        assert loader._loaded_datasets == {}


class TestDatasetConfig:
    """Tests for DatasetConfig."""

    def test_create_config(self):
        """Test creating a DatasetConfig."""
        config = DatasetConfig(
            dataset_name="test_dataset",
            domain="english",
            text_field="content"
        )

        assert config.dataset_name == "test_dataset"
        assert config.domain == "english"
        assert config.text_field == "content"
        assert config.split == "train"
        assert config.deduplication is True

    def test_to_dict(self):
        """Test converting config to dictionary."""
        config = DatasetConfig(
            dataset_name="test",
            domain="python",
            min_length=5,
            max_length=100
        )

        d = config.to_dict()
        assert d["dataset_name"] == "test"
        assert d["domain"] == "python"
        assert d["min_length"] == 5

    def test_from_dict(self):
        """Test creating config from dictionary."""
        d = {
            "dataset_name": "test",
            "domain": "english",
            "split": "validation",
            "text_field": "text"
        }

        config = DatasetConfig.from_dict(d)
        assert config.dataset_name == "test"
        assert config.split == "validation"

    def test_predefined_configs(self):
        """Test predefined dataset configs."""
        assert "english_wikitext" in DATASET_CONFIGS
        assert "python_code_search_net" in DATASET_CONFIGS

        wikitext = DATASET_CONFIGS["english_wikitext"]
        assert wikitext.domain == "english"


class TestDatasetInterpreter:
    """Tests for DatasetInterpreter."""

    def test_init(self):
        """Test DatasetInterpreter initialization."""
        interpreter = DatasetInterpreter()
        assert interpreter._word_pattern is not None
        assert len(interpreter._primitives) == 0

    def test_interpret_text_dataset(self):
        """Test interpreting text samples."""
        interpreter = DatasetInterpreter()
        samples = [
            {"text": "Hello world"},
            {"text": "The cat sat"}
        ]

        config = DatasetConfig(
            dataset_name="test",
            domain="english",
            min_length=1
        )

        sequences = interpreter.interpret_text_dataset(samples, config)

        # Should have primitives + words + sentences
        assert len(sequences) > 0

        # Check for word patterns
        words = [s for s in sequences if s.hierarchy_level == 1]
        assert len(words) > 0

    def test_interpret_code_dataset(self):
        """Test interpreting code samples."""
        interpreter = DatasetInterpreter()
        samples = [
            {"code": "x = 5"},
            {"code": "print(x)"}
        ]

        config = DatasetConfig(
            dataset_name="test",
            domain="python",
            text_field="code",
            min_length=1
        )

        sequences = interpreter.interpret_code_dataset(samples, config, language="python")

        # Should have tokens and statements
        assert len(sequences) > 0

        # Check for primitives (tokens)
        primitives = [s for s in sequences if s.hierarchy_level == 0]
        assert len(primitives) > 0

    def test_interpret_structured_dataset(self):
        """Test interpreting structured data."""
        interpreter = DatasetInterpreter()
        samples = [
            {"name": "Alice", "age": "30"},
            {"name": "Bob", "age": "25"}
        ]

        config = DatasetConfig(
            dataset_name="test",
            domain="people",
            min_length=1
        )

        sequences = interpreter.interpret_structured_dataset(samples, config)
        assert len(sequences) > 0

    def test_filter_by_quality(self):
        """Test filtering sequences by quality."""
        interpreter = DatasetInterpreter()

        sequences = [
            InterpretedSequence(
                content="good",
                sequence_type="pattern",
                hierarchy_level=1,
                composition=["g", "o", "o", "d"],
                domain="english",
                quality_score=0.9
            ),
            InterpretedSequence(
                content="bad",
                sequence_type="pattern",
                hierarchy_level=1,
                composition=["b", "a", "d"],
                domain="english",
                quality_score=0.3
            )
        ]

        filtered = interpreter.filter_by_quality(sequences, min_quality=0.5)
        assert len(filtered) == 1
        assert filtered[0].content == "good"

    def test_rank_by_frequency(self):
        """Test ranking sequences by frequency."""
        interpreter = DatasetInterpreter()

        sequences = [
            InterpretedSequence(
                content="common",
                sequence_type="pattern",
                hierarchy_level=1,
                composition=["c", "o", "m", "m", "o", "n"],
                domain="english",
                frequency=10
            ),
            InterpretedSequence(
                content="rare",
                sequence_type="pattern",
                hierarchy_level=1,
                composition=["r", "a", "r", "e"],
                domain="english",
                frequency=1
            )
        ]

        ranked = interpreter.rank_by_frequency(sequences)
        assert ranked[0].content == "common"
        assert ranked[1].content == "rare"

    def test_deduplicate(self):
        """Test deduplicating sequences."""
        interpreter = DatasetInterpreter()

        sequences = [
            InterpretedSequence(
                content="hello",
                sequence_type="pattern",
                hierarchy_level=1,
                composition=["h", "e", "l", "l", "o"],
                domain="english",
                quality_score=0.8
            ),
            InterpretedSequence(
                content="HELLO",
                sequence_type="pattern",
                hierarchy_level=1,
                composition=["H", "E", "L", "L", "O"],
                domain="english",
                quality_score=0.9
            )
        ]

        unique = interpreter.deduplicate(sequences)
        assert len(unique) == 1
        assert unique[0].quality_score == 0.9  # Kept higher quality

    def test_get_interpretation_statistics(self):
        """Test getting interpretation statistics."""
        interpreter = DatasetInterpreter()

        sequences = [
            InterpretedSequence(
                content="a",
                sequence_type="primitive",
                hierarchy_level=0,
                composition=["a"],
                domain="english"
            ),
            InterpretedSequence(
                content="hello",
                sequence_type="pattern",
                hierarchy_level=1,
                composition=["h", "e", "l", "l", "o"],
                domain="english"
            )
        ]

        stats = interpreter.get_interpretation_statistics(sequences)
        assert stats["total_sequences"] == 2
        assert stats["by_hierarchy"][0] == 1
        assert stats["by_hierarchy"][1] == 1


class TestDatasetCurriculumBuilder:
    """Tests for DatasetCurriculumBuilder."""

    def test_init(self):
        """Test CurriculumBuilder initialization."""
        builder = DatasetCurriculumBuilder()
        assert builder.loader is not None
        assert builder.interpreter is not None

    def test_build_curriculum_from_dataset(self):
        """Test building curriculum from dataset."""
        builder = DatasetCurriculumBuilder()

        samples = [
            {"text": "Hello world"},
            {"text": "The cat sat on the mat"}
        ]

        config = DatasetConfig(
            dataset_name="test",
            domain="english",
            min_length=1,
            sample_size=100
        )

        batches = builder.build_curriculum_from_dataset(
            samples, config, num_batches=2, batch_size=10
        )

        assert len(batches) > 0
        assert all(isinstance(b, CurriculumBatch) for b in batches)

    def test_create_batch(self):
        """Test creating a single batch."""
        builder = DatasetCurriculumBuilder()

        sequences = [
            InterpretedSequence(
                content="hello",
                sequence_type="pattern",
                hierarchy_level=1,
                composition=["h", "e", "l", "l", "o"],
                domain="english"
            )
        ]

        batch = builder.create_batch(sequences, "test_batch", 1, 1)

        assert batch.batch_id == "test_batch"
        assert batch.hierarchy_level == 1
        assert len(batch.lessons) == 1

    def test_validate_curriculum_progression_valid(self):
        """Test validating a valid curriculum progression."""
        builder = DatasetCurriculumBuilder()

        batches = [
            CurriculumBatch(
                batch_id="level_0",
                domain="english",
                hierarchy_level=0,
                difficulty=1,
                lessons=[{"lesson_id": "1", "content": "a"}]
            ),
            CurriculumBatch(
                batch_id="level_1",
                domain="english",
                hierarchy_level=1,
                difficulty=2,
                lessons=[{"lesson_id": "2", "content": "hello"}]
            )
        ]

        result = builder.validate_curriculum_progression(batches)
        assert result["is_valid"] is True
        assert len(result["issues"]) == 0

    def test_validate_curriculum_progression_empty_batch(self):
        """Test validating curriculum with empty batch."""
        builder = DatasetCurriculumBuilder()

        batches = [
            CurriculumBatch(
                batch_id="empty",
                domain="english",
                hierarchy_level=0,
                difficulty=1,
                lessons=[]
            )
        ]

        result = builder.validate_curriculum_progression(batches)
        assert result["is_valid"] is False
        assert any("no lessons" in i.lower() for i in result["issues"])

    def test_export_curriculum(self):
        """Test exporting curriculum to files."""
        builder = DatasetCurriculumBuilder()

        batches = [
            CurriculumBatch(
                batch_id="test_batch",
                domain="english",
                hierarchy_level=1,
                difficulty=1,
                lessons=[{"lesson_id": "1", "content": "hello"}]
            )
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            exported = builder.export_curriculum(batches, tmpdir, "english")

            assert len(exported) == 1
            assert Path(exported[0]).exists()

            # Verify file content
            with open(exported[0]) as f:
                data = json.load(f)
                assert data["batch_id"] == "test_batch"

    def test_build_quick_curriculum(self):
        """Test quick curriculum building."""
        builder = DatasetCurriculumBuilder()

        texts = ["Hello world", "The cat sat"]
        batches = builder.build_quick_curriculum(texts, "english", batch_size=5)

        assert len(batches) > 0

    def test_merge_batches(self):
        """Test merging multiple batches."""
        builder = DatasetCurriculumBuilder()

        batches = [
            CurriculumBatch(
                batch_id="batch_1",
                domain="english",
                hierarchy_level=1,
                difficulty=1,
                lessons=[{"lesson_id": "1", "content": "hello"}]
            ),
            CurriculumBatch(
                batch_id="batch_2",
                domain="english",
                hierarchy_level=1,
                difficulty=1,
                lessons=[{"lesson_id": "2", "content": "world"}]
            )
        ]

        merged = builder.merge_batches(batches)

        assert len(merged.lessons) == 2
        assert "merged" in merged.batch_id


class TestCurriculumBatch:
    """Tests for CurriculumBatch."""

    def test_create_batch(self):
        """Test creating a CurriculumBatch."""
        batch = CurriculumBatch(
            batch_id="test",
            domain="english",
            hierarchy_level=1,
            difficulty=2,
            lessons=[{"lesson_id": "1", "content": "hello"}]
        )

        assert batch.batch_id == "test"
        assert batch.domain == "english"
        assert len(batch.lessons) == 1

    def test_to_dict(self):
        """Test converting batch to dictionary."""
        batch = CurriculumBatch(
            batch_id="test",
            domain="english",
            hierarchy_level=1,
            difficulty=2,
            lessons=[]
        )

        d = batch.to_dict()
        assert d["batch_id"] == "test"
        assert d["domain"] == "english"

    def test_save(self):
        """Test saving batch to file."""
        batch = CurriculumBatch(
            batch_id="test",
            domain="english",
            hierarchy_level=1,
            difficulty=2,
            lessons=[{"lesson_id": "1", "content": "hello"}]
        )

        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            batch.save(f.name)

            with open(f.name) as saved:
                data = json.load(saved)
                assert data["batch_id"] == "test"


class TestInterpretedSequence:
    """Tests for InterpretedSequence."""

    def test_create_sequence(self):
        """Test creating an InterpretedSequence."""
        seq = InterpretedSequence(
            content="hello",
            sequence_type="pattern",
            hierarchy_level=1,
            composition=["h", "e", "l", "l", "o"],
            domain="english"
        )

        assert seq.content == "hello"
        assert seq.hierarchy_level == 1
        assert seq.frequency == 1

    def test_to_dict(self):
        """Test converting sequence to dictionary."""
        seq = InterpretedSequence(
            content="hello",
            sequence_type="pattern",
            hierarchy_level=1,
            composition=["h", "e", "l", "l", "o"],
            domain="english"
        )

        d = seq.to_dict()
        assert d["content"] == "hello"
        assert d["type"] == "pattern"
