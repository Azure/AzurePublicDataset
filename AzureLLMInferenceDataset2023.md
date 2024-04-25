# Azure LLM inference trace 2023

## Introduction
This is a sample of the traces from multiple LLM inference services in Azure, collected on November 11<sup>th</sup> 2023. This dataset is the data described and analyzed in the ISCA 2024 paper 'Splitwise: Efficient generative LLM inference using phase splitting'.

The dataset comprises this description and a [Jupyter Notebook](https://github.com/Azure/AzurePublicDataset/blob/master/analysis/AzureLLMInferenceDataset2023.ipynb) with the plots in the ISCA paper.

## Using the data

### License
The data is made available and licensed under a [CC-BY Attribution License](https://github.com/Azure/AzurePublicDataset/blob/master/LICENSE). By downloading it or using them, you agree to the terms of this license.

### Attribution
If you use this data for a publication or project, please cite the accompanying paper:

> Pratyush Patel, Esha Choukse, Chaojie Zhang, Aashaka Shah, Íñigo Goiri, Saeed Maleki, Ricardo Bianchini. "[**Splitwise: Efficient generative LLM inference using phase splitting**](https://www.microsoft.com/en-us/research/publication/splitwise-efficient-generative-llm-inference-using-phase-splitting/)", in Proceedings of the International Symposium on Computer Architecture (ISCA 2024). ACM, Buenos Aires, Argentina, 2024. 

Lastly, if you have any questions, comments, or concerns, or if you would like to share tools for working with the traces, please contact us at azurepublicdataset@service.microsoft.com 

### Downloading
You can download the datasets here:
* [Code](data/AzureLLMInferenceTrace_code.csv)
* [Conversation](data/AzureLLMInferenceTrace_conv.csv)

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
This data is the sample data used in the ISCA paper mentioned above.
To verify the data, we reproduce the characterization graphs in the paper using the released trace in this [Jupyter Notebook](https://github.com/Azure/AzurePublicDataset/blob/master/analysis/AzureLLMInferenceDataset2023.ipynb).
