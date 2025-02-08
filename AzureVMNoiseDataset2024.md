# Azure VM Noise Dataset 2024
-- revision 1, 20250202

## Introduction
This is a set of files representing a set of benchmarks run on Microsoft' Azure Virtual Machine offerings: `D8s_v5`, and `B8ms` over a period of around 483 days from `2023-05-28` to `2024-09-23`. This dataset is the data that is described in, and analyzed in the EuroSys 2025 paper 'TUNA: Tuning Unstable and Noisy Cloud Applications'.
A set of benchmarks were used to attempt to cover the main components in the VM, with the exception of the network: Cache, CPU, Disk, Memory, OS. Additionally, two end to end applications were also benchmarked: PostgreSQL and Redis.

### Main characteristics:
*	Dataset size: 277 MB
*	Number of files: 1520 files
*	Duration: 483 days
*   Average Benchmark Suite Duration: 130 minutes
*   Long Lived VM Characteristics:
    *   Metrics Collected: 3,661,602
    *   Total VMs: 12
*   Short Lived VM Characteristics:
    *   Metrics Collected: 3,375,618
    *	Total VMs: 43617
    *   Time between VM instantiations: 40 minutes


## Using the Data

### License
The data is made available and licensed under a [CC-BY Attribution License](https://github.com/Azure/AzurePublicDataset/blob/master/LICENSE). By downloading it or using them, you agree to the terms of this license.

### Attribution
If you use this data for a publication or project, please cite the accompanying paper:

> Johannes Freischuetz, Konstantinos Kanellis, Brian Kroth, and Shivaram Venkataraman. 2025. [TUNA: Tuning Unstable and Noisy Cloud Applications](https://2025.eurosys.org/accepted-papers.html). In Proceedings of the Twentieth European Conference on Computer Systems (EuroSys '25). Association for Computing Machinery, New York, NY, USA

We provide the traces as they are, but are willing to help researchers understand and use them. So, please let us know of any issues or questions by sending email to our  [mailing list](mailto:azurepublicdataset@service.microsoft.com).

### Downloading

You can download the dataset here:  [**vm-noise-data**](https://github.com/Azure/AzurePublicDataset/raw/master/data/vm-noise-data).
## Schema and Description
### Description
 * 1 file per measurement unit: `test_suite=<test_suite>/test_name=<test_name>/vm_duration=<duration>/vm_region=<region>/vm_type=<type>/<unit>.csv`

### Schema
|value|runtime|starttime|VM_id|
|--|--|
|measured value|duration of test|starting datetime of test|VM id, unique within dimension|

### Example
|value|runtime|starttime|VM_id|
|5095.0|33.26|2023-06-23 16:06:09.190|0|
|5095.0|33.23|2023-06-23 17:52:53.550|0|
|5098.0|87.77|2023-09-05 12:13:20.380|1|
|5098.0|88.12|2023-09-05 22:26:45.210|1|
|5096.0|33.23|2024-05-20 00:43:05.260|2|
|5101.0|33.22|2024-05-20 01:44:24.070|2|

#### Description
This benchmarking data was collected from `2023-05-28` to `2024-09-23` for a set of VMs and organized using the hive partitioning layout.
There are a series of `92` metrics collected from a series of `40` benchmarks. These metrics were collected from VMs in 3 dimensions: VM lifespan, VM type, and VM region.
For VM lifespan, we categorized VMs into two classes, long and short. Long running VMs ran for the entire duration of the study. Short running VMs were only ran each benchmark one time before being reallocated.
For VM types, we chose `D8s_v5` VMs and `B8ms` VMs.
For VM regions, we chose `westus2` and `eastus`.
There were three VMs allocated for each combination of dimensions.
There are some periods of missing data caused by crashes on our management nodes.