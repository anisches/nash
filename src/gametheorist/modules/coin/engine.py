"""Engine — pure simulation & statistics for the Coin module.

No Textual / UI imports.  Everything here is plain Python + numpy so
it can be tested and reused independently.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Literal

import numpy as np


# ── Data classes ────────────────────────────────────────────────

CoinFace = Literal["H", "T"]


@dataclass(slots=True)
class TrialResult:
    """Result of a sequence of coin flips."""

    flips: list[CoinFace]
    running_avg: list[float]
    n_heads: int
    n_tails: int

    @property
    def n_total(self) -> int:
        return self.n_heads + self.n_tails

    @property
    def heads_pct(self) -> float:
        return (self.n_heads / self.n_total * 100) if self.n_total else 0.0

    @property
    def tails_pct(self) -> float:
        return (self.n_tails / self.n_total * 100) if self.n_total else 0.0


@dataclass(slots=True)
class ZTestResult:
    """Result of a two-tailed z-test for coin fairness (H₀: p = 0.5)."""

    z_stat: float
    p_value: float
    reject_null: bool
    confidence_interval: tuple[float, float]


# ── Normal CDF (no scipy) ──────────────────────────────────────

def _normal_cdf(x: float) -> float:
    """Standard-normal CDF via the complementary error function."""
    return 0.5 * math.erfc(-x / math.sqrt(2.0))


# ── Biased coin ─────────────────────────────────────────────────

class BiasedCoin:
    """A coin with configurable probability of landing heads.

    Parameters
    ----------
    bias : float
        Probability of heads, in [0, 1].  Default 0.5 (fair coin).
    """

    def __init__(self, bias: float = 0.5) -> None:
        if not 0.0 <= bias <= 1.0:
            raise ValueError(f"bias must be in [0, 1], got {bias}")
        self._bias = bias
        self._rng = np.random.default_rng()

    # ── properties ──────────────────────────────────────────────

    @property
    def bias(self) -> float:
        return self._bias

    @bias.setter
    def bias(self, value: float) -> None:
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"bias must be in [0, 1], got {value}")
        self._bias = value

    # ── single flip ─────────────────────────────────────────────

    def flip(self) -> CoinFace:
        """Flip the coin once, returning ``'H'`` or ``'T'``."""
        return "H" if self._rng.random() < self._bias else "T"

    # ── batch flip (numpy-vectorised) ───────────────────────────

    def flip_many(self, n: int) -> list[CoinFace]:
        """Flip *n* times using a single numpy draw for speed."""
        draws = self._rng.random(n) < self._bias
        return ["H" if h else "T" for h in draws]


# ── Trial runner ────────────────────────────────────────────────

def run_trial(coin: BiasedCoin, n_flips: int) -> TrialResult:
    """Run *n_flips* flips and compute running proportion of heads.

    Returns a :class:`TrialResult` capturing the full flip sequence,
    running average, and summary counts.
    """
    flips = coin.flip_many(n_flips)

    # Running cumulative average via numpy for speed
    heads_mask = np.array([1.0 if f == "H" else 0.0 for f in flips])
    cumulative = np.cumsum(heads_mask)
    indices = np.arange(1, n_flips + 1, dtype=float)
    running_avg = (cumulative / indices).tolist()

    n_heads = int(cumulative[-1]) if n_flips else 0
    n_tails = n_flips - n_heads

    return TrialResult(
        flips=flips,
        running_avg=running_avg,
        n_heads=n_heads,
        n_tails=n_tails,
    )


def run_trial_incremental(
    coin: BiasedCoin,
    n_flips: int,
    prev_heads: int = 0,
    prev_total: int = 0,
) -> TrialResult:
    """Run *n_flips* additional flips, continuing from a previous state.

    Running averages start from the cumulative counts of the prior run
    so the chart shows the full history.
    """
    flips = coin.flip_many(n_flips)

    running_avg: list[float] = []
    heads = prev_heads
    total = prev_total
    for f in flips:
        if f == "H":
            heads += 1
        total += 1
        running_avg.append(heads / total)

    new_heads = sum(1 for f in flips if f == "H")
    return TrialResult(
        flips=flips,
        running_avg=running_avg,
        n_heads=new_heads,
        n_tails=n_flips - new_heads,
    )


# ── Hypothesis test ─────────────────────────────────────────────

def z_test_fair(
    n_heads: int,
    n_total: int,
    alpha: float = 0.05,
) -> ZTestResult:
    """Two-tailed z-test for H₀: p = 0.5.

    Parameters
    ----------
    n_heads : int   Number of heads observed.
    n_total : int   Total number of flips.
    alpha   : float Significance level (default 0.05).

    Returns
    -------
    ZTestResult  with z-statistic, p-value, rejection decision, and
                 95 % Wald confidence interval for the true proportion.
    """
    if n_total == 0:
        return ZTestResult(
            z_stat=0.0,
            p_value=1.0,
            reject_null=False,
            confidence_interval=(0.0, 1.0),
        )

    p_hat = n_heads / n_total
    p_0 = 0.5
    se_test = math.sqrt(p_0 * (1 - p_0) / n_total)

    z = (p_hat - p_0) / se_test if se_test > 0 else 0.0
    p_value = 2.0 * (1.0 - _normal_cdf(abs(z)))

    # 95 % Wald CI using observed proportion SE
    z_crit = 1.959964  # norm.ppf(0.975)
    se_ci = math.sqrt(p_hat * (1 - p_hat) / n_total) if n_total > 0 else 0.0
    ci_low = max(0.0, p_hat - z_crit * se_ci)
    ci_high = min(1.0, p_hat + z_crit * se_ci)

    return ZTestResult(
        z_stat=z,
        p_value=p_value,
        reject_null=p_value < alpha,
        confidence_interval=(ci_low, ci_high),
    )
