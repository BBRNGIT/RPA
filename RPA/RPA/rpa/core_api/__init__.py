"""
Core API Module - Unified Backend for Web UI and Terminal UI.

This module provides a FastAPI-based backend that serves as the single source
of truth for all RPA interfaces, ensuring consistent behavior across:
- Web UI (Next.js)
- Terminal UI (Textual)
- GitHub Actions (background tasks)

Key Components:
- Authentication (JWT-based)
- User Roles & Permissions
- Learning Endpoints
- Progress Tracking
- Admin Tools
- Design Tokens (unified visual language)
"""

from .models import (
    # User models
    UserBase,
    UserCreate,
    UserLogin,
    UserResponse,
    UserRole,
    UserPreferences,
    UserSession,

    # Learning models
    LearningSession,
    LearningProgress,
    VocabularyReviewRequest,
    VocabularyReviewResponse,
    GrammarExerciseRequest,
    GrammarExerciseResponse,
    ReadingContent,
    WritingSubmission,

    # State models
    SystemStatus,
    DashboardData,
    APIResponse,

    # Memory models
    MemorySnapshot,
    KnowledgeExport,
)

from .auth import (
    AuthManager,
    create_access_token,
    verify_token,
    get_current_user,
    require_role,
)

from .user_roles import (
    Permission,
    RolePermissions,
    check_permission,
    get_role_permissions,
)

from .design_tokens import (
    DESIGN_TOKENS,
    get_color,
    get_spacing,
    get_typography,
)

from .server import (
    create_app,
    run_server,
)

__all__ = [
    # Models
    "UserBase",
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "UserRole",
    "UserPreferences",
    "UserSession",
    "LearningSession",
    "LearningProgress",
    "VocabularyReviewRequest",
    "VocabularyReviewResponse",
    "GrammarExerciseRequest",
    "GrammarExerciseResponse",
    "ReadingContent",
    "WritingSubmission",
    "SystemStatus",
    "DashboardData",
    "APIResponse",
    "MemorySnapshot",
    "KnowledgeExport",

    # Auth
    "AuthManager",
    "create_access_token",
    "verify_token",
    "get_current_user",
    "require_role",

    # Roles
    "Permission",
    "RolePermissions",
    "check_permission",
    "get_role_permissions",

    # Design
    "DESIGN_TOKENS",
    "get_color",
    "get_spacing",
    "get_typography",

    # Server
    "create_app",
    "run_server",
]
