"""Regenerate the trace-reproducible paper figures from the downloaded traces.

Aggregate the locally-downloaded trace shards into the paper's intermediate
CSVs (``trace_metrics``) -> render PDFs with ``paper_figures`` +
``paper_style`` (the paper's styling/plotting code).

Run from inside this directory::

    python make_figures.py                 # aggregate traces + render
    python make_figures.py --skip-aggregate  # reuse existing data/*.csv

Outputs: ``data/*.csv`` (intermediate) and ``figures/*.pdf`` (final).
"""

import argparse
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import paper_figures as F
import paper_style
import trace_loader
import trace_metrics

_HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(_HERE, "data")
OUT = os.path.join(_HERE, "figures")


def load(name, **kw):
    return pd.read_csv(os.path.join(DATA, name), low_memory=False, **kw)


def llm_parallelism_all(df, output_dir):
    """CDF of LLM parallelism degree over ALL turns (including == 1).

    Companion to ``paper_figures.llm_parallelism`` (which keeps only turns with
    parallelism > 1); mirrors its exact styling, without the filter."""
    col = next((c for c in ("parallelismDegree", "llmParallelism", "maxConcurrency")
                if c in df.columns), None)
    if col is None:
        print("  Skipping llm_parallelism_all (no parallelism column)")
        return
    par = df[col].dropna()
    if par.empty:
        print("  Skipping llm_parallelism_all (empty)")
        return
    fig, ax = plt.subplots(figsize=paper_style.WIDE)
    sorted_vals = np.sort(par.values)
    cdf = np.arange(1, len(sorted_vals) + 1) / len(sorted_vals)
    ax.plot(sorted_vals, cdf, color=paper_style.COLOR_LLM, linewidth=1.5)
    paper_style.style_ax(ax, xlabel="LLM Parallelism Degree (all turns)",
                         ylabel="CDF of Sessions", keep_all_spines=True, grid_y=True)
    ax.set_ylim(0, 1.05)
    paper_style.save_fig(fig, "llm_parallelism_all", output_dir=output_dir)


def _idle_xlim(vs_ss, vs_idle):
    """Shared x-range for the two idle-time CDFs (mirrors paper make_figures)."""
    mins, maxs = [], []
    for gt in ("container_idle", "kv_idle"):
        g = vs_idle[vs_idle["gapType"] == gt]["gapMs"].dropna() / 1000.0
        g = g[g > 0]
        if len(g):
            mins.append(g.min()); maxs.append(g.max())
    u = vs_ss["userIdleMs"].dropna() / 1000.0
    u = u[u > 0]
    if len(u):
        mins.append(u.min()); maxs.append(u.max())
    return (min(mins) / 2.0, max(maxs) * 2.0) if mins else None


def group_a(out):
    """VS figures rendered with matplotlib defaults (no setup_style)."""
    vs_ss = load("vs_session_stats.csv")
    vs_idle = load("vs_idle_gaps.csv")
    idle_xlim = _idle_xlim(vs_ss, vs_idle)

    # Distributions (VS-only variants of the paper's _vs figures).
    F.session_duration_hist_cdf_logscale(vs_ss, out, name_suffix="_vs")
    F.turn_duration_hist_cdf_logscale(vs_ss, out, name_suffix="_vs")
    F.time_breakdown_llm_tool_user_cdf_vs(vs_ss, out)
    F.time_breakdown_llm_tool_cdf_single_turn_vs(vs_ss, out)
    F.time_breakdown_llm_tool_user_cdf_multi_turn_vs(vs_ss, out)
    F.per_turn_calls_cdf(vs_ss, out)
    F.session_turns_cdf(vs_ss, out)
    F.per_session_calls_cdf(vs_ss, out)
    F.per_turn_token_count_cdf(load("vs_per_turn_token_breakdown.csv"), out)

    # Per-call token / cache figures — VS-side reproductions (paper used VS Code).
    per_call = load("vs_per_call_token_breakdown.csv")
    F.token_count_cdf(per_call, out)
    F.cache_hit_rate_cdf(per_call, out)

    F.llm_parallelism(load("vs_llm_parallelism.csv"), out)
    llm_parallelism_all(load("vs_llm_parallelism.csv"), out)
    F.user_idle_time_cdf(vs_ss, out, xlim=idle_xlim)
    F.tool_driven_idle_time_cdf(vs_idle, out, xlim=idle_xlim)

    F.turn_calls_weekday_weekend_bars(load("vs_turn_calls_by_daytype.csv"), out)
    F.tool_parallelism(load("vs_tool_parallelism.csv"), out)
    F.per_tool_parallelism(load("vs_per_tool_parallelism.csv"), out)
    F.tool_usage_bar(load("vs_tool_stats.csv"), out)
    F.error_signal_composition_by_depth(load("vs_deep_loop_error_signal.csv"), out)
    F.model_distribution_anonymized(load("model_distribution.csv"), out)
    F.model_share_trend(load("model_share_trend.csv"), out, week_labels=False)
    F.turn_boundary_cache_rate(load("vs_turn_boundary_cache_agg.csv"), out)

    cbc = load("vs_cache_rate_by_call.csv")
    F.cache_rate_by_call_position_half_col(cbc, out)

    F.cache_rate_vs_idle_boxplot(load("vs_cache_after_user_idle.csv"), out)

    comp = load("vs_compaction_events.csv")
    comp = comp[(comp["prevCachePct"] - comp["TokensCachedPercentage"]) > 0]
    F.compaction_severity(comp, out)
    F.compaction_severity_cache_hit_drop(comp, out)

    F.tool_duration_by_status(load("vs_tool_duration_by_status_box.csv"), out)
    F.tool_token_delta_by_status(load("vs_tool_token_delta_box.csv"), out)

    tdr = load("vs_tool_duration_raw.csv")
    F.tool_duration_cdf(tdr, out)
    F.tool_duration_cdf_total(tdr, out, llm_df=load("vs_llm_duration_raw.csv"))

    F.token_type_breakdown(load("vs_prompt_type_breakdown.csv"), out)


def group_b(out):
    """VS figures rendered after paper_style.setup_style() (sans-serif)."""
    paper_style.setup_style()

    hourly = load("hourly_metrics.csv", parse_dates=["ts"])
    F.plot_normalized_trends(hourly, out, time_col="ts", hourly=True)
    F.plot_session_avg_trends_compact(hourly, out, time_col="ts", hourly=True)

    F.plot_tool_time_nested_by_bucket(load("vs_tool_llm_overlap_clean.csv"), out)

    bucket_delta = load("vs_turn_hole_bucket_delta_tok_only_7day.csv")
    if len(bucket_delta):
        F.compaction_token_bucket_delta_cdf(bucket_delta, out)
    else:
        print("  Skipping compaction_token_bucket_delta_cdf (no populated buckets)")


def aggregate(cache_dir=trace_loader.DEFAULT_CACHE, dates=None):
    """Load traces and (re)write the intermediate data/*.csv tables."""
    print("Loading traces + building CSV tables ...")
    trace_metrics.main(cache_dir=cache_dir, dates=dates, out_dir=DATA)


def _parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--skip-aggregate", action="store_true",
                   help="Reuse existing data/*.csv (skip the trace pass).")
    p.add_argument("--dates", help="Comma-separated UTC dates to use.")
    return p.parse_args(argv)


def main(argv=None):
    args = _parse_args(argv)
    dates = [d.strip() for d in args.dates.split(",")] if args.dates else None

    if not args.skip_aggregate:
        aggregate(dates=dates)

    os.makedirs(OUT, exist_ok=True)
    print("Group A (matplotlib defaults) ...")
    group_a(OUT)
    print("Group B (paper_style.setup_style) ...")
    group_b(OUT)
    n = len([f for f in os.listdir(OUT) if f.endswith(".pdf")])
    print(f"\nDone. {n} PDFs in {OUT}")


if __name__ == "__main__":
    main()
