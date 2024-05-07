# Azure Functions Trace 2019
-- revision 2, 20200618

## Introduction
This is a set of files representing part of the workload of Microsoft's Azure Functions offering, collected in July of 2019. This dataset is a subset of the data described in, and analyzed, in the USENIX ATC 2020 paper 'Serverless in the Wild: Characterizing and Optimizing the Serverless Workload at a Large Cloud Provider'. 

Functions in Azure Functions are grouped into Applications. Included here is only data pertaining to a random sample of Azure Functions applications. The sampling is done per application, so that if there is data about an application in the trace, then all of its functions are included. The sampling rate is small and unspecified, but as the accompanying notebook shows, the distributions in the released trace are a good match to those in the ATC paper.

In Azure Functions, [applications are the unit of resource allocation](https://docs.microsoft.com/en-us/azure/azure-functions/functions-reference#function-app). This has a few practical implications: for example, warm-up decisions are made at the application level, and memory allocation is measured by application, not by function. The 'HashOwner' field in these files is used to group applications that belong to the same subscription in Azure. It is included to indicate applications that are possibly related to each other. 

The dataset comprises this description, and an [R notebook](https://github.com/Azure/AzurePublicDataset/blob/master/analysis/AzureFunctionsDataset2019-Trace_Analysis.md) with plots comparing the released trace with the ATC paper, and the following sets of files: 

 - Function invocation counts and triggers
 - Function execution time distributions
 - Application memory allocation distributions 
 
## Using the Data

### License
The data is made available and licensed under a [CC-BY Attribution License](https://github.com/Azure/AzurePublicDataset/blob/master/LICENSE). By downloading it or using them, you agree to the terms of this license.

### Attribution
If you use this data for a publication or project, please cite the accompanying paper:

> Mohammad Shahrad, Rodrigo Fonseca, Inigo Goiri, Gohar Chaudhry, Paul Batum, Jason Cooke, Eduardo Laureano, Colby Tresness, Mark Russinovich, Ricardo Bianchini. "[**Serverless in the Wild: Characterizing and Optimizing the Serverless Workload at a Large Cloud Provider**](https://www.microsoft.com/en-us/research/uploads/prod/2020/05/serverless-ATC20.pdf)", in Proceedings of the 2020 USENIX Annual Technical Conference (USENIX ATC 20). USENIX Association, Boston, MA, July 2020. 


Lastly, if you have any questions, comments, or concerns, or if you would like to share tools for working with the traces, please contact us at azurepublicdataset@service.microsoft.com 

### Downloading

You can download the dataset here: https://azurecloudpublicdataset2.z19.web.core.windows.net/azurepublicdatasetv2/azurefunctions_dataset2019/azurefunctions-dataset2019.tar.xz 

## Schema and Description
### Function Invocation Counts
 * 14 files, one file per 24-h period: `invocations_per_function_md.anon.d[01-14].csv`
#### Schema
|Field|Description  |
|--|--|
| HashOwner | unique id of the application owner <sup>1</sup> |
| HashApp | unique id for application name <sup>1</sup> |
| HashFunction | unique id for the function name within the app <sup>1</sup>|
|Trigger | trigger for the function<sup>2</sup>|
|1 .. 1440 | 1440 fields, with the number of invocations of the function per each minute of the 24h period in the file<sup>3</sup>

#### Notes
 1. All ids are hashed using HMAC-SHA256 with secret salts. Each column uses a different salt. These are consistent across the different types of files, so you can correlate onwers, apps, and functions here with those in the duration and memory data. Note that two apps with the same original name under different owners would be hashed to *different* values. Likewise, two functions with the same original name belonging to different apps would be hashed to different values. 
 2. Trigger indicates one of the trigger groups from the paper. Azure Functions has a large number of triggers, see [here](https://docs.microsoft.com/en-us/azure/azure-functions/functions-triggers-bindings) for details. Here, as in the paper, we group triggers of similar types into the 7 following groups:

    * **http** (HTTP)
    * **timer** (Timer) 
    * **event** (Event Hub, Event Grid)
    * **queue** (Service Bus, Queue Storage, RabbitMQ, Kafka, MQTT)
    * **storage** (Blob Storage, CosmosDB, Redis, File)
    * **orchestration** (Durable Functions: activities, orcherstration)
    * **others** (all other triggers)
     

3.  The number of invocations is recorded after the functions execute

### Function Execution Duration
14 files, one file per 24-h period: `function_durations_percentiles.anon.d[01-14].csv`
#### Schema

|Field|Description  |
|--|--|
| HashOwner | unique id of the application owner |
| HashApp | unique id for application name  |
| HashFunction | unique id for the function name within the app | 
|Average | Average execution time (ms) across all invocations of the 24-period <sup>4</sup>|  
|Count | Number of executions used in computing the average<sup>5</sup>|  
|Minimum | Minimum execution time for the 24-hour period<sup>6</sup>|  
|Maximum | Maximum execution time for the 24-hour period<sup>6</sup>|  
|percentile_Average_0| Weighted 0th-percentile of the execution time *average*<sup>7</sup> |  
|percentile_Average_1| Weighted 1st-percentile of the execution time *average*<sup>7</sup> |  
|percentile_Average_25 | Weighted 25th-percentile of the execution time *average*<sup>7</sup>|  
|percentile_Average_50 | Weighted 50th-percentile of the execution time *average*<sup>7</sup>|  
|percentile_Average_75 | Weighted 75th-percentile of the execution time *average*<sup>7</sup>|  
|percentile_Average_99 | Weighted 99th-percentile of the execution time *average*<sup>7</sup>|  
|percentile_Average_100 | Weighted 100th-percentile of the execution time *average*<sup>7</sup>|

#### Notes
4. Execution time is in milliseconds and **does not** include the cold start time
5. While the number here is very close to the sum of the invocations in the 
   invocations_per_minute files, sometimes it is different. These two numbers are taken from different logs, and in a few rare cases they may diverge (even by a lot). Use the number here only to operate on or reason about the values in this table (e.g., to compose averages across 24-hour periods).
6. Min and Max are the true minimum and maximum. There are a few cases in which these values were not recorded in this dataset, because of a field naming issue in a few versions of the Azure Functions runtime.
7. These require an explanation, as we could not log the duration of every invocation. Every 30 seconds, the framework records, for each function, the number of invocations *i*, the minimum, average, and maximum execution times over these *i* invocations. The percentiles in this table are not of the invocation times, but of their averages. Suppose there are two periods with averages 10 and 12 over, respectively, 5 and 3 invocations. The percentiles are computed on the "weighted" distribution (10,10,10,10,12,12,12). If the number of samples over each 30-second interval is small, these percentiles over the average will tend to the percentiles of the true distribution.

### Application Memory
12 files, one file per 24-h period (last 2 are missing): `app_memory_percentiles.anon.d[01..12].csv`
 
 #### Schema
|Field|Description  |
|--|--|
| HashOwner | unique id of the application owner |
| HashApp | unique id for application name  |
|SampleCount | Number of samples used for computing the average |  
|AverageAllocatedMb | Average allocated memory across all SampleCount measurements throughout this 24h period<sup>8</sup> |  
|AverageAllocatedMb_pct1 | 1st percentile of the average allocated memory <sup>9</sup>|  
|AverageAllocatedMb_pct5 | 5th percentile of the average allocated memory <sup>9</sup>|  
|AverageAllocatedMb_pct25 | 25th percentile of the average allocated memory <sup>9</sup>|  
|AverageAllocatedMb_pct50 | 50th percentile of the average allocated memory <sup>9</sup>|  
|AverageAllocatedMb_pct75 | 75th percentile of the average allocated memory <sup>9</sup>|  
|AverageAllocatedMb_pct95 | 95th percentile of the average allocated memory <sup>9</sup>|  
|AverageAllocatedMb_pct99 | 99th percentile of the average allocated memory <sup>9</sup>|  
|AverageAllocatedMb_pct100 | 100th percentile of the average allocated memory <sup>9</sup>|

#### Notes
 8. Average allocated memory for the application (committed memory in Windows parlance): the total amount of virtual memory the process has allocated, not necessarily resident in physical memory. The framework samples the application memory every 5 seconds. Then, every minute, these samples are averaged. The average reported here is the average of all the 5-second samples for the application over all executions during the 24-h period. 
 9.  Like in the durations table, these percentiles are of the average, not of the true allocation. Under normal circumstances, averages are computed over 12 samples (taken every 5 seconds and aggregated every minute), except with workers start or end in a minute. We then take the weighted percentiles of these averages. For this dataset, there was a problem when logging the 0th-percentile, as under some edge cases, the value was erroneously recorded as 0, and we had to omit this value.

 ## Validation

 This data is a small subset of the data used in the ATC paper above. To verify that it is a representative subset, we reproduced the characterization graph in the paper using the released trace subset in this [R Notebook](https://github.com/Azure/AzurePublicDataset/blob/master/analysis/AzureFunctionsDataset2019-Trace_Analysis.md).


