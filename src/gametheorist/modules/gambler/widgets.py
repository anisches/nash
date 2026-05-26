"""Gambler's Ruin — custom Textual widgets.

WealthBar, WalkPathChart, RuinCurveChart, and summary stats.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static
from textual_plotext import PlotextPlot

from gametheorist.theme import (
    AMBER,
    BG_CARD,
    BG_PANEL,
    LIME,
    NEON_CYAN,
    NEON_MAGENTA,
    TEXT_DIM,
    TEXT_PRIMARY,
)

from gametheorist.modules.gambler.engine import (
    BatchRuinStats,
    WalkResult,
    exact_ruin_probability,
)


# ── Wealth / Capital Bar ────────────────────────────────────────


class WealthBar(Static):
    """Horizontal bar showing gambler capital vs house capital.

    Looks like:  [████████░░░░░░░░░░░░]  42 / 100
    With colors: cyan for gambler, magenta-ish for house.
    """

    DEFAULT_CSS = """
    WealthBar {
        width: 100%;
        height: auto;
        min-height: 5;
        background: #1a2332;
        border: round #2a3a4f;
        padding: 1 2;
        margin: 1 0;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__("", **kwargs)
        self._current = 0
        self._total = 100

    def update_capital(self, current: int, total: int) -> None:
        self._current = current
        self._total = total
        self._render()

    def _render(self) -> None:
        if self._total <= 0:
            self.update("[dim]No capital[/]")
            return

        gambler = self._current
        house = self._total - self._current
        pct_g = gambler / self._total
        pct_h = house / self._total

        bar_width = 36
        g_bars = int(pct_g * bar_width)
        h_bars = bar_width - g_bars

        bar = (
            f"[bold {NEON_CYAN}]{'█' * g_bars}[/]"
            f"[bold #ff6b6b]{'█' * h_bars}[/]"
        )

        text = (
            f"[bold {NEON_CYAN}]YOU[/]  {gambler:>4}  │  {bar}  │  {house:>4}  [bold #ff6b6b]HOUSE[/]\n"
            f"[dim]Total capital in play: {self._total}[/]"
        )
        self.update(text)


# ── Live Walk Path Chart ────────────────────────────────────────


class WalkPathChart(PlotextPlot):
    """Live line chart of one or more random walks.

    Shows capital over time until absorption.
    """

    DEFAULT_CSS = """
    WalkPathChart {
        width: 100%;
        height: 1fr;
        min-height: 16;
        background: #1e293b;
        border: round #334155;
        padding: 0;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._walks: list[list[int]] = []   # list of position sequences
        self._labels: list[str] = []

    def on_mount(self) -> None:
        self._draw_empty()

    def _setup_theme(self) -> None:
        self.plt.theme("dark")
        self.plt.canvas_color((30, 41, 59))
        self.plt.axes_color((15, 23, 42))
        self.plt.ticks_color((148, 163, 184))

    def _draw_empty(self) -> None:
        self.plt.clear_figure()
        self._setup_theme()
        self.plt.title("Capital Over Time (Random Walk)")
        self.plt.xlabel("Step")
        self.plt.ylabel("Capital")
        self.plt.ylim(0, 10)
        self.plt.xlim(0, 50)
        self.refresh()

    def set_walks(self, walks: list[list[int]], labels: list[str] | None = None) -> None:
        """Update with one or more completed or live walks."""
        self._walks = walks
        self._labels = labels or [f"Walk {i+1}" for i in range(len(walks))]
        self._draw()

    def _draw(self) -> None:
        self.plt.clear_figure()
        self._setup_theme()

        if not self._walks:
            self._draw_empty()
            return

        max_len = max(len(w) for w in self._walks)
        max_cap = max(max(w) for w in self._walks)
        min_cap = min(min(w) for w in self._walks)

        self.plt.title("Capital Over Time — Absorption at 0 or N")
        self.plt.xlabel("Step")
        self.plt.ylabel("Capital")

        self.plt.ylim(max(0, min_cap - 2), max_cap + 2)
        self.plt.xlim(0, max(20, max_len))

        colors = [
            (56, 189, 248),   # cyan
            (251, 113, 133),  # rose
            (251, 191, 36),   # amber
            (74, 222, 128),   # green
        ]

        for i, walk in enumerate(self._walks):
            x = list(range(len(walk)))
            color = colors[i % len(colors)]
            label = self._labels[i] if i < len(self._labels) else f"Walk {i+1}"
            self.plt.plot(x, walk, label=label, color=color)

        self.refresh()

    def clear_chart(self) -> None:
        self._walks = []
        self._labels = []
        self._draw_empty()


# ── Ruin Probability Curve ──────────────────────────────────────


class RuinCurveChart(PlotextPlot):
    """Exact ruin probability curve vs starting capital + simulated points."""

    DEFAULT_CSS = """
    RuinCurveChart {
        width: 100%;
        height: 1fr;
        min-height: 14;
        background: #1e293b;
        border: round #334155;
        padding: 0;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._starts: list[int] = []
        self._exact: list[float] = []
        self._sim: list[float] | None = None
        self._total = 100
        self._p = 0.5

    def on_mount(self) -> None:
        self._draw_empty()

    def _setup_theme(self) -> None:
        self.plt.theme("dark")
        self.plt.canvas_color((30, 41, 59))
        self.plt.axes_color((15, 23, 42))
        self.plt.ticks_color((148, 163, 184))

    def _draw_empty(self) -> None:
        self.plt.clear_figure()
        self._setup_theme()
        self.plt.title("P(Ruin) vs Starting Capital")
        self.plt.xlabel("Starting Capital (i)")
        self.plt.ylabel("P(ruin)")
        self.plt.ylim(0, 1.05)
        self.plt.xlim(0, 20)
        self.refresh()

    def set_exact(self, starts: list[int], exact_probs: list[float], total: int, p: float) -> None:
        self._starts = starts
        self._exact = exact_probs
        self._total = total
        self._p = p
        self._draw()

    def set_simulated(self, sim_probs: list[float]) -> None:
        self._sim = sim_probs
        self._draw()

    def _draw(self) -> None:
        self.plt.clear_figure()
        self._setup_theme()

        if not self._starts:
            self._draw_empty()
            return

        title_p = f"p = {self._p:.2f}"
        self.plt.title(f"P(Ruin) vs Starting Capital  —  N={self._total}, {title_p}")
        self.plt.xlabel("Starting Capital i")
        self.plt.ylabel("P(ruin)")

        self.plt.ylim(0, 1.05)
        self.plt.xlim(0, self._total)

        # Exact curve
        self.plt.plot(
            self._starts,
            self._exact,
            label="Exact",
            color=(56, 189, 248),
        )

        # Simulated points (if present)
        if self._sim is not None and len(self._sim) == len(self._starts):
            self.plt.scatter(
                self._starts,
                self._sim,
                label="Simulated (5k trials)",
                color=(251, 113, 133),
                marker="cross",
            )

        self.refresh()

    def clear_data(self) -> None:
        self._starts = []
        self._exact = []
        self._sim = None
        self._draw_empty()


# ── Stats Panel ─────────────────────────────────────────────────


class RuinStatsPanel(Static):
    """Formatted panel with live stats + batch simulation results."""

    DEFAULT_CSS = """
    RuinStatsPanel {
        width: 100%;
        height: auto;
        min-height: 9;
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
        self.update(
            "[bold #00e5ff]📊 Gambler's Ruin Statistics[/]\n\n"
            "[#64748b]  Set capital & bias, then run simulations…[/]"
        )

    def update_live(self, current: int, total: int, p: float) -> None:
        """Show live state before any big simulation."""
        ruin_p = exact_ruin_probability(current, total, p)
        exp_dur = None
        try:
            from gametheorist.modules.gambler.engine import exact_expected_duration
            exp_dur = exact_expected_duration(current, total, p)
        except Exception:
            pass

        lines = [
            "[bold #00e5ff]📊 Current Position[/]",
            "",
            f"  Capital: [bold {NEON_CYAN}]{current}[/] / {total}",
            f"  House:   [bold #ff6b6b]{total - current}[/]",
            f"  Bias p (you win): [bold]{p:.2f}[/]",
            "",
            f"  [bold]Exact P(ruin) now:[/] [bold #ff00e5]{ruin_p:.4f}[/] ({ruin_p*100:.1f}%)",
        ]
        if exp_dur is not None:
            lines.append(f"  [bold]E[steps] until end:[/] ~{exp_dur:.0f}")

        self.update("\n".join(lines))

    def update_batch(self, stats: BatchRuinStats) -> None:
        """Show results after a batch simulation."""
        lines = [
            "[bold #00e5ff]📊 Batch Simulation Results[/]",
            "",
            f"  Trials: {stats.n_trials:,}   |   p = {stats.p:.2f}",
            f"  Starting capital i = {stats.start},  N = {stats.total}",
            "",
            f"  [bold {NEON_MAGENTA}]Ruined:[/] {stats.ruined:,}  →  [bold #ff00e5]{stats.ruin_rate:.2%}[/]",
            f"  Reached N: {stats.reached_total:,}",
            "",
            f"  Avg duration:  {stats.avg_duration:,.0f} steps",
            f"  Median:        {stats.median_duration:,.0f}",
            f"  Range:         {stats.min_duration} – {stats.max_duration}",
        ]
        self.update("\n".join(lines))

    def clear_stats(self) -> None:
        self._render_empty()
