"""CSE Verification and Diagnostic Visualization Package."""

from __future__ import annotations

from cse.viz.plot_utils import (
    COLOR_ACCENT,
    COLOR_DOWN,
    COLOR_NEUTRAL,
    COLOR_UP,
    annotate_stats,
    placeholder_png,
    plot_bar,
    plot_box_by_category,
    plot_heatmap,
    plot_histogram,
    plot_scatter,
    plot_timeseries,
    save_fig,
    setup_style,
)

__all__ = [
    "COLOR_UP",
    "COLOR_DOWN",
    "COLOR_NEUTRAL",
    "COLOR_ACCENT",
    "setup_style",
    "save_fig",
    "annotate_stats",
    "placeholder_png",
    "plot_histogram",
    "plot_timeseries",
    "plot_box_by_category",
    "plot_scatter",
    "plot_heatmap",
    "plot_bar",
]
