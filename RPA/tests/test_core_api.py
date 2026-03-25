"""
Tests for RPA Core API.

Tests all endpoints, authentication, and authorization.
"""

import pytest
import sys
import os

# Add project path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

from rpa.core_api.server import create_app, auth_manager
from rpa.core_api.models import UserRole, UserCreate, UserLogin
from rpa.core_api.auth import AuthManager
from rpa.core_api.user_roles import (
    check_permission, get_role_config, Permission,
    ROLE_DEFINITIONS, validate_role_transition
)
from rpa.core_api.design_tokens import (
    get_color, get_spacing, get_typography,
    export_for_web, export_for_terminal, DESIGN_TOKENS
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def auth_headers_superadmin():
    """Get auth headers for superadmin."""
    # Login as superadmin
    token = auth_manager.generate_token(
        user_id="user_superadmin",
        email="superadmin@rpa.test",
        role=UserRole.SUPERADMIN
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_admin():
    """Get auth headers for admin."""
    token = auth_manager.generate_token(
        user_id="user_admin",
        email="admin@rpa.test",
        role=UserRole.ADMIN
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_user():
    """Get auth headers for regular user."""
    token = auth_manager.generate_token(
        user_id="user_default",
        email="user@rpa.test",
        role=UserRole.USER
    )
    return {"Authorization": f"Bearer {token}"}


# ============================================================================
# AUTH TESTS
# ============================================================================

class TestAuth:
    """Tests for authentication endpoints."""

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_register_user(self, client):
        """Test user registration."""
        response = client.post("/auth/register", json={
            "email": "newuser@test.com",
            "username": "newuser",
            "password": "password123",
            "role": "user"
        })
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_register_duplicate_user(self, client):
        """Test registering duplicate user fails."""
        # First registration
        client.post("/auth/register", json={
            "email": "duplicate@test.com",
            "username": "duplicate",
            "password": "password123"
        })

        # Second registration with same email
        response = client.post("/auth/register", json={
            "email": "duplicate@test.com",
            "username": "duplicate2",
            "password": "password123"
        })
        assert response.status_code == 400

    def test_login_success(self, client):
        """Test successful login."""
        # First register
        client.post("/auth/register", json={
            "email": "login@test.com",
            "username": "loginuser",
            "password": "password123"
        })

        # Then login
        response = client.post("/auth/login", json={
            "email": "login@test.com",
            "password": "password123"
        })
        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        response = client.post("/auth/login", json={
            "email": "nonexistent@test.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401

    def test_login_default_superadmin(self, client):
        """Test login with default superadmin account."""
        response = client.post("/auth/login", json={
            "email": "superadmin@rpa.test",
            "password": "admin123"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["role"] == "superadmin"

    def test_protected_endpoint_without_token(self, client):
        """Test accessing protected endpoint without token."""
        response = client.get("/users/me")
        assert response.status_code == 401

    def test_protected_endpoint_with_token(self, client, auth_headers_user):
        """Test accessing protected endpoint with valid token."""
        response = client.get("/users/me", headers=auth_headers_user)
        assert response.status_code == 200
        assert response.json()["data"]["email"] == "user@rpa.test"

    def test_logout(self, client, auth_headers_user):
        """Test logout endpoint."""
        response = client.post("/auth/logout", headers=auth_headers_user)
        assert response.status_code == 200


# ============================================================================
# USER ROLE TESTS
# ============================================================================

class TestUserRoles:
    """Tests for user roles and permissions."""

    def test_superadmin_permissions(self):
        """Test superadmin has all permissions."""
        assert check_permission("superadmin", Permission.MANAGE_SYSTEM)
        assert check_permission("superadmin", Permission.MANAGE_USERS)
        assert check_permission("superadmin", Permission.DELETE_USERS)
        assert check_permission("superadmin", Permission.ACCESS_RAW_DATA)

    def test_admin_permissions(self):
        """Test admin has appropriate permissions."""
        assert check_permission("admin", Permission.MANAGE_USERS)
        assert check_permission("admin", Permission.VIEW_REPORTS)
        assert not check_permission("admin", Permission.MANAGE_SYSTEM)
        assert not check_permission("admin", Permission.DELETE_USERS)

    def test_user_permissions(self):
        """Test regular user permissions."""
        assert check_permission("user", Permission.PRACTICE_LEARNING)
        assert check_permission("user", Permission.VIEW_OWN_PROGRESS)
        assert not check_permission("user", Permission.MANAGE_USERS)
        assert not check_permission("user", Permission.VIEW_ALL_PROGRESS)

    def test_guest_permissions(self):
        """Test guest permissions are limited."""
        assert check_permission("guest", Permission.DEMO_ACCESS)
        assert check_permission("guest", Permission.READ)
        assert not check_permission("guest", Permission.WRITE)
        assert not check_permission("guest", Permission.VIEW_OWN_PROGRESS)

    def test_role_config(self):
        """Test role configuration retrieval."""
        config = get_role_config("superadmin")
        assert config is not None
        assert config.role == "superadmin"
        assert config.can_access_admin_panel is True

    def test_role_transition_validation(self):
        """Test role transition rules."""
        # Superadmin can create any role
        assert validate_role_transition("superadmin", "admin")
        assert validate_role_transition("superadmin", "superadmin")

        # Admin can only create user/guest
        assert validate_role_transition("admin", "user")
        assert validate_role_transition("admin", "guest")
        assert not validate_role_transition("admin", "admin")
        assert not validate_role_transition("admin", "superadmin")

        # User cannot create roles
        assert not validate_role_transition("user", "user")


# ============================================================================
# VOCABULARY TESTS
# ============================================================================

class TestVocabulary:
    """Tests for vocabulary endpoints."""

    def test_get_due_vocabulary(self, client, auth_headers_user):
        """Test getting due vocabulary items."""
        response = client.get("/vocabulary/due", headers=auth_headers_user)
        assert response.status_code == 200
        assert "items" in response.json()
        assert "count" in response.json()

    def test_get_new_vocabulary(self, client, auth_headers_user):
        """Test getting new vocabulary items."""
        response = client.get("/vocabulary/new", headers=auth_headers_user)
        assert response.status_code == 200
        assert "items" in response.json()

    def test_get_vocabulary_statistics(self, client, auth_headers_user):
        """Test getting vocabulary statistics."""
        response = client.get("/vocabulary/statistics", headers=auth_headers_user)
        assert response.status_code == 200
        stats = response.json()
        assert "total_words" in stats
        assert "by_proficiency" in stats

    def test_review_vocabulary(self, client, auth_headers_user):
        """Test reviewing a vocabulary item."""
        # Get a word first
        words_response = client.get("/vocabulary/new", headers=auth_headers_user)
        words = words_response.json()["items"]

        if words:
            word_id = words[0]["word_id"]

            # Review it
            response = client.post("/vocabulary/review", json={
                "word_id": word_id,
                "quality": 4,
                "response": "test response"
            }, headers=auth_headers_user)
            assert response.status_code == 200
            data = response.json()
            assert "feedback" in data
            assert "new_proficiency" in data


# ============================================================================
# GRAMMAR TESTS
# ============================================================================

class TestGrammar:
    """Tests for grammar endpoints."""

    def test_list_grammar_rules(self, client, auth_headers_user):
        """Test listing grammar rules."""
        response = client.get("/grammar/rules", headers=auth_headers_user)
        assert response.status_code == 200
        assert "rules" in response.json()

    def test_get_grammar_rule(self, client, auth_headers_user):
        """Test getting a specific grammar rule."""
        response = client.get("/grammar/rules/grammar_sva_1", headers=auth_headers_user)
        assert response.status_code == 200
        rule = response.json()
        assert rule["rule_id"] == "grammar_sva_1"

    def test_get_nonexistent_rule(self, client, auth_headers_user):
        """Test getting nonexistent rule returns 404."""
        response = client.get("/grammar/rules/nonexistent", headers=auth_headers_user)
        assert response.status_code == 404

    def test_generate_exercise(self, client, auth_headers_user):
        """Test generating a grammar exercise."""
        response = client.post("/grammar/exercise", json={
            "exercise_type": "multiple_choice"
        }, headers=auth_headers_user)
        assert response.status_code == 200
        exercise = response.json()
        assert "exercise_id" in exercise
        assert "question" in exercise
        assert "options" in exercise

    def test_check_grammar(self, client, auth_headers_user):
        """Test grammar checking."""
        response = client.post("/grammar/check", json={
            "text": "She run every day."
        }, headers=auth_headers_user)
        assert response.status_code == 200
        result = response.json()
        assert "errors" in result
        assert "score" in result


# ============================================================================
# ADMIN TESTS
# ============================================================================

class TestAdmin:
    """Tests for admin endpoints."""

    def test_list_users_as_superadmin(self, client, auth_headers_superadmin):
        """Test listing users as superadmin."""
        response = client.get("/admin/users", headers=auth_headers_superadmin)
        assert response.status_code == 200
        assert "users" in response.json()

    def test_list_users_as_admin(self, client, auth_headers_admin):
        """Test listing users as admin."""
        response = client.get("/admin/users", headers=auth_headers_admin)
        assert response.status_code == 200

    def test_list_users_as_user_forbidden(self, client, auth_headers_user):
        """Test that regular user cannot list users."""
        response = client.get("/admin/users", headers=auth_headers_user)
        assert response.status_code == 403

    def test_update_user(self, client, auth_headers_admin):
        """Test updating a user."""
        response = client.put("/admin/users/user@rpa.test", json={
            "is_active": True
        }, headers=auth_headers_admin)
        assert response.status_code == 200

    def test_delete_user_forbidden_for_admin(self, client, auth_headers_admin):
        """Test that admin cannot delete users."""
        response = client.delete(
            "/admin/users/user@rpa.test",
            headers=auth_headers_admin
        )
        assert response.status_code == 403

    def test_get_reports(self, client, auth_headers_admin):
        """Test getting admin reports."""
        response = client.get("/admin/reports", headers=auth_headers_admin)
        assert response.status_code == 200
        assert "data" in response.json()


# ============================================================================
# DESIGN TOKENS TESTS
# ============================================================================

class TestDesignTokens:
    """Tests for design tokens."""

    def test_get_color_web(self):
        """Test getting web color."""
        color = get_color("primary", "web")
        assert color == "#3b82f6"

    def test_get_color_terminal(self):
        """Test getting terminal color."""
        color = get_color("primary", "terminal")
        assert color == "blue"

    def test_get_spacing(self):
        """Test getting spacing value."""
        spacing = get_spacing("md")
        assert spacing == 4

    def test_export_for_web(self):
        """Test web export format."""
        tokens = export_for_web()
        assert "colors" in tokens
        assert "spacing" in tokens
        assert "typography" in tokens

    def test_export_for_terminal(self):
        """Test terminal export format."""
        tokens = export_for_terminal()
        assert "colors" in tokens
        assert "spacing" in tokens

    def test_design_tokens_completeness(self):
        """Test that all expected token categories exist."""
        assert "colors" in DESIGN_TOKENS
        assert "spacing" in DESIGN_TOKENS
        assert "typography" in DESIGN_TOKENS
        assert "borders" in DESIGN_TOKENS
        assert "animations" in DESIGN_TOKENS
        assert "components" in DESIGN_TOKENS
        assert "icons" in DESIGN_TOKENS


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Integration tests for complete workflows."""

    def test_complete_learning_workflow(self, client):
        """Test complete learning workflow."""
        # 1. Register user
        client.post("/auth/register", json={
            "email": "workflow@test.com",
            "username": "workflow",
            "password": "password123"
        })

        # 2. Login
        login_response = client.post("/auth/login", json={
            "email": "workflow@test.com",
            "password": "password123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 3. Get dashboard
        dashboard_response = client.get("/dashboard", headers=headers)
        assert dashboard_response.status_code == 200

        # 4. Start learning session
        session_response = client.post(
            "/learning/sessions",
            params={"domain": "english", "exercise_type": "flashcard"},
            headers=headers
        )
        assert session_response.status_code == 200
        session_id = session_response.json()["data"]["session_id"]

        # 5. Get vocabulary
        vocab_response = client.get("/vocabulary/new", headers=headers)
        assert vocab_response.status_code == 200

        # 6. Complete session
        complete_response = client.post(
            f"/learning/sessions/{session_id}/complete",
            headers=headers
        )
        assert complete_response.status_code == 200


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
