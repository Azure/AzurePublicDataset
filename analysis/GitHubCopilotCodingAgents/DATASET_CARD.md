# Dataset Card: GHCP Coding Agent Traces (June 2026)

## Summary
A uniformly-sampled, reproducible slice of agentic GitHub Copilot sessions
from Visual Studio, covering June 1–7, 2026 (UTC). Each record is one
agentic session: an ordered set of user *turns* (ordered by time), where each turn contains the
LLM calls and tool-invocation batches that made up the agent's work.

The dataset captures the **structure and resource accounting** of agent runs —
timings, token counts, cache behavior, anonymized model usage, and the sequence
of tool calls — to support research on agent efficiency, caching, scheduling,
and workflow patterns.

## What it does **not** contain
This release is metadata-only. It includes **no**:
- source code, file contents, or diffs,
- user prompts, model responses, or tool outputs,
- file paths or repository names,
- user, account, or organization identifiers,
- real model names (models are relabeled 'Model A', 'Model B', ...).

The `message_metadata` field describes each prompt segment by *type*, *role*,
*sequence position*, and *token count* only — not the
segment's text.

## Dataset Statistics

| Metric | Value |
|--------|-------|
| Date range (UTC) | 2026-06-01 .. 2026-06-07 |
| Days | 7 |
| Agentic sessions | 265K |
| User turns | 1.2M |
| LLM calls | 9.3M |
| Tool calls | 8.7M |
| Distinct (anonymized) models | 37 |
| Prompt tokens (sum) | 638B |
| Completion tokens (sum) | 4.9B |
| Cached prompt tokens (sum) | 541B |

## Sampling
- **Population:** agentic-mode sessions.
- **Sampling:** fixed sampling rate across all dates.

## Anonymization
All identifiers (`session_id`, `turn_id`, `message_id`, and tool-batch
`request_id`) are hashed.

Model names are separately mapped to generic labels (`Model A`, `Model B`, ...) ranked by usage.

## Format & layout
- **Records:** one JSON object per session, newline-delimited (**JSONL**),
  **gzip-compressed**.
- **Sharding:** roughly 500 sessions per shard.
- **Blob layout** (`<container>/<prefix>/`):
  ```
  release_2026-06/
    schema.json
    DATASET_CARD.md
    date=2026-06-01/
      manifest.json
      shard-0000.jsonl.gz
      shard-0001.jsonl.gz
      ...
    date=2026-06-02/
      ...
  ```
- **Field reference:** see `schema.json`.

## Reading the data
```python
import gzip, json
with gzip.open("shard-0000.jsonl.gz", "rt", encoding="utf-8") as f:
    for line in f:
        session = json.loads(line)
        # session["turns"][i]["llm_calls"], ["tool_batches"], ...
```

Counts and exact shard sizes per day are recorded in each `manifest.json`.
