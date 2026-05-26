"""Birthday Paradox module."""

from .screen import BirthdayScreen

from gametheorist.modules.registry import ModuleMeta, register

register(
    ModuleMeta(
        id="birthday",
        num="03",
        icon="🎂",
        title="The Birthday Paradox Lab",
        subtitle="Probability + Simulation Thinking",
        desc="23 people. Two share a birthday. Your gut says impossible.",
        difficulty="⚡⚡",
        topics="Combinatorics • Monte Carlo • Intuition Calibration",
        available=True,
        screen_loader=lambda: BirthdayScreen,
    )
)
