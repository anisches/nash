"""Prisoner's Dilemma module."""

from .screen import PrisonerScreen

from gametheorist.modules.registry import ModuleMeta, register

register(
    ModuleMeta(
        id="prisoner",
        num="04",
        icon="⛓️",
        title="Prisoner's Dilemma Tournament",
        subtitle="Game Theory Entry",
        desc="Design a strategy. Compete against the classics. Why does cooperation win?",
        difficulty="⚡⚡⚡",
        topics="Nash Equilibrium • Iterated Games • Evolutionary Strategy",
        available=True,
        screen_loader=lambda: PrisonerScreen,
    )
)
