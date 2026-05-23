"""Chart wrapper — consistent styled plotext charts."""

from __future__ import annotations

from typing import Sequence

from textual_plotext import PlotextPlot


class ThemedChart(PlotextPlot):
    """A PlotextPlot with consistent dark-theme styling."""

    DEFAULT_CSS = """
    ThemedChart {
        width: 100%;
        height: 100%;
        background: #1e293b;
        border: round #334155;
        padding: 0;
    }
    """

    # Clean modern color palette (Slate / Pastel theme)
    COLORS = {
        "cyan": (56, 189, 248),    # Sky Blue
        "magenta": (251, 113, 133), # Soft Rose
        "amber": (251, 191, 36),    # Soft Amber
        "lime": (74, 222, 128),     # Soft Green
        "coral": (248, 113, 113),   # Soft Coral
        "blue": (96, 165, 250),     # Soft Blue
    }

    def setup(self) -> None:
        """Apply theme defaults to the plot."""
        self.plt.theme("dark")
        self.plt.canvas_color((30, 41, 59))  # slate-800
        self.plt.axes_color((15, 23, 42))    # slate-900
        self.plt.ticks_color((148, 163, 184)) # slate-400

    def line(
        self,
        x: Sequence[float],
        y: Sequence[float],
        label: str = "",
        color: str = "cyan",
    ) -> None:
        """Add a line plot with themed color."""
        self.setup()
        c = self.COLORS.get(color, self.COLORS["cyan"])
        self.plt.plot(list(x), list(y), label=label, color=c)

    def bar(
        self,
        labels: Sequence[str],
        values: Sequence[float],
        color: str = "cyan",
    ) -> None:
        """Add a bar chart with themed color."""
        self.setup()
        c = self.COLORS.get(color, self.COLORS["cyan"])
        self.plt.bar(list(labels), list(values), color=c)

    def histogram(
        self,
        data: Sequence[float],
        bins: int = 30,
        color: str = "cyan",
    ) -> None:
        """Add a histogram with themed color."""
        self.setup()
        c = self.COLORS.get(color, self.COLORS["cyan"])
        self.plt.hist(list(data), bins=bins, color=c)

    def redraw(self) -> None:
        """Clear and prepare for new drawing."""
        self.plt.clear_figure()
        self.setup()

    def refresh_plot(self) -> None:
        """Force a re-render of the plot widget."""
        self.refresh()
