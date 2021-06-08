# AzurePublicDatasetV2

## VM Trace
The trace contains a representative subset of the first-party Azure VM workload in one geographical region.  
This [jupyter notebook](https://github.com/Azure/AzurePublicDataset/blob/master/analysis/Azure%202019%20Public%20Dataset%20V2%20-%20Trace%20Analysis.ipynb) directly compares the main characteristics of the this trace and the a complete Azure workload in 2019, showing that they are qualitatively very similar (except for VM deployment sizes).

The main trace characteristics and schema are:

### Main characteristics:
*	Dataset size: 235GB
*	Compressed dataset size: 156GB
*	Number of files: 198 files
*	Duration: 30 consecutive days
*	Total number of VMs: 2,695,548
*	Total number of Azure subscriptions: 6,687
*	Timeseries data: 5-minute VM CPU utilization readings, VM information table and subscription table (with main fields encrypted)
*	Total VM hours: 104,371,713
*	Total number of VM CPU utilization readings: 1,942,780,023
*	Total virtual core hours: >380,000,000


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
13.	VM virtual core count bucket
14.	VM memory (GBs) bucket
15.	Timestamp in seconds (every 5 minutes)
16.	Min CPU utilization during the 5 minutes
17.	Max CPU utilization during the 5 minutes
18.	Avg CPU utilization during the 5 minutes
19. VM virtual core count bucket definition
20. VM memory (GBs) bucket definition

### Downloading instructions
You can download the dataset from Azure Blob Storage using the links available [here](https://github.com/Azure/AzurePublicDataset/blob/master/AzurePublicDatasetLinksV2.txt).
