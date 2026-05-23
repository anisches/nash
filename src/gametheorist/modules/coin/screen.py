"""Screen — main Textual Screen for the Coin module.

Assembles CoinWidget, ConvergenceChart, StatsPanel, and shared widgets
into a single interactive screen with flip controls.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Static

from gametheorist.theme import (
    NEON_CYAN,
    NEON_MAGENTA,
    AMBER,
    BG_DARK,
    BG_PANEL,
    BG_CARD,
    TEXT_PRIMARY,
    TEXT_DIM,
)
from gametheorist.widgets.lesson_panel import LessonPanel
from gametheorist.widgets.stats_bar import StatsBar

from gametheorist.modules.coin.engine import (
    BiasedCoin,
    run_trial_incremental,
    z_test_fair,
)
from gametheorist.modules.coin.widgets import (
    CoinWidget,
    ConvergenceChart,
    StatsPanel,
)


# ── Lesson content ──────────────────────────────────────────────

LESSON_LLN = """\
## 📐 Law of Large Numbers

As you flip the coin more times, the **sample proportion** of heads
converges to the coin's **true probability** (its bias).

- After 10 flips the proportion is noisy — it could be anywhere.
- After 100 flips it starts clustering around the true value.
- After 1 000+ flips it's almost locked on.

> **Key idea:** randomness is unpredictable in the *short run*
> but highly predictable in the *long run*.

This is the **Law of Large Numbers** — the foundation of all
statistical estimation.  Insurance, casinos, polling — they all
rely on this law to turn randomness into certainty.

### Why it matters
If you're trying to figure out whether a coin is fair, you *need*
enough data.  A handful of flips tells you almost nothing.
"""

LESSON_ZTEST = """\
## 🧪 Hypothesis Testing & Z-Test

You just saw the z-test **reject the null hypothesis** that the coin is fair!

### How it works
1. **H₀ (null hypothesis):** The coin is fair (p = 0.5).
2. We compute a **z-statistic** measuring how far our observed proportion
   is from 0.5, in units of standard error.
3. The **p-value** tells us the probability of seeing data this extreme
   *if* the coin really were fair.
4. If p < 0.05 (our significance level α), we **reject H₀**.

### The 95% Confidence Interval
The interval [lower, upper] means: *"We're 95% confident the true
proportion of heads falls in this range."*  If this interval doesn't
contain 0.5, we reject fairness.

### Type I & Type II Errors
- **Type I (false positive):** Rejecting H₀ when the coin IS fair.
  This happens ~5% of the time at α = 0.05.
- **Type II (false negative):** Failing to reject H₀ when the coin
  IS biased.  More data = less chance of this error.

> **Takeaway:** Statistical tests don't give *certainty* — they
> quantify *evidence*.  The p-value is NOT the probability
> that the coin is fair.
"""


# ── Screen ──────────────────────────────────────────────────────

class CoinScreen(Screen):
    """Interactive biased-coin experiment screen."""

    BINDINGS = [
        Binding("escape", "go_back", "Back"),
        Binding("space", "flip_one", "Flip 1", show=True),
        Binding("r", "reset", "Reset", show=True),
        Binding("l", "show_lesson", "Lesson", show=True),
    ]

    DEFAULT_CSS = """
    CoinScreen {
        background: #0a0e17;
    }

    /* ── Title bar ─────────────────────────────────────── */

    CoinScreen #title-bar {
        width: 100%;
        height: 3;
        background: #111827;
        content-align: center middle;
        text-align: center;
        padding: 1 0;
        border-bottom: solid #2a3a4f;
    }

    /* ── Main layout ───────────────────────────────────── */

    CoinScreen #main-area {
        width: 100%;
        height: 1fr;
        padding: 0;
    }

    /* ── Left panel ────────────────────────────────────── */

    CoinScreen #left-panel {
        width: 40%;
        min-width: 32;
        height: 100%;
        padding: 0 1;
    }

    CoinScreen #coin-container {
        width: 100%;
        height: auto;
        align: center middle;
        content-align: center middle;
    }

    CoinScreen #bias-row {
        width: 100%;
        height: auto;
        align: center middle;
        padding: 1 0 0 0;
    }

    CoinScreen #bias-label {
        width: auto;
        height: 3;
        padding: 1 1 0 0;
        color: #e2e8f0;
    }

    CoinScreen #bias-input {
        width: 12;
        height: 3;
    }

    CoinScreen #bias-set {
        width: auto;
        min-width: 8;
    }

    CoinScreen #flip-controls {
        width: 100%;
        height: auto;
        align: center middle;
        padding: 1 0;
    }

    CoinScreen .flip-btn {
        min-width: 10;
    }

    CoinScreen #flip-hint {
        width: 100%;
        height: auto;
        text-align: center;
        color: #64748b;
        padding: 0;
    }

    CoinScreen #sequence-display {
        width: 100%;
        height: auto;
        max-height: 6;
        padding: 1 1 0 1;
        color: #94a3b8;
        overflow-y: auto;
    }

    /* ── Right panel ───────────────────────────────────── */

    CoinScreen #right-panel {
        width: 60%;
        height: 100%;
        padding: 0 1;
    }

    CoinScreen #chart-area {
        width: 100%;
        height: 1fr;
        min-height: 14;
    }

    CoinScreen #stats-area {
        width: 100%;
        height: auto;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._bias: float = 0.6
        self._coin = BiasedCoin(bias=self._bias)
        # Cumulative state
        self._all_flips: list[str] = []
        self._running_avg: list[float] = []
        self._n_heads: int = 0
        self._n_tails: int = 0
        # Lesson triggers
        self._shown_lln_hint: bool = False
        self._shown_ztest_hint: bool = False

    # ── compose ─────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        yield Static(
            "[bold #00e5ff]🪙  THE COIN THAT LIES[/]"
            "  [#64748b]—  Probability Foundations[/]",
            id="title-bar",
        )

        with Horizontal(id="main-area"):
            # Left: coin + controls
            with Vertical(id="left-panel"):
                yield CoinWidget(id="coin-widget")
                with Horizontal(id="bias-row"):
                    yield Static("[bold]Bias:[/]", id="bias-label")
                    yield Input(
                        value="0.6",
                        placeholder="0.0–1.0",
                        id="bias-input",
                        max_length=4,
                    )
                    yield Button("Set", id="bias-set", variant="default")
                with Horizontal(id="flip-controls"):
                    yield Button("Flip 1", id="flip-1", variant="primary", classes="flip-btn")
                    yield Button("×10", id="flip-10", variant="default", classes="flip-btn")
                    yield Button("×100", id="flip-100", variant="default", classes="flip-btn")
                    yield Button("×1K", id="flip-1000", variant="default", classes="flip-btn")
                    yield Button("Reset", id="reset-btn", variant="warning", classes="flip-btn")
                yield Static(
                    "[dim]⎵ space = flip 1  •  r = reset  •  l = lesson  •  esc = back[/]",
                    id="flip-hint",
                )
                yield Static("", id="sequence-display")

            # Right: chart + stats
            with Vertical(id="right-panel"):
                yield ConvergenceChart(id="chart-area")
                yield StatsPanel(id="stats-area")

        yield LessonPanel(id="lesson-panel")
        yield StatsBar(id="stats-bar")
        yield Footer()

    # ── lifecycle ───────────────────────────────────────────

    def on_mount(self) -> None:
        """Set initial stats bar text."""
        self._update_stats_bar()

    # ── actions ─────────────────────────────────────────────

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def action_flip_one(self) -> None:
        self._do_flip(1, animate=True)

    def action_reset(self) -> None:
        self._reset()

    def action_show_lesson(self) -> None:
        panel = self.query_one("#lesson-panel", LessonPanel)
        if panel.is_visible:
            panel.hide()
        else:
            # Show the most relevant lesson
            if self._shown_ztest_hint:
                panel.show(content=LESSON_ZTEST, title="💡 What You Just Learned")
            else:
                panel.show(content=LESSON_LLN, title="💡 What You Just Learned")

    # ── button handler ──────────────────────────────────────

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id == "flip-1":
            self._do_flip(1, animate=True)
        elif btn_id == "flip-10":
            self._do_flip(10, animate=False)
        elif btn_id == "flip-100":
            self._do_flip(100, animate=False)
        elif btn_id == "flip-1000":
            self._do_flip(1000, animate=False)
        elif btn_id == "reset-btn":
            self._reset()
        elif btn_id == "bias-set":
            self._apply_bias()

    # ── input handler ───────────────────────────────────────

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "bias-input":
            self._apply_bias()

    # ── core logic ──────────────────────────────────────────

    def _apply_bias(self) -> None:
        """Read the bias input and reconfigure the coin."""
        inp = self.query_one("#bias-input", Input)
        try:
            val = float(inp.value.strip())
            if not 0.0 <= val <= 1.0:
                raise ValueError
        except ValueError:
            inp.value = str(self._bias)
            return
        self._bias = val
        self._coin.bias = val
        self._update_stats_bar()

    def _do_flip(self, count: int, *, animate: bool) -> None:
        """Execute *count* flips, optionally animating the first one."""
        coin_widget = self.query_one("#coin-widget", CoinWidget)

        if coin_widget.is_animating:
            return  # don't interrupt an ongoing animation

        trial = run_trial_incremental(
            self._coin,
            count,
            prev_heads=self._n_heads,
            prev_total=self._n_heads + self._n_tails,
        )

        # Update cumulative state
        self._all_flips.extend(trial.flips)
        self._running_avg.extend(trial.running_avg)
        self._n_heads += trial.n_heads
        self._n_tails += trial.n_tails

        if animate and count == 1:
            # Show animation for single flip, update chart/stats on land
            coin_widget.start_flip(
                trial.flips[0],
                on_land=self._refresh_displays,
            )
        else:
            # Batch flip: skip animation, show last result immediately
            coin_widget.show_result(trial.flips[-1])
            self._refresh_displays()

    def _refresh_displays(self) -> None:
        """Update chart, stats panel, sequence display, stats bar, and check lessons."""
        # Chart
        chart = self.query_one("#chart-area", ConvergenceChart)
        chart.update_data(self._running_avg, self._bias)

        # Stats panel
        total = self._n_heads + self._n_tails
        z_result = z_test_fair(self._n_heads, total) if total >= 2 else None
        stats = self.query_one("#stats-area", StatsPanel)
        stats.update_stats(self._n_heads, self._n_tails, z_result)

        # Sequence display (last 60 flips)
        seq = self._all_flips[-60:]
        colored = []
        for f in seq:
            if f == "H":
                colored.append("[bold #00e5ff]H[/]")
            else:
                colored.append("[bold #ff00e5]T[/]")
        seq_text = "".join(colored)
        tail_note = f"  [dim]({total:,} total)[/]" if total > 60 else ""
        self.query_one("#sequence-display", Static).update(
            f"[bold]Recent:[/] {seq_text}{tail_note}"
        )

        # Stats bar
        self._update_stats_bar()

        # Lesson hints
        self._check_lesson_triggers(z_result)

    def _update_stats_bar(self) -> None:
        """Refresh the bottom stats bar."""
        bar = self.query_one("#stats-bar", StatsBar)
        total = self._n_heads + self._n_tails
        heads_pct = (self._n_heads / total * 100) if total else 0.0
        bar.set_stats(
            bias=f"{self._bias:.2f}",
            flips=total,
            heads=f"{heads_pct:.1f}%",
            module="Coin",
        )

    def _check_lesson_triggers(self, z_result=None) -> None:
        """Show lesson hints when milestones are reached."""
        total = self._n_heads + self._n_tails
        panel = self.query_one("#lesson-panel", LessonPanel)

        # After 30 flips: LLN hint
        if total >= 30 and not self._shown_lln_hint:
            self._shown_lln_hint = True
            panel.show(content=LESSON_LLN, title="💡 Law of Large Numbers")

        # After z-test rejects: inference hint
        if (
            z_result is not None
            and z_result.reject_null
            and not self._shown_ztest_hint
        ):
            self._shown_ztest_hint = True
            panel.show(content=LESSON_ZTEST, title="🧪 Statistical Inference")

    def _reset(self) -> None:
        """Clear all state and reset the UI."""
        self._all_flips.clear()
        self._running_avg.clear()
        self._n_heads = 0
        self._n_tails = 0
        self._shown_lln_hint = False
        self._shown_ztest_hint = False

        self.query_one("#coin-widget", CoinWidget).reset()
        self.query_one("#chart-area", ConvergenceChart).clear_chart()
        self.query_one("#stats-area", StatsPanel).clear_stats()
        self.query_one("#sequence-display", Static).update("")
        self._update_stats_bar()

        panel = self.query_one("#lesson-panel", LessonPanel)
        if panel.is_visible:
            panel.hide()
