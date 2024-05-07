# Azure Functions Blob Access Trace 2020
-- revision 1, 20210904

## Introduction
This is a sample of the blob accesses in [Microsoft's Azure Functions](https://docs.microsoft.com/en-us/azure/azure-functions/functions-overview), collected between November 23<sup>rd</sup> and December 6<sup>th</sup> 2020.
This dataset is the data described and analyzed in the SoCC 2021 paper 'Faa$T: A Transparent Auto-Scaling Cache for Serverless Applications'.

*Functions* in Azure Functions are grouped into *Applications*.
Included here is only data pertaining to a random sample of Azure Functions applications.
The sampling is done per application, so that if there is data about an application in the trace, then all of its functions are included.
The sampling rate is unspecified for confidentiality reasons.

The dataset comprises this description and a [Jupyter Notebook](https://github.com/Azure/AzurePublicDataset/blob/master/analysis/AzureFunctionsBlobDataset2020-Trace_Analysis.ipynb) with the plots in the SoCC paper.

## Using the Data

### License
The data is made available and licensed under a [CC-BY Attribution License](https://github.com/Azure/AzurePublicDataset/blob/master/LICENSE). By downloading it or using them, you agree to the terms of this license.

### Attribution
If you use this data for a publication or project, please cite the accompanying paper:

> Francisco Romero, Gohar Irfan Chaudhry, Íñigo Goiri, Pragna Gopa, Paul Batum, Neeraja J. Yadwadkar, Rodrigo Fonseca, Christos Kozyrakis, Ricardo Bianchini. "[**Faa$T: A Transparent Auto-Scaling Cache for Serverless Applications**](https://www.microsoft.com/en-us/research/uploads/prod/2021)", in Proceedings of the ACM Symposium on Cloud Computing 2021 (SoCC 21). ACM, Seattle, WA, 2021. 

Lastly, if you have any questions, comments, or concerns, or if you would like to share tools for working with the traces, please contact us at azurepublicdataset@service.microsoft.com 

### Downloading
You can download the dataset here: https://azurecloudpublicdataset2.z19.web.core.windows.net/azurepublicdatasetv2/azurefunctions_dataset2020/azurefunctions-accesses-2020.csv.bz2

## Schema and Description

#### Schema
|Field|Description  |
|--|--|
| Timestamp | Access time in milliseconds since 1970 |
| AnonRegion | Unique id for the region<sup>1</sup> |
| AnonUserId | Unique id for the user<sup>1</sup> |
| AnonAppName | Unique id for the application<sup>1</sup> |
| AnonFunctionInvocationId | Unique id for the invocation<sup>1</sup> |
| AnonBlobName | Unique id for the blob accessed<sup>1</sup> |
| BlobType | Type of the blob accessed |
| AnonBlobETag | Version of the blob accessed<sup>1</sup> |
| BlobBytes | Number of bytes of the blob |
| Read | If the access is a read |
| Write | If the access is a write |

#### Notes
 1. Ids are hashed using HMAC-SHA512 with secret salts and cropped.

#### Sample
|Timestamp|AnonRegion|AnonUserId|AnonAppName|AnonFunctionInvocationId|AnonBlobName|BlobType|AnonBlobETag|BlobBytes|Read|Write  |
|--|--|--|--|--|--|--|--|--|--|--|
| 1606092900138 | 6ex | 775920313 | 9gti3olh | 1565080819 | jfvf7k9kwiiq7gdx | BlockBlob/application/octet-stream | kq2su6bhi0 | 30.0 | True | False |
| 1606928903185 | 6ex | 1252244298 | 7c51my6n | 1191849141 | 1fjxqoqi2nc5njpg | BlockBlob/application/zip | ibd6a5v5pv | 1938488.0 | True | False |
| 1606355700058 | iic | 1495523193 | uf2u84b0 | 1302383289 | tp783etybrgxap8x | BlockBlob/ | 6mreka6qhr | 36.0 | False | True |
| 1606924856178 | iic | 705112778 | 1jgfqbn6 | 1869133266 | 80lssrlkciitddx9 | BlockBlob/ | if8foq3a81 | 2204780.0 | False | True |
| 1606658957997 | 6ex | 1252244298 | 15dp5na6 | 1468781831 | juijw2ldiogyem3c | BlockBlob/application/zip | 414fgngli4 | 359512.0 | True | False |
| ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |
| 1607270691764 | ayi | 1003538042 | 766ofcie | 1080821259 | sfocyrxcksjgri5t | BlockBlob/application/json | tanw2860j5 | 164.0 | True | False |
| 1607270691884 | ayi | 1003538042 | 766ofcie | 1530317863 | aat6cv8j2cofwj1a | BlockBlob/application/json | gf05emgb6t | 164.0 | True | False |
| 1607270692007 | ayi | 1003538042 | 766ofcie | 358892311 | u7p02pymm07pa7bg | BlockBlob/application/json | kl2uv31e7y | 164.0 | True | False |
| 1607270692134 | ayi | 1003538042 | 766ofcie | 1978924507 | 9qeai70lggcku3c5 | BlockBlob/application/json | 3xa1dkrq7m | 164.0 | True | False |
| 1607270692284 | ayi | 1003538042 | 766ofcie | 1142206120 | t8e88ksd6fiy2dx0 | BlockBlob/application/json | bp4ynk65sl | 164.0 | True | False |

## Validation
This data is the sample data used in the SoCC paper mentioned above.
To verify the data, we reproduce the characterization graphs in the paper using the released trace in this [Jupyter Notebook](https://github.com/Azure/AzurePublicDataset/blob/master/analysis/AzureFunctionsBlobDataset2020-Trace_Analysis.ipynb).
