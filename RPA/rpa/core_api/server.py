"""
FastAPI Server for RPA Core API.

Unified backend that serves Web UI, Terminal UI, and API clients.
Provides consistent REST API endpoints for all learning, progress, and admin operations.
"""

from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional
import logging
import os
import sys

# Add parent path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import (
    FastAPI, HTTPException, Depends, Header, Query, Path, Body,
    status, Request, Response
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .models import (
    # Request/Response models
    UserCreate, UserLogin, UserResponse, UserPreferences,
    LearningSession, LearningProgress,
    VocabularyReviewRequest, VocabularyReviewResponse,
    VocabularyFlashcard, VocabularyMultipleChoice,
    GrammarExerciseRequest, GrammarExerciseResponse,
    GrammarCheckRequest, GrammarCheckResponse,
    ReadingContent, ReadingProgress,
    WritingSubmission, WritingAssessment,
    SystemStatus, DashboardData, MemorySnapshot,
    APIResponse, UserRole, DomainType, ExerciseType,
    AdminUserUpdate, SystemConfig,
)
from .auth import AuthManager, create_access_token, verify_token
from .user_roles import (
    check_permission, get_role_config, Permission,
    PermissionDeniedError, can_manage_users, can_access_admin_panel
)
from .design_tokens import DESIGN_TOKENS, export_for_web, export_for_terminal

# Import domain modules
from ..domains.english import (
    VocabularyTrainer, GrammarEngine,
    ProficiencyLevel, VocabularyItem
)

logger = logging.getLogger(__name__)


# ============================================================================
# DEPENDENCIES
# ============================================================================

# Global instances
auth_manager = AuthManager()
vocabulary_trainer = VocabularyTrainer()
grammar_engine = GrammarEngine()

# User progress store (in-memory for now, would be database in production)
user_progress: Dict[str, LearningProgress] = {}
active_sessions: Dict[str, LearningSession] = {}


async def get_current_user(
    authorization: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """Get current user from Authorization header."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required"
        )

    # Extract token
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization format. Use: Bearer <token>"
        )

    token = parts[1]
    payload = auth_manager.verify_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    return payload


async def get_current_user_optional(
    authorization: Optional[str] = Header(None)
) -> Optional[Dict[str, Any]]:
    """Get current user from Authorization header (optional)."""
    if not authorization:
        return None

    try:
        return await get_current_user(authorization)
    except HTTPException:
        return None


def require_permission_dependency(permission: Permission):
    """Create a dependency that requires a specific permission."""
    async def check(
        user: Dict[str, Any] = Depends(get_current_user)
    ) -> Dict[str, Any]:
        if not check_permission(user["role"], permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission.value}' required"
            )
        return user
    return check


# ============================================================================
# APPLICATION
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("RPA Core API starting up...")
    # Initialize resources
    yield
    logger.info("RPA Core API shutting down...")


def create_app(title: str = "RPA Core API", version: str = "1.0.0") -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title=title,
        version=version,
        description="""
        RPA (Recursive Pattern Agent) Core API

        Unified backend for Web UI and Terminal UI.
        Provides endpoints for learning, progress tracking, and administration.

        ## Authentication
        All endpoints (except /auth/*) require JWT authentication.
        Include `Authorization: Bearer <token>` in requests.

        ## Roles
        - **superadmin**: Full system control
        - **admin**: User management and reports
        - **user**: Personal learning dashboard
        - **guest**: Limited demo access
        """,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register all routers
    _register_auth_routes(app)
    _register_user_routes(app)
    _register_learning_routes(app)
    _register_vocabulary_routes(app)
    _register_grammar_routes(app)
    _register_reading_routes(app)
    _register_writing_routes(app)
    _register_progress_routes(app)
    _register_admin_routes(app)
    _register_system_routes(app)

    return app


# ============================================================================
# AUTH ROUTES
# ============================================================================

def _register_auth_routes(app: FastAPI):
    """Register authentication routes."""

    @app.post("/auth/register", response_model=APIResponse[UserResponse], tags=["Auth"])
    async def register(user_data: UserCreate):
        """Register a new user."""
        try:
            user = auth_manager.create_user(
                email=user_data.email,
                username=user_data.username,
                password=user_data.password,
                role=user_data.role
            )
            return APIResponse(
                success=True,
                message="User registered successfully",
                data=UserResponse(**user)
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

    @app.post("/auth/login", tags=["Auth"])
    async def login(credentials: UserLogin):
        """Login and get access token."""
        user = auth_manager.authenticate(
            email=credentials.email,
            password=credentials.password
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        token = auth_manager.generate_token(
            user_id=user["user_id"],
            email=user["email"],
            role=user["role"]
        )

        return {
            "access_token": token,
            "token_type": "bearer",
            "user": user,
        }

    @app.post("/auth/logout", tags=["Auth"])
    async def logout(
        authorization: Optional[str] = Header(None)
    ):
        """Logout and invalidate token."""
        if authorization:
            parts = authorization.split()
            if len(parts) == 2:
                token = parts[1]
                auth_manager.invalidate_token(token)

        return {"message": "Logged out successfully"}

    @app.post("/auth/refresh", tags=["Auth"])
    async def refresh_token(user: Dict = Depends(get_current_user)):
        """Refresh access token."""
        new_token = auth_manager.generate_token(
            user_id=user["user_id"],
            email=user["email"],
            role=UserRole(user["role"])
        )

        return {
            "access_token": new_token,
            "token_type": "bearer",
        }


# ============================================================================
# USER ROUTES
# ============================================================================

def _register_user_routes(app: FastAPI):
    """Register user management routes."""

    @app.get("/users/me", response_model=APIResponse[UserResponse], tags=["Users"])
    async def get_current_user_info(user: Dict = Depends(get_current_user)):
        """Get current user information."""
        user_data = auth_manager.get_user_by_id(user["user_id"])
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return APIResponse(data=UserResponse(**user_data))

    @app.put("/users/me/preferences", tags=["Users"])
    async def update_preferences(
        preferences: UserPreferences,
        user: Dict = Depends(get_current_user)
    ):
        """Update user preferences."""
        auth_manager.update_user(user["email"], {"preferences": preferences.model_dump()})
        return {"message": "Preferences updated", "preferences": preferences}

    @app.get("/users/me/theme", tags=["Users"])
    async def get_user_theme(user: Dict = Depends(get_current_user)):
        """Get theme settings for current user's role."""
        theme = get_role_config(user["role"])
        return {
            "role": user["role"],
            "theme": theme.ui_theme if theme else {},
            "design_tokens": export_for_web() if True else export_for_terminal()
        }


# ============================================================================
# LEARNING ROUTES
# ============================================================================

def _register_learning_routes(app: FastAPI):
    """Register learning session routes."""

    @app.post("/learning/sessions", response_model=APIResponse[LearningSession], tags=["Learning"])
    async def create_learning_session(
        domain: DomainType = DomainType.ENGLISH,
        exercise_type: ExerciseType = ExerciseType.FLASHCARD,
        user: Dict = Depends(get_current_user)
    ):
        """Start a new learning session."""
        session = LearningSession(
            user_id=user["user_id"],
            domain=domain,
            exercise_type=exercise_type,
        )
        active_sessions[session.session_id] = session

        return APIResponse(
            message="Learning session started",
            data=session
        )

    @app.get("/learning/sessions/{session_id}", tags=["Learning"])
    async def get_session(
        session_id: str,
        user: Dict = Depends(get_current_user)
    ):
        """Get learning session status."""
        session = active_sessions.get(session_id)
        if not session or session.user_id != user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        return session.to_dict()

    @app.post("/learning/sessions/{session_id}/complete", tags=["Learning"])
    async def complete_session(
        session_id: str,
        user: Dict = Depends(get_current_user)
    ):
        """Complete a learning session."""
        session = active_sessions.get(session_id)
        if not session or session.user_id != user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        session.is_active = False

        # Update user progress
        progress = user_progress.get(user["user_id"], LearningProgress(user_id=user["user_id"]))
        progress.total_time_spent += (
            datetime.now() - session.started_at
        ).total_seconds() / 60
        progress.last_session = datetime.now()
        user_progress[user["user_id"]] = progress

        return {
            "message": "Session completed",
            "session": session.to_dict()
        }


# ============================================================================
# VOCABULARY ROUTES
# ============================================================================

def _register_vocabulary_routes(app: FastAPI):
    """Register vocabulary learning routes."""

    @app.get("/vocabulary/due", tags=["Vocabulary"])
    async def get_due_vocabulary(
        limit: int = Query(default=20, ge=1, le=100),
        user: Dict = Depends(get_current_user)
    ):
        """Get vocabulary items due for review."""
        due_items = vocabulary_trainer.get_due_reviews(limit=limit)

        return {
            "items": [item.to_dict() for item in due_items],
            "count": len(due_items)
        }

    @app.get("/vocabulary/new", tags=["Vocabulary"])
    async def get_new_vocabulary(
        limit: int = Query(default=10, ge=1, le=50),
        user: Dict = Depends(get_current_user)
    ):
        """Get new vocabulary items to learn."""
        new_items = vocabulary_trainer.get_new_vocabulary(limit=limit)

        return {
            "items": [item.to_dict() for item in new_items],
            "count": len(new_items)
        }

    @app.get("/vocabulary/statistics", tags=["Vocabulary"])
    async def get_vocabulary_statistics(user: Dict = Depends(get_current_user)):
        """Get vocabulary learning statistics."""
        stats = vocabulary_trainer.get_statistics()
        return stats

    @app.get("/vocabulary/{word_id}", tags=["Vocabulary"])
    async def get_vocabulary_item(
        word_id: str,
        user: Dict = Depends(get_current_user)
    ):
        """Get a specific vocabulary item."""
        item = vocabulary_trainer.get_vocabulary(word_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vocabulary item not found"
            )
        return item.to_dict()

    @app.get("/vocabulary/{word_id}/flashcard", tags=["Vocabulary"])
    async def get_vocabulary_flashcard(
        word_id: str,
        user: Dict = Depends(get_current_user)
    ):
        """Get a flashcard for vocabulary item."""
        item = vocabulary_trainer.get_vocabulary(word_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vocabulary item not found"
            )

        flashcard = vocabulary_trainer.generate_flashcard(item)
        return flashcard

    @app.get("/vocabulary/{word_id}/multiple-choice", tags=["Vocabulary"])
    async def get_vocabulary_multiple_choice(
        word_id: str,
        num_options: int = Query(default=4, ge=3, le=6),
        user: Dict = Depends(get_current_user)
    ):
        """Get a multiple choice question for vocabulary item."""
        item = vocabulary_trainer.get_vocabulary(word_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vocabulary item not found"
            )

        mc = vocabulary_trainer.generate_multiple_choice(item, num_options)
        return mc

    @app.post("/vocabulary/review", response_model=VocabularyReviewResponse, tags=["Vocabulary"])
    async def review_vocabulary(
        review: VocabularyReviewRequest,
        user: Dict = Depends(get_current_user)
    ):
        """Review a vocabulary item (SM-2 algorithm)."""
        try:
            result = vocabulary_trainer.review(
                word_id=review.word_id,
                quality=review.quality,
                response=review.response,
                time_spent=review.time_spent_seconds
            )

            return VocabularyReviewResponse(
                word_id=result.word_id,
                correct=result.correct,
                quality=result.quality,
                feedback=result.feedback,
                new_proficiency=ProficiencyLevel(
                    vocabulary_trainer.get_vocabulary(review.word_id).proficiency.value
                ),
                next_review=vocabulary_trainer.get_vocabulary(review.word_id).next_review,
                interval=vocabulary_trainer.get_vocabulary(review.word_id).interval
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )


# ============================================================================
# GRAMMAR ROUTES
# ============================================================================

def _register_grammar_routes(app: FastAPI):
    """Register grammar learning routes."""

    @app.get("/grammar/rules", tags=["Grammar"])
    async def list_grammar_rules(
        category: Optional[str] = None,
        min_difficulty: int = Query(default=1, ge=1),
        max_difficulty: int = Query(default=5, ge=1),
        user: Dict = Depends(get_current_user)
    ):
        """List grammar rules."""
        from ..domains.english import GrammarRuleType

        if category:
            try:
                cat_enum = GrammarRuleType(category)
                rules = grammar_engine.get_rules_by_category(cat_enum)
            except ValueError:
                rules = grammar_engine.get_rules_by_difficulty(min_difficulty, max_difficulty)
        else:
            rules = grammar_engine.get_rules_by_difficulty(min_difficulty, max_difficulty)

        return {
            "rules": [r.to_dict() for r in rules],
            "count": len(rules)
        }

    @app.get("/grammar/rules/{rule_id}", tags=["Grammar"])
    async def get_grammar_rule(
        rule_id: str,
        user: Dict = Depends(get_current_user)
    ):
        """Get a specific grammar rule."""
        rule = grammar_engine.get_rule(rule_id)
        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Grammar rule not found"
            )
        return rule.to_dict()

    @app.post("/grammar/exercise", tags=["Grammar"])
    async def get_grammar_exercise(
        request: GrammarExerciseRequest,
        user: Dict = Depends(get_current_user)
    ):
        """Generate a grammar exercise."""
        if request.rule_id:
            rule = grammar_engine.get_rule(request.rule_id)
            if not rule:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Grammar rule not found"
                )
        else:
            # Get random rule
            rules = grammar_engine.get_rules_by_difficulty(
                request.difficulty or 1,
                request.difficulty or 5
            )
            if not rules:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No grammar rules found"
                )
            import random
            rule = random.choice(rules)

        exercise = grammar_engine.generate_exercise(rule, request.exercise_type.value)
        return exercise

    @app.post("/grammar/check", tags=["Grammar"])
    async def check_grammar(
        request: GrammarCheckRequest,
        user: Dict = Depends(get_current_user)
    ):
        """Check text for grammar errors."""
        errors = grammar_engine.check_text(request.text)

        # Calculate score based on errors
        word_count = len(request.text.split())
        error_penalty = len(errors) * 0.1
        score = max(0.0, min(1.0, 1.0 - error_penalty))

        return GrammarCheckResponse(
            text=request.text,
            errors=[e.to_dict() for e in errors],
            suggestions=[e.suggestion for e in errors],
            score=score
        )


# ============================================================================
# READING ROUTES
# ============================================================================

def _register_reading_routes(app: FastAPI):
    """Register reading comprehension routes."""

    @app.get("/reading/content", tags=["Reading"])
    async def list_reading_content(
        level: Optional[int] = Query(default=None, ge=1, le=5),
        limit: int = Query(default=10, ge=1, le=50),
        user: Dict = Depends(get_current_user)
    ):
        """List available reading content."""
        # Placeholder - would be populated from content database
        sample_content = [
            ReadingContent(
                content_id="read_001",
                title="Introduction to Learning",
                text="Learning is a lifelong journey that begins with curiosity...",
                level=1,
                word_count=100,
                estimated_time=2.0,
                tags=["beginner", "education"]
            )
        ]

        return {
            "content": [c.model_dump() for c in sample_content],
            "count": len(sample_content)
        }

    @app.get("/reading/content/{content_id}", tags=["Reading"])
    async def get_reading_content(
        content_id: str,
        user: Dict = Depends(get_current_user)
    ):
        """Get reading content by ID."""
        # Placeholder
        content = ReadingContent(
            content_id=content_id,
            title="Sample Reading",
            text="This is sample reading content for comprehension practice.",
            level=1,
            word_count=10,
            estimated_time=1.0
        )
        return content.model_dump()


# ============================================================================
# WRITING ROUTES
# ============================================================================

def _register_writing_routes(app: FastAPI):
    """Register writing assessment routes."""

    @app.post("/writing/submit", tags=["Writing"])
    async def submit_writing(
        submission: WritingSubmission,
        user: Dict = Depends(get_current_user)
    ):
        """Submit writing for assessment."""
        # Create submission with user ID
        full_submission = WritingSubmission(
            submission_id=submission.submission_id,
            user_id=user["user_id"],
            topic=submission.topic,
            text=submission.text,
            word_count=len(submission.text.split()),
            submitted_at=datetime.now()
        )

        # Basic assessment (would use AI/ML in production)
        assessment = WritingAssessment(
            submission_id=full_submission.submission_id,
            overall_score=75.0,
            grammar_score=80.0,
            vocabulary_score=70.0,
            coherence_score=75.0,
            structure_score=70.0,
            content_score=80.0,
            strengths=["Clear topic presentation", "Good vocabulary usage"],
            weaknesses=["Minor grammar issues", "Could use more examples"],
            suggestions=["Consider using transition words", "Add supporting examples"]
        )

        # Update user progress
        progress = user_progress.get(user["user_id"], LearningProgress(user_id=user["user_id"]))
        progress.essays_written += 1
        progress.average_score = (
            (progress.average_score * (progress.essays_written - 1) + assessment.overall_score)
            / progress.essays_written
        )
        user_progress[user["user_id"]] = progress

        return {
            "submission": full_submission.model_dump(),
            "assessment": assessment.model_dump()
        }


# ============================================================================
# PROGRESS ROUTES
# ============================================================================

def _register_progress_routes(app: FastAPI):
    """Register progress tracking routes."""

    @app.get("/progress", tags=["Progress"])
    async def get_progress(user: Dict = Depends(get_current_user)):
        """Get user's learning progress."""
        progress = user_progress.get(user["user_id"])
        if not progress:
            progress = LearningProgress(user_id=user["user_id"])

            # Populate from vocabulary trainer
            stats = vocabulary_trainer.get_statistics()
            progress.total_words = stats["total_words"]
            progress.mastered_words = stats["by_proficiency"].get("mastered", 0)
            progress.learning_words = stats["by_proficiency"].get("learning", 0)
            progress.new_words = stats["by_proficiency"].get("new", 0)

        return progress.to_dict()

    @app.get("/dashboard", response_model=DashboardData, tags=["Progress"])
    async def get_dashboard(user: Dict = Depends(get_current_user)):
        """Get dashboard data for user home screen."""
        user_data = auth_manager.get_user_by_id(user["user_id"])
        progress = user_progress.get(user["user_id"], LearningProgress(user_id=user["user_id"]))

        # Get due items
        due_vocab = vocabulary_trainer.get_due_reviews(limit=1)

        return DashboardData(
            user=UserResponse(**user_data) if user_data else None,
            progress=progress,
            due_vocabulary=len(vocabulary_trainer.get_due_reviews(limit=100)),
            due_grammar=0,
            recent_sessions=[],
            recommended_next=["vocabulary", "grammar"],
            today_items=0,
            today_time=0.0
        )

    @app.get("/progress/streak", tags=["Progress"])
    async def get_streak(user: Dict = Depends(get_current_user)):
        """Get user's learning streak."""
        progress = user_progress.get(user["user_id"], LearningProgress(user_id=user["user_id"]))
        return {
            "current_streak": progress.current_streak,
            "longest_streak": progress.longest_streak
        }


# ============================================================================
# ADMIN ROUTES
# ============================================================================

def _register_admin_routes(app: FastAPI):
    """Register admin routes."""

    @app.get("/admin/users", tags=["Admin"])
    async def list_users(
        user: Dict = Depends(require_permission_dependency(Permission.MANAGE_USERS))
    ):
        """List all users (admin+)."""
        users = auth_manager.list_users()
        return {"users": users, "count": len(users)}

    @app.put("/admin/users/{email}", tags=["Admin"])
    async def update_user(
        email: str,
        updates: AdminUserUpdate,
        user: Dict = Depends(require_permission_dependency(Permission.MANAGE_USERS))
    ):
        """Update a user (admin+)."""
        update_data = {}
        if updates.role:
            update_data["role"] = updates.role
        if updates.is_active is not None:
            update_data["is_active"] = updates.is_active
        if updates.preferences:
            update_data["preferences"] = updates.preferences.model_dump()

        result = auth_manager.update_user(email, update_data)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return {"message": "User updated", "user": result}

    @app.delete("/admin/users/{email}", tags=["Admin"])
    async def delete_user(
        email: str,
        user: Dict = Depends(require_permission_dependency(Permission.DELETE_USERS))
    ):
        """Delete a user (superadmin only)."""
        if not auth_manager.delete_user(email):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return {"message": "User deleted"}

    @app.get("/admin/sessions", tags=["Admin"])
    async def list_active_sessions(
        user: Dict = Depends(require_permission_dependency(Permission.MANAGE_USERS))
    ):
        """List active sessions (admin+)."""
        sessions = auth_manager.get_active_sessions()
        return {"sessions": sessions, "count": len(sessions)}

    @app.get("/admin/reports", tags=["Admin"])
    async def get_reports(
        report_type: str = Query(default="summary"),
        user: Dict = Depends(require_permission_dependency(Permission.VIEW_REPORTS))
    ):
        """Get admin reports."""
        return {
            "report_type": report_type,
            "generated_at": datetime.now().isoformat(),
            "data": {
                "total_users": len(auth_manager.list_users()),
                "total_sessions": len(active_sessions),
                "vocabulary_stats": vocabulary_trainer.get_statistics(),
            }
        }


# ============================================================================
# SYSTEM ROUTES
# ============================================================================

def _register_system_routes(app: FastAPI):
    """Register system routes."""

    @app.get("/health", tags=["System"])
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "service": "rpa_core_api"}

    @app.get("/status", response_model=SystemStatus, tags=["System"])
    async def get_system_status(user: Optional[Dict] = Depends(get_current_user_optional)):
        """Get system status."""
        vocab_stats = vocabulary_trainer.get_statistics()

        return SystemStatus(
            status="healthy",
            version="1.0.0",
            stm_patterns=0,
            ltm_patterns=vocab_stats["total_words"],
            total_episodes=0,
            total_users=len(auth_manager.list_users()),
            active_users=len([s for s in active_sessions.values() if s.is_active]),
            domains=["english", "python"],
        )

    @app.get("/design-tokens", tags=["System"])
    async def get_design_tokens(
        platform: str = Query(default="web", pattern="^(web|terminal)$")
    ):
        """Get design tokens for UI consistency."""
        if platform == "terminal":
            return export_for_terminal()
        return export_for_web()

    @app.get("/memory/snapshot", tags=["System"])
    async def get_memory_snapshot(
        user: Dict = Depends(require_permission_dependency(Permission.ACCESS_RAW_DATA))
    ):
        """Get memory system snapshot (superadmin only)."""
        return MemorySnapshot().model_dump()


# ============================================================================
# RUN SERVER
# ============================================================================

def run_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """Run the FastAPI server."""
    import uvicorn

    app = create_app()
    uvicorn.run(
        "rpa.core_api.server:create_app",
        host=host,
        port=port,
        reload=reload,
        factory=True
    )


# Create default app instance
app = create_app()


if __name__ == "__main__":
    run_server()
