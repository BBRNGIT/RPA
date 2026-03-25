"""
JWT Authentication System for Core API.

Provides secure authentication for Web UI, Terminal UI, and API access.
Supports:
- JWT token generation and validation
- Role-based access control
- Session management
- API key authentication (for CLI/tools)
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Callable
import hashlib
import hmac
import os
import secrets
import logging

from pydantic import BaseModel

from .models import UserRole, UserSession

logger = logging.getLogger(__name__)

# Configuration
JWT_SECRET_KEY = os.environ.get("RPA_JWT_SECRET", secrets.token_hex(32))
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24
JWT_REFRESH_EXPIRATION_DAYS = 7

# Try to import JWT library
try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    jwt = None
    logger.warning("PyJWT not installed. Using simplified token system.")


class TokenData(BaseModel):
    """Data embedded in JWT token."""
    user_id: str
    email: str
    role: UserRole
    session_id: str
    exp: datetime
    iat: datetime
    permissions: list = []


class AuthManager:
    """
    Authentication manager for RPA.

    Handles:
    - User authentication
    - Token generation and validation
    - Session management
    - API key management
    """

    def __init__(self, secret_key: Optional[str] = None):
        """
        Initialize the auth manager.

        Args:
            secret_key: Optional custom secret key for JWT signing
        """
        self.secret_key = secret_key or JWT_SECRET_KEY
        self._active_sessions: Dict[str, UserSession] = {}
        self._api_keys: Dict[str, Dict[str, Any]] = {}
        self._users_db: Dict[str, Dict[str, Any]] = {}  # In-memory user store

        # Initialize with default superadmin
        self._initialize_default_users()

    def _initialize_default_users(self) -> None:
        """Initialize default users for development/testing."""
        # Default superadmin (using .test domain which is valid for testing)
        self._users_db["superadmin@rpa.test"] = {
            "user_id": "user_superadmin",
            "email": "superadmin@rpa.test",
            "username": "superadmin",
            "password_hash": self._hash_password("admin123"),  # Change in production!
            "role": UserRole.SUPERADMIN,
            "created_at": datetime.now(),
            "is_active": True,
        }

        # Default admin
        self._users_db["admin@rpa.test"] = {
            "user_id": "user_admin",
            "email": "admin@rpa.test",
            "username": "admin",
            "password_hash": self._hash_password("admin123"),
            "role": UserRole.ADMIN,
            "created_at": datetime.now(),
            "is_active": True,
        }

        # Default user
        self._users_db["user@rpa.test"] = {
            "user_id": "user_default",
            "email": "user@rpa.test",
            "username": "user",
            "password_hash": self._hash_password("user123"),
            "role": UserRole.USER,
            "created_at": datetime.now(),
            "is_active": True,
        }

    def _hash_password(self, password: str) -> str:
        """Hash a password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify a password against its hash."""
        return hmac.compare_digest(self._hash_password(password), password_hash)

    def create_user(
        self,
        email: str,
        username: str,
        password: str,
        role: UserRole = UserRole.USER
    ) -> Dict[str, Any]:
        """
        Create a new user.

        Args:
            email: User's email
            username: Username
            password: Plain text password
            role: User role

        Returns:
            User data dictionary
        """
        if email in self._users_db:
            raise ValueError(f"User {email} already exists")

        user_id = f"user_{secrets.token_hex(8)}"
        user_data = {
            "user_id": user_id,
            "email": email,
            "username": username,
            "password_hash": self._hash_password(password),
            "role": role,
            "created_at": datetime.now(),
            "is_active": True,
        }

        self._users_db[email] = user_data
        logger.info(f"Created user: {email} with role: {role}")

        return {k: v for k, v in user_data.items() if k != "password_hash"}

    def authenticate(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate a user.

        Args:
            email: User's email
            password: Plain text password

        Returns:
            User data if authenticated, None otherwise
        """
        user_data = self._users_db.get(email)
        if not user_data:
            return None

        if not user_data["is_active"]:
            return None

        if not self.verify_password(password, user_data["password_hash"]):
            return None

        # Update last login
        user_data["last_login"] = datetime.now()

        return {k: v for k, v in user_data.items() if k != "password_hash"}

    def generate_token(
        self,
        user_id: str,
        email: str,
        role: UserRole,
        session_id: Optional[str] = None,
        expires_hours: int = JWT_EXPIRATION_HOURS
    ) -> str:
        """
        Generate a JWT token.

        Args:
            user_id: User's ID
            email: User's email
            role: User's role
            session_id: Optional session ID
            expires_hours: Token expiration in hours

        Returns:
            JWT token string
        """
        now = datetime.utcnow()
        exp = now + timedelta(hours=expires_hours)

        session_id = session_id or f"sess_{secrets.token_hex(8)}"

        payload = {
            "user_id": user_id,
            "email": email,
            "role": role.value,
            "session_id": session_id,
            "iat": now,
            "exp": exp,
            "permissions": get_role_permissions(role),
        }

        if JWT_AVAILABLE:
            token = jwt.encode(payload, self.secret_key, algorithm=JWT_ALGORITHM)
        else:
            # Simplified token for when PyJWT is not available
            token = self._create_simple_token(payload)

        # Track session
        self._active_sessions[session_id] = UserSession(
            session_id=session_id,
            user_id=user_id,
            role=role,
            started_at=now,
            last_activity=now,
        )

        return token

    def _create_simple_token(self, payload: Dict[str, Any]) -> str:
        """Create a simple token when JWT is not available."""
        import base64
        import json

        # Simple base64 encoding with signature
        data = base64.urlsafe_b64encode(json.dumps(payload).encode())
        signature = hmac.new(
            self.secret_key.encode(),
            data,
            hashlib.sha256
        ).hexdigest()

        return f"{data.decode()}.{signature}"

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify and decode a JWT token.

        Args:
            token: JWT token string

        Returns:
            Decoded token payload if valid, None otherwise
        """
        try:
            if JWT_AVAILABLE:
                payload = jwt.decode(
                    token,
                    self.secret_key,
                    algorithms=[JWT_ALGORITHM]
                )
            else:
                # Verify simple token
                parts = token.split(".")
                if len(parts) != 2:
                    return None

                data, signature = parts
                expected_sig = hmac.new(
                    self.secret_key.encode(),
                    data.encode(),
                    hashlib.sha256
                ).hexdigest()

                if not hmac.compare_digest(signature, expected_sig):
                    return None

                import base64
                import json
                payload = json.loads(base64.urlsafe_b64decode(data))

            # Check expiration
            if datetime.utcnow() > datetime.fromtimestamp(payload["exp"]):
                return None

            # Update session activity
            session_id = payload.get("session_id")
            if session_id in self._active_sessions:
                self._active_sessions[session_id].last_activity = datetime.now()

            return payload

        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            return None

    def invalidate_token(self, token: str) -> bool:
        """
        Invalidate a token (logout).

        Args:
            token: JWT token to invalidate

        Returns:
            True if token was invalidated
        """
        payload = self.verify_token(token)
        if not payload:
            return False

        session_id = payload.get("session_id")
        if session_id in self._active_sessions:
            del self._active_sessions[session_id]

        return True

    def get_user(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email."""
        user_data = self._users_db.get(email)
        if user_data:
            return {k: v for k, v in user_data.items() if k != "password_hash"}
        return None

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        for user in self._users_db.values():
            if user["user_id"] == user_id:
                return {k: v for k, v in user.items() if k != "password_hash"}
        return None

    def update_user(self, email: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update user data."""
        if email not in self._users_db:
            return None

        user = self._users_db[email]

        # Allowed updates
        if "username" in updates:
            user["username"] = updates["username"]
        if "role" in updates:
            user["role"] = updates["role"]
        if "is_active" in updates:
            user["is_active"] = updates["is_active"]
        if "preferences" in updates:
            user["preferences"] = updates["preferences"]

        return {k: v for k, v in user.items() if k != "password_hash"}

    def delete_user(self, email: str) -> bool:
        """Delete a user."""
        if email in self._users_db:
            del self._users_db[email]
            return True
        return False

    def list_users(self) -> list:
        """List all users."""
        return [
            {k: v for k, v in user.items() if k != "password_hash"}
            for user in self._users_db.values()
        ]

    def generate_api_key(
        self,
        user_id: str,
        name: str,
        permissions: list = None
    ) -> str:
        """
        Generate an API key for programmatic access.

        Args:
            user_id: User ID
            name: API key name/description
            permissions: List of permissions

        Returns:
            API key string
        """
        api_key = f"rpa_{secrets.token_hex(16)}"

        self._api_keys[api_key] = {
            "user_id": user_id,
            "name": name,
            "permissions": permissions or [],
            "created_at": datetime.now(),
            "last_used": None,
        }

        return api_key

    def verify_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Verify an API key."""
        key_data = self._api_keys.get(api_key)
        if key_data:
            key_data["last_used"] = datetime.now()
            return key_data
        return None

    def get_active_sessions(self) -> list:
        """Get all active sessions."""
        return [s.to_dict() for s in self._active_sessions.values()]


def get_role_permissions(role: UserRole) -> list:
    """Get permissions for a role."""
    permissions = {
        UserRole.SUPERADMIN: [
            "read", "write", "delete", "manage_users", "manage_system",
            "view_reports", "export_data", "configure_workflows", "access_raw_data"
        ],
        UserRole.ADMIN: [
            "read", "write", "manage_users", "view_reports", "edit_curriculum",
            "trigger_learning"
        ],
        UserRole.USER: [
            "read", "write", "view_own_progress", "practice_learning"
        ],
        UserRole.GUEST: [
            "read", "demo_access"
        ],
    }
    return permissions.get(role, [])


# Convenience functions for FastAPI dependencies

def create_access_token(
    user_id: str,
    email: str,
    role: UserRole,
    auth_manager: Optional[AuthManager] = None
) -> str:
    """Create an access token for a user."""
    if auth_manager is None:
        auth_manager = AuthManager()
    return auth_manager.generate_token(user_id, email, role)


def verify_token(token: str, auth_manager: Optional[AuthManager] = None) -> Optional[Dict[str, Any]]:
    """Verify an access token."""
    if auth_manager is None:
        auth_manager = AuthManager()
    return auth_manager.verify_token(token)


def get_current_user(token: str, auth_manager: Optional[AuthManager] = None) -> Optional[Dict[str, Any]]:
    """Get the current user from a token."""
    payload = verify_token(token, auth_manager)
    if not payload:
        return None

    if auth_manager is None:
        auth_manager = AuthManager()

    return auth_manager.get_user_by_id(payload["user_id"])


def require_role(*required_roles: UserRole) -> Callable:
    """
    Decorator to require specific roles.

    Usage:
        @require_role(UserRole.ADMIN, UserRole.SUPERADMIN)
        async def admin_endpoint():
            ...
    """
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, token: str = None, **kwargs):
            if token is None:
                raise PermissionError("Authentication required")

            payload = verify_token(token)
            if not payload:
                raise PermissionError("Invalid token")

            user_role = UserRole(payload["role"])
            if user_role not in required_roles:
                raise PermissionError(f"Role {user_role} not authorized")

            return await func(*args, **kwargs)

        return wrapper
    return decorator
