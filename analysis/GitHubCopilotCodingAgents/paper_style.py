"""Paper-figure plotting style — shared utilities.

Enforces the house style from skill.md: Times New Roman, compact figure sizes,
inward ticks, hidden spines, PDF vector export.  Every plot module under
plot_template/ should call ``setup_style()`` once at import time, then use
``save_fig()`` to export.
"""

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

# ---------------------------------------------------------------------------
# 1. Global style setup
# ---------------------------------------------------------------------------

FONT_SIZE = 8
TICK_SIZE = 6
LEGEND_SIZE = 6

def setup_style():
    """Set global rcParams to match the paper house style."""
    plt.rcParams.update({
        "font.family": "Times New Roman",
        "font.size": FONT_SIZE,
        "pdf.fonttype": 42,              # editable text in Illustrator
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.labelsize": FONT_SIZE,
        "xtick.labelsize": TICK_SIZE,
        "ytick.labelsize": TICK_SIZE,
        "xtick.direction": "in",
        "ytick.direction": "in",
        "xtick.major.size": 3,
        "ytick.major.size": 3,
        "legend.fontsize": LEGEND_SIZE,
        "legend.frameon": True,
        "figure.figsize": (2, 1.6),      # single-column default
        "figure.dpi": 300,
    })


# ---------------------------------------------------------------------------
# 2. Color palette — Microsoft brand colors
# ---------------------------------------------------------------------------

MS_BLUE       = "#00A4EF"   # Microsoft blue — primary
MS_GREEN      = "#7FBA00"   # Microsoft green
MS_RED        = "#F25022"   # Microsoft orange-red
MS_YELLOW     = "#FFB900"   # Microsoft yellow
MS_GRAY       = "#737373"   # Microsoft gray accent

# Aliases for method/baseline convention
OURS_COLOR       = MS_BLUE    # primary method
OURS_COLOR_DARK  = "#0078D4"  # darker blue variant (Azure blue)
BASELINE_A_COLOR = MS_RED     # baseline 1
BASELINE_B_COLOR = MS_GREEN   # baseline 2
BASELINE_C_COLOR = MS_YELLOW  # baseline 3

# ---------------------------------------------------------------------------
# Semantic colors — use these across ALL figures for consistency
# ---------------------------------------------------------------------------
COLOR_LLM       = MS_BLUE     # LLM / model calls
COLOR_TOOL      = MS_GREEN    # Tool execution
COLOR_USER_IDLE = MS_YELLOW   # User idle / inter-turn wait
COLOR_SYSTEM    = MS_GRAY     # System overhead

COLOR_CACHED    = "#7FBA00"   # Cached tokens (green = good/saved)
COLOR_UNCACHED  = "#F25022"   # Non-cached / fresh tokens (red)
COLOR_PROMPT    = "#0078D4"   # Prompt tokens (dark blue)
COLOR_COMPLETION = "#F25022"  # Completion/response tokens (red-orange)

COLOR_SUCCESS   = MS_BLUE     # Success status
COLOR_FAILURE   = MS_RED      # Failure/error status

COLOR_WEEKDAY   = MS_BLUE     # Weekday
COLOR_WEEKEND   = MS_RED      # Weekend

# Sequential blue ramp for ordered series
BLUES = ["#B4D6E4", "#69C3F7", "#00A4EF", "#0078D4", "#003B73"]

# A broader categorical palette for multi-series plots (up to 8 series)
CATEGORY_COLORS = [
    MS_BLUE, MS_GREEN, MS_RED, MS_YELLOW,
    "#0078D4", MS_GRAY, "#B4009E", "#00188F",
]

STYLE_MAP = {
    "ours":       {"color": OURS_COLOR,       "label": "Ours",       "linestyle": "-"},
    "baseline_a": {"color": BASELINE_A_COLOR, "label": "Baseline A", "linestyle": "-"},
    "baseline_b": {"color": BASELINE_B_COLOR, "label": "Baseline B", "linestyle": "-"},
    "baseline_c": {"color": BASELINE_C_COLOR, "label": "Baseline C", "linestyle": "--"},
}


# ---------------------------------------------------------------------------
# 3. Figure helpers
# ---------------------------------------------------------------------------

# Canonical sizes
SINGLE_COL = (2, 1.6)
WIDE       = (4, 1.6)
# DEPRECATED — kept as alias to prevent crashes in trend/prediction files
# that still use multi-panel subplots.  Split those into individual figures
# before removing this constant.
DOUBLE_COL = (4, 3.2)


def new_fig(figsize=None, nrows=1, ncols=1, **kwargs):
    """Create a figure + axes with canonical sizing.

    Parameters
    ----------
    figsize : tuple or None
        Override for figure size.  Defaults to SINGLE_COL for a single
        axes or WIDE for multi-column layouts.
    """
    if figsize is None:
        figsize = SINGLE_COL if ncols == 1 else WIDE
    fig, axes = plt.subplots(nrows, ncols, figsize=figsize, **kwargs)
    return fig, axes


def style_ax(ax, xlabel=None, ylabel=None, title=None,
             keep_all_spines=False, grid_y=False):
    """Apply house style to a single Axes.

    Parameters
    ----------
    keep_all_spines : bool
        If True, show all four spines (use for CDFs).
    grid_y : bool
        If True, add a light y-axis grid (dashed, alpha 0.7).
    title : str (deprecated, ignored)
        Kept for backward compatibility but no longer rendered.
    """
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=FONT_SIZE)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=FONT_SIZE)
    # title intentionally not rendered (paper figures use captions instead)
    ax.tick_params(axis="both", which="major",
                   labelsize=TICK_SIZE, direction="in", length=3)
    if keep_all_spines:
        for s in ("top", "right", "left", "bottom"):
            ax.spines[s].set_visible(True)
    else:
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
    if grid_y:
        ax.yaxis.grid(True, linestyle="--", alpha=0.7)
        ax.set_axisbelow(True)


def add_legend(ax, **kwargs):
    """Add a legend with house-style defaults."""
    defaults = dict(fontsize=LEGEND_SIZE, frameon=True)
    defaults.update(kwargs)
    ax.legend(**defaults)


# ---------------------------------------------------------------------------
# 4. Export
# ---------------------------------------------------------------------------

FIGURES_DIR = "./figures"


def save_fig(fig, name, output_dir=None, pad_inches=0.0):
    """Export figure as PDF with tight cropping.

    Parameters
    ----------
    name : str
        File name *without* extension (`.pdf` is appended).
    output_dir : str or None
        Destination directory.  Defaults to ``./figures``.
    pad_inches : float
        Padding around the tight bounding box.  A small positive value
        (e.g. 0.03) prevents long axis labels from being clipped at the crop
        boundary.
    """
    out = output_dir or FIGURES_DIR
    os.makedirs(out, exist_ok=True)
    fig.tight_layout()
    path = os.path.join(out, f"{name}.pdf")
    fig.savefig(path, format="pdf", dpi=300,
                bbox_inches="tight", pad_inches=pad_inches)
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# 5. Reusable recipe helpers
# ---------------------------------------------------------------------------

def moving_average(data, window_size=10):
    """Moving average, re-interpolated to the original length."""
    if len(data) <= window_size:
        return data
    w = np.ones(window_size) / window_size
    smoothed = np.convolve(data, w, mode="valid")
    x_orig = np.linspace(0, len(data) - 1, len(data))
    x_smooth = np.linspace(0, len(data) - 1, len(smoothed))
    return np.interp(x_orig, x_smooth, smoothed)


def human_readable_formatter():
    """Return a ticker formatter that shows 1K, 1M, 1B, 1T etc."""
    def _fmt(x, _pos):
        if abs(x) >= 1e12:
            return f"{x / 1e12:.1f}T"
        if abs(x) >= 1e9:
            return f"{x / 1e9:.1f}B"
        if abs(x) >= 1e6:
            return f"{x / 1e6:.1f}M"
        if abs(x) >= 1e3:
            return f"{x / 1e3:.0f}K"
        return f"{x:.0f}"
    return mticker.FuncFormatter(_fmt)


def cdf_arrays(values):
    """Return (sorted_values, cumulative_pct) for a CDF plot."""
    sorted_v = np.sort(values)
    cum = np.arange(1, len(sorted_v) + 1) / len(sorted_v) * 100
    return sorted_v, cum


def bar_offsets(n_methods, x_points, bar_width=0.2):
    """Compute per-method x offsets for grouped bar charts."""
    offset = (n_methods - 1) / 2
    return [[x + (idx - offset) * bar_width for x in x_points]
            for idx in range(n_methods)]


def truncate_label(name: str, max_len: int = 18) -> str:
    """Shorten a label for axis ticks — keeps start, appends '…' if cut."""
    if len(name) <= max_len:
        return name
    return name[: max_len - 1] + "…"


def truncate_labels(names, max_len: int = 18):
    """Vectorised version — works on lists, Series, Index."""
    return [truncate_label(str(n), max_len) for n in names]
