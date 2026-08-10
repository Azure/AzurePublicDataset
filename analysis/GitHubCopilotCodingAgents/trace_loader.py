"""Load the downloaded per-session trace shards into memory.

Reads the gzipped JSONL shards of the release (stored locally in
``downloaded_data/``) and yields one nested session dict per line, matching
``schema.json``.

Everything here streams over **all** downloaded sessions — no sampling is applied
at analysis time (the release itself is already a uniform population sample).

Typical use::

    from trace_loader import iter_sessions, load_dataframes
    for session in iter_sessions():
        ...
    frames = load_dataframes()   # flat per-call / per-batch / per-turn tables
"""

import glob
import gzip
import json
import os

import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CACHE = os.environ.get(
    "TRACE_ANALYSIS_CACHE_DIR", os.path.join(_HERE, "downloaded_data")
)


def shard_paths(cache_dir=DEFAULT_CACHE, dates=None):
    """Return the sorted list of shard files (optionally filtered by date)."""
    paths = sorted(glob.glob(os.path.join(cache_dir, "date=*", "*.jsonl.gz")))
    if dates is not None:
        dates = set(dates)
        paths = [
            p for p in paths
            if os.path.basename(os.path.dirname(p))[len("date="):] in dates
        ]
    return paths


def iter_sessions(cache_dir=DEFAULT_CACHE, dates=None):
    """Yield one session dict per line across all (or selected) shards."""
    paths = shard_paths(cache_dir, dates)
    if not paths:
        raise FileNotFoundError(
            f"No shards found under {cache_dir}. Download the trace shards "
            "from the GitHub release into downloaded_data/ first (see README.md)."
        )
    for path in paths:
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    yield json.loads(line)


def _ts(value):
    """Parse an ISO-8601 timestamp to a pandas Timestamp (UTC-naive), or NaT."""
    if value is None:
        return pd.NaT
    return pd.to_datetime(value, utc=False, errors="coerce")


def load_dataframes(cache_dir=DEFAULT_CACHE, dates=None):
    """Flatten all sessions into tidy tables used by ``trace_metrics``.

    Returns a dict with four DataFrames:

    * ``llm``      — one row per LLM call
    * ``batches``  — one row per tool batch
    * ``tools``    — one row per individual tool call (batch exploded)
    * ``turns``    — one row per (session, turn) with light rollups

    Timestamps are parsed to ``pandas.Timestamp`` (vectorized, after row
    assembly) and a ``end`` column carries ``timestamp + duration_ms`` for
    interval math. ``session_seq`` / ``turn_seq`` preserve the on-disk ordering
    (turns are stored in time order).
    """
    llm_rows, batch_rows, tool_rows, turn_rows = [], [], [], []

    for s_idx, sess in enumerate(iter_sessions(cache_dir, dates)):
        if s_idx and s_idx % 200_000 == 0:
            print(f"  ... loaded {s_idx:,} sessions", flush=True)
        sid = sess.get("session_id")
        date = sess.get("date")
        for t_idx, turn in enumerate(sess.get("turns") or []):
            tid = turn.get("turn_id")
            calls = turn.get("llm_calls") or []
            batches = turn.get("tool_batches") or []

            n_tool_calls = 0
            for c in calls:
                tok = c.get("tokens") or {}
                # Store the raw ISO string; parse vectorized below (fast).
                llm_rows.append({
                    "session_id": sid, "turn_id": tid, "date": date,
                    "session_seq": s_idx, "turn_seq": t_idx,
                    "message_id": c.get("message_id"),
                    "timestamp": c.get("timestamp"),
                    "duration_ms": c.get("duration_ms"),
                    "initiator_type": c.get("initiator_type"),
                    "model": c.get("model"),
                    "result": c.get("result"),
                    "status_code": c.get("status_code"),
                    "prompt": tok.get("prompt"),
                    "completion": tok.get("completion"),
                    "cached": tok.get("cached"),
                    "total": tok.get("total"),
                    "cached_pct": tok.get("cached_pct"),
                    "n_segments": len(c.get("message_metadata") or []),
                })

            for b in batches:
                fcs = b.get("function_calls") or []
                if fcs:  # mirrors KQL `where FunctionCalls != ""`
                    n_tool_calls += len(fcs)
                    ts = b.get("timestamp")
                    batch_rows.append({
                        "session_id": sid, "turn_id": tid, "date": date,
                        "session_seq": s_idx, "turn_seq": t_idx,
                        "timestamp": ts,
                        "duration_ms": b.get("duration_ms"),
                        "batch_size": len(fcs),
                        "request_id": b.get("request_id"),
                        "auto_continue": b.get("auto_continue"),
                        "result": b.get("result"),
                    })
                    for fc in fcs:
                        tool_rows.append({
                            "session_id": sid, "turn_id": tid,
                            "session_seq": s_idx, "turn_seq": t_idx,
                            "timestamp": ts,  # batch-level ts (shared by calls)
                            "name": fc.get("name"),
                            "status": fc.get("status"),
                            "duration_ms": fc.get("duration_ms"),
                            "batch_size": len(fcs),
                        })

            turn_rows.append({
                "session_id": sid, "turn_id": tid, "date": date,
                "session_seq": s_idx, "turn_seq": t_idx,
                "n_llm_calls": len(calls),
                "n_tool_calls": n_tool_calls,
            })

    frames = {
        "llm": pd.DataFrame(llm_rows),
        "batches": pd.DataFrame(batch_rows),
        "tools": pd.DataFrame(tool_rows),
        "turns": pd.DataFrame(turn_rows),
    }
    # Vectorized timestamp parsing + end = timestamp + duration (fast).
    for key in ("llm", "batches", "tools"):
        df = frames[key]
        if len(df):
            df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
            df["end"] = df["timestamp"] + pd.to_timedelta(
                df["duration_ms"], unit="ms")
        else:
            df["timestamp"] = pd.Series(dtype="datetime64[ns]")
            df["end"] = pd.Series(dtype="datetime64[ns]")
    return frames


if __name__ == "__main__":
    # Smoke test: summarize what was loaded.
    frames = load_dataframes()
    for name, df in frames.items():
        print(f"{name:>8}: {len(df):,} rows, cols={list(df.columns)}")
    print("sessions:", frames["turns"]["session_id"].nunique())
