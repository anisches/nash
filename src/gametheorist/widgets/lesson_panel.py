"""Lesson panel — collapsible 'What You Learned' overlay."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Button, Markdown, Static
from textual.widget import Widget
from textual.reactive import reactive


class LessonPanel(Widget):
    """A collapsible panel that displays educational content after key moments."""

    DEFAULT_CSS = """
    LessonPanel {
        dock: bottom;
        width: 100%;
        max-height: 60%;
        display: none;
        layer: overlay;
    }

    LessonPanel.visible {
        display: block;
    }

    LessonPanel .lesson-container {
        background: #111827;
        border: tall #00e5ff;
        padding: 1 2;
        margin: 0 1;
    }

    LessonPanel .lesson-title {
        color: #00e5ff;
        text-style: bold;
        padding: 0 0 1 0;
    }

    LessonPanel .lesson-body {
        padding: 0 1;
        max-height: 20;
        overflow-y: auto;
    }

    LessonPanel .lesson-dismiss {
        dock: bottom;
        width: auto;
        margin: 1 0 0 0;
        min-width: 16;
    }
    """

    is_visible = reactive(False)

    def __init__(
        self,
        title: str = "💡 What You Just Learned",
        content: str = "",
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._title_text = title
        self._content_text = content

    def compose(self) -> ComposeResult:
        with Vertical(classes="lesson-container"):
            yield Static(self._title_text, classes="lesson-title")
            yield Markdown(self._content_text, classes="lesson-body")
            yield Button("✓  Got it!", variant="success", classes="lesson-dismiss")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Dismiss the panel."""
        self.hide()
        event.stop()

    def show(self, content: str | None = None, title: str | None = None) -> None:
        """Show the lesson panel, optionally updating content."""
        if content is not None:
            self.query_one(".lesson-body", Markdown).update(content)
        if title is not None:
            self.query_one(".lesson-title", Static).update(title)
        self.add_class("visible")
        self.is_visible = True

    def hide(self) -> None:
        """Hide the lesson panel."""
        self.remove_class("visible")
        self.is_visible = False
