"""Prisoner's Dilemma — pure game theory engine.

Classic 2-player game + iterated play + tournament + simple evolutionary dynamics.

This is the heart of "nash" game theory: why rational players often
fail to cooperate even when cooperation is better for everyone.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Literal

import numpy as np


# ── Core types ──────────────────────────────────────────────────

class Move(str, Enum):
    """A single move in the Prisoner's Dilemma."""
    COOPERATE = "C"
    DEFECT = "D"


MoveType = Literal["C", "D"]


# Standard payoff matrix (row player payoff, column player payoff)
# Common values used in literature:
#   Temptation (T) = 5
#   Reward     (R) = 3
#   Punishment (P) = 1
#   Sucker     (S) = 0
#
# Payoff for (my_move, opponent_move) → my_score

PAYOFFS: dict[tuple[MoveType, MoveType], int] = {
    ("C", "C"): 3,   # Reward for mutual cooperation
    ("C", "D"): 0,   # Sucker payoff
    ("D", "C"): 5,   # Temptation to defect
    ("D", "D"): 1,   # Punishment for mutual defection
}


@dataclass(slots=True)
class RoundResult:
    """Result of one round between two players."""
    player1_move: MoveType
    player2_move: MoveType
    player1_score: int
    player2_score: int


@dataclass(slots=True)
class GameResult:
    """Full result of an iterated game between two strategies."""
    strategy1: str
    strategy2: str
    rounds: int
    p1_total: int
    p2_total: int
    p1_avg: float
    p2_avg: float
    history: list[RoundResult] = field(default_factory=list)


@dataclass(slots=True)
class TournamentResult:
    """Result of a round-robin tournament across multiple strategies."""
    strategies: list[str]
    scores: dict[str, float]          # average score per round across all opponents
    raw_matrix: dict[tuple[str, str], float]  # (s1, s2) -> avg score for s1 vs s2
    rounds_per_match: int


@dataclass(slots=True)
class EvolutionResult:
    """Result of a simple replicator dynamics simulation."""
    generations: int
    strategies: list[str]
    # population[gen][strategy_index] = proportion of that strategy at that generation
    population_history: list[list[float]]
    final_population: list[float]


# ── Strategy base + classic implementations ─────────────────────


class Strategy:
    """Base class for a Prisoner's Dilemma strategy.

    Subclasses must implement `next_move(self, my_history, opp_history)`.
    """

    name: str = "Base"

    def next_move(self, my_history: list[MoveType], opp_history: list[MoveType]) -> MoveType:
        raise NotImplementedError

    def reset(self) -> None:
        """Optional hook for stateful strategies."""
        pass


class AlwaysCooperate(Strategy):
    name = "Always Cooperate (ALLC)"

    def next_move(self, my_history, opp_history):
        return "C"


class AlwaysDefect(Strategy):
    name = "Always Defect (ALLD)"

    def next_move(self, my_history, opp_history):
        return "D"


class TitForTat(Strategy):
    """The famous champion of Axelrod's tournaments."""

    name = "Tit-for-Tat (TFT)"

    def next_move(self, my_history, opp_history):
        if not opp_history:
            return "C"  # cooperate on first move
        return opp_history[-1]


class GrimTrigger(Strategy):
    """Cooperate until opponent defects once, then defect forever."""

    name = "Grim Trigger"

    def __init__(self):
        self._triggered = False

    def next_move(self, my_history, opp_history):
        if self._triggered:
            return "D"
        if opp_history and "D" in opp_history:
            self._triggered = True
            return "D"
        return "C"

    def reset(self):
        self._triggered = False


class RandomStrategy(Strategy):
    name = "Random"

    def __init__(self, p_cooperate: float = 0.5, rng: np.random.Generator | None = None):
        self.p = p_cooperate
        self._rng = rng or np.random.default_rng()

    def next_move(self, my_history, opp_history):
        return "C" if self._rng.random() < self.p else "D"


class Pavlov(Strategy):
    """Win-Stay, Lose-Shift (also called Pavlov).

    Repeat previous move if you did well, switch if you did poorly.
    """

    name = "Pavlov (Win-Stay Lose-Shift)"

    def __init__(self):
        self._last_move: MoveType = "C"

    def next_move(self, my_history, opp_history):
        if not my_history:
            self._last_move = "C"
            return "C"

        # Look at the payoff we just got
        last_payoff = PAYOFFS[(my_history[-1], opp_history[-1])]
        if last_payoff >= 3:   # Reward or Temptation → we "won"
            return self._last_move
        else:
            # Switch
            self._last_move = "D" if self._last_move == "C" else "C"
            return self._last_move

    def reset(self):
        self._last_move = "C"


# Registry of built-in strategies (for easy tournament creation)
BUILTIN_STRATEGIES: dict[str, type[Strategy]] = {
    "ALLC": AlwaysCooperate,
    "ALLD": AlwaysDefect,
    "TFT": TitForTat,
    "Grim": GrimTrigger,
    "Random": RandomStrategy,
    "Pavlov": Pavlov,
}


# ── Core game functions ─────────────────────────────────────────


def play_round(move1: MoveType, move2: MoveType) -> RoundResult:
    """Play a single round and return payoffs."""
    s1 = PAYOFFS[(move1, move2)]
    s2 = PAYOFFS[(move2, move1)]
    return RoundResult(move1, move2, s1, s2)


def play_game(
    strat1: Strategy,
    strat2: Strategy,
    rounds: int = 100,
    noise: float = 0.0,
    rng: np.random.Generator | None = None,
) -> GameResult:
    """Play an iterated game between two strategy instances."""
    if rng is None:
        rng = np.random.default_rng()

    strat1.reset()
    strat2.reset()

    h1: list[MoveType] = []
    h2: list[MoveType] = []
    results: list[RoundResult] = []

    total1 = 0
    total2 = 0

    for _ in range(rounds):
        m1 = strat1.next_move(h1, h2)
        m2 = strat2.next_move(h2, h1)

        # Optional noise (trembling hand)
        if noise > 0:
            if rng.random() < noise:
                m1 = "D" if m1 == "C" else "C"
            if rng.random() < noise:
                m2 = "D" if m2 == "C" else "C"

        r = play_round(m1, m2)
        results.append(r)

        h1.append(m1)
        h2.append(m2)
        total1 += r.player1_score
        total2 += r.player2_score

    n = max(1, rounds)
    return GameResult(
        strategy1=strat1.name,
        strategy2=strat2.name,
        rounds=rounds,
        p1_total=total1,
        p2_total=total2,
        p1_avg=total1 / n,
        p2_avg=total2 / n,
        history=results,
    )


def run_tournament(
    strategy_classes: list[type[Strategy]],
    rounds_per_match: int = 150,
    noise: float = 0.0,
) -> TournamentResult:
    """Round-robin tournament. Each strategy plays every other (including itself)."""
    instances = [cls() for cls in strategy_classes]
    names = [s.name for s in instances]

    scores: dict[str, list[float]] = {name: [] for name in names}
    raw: dict[tuple[str, str], float] = {}

    for i, s1 in enumerate(instances):
        for j, s2 in enumerate(instances):
            game = play_game(s1, s2, rounds=rounds_per_match, noise=noise)
            scores[names[i]].append(game.p1_avg)
            raw[(names[i], names[j])] = game.p1_avg

    avg_scores = {name: float(np.mean(vals)) for name, vals in scores.items()}

    return TournamentResult(
        strategies=names,
        scores=avg_scores,
        raw_matrix=raw,
        rounds_per_match=rounds_per_match,
    )


# ── Simple evolutionary / replicator dynamics ───────────────────


def run_evolution(
    strategy_classes: list[type[Strategy]],
    generations: int = 50,
    population_size: int = 100,
    rounds_per_match: int = 50,
    mutation_rate: float = 0.01,
    seed: int | None = None,
) -> EvolutionResult:
    """Very simple Moran-process style evolutionary simulation.

    Each generation:
      - Every individual plays a random opponent
      - Average payoff is treated as fitness
      - Next generation is sampled proportional to fitness (with mutation)

    This is intentionally simple and visual rather than biologically precise.
    """
    rng = np.random.default_rng(seed)
    n_strats = len(strategy_classes)

    # Start with uniform population
    proportions = np.ones(n_strats) / n_strats

    history: list[list[float]] = [proportions.tolist()]

    for _ in range(generations):
        # Create population
        pop_indices = rng.choice(n_strats, size=population_size, p=proportions)

        # Play one game per individual against a random opponent
        payoffs = np.zeros(population_size)
        for idx in range(population_size):
            i = pop_indices[idx]
            j = rng.choice(population_size)  # random opponent
            s1 = strategy_classes[i]()
            s2 = strategy_classes[pop_indices[j]]()
            game = play_game(s1, s2, rounds=rounds_per_match)
            payoffs[idx] = game.p1_avg

        # Average payoff per strategy type in this generation
        strat_payoffs = np.zeros(n_strats)
        counts = np.zeros(n_strats)
        for k in range(n_strats):
            mask = pop_indices == k
            if np.any(mask):
                strat_payoffs[k] = payoffs[mask].mean()
                counts[k] = mask.sum()

        # Fitness = payoff (shifted to be positive)
        min_p = strat_payoffs.min()
        fitness = strat_payoffs - min_p + 1e-6

        # New proportions proportional to fitness
        new_props = fitness * counts
        new_props = new_props / new_props.sum()

        # Mutation (random drift)
        if mutation_rate > 0:
            noise = rng.dirichlet(np.ones(n_strats)) * mutation_rate
            new_props = (1 - mutation_rate) * new_props + noise
            new_props = new_props / new_props.sum()

        proportions = new_props
        history.append(proportions.tolist())

    return EvolutionResult(
        generations=generations,
        strategies=[cls().name for cls in strategy_classes],
        population_history=history,
        final_population=proportions.tolist(),
    )


# ── Pretty printing helpers (for lessons / debug) ───────────────


def payoff_matrix_text() -> str:
    """Return a nice text representation of the payoff matrix."""
    return (
        "          Opponent\n"
        "          C     D\n"
        "You  C   3,3   0,5\n"
        "     D   5,0   1,1\n"
        "\n"
        "T=5 (Temptation)  R=3 (Reward)\n"
        "P=1 (Punishment)  S=0 (Sucker)"
    )
