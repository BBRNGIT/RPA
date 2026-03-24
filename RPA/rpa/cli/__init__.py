"""
Terminal UI Module for RPA.

Provides a rich terminal interface that shares the same backend
as the Web UI, ensuring consistent user experience across platforms.

Features:
- Interactive menus with keyboard navigation
- Vocabulary flashcards with SM-2 spaced repetition
- Grammar exercises
- Progress tracking with ASCII charts
- Admin tools for user management
- Role-based theming

Usage:
    rpa login                    # Login to RPA
    rpa dashboard                # Show dashboard
    rpa learn vocabulary         # Start vocabulary learning
    rpa learn grammar            # Start grammar exercises
    rpa progress                 # View progress
    rpa admin users              # Admin: manage users
"""

from .app import RPAApp, run_cli
from .client import APIClient
from .screens import (
    LoginScreen,
    DashboardScreen,
    VocabularyScreen,
    GrammarScreen,
    ProgressScreen,
    AdminScreen,
)
from .widgets import (
    Flashcard,
    ProgressBar,
    AsciiChart,
    Menu,
    StatusBox,
)

__all__ = [
    # Main app
    "RPAApp",
    "run_cli",

    # API client
    "APIClient",

    # Screens
    "LoginScreen",
    "DashboardScreen",
    "VocabularyScreen",
    "GrammarScreen",
    "ProgressScreen",
    "AdminScreen",

    # Widgets
    "Flashcard",
    "ProgressBar",
    "AsciiChart",
    "Menu",
    "StatusBox",
]
