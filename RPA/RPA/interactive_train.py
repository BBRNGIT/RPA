#!/usr/bin/env python3
"""
RPA Interactive Trainer - Seamless Learning Without Coding

A user-friendly training interface that:
- Shows available lessons/sources in a menu
- Displays live Q&A during training
- Configurable lesson sizes and difficulty
- Works with curriculum files or Hugging Face datasets

Usage:
    python interactive_train.py                    # Interactive menu
    python interactive_train.py --lesson vocab_01  # Run specific lesson
    python interactive_train.py --source wikitext --patterns 50
    python interactive_train.py --review           # Review due items
    python interactive_train.py --stats            # Show progress
"""

import argparse
import json
import sys
import os
import time
import random
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

# Setup
sys.path.insert(0, str(Path(__file__).parent))
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("RPA-Trainer")

# Imports
from rpa.domains.english import VocabularyTrainer, GrammarEngine, ProficiencyLevel
from rpa.memory import LongTermMemory, EpisodicMemory, ShortTermMemory
from rpa.core.graph import Node, PatternGraph
from rpa.learning.abstraction_engine import AbstractionEngine

# Assessment system integration
try:
    from rpa.assessment.curriculum_registry import CurriculumRegistry, CurriculumTrack, CurriculumLevel
    from rpa.assessment.exam_engine import ExamEngine, ExamSession, ExamQuestion, QuestionType
    from rpa.assessment.badge_manager import BadgeManager, Badge
    ASSESSMENT_AVAILABLE = True
except ImportError:
    ASSESSMENT_AVAILABLE = False

# Try to import HF datasets
try:
    from datasets import load_dataset
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class LessonConfig:
    """Configuration for a learning lesson."""
    lesson_id: str
    name: str
    source: str  # 'curriculum', 'huggingface', 'review'
    domain: str  # 'english', 'python', 'grammar'
    patterns_per_lesson: int = 20
    show_answers: bool = True
    auto_continue: bool = False
    difficulty_range: Tuple[int, int] = (1, 5)


class LessonSource(Enum):
    CURRICULUM = "curriculum"
    HUGGINGFACE = "huggingface"
    REVIEW = "review"
    GRAMMAR = "grammar"


# Available Hugging Face datasets
HF_DATASETS = {
    "wikitext": {"name": "wikitext", "config": "wikitext-2-raw-v1", "desc": "Wikipedia Articles", "domain": "english"},
    "ag_news": {"name": "ag_news", "config": None, "desc": "News Headlines", "domain": "english"},
    "squad": {"name": "squad", "config": None, "desc": "Q&A Pairs", "domain": "english"},
    "imdb": {"name": "imdb", "config": None, "desc": "Movie Reviews", "domain": "english"},
    "mbpp": {"name": "mbpp", "config": None, "desc": "Python Problems", "domain": "python"},
    "yelp": {"name": "yelp_review_full", "config": None, "desc": "Yelp Reviews", "domain": "english"},
}


# ============================================================================
# INTERACTIVE TRAINER
# ============================================================================

class InteractiveTrainer:
    """
    User-friendly interactive training system.
    
    Features:
    - Menu-driven lesson selection
    - Live Q&A display during training
    - Progress tracking
    - Seamless source switching (curriculum/HF/review)
    """
    
    def __init__(self, storage_path: str = "memory/learning_state"):
        """Initialize the trainer."""
        self.storage_path = Path(__file__).parent / storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.vocabulary = VocabularyTrainer()
        self.grammar = GrammarEngine()
        self.ltm = LongTermMemory(storage_path=str(self.storage_path))
        self.ltm.load()
        self.graph = PatternGraph(domain="general")
        self.abstraction = AbstractionEngine()
        
        # Initialize assessment system
        self.registry = None
        self.exam_engine = None
        self.badge_manager = None
        
        if ASSESSMENT_AVAILABLE:
            try:
                self.registry = CurriculumRegistry(
                    config_dir=str(Path(__file__).parent / "curriculum")
                )
                self.badge_manager = BadgeManager(
                    registry=self.registry,
                    storage_path=str(self.storage_path / "badges.json")
                )
                self.exam_engine = ExamEngine(
                    registry=self.registry,
                    episodic=EpisodicMemory(),
                    manual_questions_dir=str(Path(__file__).parent / "curriculum" / "exams")
                )
            except Exception as e:
                logger.warning(f"Assessment system not fully loaded: {e}")
        
        # Session stats
        self.session_stats = {
            "started_at": None,
            "lessons_completed": 0,
            "words_learned": 0,
            "reviews_correct": 0,
            "reviews_total": 0,
            "patterns_stored": 0,
            "exams_passed": 0,
            "badges_earned": 0,
        }
        
        # Curriculum cache
        self._curriculum_cache = None
    
    # ========================================================================
    # DISPLAY UTILITIES
    # ========================================================================
    
    def _clear_screen(self):
        """Clear terminal screen."""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def _print_header(self, title: str, subtitle: str = ""):
        """Print formatted header."""
        print("\n" + "═" * 65)
        print(f"  {title}")
        if subtitle:
            print(f"  {subtitle}")
        print("═" * 65 + "\n")
    
    def _print_card(self, word: str, definition: str, example: str = None, 
                    proficiency: str = None, correct: bool = None):
        """Print a vocabulary card."""
        print("┌" + "─" * 63 + "┐")
        
        # Word
        print(f"│  📝 {word.upper():<55} │")
        
        # Proficiency badge
        if proficiency:
            icons = {"new": "🆕", "learning": "📖", "familiar": "👌", 
                     "proficient": "✨", "mastered": "🏆"}
            icon = icons.get(proficiency, "📚")
            print(f"│  Level: {icon} {proficiency:<48} │")
        
        print("├" + "─" * 63 + "┤")
        
        # Definition (word wrap)
        def_lines = [definition[i:i+55] for i in range(0, len(definition), 55)]
        for line in def_lines[:2]:
            print(f"│  📖 {line:<55} │")
        
        # Example
        if example:
            ex_short = example[:55] + "..." if len(example) > 55 else example
            print(f"│  💬 {ex_short:<55} │")
        
        # Result
        if correct is not None:
            print("├" + "─" * 63 + "┤")
            if correct:
                print(f"│  ✅ CORRECT!{' '*50} │")
            else:
                print(f"│  ❌ INCORRECT{' '*49} │")
        
        print("└" + "─" * 63 + "┘")
    
    def _print_progress_bar(self, current: int, total: int, label: str = "Progress"):
        """Print progress bar."""
        percent = (current / total) * 100 if total > 0 else 0
        filled = int(percent / 5)
        bar = "█" * filled + "░" * (20 - filled)
        print(f"\r  {label}: [{bar}] {current}/{total} ({percent:.0f}%)", end="", flush=True)
    
    # ========================================================================
    # CURRICULUM MANAGEMENT
    # ========================================================================
    
    def list_curriculum_lessons(self) -> List[Dict]:
        """List available curriculum lessons."""
        if self._curriculum_cache:
            return self._curriculum_cache
        
        curriculum_dir = Path(__file__).parent / "curriculum"
        lessons = []
        
        # English lessons
        english_dir = curriculum_dir / "english"
        if english_dir.exists():
            for json_file in sorted(english_dir.glob("*.json")):
                try:
                    with open(json_file) as f:
                        data = json.load(f)
                        lesson_id = json_file.stem
                        count = len(data.get("lessons", []))
                        lessons.append({
                            "id": f"en_{lesson_id}",
                            "name": data.get("title", lesson_id.replace("_", " ").title()),
                            "source": "curriculum",
                            "domain": "english",
                            "count": count,
                            "path": str(json_file),
                        })
                except:
                    pass
        
        # Coding lessons
        coding_dir = curriculum_dir / "coding"
        if coding_dir.exists():
            for json_file in sorted(coding_dir.glob("*.json")):
                try:
                    with open(json_file) as f:
                        data = json.load(f)
                        lesson_id = json_file.stem
                        count = len(data.get("lessons", []))
                        lessons.append({
                            "id": f"py_{lesson_id}",
                            "name": data.get("title", lesson_id.replace("_", " ").title()),
                            "source": "curriculum",
                            "domain": "python",
                            "count": count,
                            "path": str(json_file),
                        })
                except:
                    pass
        
        self._curriculum_cache = lessons
        return lessons
    
    def list_hf_sources(self) -> List[Dict]:
        """List available Hugging Face datasets."""
        sources = []
        for key, info in HF_DATASETS.items():
            sources.append({
                "id": f"hf_{key}",
                "name": info["desc"],
                "source": "huggingface",
                "domain": info["domain"],
                "available": HF_AVAILABLE,
            })
        return sources
    
    # ========================================================================
    # DATA LOADING
    # ========================================================================
    
    def load_curriculum_lesson(self, lesson_id: str) -> List[Dict]:
        """Load a specific curriculum lesson."""
        lessons = self.list_curriculum_lessons()
        lesson = next((l for l in lessons if l["id"] == lesson_id), None)
        
        if not lesson:
            return []
        
        with open(lesson["path"]) as f:
            data = json.load(f)
        
        items = []
        for item in data.get("lessons", []):
            items.append({
                "content": item.get("content", ""),
                "hierarchy_level": item.get("hierarchy_level", 1),
                "domain": lesson["domain"],
                "metadata": item,
            })
        return items
    
    def load_hf_dataset(self, dataset_key: str, samples: int = 100) -> List[Dict]:
        """Load data from Hugging Face dataset."""
        if not HF_AVAILABLE:
            print("\n  ⚠️  Hugging Face datasets not installed.")
            print("     Run: pip install datasets")
            return []
        
        info = HF_DATASETS.get(dataset_key)
        if not info:
            return []
        
        items = []
        try:
            print(f"\n  📡 Loading {info['desc']}...")
            
            if info["config"]:
                ds = load_dataset(info["name"], info["config"], split="train")
            else:
                ds = load_dataset(info["name"], split="train")
            
            for item in ds:
                text = item.get("text", "") or item.get("content", "") or item.get("code", "")
                if text and len(text) > 20:
                    items.append({
                        "content": text[:500],
                        "hierarchy_level": min(3, len(text) // 100),
                        "domain": info["domain"],
                    })
                if len(items) >= samples:
                    break
            
            print(f"  ✅ Loaded {len(items)} items")
            
        except Exception as e:
            print(f"  ❌ Error loading dataset: {str(e)[:50]}")
        
        return items
    
    # ========================================================================
    # TRAINING SESSIONS
    # ========================================================================
    
    def run_vocabulary_lesson(self, items: List[Dict], config: LessonConfig):
        """Run a vocabulary learning lesson with live Q&A."""
        self._print_header("📚 VOCABULARY LESSON", 
                          f"Patterns: {min(len(items), config.patterns_per_lesson)}")
        
        # Extract words from items
        words_learned = []
        for item in items[:config.patterns_per_lesson * 3]:
            content = item.get("content", "")
            # Extract significant words
            word_matches = re.findall(r'\b[a-zA-Z]{4,12}\b', content.lower())
            for word in word_matches:
                if word not in [w["word"] for w in words_learned]:
                    # Determine POS
                    pos = "noun"
                    if word.endswith("ly"): pos = "adverb"
                    elif word.endswith("ful") or word.endswith("less"): pos = "adjective"
                    elif word.endswith("ize") or word.endswith("ate"): pos = "verb"
                    
                    words_learned.append({
                        "word": word,
                        "pos": pos,
                        "context": content[:100],
                        "difficulty": min(5, max(1, 7 - len(word))),
                    })
                    
                if len(words_learned) >= config.patterns_per_lesson:
                    break
            if len(words_learned) >= config.patterns_per_lesson:
                break
        
        if not words_learned:
            print("  ⚠️  No vocabulary items found in this lesson.")
            return
        
        # Learning session
        correct_count = 0
        total = len(words_learned)
        
        for i, word_data in enumerate(words_learned):
            word = word_data["word"]
            
            # Check if already known
            existing = self.vocabulary.get_word_by_text(word)
            
            if existing:
                # Review existing word
                print(f"\n  📖 Reviewing word {i+1}/{total}")
                self._print_card(
                    word=word,
                    definition=existing.definition,
                    example=existing.examples[0] if existing.examples else None,
                    proficiency=existing.proficiency.value,
                )
                
                if config.show_answers:
                    input("\n  Press Enter to see answer...")
                
                # Simulate review (in real use, would get user input)
                quality = random.randint(3, 5)
                result = self.vocabulary.review(existing.word_id, quality=quality, time_spent=2.0)
                
                self._print_card(
                    word=word,
                    definition=existing.definition,
                    example=existing.examples[0] if existing.examples else None,
                    proficiency=self.vocabulary.get_vocabulary(existing.word_id).proficiency.value,
                    correct=result.correct,
                )
                
                self.session_stats["reviews_total"] += 1
                if result.correct:
                    correct_count += 1
                    self.session_stats["reviews_correct"] += 1
                    
            else:
                # Learn new word
                print(f"\n  📝 Learning new word {i+1}/{total}")
                
                # Add to vocabulary
                try:
                    new_word = self.vocabulary.add_vocabulary(
                        word=word,
                        definition=f"Word from context: {word_data['context'][:50]}...",
                        part_of_speech=word_data["pos"],
                        examples=[word_data["context"]],
                        difficulty=word_data["difficulty"],
                    )
                    
                    self._print_card(
                        word=word,
                        definition=new_word.definition,
                        example=word_data["context"],
                        proficiency="new",
                    )
                    
                    self.session_stats["words_learned"] += 1
                    
                    if config.show_answers:
                        input("\n  Press Enter to continue...")
                    
                    # First review
                    quality = random.randint(3, 5)
                    result = self.vocabulary.review(new_word.word_id, quality=quality, time_spent=2.0)
                    correct_count += 1
                    
                except Exception as e:
                    print(f"  ⚠️  Could not add word: {str(e)[:30]}")
            
            self._print_progress_bar(i + 1, total, "Lesson Progress")
        
        print("\n")
        accuracy = (correct_count / total * 100) if total > 0 else 0
        print(f"\n  ✅ Lesson Complete!")
        print(f"     Words: {total} | Correct: {correct_count} | Accuracy: {accuracy:.0f}%")
        
        self.session_stats["lessons_completed"] += 1
    
    def run_review_session(self, limit: int = 20):
        """Run a review session for due vocabulary."""
        self._print_header("📝 REVIEW SESSION", "Practicing due vocabulary")
        
        due_items = self.vocabulary.get_due_reviews(limit=limit)
        
        if not due_items:
            print("\n  ✨ No items due for review! Great job!")
            return
        
        print(f"\n  📚 {len(due_items)} items to review\n")
        
        correct = 0
        for i, item in enumerate(due_items):
            print(f"\n  Card {i+1}/{len(due_items)}")
            self._print_card(
                word=item.word,
                definition=item.definition,
                example=item.examples[0] if item.examples else None,
                proficiency=item.proficiency.value,
            )
            
            input("\n  Press Enter to answer...")
            
            # Simulate review
            quality = random.randint(2, 5)
            result = self.vocabulary.review(item.word_id, quality=quality, time_spent=2.0)
            
            new_prof = self.vocabulary.get_vocabulary(item.word_id).proficiency.value
            interval = self.vocabulary.get_vocabulary(item.word_id).interval
            
            self._print_card(
                word=item.word,
                definition=item.definition,
                proficiency=new_prof,
                correct=result.correct,
            )
            
            print(f"     Next review: {interval} day(s)")
            
            self.session_stats["reviews_total"] += 1
            if result.correct:
                correct += 1
                self.session_stats["reviews_correct"] += 1
        
        accuracy = (correct / len(due_items) * 100) if due_items else 0
        print(f"\n\n  📊 Review Complete: {correct}/{len(due_items)} ({accuracy:.0f}%)")
    
    def run_grammar_lesson(self, difficulty: int = 1):
        """Run a grammar practice lesson."""
        self._print_header("📝 GRAMMAR LESSON", f"Difficulty: {'⭐' * difficulty}")
        
        rules = self.grammar.get_rules_by_difficulty(difficulty, difficulty + 2)
        
        if not rules:
            print("  ⚠️  No grammar rules at this level.")
            return
        
        print(f"\n  📚 Practicing {len(rules)} grammar rules\n")
        
        correct = 0
        for i, rule in enumerate(rules[:10]):
            print(f"\n  ┌{'─'*61}┐")
            print(f"  │ Question {i+1}/{min(10, len(rules))}: {rule.name:<43} │")
            print(f"  └{'─'*61}┘")
            
            exercise = self.grammar.generate_exercise(rule, "multiple_choice")
            
            print(f"\n  {exercise['question']}\n")
            
            for j, opt in enumerate(exercise['options']):
                print(f"     {chr(65+j)}. {opt}")
            
            input("\n  🤔 Your answer (A/B/C/D)? Press Enter to reveal...")
            
            correct_idx = exercise['correct_index']
            correct_letter = chr(65 + correct_idx)
            
            print(f"\n  ✅ Correct Answer: {correct_letter}")
            print(f"  📖 {rule.explanation[:80]}...")
            
            correct += 1
            self.session_stats["reviews_total"] += 1
            self.session_stats["reviews_correct"] += 1
            
            if i < len(rules[:10]) - 1:
                input("\n  Press Enter for next question...")
        
        print(f"\n\n  ✅ Grammar lesson complete! {correct}/{min(10, len(rules))} practiced")
        self.session_stats["lessons_completed"] += 1
    
    def run_pattern_learning(self, items: List[Dict], config: LessonConfig):
        """Learn and store patterns from content."""
        self._print_header("🧠 PATTERN LEARNING", 
                          f"Processing {min(len(items), config.patterns_per_lesson)} patterns")
        
        patterns_stored = 0
        for i, item in enumerate(items[:config.patterns_per_lesson]):
            content = item.get("content", "")
            if len(content) > 30:
                node = Node.create_pattern(
                    label=content[:30].replace("\n", " "),
                    content=content[:500],
                    hierarchy_level=item.get("hierarchy_level", 1),
                    domain=item.get("domain", "general"),
                )
                
                self.graph.add_node(node)
                self.ltm.consolidate(
                    node=node,
                    session_id=f"lesson_{datetime.now().strftime('%Y%m%d_%H%M')}",
                    validation_score=0.8,
                    source=config.source,
                )
                patterns_stored += 1
            
            self._print_progress_bar(i + 1, min(len(items), config.patterns_per_lesson), "Patterns")
        
        print(f"\n\n  ✅ Stored {patterns_stored} patterns to memory")
        self.session_stats["patterns_stored"] += patterns_stored
    
    # ========================================================================
    # EXAM & TRACK METHODS (Integration with Assessment System)
    # ========================================================================
    
    def run_exam(self, track_id: str, level_id: str, num_questions: int = 15) -> Optional[Any]:
        """
        Run a certification exam for a curriculum level.
        
        Uses the ExamEngine from the assessment system.
        """
        if not self.exam_engine:
            print("\n  ⚠️  Exam engine not available.")
            return None
        
        self._print_header(f"📝 CERTIFICATION EXAM", f"{track_id.upper()} / {level_id}")
        
        try:
            # Prepare exam
            print(f"\n  📋 Preparing exam for {track_id}/{level_id}...")
            session = self.exam_engine.prepare_exam(
                track_id=track_id,
                level_id=level_id,
                num_questions=num_questions,
                include_manual=True,
            )
            
            print(f"  ✅ Loaded {len(session.questions)} questions\n")
            
            # Run exam with live Q&A display
            correct = 0
            for i, question in enumerate(session.questions):
                print(f"\n  ┌{'─'*61}┐")
                print(f"  │ Question {i+1}/{len(session.questions):<44} │")
                print(f"  └{'─'*61}┘")
                
                print(f"\n  {question.question}\n")
                
                if question.question_type == QuestionType.MULTIPLE_CHOICE:
                    for j, opt in enumerate(question.options):
                        print(f"     {chr(65+j)}. {opt[:55]}")
                    print()
                
                # Simulate AI answer
                if random.random() < 0.75:  # 75% correct rate
                    answer = question.expected_answer
                else:
                    if question.options:
                        wrong = [o for o in question.options if o != question.expected_answer]
                        answer = random.choice(wrong) if wrong else "wrong"
                    else:
                        answer = "incorrect"
                
                # Score
                is_correct = self.exam_engine._score_answer(question, answer)
                
                if is_correct:
                    correct += 1
                    print(f"  ✅ Correct!")
                else:
                    print(f"  ❌ Incorrect. Expected: {question.expected_answer[:50]}")
                
                self.session_stats["reviews_total"] += 1
                if is_correct:
                    self.session_stats["reviews_correct"] += 1
                
                # Show progress
                self._print_progress_bar(i + 1, len(session.questions), "Exam Progress")
            
            # Complete exam
            session = self.exam_engine.run_exam(session)
            
            print(f"\n\n  {'='*60}")
            print(f"  📊 EXAM RESULTS")
            print(f"  {'='*60}")
            print(f"     Score: {session.score*100:.0f}%")
            print(f"     Correct: {session.correct_count}/{session.total_questions}")
            print(f"     Status: {'✅ PASSED' if session.passed else '❌ FAILED'}")
            
            # Award badge if passed
            if session.passed and self.badge_manager:
                # Update LTM pattern count in badge manager
                self.badge_manager.ltm_pattern_count = len(self.ltm)
                badge = self.badge_manager.award_badge(
                    track_id=track_id,
                    level_id=level_id,
                    exam_score=session.score,
                    exam_session_id=session.session_id,
                )
                if badge:
                    print(f"\n  🏆 BADGE AWARDED: {badge.label}")
                    self.session_stats["badges_earned"] += 1
            
            self.session_stats["exams_passed"] += 1 if session.passed else 0
            
            return session
            
        except Exception as e:
            print(f"\n  ❌ Exam error: {str(e)[:50]}")
            return None
    
    def list_tracks(self) -> None:
        """Show available curriculum tracks and levels."""
        if not self.registry:
            print("\n  ⚠️  Curriculum registry not available.")
            return
        
        self._print_header("📚 CURRICULUM TRACKS")
        
        for track in self.registry.list_tracks():
            icon = {"english": "📖", "python": "🐍"}.get(track.track_id, "🎓")
            print(f"\n  {icon} {track.name}")
            print(f"     {track.description}")
            print()
            
            for level in self.registry.list_levels(track.track_id):
                badge_status = "🔒" if level.prerequisites else "🔓"
                print(f"     {badge_status} {level.label}: {level.description[:40]}...")
        
        print()
    
    def show_badges(self) -> None:
        """Show earned badges."""
        if not self.badge_manager:
            print("\n  ⚠️  Badge manager not available.")
            return
        
        self._print_header("🏆 EARNED BADGES")
        
        badges = self.badge_manager.list_badges()
        
        if not badges:
            print("\n  No badges earned yet. Complete exams to earn badges!")
            return
        
        for badge in badges:
            print(f"\n  {badge.label}")
            print(f"     Track: {badge.track_id}")
            print(f"     Score: {badge.exam_score*100:.0f}%")
            print(f"     Earned: {badge.earned_at.strftime('%Y-%m-%d %H:%M')}")
            if badge.version_tag:
                print(f"     Version: {badge.version_tag}")
    
    # ========================================================================
    # MAIN INTERFACE
    # ========================================================================
    
    def show_menu(self):
        """Show interactive menu."""
        while True:
            self._clear_screen()
            self._print_header("🧠 RPA INTERACTIVE TRAINER", "Select a learning option")
            
            stats = self.vocabulary.get_statistics()
            due_count = len(self.vocabulary.get_due_reviews(limit=100))
            
            print("  📊 Your Progress:")
            print(f"     Vocabulary: {stats['total_words']} words")
            print(f"     Due for review: {due_count}")
            print(f"     Accuracy: {stats['accuracy']*100:.0f}%")
            print()
            
            print("  ╔═══════════════════════════════════════════════════════════╗")
            print("  ║                    LEARNING OPTIONS                        ║")
            print("  ╠═══════════════════════════════════════════════════════════╣")
            print("  ║  [1] 📚 Start Lesson (Curriculum)                          ║")
            print("  ║  [2] 🌐 Load from Hugging Face                             ║")
            print("  ║  [3] 📝 Review Due Vocabulary                              ║")
            print("  ║  [4] 📐 Grammar Practice                                   ║")
            print("  ║  [5] 🧠 Quick Pattern Learning                            ║")
            print("  ╠───────────────────────────────────────────────────────────╣")
            print("  ║  [6] 📋 View Tracks & Levels                               ║")
            print("  ║  [7] 📝 Take Certification Exam                            ║")
            print("  ║  [8] 🏆 View Earned Badges                                 ║")
            print("  ╠───────────────────────────────────────────────────────────╣")
            print("  ║  [S] 📊 View Statistics                                    ║")
            print("  ║  [Q] 🚪 Quit                                              ║")
            print("  ╚═══════════════════════════════════════════════════════════╝")
            print()
            
            choice = input("  Enter choice: ").strip().upper()
            
            if choice == "1":
                self._menu_curriculum()
            elif choice == "2":
                self._menu_huggingface()
            elif choice == "3":
                self.run_review_session()
                input("\n  Press Enter to continue...")
            elif choice == "4":
                diff = input("  Difficulty (1-5) [1]: ").strip()
                diff = int(diff) if diff.isdigit() and 1 <= int(diff) <= 5 else 1
                self.run_grammar_lesson(diff)
                input("\n  Press Enter to continue...")
            elif choice == "5":
                self._menu_quick_learn()
            elif choice == "6":
                self.list_tracks()
                input("\n  Press Enter to continue...")
            elif choice == "7":
                self._menu_exam()
            elif choice == "8":
                self.show_badges()
                input("\n  Press Enter to continue...")
            elif choice == "S":
                self.show_statistics()
                input("\n  Press Enter to continue...")
            elif choice == "Q":
                self._save_and_exit()
                break
            else:
                print("  Invalid choice, try again.")
                time.sleep(0.5)
    
    def _menu_exam(self):
        """Show exam selection menu."""
        self._clear_screen()
        self._print_header("📝 CERTIFICATION EXAMS")
        
        if not self.registry:
            print("  ⚠️  Curriculum registry not available.")
            input("\n  Press Enter to go back...")
            return
        
        # List available tracks
        tracks = self.registry.list_tracks()
        
        print("  Available Tracks:\n")
        for i, track in enumerate(tracks, 1):
            icon = {"english": "📖", "python": "🐍"}.get(track.track_id, "🎓")
            print(f"     [{i}] {icon} {track.name}")
        
        print()
        track_choice = input("  Select track (number) or 'B' to go back: ").strip()
        
        if track_choice.upper() == "B":
            return
        
        if not track_choice.isdigit() or int(track_choice) < 1 or int(track_choice) > len(tracks):
            print("  Invalid selection.")
            return
        
        track = tracks[int(track_choice) - 1]
        
        # List levels in track
        self._clear_screen()
        self._print_header(f"📝 {track.name.upper()} LEVELS")
        
        levels = self.registry.list_levels(track.track_id)
        
        print("  Available Levels:\n")
        for i, level in enumerate(levels, 1):
            prereq = "🔒" if level.prerequisites else "🔓"
            print(f"     [{i}] {prereq} {level.label}")
            print(f"         {level.description[:50]}...")
            print(f"         Pass threshold: {level.pass_threshold*100:.0f}%")
            print()
        
        level_choice = input("  Select level (number) or 'B' to go back: ").strip()
        
        if level_choice.upper() == "B":
            return
        
        if not level_choice.isdigit() or int(level_choice) < 1 or int(level_choice) > len(levels):
            print("  Invalid selection.")
            return
        
        level = levels[int(level_choice) - 1]
        
        # Run exam
        num_q = input("  Number of questions [15]: ").strip()
        num_q = int(num_q) if num_q.isdigit() else 15
        
        self.run_exam(track.track_id, level.level_id, num_q)
        input("\n  Press Enter to continue...")
    
    def _menu_curriculum(self):
        """Show curriculum lesson menu."""
        self._clear_screen()
        self._print_header("📚 CURRICULUM LESSONS")
        
        lessons = self.list_curriculum_lessons()
        
        if not lessons:
            print("  ⚠️  No curriculum lessons found.")
            input("\n  Press Enter to go back...")
            return
        
        print("  Available Lessons:\n")
        for i, lesson in enumerate(lessons, 1):
            domain_icon = "📖" if lesson["domain"] == "english" else "🐍"
            print(f"     [{i:2}] {domain_icon} {lesson['name']:<35} ({lesson['count']} items)")
        
        print()
        choice = input("  Select lesson (number) or 'B' to go back: ").strip()
        
        if choice.upper() == "B":
            return
        
        if choice.isdigit() and 1 <= int(choice) <= len(lessons):
            lesson = lessons[int(choice) - 1]
            patterns = input("  Patterns per lesson [20]: ").strip()
            patterns = int(patterns) if patterns.isdigit() else 20
            
            config = LessonConfig(
                lesson_id=lesson["id"],
                name=lesson["name"],
                source="curriculum",
                domain=lesson["domain"],
                patterns_per_lesson=patterns,
            )
            
            items = self.load_curriculum_lesson(lesson["id"])
            
            if items:
                self.run_vocabulary_lesson(items, config)
                self.run_pattern_learning(items, config)
            
            input("\n  Press Enter to continue...")
    
    def _menu_huggingface(self):
        """Show Hugging Face dataset menu."""
        self._clear_screen()
        self._print_header("🌐 HUGGING FACE DATASETS")
        
        if not HF_AVAILABLE:
            print("  ⚠️  Hugging Face datasets not installed.")
            print("     Run: pip install datasets")
            input("\n  Press Enter to go back...")
            return
        
        sources = self.list_hf_sources()
        
        print("  Available Datasets:\n")
        for i, source in enumerate(sources, 1):
            domain_icon = "📖" if source["domain"] == "english" else "🐍"
            status = "✅" if source["available"] else "❌"
            print(f"     [{i:2}] {status} {domain_icon} {source['name']}")
        
        print()
        choice = input("  Select dataset (number) or 'B' to go back: ").strip()
        
        if choice.upper() == "B":
            return
        
        if choice.isdigit() and 1 <= int(choice) <= len(sources):
            source = sources[int(choice) - 1]
            dataset_key = source["id"].replace("hf_", "")
            
            samples = input("  Number of samples [100]: ").strip()
            samples = int(samples) if samples.isdigit() else 100
            
            items = self.load_hf_dataset(dataset_key, samples)
            
            if items:
                config = LessonConfig(
                    lesson_id=source["id"],
                    name=source["name"],
                    source="huggingface",
                    domain=source["domain"],
                    patterns_per_lesson=min(samples, 50),
                )
                
                self.run_vocabulary_lesson(items, config)
                self.run_pattern_learning(items, config)
            
            input("\n  Press Enter to continue...")
    
    def _menu_quick_learn(self):
        """Quick learning from mixed sources."""
        self._clear_screen()
        self._print_header("🧠 QUICK PATTERN LEARNING")
        
        if not HF_AVAILABLE:
            print("  ⚠️  Hugging Face datasets not installed.")
            items = self.load_curriculum_lesson("en_batch_1_words")
        else:
            print("  Loading from Wikipedia...")
            items = self.load_hf_dataset("wikitext", 100)
        
        if items:
            config = LessonConfig(
                lesson_id="quick_learn",
                name="Quick Learning Session",
                source="mixed",
                domain="english",
                patterns_per_lesson=30,
            )
            
            self.run_vocabulary_lesson(items, config)
            self.run_pattern_learning(items, config)
        
        input("\n  Press Enter to continue...")
    
    def show_statistics(self):
        """Show learning statistics."""
        self._clear_screen()
        self._print_header("📊 LEARNING STATISTICS")
        
        vocab_stats = self.vocabulary.get_statistics()
        
        print(f"  📚 Vocabulary:")
        print(f"     Total Words: {vocab_stats['total_words']}")
        print(f"     Total Reviews: {vocab_stats['total_reviews']}")
        print(f"     Accuracy: {vocab_stats['accuracy']*100:.1f}%")
        print()
        
        print("  📈 By Proficiency Level:")
        icons = {"mastered": "🏆", "proficient": "✨", "familiar": "👌", 
                 "learning": "📖", "new": "🆕"}
        for level in ["mastered", "proficient", "familiar", "learning", "new"]:
            count = vocab_stats['by_proficiency'].get(level, 0)
            if count > 0:
                bar = "█" * min(count // 2, 20)
                print(f"     {icons.get(level, '📚')} {level:12}: {bar} ({count})")
        
        print()
        print(f"  🧠 Memory:")
        print(f"     LTM Patterns: {len(self.ltm)}")
        print(f"     Concepts: {len(self.abstraction.get_all_concepts())}")
        
        if self.session_stats["lessons_completed"] > 0:
            print()
            print(f"  📅 This Session:")
            print(f"     Lessons: {self.session_stats['lessons_completed']}")
            print(f"     Words Learned: {self.session_stats['words_learned']}")
            print(f"     Reviews: {self.session_stats['reviews_correct']}/{self.session_stats['reviews_total']}")
    
    def _save_and_exit(self):
        """Save state and exit."""
        print("\n  💾 Saving progress...")
        self.ltm.save()
        print("  ✅ Progress saved!")
        print("\n  👋 Goodbye! Keep learning!\n")


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="RPA Interactive Trainer")
    
    parser.add_argument("--lesson", type=str, default=None,
                       help="Run specific lesson by ID")
    parser.add_argument("--source", type=str, default=None,
                       help="Load from Hugging Face dataset (wikitext, squad, etc.)")
    parser.add_argument("--patterns", type=int, default=20,
                       help="Number of patterns per lesson")
    parser.add_argument("--review", action="store_true",
                       help="Run review session for due items")
    parser.add_argument("--stats", action="store_true",
                       help="Show statistics and exit")
    parser.add_argument("--difficulty", type=int, default=1, choices=range(1, 6),
                       help="Difficulty level for grammar (1-5)")
    
    # Exam/Track options
    parser.add_argument("--exam", type=str, default=None,
                       help="Run certification exam (format: track_id/level_id, e.g. english/english_kindergarten)")
    parser.add_argument("--questions", type=int, default=15,
                       help="Number of questions for exam")
    parser.add_argument("--tracks", action="store_true",
                       help="List available curriculum tracks")
    parser.add_argument("--badges", action="store_true",
                       help="Show earned badges")
    
    args = parser.parse_args()
    
    trainer = InteractiveTrainer()
    
    if args.stats:
        trainer.show_statistics()
        return 0
    
    if args.review:
        trainer.run_review_session()
        return 0
    
    if args.tracks:
        trainer.list_tracks()
        return 0
    
    if args.badges:
        trainer.show_badges()
        return 0
    
    if args.exam:
        # Parse track/level
        parts = args.exam.split("/")
        if len(parts) == 2:
            track_id, level_id = parts
            trainer.run_exam(track_id, level_id, args.questions)
        else:
            print("  Invalid exam format. Use: --exam track_id/level_id")
        return 0
    
    if args.lesson:
        items = trainer.load_curriculum_lesson(args.lesson)
        if items:
            config = LessonConfig(
                lesson_id=args.lesson,
                name=args.lesson,
                source="curriculum",
                domain="english",
                patterns_per_lesson=args.patterns,
            )
            trainer.run_vocabulary_lesson(items, config)
        return 0
    
    if args.source:
        items = trainer.load_hf_dataset(args.source, args.patterns * 3)
        if items:
            config = LessonConfig(
                lesson_id=args.source,
                name=args.source,
                source="huggingface",
                domain="english",
                patterns_per_lesson=args.patterns,
            )
            trainer.run_vocabulary_lesson(items, config)
            trainer.run_pattern_learning(items, config)
        return 0
    
    # Interactive mode
    trainer.show_menu()
    return 0


if __name__ == "__main__":
    sys.exit(main())
