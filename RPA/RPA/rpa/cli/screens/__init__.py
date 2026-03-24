"""
Terminal UI Screens.

Individual screen modules for different functionalities.
Each screen represents a full-page view in the terminal.
"""

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.layout import Layout
from typing import Any, Dict, List, Optional
import time
import os
import sys

# Add parent path for imports
sys.path.insert(0, str(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from ..client import APIClient
from ..widgets import (
    Flashcard, ProgressBar, AsciiChart, Menu, StatusBox,
    LearningSession, Notification, clear_screen, print_header,
    print_footer, confirm, prompt, select, console
)

__all__ = [
    "BaseScreen",
    "LoginScreen",
    "DashboardScreen",
    "VocabularyScreen",
    "GrammarScreen",
    "ProgressScreen",
    "AdminScreen",
]


class BaseScreen:
    """Base class for all screens."""

    def __init__(self, client: APIClient):
        self.client = client
        self.running = True
        self.next_screen: Optional[str] = None

    def render(self) -> None:
        """Render the screen."""
        raise NotImplementedError

    def handle_input(self, key: str) -> bool:
        """Handle input. Returns True if screen should continue."""
        raise NotImplementedError

    def run(self) -> Optional[str]:
        """Run the screen. Returns next screen name or None."""
        while self.running:
            clear_screen()
            self.render()

            try:
                key = console.input("\n[bold cyan]Command:[/bold cyan] ").strip().lower()
                if not self.handle_input(key):
                    break
            except (KeyboardInterrupt, EOFError):
                break

        return self.next_screen


class LoginScreen(BaseScreen):
    """Login screen for authentication."""

    def __init__(self, client: APIClient):
        super().__init__(client)
        self.error_message = ""

    def render(self) -> None:
        """Render login screen."""
        print_header("RPA Learning System", "Terminal Interface")

        # Check for saved login
        user = self.client.get_current_user()
        if user:
            console.print(Panel(
                Text(f"Logged in as: {user.get('email', 'Unknown')}\n"
                     f"Role: {user.get('role', 'user').upper()}"),
                title="Session Active",
                border_style="green"
            ))
            console.print("\n[dim]Press Enter to continue or 'l' to logout[/dim]")
            return

        # Login form
        console.print(Panel(
            Text("Welcome to RPA Learning System\n\n"
                 "Enter your credentials to continue"),
            title="🔐 Login",
            border_style="blue"
        ))

        if self.error_message:
            console.print(f"\n[red]Error: {self.error_message}[/red]")

        console.print("\n[dim]Enter email and password, or 'g' for guest mode[/dim]")

    def handle_input(self, key: str) -> bool:
        """Handle login input."""
        user = self.client.get_current_user()

        if user:
            if key == 'l':
                self.client.logout()
                self.error_message = ""
                return True
            elif key == '' or key == 'enter':
                self.next_screen = "dashboard"
                return False
            return True

        if key == 'g':
            # Guest mode - no login required
            self.client.user = {"email": "guest@rpa.test", "role": "guest"}
            self.next_screen = "dashboard"
            return False

        # Get email
        email = prompt("Email")
        if not email:
            self.error_message = "Email required"
            return True

        # Get password (hidden)
        password = prompt("Password")
        if not password:
            self.error_message = "Password required"
            return True

        # Attempt login
        result = self.client.login(email, password)

        if result.get("success"):
            self.next_screen = "dashboard"
            return False
        else:
            self.error_message = result.get("error", "Login failed")
            return True


class DashboardScreen(BaseScreen):
    """Main dashboard screen."""

    def __init__(self, client: APIClient):
        super().__init__(client)
        self.menu = Menu(
            title="Navigation",
            options=[
                {"key": "v", "label": "Vocabulary", "description": "Learn vocabulary with flashcards"},
                {"key": "g", "label": "Grammar", "description": "Practice grammar exercises"},
                {"key": "p", "label": "Progress", "description": "View your learning progress"},
                {"key": "s", "label": "Settings", "description": "Configure preferences"},
                {"key": "q", "label": "Quit", "description": "Exit the application"},
            ]
        )
        # Add admin option if applicable
        user = client.get_current_user()
        if user and user.get("role") in ("admin", "superadmin"):
            self.menu.add_option("a", "Admin", "User management", None)

    def render(self) -> None:
        """Render dashboard."""
        user = self.client.get_current_user()
        role = user.get("role", "guest") if user else "guest"
        email = user.get("email", "Guest") if user else "Guest"

        print_header("📚 Dashboard", f"Logged in as: {email} ({role.upper()})")

        # Get due items
        due_vocab = self.client.get_due_vocabulary(1)

        # Stats panel
        stats_table = Table(show_header=False, box=None)
        stats_table.add_column("Metric", style="cyan", width=20)
        stats_table.add_column("Value", style="bold")

        vocab_stats = self.client.get_vocabulary_stats()

        stats_table.add_row("Total Words", str(vocab_stats.get("total_words", 0)))
        stats_table.add_row("Words Due", str(len(due_vocab)))
        stats_table.add_row("Accuracy", f"{vocab_stats.get('accuracy', 0) * 100:.1f}%")
        stats_table.add_row("Total Reviews", str(vocab_stats.get("total_reviews", 0)))

        console.print(Panel(stats_table, title="📊 Quick Stats", border_style="green"))

        # Menu
        console.print(self.menu.render())

        console.print("\n[dim]Press a key to navigate[/dim]")

    def handle_input(self, key: str) -> bool:
        """Handle menu selection."""
        option = self.menu.get_selected(key)

        if option:
            label = option['label'].lower()

            if label == "quit":
                self.running = False
                return False
            elif label == "vocabulary":
                self.next_screen = "vocabulary"
                return False
            elif label == "grammar":
                self.next_screen = "grammar"
                return False
            elif label == "progress":
                self.next_screen = "progress"
                return False
            elif label == "admin":
                self.next_screen = "admin"
                return False
            elif label == "settings":
                self.next_screen = "settings"
                return False

        return True


class VocabularyScreen(BaseScreen):
    """Vocabulary learning screen."""

    def __init__(self, client: APIClient):
        super().__init__(client)
        self.session = LearningSession("vocabulary")
        self.current_flashcard: Optional[Flashcard] = None
        self.due_items: List[Dict] = []
        self.mode = "menu"  # menu, learning, rating
        self.start_time = 0

    def render(self) -> None:
        """Render vocabulary screen."""
        if self.mode == "menu":
            self._render_menu()
        elif self.mode == "learning":
            self._render_learning()
        elif self.mode == "rating":
            self._render_rating()

    def _render_menu(self) -> None:
        """Render vocabulary menu."""
        print_header("📖 Vocabulary Learning", "SM-2 Spaced Repetition System")

        # Get stats
        stats = self.client.get_vocabulary_stats()
        due_items = self.client.get_due_vocabulary(100)

        # Stats display
        stats_table = Table(show_header=False, box=None)
        stats_table.add_column("Metric", style="cyan", width=20)
        stats_table.add_column("Value", style="bold")

        stats_table.add_row("Total Words", str(stats.get("total_words", 0)))
        stats_table.add_row("Words Due", str(len(due_items)))
        stats_table.add_row("Mastered", str(stats.get("by_proficiency", {}).get("mastered", 0)))
        stats_table.add_row("Learning", str(stats.get("by_proficiency", {}).get("learning", 0)))

        console.print(Panel(stats_table, title="📊 Your Progress", border_style="blue"))

        # Menu
        menu = Menu(title="Options")
        menu.add_option("s", "Start Review", f"{len(due_items)} words due")
        menu.add_option("n", "Learn New Words", "Start fresh vocabulary")
        menu.add_option("b", "Back", "Return to dashboard")

        console.print(menu.render())

    def _render_learning(self) -> None:
        """Render learning mode."""
        if self.current_flashcard:
            self.session.set_flashcard(self.current_flashcard)
            console.print(self.session.render())

            if self.current_flashcard.flipped:
                console.print("\n[dim]Rate your recall (0-5), or 'f' to flip back[/dim]")
            else:
                console.print("\n[dim]Press 'f' to flip, 'q' to quit[/dim]")
        else:
            console.print(Panel(
                "No vocabulary items available.\n"
                "Add new words or wait for scheduled reviews.",
                title="No Items",
                border_style="yellow"
            ))
            self.mode = "menu"

    def _render_rating(self) -> None:
        """Render rating options."""
        console.print(self.current_flashcard.render())
        console.print(self.current_flashcard.render_rating_options())
        console.print("\n[dim]Press 0-5 to rate, 'q' to quit[/dim]")

    def handle_input(self, key: str) -> bool:
        """Handle vocabulary input."""
        if self.mode == "menu":
            return self._handle_menu_input(key)
        elif self.mode == "learning":
            return self._handle_learning_input(key)
        elif self.mode == "rating":
            return self._handle_rating_input(key)
        return True

    def _handle_menu_input(self, key: str) -> bool:
        """Handle menu input."""
        if key == 's':
            # Start review
            self.due_items = self.client.get_due_vocabulary(20)
            if self.due_items:
                self.session.total_items = len(self.due_items)
                self.session.current_item = 0
                self._load_next_item()
                self.mode = "learning"
            return True
        elif key == 'n':
            # Learn new words
            self.due_items = self.client.get_new_vocabulary(10)
            if self.due_items:
                self.session.total_items = len(self.due_items)
                self.session.current_item = 0
                self._load_next_item()
                self.mode = "learning"
            return True
        elif key == 'b':
            self.next_screen = "dashboard"
            return False
        return True

    def _handle_learning_input(self, key: str) -> bool:
        """Handle learning input."""
        if key == 'f':
            if self.current_flashcard:
                self.current_flashcard.flip()
                if self.current_flashcard.flipped:
                    self.mode = "rating"
                    self.start_time = time.time()
        elif key == 'q':
            self.mode = "menu"
        return True

    def _handle_rating_input(self, key: str) -> bool:
        """Handle rating input."""
        if key in '012345':
            quality = int(key)
            time_spent = time.time() - self.start_time

            # Submit review
            if self.current_flashcard:
                result = self.client.review_vocabulary(
                    word_id=self.current_flashcard.word_id,
                    quality=quality,
                    time_spent=time_spent
                )

                # Record result
                self.session.record_answer(quality >= 3)

                # Show feedback
                if result:
                    console.print(Notification.show(
                        result.get('feedback', 'Review recorded'),
                        'success' if quality >= 3 else 'warning'
                    ))
                    time.sleep(1)

            # Load next item
            self.due_items.pop(0)
            if self.due_items:
                self._load_next_item()
                self.mode = "learning"
            else:
                console.print(Notification.show(
                    "Session complete! Great job!",
                    'success'
                ))
                time.sleep(2)
                self.mode = "menu"

        elif key == 'f':
            # Flip back
            if self.current_flashcard:
                self.current_flashcard.flip()
                self.mode = "learning"
        elif key == 'q':
            self.mode = "menu"

        return True

    def _load_next_item(self) -> None:
        """Load next vocabulary item."""
        if self.due_items:
            item = self.due_items[0]
            self.current_flashcard = Flashcard(
                word_id=item['word_id'],
                front=item['word'],
                back=item['definition'],
                examples=item.get('examples', []),
                part_of_speech=item.get('part_of_speech', ''),
                difficulty=item.get('difficulty', 1)
            )


class GrammarScreen(BaseScreen):
    """Grammar practice screen."""

    def __init__(self, client: APIClient):
        super().__init__(client)
        self.mode = "menu"
        self.current_exercise: Optional[Dict] = None
        self.rules: List[Dict] = []

    def render(self) -> None:
        """Render grammar screen."""
        if self.mode == "menu":
            self._render_menu()
        elif self.mode == "exercise":
            self._render_exercise()

    def _render_menu(self) -> None:
        """Render grammar menu."""
        print_header("📝 Grammar Practice", "Improve your English grammar")

        # Get rules
        if not self.rules:
            self.rules = self.client.get_grammar_rules()

        # Stats
        stats_table = Table(show_header=False, box=None)
        stats_table.add_column("Category", style="cyan")
        stats_table.add_column("Rules", style="bold", justify="right")

        categories = {}
        for rule in self.rules:
            cat = rule.get('category', 'general')
            categories[cat] = categories.get(cat, 0) + 1

        for cat, count in categories.items():
            stats_table.add_row(cat.replace('_', ' ').title(), str(count))

        console.print(Panel(stats_table, title="📚 Grammar Rules", border_style="blue"))

        # Menu
        menu = Menu(title="Options")
        menu.add_option("p", "Practice", "Start grammar exercises")
        menu.add_option("c", "Check Text", "Check your writing")
        menu.add_option("b", "Back", "Return to dashboard")

        console.print(menu.render())

    def _render_exercise(self) -> None:
        """Render exercise."""
        if self.current_exercise:
            console.print(Panel(
                self.current_exercise.get('question', 'No question'),
                title="📝 Grammar Exercise",
                border_style="blue",
                padding=(1, 2)
            ))

            # Options
            options = self.current_exercise.get('options', [])
            if options:
                for i, opt in enumerate(options):
                    console.print(f"  [{i+1}] {opt}")

            console.print("\n[dim]Select 1-4, or 'q' to quit[/dim]")
        else:
            console.print("Loading exercise...")
            self.mode = "menu"

    def handle_input(self, key: str) -> bool:
        """Handle grammar input."""
        if self.mode == "menu":
            if key == 'p':
                self.current_exercise = self.client.get_grammar_exercise()
                self.mode = "exercise"
            elif key == 'c':
                self._check_text()
            elif key == 'b':
                self.next_screen = "dashboard"
                return False
        elif self.mode == "exercise":
            if key == 'q':
                self.mode = "menu"
            elif key in '1234':
                self._check_answer(int(key) - 1)
        return True

    def _check_text(self) -> None:
        """Check user text for grammar errors."""
        console.print("\n[dim]Enter text to check (empty line to finish):[/dim]")
        lines = []
        while True:
            try:
                line = input()
                if not line:
                    break
                lines.append(line)
            except EOFError:
                break

        text = " ".join(lines)
        if text:
            result = self.client.check_grammar(text)

            console.print(Panel(
                f"Score: {result.get('score', 1.0) * 100:.0f}%\n"
                f"Errors: {len(result.get('errors', []))}",
                title="📊 Grammar Check Result",
                border_style="green" if result.get('score', 1.0) > 0.8 else "yellow"
            ))

            for error in result.get('errors', [])[:5]:
                console.print(f"  [red]✗[/red] {error.get('message', 'Error')}")
                console.print(f"    [dim]Suggestion: {error.get('suggestion', '')}[/dim]")

            console.input("\n[dim]Press Enter to continue...[/dim]")

    def _check_answer(self, selected: int) -> None:
        """Check exercise answer."""
        if self.current_exercise:
            correct_index = self.current_exercise.get('correct_index', 0)
            explanation = self.current_exercise.get('explanation', '')

            if selected == correct_index:
                console.print(Notification.show("Correct! 🎉", 'success'))
            else:
                console.print(Notification.show(f"Incorrect. The answer was: {self.current_exercise.get('correct_answer', '')}", 'error'))

            console.print(f"\n[dim]{explanation}[/dim]")
            console.input("\n[dim]Press Enter for next exercise...[/dim]")

            # Load next
            self.current_exercise = self.client.get_grammar_exercise()


class ProgressScreen(BaseScreen):
    """Progress tracking screen."""

    def __init__(self, client: APIClient):
        super().__init__(client)
        self.chart = AsciiChart("Learning Progress")

    def render(self) -> None:
        """Render progress screen."""
        print_header("📈 Your Progress", "Track your learning journey")

        # Get progress data
        progress = self.client.get_progress()

        # Summary stats
        stats_table = Table.grid(padding=2)
        stats_table.add_column("Stat", style="cyan")
        stats_table.add_column("Value", style="bold")

        stats_table.add_row("Vocabulary", f"{progress.get('total_words', 0)} words")
        stats_table.add_row("Mastered", f"{progress.get('mastered_words', 0)} words")
        stats_table.add_row("Learning", f"{progress.get('learning_words', 0)} words")
        stats_table.add_row("Total Reviews", f"{progress.get('total_reviews', 0)}")
        stats_table.add_row("Accuracy", f"{progress.get('accuracy', 0) * 100:.1f}%")

        console.print(Panel(stats_table, title="📊 Statistics", border_style="blue"))

        # Proficiency breakdown
        vocab_stats = self.client.get_vocabulary_stats()
        by_prof = vocab_stats.get('by_proficiency', {})

        if by_prof:
            self.chart.set_data(
                [by_prof.get('new', 0), by_prof.get('learning', 0),
                 by_prof.get('familiar', 0), by_prof.get('proficient', 0),
                 by_prof.get('mastered', 0)],
                ['New', 'Learning', 'Familiar', 'Proficient', 'Mastered']
            )
            console.print(self.chart.render())

        # Menu
        console.print("\n[dim]Press 'b' to go back[/dim]")

    def handle_input(self, key: str) -> bool:
        """Handle progress input."""
        if key == 'b':
            self.next_screen = "dashboard"
            return False
        return True


class AdminScreen(BaseScreen):
    """Admin management screen."""

    def __init__(self, client: APIClient):
        super().__init__(client)
        self.users: List[Dict] = []
        self.selected_user: int = 0

    def render(self) -> None:
        """Render admin screen."""
        user = self.client.get_current_user()
        role = user.get('role', 'guest') if user else 'guest'

        if role not in ('admin', 'superadmin'):
            console.print(Panel(
                "You don't have permission to access this page.",
                title="🔒 Access Denied",
                border_style="red"
            ))
            console.print("\n[dim]Press 'b' to go back[/dim]")
            return

        print_header("🛡️ Admin Panel", "User Management")

        # Load users
        if not self.users:
            self.users = self.client.list_users()

        # Users table
        table = Table(title="Users", show_lines=True)
        table.add_column("#", style="dim", width=3)
        table.add_column("Email", style="cyan")
        table.add_column("Role", style="bold")
        table.add_column("Status", style="green")

        for i, u in enumerate(self.users[:15]):  # Show first 15
            marker = ">" if i == self.selected_user else " "
            status = "Active" if u.get('is_active', True) else "Inactive"
            table.add_row(
                f"{marker}{i+1}",
                u.get('email', 'N/A'),
                u.get('role', 'user').upper(),
                status
            )

        console.print(table)

        # Menu
        menu = Menu(title="Actions")
        menu.add_option("j/k", "Navigate", "Select user")
        menu.add_option("e", "Edit Role", "Change user role")
        menu.add_option("d", "Disable", "Disable user")
        menu.add_option("r", "Refresh", "Reload user list")
        menu.add_option("b", "Back", "Return to dashboard")

        console.print(menu.render())

    def handle_input(self, key: str) -> bool:
        """Handle admin input."""
        user = self.client.get_current_user()
        role = user.get('role', 'guest') if user else 'guest'

        if role not in ('admin', 'superadmin'):
            if key == 'b':
                self.next_screen = "dashboard"
                return False
            return True

        if key == 'j':
            self.selected_user = min(self.selected_user + 1, len(self.users) - 1)
        elif key == 'k':
            self.selected_user = max(self.selected_user - 1, 0)
        elif key == 'r':
            self.users = []
        elif key == 'b':
            self.next_screen = "dashboard"
            return False
        elif key == 'e' and self.users:
            # Edit role
            target = self.users[self.selected_user]
            new_role = prompt(f"New role for {target['email']}", target.get('role', 'user'))
            if self.client.update_user(target['email'], {'role': new_role}):
                console.print(Notification.show("Role updated", 'success'))
                time.sleep(1)
                self.users = []

        return True
