"""
Pydantic Models for Core API.

All API request/response models used by both Web UI and Terminal UI.
Ensures consistent data structures across all interfaces.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Generic, TypeVar
from pydantic import BaseModel, Field, field_validator
import uuid
import re


# ============================================================================
# ENUMS
# ============================================================================

class UserRole(str, Enum):
    """User roles with hierarchical permissions."""
    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"


class ProficiencyLevel(str, Enum):
    """Vocabulary proficiency levels."""
    NEW = "new"
    LEARNING = "learning"
    FAMILIAR = "familiar"
    PROFICIENT = "proficient"
    MASTERED = "mastered"


class ExerciseType(str, Enum):
    """Types of exercises."""
    FLASHCARD = "flashcard"
    MULTIPLE_CHOICE = "multiple_choice"
    FILL_BLANK = "fill_blank"
    TYPING = "typing"
    ERROR_CORRECTION = "error_correction"


class DomainType(str, Enum):
    """Learning domains."""
    ENGLISH = "english"
    PYTHON = "python"
    GENERAL = "general"


# ============================================================================
# GENERIC RESPONSE
# ============================================================================

T = TypeVar('T')


class APIResponse(BaseModel, Generic[T]):
    """Standard API response wrapper."""
    success: bool = True
    message: str = ""
    data: Optional[T] = None
    errors: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# ============================================================================
# USER MODELS
# ============================================================================

class UserBase(BaseModel):
    """Base user model."""
    email: str = Field(..., description="User email address")
    username: str = Field(..., min_length=3, max_length=50)

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        """Validate email format (more permissive for testing)."""
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', v):
            raise ValueError('Invalid email format')
        return v


class UserCreate(UserBase):
    """User registration model."""
    password: str = Field(..., min_length=8, max_length=100)
    role: UserRole = UserRole.USER


class UserLogin(BaseModel):
    """User login model."""
    email: str = Field(..., description="User email address")
    password: str

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        """Validate email format (more permissive for testing)."""
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', v):
            raise ValueError('Invalid email format')
        return v


class UserPreferences(BaseModel):
    """User preferences - synced across all interfaces."""
    # Theme
    theme: str = "auto"  # Web: light/dark/auto, Terminal: color scheme

    # Learning preferences
    difficulty: str = "adaptive"  # easy, medium, hard, adaptive
    daily_goal: int = Field(default=30, ge=5, le=200)  # items per day
    notifications: bool = True
    sound_effects: bool = True

    # Terminal-specific (ignored by Web UI)
    editor: str = "vim"  # For writing exercises in TUI
    pager: str = "less"  # For reading content in TUI

    # Accessibility
    font_size: int = Field(default=16, ge=10, le=32)
    high_contrast: bool = False
    reduced_motion: bool = False

    class Config:
        # Allow extra fields for future extensibility
        extra = "allow"


class UserResponse(UserBase):
    """User response model."""
    user_id: str
    role: UserRole = UserRole.USER
    preferences: UserPreferences = Field(default_factory=UserPreferences)
    created_at: datetime = Field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    is_active: bool = True

    class Config:
        from_attributes = True


class UserSession(BaseModel):
    """Active user session."""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    role: UserRole
    started_at: datetime = Field(default_factory=datetime.now)
    last_activity: datetime = Field(default_factory=datetime.now)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "role": self.role.value,
            "started_at": self.started_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
        }


# ============================================================================
# LEARNING MODELS
# ============================================================================

class LearningSession(BaseModel):
    """Active learning session."""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    domain: DomainType = DomainType.ENGLISH
    exercise_type: ExerciseType = ExerciseType.FLASHCARD

    # Progress tracking
    current_item: int = 0
    total_items: int = 0
    correct_count: int = 0
    incorrect_count: int = 0

    # Timing
    started_at: datetime = Field(default_factory=datetime.now)
    last_activity: datetime = Field(default_factory=datetime.now)

    # State
    is_active: bool = True
    items_reviewed: List[str] = Field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "domain": self.domain.value,
            "exercise_type": self.exercise_type.value,
            "current_item": self.current_item,
            "total_items": self.total_items,
            "correct_count": self.correct_count,
            "incorrect_count": self.incorrect_count,
            "accuracy": self.accuracy,
            "started_at": self.started_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "is_active": self.is_active,
        }

    @property
    def accuracy(self) -> float:
        """Calculate accuracy percentage."""
        total = self.correct_count + self.incorrect_count
        return self.correct_count / total if total > 0 else 0.0


class LearningProgress(BaseModel):
    """User's learning progress across all domains."""
    user_id: str

    # Vocabulary stats
    total_words: int = 0
    mastered_words: int = 0
    learning_words: int = 0
    new_words: int = 0

    # Grammar stats
    total_rules: int = 0
    mastered_rules: int = 0

    # Reading stats
    articles_read: int = 0
    total_reading_time: float = 0.0  # minutes

    # Writing stats
    essays_written: int = 0
    average_score: float = 0.0

    # Streaks
    current_streak: int = 0
    longest_streak: int = 0

    # Time tracking
    total_time_spent: float = 0.0  # minutes
    last_session: Optional[datetime] = None

    # Achievements
    achievements: List[str] = Field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "user_id": self.user_id,
            "vocabulary": {
                "total": self.total_words,
                "mastered": self.mastered_words,
                "learning": self.learning_words,
                "new": self.new_words,
            },
            "grammar": {
                "total": self.total_rules,
                "mastered": self.mastered_rules,
            },
            "reading": {
                "articles_read": self.articles_read,
                "total_time": self.total_reading_time,
            },
            "writing": {
                "essays_written": self.essays_written,
                "average_score": self.average_score,
            },
            "streaks": {
                "current": self.current_streak,
                "longest": self.longest_streak,
            },
            "total_time_spent": self.total_time_spent,
            "last_session": self.last_session.isoformat() if self.last_session else None,
            "achievements": self.achievements,
        }


# ============================================================================
# VOCABULARY MODELS
# ============================================================================

class VocabularyItemResponse(BaseModel):
    """Vocabulary item for API responses."""
    word_id: str
    word: str
    definition: str
    part_of_speech: str
    examples: List[str] = Field(default_factory=list)
    synonyms: List[str] = Field(default_factory=list)
    antonyms: List[str] = Field(default_factory=list)
    difficulty: int = 1
    proficiency: ProficiencyLevel = ProficiencyLevel.NEW
    next_review: Optional[datetime] = None


class VocabularyReviewRequest(BaseModel):
    """Request to review a vocabulary item."""
    word_id: str
    quality: int = Field(..., ge=0, le=5)  # SM-2 quality scale
    response: str = ""
    time_spent_seconds: float = 0.0


class VocabularyReviewResponse(BaseModel):
    """Response after vocabulary review."""
    word_id: str
    correct: bool
    quality: int
    feedback: str
    new_proficiency: ProficiencyLevel
    next_review: datetime
    interval: int  # days until next review


class VocabularyFlashcard(BaseModel):
    """Flashcard for vocabulary learning."""
    word_id: str
    front: str  # The word
    back: str   # The definition
    examples: List[str] = Field(default_factory=list)
    part_of_speech: str
    difficulty: int
    hint: Optional[str] = None


class VocabularyMultipleChoice(BaseModel):
    """Multiple choice question for vocabulary."""
    word_id: str
    question: str
    options: List[str]
    correct_index: int
    difficulty: int


# ============================================================================
# GRAMMAR MODELS
# ============================================================================

class GrammarRuleResponse(BaseModel):
    """Grammar rule for API responses."""
    rule_id: str
    name: str
    category: str
    description: str
    correct_examples: List[str] = Field(default_factory=list)
    incorrect_examples: List[str] = Field(default_factory=list)
    explanation: str
    difficulty: int = 1


class GrammarExerciseRequest(BaseModel):
    """Request for a grammar exercise."""
    rule_id: Optional[str] = None
    category: Optional[str] = None
    difficulty: Optional[int] = None
    exercise_type: ExerciseType = ExerciseType.MULTIPLE_CHOICE


class GrammarExerciseResponse(BaseModel):
    """Grammar exercise response."""
    exercise_id: str
    rule_id: str
    type: ExerciseType
    question: str
    options: Optional[List[str]] = None
    correct_answer: str
    explanation: str
    difficulty: int


class GrammarCheckRequest(BaseModel):
    """Request to check grammar."""
    text: str = Field(..., min_length=1, max_length=10000)


class GrammarCheckResponse(BaseModel):
    """Response from grammar check."""
    text: str
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    score: float = 1.0  # Grammar quality score (0-1)


# ============================================================================
# READING MODELS
# ============================================================================

class ReadingContent(BaseModel):
    """Reading content for comprehension."""
    content_id: str
    title: str
    text: str
    level: int = 1  # Reading difficulty level (1-5)
    word_count: int = 0
    estimated_time: float = 0.0  # minutes
    domain: DomainType = DomainType.ENGLISH
    tags: List[str] = Field(default_factory=list)
    questions: List[Dict[str, Any]] = Field(default_factory=list)


class ReadingProgress(BaseModel):
    """Progress on reading content."""
    content_id: str
    user_id: str
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    time_spent: float = 0.0  # minutes
    comprehension_score: Optional[float] = None
    is_completed: bool = False


# ============================================================================
# WRITING MODELS
# ============================================================================

class WritingSubmission(BaseModel):
    """Writing exercise submission."""
    submission_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    topic: str
    text: str
    word_count: int = 0
    submitted_at: datetime = Field(default_factory=datetime.now)


class WritingAssessment(BaseModel):
    """Writing assessment result."""
    submission_id: str
    overall_score: float = Field(..., ge=0, le=100)

    # Assessment criteria (each 0-100)
    grammar_score: float = 0.0
    vocabulary_score: float = 0.0
    coherence_score: float = 0.0
    structure_score: float = 0.0
    content_score: float = 0.0

    # Feedback
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)

    # Detailed errors
    grammar_errors: List[Dict[str, Any]] = Field(default_factory=list)

    assessed_at: datetime = Field(default_factory=datetime.now)


# ============================================================================
# SYSTEM MODELS
# ============================================================================

class SystemStatus(BaseModel):
    """System status for health checks and monitoring."""
    status: str = "healthy"  # healthy, degraded, error
    version: str = "1.0.0"
    uptime_seconds: float = 0.0

    # Memory stats
    stm_patterns: int = 0
    ltm_patterns: int = 0
    total_episodes: int = 0

    # User stats
    total_users: int = 0
    active_users: int = 0

    # Learning stats
    total_sessions_today: int = 0
    total_items_reviewed_today: int = 0

    # System info
    domains: List[str] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DashboardData(BaseModel):
    """Dashboard data for user home screen."""
    user: UserResponse
    progress: LearningProgress

    # Due items
    due_vocabulary: int = 0
    due_grammar: int = 0

    # Recent activity
    recent_sessions: List[Dict[str, Any]] = Field(default_factory=list)

    # Recommendations
    recommended_next: List[str] = Field(default_factory=list)

    # Quick stats
    today_items: int = 0
    today_time: float = 0.0
    weekly_trend: List[Dict[str, Any]] = Field(default_factory=list)


class MemorySnapshot(BaseModel):
    """Snapshot of memory state."""
    snapshot_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)

    # STM snapshot
    stm_nodes: int = 0
    stm_edges: int = 0

    # LTM snapshot
    ltm_nodes: int = 0
    ltm_edges: int = 0

    # Episodic snapshot
    total_events: int = 0

    # Metadata
    domains: Dict[str, int] = Field(default_factory=dict)
    hierarchy_levels: Dict[int, int] = Field(default_factory=dict)


class KnowledgeExport(BaseModel):
    """Exported knowledge graph."""
    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    edges: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    exported_at: datetime = Field(default_factory=datetime.now)


# ============================================================================
# ADMIN MODELS
# ============================================================================

class AdminUserUpdate(BaseModel):
    """Admin update for user."""
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    preferences: Optional[UserPreferences] = None


class AdminReport(BaseModel):
    """Admin report data."""
    report_type: str
    generated_at: datetime = Field(default_factory=datetime.now)
    data: Dict[str, Any] = Field(default_factory=dict)


class SystemConfig(BaseModel):
    """System configuration."""
    # Learning settings
    default_daily_goal: int = 30
    max_session_items: int = 100
    spaced_repetition_enabled: bool = True
    adaptive_difficulty: bool = True

    # Memory settings
    stm_capacity: int = 100
    consolidation_threshold: float = 0.7

    # System settings
    max_users: int = 1000
    session_timeout_minutes: int = 60
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # seconds

    # Feature flags
    experimental_features: bool = False
    analytics_enabled: bool = True
    debug_mode: bool = False


class WorkflowConfig(BaseModel):
    """GitHub Actions workflow configuration."""
    workflow_id: str
    name: str
    schedule: str  # cron expression
    enabled: bool = True
    domain: DomainType
    parameters: Dict[str, Any] = Field(default_factory=dict)
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
