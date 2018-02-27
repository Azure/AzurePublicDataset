# Overview


This repository contains a representative subset of the first-party virtual machine workload (VM) of Microsoft Azure in one of its geographical regions.  The trace is a sanitized subset of the Azure VM workload described in ["Resource Central: Understanding and Predicting Workloads for Improved Resource Management in Large Cloud Platforms"](https://www.microsoft.com/en-us/research/wp-content/uploads/2017/10/Resource-Central-SOSP17.pdf) in SOSP’17.  We include in this repository a [jupyter notebook](https://github.com/Azure/AzurePublicDataset/blob/master/analysis/Azure%20Public%20Dataset%20-%20Trace%20Analysis.ipynb) that directly compares the main characteristics of the two traces, showing that they are qualitatively very similar.

We provide the trace as is, but are willing to help researchers understand and use it.  So, please let us know of any issues or questions by sending email to our [mailing list](mailto:azurepublicdataset@service.microsoft.com).

If you do use this trace in your research, please make sure to cite our SOSP’17 paper (mentioned above).

## VM Trace
The trace contains a representative subset of the first-party Azure VM workload in one geographical region.  The main trace characteristics and schema are:

### Main characteristics:
*	Dataset size: 117GB
*	Compressed dataset size: 78.5GB
*	Number of files: 128 files
*	Duration: 30 consecutive days
*	Total number of VMs: 2,013,767
*	Total number of Azure subscriptions: 5,958
*	Timeseries data: 5-minute VM CPU utilization readings, VM information table and subscription table (with main fields encrypted)
*	Total VM hours: 104,371,713
*	Total number of VM CPU utilization readings: 1,246,539,221
*	Total virtual core hours: 237,815,104


### Schema:
1.	Encrypted subscription id
2.	Encrypted deployment id 
3.	Timestamp in seconds (starting from 0) when first VM created
4.	Count VMs created
5.	Deployment size (we define a “deployment” differently than Azure in our paper)
6.	Encrypted VM id
7.	Timestamp VM created
8.	Timestamp VM deleted
9.	Max CPU utilization
10.	Avg CPU utilization
11.	P95 of Max CPU utilization
12.	VM category
13.	VM virtual core count
14.	VM memory (GBs)
15.	Timestamp in seconds (every 5 minutes)
16.	Min CPU utilization during the 5 minutes
17.	Max CPU utilization during the 5 minutes
18.	Avg CPU utilization during the 5 minutes

### Downloading instructions
You can download the dataset from Azure Blob Storage using the links available [here](https://github.com/Azure/AzurePublicDataset/blob/master/AzurePublicDatasetLinks.txt).

### Contact us
Please let us know of any issues or questions by sending email to our [mailing list](mailto:azurepublicdataset@service.microsoft.com).

This trace derives from a collaboration between Azure and Microsoft Research.
