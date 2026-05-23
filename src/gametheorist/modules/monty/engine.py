"""Monty Hall engine — pure game logic, no UI dependencies.

Provides single-game play, batch simulation with numpy, and
Bayesian posterior computation for the Monty Hall problem.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Literal

import numpy as np


# ── Data Classes ─────────────────────────────────────────────────


class GameState(Enum):
    """States in the Monty Hall game state-machine."""

    SETUP = auto()
    PICKED = auto()
    MONTY_OPENED = auto()
    DECIDED = auto()
    REVEALED = auto()


@dataclass(frozen=True)
class GameResult:
    """Immutable result of one completed Monty Hall game."""

    car_door: int
    player_door: int
    won: bool
    strategy: Literal["switch", "stay"]
    monty_opened: list[int]
    n_doors: int
    monty_knew: bool


@dataclass(frozen=True)
class SimResult:
    """Summary statistics for a batch simulation."""

    wins: int
    losses: int
    win_rate: float
    n_games: int
    strategy: Literal["switch", "stay"]
    n_doors: int
    monty_knew: bool


@dataclass
class MontyHallGame:
    """A single interactive Monty Hall game.

    Parameters
    ----------
    n_doors : int
        Number of doors (default 3, must be >= 3).
    monty_knows : bool
        If True, Monty always opens goat doors.
        If False, Monty opens randomly (may reveal the car → instant loss).
    """

    n_doors: int = 3
    monty_knows: bool = True

    # ── internal state ──
    _car_door: int = field(default=-1, init=False, repr=False)
    _player_door: int = field(default=-1, init=False, repr=False)
    _monty_opened: list[int] = field(default_factory=list, init=False, repr=False)
    _state: GameState = field(default=GameState.SETUP, init=False, repr=False)
    _strategy: Literal["switch", "stay"] | None = field(
        default=None, init=False, repr=False
    )
    _car_revealed_by_monty: bool = field(default=False, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.n_doors < 3:
            raise ValueError("Need at least 3 doors for a Monty Hall game.")

    # ── public properties ────────────────────────────────────────

    @property
    def state(self) -> GameState:
        """Current game state."""
        return self._state

    @property
    def car_door(self) -> int:
        """Door hiding the car (0-indexed)."""
        return self._car_door

    @property
    def player_door(self) -> int:
        """Player's current door choice (0-indexed)."""
        return self._player_door

    @property
    def monty_opened(self) -> list[int]:
        """List of doors Monty has opened."""
        return list(self._monty_opened)

    @property
    def car_revealed_by_monty(self) -> bool:
        """True if ignorant Monty accidentally revealed the car."""
        return self._car_revealed_by_monty

    # ── game actions ─────────────────────────────────────────────

    def setup(self) -> None:
        """Randomly place the car behind one door and reset state."""
        self._car_door = random.randint(0, self.n_doors - 1)
        self._player_door = -1
        self._monty_opened = []
        self._state = GameState.SETUP
        self._strategy = None
        self._car_revealed_by_monty = False

    def player_pick(self, door: int) -> None:
        """Player makes their initial door choice (0-indexed)."""
        if self._state not in (GameState.SETUP,):
            raise RuntimeError(f"Cannot pick in state {self._state.name}")
        if not (0 <= door < self.n_doors):
            raise ValueError(f"Door must be 0..{self.n_doors - 1}, got {door}")
        self._player_door = door
        self._state = GameState.PICKED

    def monty_opens(self) -> list[int]:
        """Monty opens door(s) to reveal goat(s).

        For a classic 3-door game, opens 1 door.
        For n-door games, opens n-2 doors (leaving player's pick and one other).

        Returns
        -------
        list[int]
            The door indices Monty opened (0-indexed).
        """
        if self._state != GameState.PICKED:
            raise RuntimeError(f"Cannot open doors in state {self._state.name}")

        doors_to_open = self.n_doors - 2  # leave player's door + one other

        if self.monty_knows:
            # Monty knows where the car is — never opens the car door
            candidates = [
                d
                for d in range(self.n_doors)
                if d != self._player_door and d != self._car_door
            ]
            random.shuffle(candidates)
            self._monty_opened = sorted(candidates[:doors_to_open])
        else:
            # Ignorant Monty — picks randomly from non-player doors
            candidates = [d for d in range(self.n_doors) if d != self._player_door]
            random.shuffle(candidates)
            self._monty_opened = sorted(candidates[:doors_to_open])
            # Check if Monty accidentally revealed the car
            if self._car_door in self._monty_opened:
                self._car_revealed_by_monty = True

        self._state = GameState.MONTY_OPENED
        return list(self._monty_opened)

    def switch(self, new_door: int | None = None) -> None:
        """Player switches to another door.

        Parameters
        ----------
        new_door : int | None
            Specific door to switch to. If None, picks the remaining
            unopened, non-player door (classic behavior).
        """
        if self._state != GameState.MONTY_OPENED:
            raise RuntimeError(f"Cannot switch in state {self._state.name}")

        remaining = [
            d
            for d in range(self.n_doors)
            if d != self._player_door and d not in self._monty_opened
        ]

        if new_door is None:
            if not remaining:
                raise RuntimeError("No door to switch to (all opened by Monty)")
            self._player_door = remaining[0]
        else:
            if new_door not in remaining:
                raise ValueError(
                    f"Door {new_door} is not available. Options: {remaining}"
                )
            self._player_door = new_door

        self._strategy = "switch"
        self._state = GameState.DECIDED

    def stay(self) -> None:
        """Player stays with their original choice."""
        if self._state != GameState.MONTY_OPENED:
            raise RuntimeError(f"Cannot stay in state {self._state.name}")
        self._strategy = "stay"
        self._state = GameState.DECIDED

    def reveal(self) -> GameResult:
        """Open all doors and return the result."""
        if self._state != GameState.DECIDED:
            raise RuntimeError(f"Cannot reveal in state {self._state.name}")

        won = self._player_door == self._car_door
        # If ignorant Monty revealed the car, it's always a loss
        if self._car_revealed_by_monty:
            won = False

        self._state = GameState.REVEALED
        assert self._strategy is not None

        return GameResult(
            car_door=self._car_door,
            player_door=self._player_door,
            won=won,
            strategy=self._strategy,
            monty_opened=list(self._monty_opened),
            n_doors=self.n_doors,
            monty_knew=self.monty_knows,
        )


# ── Batch Simulation ─────────────────────────────────────────────


def simulate_batch(
    n_games: int,
    n_doors: int = 3,
    strategy: Literal["switch", "stay"] = "switch",
    monty_knows: bool = True,
) -> SimResult:
    """Run many Monty Hall games at once using numpy for speed.

    Parameters
    ----------
    n_games : int
        Number of games to simulate.
    n_doors : int
        Number of doors per game.
    strategy : "switch" | "stay"
        Player strategy after Monty opens doors.
    monty_knows : bool
        Whether Monty knows where the car is.

    Returns
    -------
    SimResult
        Aggregated simulation results.
    """
    rng = np.random.default_rng()

    car_doors = rng.integers(0, n_doors, size=n_games)
    player_picks = rng.integers(0, n_doors, size=n_games)

    if strategy == "stay":
        # Player stays — wins iff they initially picked the car
        wins_arr = car_doors == player_picks
    else:
        # strategy == "switch"
        if monty_knows:
            # Monty always reveals goats, then player switches.
            # With n_doors, switching wins unless player initially had the car.
            # (Classic result: switch wins with prob (n-1)/n for smart Monty)
            wins_arr = car_doors != player_picks
        else:
            # Ignorant Monty — may reveal car (instant loss).
            # We need to simulate which doors Monty opens.
            wins = np.zeros(n_games, dtype=bool)
            for i in range(n_games):
                car = int(car_doors[i])
                pick = int(player_picks[i])
                candidates = [d for d in range(n_doors) if d != pick]
                random.shuffle(candidates)
                opened = candidates[: n_doors - 2]
                if car in opened:
                    # Monty revealed the car — loss
                    wins[i] = False
                else:
                    # Switch to remaining door
                    remaining = [
                        d for d in range(n_doors) if d != pick and d not in opened
                    ]
                    wins[i] = remaining[0] == car if remaining else False
            wins_arr = wins

    total_wins = int(np.sum(wins_arr))
    return SimResult(
        wins=total_wins,
        losses=n_games - total_wins,
        win_rate=total_wins / n_games if n_games > 0 else 0.0,
        n_games=n_games,
        strategy=strategy,
        n_doors=n_doors,
        monty_knew=monty_knows,
    )


# ── Bayesian Posterior ───────────────────────────────────────────


def bayes_posterior(
    n_doors: int,
    player_pick: int,
    monty_opened: list[int],
) -> dict[int, float]:
    """Compute posterior probability of the car being behind each door.

    Uses Bayes' theorem assuming Monty knows and always opens goat doors.

    P(car=d | Monty opened O, player picked P)

    For the classic 3-door game:
      - Player's door keeps its prior 1/3
      - The remaining unopened door gets (n-1)/n probability

    For the general n-door case with smart Monty:
      - Player's door: 1/n
      - Each remaining unopened door (not player's): (n-1) / (n * remaining_count)

    Parameters
    ----------
    n_doors : int
        Total number of doors.
    player_pick : int
        Door the player initially chose (0-indexed).
    monty_opened : list[int]
        Doors Monty opened (0-indexed).

    Returns
    -------
    dict[int, float]
        Mapping of door index → posterior probability.
    """
    posteriors: dict[int, float] = {}
    opened_set = set(monty_opened)

    # Doors that are still closed (player's + remaining)
    closed_doors = [d for d in range(n_doors) if d not in opened_set]

    # Player's door keeps prior 1/n
    player_prob = 1.0 / n_doors

    # Total probability redistributed to remaining doors
    # The (n-1)/n probability that car is NOT behind player's door
    # is now spread across the remaining closed non-player doors
    remaining_non_player = [d for d in closed_doors if d != player_pick]
    other_prob = (1.0 - player_prob) / len(remaining_non_player) if remaining_non_player else 0.0

    for door in range(n_doors):
        if door in opened_set:
            posteriors[door] = 0.0
        elif door == player_pick:
            posteriors[door] = player_prob
        else:
            posteriors[door] = other_prob

    return posteriors


def format_bayes_explanation(
    n_doors: int,
    player_pick: int,
    monty_opened: list[int],
) -> str:
    """Generate a human-readable Bayes' theorem explanation.

    Returns a Rich-markup formatted string showing the prior → posterior update.
    """
    posteriors = bayes_posterior(n_doors, player_pick, monty_opened)
    prior = 1.0 / n_doors

    lines: list[str] = []
    lines.append("[bold #00e5ff]━━━ Bayes' Theorem Update ━━━[/]")
    lines.append("")
    lines.append(f"[dim]Prior probability (each door):[/]  [bold]1/{n_doors} = {prior:.4f}[/]")
    lines.append("")

    # Show what Monty did
    opened_str = ", ".join(str(d + 1) for d in monty_opened)
    lines.append(f"[dim]Monty opened door(s):[/]  [bold #ff6b6b]{opened_str}[/]")
    lines.append(f"[dim]Your pick:[/]  [bold #00e5ff]Door {player_pick + 1}[/]")
    lines.append("")

    lines.append("[bold #ff00e5]━━━ Posterior Probabilities ━━━[/]")
    lines.append("")

    # Build a visual table
    for door in range(n_doors):
        prob = posteriors[door]
        if door in monty_opened:
            bar = "[dim]░░░░░░░░░░ 0.0%  (opened — 🐐)[/]"
        elif door == player_pick:
            filled = int(prob * 20)
            bar_str = "█" * filled + "░" * (20 - filled)
            bar = f"[#00e5ff]{bar_str}[/] [bold]{prob:.1%}[/]  ← [#00e5ff]your pick[/]"
        else:
            filled = int(prob * 20)
            bar_str = "█" * filled + "░" * (20 - filled)
            bar = f"[#ffab00]{bar_str}[/] [bold]{prob:.1%}[/]  ← [#ffab00]switch here![/]"

        lines.append(f"  Door {door + 1}: {bar}")

    lines.append("")

    # The insight
    if n_doors == 3:
        lines.append(
            "[bold #76ff03]⚡ Insight:[/] Your door still has a 1/3 chance."
        )
        lines.append(
            "   The other door now has [bold]2/3[/] — switch to double your odds!"
        )
    else:
        switch_prob = (n_doors - 1) / n_doors
        lines.append(
            f"[bold #76ff03]⚡ Insight:[/] Your door still has 1/{n_doors} = {prior:.2%} chance."
        )
        lines.append(
            f"   Switching gives you [bold]{switch_prob:.2%}[/] — "
            f"that's {n_doors - 1}× better!"
        )

    return "\n".join(lines)
