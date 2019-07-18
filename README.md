# Overview

This repository contains two representative traces of the virtual machine (VM) workload of Microsoft Azure collected in 2017 and 2019.  The traces are sanitized subsets of the first-party VM workload in one of Azure’s geographical regions.  We include jupyter notebooks that directly compare the main characteristics of each trace to its corresponding full VM workload, showing that they are qualitatively very similar (except for VM deployment sizes in 2019).  Comparing the characteristics of the two traces illustrates how the workload has changed over this two-year span.

We provide the trace as is, but are willing to help researchers understand and use it.  So, please let us know of any issues or questions by sending email to our [mailing list](mailto:azurepublicdataset@service.microsoft.com).

If you do use either of these traces in your research, please make sure to cite our SOSP’17 paper ["Resource Central: Understanding and Predicting Workloads for Improved Resource Management in Large Cloud Platforms"](https://www.microsoft.com/en-us/research/wp-content/uploads/2017/10/Resource-Central-SOSP17.pdf), which includes a full analysis of the Azure VM workload in 2017.

## VM Trace

* [AzurePublicDatasetV1](https://github.com/Azure/AzurePublicDataset/blob/master/AzurePublicDatasetV1.md) - Trace built using data from 2017 Azure VM Workload containing information about ~2MM VMs and 1.2B CPU Readings.
* [AzurePublicDatasetV2](https://github.com/Azure/AzurePublicDataset/blob/master/AzurePublicDatasetV2.md) - Trace built using data from 2019 Azure VM Workload containing information about ~2.6MM VMs and 1.9B CPU Readings.


### Contact us
Please let us know of any issues or questions by sending email to our [mailing list](mailto:azurepublicdataset@service.microsoft.com).

This trace derives from a collaboration between Azure and Microsoft Research.
