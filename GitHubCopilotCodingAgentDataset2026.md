# GitHub Copilot Coding Agent Traces 2026

## Introduction

The traces contain uniformly-sampled agentic coding sessions from GitHub Copilot, covering June 1–7, 2026.

Detailed analysis on the full traces can be found in our [arXiv paper](https://arxiv.org/abs/2608.00101).

The dataset captures the structure and resource accounting of agent runs, including timings, token counts, cache behavior, anonymized model usage, and the sequence of tool calls, to support research on agent efficiency, caching, scheduling, workflow patterns, and so on.

The dataset comprises this description, a schema reference ([`analysis/GitHubCopilotCodingAgents/schema.json`](analysis/GitHubCopilotCodingAgents/schema.json)), a dataset card ([`analysis/GitHubCopilotCodingAgents/DATASET_CARD.md`](analysis/GitHubCopilotCodingAgents/DATASET_CARD.md)), and a [Jupyter Notebook](analysis/GitHubCopilotCodingAgents/GitHubCopilotCodingAgentDataset2026.ipynb) that reproduces the paper figures.

## Using the data

### License

The data is made available and licensed under a [CC-BY Attribution License](https://github.com/Azure/AzurePublicDataset/blob/master/LICENSE). By downloading it or using them, you agree to the terms of this license.

### Attribution

If you use this data for a publication or project, please cite the accompanying paper:

```
@article{liu2026agentic,
  title={Agentic Coding in the Wild: Characterizing GitHub Copilot Traces at Production Scale},
  author={Liu, Banruo and Qiu, Haoran and Goiri, {\'I}{\~n}igo and Fonseca, Rodrigo and Bianchini, Ricardo and Choukse, Esha},
  journal={arXiv preprint arXiv:2608.00101},
  year={2026}
}
```

### Downloading

Download the trace shards from the [GitHub release](https://github.com/Azure/AzurePublicDataset/releases/tag/ghcp-coding-agent-2026).

The release contains gzip-compressed JSONL files partitioned by date (`date=2026-06-01/shard-0000.jsonl.gz`, etc.).

### Schema

Each line in a shard file is a JSON object representing one agentic session. See [`analysis/GitHubCopilotCodingAgents/schema.json`](analysis/GitHubCopilotCodingAgents/schema.json) for the full field reference.

Top-level fields:

| Field | Description |
|-------|-------------|
| `session_id` | Anonymized agentic conversation id |
| `date` | UTC partition date (YYYY-MM-DD) |
| `turns` | Array of user turns, each containing `llm_calls` and `tool_batches` |

Each LLM call includes: `timestamp`, `duration_ms`, `model` (anonymized), `tokens` (prompt/completion/cached), and `message_metadata` (segment types and token counts — no text content).

Each tool batch includes: `timestamp`, `duration_ms`, `function_calls` (tool name, status, duration).

### What it does **not** contain

This release is metadata-only. It includes **no**:
- source code, file contents, or diffs
- user prompts, model responses, or tool outputs
- file paths or repository names
- user, account, or organization identifiers
- real model names (models are relabeled 'Model A', 'Model B', ...)

### Validation

This data is the sample data used in the arXiv paper mentioned above.
To verify the data, we reproduce the characterization graphs in the paper using the released trace in this [Jupyter Notebook](analysis/GitHubCopilotCodingAgents/GitHubCopilotCodingAgentDataset2026.ipynb).
