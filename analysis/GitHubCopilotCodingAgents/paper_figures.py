"""Paper figure functions — extracted verbatim from the analysis-pipeline plot
modules so the arXiv figures reproduce exactly. Each function takes a DataFrame
(or output_dir) and writes one PDF via ``paper_style.save_fig``.

Do NOT call ``paper_style.setup_style()`` before the ``generate_paper_figures``
group (they were produced with matplotlib defaults). The trends, deep-loop and
nested-bucket figures were produced *after* ``setup_style()`` — see
``make_figures.py`` for the exact ordering the paper used.
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paper_style


def _tool_rw_category(name: str) -> str:
    """Classify a tool as a 'write' (mutating/side-effecting) or 'read' operation."""
    n = str(name).lower()
    write_kw = ("create", "edit", "replace", "apply", "patch", "write", "insert",
                "delete", "remove", "rename", "move", "update", "run_", "run ",
                "build", "terminal", "execute", "command")
    return "write" if any(k in n for k in write_kw) else "read"


# Word-level abbreviations for tool names (applied per underscore-separated token)
# so x-axis tick labels stay compact and consistent across tool figures.
_TOOL_WORD_ABBREV = {
    "command": "cmd", "commands": "cmds",
    "string": "str", "strings": "strs",
    "project": "proj", "projects": "projs",
    "terminal": "term",
    "replace": "repl",
    "search": "srch",
    "symbol": "sym", "symbols": "syms",
    "error": "err", "errors": "errs",
    "progress": "prog",
    "solution": "soln",
    "function": "func", "functions": "funcs",
    "directory": "dir", "directories": "dirs",
    "reference": "ref", "references": "refs",
    "number": "num",
}


def _abbrev_tool_label(name: str) -> str:
    """Shorten a tool name by abbreviating known words (e.g. run_command_in_terminal
    -> run_cmd_in_term). Unknown tokens are left unchanged."""
    parts = str(name).split("_")
    return "_".join(_TOOL_WORD_ABBREV.get(p, p) for p in parts)


def _abbrev_tool_labels(names):
    """Vectorised ``_abbrev_tool_label`` for lists/Series/Index."""
    return [_abbrev_tool_label(n) for n in names]



def _annotate_median(ax, vals, color, y_text, ha="left"):
    """Draw a median dashed line + text annotation (not in legend) on a CDF axis."""
    med = float(np.median(vals))
    # vertical dashed line from baseline up to the curve at CDF=0.5
    ax.plot([med, med], [0, 0.5], linestyle="--", linewidth=1.0, color=color, zorder=4)
    ax.plot([med], [0.5], marker="o", markersize=4, color=color, zorder=5)
    if med >= 100:
        label = f"{med:,.0f}s"
    elif med >= 10:
        label = f"{med:.0f}s"
    else:
        label = f"{med:.1f}s"
    x_text = med * 1.6 if ha == "left" else med / 1.6
    ax.annotate(label, xy=(med, 0.5), xytext=(x_text, y_text),
                color=color, fontsize=paper_style.LEGEND_SIZE, ha=ha, va="center",
                zorder=6,
                bbox=dict(boxstyle="round,pad=0.1", facecolor="white",
                          edgecolor="none", alpha=0.85))
    return med


# Human-friendly log-axis ticks.
# Time anchors are canonical values in *seconds*; token anchors are raw counts.
_TIME_ANCHORS = [
    (1e-3, "1ms"), (1e-2, "10ms"), (1e-1, "100ms"),
    (1, "1s"), (10, "10s"),
    (60, "1min"), (600, "10min"), (3600, "1h"), (86400, "1d"),
]
_TOKEN_ANCHORS = [
    (1, "1"), (10, "10"), (100, "100"), (1e3, "1k"), (1e4, "10k"),
    (1e5, "100k"), (1e6, "1M"), (1e7, "10M"), (1e8, "100M"), (1e9, "1B"),
]
# Count anchors are raw counts (calls, turns, sessions, users per axis).
_COUNT_ANCHORS = [
    (1, "1"), (10, "10"), (100, "100"), (1e3, "1K"), (1e4, "10K"),
    (1e5, "100K"), (1e6, "1M"), (1e7, "10M"), (1e8, "100M"), (1e9, "1B"),
]
# Seconds per axis time-unit (used to map canonical anchors onto the axis).
_TIME_UNIT_SECONDS = {"ms": 1e-3, "s": 1.0, "min": 60.0, "h": 3600.0}


def _apply_log_ticks(ax, anchors, to_axis, which="x"):
    """Place human-friendly major ticks on a log x- or y-axis.

    Only anchors inside the current axis limits are shown, and the set is thinned
    (evenly, keeping endpoints) to what fits the figure extent so labels never
    overlap. Minor tick labels are suppressed so the curated labels are the only
    ones rendered.
    """
    if which == "y":
        lo, hi = ax.get_ylim()
        extent_in = ax.figure.get_size_inches()[1]
        axis = ax.yaxis
    else:
        lo, hi = ax.get_xlim()
        extent_in = ax.figure.get_size_inches()[0]
        axis = ax.xaxis
    in_range = [(to_axis(c), label) for c, label in anchors if lo <= to_axis(c) <= hi]
    if not in_range:
        return
    max_ticks = max(4, int(extent_in / 0.55))
    if len(in_range) > max_ticks:
        keep = sorted({int(round(i)) for i in np.linspace(0, len(in_range) - 1, max_ticks)})
        in_range = [in_range[i] for i in keep]
    ticks = [t for t, _ in in_range]
    labels = [label for _, label in in_range]
    axis.set_major_locator(mticker.FixedLocator(ticks))
    axis.set_major_formatter(mticker.FixedFormatter(labels))
    axis.set_minor_formatter(mticker.NullFormatter())


def _set_time_xticks(ax, axis_unit):
    """Human-friendly time ticks (1ms/1s/10s/1min/1h/...) on a log x-axis whose
    values are expressed in ``axis_unit`` (one of 'ms', 's', 'min', 'h')."""
    factor = _TIME_UNIT_SECONDS[axis_unit]
    _apply_log_ticks(ax, _TIME_ANCHORS, lambda sec: sec / factor)


def _set_token_xticks(ax):
    """Human-friendly token ticks (1/10/100/1k/.../1M) on a log x-axis of raw
    token counts."""
    _apply_log_ticks(ax, _TOKEN_ANCHORS, lambda v: v)


def _set_token_yticks(ax):
    """Human-friendly token ticks (1/10/100/1k/.../1M) on a log y-axis of raw
    token counts."""
    _apply_log_ticks(ax, _TOKEN_ANCHORS, lambda v: v, which="y")


def _set_count_xticks(ax):
    """Human-friendly count ticks (1/10/100/1K/10K/.../1M) on a log x-axis of
    raw counts (calls, turns, sessions, users)."""
    _apply_log_ticks(ax, _COUNT_ANCHORS, lambda v: v)


def _calls_weekday_weekend_bars(df: pd.DataFrame, output_dir: str,
                                fig_name: str, unit: str):
    """Grouped bars comparing weekday vs weekend call counts (per session or turn).

    Two panels (LLM calls, tool calls per *unit*), each showing Median / Mean /
    P75 / P90 as grouped bars for Weekday vs Weekend.  Expects a summary CSV with
    one row per ``dayType`` and columns ``{llm,tool}_{median,mean,p75,p90}``.
    """
    required = [f"{m}_{s}" for m in ("llm", "tool")
                for s in ("median", "mean", "p90", "p99")]
    if "dayType" not in df.columns or any(c not in df.columns for c in required):
        print(f"  Skipping {fig_name} (missing columns)")
        return

    stats = ["median", "mean", "p90", "p99"]
    stat_labels = ["Median", "Mean", "P90", "P99"]
    d = df.set_index("dayType")
    day_order = [dt for dt in ("Weekday", "Weekend") if dt in d.index]
    colors = {"Weekday": paper_style.COLOR_WEEKDAY, "Weekend": paper_style.COLOR_WEEKEND}

    x = np.arange(len(stats))
    width = 0.38
    fig, axes = plt.subplots(1, 2, figsize=paper_style.WIDE)
    for ax, metric, ylabel in ((axes[0], "llm", f"LLM Calls / {unit}"),
                               (axes[1], "tool", f"Tool Calls / {unit}")):
        for i, dt in enumerate(day_order):
            vals = [d.loc[dt, f"{metric}_{s}"] for s in stats]
            offset = (i - (len(day_order) - 1) / 2) * width
            ax.bar(x + offset, vals, width, label=dt, color=colors[dt])
        paper_style.style_ax(ax, ylabel=ylabel, grid_y=True)
        ax.set_xticks(x)
        ax.set_xticklabels(stat_labels)

    axes[0].legend(fontsize=paper_style.LEGEND_SIZE, frameon=True, loc="upper left")
    paper_style.save_fig(fig, fig_name, output_dir=output_dir)


def session_duration_hist_cdf_logscale(df: pd.DataFrame, output_dir: str,
                                       name_suffix: str = ""):
    """CDF of session duration on log-x scale."""
    dur_min = df["wallClockMs"].dropna() / 60_000
    dur_min = dur_min[dur_min > 0]

    fig, ax = plt.subplots(figsize=(2.5, 1.6))
    sorted_vals = np.sort(dur_min.values)
    cdf = np.arange(1, len(sorted_vals) + 1) / len(sorted_vals)
    ax.plot(sorted_vals, cdf, color=paper_style.COLOR_LLM, linewidth=1.5)
    ax.set_xscale("log")

    med = float(np.median(sorted_vals))
    ax.axvline(med, color=paper_style.MS_RED, linestyle="--", linewidth=1.2,
               label=f"Median: {med:.1f} min")

    paper_style.style_ax(ax, xlabel="Session Duration (log)", ylabel="CDF of Sessions",
                         keep_all_spines=True, grid_y=True)
    ax.set_ylim(0, 1.05)
    _set_time_xticks(ax, "min")
    ax.legend(fontsize=paper_style.LEGEND_SIZE, frameon=True, loc="upper left")
    paper_style.save_fig(fig, f"session_duration_hist_cdf_logscale{name_suffix}",
                         output_dir=output_dir, pad_inches=0.05)


def turn_duration_hist_cdf_logscale(df: pd.DataFrame, output_dir: str,
                                    name_suffix: str = ""):
    """CDF of per-turn duration on log-x scale."""
    if "turnsActiveMs" in df.columns and "turns" in df.columns:
        valid = df[(df["turns"] > 0) & (df["turnsActiveMs"] > 0)].copy()
        turn_sec = valid["turnsActiveMs"] / valid["turns"] / 1000.0
    elif "wallClockMs" in df.columns and "turns" in df.columns:
        valid = df[(df["turns"] > 0) & (df["wallClockMs"] > 0)].copy()
        turn_sec = valid["wallClockMs"] / valid["turns"] / 1000.0
    else:
        print("  Skipping turn_duration_hist_cdf_logscale (no suitable columns)")
        return

    turn_sec = turn_sec[turn_sec > 0]
    sorted_vals = np.sort(turn_sec.values)
    cdf = np.arange(1, len(sorted_vals) + 1) / len(sorted_vals)

    fig, ax = plt.subplots(figsize=(2.5, 1.6))
    ax.plot(sorted_vals, cdf, color=paper_style.COLOR_TOOL, linewidth=1.5)
    ax.set_xscale("log")

    med = float(np.median(sorted_vals))
    ax.axvline(med, color=paper_style.MS_RED, linestyle="--", linewidth=1.2,
               label=f"Median: {med:.1f} s")

    paper_style.style_ax(ax, xlabel="Turn Duration (log)", ylabel="CDF of Sessions",
                         keep_all_spines=True, grid_y=True)
    ax.set_ylim(0, 1.05)
    _set_time_xticks(ax, "s")
    ax.legend(fontsize=paper_style.LEGEND_SIZE, frameon=True, loc="upper left")
    paper_style.save_fig(fig, f"turn_duration_hist_cdf_logscale{name_suffix}",
                         output_dir=output_dir, pad_inches=0.05)


def _token_count_cdf(df: pd.DataFrame, output_dir: str, name: str,
                     xlabel: str, ylabel: str):
    """CDF of prompt, completion, and cached token counts (per LLM call or per
    turn, depending on the input CSV).

    Dashed vertical lines mark each series' median (not shown in the legend).
    """
    fig, ax = plt.subplots(figsize=paper_style.WIDE)

    def _pick(*candidates):
        for c in candidates:
            if c in df.columns:
                return c
        return None

    prompt_col = _pick("promptTokens", "totalPromptTokens")
    comp_col = _pick("completionTokens", "totalCompletionTokens", "totalResponseTokens")
    cached_col = _pick("cachedTokens", "totalCachedTokens")

    entries = [
        (prompt_col, "Prompt tokens", paper_style.COLOR_PROMPT),
        (comp_col, "Completion tokens", paper_style.COLOR_COMPLETION),
        (cached_col, "Cached tokens", paper_style.COLOR_CACHED),
    ]

    def _fmt_med(v):
        if v >= 1e6:
            return f"{v / 1e6:.1f}M"
        if v >= 1e3:
            return f"{v / 1e3:.0f}K"
        return f"{v:.0f}"

    # Per-series annotation placement (stagger to avoid the close prompt/cached labels).
    annot = {
        "Prompt tokens": dict(y=0.90, ha="left", xmul=1.25),
        "Cached tokens": dict(y=0.68, ha="right", xmul=1 / 1.25),
        "Completion tokens": dict(y=0.90, ha="right", xmul=1 / 1.25),
    }

    for col, label, color in entries:
        if not col or col not in df.columns:
            continue
        vals = df[col].dropna().values
        vals = np.sort(vals[vals > 0])
        if len(vals) == 0:
            continue
        cdf = np.arange(1, len(vals) + 1) / len(vals)
        ax.plot(vals, cdf, color=color, linewidth=1.5, label=label)
        # Dashed vertical line at the median (kept out of the legend) with the
        # median value annotated in text, in the same color.
        med = float(np.median(vals))
        ax.axvline(med, color=color, linestyle="--", linewidth=1.0, alpha=0.9)
        a = annot.get(label, dict(y=0.9, ha="left", xmul=1.25))
        ax.text(med * a["xmul"], a["y"], _fmt_med(med), color=color,
                ha=a["ha"], va="center", fontsize=paper_style.TICK_SIZE,
                fontweight="bold", transform=ax.get_xaxis_transform())

    ax.set_xscale("log")
    paper_style.style_ax(ax, xlabel=xlabel, ylabel=ylabel,
                         keep_all_spines=True, grid_y=True)
    ax.legend(fontsize=paper_style.LEGEND_SIZE)
    ax.set_ylim(0, 1.05)
    _set_token_xticks(ax)
    paper_style.save_fig(fig, name, output_dir=output_dir)


def token_count_cdf(df: pd.DataFrame, output_dir: str):
    """CDF of prompt/completion/cached token counts per LLM call (VS Code)."""
    _token_count_cdf(df, output_dir, "token_count_cdf",
                     xlabel="Tokens per LLM Call (log)", ylabel="CDF of LLM Calls")


def per_turn_token_count_cdf(df: pd.DataFrame, output_dir: str):
    """CDF of total prompt/completion/cached token counts per turn (VS)."""
    _token_count_cdf(df, output_dir, "per_turn_token_count_cdf",
                     xlabel="Tokens per Turn (log)", ylabel="CDF of Turns")


def cache_hit_rate_cdf(df: pd.DataFrame, output_dir: str):
    """CDF of per-call cache hit rate.

    Reads from cache_rate_by_call.csv or cache_rate_distribution.csv or token_stats.csv.
    Falls back to session-level cacheRate if available.
    """
    if "cacheRate" in df.columns:
        rates = df["cacheRate"].dropna()
    elif "CacheRate" in df.columns:
        rates = df["CacheRate"].dropna()
    elif "TokensCachedPercentage" in df.columns:
        rates = df["TokensCachedPercentage"].dropna()
    elif "CachedTokens" in df.columns and "PromptTokens" in df.columns:
        valid = df[(df["PromptTokens"] > 0)].copy()
        rates = (valid["CachedTokens"] / valid["PromptTokens"] * 100)
    elif "cachedTokens" in df.columns and "promptTokens" in df.columns:
        valid = df[(df["promptTokens"] > 0)].copy()
        rates = (valid["cachedTokens"] / valid["promptTokens"] * 100)
    else:
        print("  Skipping cache_hit_rate_cdf (no cache rate column)")
        return

    rates = rates[rates >= 0].clip(upper=100)
    sorted_vals = np.sort(rates.values)
    cdf = np.arange(1, len(sorted_vals) + 1) / len(sorted_vals)

    fig, ax = plt.subplots(figsize=paper_style.SINGLE_COL)
    ax.plot(sorted_vals, cdf, color=paper_style.COLOR_CACHED, linewidth=1.5)
    paper_style.style_ax(ax, xlabel="Cache Hit Rate (%)", ylabel="CDF of LLM Calls",
                         keep_all_spines=True, grid_y=True)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 1.05)
    paper_style.save_fig(fig, "cache_hit_rate_cdf", output_dir=output_dir)


def model_switch_selection_mode(df: pd.DataFrame, output_dir: str):
    """Stacked bars: auto/manual model-selection modes by switch detail."""
    required = {"selectionMode", "switchDetail", "switchCount", "pctWithinMode"}
    if not required.issubset(df.columns):
        print("  Skipping model_switch_selection_mode (missing columns)")
        return

    mode_order = ["auto", "manual", "auto->manual", "manual->auto"]
    mode_labels = {
        "auto": "Auto",
        "manual": "Manual",
        "auto->manual": "Auto ->\nManual",
        "manual->auto": "Manual ->\nAuto",
    }
    detail_order = [
        "same-family upgrade",
        "same-family downgrade",
        "same-family lateral",
        "diff-family upgrade",
        "diff-family downgrade",
        "diff-family lateral",
    ]
    detail_labels = {
        "same-family upgrade": "Same fam. up",
        "same-family downgrade": "Same fam. down",
        "same-family lateral": "Same fam. lat.",
        "diff-family upgrade": "Diff fam. up",
        "diff-family downgrade": "Diff fam. down",
        "diff-family lateral": "Diff fam. lat.",
    }
    colors = ["#59A14F", "#E15759", "#4E79A7", "#8CD17D", "#FF9D9A", "#B07AA1"]

    d = df.copy()
    d["switchCount"] = pd.to_numeric(d["switchCount"], errors="coerce")
    d["pctWithinMode"] = pd.to_numeric(d["pctWithinMode"], errors="coerce")
    d = d.dropna(subset=["switchCount", "pctWithinMode"])
    d = d[d["selectionMode"].isin(mode_order) & d["switchDetail"].isin(detail_order)]
    if d.empty:
        print("  Skipping model_switch_selection_mode (no classified switches)")
        return

    pivot = (d.pivot_table(index="selectionMode", columns="switchDetail",
                           values="pctWithinMode", aggfunc="sum")
             .reindex(mode_order)
             .fillna(0.0))

    x = np.arange(len(mode_order))
    fig, ax = plt.subplots(figsize=(4.0, 2.15))
    bottom = np.zeros(len(mode_order))
    for detail, color in zip(detail_order, colors):
        vals = pivot[detail].values if detail in pivot.columns else np.zeros(len(mode_order))
        bars = ax.bar(x, vals, bottom=bottom, width=0.68, color=color,
                      edgecolor="white", linewidth=0.45,
                      label=detail_labels[detail])
        for i, (bar, val) in enumerate(zip(bars, vals)):
            if val >= 12:
                ax.text(bar.get_x() + bar.get_width() / 2, bottom[i] + val / 2,
                        f"{val:.0f}", ha="center", va="center",
                        fontsize=paper_style.TICK_SIZE - 1,
                        color="white", fontweight="bold")
        bottom += vals

    totals = d.groupby("selectionMode")["switchCount"].sum()
    ax.set_xticks(x)
    ax.set_xticklabels([mode_labels[m] for m in mode_order])
    for i, mode in enumerate(mode_order):
        if mode in totals:
            ax.text(i, 103, f"n={int(totals[mode]):,}", ha="center", va="bottom",
                    fontsize=paper_style.TICK_SIZE - 1, color="#555")

    paper_style.style_ax(ax, ylabel="Within Mode (%)", grid_y=True)
    ax.set_ylim(0, 112)
    ax.legend(fontsize=paper_style.LEGEND_SIZE - 1, ncol=3,
              loc="upper center", bbox_to_anchor=(0.5, -0.23),
              frameon=True, columnspacing=0.8, handletextpad=0.4)
    paper_style.save_fig(fig, "model_switch_selection_mode",
                         output_dir=output_dir, pad_inches=0.04)


def _model_switch_stacked_bars(d, mode_order, mode_labels, stack_order, stack_labels,
                                colors, fig_name, output_dir):
    """Shared helper: 4-bar stacked chart for model-switch sub-figures."""
    pivot = (d.pivot_table(index="selectionMode", columns="_stack",
                           values="pctWithinMode", aggfunc="sum")
             .reindex(mode_order).fillna(0.0))

    x = np.arange(len(mode_order))
    fig, ax = plt.subplots(figsize=(4.0, 2.15))
    bottom = np.zeros(len(mode_order))
    for stk, color in zip(stack_order, colors):
        vals = pivot[stk].values if stk in pivot.columns else np.zeros(len(mode_order))
        bars = ax.bar(x, vals, bottom=bottom, width=0.68, color=color,
                      edgecolor="white", linewidth=0.45, label=stack_labels[stk])
        for i, (bar, val) in enumerate(zip(bars, vals)):
            if val >= 14:
                ax.text(bar.get_x() + bar.get_width() / 2, bottom[i] + val / 2,
                        f"{val:.0f}", ha="center", va="center",
                        fontsize=paper_style.TICK_SIZE - 1, color="white", fontweight="bold")
        bottom += vals

    totals = d.groupby("selectionMode")["switchCount"].sum()
    ax.set_xticks(x)
    ax.set_xticklabels([mode_labels[m] for m in mode_order])
    for i, mode in enumerate(mode_order):
        if mode in totals.index:
            ax.text(i, 103, f"n={int(totals[mode]):,}", ha="center", va="bottom",
                    fontsize=paper_style.TICK_SIZE - 1, color="#555")

    paper_style.style_ax(ax, ylabel="Within Mode (%)", grid_y=True)
    ax.set_ylim(0, 112)
    ncols = min(len(stack_order), 3)
    ax.legend(fontsize=paper_style.LEGEND_SIZE - 1, ncol=ncols,
              loc="upper center", bbox_to_anchor=(0.5, -0.23),
              frameon=True, columnspacing=0.8, handletextpad=0.4)
    paper_style.save_fig(fig, fig_name, output_dir=output_dir, pad_inches=0.04)


def model_switch_family_only(df: pd.DataFrame, output_dir: str):
    """4-bar stacked chart: auto/manual modes stacked by same-family vs diff-family."""
    required = {"selectionMode", "switchDetail", "switchCount", "pctWithinMode"}
    if not required.issubset(df.columns):
        print("  Skipping model_switch_family_only (missing columns)")
        return

    mode_order  = ["auto", "manual", "auto->manual", "manual->auto"]
    mode_labels = {"auto": "Auto", "manual": "Manual",
                   "auto->manual": "Auto ->\nManual", "manual->auto": "Manual ->\nAuto"}
    detail_order = ["same-family upgrade", "same-family downgrade", "same-family lateral",
                    "diff-family upgrade",  "diff-family downgrade",  "diff-family lateral"]

    d = df.copy()
    d["switchCount"]    = pd.to_numeric(d["switchCount"],    errors="coerce")
    d["pctWithinMode"]  = pd.to_numeric(d["pctWithinMode"],  errors="coerce")
    d = d.dropna(subset=["switchCount", "pctWithinMode"])
    d = d[d["selectionMode"].isin(mode_order) & d["switchDetail"].isin(detail_order)]
    if d.empty:
        print("  Skipping model_switch_family_only (no data)"); return

    d["_stack"] = d["switchDetail"].str.split(" ").str[0]   # "same-family" or "diff-family"
    stack_order  = ["same-family", "diff-family"]
    stack_labels = {"same-family": "Same family", "diff-family": "Diff family"}
    colors       = [paper_style.MS_BLUE, paper_style.MS_RED]

    _model_switch_stacked_bars(d, mode_order, mode_labels, stack_order, stack_labels,
                                colors, "model_switch_family_only", output_dir)


def model_switch_direction_only(df: pd.DataFrame, output_dir: str):
    """Horizontal stacked bars: auto->manual and manual->auto.
    Stacks (left→right): upgrade same-fam / upgrade diff-fam /
                         downgrade same-fam / downgrade diff-fam / lateral.
    Color encodes direction (upgrade / downgrade / lateral); hatch encodes
    family (solid = same family, hatched = different family).
    """
    required = {"selectionMode", "switchDetail", "switchCount", "pctWithinMode"}
    if not required.issubset(df.columns):
        print("  Skipping model_switch_direction_only (missing columns)")
        return

    mode_order  = ["auto->manual", "manual->auto"]
    mode_labels = {"auto->manual": "Auto→Manual", "manual->auto": "Manual→Auto"}
    detail_order = ["same-family upgrade", "same-family downgrade", "same-family lateral",
                    "diff-family upgrade",  "diff-family downgrade",  "diff-family lateral"]

    d = df.copy()
    d["switchCount"]   = pd.to_numeric(d["switchCount"],   errors="coerce")
    d["pctWithinMode"] = pd.to_numeric(d["pctWithinMode"], errors="coerce")
    d = d.dropna(subset=["switchCount", "pctWithinMode"])
    d = d[d["selectionMode"].isin(mode_order) & d["switchDetail"].isin(detail_order)]
    if d.empty:
        print("  Skipping model_switch_direction_only (no data)"); return

    # Collapse both lateral categories into a single "lateral" key
    d["_stack"] = d["switchDetail"].apply(
        lambda x: "lateral" if "lateral" in x else x
    )
    # Order: upgrades (same/diff fam), then downgrades (same/diff fam), then lateral
    stack_order = [
        "same-family upgrade",
        "diff-family upgrade",
        "same-family downgrade",
        "diff-family downgrade",
        "lateral",
    ]
    stack_labels = {
        "same-family upgrade":   "Upgrade (same fam.)",
        "diff-family upgrade":   "Upgrade (diff fam.)",
        "same-family downgrade": "Downgrade (same fam.)",
        "diff-family downgrade": "Downgrade (diff fam.)",
        "lateral":               "Lateral",
    }
    # Color encodes direction; hatch encodes family (solid=same, hatched=diff).
    UP_COLOR, DOWN_COLOR, LAT_COLOR = paper_style.MS_GREEN, paper_style.MS_RED, paper_style.MS_GRAY
    HATCH = "///"
    stack_style = {
        "same-family upgrade":   (UP_COLOR,   None),
        "diff-family upgrade":   (UP_COLOR,   HATCH),
        "same-family downgrade": (DOWN_COLOR, None),
        "diff-family downgrade": (DOWN_COLOR, HATCH),
        "lateral":               (LAT_COLOR,  None),
    }

    pivot = (d.pivot_table(index="selectionMode", columns="_stack",
                           values="pctWithinMode", aggfunc="sum")
             .reindex(mode_order).fillna(0.0))

    fig, ax = plt.subplots(figsize=(4, 2.0))
    y = np.arange(len(mode_order))
    left = np.zeros(len(mode_order))
    for stk in stack_order:
        color, hatch = stack_style[stk]
        vals = pivot[stk].values if stk in pivot.columns else np.zeros(len(mode_order))
        bars = ax.barh(y, vals, left=left, height=0.52, color=color, hatch=hatch,
                       edgecolor="white", linewidth=0.45)
        for i, (bar, val) in enumerate(zip(bars, vals)):
            if val >= 3:
                ax.text(left[i] + val / 2, i, f"{val:.0f}%",
                        ha="center", va="center",
                        fontsize=paper_style.TICK_SIZE - 1, color="white", fontweight="bold")
        left += vals

    ax.set_yticks(y)
    ax.set_yticklabels([mode_labels[m] for m in mode_order])

    paper_style.style_ax(ax, xlabel="Percentage of Each Model Switch Type (%)", grid_y=False)
    ax.xaxis.grid(True, linestyle="--", alpha=0.7)
    ax.set_axisbelow(True)
    ax.set_xlim(0, 100)

    # Two-part legend: color = direction, hatch = family.
    legend_handles = [
        Rectangle((0, 0), 1, 1, facecolor=UP_COLOR,   edgecolor="white", label="Upgrade"),
        Rectangle((0, 0), 1, 1, facecolor=DOWN_COLOR, edgecolor="white", label="Downgrade"),
        Rectangle((0, 0), 1, 1, facecolor=LAT_COLOR,  edgecolor="white", label="Lateral"),
        Rectangle((0, 0), 1, 1, facecolor="#B0B0B0", edgecolor="white", label="Same family"),
        Rectangle((0, 0), 1, 1, facecolor="#B0B0B0", edgecolor="white", hatch=HATCH,
                  label="Different family"),
    ]
    ax.legend(handles=legend_handles, fontsize=paper_style.LEGEND_SIZE, ncol=5,
              loc="upper center", bbox_to_anchor=(0.5, -0.30),
              frameon=True, columnspacing=0.9, handletextpad=0.4)
    paper_style.save_fig(fig, "model_switch_direction_only", output_dir=output_dir, pad_inches=0.04)


def cache_rate_vs_idle_boxplot(df: pd.DataFrame, output_dir: str):
    """Box plot of turn-boundary cache hit rate vs bucketed inter-turn idle time.

    X = idle time between turns (bucketed); Y = distribution of the first LLM
    call's cache hit rate after each turn boundary.
    """
    if not {"IdleTimeSec", "CacheRate"}.issubset(df.columns):
        print("  Skipping cache_rate_vs_idle_boxplot (missing columns)")
        return

    d = df.dropna(subset=["IdleTimeSec", "CacheRate"]).copy()
    d = d[(d["CacheRate"] >= 0) & (d["CacheRate"] <= 100)]

    edges = [0, 1, 5, 30, 120, 600, 3600, np.inf]
    labels = ["<1s", "1-5s", "5-30s", "30s-2m", "2-10m", "10m-1h", ">1h"]
    d["bucket"] = pd.cut(d["IdleTimeSec"], bins=edges, labels=labels, right=False)
    groups = [d.loc[d["bucket"] == lab, "CacheRate"].values for lab in labels]

    fig, ax = plt.subplots(figsize=paper_style.WIDE)
    bp = ax.boxplot(groups, showfliers=False, patch_artist=True, widths=0.6,
                    medianprops=dict(color="black", linewidth=1.2))
    for patch in bp["boxes"]:
        patch.set_facecolor(paper_style.COLOR_CACHED)
        patch.set_alpha(0.6)
    for whisk in bp["whiskers"]:
        whisk.set_color("#666")
    for cap in bp["caps"]:
        cap.set_color("#666")

    ax.set_xticks(range(1, len(labels) + 1))
    ax.set_xticklabels(labels)
    paper_style.style_ax(ax, xlabel="Idle Time Between Turns",
                         ylabel="Cache Hit Rate (%)", grid_y=True)
    ax.set_ylim(0, 100)
    paper_style.save_fig(fig, "cache_rate_vs_idle_boxplot", output_dir=output_dir)


def _time_breakdown_cdf(df: pd.DataFrame, output_dir: str, name: str,
                        turn_mode: str = "multi", include_user_idle: bool = True,
                        xlabel: str = "% of Session Wall-Clock Time"):
    """CDF of time-breakdown percentages (LLM, Tool batch, optionally User idle).

    ``turn_mode`` selects the session population:

    * ``"multi"``  — multi-turn sessions only (``turns > 1``).
    * ``"single"`` — single-turn sessions only (``turns == 1``).
    * ``"all"``    — no turn filter.

    User idle is only meaningful across turns, so ``include_user_idle`` should be
    ``False`` for single-turn sessions (which have no inter-turn idle by
    definition and would otherwise inflate the zero-idle population).
    """
    if "turns" in df.columns:
        if turn_mode == "multi":
            df = df[df["turns"] > 1].copy()
        elif turn_mode == "single":
            df = df[df["turns"] == 1].copy()

    fig, ax = plt.subplots(figsize=paper_style.WIDE)

    components = [
        ("llmPct", "LLM time", paper_style.COLOR_LLM),
        ("toolPct", "Tool batch time", paper_style.COLOR_TOOL),
    ]
    if include_user_idle:
        components.append(("userIdlePct", "User idle", paper_style.COLOR_USER_IDLE))
    for col, label, color in components:
        if col not in df.columns:
            continue
        vals = df[col].dropna()
        vals = vals[vals >= 0].clip(upper=100)
        sorted_vals = np.sort(vals.values)
        cdf = np.arange(1, len(sorted_vals) + 1) / len(sorted_vals)
        med = np.median(sorted_vals)
        ax.plot(sorted_vals, cdf, color=color, linewidth=1.5,
                label=f"{label} (med {med:.1f}%)")

    paper_style.style_ax(ax, xlabel=xlabel, ylabel="CDF of Sessions",
                         keep_all_spines=True, grid_y=True)
    paper_style.add_legend(ax, loc="lower right")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 1.05)
    paper_style.save_fig(fig, name, output_dir=output_dir)


def time_breakdown_llm_tool_user_cdf(df: pd.DataFrame, output_dir: str):
    """CDF of time breakdown percentages (LLM, Tool, User idle) for multi-turn
    sessions. Single-turn sessions (``turns <= 1``) are excluded because they
    have no inter-turn idle and would inflate the zero-idle population."""
    _time_breakdown_cdf(df, output_dir, "time_breakdown_llm_tool_user_cdf",
                        turn_mode="multi", include_user_idle=True)


def time_breakdown_llm_tool_user_cdf_multi_turn(df: pd.DataFrame, output_dir: str):
    """Multi-turn-only time breakdown (LLM, Tool, User idle)."""
    _time_breakdown_cdf(df, output_dir, "time_breakdown_llm_tool_user_cdf_multi_turn",
                        turn_mode="multi", include_user_idle=True)


def time_breakdown_llm_tool_cdf_single_turn(df: pd.DataFrame, output_dir: str):
    """Single-turn-only time breakdown (LLM, Tool). User idle is omitted because
    single-turn sessions have no inter-turn idle by definition."""
    _time_breakdown_cdf(df, output_dir, "time_breakdown_llm_tool_cdf_single_turn",
                        turn_mode="single", include_user_idle=False)


def time_breakdown_llm_tool_user_cdf_vs(df: pd.DataFrame, output_dir: str):
    """VS (GHCP) multi-turn time breakdown (LLM, Tool, User idle).

    Uses the VS pipeline's wall-clock and per-turn spans reconstructed from real
    per-call timestamps, so inter-turn idle is measured (not estimated as in the
    VS Code pipeline, where idle collapses to 0). Each component is normalized by
    the User+LLM+Tool total (system overhead excluded), so the three curves are
    fractions of that total."""
    _time_breakdown_cdf(df, output_dir, "time_breakdown_llm_tool_user_cdf_vs",
                        turn_mode="multi", include_user_idle=True,
                        xlabel="% of Total Session Time")


def time_breakdown_llm_tool_cdf_single_turn_vs(df: pd.DataFrame, output_dir: str):
    """VS (GHCP) single-turn time breakdown (LLM, Tool). User idle is omitted
    because single-turn sessions have no inter-turn idle by definition. Each
    component is normalized by the User+LLM+Tool total."""
    _time_breakdown_cdf(df, output_dir, "time_breakdown_llm_tool_cdf_single_turn_vs",
                        turn_mode="single", include_user_idle=False,
                        xlabel="% of Total Session Time")


def time_breakdown_llm_tool_user_cdf_multi_turn_vs(df: pd.DataFrame, output_dir: str):
    """VS (GHCP) multi-turn time breakdown (LLM, Tool, User idle), normalized by
    the User+LLM+Tool total."""
    _time_breakdown_cdf(df, output_dir, "time_breakdown_llm_tool_user_cdf_multi_turn_vs",
                        turn_mode="multi", include_user_idle=True,
                        xlabel="% of Total Session Time")


def per_turn_calls_cdf(df: pd.DataFrame, output_dir: str):
    """CDF of LLM calls and tool calls per turn."""
    fig, ax = plt.subplots(figsize=paper_style.WIDE)

    if "llmCallsPerTurn" in df.columns:
        vals = df["llmCallsPerTurn"].dropna().sort_values().values
    elif "llmCalls" in df.columns and "turns" in df.columns:
        valid = df[df["turns"] > 0]
        vals = np.sort((valid["llmCalls"] / valid["turns"]).values)
    else:
        print("  Skipping per_turn_calls_cdf (no suitable columns)")
        return

    cdf = np.arange(1, len(vals) + 1) / len(vals)
    ax.plot(vals, cdf, color="darkorange", linewidth=1.5, label="LLM calls/turn")
    llm_med = float(np.median(vals))
    ax.axvline(llm_med, color="darkorange", linestyle="--", linewidth=1.0, alpha=0.9)
    ax.text(llm_med * 1.18, 0.90, f"{llm_med:g}", color="darkorange",
            ha="left", va="center", fontsize=paper_style.TICK_SIZE,
            fontweight="bold", transform=ax.get_xaxis_transform())

    if "toolCalls" in df.columns and "turns" in df.columns:
        valid = df[df["turns"] > 0]
        tool_vals = np.sort((valid["toolCalls"] / valid["turns"]).values)
        tool_cdf = np.arange(1, len(tool_vals) + 1) / len(tool_vals)
        ax.plot(tool_vals, tool_cdf, color="seagreen", linewidth=1.5, label="Tool calls/turn")
        tool_med = float(np.median(tool_vals))
        ax.axvline(tool_med, color="seagreen", linestyle="--", linewidth=1.0, alpha=0.9)
        ax.text(tool_med / 1.18, 0.72, f"{tool_med:g}", color="seagreen",
                ha="right", va="center", fontsize=paper_style.TICK_SIZE,
                fontweight="bold", transform=ax.get_xaxis_transform())

    paper_style.style_ax(ax, xlabel="Calls per Turn (log scale)", ylabel="CDF of Sessions",
                         keep_all_spines=True, grid_y=True)
    ax.set_xscale("log")
    ax.set_xlim(left=0.8)
    ax.legend(fontsize=paper_style.LEGEND_SIZE)
    ax.set_ylim(0, 1.05)
    _set_count_xticks(ax)
    paper_style.save_fig(fig, "per_turn_calls_cdf", output_dir=output_dir)


def session_turns_cdf(df: pd.DataFrame, output_dir: str, name_suffix: str = ""):
    """CDF of the number of user turns per session."""
    if "turns" not in df.columns:
        print("  Skipping session_turns_cdf (no turns column)")
        return
    turns = df["turns"].dropna()
    turns = turns[turns > 0]

    fig, ax = plt.subplots(figsize=paper_style.WIDE)
    vals = np.sort(turns.values)
    cdf = np.arange(1, len(vals) + 1) / len(vals)
    ax.plot(vals, cdf, color=paper_style.COLOR_LLM, linewidth=1.5)
    med = float(np.median(vals))
    ax.axvline(med, color="red", linestyle="--", linewidth=1.0, alpha=0.9,
               label=f"Median: {med:g}")

    paper_style.style_ax(ax, xlabel="User Turns per Session (log scale)",
                         ylabel="CDF of Sessions", keep_all_spines=True, grid_y=True)
    ax.set_xscale("log")
    ax.set_xlim(left=0.8)
    ax.legend(fontsize=paper_style.LEGEND_SIZE)
    ax.set_ylim(0, 1.05)
    _set_count_xticks(ax)
    paper_style.save_fig(fig, f"session_turns_cdf{name_suffix}", output_dir=output_dir)


def per_session_calls_cdf(df: pd.DataFrame, output_dir: str, name_suffix: str = ""):
    """CDF of LLM calls and tool calls per session."""
    fig, ax = plt.subplots(figsize=paper_style.WIDE)

    if "llmCalls" in df.columns:
        vals = np.sort(df["llmCalls"].dropna().values)
        cdf = np.arange(1, len(vals) + 1) / len(vals)
        ax.plot(vals, cdf, color="darkorange", linewidth=1.5, label="LLM calls/session")
        llm_med = float(np.median(vals))
        ax.axvline(llm_med, color="darkorange", linestyle="--", linewidth=1.0, alpha=0.9)
        ax.text(llm_med * 1.18, 0.90, f"{llm_med:g}", color="darkorange",
                ha="left", va="center", fontsize=paper_style.TICK_SIZE,
                fontweight="bold", transform=ax.get_xaxis_transform())

    if "toolCalls" in df.columns:
        tool_vals = np.sort(df["toolCalls"].dropna().values)
        tool_cdf = np.arange(1, len(tool_vals) + 1) / len(tool_vals)
        ax.plot(tool_vals, tool_cdf, color="seagreen", linewidth=1.5, label="Tool calls/session")
        tool_med = float(np.median(tool_vals))
        ax.axvline(tool_med, color="seagreen", linestyle="--", linewidth=1.0, alpha=0.9)
        ax.text(tool_med / 1.18, 0.72, f"{tool_med:g}", color="seagreen",
                ha="right", va="center", fontsize=paper_style.TICK_SIZE,
                fontweight="bold", transform=ax.get_xaxis_transform())

    paper_style.style_ax(ax, xlabel="Calls per Session (log scale)", ylabel="CDF of Sessions",
                         keep_all_spines=True, grid_y=True)
    ax.set_xscale("log")
    ax.set_xlim(left=0.8)
    ax.legend(fontsize=paper_style.LEGEND_SIZE)
    ax.set_ylim(0, 1.05)
    _set_count_xticks(ax)
    paper_style.save_fig(fig, f"per_session_calls_cdf{name_suffix}", output_dir=output_dir)


def user_session_turns_cdf(df: pd.DataFrame, output_dir: str):
    """CDF of sessions per user and turns per user (agent mode)."""
    fig, ax = plt.subplots(figsize=paper_style.WIDE)

    if "sessions" in df.columns:
        vals = np.sort(df["sessions"].dropna().values)
        cdf = np.arange(1, len(vals) + 1) / len(vals)
        ax.plot(vals, cdf, color="darkorange", linewidth=1.5, label="Sessions/user")
        s_med = float(np.median(vals))
        ax.axvline(s_med, color="darkorange", linestyle="--", linewidth=1.0, alpha=0.9)
        ax.text(s_med * 1.18, 0.90, f"{s_med:g}", color="darkorange",
                ha="left", va="center", fontsize=paper_style.TICK_SIZE,
                fontweight="bold", transform=ax.get_xaxis_transform())

    if "turns" in df.columns:
        tvals = np.sort(df["turns"].dropna().values)
        tcdf = np.arange(1, len(tvals) + 1) / len(tvals)
        ax.plot(tvals, tcdf, color="seagreen", linewidth=1.5, label="Turns/user")
        t_med = float(np.median(tvals))
        ax.axvline(t_med, color="seagreen", linestyle="--", linewidth=1.0, alpha=0.9)
        ax.text(t_med / 1.18, 0.72, f"{t_med:g}", color="seagreen",
                ha="right", va="center", fontsize=paper_style.TICK_SIZE,
                fontweight="bold", transform=ax.get_xaxis_transform())

    paper_style.style_ax(ax, xlabel="Per User (log scale)", ylabel="CDF of Users",
                         keep_all_spines=True, grid_y=True)
    ax.set_xscale("log")
    ax.set_xlim(left=0.8)
    ax.legend(fontsize=paper_style.LEGEND_SIZE)
    ax.set_ylim(0, 1.05)
    _set_count_xticks(ax)
    paper_style.save_fig(fig, "user_session_turns_cdf", output_dir=output_dir)


def user_token_consumption_cdf(df: pd.DataFrame, output_dir: str):
    """CDF of total prompt and completion tokens consumed per user.

    Dashed vertical lines mark each series' median (not shown in the legend).
    """
    fig, ax = plt.subplots(figsize=paper_style.WIDE)

    def _fmt(v):
        if v >= 1e6:
            return f"{v / 1e6:.1f}M"
        if v >= 1e3:
            return f"{v / 1e3:.0f}K"
        return f"{v:.0f}"

    entries = [
        ("promptTokens", "Prompt tokens", paper_style.COLOR_PROMPT,
         dict(y=0.90, ha="left", xmul=1.3)),
        ("completionTokens", "Completion tokens", paper_style.COLOR_COMPLETION,
         dict(y=0.90, ha="right", xmul=1 / 1.3)),
    ]
    for col, label, color, a in entries:
        if col not in df.columns:
            continue
        vals = df[col].dropna().values
        vals = np.sort(vals[vals > 0])
        if len(vals) == 0:
            continue
        cdf = np.arange(1, len(vals) + 1) / len(vals)
        ax.plot(vals, cdf, color=color, linewidth=1.5, label=label)
        med = float(np.median(vals))
        ax.axvline(med, color=color, linestyle="--", linewidth=1.0, alpha=0.9)
        ax.text(med * a["xmul"], a["y"], _fmt(med), color=color,
                ha=a["ha"], va="center", fontsize=paper_style.TICK_SIZE,
                fontweight="bold", transform=ax.get_xaxis_transform())

    ax.set_xscale("log")
    paper_style.style_ax(ax, xlabel="Total Tokens per User (log)", ylabel="CDF of Users",
                         keep_all_spines=True, grid_y=True)
    ax.legend(fontsize=paper_style.LEGEND_SIZE)
    ax.set_ylim(0, 1.05)
    _set_token_xticks(ax)
    paper_style.save_fig(fig, "user_token_consumption_cdf", output_dir=output_dir)


def llm_parallelism(df: pd.DataFrame, output_dir: str):
    """CDF of LLM parallelism degree — only turns with actual parallelism (> 1)."""
    col = next((c for c in ("parallelismDegree", "llmParallelism", "maxConcurrency")
                if c in df.columns), None)
    if col not in df.columns:
        print(f"  Skipping llm_parallelism (no {col} column)")
        return

    par = df[col].dropna()
    par = par[par > 1.0]
    if par.empty:
        print("  Skipping llm_parallelism (no turns with parallelism > 1)")
        return

    fig, ax = plt.subplots(figsize=paper_style.WIDE)
    sorted_vals = np.sort(par.values)
    cdf = np.arange(1, len(sorted_vals) + 1) / len(sorted_vals)
    ax.plot(sorted_vals, cdf, color=paper_style.COLOR_LLM, linewidth=1.5)

    paper_style.style_ax(ax, xlabel="LLM Parallelism Degree (only turns with parallelism > 1)",
                         ylabel="CDF of Sessions", keep_all_spines=True, grid_y=True)
    ax.set_ylim(0, 1.05)
    paper_style.save_fig(fig, "llm_parallelism", output_dir=output_dir)


def tool_parallelism(df: pd.DataFrame, output_dir: str):
    """CDF of tool parallelism — only batches with actual parallelism (> 1)."""
    # Determine which column has parallelism data
    if "toolCount" in df.columns and "batchCount" in df.columns:
        par = df.loc[df.index.repeat(df["batchCount"])]["toolCount"].values.astype(float)
    elif "avgParallelism" in df.columns:
        par = df["avgParallelism"].dropna().values
    elif "maxConcurrency" in df.columns:
        par = df["maxConcurrency"].dropna().values
    elif "parallelism" in df.columns:
        par = df["parallelism"].dropna().values
    else:
        print("  Skipping tool_parallelism (no parallelism column)")
        return

    par = par[par > 1.0]
    if len(par) == 0:
        print("  Skipping tool_parallelism (no batches with parallelism > 1)")
        return

    fig, ax = plt.subplots(figsize=paper_style.WIDE)
    sorted_vals = np.sort(par)
    cdf = np.arange(1, len(sorted_vals) + 1) / len(sorted_vals)
    ax.plot(sorted_vals, cdf, color=paper_style.COLOR_TOOL, linewidth=1.5)
    med = np.median(par)
    ax.axvline(med, color="red", linestyle="--", label=f"Median: {med:.2f}")

    paper_style.style_ax(ax, xlabel="Tools per Batch (only batches with parallelism > 1)",
                         ylabel="CDF of Batches", keep_all_spines=True, grid_y=True)
    ax.set_xscale("log")
    ax.set_xlim(left=1.8)
    ax.legend(fontsize=paper_style.LEGEND_SIZE)
    ax.set_ylim(0, 1.05)
    # Custom ticks: the data is concentrated in 2-10, so add intermediate anchors
    # rather than the bare decade ticks (10, 100).
    lo, hi = ax.get_xlim()
    tick_vals = [v for v in (2, 3, 5, 10, 20, 50, 100, 200) if lo <= v <= hi]
    ax.xaxis.set_major_locator(mticker.FixedLocator(tick_vals))
    ax.xaxis.set_major_formatter(mticker.FixedFormatter([str(v) for v in tick_vals]))
    ax.xaxis.set_minor_formatter(mticker.NullFormatter())
    paper_style.save_fig(fig, "tool_parallelism", output_dir=output_dir)


def per_tool_parallelism(df: pd.DataFrame, output_dir: str):
    """Horizontal bar: parallelism rate and avg batch size per tool type.

    Bars are colored by whether the tool is a read (information-retrieval) or
    write (mutating/side-effecting) operation.
    """
    if "toolName" not in df.columns or "parallelismRate" not in df.columns:
        print("  Skipping per_tool_parallelism (missing columns)")
        return

    # Sort by parallelism rate descending
    df = df.sort_values("parallelismRate", ascending=True).copy()
    df["rw"] = df["toolName"].map(_tool_rw_category)
    rw_color = {"read": paper_style.MS_BLUE, "write": paper_style.MS_RED}

    # Height scales with tool count so y labels don't overlap.
    fig_h = max(2.0, 0.26 * len(df))
    fig, ax = plt.subplots(figsize=(4, fig_h))
    y = np.arange(len(df))
    ax.barh(y, df["parallelismRate"], color=[rw_color[c] for c in df["rw"]],
            alpha=0.85, height=0.7)

    ax.set_yticks(y)
    ax.set_yticklabels(df["toolName"], fontsize=paper_style.TICK_SIZE)
    ax.set_ylim(-0.6, len(df) - 0.4)
    paper_style.style_ax(ax, xlabel="Parallelism Rate (%)")
    ax.set_xlim(0, min(df["parallelismRate"].max() * 1.18, 100))
    ax.grid(True, alpha=0.3, axis="x")
    ax.set_axisbelow(True)

    # Add avg batch size annotation
    if "avgBatchSize" in df.columns:
        for i, (_, row) in enumerate(df.iterrows()):
            ax.text(row["parallelismRate"] + 0.5, i,
                    f"{row['avgBatchSize']:.1f}×",
                    va="center", fontsize=paper_style.TICK_SIZE - 1, color="#555")

    handles = [plt.Rectangle((0, 0), 1, 1, color=rw_color["read"], alpha=0.85),
               plt.Rectangle((0, 0), 1, 1, color=rw_color["write"], alpha=0.85)]
    ax.legend(handles, ["Read", "Write"], fontsize=paper_style.LEGEND_SIZE,
              frameon=True, loc="lower right")

    paper_style.save_fig(fig, "per_tool_parallelism", output_dir=output_dir)


def tool_usage_bar(df: pd.DataFrame, output_dir: str):
    """Bar chart of tool-call share: top 15 tools + 'Others' (x=tool, y=% of calls)."""
    if "toolName" not in df.columns or "callCount" not in df.columns:
        print("  Skipping tool_usage_bar (missing columns)")
        return

    s = df.groupby("toolName")["callCount"].sum().sort_values(ascending=False)
    top = s.head(15)
    others = float(s.iloc[15:].sum())
    total = float(s.sum())
    labels = list(top.index)
    pct = [v / total * 100 for v in top.values]
    if others > 0:
        labels.append("Others")
        pct.append(others / total * 100)

    x = np.arange(len(labels))
    colors = ["seagreen"] * len(top) + ([paper_style.MS_GRAY] if others > 0 else [])

    fig, ax = plt.subplots(figsize=(3.4, 2.7))
    ax.bar(x, pct, color=colors, width=0.78)
    for xi, p in zip(x, pct):
        ax.text(xi, p + 0.4, f"{p:.1f}", ha="center", va="bottom",
                fontsize=paper_style.TICK_SIZE - 1.5, rotation=0)

    ax.set_xticks(x)
    ax.set_xticklabels(_abbrev_tool_labels(labels), rotation=45, ha="right",
                       rotation_mode="anchor", fontsize=paper_style.TICK_SIZE)
    ax.set_xlim(-0.7, len(labels) - 0.3)
    paper_style.style_ax(ax, ylabel="Invocation %")
    ax.grid(True, alpha=0.3, axis="y")
    ax.set_axisbelow(True)
    ax.set_ylim(0, max(pct) * 1.12)
    paper_style.save_fig(fig, "tool_usage_bar", output_dir=output_dir, pad_inches=0.03)


def error_signal_composition_by_depth(df: pd.DataFrame, output_dir: str):
    """Stacked bar: error-signal composition of agent turns by loop depth.

    Tests the converse of "error -> deep loop": given a deep loop, is it always
    an error/retry loop?  Turns (x = loop depth in tool calls) are split into
    three mutually exclusive classes and stacked to 100%:
        * Has tool failure   (>=1 tool call with Status == 2)
        * Diagnostics only   (error signal but no failure: get_errors /
                              get_diagnostics / get_errors_in_file)
        * No error signal    (neither of the above)
    Even the deepest loops keep a large "no error signal" share, so depth does
    not imply error recovery.  Uses ``vs_deep_loop_error_signal.csv``.
    """
    required = {"depthBucket", "turns", "turnsWithFailure", "turnsWithErrSignal"}
    if df is None or df.empty or not required.issubset(df.columns):
        print("  Skipping error_signal_composition_by_depth (missing columns)")
        return

    d = df.copy()
    turns = d["turns"].astype(float)
    # error signal (failure OR diagnostics) is a superset of failure, so:
    fail_pct = 100.0 * d["turnsWithFailure"] / turns
    diag_pct = 100.0 * (d["turnsWithErrSignal"] - d["turnsWithFailure"]) / turns
    none_pct = 100.0 * (turns - d["turnsWithErrSignal"]) / turns

    x = np.arange(len(d))
    fig, ax = plt.subplots(figsize=(3.4, 2.15))
    stacks = [
        (fail_pct.values, paper_style.MS_RED,    "Has tool failure"),
        (diag_pct.values, paper_style.MS_YELLOW, "Diagnostics only"),
        (none_pct.values, paper_style.MS_GRAY,   "No error signal"),
    ]
    bottom = np.zeros(len(d))
    for vals, color, label in stacks:
        ax.bar(x, vals, bottom=bottom, width=0.68, color=color,
               edgecolor="white", linewidth=0.45, label=label)
        for i, val in enumerate(vals):
            if val >= 4:
                txt_color = "black" if color == paper_style.MS_YELLOW else "white"
                ax.text(i, bottom[i] + val / 2, f"{val:.0f}", ha="center",
                        va="center", fontsize=paper_style.TICK_SIZE - 1,
                        color=txt_color, fontweight="bold")
        bottom += vals

    ax.set_xticks(x)
    ax.set_xticklabels(d["depthBucket"].astype(str))
    ax.set_ylim(0, 105)
    paper_style.style_ax(ax, xlabel="Loop depth (tool calls per turn)",
                         ylabel="Share of turns (%)", grid_y=True)
    ax.legend(fontsize=paper_style.LEGEND_SIZE - 1, ncol=3,
              loc="upper center", bbox_to_anchor=(0.5, -0.24),
              frameon=True, columnspacing=0.8, handletextpad=0.4)
    paper_style.save_fig(fig, "error_signal_composition_by_depth",
                         output_dir=output_dir, pad_inches=0.04)


def model_distribution_anonymized(df: pd.DataFrame, output_dir: str):
    """Bar chart of anonymized model request share: top 15 models + 'Others'.

    Expects a pre-aggregated, anonymized CSV (``rank``, ``model``, ``calls``,
    ``pct``) from the aggregation step. Model bars use the LLM
    color from ``session_avg_trends`` (darkorange); ``Others`` is gray — mirroring
    the layout of ``tool_usage_bar`` (which uses the Tool color, seagreen).
    """
    if "model" not in df.columns or "pct" not in df.columns:
        print("  Skipping model_distribution_anonymized (missing columns)")
        return

    df = df.sort_values("rank") if "rank" in df.columns else df
    labels = list(df["model"])
    pct = list(df["pct"])
    x = np.arange(len(labels))
    colors = [paper_style.MS_GRAY if lbl == "Others" else "darkorange" for lbl in labels]

    fig, ax = plt.subplots(figsize=(3.4, 2.1))
    ax.bar(x, pct, color=colors, width=0.78)
    for xi, p in zip(x, pct):
        ax.text(xi, p + 0.4, f"{p:.1f}", ha="center", va="bottom",
                fontsize=paper_style.TICK_SIZE - 1.5, rotation=0)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=90, ha="center", fontsize=paper_style.TICK_SIZE)
    ax.set_xlim(-0.7, len(labels) - 0.3)
    paper_style.style_ax(ax, ylabel="Invocation %")
    ax.grid(True, alpha=0.3, axis="y")
    ax.set_axisbelow(True)
    ax.set_ylim(0, max(pct) * 1.12)
    paper_style.save_fig(fig, "model_distribution_anonymized", output_dir=output_dir,
                         pad_inches=0.03)


def cache_rate_by_call_position(df: pd.DataFrame, output_dir: str):
    """Line chart: cache rate by LLM call position within a turn.

    Call 1 = first call in turn (boundary, low cache). Calls 2+ = intra-turn
    (high cache since context is mostly reused from previous call in same turn).
    """
    if "callIndex" not in df.columns or "avgCachePct" not in df.columns:
        print("  Skipping cache_rate_by_call_position (missing columns)")
        return

    df = df.dropna(subset=["callIndex"]).copy()
    df["callIndex"] = df["callIndex"].astype(int)
    df = df[df["callIndex"] <= 20]

    fig, ax = plt.subplots(figsize=paper_style.WIDE)
    ax.plot(df["callIndex"], df["avgCachePct"], "o-", color=paper_style.COLOR_CACHED,
            linewidth=1.5, markersize=3, label="API-reported cache rate")

    # Annotate the boundary value
    if len(df) >= 1:
        boundary = df.iloc[0]["avgCachePct"]
        ax.annotate(f"{boundary:.0f}%", xy=(1, boundary),
                    fontsize=paper_style.TICK_SIZE, color="#555",
                    ha="right", va="bottom")

    paper_style.style_ax(ax, xlabel="LLM Call Position within Turn",
                         ylabel="Cache Hit Rate (%)", grid_y=True)
    ax.set_ylim(0, 100)
    ax.set_xlim(left=1)
    ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    paper_style.add_legend(ax, loc="lower right")
    paper_style.save_fig(fig, "cache_rate_by_call_position", output_dir=output_dir)


def cache_rate_by_call_position_half_col(df: pd.DataFrame, output_dir: str):
    """Half-column variant of cache_rate_by_call_position (x capped at 10, no legend)."""
    if "callIndex" not in df.columns or "avgCachePct" not in df.columns:
        print("  Skipping cache_rate_by_call_position_half_col (missing columns)")
        return

    df = df.dropna(subset=["callIndex"]).copy()
    df["callIndex"] = df["callIndex"].astype(int)
    df = df[df["callIndex"] <= 10]

    fig, ax = plt.subplots(figsize=(1.8, 1.5))
    ax.plot(df["callIndex"], df["avgCachePct"], "o-", color=paper_style.COLOR_CACHED,
            linewidth=1.5, markersize=3)

    # Annotate the boundary (first-call) value.
    if len(df) >= 1:
        boundary = df.iloc[0]["avgCachePct"]
        ax.annotate(f"{boundary:.0f}%", xy=(1, boundary), xytext=(1.4, boundary - 9),
                    fontsize=paper_style.TICK_SIZE, color="#555",
                    ha="left", va="top")

    paper_style.style_ax(ax, xlabel="LLM Call Position",
                         ylabel="Cache Hit %", grid_y=True)
    ax.set_ylim(0, 100)
    ax.set_xlim(1, 10)
    ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    paper_style.save_fig(fig, "cache_rate_by_call_position_half_col",
                         output_dir=output_dir)


def turn_boundary_cache_rate(df: pd.DataFrame, output_dir: str):
    """Grouped bars: avg cache hit rate of the last call before vs first call after,
    across intra-turn / turn-boundary (same model) / turn-boundary (model switch).

    Expects columns: category, avgBefore, avgAfter (and optional n).
    """
    if not {"category", "avgBefore", "avgAfter"}.issubset(df.columns):
        print("  Skipping turn_boundary_cache_rate (no before/after columns)")
        return

    order = ["Intra-turn (same model)",
             "Turn boundary (same model)",
             "Turn boundary (model switch)"]
    short = {
        "Intra-turn (same model)": "Intra-turn\n(same model)",
        "Turn boundary (same model)": "Turn bound.\n(same model)",
        "Turn boundary (model switch)": "Turn bound.\n(model switch)",
    }
    d = df.set_index("category")
    cats = [c for c in order if c in d.index]
    before = [float(d.loc[c, "avgBefore"]) for c in cats]
    after = [float(d.loc[c, "avgAfter"]) for c in cats]
    labels = [short.get(c, c) for c in cats]

    x = np.arange(len(cats))
    width = 0.38
    fig, ax = plt.subplots(figsize=paper_style.WIDE)
    ax.bar(x - width / 2, before, width, label="Last call (before)",
           color=paper_style.MS_GREEN, alpha=0.9)
    ax.bar(x + width / 2, after, width, label="First call (after)",
           color=paper_style.MS_RED, alpha=0.9)
    for xi, (b, a) in enumerate(zip(before, after)):
        ax.text(xi - width / 2, b + 2, f"{b:.0f}%", ha="center",
                va="bottom", fontsize=paper_style.TICK_SIZE)
        ax.text(xi + width / 2, a + 2, f"{a:.0f}%", ha="center",
                va="bottom", fontsize=paper_style.TICK_SIZE)

    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    paper_style.style_ax(ax, ylabel="Avg Cache Hit Rate (%)", grid_y=True)
    ax.set_ylim(0, 108)
    ax.legend(fontsize=paper_style.LEGEND_SIZE, loc="lower center",
              bbox_to_anchor=(0.5, 1.0), ncol=2, frameon=True)
    paper_style.save_fig(fig, "turn_boundary_cache_rate", output_dir=output_dir,
                         pad_inches=0.03)


def compaction_severity(df: pd.DataFrame, output_dir: str):
    """CDF of compaction severity (token drop %), y-axis as % of events."""
    if "dropPct" in df.columns:
        col = "dropPct"
    elif "tokenDropPct" in df.columns:
        col = "tokenDropPct"
    elif "severity" in df.columns:
        col = "severity"
    else:
        print("  Skipping compaction_severity (no severity column)")
        return

    vals = df[col].dropna()
    sorted_vals = np.sort(vals.values)
    cdf = np.arange(1, len(sorted_vals) + 1) / len(sorted_vals)

    fig, ax = plt.subplots(figsize=paper_style.WIDE)
    ax.plot(sorted_vals, cdf, color=paper_style.COLOR_FAILURE, linewidth=1.5)
    ax.axvline(vals.median(), color="black", linestyle="--", label=f"Median: {vals.median():.1f}%")

    paper_style.style_ax(ax, xlabel="Token Drop (%)", ylabel="CDF of Events",
                         keep_all_spines=True, grid_y=True)
    ax.legend(fontsize=paper_style.LEGEND_SIZE)
    ax.set_ylim(0, 1.05)
    paper_style.save_fig(fig, "compaction_severity", output_dir=output_dir)


def compaction_severity_cache_hit_drop(df: pd.DataFrame, output_dir: str):
    """CDF of the cache-hit-rate drop (percentage points) after a context compaction.

    Drop = cache % on the last call before compaction minus cache % on the first
    call after (prevCachePct - TokensCachedPercentage).
    """
    if not {"prevCachePct", "TokensCachedPercentage"}.issubset(df.columns):
        print("  Skipping compaction_severity_cache_hit_drop (missing cache columns)")
        return

    drop = (df["prevCachePct"] - df["TokensCachedPercentage"]).dropna()
    if drop.empty:
        print("  Skipping compaction_severity_cache_hit_drop (no data)")
        return
    sorted_vals = np.sort(drop.values)
    cdf = np.arange(1, len(sorted_vals) + 1) / len(sorted_vals)

    fig, ax = plt.subplots(figsize=paper_style.WIDE)
    ax.plot(sorted_vals, cdf, color=paper_style.COLOR_FAILURE, linewidth=1.5)
    med = float(np.median(sorted_vals))
    ax.axvline(med, color="black", linestyle="--", label=f"Median: {med:.1f}%")

    paper_style.style_ax(ax, xlabel="Cache Hit Rate Drop (%)", ylabel="CDF of Events",
                         keep_all_spines=True, grid_y=True)
    ax.legend(fontsize=paper_style.LEGEND_SIZE)
    ax.set_ylim(0, 1.05)
    paper_style.save_fig(fig, "compaction_severity_cache_hit_drop", output_dir=output_dir)


def tool_duration_by_status(df: pd.DataFrame, output_dir: str):
    """Single-panel: per-tool duration box plots (success vs failure) + success-rate line.

    Left y-axis (log): Duration (ms) — side-by-side box plots for success (green)
    and failure (red) per tool. Right y-axis: success rate (%) as a marker line.
    Expects columns: toolName, toolStatus, callCount, p5, p25, p50, p75, p95.
    """
    needed = {"toolName", "toolStatus", "callCount", "p5", "p25", "p50", "p75", "p95"}
    if not needed.issubset(df.columns):
        print("  Skipping tool_duration_by_status (missing box columns)")
        return

    top = df.groupby("toolName")["callCount"].sum().nlargest(15).index.tolist()
    d = df.set_index(["toolName", "toolStatus"])
    width = 0.36
    C_SUCCESS, C_FAIL, C_RATE = "#55A868", "#C44E52", "#DD8452"

    def _floor(v):  # keep strictly positive for log scale
        return max(float(v), 1.0)

    def _bxstat(row):
        return dict(med=_floor(row["p50"]), q1=_floor(row["p25"]), q3=_floor(row["p75"]),
                    whislo=_floor(row["p5"]), whishi=_floor(row["p95"]), fliers=[])

    succ_stats, succ_pos, fail_stats, fail_pos, rate = [], [], [], [], []
    for i, t in enumerate(top):
        sc = fc = 0
        if (t, 1) in d.index:
            r = d.loc[(t, 1)]
            succ_stats.append(_bxstat(r)); succ_pos.append(i - width / 2)
            sc = float(r["callCount"])
        if (t, 2) in d.index:
            r = d.loc[(t, 2)]
            fail_stats.append(_bxstat(r)); fail_pos.append(i + width / 2)
            fc = float(r["callCount"])
        rate.append(sc / (sc + fc) * 100 if sc + fc > 0 else np.nan)

    fig, ax = plt.subplots(figsize=(3.6, 3.0))

    def _draw(stats, pos, color):
        if not stats:
            return
        ax.bxp(stats, positions=pos, widths=width, patch_artist=True, showfliers=False,
               boxprops=dict(facecolor=color, edgecolor=color, alpha=0.8),
               medianprops=dict(color="black", linewidth=1.0),
               whiskerprops=dict(color=color, linewidth=0.8),
               capprops=dict(color=color, linewidth=0.8))

    _draw(succ_stats, succ_pos, C_SUCCESS)
    _draw(fail_stats, fail_pos, C_FAIL)

    ax.set_yscale("log")
    ax.set_xticks(range(len(top)))
    ax.set_xticklabels(_abbrev_tool_labels(top), rotation=45, ha="right",
                       rotation_mode="anchor", fontsize=paper_style.TICK_SIZE)
    ax.set_xlim(-0.6, len(top) - 0.4)
    paper_style.style_ax(ax, ylabel="Duration (ms)")
    ax.grid(True, alpha=0.3, axis="y")
    ax.set_axisbelow(True)

    ax2 = ax.twinx()
    ax2.plot(range(len(top)), rate, "o-", color=C_RATE, linewidth=1.2,
             markersize=3, label="Success rate")
    ax2.set_ylabel("Success Rate (%)", fontsize=paper_style.FONT_SIZE)
    lo = np.nanmin(rate)
    ax2.set_ylim(max(0, lo - 8), 101)
    ax2.tick_params(axis="y", labelsize=paper_style.TICK_SIZE, direction="in")
    ax2.spines["right"].set_visible(True)

    handles = [
        plt.Rectangle((0, 0), 1, 1, facecolor=C_SUCCESS, alpha=0.8, label="Success dur."),
        plt.Rectangle((0, 0), 1, 1, facecolor=C_FAIL, alpha=0.8, label="Failure dur."),
        plt.Line2D([0], [0], color=C_RATE, marker="o", markersize=3, label="Success rate"),
    ]
    ax.legend(handles=handles, fontsize=paper_style.LEGEND_SIZE, ncol=3,
              loc="lower center", bbox_to_anchor=(0.5, 1.0), frameon=True,
              handletextpad=0.4, columnspacing=1.0)
    paper_style.save_fig(fig, "tool_duration_by_status", output_dir=output_dir,
                         pad_inches=0.03)


def tool_token_delta_by_status(df: pd.DataFrame, output_dir: str):
    """Per-tool prompt-token delta box plots (success vs failure) for the top 15 tools.

    Token delta = the increase in prompt tokens on the next LLM call after the
    tool ran, attributed to that tool (how many tokens each tool adds to the
    context). Box style mirrors ``tool_duration_by_status`` on a log y-axis with
    human-friendly token ticks. Expects: toolName, toolStatus, callCount,
    p5, p25, p50, p75, p95.
    """
    needed = {"toolName", "toolStatus", "callCount", "p5", "p25", "p50", "p75", "p95"}
    if not needed.issubset(df.columns):
        print("  Skipping tool_token_delta_by_status (missing box columns)")
        return

    top = df.groupby("toolName")["callCount"].sum().nlargest(15).index.tolist()
    d = df.set_index(["toolName", "toolStatus"])
    width = 0.36
    C_SUCCESS, C_FAIL = "#55A868", "#C44E52"

    def _bxstat(row):
        def _floor(v):  # keep strictly positive for log scale
            return max(float(v), 1.0)
        return dict(med=_floor(row["p50"]), q1=_floor(row["p25"]), q3=_floor(row["p75"]),
                    whislo=_floor(row["p5"]), whishi=_floor(row["p95"]), fliers=[])

    succ_stats, succ_pos, fail_stats, fail_pos = [], [], [], []
    for i, t in enumerate(top):
        if (t, 1) in d.index:
            succ_stats.append(_bxstat(d.loc[(t, 1)])); succ_pos.append(i - width / 2)
        if (t, 2) in d.index:
            fail_stats.append(_bxstat(d.loc[(t, 2)])); fail_pos.append(i + width / 2)

    fig, ax = plt.subplots(figsize=(3.6, 3.0))

    def _draw(stats, pos, color):
        if not stats:
            return
        ax.bxp(stats, positions=pos, widths=width, patch_artist=True, showfliers=False,
               boxprops=dict(facecolor=color, edgecolor=color, alpha=0.8),
               medianprops=dict(color="black", linewidth=1.0),
               whiskerprops=dict(color=color, linewidth=0.8),
               capprops=dict(color=color, linewidth=0.8))

    _draw(succ_stats, succ_pos, C_SUCCESS)
    _draw(fail_stats, fail_pos, C_FAIL)

    ax.set_yscale("log")
    ax.set_xticks(range(len(top)))
    ax.set_xticklabels(_abbrev_tool_labels(top), rotation=45, ha="right",
                       rotation_mode="anchor", fontsize=paper_style.TICK_SIZE)
    ax.set_xlim(-0.6, len(top) - 0.4)
    paper_style.style_ax(ax, ylabel="Prompt Token Delta")
    _set_token_yticks(ax)
    ax.grid(True, alpha=0.3, axis="y")
    ax.set_axisbelow(True)

    handles = [
        plt.Rectangle((0, 0), 1, 1, facecolor=C_SUCCESS, alpha=0.8, label="Success"),
        plt.Rectangle((0, 0), 1, 1, facecolor=C_FAIL, alpha=0.8, label="Failure"),
    ]
    ax.legend(handles=handles, fontsize=paper_style.LEGEND_SIZE, ncol=2,
              loc="lower center", bbox_to_anchor=(0.5, 1.0), frameon=True,
              handletextpad=0.4, columnspacing=1.0)
    paper_style.save_fig(fig, "tool_token_delta_by_status", output_dir=output_dir,
                         pad_inches=0.03)


def tool_driven_idle_time_cdf(df: pd.DataFrame, output_dir: str, xlim=None):
    """CDF of container/KV idle times driven by tool execution gaps."""
    container = df[df["gapType"] == "container_idle"]["gapMs"].dropna() / 1000.0
    container = container[container > 0]
    kv = df[df["gapType"] == "kv_idle"]["gapMs"].dropna() / 1000.0
    kv = kv[kv > 0]

    fig, ax = plt.subplots(figsize=paper_style.SINGLE_COL)
    if len(container) > 0:
        vals = np.sort(container.values)
        cdf = np.arange(1, len(vals) + 1) / len(vals)
        ax.plot(vals, cdf, color=paper_style.COLOR_TOOL, linewidth=1.5, label="Container")
        _annotate_median(ax, vals, paper_style.COLOR_TOOL, y_text=0.62, ha="left")
    if len(kv) > 0:
        vals = np.sort(kv.values)
        cdf = np.arange(1, len(vals) + 1) / len(vals)
        ax.plot(vals, cdf, color=paper_style.COLOR_LLM, linewidth=1.5, label="KV Cache")
        _annotate_median(ax, vals, paper_style.COLOR_LLM, y_text=0.38, ha="right")

    ax.set_xscale("log")
    paper_style.style_ax(ax, xlabel="Idle Time (log)", ylabel="CDF of Idle Gaps",
                         keep_all_spines=True, grid_y=True)
    ax.legend(fontsize=paper_style.LEGEND_SIZE)
    ax.set_ylim(0, 1.05)
    if xlim is not None:
        ax.set_xlim(xlim)
    _set_time_xticks(ax, "s")
    paper_style.save_fig(fig, "tool_driven_idle_time_cdf", output_dir=output_dir)


def user_idle_time_cdf(df: pd.DataFrame, output_dir: str, xlim=None):
    """CDF of user idle time (inter-turn gaps) per session."""
    if "userIdleMs" in df.columns:
        idle_sec = df["userIdleMs"].dropna() / 1000.0
        idle_sec = idle_sec[idle_sec > 0]
    elif "gapType" in df.columns:
        inter = df[df["gapType"] == "inter_turn"]["gapMs"].dropna() / 1000.0
        idle_sec = inter[inter > 0]
    else:
        print("  Skipping user_idle_time_cdf (no idle time data)")
        return

    sorted_vals = np.sort(idle_sec.values)
    cdf = np.arange(1, len(sorted_vals) + 1) / len(sorted_vals)

    fig, ax = plt.subplots(figsize=paper_style.SINGLE_COL)
    ax.plot(sorted_vals, cdf, color=paper_style.COLOR_USER_IDLE, linewidth=1.5,
            label="User Idle")
    _annotate_median(ax, sorted_vals, paper_style.COLOR_USER_IDLE, y_text=0.62, ha="right")
    ax.set_xscale("log")
    paper_style.style_ax(ax, xlabel="Idle Time (log)", ylabel="CDF of Sessions",
                         keep_all_spines=True, grid_y=True)
    ax.legend(fontsize=paper_style.LEGEND_SIZE)
    ax.set_ylim(0, 1.05)
    if xlim is not None:
        ax.set_xlim(xlim)
    _set_time_xticks(ax, "s")
    paper_style.save_fig(fig, "user_idle_time_cdf", output_dir=output_dir)


def tool_duration_cdf(df: pd.DataFrame, output_dir: str):
    """CDF of per-call tool execution times, one line per tool type.

    Input: DataFrame with columns toolName, toolDurMs (raw per-call data).
    """
    if "toolName" not in df.columns or "toolDurMs" not in df.columns:
        print("  Skipping tool_duration_cdf (missing columns)")
        return

    fig, ax = plt.subplots(figsize=(4, 2.4))

    # Cap to the most-used tools by call count: the legend expands below the
    # axes (mode="expand"), so an unbounded tool count (e.g. hundreds of MCP /
    # custom tools) balloons the figure height and makes the plot unreadable.
    # Days with <= _TOOL_CDF_MAX_TOOLS distinct tools are unaffected.
    _TOOL_CDF_MAX_TOOLS = 12
    tools = (df.groupby("toolName")["toolDurMs"].count()
             .sort_values(ascending=False).index.tolist())[:_TOOL_CDF_MAX_TOOLS]

    colors = paper_style.CATEGORY_COLORS
    for i, tool in enumerate(tools):
        values = np.sort(df.loc[df["toolName"] == tool, "toolDurMs"].dropna().values)
        if len(values) == 0:
            continue
        cdf = np.arange(1, len(values) + 1) / len(values)
        ax.step(values, cdf, where="post",
                label=f"{tool}",
                color=colors[i % len(colors)], linewidth=1.2)

    ax.set_xscale("log")
    paper_style.style_ax(ax, xlabel="Duration (log scale)", ylabel="CDF of Tool Calls",
                         keep_all_spines=True, grid_y=True)
    ax.legend(fontsize=paper_style.LEGEND_SIZE - 1, loc="upper left",
              bbox_to_anchor=(0.0, -0.42, 1.0, 0.12), mode="expand",
              ncol=3, frameon=True, borderaxespad=0.0)
    ax.set_ylim(0, 1.05)
    _set_time_xticks(ax, "ms")
    paper_style.save_fig(fig, "tool_duration_cdf", output_dir=output_dir,
                         pad_inches=0.05)


def tool_duration_cdf_total(df: pd.DataFrame, output_dir: str, llm_df: pd.DataFrame = None):
    """CDF of all tool-call durations and (optionally) all LLM-call durations.

    Tool line = seagreen, LLM line = darkorange (consistent with other figures).
    Medians are drawn as dashed vertical lines (not in the legend) and annotated
    as colored text.
    """
    if "toolDurMs" not in df.columns:
        print("  Skipping tool_duration_cdf_total (missing toolDurMs)")
        return

    def _fmt(v):
        return f"{v / 1000:.1f}s" if v >= 1000 else f"{v:.0f}ms"

    fig, ax = plt.subplots(figsize=paper_style.WIDE)

    # Tool-call durations
    tool_vals = np.sort(df["toolDurMs"].dropna().values)
    tool_vals = tool_vals[tool_vals > 0]
    tcdf = np.arange(1, len(tool_vals) + 1) / len(tool_vals)
    ax.step(tool_vals, tcdf, where="post", color="seagreen", linewidth=1.5,
            label="Tool call")
    tool_med = float(np.median(tool_vals))
    ax.axvline(tool_med, color="seagreen", linestyle="--", linewidth=1.0, alpha=0.9)
    ax.text(tool_med / 1.2, 0.88, _fmt(tool_med), color="seagreen", ha="right",
            va="center", fontsize=paper_style.TICK_SIZE, fontweight="bold",
            transform=ax.get_xaxis_transform())

    # LLM-call durations
    if llm_df is not None and "llmDurMs" in llm_df.columns:
        llm_vals = np.sort(llm_df["llmDurMs"].dropna().values)
        llm_vals = llm_vals[llm_vals > 0]
        lcdf = np.arange(1, len(llm_vals) + 1) / len(llm_vals)
        ax.step(llm_vals, lcdf, where="post", color="darkorange", linewidth=1.5,
                label="LLM call")
        llm_med = float(np.median(llm_vals))
        ax.axvline(llm_med, color="darkorange", linestyle="--", linewidth=1.0, alpha=0.9)
        ax.text(llm_med * 1.2, 0.18, _fmt(llm_med), color="darkorange", ha="left",
                va="center", fontsize=paper_style.TICK_SIZE, fontweight="bold",
                transform=ax.get_xaxis_transform())

    ax.set_xscale("log")
    paper_style.style_ax(ax, xlabel="Duration (log scale)", ylabel="CDF of Calls",
                         keep_all_spines=True, grid_y=True)
    ax.legend(fontsize=paper_style.LEGEND_SIZE, loc="upper left")
    ax.set_ylim(0, 1.05)
    _set_time_xticks(ax, "ms")
    paper_style.save_fig(fig, "tool_duration_cdf_total", output_dir=output_dir)


def token_type_breakdown(df: pd.DataFrame, output_dir: str):
    """Stacked horizontal bar of token type breakdown (prompt components).

    Uses prompt_type_breakdown.csv.
    """
    if df is None or df.empty:
        print("  Skipping token_type_breakdown (no data)")
        return

    # Expect columns like avgSystemRatio, avgHistoryRatio, etc.
    ratio_cols = [c for c in df.columns if "Ratio" in c or "ratio" in c]
    if not ratio_cols:
        # Alternative: totalPromptTokens, totalCompletionTokens from session_stats
        if "totalPromptTokens" in df.columns and "totalCompletionTokens" in df.columns:
            prompt = df["totalPromptTokens"].sum()
            comp = df["totalCompletionTokens"].sum() if "totalCompletionTokens" in df.columns else (
                df["totalResponseTokens"].sum() if "totalResponseTokens" in df.columns else 0)
            fig, ax = plt.subplots(figsize=paper_style.WIDE)
            total = prompt + comp
            ax.barh("Avg", prompt / total * 100, color=paper_style.COLOR_PROMPT, label="Prompt")
            ax.barh("Avg", comp / total * 100, left=prompt / total * 100,
                    color=paper_style.COLOR_COMPLETION, label="Completion")
            paper_style.style_ax(ax, xlabel="Token Share (%)")
            ax.legend(fontsize=paper_style.LEGEND_SIZE)
            paper_style.save_fig(fig, "token_type_breakdown", output_dir=output_dir)
            return
        print("  Skipping token_type_breakdown (no ratio columns)")
        return

    row = df.iloc[0]
    labels = []
    values = []
    for c in ratio_cols:
        val = float(row[c])
        if val > 0.01:
            name = c.replace("avg", "").replace("Ratio", "").replace("ratio", "")
            labels.append(name)
            values.append(val * 100)

    fig, ax = plt.subplots(figsize=paper_style.WIDE)
    colors = [paper_style.MS_BLUE, paper_style.MS_RED, paper_style.MS_GREEN,
              paper_style.MS_YELLOW, paper_style.MS_GRAY, "#7B68EE", "#8C564B",
              "#E377C2", "#17BECF", "#BCBD22"]
    left = 0
    for i, (lbl, val) in enumerate(zip(labels, values)):
        ax.barh("Avg per Call", val, left=left, color=colors[i % len(colors)],
                edgecolor="white", linewidth=0.5, label=lbl)
        left += val
    paper_style.style_ax(ax, xlabel="Token Share (%)")
    ax.legend(fontsize=paper_style.LEGEND_SIZE, ncol=2, loc="upper right")
    ax.set_xlim(0, 100)
    paper_style.save_fig(fig, "token_type_breakdown", output_dir=output_dir)


def model_share_trend(df: pd.DataFrame, output_dir: str,
                      name: str = "model_share_trend", week_labels: bool = True):
    """100%-stacked bars of agent model request share across four sampled days.

    Input CSV columns: day, model, rank, pct — the top 7 models plus ``Others``.
    Styled to match ``token_type_breakdown`` (MS palette, white segment borders,
    sans-serif). When ``week_labels`` the x-axis is anonymized to ``Week 1..N``;
    otherwise the real dates are shown.
    """
    if df is None or df.empty:
        print("  Skipping model_share_trend (no data)")
        return

    days = sorted(df["day"].unique())
    order = (df[["model", "rank"]].drop_duplicates()
             .sort_values("rank")["model"].tolist())
    piv = df.pivot_table(index="model", columns="day", values="pct",
                         fill_value=0).reindex(order)[days]

    palette = [paper_style.MS_BLUE, paper_style.MS_RED, paper_style.MS_GREEN,
               paper_style.MS_YELLOW, "#7B68EE", "#8C564B", "#E377C2"]
    color_map, ci = {}, 0
    for m in order:
        if m == "Others":
            color_map[m] = paper_style.MS_GRAY
        else:
            color_map[m] = palette[ci % len(palette)]
            ci += 1

    if week_labels:
        xlabels = [f"Week {i + 1}" for i in range(len(days))]
    else:
        xlabels = [pd.to_datetime(d).strftime("%b %d") for d in days]

    with plt.rc_context({"font.family": "sans-serif"}):
        fig, ax = plt.subplots(figsize=(3.4, 3.0))
        x = np.arange(len(days))
        bottom = np.zeros(len(days))
        for m in order:
            vals = piv.loc[m].values
            ax.bar(x, vals, 0.62, bottom=bottom, label=m, color=color_map[m],
                   edgecolor="white", linewidth=0.5)
            for xi, (v, b) in enumerate(zip(vals, bottom)):
                if v >= 5:
                    ax.text(xi, b + v / 2, f"{v:.0f}", ha="center", va="center",
                            fontsize=paper_style.TICK_SIZE - 1, color="white",
                            fontweight="bold")
            bottom += vals

        paper_style.style_ax(ax, ylabel="Request Share (%)")
        ax.set_xticks(x)
        ax.set_xticklabels(xlabels)
        ax.set_ylim(0, 100)
        ax.legend(fontsize=paper_style.LEGEND_SIZE - 1, frameon=True,
                  loc="upper center", bbox_to_anchor=(0.5, -0.07), ncol=4,
                  columnspacing=0.9, handlelength=1.0, handletextpad=0.4)
        paper_style.save_fig(fig, name, output_dir=output_dir)


def turn_calls_weekday_weekend_bars(df: pd.DataFrame, output_dir: str):
    """Weekday-vs-weekend per-turn LLM & tool call counts (grouped bars)."""
    _calls_weekday_weekend_bars(df, output_dir,
                                "turn_calls_weekday_weekend_bars", "Turn")


def model_switch_family_direction(df: pd.DataFrame, output_dir: str):
    """Bar chart of VS main-model switches by family relation and strength direction."""
    required = {"switchDetail", "switchCount", "pctSwitches"}
    if not required.issubset(df.columns):
        print("  Skipping model_switch_family_direction (missing columns)")
        return

    order = [
        "same-family upgrade",
        "same-family downgrade",
        "same-family lateral",
        "diff-family upgrade",
        "diff-family downgrade",
        "diff-family lateral",
    ]
    labels = {
        "same-family upgrade": "Same-family\nupgrade",
        "same-family downgrade": "Same-family\ndowngrade",
        "same-family lateral": "Same-family\nlateral",
        "diff-family upgrade": "Diff-family\nupgrade",
        "diff-family downgrade": "Diff-family\ndowngrade",
        "diff-family lateral": "Diff-family\nlateral",
    }
    colors = [
        paper_style.MS_GREEN,
        paper_style.MS_RED,
        paper_style.MS_BLUE,
        "#59A14F",
        "#E15759",
        "#B07AA1",
    ]

    d = df.copy()
    d["switchCount"] = pd.to_numeric(d["switchCount"], errors="coerce")
    d["pctSwitches"] = pd.to_numeric(d["pctSwitches"], errors="coerce")
    d = d.dropna(subset=["switchCount", "pctSwitches"])
    d = d[d["switchDetail"].isin(order)]
    d["_order"] = d["switchDetail"].map({name: i for i, name in enumerate(order)})
    d = d.sort_values("_order")
    if d.empty:
        print("  Skipping model_switch_family_direction (no classified switches)")
        return

    x = np.arange(len(d))
    fig, ax = plt.subplots(figsize=paper_style.WIDE)
    bars = ax.bar(x, d["pctSwitches"], width=0.72, color=colors[:len(d)],
                  edgecolor="white", linewidth=0.6)
    for bar, pct in zip(bars, d["pctSwitches"]):
        if pct >= 1:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                    f"{pct:.1f}", ha="center", va="bottom",
                    fontsize=paper_style.TICK_SIZE - 0.5)

    ax.set_xticks(x)
    ax.set_xticklabels([labels[v] for v in d["switchDetail"]],
                       fontsize=paper_style.TICK_SIZE - 0.5)
    paper_style.style_ax(ax, ylabel="Switches (%)", grid_y=True)
    ax.set_ylim(0, max(d["pctSwitches"]) * 1.18)
    paper_style.save_fig(fig, "model_switch_family_direction",
                         output_dir=output_dir, pad_inches=0.03)


def _format_hourly_axis(ax):
    """Format x-axis for hourly data spanning a few days.

    Major ticks label each day (UTC midnight); light dashed vertical gridlines
    at every midnight make the diurnal (day/night) cycle easy to read.
    """
    ax.xaxis.set_major_locator(mdates.DayLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    ax.xaxis.set_minor_locator(mdates.HourLocator(byhour=[6, 12, 18]))
    ax.tick_params(axis="x", which="major", labelrotation=45)
    ax.tick_params(axis="x", which="minor", length=1.5)
    for label in ax.get_xticklabels():
        label.set_ha("right")
    ax.grid(True, which="major", axis="x", linestyle="--",
            linewidth=0.5, alpha=0.5)
    ax.set_axisbelow(True)


def _human_readable_formatter():
    """Return a ticker formatter that shows 1K, 1M, 1B, 1T etc."""
    return paper_style.human_readable_formatter()


def _apply_human_fmt(ax):
    """Apply human-readable formatting to y-axis."""
    ax.yaxis.set_major_formatter(_human_readable_formatter())


def plot_normalized_trends(df: pd.DataFrame, output_dir: str,
                           time_col: str = "day", hourly: bool = False):
    """Plot sessions, LLM calls, tokens, and tool calls normalized to first bin = 1.

    Parameters
    ----------
    time_col : str
        Name of the datetime column on the x-axis ("day" for daily, "ts" for hourly).
    hourly : bool
        If True, use the per-day/midnight-gridline hourly axis formatter.
    """
    fmt_axis = _format_hourly_axis if hourly else _format_date_axis
    base_label = "hour 1" if hourly else "day 1"

    # Prefer total (prompt + completion) tokens when completion is available.
    if "totalCompletionTokens" in df.columns and "totalPromptTokens" in df.columns:
        df = df.copy()
        df["totalTokens"] = df["totalPromptTokens"] + df["totalCompletionTokens"]
        token_col, token_label = "totalTokens", "Tokens (Total)"
    else:
        token_col, token_label = "totalPromptTokens", "Tokens (Prompt)"

    with plt.rc_context({"font.family": "sans-serif"}):
        fig, ax = plt.subplots(figsize=paper_style.WIDE)

        metrics = [
            ("sessions", "Sessions", "steelblue"),
            ("llmCalls", "LLM Calls", "darkorange"),
            (token_col, token_label, paper_style.COLOR_COMPLETION),
            ("toolCalls", "Tool Calls", "seagreen"),
        ]
        for col, label, color in metrics:
            base = df[col].iloc[0] if df[col].iloc[0] > 0 else 1
            ax.plot(df[time_col], df[col] / base, label=label, color=color, linewidth=1.2)

        ax.axhline(1, color="gray", linestyle="--", linewidth=0.8, alpha=0.5)
        paper_style.style_ax(ax, ylabel="Normalized Volume")
        ax.legend(fontsize=paper_style.LEGEND_SIZE, frameon=True)
        fmt_axis(ax)

        paper_style.save_fig(fig, "normalized_trends", output_dir=output_dir)


# User-type colours + display order, shared by the hourly active-user figure.
USER_TYPE_SERIES = [
    ("readers", "Readers", "steelblue"),
    ("coders", "Coders", "seagreen"),
    ("terminal", "Terminal", "darkorange"),
    ("deeploop", "Deep-loop", "#c44e52"),
    ("chatonly", "Chat-only", "#9467bd"),
]


def plot_user_type_hourly(df: pd.DataFrame, output_dir: str,
                          time_col: str = "ts", hourly: bool = True):
    """Hourly count of distinct active users per user-type, each normalized to
    its own first hour = 1.

    Mirrors ``plot_normalized_trends``: one line per user-type (Readers, Coders,
    Terminal, Deep-loop, Chat-only), indexed to the first hour so the relative
    day-of-week / diurnal dynamics of each type are comparable. Users are
    classified once from whole-week behaviour during aggregation; the CSV
    carries one distinct-active-user count per type per hour.
    """
    fmt_axis = _format_hourly_axis if hourly else _format_date_axis

    with plt.rc_context({"font.family": "sans-serif"}):
        fig, ax = plt.subplots(figsize=paper_style.WIDE)

        for col, label, color in USER_TYPE_SERIES:
            if col not in df.columns:
                continue
            base = df[col].iloc[0] if df[col].iloc[0] > 0 else 1
            ax.plot(df[time_col], df[col] / base, label=label, color=color, linewidth=1.2)

        ax.axhline(1, color="gray", linestyle="--", linewidth=0.8, alpha=0.5)
        paper_style.style_ax(ax, ylabel="Normalized Users")
        ax.legend(fontsize=paper_style.LEGEND_SIZE, frameon=True, ncol=2)
        fmt_axis(ax)

        paper_style.save_fig(fig, "user_type_hourly", output_dir=output_dir)


def plot_session_avg_trends_compact(df: pd.DataFrame, output_dir: str,
                                    time_col: str = "day", hourly: bool = False):
    """Per-session averages as three stacked, shared-x subfigures.

    1. LLM calls & tool calls per session (overlaid).
    2. Prompt tokens per session.
    3. Completion tokens per session.
    """
    fmt_axis = _format_hourly_axis if hourly else _format_date_axis

    with plt.rc_context({"font.family": "sans-serif"}):
        fig, axes = plt.subplots(3, 1, figsize=(3.5, 3.4), sharex=True)

        ax = axes[0]
        ax.plot(df[time_col], df["avgLlmCallsPerSession"], color="darkorange",
                linewidth=1.2, label="LLM Calls")
        ax.plot(df[time_col], df["avgToolCallsPerSession"], color="seagreen",
                linewidth=1.2, label="Tool Calls")
        paper_style.style_ax(ax, ylabel="Calls")
        ax.legend(fontsize=paper_style.LEGEND_SIZE, frameon=True, loc="upper left")

        ax = axes[1]
        ax.plot(df[time_col], df["avgPromptTokensPerSession"], color="#4c78a8", linewidth=1.2)
        paper_style.style_ax(ax, ylabel="Prompt Tokens")
        _apply_human_fmt(ax)

        ax = axes[2]
        ax.plot(df[time_col], df["avgCompletionTokensPerSession"], color="#f58518", linewidth=1.2)
        paper_style.style_ax(ax, ylabel="Completion Tokens")

        # Shared x-axis: gridlines on every panel, tick labels only on the bottom.
        for ax in axes:
            fmt_axis(ax)
        for ax in axes[:-1]:
            ax.tick_params(axis="x", labelbottom=False)
        # Pad the data range by ~12% so lines aren't glued to the axis edges,
        # without forcing a (misleading) zero baseline on these trend panels.
        for ax, col in ((axes[0], "avgLlmCallsPerSession"),
                        (axes[1], "avgPromptTokensPerSession"),
                        (axes[2], "avgCompletionTokensPerSession")):
            lo = float(df[col].min())
            hi = float(df[col].max())
            if col == "avgLlmCallsPerSession":
                lo = min(lo, float(df["avgToolCallsPerSession"].min()))
                hi = max(hi, float(df["avgToolCallsPerSession"].max()))
            pad = 0.12 * (hi - lo)
            ax.set_ylim(max(0.0, lo - pad), hi + pad)

        fig.align_ylabels(axes)
        paper_style.save_fig(fig, "session_avg_trends", output_dir=output_dir)


def plot_session_percentile_trends_compact(df: pd.DataFrame, output_dir: str,
                                           time_col: str = "day", hourly: bool = False):
    """Per-session percentile (P25/P50/P75/P95) trends as four stacked, shared-x subfigures.

    Mirrors ``plot_session_avg_trends_compact`` but shows the distribution across
    sessions active in each hour (each session's per-hour metric summed first).

    1. LLM calls per session.
    2. Tool calls per session.
    3. Prompt tokens per session.
    4. Completion tokens per session.
    """
    from matplotlib.lines import Line2D

    fmt_axis = _format_hourly_axis if hourly else _format_date_axis

    # Percentile -> color (light/low to dark/high), consistent across all panels.
    pctl_colors = [
        ("p25", "P25", "#9ecae1"),
        ("p50", "P50", "#4292c6"),
        ("p75", "P75", "#f58518"),
        ("p95", "P95", "#c44e52"),
    ]
    panels = [
        ("LlmCalls", "LLM Calls", False),
        ("ToolCalls", "Tool Calls", False),
        ("PromptTokens", "Prompt Tokens", True),
        ("CompletionTokens", "Completion Tokens", True),
    ]

    with plt.rc_context({"font.family": "sans-serif"}):
        fig, axes = plt.subplots(4, 1, figsize=(3.5, 4.4), sharex=True)

        for ax, (metric, ylabel, human) in zip(axes, panels):
            for pctl, _, color in pctl_colors:
                lw = 1.4 if pctl == "p50" else 1.1
                ax.plot(df[time_col], df[f"{pctl}{metric}"], color=color, linewidth=lw)
            paper_style.style_ax(ax, ylabel=ylabel)
            if human:
                ax.set_yscale("log")
                _apply_human_fmt(ax)

        legend_handles = [
            Line2D([0], [0], color=color, linewidth=1.3, label=label)
            for _, label, color in pctl_colors
        ]
        axes[0].legend(handles=legend_handles, fontsize=paper_style.LEGEND_SIZE,
                       frameon=True, loc="upper left", ncol=4, columnspacing=1.0,
                       handlelength=1.4, handletextpad=0.4)

        # Shared x-axis: gridlines on every panel, tick labels only on the bottom.
        for ax in axes:
            fmt_axis(ax)
        for ax in axes[:-1]:
            ax.tick_params(axis="x", labelbottom=False)

        fig.align_ylabels(axes)
        paper_style.save_fig(fig, "session_percentile_trends", output_dir=output_dir)


def plot_short_medium_long_hourly(df: pd.DataFrame, output_dir: str,
                                  time_col: str = "ts", hourly: bool = True,
                                  percentage: bool = False):
    """Hourly LLM-call volume split into prompt-length buckets (stacked area).

    Buckets use static prompt-token thresholds (short / medium / long /
    extremely long), computed during aggregation and carried in the CSV as
    ``thr1``/``thr2``/``thr3``.

    ``percentage=False`` (default): every bucket is divided by the first-hour
    *total* (all buckets summed), so the top of the stack is indexed to the
    first hour = 1 while the bands show composition.
    ``percentage=True``: every bucket is divided by *its own hour's* total, so
    each stack sums to 100% — the y-axis is the share of requests per bucket.
    The x-axis mirrors ``session_avg_trends``.
    """
    fmt_axis = _format_hourly_axis if hourly else _format_date_axis

    t1 = int(df["thr1"].iloc[0]) if "thr1" in df.columns else None
    t2 = int(df["thr2"].iloc[0]) if "thr2" in df.columns else None
    t3 = int(df["thr3"].iloc[0]) if "thr3" in df.columns else None

    def _fmt(n):
        return f"{n / 1000:.0f}K" if n is not None and n >= 1000 else str(n)

    have = t1 is not None
    series = [
        ("xlongCalls",
         f"Extremely Long (>{_fmt(t3)})" if have else "Extremely Long", "#c44e52"),
        ("longCalls",
         f"Long ({_fmt(t2)}\u2013{_fmt(t3)})" if have else "Long", "seagreen"),
        ("mediumCalls",
         f"Medium ({_fmt(t1)}\u2013{_fmt(t2)})" if have else "Medium", "darkorange"),
        ("shortCalls", f"Short (\u2264{_fmt(t1)})" if have else "Short", "steelblue"),
    ]

    cols = [c for c, _, _ in series]
    if percentage:
        row_total = df[cols].sum(axis=1).replace(0, np.nan)
        stacks = [df[c] / row_total * 100 for c in cols]
    else:
        first_total = float(df[cols].iloc[0].sum())
        base = first_total if first_total > 0 else 1.0
        stacks = [df[c] / base for c in cols]

    with plt.rc_context({"font.family": "sans-serif"}):
        fig, ax = plt.subplots(figsize=paper_style.WIDE)

        labels = [label for _, label, _ in series]
        colors = [color for _, _, color in series]
        ax.stackplot(df[time_col], *stacks, labels=labels, colors=colors, alpha=0.85)

        if percentage:
            paper_style.style_ax(ax, ylabel="Share of Requests (%)")
            ax.set_ylim(0, 100)
        else:
            ax.axhline(1, color="gray", linestyle="--", linewidth=0.8, alpha=0.5)
            paper_style.style_ax(ax, ylabel="Normalized Calls")
            ax.set_ylim(bottom=0)
        ax.margins(x=0)
        ax.legend(fontsize=paper_style.LEGEND_SIZE, frameon=True, loc="upper right")
        fmt_axis(ax)

        name = "short_medium_long_hourly_percentage" if percentage else "short_medium_long_hourly"
        paper_style.save_fig(fig, name, output_dir=output_dir)


def plot_tool_time_nested_by_bucket(df: pd.DataFrame, output_dir: str):
    """100%-stacked bar: overlapped vs independent share of tool time per bucket."""
    # Match the sans-serif fallback used by the other figures (seaborn's import
    # in this module otherwise lets Times New Roman resolve here only).
    plt.rcParams["font.family"] = "sans-serif"

    df = df.copy()
    df["overlapMs"] = df["maxOverlapMs"].clip(upper=df["toolDurMs"])
    df["independentMs"] = df["toolDurMs"] - df["overlapMs"]

    buckets = [
        ("< 50ms", 0, 50),
        ("50\u2013500ms", 50, 500),
        ("0.5\u20135s", 500, 5000),
        ("5\u201330s", 5000, 30000),
        ("30s+", 30000, 9999999),
    ]

    names = []
    overlap_pct = []
    indep_pct = []
    batch_pct = []
    total_batches = len(df)
    for name, lo, hi in buckets:
        sub = df[(df["toolDurMs"] >= lo) & (df["toolDurMs"] < hi)]
        ov = sub["overlapMs"].sum()
        ind = sub["independentMs"].sum()
        total = ov + ind
        names.append(name)
        overlap_pct.append(ov / total * 100 if total > 0 else 0.0)
        indep_pct.append(ind / total * 100 if total > 0 else 0.0)
        batch_pct.append(len(sub) / total_batches * 100 if total_batches > 0 else 0.0)

    fig, ax = plt.subplots(figsize=paper_style.WIDE)
    x = np.arange(len(names))
    width = 0.6

    ax.bar(x, overlap_pct, width, color=paper_style.MS_RED, alpha=0.85,
           label="Overlapped (inside LLM window)")
    ax.bar(x, indep_pct, width, bottom=overlap_pct,
           color=paper_style.MS_BLUE, alpha=0.85,
           label="Independent (outside LLM window)")

    # Label each segment with its share when it is tall enough to fit.
    for i, (ov, ind) in enumerate(zip(overlap_pct, indep_pct)):
        if ov >= 7:
            ax.text(i, ov / 2, f"{ov:.0f}%", ha="center", va="center",
                    fontsize=paper_style.TICK_SIZE, color="white", fontweight="bold")
        if ind >= 7:
            ax.text(i, ov + ind / 2, f"{ind:.0f}%", ha="center", va="center",
                    fontsize=paper_style.TICK_SIZE, color="white", fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels([f"{n}\n({p:.0f}%)" for n, p in zip(names, batch_pct)])
    ax.set_ylim(0, 100)
    paper_style.style_ax(ax, xlabel="Tool Batch Duration Bucket (with % over All Batches)",
                         ylabel="Share of Tool Time (%)")
    ax.grid(True, alpha=0.3, axis="y")
    ax.set_axisbelow(True)

    paper_style.add_legend(ax, loc="lower left")
    paper_style.save_fig(fig, "tool_time_nested_by_bucket",
                         output_dir=output_dir, pad_inches=0.15)
    print("  Saved tool_time_nested_by_bucket.pdf")


GAP = ("gap",)


ROWS = [
    ("step", "9.1s", "get_file", "76ms", False),
    ("step", "4.0s", "run_build", "28ms", False),
    ("step", "3.8s", "get_errors", "30ms", False),
    GAP,
    ("step", "6.9s", "run_command", "37ms", True),   # <- failure
    ("step", "4.3s", "get_errors", "44ms", False),
    ("step", "5.9s", "edit_file", "1.0s", False),
    ("step", "7.4s", "run_build", "52ms", False),
    GAP,
    ("step", "12.1s", "run_command", "17ms", False),  # eventual success
]


COL_LLM = "#F5A623"


COL_TOOL = "#4C78A8"


COL_FAIL = "#C0202A"


COL_ARC = "#9A9A9A"


COL_BAND = "#C0202A"


X_LLM = 0.18


LLM_W, LLM_H = 0.32, 0.052


X_TOOL = 0.55


TOOL_R = 0.026


X_TLABEL = 0.61


FS_NODE = 6.8


FS_LABEL = 6.8


def _weights():
    return [1.0 if r[0] == "step" else 0.55 for r in ROWS]


def _centers(top=0.88, bottom=0.15):
    w = _weights()
    unit = (top - bottom) / sum(w)
    ys, y = [], top
    for wi in w:
        ys.append(y - unit * wi / 2)
        y -= unit * wi
    return ys


def _arc(ax, p0, p1, rad, color=COL_ARC, lw=0.7, ls="-", z=1):
    ax.add_patch(FancyArrowPatch(
        p0, p1, connectionstyle=f"arc3,rad={rad}", arrowstyle="-|>",
        mutation_scale=6, lw=lw, color=color, linestyle=ls,
        shrinkA=1.0, shrinkB=1.0, zorder=z, alpha=0.9))


def deep_loop_failure_flow(output_dir):
    plt.rcParams["font.family"] = "sans-serif"
    ys = _centers(top=0.975, bottom=0.075)
    fig, ax = plt.subplots(figsize=(3.2, 4.9))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # --- shaded band behind the failure -> retry burst -----------------------
    step_idx = [i for i, r in enumerate(ROWS) if r[0] == "step"]
    fail_i = next(i for i, r in enumerate(ROWS) if r[0] == "step" and r[4])
    band_rows = [i for i in step_idx if i >= fail_i]  # failure + retries shown
    y_top = ys[band_rows[0]] + LLM_H
    y_bot = ys[band_rows[-1]] - LLM_H
    ax.add_patch(Rectangle((0.01, y_bot), 0.98, y_top - y_bot,
                           facecolor=COL_BAND, alpha=0.07, edgecolor="none",
                           zorder=0))
    ax.text(0.965, (y_top + y_bot) / 2,
            "failure \u2192 retry burst\n(extra LLM calls, tools, compute)",
            rotation=90, ha="center", va="center", fontsize=6.0,
            color=COL_FAIL, fontweight="bold")

    # --- draw path arcs (LLM -> tool -> next LLM) ----------------------------
    prev_tool = None
    gap_pending = False
    for i, row in enumerate(ROWS):
        if row[0] == "gap":
            ax.text(X_LLM, ys[i], "...", ha="center", va="center",
                    rotation=90, fontsize=11, color="#666")
            ax.text(X_TOOL, ys[i], "...", ha="center", va="center",
                    rotation=90, fontsize=11, color="#666")
            gap_pending = True
            continue
        y = ys[i]
        is_fail = row[4]
        # tool -> this LLM (from previous step)
        if prev_tool is not None:
            ls = (0, (2, 2)) if gap_pending else "-"
            _arc(ax, prev_tool, (X_LLM - LLM_W / 2 + 0.01, y),
                 rad=0.28, ls=ls)
        gap_pending = False
        # LLM -> tool (this step); color the failing hop red
        hop_color = COL_FAIL if is_fail else COL_ARC
        _arc(ax, (X_LLM + LLM_W / 2 - 0.01, y), (X_TOOL - TOOL_R, y),
             rad=0.06, color=hop_color, lw=1.1 if is_fail else 0.7)
        prev_tool = (X_TOOL, y)

    # --- nodes (drawn on top) ------------------------------------------------
    for i, row in enumerate(ROWS):
        if row[0] == "step":
            _, llm_dur, tool, tool_dur, is_fail = row
            y = ys[i]
            # LLM box
            ax.add_patch(FancyBboxPatch(
                (X_LLM - LLM_W / 2, y - LLM_H / 2), LLM_W, LLM_H,
                boxstyle="round,pad=0.006,rounding_size=0.02",
                facecolor=COL_LLM, edgecolor="#B9791A", lw=0.6, zorder=3))
            ax.text(X_LLM, y, f"LLM call  \u00b7  {llm_dur}", ha="center",
                    va="center", fontsize=FS_NODE, zorder=4)
            # tool circle (scatter marker -> true circle regardless of aspect)
            fill = COL_FAIL if is_fail else COL_TOOL
            ax.scatter([X_TOOL], [y], s=200, c=fill, edgecolors="black",
                       linewidths=0.5, zorder=3)
            if is_fail:
                ax.text(X_TOOL, y, "X", ha="center", va="center",
                        fontsize=7, color="white", fontweight="bold", zorder=4)
            label = f"{tool}  \u00b7  {tool_dur}"
            if is_fail:
                label = f"{tool}  \u00b7  failed"
            ax.text(X_TLABEL, y, label, ha="left", va="center",
                    fontsize=FS_LABEL, zorder=4,
                    color=COL_FAIL if is_fail else "black",
                    fontweight="bold" if is_fail else "normal")

    # --- compact legend ------------------------------------------------------
    handles = [
        plt.Line2D([0], [0], marker="s", color="none",
                   markerfacecolor=COL_LLM, markeredgecolor="#B9791A",
                   markersize=8, label="LLM call"),
        plt.Line2D([0], [0], marker="o", color="none",
                   markerfacecolor=COL_TOOL, markeredgecolor="black",
                   markersize=8, label="Tool call"),
        plt.Line2D([0], [0], marker="o", color="none",
                   markerfacecolor=COL_FAIL, markeredgecolor="black",
                   markersize=8, label="Failure"),
    ]
    ax.legend(handles=[h for h in handles], loc="upper center",
              bbox_to_anchor=(0.5, 0.055), ncol=3, frameon=True,
              fontsize=6.5, handletextpad=0.3, columnspacing=1.0,
              borderpad=0.4)

    os.makedirs(output_dir, exist_ok=True)
    paper_style.save_fig(fig, "deep_loop_failure_flow", output_dir=output_dir,
                         pad_inches=0.04)


# ---------------------------------------------------------------------------
# Compaction excess-hole CDF
# ---------------------------------------------------------------------------

_LLM_BINS   = [0, 1, 3, 7, 15, 30, np.inf]
_LLM_LABELS = ["1", "2-3", "4-7", "8-15", "16-30", "31+"]
_TOK_BINS   = [0, 10_000, 30_000, 60_000, 100_000, 150_000, np.inf]
_TOK_LABELS = ["<10K", "10-30K", "30-60K", "60-100K", "100-150K", "150K+"]


def compaction_excess_hole_cdf(df: pd.DataFrame, output_dir: str):
    """Two-panel CDF of bucket-adjusted compaction time-hole excess.

    Panel A: compaction turns vs centred non-compaction (overall).
    Panel B: compaction turns broken out by #LLM-call bucket.

    ``df`` is ``vs_compaction_turn_hole.csv`` which contains one row per turn
    with columns: holePct, llmCalls, promptTokens, hasCompaction,
    llm_bucket, tok_bucket, nocomp_avg, excess_hole_pct.
    """
    plt.rcParams.update({"font.family": "sans-serif"})

    # --- re-derive excess for non-compaction (centred) -----------------------
    df = df.copy()
    df["excess_hole_pct"] = df["excess_hole_pct"].astype(float)
    df["nocomp_avg"]      = df["nocomp_avg"].astype(float)
    df["holePct"]         = df["holePct"].astype(float)
    df["hasCompaction"]   = df["hasCompaction"].astype(bool)
    df["llm_bucket"]      = df["llm_bucket"].astype(str)

    comp   = df[df["hasCompaction"]  & df["excess_hole_pct"].notna()]
    nocomp = df[~df["hasCompaction"] & df["nocomp_avg"].notna()].copy()
    nocomp["excess_hole_pct"] = nocomp["holePct"] - nocomp["nocomp_avg"]

    fig, axes = paper_style.new_fig(figsize=(4, 1.8), ncols=2)

    lw = 1.2
    CLIP = (-100, 100)

    # ── Panel A: overall CDF ─────────────────────────────────────────────────
    ax = axes[0]
    for series, label, color, ls in [
        (comp["excess_hole_pct"],
         f"Compaction (n={len(comp):,})", paper_style.MS_RED, "-"),
        (nocomp["excess_hole_pct"],
         f"Non-compaction (n={len(nocomp):,})", paper_style.MS_BLUE, "--"),
    ]:
        s = np.sort(np.clip(series.values, *CLIP))
        ax.plot(s, np.linspace(0, 1, len(s)), color=color, linewidth=lw,
                linestyle=ls, label=label)

    ax.axvline(0, color=paper_style.MS_GRAY, linewidth=0.7, linestyle=":")

    # annotate P50, P75, P90 of compaction excess
    for p, label in [(0.50, "P50"), (0.75, "P75"), (0.90, "P90")]:
        v = float(np.quantile(comp["excess_hole_pct"].dropna(), p))
        ax.plot(v, p, marker="|", markersize=6,
                color=paper_style.MS_RED, linewidth=1.0, zorder=5)
        ax.annotate(f"{label}\n{v:+.0f}pp",
                    xy=(v, p), xytext=(v + 6, p - 0.12),
                    fontsize=paper_style.LEGEND_SIZE - 1,
                    color=paper_style.MS_RED,
                    arrowprops=dict(arrowstyle="-", color=paper_style.MS_RED,
                                   lw=0.6))

    paper_style.style_ax(ax,
                         xlabel="Excess hole% above bucket baseline (pp)",
                         ylabel="CDF")
    paper_style.add_legend(ax, loc="upper left")
    ax.set_xlim(-80, 100)
    ax.set_ylim(0, 1.02)
    ax.xaxis.set_major_locator(mticker.MultipleLocator(40))
    ax.xaxis.set_minor_locator(mticker.MultipleLocator(10))

    # ── Panel B: by LLM-call bucket (compaction only) ────────────────────────
    ax2 = axes[1]
    palette = [paper_style.MS_BLUE, paper_style.OURS_COLOR_DARK,
               paper_style.MS_GREEN, paper_style.MS_YELLOW,
               paper_style.MS_RED, paper_style.MS_GRAY]
    for llm_b, color in zip(_LLM_LABELS, palette):
        sub = comp[comp["llm_bucket"] == llm_b]["excess_hole_pct"].dropna()
        if len(sub) < 10:
            continue
        s = np.sort(np.clip(sub.values, *CLIP))
        ax2.plot(s, np.linspace(0, 1, len(s)), color=color, linewidth=lw,
                 label=f"{llm_b} LLM (n={len(sub):,})")

    ax2.axvline(0, color=paper_style.MS_GRAY, linewidth=0.7, linestyle=":")
    paper_style.style_ax(ax2,
                         xlabel="Excess hole% above bucket baseline (pp)",
                         ylabel="CDF")
    paper_style.add_legend(ax2, loc="upper left",
                           fontsize=paper_style.LEGEND_SIZE - 1)
    ax2.set_xlim(-80, 100)
    ax2.set_ylim(0, 1.02)
    ax2.xaxis.set_major_locator(mticker.MultipleLocator(40))
    ax2.xaxis.set_minor_locator(mticker.MultipleLocator(10))

    paper_style.save_fig(fig, "compaction_excess_hole_cdf",
                         output_dir=output_dir, pad_inches=0.03)


def compaction_bucket_delta_cdf(df: pd.DataFrame, output_dir: str):
    """CDF of per-bucket mean delta hole% (compaction − non-compaction).

    Each point = one (exact LLM call count × token range) bucket,
    pooled across 7 days. x = avg_hole_comp − avg_hole_nocomp (pp).
    """
    plt.rcParams.update({"font.family": "sans-serif"})

    deltas = np.sort(df["delta_mean"].astype(float).values)
    n = len(deltas)
    y = np.arange(1, n + 1) / n * 100

    fig, ax = paper_style.new_fig(figsize=paper_style.WIDE)

    ax.step(np.append(deltas[0] - 1, deltas), np.append(0, y),
            where="post", color=paper_style.MS_RED, linewidth=1.4)

    ax.axvline(0, color=paper_style.MS_GRAY, linewidth=0.8, linestyle=":")

    for p, label in [(25, "P25"), (50, "P50"), (75, "P75"), (90, "P90")]:
        v = float(np.percentile(deltas, p))
        ax.axvline(v, color=paper_style.MS_GRAY, linewidth=0.7, linestyle="--")
        ax.text(v + 0.4, 2, label, fontsize=paper_style.LEGEND_SIZE - 1,
                color=paper_style.MS_GRAY, rotation=90, va="bottom")

    paper_style.style_ax(
        ax,
        xlabel="Compaction Time (% of Turn Time)",
        ylabel="CDF of Events (%)")
    ax.set_ylim(0, 105)
    ax.yaxis.set_major_locator(mticker.MultipleLocator(20))
    ax.set_xlim(0, 40)
    ax.xaxis.set_major_locator(mticker.MultipleLocator(10))
    ax.xaxis.set_minor_locator(mticker.MultipleLocator(5))
    ax.grid(True, axis="y", linestyle="--", alpha=0.4)

    paper_style.save_fig(fig, "compaction_bucket_delta_cdf",
                         output_dir=output_dir, pad_inches=0.03)


def compaction_token_bucket_delta_cdf(df: pd.DataFrame, output_dir: str):
    """CDF of per-token-bucket mean delta hole% (compaction − non-compaction).

    Each point = one token-range bucket, pooled across 7 days and all LLM counts.
    ``df`` is ``vs_turn_hole_bucket_delta_tok_only_7day.csv``.
    """
    plt.rcParams.update({"font.family": "sans-serif"})

    deltas = np.sort(df["delta_mean"].astype(float).values)
    n = len(deltas)
    y = np.arange(1, n + 1) / n * 100

    fig, ax = paper_style.new_fig(figsize=paper_style.WIDE)

    ax.step(np.append(deltas[0] - 1, deltas), np.append(0, y),
            where="post", color=paper_style.MS_BLUE, linewidth=1.4)

    med = float(np.median(deltas))
    ax.axvline(med, color=paper_style.MS_RED, linestyle="--", linewidth=1.0,
               label=f"Median: {med:.0f}%")

    paper_style.style_ax(
        ax,
        xlabel="Compaction Time (% of Turn Time)",
        ylabel="CDF of Events (%)")
    ax.set_ylim(0, 105)
    ax.yaxis.set_major_locator(mticker.MultipleLocator(20))
    ax.set_xlim(0, 40)
    ax.xaxis.set_major_locator(mticker.MultipleLocator(10))
    ax.xaxis.set_minor_locator(mticker.MultipleLocator(5))
    ax.grid(True, axis="y", linestyle="--", alpha=0.4)
    paper_style.add_legend(ax, loc="lower right")

    paper_style.save_fig(fig, "compaction_token_bucket_delta_cdf",
                         output_dir=output_dir, pad_inches=0.03)
