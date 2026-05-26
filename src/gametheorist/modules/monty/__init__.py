"""Monty Hall module."""

from .screen import MontyScreen

from gametheorist.modules.registry import ModuleMeta, register

register(
    ModuleMeta(
        id="monty",
        num="02",
        icon="🚪",
        title="The Monty Hall Arena",
        subtitle="Probability + Intuition-Breaking",
        desc="Goats, cars, and the door you didn't pick. Should you switch?",
        difficulty="⚡⚡",
        topics="Conditional Probability • Bayes' Theorem • Simulation",
        available=True,
        screen_loader=lambda: MontyScreen,
    )
)
