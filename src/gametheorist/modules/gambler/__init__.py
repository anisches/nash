"""Gambler's Ruin module."""

from .screen import GamblerScreen

from gametheorist.modules.registry import ModuleMeta, register

register(
    ModuleMeta(
        id="gambler",
        num="07",
        icon="💸",
        title="The Gambler's Ruin",
        subtitle="Variance • Absorption • Fair Games Are Brutal",
        desc="You start with $50. The house has $50. Fair coin flips. How long until you're broke?",
        difficulty="⚡⚡",
        topics="Random Walks • Ruin Probability • Martingales • Expected Duration",
        available=True,
        screen_loader=lambda: GamblerScreen,
    )
)
