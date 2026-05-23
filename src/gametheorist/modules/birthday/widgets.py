"""Birthday Paradox — custom Textual widgets.

PersonWidget, RoomDisplay, ProbabilityChart, CalendarHeatmap.
"""

from __future__ import annotations

from typing import Sequence

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static
from textual_plotext import PlotextPlot

from gametheorist.modules.birthday.engine import (
    DAYS_IN_YEAR,
    MONTH_DAYS,
    MONTH_NAMES,
    day_to_label,
    day_to_month_day,
)
from gametheorist.theme import (
    AMBER,
    BG_CARD,
    BG_DARK,
    BG_PANEL,
    LIME,
    NEON_CYAN,
    NEON_MAGENTA,
    TEXT_DIM,
    TEXT_PRIMARY,
)


# ── PersonWidget ─────────────────────────────────────────────────

class PersonWidget(Static):
    """A compact person icon with their birthday.

    Shows ``👤`` with the birthday label below. Persons whose birthday
    collides with someone else are highlighted in neon magenta.
    """

    DEFAULT_CSS = """
    PersonWidget {
        width: 10;
        height: 3;
        content-align: center middle;
        text-align: center;
        padding: 0;
        margin: 0;
    }

    PersonWidget.collision {
        color: #ff00e5;
        text-style: bold;
        background: #2a0025;
    }

    PersonWidget.new-arrival {
        color: #76ff03;
        text-style: bold;
    }
    """

    is_collision: reactive[bool] = reactive(False)
    is_new: reactive[bool] = reactive(False)

    def __init__(
        self,
        person_index: int,
        birthday: int,
        collision: bool = False,
        **kwargs,
    ) -> None:
        self.person_index = person_index
        self.birthday = birthday
        label = day_to_label(birthday)
        icon = "💥" if collision else "👤"
        display_text = f"{icon}\n{label}"
        super().__init__(display_text, **kwargs)
        self.is_collision = collision
        if collision:
            self.add_class("collision")

    def mark_collision(self) -> None:
        """Mark this person as having a colliding birthday."""
        self.is_collision = True
        self.add_class("collision")
        label = day_to_label(self.birthday)
        self.update(f"💥\n{label}")

    def mark_new(self) -> None:
        """Temporarily mark as newly arrived."""
        self.is_new = True
        self.add_class("new-arrival")

    def clear_new(self) -> None:
        """Remove the new-arrival highlight."""
        self.is_new = False
        self.remove_class("new-arrival")


# ── RoomDisplay ──────────────────────────────────────────────────

class RoomDisplay(Widget):
    """Grid of PersonWidgets representing the room.

    Scrollable, highlights collisions with color changes.
    """

    DEFAULT_CSS = """
    RoomDisplay {
        width: 100%;
        height: 1fr;
        background: #111827;
        border: round #2a3a4f;
        padding: 1;
        overflow-y: auto;
        overflow-x: hidden;
    }

    RoomDisplay .room-grid {
        width: 100%;
        height: auto;
        layout: horizontal;
        overflow: hidden;
        content-align: left top;
    }

    RoomDisplay .room-empty {
        width: 100%;
        height: 100%;
        content-align: center middle;
        text-align: center;
        color: #64748b;
    }

    RoomDisplay .room-title {
        width: 100%;
        height: 1;
        color: #00e5ff;
        text-style: bold;
        padding: 0 0 1 0;
    }

    RoomDisplay .explosion-banner {
        width: 100%;
        height: auto;
        content-align: center middle;
        text-align: center;
        color: #ff00e5;
        text-style: bold;
        padding: 1 0;
        display: none;
    }

    RoomDisplay .explosion-banner.visible {
        display: block;
    }
    """

    person_count: reactive[int] = reactive(0)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._birthdays: list[int] = []
        self._colliding_days: set[int] = set()

    def compose(self) -> ComposeResult:
        yield Static(
            "🏠 [bold cyan]The Room[/]",
            classes="room-title",
        )
        yield Static(
            "[dim]Press [bold]Enter[/bold] to add a person…[/]",
            classes="room-empty",
            id="room-empty-msg",
        )
        yield Horizontal(classes="room-grid", id="room-grid")
        yield Static("", classes="explosion-banner", id="explosion-banner")

    def add_person(self, birthday: int) -> tuple[bool, int | None]:
        """Add a person to the room.

        Returns
        -------
        tuple[bool, int | None]
            ``(is_new_collision, person_index_or_None)``
        """
        person_idx = len(self._birthdays)
        is_collision = birthday in self._colliding_days or (
            birthday in self._birthdays
        )

        self._birthdays.append(birthday)

        # Check if this person caused a NEW collision
        new_collision = birthday in self._birthdays[:-1]
        if new_collision:
            self._colliding_days.add(birthday)

        # Hide the empty message
        empty_msg = self.query_one("#room-empty-msg", Static)
        empty_msg.styles.display = "none"

        # Create person widget
        grid = self.query_one("#room-grid", Horizontal)
        pw = PersonWidget(
            person_idx,
            birthday,
            collision=new_collision,
            id=f"person-{person_idx}",
        )
        grid.mount(pw)

        # If collision, also highlight earlier person(s) with same birthday
        if new_collision:
            for i, bd in enumerate(self._birthdays[:-1]):
                if bd == birthday:
                    try:
                        earlier = self.query_one(f"#person-{i}", PersonWidget)
                        earlier.mark_collision()
                    except Exception:
                        pass

        self.person_count = len(self._birthdays)
        return new_collision, person_idx if new_collision else None

    def show_explosion(self, day: int) -> None:
        """Show the explosion banner for a collision."""
        label = day_to_label(day)
        banner = self.query_one("#explosion-banner", Static)
        banner.update(
            f"\n💥💥💥  [bold #ff00e5]COLLISION![/]  💥💥💥\n"
            f"[bold #ffab00]Two people share [#ff00e5]{label}[/#ff00e5]![/]\n"
            f"[dim]With just [bold]{self.person_count}[/bold] people in the room![/]\n"
        )
        banner.add_class("visible")

    def hide_explosion(self) -> None:
        """Hide the explosion banner."""
        banner = self.query_one("#explosion-banner", Static)
        banner.remove_class("visible")

    def clear_room(self) -> None:
        """Remove all people from the room."""
        self._birthdays.clear()
        self._colliding_days.clear()
        self.person_count = 0

        grid = self.query_one("#room-grid", Horizontal)
        grid.remove_children()

        empty_msg = self.query_one("#room-empty-msg", Static)
        empty_msg.styles.display = "block"

        self.hide_explosion()

    @property
    def birthdays(self) -> list[int]:
        """Current list of birthdays in the room."""
        return list(self._birthdays)

    @property
    def colliding_days(self) -> set[int]:
        """Set of days that have collisions."""
        return set(self._colliding_days)

    @property
    def has_collision(self) -> bool:
        """Whether any collision has occurred."""
        return len(self._colliding_days) > 0


# ── ProbabilityChart ─────────────────────────────────────────────

class ProbabilityChart(PlotextPlot):
    """Line chart of collision probability vs number of people.

    Two lines: simulated (scatter) and theoretical (solid).
    Reference lines at P=0.5 / n=23.
    """

    DEFAULT_CSS = """
    ProbabilityChart {
        width: 100%;
        height: 100%;
        min-height: 14;
        background: #1e293b;
        border: round #334155;
        padding: 0;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._exact_data: list[float] | None = None
        self._sim_data: list[float] | None = None
        self._max_people: int = 80

    def on_mount(self) -> None:
        """Draw an empty chart on mount."""
        self._draw()

    def _setup_theme(self) -> None:
        """Apply dark theme to the plot."""
        self.plt.theme("dark")
        self.plt.canvas_color((30, 41, 59))  # slate-800
        self.plt.axes_color((15, 23, 42))    # slate-900
        self.plt.ticks_color((148, 163, 184)) # slate-400

    def _draw(self) -> None:
        """Render the chart with current data."""
        self.plt.clear_figure()
        self._setup_theme()
        self.plt.title("P(Birthday Collision)")
        self.plt.xlabel("People in Room")
        self.plt.ylabel("P(collision)")
        self.plt.ylim(0, 1.05)
        self.plt.xlim(2, self._max_people)

        x = list(range(2, self._max_people + 1))

        # Exact (theoretical) line
        if self._exact_data is not None:
            self.plt.plot(
                x,
                self._exact_data,
                label="Exact",
                color=(56, 189, 248),  # Slate Blue
            )

        # Simulated scatter
        if self._sim_data is not None:
            self.plt.scatter(
                x,
                self._sim_data,
                label="Simulated",
                color=(251, 113, 133),  # Slate Rose
                marker="dot",
            )

        # Reference lines
        # P = 0.5 horizontal
        self.plt.hline(0.5, color=(251, 191, 36))  # Slate Amber
        # n = 23 vertical
        self.plt.vline(23, color=(251, 191, 36))

        self.refresh()

    def set_exact(self, data: list[float], max_people: int = 80) -> None:
        """Set the exact probability curve."""
        self._exact_data = data
        self._max_people = max_people
        self._draw()

    def set_simulated(self, data: list[float], max_people: int = 80) -> None:
        """Set the simulated probability data."""
        self._sim_data = data
        self._max_people = max_people
        self._draw()

    def clear_data(self) -> None:
        """Reset both datasets."""
        self._exact_data = None
        self._sim_data = None
        self._draw()


# ── CalendarHeatmap ──────────────────────────────────────────────

class CalendarHeatmap(Static):
    """Compact 12×31 grid showing birthday distribution.

    Empty cells are dim, occupied cells are cyan, collisions magenta.
    """

    DEFAULT_CSS = """
    CalendarHeatmap {
        width: 100%;
        height: auto;
        min-height: 16;
        background: #111827;
        border: round #2a3a4f;
        padding: 1 2;
        overflow: hidden;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__("", **kwargs)
        self._occupied: set[int] = set()
        self._collisions: set[int] = set()

    def update_calendar(
        self,
        birthdays: Sequence[int],
        colliding_days: set[int],
    ) -> None:
        """Rebuild the heatmap from current room state."""
        self._occupied = set(birthdays)
        self._collisions = set(colliding_days)
        self._render_grid()

    def clear_calendar(self) -> None:
        """Reset the heatmap."""
        self._occupied.clear()
        self._collisions.clear()
        self._render_grid()

    def _render_grid(self) -> None:
        """Build the rich-markup grid string."""
        lines: list[str] = []
        lines.append("[bold cyan]📅 Calendar Heatmap[/]")
        lines.append("")

        # Header: day numbers
        header = "     "
        for d in range(1, 32):
            if d % 5 == 1:
                header += f"[dim]{d:<2}[/]"
            else:
                header += "  "
        lines.append(header)

        for m in range(12):
            row = f"[bold #64748b]{MONTH_NAMES[m]}[/] "
            for d in range(1, 32):
                if d > MONTH_DAYS[m]:
                    row += "  "
                    continue
                # Convert to day-of-year
                day_num = sum(MONTH_DAYS[:m]) + d - 1
                if day_num in self._collisions:
                    row += "[bold #ff00e5]██[/]"
                elif day_num in self._occupied:
                    row += "[#00e5ff]██[/]"
                else:
                    row += "[#1a2332]░░[/]"
            lines.append(row)

        # Legend
        lines.append("")
        lines.append(
            "[#1a2332]░░[/] Empty  "
            "[#00e5ff]██[/] Occupied  "
            "[bold #ff00e5]██[/] Collision"
        )

        self.update("\n".join(lines))


# ── MathDerivation ───────────────────────────────────────────────

class MathDerivation(Static):
    """Interactive step-by-step derivation of the exact formula.

    Shows complementary counting with each factor visible.
    """

    DEFAULT_CSS = """
    MathDerivation {
        width: 100%;
        height: auto;
        min-height: 10;
        background: #111827;
        border: round #2a3a4f;
        padding: 1 2;
        overflow-y: auto;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__("", **kwargs)
        self._n_people: int = 0

    def set_n(self, n: int) -> None:
        """Show the derivation for *n* people."""
        self._n_people = max(2, min(n, 50))  # Clamp for display
        self._render()

    def _render(self) -> None:
        """Build the rich-markup derivation."""
        from gametheorist.modules.birthday.engine import (
            exact_factors,
            exact_probability,
            exact_running_product,
        )

        n = self._n_people
        if n < 2:
            self.update("[dim]Select n ≥ 2 to see the derivation.[/]")
            return

        lines: list[str] = []
        lines.append("[bold cyan]📐 The Math — Complementary Counting[/]")
        lines.append("")
        lines.append(
            "[#e2e8f0]Instead of counting collisions, count the opposite:[/]"
        )
        lines.append(
            "[bold #ffab00]P(collision) = 1 − P(everyone has a unique birthday)[/]"
        )
        lines.append("")

        factors = exact_factors(n)
        running = exact_running_product(n)

        lines.append(f"[bold #e2e8f0]For n = {n} people:[/]")
        lines.append("")
        lines.append("[#64748b]Person  Factor              Running P(no collision)[/]")
        lines.append("[#64748b]" + "─" * 56 + "[/]")

        # Show each factor
        display_max = min(n, 30)
        for i in range(display_max):
            numerator = 365 - i
            factor_str = f"{numerator}/365"
            factor_val = factors[i]
            running_val = running[i]

            # Color by how much probability remains
            if running_val > 0.7:
                color = "#76ff03"
            elif running_val > 0.4:
                color = "#ffab00"
            else:
                color = "#ff6b6b"

            person_label = f"#{i + 1:>3}"
            lines.append(
                f"  [#64748b]{person_label}[/]    "
                f"[#e2e8f0]{factor_str:<8}[/] = "
                f"[{color}]{factor_val:.6f}[/]    "
                f"[{color}]{running_val:.6f}[/]"
            )

        if n > display_max:
            lines.append(f"  [dim]… ({n - display_max} more factors) …[/]")

        # Final result
        p = exact_probability(n)
        lines.append("")
        lines.append("[#64748b]" + "─" * 56 + "[/]")
        lines.append(
            f"[bold]P(no collision)  = [#76ff03]{1 - p:.6f}[/][/]"
        )
        lines.append(
            f"[bold]P(collision)     = [bold #ff00e5]{p:.6f}[/]  "
            f"({p * 100:.2f}%)[/]"
        )

        if p >= 0.5:
            lines.append("")
            lines.append(
                "[bold #ff00e5]⚡ > 50% — More likely than not![/]"
            )

        self.update("\n".join(lines))
