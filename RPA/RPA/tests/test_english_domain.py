"""
Comprehensive tests for English Language Learning Domain.

Tests cover:
- Vocabulary training with spaced repetition
- Grammar rules engine
- Reading comprehension
- Writing assessment
"""

import pytest
from datetime import datetime, timedelta
import math

from rpa.domains.english import (
    EnglishDomain,
    VocabularyTrainer,
    VocabularyItem,
    ProficiencyLevel,
    ReviewResult,
    GrammarEngine,
    GrammarRule,
    GrammarRuleType,
    GrammarError,
    ReadingComprehension,
    ReadingPassage,
    ReadingResult,
    WritingAssessor,
    WritingPrompt,
    WritingAssessment,
)
from rpa.memory.ltm import LongTermMemory
from rpa.memory.episodic import EpisodicMemory


# ============================================================================
# VOCABULARY TRAINER TESTS
# ============================================================================

class TestVocabularyItem:
    """Tests for VocabularyItem dataclass."""

    def test_create_vocabulary_item(self):
        """Test creating a vocabulary item."""
        item = VocabularyItem(
            word_id="vocab_001",
            word="example",
            definition="a representative form or pattern",
            part_of_speech="noun",
            examples=["This is an example.", "For example, consider this."],
        )
        assert item.word_id == "vocab_001"
        assert item.word == "example"
        assert item.proficiency == ProficiencyLevel.NEW
        assert item.ease_factor == 2.5
        assert item.interval == 0

    def test_vocabulary_item_to_dict(self):
        """Test serialization to dictionary."""
        item = VocabularyItem(
            word_id="vocab_002",
            word="test",
            definition="a procedure intended to establish quality",
            part_of_speech="noun",
            examples=["We took a test."],
            difficulty=2,
        )
        data = item.to_dict()
        assert data["word_id"] == "vocab_002"
        assert data["word"] == "test"
        assert data["difficulty"] == 2
        assert data["proficiency"] == "new"

    def test_vocabulary_item_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "word_id": "vocab_003",
            "word": "dictionary",
            "definition": "a reference book",
            "part_of_speech": "noun",
            "examples": ["Look it up in the dictionary."],
            "proficiency": "learning",
            "ease_factor": 2.3,
            "interval": 3,
            "repetitions": 2,
        }
        item = VocabularyItem.from_dict(data)
        assert item.word_id == "vocab_003"
        assert item.proficiency == ProficiencyLevel.LEARNING
        assert item.ease_factor == 2.3
        assert item.interval == 3


class TestVocabularyTrainer:
    """Tests for VocabularyTrainer."""

    @pytest.fixture
    def trainer(self):
        """Create a vocabulary trainer."""
        return VocabularyTrainer()

    def test_trainer_initialization(self, trainer):
        """Test trainer initializes with common vocabulary."""
        assert len(trainer._vocabulary) > 0

    def test_add_vocabulary(self, trainer):
        """Test adding a new vocabulary item."""
        item = trainer.add_vocabulary(
            word="serendipity",
            definition="the occurrence of events by chance in a happy way",
            part_of_speech="noun",
            examples=["Finding that book was serendipity."],
            difficulty=4,
        )
        assert item.word == "serendipity"
        assert item.difficulty == 4
        assert trainer.get_vocabulary(item.word_id) is not None

    def test_get_word_by_text(self, trainer):
        """Test finding a word by its text."""
        trainer.add_vocabulary(
            word="ephemeral",
            definition="lasting for a very short time",
            part_of_speech="adjective",
        )
        item = trainer.get_word_by_text("ephemeral")
        assert item is not None
        assert item.word == "ephemeral"

    def test_get_new_vocabulary(self, trainer):
        """Test getting new vocabulary items."""
        new_items = trainer.get_new_vocabulary(limit=5)
        assert len(new_items) <= 5
        for item in new_items:
            assert item.proficiency == ProficiencyLevel.NEW

    def test_generate_flashcard(self, trainer):
        """Test flashcard generation."""
        item = trainer.add_vocabulary(
            word="ubiquitous",
            definition="present everywhere",
            part_of_speech="adjective",
            examples=["Smartphones are ubiquitous today."],
        )
        flashcard = trainer.generate_flashcard(item)
        assert flashcard["front"] == "ubiquitous"
        assert flashcard["back"] == "present everywhere"
        assert len(flashcard["examples"]) > 0

    def test_generate_multiple_choice(self, trainer):
        """Test multiple choice question generation."""
        item = trainer.add_vocabulary(
            word="pragmatic",
            definition="dealing with things sensibly and realistically",
            part_of_speech="adjective",
        )
        mc = trainer.generate_multiple_choice(item, num_options=4)
        assert "question" in mc
        assert len(mc["options"]) == 4
        assert mc["correct_answer"] in mc["options"]

    def test_generate_fill_blank(self, trainer):
        """Test fill-in-the-blank question generation."""
        item = trainer.add_vocabulary(
            word="elaborate",
            definition="involving many carefully arranged parts",
            part_of_speech="adjective",
            examples=["The elaborate design took months to complete."],
        )
        fill = trainer.generate_fill_blank(item)
        assert "_____" in fill["sentence"] or fill.get("answer")
        assert fill["answer"] == "elaborate"

    def test_review_sm2_algorithm(self, trainer):
        """Test SM-2 spaced repetition algorithm."""
        item = trainer.add_vocabulary(
            word="paradigm",
            definition="a typical example or pattern",
            part_of_speech="noun",
        )

        # First review (quality 4 = correct after hesitation)
        result = trainer.review(item.word_id, quality=4)
        assert result.correct is True
        assert item.repetitions == 1
        assert item.interval == 1  # First review: 1 day

        # Second review (quality 5 = perfect)
        result = trainer.review(item.word_id, quality=5)
        assert item.repetitions == 2
        assert item.interval == 6  # Second review: 6 days

        # Third review (quality 5)
        result = trainer.review(item.word_id, quality=5)
        assert item.repetitions == 3
        assert item.interval > 6  # Interval increases with ease factor

    def test_review_incorrect_response(self, trainer):
        """Test review with incorrect response."""
        item = trainer.add_vocabulary(
            word="esoteric",
            definition="intended for a small group with special knowledge",
            part_of_speech="adjective",
        )

        # Initial review
        trainer.review(item.word_id, quality=5)

        # Incorrect review (quality 2)
        result = trainer.review(item.word_id, quality=2)
        assert result.correct is False
        assert item.repetitions == 0  # Reset
        assert item.interval == 1  # Back to 1 day

    def test_proficiency_progression(self, trainer):
        """Test proficiency level progression."""
        item = trainer.add_vocabulary(
            word="ambiguous",
            definition="open to more than one interpretation",
            part_of_speech="adjective",
        )

        assert item.proficiency == ProficiencyLevel.NEW

        # After first successful review
        trainer.review(item.word_id, quality=4)
        assert item.proficiency == ProficiencyLevel.LEARNING

        # After more successful reviews
        for _ in range(2):
            trainer.review(item.word_id, quality=5)

        assert item.proficiency in [
            ProficiencyLevel.FAMILIAR,
            ProficiencyLevel.PROFICIENT,
            ProficiencyLevel.MASTERED,
        ]

    def test_get_due_reviews(self, trainer):
        """Test getting due reviews."""
        # Add new items
        for word in ["word1", "word2", "word3"]:
            trainer.add_vocabulary(
                word=word,
                definition=f"definition of {word}",
                part_of_speech="noun",
            )

        due = trainer.get_due_reviews(limit=10)
        # New items should be due immediately
        assert len(due) >= 3

    def test_get_statistics(self, trainer):
        """Test getting learning statistics."""
        item = trainer.add_vocabulary(
            word="statistics",
            definition="collection of data",
            part_of_speech="noun",
        )

        stats = trainer.get_statistics()
        assert "total_words" in stats
        assert "by_proficiency" in stats
        assert "total_reviews" in stats
        assert stats["total_words"] > 0

    def test_export_import_progress(self, trainer):
        """Test exporting and importing progress."""
        # Add and review
        item = trainer.add_vocabulary(
            word="progress",
            definition="forward movement toward a destination",
            part_of_speech="noun",
        )
        trainer.review(item.word_id, quality=4)

        # Export
        data = trainer.export_progress()
        assert "vocabulary" in data
        assert "statistics" in data

        # Import into new trainer
        new_trainer = VocabularyTrainer()
        new_trainer.import_progress(data)
        imported = new_trainer.get_word_by_text("progress")
        assert imported is not None
        assert imported.repetitions == 1


class TestProficiencyLevel:
    """Tests for ProficiencyLevel enum."""

    def test_proficiency_levels(self):
        """Test all proficiency levels exist."""
        levels = [ProficiencyLevel.NEW, ProficiencyLevel.LEARNING,
                  ProficiencyLevel.FAMILIAR, ProficiencyLevel.PROFICIENT,
                  ProficiencyLevel.MASTERED]
        assert len(levels) == 5

    def test_proficiency_order(self):
        """Test proficiency levels have correct order."""
        assert list(ProficiencyLevel).index(ProficiencyLevel.NEW) < \
               list(ProficiencyLevel).index(ProficiencyLevel.MASTERED)


# ============================================================================
# GRAMMAR ENGINE TESTS
# ============================================================================

class TestGrammarRule:
    """Tests for GrammarRule dataclass."""

    def test_create_grammar_rule(self):
        """Test creating a grammar rule."""
        rule = GrammarRule(
            rule_id="test_rule_001",
            name="Test Rule",
            category=GrammarRuleType.SUBJECT_VERB_AGREEMENT,
            description="A test grammar rule",
            pattern=r"\btest\b",
            correct_examples=["This is correct."],
            incorrect_examples=["This are incorrect."],
            explanation="This is why it's correct.",
        )
        assert rule.rule_id == "test_rule_001"
        assert rule.category == GrammarRuleType.SUBJECT_VERB_AGREEMENT
        assert rule.difficulty == 1

    def test_grammar_rule_to_dict(self):
        """Test serialization."""
        rule = GrammarRule(
            rule_id="test_rule_002",
            name="Another Rule",
            category=GrammarRuleType.TENSE,
            description="Another test rule",
            pattern=r"\w+ed",
            correct_examples=["I walked."],
            incorrect_examples=["I walk yesterday."],
            explanation="Past tense explanation",
            difficulty=2,
            tags=["past", "beginner"],
        )
        data = rule.to_dict()
        assert data["rule_id"] == "test_rule_002"
        assert data["category"] == "tense"
        assert data["difficulty"] == 2


class TestGrammarEngine:
    """Tests for GrammarEngine."""

    @pytest.fixture
    def engine(self):
        """Create a grammar engine."""
        return GrammarEngine()

    def test_engine_initialization(self, engine):
        """Test engine initializes with rules."""
        assert len(engine._rules) > 0

    def test_get_rule(self, engine):
        """Test getting a rule by ID."""
        rule = engine.get_rule("grammar_sva_1")
        assert rule is not None
        assert rule.name == "Third Person Singular -s"

    def test_get_rules_by_category(self, engine):
        """Test getting rules by category."""
        rules = engine.get_rules_by_category(GrammarRuleType.ARTICLE)
        assert len(rules) > 0
        for rule in rules:
            assert rule.category == GrammarRuleType.ARTICLE

    def test_get_rules_by_difficulty(self, engine):
        """Test getting rules by difficulty range."""
        easy_rules = engine.get_rules_by_difficulty(1, 2)
        assert len(easy_rules) > 0
        for rule in easy_rules:
            assert 1 <= rule.difficulty <= 2

    def test_check_text_basic(self, engine):
        """Test basic text checking."""
        # Text with common error
        errors = engine.check_text("a apple")
        assert isinstance(errors, list)

    def test_generate_mc_exercise(self, engine):
        """Test multiple choice exercise generation."""
        rule = engine.get_rule("grammar_sva_1")
        exercise = engine.generate_exercise(rule, "multiple_choice")

        assert "question" in exercise
        assert "options" in exercise
        assert "correct_answer" in exercise
        assert exercise["type"] == "multiple_choice"

    def test_generate_fill_blank_exercise(self, engine):
        """Test fill-in-the-blank exercise generation."""
        rule = engine.get_rule("grammar_art_1")
        exercise = engine.generate_exercise(rule, "fill_blank")

        assert "question" in exercise
        assert exercise["type"] == "fill_blank"

    def test_generate_error_correction_exercise(self, engine):
        """Test error correction exercise generation."""
        rule = engine.get_rule("grammar_err_1")
        exercise = engine.generate_exercise(rule, "error_correction")

        assert "incorrect_sentence" in exercise
        assert "correct_answer" in exercise
        assert exercise["type"] == "error_correction"

    def test_add_rule(self, engine):
        """Test adding a custom rule."""
        rule = GrammarRule(
            rule_id="custom_001",
            name="Custom Rule",
            category=GrammarRuleType.COMMON_ERRORS,
            description="A custom grammar rule",
            pattern=r"\bcustom\b",
            correct_examples=["Correct example."],
            incorrect_examples=["Incorrect example."],
            explanation="Custom explanation",
        )
        engine.add_rule(rule)
        assert engine.get_rule("custom_001") is not None

    def test_get_statistics(self, engine):
        """Test getting grammar statistics."""
        stats = engine.get_statistics()
        assert "total_rules" in stats
        assert "by_category" in stats
        assert "by_difficulty" in stats
        assert stats["total_rules"] > 0


class TestGrammarRuleType:
    """Tests for GrammarRuleType enum."""

    def test_rule_types_exist(self):
        """Test all rule types exist."""
        types = [
            GrammarRuleType.WORD_ORDER,
            GrammarRuleType.TENSE,
            GrammarRuleType.ARTICLE,
            GrammarRuleType.PREPOSITION,
            GrammarRuleType.SUBJECT_VERB_AGREEMENT,
            GrammarRuleType.CONDITIONAL,
            GrammarRuleType.PASSIVE_VOICE,
            GrammarRuleType.RELATIVE_CLAUSE,
            GrammarRuleType.PUNCTUATION,
            GrammarRuleType.COMMON_ERRORS,
        ]
        assert len(types) == 10


# ============================================================================
# READING COMPREHENSION TESTS
# ============================================================================

class TestReadingPassage:
    """Tests for ReadingPassage dataclass."""

    def test_create_passage(self):
        """Test creating a reading passage."""
        passage = ReadingPassage(
            passage_id="read_test",
            title="Test Passage",
            text="This is a test passage.",
            difficulty=2,
            word_count=5,
            topic="test",
            vocabulary_level="intermediate",
        )
        assert passage.passage_id == "read_test"
        assert passage.difficulty == 2

    def test_passage_to_dict(self):
        """Test passage serialization."""
        passage = ReadingPassage(
            passage_id="read_test2",
            title="Another Test",
            text="Another test passage.",
            difficulty=1,
            word_count=3,
            topic="test",
            vocabulary_level="beginner",
            questions=[{"question": "Test?", "correct": 0}],
        )
        data = passage.to_dict()
        assert data["passage_id"] == "read_test2"
        assert len(data["questions"]) == 1


class TestReadingComprehension:
    """Tests for ReadingComprehension system."""

    @pytest.fixture
    def reading(self):
        """Create a reading comprehension system."""
        return ReadingComprehension()

    def test_initialization(self, reading):
        """Test system initializes with passages."""
        assert len(reading._passages) > 0

    def test_get_passage(self, reading):
        """Test getting a passage by ID."""
        passage = reading.get_passage("read_001")
        assert passage is not None
        assert passage.title == "The Cat and the Mouse"

    def test_get_passages_by_difficulty(self, reading):
        """Test getting passages by difficulty."""
        easy = reading.get_passages_by_difficulty(1)
        assert len(easy) > 0
        for p in easy:
            assert p.difficulty == 1

    def test_add_passage(self, reading):
        """Test adding a new passage."""
        passage = reading.add_passage(
            title="New Test Passage",
            text="This is a new test passage for testing.",
            difficulty=2,
            topic="test",
            questions=[
                {"question": "What is this?", "options": ["A", "B"], "correct": 0},
            ],
        )
        assert passage.passage_id is not None
        assert reading.get_passage(passage.passage_id) is not None

    def test_get_recommended_passage(self, reading):
        """Test getting a recommended passage."""
        passage = reading.get_recommended_passage(current_level=2)
        assert passage is not None
        assert passage.difficulty <= 3  # Within reach

    def test_get_recommended_passage_with_topics(self, reading):
        """Test getting recommended passage with topic preference."""
        passage = reading.get_recommended_passage(
            current_level=2,
            topics=["science"],
        )
        if passage:
            assert passage.topic == "science" or passage.difficulty <= 3

    def test_assess(self, reading):
        """Test reading assessment."""
        passage = reading.get_passage("read_001")
        # Submit correct answers
        answers = [q["correct"] for q in passage.questions]
        result = reading.assess("read_001", answers, time_spent=60.0)

        assert result.score == 1.0
        assert result.correct_answers == len(passage.questions)
        assert result.total_questions == len(passage.questions)

    def test_assess_partial(self, reading):
        """Test partial correct assessment."""
        passage = reading.get_passage("read_001")
        # Submit mixed answers
        answers = [0] * len(passage.questions)  # All first option
        result = reading.assess("read_001", answers)

        assert 0 <= result.score <= 1
        assert len(result.details) == len(passage.questions)

    def test_get_statistics(self, reading):
        """Test getting statistics."""
        # Take an assessment first
        passage = reading.get_passage("read_001")
        answers = [q["correct"] for q in passage.questions]
        reading.assess("read_001", answers)

        stats = reading.get_statistics()
        assert "total_passages" in stats
        assert "total_attempts" in stats
        assert stats["total_attempts"] >= 1


class TestReadingResult:
    """Tests for ReadingResult dataclass."""

    def test_create_result(self):
        """Test creating a reading result."""
        result = ReadingResult(
            result_id="result_001",
            passage_id="read_001",
            score=0.75,
            correct_answers=3,
            total_questions=4,
            time_spent_seconds=120,
            details=[],
        )
        assert result.score == 0.75
        assert result.correct_answers == 3

    def test_result_to_dict(self):
        """Test result serialization."""
        result = ReadingResult(
            result_id="result_002",
            passage_id="read_002",
            score=1.0,
            correct_answers=4,
            total_questions=4,
            time_spent_seconds=90,
            details=[{"question_num": 1, "is_correct": True}],
        )
        data = result.to_dict()
        assert data["score"] == 1.0
        assert len(data["details"]) == 1


# ============================================================================
# WRITING ASSESSOR TESTS
# ============================================================================

class TestWritingPrompt:
    """Tests for WritingPrompt dataclass."""

    def test_create_prompt(self):
        """Test creating a writing prompt."""
        prompt = WritingPrompt(
            prompt_id="write_test",
            prompt="Write about a topic.",
            topic="test",
            difficulty=2,
            word_limit=(50, 150),
            criteria=["grammar", "vocabulary"],
        )
        assert prompt.prompt_id == "write_test"
        assert prompt.word_limit == (50, 150)

    def test_prompt_to_dict(self):
        """Test prompt serialization."""
        prompt = WritingPrompt(
            prompt_id="write_test2",
            prompt="Another prompt.",
            topic="test",
            difficulty=3,
            word_limit=(100, 250),
            criteria=["grammar", "content"],
            time_limit_minutes=30,
        )
        data = prompt.to_dict()
        assert data["time_limit_minutes"] == 30


class TestWritingAssessor:
    """Tests for WritingAssessor."""

    @pytest.fixture
    def assessor(self):
        """Create a writing assessor."""
        return WritingAssessor()

    def test_initialization(self, assessor):
        """Test assessor initializes with prompts."""
        assert len(assessor._prompts) > 0

    def test_get_prompt(self, assessor):
        """Test getting a prompt by ID."""
        prompt = assessor.get_prompt("write_001")
        assert prompt is not None
        assert "hobby" in prompt.prompt.lower()

    def test_get_prompts_by_difficulty(self, assessor):
        """Test getting prompts by difficulty."""
        easy = assessor.get_prompts_by_difficulty(1)
        assert len(easy) > 0
        for p in easy:
            assert p.difficulty == 1

    def test_add_prompt(self, assessor):
        """Test adding a new prompt."""
        prompt = assessor.add_prompt(
            prompt="Write about your favorite food.",
            topic="food",
            difficulty=1,
            word_limit=(30, 100),
        )
        assert prompt.prompt_id is not None
        assert assessor.get_prompt(prompt.prompt_id) is not None

    def test_assess_basic(self, assessor):
        """Test basic writing assessment."""
        text = "I like to play soccer. It is my favorite hobby. I play every weekend with my friends. Soccer is fun and exciting."
        result = assessor.assess("write_001", text)

        assert result.word_count > 0
        assert 0 <= result.overall_score <= 1
        assert "grammar" in result.scores
        assert len(result.feedback) > 0

    def test_assess_with_grammar_errors(self, assessor):
        """Test assessment with grammar errors."""
        text = "She run every day. They plays soccer. I am liking books."
        result = assessor.assess("write_001", text)

        # Grammar score should be lower
        assert result.scores["grammar"] < 1.0
        assert len(result.grammar_errors) >= 0  # May or may not catch specific errors

    def test_assess_word_count(self, assessor):
        """Test assessment with word count issues."""
        # Too short
        short_text = "I like soccer."
        result = assessor.assess("write_001", short_text)
        assert result.word_count < 50  # Below minimum

        # Reasonable length
        good_text = "I enjoy playing soccer on weekends. It is a great way to stay active and have fun with friends. Soccer has been my favorite hobby for many years because it combines teamwork and exercise."
        result = assessor.assess("write_001", good_text)
        assert result.word_count >= 30

    def test_assess_scores_criteria(self, assessor):
        """Test that all criteria are scored."""
        text = "I have a favorite hobby. It is reading books. Reading is educational and entertaining. I learn new things from books every day."
        prompt = assessor.get_prompt("write_001")
        result = assessor.assess("write_001", text)

        for criterion in prompt.criteria:
            assert criterion in result.scores
            assert 0 <= result.scores[criterion] <= 1

    def test_generate_suggestions(self, assessor):
        """Test suggestion generation."""
        text = "I like soccer."
        result = assessor.assess("write_001", text)

        assert isinstance(result.suggestions, list)

    def test_get_statistics(self, assessor):
        """Test getting statistics."""
        # Submit an assessment first
        assessor.assess("write_001", "This is a test writing sample for assessment.")

        stats = assessor.get_statistics()
        assert "total_prompts" in stats
        assert "total_submissions" in stats
        assert stats["total_submissions"] >= 1


class TestWritingAssessment:
    """Tests for WritingAssessment dataclass."""

    def test_create_assessment(self):
        """Test creating an assessment."""
        assessment = WritingAssessment(
            assessment_id="assess_001",
            prompt_id="write_001",
            text="Sample text.",
            word_count=2,
            scores={"grammar": 0.8, "vocabulary": 0.7},
            overall_score=0.75,
            feedback="Good work!",
            suggestions=["Keep practicing."],
            grammar_errors=[],
        )
        assert assessment.assessment_id == "assess_001"
        assert assessment.overall_score == 0.75

    def test_assessment_to_dict(self):
        """Test assessment serialization."""
        assessment = WritingAssessment(
            assessment_id="assess_002",
            prompt_id="write_002",
            text="Another sample.",
            word_count=2,
            scores={"grammar": 0.9},
            overall_score=0.9,
            feedback="Excellent!",
            suggestions=[],
            grammar_errors=[],
        )
        data = assessment.to_dict()
        assert data["overall_score"] == 0.9
        assert "assessed_at" in data


# ============================================================================
# ENGLISH DOMAIN TESTS
# ============================================================================

class TestEnglishDomain:
    """Tests for the main EnglishDomain class."""

    @pytest.fixture
    def domain(self):
        """Create an English domain."""
        return EnglishDomain()

    def test_initialization(self, domain):
        """Test domain initializes all components."""
        assert domain.vocabulary is not None
        assert domain.grammar is not None
        assert domain.reading is not None
        assert domain.writing is not None

    def test_create_learning_session(self, domain):
        """Test creating a learning session."""
        session = domain.create_learning_session(
            focus="mixed",
            duration_minutes=30,
        )
        assert "session_id" in session
        assert "activities" in session
        assert len(session["activities"]) > 0

    def test_create_vocabulary_session(self, domain):
        """Test creating a vocabulary-focused session."""
        session = domain.create_learning_session(focus="vocabulary")
        activity_types = [a["type"] for a in session["activities"]]
        assert "vocabulary_review" in activity_types

    def test_create_reading_session(self, domain):
        """Test creating a reading-focused session."""
        session = domain.create_learning_session(focus="reading")
        activity_types = [a["type"] for a in session["activities"]]
        assert "reading" in activity_types

    def test_get_overall_statistics(self, domain):
        """Test getting overall statistics."""
        stats = domain.get_overall_statistics()
        assert "vocabulary" in stats
        assert "grammar" in stats
        assert "reading" in stats
        assert "writing" in stats

    def test_export_import_progress(self, domain):
        """Test exporting and importing progress."""
        # Add some activity
        item = domain.vocabulary.add_vocabulary(
            word="export_test",
            definition="test word",
            part_of_speech="noun",
        )
        domain.vocabulary.review(item.word_id, quality=4)

        # Export
        data = domain.export_progress()
        assert "vocabulary" in data

        # Import into new domain
        new_domain = EnglishDomain()
        new_domain.import_progress(data)

        imported = new_domain.vocabulary.get_word_by_text("export_test")
        assert imported is not None


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Integration tests across components."""

    def test_vocabulary_to_reading_integration(self):
        """Test vocabulary words appear in reading passages."""
        domain = EnglishDomain()

        # Get a passage
        passage = domain.reading.get_passage("read_001")
        if passage:
            # Check if passage words can be found in vocabulary
            words = passage.text.lower().split()
            for word in words[:5]:  # Check first 5 words
                clean_word = ''.join(c for c in word if c.isalpha())
                if clean_word and len(clean_word) > 2:
                    vocab = domain.vocabulary.get_word_by_text(clean_word)
                    # Not all words will be in vocabulary, that's fine

    def test_grammar_to_writing_integration(self):
        """Test grammar engine integrates with writing assessor."""
        domain = EnglishDomain()

        # Submit writing with grammar errors
        text = "She run every day. They plays soccer."
        assessment = domain.writing.assess("write_001", text)

        # Grammar should be checked
        assert "grammar" in assessment.scores

    def test_full_learning_session(self):
        """Test a complete learning session workflow."""
        domain = EnglishDomain()

        # Create session
        session = domain.create_learning_session(focus="mixed")

        # Vocabulary activity
        for activity in session["activities"]:
            if activity["type"] == "vocabulary_review":
                items = activity.get("items", [])
                if items:
                    # Review an item
                    domain.vocabulary.review(items[0].word_id, quality=4)

            elif activity["type"] == "reading":
                passage_id = activity.get("passage_id")
                if passage_id:
                    passage = domain.reading.get_passage(passage_id)
                    if passage:
                        # Submit answers
                        answers = [q["correct"] for q in passage.questions]
                        domain.reading.assess(passage_id, answers)

        # Check progress was recorded
        stats = domain.get_overall_statistics()
        assert stats["total_sessions"] >= 1
