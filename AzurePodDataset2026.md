# Azure Pod Trace 2026

## Introduction

This trace is a representative sample of first-party Azure Kubernetes
Service (AKS) pod creation and lifecycle records over seven consecutive
relative days. It supports research on pre-provisioning, resource
allocation, packing, workload arrivals, lifetimes, and reuse of container
image bundles.

The release contains 85,570,448 records from a uniform draw of whole
namespace groups, followed by whole-group image-identity
exclusions. Sampling is at the group level, not the record level. The
resources are declared pod aggregates, not measured CPU or memory usage.

CPU and memory requests and limits are independently rounded **down** to
powers of two. Identifiers are pseudonymized and timestamps are relative.

The related publication is *Unipool: Efficient Management of
Pre-Provisioned Resources for Container Platforms* (SIGOPS ATC 2026).
This coarsened release is not a claim that every result in the paper can
be reproduced from these fields alone.

The dataset includes this description, a
[dataset card](analysis/AzurePods2026/DATASET_CARD.md), a
[field reference](analysis/AzurePods2026/schema.json), and
[reading and verification instructions](analysis/AzurePods2026/README.md).

## Using the data

### License

The data is licensed under the repository's
[Creative Commons Attribution 4.0 license](LICENSE).
Code examples follow the repository's [MIT license](LICENSE-CODE).

### Attribution

Please cite **Azure Pod Trace 2026**, in the
[Azure Public Dataset repository](https://github.com/Azure/AzurePublicDataset),
and the related paper:

> Hanfei Yu, Enrique Saurez, Íñigo Goiri, Hao Wang, and Rodrigo Fonseca.
> 2026. **Unipool: Efficient Management of Pre-Provisioned Resources for
> Container Platforms.** In *The 2026 ACM SIGOPS Annual Technical
> Conference (SIGOPS ATC 2026)*, November 15-18, 2026, Hong Kong, China.
> ACM, New York, NY, USA, 16 pages. DOI: `10.1145/3828523.3857110`.

[BibTeX entries](analysis/AzurePods2026/citation.bib) are provided for the
dataset and paper.

For questions about the release, use the repository's
[mailing list](mailto:azurepublicdataset@service.microsoft.com).

### Downloading

Download from the
[dataset release](https://github.com/Azure/AzurePublicDataset/releases/tag/dataset-pods-2026):

| Asset | Contents | Size |
| --- | --- | ---: |
| [AzurePodDataset2026.tar.gz](https://github.com/Azure/AzurePublicDataset/releases/download/dataset-pods-2026/AzurePodDataset2026.tar.gz) | CSV shards, manifest, and README | 1,756,177,115 bytes |
| [SHA256SUMS](https://github.com/Azure/AzurePublicDataset/releases/download/dataset-pods-2026/SHA256SUMS) | Archive checksum | Small text file |

The [download list](AzurePodDataset2026Links.txt) contains the same asset
URLs. Trace data is hosted as release assets, not as Git-tracked files.

The archive is approximately 1.64 GiB and contains 674 members:
`README.md`, `manifest.json`, and 672 header-bearing CSVs named
`part_0000.csv` through `part_0671.csv`. Each CSV corresponds to one
15-minute creation window. The uncompressed CSV payload is
10,517,181,916 bytes.

All shards belong to **one** dataset: IDs and invocation ordering are
consistent across files. The archive is not a byte-split download and
requires no concatenation with another archive.

## Dataset statistics

| Metric | Value |
| --- | ---: |
| Creation window | 7 days / 604,800,000 milliseconds |
| Pod records | 85,570,448 |
| Pseudonymous namespace groups | 383,364 |
| Pseudonymous image bundles | 103,360 |
| CSV shards | 672 |
| Missing CPU limits | 9,811,395 |
| Missing memory limits | 4,910,271 |
| Missing deletion times | 19,768,534 |
| Zero memory requests | 1,238,515 |
| Zero memory limits | 600 |

## Schema and processing

Each row represents one captured pod creation/lifecycle record.
`invocation_id` is the row identifier, not a serverless-function invocation.

| Field | Type | Meaning and processing |
| --- | --- | --- |
| `invocation_id` | Integer | Global sequence starting at 1 after creation-time/private tie-break ordering. |
| `customer_id` | String | Pseudonymous namespace identifier, stable across shards. |
| `container_group_id` | String | Keyed pseudonym of the normalized image-repository multiset; stable across namespaces and shards. |
| `created_time` | Integer | Creation time in milliseconds relative to the private trace origin. |
| `deleted_time` | Nullable integer | Deletion time relative to the same origin; blank when unavailable. |
| `requested_cpu` | Number | Aggregate CPU request, floored to powers of two in cores and stored in millicores. |
| `requested_memory_mib` | Number | Aggregate memory request, floored to powers of two in GiB and stored in MiB; zero preserved. |
| `limit_cpu` | Nullable number | Same CPU rounding for a present aggregate limit; blank remains blank. |
| `limit_memory_mib` | Nullable number | Same memory rounding for a present aggregate limit; zero and blank are distinct. |
| `num_containers` | Integer | Count of represented regular containers, unchanged by resource rounding. |
| `has_all_cpu_limits` | Boolean | Whether all represented containers have a CPU limit. |
| `has_all_mem_limits` | Boolean | Whether all represented containers have a memory limit. |

For positive `x` in cores or GiB, the released value is
`2^floor(log2(x))`: the largest power of two not exceeding `x`.
For example, 1.5 cores becomes 1 core, while 2 cores stays 2.
CPU conversion uses 1 core = 1,000 millicores; memory conversion uses
1 GiB = 1,024 MiB. Read resource fields as floating-point numbers,
not integers.

CPU uses emitted exponents -10 through 12; memory uses -33 through 12.
Smaller positive memory amounts extend below the nominal exponent -10
rather than being clipped or converted to zero. Missing limits remain
blank. The shared monotone rule for each dimension preserves valid
request/limit ordering, but it can change equality and ratios.

Identifiers use independent hashing domains. Hash outputs are truncated
to 16 bytes and rendered as 32 lowercase hexadecimal characters. Image grouping ignores
tags and digests, preserves registry/repository and duplicate images,
and is independent of container ordering. No individual-image identifiers
or raw image names are released.

The [dataset card](analysis/AzurePods2026/DATASET_CARD.md) describes the
selection, source coverage, exclusions, and interpretation limits.

## Validation and limitations

The producer checks source checksums, row counts, identifier consistency,
timestamps, and resource relationships. Persisted output fields are
verified, and every decompressed archive member is checked against its
expected SHA-256. A public checksum is also provided in
[SHA256SUMS](analysis/AzurePods2026/SHA256SUMS).

This validates the release's integrity and transformation rules, not
population representativeness. Declared resources are not
usage measurements. A missing deletion is not necessarily ordinary
right-censoring. Quantized values and combinations may be unobserved in
the source or unsuitable for verbatim use in a Kubernetes API request.
