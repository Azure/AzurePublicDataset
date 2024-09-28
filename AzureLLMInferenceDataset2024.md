# Azure LLM inference trace 2024

## Introduction
This is a sample of the traces from multiple LLM inference services in Azure, collected on May 10<sup>th</sup>-19<sup>th</sup> 2024. This dataset is the data described and analyzed in the arxiv paper 'DynamoLLM: Designing LLM Inference Clusters for Performance and Energy Efficiency'.

## Using the data

### License
The data is made available and licensed under a [CC-BY Attribution License](https://github.com/Azure/AzurePublicDataset/blob/master/LICENSE). By downloading it or using them, you agree to the terms of this license.

### Attribution
If you use this data for a publication or project, please cite the accompanying paper:

> Jovan Stojkovic, Chaojie Zhang, Íñigo Goiri, Josep Torrellas, Esha Choukse. "[**DynamoLLM: Designing LLM Inference Clusters for Performance and Energy Efficiency**](https://arxiv.org/abs/2408.00741)", in arxiv. 

Lastly, if you have any questions, comments, or concerns, or if you would like to share tools for working with the traces, please contact us at azurepublicdataset@service.microsoft.com 

### Downloading
You can download the datasets here:
* [Code](https://azurepublicdatasettraces.blob.core.windows.net/azurellminfererencetrace/AzureLLMInferenceTrace_code_1week.csv)

### Schema
|Field|Description |
|--|--|
| TIMESTAMP | Invocation time |
| ContextTokens | Number of context tokens |
| GeneratedTokens | Number of generated  tokens |

### Prompt content
Due to customer privacy requirements (e.g., GDPR), we do not have visibility into the content of the prompts. We instead use the production traces to guide the input and output sizes, where we send the input prompt with the required number of tokens, 
and force the model to generate the corresponding number of output tokens for each request. Note that the text of the inputs prompts does not impact the performance metrics that we benchmark, since they depend only on the input and output sizes.

### Validation
This data is the sample data used in the arxiv paper mentioned above.
