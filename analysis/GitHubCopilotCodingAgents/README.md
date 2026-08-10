# Reproducing the paper figures from the released GHCP traces

This folder contains scripts and instructions that reproduce the paper figures from the
public GitHub Copilot agentic coding trace release.

Everything you need is in this folder — download the trace data from the
[GitHub release](https://github.com/Azure/AzurePublicDataset/releases/tag/ghcp-coding-agent-2026)
into `downloaded_data/`, then run the analysis.

```
downloaded_data/     trace shards (gzipped JSONL, one folder per date)
trace_loader.py      shards  ->  tidy per-call/batch/turn DataFrames
trace_metrics.py     traces  ->  data/*.csv               (intermediate tables)
paper_figures.py  }  CSVs    ->  figures/*.pdf            (the paper's plotting
paper_style.py    }                                        code + styling)
make_figures.py      orchestrates all of the above
GitHubCopilotCodingAgentDataset2026.ipynb   notebook: overview + render + inline display
```

See [`schema.json`](schema.json) and [`DATASET_CARD.md`](DATASET_CARD.md) for the
full field reference and dataset description.

---

## Prerequisites

1. **Python 3.9+** and the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. **Download the traces** from the GitHub release into `downloaded_data/`:

   ```
   https://github.com/Azure/AzurePublicDataset/releases/tag/ghcp-coding-agent-2026
   ```

   After extracting, the folder should contain `date=2026-06-01/`, `date=2026-06-02/`, etc., each with `.jsonl.gz` shard files.

---

## Running

Run the commands from **inside this directory** (the scripts use bare imports).

### Option A — one command, end to end

```bash
python make_figures.py
```

This aggregates the local traces into `data/*.csv` and renders `figures/*.pdf`.

### Option B — step by step

```bash
python make_figures.py --skip-aggregate   # reuse existing data/*.csv, just re-render
```

### Option C — the guided notebook

Open [`GitHubCopilotCodingAgentDataset2026.ipynb`](GitHubCopilotCodingAgentDataset2026.ipynb)
for an inline-figure walkthrough that also prints a **dataset-scale overview**
(sessions, turns, LLM calls, tool calls, token volume, models, per-session/per-turn
averages) before plotting.

### Useful flags

```bash
# Iterate on a single day (much faster while exploring):
python make_figures.py --dates 2026-06-01

# Re-render from already-built data/*.csv (skip the trace pass):
python make_figures.py --skip-aggregate
```

Outputs:
- `data/*.csv` — intermediate tables (regenerable; gitignored).
- `figures/*.pdf` — the reproduced figures.

---

## Reproducible figures

All are agentic metrics derived from the released fields
(`llm_calls`: tokens / cache / model / duration / timestamp / `message_metadata`;
`tool_batches`: tool name / status / duration).

| Figure(s) | Source table(s) |
|-----------|-----------------|
| `session_duration_hist_cdf_logscale_vs`, `turn_duration_hist_cdf_logscale_vs`, `session_turns_cdf`, `per_session_calls_cdf`, `per_turn_calls_cdf` | `vs_session_stats` |
| `time_breakdown_llm_tool_user_cdf_vs`, `..._multi_turn_vs`, `time_breakdown_llm_tool_cdf_single_turn_vs` | `vs_session_stats` |
| `user_idle_time_cdf` / `tool_driven_idle_time_cdf` | `vs_session_stats` / `vs_idle_gaps` |
| `per_turn_token_count_cdf`, `token_count_cdf`, `cache_hit_rate_cdf` | `vs_per_turn_token_breakdown`, `vs_per_call_token_breakdown` |
| `token_type_breakdown` | `vs_prompt_type_breakdown` (`message_metadata` token_len) |
| `tool_usage_bar`, `tool_parallelism`, `per_tool_parallelism` | `vs_tool_stats`, `vs_tool_parallelism`, `vs_per_tool_parallelism` |
| `tool_duration_cdf`, `tool_duration_cdf_total`, `tool_duration_by_status`, `tool_token_delta_by_status` | `vs_tool_duration_raw`, `vs_llm_duration_raw`, `vs_tool_duration_by_status_box`, `vs_tool_token_delta_box` |
| `tool_time_nested_by_bucket` | `vs_tool_llm_overlap_clean` |
| `llm_parallelism` (turns with parallelism > 1), `llm_parallelism_all` (all turns) | `vs_llm_parallelism` (per-turn interval-union) |
| `cache_rate_by_call_position_half_col`, `turn_boundary_cache_rate`, `cache_rate_vs_idle_boxplot` | `vs_cache_rate_by_call`, `vs_turn_boundary_cache_agg`, `vs_cache_after_user_idle` |
| `compaction_severity`, `compaction_severity_cache_hit_drop`, `compaction_token_bucket_delta_cdf` | `vs_compaction_events`, `vs_turn_hole_bucket_delta_tok_only_7day` |
| `error_signal_composition_by_depth` | `vs_deep_loop_error_signal` |
| `turn_calls_weekday_weekend_bars` | `vs_turn_calls_by_daytype` |
| `model_distribution_anonymized`, `model_share_trend` | `model_distribution`, `model_share_trend` (VS, anonymized labels) |
| `normalized_trends`, `session_avg_trends` | `hourly_metrics` (VS hourly, clamped to the release date window) |

---