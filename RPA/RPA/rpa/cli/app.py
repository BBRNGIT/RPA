"""
RPA Terminal Application.

Main entry point for the Terminal UI.
Provides a unified interface that mirrors the Web UI experience.

Usage:
    rpa                     # Start interactive mode
    rpa login               # Login to RPA
    rpa dashboard           # Show dashboard
    rpa learn vocab         # Start vocabulary learning
    rpa learn grammar       # Start grammar exercises
    rpa progress            # View progress
    rpa admin users         # Admin: manage users
    rpa --help              # Show help
"""

import argparse
import os
import sys
from typing import Any, Dict, Optional

# Add parent path for imports
sys.path.insert(0, str(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.live import Live
import time

from .client import APIClient
from .screens import (
    LoginScreen, DashboardScreen, VocabularyScreen,
    GrammarScreen, ProgressScreen, AdminScreen
)
from .widgets import (
    clear_screen, print_header, print_footer,
    confirm, prompt, Notification, console
)

__version__ = "1.0.0"


class RPAApp:
    """
    Main RPA Terminal Application.

    Coordinates screens and manages the application lifecycle.
    Provides the same experience as the Web UI in terminal format.
    """

    SCREENS = {
        "login": LoginScreen,
        "dashboard": DashboardScreen,
        "vocabulary": VocabularyScreen,
        "grammar": GrammarScreen,
        "progress": ProgressScreen,
        "admin": AdminScreen,
    }

    def __init__(self, api_url: str = "http://localhost:8000"):
        """Initialize the application."""
        self.client = APIClient(api_url)
        self.running = True
        self.current_screen: Optional[str] = None

    def run(self, start_screen: str = "login") -> None:
        """
        Run the application.

        Args:
            start_screen: Screen to start with
        """
        self.current_screen = start_screen

        # Show welcome
        self._show_welcome()

        while self.running:
            screen_class = self.SCREENS.get(self.current_screen)

            if not screen_class:
                console.print(f"[red]Unknown screen: {self.current_screen}[/red]")
                self.current_screen = "dashboard"
                continue

            # Create and run screen
            screen = screen_class(self.client)
            next_screen = screen.run()

            if next_screen:
                self.current_screen = next_screen
            else:
                self.running = False

        # Show goodbye
        self._show_goodbye()

    def _show_welcome(self) -> None:
        """Show welcome message."""
        clear_screen()

        # Check if already logged in
        user = self.client.get_current_user()

        welcome_text = Text()
        welcome_text.append("RPA Learning System\n", style="bold blue")
        welcome_text.append("Terminal Interface v" + __version__ + "\n\n", style="dim")

        if user:
            welcome_text.append(f"Welcome back, {user.get('email', 'User')}!\n", style="green")
            welcome_text.append(f"Role: {user.get('role', 'user').upper()}", style="cyan")
        else:
            welcome_text.append("Press Enter to login or 'g' for guest mode", style="dim")

        console.print(Panel(
            welcome_text,
            border_style="blue",
            padding=(2, 4)
        ))

        time.sleep(1)

    def _show_goodbye(self) -> None:
        """Show goodbye message."""
        clear_screen()
        console.print(Panel(
            Text("Thank you for using RPA!\n\nKeep learning! 📚", style="cyan"),
            title="👋 Goodbye",
            border_style="blue",
            padding=(2, 4)
        ))


def run_cli():
    """Run the CLI application."""
    parser = argparse.ArgumentParser(
        prog="rpa",
        description="RPA Learning System - Terminal Interface"
    )

    parser.add_argument(
        "--version", "-v",
        action="version",
        version=f"%(prog)s {__version__}"
    )

    parser.add_argument(
        "--api-url",
        default="http://localhost:8000",
        help="RPA API URL (default: http://localhost:8000)"
    )

    parser.add_argument(
        "--offline",
        action="store_true",
        help="Run in offline mode (direct module access)"
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Login command
    login_parser = subparsers.add_parser("login", help="Login to RPA")
    login_parser.add_argument("--email", "-e", help="Email address")
    login_parser.add_argument("--password", "-p", help="Password")

    # Learn command
    learn_parser = subparsers.add_parser("learn", help="Start learning")
    learn_parser.add_argument(
        "domain",
        nargs="?",
        choices=["vocab", "vocabulary", "grammar", "reading", "writing"],
        help="Learning domain"
    )

    # Progress command
    subparsers.add_parser("progress", help="View progress")

    # Admin command
    admin_parser = subparsers.add_parser("admin", help="Admin tools")
    admin_parser.add_argument(
        "action",
        nargs="?",
        choices=["users", "stats", "config"],
        help="Admin action"
    )

    # Logout command
    subparsers.add_parser("logout", help="Logout from RPA")

    # Parse arguments
    args = parser.parse_args()

    # Handle commands
    if args.command == "login":
        return _cmd_login(args)
    elif args.command == "logout":
        return _cmd_logout(args)
    elif args.command == "learn":
        return _cmd_learn(args)
    elif args.command == "progress":
        return _cmd_progress(args)
    elif args.command == "admin":
        return _cmd_admin(args)
    else:
        # Interactive mode
        app = RPAApp(args.api_url)

        # Determine start screen
        if args.offline:
            app.client._init_direct_mode()

        user = app.client.get_current_user()
        start_screen = "dashboard" if user else "login"

        app.run(start_screen=start_screen)


def _cmd_login(args) -> int:
    """Handle login command."""
    client = APIClient(args.api_url)

    # Check if already logged in
    user = client.get_current_user()
    if user:
        console.print(f"[green]Already logged in as {user.get('email')}[/green]")
        return 0

    # Get credentials
    email = args.email or prompt("Email")
    password = args.password or prompt("Password")

    # Login
    result = client.login(email, password)

    if result.get("success"):
        console.print(Notification.show(
            f"Logged in as {result['user'].get('email')}",
            'success'
        ))
        return 0
    else:
        console.print(Notification.show(
            result.get("error", "Login failed"),
            'error'
        ))
        return 1


def _cmd_logout(args) -> int:
    """Handle logout command."""
    client = APIClient()
    client.logout()
    console.print(Notification.show("Logged out successfully", 'success'))
    return 0


def _cmd_learn(args) -> int:
    """Handle learn command."""
    client = APIClient()

    if not client.is_authenticated():
        console.print("[red]Please login first: rpa login[/red]")
        return 1

    domain = args.domain or "vocab"

    if domain in ("vocab", "vocabulary"):
        screen = VocabularyScreen(client)
        screen.mode = "learning"
        screen.due_items = client.get_due_vocabulary(20)
        if screen.due_items:
            screen.session.total_items = len(screen.due_items)
            screen._load_next_item()
        screen.run()
    elif domain == "grammar":
        screen = GrammarScreen(client)
        screen.current_exercise = client.get_grammar_exercise()
        screen.mode = "exercise"
        screen.run()
    else:
        console.print(f"[red]Unknown domain: {domain}[/red]")
        return 1

    return 0


def _cmd_progress(args) -> int:
    """Handle progress command."""
    client = APIClient()

    if not client.is_authenticated():
        console.print("[red]Please login first: rpa login[/red]")
        return 1

    screen = ProgressScreen(client)
    screen.run()
    return 0


def _cmd_admin(args) -> int:
    """Handle admin command."""
    client = APIClient()

    if not client.is_authenticated():
        console.print("[red]Please login first: rpa login[/red]")
        return 1

    user = client.get_current_user()
    if user.get("role") not in ("admin", "superadmin"):
        console.print("[red]Admin access required[/red]")
        return 1

    screen = AdminScreen(client)
    screen.run()
    return 0


def main():
    """Main entry point."""
    try:
        run_cli()
    except KeyboardInterrupt:
        console.print("\n[dim]Interrupted[/dim]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
