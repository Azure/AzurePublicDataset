# Dataset Card: Azure Pod Trace 2026

## Summary

First-party Azure Kubernetes Service (AKS) pod
creation/lifecycle records covering seven consecutive relative days.
The trace contains 85,570,448 records in 672 fifteen-minute CSV shards,
with 383,364 pseudonymous namespace groups and 103,360 pseudonymous image
bundles.

This dataset contains a representative sample of pod creation records,
with an unspecified sampling fraction. The released trace alone does not
support estimating total service traffic.

Intended uses include pre-provisioning, allocation, packing, arrival and
lifetime replay, and image-bundle reuse studies. Resources are declared
requests and limits, not measurements of actual CPU or memory consumption.

## Collection and selection

1. Source collection uses successful controller-manager pod creates,
   excludes `kube-system`, and represents regular containers with CPU
   requests. Init containers and regular containers without CPU requests
   are not represented.
2. A verified ownership lookup retains confirmed first-party rows;
   third-party and unresolved ownership are excluded. Ownership reflects
   the lookup snapshot rather than necessarily the original event time.
3. Existing request exclusions remove CPU requests at or below zero or
   above 256,000 millicores, and memory requests above 1,048,576 MiB.
   Those request cutoffs are not applied to limits.
4. One uniform draw selects whole namespace groups.
   All eligible records for selected groups are retained without seed
   retries or a record-count balancing target.
5. A selected group is excluded in full if any eligible row has an
   invalid image-repository multiset or inconsistent represented-container
   count. No replacement groups are drawn.

Sampling is at the group level rather than the pod-record level.
The reported counts describe only the released sample.

## Pseudonymization and resource processing

`customer_id` is the pseudonymous namespace identifier, stable across
shards. Cluster identifiers are not included. A namespace ID can combine
records from multiple clusters.

Image-bundle IDs encode sorted image-repository multisets. Tags and digests
are ignored; registries, repository paths, and duplicates are retained.
The same normalized bundle has one ID across namespaces and shards.
Different image bundles can nevertheless represent the same software family.

Identifiers use independent hashing domains. Hash outputs are truncated
to 16 bytes and rendered as 32 lowercase hexadecimal characters. The keys and
selection-to-dataset mappings are not included.

The four resource columns are rounded independently down to the largest
power of two not exceeding each positive value, in cores or GiB.
CSV units remain millicores and MiB. Zero stays zero, and missing limits
stay blank. Positive amounts remain positive by extending the lower grid
when necessary; no out-of-range amount is clipped to a fixed endpoint.
Requests and limits use the same monotone rule for their dimension.

The source aggregates are used as captured; original Kubernetes quantity
strings are not reconstructed or reparsed. Values and complete resource
combinations may be new after quantization. No dataset row, identifier,
time, ordering, count, or limit-presence flag is changed by this step.

## Timing and missingness

Creation and known deletion times are millisecond offsets from one private
trace origin. Shard names identify relative
creation windows, not production calendar dates.

Rows are ordered by creation time and a private keyed UID tie-breaker.
Invocation IDs start at 1 and continue across all shards.

The source deletion lookup includes completed lifetimes of at least two
seconds. Missing deletion times can therefore arise for reasons other
than ordinary right-censoring. Known deletion times may extend beyond the
seven-day creation window.

Missing memory requests are zero upstream. A pod-level limit is present
only when all represented containers provide that resource limit.
Zero memory and a missing limit are distinct states.

## Format and integrity

One `.tar.gz` contains `README.md`, `manifest.json`, and 672 CSVs.
All CSVs include the twelve-column header defined in [schema.json](schema.json).
The archive is 1,756,175,813 bytes; the CSV payload is 10,517,181,916 bytes.

The manifest records shard checksums, sizes, row counts, and invocation
ranges. The archive checksum is in [SHA256SUMS](SHA256SUMS).
Source and output integrity checks preserve the selected population and
non-resource fields; archive validation checks every decompressed member.

## Excluded information and limitations

The release contains no raw pod UIDs, namespace or
container names, image references, individual-image hashes, absolute
production timestamps, keys, or private audit/identity mappings.
It also does not label pre-provisioned versus active pods or provide
measured cold-start, readiness-latency, or resource-utilization telemetry.

Bundle equality does not identify a software family or version.

Do not interpret the data as actual utilization, exact original resource
allocations, a list of Kubernetes-API-valid deployment quantities, or a
representative sample of third-party customers. Quantization can change
request/limit ratios and equality even though valid ordering is preserved.

The [related paper and dataset citation](citation.bib) provide attribution;
this release does not claim exact reproduction of all paper results.

## License

Data: [CC-BY 4.0](../../LICENSE). Code examples: [MIT](../../LICENSE-CODE).
