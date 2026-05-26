"""Gambler's Ruin — pure simulation & exact math engine.

Classic random walk with two absorbing barriers at 0 and N.

Teaches: variance, absorption, expected duration, why "fair" games
can still be brutal when one side has finite capital.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np


# ── Data classes ────────────────────────────────────────────────


@dataclass(slots=True)
class WalkResult:
    """Result of one complete random walk until absorption."""

    positions: list[int]   # full path, including starting capital
    steps: int             # number of steps taken until absorption
    ended_at_zero: bool    # True = gambler ruined, False = reached total (opponent ruined)
    final_capital: int


@dataclass(slots=True)
class BatchRuinStats:
    """Summary statistics from many independent walks."""

    n_trials: int
    start: int
    total: int
    p: float
    ruined: int                 # number of trials that hit 0
    ruin_rate: float
    reached_total: int
    avg_duration: float
    median_duration: float
    min_duration: int
    max_duration: int


# ── Exact formulas (no simulation) ─────────────────────────────


def exact_ruin_probability(start: int, total: int, p: float) -> float:
    """Exact probability that the gambler is ruined (hits 0 before total).

    Parameters
    ----------
    start : int   Starting capital for the gambler (1 .. total-1)
    total : int   Total capital in the game (gambler + opponent)
    p     : float Probability of +1 on each step (0 < p < 1)

    Returns
    -------
    float  Probability of eventual ruin for the gambler.
    """
    if not 0 < start < total:
        raise ValueError(f"start must be in (0, {total})")
    if not 0.0 < p < 1.0:
        raise ValueError("p must be in (0, 1)")

    if abs(p - 0.5) < 1e-12:
        # Fair game: simple linear formula
        return (total - start) / total

    # Biased case
    r = (1.0 - p) / p
    if abs(r - 1.0) < 1e-12:
        return (total - start) / total

    num = r**start - r**total
    den = 1.0 - r**total
    return num / den


def exact_reach_total_probability(start: int, total: int, p: float) -> float:
    """Probability the gambler reaches total capital before 0."""
    return 1.0 - exact_ruin_probability(start, total, p)


def exact_expected_duration(start: int, total: int, p: float) -> float:
    """Expected number of steps until absorption.

    Closed form for both fair and biased cases.
    """
    if not 0 < start < total:
        raise ValueError(f"start must be in (0, {total})")
    if not 0.0 < p < 1.0:
        raise ValueError("p must be in (0, 1)")

    if abs(p - 0.5) < 1e-12:
        # Fair game
        return float(start * (total - start))

    r = (1.0 - p) / p
    if abs(r - 1.0) < 1e-12:
        return float(start * (total - start))

    # Standard formula
    term1 = start / (1.0 - 2.0 * p)
    term2 = (total / (1.0 - 2.0 * p)) * (1.0 - r**start) / (1.0 - r**total)
    return term1 - term2


# ── Simulation (single walk, for live animation) ───────────────


def simulate_walk(
    start: int,
    total: int,
    p: float = 0.5,
    max_steps: int = 200_000,
    rng: np.random.Generator | None = None,
) -> WalkResult:
    """Simulate one gambler until absorption at 0 or total.

    Returns the full path so the UI can animate it beautifully.
    """
    if not 0 < start < total:
        raise ValueError(f"start must be in (0, {total})")
    if not 0.0 <= p <= 1.0:
        raise ValueError("p must be in [0, 1]")

    if rng is None:
        rng = np.random.default_rng()

    pos = start
    positions: list[int] = [pos]

    for step in range(1, max_steps + 1):
        if rng.random() < p:
            pos += 1
        else:
            pos -= 1

        positions.append(pos)

        if pos == 0 or pos == total:
            return WalkResult(
                positions=positions,
                steps=step,
                ended_at_zero=(pos == 0),
                final_capital=pos,
            )

    # Safety: did not absorb (extremely unlikely with max_steps)
    return WalkResult(
        positions=positions,
        steps=max_steps,
        ended_at_zero=False,
        final_capital=pos,
    )


# ── Batch simulation (fast, vectorized where possible) ─────────


def simulate_batch(
    n_trials: int,
    start: int,
    total: int,
    p: float = 0.5,
    max_steps: int = 200_000,
) -> list[WalkResult]:
    """Run many independent walks. Returns full results for analysis."""
    rng = np.random.default_rng()
    results: list[WalkResult] = []

    for _ in range(n_trials):
        res = simulate_walk(start, total, p, max_steps, rng=rng)
        results.append(res)

    return results


def batch_ruin_stats(
    n_trials: int,
    start: int,
    total: int,
    p: float = 0.5,
    max_steps: int = 200_000,
) -> BatchRuinStats:
    """Fast summary statistics without storing every full path."""
    results = simulate_batch(n_trials, start, total, p, max_steps)

    durations = [r.steps for r in results]
    ruined = sum(1 for r in results if r.ended_at_zero)

    return BatchRuinStats(
        n_trials=n_trials,
        start=start,
        total=total,
        p=p,
        ruined=ruined,
        ruin_rate=ruined / n_trials if n_trials > 0 else 0.0,
        reached_total=n_trials - ruined,
        avg_duration=float(np.mean(durations)),
        median_duration=float(np.median(durations)),
        min_duration=min(durations),
        max_duration=max(durations),
    )


# ── Sweep helpers (for the probability curve chart) ───────────


def ruin_probability_sweep(
    total: int,
    p: float,
    start_values: Sequence[int] | None = None,
) -> tuple[list[int], list[float]]:
    """Exact ruin probability for every starting capital 1..total-1."""
    if start_values is None:
        start_values = list(range(1, total))

    exact = [exact_ruin_probability(s, total, p) for s in start_values]
    return list(start_values), exact


def simulate_ruin_rate_sweep(
    total: int,
    p: float,
    n_trials: int = 5_000,
    start_values: Sequence[int] | None = None,
) -> tuple[list[int], list[float]]:
    """Monte Carlo estimate of ruin probability across starting capitals."""
    if start_values is None:
        start_values = list(range(1, total))

    rates: list[float] = []
    for s in start_values:
        stats = batch_ruin_stats(n_trials, s, total, p)
        rates.append(stats.ruin_rate)

    return list(start_values), rates


# ── Convenience for the UI ─────────────────────────────────────


def capital_bar_data(current: int, total: int) -> tuple[int, int]:
    """Return (gambler, house) capital for a nice bar widget."""
    return current, total - current
