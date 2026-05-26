"""Coin module."""

from .screen import CoinScreen

from gametheorist.modules.registry import ModuleMeta, register

register(
    ModuleMeta(
        id="coin",
        num="01",
        icon="🪙",
        title="The Coin That Lies",
        subtitle="Probability Foundations",
        desc="Flip a biased coin. How many flips until you're sure it's rigged?",
        difficulty="⚡",
        topics="Law of Large Numbers • Z-Test • Confidence Intervals",
        available=True,
        screen_loader=lambda: CoinScreen,
    )
)
