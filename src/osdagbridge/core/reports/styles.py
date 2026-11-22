"""Centralized report styling and chart configuration for OsdagBridge reports.

This module unifies document geometry, LaTeX colors, table spacing,
typography, and matplotlib chart styling rules across all report chapters.
"""

from typing import Dict, Any, Optional

# =============================================================================
# Document Geometry & Page Margins
# =============================================================================
PAGE_SIZE = "a4paper"
MARGIN_INCHES = 1.0
HEAD_HEIGHT_PT = 15
FOOT_SKIP_PT = 25
GEOMETRY_OPTIONS = (
    f"{PAGE_SIZE}, margin={MARGIN_INCHES}in, "
    f"headheight={HEAD_HEIGHT_PT}pt, footskip={FOOT_SKIP_PT}pt"
)

# =============================================================================
# Color Palette
# =============================================================================
# Primary brand & status colors
OSDAG_GREEN_HEX = "#91B014"
OSDAG_GREEN_LATEX = "91B014"

PASS_GREEN_HEX = "#2E7D32"
FAIL_RED_HEX = "#D32F2F"
WARNING_AMBER_HEX = "#F57C00"
THRESHOLD_RED_HEX = "#C62828"

# Structural component & material colors
GIRDER_BLUE_HEX = "#1565C0"
DECK_GREEN_HEX = "#2E7D32"
BRACING_PURPLE_HEX = "#6A1B9A"
DIAPHRAGM_TEAL_HEX = "#00695C"

STEEL_BLUE_HEX = "#1976D2"
CONCRETE_GRAY_HEX = "#607D8B"
REBAR_ORANGE_HEX = "#E65100"

# Neutral / background colors
GRID_GRAY_HEX = "#E0E0E0"
TEXT_DARK_HEX = "#212121"
BACKGROUND_LIGHT_HEX = "#FAFAFA"

COLORS: Dict[str, str] = {
    "brand": OSDAG_GREEN_HEX,
    "pass": PASS_GREEN_HEX,
    "fail": FAIL_RED_HEX,
    "warning": WARNING_AMBER_HEX,
    "threshold": THRESHOLD_RED_HEX,
    "girder": GIRDER_BLUE_HEX,
    "deck": DECK_GREEN_HEX,
    "bracing": BRACING_PURPLE_HEX,
    "diaphragm": DIAPHRAGM_TEAL_HEX,
    "steel": STEEL_BLUE_HEX,
    "concrete": CONCRETE_GRAY_HEX,
    "rebar": REBAR_ORANGE_HEX,
    "grid": GRID_GRAY_HEX,
    "text": TEXT_DARK_HEX,
}

# =============================================================================
# Table Formatting Specifications
# =============================================================================
TABCOLSEP_DEFAULT_PT = 5.0
TABCOLSEP_COMPACT_PT = 2.5
ARRAY_STRETCH = 1.15
ARRAY_RULE_WIDTH_PT = 0.5
EXTRA_ROW_HEIGHT_PT = 0.6
LT_PRE_PT = 4.0
LT_POST_PT = 8.0
INTEXT_SEP_PT = 8.0
TEXTFLOAT_SEP_PT = 10.0

NEEDSPACE_TABLE_LINES = 6
NEEDSPACE_LONGTABLE_LINES = 8

TABLE_STYLE: Dict[str, Any] = {
    "tabcolsep": TABCOLSEP_DEFAULT_PT,
    "tabcolsep_compact": TABCOLSEP_COMPACT_PT,
    "arraystretch": ARRAY_STRETCH,
    "arrayrulewidth": ARRAY_RULE_WIDTH_PT,
    "extrarowheight": EXTRA_ROW_HEIGHT_PT,
    "lt_pre": LT_PRE_PT,
    "lt_post": LT_POST_PT,
    "needspace_table": NEEDSPACE_TABLE_LINES,
    "needspace_longtable": NEEDSPACE_LONGTABLE_LINES,
}

# =============================================================================
# Chart Typography & Figure Dimensions
# =============================================================================
CHART_DPI = 300
CHART_FIGSIZE_STANDARD = (7.5, 3.8)
CHART_FIGSIZE_TALL = (7.5, 4.4)
CHART_FIGSIZE_SPLIT = (8.5, 4.2)

FONT_FAMILY = "sans-serif"
FONT_SIZES: Dict[str, float] = {
    "title": 11.5,
    "axis_label": 9.5,
    "tick_label": 8.5,
    "bar_label": 8.0,
    "legend": 8.5,
}


def setup_matplotlib_style() -> None:
    """Configure matplotlib with headless and non-interactive publication styling."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        plt.rcParams.update({
            "font.family": FONT_FAMILY,
            "font.size": FONT_SIZES["tick_label"],
            "axes.titlesize": FONT_SIZES["title"],
            "axes.titleweight": "bold",
            "axes.labelsize": FONT_SIZES["axis_label"],
            "axes.labelweight": "medium",
            "xtick.labelsize": FONT_SIZES["tick_label"],
            "ytick.labelsize": FONT_SIZES["tick_label"],
            "legend.fontsize": FONT_SIZES["legend"],
            "figure.titlesize": FONT_SIZES["title"],
            "figure.dpi": CHART_DPI,
            "savefig.dpi": CHART_DPI,
            "savefig.bbox": "tight",
            "axes.grid": True,
            "grid.color": GRID_GRAY_HEX,
            "grid.linestyle": "--",
            "grid.linewidth": 0.6,
            "grid.alpha": 0.7,
            "axes.axisbelow": True,
            "axes.edgecolor": "#CCCCCC",
            "axes.linewidth": 0.8,
        })
    except ImportError:
        pass


def apply_chart_styling(
    ax: Any,
    title: Optional[str] = None,
    xlabel: Optional[str] = None,
    ylabel: Optional[str] = None,
    y_threshold: Optional[float] = 1.0,
    threshold_label: str = "Limit (UR = 1.0)",
) -> None:
    """Apply uniform engineering chart styling to a matplotlib Axes object."""
    if title:
        ax.set_title(title, pad=12, fontsize=FONT_SIZES["title"], color=TEXT_DARK_HEX)
    if xlabel:
        ax.set_xlabel(xlabel, labelpad=8, fontsize=FONT_SIZES["axis_label"], color=TEXT_DARK_HEX)
    if ylabel:
        ax.set_ylabel(ylabel, labelpad=8, fontsize=FONT_SIZES["axis_label"], color=TEXT_DARK_HEX)

    # Spine cleanup
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#888888")
    ax.spines["bottom"].set_color("#888888")

    # Add red dashed threshold line for Utilization Ratio
    if y_threshold is not None:
        ax.axhline(
            y=y_threshold,
            color=THRESHOLD_RED_HEX,
            linestyle="--",
            linewidth=1.2,
            label=threshold_label,
            zorder=4,
        )
