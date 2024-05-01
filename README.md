# Overview

This repository contains public releases of Microsoft Azure traces for the benefit of the research and academic community.
There are currently two classes of traces: 

* VM Traces: two representative traces of the virtual machine (VM) workload of Microsoft Azure collected in 2017 and 2019, and one VM request trace specifically for investigating packing algorihtms.
* Azure Functions Traces: representative traces of Azure Functions invocations, collected over two weeks in 2019, and of Azure Functions blob accesses, collected between November and December of 2020.
* Azure LLM Inference Traces: representative traces of LLM inference invocations with input and output tokens, collected on November 2023.

We provide the traces as they are, but are willing to help researchers understand and use them. So, please let us know of any issues or questions by sending email to our  [mailing list](mailto:azurepublicdataset@service.microsoft.com).

## Quick links by paper:

* Traces ([2017](https://github.com/Azure/AzurePublicDataset/blob/master/AzurePublicDatasetV1.md))([2019](https://github.com/Azure/AzurePublicDataset/blob/master/AzurePublicDatasetV2.md)) for the paper "Resource Central: Understanding and Predicting Workloads for Improved Resource Management in Large Cloud Platforms" (SOSP'17)
* Traces ([2019](https://github.com/Azure/AzurePublicDataset/blob/master/AzureFunctionsDataset2019.md)) for the paper "Serverless in the Wild: Characterizing and Optimizing the Serverless Workload at a Large Cloud Provider" (ATC'19)
* Traces ([2020](https://github.com/Azure/AzurePublicDataset/blob/master/AzureTracesForPacking2020.md)) for the paper "Protean: VM Allocation Service at Scale" (OSDI'20)
* Traces ([2020](https://github.com/Azure/AzurePublicDataset/blob/master/AzureFunctionsBlobDataset2020.md)) for the paper "Faa$T: A Transparent Auto-Scaling Cache for Serverless Applications" (SoCC'21)
* Traces ([2023](https://github.com/Azure/AzurePublicDataset/blob/master/AzureLLMInferenceDataset2023.md)) for the paper "Splitwise: Efficient generative LLM inference using phase splitting" (ISCA'24)

## VM Traces

The traces are sanitized subsets of the first-party VM workload in one of Azure’s geographical regions.  We include jupyter notebooks that directly compare the main characteristics of each trace to its corresponding full VM workload, showing that they are qualitatively very similar (except for VM deployment sizes in 2019).  Comparing the characteristics of the two traces illustrates how the workload has changed over this two-year span.

If you do use either of these VM traces in your research, please make sure to cite our SOSP’17 paper ["Resource Central: Understanding and Predicting Workloads for Improved Resource Management in Large Cloud Platforms"](https://www.microsoft.com/en-us/research/wp-content/uploads/2017/10/Resource-Central-SOSP17.pdf), which includes a full analysis of the Azure VM workload in 2017.

### Trace Locations

* [AzurePublicDatasetV1](https://github.com/Azure/AzurePublicDataset/blob/master/AzurePublicDatasetV1.md) - Trace created using data from 2017 Azure VM workload containing information about ~2M VMs and 1.2B utilization readings.
* [AzurePublicDatasetV2](https://github.com/Azure/AzurePublicDataset/blob/master/AzurePublicDatasetV2.md) - Trace created using data from 2019 Azure VM workload containing information about ~2.6M VMs and 1.9B utilization readings.

## Azure Traces for Packing

* [AzureTracesForPacking2020](https://github.com/Azure/AzurePublicDataset/blob/master/AzureTracesForPacking2020.md) - This dataset represents part of the workload on Microsoft's Azure Compute and is specifically intended to evaluate packing algorithms. The dataset includes:

  * VM requests along with their priority
  * The lifetime for each requested VM
  * The (normalized) resources allocated for each VM type.

If you do use the Azure Trace for Packing in your research, please make sure to cite our OSDI'20 paper ["Protean: VM Allocation Service at Scale"](https://www.usenix.org/system/files/osdi20-hadary.pdf), which includes a description of the Azure allocator and related workload analysis.


## Azure Functions Traces

### Function Invocations
* [AzureFunctionsDataset2019](https://github.com/Azure/AzurePublicDataset/blob/master/AzureFunctionsDataset2019.md) - These traces contain, for a subset of applications running on Azure Functions in July of 2019:

  * how many times per minute each (anonymized) function is invoked and its corresponding trigger group
  * how (anonymized) functions are grouped into (anonymized) applications, and how applications are grouped by (anonymized) owner
  * the distribution of execution times per function
  * the distribution of memory usage per application

If you do use the Azure Functions 2019 traces in your research, please make sure to cite our ATC'20 paper ["Serverless in the Wild: Characterizing and Optimizing the Serverless Workload at a Large Cloud Provider"](https://www.microsoft.com/en-us/research/uploads/prod/2020/05/serverless-ATC20.pdf), which includes a full analysis of the Azure Functions workload in July 2019.

* [AzureFunctionsInvocationTrace2021](https://github.com/Azure/AzurePublicDataset/blob/master/AzureFunctionsInvocationTrace2021.md) - This is a trace of function invocations for two weeks starting on 2021-01-31. The trace contains invocation arrival and departure (or compeletion) times, with the folloiwng schema:  

  * app: application id (encrypted)
  * func: function id (encrypted), and unique only within an application 
  * end_timestamp: function invocation end timestamp in millisecond
  * duration: duration of function invocation in millisecond


If you do use the Azure Functions 2021 trace in your research, please cite this SOSP'21 paper ["Faster and Cheaper Serverless Computing on Harvested Resources"](https://www.microsoft.com/en-us/research/publication/faster-and-cheaper-serverless-computing-on-harvested-resources/).

### Functions Blob Accesses

* [AzureFunctionsBlobDataset2020](https://github.com/Azure/AzurePublicDataset/blob/master/AzureFunctionsBlobDataset2020.md) - This is a sample of the blob accesses in Microsoft's Azure Functions, collected between November 23<sup>rd</sup> and December 6<sup>th</sup> 2020. This dataset is the data described and analyzed in the SoCC 2021 paper 'Faa$T: A Transparent Auto-Scaling Cache for Serverless Applications'.


## Azure LLM Inference Traces
* [AzureLLMInferenceDataset2023](https://github.com/Azure/AzurePublicDataset/blob/master/AzureLLMInferenceDataset2023.md) - This is a sample of two LLM inference services in Azure containing the input and output tokens. This dataset was collected on November 11<sup>th</sup> 2023. This contains the data described and analyzed in the ISCA 2024 paper 'Splitwise: Efficient generative LLM inference using phase splitting'.

### Contact us
Please let us know of any issues or questions by sending email to our [mailing list](mailto:azurepublicdataset@service.microsoft.com).

These traces derive from a collaboration between Azure and Microsoft Research.
