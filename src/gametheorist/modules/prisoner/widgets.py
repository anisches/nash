"""Prisoner's Dilemma — custom Textual widgets.

PayoffMatrix, LiveMatchDisplay, ScoreHistoryChart, TournamentTable, EvolutionChart.
"""

from __future__ import annotations

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
    SUCCESS,
    ERROR,
    TEXT_DIM,
    TEXT_PRIMARY,
)

from gametheorist.modules.prisoner.engine import (
    Move,
    PAYOFFS,
    RoundResult,
    GameResult,
    TournamentResult,
    EvolutionResult,
)


# ── Payoff Matrix Widget ────────────────────────────────────────


class PayoffMatrix(Static):
    """Beautiful 2x2 payoff matrix with current outcome highlighted."""

    DEFAULT_CSS = """
    PayoffMatrix {
        width: 100%;
        height: auto;
        min-height: 11;
        background: #1a2332;
        border: round #2a3a4f;
        padding: 1 2;
        margin: 0 0 1 0;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__("", **kwargs)
        self._last_round: RoundResult | None = None

    def update_matrix(self, last_round: RoundResult | None = None) -> None:
        self._last_round = last_round
        self._render()

    def _render(self) -> None:
        lines: list[str] = []
        lines.append("[bold #00e5ff]Payoff Matrix (your score, opponent score)[/]")
        lines.append("")

        # Header
        lines.append("             [bold]Opponent[/]")
        lines.append("          [bold]C[/]             [bold]D[/]")

        # Row C
        c_c = PAYOFFS[("C", "C")]
        c_d = PAYOFFS[("C", "D")]
        c_line = f"  [bold]You C[/]   {self._cell(c_c, 'C', 'C')}      {self._cell(c_d, 'C', 'D')}"
        lines.append(c_line)

        # Row D
        d_c = PAYOFFS[("D", "C")]
        d_d = PAYOFFS[("D", "D")]
        d_line = f"  [bold]You D[/]   {self._cell(d_c, 'D', 'C')}      {self._cell(d_d, 'D', 'D')}"
        lines.append(d_line)

        lines.append("")
        lines.append("[dim]T=5 (Temptation)  R=3 (Reward)  P=1 (Punishment)  S=0 (Sucker)[/]")

        if self._last_round:
            r = self._last_round
            outcome = f"[bold]Last outcome:[/] You {r.player1_move} vs Opp {r.player2_move} → [bold #ffab00]+{r.player1_score}[/] for you"
            lines.append("")
            lines.append(outcome)

        self.update("\n".join(lines))

    def _cell(self, payoff: int, my_move: str, opp_move: str) -> str:
        """Format a single cell, highlight if it was the last outcome."""
        highlight = False
        if self._last_round:
            if self._last_round.player1_move == my_move and self._last_round.player2_move == opp_move:
                highlight = True

        val = f"{payoff},{PAYOFFS[(opp_move, my_move)]}"

        if highlight:
            return f"[bold on #334155 #ffab00]{val}[/]"
        return f"[#e2e8f0]{val}[/]"


# ── Live Match Display ──────────────────────────────────────────


class LiveMatchDisplay(Static):
    """Shows current round moves, cumulative scores, and recent history strip."""

    DEFAULT_CSS = """
    LiveMatchDisplay {
        width: 100%;
        height: auto;
        min-height: 8;
        background: #1a2332;
        border: round #2a3a4f;
        padding: 1 2;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__("", **kwargs)
        self._p1_name = "You"
        self._p2_name = "Opponent"
        self._p1_score = 0
        self._p2_score = 0
        self._history: list[RoundResult] = []

    def set_players(self, p1_name: str, p2_name: str) -> None:
        self._p1_name = p1_name
        self._p2_name = p2_name

    def update_match(
        self,
        p1_score: int,
        p2_score: int,
        history: list[RoundResult],
    ) -> None:
        self._p1_score = p1_score
        self._p2_score = p2_score
        self._history = history[-12:]  # last 12 rounds
        self._render()

    def _render(self) -> None:
        lines: list[str] = []
        lines.append(f"[bold {NEON_CYAN}]{self._p1_name}[/]  [bold #ffab00]{self._p1_score}[/]   vs   [bold #ff6b6b]{self._p2_score}[/]  [bold]{self._p2_name}[/]")
        lines.append("")

        if not self._history:
            lines.append("[dim]No rounds played yet. Choose strategies and press Play.[/]")
        else:
            # Recent history strip
            strip: list[str] = []
            for r in self._history:
                p1c = "[bold #76ff03]C[/]" if r.player1_move == "C" else "[bold #ef4444]D[/]"
                p2c = "[bold #76ff03]C[/]" if r.player2_move == "C" else "[bold #ef4444]D[/]"
                strip.append(f"{p1c}{p2c}")

            lines.append("[dim]Recent (you/opp):[/] " + " ".join(strip))
            lines.append(f"[dim](showing last {len(self._history)} rounds)[/]")

        self.update("\n".join(lines))


# ── Score History Chart ─────────────────────────────────────────


class ScoreHistoryChart(PlotextPlot):
    """Line chart of cumulative scores over rounds for both players."""

    DEFAULT_CSS = """
    ScoreHistoryChart {
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
        self._p1_scores: list[int] = []
        self._p2_scores: list[int] = []
        self._p1_name = "You"
        self._p2_name = "Opponent"

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
        self.plt.title("Cumulative Score Over Rounds")
        self.plt.xlabel("Round")
        self.plt.ylabel("Total Score")
        self.plt.ylim(0, 10)
        self.plt.xlim(0, 20)
        self.refresh()

    def set_data(
        self,
        p1_cumulative: list[int],
        p2_cumulative: list[int],
        p1_name: str,
        p2_name: str,
    ) -> None:
        self._p1_scores = p1_cumulative
        self._p2_scores = p2_cumulative
        self._p1_name = p1_name
        self._p2_name = p2_name
        self._draw()

    def _draw(self) -> None:
        self.plt.clear_figure()
        self._setup_theme()

        if not self._p1_scores:
            self._draw_empty()
            return

        n = len(self._p1_scores)
        x = list(range(1, n + 1))

        self.plt.title("Cumulative Score Over Rounds")
        self.plt.xlabel("Round")
        self.plt.ylabel("Total Score")

        max_score = max(max(self._p1_scores or [0]), max(self._p2_scores or [0]))
        self.plt.ylim(0, max(10, max_score + 5))
        self.plt.xlim(0, max(20, n))

        self.plt.plot(x, self._p1_scores, label=self._p1_name, color=(56, 189, 248))
        self.plt.plot(x, self._p2_scores, label=self._p2_name, color=(251, 113, 133))

        self.refresh()

    def clear_chart(self) -> None:
        self._p1_scores = []
        self._p2_scores = []
        self._draw_empty()


# ── Tournament Results Table ────────────────────────────────────


class TournamentTable(Static):
    """Simple text table of tournament average scores."""

    DEFAULT_CSS = """
    TournamentTable {
        width: 100%;
        height: auto;
        min-height: 10;
        background: #1a2332;
        border: round #2a3a4f;
        padding: 1 2;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__("", **kwargs)

    def set_results(self, result: TournamentResult) -> None:
        lines: list[str] = []
        lines.append("[bold #00e5ff]Tournament Results[/] (avg score per round)")
        lines.append("")

        # Sort by score descending
        ranked = sorted(result.scores.items(), key=lambda x: x[1], reverse=True)

        for rank, (name, score) in enumerate(ranked, 1):
            medal = "🥇" if rank == 1 else ("🥈" if rank == 2 else ("🥉" if rank == 3 else "  "))
            color = "#76ff03" if rank == 1 else ("#ffab00" if rank <= 3 else "#e2e8f0")
            lines.append(f"  {medal}  [{color}]{name:<28}[/]  [bold]{score:.2f}[/]")

        lines.append("")
        lines.append(f"[dim]Each pair played {result.rounds_per_match} rounds[/]")

        self.update("\n".join(lines))

    def clear(self) -> None:
        self.update("[dim]Run a tournament to see results...[/]")


# ── Evolution Chart ─────────────────────────────────────────────


class EvolutionChart(PlotextPlot):
    """Stacked area / lines showing strategy population proportions over generations."""

    DEFAULT_CSS = """
    EvolutionChart {
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
        self._history: list[list[float]] = []
        self._strategies: list[str] = []

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
        self.plt.title("Strategy Evolution (Replicator Dynamics)")
        self.plt.xlabel("Generation")
        self.plt.ylabel("Population %")
        self.plt.ylim(0, 1.05)
        self.plt.xlim(0, 20)
        self.refresh()

    def set_data(self, strategies: list[str], history: list[list[float]]) -> None:
        self._strategies = strategies
        self._history = history
        self._draw()

    def _draw(self) -> None:
        self.plt.clear_figure()
        self._setup_theme()

        if not self._history:
            self._draw_empty()
            return

        gens = list(range(len(self._history)))
        self.plt.title("Strategy Population Over Generations")
        self.plt.xlabel("Generation")
        self.plt.ylabel("Proportion")

        colors = [
            (56, 189, 248), (251, 113, 133), (251, 191, 36),
            (74, 222, 128), (248, 113, 113), (167, 139, 250),
        ]

        for i, name in enumerate(self._strategies):
            y = [row[i] for row in self._history]
            self.plt.plot(gens, y, label=name[:20], color=colors[i % len(colors)])

        self.plt.ylim(0, 1.05)
        self.refresh()

    def clear_chart(self) -> None:
        self._history = []
        self._strategies = []
        self._draw_empty()
