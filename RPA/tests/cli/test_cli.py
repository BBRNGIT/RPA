"""
Tests for RPA Terminal CLI.

Tests the terminal UI components, API client, and screens.
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from io import StringIO

# Add project path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from rpa.cli.client import APIClient, ConfigManager
from rpa.cli.widgets import (
    Flashcard, ProgressBar, AsciiChart, Menu, StatusBox,
    LearningSession, Notification
)
from rpa.cli.screens import (
    LoginScreen, DashboardScreen, VocabularyScreen,
    GrammarScreen, ProgressScreen, AdminScreen
)


# ============================================================================
# CONFIG MANAGER TESTS
# ============================================================================

class TestConfigManager:
    """Tests for ConfigManager."""

    def test_load_config_empty(self, tmp_path):
        """Test loading config when file doesn't exist."""
        manager = ConfigManager()
        manager.CONFIG_DIR = tmp_path
        manager.CONFIG_FILE = tmp_path / "config.json"

        config = manager.load_config()
        assert "api_url" in config
        assert "theme" in config

    def test_save_and_load_config(self, tmp_path):
        """Test saving and loading config."""
        manager = ConfigManager()
        manager.CONFIG_DIR = tmp_path
        manager.CONFIG_FILE = tmp_path / "config.json"

        test_config = {
            "api_url": "http://test.local:8000",
            "theme": "dark",
            "custom": "value"
        }

        manager.save_config(test_config)
        loaded = manager.load_config()

        assert loaded["api_url"] == "http://test.local:8000"
        assert loaded["theme"] == "dark"
        assert loaded["custom"] == "value"

    def test_save_and_load_auth(self, tmp_path):
        """Test saving and loading auth data."""
        manager = ConfigManager()
        manager.CONFIG_DIR = tmp_path
        manager.AUTH_FILE = tmp_path / "auth.json"

        manager.save_auth("test_token", {"email": "test@test.com", "role": "user"})

        token = manager.get_token()
        user = manager.get_user()

        assert token == "test_token"
        assert user["email"] == "test@test.com"

    def test_clear_auth(self, tmp_path):
        """Test clearing auth data."""
        manager = ConfigManager()
        manager.CONFIG_DIR = tmp_path
        manager.AUTH_FILE = tmp_path / "auth.json"

        manager.save_auth("token", {"email": "test@test.com"})
        manager.clear_auth()

        assert manager.get_token() is None
        assert manager.get_user() is None


# ============================================================================
# API CLIENT TESTS
# ============================================================================

class TestAPIClient:
    """Tests for APIClient."""

    def test_init(self):
        """Test client initialization."""
        client = APIClient("http://localhost:8080")
        assert client.api_url == "http://localhost:8080"

    def test_is_authenticated_false(self):
        """Test authentication check when not logged in."""
        client = APIClient()
        # Clear any saved auth
        client.token = None
        client.user = None

        assert client.is_authenticated() is False

    def test_is_authenticated_true(self):
        """Test authentication check when logged in."""
        client = APIClient()
        client.token = "test_token"

        assert client.is_authenticated() is True

    def test_get_current_user_none(self):
        """Test getting user when not logged in."""
        client = APIClient()
        client.user = None

        assert client.get_current_user() is None

    def test_get_current_user_exists(self):
        """Test getting user when logged in."""
        client = APIClient()
        client.user = {"email": "test@test.com", "role": "user"}

        user = client.get_current_user()
        assert user["email"] == "test@test.com"

    def test_get_due_vocabulary_direct_mode(self):
        """Test getting vocabulary in direct mode."""
        client = APIClient()
        client._init_direct_mode()

        items = client.get_due_vocabulary(limit=5)
        assert isinstance(items, list)

    def test_get_vocabulary_stats_direct_mode(self):
        """Test getting vocabulary stats in direct mode."""
        client = APIClient()
        client._init_direct_mode()

        stats = client.get_vocabulary_stats()
        assert isinstance(stats, dict)
        assert "total_words" in stats

    def test_get_grammar_rules_direct_mode(self):
        """Test getting grammar rules in direct mode."""
        client = APIClient()
        client._init_direct_mode()

        rules = client.get_grammar_rules()
        assert isinstance(rules, list)

    def test_check_grammar_direct_mode(self):
        """Test checking grammar in direct mode."""
        client = APIClient()
        client._init_direct_mode()

        result = client.check_grammar("She runs every day.")
        assert isinstance(result, dict)
        assert "text" in result
        assert "errors" in result


# ============================================================================
# WIDGET TESTS
# ============================================================================

class TestFlashcard:
    """Tests for Flashcard widget."""

    def test_create(self):
        """Test creating a flashcard."""
        card = Flashcard(
            word_id="test_1",
            front="Hello",
            back="A greeting",
            examples=["Hello, world!"],
            part_of_speech="noun",
            difficulty=2
        )

        assert card.word_id == "test_1"
        assert card.front == "Hello"
        assert card.back == "A greeting"
        assert not card.flipped

    def test_flip(self):
        """Test flipping flashcard."""
        card = Flashcard(word_id="test", front="Front", back="Back")

        card.flip()
        assert card.flipped is True

        card.flip()
        assert card.flipped is False

    def test_render(self):
        """Test rendering flashcard."""
        card = Flashcard(
            word_id="test",
            front="Word",
            back="Definition",
            difficulty=3
        )

        panel = card.render()
        assert panel is not None

    def test_render_rating_options(self):
        """Test rendering rating options."""
        card = Flashcard(word_id="test", front="W", back="D")
        table = card.render_rating_options()

        assert table is not None


class TestProgressBar:
    """Tests for ProgressBar widget."""

    def test_create(self):
        """Test creating progress bar."""
        bar = ProgressBar(total=100, completed=50, label="Progress")

        assert bar.total == 100
        assert bar.completed == 50

    def test_render(self):
        """Test rendering progress bar."""
        bar = ProgressBar(total=100, completed=75)
        panel = bar.render()

        assert panel is not None

    def test_update(self):
        """Test updating progress."""
        bar = ProgressBar(total=100, completed=0)
        bar.update(50)

        assert bar.completed == 50

    def test_zero_total(self):
        """Test progress bar with zero total."""
        bar = ProgressBar(total=0, completed=0)
        panel = bar.render()

        assert panel is not None


class TestAsciiChart:
    """Tests for AsciiChart widget."""

    def test_create(self):
        """Test creating chart."""
        chart = AsciiChart(title="Test Chart")
        assert chart.title == "Test Chart"

    def test_set_data(self):
        """Test setting data."""
        chart = AsciiChart()
        chart.set_data([1, 2, 3, 4, 5], ["A", "B", "C", "D", "E"])

        assert len(chart.data) == 5
        assert len(chart.labels) == 5

    def test_render_bar(self):
        """Test rendering bar chart."""
        chart = AsciiChart("Test")
        chart.set_data([10, 20, 30], ["A", "B", "C"])

        table = chart.render_bar()
        assert table is not None

    def test_render_empty(self):
        """Test rendering with no data."""
        chart = AsciiChart()
        result = chart.render_bar()
        assert result is not None


class TestMenu:
    """Tests for Menu widget."""

    def test_create(self):
        """Test creating menu."""
        menu = Menu(title="Test Menu")
        assert menu.title == "Test Menu"
        assert len(menu.options) == 0

    def test_add_option(self):
        """Test adding option."""
        menu = Menu(title="Test")
        menu.add_option("a", "Option A", "Description")

        assert len(menu.options) == 1
        assert menu.options[0]["key"] == "a"

    def test_render(self):
        """Test rendering menu."""
        menu = Menu(title="Test")
        menu.add_option("a", "Option A")
        menu.add_option("b", "Option B")

        panel = menu.render()
        assert panel is not None

    def test_get_selected(self):
        """Test getting selected option."""
        menu = Menu()
        menu.add_option("a", "Option A")

        opt = menu.get_selected("a")
        assert opt is not None
        assert opt["label"] == "Option A"

        opt = menu.get_selected("x")
        assert opt is None


class TestStatusBox:
    """Tests for StatusBox widget."""

    def test_create(self):
        """Test creating status box."""
        box = StatusBox(title="Status")
        assert box.title == "Status"

    def test_set_item(self):
        """Test setting item."""
        box = StatusBox()
        box.set_item("Users", 10)

        assert box.items["Users"] == 10

    def test_render(self):
        """Test rendering status box."""
        box = StatusBox(title="Stats", items={"A": 1, "B": 2})
        panel = box.render()

        assert panel is not None


class TestLearningSession:
    """Tests for LearningSession widget."""

    def test_create(self):
        """Test creating session."""
        session = LearningSession("vocabulary")

        assert session.domain == "vocabulary"
        assert session.current_item == 0
        assert session.total_items == 0

    def test_record_answer(self):
        """Test recording answers."""
        session = LearningSession()
        session.total_items = 5

        session.record_answer(True)
        assert session.correct == 1
        assert session.current_item == 1

        session.record_answer(False)
        assert session.incorrect == 1
        assert session.current_item == 2

    def test_set_flashcard(self):
        """Test setting flashcard."""
        session = LearningSession()
        card = Flashcard("test", "Front", "Back")

        session.set_flashcard(card)
        assert session.flashcard is not None


class TestNotification:
    """Tests for Notification widget."""

    def test_show_success(self):
        """Test success notification."""
        panel = Notification.show("Success!", "success")
        assert panel is not None

    def test_show_error(self):
        """Test error notification."""
        panel = Notification.show("Error!", "error")
        assert panel is not None

    def test_show_warning(self):
        """Test warning notification."""
        panel = Notification.show("Warning!", "warning")
        assert panel is not None

    def test_show_info(self):
        """Test info notification."""
        panel = Notification.show("Info", "info")
        assert panel is not None


# ============================================================================
# SCREEN TESTS
# ============================================================================

class TestScreens:
    """Tests for screen classes."""

    def test_login_screen_create(self):
        """Test creating login screen."""
        client = APIClient()
        screen = LoginScreen(client)

        assert screen.client is not None
        assert screen.error_message == ""

    def test_dashboard_screen_create(self):
        """Test creating dashboard screen."""
        client = APIClient()
        screen = DashboardScreen(client)

        assert screen.client is not None
        assert screen.menu is not None

    def test_vocabulary_screen_create(self):
        """Test creating vocabulary screen."""
        client = APIClient()
        screen = VocabularyScreen(client)

        assert screen.client is not None
        assert screen.mode == "menu"

    def test_grammar_screen_create(self):
        """Test creating grammar screen."""
        client = APIClient()
        screen = GrammarScreen(client)

        assert screen.client is not None
        assert screen.mode == "menu"

    def test_progress_screen_create(self):
        """Test creating progress screen."""
        client = APIClient()
        screen = ProgressScreen(client)

        assert screen.client is not None

    def test_admin_screen_create(self):
        """Test creating admin screen."""
        client = APIClient()
        screen = AdminScreen(client)

        assert screen.client is not None
        assert screen.selected_user == 0


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
