# Trace Data

This folder should contain the downloaded GHCP coding agent trace shards.

## Download Instructions

Download the trace files from the GitHub release:

**[Download from GitHub Releases](https://github.com/Azure/AzurePublicDataset/releases/tag/ghcp-coding-agent-2026)**

After downloading, extract the files so the folder structure looks like:

```
downloaded_data/
  date=2026-06-01/
    shard-0000.jsonl.gz
    shard-0001.jsonl.gz
    ...
  date=2026-06-02/
    ...
  date=2026-06-07/
    ...
```

The analysis scripts expect the `date=YYYY-MM-DD/` subfolders with `.jsonl.gz` shard files.

## Schema

See [`../schema.json`](../schema.json) and [`../DATASET_CARD.md`](../DATASET_CARD.md) for the full field reference and dataset description.
