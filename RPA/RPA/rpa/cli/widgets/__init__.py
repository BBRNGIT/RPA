"""
Terminal UI Widgets.

Reusable components for building the terminal interface.
"""

from rich.console import Console, RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.progress import Progress, BarColumn, TextColumn
from rich.layout import Layout
from rich.style import Style
from typing import Any, Dict, List, Optional
import time

console = Console()


class Flashcard:
    """
    Interactive flashcard widget for vocabulary learning.

    Displays a card that can be flipped to reveal the answer,
    with quality rating buttons (SM-2 algorithm).
    """

    def __init__(
        self,
        word_id: str,
        front: str,
        back: str,
        examples: List[str] = None,
        part_of_speech: str = "",
        difficulty: int = 1,
        hint: Optional[str] = None
    ):
        self.word_id = word_id
        self.front = front
        self.back = back
        self.examples = examples or []
        self.part_of_speech = part_of_speech
        self.difficulty = difficulty
        self.hint = hint
        self.flipped = False

    def render(self) -> Panel:
        """Render the flashcard."""
        if self.flipped:
            content = Text()
            content.append(self.back, style="bold green")
            content.append("\n\n")

            if self.examples:
                content.append("Examples:\n", style="dim")
                for ex in self.examples[:2]:
                    content.append(f"  • {ex}\n", style="italic")

            title = f"📖 {self.front}"
        else:
            content = Text()
            content.append(self.front, style="bold blue center")

            if self.hint:
                content.append(f"\n\n💡 {self.hint}", style="dim italic")

            title = "📚 Vocabulary"

        # Add difficulty indicator
        diff_stars = "★" * self.difficulty + "☆" * (5 - self.difficulty)
        subtitle = f"[{diff_stars}]"

        return Panel(
            content,
            title=title,
            subtitle=subtitle,
            border_style="blue",
            padding=(2, 4),
            expand=False
        )

    def flip(self) -> None:
        """Flip the card."""
        self.flipped = not self.flipped

    def render_rating_options(self) -> Table:
        """Render quality rating options (SM-2)."""
        table = Table(show_header=False, box=None, expand=True)
        table.add_column("Key", style="bold", width=4)
        table.add_column("Rating", style="cyan")
        table.add_column("Description", style="dim")

        ratings = [
            ("0", "Again", "Complete failure - no recollection"),
            ("1", "Hard", "Incorrect, but somewhat familiar"),
            ("2", "Medium", "Incorrect, but recognized the answer"),
            ("3", "Good", "Correct with difficulty"),
            ("4", "Easy", "Correct after hesitation"),
            ("5", "Perfect", "Immediate, confident recall"),
        ]

        for key, rating, desc in ratings:
            table.add_row(f"[{key}]", rating, desc)

        return table


class ProgressBar:
    """
    Progress bar widget for tracking learning progress.

    Supports multiple progress items and animated display.
    """

    def __init__(
        self,
        total: int = 100,
        completed: int = 0,
        label: str = "Progress",
        color: str = "blue"
    ):
        self.total = total
        self.completed = completed
        self.label = label
        self.color = color

    def render(self, width: int = 40) -> Panel:
        """Render the progress bar."""
        if self.total == 0:
            percentage = 0
        else:
            percentage = (self.completed / self.total) * 100

        # Build progress bar
        filled = int((self.completed / max(self.total, 1)) * width)
        empty = width - filled

        bar = Text()
        bar.append("█" * filled, style=self.color)
        bar.append("░" * empty, style="dim")
        bar.append(f" {percentage:.1f}%", style="bold")

        return Panel(
            bar,
            title=f"{self.label}: {self.completed}/{self.total}",
            border_style=self.color
        )

    def update(self, completed: int) -> None:
        """Update progress."""
        self.completed = min(completed, self.total)


class AsciiChart:
    """
    ASCII chart widget for displaying data visually.

    Supports line charts and bar charts in the terminal.
    """

    def __init__(self, title: str = "Chart"):
        self.title = title
        self.data: List[float] = []
        self.labels: List[str] = []
        self.width = 50
        self.height = 10

    def set_data(self, data: List[float], labels: List[str] = None) -> None:
        """Set chart data."""
        self.data = data
        self.labels = labels or [str(i) for i in range(len(data))]

    def render_line(self) -> str:
        """Render as line chart."""
        if not self.data:
            return "No data"

        max_val = max(self.data) if self.data else 1
        min_val = min(self.data) if self.data else 0
        range_val = max_val - min_val if max_val != min_val else 1

        lines = []
        lines.append(f"     {self.title}")
        lines.append(f"  {max_val:.0f} ┤")

        for i, val in enumerate(self.data):
            # Normalize to height
            normalized = int(((val - min_val) / range_val) * (self.height - 1))
            normalized = max(0, min(self.height - 1, normalized))

            # Create line
            line = [" "] * self.width
            pos = int((i / max(len(self.data) - 1, 1)) * (self.width - 1))
            line[pos] = "●"

            lines.append(f"     │{''.join(line)}")

        lines.append(f"  {min_val:.0f} └" + "─" * (self.width - 1) + "►")

        return "\n".join(lines)

    def render_bar(self) -> Table:
        """Render as bar chart."""
        if not self.data:
            return Table()

        max_val = max(self.data) if self.data else 1

        table = Table(title=self.title, show_header=False, box=None)
        table.add_column("Label", style="cyan", width=12)
        table.add_column("Bar", width=self.width)
        table.add_column("Value", style="bold", justify="right")

        for label, val in zip(self.labels, self.data):
            # Create bar
            bar_width = int((val / max_val) * (self.width - 2))
            bar = "█" * bar_width

            table.add_row(label[:12], bar, f"{val:.1f}")

        return table

    def render(self, chart_type: str = "bar") -> str:
        """Render chart."""
        if chart_type == "line":
            return self.render_line()
        return self.render_bar()


class Menu:
    """
    Interactive menu widget for navigation.

    Supports keyboard navigation and selection.
    """

    def __init__(
        self,
        title: str = "Menu",
        options: List[Dict[str, Any]] = None
    ):
        self.title = title
        self.options = options or []
        self.selected = 0

    def add_option(
        self,
        key: str,
        label: str,
        description: str = "",
        handler: callable = None
    ) -> None:
        """Add menu option."""
        self.options.append({
            "key": key,
            "label": label,
            "description": description,
            "handler": handler
        })

    def render(self) -> Panel:
        """Render the menu."""
        table = Table(show_header=False, box=None, expand=True)
        table.add_column("Key", style="bold yellow", width=6)
        table.add_column("Option", style="cyan")
        table.add_column("Description", style="dim")

        for opt in self.options:
            key = f"[{opt['key']}]"
            label = opt['label']
            desc = opt.get('description', '')
            table.add_row(key, label, desc)

        return Panel(table, title=self.title, border_style="blue")

    def get_selected(self, key: str) -> Optional[Dict[str, Any]]:
        """Get option by key."""
        for opt in self.options:
            if opt['key'].lower() == key.lower():
                return opt
        return None


class StatusBox:
    """
    Status display widget for showing current state.

    Displays user info, session stats, or system messages.
    """

    def __init__(
        self,
        title: str = "Status",
        items: Dict[str, Any] = None
    ):
        self.title = title
        self.items = items or {}

    def set_item(self, key: str, value: Any) -> None:
        """Set status item."""
        self.items[key] = value

    def render(self) -> Panel:
        """Render status box."""
        table = Table(show_header=False, box=None)
        table.add_column("Key", style="dim", width=15)
        table.add_column("Value", style="bold")

        for key, value in self.items.items():
            table.add_row(key, str(value))

        return Panel(table, title=self.title, border_style="green")


class LearningSession:
    """
    Complete learning session display.

    Combines flashcard, progress, and controls into one view.
    """

    def __init__(self, domain: str = "vocabulary"):
        self.domain = domain
        self.current_item = 0
        self.total_items = 0
        self.correct = 0
        self.incorrect = 0
        self.start_time = time.time()
        self.flashcard: Optional[Flashcard] = None

    def set_flashcard(self, flashcard: Flashcard) -> None:
        """Set current flashcard."""
        self.flashcard = flashcard

    def render(self) -> Layout:
        """Render complete session view."""
        layout = Layout()

        # Header
        elapsed = time.time() - self.start_time
        header = Panel(
            Text(
                f"Domain: {self.domain.upper()} | "
                f"Progress: {self.current_item}/{self.total_items} | "
                f"Time: {int(elapsed // 60):02d}:{int(elapsed % 60):02d}",
                style="bold"
            ),
            border_style="blue"
        )

        # Main content (flashcard)
        if self.flashcard:
            main = self.flashcard.render()
        else:
            main = Panel("No content", title="Loading...")

        # Progress bar
        progress = ProgressBar(
            total=self.total_items,
            completed=self.current_item,
            color="green" if self.correct > self.incorrect else "red"
        ).render()

        # Stats
        stats = StatusBox(
            title="Session Stats",
            items={
                "Correct": self.correct,
                "Incorrect": self.incorrect,
                "Accuracy": f"{(self.correct / max(self.correct + self.incorrect, 1)) * 100:.1f}%"
            }
        ).render()

        layout.split_column(
            Layout(header, size=3),
            Layout(main, size=12),
            Layout(progress, size=3),
            Layout(stats, size=6),
        )

        return layout

    def record_answer(self, correct: bool) -> None:
        """Record an answer."""
        if correct:
            self.correct += 1
        else:
            self.incorrect += 1
        self.current_item += 1


class Notification:
    """
    Notification/toast widget for messages.

    Shows temporary messages with auto-dismiss.
    """

    TYPES = {
        "success": ("✓", "green"),
        "error": ("✗", "red"),
        "warning": ("⚠", "yellow"),
        "info": ("ℹ", "blue"),
    }

    @classmethod
    def show(
        cls,
        message: str,
        type: str = "info",
        duration: float = 2.0
    ) -> Panel:
        """Show a notification."""
        icon, color = cls.TYPES.get(type, cls.TYPES["info"])

        content = Text()
        content.append(f"{icon} ", style=f"bold {color}")
        content.append(message)

        return Panel(
            content,
            border_style=color,
            padding=(0, 2)
        )


# Utility functions

def clear_screen() -> None:
    """Clear the terminal screen."""
    console.clear()


def print_header(title: str, subtitle: str = "") -> None:
    """Print a formatted header."""
    console.rule(f"[bold blue]{title}[/bold blue]")
    if subtitle:
        console.print(f"[dim]{subtitle}[/dim]", justify="center")
    console.print()


def print_footer(message: str = "") -> None:
    """Print a formatted footer."""
    console.print()
    console.rule(style="dim")
    if message:
        console.print(f"[dim]{message}[/dim]", justify="center")


def confirm(message: str, default: bool = True) -> bool:
    """Ask for confirmation."""
    hint = "[Y/n]" if default else "[y/N]"
    response = console.input(f"{message} {hint}: ").strip().lower()

    if not response:
        return default
    return response in ("y", "yes")


def prompt(message: str, default: str = "") -> str:
    """Prompt for input."""
    hint = f" [{default}]" if default else ""
    response = console.input(f"{message}{hint}: ").strip()
    return response if response else default


def select(
    message: str,
    options: List[str],
    default: int = 0
) -> int:
    """Select from options (returns index)."""
    console.print(f"\n[bold]{message}[/bold]\n")

    for i, opt in enumerate(options):
        marker = ">" if i == default else " "
        console.print(f"  {marker} [{i+1}] {opt}")

    console.print()
    choice = console.input(f"Select [1-{len(options)}]: ").strip()

    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(options):
            return idx

    return default
