# Azure VM Noise Dataset 2024

-- revision 1, 20250202

## Introduction

This directory contains a set of files representing a collection of benchmarks run on Microsoft Azure Virtual Machine offerings (`D8s_v5` and `B8ms`) over a period of around 483 days from `2023-05-28` to `2024-09-23`.
We used [SSDv2 Disks](https://learn.microsoft.com/en-us/azure/virtual-machines/disks-types#premium-ssd-v2) as the "remote disk", and a [Premium SSDs](https://learn.microsoft.com/en-us/azure/virtual-machines/disks-types#premium-ssds) as the "local disk" in the tests.
This dataset is the data that is described in, and analyzed in the EuroSys 2025 paper [TUNA: Tuning Unstable and Noisy Cloud Applications](https://www.microsoft.com/en-us/research/publication/tuna-tuning-unstable-and-noisy-cloud-applications/).
A set of benchmarks were used to attempt to cover the main components in the VM, with the exception of the network: Cache, CPU, Disk, Memory, OS.
Additionally, two end to end applications were also benchmarked: PostgreSQL and Redis.

### Main characteristics

* Dataset size: 277 MB
* Number of files: 1520 files
* Duration: 483 days
* Average Benchmark Suite Duration: 130 minutes
* Long Lived VM Characteristics:
  * Metrics Collected: 3,661,602
  * Total VMs: 12
* Short Lived VM Characteristics:
  * Metrics Collected: 3,375,618
  * Total VMs: 43617
  * Time between VM instantiations: 40 minutes

## Using the Data

### License

The data is made available and licensed under a [CC-BY Attribution License](https://github.com/Azure/AzurePublicDataset/blob/master/LICENSE). By downloading it or using them, you agree to the terms of this license.

### Attribution

If you use this data for a publication or project, please cite the accompanying paper:

> Johannes Freischuetz, Konstantinos Kanellis, Brian Kroth, and Shivaram Venkataraman. 2025. \
> [TUNA: Tuning Unstable and Noisy Cloud Applications](https://www.microsoft.com/en-us/research/publication/tuna-tuning-unstable-and-noisy-cloud-applications/). \
> In Proceedings of the Twentieth European Conference on Computer Systems (EuroSys '25). \
> Association for Computing Machinery, New York, NY, USA

```bibtex
@inproceedings {TUNA,
  author = {Johannes Freischuetz and Konstantinos Kanellis and Brian Kroth, and Shivaram Venkataraman},
  title = {TUNA: Tuning Unstable and Noisy Cloud Applications},
  booktitle = {EuroSys '25: Proceedings of the Nineteenth European Conference on Computer Systems},
  publisher = {Association for Computing Machinery}, address = {New York, NY, USA}, year={2025}, month = {mar}
}
```

We provide the traces as they are, but are willing to help researchers understand and use them. So, please let us know of any issues or questions by sending email to our  [mailing list](mailto:azurepublicdataset@service.microsoft.com).

### Downloading

You can download the dataset here:  [**vm-noise-data**](https://github.com/Azure/AzurePublicDataset/tree/master/vm-noise-data).

## Schema and Description

### Layout

* 1 file per measurement unit, partitioned using Hive style table partitioning layout:

  ```txt
  test_suite=<test_suite>/test_name=<test_name>/vm_lifespan=(short|long)/vm_region=(eastus|westus2)/vm_sku=(B8ms|D8s_v5)/unit=<unit>.csv
  ```

  Where `test_suite` and `test_name` can be taken from the table in the [benchmarks](#benchmarks) section below.

### Schema

|value|runtime|starttime|VM_id|
|--|--|--------|--|
|measured value|duration of test (in seconds)|starting datetime of test|VM id (unique within dimension)|

### Example

|value|runtime|starttime|VM_id|
|-----|-------|---------|-----|
|5095.0|33.26|2023-06-23 16:06:09.190|0|
|5095.0|33.23|2023-06-23 17:52:53.550|0|
|5098.0|87.77|2023-09-05 12:13:20.380|1|
|5098.0|88.12|2023-09-05 22:26:45.210|1|
|5096.0|33.23|2024-05-20 00:43:05.260|2|
|5101.0|33.22|2024-05-20 01:44:24.070|2|

### Sample Code

Some sample code for using this data in a notebook can be found in [`vm-noise-data/sample.ipynb`](https://github.com/Azure/AzurePublicDataset/tree/master/vm-noise-data/sample.ipynb)

#### Description

This benchmarking data was collected from `2023-05-28` to `2024-09-23` for a set of VMs and organized using the hive partitioning layout.

There are a series of `92` metrics collected from a series of `40` benchmarks.

These metrics were collected from VMs in 3 dimensions:

1. VM lifespan

    For VM lifespan, we categorized VMs into two classes: `short` and `long`.

    Long running VMs were provisioned once and ran for the entire duration of the study.

    Short running VMs were only ran each benchmark one time before being reallocated.

    The purpose of this dimension is to influence which backend host the VM was assigned to in order to increase samples across different backend hosts. While we omit host information, short lived VMs were mostly place on distinct hosts, and long lived VMs had almost no migrations.

2. VM SKU

    For VM SKUs, we chose [`D8s_v5`](https://learn.microsoft.com/en-us/azure/virtual-machines/sizes/general-purpose/d-family?tabs=dpsv6%2Cdpdsv6%2Cdasv6%2Cdalsv6%2Cdv5%2Cddv5%2Cdasv5%2Cdpsv5%2Cdplsv5%2Cdlsv5%2Cdv4%2Cdav4%2Cddv4%2Cdv3%2Cdv2#dv5-and-dsv5-series) VMs and [`B8ms`](https://learn.microsoft.com/en-us/azure/virtual-machines/sizes/general-purpose/b-family) VMs.

3. VM region

    For VM regions, we chose [`westus2`](https://datacenters.microsoft.com/globe/explore?info=region_westus2) and [`eastus`](https://datacenters.microsoft.com/globe/explore?info=region_eastus)

There were three VMs allocated for each combination of VM dimensions.

> Note: There are some periods of missing data caused by crashes on our management nodes.

#### Benchmarks

The benchmarks used came from the following suites:

| Suite | Benchmarks | Description |
|---|---|---|
| [Flexible IO Tester](https://openbenchmarking.org/test/pts/fio) | (Random Read) <br> Random Write <br> Sequential Read <br> Sequential Write | Test the throughput in MiB/s and IOPS, and the latency of various disk operations |
| [Intel Memory Latency Checker](https://openbenchmarking.org/test/pts/intel-mlc) | Idle Latency Max Bandwidth and Peak Injeciton Bandwidth: <br> - All reads <br> - 1:1 read <br> - write ratio <br> - 2:1 read <br> - write ratio <br> - 3:1 read <br> - write ratio <br> - stream-triad like | Test throughput of various memory operations |
| [OS Bench](https://openbenchmarking.org/test/pts/osbench) | Create Files <br> Create Processes <br> Create Threads <br> Launch Programs <br> Memory Allocations | Measure latency for various OS related operations |
| [perf-bench](https://openbenchmarking.org/test/pts/perf-bench) | Epoll Wait <br> Memcpy <br> Memset <br> Syscall Basic | Measure other OS related operations |
| [PostgreSQL](https://openbenchmarking.org/test/pts/pgbench) | All combinations of the following: <br> Scaling Factor: 25 / 2500 <br> Client: 1 / 25 <br> Mode: Read Only / Read Write from pgbench | Measure various workload combinations using pgbench |
| [Redis](https://openbenchmarking.org/test/pts/redis-1.3.1) | redis-benchmark tests for the following: <br> - GET <br> - LPOP <br> - LPUSH <br> - SADD <br> - SET | Benchmark various redis operations using redis-benchmark |
| [stress-ng](https://openbenchmarking.org/test/pts/stress-ng) | CPU_Cache <br> CPU Stress <br> Matrix Math <br> Memory Copy | Benchmark the CPU, and one memory benchmark |
| [Sysbench](https://openbenchmarking.org/test/pts/sysbench) | CPU <br> RAM Memory | Benchmark CPU and Benchmark |

During each iteration, the full set of benchmarks were run in a random order with a random splay between each benchmark.

## See Also

* <https://aka.ms/mlos/tuna-eurosys-artifacts> - The artifacts for the EuroSys 2025 paper 'TUNA: Tuning Unstable and Noisy Cloud Applications'
