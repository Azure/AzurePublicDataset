# Azure Trace for Packing 2020
-- revision 1, 20201105

## Introduction
This dataset represents part of the workload on Microsoft's Azure Compute and is specifically designed to evaluate packing algorithms. The packing algorithm used by Azure for Virtual Machine (VM) allocation is discussed in the OSDI 2020 paper 'Protean: VM Allocation Service at Scale'. 

A VM request is associated with a predefined VM type, which defines the quantity of resources required (CPU/MEM/SSD). A single VM type can be used on different hardware generations, and a single hardware generation can support multiple VM types. In our dataset the VM type resources are measured in fractional machine units. For example, a VM type that requires 0.5 'units' of CPU indicates that it would take half the CPU resources for that machine generation.

We have included the lifetimes of VMs when known. The VMs still alive at the time of data collection have their end time set to NULL.  VM requests have priority (e.g., low/high). Low-priority VMs can be evicted before they complete their purpose, in which case we report the actual lifetime - since the intended lifetime is unknown.  Thus, the low-priority VM lifetime is dependent on allocation choices; this is not the case for high-priority VMs.
 
## Using the Data

### License
The data is made available and licensed under a [CC-BY Attribution License](https://github.com/Azure/AzurePublicDataset/blob/master/LICENSE). By downloading it or using them, you agree to the terms of this license.

### Attribution
If you use this data for a publication or project, please cite the accompanying paper:

> Ori Hadary, Luke Marshall, Ishai Menache, Abhisek Pan, David Dion, Esaias Greeff, Star Dorminey, Shailesh Joshi, Yang Chen, Mark Russinovich and Thomas Moscibroda. "[**Protean: VM Allocation Service at Scale**](https://www.microsoft.com/en-us/research/publication/protean-vm-allocation-service-at-scale/)", in Proceedings of the 14th USENIX Symposium on Operating Systems Design and Implementation (OSDI 2020). USENIX Association, November 2020. 


Lastly, if you have any questions, comments, or concerns, or if you would like to share tools for working with the traces, please contact us at protean_azure@microsoft.com 

### Downloading

You can download the dataset here: https://azurecloudpublicdataset2.z19.web.core.windows.net/azurepublicdatasetv2/azurevmallocation_dataset2020/AzurePackingTraceV1.zip 

## Schema and Description

The data is stored in a [sqlite](https://www.sqlite.org/index.html) database format.  It is a compact and portable binary format with extensive open-source support. Currently the dataset contains a single zone, in the future this may be extended to include others.  Each file is considered independent of the others, that is, the IDs will be reused and have no correlation between files.

### VM Requests
#### Schema
|Field|Description  |
|--|--|
| vmId | unique id of the vm request<sup>1</sup> |
| tenantId | unique id for the owner of a group of requests<sup>1</sup> |
| vmTypeId | requested VM type<sup>1</sup>|
| priority | priority of the VM request<sup>2</sup>|
| starttime | the time (in fractional days) when the VM request was created<sup>3</sup>
| endtime | the time (in fractional days) when the VM left the system<sup>3</sup>

#### Notes
 1. All ids are anonymized. These are consistent only within a single sqlite file. 
 2. High-priority (0) and low-priority (1). Low-priority work may be evicted early.
 3. The dataset was collected over a 14-day period and includes VMs alive at the beginning of collection (denoted with a negative start time). It was collected from historical data, and so the endtime extends past the 14 days - it is capped at 90 days to anonymize time. The endtime will be NULL if VM was still alive longer after this cap. Time is measured in fractional days, for example, the time 2.5 indicates two and a half days after time of collection.

### VM Types
#### Schema

|Field|Description  |
|--|--|
| id | unique row id |
| vmTypeId | unique id for VM type name, can be used on different machines |
| machineId | unique id for machine | 
| core | requested CPU resource allocation for this VM type on this machine<sup>4</sup>|  
| memory | requested memory resource allocation for this VM type on this machine<sup>4</sup>|  
| hdd | requested hard drive resource allocation for this VM type on this machine<sup>4</sup>|  
| ssd | requested solid state drive resource allocation for this VM type on this machine<sup>4</sup>|  
| nic | requested network bandwidth allocation for this VM type on this machine<sup>4</sup>|  

#### Notes
4. Measured in fractional machine usage.

