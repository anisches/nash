"""Game Theorist — Main application."""

from __future__ import annotations

from pathlib import Path

from textual.app import App

from gametheorist.screens.home import HomeScreen
from gametheorist.screens.about import AboutScreen
from gametheorist.modules.registry import get_screens


CSS_PATH = Path(__file__).parent / "css" / "app.tcss"


class GameTheoristApp(App):
    """Interactive CLI app for learning probability, statistics & game theory."""

    TITLE = "Game Theorist"
    SUB_TITLE = "Probability • Statistics • Game Theory"
    CSS_PATH = CSS_PATH

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("h", "home", "Home"),
        ("question_mark", "about", "About"),
    ]

    SCREENS = {
        "home": HomeScreen,
        "about": AboutScreen,
        **get_screens(),
    }

    def on_mount(self) -> None:
        self.push_screen("home")

    def action_home(self) -> None:
        """Return to the home screen."""
        # Pop all screens back to root, then push home
        while len(self.screen_stack) > 1:
            self.pop_screen()

    def action_about(self) -> None:
        self.push_screen("about")

    def action_quit(self) -> None:
        self.exit()


def main() -> None:
    """Entry point for the gmetry CLI command."""
    app = GameTheoristApp()
    app.run()


if __name__ == "__main__":
    main()
