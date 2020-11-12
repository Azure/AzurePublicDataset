# Overview

This repository contains public releases of Microsoft Azure traces for the benefit of the research and academic community.
There are currently two classes of traces: 

* The first class contains two representative traces of the virtual machine (VM) workload of Microsoft Azure collected in 2017 and 2019.  
* The second contains representative traces of Azure Functions invocations, collected over two weeks in 2019. 

We provide the traces as they are, but are willing to help researchers understand and use them. So, please let us know of any issues or questions by sending email to our  [mailing list](mailto:azurepublicdataset@service.microsoft.com).

## VM Traces

The traces are sanitized subsets of the first-party VM workload in one of Azure’s geographical regions.  We include jupyter notebooks that directly compare the main characteristics of each trace to its corresponding full VM workload, showing that they are qualitatively very similar (except for VM deployment sizes in 2019).  Comparing the characteristics of the two traces illustrates how the workload has changed over this two-year span.


If you do use either of these VM traces in your research, please make sure to cite our SOSP’17 paper ["Resource Central: Understanding and Predicting Workloads for Improved Resource Management in Large Cloud Platforms"](https://www.microsoft.com/en-us/research/wp-content/uploads/2017/10/Resource-Central-SOSP17.pdf), which includes a full analysis of the Azure VM workload in 2017.

### Trace Locations

* [AzurePublicDatasetV1](https://github.com/Azure/AzurePublicDataset/blob/master/AzurePublicDatasetV1.md) - Trace created using data from 2017 Azure VM workload containing information about ~2M VMs and 1.2B utilization readings.
* [AzurePublicDatasetV2](https://github.com/Azure/AzurePublicDataset/blob/master/AzurePublicDatasetV2.md) - Trace created using data from 2019 Azure VM workload containing information about ~2.6M VMs and 1.9B utilization readings.

## Azure Functions Traces

* [AzureFunctionsDataset2019](https://github.com/Azure/AzurePublicDataset/blob/master/AzureFunctionsDataset2019.md) - These traces contain, for a subset of applications running on Azure Functions in July of 2019:

  * how many times per minute each (anonymized) function is invoked and its corresponding trigger group
  * how (anonymized) functions are grouped into (anonymized) applications, and how applications are grouped by (anonymized) owner
  * the distribution of execution times per function
  * the distribution of memory usage per application

If you do use the Azure Functions traces in your research, please make sure to cite our ATC'20 paper ["Serverless in the Wild: Characterizing and Optimizing the Serverless Workload at a Large Cloud Provider"](https://www.microsoft.com/en-us/research/uploads/prod/2020/05/serverless-ATC20.pdf), which includes a full analysis of the Azure Functions workload in July 2019.

## Azure Trace for Packing

* [AzureTracesForPackingV1](https://github.com/Azure/AzurePublicDataset/blob/master/AzureTracesForPackingV1.md) - This dataset represents part of the workload on Microsoft's Azure Compute and is specifically designed to evaluate packing algorithms.

### Contact us
Please let us know of any issues or questions by sending email to our [mailing list](mailto:azurepublicdataset@service.microsoft.com).

These traces derive from a collaboration between Azure and Microsoft Research.
