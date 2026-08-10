"""Reproduce the paper's intermediate ``data/`` CSVs from the released traces.

Every function here re-derives one (or a few) of the CSV tables that the paper's
plotting code (``paper_figures.py``) consumes, sourced from the **locally downloaded
traces**. Two properties of the released data shape the results:

* **No sampling.** We stream over *all* downloaded sessions (the release is
  already a uniform 25% population sample).
* **Visual Studio only.** The release contains VS agentic traces, so VS Code and
  per-user figures are not reproduced (see README). Trend/model tables are
  reproduced as their **VS-side** equivalent over the released June 1-7 window.

Output CSV column names/orders match what ``paper_figures.py`` expects, so it
renders without modification.
"""

import os

import numpy as np
import pandas as pd

import trace_loader

_HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(_HERE, "data")

# Instant-apply edit model is labelled "tool-model" in the release (== the KQL
# `Model contains "instant-apply"` filter target).
TOOL_MODEL = "tool-model"

# Compaction thresholds (GHCP/config.py).
COMPACTION_MIN_PROMPT_BEFORE = 10000
COMPACTION_MIN_DROP_PCT = 30

# Prompt-token buckets for short/medium/long/xlong.
SML_THRESHOLDS = (40000, 80000, 120000)

_PCTLS = [5, 25, 50, 75, 95]


def _ms(delta):
    """Timedelta (or Series of) -> milliseconds as float."""
    return delta.dt.total_seconds() * 1000.0


def _epoch_ms(s):
    """Datetime Series -> float milliseconds since the Unix epoch.

    Resolution- and tz-independent: uses timedelta ``total_seconds`` rather than
    ``astype('int64')`` (whose scale depends on the column's datetime unit —
    e.g. ``datetime64[us]`` yields microseconds, ``[ns]`` nanoseconds). Mixing
    those units previously inflated LLM parallelism ~1000x/2.5x."""
    s = pd.to_datetime(s)
    if getattr(s.dt, "tz", None) is not None:
        s = s.dt.tz_convert("UTC").dt.tz_localize(None)
    return (s - pd.Timestamp("1970-01-01")).dt.total_seconds() * 1000.0


# ═══════════════════════════════════════════════════════════════════════════
# Per-turn timing (shared building block for session_stats + compaction hole)
# ═══════════════════════════════════════════════════════════════════════════

def turn_timing(frames):
    """One row per (session, turn) with LLM/tool spans and the derived
    turn-span / adjusted / overhead decomposition used by the paper."""
    llm, batches, turns = frames["llm"], frames["batches"], frames["turns"]

    lg = llm.groupby(["session_id", "turn_id"], sort=False).agg(
        llmSumMs=("duration_ms", "sum"),
        llmTurnStart=("timestamp", "min"),
        llmTurnEnd=("end", "max"),
        llmCalls=("message_id", "size"),
        promptTokens=("prompt", "sum"),
        completionTokens=("completion", "sum"),
        cachedTokens=("cached", "sum"),
    ).reset_index()

    if len(batches):
        bg = batches.groupby(["session_id", "turn_id"], sort=False).agg(
            toolSumMs=("duration_ms", "sum"),
            toolTurnStart=("timestamp", "min"),
            toolTurnEnd=("end", "max"),
        ).reset_index()
    else:
        bg = pd.DataFrame(columns=["session_id", "turn_id", "toolSumMs",
                                   "toolTurnStart", "toolTurnEnd"])

    m = lg.merge(bg, on=["session_id", "turn_id"], how="left")
    tc = turns.groupby(["session_id", "turn_id"], sort=False)["n_tool_calls"].sum()
    m = m.merge(tc.rename("toolCalls").reset_index(), on=["session_id", "turn_id"],
                how="left")
    m["toolSumMs"] = m["toolSumMs"].fillna(0.0)
    m["toolCalls"] = m["toolCalls"].fillna(0).astype("int64")

    # turnStart = earliest of llm/tool start; turnEnd = latest of llm/tool end.
    m["turnStart"] = m["llmTurnStart"]
    earlier = m["toolTurnStart"].notna() & (m["toolTurnStart"] < m["llmTurnStart"])
    m.loc[earlier, "turnStart"] = m.loc[earlier, "toolTurnStart"]
    m["turnEnd"] = m["llmTurnEnd"]
    later = m["toolTurnEnd"].notna() & (m["toolTurnEnd"] > m["llmTurnEnd"])
    m.loc[later, "turnEnd"] = m.loc[later, "toolTurnEnd"]

    m["turnSpanMs"] = _ms(m["turnEnd"] - m["turnStart"])
    m["llmAdjMs"] = np.minimum(m["llmSumMs"], m["turnSpanMs"])
    m["toolAdjMs"] = np.minimum(m["toolSumMs"], m["turnSpanMs"])
    m["overheadMs"] = np.maximum(
        0.0, m["turnSpanMs"] - np.maximum(m["llmAdjMs"], m["toolAdjMs"]))
    return m


# ═══════════════════════════════════════════════════════════════════════════
# Session-level stats  ->  vs_session_stats.csv
# ═══════════════════════════════════════════════════════════════════════════

def session_stats(frames, timing=None):
    m = turn_timing(frames) if timing is None else timing
    g = m.groupby("session_id", sort=False).agg(
        turns=("turn_id", "size"),
        llmCalls=("llmCalls", "sum"),
        toolCalls=("toolCalls", "sum"),
        sessionStart=("turnStart", "min"),
        sessionEnd=("turnEnd", "max"),
        llmRawSumMs=("llmSumMs", "sum"),
        llmTotalDurationMs=("llmAdjMs", "sum"),
        toolTotalDurationMs=("toolAdjMs", "sum"),
        totalSystemOverheadMs=("overheadMs", "sum"),
        turnsActiveMs=("turnSpanMs", "sum"),
    ).reset_index()

    g["wallClockMs"] = _ms(g["sessionEnd"] - g["sessionStart"])
    g = g[g["wallClockMs"] > 0].copy()
    g["llmParallelism"] = np.where(
        g["llmTotalDurationMs"] > 0, g["llmRawSumMs"] / g["llmTotalDurationMs"], 1.0)
    active = np.maximum(g["llmTotalDurationMs"], g["toolTotalDurationMs"]) \
        + g["totalSystemOverheadMs"]
    g["userIdleMs"] = np.maximum(0.0, g["wallClockMs"] - active)
    denom = g["userIdleMs"] + g["llmTotalDurationMs"] + g["toolTotalDurationMs"]
    g["llmPct"] = np.where(denom > 0, g["llmTotalDurationMs"] / denom * 100, 0.0)
    g["toolPct"] = np.where(denom > 0, g["toolTotalDurationMs"] / denom * 100, 0.0)
    g["userIdlePct"] = np.where(denom > 0, g["userIdleMs"] / denom * 100, 0.0)
    return g[["turns", "llmCalls", "toolCalls", "llmParallelism", "userIdleMs",
              "wallClockMs", "turnsActiveMs", "llmPct", "toolPct", "userIdlePct"]]


# ═══════════════════════════════════════════════════════════════════════════
# Token breakdowns
# ═══════════════════════════════════════════════════════════════════════════

def per_turn_token_breakdown(frames):
    """vs_per_turn_token_breakdown.csv — per turn (calls with prompt>0)."""
    llm = frames["llm"]
    p = llm[llm["prompt"] > 0]
    g = p.groupby(["session_id", "turn_id"], sort=False).agg(
        promptTokens=("prompt", "sum"),
        completionTokens=("completion", "sum"),
        cachedTokens=("cached", "sum"),
    ).reset_index()
    return g[["promptTokens", "cachedTokens", "completionTokens"]]


def per_call_token_breakdown(frames):
    """vs_per_call_token_breakdown.csv — per LLM call (prompt>0).

    Feeds token_count_cdf (prompt/completion/cached) and cache_hit_rate_cdf
    (cacheRate). VS-side reproduction of the VS Code-only paper figures."""
    llm = frames["llm"]
    p = llm[llm["prompt"] > 0]
    out = pd.DataFrame({
        "promptTokens": p["prompt"].astype(float),
        "completionTokens": p["completion"].astype(float),
        "cachedTokens": p["cached"].astype(float),
        "cacheRate": p["cached_pct"].astype(float),
    })
    return out.reset_index(drop=True)


# ═══════════════════════════════════════════════════════════════════════════
# Idle gaps  ->  vs_idle_gaps.csv
# ═══════════════════════════════════════════════════════════════════════════

def _consecutive_gaps(df, gap_type):
    """Inter-event idle gaps within each session (event end -> next event start)."""
    if not len(df):
        return pd.DataFrame({"gapType": [], "gapMs": []})
    d = df[["session_id", "timestamp", "end"]].dropna(subset=["timestamp"]) \
        .sort_values(["session_id", "timestamp"])
    prev_end = d.groupby("session_id", sort=False)["end"].shift()
    same = prev_end.notna()
    gap = _ms(d["timestamp"] - prev_end).clip(lower=0.0)
    out = pd.DataFrame({"gapType": gap_type, "gapMs": gap[same].values})
    return out


def idle_gaps(frames):
    container = _consecutive_gaps(frames["batches"], "container_idle")
    kv = _consecutive_gaps(frames["llm"], "kv_idle")
    return pd.concat([container, kv], ignore_index=True)[["gapType", "gapMs"]]


# ═══════════════════════════════════════════════════════════════════════════
# Cache rate after a user-idle gap  ->  vs_cache_after_user_idle.csv
# ═══════════════════════════════════════════════════════════════════════════

def cache_after_user_idle(frames):
    llm = frames["llm"]
    user = llm[llm["initiator_type"] == "user"]
    keep = user.groupby("session_id")["message_id"].size()
    keep = set(keep[keep >= 2].index)
    if not keep:
        return pd.DataFrame({"IdleTimeSec": [], "CacheRate": []})

    sub = llm[llm["session_id"].isin(keep)]
    # Per-turn start/end across all calls, and the user call's prompt/cached.
    tg = sub.groupby(["session_id", "turn_id"], sort=False).agg(
        turnStart=("timestamp", "min"), turnEnd=("end", "max")).reset_index()
    ug = (sub[sub["initiator_type"] == "user"]
          .groupby(["session_id", "turn_id"], sort=False)
          .agg(PromptTokens=("prompt", "first"),
               CachedTokens=("cached", "first")).reset_index())
    t = tg.merge(ug, on=["session_id", "turn_id"], how="left") \
          .sort_values(["session_id", "turnStart"])
    t["TurnIndex"] = t.groupby("session_id", sort=False).cumcount() + 1
    t["prevTurnEnd"] = t.groupby("session_id", sort=False)["turnEnd"].shift()

    t = t[(t["TurnIndex"] >= 2) & (t["PromptTokens"] > 0)].copy()
    t["IdleTimeSec"] = (t["turnStart"] - t["prevTurnEnd"]).dt.total_seconds()
    t = t[t["IdleTimeSec"] >= 0]
    t["IdleTimeSec"] = t["IdleTimeSec"].astype("int64")
    t["CacheRate"] = (t["CachedTokens"] * 100.0 / t["PromptTokens"]).round(2)
    return t[["IdleTimeSec", "CacheRate"]].reset_index(drop=True)


# ═══════════════════════════════════════════════════════════════════════════
# Tool parallelism / usage
# ═══════════════════════════════════════════════════════════════════════════

def tool_parallelism(frames):
    b = frames["batches"]
    g = b.groupby("batch_size").size().reset_index(name="batchCount")
    return g.rename(columns={"batch_size": "toolCount"}).sort_values("toolCount")


def per_tool_parallelism(frames):
    t = frames["tools"]
    g = t.groupby("name", sort=False).agg(
        totalInvocations=("name", "size"),
        parallelCount=("batch_size", lambda s: int((s > 1).sum())),
        avgBatchSize=("batch_size", "mean"),
    ).reset_index()
    g["parallelismRate"] = (g["parallelCount"] / g["totalInvocations"] * 100).round(1)
    g = g.sort_values("totalInvocations", ascending=False).head(15)
    return g.rename(columns={"name": "toolName"})[
        ["toolName", "totalInvocations", "parallelCount", "avgBatchSize",
         "parallelismRate"]]


def tool_stats(frames):
    t = frames["tools"]
    g = t.groupby("name").size().reset_index(name="callCount")
    g = g.sort_values("callCount", ascending=False)
    return g.rename(columns={"name": "toolName"})[["toolName", "callCount"]]


# ═══════════════════════════════════════════════════════════════════════════
# Deep-loop error signal  ->  vs_deep_loop_error_signal.csv
# ═══════════════════════════════════════════════════════════════════════════

_DIAG = ("get_errors", "get_diagnostics")


def deep_loop_error_signal(frames):
    t = frames["tools"]
    g = t.groupby(["session_id", "turn_id"], sort=False).agg(
        toolCalls=("name", "size"),
        failed=("status", lambda s: int((s == 2).sum())),
        diagCalls=("name", lambda s: int(s.isin(_DIAG).sum())),
        getErrFile=("name", lambda s: int((s == "get_errors_in_file").sum())),
    ).reset_index()

    def bucket(n):
        return ("1-2" if n <= 2 else "3-5" if n <= 5 else "6-9" if n <= 9
                else "10-14" if n <= 14 else "15-24" if n <= 24 else "25+")

    def sortkey(n):
        return (1 if n <= 2 else 2 if n <= 5 else 3 if n <= 9
                else 4 if n <= 14 else 5 if n <= 24 else 6)

    g["depthBucket"] = g["toolCalls"].map(bucket)
    g["sortKey"] = g["toolCalls"].map(sortkey)
    g["errSignal"] = (g["failed"] > 0) | (g["diagCalls"] > 0) | (g["getErrFile"] > 0)
    out = g.groupby(["depthBucket", "sortKey"], sort=False).agg(
        turns=("turn_id", "size"),
        turnsWithFailure=("failed", lambda s: int((s > 0).sum())),
        turnsWithErrSignal=("errSignal", "sum"),
    ).reset_index().sort_values("sortKey")
    return out[["depthBucket", "turns", "turnsWithFailure", "turnsWithErrSignal"]]


# ═══════════════════════════════════════════════════════════════════════════
# Cache rate by call position  ->  vs_cache_rate_by_call.csv
# ═══════════════════════════════════════════════════════════════════════════

def cache_rate_by_call(frames):
    llm = frames["llm"]
    p = llm[llm["prompt"] > 0].sort_values(
        ["session_id", "turn_id", "timestamp"])
    p = p.assign(callIndex=p.groupby(["session_id", "turn_id"], sort=False)
                 .cumcount() + 1)
    g = p[p["callIndex"] <= 30].groupby("callIndex")["cached_pct"] \
        .mean().reset_index(name="avgCachePct")
    return g.sort_values("callIndex")


# ═══════════════════════════════════════════════════════════════════════════
# Prompt-type breakdown  ->  vs_prompt_type_breakdown.csv
# (needs nested message_metadata; separate streaming pass.)
# ═══════════════════════════════════════════════════════════════════════════

_TYPE_COLS = [
    ("System", "avgSystemRatio"),
    ("History", "avgHistoryRatio"),
    ("FunctionCalls", "avgFuncCallsRatio"),
    ("Context", "avgContextRatio"),
    ("RepositoryWideCustomInstructions", "avgRepoInstrRatio"),
    ("IdeState", "avgIdeStateRatio"),
    ("UserMessage", "avgUserMsgRatio"),
    ("PathSpecificCustomInstructions", "avgPathInstrRatio"),
    ("AgentSkillsInstructions", "avgAgentSkillsRatio"),
    ("McpInstructions", "avgMcpInstrRatio"),
]


def prompt_type_breakdown(cache_dir=trace_loader.DEFAULT_CACHE, dates=None):
    types = [t for t, _ in _TYPE_COLS]
    n = 0
    prompt_sum = cached_sum = 0.0
    ratio_sum = {t: 0.0 for t in types}

    for sess in trace_loader.iter_sessions(cache_dir, dates):
        for turn in sess.get("turns") or []:
            for c in turn.get("llm_calls") or []:
                tok = c.get("tokens") or {}
                prompt = tok.get("prompt") or 0
                meta = c.get("message_metadata") or []
                if prompt <= 0 or not meta:
                    continue
                per_type = {t: 0 for t in types}
                total = 0
                for seg in meta:
                    slen = seg.get("token_len") or 0
                    total += slen
                    st = seg.get("type")
                    if st in per_type:
                        per_type[st] += slen
                if total <= 0:
                    continue
                n += 1
                prompt_sum += prompt
                cached_sum += (tok.get("cached") or 0)
                for t in types:
                    ratio_sum[t] += per_type[t] / total

    if n == 0:
        cols = ["avgPrompt", "avgCached"] + [c for _, c in _TYPE_COLS] + ["callCount"]
        return pd.DataFrame(columns=cols)

    row = {"avgPrompt": prompt_sum / n, "avgCached": cached_sum / n}
    for t, col in _TYPE_COLS:
        row[col] = ratio_sum[t] / n
    row["callCount"] = n
    cols = ["avgPrompt", "avgCached"] + [c for _, c in _TYPE_COLS] + ["callCount"]
    return pd.DataFrame([row])[cols]


# ═══════════════════════════════════════════════════════════════════════════
# Compaction events & turn-boundary cache  (per-session ordered LLM calls)
# ═══════════════════════════════════════════════════════════════════════════

def _ordered_calls(frames):
    """LLM calls (prompt>0) ordered per session by timestamp, with prev-row cols."""
    llm = frames["llm"]
    p = llm[llm["prompt"] > 0].sort_values(["session_id", "timestamp"]).copy()
    grp = p.groupby("session_id", sort=False)
    p["prevPrompt"] = grp["prompt"].shift()
    p["prevModel"] = grp["model"].shift()
    p["prevCachePct"] = grp["cached_pct"].shift()
    p["prevTurn"] = grp["turn_id"].shift()
    p["hasPrev"] = grp.cumcount() > 0
    return p


def compaction_events(frames, ordered=None):
    p = _ordered_calls(frames) if ordered is None else ordered
    c = p[p["hasPrev"] & (p["model"] == p["prevModel"])
          & (p["prevPrompt"] > COMPACTION_MIN_PROMPT_BEFORE)].copy()
    c["dropPct"] = ((c["prevPrompt"] - c["prompt"]) * 100.0 / c["prevPrompt"]).round(1)
    c = c[c["dropPct"] > COMPACTION_MIN_DROP_PCT]
    out = c.rename(columns={"cached_pct": "TokensCachedPercentage"})
    return out[["dropPct", "prevCachePct", "TokensCachedPercentage"]] \
        .reset_index(drop=True)


def turn_boundary_cache(frames, ordered=None):
    p = _ordered_calls(frames) if ordered is None else ordered
    q = p[p["hasPrev"] & (p["model"] != TOOL_MODEL)
          & (p["prevModel"] != TOOL_MODEL)].copy()
    same_turn = q["turn_id"] == q["prevTurn"]
    same_model = q["model"] == q["prevModel"]
    q["category"] = np.select(
        [same_turn & same_model, (~same_turn) & same_model, (~same_turn) & (~same_model)],
        ["Intra-turn (same model)", "Turn boundary (same model)",
         "Turn boundary (model switch)"], default="Other")
    q = q[q["category"] != "Other"]
    g = q.groupby("category", sort=False).agg(
        n=("category", "size"),
        avgBefore=("prevCachePct", "mean"),
        avgAfter=("cached_pct", "mean"),
    ).reset_index()
    return g[["category", "n", "avgBefore", "avgAfter"]]


# ═══════════════════════════════════════════════════════════════════════════
# Tool duration / token-delta boxes, raw durations, tool-LLM overlap
# ═══════════════════════════════════════════════════════════════════════════

def _pctile_box(df, group_cols, value_col):
    def agg(s):
        s = s.dropna()
        return pd.Series({
            "callCount": len(s),
            "p5": np.percentile(s, 5) if len(s) else np.nan,
            "p25": np.percentile(s, 25) if len(s) else np.nan,
            "p50": np.percentile(s, 50) if len(s) else np.nan,
            "p75": np.percentile(s, 75) if len(s) else np.nan,
            "p95": np.percentile(s, 95) if len(s) else np.nan,
        })
    return df.groupby(group_cols, sort=False)[value_col].apply(agg) \
        .unstack().reset_index()


def tool_duration_by_status(frames):
    t = frames["tools"]
    s = t[t["status"].isin([1, 2])]
    out = _pctile_box(s, ["name", "status"], "duration_ms")
    out = out.rename(columns={"name": "toolName", "status": "toolStatus"})
    out["callCount"] = out["callCount"].astype("int64")
    return out.sort_values(["toolName", "toolStatus"])[
        ["toolName", "toolStatus", "callCount", "p5", "p25", "p50", "p75", "p95"]]


def tool_token_delta_box(frames):
    """Per-tool prompt-token delta (success vs failure), attributed to the tool
    that ran between two consecutive LLM calls in the same turn."""
    llm = frames["llm"]
    tools = frames["tools"]
    p = llm[llm["prompt"] > 0].sort_values(
        ["session_id", "turn_id", "timestamp"]).copy()
    grp = p.groupby(["session_id", "turn_id"], sort=False)
    p["prevPrompt"] = grp["prompt"].shift()
    p["prevTs"] = grp["timestamp"].shift()
    w = p[p["prevTs"].notna()].copy()
    w["tokenDelta"] = w["prompt"] - w["prevPrompt"]
    w = w[["session_id", "turn_id", "prevTs", "timestamp", "tokenDelta"]] \
        .rename(columns={"prevTs": "windowStart", "timestamp": "windowEnd"})

    tj = tools[tools["status"].isin([1, 2])][
        ["session_id", "turn_id", "timestamp", "name", "status"]]
    j = w.merge(tj, on=["session_id", "turn_id"], how="inner")
    j = j[(j["timestamp"] > j["windowStart"]) & (j["timestamp"] < j["windowEnd"])]
    out = _pctile_box(j, ["name", "status"], "tokenDelta")
    out = out.rename(columns={"name": "toolName", "status": "toolStatus"})
    out["callCount"] = out["callCount"].astype("int64")
    return out.sort_values(["toolName", "toolStatus"])[
        ["toolName", "toolStatus", "callCount", "p5", "p25", "p50", "p75", "p95"]]


def llm_duration_raw(frames):
    llm = frames["llm"]
    d = llm[(llm["model"] != TOOL_MODEL) & (llm["duration_ms"] > 0)
            & (llm["duration_ms"] < 30 * 60 * 1000)]
    return pd.DataFrame({"llmDurMs": d["duration_ms"].astype(float)}) \
        .reset_index(drop=True)


def tool_duration_raw(frames):
    t = frames["tools"]
    return t.rename(columns={"name": "toolName", "duration_ms": "toolDurMs"})[
        ["toolName", "toolDurMs"]].reset_index(drop=True)


def tool_llm_overlap(frames):
    """vs_tool_llm_overlap_clean.csv — per tool batch, max overlap (ms) with any
    LLM call in the same turn. All times in milliseconds via ``_epoch_ms`` +
    ``duration_ms`` (resolution-independent)."""
    llm = frames["llm"]
    batches = frames["batches"].reset_index(drop=True).copy()
    batches["_bid"] = np.arange(len(batches))

    lc = llm[(llm["model"] != TOOL_MODEL) & (llm["duration_ms"] > 0)
             & (llm["duration_ms"] < 30 * 60 * 1000)][
        ["session_id", "turn_id", "timestamp", "duration_ms"]].copy()
    lc["llmStartMs"] = _epoch_ms(lc["timestamp"])
    lc["llmEndMs"] = lc["llmStartMs"] + lc["duration_ms"].astype(float)

    b = batches[["_bid", "session_id", "turn_id", "timestamp", "duration_ms"]].copy()
    b["toolStartMs"] = _epoch_ms(b["timestamp"])
    b["toolEndMs"] = b["toolStartMs"] + b["duration_ms"].astype(float)

    j = b[["_bid", "session_id", "turn_id", "toolStartMs", "toolEndMs"]].merge(
        lc[["session_id", "turn_id", "llmStartMs", "llmEndMs"]],
        on=["session_id", "turn_id"], how="inner")
    start = np.maximum(j["toolStartMs"].to_numpy(), j["llmStartMs"].to_numpy())
    stop = np.minimum(j["toolEndMs"].to_numpy(), j["llmEndMs"].to_numpy())
    j["overlapMs"] = np.maximum(0.0, stop - start)
    ov = j.groupby("_bid")["overlapMs"].max().rename("maxOverlapMs")
    out = batches[["_bid", "duration_ms"]].merge(ov, on="_bid", how="left")
    out["maxOverlapMs"] = out["maxOverlapMs"].fillna(0.0)
    return out.rename(columns={"duration_ms": "toolDurMs"})[
        ["toolDurMs", "maxOverlapMs"]].reset_index(drop=True)


# ═══════════════════════════════════════════════════════════════════════════
# Per-turn LLM parallelism (interval union)  ->  vs_llm_parallelism.csv
# ═══════════════════════════════════════════════════════════════════════════

def llm_parallelism(frames):
    """Per-turn LLM parallelism degree = sum(call durations) / wall-clock union
    of the call intervals (matches GHCP/analysis/llm_concurrency.py).

    Fully vectorized via a per-group interval-union sweep (no Python loop), with
    times in milliseconds from ``_epoch_ms`` + ``duration_ms``."""
    llm = frames["llm"]
    d = llm[(llm["model"] != TOOL_MODEL) & (llm["duration_ms"] > 0)
            & (llm["duration_ms"] < 30 * 60 * 1000)
            & llm["timestamp"].notna()].copy()
    if not len(d):
        return pd.DataFrame(columns=["numCalls", "parallelismDegree"])

    d["startMs"] = _epoch_ms(d["timestamp"])
    d["endMs"] = d["startMs"] + d["duration_ms"].astype(float)
    key = ["session_id", "turn_id"]
    d = d.sort_values(key + ["startMs"])
    # Union of intervals per turn: each interval contributes only the span not
    # already covered by the running max end of earlier intervals in the turn.
    d["_cummaxEnd"] = d.groupby(key, sort=False)["endMs"].cummax()
    prev = d.groupby(key, sort=False)["_cummaxEnd"].shift().to_numpy()
    starts = d["startMs"].to_numpy()
    eff_start = np.where(np.isnan(prev), starts, np.maximum(starts, prev))
    d["_contrib"] = np.maximum(0.0, d["endMs"].to_numpy() - eff_start)

    agg = d.groupby(key, sort=False).agg(
        numCalls=("startMs", "size"),
        rawMs=("duration_ms", "sum"),
        unionMs=("_contrib", "sum"),
    ).reset_index()
    agg["parallelismDegree"] = np.where(
        agg["unionMs"] > 0, agg["rawMs"] / agg["unionMs"], 1.0)
    return agg[["numCalls", "parallelismDegree"]].reset_index(drop=True)


# ═══════════════════════════════════════════════════════════════════════════
# Weekday / weekend per-turn call counts  ->  vs_turn_calls_by_daytype.csv
# ═══════════════════════════════════════════════════════════════════════════

def turn_calls_by_daytype(frames):
    turns = frames["turns"].copy()
    dow = pd.to_datetime(turns["date"], errors="coerce").dt.dayofweek
    turns["dayType"] = np.where(dow.isin([5, 6]), "Weekend", "Weekday")

    def agg(df):
        return pd.Series({
            "n": len(df),
            "llm_median": df["n_llm_calls"].median(),
            "llm_mean": df["n_llm_calls"].mean(),
            "llm_p90": np.percentile(df["n_llm_calls"], 90),
            "llm_p99": np.percentile(df["n_llm_calls"], 99),
            "tool_median": df["n_tool_calls"].median(),
            "tool_mean": df["n_tool_calls"].mean(),
            "tool_p90": np.percentile(df["n_tool_calls"], 90),
            "tool_p99": np.percentile(df["n_tool_calls"], 99),
        })

    return turns.groupby("dayType", sort=False).apply(agg).reset_index()


# ═══════════════════════════════════════════════════════════════════════════
# Model distribution & share trend (VS-side, anonymized labels)
# ═══════════════════════════════════════════════════════════════════════════

def model_distribution(frames):
    llm = frames["llm"]
    d = llm[llm["model"] != TOOL_MODEL]
    counts = d.groupby("model").size().sort_values(ascending=False)
    total = float(counts.sum()) or 1.0
    top = counts.head(15)
    others = float(counts.iloc[15:].sum())
    rows = [{"rank": i + 1, "model": m, "calls": float(c), "pct": c / total * 100}
            for i, (m, c) in enumerate(top.items())]
    if others > 0:
        rows.append({"rank": len(top) + 1, "model": "Others",
                     "calls": others, "pct": others / total * 100})
    return pd.DataFrame(rows, columns=["rank", "model", "calls", "pct"])


def model_share_trend(frames):
    """Per-day model request share over the released window (top 7 + Others)."""
    llm = frames["llm"]
    d = llm[llm["model"] != TOOL_MODEL].copy()
    d = d[d["date"].notna()]
    raw = d.groupby(["date", "model"]).size().reset_index(name="calls")
    top = list(raw.groupby("model")["calls"].sum()
               .sort_values(ascending=False).head(7).index)
    raw["label"] = np.where(raw["model"].isin(top), raw["model"], "Others")
    agg = raw.groupby(["date", "label"], as_index=False)["calls"].sum()
    agg["pct"] = agg["calls"] / agg.groupby("date")["calls"].transform("sum") * 100
    rank_map = {m: i + 1 for i, m in enumerate(top)}
    rank_map["Others"] = 99
    agg["rank"] = agg["label"].map(rank_map)
    return (agg.rename(columns={"label": "model", "date": "day"})
            [["day", "model", "rank", "pct"]]
            .sort_values(["day", "rank"]).reset_index(drop=True))


# ═══════════════════════════════════════════════════════════════════════════
# Hourly trends (VS-side)  ->  hourly_metrics / short_medium_long / percentiles
# ═══════════════════════════════════════════════════════════════════════════

def _date_window(frames):
    """[start, end) timestamps covering the release partition dates.

    ClientTimestamp can be skewed far from a session's partition date (client
    clock skew); the paper's KQL binned trends only within the analysis window,
    so trend metrics clamp to it too (avoids spurious 1-session hours)."""
    dates = pd.to_datetime(frames["turns"]["date"], errors="coerce").dropna()
    if not len(dates):
        return None, None
    return dates.min().normalize(), dates.max().normalize() + pd.Timedelta(days=1)


def _turn_level(frames, timing=None):
    """Per-turn frame carrying an hour bin, token sums and call counts,
    restricted to the release date window (see ``_date_window``)."""
    m = turn_timing(frames) if timing is None else timing
    t = m[["session_id", "turnStart", "llmCalls", "toolCalls",
           "promptTokens", "completionTokens"]].copy()
    t = t[t["turnStart"].notna()]
    # Blob timestamps are tz-aware (UTC); the partition-date window is tz-naive.
    # Normalize turnStart to tz-naive UTC so the two compare cleanly.
    ts = t["turnStart"]
    if getattr(ts.dt, "tz", None) is not None:
        t["turnStart"] = ts.dt.tz_convert("UTC").dt.tz_localize(None)
    start, end = _date_window(frames)
    if start is not None:
        t = t[(t["turnStart"] >= start) & (t["turnStart"] < end)]
    t["ts"] = t["turnStart"].dt.floor("h")
    return t


def hourly_metrics(frames, timing=None):
    t = _turn_level(frames, timing)
    g = t.groupby("ts").agg(
        sessions=("session_id", "nunique"),
        turns=("session_id", "size"),
        llmCalls=("llmCalls", "sum"),
        toolCalls=("toolCalls", "sum"),
        totalPromptTokens=("promptTokens", "sum"),
        totalCompletionTokens=("completionTokens", "sum"),
    ).reset_index().sort_values("ts")
    g["avgPromptPerCall"] = g["totalPromptTokens"] / g["llmCalls"].replace(0, np.nan)
    g["avgCompletionPerCall"] = g["totalCompletionTokens"] / g["llmCalls"].replace(0, np.nan)
    g["avgLlmCallsPerSession"] = g["llmCalls"] / g["sessions"]
    g["avgToolCallsPerSession"] = g["toolCalls"] / g["sessions"]
    g["avgTurnsPerSession"] = g["turns"] / g["sessions"]
    g["avgPromptTokensPerSession"] = g["totalPromptTokens"] / g["sessions"]
    g["avgCompletionTokensPerSession"] = g["totalCompletionTokens"] / g["sessions"]
    return g[["ts", "sessions", "turns", "llmCalls", "toolCalls",
              "totalPromptTokens", "totalCompletionTokens", "avgPromptPerCall",
              "avgCompletionPerCall", "avgLlmCallsPerSession",
              "avgToolCallsPerSession", "avgTurnsPerSession",
              "avgPromptTokensPerSession", "avgCompletionTokensPerSession"]]


def short_medium_long_hourly(frames):
    t1, t2, t3 = SML_THRESHOLDS
    llm = frames["llm"]
    p = llm[llm["prompt"] > 0].copy()
    p = p[p["timestamp"].notna()]
    p["ts"] = p["timestamp"].dt.floor("h")
    p["bucket"] = np.select(
        [p["prompt"] <= t1, p["prompt"] <= t2, p["prompt"] <= t3],
        ["shortCalls", "mediumCalls", "longCalls"], default="xlongCalls")
    piv = p.groupby(["ts", "bucket"]).size().unstack(fill_value=0).reset_index()
    for c in ("shortCalls", "mediumCalls", "longCalls", "xlongCalls"):
        if c not in piv.columns:
            piv[c] = 0
    piv["thr1"], piv["thr2"], piv["thr3"] = t1, t2, t3
    return piv.sort_values("ts")[
        ["ts", "shortCalls", "mediumCalls", "longCalls", "xlongCalls",
         "thr1", "thr2", "thr3"]]


def session_percentile_trends(frames, timing=None):
    t = _turn_level(frames, timing)
    per = t.groupby(["ts", "session_id"]).agg(
        LlmCalls=("llmCalls", "sum"),
        ToolCalls=("toolCalls", "sum"),
        PromptTokens=("promptTokens", "sum"),
        CompletionTokens=("completionTokens", "sum"),
    ).reset_index()
    metrics = ["LlmCalls", "ToolCalls", "PromptTokens", "CompletionTokens"]
    rows = []
    for ts, grp in per.groupby("ts"):
        row = {"ts": ts}
        for mtr in metrics:
            for q in (25, 50, 75, 95):
                row[f"p{q}{mtr}"] = np.percentile(grp[mtr], q)
        rows.append(row)
    cols = ["ts"] + [f"p{q}{m}" for m in metrics for q in (25, 50, 75, 95)]
    return pd.DataFrame(rows).sort_values("ts")[cols]


# ═══════════════════════════════════════════════════════════════════════════
# Compaction time-hole (7-day pool)  -> vs_turn_hole_bucket_delta_tok_only_7day
#                                       vs_compaction_turn_hole
# ═══════════════════════════════════════════════════════════════════════════

_FIG_LLM_BINS = [0, 1, 3, 7, 15, 30, np.inf]
_FIG_LLM_LABELS = ["1", "2-3", "4-7", "8-15", "16-30", "31+"]
_FIG_TOK_BINS = [0, 10_000, 30_000, 60_000, 100_000, 150_000, np.inf]
_FIG_TOK_LABELS = ["<10K", "10-30K", "30-60K", "60-100K", "100-150K", "150K+"]


def _turn_hole_frame(frames, ordered=None, timing=None):
    m = turn_timing(frames) if timing is None else timing
    th = m[m["turnSpanMs"] > 0].copy()
    th["holePct"] = (th["turnSpanMs"] - th["llmSumMs"] - th["toolSumMs"]) \
        / th["turnSpanMs"] * 100
    th = th.rename(columns={"llmCalls": "llmCallsN"})
    th = th[["session_id", "turn_id", "holePct", "llmCallsN", "promptTokens"]] \
        .rename(columns={"llmCallsN": "llmCalls"})

    # Compaction turns: any prompt drop >30% between consecutive same-model calls.
    p = _ordered_calls(frames) if ordered is None else ordered
    comp = p[p["hasPrev"] & (p["model"] == p["prevModel"])
             & (p["prevPrompt"] > COMPACTION_MIN_PROMPT_BEFORE)]
    comp = comp[(comp["prevPrompt"] - comp["prompt"]) * 100.0 / comp["prevPrompt"]
                > COMPACTION_MIN_DROP_PCT]
    comp_keys = comp[["session_id", "turn_id"]].drop_duplicates()
    comp_keys["hasCompaction"] = True
    th = th.merge(comp_keys, on=["session_id", "turn_id"], how="left")
    th["hasCompaction"] = th["hasCompaction"].fillna(False).astype(bool)
    return th


def compaction_turn_hole(frames, ordered=None, timing=None):
    th = _turn_hole_frame(frames, ordered, timing).copy()
    th["llm_bucket"] = pd.cut(th["llmCalls"], bins=_FIG_LLM_BINS,
                              labels=_FIG_LLM_LABELS, right=True).astype(str)
    th["tok_bucket"] = pd.cut(th["promptTokens"], bins=_FIG_TOK_BINS,
                              labels=_FIG_TOK_LABELS, right=True).astype(str)
    nocomp_avg = (th[~th["hasCompaction"]]
                  .groupby(["llm_bucket", "tok_bucket"], observed=True)["holePct"]
                  .mean().rename("nocomp_avg").reset_index())
    th = th.merge(nocomp_avg, on=["llm_bucket", "tok_bucket"], how="left")
    th["excess_hole_pct"] = th["holePct"] - th["nocomp_avg"]
    return th[["holePct", "llmCalls", "promptTokens", "hasCompaction",
               "llm_bucket", "tok_bucket", "nocomp_avg", "excess_hole_pct"]] \
        .reset_index(drop=True)


def turn_hole_bucket_delta_tok_only(frames, ordered=None, timing=None):
    th = _turn_hole_frame(frames, ordered, timing).copy()
    th["tok5k"] = (th["promptTokens"] // 5000 * 5000).astype("int64")
    rows = []
    for tb, grp in th.groupby("tok5k", observed=True):
        if tb > 300_000:
            continue
        comp = grp[grp["hasCompaction"]]["holePct"]
        nocomp = grp[~grp["hasCompaction"]]["holePct"]
        if len(comp) < 20 or len(nocomp) < 5:
            continue
        rows.append({
            "tok_bucket": int(tb), "n_comp": len(comp), "n_nocomp": len(nocomp),
            "avg_comp": comp.mean(), "avg_nocomp": nocomp.mean(),
            "delta_mean": comp.mean() - nocomp.mean(),
            "delta_median": comp.median() - nocomp.median(),
        })
    return pd.DataFrame(rows, columns=[
        "tok_bucket", "n_comp", "n_nocomp", "avg_comp", "avg_nocomp",
        "delta_mean", "delta_median"])


# ═══════════════════════════════════════════════════════════════════════════
# Dataset-scale summary (for the notebook overview)
# ═══════════════════════════════════════════════════════════════════════════

def scale_summary(frames):
    llm, tools, turns, batches = (frames["llm"], frames["tools"],
                                  frames["turns"], frames["batches"])
    dates = sorted(d for d in turns["date"].dropna().unique())
    n_sessions = turns["session_id"].nunique()
    n_turns = len(turns)
    n_llm = len(llm)
    n_batches = len(batches)
    n_tools = len(tools)
    return {
        "date_range": f"{dates[0]} .. {dates[-1]}" if dates else "n/a",
        "n_days": len(dates),
        "sessions": int(n_sessions),
        "turns": int(n_turns),
        "llm_calls": int(n_llm),
        "tool_batches": int(n_batches),
        "tool_calls": int(n_tools),
        "distinct_models": int(llm[llm["model"] != TOOL_MODEL]["model"].nunique()),
        "prompt_tokens": float(llm["prompt"].fillna(0).sum()),
        "completion_tokens": float(llm["completion"].fillna(0).sum()),
        "cached_tokens": float(llm["cached"].fillna(0).sum()),
        "avg_turns_per_session": round(n_turns / n_sessions, 2) if n_sessions else 0,
        "avg_llm_calls_per_turn": round(n_llm / n_turns, 2) if n_turns else 0,
        "avg_tool_calls_per_turn": round(n_tools / n_turns, 2) if n_turns else 0,
    }


# ═══════════════════════════════════════════════════════════════════════════
# Orchestration
# ═══════════════════════════════════════════════════════════════════════════

def build_all(frames, cache_dir=trace_loader.DEFAULT_CACHE, dates=None):
    """Compute every reproducible CSV table. Returns {name: DataFrame}."""
    timing = turn_timing(frames)
    ordered = _ordered_calls(frames)
    # (name, thunk) so we can print progress as each table is computed.
    steps = [
        ("vs_session_stats.csv", lambda: session_stats(frames, timing)),
        ("vs_per_turn_token_breakdown.csv", lambda: per_turn_token_breakdown(frames)),
        ("vs_per_call_token_breakdown.csv", lambda: per_call_token_breakdown(frames)),
        ("vs_idle_gaps.csv", lambda: idle_gaps(frames)),
        ("vs_cache_after_user_idle.csv", lambda: cache_after_user_idle(frames)),
        ("vs_tool_parallelism.csv", lambda: tool_parallelism(frames)),
        ("vs_per_tool_parallelism.csv", lambda: per_tool_parallelism(frames)),
        ("vs_tool_stats.csv", lambda: tool_stats(frames)),
        ("vs_deep_loop_error_signal.csv", lambda: deep_loop_error_signal(frames)),
        ("vs_cache_rate_by_call.csv", lambda: cache_rate_by_call(frames)),
        ("vs_prompt_type_breakdown.csv", lambda: prompt_type_breakdown(cache_dir, dates)),
        ("vs_compaction_events.csv", lambda: compaction_events(frames, ordered)),
        ("vs_turn_boundary_cache_agg.csv", lambda: turn_boundary_cache(frames, ordered)),
        ("vs_tool_duration_by_status_box.csv", lambda: tool_duration_by_status(frames)),
        ("vs_tool_token_delta_box.csv", lambda: tool_token_delta_box(frames)),
        ("vs_llm_duration_raw.csv", lambda: llm_duration_raw(frames)),
        ("vs_tool_duration_raw.csv", lambda: tool_duration_raw(frames)),
        ("vs_tool_llm_overlap_clean.csv", lambda: tool_llm_overlap(frames)),
        ("vs_llm_parallelism.csv", lambda: llm_parallelism(frames)),
        ("vs_turn_calls_by_daytype.csv", lambda: turn_calls_by_daytype(frames)),
        ("model_distribution.csv", lambda: model_distribution(frames)),
        ("model_share_trend.csv", lambda: model_share_trend(frames)),
        ("hourly_metrics.csv", lambda: hourly_metrics(frames, timing)),
        ("vs_turn_hole_bucket_delta_tok_only_7day.csv",
         lambda: turn_hole_bucket_delta_tok_only(frames, ordered, timing)),
    ]
    tables = {}
    for i, (name, thunk) in enumerate(steps, 1):
        print(f"  [{i:>2}/{len(steps)}] {name} ...", flush=True)
        tables[name] = thunk()
    return tables


def write_all(tables, out_dir=DATA_DIR):
    os.makedirs(out_dir, exist_ok=True)
    for name, df in tables.items():
        path = os.path.join(out_dir, name)
        df.to_csv(path, index=False)
        print(f"  wrote {name:<44} {len(df):>10,} rows")
    return out_dir


def main(cache_dir=trace_loader.DEFAULT_CACHE, dates=None, out_dir=DATA_DIR):
    print("Loading traces ...")
    frames = trace_loader.load_dataframes(cache_dir, dates)
    print("Dataset scale:")
    for k, v in scale_summary(frames).items():
        print(f"  {k:<26} {v:,}" if isinstance(v, (int, float)) else f"  {k:<26} {v}")
    print("Building CSV tables ...")
    tables = build_all(frames, cache_dir, dates)
    write_all(tables, out_dir)
    print(f"\nDone. CSVs in {out_dir}")


if __name__ == "__main__":
    main()
