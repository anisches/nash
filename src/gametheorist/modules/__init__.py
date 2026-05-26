"""Modules package.

This is the single place that declares what modules exist.
Real modules register themselves when imported. Planned/locked modules
are registered here with available=False until they are implemented.
"""

# Real, implemented modules (import triggers self-registration via registry)
from . import coin      # noqa: F401
from . import monty     # noqa: F401
from . import birthday  # noqa: F401
from . import gambler   # noqa: F401   # NEW — The Gambler's Ruin (module 07)

# ── Planned / locked modules (shown on home grid but not yet playable) ──
# When you implement one, move the registration into its own package
# (e.g. modules/prisoner/__init__.py) and import it above instead.

from gametheorist.modules.registry import ModuleMeta, register

# Prisoner is now a real module (registered inside its own __init__.py)

register(
    ModuleMeta(
        id="polling",
        num="05",
        icon="🗳️",
        title="Election Polling Simulator",
        subtitle="Statistics, Real-World",
        desc="You're a pollster. Sample voters. How wrong can you be?",
        difficulty="⚡⚡⚡",
        topics="Sampling • CLT • Margin of Error • Bias vs Variance",
        available=False,
        screen_loader=None,
    )
)

register(
    ModuleMeta(
        id="poker",
        num="06",
        icon="🃏",
        title="Poker Hand Showdown",
        subtitle="Probability + Game Theory Finale",
        desc="Calculate odds, then bluff. When should you bet with nothing?",
        difficulty="🔥🔥🔥",
        topics="Expected Value • Pot Odds • Nash Equilibrium • Bluffing",
        available=False,
        screen_loader=None,
    )
)

