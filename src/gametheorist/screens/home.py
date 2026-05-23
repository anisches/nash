"""Home screen — module selector with cards."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, Grid
from textual.screen import Screen
from textual.widgets import Static, Header, Footer, Button
from textual.widget import Widget


MODULE_CARDS = [
    {
        "id": "coin",
        "num": "01",
        "icon": "🪙",
        "title": "The Coin That Lies",
        "subtitle": "Probability Foundations",
        "desc": "Flip a biased coin. How many flips until you're sure it's rigged?",
        "difficulty": "⚡",
        "topics": "Law of Large Numbers • Z-Test • Confidence Intervals",
        "available": True,
    },
    {
        "id": "monty",
        "num": "02",
        "icon": "🚪",
        "title": "The Monty Hall Arena",
        "subtitle": "Probability + Intuition-Breaking",
        "desc": "Goats, cars, and the door you didn't pick. Should you switch?",
        "difficulty": "⚡⚡",
        "topics": "Conditional Probability • Bayes' Theorem • Simulation",
        "available": True,
    },
    {
        "id": "birthday",
        "num": "03",
        "icon": "🎂",
        "title": "The Birthday Paradox Lab",
        "subtitle": "Probability + Simulation Thinking",
        "desc": "23 people. Two share a birthday. Your gut says impossible.",
        "difficulty": "⚡⚡",
        "topics": "Combinatorics • Monte Carlo • Intuition Calibration",
        "available": True,
    },
    {
        "id": "prisoner",
        "num": "04",
        "icon": "⛓️",
        "title": "Prisoner's Dilemma Tournament",
        "subtitle": "Game Theory Entry",
        "desc": "Design a strategy. Compete against the classics. Why does cooperation win?",
        "difficulty": "⚡⚡⚡",
        "topics": "Nash Equilibrium • Iterated Games • Evolutionary Strategy",
        "available": False,
    },
    {
        "id": "polling",
        "num": "05",
        "icon": "🗳️",
        "title": "Election Polling Simulator",
        "subtitle": "Statistics, Real-World",
        "desc": "You're a pollster. Sample voters. How wrong can you be?",
        "difficulty": "⚡⚡⚡",
        "topics": "Sampling • CLT • Margin of Error • Bias vs Variance",
        "available": False,
    },
    {
        "id": "poker",
        "num": "06",
        "icon": "🃏",
        "title": "Poker Hand Showdown",
        "subtitle": "Probability + Game Theory Finale",
        "desc": "Calculate odds, then bluff. When should you bet with nothing?",
        "difficulty": "🔥🔥🔥",
        "topics": "Expected Value • Pot Odds • Nash Equilibrium • Bluffing",
        "available": False,
    },
]


class ModuleCard(Widget):
    """A single module card in the home screen grid."""

    DEFAULT_CSS = """
    ModuleCard {
        width: 1fr;
        height: auto;
        min-height: 11;
        background: #1a2332;
        border: round #2a3a4f;
        padding: 1 2;
        margin: 0 1 1 0;
    }

    ModuleCard:hover {
        border: round #00e5ff;
        background: #1e3a5f;
    }

    ModuleCard.locked {
        opacity: 50%;
    }

    ModuleCard.locked:hover {
        border: round #64748b;
        background: #1a2332;
    }

    ModuleCard .card-header {
        height: 1;
        color: #64748b;
    }

    ModuleCard .card-title {
        color: #e2e8f0;
        text-style: bold;
        padding: 0 0 0 0;
    }

    ModuleCard .card-subtitle {
        color: #00e5ff;
        text-style: italic;
    }

    ModuleCard .card-desc {
        color: #94a3b8;
        padding: 1 0 0 0;
    }

    ModuleCard .card-topics {
        color: #64748b;
        padding: 1 0 0 0;
    }

    ModuleCard .card-footer {
        height: 1;
        padding: 1 0 0 0;
    }
    """

    def __init__(self, card_data: dict, **kwargs) -> None:
        super().__init__(**kwargs)
        self.card_data = card_data
        if not card_data["available"]:
            self.add_class("locked")

    def compose(self) -> ComposeResult:
        d = self.card_data
        lock = "" if d["available"] else " 🔒"
        yield Static(
            f"[bold #64748b]MODULE {d['num']}[/]  {d['difficulty']}{lock}",
            classes="card-header",
        )
        yield Static(f"{d['icon']}  {d['title']}", classes="card-title")
        yield Static(d["subtitle"], classes="card-subtitle")
        yield Static(d["desc"], classes="card-desc")
        yield Static(f"[dim]{d['topics']}[/]", classes="card-topics")

    def on_click(self) -> None:
        if self.card_data["available"]:
            self.app.push_screen(self.card_data["id"])


TITLE_ART = r"""[bold #00e5ff]
  ╔══════════════════════════════════════════════════════════════╗
  ║   ▄▀▀▀▀▄  ▄▀▀█▄▄▄▄  ▄▀▀▄▀▀▀▄  ▄▀▀█▄▄▄▄  ▄▀▀▀█▀▀▄  ▄▀▀▄▀▀▀▄  ▄▀▀▄ ▀▀▄   ║
  ║  █        ▐  ▄▀   ▐ █   █   █ ▐  ▄▀   ▐ █    █  ▐ █   █   █ █   ▀▄ ▄▀   ║
  ║  █    ▀▄▄   █▄▄▄▄▄  ▐  █▀▀█▀    █▄▄▄▄▄  ▐   █    ▐  █▀▀█▀  ▐     █      ║
  ║  ▀▄▄▄▄▀    █    ▌    ▄▀    █    █    ▌     █      ▄▀    █       ▄▀         ║
  ║            ▐           █         ▐        ▐      █            ▄▀           ║
  ╚══════════════════════════════════════════════════════════════╝
[/][bold #ff00e5]          ─── Game Theory • Probability • Statistics ───[/]
"""

SUBTITLE = (
    "[#94a3b8]Learn by playing. Break your intuition. Build it back stronger.[/]\n"
    "[#64748b]Select a module below to begin  •  Arrow keys + Enter  •  q to quit[/]"
)


class HomeScreen(Screen):
    """Main landing screen with module selection cards."""

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("question_mark", "about", "About"),
    ]

    DEFAULT_CSS = """
    HomeScreen {
        background: #0a0e17;
        align: center top;
    }

    HomeScreen #title-art {
        width: 100%;
        content-align: center top;
        padding: 1 0 0 0;
        height: auto;
    }

    HomeScreen #subtitle {
        width: 100%;
        content-align: center middle;
        text-align: center;
        padding: 0 0 1 0;
        height: auto;
    }

    HomeScreen #card-grid {
        width: 100%;
        max-width: 140;
        grid-size: 2;
        grid-gutter: 0;
        padding: 0 2;
        height: auto;
    }

    HomeScreen #footer-hint {
        dock: bottom;
        width: 100%;
        height: 1;
        background: #111827;
        color: #64748b;
        content-align: center middle;
        text-align: center;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static(TITLE_ART, id="title-art")
        yield Static(SUBTITLE, id="subtitle")
        with Grid(id="card-grid"):
            for card_data in MODULE_CARDS:
                yield ModuleCard(card_data, id=f"card-{card_data['id']}")
        yield Static(
            "[#64748b]  🪙 Coin  │  🚪 Monty  │  🎂 Birthday  │  "
            "⛓️  Prisoner [dim](soon)[/]  │  🗳️  Polling [dim](soon)[/]  │  "
            "🃏 Poker [dim](soon)[/]  [/]",
            id="footer-hint",
        )
        yield Footer()

    def action_about(self) -> None:
        """Show the about screen."""
        self.app.push_screen("about")

    def action_quit(self) -> None:
        self.app.exit()
