"""Birthday Paradox — pure simulation & math engine.

No UI imports.  All functions are deterministic-seed-friendly for
reproducibility or fast NumPy vectorised for Monte Carlo.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Sequence

import numpy as np

# ── Constants ────────────────────────────────────────────────────
DAYS_IN_YEAR: int = 365

MONTH_NAMES: list[str] = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]

MONTH_DAYS: list[int] = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

# Cumulative days at start of each month (0-indexed)
_MONTH_STARTS: list[int] = []
_acc = 0
for _d in MONTH_DAYS:
    _MONTH_STARTS.append(_acc)
    _acc += _d


# ── Helpers ──────────────────────────────────────────────────────

def day_to_month_day(day: int) -> tuple[int, int]:
    """Convert a 0-364 day number to (month_index, day_of_month).

    Returns
    -------
    tuple[int, int]
        ``(month_index, day_of_month)`` where *month_index* is 0-11
        and *day_of_month* is 1-based (e.g. Jan 1 → ``(0, 1)``).
    """
    for m in range(11, -1, -1):
        if day >= _MONTH_STARTS[m]:
            return m, day - _MONTH_STARTS[m] + 1
    return 0, day + 1  # pragma: no cover


def day_to_label(day: int) -> str:
    """Human-readable label like ``'Jan 15'``."""
    m, d = day_to_month_day(day)
    return f"{MONTH_NAMES[m]} {d:>2}"


# ── Data classes ─────────────────────────────────────────────────

@dataclass(slots=True)
class RoomResult:
    """Result of simulating one room of *n* people."""

    birthdays: list[int]
    has_collision: bool
    first_collision_at: int | None = None
    colliding_days: list[int] = field(default_factory=list)


# ── Core simulation functions ────────────────────────────────────

def generate_birthday() -> int:
    """Return a uniformly random birthday in ``[0, 364]``."""
    return random.randint(0, DAYS_IN_YEAR - 1)


def simulate_room(n_people: int) -> RoomResult:
    """Generate *n_people* birthdays and check for collisions.

    Parameters
    ----------
    n_people:
        Number of people to place in the room (≥ 1).

    Returns
    -------
    RoomResult
        Full details of the simulation including whether a collision
        occurred, on which person it first appeared, and which days
        collided.
    """
    birthdays: list[int] = []
    seen: dict[int, int] = {}  # day → index of first person with that day
    first_collision_at: int | None = None
    colliding_days_set: set[int] = set()

    for i in range(n_people):
        day = generate_birthday()
        birthdays.append(day)
        if day in seen:
            colliding_days_set.add(day)
            if first_collision_at is None:
                first_collision_at = i  # 0-indexed person who caused it
        else:
            seen[day] = i

    return RoomResult(
        birthdays=birthdays,
        has_collision=first_collision_at is not None,
        first_collision_at=first_collision_at,
        colliding_days=sorted(colliding_days_set),
    )


# ── Monte Carlo ──────────────────────────────────────────────────

def monte_carlo_probability(n_people: int, n_trials: int = 10_000) -> float:
    """Estimate P(collision) for *n_people* via Monte Carlo.

    Uses NumPy for vectorised simulation.

    Parameters
    ----------
    n_people:
        Number of people per room.
    n_trials:
        Number of independent rooms to simulate.

    Returns
    -------
    float
        Fraction of rooms that had at least one birthday collision.
    """
    # Each row is one trial, each column is one person's birthday
    rooms = np.random.randint(0, DAYS_IN_YEAR, size=(n_trials, n_people))
    # Count unique birthdays per row; collision iff nunique < n_people
    collisions = 0
    for row in rooms:
        if len(np.unique(row)) < n_people:
            collisions += 1
    return collisions / n_trials


def monte_carlo_sweep(
    max_people: int = 80,
    n_trials: int = 10_000,
) -> list[float]:
    """Run Monte Carlo for n = 2 … *max_people*.

    Parameters
    ----------
    max_people:
        Upper bound of people to sweep through (inclusive).
    n_trials:
        Trials per value of n.

    Returns
    -------
    list[float]
        ``result[i]`` is the simulated P(collision) for ``n = i + 2`` people.
    """
    probabilities: list[float] = []
    for n in range(2, max_people + 1):
        probabilities.append(monte_carlo_probability(n, n_trials))
    return probabilities


def monte_carlo_sweep_progressive(
    max_people: int = 80,
    n_trials: int = 10_000,
) -> list[float]:
    """Optimised progressive Monte Carlo sweep.

    Uses a smarter strategy: for each trial, build the room person by
    person and record *when* the first collision happens.  This lets
    us compute P(collision) for every n in a single pass per trial.

    Returns
    -------
    list[float]
        ``result[i]`` is the simulated P(collision) for ``n = i + 2``.
    """
    # collision_by[k] counts trials where first collision happened
    # on person index k (0-indexed person who caused the collision)
    collision_by = np.zeros(max_people + 1, dtype=np.int64)

    for _ in range(n_trials):
        seen: set[int] = set()
        for k in range(max_people):
            day = random.randint(0, DAYS_IN_YEAR - 1)
            if day in seen:
                collision_by[k] += 1
                break
            seen.add(day)

    # Cumulative: P(collision with n people) = sum of collision_by[0..n-1] / n_trials
    cum = np.cumsum(collision_by) / n_trials
    # We want n=2..max_people → indices 1..(max_people-1) in cum
    return [float(cum[n - 1]) for n in range(2, max_people + 1)]


# ── Exact probability ───────────────────────────────────────────

def exact_probability(n_people: int) -> float:
    """Exact P(at least one collision) for *n_people* in a 365-day year.

    Uses complementary counting:
        P = 1 − ∏_{i=0}^{n-1} (365 − i) / 365

    Parameters
    ----------
    n_people:
        Number of people (≥ 1).

    Returns
    -------
    float
        Exact collision probability.
    """
    if n_people <= 1:
        return 0.0
    if n_people > DAYS_IN_YEAR:
        return 1.0
    # Product of (365-i)/365 for i in 0..n-1
    log_no_collision = sum(
        math.log(DAYS_IN_YEAR - i) - math.log(DAYS_IN_YEAR)
        for i in range(n_people)
    )
    return 1.0 - math.exp(log_no_collision)


def exact_sweep(max_people: int = 80) -> list[float]:
    """Exact P(collision) for n = 2 … *max_people*.

    Returns
    -------
    list[float]
        ``result[i]`` is P(collision) for ``n = i + 2``.
    """
    return [exact_probability(n) for n in range(2, max_people + 1)]


def exact_factors(n_people: int) -> list[float]:
    """Return individual factors ``(365-i)/365`` for i in ``0 … n-1``.

    Useful for the step-by-step derivation display.
    """
    return [(DAYS_IN_YEAR - i) / DAYS_IN_YEAR for i in range(n_people)]


def exact_running_product(n_people: int) -> list[float]:
    """Running product of no-collision factors → P(no collision) after each person.

    Returns
    -------
    list[float]
        ``result[k]`` is P(no collision) after person ``k`` (0-indexed).
    """
    products: list[float] = []
    p = 1.0
    for i in range(n_people):
        p *= (DAYS_IN_YEAR - i) / DAYS_IN_YEAR
        products.append(p)
    return products


# ── Threshold finder ─────────────────────────────────────────────

def find_threshold(target_prob: float = 0.5) -> int:
    """Find smallest *n* where P(collision) ≥ *target_prob*.

    Parameters
    ----------
    target_prob:
        Target probability (default 0.5 → the classic "23 people" answer).

    Returns
    -------
    int
        Smallest n such that ``exact_probability(n) >= target_prob``.
    """
    for n in range(2, DAYS_IN_YEAR + 2):
        if exact_probability(n) >= target_prob:
            return n
    return DAYS_IN_YEAR + 1  # pigeonhole guarantee


# ── Notable thresholds ───────────────────────────────────────────

THRESHOLD_50 = find_threshold(0.50)   # 23
THRESHOLD_97 = find_threshold(0.97)   # ~50
THRESHOLD_999 = find_threshold(0.999) # ~70
