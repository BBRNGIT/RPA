"""
API Client for Terminal UI.

Communicates with the RPA Core API backend, providing the same
interface as the Web UI. Supports both online (HTTP) and offline
(direct module import) modes.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import logging

# Add parent path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Try to import httpx for HTTP mode
try:
    import httpx
    HTTP_AVAILABLE = True
except ImportError:
    HTTP_AVAILABLE = False

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages CLI configuration and authentication."""

    CONFIG_DIR = Path.home() / ".rpa"
    CONFIG_FILE = CONFIG_DIR / "config.json"
    AUTH_FILE = CONFIG_DIR / "auth.json"

    def __init__(self):
        self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    def save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to file."""
        with open(self.CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if self.CONFIG_FILE.exists():
            with open(self.CONFIG_FILE, 'r') as f:
                return json.load(f)
        return {
            "api_url": "http://localhost:8000",
            "theme": "dark",
            "editor": os.environ.get("EDITOR", "vim"),
        }

    def save_auth(self, token: str, user: Dict[str, Any]) -> None:
        """Save authentication data."""
        auth_data = {
            "token": token,
            "user": user,
            "saved_at": datetime.now().isoformat(),
        }
        with open(self.AUTH_FILE, 'w') as f:
            json.dump(auth_data, f, indent=2)
        # Set restrictive permissions
        os.chmod(self.AUTH_FILE, 0o600)

    def load_auth(self) -> Optional[Dict[str, Any]]:
        """Load authentication data."""
        if self.AUTH_FILE.exists():
            with open(self.AUTH_FILE, 'r') as f:
                return json.load(f)
        return None

    def clear_auth(self) -> None:
        """Clear saved authentication."""
        if self.AUTH_FILE.exists():
            os.remove(self.AUTH_FILE)

    def get_token(self) -> Optional[str]:
        """Get saved token."""
        auth = self.load_auth()
        return auth.get("token") if auth else None

    def get_user(self) -> Optional[Dict[str, Any]]:
        """Get saved user data."""
        auth = self.load_auth()
        return auth.get("user") if auth else None


class APIClient:
    """
    API client for communicating with RPA Core API.

    Supports two modes:
    1. HTTP mode: Connect to running FastAPI server
    2. Direct mode: Import modules directly (offline)
    """

    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self.config = ConfigManager()
        self.token: Optional[str] = None
        self.user: Optional[Dict[str, Any]] = None

        # Load saved auth
        self._load_saved_auth()

        # Direct mode components (for offline use)
        self._direct_mode = False
        self._auth_manager = None
        self._vocabulary_trainer = None
        self._grammar_engine = None

    def _load_saved_auth(self) -> None:
        """Load saved authentication."""
        self.token = self.config.get_token()
        self.user = self.config.get_user()

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with auth."""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _init_direct_mode(self) -> None:
        """Initialize direct mode components."""
        if self._direct_mode:
            return

        try:
            from ..core_api.auth import AuthManager
            from ..domains.english import VocabularyTrainer, GrammarEngine

            self._auth_manager = AuthManager()
            self._vocabulary_trainer = VocabularyTrainer()
            self._grammar_engine = GrammarEngine()
            self._direct_mode = True
        except ImportError as e:
            logger.warning(f"Direct mode unavailable: {e}")

    # =========================================================================
    # Authentication
    # =========================================================================

    def login(self, email: str, password: str) -> Dict[str, Any]:
        """
        Login to RPA.

        Args:
            email: User email
            password: User password

        Returns:
            Login response with token and user data
        """
        # Try direct mode first
        self._init_direct_mode()

        if self._direct_mode and self._auth_manager:
            user = self._auth_manager.authenticate(email, password)
            if user:
                token = self._auth_manager.generate_token(
                    user["user_id"],
                    user["email"],
                    user["role"]
                )
                self.token = token
                self.user = user
                self.config.save_auth(token, user)
                return {"success": True, "token": token, "user": user}
            return {"success": False, "error": "Invalid credentials"}

        # HTTP mode
        if HTTP_AVAILABLE:
            try:
                response = httpx.post(
                    f"{self.api_url}/auth/login",
                    json={"email": email, "password": password},
                    timeout=10.0
                )
                if response.status_code == 200:
                    data = response.json()
                    self.token = data["access_token"]
                    self.user = data["user"]
                    self.config.save_auth(self.token, self.user)
                    return {"success": True, **data}
                return {"success": False, "error": response.json().get("detail", "Login failed")}
            except Exception as e:
                return {"success": False, "error": str(e)}

        return {"success": False, "error": "No authentication method available"}

    def logout(self) -> bool:
        """Logout and clear saved auth."""
        self.token = None
        self.user = None
        self.config.clear_auth()
        return True

    def is_authenticated(self) -> bool:
        """Check if authenticated."""
        return self.token is not None

    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get current user."""
        return self.user

    # =========================================================================
    # Vocabulary
    # =========================================================================

    def get_due_vocabulary(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get vocabulary items due for review."""
        if self._direct_mode and self._vocabulary_trainer:
            items = self._vocabulary_trainer.get_due_reviews(limit)
            return [item.to_dict() for item in items]

        if HTTP_AVAILABLE and self.token:
            try:
                response = httpx.get(
                    f"{self.api_url}/vocabulary/due",
                    params={"limit": limit},
                    headers=self._get_headers(),
                    timeout=10.0
                )
                if response.status_code == 200:
                    return response.json()["items"]
            except Exception as e:
                logger.error(f"Failed to get due vocabulary: {e}")

        return []

    def get_new_vocabulary(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get new vocabulary items."""
        if self._direct_mode and self._vocabulary_trainer:
            items = self._vocabulary_trainer.get_new_vocabulary(limit)
            return [item.to_dict() for item in items]

        if HTTP_AVAILABLE and self.token:
            try:
                response = httpx.get(
                    f"{self.api_url}/vocabulary/new",
                    params={"limit": limit},
                    headers=self._get_headers(),
                    timeout=10.0
                )
                if response.status_code == 200:
                    return response.json()["items"]
            except Exception as e:
                logger.error(f"Failed to get new vocabulary: {e}")

        return []

    def get_vocabulary_flashcard(self, word_id: str) -> Optional[Dict[str, Any]]:
        """Get flashcard for vocabulary item."""
        if self._direct_mode and self._vocabulary_trainer:
            item = self._vocabulary_trainer.get_vocabulary(word_id)
            if item:
                return self._vocabulary_trainer.generate_flashcard(item)

        if HTTP_AVAILABLE and self.token:
            try:
                response = httpx.get(
                    f"{self.api_url}/vocabulary/{word_id}/flashcard",
                    headers=self._get_headers(),
                    timeout=10.0
                )
                if response.status_code == 200:
                    return response.json()
            except Exception as e:
                logger.error(f"Failed to get flashcard: {e}")

        return None

    def review_vocabulary(
        self,
        word_id: str,
        quality: int,
        response: str = "",
        time_spent: float = 0.0
    ) -> Optional[Dict[str, Any]]:
        """Submit vocabulary review."""
        if self._direct_mode and self._vocabulary_trainer:
            try:
                result = self._vocabulary_trainer.review(
                    word_id=word_id,
                    quality=quality,
                    response=response,
                    time_spent=time_spent
                )
                return result.to_dict()
            except ValueError as e:
                logger.error(f"Review failed: {e}")
                return None

        if HTTP_AVAILABLE and self.token:
            try:
                response = httpx.post(
                    f"{self.api_url}/vocabulary/review",
                    json={
                        "word_id": word_id,
                        "quality": quality,
                        "response": response,
                        "time_spent_seconds": time_spent
                    },
                    headers=self._get_headers(),
                    timeout=10.0
                )
                if response.status_code == 200:
                    return response.json()
            except Exception as e:
                logger.error(f"Failed to submit review: {e}")

        return None

    def get_vocabulary_stats(self) -> Dict[str, Any]:
        """Get vocabulary statistics."""
        if self._direct_mode and self._vocabulary_trainer:
            return self._vocabulary_trainer.get_statistics()

        if HTTP_AVAILABLE and self.token:
            try:
                response = httpx.get(
                    f"{self.api_url}/vocabulary/statistics",
                    headers=self._get_headers(),
                    timeout=10.0
                )
                if response.status_code == 200:
                    return response.json()
            except Exception as e:
                logger.error(f"Failed to get stats: {e}")

        return {}

    # =========================================================================
    # Grammar
    # =========================================================================

    def get_grammar_rules(
        self,
        category: Optional[str] = None,
        min_difficulty: int = 1,
        max_difficulty: int = 5
    ) -> List[Dict[str, Any]]:
        """Get grammar rules."""
        if self._direct_mode and self._grammar_engine:
            rules = self._grammar_engine.get_rules_by_difficulty(min_difficulty, max_difficulty)
            return [r.to_dict() for r in rules]

        if HTTP_AVAILABLE and self.token:
            try:
                params = {"min_difficulty": min_difficulty, "max_difficulty": max_difficulty}
                if category:
                    params["category"] = category
                response = httpx.get(
                    f"{self.api_url}/grammar/rules",
                    params=params,
                    headers=self._get_headers(),
                    timeout=10.0
                )
                if response.status_code == 200:
                    return response.json()["rules"]
            except Exception as e:
                logger.error(f"Failed to get grammar rules: {e}")

        return []

    def get_grammar_exercise(
        self,
        rule_id: Optional[str] = None,
        exercise_type: str = "multiple_choice"
    ) -> Optional[Dict[str, Any]]:
        """Get grammar exercise."""
        if self._direct_mode and self._grammar_engine:
            import random
            rules = self._grammar_engine.get_rules_by_difficulty(1, 5)
            if rules:
                rule = random.choice(rules) if not rule_id else self._grammar_engine.get_rule(rule_id)
                if rule:
                    return self._grammar_engine.generate_exercise(rule, exercise_type)

        if HTTP_AVAILABLE and self.token:
            try:
                json_data = {"exercise_type": exercise_type}
                if rule_id:
                    json_data["rule_id"] = rule_id
                response = httpx.post(
                    f"{self.api_url}/grammar/exercise",
                    json=json_data,
                    headers=self._get_headers(),
                    timeout=10.0
                )
                if response.status_code == 200:
                    return response.json()
            except Exception as e:
                logger.error(f"Failed to get exercise: {e}")

        return None

    def check_grammar(self, text: str) -> Dict[str, Any]:
        """Check text for grammar errors."""
        if self._direct_mode and self._grammar_engine:
            errors = self._grammar_engine.check_text(text)
            return {
                "text": text,
                "errors": [e.to_dict() for e in errors],
                "score": max(0, 1.0 - len(errors) * 0.1)
            }

        if HTTP_AVAILABLE and self.token:
            try:
                response = httpx.post(
                    f"{self.api_url}/grammar/check",
                    json={"text": text},
                    headers=self._get_headers(),
                    timeout=10.0
                )
                if response.status_code == 200:
                    return response.json()
            except Exception as e:
                logger.error(f"Failed to check grammar: {e}")

        return {"text": text, "errors": [], "score": 1.0}

    # =========================================================================
    # Progress & Dashboard
    # =========================================================================

    def get_dashboard(self) -> Dict[str, Any]:
        """Get dashboard data."""
        if HTTP_AVAILABLE and self.token:
            try:
                response = httpx.get(
                    f"{self.api_url}/dashboard",
                    headers=self._get_headers(),
                    timeout=10.0
                )
                if response.status_code == 200:
                    return response.json()
            except Exception as e:
                logger.error(f"Failed to get dashboard: {e}")

        # Fallback to vocabulary stats
        vocab_stats = self.get_vocabulary_stats()
        return {
            "progress": vocab_stats,
            "due_vocabulary": len(self.get_due_vocabulary(100)),
        }

    def get_progress(self) -> Dict[str, Any]:
        """Get user progress."""
        if HTTP_AVAILABLE and self.token:
            try:
                response = httpx.get(
                    f"{self.api_url}/progress",
                    headers=self._get_headers(),
                    timeout=10.0
                )
                if response.status_code == 200:
                    return response.json()
            except Exception as e:
                logger.error(f"Failed to get progress: {e}")

        return self.get_vocabulary_stats()

    # =========================================================================
    # Admin
    # =========================================================================

    def list_users(self) -> List[Dict[str, Any]]:
        """List all users (admin only)."""
        if self._direct_mode and self._auth_manager:
            return self._auth_manager.list_users()

        if HTTP_AVAILABLE and self.token:
            try:
                response = httpx.get(
                    f"{self.api_url}/admin/users",
                    headers=self._get_headers(),
                    timeout=10.0
                )
                if response.status_code == 200:
                    return response.json()["users"]
            except Exception as e:
                logger.error(f"Failed to list users: {e}")

        return []

    def update_user(self, email: str, updates: Dict[str, Any]) -> bool:
        """Update user (admin only)."""
        if self._direct_mode and self._auth_manager:
            result = self._auth_manager.update_user(email, updates)
            return result is not None

        if HTTP_AVAILABLE and self.token:
            try:
                response = httpx.put(
                    f"{self.api_url}/admin/users/{email}",
                    json=updates,
                    headers=self._get_headers(),
                    timeout=10.0
                )
                return response.status_code == 200
            except Exception as e:
                logger.error(f"Failed to update user: {e}")

        return False

    # =========================================================================
    # System
    # =========================================================================

    def health_check(self) -> bool:
        """Check API health."""
        if HTTP_AVAILABLE:
            try:
                response = httpx.get(
                    f"{self.api_url}/health",
                    timeout=5.0
                )
                return response.status_code == 200
            except Exception:
                return False

        return self._direct_mode

    def get_design_tokens(self, platform: str = "terminal") -> Dict[str, Any]:
        """Get design tokens for theming."""
        if self._direct_mode:
            try:
                from ..core_api.design_tokens import export_for_terminal
                return export_for_terminal()
            except ImportError:
                pass

        if HTTP_AVAILABLE:
            try:
                response = httpx.get(
                    f"{self.api_url}/design-tokens",
                    params={"platform": platform},
                    timeout=10.0
                )
                if response.status_code == 200:
                    return response.json()
            except Exception as e:
                logger.error(f"Failed to get design tokens: {e}")

        # Default tokens
        return {
            "colors": {
                "primary": "blue",
                "success": "green",
                "warning": "yellow",
                "danger": "red",
            }
        }
