# Reading Azure Pod Trace 2026

See the [dataset page](../../AzurePodDataset2026.md),
[dataset card](DATASET_CARD.md), and [field reference](schema.json).
This directory contains documentation, checksums, and analysis code, not
the trace data or the paper PDF.

This dataset contains a representative sample of pod creation records,
with an unspecified sampling fraction. The released trace alone does not
support estimating total service traffic.

## Analysis notebook

[AzurePodDataset2026.ipynb](AzurePodDataset2026.ipynb) presents the Unipool
paper's **Instance lifetimes** and **Request arrivals** analyses, plus CPU
and memory distributions, on this release. The notebook contains its
analysis code, which downloads, verifies, and streams the archive, so no
companion script is needed.

```bash
pip install -r requirements.txt
```

Open the notebook in Jupyter or VS Code and run all cells. The first run
downloads the 1.64 GiB archive into `downloaded_data/`.

## Download and verify

Download `AzurePodDataset2026.tar.gz` from the
[release](https://github.com/Azure/AzurePublicDataset/releases/tag/dataset-pods-2026)
into an ignored `downloaded_data` directory. Use the
[repository checksum file](SHA256SUMS) to verify it.

In PowerShell, from this directory:

```powershell
New-Item -ItemType Directory -Path downloaded_data -Force | Out-Null
Copy-Item -LiteralPath SHA256SUMS -Destination downloaded_data
Set-Location downloaded_data
$release = 'https://github.com/Azure/AzurePublicDataset/releases/download/dataset-pods-2026'
Invoke-WebRequest -Uri "$release/AzurePodDataset2026.tar.gz" -OutFile AzurePodDataset2026.tar.gz
$expected = ((Get-Content -LiteralPath SHA256SUMS -Raw).Trim() -split '\s+')[0]
$actual = (Get-FileHash -LiteralPath AzurePodDataset2026.tar.gz -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actual -cne $expected) { throw 'Archive checksum mismatch' }
tar -xzf AzurePodDataset2026.tar.gz
```

On systems with `sha256sum`, copy the repository checksum file beside the
archive and check it with `sha256sum --check SHA256SUMS`.

The extracted archive has this flat layout:

```text
README.md
manifest.json
part_0000.csv
part_0001.csv
...
part_0671.csv
```

The manifest lists per-shard byte counts, SHA-256 checksums, record counts,
and global invocation ranges. It also specifies the resource policy and
dataset-wide counts. It contains no keys or reversible identity mapping.

## Read incrementally

Each CSV has its own header. Read one file at a time or stream rows; the
complete CSV payload is about 10.52 GB.

This Python standard-library example reads a single shard without loading
it into memory:

```python
import csv

with open("part_0000.csv", encoding="utf-8", newline="") as stream:
    for row in csv.DictReader(stream):
        created_ms = int(row["created_time"])
        deleted_ms = (
            int(row["deleted_time"]) if row["deleted_time"] else None
        )
        requested_cores = float(row["requested_cpu"]) / 1000.0
        requested_mib = float(row["requested_memory_mib"])
        limit_cores = (
            float(row["limit_cpu"]) / 1000.0 if row["limit_cpu"] else None
        )
        completed_duration_ms = (
            deleted_ms - created_ms if deleted_ms is not None else None
        )
        # Consume this row before continuing to the next record.
```

Preserve `customer_id` and `container_group_id` as strings. Their values
are stable throughout this release, including across shards. Resource
fields require floating-point parsing; some values are fractional
millicores or MiB. Do not replace missing limits or deletion times with
zero, and do not assume every missing deletion means the pod remained
alive until the end of the creation window.

For a full chronological replay, traverse shards by their numbered names.
Do not concatenate raw CSV files without removing repeated headers.
Downloading or analyzing fewer shards gives a partial observation of
otherwise whole-group traces.

## Reproducibility scope

The released trace preserves its selected records' identifiers, ordering,
relative timestamps, container counts, and limit-presence flags.
The four resource fields are independently floored to powers of two.
This material does not claim to reproduce all results in the related
paper, whose experiments can require additional data or configurations.

The data follows the repository's [CC-BY 4.0 license](../../LICENSE);
code examples follow [MIT](../../LICENSE-CODE).
