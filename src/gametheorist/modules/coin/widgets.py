"""Custom Textual widgets for the Coin module."""

from __future__ import annotations

import math
from typing import Sequence

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.reactive import reactive
from textual.timer import Timer
from textual.widget import Widget
from textual.widgets import Static
from textual_plotext import PlotextPlot

from gametheorist.theme import (
    NEON_CYAN,
    NEON_MAGENTA,
    AMBER,
    LIME,
    BG_DARK,
    BG_PANEL,
    BG_CARD,
    TEXT_PRIMARY,
    TEXT_DIM,
    SUCCESS,
    ERROR,
)

from gametheorist.modules.coin.engine import ZTestResult


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ASCII art frames for coin animation
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

COIN_HEADS = """\
[bold #00e5ff]
    ╭─────────────╮
    │  ┌───────┐  │
    │  │ ╦ ╦   │  │
    │  │ ╠═╣   │  │
    │  │ ╩ ╩   │  │
    │  │ HEADS │  │
    │  └───────┘  │
    ╰─────────────╯[/]"""

COIN_TAILS = """\
[bold #ff00e5]
    ╭─────────────╮
    │  ┌───────┐  │
    │  │ ╔╦╗   │  │
    │  │  ║    │  │
    │  │  ╩    │  │
    │  │ TAILS │  │
    │  └───────┘  │
    ╰─────────────╯[/]"""

# Spinning frames — narrow "edge" views for animation
SPIN_FRAMES = [
    """\
[bold #ffab00]
    ╭─────────────╮
    │  ┌───────┐  │
    │  │       │  │
    │  │  ───  │  │
    │  │       │  │
    │  │  ···  │  │
    │  └───────┘  │
    ╰─────────────╯[/]""",
    """\
[bold #76ff03]
    ╭─────────────╮
    │   ┌─────┐   │
    │   │     │   │
    │   │  ╳  │   │
    │   │     │   │
    │   │ ··· │   │
    │   └─────┘   │
    ╰─────────────╯[/]""",
    """\
[bold #ffab00]
    ╭─────────────╮
    │    ┌───┐    │
    │    │   │    │
    │    │ ● │    │
    │    │   │    │
    │    │···│    │
    │    └───┘    │
    ╰─────────────╯[/]""",
    """\
[bold #76ff03]
    ╭─────────────╮
    │     ┌─┐     │
    │     │ │     │
    │     │█│     │
    │     │ │     │
    │     │·│     │
    │     └─┘     │
    ╰─────────────╯[/]""",
    """\
[bold #ffab00]
    ╭─────────────╮
    │    ┌───┐    │
    │    │   │    │
    │    │ ● │    │
    │    │   │    │
    │    │···│    │
    │    └───┘    │
    ╰─────────────╯[/]""",
    """\
[bold #76ff03]
    ╭─────────────╮
    │   ┌─────┐   │
    │   │     │   │
    │   │  ╳  │   │
    │   │     │   │
    │   │ ··· │   │
    │   └─────┘   │
    ╰─────────────╯[/]""",
]

COIN_BLANK = """\
[dim]
    ╭─────────────╮
    │             │
    │    Ready    │
    │     to      │
    │    flip!    │
    │             │
    │    [⎵]      │
    ╰─────────────╯[/]"""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CoinWidget
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class CoinWidget(Static):
    """Displays a large ASCII-art coin with flip animation."""

    DEFAULT_CSS = """
    CoinWidget {
        width: 100%;
        height: auto;
        min-height: 10;
        content-align: center middle;
        text-align: center;
        padding: 1 0;
    }
    """

    is_animating: reactive[bool] = reactive(False)

    def __init__(self, **kwargs) -> None:
        super().__init__(COIN_BLANK, **kwargs)
        self._anim_timer: Timer | None = None
        self._anim_frame: int = 0
        self._anim_result: str = "H"
        self._on_land: callable = lambda: None  # type: ignore[assignment]

    def start_flip(
        self,
        result: str,
        on_land: callable | None = None,  # type: ignore[type-arg]
    ) -> None:
        """Start the flip animation, landing on *result* ('H' or 'T').

        Parameters
        ----------
        result : str  The face to land on.
        on_land : callable, optional  Callback invoked after the animation.
        """
        if self.is_animating:
            return
        self.is_animating = True
        self._anim_frame = 0
        self._anim_result = result
        self._on_land = on_land or (lambda: None)
        # ~0.8s total: 6 frames × 130ms each ≈ 780ms
        self._anim_timer = self.set_interval(0.13, self._tick_animation)

    def show_result(self, result: str) -> None:
        """Immediately display a result without animation."""
        self.update(COIN_HEADS if result == "H" else COIN_TAILS)

    def reset(self) -> None:
        """Return to the blank/ready state."""
        if self._anim_timer is not None:
            self._anim_timer.stop()
            self._anim_timer = None
        self.is_animating = False
        self.update(COIN_BLANK)

    def _tick_animation(self) -> None:
        """Advance one animation frame."""
        if self._anim_frame < len(SPIN_FRAMES):
            self.update(SPIN_FRAMES[self._anim_frame])
            self._anim_frame += 1
        else:
            # Land on the result
            if self._anim_timer is not None:
                self._anim_timer.stop()
                self._anim_timer = None
            self.is_animating = False
            self.update(
                COIN_HEADS if self._anim_result == "H" else COIN_TAILS
            )
            self._on_land()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ConvergenceChart
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class ConvergenceChart(PlotextPlot):
    """Line chart showing the running average of heads converging
    toward the true bias."""

    DEFAULT_CSS = """
    ConvergenceChart {
        width: 100%;
        height: 100%;
        min-height: 14;
        background: #c0c0c0;
        border: solid #000000;
        padding: 0;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._running_avg: list[float] = []
        self._true_bias: float = 0.5

    def on_mount(self) -> None:
        """Draw an empty chart initially."""
        self._draw_empty()

    def _apply_theme(self) -> None:
        """Apply light theme to plotext."""
        self.plt.theme("light")
        self.plt.canvas_color((255, 255, 255))
        self.plt.axes_color((192, 192, 192))
        self.plt.ticks_color((0, 0, 0))

    def _draw_empty(self) -> None:
        """Draw an empty chart with title and axis labels."""
        self.plt.clear_figure()
        self._apply_theme()
        self.plt.title("Convergence of Sample Proportion")
        self.plt.xlabel("Flip #")
        self.plt.ylabel("P(Heads)")
        self.plt.ylim(0.0, 1.0)
        self.plt.xlim(0, 10)
        # Draw the bias line
        self.plt.hline(self._true_bias, color=(255, 0, 0))
        self.refresh()

    def update_data(
        self,
        running_avg: list[float],
        true_bias: float,
    ) -> None:
        """Redraw the chart with new data.

        Parameters
        ----------
        running_avg : list[float]  Running proportion of heads.
        true_bias   : float        The coin's actual bias (shown as hline).
        """
        self._running_avg = running_avg
        self._true_bias = true_bias

        self.plt.clear_figure()
        self._apply_theme()
        self.plt.title("Convergence of Sample Proportion")
        self.plt.xlabel("Flip #")
        self.plt.ylabel("P(Heads)")
        self.plt.ylim(0.0, 1.0)

        n = len(running_avg)
        if n == 0:
            self._draw_empty()
            return

        x = list(range(1, n + 1))
        self.plt.plot(x, running_avg, color=(0, 0, 255), label="Observed")
        # True bias horizontal line
        self.plt.hline(true_bias, color=(255, 0, 0))
        # Fair coin reference if bias != 0.5
        if abs(true_bias - 0.5) > 0.01:
            self.plt.hline(0.5, color=(128, 128, 128))

        self.refresh()

    def clear_chart(self) -> None:
        """Reset to a blank chart."""
        self._running_avg = []
        self._draw_empty()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# StatsPanel
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class StatsPanel(Static):
    """Formatted panel showing live flip statistics and z-test results."""

    DEFAULT_CSS = """
    StatsPanel {
        width: 100%;
        height: auto;
        min-height: 10;
        background: #1a2332;
        border: round #2a3a4f;
        padding: 1 2;
        margin: 1 0 0 0;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__("", **kwargs)
        self._render_empty()

    def _render_empty(self) -> None:
        """Show placeholder text before any flips."""
        self.update(
            "[bold #00e5ff]📊 Statistics[/]\n\n"
            "[#64748b]  Flip the coin to start collecting data…[/]"
        )

    def update_stats(
        self,
        n_heads: int,
        n_tails: int,
        z_result: ZTestResult | None,
    ) -> None:
        """Redraw the stats panel with current data.

        Parameters
        ----------
        n_heads  : int           Cumulative heads count.
        n_tails  : int           Cumulative tails count.
        z_result : ZTestResult   Result from ``z_test_fair``, or None.
        """
        total = n_heads + n_tails
        if total == 0:
            self._render_empty()
            return

        heads_pct = n_heads / total * 100
        tails_pct = n_tails / total * 100

        lines: list[str] = [
            "[bold #00e5ff]📊 Statistics[/]",
            "",
            f"  [bold]Total Flips:[/]   {total:,}",
            f"  [bold #00e5ff]Heads:[/]         {n_heads:,}  ({heads_pct:.1f}%)",
            f"  [bold #ff00e5]Tails:[/]         {n_tails:,}  ({tails_pct:.1f}%)",
        ]

        if z_result is not None and total >= 2:
            ci = z_result.confidence_interval
            verdict_color = "#ef4444" if z_result.reject_null else "#22c55e"
            verdict_icon = "✘" if z_result.reject_null else "✔"
            verdict_text = (
                "REJECT H₀ — coin is biased!"
                if z_result.reject_null
                else "Cannot reject H₀ — looks fair"
            )

            lines += [
                "",
                "  [bold #ffab00]─── Hypothesis Test (H₀: p = 0.5) ───[/]",
                f"  [bold]Z-statistic:[/]   {z_result.z_stat:+.4f}",
                f"  [bold]P-value:[/]       {z_result.p_value:.6f}",
                f"  [bold]95% CI:[/]        [{ci[0]:.4f}, {ci[1]:.4f}]",
                "",
                f"  [{verdict_color}]{verdict_icon}  {verdict_text}[/]",
            ]

        self.update("\n".join(lines))

    def clear_stats(self) -> None:
        """Reset to the empty state."""
        self._render_empty()
