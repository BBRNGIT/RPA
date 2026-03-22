#!/usr/bin/env python3
"""
RPA Unified Learning Pipeline - Complete automated learning from HF datasets.

Pipeline Stages:
1. EXTRACT: Load data from Hugging Face datasets
2. PREPROCESS: Clean, interpret, and filter data
3. CURRICULUM: Build progressive learning curriculum
4. LEARN: Train domain-specific learning systems
5. EVOLVE: Store patterns with evolution tracking

Usage:
    python learn_pipeline.py --domain english --samples 100
    python learn_pipeline.py --domain python --samples 50
    python learn_pipeline.py --domain all --phase foundations
    python learn_pipeline.py --auto  # Auto-detect and run based on schedule
"""

import argparse
import json
import sys
import os
import time
import traceback
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import random
import hashlib
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("RPA-Learn")

# Add RPA to path
sys.path.insert(0, str(Path(__file__).parent))

# RPA Components
from rpa.memory.ltm import LongTermMemory
from rpa.memory.episodic import EpisodicMemory, EventType
from rpa.memory.stm import ShortTermMemory
from rpa.core.graph import PatternGraph, Node
from rpa.preprocessing.dataset_loader import DatasetLoader, DatasetConfig
from rpa.preprocessing.dataset_interpreter import DatasetInterpreter
from rpa.preprocessing.dataset_curriculum_builder import DatasetCurriculumBuilder

# Domain-specific learning
from rpa.domains.english import (
    EnglishDomain,
    VocabularyTrainer,
    GrammarEngine,
    ReadingComprehension,
    WritingAssessor,
    VocabularyItem,
    ProficiencyLevel,
)


# ============================================================================
# PIPELINE CONFIGURATION
# ============================================================================

CONFIG_PATH = Path(__file__).parent / "config" / "datasets.json"

ENGLISH_DATASETS = ["wikitext", "squad", "wordnet", "simple_wikipedia"]
PYTHON_DATASETS = ["mbpp", "humaneval", "code_alpaca", "python_docs"]

DEFAULT_CONFIG = {
    "batch_size": 50,
    "quality_threshold": 0.5,
    "max_vocabulary_per_session": 100,
    "max_grammar_per_session": 30,
    "max_reading_per_session": 10,
    "max_writing_per_session": 5,
    "persistence_path": "memory/learning_state",
}


# ============================================================================
# PIPELINE STAGES
# ============================================================================

class PipelineStage:
    """Base class for pipeline stages."""

    def __init__(self, name: str):
        self.name = name
        self.start_time = None
        self.end_time = None
        self.stats = {}

    def __enter__(self):
        self.start_time = datetime.now()
        logger.info(f"\n{'='*60}")
        logger.info(f"  STAGE: {self.name}")
        logger.info(f"{'='*60}")
        return self

    def __exit__(self, *args):
        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds()
        logger.info(f"  Stage completed in {duration:.2f}s")
        logger.info(f"  Stats: {self.stats}")


class ExtractionStage(PipelineStage):
    """Stage 1: Extract data from Hugging Face datasets or local curriculum."""

    def __init__(self, loader: DatasetLoader):
        super().__init__("EXTRACTION")
        self.loader = loader

    def run(self, dataset_name: str, sample_size: int, config: Dict) -> Tuple[List[Dict], Dict]:
        """Load dataset from Hugging Face or local curriculum files."""
        dataset_config = config["datasets"].get(dataset_name, {
            "domain": "english" if dataset_name in ENGLISH_DATASETS else "python",
            "dataset_name": dataset_name,
        })

        # Try HF datasets first
        try:
            kwargs = {
                "dataset_name": dataset_config.get("dataset_name"),
                "split": dataset_config.get("split", "train"),
            }

            if dataset_config.get("config_name"):
                kwargs["name"] = dataset_config["config_name"]

            samples = self.loader.load_huggingface_dataset(**kwargs)

            # Apply sample rate
            sample_rate = dataset_config.get("sample_rate", 1.0)
            if sample_rate < 1.0:
                samples = random.sample(samples, int(len(samples) * sample_rate))

            samples = samples[:sample_size]

            self.stats = {
                "dataset": dataset_name,
                "samples_loaded": len(samples),
                "domain": dataset_config.get("domain", "unknown"),
                "source": "huggingface",
            }

            return samples, dataset_config

        except Exception as e:
            logger.warning(f"HF dataset unavailable, using local curriculum: {e}")
            
            # Fallback to local curriculum files
            samples = self._load_local_curriculum(dataset_name, sample_size)
            
            if samples:
                self.stats = {
                    "dataset": dataset_name,
                    "samples_loaded": len(samples),
                    "domain": dataset_config.get("domain", "english"),
                    "source": "local_curriculum",
                }
                return samples, dataset_config
            
            return [], dataset_config

    def _load_local_curriculum(self, domain: str, sample_size: int) -> List[Dict]:
        """Load from local curriculum files as fallback."""
        curriculum_dir = Path(__file__).parent / "curriculum"
        samples = []

        # Load English curriculum
        english_dir = curriculum_dir / "english"
        if english_dir.exists():
            for json_file in english_dir.glob("*.json"):
                try:
                    with open(json_file) as f:
                        data = json.load(f)
                        lessons = data.get("lessons", [])
                        for lesson in lessons:
                            samples.append({
                                "text": lesson.get("content", ""),
                                "content": lesson.get("content", ""),
                                "hierarchy_level": lesson.get("hierarchy_level", 1),
                                "domain": "english",
                                "metadata": lesson,
                            })
                except Exception as e:
                    logger.warning(f"Failed to load {json_file}: {e}")

        # Load Coding curriculum
        coding_dir = curriculum_dir / "coding"
        if coding_dir.exists():
            for json_file in coding_dir.glob("*.json"):
                try:
                    with open(json_file) as f:
                        data = json.load(f)
                        lessons = data.get("lessons", [])
                        for lesson in lessons:
                            samples.append({
                                "code": lesson.get("content", ""),
                                "content": lesson.get("content", ""),
                                "hierarchy_level": lesson.get("hierarchy_level", 2),
                                "domain": "python",
                                "metadata": lesson,
                            })
                except Exception as e:
                    logger.warning(f"Failed to load {json_file}: {e}")

        # Filter by domain if specified
        if domain in ENGLISH_DATASETS or domain == "english":
            samples = [s for s in samples if s.get("domain") == "english"]
        elif domain in PYTHON_DATASETS or domain == "python":
            samples = [s for s in samples if s.get("domain") == "python"]

        # Limit samples
        return samples[:sample_size]


class PreprocessStage(PipelineStage):
    """Stage 2: Preprocess and clean data."""

    def __init__(self, interpreter: DatasetInterpreter):
        super().__init__("PREPROCESSING")
        self.interpreter = interpreter

    def run(
        self,
        samples: List[Dict],
        config: Dict,
        pipeline_config: Dict,
    ) -> List[Dict]:
        """Interpret and clean samples."""
        if not samples:
            return []

        domain = config.get("domain", "english")

        # Check if data is already preprocessed (from local curriculum)
        if samples and "hierarchy_level" in samples[0]:
            # Already formatted, just ensure required fields
            processed = []
            for sample in samples:
                processed.append({
                    "content": sample.get("content", ""),
                    "hierarchy_level": sample.get("hierarchy_level", 1),
                    "domain": sample.get("domain", domain),
                    "composition": sample.get("composition", []),
                    "frequency": sample.get("frequency", 1),
                    "quality": sample.get("quality", 0.8),
                    "source": sample.get("source", "local_curriculum"),
                    "metadata": sample.get("metadata", {}),
                })
            
            self.stats = {
                "input_samples": len(samples),
                "output_sequences": len(processed),
                "filtered": 0,
                "domain": domain,
                "source": "preprocessed",
            }
            return processed

        # Create DatasetConfig for raw HF data
        ds_config = DatasetConfig(
            dataset_name=config.get("dataset_name", "unknown"),
            domain=domain,
            text_field=config.get("fields", {}).get("text", "text"),
            min_length=config.get("filter", {}).get("min_text_length", 10),
            max_length=config.get("filter", {}).get("max_text_length", 5000),
            quality_threshold=pipeline_config.get("quality_threshold", 0.5),
        )

        # Interpret based on domain
        if domain in ("python", "javascript", "java", "cpp"):
            sequences = self.interpreter.interpret_code_dataset(samples, ds_config)
        else:
            sequences = self.interpreter.interpret_text_dataset(samples, ds_config)

        # Filter by quality
        sequences = self.interpreter.filter_by_quality(
            sequences,
            min_quality=ds_config.quality_threshold,
            min_length=ds_config.min_length,
            max_length=ds_config.max_length,
        )

        # Deduplicate
        sequences = self.interpreter.deduplicate(sequences)

        # Rank by frequency
        sequences = self.interpreter.rank_by_frequency(sequences)

        # Convert to dict format
        processed = []
        for seq in sequences:
            processed.append({
                "content": seq.content,
                "hierarchy_level": seq.hierarchy_level,
                "domain": seq.domain,
                "composition": seq.composition,
                "frequency": seq.frequency,
                "quality": seq.quality_score,
                "source": seq.source,
                "metadata": seq.metadata,
            })

        self.stats = {
            "input_samples": len(samples),
            "output_sequences": len(processed),
            "filtered": len(samples) - len(processed),
            "domain": domain,
        }

        return processed


class CurriculumStage(PipelineStage):
    """Stage 3: Build learning curriculum."""

    def __init__(self, builder: DatasetCurriculumBuilder):
        super().__init__("CURRICULUM")
        self.builder = builder

    def run(self, processed_data: List[Dict], domain: str) -> Dict[str, List[Dict]]:
        """Organize data into curriculum structure."""
        curriculum = {
            "vocabulary": [],
            "grammar": [],
            "reading": [],
            "patterns": [],
        }

        if domain == "english":
            curriculum = self._build_english_curriculum(processed_data)
        elif domain == "python":
            curriculum = self._build_python_curriculum(processed_data)
        else:
            curriculum["patterns"] = processed_data

        self.stats = {
            "vocabulary_items": len(curriculum["vocabulary"]),
            "grammar_rules": len(curriculum["grammar"]),
            "reading_passages": len(curriculum["reading"]),
            "patterns": len(curriculum["patterns"]),
        }

        return curriculum

    def _build_english_curriculum(self, data: List[Dict]) -> Dict[str, List[Dict]]:
        """Build English-specific curriculum."""
        curriculum = {
            "vocabulary": [],
            "grammar": [],
            "reading": [],
            "patterns": [],
        }

        for item in data:
            content = item.get("content", "")
            level = item.get("hierarchy_level", 1)
            metadata = item.get("metadata", {})

            if not content:
                continue

            # Level 1: Words -> Vocabulary
            if level == 1 and len(content.split()) <= 3:
                word = content.strip().lower()
                if len(word) >= 2 and word.isalpha():
                    curriculum["vocabulary"].append({
                        "word": word,
                        "content": content,
                        "context": metadata.get("usage_contexts", []),
                        "definition": f"Common English word: {word}",
                        "metadata": metadata,
                        "source": item.get("source", "local_curriculum"),
                    })

            # Level 2: Sentences -> Reading/Grammar
            elif level == 2:
                # For grammar analysis
                curriculum["grammar"].append({
                    "sentence": content,
                    "content": content,
                    "source": item.get("source", "local_curriculum"),
                })

                # Longer sentences for reading
                if len(content.split()) >= 10:
                    curriculum["reading"].append({
                        "text": content,
                        "content": content,
                        "source": item.get("source", "local_curriculum"),
                    })

            # Level 3+: Passages -> Reading
            elif level >= 3 and len(content) > 50:
                curriculum["reading"].append({
                    "text": content,
                    "content": content,
                    "source": item.get("source", "local_curriculum"),
                })

            # All levels -> General patterns
            curriculum["patterns"].append({
                "content": content,
                "hierarchy_level": level,
                "source": item.get("source", "local_curriculum"),
            })

        # Deduplicate vocabulary by word
        seen_words = set()
        unique_vocab = []
        for item in curriculum["vocabulary"]:
            if item["word"] not in seen_words:
                seen_words.add(item["word"])
                unique_vocab.append(item)
        curriculum["vocabulary"] = unique_vocab

        logger.info(f"Built English curriculum: {len(curriculum['vocabulary'])} vocab, "
                   f"{len(curriculum['grammar'])} grammar, {len(curriculum['reading'])} reading")

        return curriculum

    def _build_python_curriculum(self, data: List[Dict]) -> Dict[str, List[Dict]]:
        """Build Python-specific curriculum."""
        curriculum = {
            "vocabulary": [],  # Reserved for keywords
            "grammar": [],     # Syntax patterns
            "reading": [],     # Code with comments
            "patterns": [],    # All code patterns
        }

        for item in data:
            content = item.get("content", "")
            level = item.get("hierarchy_level", 1)

            # Extract Python keywords/tokens
            if level <= 1:
                keywords = ["def", "class", "if", "else", "for", "while", "return", "import", "from"]
                for kw in keywords:
                    if kw in content:
                        curriculum["vocabulary"].append({
                            "word": kw,
                            "context": content,
                            "type": "keyword",
                        })

            # Syntax patterns
            curriculum["grammar"].append({
                "code": content,
                "level": level,
            })

            # All as patterns
            curriculum["patterns"].append(item)

        return curriculum


class LearnStage(PipelineStage):
    """Stage 4: Train domain learning systems."""

    def __init__(
        self,
        english_domain: Optional[EnglishDomain] = None,
        ltm: Optional[LongTermMemory] = None,
    ):
        super().__init__("LEARNING")
        self.english_domain = english_domain or EnglishDomain()
        self.ltm = ltm

    def run(
        self,
        curriculum: Dict[str, List[Dict]],
        domain: str,
        pipeline_config: Dict,
    ) -> Dict[str, Any]:
        """Execute learning from curriculum."""
        results = {
            "vocabulary": {},
            "grammar": {},
            "reading": {},
            "patterns": {},
        }

        if domain == "english":
            results = self._learn_english(curriculum, pipeline_config)
        elif domain == "python":
            results = self._learn_python(curriculum, pipeline_config)

        self.stats = {
            "vocabulary_learned": results["vocabulary"].get("learned", 0),
            "grammar_practiced": results["grammar"].get("practiced", 0),
            "reading_completed": results["reading"].get("completed", 0),
            "patterns_stored": results["patterns"].get("stored", 0),
        }

        return results

    def _learn_english(self, curriculum: Dict, config: Dict) -> Dict:
        """Learn English domain content."""
        results = {"vocabulary": {}, "grammar": {}, "reading": {}, "patterns": {}}

        # Learn vocabulary from curriculum vocabulary items
        vocab_items = curriculum.get("vocabulary", [])[:config.get("max_vocabulary_per_session", 100)]
        learned_vocab = 0

        for item in vocab_items:
            word = item.get("word", item.get("content", ""))
            if not word or len(word) < 2:
                continue
                
            existing = self.english_domain.vocabulary.get_word_by_text(word)

            if not existing:
                # Add new word
                try:
                    new_item = self.english_domain.vocabulary.add_vocabulary(
                        word=word,
                        definition=item.get("definition", f"Word from context: {item.get('context', '')[:50]}"),
                        part_of_speech=item.get("metadata", {}).get("usage_contexts", ["unknown"])[0] if item.get("metadata", {}).get("usage_contexts") else "unknown",
                        examples=[item.get("context", "")] if item.get("context") else [],
                    )
                    learned_vocab += 1
                except Exception as e:
                    logger.debug(f"Failed to add word '{word}': {e}")
            else:
                # Reinforce existing word with simulated review
                try:
                    self.english_domain.vocabulary.review(
                        existing.word_id,
                        quality=random.randint(3, 5),
                    )
                except Exception as e:
                    logger.debug(f"Failed to review word '{word}': {e}")

        results["vocabulary"]["learned"] = learned_vocab
        results["vocabulary"]["total"] = len(self.english_domain.vocabulary._vocabulary)

        # Practice grammar
        grammar_items = curriculum.get("grammar", [])[:config.get("max_grammar_per_session", 30)]
        for item in grammar_items:
            sentence = item.get("sentence", item.get("content", ""))
            if sentence:
                # Check for grammar patterns
                errors = self.english_domain.grammar.check_text(sentence)

        results["grammar"]["practiced"] = len(grammar_items)
        results["grammar"]["rules"] = len(self.english_domain.grammar._rules)

        # Reading comprehension
        reading_items = curriculum.get("reading", [])[:config.get("max_reading_per_session", 10)]
        for item in reading_items:
            text = item.get("text", item.get("content", ""))
            if text and len(text) > 50:
                try:
                    passage = self.english_domain.reading.add_passage(
                        title=f"Extracted passage",
                        text=text[:1000],  # Limit length
                        difficulty=min(5, max(1, len(text.split()) // 50)),
                        topic="extracted",
                        questions=[],  # Would need question generation
                    )
                except Exception as e:
                    logger.debug(f"Failed to add passage: {e}")

        results["reading"]["completed"] = len(reading_items)
        results["reading"]["passages"] = len(self.english_domain.reading._passages)

        # Store patterns in LTM
        patterns = curriculum.get("patterns", [])
        stored = 0
        for item in patterns[:50]:  # Limit
            if self.ltm and item.get("content"):
                try:
                    node = Node.create_pattern(
                        label=item.get("content", "")[:30],
                        content=item.get("content", ""),
                        hierarchy_level=item.get("hierarchy_level", 1),
                        domain="english",
                    )
                    self.ltm.consolidate(
                        node=node,
                        session_id="pipeline_english",
                        validation_score=0.8,
                        source=item.get("source", "local_curriculum"),
                    )
                    stored += 1
                except Exception as e:
                    logger.debug(f"Failed to store pattern: {e}")

        results["patterns"]["stored"] = stored

        return results

    def _learn_python(self, curriculum: Dict, config: Dict) -> Dict:
        """Learn Python domain content."""
        results = {"vocabulary": {}, "grammar": {}, "reading": {}, "patterns": {}}

        # Store patterns in LTM
        patterns = curriculum["patterns"]
        stored = 0

        for item in patterns[:100]:  # Limit
            if self.ltm:
                node = Node.create_pattern(
                    label=item.get("content", "")[:30],
                    content=item.get("content", ""),
                    hierarchy_level=item.get("hierarchy_level", 1),
                    domain="python",
                )
                self.ltm.consolidate(
                    node=node,
                    session_id="pipeline_python",
                    validation_score=item.get("quality", 0.8),
                    source=item.get("source", "huggingface"),
                )
                stored += 1

        results["patterns"]["stored"] = stored
        return results


class EvolveStage(PipelineStage):
    """Stage 5: Store patterns with evolution tracking."""

    def __init__(self, ltm: LongTermMemory, episodic: EpisodicMemory):
        super().__init__("EVOLUTION")
        self.ltm = ltm
        self.episodic = episodic

    def run(self, learning_results: Dict, domain: str) -> Dict:
        """Store learning outcomes with evolution tracking."""
        # Log learning event
        self.episodic.log_event(
            event_type=EventType.PATTERN_LEARNED,
            session_id=f"pipeline_{domain}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            data={
                "domain": domain,
                "results": learning_results,
                "timestamp": datetime.now().isoformat(),
            },
        )

        # Save memory state
        stats = {
            "ltm_size": len(self.ltm) if self.ltm else 0,
            "episodic_events": len(self.episodic) if self.episodic else 0,
        }

        self.stats = stats
        return stats


# ============================================================================
# MAIN PIPELINE
# ============================================================================

class UnifiedLearningPipeline:
    """
    Complete learning pipeline from data extraction to evolution.
    """

    def __init__(self, config_path: str = None, persistence_path: str = None):
        """Initialize the pipeline."""
        self.config = self._load_config(config_path)
        self.pipeline_config = {**DEFAULT_CONFIG, **self.config.get("processing", {})}

        # Initialize components
        self.loader = DatasetLoader()
        self.interpreter = DatasetInterpreter()
        self.builder = DatasetCurriculumBuilder(self.loader, self.interpreter)

        # Initialize memory
        self.persistence_path = persistence_path or self.pipeline_config.get("persistence_path")
        self.ltm = LongTermMemory(storage_path=self.persistence_path)
        self.episodic = EpisodicMemory()
        self.stm = ShortTermMemory()

        # Initialize domain learning
        self.english_domain = EnglishDomain(self.ltm, self.episodic)

        # Pipeline stages
        self.extract = ExtractionStage(self.loader)
        self.preprocess = PreprocessStage(self.interpreter)
        self.curriculum = CurriculumStage(self.builder)
        self.learn = LearnStage(self.english_domain, self.ltm)
        self.evolve = EvolveStage(self.ltm, self.episodic)

    def _load_config(self, config_path: str) -> Dict:
        """Load dataset configuration."""
        if config_path:
            path = Path(config_path)
        else:
            path = CONFIG_PATH

        if path.exists():
            with open(path) as f:
                return json.load(f)
        return {"datasets": {}, "processing": {}}

    def run(
        self,
        domain: str = "english",
        dataset: str = None,
        samples: int = 100,
        verbose: bool = True,
    ) -> Dict[str, Any]:
        """
        Run the complete learning pipeline.

        Args:
            domain: Learning domain (english, python, all)
            dataset: Specific dataset to use (auto-selected if None)
            samples: Number of samples to process
            verbose: Show detailed output

        Returns:
            Pipeline execution results
        """
        start_time = datetime.now()
        logger.info(f"\n{'#'*60}")
        logger.info(f"# RPA UNIFIED LEARNING PIPELINE")
        logger.info(f"# Domain: {domain}")
        logger.info(f"# Samples: {samples}")
        logger.info(f"# Started: {start_time.isoformat()}")
        logger.info(f"{'#'*60}")

        results = {
            "domain": domain,
            "started_at": start_time.isoformat(),
            "stages": {},
            "success": False,
        }

        try:
            # Select dataset
            if not dataset:
                if domain == "english":
                    dataset = random.choice(ENGLISH_DATASETS)
                elif domain == "python":
                    dataset = random.choice(PYTHON_DATASETS)
                else:
                    dataset = random.choice(ENGLISH_DATASETS + PYTHON_DATASETS)

            logger.info(f"\nSelected dataset: {dataset}")

            # Stage 1: Extract
            with self.extract as stage:
                samples_data, ds_config = stage.run(
                    dataset, samples, self.config
                )

            if not samples_data:
                logger.error("No data extracted, pipeline terminated")
                return results

            results["stages"]["extraction"] = stage.stats

            # Stage 2: Preprocess
            with self.preprocess as stage:
                processed = stage.run(
                    samples_data, ds_config, self.pipeline_config
                )

            results["stages"]["preprocessing"] = stage.stats

            # Stage 3: Curriculum
            with self.curriculum as stage:
                curriculum = stage.run(processed, ds_config.get("domain", domain))

            results["stages"]["curriculum"] = stage.stats

            # Stage 4: Learn
            with self.learn as stage:
                learning_results = stage.run(
                    curriculum, ds_config.get("domain", domain), self.pipeline_config
                )

            results["stages"]["learning"] = stage.stats
            results["learning_results"] = learning_results

            # Stage 5: Evolve
            with self.evolve as stage:
                evolution_stats = stage.run(learning_results, domain)

            results["stages"]["evolution"] = stage.stats

            # Save state
            self._save_state()

            results["success"] = True

        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            traceback.print_exc()
            results["error"] = str(e)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        results["completed_at"] = end_time.isoformat()
        results["duration_seconds"] = duration

        logger.info(f"\n{'#'*60}")
        logger.info(f"# PIPELINE COMPLETE")
        logger.info(f"# Duration: {duration:.2f}s")
        logger.info(f"# Success: {results['success']}")
        logger.info(f"{'#'*60}")

        return results

    def run_multi_domain(self, samples_per_domain: int = 50) -> Dict:
        """Run pipeline for all domains."""
        results = {}

        for domain in ["english", "python"]:
            logger.info(f"\n{'='*60}")
            logger.info(f"Running domain: {domain}")
            logger.info(f"{'='*60}")

            results[domain] = self.run(
                domain=domain,
                samples=samples_per_domain,
            )

        return results

    def _save_state(self):
        """Save learning state to disk."""
        if self.persistence_path:
            path = Path(self.persistence_path)
            path.mkdir(parents=True, exist_ok=True)

            # Save LTM
            self.ltm.save()

            # Save English domain progress
            progress = self.english_domain.export_progress()
            progress_path = path / "english_progress.json"
            with open(progress_path, "w") as f:
                json.dump(progress, f, indent=2)

            logger.info(f"State saved to {self.persistence_path}")


# ============================================================================
# AUTO-RUN MODE
# ============================================================================

def auto_run():
    """
    Auto-detect and run appropriate learning based on schedule.
    Used by GitHub Actions cron jobs.
    """
    logger.info("Running in AUTO mode")

    # Determine what to run based on day/time
    now = datetime.now()
    hour = now.hour
    day_of_week = now.weekday()

    pipeline = UnifiedLearningPipeline()

    # Different schedules for different learning
    if day_of_week < 5:  # Weekdays
        if hour < 6:  # Early morning - English vocabulary
            logger.info("Scheduled: English vocabulary session")
            return pipeline.run(domain="english", dataset="wikitext", samples=100)
        elif hour < 12:  # Morning - Python
            logger.info("Scheduled: Python coding session")
            return pipeline.run(domain="python", dataset="mbpp", samples=50)
        elif hour < 18:  # Afternoon - Reading comprehension
            logger.info("Scheduled: Reading comprehension session")
            return pipeline.run(domain="english", dataset="squad", samples=80)
        else:  # Evening - Mixed review
            logger.info("Scheduled: Mixed review session")
            return pipeline.run_multi_domain(samples_per_domain=30)
    else:  # Weekends
        logger.info("Scheduled: Full training session")
        return pipeline.run_multi_domain(samples_per_domain=100)


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="RPA Unified Learning Pipeline")

    parser.add_argument("--domain", type=str, default="english",
                       choices=["english", "python", "all"],
                       help="Learning domain")

    parser.add_argument("--dataset", type=str, default=None,
                       help="Specific dataset (auto-selected if not specified)")

    parser.add_argument("--samples", type=int, default=100,
                       help="Number of samples to process")

    parser.add_argument("--auto", action="store_true",
                       help="Auto-run mode for scheduled execution")

    parser.add_argument("--persistence", type=str, default=None,
                       help="Path to persist learning state")

    parser.add_argument("--verbose", "-v", action="store_true", default=True,
                       help="Verbose output")

    parser.add_argument("--quiet", "-q", action="store_true",
                       help="Minimal output")

    args = parser.parse_args()

    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)

    if args.auto:
        result = auto_run()
    else:
        pipeline = UnifiedLearningPipeline(persistence_path=args.persistence)
        result = pipeline.run(
            domain=args.domain,
            dataset=args.dataset,
            samples=args.samples,
            verbose=args.verbose,
        )

    # Output result summary
    print(json.dumps(result, indent=2, default=str))

    return 0 if result.get("success") else 1


if __name__ == "__main__":
    sys.exit(main())
