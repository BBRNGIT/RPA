"""
English Language Learning Domain for RPA.

This module provides comprehensive English language learning capabilities:
- Vocabulary training with spaced repetition
- Grammar rules engine and exercises
- Reading comprehension system
- Writing assessment and feedback
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Set
import json
import math
import random
import re
import uuid
import logging

from rpa.memory.ltm import LongTermMemory
from rpa.memory.episodic import EpisodicMemory, EventType
from rpa.core.graph import Node, NodeType

logger = logging.getLogger(__name__)


# ============================================================================
# VOCABULARY LEARNING
# ============================================================================

class ProficiencyLevel(Enum):
    """Vocabulary proficiency levels."""
    NEW = "new"                    # Never seen before
    LEARNING = "learning"          # Currently learning
    FAMILIAR = "familiar"          # Recognized but not mastered
    PROFICIENT = "proficient"      # Well known
    MASTERED = "mastered"          # Fully mastered


@dataclass
class VocabularyItem:
    """A vocabulary word with learning metadata."""
    word_id: str
    word: str
    definition: str
    part_of_speech: str  # noun, verb, adjective, adverb, etc.
    examples: List[str]
    synonyms: List[str] = field(default_factory=list)
    antonyms: List[str] = field(default_factory=list)
    etymology: str = ""
    difficulty: int = 1  # 1-5 scale
    frequency_rank: int = 0  # Common usage rank

    # Spaced repetition fields
    proficiency: ProficiencyLevel = ProficiencyLevel.NEW
    ease_factor: float = 2.5  # SM-2 algorithm
    interval: int = 0  # Days until next review
    repetitions: int = 0  # Number of successful reviews
    next_review: Optional[datetime] = None
    last_review: Optional[datetime] = None

    # Learning metrics
    total_reviews: int = 0
    correct_reviews: int = 0
    incorrect_reviews: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "word_id": self.word_id,
            "word": self.word,
            "definition": self.definition,
            "part_of_speech": self.part_of_speech,
            "examples": self.examples,
            "synonyms": self.synonyms,
            "antonyms": self.antonyms,
            "etymology": self.etymology,
            "difficulty": self.difficulty,
            "frequency_rank": self.frequency_rank,
            "proficiency": self.proficiency.value,
            "ease_factor": self.ease_factor,
            "interval": self.interval,
            "repetitions": self.repetitions,
            "next_review": self.next_review.isoformat() if self.next_review else None,
            "last_review": self.last_review.isoformat() if self.last_review else None,
            "total_reviews": self.total_reviews,
            "correct_reviews": self.correct_reviews,
            "incorrect_reviews": self.incorrect_reviews,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VocabularyItem":
        """Deserialize from dictionary."""
        return cls(
            word_id=data["word_id"],
            word=data["word"],
            definition=data["definition"],
            part_of_speech=data["part_of_speech"],
            examples=data.get("examples", []),
            synonyms=data.get("synonyms", []),
            antonyms=data.get("antonyms", []),
            etymology=data.get("etymology", ""),
            difficulty=data.get("difficulty", 1),
            frequency_rank=data.get("frequency_rank", 0),
            proficiency=ProficiencyLevel(data.get("proficiency", "new")),
            ease_factor=data.get("ease_factor", 2.5),
            interval=data.get("interval", 0),
            repetitions=data.get("repetitions", 0),
            next_review=datetime.fromisoformat(data["next_review"]) if data.get("next_review") else None,
            last_review=datetime.fromisoformat(data["last_review"]) if data.get("last_review") else None,
            total_reviews=data.get("total_reviews", 0),
            correct_reviews=data.get("correct_reviews", 0),
            incorrect_reviews=data.get("incorrect_reviews", 0),
        )


@dataclass
class ReviewResult:
    """Result of a vocabulary review."""
    word_id: str
    correct: bool
    quality: int  # 0-5 scale (SM-2)
    time_spent_seconds: float
    response: str
    expected: str
    feedback: str
    reviewed_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "word_id": self.word_id,
            "correct": self.correct,
            "quality": self.quality,
            "time_spent_seconds": self.time_spent_seconds,
            "response": self.response,
            "expected": self.expected,
            "feedback": self.feedback,
            "reviewed_at": self.reviewed_at.isoformat(),
        }


class VocabularyTrainer:
    """
    Vocabulary training with spaced repetition (SM-2 algorithm).

    Features:
    - Leitner system for spaced repetition
    - Multiple review modes (flashcard, multiple choice, typing)
    - Progress tracking and statistics
    - Difficulty-based scheduling
    """

    # Quality thresholds for SM-2
    QUALITY_THRESHOLDS = {
        5: "Perfect - immediate, confident recall",
        4: "Correct after hesitation",
        3: "Correct with difficulty",
        2: "Incorrect, but recognized the answer",
        1: "Incorrect, but somewhat familiar",
        0: "Complete failure - no recollection",
    }

    def __init__(
        self,
        ltm: Optional[LongTermMemory] = None,
        episodic: Optional[EpisodicMemory] = None,
    ):
        """Initialize vocabulary trainer."""
        self.ltm = ltm or LongTermMemory()
        self.episodic = episodic or EpisodicMemory()
        self._vocabulary: Dict[str, VocabularyItem] = {}
        self._review_history: List[ReviewResult] = []
        self._initialize_common_vocabulary()

    def _initialize_common_vocabulary(self) -> None:
        """Initialize with common English vocabulary."""
        common_words = [
            # High frequency words (difficulty 1-2)
            ("the", "determiner", "Used to refer to a specific person or thing", ["The cat sat.", "The book is here."], 1, 1),
            ("be", "verb", "Exist; occur; used as an auxiliary verb", ["I am happy.", "She is here."], 1, 2),
            ("to", "preposition", "Expressing direction or motion", ["Go to school.", "Give it to me."], 1, 3),
            ("of", "preposition", "Expressing relationship or origin", ["A cup of tea.", "King of France."], 1, 4),
            ("and", "conjunction", "Used to connect words", ["You and I.", "Apples and oranges."], 1, 5),

            # Medium frequency words (difficulty 2-3)
            ("accomplish", "verb", "To achieve or complete successfully", ["She accomplished her goals.", "Mission accomplished!"], 2, 1000),
            ("adequate", "adjective", "Sufficient or acceptable", ["The resources were adequate.", "An adequate solution."], 2, 2000),
            ("benefit", "noun", "An advantage or profit", ["Health benefits.", "For your benefit."], 2, 1500),
            ("capacity", "noun", "The maximum amount something can hold", ["Full capacity.", "Mental capacity."], 2, 1800),
            ("demonstrate", "verb", "To show clearly", ["Demonstrate the process.", "He demonstrated courage."], 3, 2500),

            # Advanced words (difficulty 3-4)
            ("ambiguous", "adjective", "Open to more than one interpretation", ["An ambiguous statement.", "The meaning was ambiguous."], 3, 4000),
            ("comprehensive", "adjective", "Complete and including everything", ["A comprehensive study.", "Comprehensive coverage."], 3, 3500),
            ("elaborate", "adjective", "Involving many details", ["Elaborate design.", "An elaborate plan."], 3, 4500),
            ("fundamental", "adjective", "Forming a necessary base", ["Fundamental rights.", "The fundamental issue."], 3, 3200),
            ("hypothetical", "adjective", "Based on a suggested idea", ["A hypothetical scenario.", "Hypothetical question."], 4, 5500),

            # Expert words (difficulty 4-5)
            ("ubiquitous", "adjective", "Present everywhere", ["Smartphones are ubiquitous.", "Ubiquitous technology."], 4, 8000),
            ("ephemeral", "adjective", "Lasting for a very short time", ["Ephemeral beauty.", "Ephemeral moments."], 5, 10000),
            ("paradigm", "noun", "A typical example or pattern", ["A new paradigm.", "Paradigm shift."], 4, 7000),
            ("pragmatic", "adjective", "Dealing with things sensibly", ["A pragmatic approach.", "Pragmatic solution."], 4, 6500),
            ("esoteric", "adjective", "Intended for a small group", ["Esoteric knowledge.", "Esoteric subject."], 5, 12000),
        ]

        for word, pos, definition, examples, difficulty, freq in common_words:
            item = VocabularyItem(
                word_id=f"vocab_{uuid.uuid4().hex[:8]}",
                word=word,
                definition=definition,
                part_of_speech=pos,
                examples=examples,
                difficulty=difficulty,
                frequency_rank=freq,
            )
            self._vocabulary[item.word_id] = item

    def add_vocabulary(
        self,
        word: str,
        definition: str,
        part_of_speech: str,
        examples: Optional[List[str]] = None,
        synonyms: Optional[List[str]] = None,
        antonyms: Optional[List[str]] = None,
        difficulty: int = 1,
    ) -> VocabularyItem:
        """Add a new vocabulary item."""
        item = VocabularyItem(
            word_id=f"vocab_{uuid.uuid4().hex[:8]}",
            word=word,
            definition=definition,
            part_of_speech=part_of_speech,
            examples=examples or [],
            synonyms=synonyms or [],
            antonyms=antonyms or [],
            difficulty=difficulty,
        )
        self._vocabulary[item.word_id] = item
        return item

    def get_vocabulary(self, word_id: str) -> Optional[VocabularyItem]:
        """Get a vocabulary item by ID."""
        return self._vocabulary.get(word_id)

    def get_word_by_text(self, word: str) -> Optional[VocabularyItem]:
        """Get a vocabulary item by word text."""
        for item in self._vocabulary.values():
            if item.word.lower() == word.lower():
                return item
        return None

    def get_due_reviews(self, limit: int = 20) -> List[VocabularyItem]:
        """Get vocabulary items due for review."""
        now = datetime.now()
        due = []

        for item in self._vocabulary.values():
            if item.next_review is None or item.next_review <= now:
                due.append(item)

        # Sort by proficiency (new words first) and difficulty
        due.sort(key=lambda x: (list(ProficiencyLevel).index(x.proficiency), x.difficulty))

        return due[:limit]

    def get_new_vocabulary(self, limit: int = 10) -> List[VocabularyItem]:
        """Get new vocabulary items to learn."""
        new_items = [
            item for item in self._vocabulary.values()
            if item.proficiency == ProficiencyLevel.NEW
        ]
        new_items.sort(key=lambda x: x.frequency_rank)
        return new_items[:limit]

    def generate_flashcard(self, item: VocabularyItem) -> Dict[str, Any]:
        """Generate a flashcard for review."""
        return {
            "word_id": item.word_id,
            "front": item.word,
            "back": item.definition,
            "examples": item.examples,
            "part_of_speech": item.part_of_speech,
            "synonyms": item.synonyms,
            "difficulty": item.difficulty,
        }

    def generate_multiple_choice(
        self,
        item: VocabularyItem,
        num_options: int = 4,
    ) -> Dict[str, Any]:
        """Generate a multiple choice question."""
        # Get distractors
        distractors = []
        for other in self._vocabulary.values():
            if other.word_id != item.word_id:
                distractors.append(other.definition)

        random.shuffle(distractors)
        distractors = distractors[:num_options - 1]

        # Create options
        options = [item.definition] + distractors
        random.shuffle(options)

        return {
            "word_id": item.word_id,
            "question": f"What is the meaning of '{item.word}' ({item.part_of_speech})?",
            "options": options,
            "correct_answer": item.definition,
            "correct_index": options.index(item.definition),
        }

    def generate_fill_blank(
        self,
        item: VocabularyItem,
    ) -> Dict[str, Any]:
        """Generate a fill-in-the-blank question."""
        if not item.examples:
            return self.generate_flashcard(item)

        example = random.choice(item.examples)
        # Replace the word with blank
        blanked = re.sub(
            re.escape(item.word),
            "______",
            example,
            flags=re.IGNORECASE
        )

        return {
            "word_id": item.word_id,
            "sentence": blanked,
            "original_sentence": example,
            "answer": item.word,
            "hint": f"{item.part_of_speech}: {item.definition[:50]}...",
        }

    def review(
        self,
        word_id: str,
        quality: int,
        response: str = "",
        time_spent: float = 0.0,
    ) -> ReviewResult:
        """
        Review a vocabulary item using SM-2 algorithm.

        Args:
            word_id: The vocabulary item ID
            quality: Quality of recall (0-5)
            response: User's response
            time_spent: Time spent on review in seconds

        Returns:
            ReviewResult with feedback
        """
        item = self._vocabulary.get(word_id)
        if not item:
            raise ValueError(f"Vocabulary item not found: {word_id}")

        now = datetime.now()

        # SM-2 Algorithm
        if quality >= 3:
            # Correct response
            if item.repetitions == 0:
                item.interval = 1
            elif item.repetitions == 1:
                item.interval = 6
            else:
                item.interval = math.ceil(item.interval * item.ease_factor)

            item.repetitions += 1
            item.correct_reviews += 1
        else:
            # Incorrect response
            item.repetitions = 0
            item.interval = 1
            item.incorrect_reviews += 1

        # Update ease factor
        item.ease_factor = max(
            1.3,
            item.ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        )

        # Update proficiency level
        self._update_proficiency(item)

        # Set next review date
        item.next_review = now + timedelta(days=item.interval)
        item.last_review = now
        item.total_reviews += 1

        # Generate feedback
        feedback = self._generate_feedback(item, quality)

        # Create review result
        result = ReviewResult(
            word_id=word_id,
            correct=quality >= 3,
            quality=quality,
            time_spent_seconds=time_spent,
            response=response,
            expected=item.definition,
            feedback=feedback,
        )

        self._review_history.append(result)

        # Log to episodic memory
        self.episodic.log_event(
            event_type=EventType.PATTERN_LEARNED,
            session_id="vocabulary",
            data={
                "action": "vocabulary_review",
                "word": item.word,
                "quality": quality,
                "correct": quality >= 3,
                "new_proficiency": item.proficiency.value,
                "next_review": item.next_review.isoformat(),
            },
        )

        return result

    def _update_proficiency(self, item: VocabularyItem) -> None:
        """Update proficiency level based on learning progress."""
        accuracy = item.correct_reviews / max(item.total_reviews, 1)

        if item.repetitions >= 5 and accuracy >= 0.9:
            item.proficiency = ProficiencyLevel.MASTERED
        elif item.repetitions >= 3 and accuracy >= 0.8:
            item.proficiency = ProficiencyLevel.PROFICIENT
        elif item.repetitions >= 2 and accuracy >= 0.7:
            item.proficiency = ProficiencyLevel.FAMILIAR
        elif item.repetitions >= 1 or item.total_reviews >= 1:
            item.proficiency = ProficiencyLevel.LEARNING
        else:
            item.proficiency = ProficiencyLevel.NEW

    def _generate_feedback(self, item: VocabularyItem, quality: int) -> str:
        """Generate feedback for a review."""
        if quality >= 4:
            return f"Excellent! You have a strong grasp of '{item.word}'."
        elif quality == 3:
            return f"Good! '{item.word}' means: {item.definition}"
        elif quality == 2:
            return f"Almost! Remember: '{item.word}' means: {item.definition}"
        else:
            return f"Let's review: '{item.word}' ({item.part_of_speech}) means: {item.definition}. Example: {item.examples[0] if item.examples else 'No example available.'}"

    def get_statistics(self) -> Dict[str, Any]:
        """Get vocabulary learning statistics."""
        by_proficiency = {}
        for level in ProficiencyLevel:
            by_proficiency[level.value] = sum(
                1 for item in self._vocabulary.values()
                if item.proficiency == level
            )

        total_reviews = len(self._review_history)
        correct_reviews = sum(1 for r in self._review_history if r.correct)

        return {
            "total_words": len(self._vocabulary),
            "by_proficiency": by_proficiency,
            "total_reviews": total_reviews,
            "correct_reviews": correct_reviews,
            "accuracy": correct_reviews / max(total_reviews, 1),
            "average_time": (
                sum(r.time_spent_seconds for r in self._review_history) / max(total_reviews, 1)
            ),
        }

    def export_progress(self) -> Dict[str, Any]:
        """Export vocabulary progress for persistence."""
        return {
            "vocabulary": {k: v.to_dict() for k, v in self._vocabulary.items()},
            "review_history": [r.to_dict() for r in self._review_history],
            "statistics": self.get_statistics(),
        }

    def import_progress(self, data: Dict[str, Any]) -> None:
        """Import vocabulary progress from persistence."""
        if "vocabulary" in data:
            for word_id, item_data in data["vocabulary"].items():
                self._vocabulary[word_id] = VocabularyItem.from_dict(item_data)


# ============================================================================
# GRAMMAR ENGINE
# ============================================================================

class GrammarRuleType(Enum):
    """Types of grammar rules."""
    WORD_ORDER = "word_order"
    TENSE = "tense"
    ARTICLE = "article"
    PREPOSITION = "preposition"
    SUBJECT_VERB_AGREEMENT = "subject_verb_agreement"
    CONDITIONAL = "conditional"
    PASSIVE_VOICE = "passive_voice"
    RELATIVE_CLAUSE = "relative_clause"
    PUNCTUATION = "punctuation"
    COMMON_ERRORS = "common_errors"


@dataclass
class GrammarRule:
    """A grammar rule with examples and exercises."""
    rule_id: str
    name: str
    category: GrammarRuleType
    description: str
    pattern: str  # Regex or pattern description
    correct_examples: List[str]
    incorrect_examples: List[str]
    explanation: str
    difficulty: int = 1
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "category": self.category.value,
            "description": self.description,
            "pattern": self.pattern,
            "correct_examples": self.correct_examples,
            "incorrect_examples": self.incorrect_examples,
            "explanation": self.explanation,
            "difficulty": self.difficulty,
            "tags": self.tags,
        }


@dataclass
class GrammarError:
    """A detected grammar error."""
    error_id: str
    text: str
    rule_id: str
    message: str
    position: Tuple[int, int]  # (start, end)
    suggestion: str
    severity: str = "error"  # error, warning, suggestion

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "error_id": self.error_id,
            "text": self.text,
            "rule_id": self.rule_id,
            "message": self.message,
            "position": self.position,
            "suggestion": self.suggestion,
            "severity": self.severity,
        }


class GrammarEngine:
    """
    Grammar rules engine for English language learning.

    Features:
    - Grammar rule database
    - Error detection and correction
    - Grammar exercises generation
    - Progress tracking
    """

    def __init__(
        self,
        ltm: Optional[LongTermMemory] = None,
        episodic: Optional[EpisodicMemory] = None,
    ):
        """Initialize grammar engine."""
        self.ltm = ltm or LongTermMemory()
        self.episodic = episodic or EpisodicMemory()
        self._rules: Dict[str, GrammarRule] = {}
        self._initialize_grammar_rules()

    def _initialize_grammar_rules(self) -> None:
        """Initialize with common grammar rules."""
        rules = [
            # Subject-Verb Agreement
            GrammarRule(
                rule_id="grammar_sva_1",
                name="Third Person Singular -s",
                category=GrammarRuleType.SUBJECT_VERB_AGREEMENT,
                description="Add -s to verbs in third person singular",
                pattern=r"^(he|she|it|[\w]+s?)\s+(\w+[^s])$",
                correct_examples=[
                    "She runs every day.",
                    "He plays soccer.",
                    "It works perfectly.",
                ],
                incorrect_examples=[
                    "She run every day.",
                    "He play soccer.",
                    "It work perfectly.",
                ],
                explanation="In present tense, third person singular (he, she, it) requires the verb to end in -s or -es.",
                difficulty=1,
                tags=["beginner", "present_tense", "verbs"],
            ),

            GrammarRule(
                rule_id="grammar_sva_2",
                name="Plural Subjects",
                category=GrammarRuleType.SUBJECT_VERB_AGREEMENT,
                description="Plural subjects take base form verbs",
                pattern=r"^(they|we|[\w]+s)\s+(\w+s)$",
                correct_examples=[
                    "They run every day.",
                    "The dogs play outside.",
                    "We work together.",
                ],
                incorrect_examples=[
                    "They runs every day.",
                    "The dogs plays outside.",
                    "We works together.",
                ],
                explanation="Plural subjects use the base form of the verb without -s.",
                difficulty=1,
                tags=["beginner", "present_tense", "verbs"],
            ),

            # Articles
            GrammarRule(
                rule_id="grammar_art_1",
                name="Indefinite Article A/An",
                category=GrammarRuleType.ARTICLE,
                description="Use 'a' before consonant sounds, 'an' before vowel sounds",
                pattern=r"\b(a|an)\s+([aeiou]|[aeiou]\w+)",
                correct_examples=[
                    "a book",
                    "an apple",
                    "a university",
                    "an hour",
                ],
                incorrect_examples=[
                    "an book",
                    "a apple",
                    "an university",
                    "a hour",
                ],
                explanation="The choice between 'a' and 'an' depends on the SOUND, not the spelling. Use 'an' before vowel sounds.",
                difficulty=1,
                tags=["beginner", "articles", "nouns"],
            ),

            GrammarRule(
                rule_id="grammar_art_2",
                name="Definite Article The",
                category=GrammarRuleType.ARTICLE,
                description="Use 'the' for specific or previously mentioned nouns",
                pattern=r"\bthe\s+\w+",
                correct_examples=[
                    "The sun rises in the east.",
                    "I saw a dog. The dog was brown.",
                    "The United States",
                ],
                incorrect_examples=[
                    "Sun rises in east.",
                    "I saw dog. Dog was brown.",
                ],
                explanation="Use 'the' when referring to something specific, unique, or previously mentioned.",
                difficulty=2,
                tags=["beginner", "articles", "nouns"],
            ),

            # Tenses
            GrammarRule(
                rule_id="grammar_tense_1",
                name="Present Continuous",
                category=GrammarRuleType.TENSE,
                description="Use am/is/are + -ing for ongoing actions",
                pattern=r"\b(am|is|are)\s+\w+ing\b",
                correct_examples=[
                    "I am studying now.",
                    "She is working today.",
                    "They are playing outside.",
                ],
                incorrect_examples=[
                    "I studying now.",
                    "She working today.",
                    "They is playing outside.",
                ],
                explanation="Present continuous requires the auxiliary verb (am/is/are) + verb-ing.",
                difficulty=2,
                tags=["beginner", "present_tense", "continuous"],
            ),

            GrammarRule(
                rule_id="grammar_tense_2",
                name="Simple Past Regular Verbs",
                category=GrammarRuleType.TENSE,
                description="Add -ed to regular verbs for past tense",
                pattern=r"\b\w+ed\b",
                correct_examples=[
                    "I walked to school.",
                    "She played piano.",
                    "They worked hard.",
                ],
                incorrect_examples=[
                    "I walk to school yesterday.",
                    "She play piano last week.",
                    "They work hard yesterday.",
                ],
                explanation="Regular verbs form the past tense by adding -ed. Some verbs double the final consonant.",
                difficulty=1,
                tags=["beginner", "past_tense", "regular_verbs"],
            ),

            GrammarRule(
                rule_id="grammar_tense_3",
                name="Present Perfect",
                category=GrammarRuleType.TENSE,
                description="Use have/has + past participle",
                pattern=r"\b(have|has)\s+\w+ed\b",
                correct_examples=[
                    "I have finished my work.",
                    "She has visited Paris.",
                    "They have learned English.",
                ],
                incorrect_examples=[
                    "I finished my work already.",
                    "She has visit Paris.",
                    "They have learn English.",
                ],
                explanation="Present perfect connects past to present. Use 'have' with I/you/we/they, 'has' with he/she/it.",
                difficulty=3,
                tags=["intermediate", "present_perfect", "perfect_tense"],
            ),

            # Conditionals
            GrammarRule(
                rule_id="grammar_cond_1",
                name="First Conditional",
                category=GrammarRuleType.CONDITIONAL,
                description="If + present, will + base verb",
                pattern=r"\bif\s+\w+\s+\w+s?\s*,\s*\w+\s+will\s+\w+",
                correct_examples=[
                    "If it rains, I will stay home.",
                    "If she comes, we will be happy.",
                    "If you study, you will pass.",
                ],
                incorrect_examples=[
                    "If it will rain, I stay home.",
                    "If she come, we will be happy.",
                    "If you will study, you pass.",
                ],
                explanation="First conditional: If + present simple, will + infinitive. Used for real future possibilities.",
                difficulty=3,
                tags=["intermediate", "conditionals", "future"],
            ),

            GrammarRule(
                rule_id="grammar_cond_2",
                name="Second Conditional",
                category=GrammarRuleType.CONDITIONAL,
                description="If + past, would + base verb",
                pattern=r"\bif\s+\w+\s+\w+ed\s*,\s*\w+\s+would\s+\w+",
                correct_examples=[
                    "If I had money, I would buy a car.",
                    "If she were here, she would help.",
                    "If they knew, they would tell us.",
                ],
                incorrect_examples=[
                    "If I have money, I would buy a car.",
                    "If she was here, she would help.",
                    "If they know, they would tell us.",
                ],
                explanation="Second conditional: If + past simple, would + infinitive. Used for hypothetical situations.",
                difficulty=4,
                tags=["intermediate", "conditionals", "hypothetical"],
            ),

            # Common Errors
            GrammarRule(
                rule_id="grammar_err_1",
                name="Their/There/They're",
                category=GrammarRuleType.COMMON_ERRORS,
                description="Distinguish between their, there, and they're",
                pattern=r"\b(their|there|they're)\b",
                correct_examples=[
                    "Their house is big.",
                    "The book is over there.",
                    "They're going to school.",
                ],
                incorrect_examples=[
                    "There house is big.",
                    "Their going to school.",
                    "The book is over they're.",
                ],
                explanation="'Their' = possessive, 'There' = location, 'They're' = they are",
                difficulty=2,
                tags=["beginner", "homophones", "common_errors"],
            ),

            GrammarRule(
                rule_id="grammar_err_2",
                name="Your/You're",
                category=GrammarRuleType.COMMON_ERRORS,
                description="Distinguish between your and you're",
                pattern=r"\b(your|you're)\b",
                correct_examples=[
                    "Your book is here.",
                    "You're very kind.",
                    "Is this your phone?",
                ],
                incorrect_examples=[
                    "You're book is here.",
                    "Your very kind.",
                    "Is this you're phone?",
                ],
                explanation="'Your' = possessive, 'You're' = you are",
                difficulty=1,
                tags=["beginner", "homophones", "common_errors"],
            ),

            GrammarRule(
                rule_id="grammar_err_3",
                name="Its/It's",
                category=GrammarRuleType.COMMON_ERRORS,
                description="Distinguish between its and it's",
                pattern=r"\b(its|it's)\b",
                correct_examples=[
                    "The cat licked its paw.",
                    "It's a beautiful day.",
                    "The company changed its policy.",
                ],
                incorrect_examples=[
                    "The cat licked it's paw.",
                    "Its a beautiful day.",
                    "The company changed it's policy.",
                ],
                explanation="'Its' = possessive form of it, 'It's' = it is or it has",
                difficulty=2,
                tags=["beginner", "homophones", "common_errors", "possessives"],
            ),

            # Passive Voice
            GrammarRule(
                rule_id="grammar_pass_1",
                name="Passive Voice Formation",
                category=GrammarRuleType.PASSIVE_VOICE,
                description="be + past participle forms passive voice",
                pattern=r"\b(am|is|are|was|were|been)\s+\w+ed\b",
                correct_examples=[
                    "The book was written by her.",
                    "The cake is being made.",
                    "The work has been completed.",
                ],
                incorrect_examples=[
                    "The book written by her.",
                    "The cake is made being.",
                    "The work has completed been.",
                ],
                explanation="Passive voice: subject + be + past participle (+ by agent). Focus is on the action, not the doer.",
                difficulty=4,
                tags=["intermediate", "passive", "voice"],
            ),
        ]

        for rule in rules:
            self._rules[rule.rule_id] = rule

    def add_rule(self, rule: GrammarRule) -> None:
        """Add a grammar rule."""
        self._rules[rule.rule_id] = rule

    def get_rule(self, rule_id: str) -> Optional[GrammarRule]:
        """Get a grammar rule by ID."""
        return self._rules.get(rule_id)

    def get_rules_by_category(self, category: GrammarRuleType) -> List[GrammarRule]:
        """Get rules by category."""
        return [r for r in self._rules.values() if r.category == category]

    def get_rules_by_difficulty(self, min_diff: int, max_diff: int) -> List[GrammarRule]:
        """Get rules by difficulty range."""
        return [r for r in self._rules.values() if min_diff <= r.difficulty <= max_diff]

    def check_text(self, text: str) -> List[GrammarError]:
        """Check text for grammar errors."""
        errors = []

        # Check each rule
        for rule in self._rules.values():
            rule_errors = self._check_rule(text, rule)
            errors.extend(rule_errors)

        return errors

    def _check_rule(self, text: str, rule: GrammarRule) -> List[GrammarError]:
        """Check text against a specific rule."""
        errors = []
        text_lower = text.lower()

        # Check for incorrect patterns based on incorrect examples
        for incorrect in rule.incorrect_examples:
            # Simple substring matching (could be enhanced with NLP)
            incorrect_lower = incorrect.lower()
            if incorrect_lower in text_lower:
                # Find position
                start = text_lower.find(incorrect_lower)
                end = start + len(incorrect_lower)

                # Find corresponding correct form
                correct = rule.correct_examples[
                    rule.incorrect_examples.index(incorrect)
                ] if incorrect in rule.incorrect_examples else ""

                error = GrammarError(
                    error_id=f"err_{uuid.uuid4().hex[:8]}",
                    text=incorrect,
                    rule_id=rule.rule_id,
                    message=f"Grammar error: {rule.description}",
                    position=(start, end),
                    suggestion=f"Consider: {correct}",
                    severity="error",
                )
                errors.append(error)

        return errors

    def generate_exercise(
        self,
        rule: GrammarRule,
        exercise_type: str = "multiple_choice",
    ) -> Dict[str, Any]:
        """Generate a grammar exercise."""
        if exercise_type == "multiple_choice":
            return self._generate_mc_exercise(rule)
        elif exercise_type == "fill_blank":
            return self._generate_fill_blank_exercise(rule)
        elif exercise_type == "error_correction":
            return self._generate_error_correction_exercise(rule)
        else:
            return self._generate_mc_exercise(rule)

    def _generate_mc_exercise(self, rule: GrammarRule) -> Dict[str, Any]:
        """Generate a multiple choice exercise."""
        # Pick a correct example and create options
        correct = random.choice(rule.correct_examples)
        incorrect = random.sample(rule.incorrect_examples, min(3, len(rule.incorrect_examples)))

        options = [correct] + incorrect
        random.shuffle(options)

        return {
            "exercise_id": f"ex_{uuid.uuid4().hex[:8]}",
            "rule_id": rule.rule_id,
            "type": "multiple_choice",
            "question": f"Which sentence is grammatically correct?\nRule: {rule.description}",
            "options": options,
            "correct_answer": correct,
            "correct_index": options.index(correct),
            "explanation": rule.explanation,
            "difficulty": rule.difficulty,
        }

    def _generate_fill_blank_exercise(self, rule: GrammarRule) -> Dict[str, Any]:
        """Generate a fill-in-the-blank exercise."""
        correct_example = random.choice(rule.correct_examples)

        # Find words to blank out
        words_to_blank = []

        # For article rules, blank articles
        if rule.category == GrammarRuleType.ARTICLE:
            articles = re.findall(r"\b(a|an|the)\b", correct_example)
            if articles:
                words_to_blank = articles

        # For SVA, blank verb endings
        elif rule.category == GrammarRuleType.SUBJECT_VERB_AGREEMENT:
            verbs = re.findall(r"\b\w+s\b", correct_example)
            if verbs:
                words_to_blank = verbs

        if not words_to_blank:
            # Generic blank: remove a random word
            words = correct_example.split()
            if len(words) > 2:
                blank_idx = random.randint(0, len(words) - 1)
                words_to_blank = [words[blank_idx]]

        # Create blanked sentence
        blanked = correct_example
        for word in words_to_blank:
            blanked = blanked.replace(word, "_____", 1)

        return {
            "exercise_id": f"ex_{uuid.uuid4().hex[:8]}",
            "rule_id": rule.rule_id,
            "type": "fill_blank",
            "question": f"Fill in the blank:\n{blanked}",
            "answer": words_to_blank[0] if words_to_blank else "",
            "full_answer": correct_example,
            "explanation": rule.explanation,
            "difficulty": rule.difficulty,
        }

    def _generate_error_correction_exercise(self, rule: GrammarRule) -> Dict[str, Any]:
        """Generate an error correction exercise."""
        incorrect = random.choice(rule.incorrect_examples)
        correct_idx = rule.incorrect_examples.index(incorrect)
        correct = rule.correct_examples[correct_idx]

        return {
            "exercise_id": f"ex_{uuid.uuid4().hex[:8]}",
            "rule_id": rule.rule_id,
            "type": "error_correction",
            "question": f"Find and correct the error:\n{incorrect}",
            "incorrect_sentence": incorrect,
            "correct_answer": correct,
            "explanation": rule.explanation,
            "difficulty": rule.difficulty,
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Get grammar learning statistics."""
        by_category = {}
        for cat in GrammarRuleType:
            by_category[cat.value] = sum(
                1 for r in self._rules.values() if r.category == cat
            )

        by_difficulty = {}
        for i in range(1, 6):
            by_difficulty[i] = sum(
                1 for r in self._rules.values() if r.difficulty == i
            )

        return {
            "total_rules": len(self._rules),
            "by_category": by_category,
            "by_difficulty": by_difficulty,
        }


# ============================================================================
# READING COMPREHENSION
# ============================================================================

@dataclass
class ReadingPassage:
    """A reading comprehension passage."""
    passage_id: str
    title: str
    text: str
    difficulty: int  # 1-5
    word_count: int
    topic: str
    vocabulary_level: str  # beginner, intermediate, advanced
    questions: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "passage_id": self.passage_id,
            "title": self.title,
            "text": self.text,
            "difficulty": self.difficulty,
            "word_count": self.word_count,
            "topic": self.topic,
            "vocabulary_level": self.vocabulary_level,
            "questions": self.questions,
        }


@dataclass
class ReadingResult:
    """Result of reading comprehension assessment."""
    result_id: str
    passage_id: str
    score: float
    correct_answers: int
    total_questions: int
    time_spent_seconds: float
    details: List[Dict[str, Any]]
    completed_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "result_id": self.result_id,
            "passage_id": self.passage_id,
            "score": self.score,
            "correct_answers": self.correct_answers,
            "total_questions": self.total_questions,
            "time_spent_seconds": self.time_spent_seconds,
            "details": self.details,
            "completed_at": self.completed_at.isoformat(),
        }


class ReadingComprehension:
    """
    Reading comprehension system for English learning.

    Features:
    - Multiple difficulty levels
    - Various question types
    - Progress tracking
    - Vocabulary integration
    """

    def __init__(
        self,
        ltm: Optional[LongTermMemory] = None,
        episodic: Optional[EpisodicMemory] = None,
    ):
        """Initialize reading comprehension system."""
        self.ltm = ltm or LongTermMemory()
        self.episodic = episodic or EpisodicMemory()
        self._passages: Dict[str, ReadingPassage] = {}
        self._results: List[ReadingResult] = []
        self._initialize_passages()

    def _initialize_passages(self) -> None:
        """Initialize with sample passages."""
        passages = [
            ReadingPassage(
                passage_id="read_001",
                title="The Cat and the Mouse",
                text="""Once upon a time, there was a cat who lived in a small house. The cat was very lazy and liked to sleep all day. One day, a little mouse came into the house. The mouse was looking for food. The cat saw the mouse but was too lazy to catch it. The mouse found some cheese and left happily. The cat continued to sleep.""",
                difficulty=1,
                word_count=68,
                topic="story",
                vocabulary_level="beginner",
                questions=[
                    {
                        "question": "What did the cat like to do?",
                        "options": ["Play", "Sleep", "Eat", "Run"],
                        "correct": 1,
                        "type": "detail",
                    },
                    {
                        "question": "Why did the mouse come to the house?",
                        "options": ["To play", "To sleep", "To find food", "To meet the cat"],
                        "correct": 2,
                        "type": "detail",
                    },
                    {
                        "question": "Did the cat catch the mouse?",
                        "options": ["Yes", "No", "Maybe", "Not mentioned"],
                        "correct": 1,
                        "type": "detail",
                    },
                    {
                        "question": "What is the main idea of the story?",
                        "options": ["Cats are good hunters", "Being lazy has consequences", "Mice like cheese", "Houses are comfortable"],
                        "correct": 1,
                        "type": "main_idea",
                    },
                ],
            ),
            ReadingPassage(
                passage_id="read_002",
                title="The Water Cycle",
                text="""The water cycle is the continuous movement of water on Earth. It begins when the sun heats up water in oceans and lakes. The water turns into vapor and rises into the air. This process is called evaporation. As the vapor rises higher, it cools down and forms clouds. This is called condensation. When the clouds become heavy with water, it rains or snows. This is called precipitation. The water flows back to oceans and lakes, and the cycle begins again.""",
                difficulty=2,
                word_count=87,
                topic="science",
                vocabulary_level="intermediate",
                questions=[
                    {
                        "question": "What is evaporation?",
                        "options": ["Water turning into vapor", "Water freezing", "Rain falling", "Clouds forming"],
                        "correct": 0,
                        "type": "detail",
                    },
                    {
                        "question": "What happens during condensation?",
                        "options": ["Water evaporates", "Clouds form", "Rain falls", "Water flows"],
                        "correct": 1,
                        "type": "detail",
                    },
                    {
                        "question": "What is precipitation?",
                        "options": ["Water rising", "Clouds forming", "Rain or snow falling", "Sun heating water"],
                        "correct": 2,
                        "type": "detail",
                    },
                    {
                        "question": "What is the main topic of this passage?",
                        "options": ["Weather patterns", "The water cycle", "Ocean currents", "Climate change"],
                        "correct": 1,
                        "type": "main_idea",
                    },
                ],
            ),
            ReadingPassage(
                passage_id="read_003",
                title="The Benefits of Exercise",
                text="""Regular exercise has numerous benefits for both physical and mental health. Physically, exercise strengthens the heart, improves circulation, and helps maintain a healthy weight. It also increases muscle strength and flexibility. Mentally, exercise reduces stress and anxiety by releasing endorphins, which are natural mood elevators. Studies have shown that people who exercise regularly sleep better and have more energy throughout the day. Additionally, exercise can help prevent chronic diseases such as diabetes and heart disease.""",
                difficulty=3,
                word_count=78,
                topic="health",
                vocabulary_level="intermediate",
                questions=[
                    {
                        "question": "What are endorphins?",
                        "options": ["Types of exercise", "Natural mood elevators", "Chronic diseases", "Muscle builders"],
                        "correct": 1,
                        "type": "detail",
                    },
                    {
                        "question": "How does exercise benefit mental health?",
                        "options": ["It increases weight", "It reduces stress and anxiety", "It causes diabetes", "It weakens the heart"],
                        "correct": 1,
                        "type": "detail",
                    },
                    {
                        "question": "What chronic diseases can exercise help prevent?",
                        "options": ["Cancer and flu", "Diabetes and heart disease", "Cold and headache", "None"],
                        "correct": 1,
                        "type": "detail",
                    },
                    {
                        "question": "What is the author's purpose in this passage?",
                        "options": ["To sell exercise equipment", "To explain the benefits of exercise", "To compare different exercises", "To describe chronic diseases"],
                        "correct": 1,
                        "type": "purpose",
                    },
                ],
            ),
        ]

        for passage in passages:
            self._passages[passage.passage_id] = passage

    def add_passage(
        self,
        title: str,
        text: str,
        difficulty: int,
        topic: str,
        questions: List[Dict[str, Any]],
        vocabulary_level: str = "intermediate",
    ) -> ReadingPassage:
        """Add a new reading passage."""
        passage = ReadingPassage(
            passage_id=f"read_{uuid.uuid4().hex[:8]}",
            title=title,
            text=text,
            difficulty=difficulty,
            word_count=len(text.split()),
            topic=topic,
            vocabulary_level=vocabulary_level,
            questions=questions,
        )
        self._passages[passage.passage_id] = passage
        return passage

    def get_passage(self, passage_id: str) -> Optional[ReadingPassage]:
        """Get a passage by ID."""
        return self._passages.get(passage_id)

    def get_passages_by_difficulty(self, difficulty: int) -> List[ReadingPassage]:
        """Get passages by difficulty level."""
        return [p for p in self._passages.values() if p.difficulty == difficulty]

    def get_recommended_passage(
        self,
        current_level: int,
        topics: Optional[List[str]] = None,
    ) -> Optional[ReadingPassage]:
        """Get a recommended passage based on level and topics."""
        candidates = [
            p for p in self._passages.values()
            if p.difficulty <= current_level + 1
        ]

        if topics:
            topic_matches = [p for p in candidates if p.topic in topics]
            if topic_matches:
                candidates = topic_matches

        if candidates:
            return random.choice(candidates)
        return None

    def assess(
        self,
        passage_id: str,
        answers: List[int],
        time_spent: float = 0.0,
    ) -> ReadingResult:
        """Assess reading comprehension answers."""
        passage = self._passages.get(passage_id)
        if not passage:
            raise ValueError(f"Passage not found: {passage_id}")

        correct_count = 0
        details = []

        for i, (question, answer) in enumerate(zip(passage.questions, answers)):
            is_correct = answer == question["correct"]
            if is_correct:
                correct_count += 1

            details.append({
                "question_num": i + 1,
                "question": question["question"],
                "user_answer": question["options"][answer] if answer < len(question["options"]) else "N/A",
                "correct_answer": question["options"][question["correct"]],
                "is_correct": is_correct,
                "type": question.get("type", "detail"),
            })

        score = correct_count / len(passage.questions)

        result = ReadingResult(
            result_id=f"result_{uuid.uuid4().hex[:8]}",
            passage_id=passage_id,
            score=score,
            correct_answers=correct_count,
            total_questions=len(passage.questions),
            time_spent_seconds=time_spent,
            details=details,
        )

        self._results.append(result)

        # Log to episodic memory
        self.episodic.log_event(
            event_type=EventType.PATTERN_LEARNED,
            session_id="reading",
            data={
                "action": "reading_assessment",
                "passage_id": passage_id,
                "score": score,
                "correct": correct_count,
                "total": len(passage.questions),
            },
        )

        return result

    def get_statistics(self) -> Dict[str, Any]:
        """Get reading comprehension statistics."""
        if not self._results:
            return {
                "total_passages": len(self._passages),
                "total_attempts": 0,
                "average_score": 0,
            }

        avg_score = sum(r.score for r in self._results) / len(self._results)
        avg_time = sum(r.time_spent_seconds for r in self._results) / len(self._results)

        return {
            "total_passages": len(self._passages),
            "total_attempts": len(self._results),
            "average_score": avg_score,
            "average_time": avg_time,
            "best_score": max(r.score for r in self._results),
        }


# ============================================================================
# WRITING ASSESSMENT
# ============================================================================

@dataclass
class WritingPrompt:
    """A writing prompt for assessment."""
    prompt_id: str
    prompt: str
    topic: str
    difficulty: int
    word_limit: Tuple[int, int]  # (min, max)
    criteria: List[str]  # Assessment criteria
    time_limit_minutes: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "prompt_id": self.prompt_id,
            "prompt": self.prompt,
            "topic": self.topic,
            "difficulty": self.difficulty,
            "word_limit": self.word_limit,
            "criteria": self.criteria,
            "time_limit_minutes": self.time_limit_minutes,
        }


@dataclass
class WritingAssessment:
    """Result of writing assessment."""
    assessment_id: str
    prompt_id: str
    text: str
    word_count: int
    scores: Dict[str, float]  # criterion -> score
    overall_score: float
    feedback: str
    suggestions: List[str]
    grammar_errors: List[Dict[str, Any]]
    assessed_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "assessment_id": self.assessment_id,
            "prompt_id": self.prompt_id,
            "text": self.text,
            "word_count": self.word_count,
            "scores": self.scores,
            "overall_score": self.overall_score,
            "feedback": self.feedback,
            "suggestions": self.suggestions,
            "grammar_errors": self.grammar_errors,
            "assessed_at": self.assessed_at.isoformat(),
        }


class WritingAssessor:
    """
    Writing assessment system for English learning.

    Features:
    - Multiple assessment criteria
    - Grammar checking integration
    - Feedback generation
    - Progress tracking
    """

    DEFAULT_CRITERIA = [
        "grammar",
        "vocabulary",
        "organization",
        "coherence",
        "content",
    ]

    def __init__(
        self,
        ltm: Optional[LongTermMemory] = None,
        episodic: Optional[EpisodicMemory] = None,
        grammar_engine: Optional[GrammarEngine] = None,
    ):
        """Initialize writing assessor."""
        self.ltm = ltm or LongTermMemory()
        self.episodic = episodic or EpisodicMemory()
        self.grammar_engine = grammar_engine or GrammarEngine()
        self._prompts: Dict[str, WritingPrompt] = {}
        self._assessments: List[WritingAssessment] = []
        self._initialize_prompts()

    def _initialize_prompts(self) -> None:
        """Initialize with sample writing prompts."""
        prompts = [
            WritingPrompt(
                prompt_id="write_001",
                prompt="Write about your favorite hobby. Explain why you enjoy it and how often you do it.",
                topic="hobbies",
                difficulty=1,
                word_limit=(50, 150),
                criteria=["grammar", "vocabulary", "organization"],
                time_limit_minutes=15,
            ),
            WritingPrompt(
                prompt_id="write_002",
                prompt="Describe a memorable trip you have taken. Include details about where you went, what you did, and why it was memorable.",
                topic="travel",
                difficulty=2,
                word_limit=(100, 250),
                criteria=["grammar", "vocabulary", "organization", "coherence"],
                time_limit_minutes=25,
            ),
            WritingPrompt(
                prompt_id="write_003",
                prompt="Do you agree or disagree with the statement: 'Social media has more positive effects than negative effects on society.' Support your opinion with reasons and examples.",
                topic="opinion",
                difficulty=3,
                word_limit=(150, 300),
                criteria=self.DEFAULT_CRITERIA,
                time_limit_minutes=35,
            ),
            WritingPrompt(
                prompt_id="write_004",
                prompt="Write a story that begins with: 'The door slowly opened, revealing something unexpected...'",
                topic="creative",
                difficulty=3,
                word_limit=(200, 400),
                criteria=["grammar", "vocabulary", "organization", "coherence", "creativity"],
                time_limit_minutes=40,
            ),
        ]

        for prompt in prompts:
            self._prompts[prompt.prompt_id] = prompt

    def add_prompt(
        self,
        prompt: str,
        topic: str,
        difficulty: int,
        word_limit: Tuple[int, int],
        criteria: Optional[List[str]] = None,
        time_limit: Optional[int] = None,
    ) -> WritingPrompt:
        """Add a new writing prompt."""
        wp = WritingPrompt(
            prompt_id=f"write_{uuid.uuid4().hex[:8]}",
            prompt=prompt,
            topic=topic,
            difficulty=difficulty,
            word_limit=word_limit,
            criteria=criteria or self.DEFAULT_CRITERIA,
            time_limit_minutes=time_limit,
        )
        self._prompts[wp.prompt_id] = wp
        return wp

    def get_prompt(self, prompt_id: str) -> Optional[WritingPrompt]:
        """Get a writing prompt by ID."""
        return self._prompts.get(prompt_id)

    def get_prompts_by_difficulty(self, difficulty: int) -> List[WritingPrompt]:
        """Get prompts by difficulty level."""
        return [p for p in self._prompts.values() if p.difficulty == difficulty]

    def assess(
        self,
        prompt_id: str,
        text: str,
    ) -> WritingAssessment:
        """Assess a writing sample."""
        prompt = self._prompts.get(prompt_id)
        if not prompt:
            raise ValueError(f"Prompt not found: {prompt_id}")

        word_count = len(text.split())

        # Check grammar
        grammar_errors = [
            err.to_dict()
            for err in self.grammar_engine.check_text(text)
        ]

        # Score each criterion
        scores = {}
        for criterion in prompt.criteria:
            scores[criterion] = self._score_criterion(text, criterion, prompt)

        # Calculate overall score
        overall = sum(scores.values()) / len(scores)

        # Generate feedback
        feedback = self._generate_feedback(scores, word_count, prompt)
        suggestions = self._generate_suggestions(scores, grammar_errors)

        assessment = WritingAssessment(
            assessment_id=f"assess_{uuid.uuid4().hex[:8]}",
            prompt_id=prompt_id,
            text=text,
            word_count=word_count,
            scores=scores,
            overall_score=overall,
            feedback=feedback,
            suggestions=suggestions,
            grammar_errors=grammar_errors,
        )

        self._assessments.append(assessment)

        # Log to episodic memory
        self.episodic.log_event(
            event_type=EventType.PATTERN_LEARNED,
            session_id="writing",
            data={
                "action": "writing_assessment",
                "prompt_id": prompt_id,
                "word_count": word_count,
                "overall_score": overall,
                "grammar_errors": len(grammar_errors),
            },
        )

        return assessment

    def _score_criterion(
        self,
        text: str,
        criterion: str,
        prompt: WritingPrompt,
    ) -> float:
        """Score a specific criterion (0.0 to 1.0)."""
        word_count = len(text.split())
        min_words, max_words = prompt.word_limit

        if criterion == "grammar":
            errors = self.grammar_engine.check_text(text)
            error_rate = len(errors) / max(word_count / 10, 1)
            return max(0, 1 - error_rate * 0.2)

        elif criterion == "vocabulary":
            # Check word variety
            words = text.lower().split()
            unique_ratio = len(set(words)) / max(len(words), 1)
            # Check for advanced vocabulary
            advanced_words = sum(1 for w in words if len(w) > 7)
            advanced_ratio = advanced_words / max(len(words), 1)
            return min(1, unique_ratio * 0.6 + advanced_ratio * 2)

        elif criterion == "organization":
            # Check for paragraph structure
            paragraphs = text.split("\n\n")
            has_structure = len(paragraphs) >= 2
            # Check for transition words
            transitions = ["first", "second", "finally", "however", "therefore", "moreover", "in addition"]
            has_transitions = any(t in text.lower() for t in transitions)
            return (0.5 if has_structure else 0.3) + (0.3 if has_transitions else 0) + 0.2

        elif criterion == "coherence":
            # Check sentence variety
            sentences = re.split(r'[.!?]+', text)
            sentences = [s.strip() for s in sentences if s.strip()]
            if not sentences:
                return 0.3
            avg_sent_len = sum(len(s.split()) for s in sentences) / len(sentences)
            variety = len(set(len(s.split()) for s in sentences)) / max(len(sentences), 1)
            return min(1, (avg_sent_len / 15) * 0.5 + variety * 0.5)

        elif criterion == "content":
            # Check word count compliance
            if min_words <= word_count <= max_words:
                length_score = 1.0
            elif word_count < min_words:
                length_score = word_count / min_words
            else:
                length_score = max(0.7, 1 - (word_count - max_words) / max_words)

            # Check topic relevance (simple keyword matching)
            topic_keywords = prompt.topic.lower().split()
            text_lower = text.lower()
            relevance = sum(1 for k in topic_keywords if k in text_lower) / max(len(topic_keywords), 1)

            return length_score * 0.5 + relevance * 0.5 + 0.0

        elif criterion == "creativity":
            # Check for unique vocabulary and expressions
            words = text.lower().split()
            unique_words = set(words)
            creativity_ratio = len(unique_words) / max(len(words), 1)
            return min(1, creativity_ratio * 1.2)

        return 0.5

    def _generate_feedback(
        self,
        scores: Dict[str, float],
        word_count: int,
        prompt: WritingPrompt,
    ) -> str:
        """Generate overall feedback."""
        min_words, max_words = prompt.word_limit

        # Find strengths and weaknesses
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        strengths = [s[0] for s in sorted_scores[:2]]
        weaknesses = [s[0] for s in sorted_scores[-2:] if s[1] < 0.7]

        feedback_parts = []

        # Overall comment
        overall = sum(scores.values()) / len(scores)
        if overall >= 0.8:
            feedback_parts.append("Excellent work! Your writing demonstrates strong skills.")
        elif overall >= 0.6:
            feedback_parts.append("Good effort! Your writing shows competence with room for improvement.")
        else:
            feedback_parts.append("Keep practicing! There are several areas for improvement.")

        # Strengths
        if strengths:
            feedback_parts.append(f"Strengths: {', '.join(strengths)}.")

        # Weaknesses
        if weaknesses:
            feedback_parts.append(f"Areas to improve: {', '.join(weaknesses)}.")

        # Word count feedback
        if word_count < min_words:
            feedback_parts.append(f"Your response is below the minimum word count ({word_count}/{min_words}).")
        elif word_count > max_words:
            feedback_parts.append(f"Your response exceeds the word limit ({word_count}/{max_words}).")

        return " ".join(feedback_parts)

    def _generate_suggestions(
        self,
        scores: Dict[str, float],
        grammar_errors: List[Dict[str, Any]],
    ) -> List[str]:
        """Generate improvement suggestions."""
        suggestions = []

        for criterion, score in scores.items():
            if score < 0.6:
                if criterion == "grammar":
                    suggestions.append("Review basic grammar rules and proofread carefully.")
                elif criterion == "vocabulary":
                    suggestions.append("Try using more varied vocabulary and avoid repetition.")
                elif criterion == "organization":
                    suggestions.append("Structure your writing with clear paragraphs and transitions.")
                elif criterion == "coherence":
                    suggestions.append("Connect your ideas more clearly with linking words.")
                elif criterion == "content":
                    suggestions.append("Make sure to fully address the prompt and meet word requirements.")

        if grammar_errors:
            error_types = set(e.get("rule_id", "") for e in grammar_errors[:3])
            for error_type in list(error_types)[:2]:
                suggestions.append(f"Pay attention to grammar rules, particularly: {error_type}")

        return suggestions[:5]  # Limit to 5 suggestions

    def get_statistics(self) -> Dict[str, Any]:
        """Get writing assessment statistics."""
        if not self._assessments:
            return {
                "total_prompts": len(self._prompts),
                "total_submissions": 0,
                "average_score": 0,
            }

        avg_score = sum(a.overall_score for a in self._assessments) / len(self._assessments)
        avg_word_count = sum(a.word_count for a in self._assessments) / len(self._assessments)

        # Average by criterion
        criterion_scores = {}
        for criterion in self.DEFAULT_CRITERIA:
            scores = [a.scores.get(criterion, 0) for a in self._assessments if criterion in a.scores]
            if scores:
                criterion_scores[criterion] = sum(scores) / len(scores)

        return {
            "total_prompts": len(self._prompts),
            "total_submissions": len(self._assessments),
            "average_score": avg_score,
            "average_word_count": avg_word_count,
            "average_by_criterion": criterion_scores,
        }


# ============================================================================
# ENGLISH DOMAIN (MAIN CLASS)
# ============================================================================

class EnglishDomain:
    """
    Main English Language Learning Domain.

    Integrates all English learning components:
    - Vocabulary training
    - Grammar rules
    - Reading comprehension
    - Writing assessment
    """

    def __init__(
        self,
        ltm: Optional[LongTermMemory] = None,
        episodic: Optional[EpisodicMemory] = None,
    ):
        """Initialize English domain."""
        self.ltm = ltm or LongTermMemory()
        self.episodic = episodic or EpisodicMemory()

        # Initialize components
        self.vocabulary = VocabularyTrainer(self.ltm, self.episodic)
        self.grammar = GrammarEngine(self.ltm, self.episodic)
        self.reading = ReadingComprehension(self.ltm, self.episodic)
        self.writing = WritingAssessor(self.ltm, self.episodic, self.grammar)

        # Learning progress
        self._sessions: List[Dict[str, Any]] = []

    def create_learning_session(
        self,
        focus: str = "mixed",
        duration_minutes: int = 30,
    ) -> Dict[str, Any]:
        """Create a learning session plan."""
        session_id = f"session_{uuid.uuid4().hex[:8]}"

        activities = []

        if focus in ["vocabulary", "mixed"]:
            due = self.vocabulary.get_due_reviews(limit=10)
            new = self.vocabulary.get_new_vocabulary(limit=5)
            activities.append({
                "type": "vocabulary_review",
                "count": len(due),
                "new_items": len(new),
                "items": due[:5],
            })

        if focus in ["grammar", "mixed"]:
            rules = self.grammar.get_rules_by_difficulty(1, 3)[:5]
            activities.append({
                "type": "grammar_practice",
                "count": len(rules),
                "rules": [r.rule_id for r in rules],
            })

        if focus in ["reading", "mixed"]:
            passage = self.reading.get_recommended_passage(current_level=2)
            if passage:
                activities.append({
                    "type": "reading",
                    "passage_id": passage.passage_id,
                    "title": passage.title,
                    "questions": len(passage.questions),
                })

        session = {
            "session_id": session_id,
            "focus": focus,
            "duration_minutes": duration_minutes,
            "activities": activities,
            "created_at": datetime.now().isoformat(),
        }

        self._sessions.append(session)
        return session

    def get_overall_statistics(self) -> Dict[str, Any]:
        """Get overall English learning statistics."""
        return {
            "vocabulary": self.vocabulary.get_statistics(),
            "grammar": self.grammar.get_statistics(),
            "reading": self.reading.get_statistics(),
            "writing": self.writing.get_statistics(),
            "total_sessions": len(self._sessions),
        }

    def export_progress(self) -> Dict[str, Any]:
        """Export all progress for persistence."""
        return {
            "vocabulary": self.vocabulary.export_progress(),
            "grammar_rules": {k: v.to_dict() for k, v in self.grammar._rules.items()},
            "reading_results": [r.to_dict() for r in self.reading._results],
            "writing_assessments": [a.to_dict() for a in self.writing._assessments],
            "sessions": self._sessions,
        }

    def import_progress(self, data: Dict[str, Any]) -> None:
        """Import progress from persistence."""
        if "vocabulary" in data:
            self.vocabulary.import_progress(data["vocabulary"])
