"""Screen — main Textual Screen for The Gambler's Ruin module.

Live random walk + exact ruin probability curves + batch simulation.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Static

from gametheorist.theme import (
    AMBER,
    NEON_CYAN,
    NEON_MAGENTA,
    BG_DARK,
    BG_PANEL,
    TEXT_PRIMARY,
    TEXT_DIM,
)
from gametheorist.widgets.lesson_panel import LessonPanel
from gametheorist.widgets.stats_bar import StatsBar

from gametheorist.modules.gambler.engine import (
    simulate_walk,
    batch_ruin_stats,
    ruin_probability_sweep,
    simulate_ruin_rate_sweep,
    exact_ruin_probability,
    exact_expected_duration,
    capital_bar_data,
)
from gametheorist.modules.gambler.widgets import (
    WealthBar,
    WalkPathChart,
    RuinCurveChart,
    RuinStatsPanel,
)


# ── Lesson Content ──────────────────────────────────────────────

LESSON_FAIR_GAME = """\
## 💸 The Gambler's Ruin — Fair Games Are Brutal

You start with **i** dollars. The house (or opponent) has **N - i**.

Each round you win $1 with probability **p**, lose $1 with **1-p**.

You play until one of you is broke.

### The Shocking Truth (when p = 0.5)

Even when the game is perfectly **fair**, your probability of eventual ruin is:

**P(ruin) = (N - i) / N**

If the house has 10× your money, you have only a **9%** chance of breaking them before they break you.

> This is one of the most important results in probability.
> "Fair" does **not** mean "you have a good chance of winning."

The longer you play, the more certain ruin becomes when the other side has more capital.
"""

LESSON_BIAS = """\
## 📉 When p ≠ 0.5 — The House Edge Changes Everything

A tiny bias against you (p = 0.49 instead of 0.5) makes the ruin probability dramatically worse.

The exact formula becomes:

P(ruin) = (r^i - r^N) / (1 - r^N)   where r = (1-p)/p

When r > 1 (house has the edge), this approaches 1 extremely fast as N grows.

### Expected Duration

Even in a fair game, the **expected number of steps** until someone goes broke is:

E[steps] = i × (N - i)

With i=50, N=100 → you expect **2,500** flips before the game ends.

Real casinos have effectively **N = ∞**. Against infinite capital, a fair game still leads to almost certain ruin for the player.
"""

LESSON_VARIANCE = """\
## 🎲 Variance + Absorption

This module is the perfect sequel to the Coin module.

- In the Coin lab you saw the **Law of Large Numbers**: averages converge.
- Here you see what happens when you have **absorbing barriers** (0 and N).

The gambler's fortune performs a random walk. With no barriers it would wander forever (recurrent). With barriers at 0 and N it is **guaranteed** to be absorbed eventually.

This is why professional gamblers and insurance companies care so much about **capital reserves**. One bad streak can ruin you even if the odds are in your favor long-term.
"""


class GamblerScreen(Screen):
    """Interactive Gambler's Ruin lab."""

    BINDINGS = [
        Binding("escape", "go_back", "Back"),
        Binding("space", "step", "Step 1", show=True),
        Binding("r", "reset", "Reset", show=True),
        Binding("s", "run_batch", "Simulate 5k", show=True),
        Binding("l", "show_lesson", "Lesson", show=True),
    ]

    DEFAULT_CSS = """
    GamblerScreen {
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
        width: 38%;
        min-width: 34;
        height: 100%;
        padding: 1 2;
        layout: vertical;
    }

    #right-panel {
        width: 62%;
        height: 100%;
        background: #111827;
        border-left: solid #2a3a4f;
        padding: 1 2;
        layout: vertical;
    }

    #param-row {
        height: auto;
        align: center middle;
        margin: 1 0;
    }

    .param-label {
        width: auto;
        padding-right: 1;
        color: #e2e8f0;
    }

    .param-input {
        width: 10;
    }

    #control-buttons {
        height: 3;
        align: center middle;
        margin: 1 0;
    }

    .control-btn {
        min-width: 11;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        # Parameters
        self._i: int = 25          # starting capital
        self._N: int = 50          # total capital
        self._p: float = 0.5       # prob of +1 for the gambler

        # Live state
        self._current: int = self._i
        self._live_positions: list[int] = [self._i]
        self._live_walks: list[list[int]] = [[self._i]]

        # Last batch result
        self._last_stats: "BatchRuinStats | None" = None  # type: ignore[name-defined]

    # ── compose ─────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        yield Static(
            "💸 [bold #ffab00]THE GAMBLER'S RUIN[/]  —  Variance • Absorption • Fair Games Are Brutal",
            id="title-bar",
        )

        with Horizontal(id="main-area"):
            # Left: controls + wealth
            with Vertical(id="left-panel"):
                yield WealthBar(id="wealth-bar")

                with Horizontal(id="param-row"):
                    yield Static("[bold]Your capital (i):[/]", classes="param-label")
                    yield Input(value="25", id="input-i", classes="param-input", max_length=4)
                    yield Static("   [bold]Total (N):[/]", classes="param-label")
                    yield Input(value="50", id="input-n", classes="param-input", max_length=4)

                with Horizontal(id="param-row"):
                    yield Static("[bold]p (you win):[/]", classes="param-label")
                    yield Input(value="0.50", id="input-p", classes="param-input", max_length=5)
                    yield Button("Set", id="btn-set-params", variant="default")

                with Horizontal(id="control-buttons"):
                    yield Button("Step 1", id="btn-step-1", variant="primary", classes="control-btn")
                    yield Button("Step 10", id="btn-step-10", classes="control-btn")
                    yield Button("Step 100", id="btn-step-100", classes="control-btn")
                    yield Button("Reset", id="btn-reset", variant="warning", classes="control-btn")

                yield Static(
                    "[dim]⎵ space = step  •  r = reset  •  s = 5k sim  •  l = lesson[/]",
                    id="hint",
                )

            # Right: charts + stats
            with Vertical(id="right-panel"):
                yield WalkPathChart(id="walk-chart")
                yield RuinCurveChart(id="ruin-chart")
                yield RuinStatsPanel(id="stats-panel")

        yield LessonPanel(id="lesson-panel")
        yield StatsBar(id="stats-bar")
        yield Footer()

    # ── lifecycle ───────────────────────────────────────────────

    def on_mount(self) -> None:
        self._update_wealth_and_live()
        self._update_stats_panel_live()
        self._update_stats_bar()

    # ── actions ─────────────────────────────────────────────────

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def action_step(self) -> None:
        self._do_steps(1)

    def action_reset(self) -> None:
        self._reset_live()

    def action_run_batch(self) -> None:
        self._run_batch_simulation()

    def action_show_lesson(self) -> None:
        panel = self.query_one("#lesson-panel", LessonPanel)
        if panel.is_visible:
            panel.hide()
        else:
            # Show the most relevant lesson
            if self._p != 0.5:
                panel.show(content=LESSON_BIAS, title="📉 Bias & The House Edge")
            else:
                panel.show(content=LESSON_FAIR_GAME, title="💸 Fair Games Are Brutal")

    # ── button handlers ─────────────────────────────────────────

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "btn-step-1":
            self._do_steps(1)
        elif bid == "btn-step-10":
            self._do_steps(10)
        elif bid == "btn-step-100":
            self._do_steps(100)
        elif bid == "btn-reset":
            self._reset_live()
        elif bid == "btn-set-params":
            self._apply_parameters()

    # ── input handling ──────────────────────────────────────────

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id in ("input-i", "input-n", "input-p"):
            self._apply_parameters()

    # ── core logic ──────────────────────────────────────────────

    def _apply_parameters(self) -> None:
        """Read inputs and update i / N / p (with validation)."""
        try:
            new_i = int(self.query_one("#input-i", Input).value.strip())
            new_N = int(self.query_one("#input-n", Input).value.strip())
            new_p = float(self.query_one("#input-p", Input).value.strip())
        except ValueError:
            self._revert_inputs()
            return

        if not (1 <= new_i < new_N <= 500):
            self._revert_inputs()
            return
        if not (0.0 < new_p < 1.0):
            self._revert_inputs()
            return

        self._i = new_i
        self._N = new_N
        self._p = new_p
        self._reset_live()

    def _revert_inputs(self) -> None:
        self.query_one("#input-i", Input).value = str(self._i)
        self.query_one("#input-n", Input).value = str(self._N)
        self.query_one("#input-p", Input).value = f"{self._p:.2f}"

    def _update_wealth_and_live(self) -> None:
        """Refresh wealth bar and live walk chart."""
        wealth = self.query_one("#wealth-bar", WealthBar)
        wealth.update_capital(self._current, self._N)

        chart = self.query_one("#walk-chart", WalkPathChart)
        chart.set_walks(self._live_walks, labels=["Live Walk"])

    def _update_stats_panel_live(self) -> None:
        panel = self.query_one("#stats-panel", RuinStatsPanel)
        panel.update_live(self._current, self._N, self._p)

    def _update_stats_bar(self) -> None:
        bar = self.query_one("#stats-bar", StatsBar)
        ruin_p = exact_ruin_probability(self._current, self._N, self._p)
        bar.set_stats(
            capital=f"{self._current}/{self._N}",
            p=f"{self._p:.2f}",
            exact_ruin=f"{ruin_p:.2%}",
            module="Gambler",
        )

    def _do_steps(self, count: int) -> None:
        """Advance the live walk by up to `count` steps (stops at absorption)."""
        if self._current == 0 or self._current == self._N:
            return  # already absorbed

        rng = None  # let engine create its own
        steps_taken = 0

        for _ in range(count):
            if self._current == 0 or self._current == self._N:
                break
            # Single step using the same logic as engine
            import random
            if random.random() < self._p:
                self._current += 1
            else:
                self._current -= 1

            self._live_positions.append(self._current)
            steps_taken += 1

        # Keep only the latest walk for the chart (or we could support multiple)
        self._live_walks = [self._live_positions[:]]

        self._update_wealth_and_live()
        self._update_stats_panel_live()
        self._update_stats_bar()

        # Auto-show lesson after first absorption in a while
        if self._current in (0, self._N) and steps_taken > 0:
            panel = self.query_one("#lesson-panel", LessonPanel)
            if not panel.is_visible:
                panel.show(LESSON_FAIR_GAME, title="💸 Absorption Reached")

    def _reset_live(self) -> None:
        """Reset the live walker back to starting capital."""
        self._current = self._i
        self._live_positions = [self._i]
        self._live_walks = [[self._i]]

        self.query_one("#wealth-bar", WealthBar).update_capital(self._current, self._N)
        self.query_one("#walk-chart", WalkPathChart).set_walks(self._live_walks, ["Live Walk"])
        self._update_stats_panel_live()
        self._update_stats_bar()

        # Hide lesson if visible
        panel = self.query_one("#lesson-panel", LessonPanel)
        if panel.is_visible:
            panel.hide()

    def _run_batch_simulation(self) -> None:
        """Run 5,000 trials and update the ruin curve + stats."""
        n_trials = 5000

        # Exact curve
        starts, exact = ruin_probability_sweep(self._N, self._p)

        # Simulated rates for the same starts
        _, sim_rates = simulate_ruin_rate_sweep(self._N, self._p, n_trials=n_trials, start_values=starts)

        # Update ruin curve chart
        curve = self.query_one("#ruin-chart", RuinCurveChart)
        curve.set_exact(starts, exact, self._N, self._p)
        curve.set_simulated(sim_rates)

        # Batch stats at current starting capital
        stats = batch_ruin_stats(n_trials, self._i, self._N, self._p)
        self._last_stats = stats

        panel = self.query_one("#stats-panel", RuinStatsPanel)
        panel.update_batch(stats)

        # Also update stats bar with the simulated ruin rate
        bar = self.query_one("#stats-bar", StatsBar)
        bar.set_stats(
            capital=f"{self._i}/{self._N}",
            p=f"{self._p:.2f}",
            sim_ruin=f"{stats.ruin_rate:.2%}",
            module="Gambler",
        )

        # Show the bias lesson if p != 0.5
        lesson_panel = self.query_one("#lesson-panel", LessonPanel)
        if not lesson_panel.is_visible:
            if abs(self._p - 0.5) > 0.01:
                lesson_panel.show(LESSON_BIAS, title="📉 The Power of a Small Edge")
            else:
                lesson_panel.show(LESSON_FAIR_GAME, title="💸 Fair Game, Brutal Outcome")
