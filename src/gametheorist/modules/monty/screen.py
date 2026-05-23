"""Screen — main Textual Screen for the Monty Hall Arena module.

Assembles DoorRow, ResultsChart, BayesPanel, and shared widgets
into an interactive screen with classic and 100-door variants.
"""

from __future__ import annotations

import random
from typing import Literal

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Static

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

from gametheorist.modules.monty.engine import (
    MontyHallGame,
    GameState,
    simulate_batch,
)
from gametheorist.modules.monty.widgets import (
    DoorRow,
    ResultsChart,
    BayesPanel,
)

# ── Lesson Content ──────────────────────────────────────────────

LESSON_CONDITIONAL_PROB = """\
## 🚪 The Monty Hall Paradox & Conditional Probability

Why does switching double your chances of winning in a 3-door game?

### The Intuition Trap
When Monty opens one door to show a goat, two doors remain closed. Your gut says: *"It's 50/50. Switching doesn't matter."*
**This is wrong.** It would only be 50/50 if Monty had chosen which door to open completely at random (which might have revealed the car).

### The Math
1. **Initial Choice:** When you pick your first door, you have a **1/3** chance of choosing the car, and a **2/3** chance of choosing a goat.
2. **Monty's Action:** Monty *always* opens a door containing a goat. He acts like a filter.
3. **If you picked a goat first (2/3 chance):** The car *must* be behind the other closed door. Monty's hands were tied; he had to open the remaining goat. Switching wins 100% of the time in this scenario!
4. **If you picked the car first (1/3 chance):** Switching loses.

So:
- **Staying** wins with probability **1/3** (your initial choice).
- **Switching** wins with probability **2/3** (the probability you picked a goat initially).

> **Bayes' Theorem:** The opening of a door by Monty provides *new information*, changing the conditional probabilities of the unopened doors.
"""

LESSON_100_DOORS = """\
## 🚪 100 Doors: Making It Obvious

If the 3-door explanation feels slippery, scale the problem up to **100 doors**.

### The Scenario
1. You choose **1 door** out of 100.
   - Probability you got the car: **1/100 (1%)**
   - Probability the car is behind one of the other 99 doors: **99/100 (99%)**
2. Monty (who knows where the car is) opens **98 doors** to reveal 98 goats, leaving only:
   - Your door
   - One other specific door
3. Monty asks: *"Do you want to switch?"*

### The Choice
Do you think your initial 1-in-100 guess was correct, or do you think the car is behind the door Monty deliberately avoided opening?
The other door has concentrated all **99%** of the remaining probability!

> **Takeaway:** Monty did not just randomly choose a door. He actively scanned 99 doors, eliminated all the goats, and left the car (if it was there). Switching wins **99%** of the time.
"""

LESSON_IGNORANT_MONTY = """\
## 🐐 Ignorant Monty (The \"Monty Fall\" Problem)

What if Monty doesn't know where the car is, and just opens a door at random?

### The Rules Change
1. You pick Door 1.
2. Monty randomly picks Door 3. By pure luck, it contains a goat.
3. Should you switch?

### The Math
Since Monty chose randomly, there was a **1/3** chance he would reveal the car and end the game. The fact that he *happened* to reveal a goat changes the sample space.

Let's list the equally likely outcomes:
- Car is behind Door 1: Monty opens Door 2 (goat) or Door 3 (goat).
- Car is behind Door 2: Monty opens Door 3 (goat) - *if he opened Door 2, game would end.*
- Car is behind Door 3: Monty opens Door 2 (goat) - *if he opened Door 3, game would end.*

Since we know Monty opened a door that *contained a goat*, the remaining possibilities are symmetric. Your door and the other closed door now both have a **50/50** chance!

> **Key Lesson:** The intent and knowledge of the agent revealing information is critical! If the information was revealed by a blind, random process, switching provides **no advantage** (50% win rate).
"""


class MontyScreen(Screen):
    """Interactive Monty Hall screen."""

    BINDINGS = [
        Binding("escape", "go_back", "Back"),
        Binding("1", "press_door(0)", "Door 1", show=False),
        Binding("2", "press_door(1)", "Door 2", show=False),
        Binding("3", "press_door(2)", "Door 3", show=False),
        Binding("s", "do_switch", "Switch", show=False),
        Binding("d", "do_stay", "Stay", show=False),
        Binding("r", "reset_game", "Reset", show=True),
        Binding("m", "run_simulation", "Simulate", show=True),
        Binding("l", "show_lesson", "Lesson", show=True),
    ]

    DEFAULT_CSS = """
    MontyScreen {
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
        width: 65%;
        height: 100%;
        padding: 1 2;
        layout: vertical;
    }

    #right-panel {
        width: 35%;
        height: 100%;
        background: #111827;
        border-left: solid #2a3a4f;
        padding: 1;
        layout: vertical;
    }

    #game-status {
        height: auto;
        content-align: center middle;
        text-align: center;
        padding: 1;
        background: #1a2332;
        border: round #2a3a4f;
        margin: 1 0;
        color: #e2e8f0;
        text-style: bold;
    }

    #control-row {
        height: 3;
        align: center middle;
        margin-top: 1;
    }

    #config-row {
        height: 3;
        align: center middle;
        border-bottom: solid #1a2332;
        margin-bottom: 1;
    }

    #sidebar-stats {
        height: auto;
        background: #1a2332;
        border: round #2a3a4f;
        padding: 1;
        margin-top: 1;
        color: #e2e8f0;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.game = MontyHallGame(n_doors=3, monty_knows=True)
        self.switch_wins = 0
        self.switch_losses = 0
        self.stay_wins = 0
        self.stay_losses = 0
        self.game_count = 0

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static(
            "🚪 [bold #00e5ff]THE MONTY HALL ARENA[/] — Probability & Intuition-Breaking",
            id="title-bar",
        )
        with Horizontal(id="main-area"):
            with Vertical(id="left-panel"):
                # Config options
                with Horizontal(id="config-row"):
                    yield Button("Classic (3 doors)", id="btn-opt-3", variant="primary")
                    yield Button("100 Doors", id="btn-opt-100")
                    yield Button("Ignorant Monty", id="btn-opt-ignorant")

                yield DoorRow(id="door-row")

                yield Static("Pick a door to start the game!", id="game-status")

                with Horizontal(id="control-row"):
                    yield Button("Switch", id="btn-switch", variant="success", disabled=True)
                    yield Button("Stay", id="btn-stay", variant="warning", disabled=True)
                    yield Button("Next Round", id="btn-next", variant="primary", disabled=True)

                yield BayesPanel(id="bayes-panel")

            with Vertical(id="right-panel"):
                yield ResultsChart(id="results-chart")
                with ScrollableContainer(id="sidebar-stats"):
                    yield Static(self._get_stats_text(), id="stats-text")

        yield LessonPanel(id="lesson-panel")
        yield StatsBar(id="stats-bar")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#door-row", DoorRow).setup_doors(3)
        self.reset_game()

    def reset_game(self) -> None:
        """Reset the current interactive game."""
        self.game.setup()
        self.query_one("#bayes-panel", BayesPanel).hide_panel()
        self.query_one("#btn-switch").disabled = True
        self.query_one("#btn-stay").disabled = True
        self.query_one("#btn-next").disabled = True

        # Redraw closed doors
        door_row = self.query_one("#door-row", DoorRow)
        for door in door_row.doors:
            door.set_state("closed")

        self._update_status("[bold #00e5ff]Pick a door by clicking it or pressing keys 1-3.[/]")
        self._update_stats_displays()

    def _update_status(self, text: str) -> None:
        self.query_one("#game-status", Static).update(text)

    def _get_stats_text(self) -> str:
        s_total = self.switch_wins + self.switch_losses
        st_total = self.stay_wins + self.stay_losses
        s_rate = (self.switch_wins / s_total * 100) if s_total else 0.0
        st_rate = (self.stay_wins / st_total * 100) if st_total else 0.0

        monty_mode = "Smart (Knows)" if self.game.monty_knows else "Ignorant (Random)"

        return (
            f"[bold #00e5ff]=== Session Stats ===[/]\n"
            f"Doors: [bold]{self.game.n_doors}[/]\n"
            f"Monty: [bold]{monty_mode}[/]\n"
            f"Total Rounds: [bold]{self.game_count}[/]\n\n"
            f"[bold #ffab00]Switch Strategy:[/]\n"
            f"  Wins: {self.switch_wins}  │  Losses: {self.switch_losses}\n"
            f"  Win Rate: [bold #76ff03]{s_rate:.1f}%[/]\n\n"
            f"[bold #ff00e5]Stay Strategy:[/]\n"
            f"  Wins: {self.stay_wins}  │  Losses: {self.stay_losses}\n"
            f"  Win Rate: [bold #76ff03]{st_rate:.1f}%[/]"
        )

    def _update_stats_displays(self) -> None:
        self.query_one("#stats-text", Static).update(self._get_stats_text())
        s_total = self.switch_wins + self.switch_losses
        st_total = self.stay_wins + self.stay_losses
        s_rate = (self.switch_wins / s_total) if s_total else 0.0
        st_rate = (self.stay_wins / st_total) if st_total else 0.0

        chart = self.query_one("#results-chart", ResultsChart)
        if s_total > 0 or st_total > 0:
            chart.update_rates(s_rate, st_rate)

        # Update stats bar
        self.query_one("#stats-bar", StatsBar).set_stats(
            rounds=self.game_count,
            switch_wins=self.switch_wins,
            stay_wins=self.stay_wins,
        )

    def action_press_door(self, idx: int) -> None:
        """Handle choosing a door."""
        if self.game.state != GameState.SETUP:
            return
        if idx >= self.game.n_doors:
            return

        self.game.player_pick(idx)
        door_row = self.query_one("#door-row", DoorRow)
        door_row.get_door(idx).set_state("selected")

        # Monty opens door(s)
        opened = self.game.monty_opens()

        # Update opened doors in UI
        for d in opened:
            if d == self.game.car_door:
                door_row.get_door(d).set_state("car")
            else:
                door_row.get_door(d).set_state("goat")

        # Show Bayes panel
        bayes = self.query_one("#bayes-panel", BayesPanel)
        bayes.show_update(self.game.n_doors, idx, opened)

        if self.game.car_revealed_by_monty:
            self._update_status(
                "[bold #ff6b6b]Oops! Monty opened a door revealing the CAR![/]\n"
                "This game is over. Ignorant Monty ruined it."
            )
            # Finish round immediately
            self.game.switch() # dummy choice
            res = self.game.reveal()
            self.stay_losses += 1  # count as loss
            self.game_count += 1
            self.query_one("#btn-next").disabled = False
            self._update_stats_displays()
        else:
            self._update_status(
                f"[bold #ffab00]Monty opened door(s) to reveal goat(s).[/] "
                f"Should you [bold #00e5ff]Switch[/] or [bold #ff00e5]Stay[/]?"
            )
            self.query_one("#btn-switch").disabled = False
            self.query_one("#btn-stay").disabled = False

    def on_click(self, event: any) -> None:
        """Handle clicks on door widgets."""
        # Find which door was clicked, if any
        if self.game.state != GameState.SETUP:
            return
        for idx, door in enumerate(self.query_one("#door-row", DoorRow).doors):
            if event.screen_x >= door.region.x and event.screen_x < door.region.x + door.region.width:
                if event.screen_y >= door.region.y and event.screen_y < door.region.y + door.region.height:
                    self.action_press_door(idx)
                    break

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id == "btn-opt-3":
            self._change_config(3, True)
            self._toggle_active_button("btn-opt-3")
        elif btn_id == "btn-opt-100":
            self._change_config(100, True)
            self._toggle_active_button("btn-opt-100")
        elif btn_id == "btn-opt-ignorant":
            self._change_config(3, False)
            self._toggle_active_button("btn-opt-ignorant")
        elif btn_id == "btn-switch":
            self.action_do_switch()
        elif btn_id == "btn-stay":
            self.action_do_stay()
        elif btn_id == "btn-next":
            self.reset_game()

    def _toggle_active_button(self, active_id: str) -> None:
        for bid in ("btn-opt-3", "btn-opt-100", "btn-opt-ignorant"):
            btn = self.query_one(f"#{bid}", Button)
            if bid == active_id:
                btn.variant = "primary"
            else:
                btn.variant = "default"

    def _change_config(self, n_doors: int, monty_knows: bool) -> None:
        self.game = MontyHallGame(n_doors=n_doors, monty_knows=monty_knows)
        self.query_one("#door-row", DoorRow).setup_doors(n_doors)
        self.reset_game()

        # Trigger lesson after 100 doors or ignorant monty selected
        if n_doors == 100:
            self.query_one("#lesson-panel", LessonPanel).show(LESSON_100_DOORS)
        elif not monty_knows:
            self.query_one("#lesson-panel", LessonPanel).show(LESSON_IGNORANT_MONTY)

    def action_do_switch(self) -> None:
        """Execute switch action."""
        if self.game.state != GameState.MONTY_OPENED:
            return
        self.game.switch()
        self._complete_game()

    def action_do_stay(self) -> None:
        """Execute stay action."""
        if self.game.state != GameState.MONTY_OPENED:
            return
        self.game.stay()
        self._complete_game()

    def _complete_game(self) -> None:
        res = self.game.reveal()
        door_row = self.query_one("#door-row", DoorRow)

        # Show car and goat everywhere
        for i in range(self.game.n_doors):
            if i == self.game.car_door:
                door_row.get_door(i).set_state("car")
            elif i not in res.monty_opened:
                door_row.get_door(i).set_state("goat")

        self.game_count += 1

        if res.won:
            if res.strategy == "switch":
                self.switch_wins += 1
            else:
                self.stay_wins += 1
            self._update_status("🎉 [bold #76ff03]YOU WON THE CAR![/] Absolutely brilliant!")
        else:
            if res.strategy == "switch":
                self.switch_losses += 1
            else:
                self.stay_losses += 1
            self._update_status("😭 [bold #ff6b6b]YOU GOT A GOAT.[/] Better luck next time!")

        self.query_one("#btn-switch").disabled = True
        self.query_one("#btn-stay").disabled = True
        self.query_one("#btn-next").disabled = False
        self._update_stats_displays()

        # Trigger automatic lessons
        if self.game_count == 5:
            self.query_one("#lesson-panel", LessonPanel).show(LESSON_CONDITIONAL_PROB)

    def action_run_simulation(self) -> None:
        """Run batch simulation of 10,000 games."""
        s_res = simulate_batch(10000, self.game.n_doors, "switch", self.game.monty_knows)
        st_res = simulate_batch(10000, self.game.n_doors, "stay", self.game.monty_knows)

        self.switch_wins += s_res.wins
        self.switch_losses += s_res.losses
        self.stay_wins += st_res.wins
        self.stay_losses += st_res.losses
        self.game_count += 20000

        self._update_status(
            f"Simulated [bold]10,000[/] rounds of both strategies!\n"
            f"Switch win-rate: [bold #00e5ff]{s_res.win_rate:.1%}[/]  │  "
            f"Stay win-rate: [bold #ff00e5]{st_res.win_rate:.1%}[/]"
        )
        self._update_stats_displays()

    def action_show_lesson(self) -> None:
        """Toggle or show lesson panel."""
        panel = self.query_one("#lesson-panel", LessonPanel)
        if panel.is_visible:
            panel.hide()
        else:
            if self.game.n_doors == 100:
                panel.show(LESSON_100_DOORS)
            elif not self.game.monty_knows:
                panel.show(LESSON_IGNORANT_MONTY)
            else:
                panel.show(LESSON_CONDITIONAL_PROB)

    def action_go_back(self) -> None:
        self.app.pop_screen()
