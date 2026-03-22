"""
Design Tokens for Unified UI Experience.

Provides consistent visual language across Web UI (Next.js) and Terminal UI (Textual).
Both interfaces use the same tokens, translated to their respective formats.

Usage:
    # In Python (Terminal UI)
    from rpa.core_api.design_tokens import DESIGN_TOKENS, get_color
    primary_color = get_color("primary", "web")  # "#3b82f6"

    # In JavaScript (Web UI)
    # These tokens would be exported to JSON and used in CSS/Tailwind
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, field


# ============================================================================
# COLOR TOKENS
# ============================================================================

COLORS = {
    # Primary colors
    "primary": {
        "web": "#3b82f6",      # Tailwind blue-500
        "terminal": "blue",     # ANSI blue
        "tailwind": "bg-blue-500",
    },

    # Secondary colors
    "secondary": {
        "web": "#6366f1",       # Tailwind indigo-500
        "terminal": "magenta",
        "tailwind": "bg-indigo-500",
    },

    # Success/Positive
    "success": {
        "web": "#22c55e",       # Tailwind green-500
        "terminal": "green",
        "tailwind": "bg-green-500",
    },

    # Warning/Caution
    "warning": {
        "web": "#f59e0b",       # Tailwind amber-500
        "terminal": "yellow",
        "tailwind": "bg-amber-500",
    },

    # Error/Danger
    "danger": {
        "web": "#ef4444",       # Tailwind red-500
        "terminal": "red",
        "tailwind": "bg-red-500",
    },

    # Info/Neutral
    "info": {
        "web": "#06b6d4",       # Tailwind cyan-500
        "terminal": "cyan",
        "tailwind": "bg-cyan-500",
    },

    # Background colors
    "background": {
        "web": "#ffffff",
        "terminal": "default",   # Terminal default bg
        "tailwind": "bg-white",
    },

    "background_dark": {
        "web": "#0f172a",        # Tailwind slate-900
        "terminal": "black",
        "tailwind": "bg-slate-900",
    },

    # Text colors
    "text_primary": {
        "web": "#1e293b",        # Tailwind slate-800
        "terminal": "white",
        "tailwind": "text-slate-800",
    },

    "text_secondary": {
        "web": "#64748b",        # Tailwind slate-500
        "terminal": "bright_black",
        "tailwind": "text-slate-500",
    },

    "text_muted": {
        "web": "#94a3b8",        # Tailwind slate-400
        "terminal": "black",
        "tailwind": "text-slate-400",
    },

    # Border colors
    "border": {
        "web": "#e2e8f0",        # Tailwind slate-200
        "terminal": "bright_black",
        "tailwind": "border-slate-200",
    },

    "border_focus": {
        "web": "#3b82f6",
        "terminal": "blue",
        "tailwind": "border-blue-500",
    },

    # Role-specific colors
    "superadmin_accent": {
        "web": "#ffd700",        # Gold
        "terminal": "yellow",
        "tailwind": "text-yellow-400",
    },

    "admin_accent": {
        "web": "#3b82f6",
        "terminal": "blue",
        "tailwind": "text-blue-500",
    },

    "user_accent": {
        "web": "#22c55e",
        "terminal": "green",
        "tailwind": "text-green-500",
    },

    "guest_accent": {
        "web": "#94a3b8",
        "terminal": "bright_black",
        "tailwind": "text-slate-400",
    },
}


# ============================================================================
# SPACING TOKENS
# ============================================================================

SPACING = {
    "none": {"value": 0, "tailwind": "0"},
    "xs": {"value": 1, "tailwind": "1"},     # 4px / 1 char
    "sm": {"value": 2, "tailwind": "2"},     # 8px / 2 chars
    "md": {"value": 4, "tailwind": "4"},     # 16px / 4 chars
    "lg": {"value": 6, "tailwind": "6"},     # 24px / 6 chars
    "xl": {"value": 8, "tailwind": "8"},     # 32px / 8 chars
    "2xl": {"value": 12, "tailwind": "12"},  # 48px / 12 chars
    "3xl": {"value": 16, "tailwind": "16"},  # 64px / 16 chars
}


# ============================================================================
# TYPOGRAPHY TOKENS
# ============================================================================

TYPOGRAPHY = {
    "heading_1": {
        "web": {"font_size": "2rem", "font_weight": "bold"},
        "terminal": {"style": "bold", "scale": 2},
        "tailwind": "text-3xl font-bold",
    },

    "heading_2": {
        "web": {"font_size": "1.5rem", "font_weight": "bold"},
        "terminal": {"style": "bold", "scale": 1.5},
        "tailwind": "text-2xl font-bold",
    },

    "heading_3": {
        "web": {"font_size": "1.25rem", "font_weight": "semibold"},
        "terminal": {"style": "bold", "scale": 1.25},
        "tailwind": "text-xl font-semibold",
    },

    "body": {
        "web": {"font_size": "1rem", "font_weight": "normal"},
        "terminal": {"style": "normal", "scale": 1},
        "tailwind": "text-base",
    },

    "body_small": {
        "web": {"font_size": "0.875rem", "font_weight": "normal"},
        "terminal": {"style": "normal", "scale": 0.875},
        "tailwind": "text-sm",
    },

    "caption": {
        "web": {"font_size": "0.75rem", "font_weight": "normal"},
        "terminal": {"style": "dim", "scale": 0.75},
        "tailwind": "text-xs",
    },

    "code": {
        "web": {"font_family": "monospace", "font_size": "0.875em"},
        "terminal": {"style": "monospace", "scale": 1},
        "tailwind": "font-mono text-sm",
    },
}


# ============================================================================
# BORDER TOKENS
# ============================================================================

BORDERS = {
    "none": {
        "web": "none",
        "terminal": "",
        "tailwind": "border-none",
    },

    "thin": {
        "web": "1px solid",
        "terminal": "single",
        "tailwind": "border",
    },

    "medium": {
        "web": "2px solid",
        "terminal": "double",
        "tailwind": "border-2",
    },

    "thick": {
        "web": "4px solid",
        "terminal": "thick",
        "tailwind": "border-4",
    },

    # Rounded corners
    "rounded_sm": {
        "web": "4px",
        "terminal": "╭╮╰╯",  # Box drawing for rounded
        "tailwind": "rounded",
    },

    "rounded_md": {
        "web": "8px",
        "terminal": "╭╮╰╯",
        "tailwind": "rounded-md",
    },

    "rounded_lg": {
        "web": "12px",
        "terminal": "╭╮╰╯",
        "tailwind": "rounded-lg",
    },

    "rounded_full": {
        "web": "9999px",
        "terminal": "○●",  # Circular
        "tailwind": "rounded-full",
    },
}


# ============================================================================
# ANIMATION TOKENS
# ============================================================================

ANIMATIONS = {
    "duration_fast": {
        "web": "150ms",
        "terminal": "instant",
        "tailwind": "duration-150",
    },

    "duration_normal": {
        "web": "300ms",
        "terminal": "instant",
        "tailwind": "duration-300",
    },

    "duration_slow": {
        "web": "500ms",
        "terminal": "instant",
        "tailwind": "duration-500",
    },

    "ease_in": {
        "web": "cubic-bezier(0.4, 0, 1, 1)",
        "terminal": "",
        "tailwind": "ease-in",
    },

    "ease_out": {
        "web": "cubic-bezier(0, 0, 0.2, 1)",
        "terminal": "",
        "tailwind": "ease-out",
    },

    "ease_in_out": {
        "web": "cubic-bezier(0.4, 0, 0.2, 1)",
        "terminal": "",
        "tailwind": "ease-in-out",
    },
}


# ============================================================================
# COMPONENT TOKENS
# ============================================================================

COMPONENTS = {
    "button": {
        "padding": {"x": "md", "y": "sm"},
        "border_radius": "rounded_md",
        "font": "body",
        "min_height": {"web": "40px", "terminal": "3"},
    },

    "input": {
        "padding": {"x": "sm", "y": "xs"},
        "border": "thin",
        "border_radius": "rounded_sm",
        "font": "body",
        "min_height": {"web": "40px", "terminal": "3"},
    },

    "card": {
        "padding": "md",
        "border": "thin",
        "border_radius": "rounded_lg",
        "shadow": {"web": "0 4px 6px -1px rgb(0 0 0 / 0.1)", "terminal": "none"},
    },

    "modal": {
        "padding": "lg",
        "border_radius": "rounded_lg",
        "overlay_opacity": 0.5,
    },

    "progress_bar": {
        "height": {"web": "8px", "terminal": "1"},
        "border_radius": "rounded_full",
        "filled_color": "primary",
        "background_color": "border",
    },

    "toast": {
        "padding": {"x": "md", "y": "sm"},
        "border_radius": "rounded_md",
        "duration": "3000ms",
    },
}


# ============================================================================
# ICON MAPPINGS
# ============================================================================

ICONS = {
    # Icon name -> {web: emoji/icon, terminal: char}
    "check": {"web": "✓", "terminal": "✓"},
    "cross": {"web": "✗", "terminal": "✗"},
    "info": {"web": "ℹ", "terminal": "ℹ"},
    "warning": {"web": "⚠", "terminal": "⚠"},
    "error": {"web": "✕", "terminal": "✕"},
    "success": {"web": "✓", "terminal": "✓"},
    "loading": {"web": "⟳", "terminal": "⠋"},
    "arrow_right": {"web": "→", "terminal": "→"},
    "arrow_left": {"web": "←", "terminal": "←"},
    "arrow_up": {"web": "↑", "terminal": "↑"},
    "arrow_down": {"web": "↓", "terminal": "↓"},
    "menu": {"web": "☰", "terminal": "☰"},
    "close": {"web": "×", "terminal": "×"},
    "search": {"web": "🔍", "terminal": "🔍"},
    "user": {"web": "👤", "terminal": "👤"},
    "settings": {"web": "⚙", "terminal": "⚙"},
    "learn": {"web": "📚", "terminal": "📚"},
    "progress": {"web": "📊", "terminal": "📊"},
    "home": {"web": "🏠", "terminal": "🏠"},
}


# ============================================================================
# MASTER TOKENS OBJECT
# ============================================================================

DESIGN_TOKENS = {
    "colors": COLORS,
    "spacing": SPACING,
    "typography": TYPOGRAPHY,
    "borders": BORDERS,
    "animations": ANIMATIONS,
    "components": COMPONENTS,
    "icons": ICONS,
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_color(name: str, platform: str = "web") -> str:
    """
    Get a color value for a specific platform.

    Args:
        name: Color name (e.g., "primary", "success")
        platform: Platform type ("web", "terminal", "tailwind")

    Returns:
        Color value for the platform
    """
    if name in COLORS:
        return COLORS[name].get(platform, COLORS[name]["web"])
    return COLORS["primary"]["web"]


def get_spacing(name: str, platform: str = "web") -> int:
    """
    Get a spacing value.

    Args:
        name: Spacing name (e.g., "sm", "md", "lg")
        platform: Platform type

    Returns:
        Spacing value
    """
    if name in SPACING:
        return SPACING[name]["value"]
    return SPACING["md"]["value"]


def get_typography(name: str, platform: str = "web") -> Dict[str, Any]:
    """
    Get typography settings.

    Args:
        name: Typography name (e.g., "heading_1", "body")
        platform: Platform type

    Returns:
        Typography settings dictionary
    """
    if name in TYPOGRAPHY:
        return TYPOGRAPHY[name].get(platform, TYPOGRAPHY[name]["web"])
    return TYPOGRAPHY["body"]["web"]


def get_component(name: str) -> Dict[str, Any]:
    """
    Get component design tokens.

    Args:
        name: Component name (e.g., "button", "card")

    Returns:
        Component tokens dictionary
    """
    return COMPONENTS.get(name, {})


def get_icon(name: str, platform: str = "web") -> str:
    """
    Get an icon for a platform.

    Args:
        name: Icon name
        platform: Platform type

    Returns:
        Icon character/emoji
    """
    if name in ICONS:
        return ICONS[name].get(platform, ICONS[name]["web"])
    return "?"


def export_for_web() -> Dict[str, Any]:
    """
    Export design tokens formatted for Web/JavaScript use.

    Returns:
        Dictionary with web-specific values
    """
    return {
        "colors": {k: v["web"] for k, v in COLORS.items()},
        "colorsTailwind": {k: v["tailwind"] for k, v in COLORS.items()},
        "spacing": {k: v["tailwind"] for k, v in SPACING.items()},
        "typography": {k: v["tailwind"] for k, v in TYPOGRAPHY.items()},
        "borders": {k: v["tailwind"] for k, v in BORDERS.items()},
        "animations": {k: v["tailwind"] for k, v in ANIMATIONS.items()},
        "icons": {k: v["web"] for k, v in ICONS.items()},
    }


def export_for_terminal() -> Dict[str, Any]:
    """
    Export design tokens formatted for Terminal/Textual use.

    Returns:
        Dictionary with terminal-specific values
    """
    return {
        "colors": {k: v["terminal"] for k, v in COLORS.items()},
        "spacing": {k: v["value"] for k, v in SPACING.items()},
        "typography": {k: v["terminal"] for k, v in TYPOGRAPHY.items()},
        "borders": {k: v["terminal"] for k, v in BORDERS.items()},
        "icons": {k: v["terminal"] for k, v in ICONS.items()},
    }


def to_css_variables() -> str:
    """
    Generate CSS custom properties from design tokens.

    Returns:
        CSS string with :root variables
    """
    lines = [":root {"]

    # Colors
    for name, values in COLORS.items():
        web_color = values["web"]
        lines.append(f"  --color-{name}: {web_color};")

    # Spacing
    for name, values in SPACING.items():
        value = values["value"]
        lines.append(f"  --spacing-{name}: {value * 4}px;")

    # Typography
    for name, values in TYPOGRAPHY.items():
        web_values = values["web"]
        if "font_size" in web_values:
            lines.append(f"  --font-size-{name}: {web_values['font_size']};")
        if "font_weight" in web_values:
            lines.append(f"  --font-weight-{name}: {web_values['font_weight']};")

    lines.append("}")
    return "\n".join(lines)


# Generate CSS when run as script
if __name__ == "__main__":
    print(to_css_variables())
