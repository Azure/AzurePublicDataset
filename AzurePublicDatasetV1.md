# AzurePublicDatasetV1

## VM Trace
The trace contains a representative subset of the first-party Azure VM workload in one geographical region.  
This [jupyter notebook](https://github.com/Azure/AzurePublicDataset/blob/master/analysis/Azure%20Public%20Dataset%20-%20Trace%20Analysis.ipynb) directly compares the main characteristics of the this trace and the one described in ["Resource Central: Understanding and Predicting Workloads for Improved Resource Management in Large Cloud Platforms"](https://www.microsoft.com/en-us/research/wp-content/uploads/2017/10/Resource-Central-SOSP17.pdf) -  SOSP’17, showing that they are qualitatively very similar.

The main trace characteristics and schema are:

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
You can download the dataset from Azure Blob Storage using the links available [here](https://github.com/Azure/AzurePublicDataset/blob/master/AzurePublicDatasetV1Links.txt).
