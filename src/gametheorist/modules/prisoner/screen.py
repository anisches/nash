"""Screen — main Textual Screen for the Prisoner's Dilemma module.

Interactive single match + full tournament + evolutionary simulation.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Select, Static

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
)
from gametheorist.widgets.lesson_panel import LessonPanel
from gametheorist.widgets.stats_bar import StatsBar

from gametheorist.modules.prisoner.engine import (
    Strategy,
    BUILTIN_STRATEGIES,
    play_game,
    run_tournament,
    run_evolution,
    RoundResult,
    payoff_matrix_text,
)
from gametheorist.modules.prisoner.widgets import (
    PayoffMatrix,
    LiveMatchDisplay,
    ScoreHistoryChart,
    TournamentTable,
    EvolutionChart,
)


# ── Lesson Content ──────────────────────────────────────────────

LESSON_PD = """\
## ⛓️ The Prisoner's Dilemma — The Core of Game Theory

Two prisoners. Each can cooperate (stay silent) or defect (rat out the other).

**Payoffs (your score):**
- Both cooperate → 3 each (best joint outcome)
- You defect, they cooperate → **5** for you (temptation)
- You cooperate, they defect → **0** for you (sucker)
- Both defect → 1 each (mutual punishment)

Rational self-interest says **always defect**. But if both do, everyone is worse off.

This is the fundamental tension in game theory and real life (cartels, climate agreements, open source, etc.).
"""

LESSON_TFT = """\
## ♻️ Tit-for-Tat Wins Tournaments

In Robert Axelrod's famous computer tournaments, the simplest strategy won:

**Tit-for-Tat (TFT):**
1. Start by cooperating.
2. Then copy whatever the opponent did last round.

Why it works so well:
- **Nice**: It starts cooperative.
- **Retaliatory**: It punishes defection immediately.
- **Forgiving**: It returns to cooperation if the opponent does.
- **Clear**: Easy for others to understand.

Evolution and repeated interaction turn "selfish" games into cooperation engines.
"""

LESSON_EVOLUTION = """\
## 🧬 Evolution of Cooperation

When strategies compete over many generations (replicator dynamics), the population doesn't always collapse to "Always Defect".

- Tit-for-Tat and other conditional cooperators can invade and stabilize.
- A small cluster of cooperators can grow if they mostly meet each other.
- Noise and mutation matter — too much noise destroys cooperation.

This is why institutions, reputation, and repeated relationships are so important in real societies.
"""


class PrisonerScreen(Screen):
    """Interactive Prisoner's Dilemma lab."""

    BINDINGS = [
        Binding("escape", "go_back", "Back"),
        Binding("p", "play_round", "Play 1 Round", show=True),
        Binding("r", "reset_match", "Reset Match", show=True),
        Binding("t", "run_tournament", "Run Tournament", show=True),
        Binding("e", "run_evolution", "Run Evolution", show=True),
        Binding("l", "show_lesson", "Lesson", show=True),
    ]

    DEFAULT_CSS = """
    PrisonerScreen {
        background: #0a0e17;
    }

    #title-bar {
        width: 100%;
        height: 3;
        background: #111827;
        content-align: center middle;
        text-align: center;
        padding: 1 0;
        border-bottom: solid #2a3a4f;
    }

    #main-area {
        width: 100%;
        height: 1fr;
        layout: horizontal;
    }

    #left-panel {
        width: 42%;
        min-width: 36;
        height: 100%;
        padding: 1 2;
        layout: vertical;
    }

    #right-panel {
        width: 58%;
        height: 100%;
        background: #111827;
        border-left: solid #2a3a4f;
        padding: 1 2;
        layout: vertical;
    }

    #strategy-row {
        height: auto;
        margin: 1 0;
    }

    .strat-label {
        width: 14;
        color: #e2e8f0;
    }

    #match-controls {
        height: 3;
        align: center middle;
        margin: 1 0;
    }

    .mode-btn {
        min-width: 16;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        # Strategy selection
        self._p1_cls: type[Strategy] = BUILTIN_STRATEGIES["TFT"]
        self._p2_cls: type[Strategy] = BUILTIN_STRATEGIES["ALLD"]

        # Current match state
        self._p1_inst: Strategy | None = None
        self._p2_inst: Strategy | None = None
        self._p1_score: int = 0
        self._p2_score: int = 0
        self._history: list[RoundResult] = []

        # Cached results
        self._last_tournament: "TournamentResult | None" = None
        self._last_evolution: "EvolutionResult | None" = None

    # ── compose ─────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        yield Static(
            "⛓️ [bold #ff00e5]PRISONER'S DILEMMA TOURNAMENT[/]  —  Why Cooperation Is Hard",
            id="title-bar",
        )

        with Horizontal(id="main-area"):
            # Left: strategy choice + matrix + match
            with Vertical(id="left-panel"):
                yield Static("[bold #00e5ff]Choose Strategies[/]", classes="strat-label")

                with Horizontal(id="strategy-row"):
                    yield Static("You:", classes="strat-label")
                    yield Select(
                        options=[(name, key) for key, name in self._strategy_options()],
                        id="select-p1",
                        value="TFT",
                    )

                with Horizontal(id="strategy-row"):
                    yield Static("Opponent:", classes="strat-label")
                    yield Select(
                        options=[(name, key) for key, name in self._strategy_options()],
                        id="select-p2",
                        value="ALLD",
                    )

                yield Button("Apply Strategies", id="btn-apply", variant="primary")

                yield PayoffMatrix(id="payoff-matrix")

                yield LiveMatchDisplay(id="live-match")

                with Horizontal(id="match-controls"):
                    yield Button("Play 1 Round", id="btn-play-1", variant="success", classes="mode-btn")
                    yield Button("Play 50 Rounds", id="btn-play-50", classes="mode-btn")
                    yield Button("Reset Match", id="btn-reset-match", variant="warning", classes="mode-btn")

            # Right: charts + modes
            with Vertical(id="right-panel"):
                yield ScoreHistoryChart(id="score-chart")

                with Horizontal(id="mode-buttons"):
                    yield Button("Run Full Tournament", id="btn-tournament", variant="primary", classes="mode-btn")
                    yield Button("Run Evolution (50 gens)", id="btn-evolution", classes="mode-btn")

                yield TournamentTable(id="tournament-table")
                yield EvolutionChart(id="evolution-chart")

        yield LessonPanel(id="lesson-panel")
        yield StatsBar(id="stats-bar")
        yield Footer()

    def _strategy_options(self):
        """Return (label, key) pairs for the Select widgets."""
        return [(cls().name, key) for key, cls in BUILTIN_STRATEGIES.items()]

    # ── lifecycle ───────────────────────────────────────────────

    def on_mount(self) -> None:
        self._apply_strategies()
        self.query_one("#payoff-matrix", PayoffMatrix).update_matrix()
        self._update_stats_bar()

    # ── actions ─────────────────────────────────────────────────

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def action_play_round(self) -> None:
        self._play_rounds(1)

    def action_reset_match(self) -> None:
        self._reset_current_match()

    def action_run_tournament(self) -> None:
        self._run_full_tournament()

    def action_run_evolution(self) -> None:
        self._run_evolution_sim()

    def action_show_lesson(self) -> None:
        panel = self.query_one("#lesson-panel", LessonPanel)
        if panel.is_visible:
            panel.hide()
        else:
            panel.show(LESSON_PD, title="⛓️ The Core Dilemma")

    # ── button + select handlers ────────────────────────────────

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "btn-apply":
            self._apply_strategies()
        elif bid == "btn-play-1":
            self._play_rounds(1)
        elif bid == "btn-play-50":
            self._play_rounds(50)
        elif bid == "btn-reset-match":
            self._reset_current_match()
        elif bid == "btn-tournament":
            self._run_full_tournament()
        elif bid == "btn-evolution":
            self._run_evolution_sim()

    def on_select_changed(self, event: Select.Changed) -> None:
        # We don't auto-apply on change — user must click "Apply Strategies"
        pass

    # ── core logic ──────────────────────────────────────────────

    def _apply_strategies(self) -> None:
        """Create fresh strategy instances from the Select widgets."""
        p1_key = self.query_one("#select-p1", Select).value
        p2_key = self.query_one("#select-p2", Select).value

        self._p1_cls = BUILTIN_STRATEGIES[str(p1_key)]
        self._p2_cls = BUILTIN_STRATEGIES[str(p2_key)]

        self._reset_current_match()

        # Update live match widget names
        live = self.query_one("#live-match", LiveMatchDisplay)
        live.set_players(self._p1_cls().name, self._p2_cls().name)

    def _reset_current_match(self) -> None:
        """Start a fresh match with the current strategies."""
        self._p1_inst = self._p1_cls()
        self._p2_inst = self._p2_cls()
        self._p1_score = 0
        self._p2_score = 0
        self._history = []

        self.query_one("#live-match", LiveMatchDisplay).update_match(0, 0, [])
        self.query_one("#score-chart", ScoreHistoryChart).clear_chart()
        self.query_one("#payoff-matrix", PayoffMatrix).update_matrix(None)

        self._update_stats_bar()

    def _play_rounds(self, n: int) -> None:
        """Play n rounds using the current strategy instances."""
        if self._p1_inst is None or self._p2_inst is None:
            self._apply_strategies()

        p1_hist: list[str] = []
        p2_hist: list[str] = []

        for _ in range(n):
            m1 = self._p1_inst.next_move(p1_hist, p2_hist)
            m2 = self._p2_inst.next_move(p2_hist, p1_hist)

            from gametheorist.modules.prisoner.engine import play_round
            r = play_round(m1, m2)

            self._history.append(r)
            p1_hist.append(m1)
            p2_hist.append(m2)

            self._p1_score += r.player1_score
            self._p2_score += r.player2_score

        # Update UI
        live = self.query_one("#live-match", LiveMatchDisplay)
        live.update_match(self._p1_score, self._p2_score, self._history)

        # Build cumulative score lists for the chart
        p1_cum = []
        p2_cum = []
        s1 = s2 = 0
        for r in self._history:
            s1 += r.player1_score
            s2 += r.player2_score
            p1_cum.append(s1)
            p2_cum.append(s2)

        chart = self.query_one("#score-chart", ScoreHistoryChart)
        chart.set_data(
            p1_cum,
            p2_cum,
            self._p1_inst.name if self._p1_inst else "You",
            self._p2_inst.name if self._p2_inst else "Opponent",
        )

        self.query_one("#payoff-matrix", PayoffMatrix).update_matrix(self._history[-1])

        self._update_stats_bar()

        # Show lesson on first real cooperation or big score gap
        if len(self._history) >= 5 and not self.query_one("#lesson-panel", LessonPanel).is_visible:
            if any(r.player1_move == "C" and r.player2_move == "C" for r in self._history[-5:]):
                self.query_one("#lesson-panel", LessonPanel).show(LESSON_TFT, title="♻️ Tit-for-Tat in Action")

    def _run_full_tournament(self) -> None:
        """Run a round-robin tournament across all built-in strategies."""
        classes = list(BUILTIN_STRATEGIES.values())
        result = run_tournament(classes, rounds_per_match=120)

        self._last_tournament = result

        table = self.query_one("#tournament-table", TournamentTable)
        table.set_results(result)

        # Show the evolution lesson as a teaser
        panel = self.query_one("#lesson-panel", LessonPanel)
        if not panel.is_visible:
            panel.show(LESSON_EVOLUTION, title="🧬 From Tournaments to Evolution")

        self._update_stats_bar_tournament(result)

    def _run_evolution_sim(self) -> None:
        """Run replicator dynamics for 50 generations."""
        classes = list(BUILTIN_STRATEGIES.values())
        result = run_evolution(classes, generations=60, population_size=80, rounds_per_match=40)

        self._last_evolution = result

        chart = self.query_one("#evolution-chart", EvolutionChart)
        chart.set_data(result.strategies, result.population_history)

        panel = self.query_one("#lesson-panel", LessonPanel)
        if not panel.is_visible:
            panel.show(LESSON_EVOLUTION, title="🧬 Evolution of Cooperation")

    def _update_stats_bar(self) -> None:
        bar = self.query_one("#stats-bar", StatsBar)
        rounds = len(self._history)
        bar.set_stats(
            rounds=rounds,
            your_score=self._p1_score,
            opp_score=self._p2_score,
            module="Prisoner",
        )

    def _update_stats_bar_tournament(self, result: "TournamentResult") -> None:
        bar = self.query_one("#stats-bar", StatsBar)
        top = max(result.scores.items(), key=lambda x: x[1])
        bar.set_stats(
            tournament="done",
            winner=top[0][:20],
            top_score=f"{top[1]:.2f}",
            module="Prisoner",
        )
