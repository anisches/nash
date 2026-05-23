"""Monty Hall widgets — custom Textual widgets for the Monty Hall module.

Provides:
- DoorWidget: ASCII art door with multiple visual states
- DoorRow: Horizontal container for multiple doors
- ResultsChart: Plotext bar chart comparing switch vs stay
- BayesPanel: Visual Bayesian update panel
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
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
    CORAL,
)


# ── ASCII Door Art ───────────────────────────────────────────────

def _door_closed(number: int) -> str:
    """A closed door with its number."""
    n = str(number)
    return (
        f"[bold {NEON_CYAN}]╔══════════╗[/]\n"
        f"[bold {NEON_CYAN}]║[/]          [{NEON_CYAN}]║[/]\n"
        f"[bold {NEON_CYAN}]║[/]   [bold {TEXT_PRIMARY}]DOOR[/]   [{NEON_CYAN}]║[/]\n"
        f"[bold {NEON_CYAN}]║[/]    [bold {NEON_CYAN}]{n:^2s}[/]    [{NEON_CYAN}]║[/]\n"
        f"[bold {NEON_CYAN}]║[/]          [{NEON_CYAN}]║[/]\n"
        f"[bold {NEON_CYAN}]║[/]      [dim]●[/]   [{NEON_CYAN}]║[/]\n"
        f"[bold {NEON_CYAN}]║[/]          [{NEON_CYAN}]║[/]\n"
        f"[bold {NEON_CYAN}]║[/]          [{NEON_CYAN}]║[/]\n"
        f"[bold {NEON_CYAN}]╚══════════╝[/]"
    )


def _door_selected(number: int) -> str:
    """A selected/highlighted door."""
    n = str(number)
    return (
        f"[bold {NEON_CYAN}]╔══════════╗[/]\n"
        f"[bold {NEON_CYAN}]║[/] [on {BG_CARD}]        [/] [{NEON_CYAN}]║[/]\n"
        f"[bold {NEON_CYAN}]║[/] [on {BG_CARD}]  [bold {NEON_CYAN}]DOOR[/]  [/] [{NEON_CYAN}]║[/]\n"
        f"[bold {NEON_CYAN}]║[/] [on {BG_CARD}]   [{NEON_CYAN}]{n:^2s}[/]   [/] [{NEON_CYAN}]║[/]\n"
        f"[bold {NEON_CYAN}]║[/] [on {BG_CARD}]  [bold {NEON_CYAN}]◆ ◆[/]  [/] [{NEON_CYAN}]║[/]\n"
        f"[bold {NEON_CYAN}]║[/] [on {BG_CARD}]     [{NEON_CYAN}]●[/]  [/] [{NEON_CYAN}]║[/]\n"
        f"[bold {NEON_CYAN}]║[/] [on {BG_CARD}]  [bold {NEON_CYAN}]YOU[/]  [/] [{NEON_CYAN}]║[/]\n"
        f"[bold {NEON_CYAN}]║[/] [on {BG_CARD}]        [/] [{NEON_CYAN}]║[/]\n"
        f"[bold {NEON_CYAN}]╚══════════╝[/]"
    )


def _door_goat(number: int) -> str:
    """An opened door revealing a goat."""
    n = str(number)
    return (
        f"[dim]┌──────────┐[/]\n"
        f"[dim]│[/]          [dim]│[/]\n"
        f"[dim]│[/]    [bold]🐐[/]    [dim]│[/]\n"
        f"[dim]│[/]          [dim]│[/]\n"
        f"[dim]│[/]  [dim italic]goat![/]  [dim]│[/]\n"
        f"[dim]│[/]          [dim]│[/]\n"
        f"[dim]│[/]  [dim]door {n}[/] [dim]│[/]\n"
        f"[dim]│[/]          [dim]│[/]\n"
        f"[dim]└──────────┘[/]"
    )


def _door_car(number: int) -> str:
    """An opened door revealing the car."""
    n = str(number)
    return (
        f"[bold {AMBER}]╔══════════╗[/]\n"
        f"[bold {AMBER}]║[/]  [bold {AMBER}]★  ★[/]   [{AMBER}]║[/]\n"
        f"[bold {AMBER}]║[/]    [bold]🚗[/]    [{AMBER}]║[/]\n"
        f"[bold {AMBER}]║[/]          [{AMBER}]║[/]\n"
        f"[bold {AMBER}]║[/]  [bold {LIME}]CAR!![/]  [{AMBER}]║[/]\n"
        f"[bold {AMBER}]║[/]  [bold {AMBER}]★  ★[/]   [{AMBER}]║[/]\n"
        f"[bold {AMBER}]║[/]  [dim]door {n}[/] [{AMBER}]║[/]\n"
        f"[bold {AMBER}]║[/]          [{AMBER}]║[/]\n"
        f"[bold {AMBER}]╚══════════╝[/]"
    )


def _door_compact_closed(number: int) -> str:
    """Compact door icon for 100-door mode."""
    return f"[bold {NEON_CYAN}]▐{number:>2d}▌[/]"


def _door_compact_selected(number: int) -> str:
    """Compact selected door for 100-door mode."""
    return f"[bold {NEON_CYAN} on {BG_CARD}]▐{number:>2d}▌[/]"


def _door_compact_goat(_number: int) -> str:
    """Compact goat icon for 100-door mode."""
    return f"[dim]▐🐐▌[/]"


def _door_compact_car(number: int) -> str:
    """Compact car icon for 100-door mode."""
    return f"[bold {AMBER}]▐🚗▌[/]"


# ── DoorWidget ───────────────────────────────────────────────────


class DoorWidget(Static):
    """A single ASCII-art door that can be in various visual states.

    States: 'closed', 'selected', 'goat', 'car'
    """

    DEFAULT_CSS = f"""
    DoorWidget {{
        width: auto;
        height: auto;
        padding: 0 1;
        content-align: center middle;
    }}
    """

    door_state = reactive("closed")

    def __init__(self, door_number: int = 1, compact: bool = False, **kwargs) -> None:
        super().__init__(**kwargs)
        self._door_number = door_number
        self._compact = compact

    def render_door(self) -> str:
        """Build the door art string from current state."""
        n = self._door_number
        if self._compact:
            lookup = {
                "closed": _door_compact_closed,
                "selected": _door_compact_selected,
                "goat": _door_compact_goat,
                "car": _door_compact_car,
            }
        else:
            lookup = {
                "closed": _door_closed,
                "selected": _door_selected,
                "goat": _door_goat,
                "car": _door_car,
            }
        fn = lookup.get(self.door_state, _door_closed if not self._compact else _door_compact_closed)
        return fn(n)

    def watch_door_state(self, value: str) -> None:
        """Re-render when state changes."""
        self.update(self.render_door())

    def on_mount(self) -> None:
        """Initial render."""
        self.update(self.render_door())

    def set_state(self, state: str) -> None:
        """Set the door visual state.

        Parameters
        ----------
        state : str
            One of 'closed', 'selected', 'goat', 'car'.
        """
        self.door_state = state


# ── DoorRow ──────────────────────────────────────────────────────


class DoorRow(Widget):
    """Container holding multiple DoorWidgets in a horizontal layout."""

    DEFAULT_CSS = f"""
    DoorRow {{
        width: 100%;
        height: auto;
        align: center middle;
        padding: 1 0;
    }}

    DoorRow > Horizontal {{
        width: auto;
        height: auto;
        align: center middle;
    }}

    DoorRow .compact-grid {{
        width: 100%;
        height: auto;
        padding: 1 2;
    }}
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._n_doors: int = 3
        self._compact: bool = False
        self._doors: list[DoorWidget] = []

    def compose(self) -> ComposeResult:
        """Yield placeholder; doors added dynamically."""
        yield Horizontal(id="door-container")

    def setup_doors(self, n: int) -> None:
        """Create n door widgets, using compact mode for large n.

        Parameters
        ----------
        n : int
            Number of doors to display.
        """
        self._n_doors = n
        self._compact = n > 10
        self._doors = []

        container = self.query_one("#door-container", Horizontal)
        container.remove_children()

        for i in range(n):
            door = DoorWidget(door_number=i + 1, compact=self._compact, id=f"door-{i}")
            self._doors.append(door)
            container.mount(door)

    def get_door(self, index: int) -> DoorWidget:
        """Get door widget by 0-based index."""
        return self._doors[index]

    @property
    def doors(self) -> list[DoorWidget]:
        """All door widgets."""
        return list(self._doors)


# ── ResultsChart ─────────────────────────────────────────────────


class ResultsChart(PlotextPlot):
    """Bar chart comparing switch vs stay win rates.

    Updates live as games are played.
    """

    DEFAULT_CSS = """
    ResultsChart {
        width: 100%;
        height: 16;
        background: #1e293b;
        border: round #334155;
        padding: 0;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._switch_rate: float = 0.0
        self._stay_rate: float = 0.0
        self._has_data: bool = False

    def on_mount(self) -> None:
        """Initial setup of the chart."""
        self._draw_chart()

    def update_rates(
        self, switch_rate: float, stay_rate: float
    ) -> None:
        """Update the chart with new win rates.

        Parameters
        ----------
        switch_rate : float
            Win rate when switching (0.0 - 1.0).
        stay_rate : float
            Win rate when staying (0.0 - 1.0).
        """
        self._switch_rate = switch_rate
        self._stay_rate = stay_rate
        self._has_data = True
        self._draw_chart()
        self.refresh()

    def _draw_chart(self) -> None:
        """Redraw the plotext chart."""
        self.plt.clear_figure()
        self.plt.theme("dark")
        self.plt.canvas_color((30, 41, 59))  # slate-800
        self.plt.axes_color((15, 23, 42))    # slate-900
        self.plt.ticks_color((148, 163, 184)) # slate-400

        if not self._has_data:
            self.plt.title("Win Rates — play some games!")
            return

        labels = ["Switch", "Stay"]
        values = [self._switch_rate * 100, self._stay_rate * 100]
        colors = [(56, 189, 248), (251, 113, 133)]  # Slate Blue and Rose

        self.plt.bar(labels, values, color=colors, width=0.6)
        self.plt.ylim(0, 100)
        self.plt.ylabel("Win %")
        self.plt.title("Switch vs Stay")


# ── BayesPanel ───────────────────────────────────────────────────


class BayesPanel(Static):
    """Displays a visual Bayesian update showing prior → posterior probabilities.

    Shows the mathematical reasoning behind why switching is optimal.
    """

    DEFAULT_CSS = f"""
    BayesPanel {{
        width: 100%;
        height: auto;
        background: {BG_PANEL};
        border: round {NEON_MAGENTA};
        padding: 1 2;
        margin: 0 1;
        display: none;
    }}

    BayesPanel.visible {{
        display: block;
    }}
    """

    def show_update(
        self,
        n_doors: int,
        player_pick: int,
        monty_opened: list[int],
    ) -> None:
        """Show the Bayesian update for the current game state.

        Parameters
        ----------
        n_doors : int
            Total number of doors.
        player_pick : int
            Player's chosen door (0-indexed).
        monty_opened : list[int]
            Doors Monty opened (0-indexed).
        """
        from gametheorist.modules.monty.engine import format_bayes_explanation

        text = format_bayes_explanation(n_doors, player_pick, monty_opened)
        self.update(text)
        self.add_class("visible")

    def hide_panel(self) -> None:
        """Hide the Bayes panel."""
        self.remove_class("visible")

    def toggle(self) -> None:
        """Toggle visibility."""
        if self.has_class("visible"):
            self.hide_panel()
        else:
            # Only show if we have content
            if str(self.renderable).strip():
                self.add_class("visible")
