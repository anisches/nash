"""Screen — main Textual Screen for the Birthday Paradox Lab.

Assembles RoomDisplay, CalendarHeatmap, ProbabilityChart, MathDerivation,
and shared widgets into an interactive experiment screen.
"""

from __future__ import annotations

import random
from typing import Literal

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Static, ContentSwitcher

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

from gametheorist.modules.birthday.engine import (
    RoomResult,
    simulate_room,
    monte_carlo_sweep_progressive,
    exact_sweep,
    generate_birthday,
    day_to_label,
)
from gametheorist.modules.birthday.widgets import (
    RoomDisplay,
    ProbabilityChart,
    CalendarHeatmap,
    MathDerivation,
)

# ── Lesson Content ──────────────────────────────────────────────

LESSON_BIRTHDAY_PARADOX = """\
## 🎂 The Birthday Paradox

Why does it take only **23 people** in a room to have a 50% chance of a shared birthday?

### The Gut Feeling Error
Our brain thinks: *"A year has 365 days. If I'm in a room with 23 people, the odds of someone matching MY birthday are tiny: 23/365 ≈ 6%."*
This is correct. But the paradox isn't about matches with *you*. It's about *any two people* matching.

### The Power of Pairs
When we look for *any* match, we are asking how many **pairs** we can form:
- With 2 people: 1 pair.
- With 5 people: 10 pairs.
- With 23 people: **253 pairs**! `(23 × 22) / 2 = 253`

Each of those 253 pairs has a `1/365` chance of matching. The probability starts to add up quickly!

> **Pigeonhole Principle:** To guarantee a match (100% probability), you need **366 people** (367 in leap years). But to make it *more likely than not* (50%), you need only **23**.
"""

LESSON_MATH_DETAILS = """\
## 📐 The Math: Complementary Counting

Calculating the probability of "at least one collision" directly is hard because we have to sum up the odds of exactly 1 collision, exactly 2, etc.

Instead, we calculate the probability of the **opposite event**: *What are the odds that everyone has a unique birthday?*

### Step-by-Step
1. **Person 1** enters. They can have any birthday: `365/365 = 1.0`
2. **Person 2** enters. To be unique, they must not match Person 1: `364/365`
3. **Person 3** enters. Must not match Person 1 or 2: `363/365`
4. ...
5. **Person N** enters: `(365 - N + 1) / 365`

Multiplying these independent probabilities:
`P(Unique) = 1 × (364/365) × (363/365) × ... × ((365 - N + 1)/365)`

Subtract from 1 to get the final probability:
`P(Collision) = 1 − P(Unique)`

For **N = 23**:
`P(Unique) ≈ 0.4927`
`P(Collision) ≈ 0.5073` (50.7%)!
"""


class BirthdayScreen(Screen):
    """Interactive Birthday Paradox lab screen."""

    BINDINGS = [
        Binding("escape", "go_back", "Back"),
        Binding("enter", "add_one", "Add 1 Person", show=False),
        Binding("space", "add_one", "Add 1 Person", show=False),
        Binding("r", "reset_all", "Reset", show=True),
        Binding("s", "run_sim", "Simulate Sweep", show=True),
        Binding("l", "show_lesson", "Lesson", show=True),
    ]

    DEFAULT_CSS = """
    BirthdayScreen {
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
        width: 50%;
        height: 100%;
        padding: 1;
        layout: vertical;
    }

    #right-panel {
        width: 50%;
        height: 100%;
        background: #111827;
        border-left: solid #2a3a4f;
        padding: 1;
        layout: vertical;
    }

    #tabs-row {
        height: 3;
        align: center middle;
        border-bottom: solid #1a2332;
        margin-bottom: 1;
    }

    #control-row {
        height: 3;
        align: center middle;
        margin-top: 1;
    }

    #stats-display {
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
        self.active_tab = "room"
        self.exact_sweep_data = exact_sweep(80)
        self.sim_sweep_data: list[float] | None = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static(
            "🎂 [bold #ff00e5]THE BIRTHDAY PARADOX LAB[/] — Trust No Gut Feeling",
            id="title-bar",
        )
        with Horizontal(id="main-area"):
            with Vertical(id="left-panel"):
                # Navigation tabs
                with Horizontal(id="tabs-row"):
                    yield Button("Build a Room", id="btn-tab-room", variant="primary")
                    yield Button("Simulation Sweep", id="btn-tab-sim")
                    yield Button("The Math Derivation", id="btn-tab-math")

                with ContentSwitcher(initial="tab-room-view", id="content-switcher"):
                    with Vertical(id="tab-room-view"):
                        yield RoomDisplay(id="room-display")
                        yield CalendarHeatmap(id="calendar-heatmap")
                    with Vertical(id="tab-sim-view"):
                        yield Static(
                            "[bold #ffab00]Simulation Sweep Mode[/]\n"
                            "Click 'Simulate' or press 's' to run 10,000 Monte Carlo trials "
                            "for each room size from 2 to 80 people. Observe how the random "
                            "simulations align perfectly with the theoretical exact curve.",
                            classes="room-empty",
                        )
                    with Vertical(id="tab-math-view"):
                        yield MathDerivation(id="math-derivation")

                with Horizontal(id="control-row"):
                    yield Button("Add 1 Person", id="btn-add-1", variant="success")
                    yield Button("Add 5 People", id="btn-add-5")
                    yield Button("Add to 23", id="btn-add-23")
                    yield Button("Run 10,000 Sim", id="btn-run-sim", variant="primary", disabled=True)

            with Vertical(id="right-panel"):
                yield ProbabilityChart(id="prob-chart")
                with ScrollableContainer(id="stats-display"):
                    yield Static("Loading...", id="stats-text")

        yield LessonPanel(id="lesson-panel")
        yield StatsBar(id="stats-bar")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#prob-chart", ProbabilityChart).set_exact(self.exact_sweep_data, 80)
        self.reset_all()

    def reset_all(self) -> None:
        """Reset the room state and clear graphs."""
        self.query_one("#room-display", RoomDisplay).clear_room()
        self.query_one("#calendar-heatmap", CalendarHeatmap).clear_calendar()
        self.query_one("#math-derivation", MathDerivation).set_n(2)
        self._update_stats()

    def _get_stats_text(self, n: int = 0, has_collision: bool = False) -> str:
        """Build stats text from explicit values (safe to call before mount)."""
        from gametheorist.modules.birthday.engine import exact_probability
        collision_status = "💥 Collision Found!" if has_collision else "None yet"
        prob = exact_probability(n)
        return (
            f"=== Room Statistics ===\n"
            f"People in Room (N): {n}\n"
            f"Possible Pairs: {(n * (n - 1) // 2) if n > 1 else 0}\n"
            f"Collision: {collision_status}\n\n"
            f"Theoretical Probability:\n"
            f"  P(collision) = {prob:.2%}\n"
            f"  P(no collision) = {(1 - prob):.2%}"
        )

    def _update_stats(self) -> None:
        room = self.query_one("#room-display", RoomDisplay)
        n = room.person_count
        has_collision = room.has_collision
        self.query_one("#stats-text", Static).update(
            self._get_stats_text(n=n, has_collision=has_collision)
        )

        # Update stats bar
        from gametheorist.modules.birthday.engine import exact_probability
        prob = exact_probability(n)
        self.query_one("#stats-bar", StatsBar).set_stats(
            people=n,
            prob_collision=f"{prob:.2%}",
            collision="Yes" if has_collision else "No",
        )

        if self.active_tab == "math":
            self.query_one("#math-derivation", MathDerivation).set_n(n)

    def action_add_one(self) -> None:
        """Add a single random person to the room."""
        if self.active_tab != "room":
            return

        room = self.query_one("#room-display", RoomDisplay)
        if room.has_collision:
            # If collision already found, ask for reset first
            self._update_status("[bold #ff6b6b]Collision already found. Reset room to start over![/]")
            return

        bday = generate_birthday()
        new_collision, idx = room.add_person(bday)

        # Update calendar heatmap
        self.query_one("#calendar-heatmap", CalendarHeatmap).update_calendar(
            room.birthdays, room.colliding_days
        )

        self._update_stats()

        if new_collision:
            room.show_explosion(bday)
            # Show lesson panel on first collision
            self.query_one("#lesson-panel", LessonPanel).show(LESSON_BIRTHDAY_PARADOX)

    def _update_status(self, text: str) -> None:
        pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id == "btn-tab-room":
            self._switch_tab("room")
        elif btn_id == "btn-tab-sim":
            self._switch_tab("sim")
        elif btn_id == "btn-tab-math":
            self._switch_tab("math")
        elif btn_id == "btn-add-1":
            self.action_add_one()
        elif btn_id == "btn-add-5":
            for _ in range(5):
                if not self.query_one("#room-display", RoomDisplay).has_collision:
                    self.action_add_one()
        elif btn_id == "btn-add-23":
            # Add until we hit 23 people or a collision happens
            room = self.query_one("#room-display", RoomDisplay)
            while room.person_count < 23 and not room.has_collision:
                self.action_add_one()
        elif btn_id == "btn-run-sim" or btn_id == "btn-tab-sim-run":
            self.action_run_sim()

    def _switch_tab(self, tab: str) -> None:
        self.active_tab = tab
        switcher = self.query_one("#content-switcher", ContentSwitcher)

        # Update tab button states
        for tid in ("room", "sim", "math"):
            btn = self.query_one(f"#btn-tab-{tid}", Button)
            btn.variant = "primary" if tid == tab else "default"

        # Update button rows depending on active tab
        self.query_one("#btn-add-1").disabled = tab != "room"
        self.query_one("#btn-add-5").disabled = tab != "room"
        self.query_one("#btn-add-23").disabled = tab != "room"
        self.query_one("#btn-run-sim").disabled = tab != "sim"

        if tab == "room":
            switcher.current = "tab-room-view"
        elif tab == "sim":
            switcher.current = "tab-sim-view"
        elif tab == "math":
            switcher.current = "tab-math-view"
            n = self.query_one("#room-display", RoomDisplay).person_count
            self.query_one("#math-derivation", MathDerivation).set_n(n)

    def action_run_sim(self) -> None:
        """Run progressive simulation sweep from N=2 to 80."""
        self.sim_sweep_data = monte_carlo_sweep_progressive(80, 10000)
        self.query_one("#prob-chart", ProbabilityChart).set_simulated(self.sim_sweep_data, 80)

        # Notify stats bar & text
        self.query_one("#stats-text", Static).update(
            f"[bold #76ff03]Simulation Sweep Complete![/]\n"
            f"Ran [bold]10,000[/] trials for each room size N=2..80.\n"
            f"See the orange dots on the chart aligning with the cyan exact math line."
        )

    def action_show_lesson(self) -> None:
        panel = self.query_one("#lesson-panel", LessonPanel)
        if panel.is_visible:
            panel.hide()
        else:
            if self.active_tab == "math":
                panel.show(LESSON_MATH_DETAILS)
            else:
                panel.show(LESSON_BIRTHDAY_PARADOX)

    def action_go_back(self) -> None:
        self.app.pop_screen()
