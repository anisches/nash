"""Stats bar — persistent footer showing live statistics."""

from __future__ import annotations

from textual.widgets import Static
from textual.reactive import reactive


class StatsBar(Static):
    """A bottom-docked bar that shows live statistics for the current module."""

    DEFAULT_CSS = """
    StatsBar {
        dock: bottom;
        width: 100%;
        height: 1;
        background: #1a2332;
        color: #64748b;
        padding: 0 2;
    }
    """

    stats_text = reactive("", layout=False)

    def __init__(self, **kwargs) -> None:
        super().__init__("", **kwargs)

    def watch_stats_text(self, value: str) -> None:
        """Update display when stats change."""
        self.update(value)

    def set_stats(self, **kwargs: str | int | float) -> None:
        """Update stats from keyword arguments.

        Example:
            stats_bar.set_stats(n=100, heads="53%", p_value=0.42)
        """
        parts = []
        for key, val in kwargs.items():
            label = key.replace("_", " ").title()
            if isinstance(val, float):
                val = f"{val:.4f}"
            parts.append(f"[bold #00e5ff]{label}[/]: {val}")
        self.stats_text = "  │  ".join(parts)
