"""About screen — how to use the app."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, Header, Footer, Markdown
from textual.containers import Vertical, ScrollableContainer


ABOUT_CONTENT = """\
# 🎮 Game Theorist — About

## The Big Idea

**Probability** is the foundation — *what's likely?*
**Statistics** builds on it — *what does the data say?*
**Game Theory** uses both — *what should I do when others are also deciding?*

We bounce between them so it stays fun, not a slog through prerequisites.

---

## How To Play

Each module is a **build-and-tinker session**. You don't read about concepts —
you *discover* them by playing.

| Key | Action |
|-----|--------|
| `↑ ↓ ← →` | Navigate |
| `Enter` | Select / Confirm |
| `Space` | Primary action (flip, pick, simulate) |
| `Escape` | Go back |
| `h` | Return to home |
| `q` | Quit |
| `?` | Show help |

---

## Modules

1. **🪙 The Coin That Lies** — Flip a biased coin. Discover the law of large numbers.
2. **🚪 The Monty Hall Arena** — Goats, cars, conditional probability.
3. **🎂 The Birthday Paradox Lab** — Why 23 people is enough.
4. **⛓️  Prisoner's Dilemma** — Design a strategy. Compete. *(coming soon)*
5. **🗳️  Election Polling** — Be a pollster. See how wrong you can be. *(coming soon)*
6. **🃏 Poker Showdown** — Odds, bluffs, Nash equilibrium. *(coming soon)*

---

*Press Escape to go back.*
"""


class AboutScreen(Screen):
    """Information screen explaining how to use the app."""

    BINDINGS = [
        ("escape", "go_back", "Back"),
        ("q", "quit", "Quit"),
    ]

    DEFAULT_CSS = """
    AboutScreen {
        background: #0a0e17;
    }

    AboutScreen #about-container {
        width: 100%;
        max-width: 100;
        margin: 0 auto;
        padding: 1 4;
        height: 100%;
        overflow-y: auto;
    }

    AboutScreen Markdown {
        margin: 1 0;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with ScrollableContainer(id="about-container"):
            yield Markdown(ABOUT_CONTENT)
        yield Footer()

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def action_quit(self) -> None:
        self.app.exit()
