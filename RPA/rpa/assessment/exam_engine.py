"""
Exam Engine - Run standardized exams for AI proficiency certification.

Loads questions from Hugging Face datasets or manual JSON files,
runs the AI against them, and scores results.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pathlib import Path
import json
import uuid
import logging
import random

from rpa.assessment.curriculum_registry import CurriculumRegistry, CurriculumLevel
from rpa.memory.episodic import EpisodicMemory, EventType
from rpa.preprocessing.dataset_loader import DatasetLoader

logger = logging.getLogger(__name__)


class QuestionType(Enum):
    """Types of exam questions."""
    MULTIPLE_CHOICE = "multiple_choice"
    CODE_COMPLETION = "code_completion"
    SHORT_ANSWER = "short_answer"
    FILL_BLANK = "fill_blank"
    TRUE_FALSE = "true_false"


@dataclass
class ExamQuestion:
    """A single exam question."""
    question_id: str
    question_type: QuestionType
    question: str
    expected_answer: str  # Required field - must come before defaults
    options: List[str] = field(default_factory=list)
    source: str = "manual"  # HF dataset name or "manual"
    difficulty: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "question_id": self.question_id,
            "question_type": self.question_type.value,
            "question": self.question,
            "options": self.options,
            "expected_answer": self.expected_answer,
            "source": self.source,
            "difficulty": self.difficulty,
            "metadata": self.metadata,
        }


@dataclass
class ExamAnswer:
    """An AI's answer to an exam question."""
    question_id: str
    ai_answer: str
    is_correct: bool
    confidence: float = 0.0
    time_spent_seconds: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "question_id": self.question_id,
            "ai_answer": self.ai_answer,
            "is_correct": self.is_correct,
            "confidence": self.confidence,
            "time_spent_seconds": self.time_spent_seconds,
            "metadata": self.metadata,
        }


@dataclass
class ExamSession:
    """
    A complete exam session with all questions and results.
    
    Tracks per-question detail and overall score.
    """
    session_id: str
    track_id: str
    level_id: str
    
    # Questions and answers
    questions: List[ExamQuestion] = field(default_factory=list)
    answers: List[ExamAnswer] = field(default_factory=list)
    
    # Scoring
    score: float = 0.0
    correct_count: int = 0
    total_questions: int = 0
    passed: bool = False
    
    # Metadata
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0
    badge_awarded: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "session_id": self.session_id,
            "track_id": self.track_id,
            "level_id": self.level_id,
            "questions": [q.to_dict() for q in self.questions],
            "answers": [a.to_dict() for a in self.answers],
            "score": self.score,
            "correct_count": self.correct_count,
            "total_questions": self.total_questions,
            "passed": self.passed,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
            "badge_awarded": self.badge_awarded,
        }


class ExamEngine:
    """
    Engine for running standardized exams.
    
    Features:
    - Loads questions from HF datasets (MMLU, HumanEval, SQuAD, etc.)
    - Supports manually curated questions
    - Submits questions to AI via AgentInterface
    - Scores answers and determines pass/fail
    - Stores results in EpisodicMemory
    """
    
    # Maximum questions per exam
    MAX_QUESTIONS = 50
    
    # HF dataset field mappings
    DATASET_FIELD_MAP = {
        "mmlu": {"question": "question", "choices": "choices", "answer": "answer"},
        "squad": {"question": "question", "answer": "answers"},
        "humaneval": {"question": "prompt", "answer": "canonical_solution"},
        "mbpp": {"question": "prompt", "answer": "code"},
        "openbookqa": {"question": "question_stem", "choices": "choices", "answer": "answerKey"},
    }
    
    def __init__(
        self,
        registry: Optional[CurriculumRegistry] = None,
        episodic: Optional[EpisodicMemory] = None,
        loader: Optional[DatasetLoader] = None,
        manual_questions_dir: Optional[str] = None,
    ):
        """
        Initialize the ExamEngine.
        
        Args:
            registry: CurriculumRegistry for track/level lookup
            episodic: EpisodicMemory for storing exam results
            loader: DatasetLoader for HF dataset access
            manual_questions_dir: Directory for manual question files
        """
        self.registry = registry or CurriculumRegistry()
        self.episodic = episodic or EpisodicMemory()
        self.loader = loader or DatasetLoader()
        self.manual_dir = Path(manual_questions_dir) if manual_questions_dir else None
        
        # Session history
        self._sessions: Dict[str, ExamSession] = {}
        self._max_history = 200
    
    def prepare_exam(
        self,
        track_id: str,
        level_id: str,
        num_questions: int = 20,
        include_manual: bool = True,
    ) -> ExamSession:
        """
        Prepare an exam session by loading questions.
        
        Args:
            track_id: Curriculum track ID
            level_id: Level ID within track
            num_questions: Number of questions to include
            include_manual: Whether to include manual questions
            
        Returns:
            ExamSession with loaded questions
        """
        # Get level config
        level = self.registry.get_level(track_id, level_id)
        if not level:
            raise ValueError(f"Level not found: {track_id}/{level_id}")
        
        session_id = f"exam_{uuid.uuid4().hex[:8]}"
        
        session = ExamSession(
            session_id=session_id,
            track_id=track_id,
            level_id=level_id,
        )
        
        # Load questions from HF dataset
        hf_questions = self._load_hf_questions(
            dataset=level.exam_dataset,
            subset=level.exam_subset,
            limit=num_questions,
        )
        session.questions.extend(hf_questions)
        
        # Load manual questions if available
        if include_manual and self.manual_dir:
            manual_questions = self._load_manual_questions(
                track_id=track_id,
                level_id=level_id,
                limit=num_questions,
            )
            session.questions.extend(manual_questions)
        
        # Limit to requested count
        session.questions = session.questions[:num_questions]
        session.total_questions = len(session.questions)
        
        logger.info(
            f"Prepared exam {session_id}: {len(session.questions)} questions "
            f"for {track_id}/{level_id}"
        )
        
        return session
    
    def run_exam(
        self,
        session: ExamSession,
        answer_callback: Optional[callable] = None,
    ) -> ExamSession:
        """
        Run an exam session, collecting AI answers.
        
        Args:
            session: Prepared ExamSession
            answer_callback: Optional function(question) -> answer
            
        Returns:
            Completed ExamSession with scores
        """
        if not session.questions:
            logger.warning(f"No questions in session {session.session_id}")
            return session
        
        logger.info(f"Running exam {session.session_id}")
        
        # Process each question
        for question in session.questions:
            # Get answer from callback or simulate
            if answer_callback:
                answer = answer_callback(question)
            else:
                # Simulate AI answer (in real use, would call AgentInterface)
                answer = self._simulate_answer(question)
            
            # Score the answer
            is_correct = self._score_answer(question, answer)
            
            session.answers.append(ExamAnswer(
                question_id=question.question_id,
                ai_answer=answer,
                is_correct=is_correct,
            ))
        
        # Calculate score
        session.correct_count = sum(1 for a in session.answers if a.is_correct)
        session.score = session.correct_count / session.total_questions if session.total_questions > 0 else 0
        
        # Check if passed
        level = self.registry.get_level(session.track_id, session.level_id)
        if level:
            session.passed = session.score >= level.pass_threshold
        
        # Complete session
        session.completed_at = datetime.now()
        session.duration_seconds = (session.completed_at - session.started_at).total_seconds()
        
        # Store in episodic memory
        self._store_session(session)
        
        # Store in history
        self._sessions[session.session_id] = session
        self._trim_history()
        
        logger.info(
            f"Exam {session.session_id} complete: "
            f"{session.correct_count}/{session.total_questions} ({session.score:.1%}) - "
            f"{'PASSED' if session.passed else 'FAILED'}"
        )
        
        return session
    
    def run_exam_quick(
        self,
        track_id: str,
        level_id: str,
        num_questions: int = 20,
    ) -> ExamSession:
        """
        Prepare and run an exam in one call.
        
        Uses simulated answers for testing.
        """
        session = self.prepare_exam(track_id, level_id, num_questions)
        return self.run_exam(session)
    
    def _load_hf_questions(
        self,
        dataset: str,
        subset: Optional[str],
        limit: int,
    ) -> List[ExamQuestion]:
        """Load questions from Hugging Face dataset."""
        questions = []
        
        # Check if we have HF datasets
        try:
            from datasets import load_dataset
        except ImportError:
            logger.warning("Hugging Face datasets not available")
            return self._generate_sample_questions(dataset, limit)
        
        try:
            # Load dataset
            if subset:
                ds = load_dataset(dataset, subset, split="test", trust_remote_code=True)
            else:
                ds = load_dataset(dataset, split="test", trust_remote_code=True)
            
            field_map = self.DATASET_FIELD_MAP.get(dataset, {})
            
            for i, item in enumerate(ds):
                if len(questions) >= limit:
                    break
                
                question = self._parse_hf_item(dataset, item, field_map, i)
                if question:
                    questions.append(question)
            
            logger.info(f"Loaded {len(questions)} questions from {dataset}")
            
        except Exception as e:
            logger.warning(f"Failed to load HF dataset {dataset}: {e}")
            return self._generate_sample_questions(dataset, limit)
        
        return questions
    
    def _parse_hf_item(
        self,
        dataset: str,
        item: Dict,
        field_map: Dict,
        index: int,
    ) -> Optional[ExamQuestion]:
        """Parse a Hugging Face dataset item into ExamQuestion."""
        try:
            if dataset == "mmlu":
                question_text = item.get("question", "")
                choices = item.get("choices", [])
                answer_idx = item.get("answer", 0)
                
                return ExamQuestion(
                    question_id=f"mmlu_{index}",
                    question_type=QuestionType.MULTIPLE_CHOICE,
                    question=question_text,
                    options=choices,
                    expected_answer=choices[answer_idx] if choices else "",
                    source="mmlu",
                )
            
            elif dataset == "squad":
                question_text = item.get("question", "")
                answers = item.get("answers", {})
                answer_list = answers.get("text", [""]) if isinstance(answers, dict) else [answers]
                
                return ExamQuestion(
                    question_id=f"squad_{index}",
                    question_type=QuestionType.SHORT_ANSWER,
                    question=question_text,
                    expected_answer=answer_list[0] if answer_list else "",
                    source="squad",
                )
            
            elif dataset == "mbpp":
                prompt = item.get("prompt", item.get("text", ""))
                code = item.get("code", "")
                
                return ExamQuestion(
                    question_id=f"mbpp_{index}",
                    question_type=QuestionType.CODE_COMPLETION,
                    question=prompt,
                    expected_answer=code,
                    source="mbpp",
                )
            
            elif dataset == "humaneval":
                prompt = item.get("prompt", "")
                solution = item.get("canonical_solution", "")
                
                return ExamQuestion(
                    question_id=f"humaneval_{index}",
                    question_type=QuestionType.CODE_COMPLETION,
                    question=prompt,
                    expected_answer=solution,
                    source="humaneval",
                )
            
            else:
                # Generic parsing
                question_text = item.get("question", item.get("prompt", item.get("text", "")))
                answer = item.get("answer", item.get("solution", item.get("label", "")))
                
                if question_text:
                    return ExamQuestion(
                        question_id=f"{dataset}_{index}",
                        question_type=QuestionType.SHORT_ANSWER,
                        question=str(question_text),
                        expected_answer=str(answer),
                        source=dataset,
                    )
        
        except Exception as e:
            logger.debug(f"Failed to parse item: {e}")
        
        return None
    
    def _load_manual_questions(
        self,
        track_id: str,
        level_id: str,
        limit: int,
    ) -> List[ExamQuestion]:
        """Load manually curated questions from JSON files."""
        questions = []
        
        if not self.manual_dir:
            return questions
        
        # Look for track/level specific file
        exam_file = self.manual_dir / track_id / f"{level_id}.json"
        
        if not exam_file.exists():
            return questions
        
        try:
            with open(exam_file) as f:
                data = json.load(f)
            
            for i, item in enumerate(data.get("questions", [])):
                question = ExamQuestion(
                    question_id=f"manual_{track_id}_{i}",
                    question_type=QuestionType(item.get("type", "short_answer")),
                    question=item.get("question", ""),
                    options=item.get("options", []),
                    expected_answer=item.get("answer", ""),
                    source="manual",
                    difficulty=item.get("difficulty", 1),
                )
                questions.append(question)
            
            logger.info(f"Loaded {len(questions)} manual questions from {exam_file}")
            
        except Exception as e:
            logger.warning(f"Failed to load manual questions: {e}")
        
        return questions[:limit]
    
    def _generate_sample_questions(
        self,
        dataset: str,
        limit: int,
    ) -> List[ExamQuestion]:
        """Generate sample questions for testing."""
        questions = []
        
        sample_questions = {
            "english": [
                ("What is the past tense of 'go'?", "went"),
                ("Choose the correct article: ___ apple", "an"),
                ("Complete: She ___ to school every day.", "goes"),
                ("What is a synonym for 'happy'?", "joyful"),
            ],
            "python": [
                ("Write a function to reverse a list", "def reverse_list(lst): return lst[::-1]"),
                ("How do you create a dictionary?", "{}"),
                ("What is the output of len([1,2,3])?", "3"),
                ("Write a list comprehension for squares", "[x**2 for x in range(10)]"),
            ],
            "default": [
                ("What is 2 + 2?", "4"),
                ("Complete: The sky is ___.", "blue"),
            ],
        }
        
        bank = sample_questions.get(dataset, sample_questions["default"])
        
        for i, (q, a) in enumerate(bank[:limit]):
            questions.append(ExamQuestion(
                question_id=f"sample_{i}",
                question_type=QuestionType.SHORT_ANSWER,
                question=q,
                expected_answer=a,
                source="sample",
            ))
        
        return questions
    
    def _simulate_answer(self, question: ExamQuestion) -> str:
        """Simulate an AI answer for testing."""
        # For testing, randomly choose between correct and incorrect
        if random.random() < 0.7:  # 70% correct rate
            return question.expected_answer
        else:
            # Return a wrong answer
            if question.options:
                wrong = [o for o in question.options if o != question.expected_answer]
                return random.choice(wrong) if wrong else "wrong"
            return "incorrect answer"
    
    def _score_answer(self, question: ExamQuestion, answer: str) -> bool:
        """Score an answer against the expected answer."""
        # Normalize for comparison
        expected = question.expected_answer.strip().lower()
        given = answer.strip().lower()
        
        # Exact match for code
        if question.question_type == QuestionType.CODE_COMPLETION:
            # For code, check if key parts match
            return expected in given or given in expected
        
        # Exact match for multiple choice
        if question.question_type == QuestionType.MULTIPLE_CHOICE:
            return expected == given
        
        # Keyword matching for short answer
        if question.question_type == QuestionType.SHORT_ANSWER:
            # Check if answer contains key words from expected
            expected_words = set(expected.split())
            given_words = set(given.split())
            overlap = len(expected_words & given_words)
            return overlap >= len(expected_words) * 0.5
        
        # Default to exact match
        return expected == given
    
    def _store_session(self, session: ExamSession) -> None:
        """Store exam session in episodic memory."""
        self.episodic.log_event(
            event_type=EventType.PATTERN_LEARNED,
            session_id=session.session_id,
            data={
                "type": "exam_session",
                "track_id": session.track_id,
                "level_id": session.level_id,
                "score": session.score,
                "passed": session.passed,
                "correct_count": session.correct_count,
                "total_questions": session.total_questions,
            },
        )
    
    def _trim_history(self) -> None:
        """Trim old sessions from history."""
        if len(self._sessions) > self._max_history:
            # Remove oldest
            sorted_ids = sorted(
                self._sessions.keys(),
                key=lambda x: self._sessions[x].started_at,
            )
            for sid in sorted_ids[:-self._max_history]:
                del self._sessions[sid]
    
    def get_session(self, session_id: str) -> Optional[ExamSession]:
        """Get a stored exam session."""
        return self._sessions.get(session_id)
    
    def get_recent_sessions(self, limit: int = 20) -> List[ExamSession]:
        """Get recent exam sessions."""
        sessions = sorted(
            self._sessions.values(),
            key=lambda s: s.started_at,
            reverse=True,
        )
        return sessions[:limit]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get exam engine statistics."""
        total = len(self._sessions)
        passed = sum(1 for s in self._sessions.values() if s.passed)
        
        by_track = {}
        for session in self._sessions.values():
            track = session.track_id
            if track not in by_track:
                by_track[track] = {"total": 0, "passed": 0, "avg_score": 0}
            by_track[track]["total"] += 1
            if session.passed:
                by_track[track]["passed"] += 1
            by_track[track]["avg_score"] = (
                by_track[track]["avg_score"] * (by_track[track]["total"] - 1) + session.score
            ) / by_track[track]["total"]
        
        return {
            "total_sessions": total,
            "passed_sessions": passed,
            "pass_rate": passed / max(1, total),
            "by_track": by_track,
        }
