# Azure LMM inference trace 2025

## Introduction
This is a sample of the traces from a multimodal model inference cluster in Azure, collected on Oct. 15<sup>th</sup>-22<sup>th</sup> 2024. This dataset is the data described and analyzed in the SoCC 2025 paper 'ModServe: Modality- and Stage-Aware Resource Disaggregation for Scalable Multimodal Model Serving'.

The dataset comprises this description and a [Jupyter Notebook](analysis/AzureLMMInferenceDataset2025.ipynb) with the plots in the SoCC paper.

## Using the data

### License

The data is made available and licensed under a [CC-BY Attribution License](https://github.com/Azure/AzurePublicDataset/blob/master/LICENSE). By downloading it or using them, you agree to the terms of this license.

### Attribution

If you use this data for a publication or project, please cite the accompanying paper:

```
@inproceedings{qlm2024patke,
  author = {Qiu, Haoran and Biswas, Anish and Zhao, Zihan and Mohan, Jayashree and Khare, Alind and Choukse, Esha and Goiri, {\'I}{\~n}igo and Zhang, Zeyu and Shen, Haiying and Bansal, Chetan and Ramjee, Ramachandran and Fonseca, Rodrigo},
  title = {ModServe: Modality- and Stage-Aware Resource Disaggregation for Scalable Multimodal Model Serving},
  year = {2025},
  publisher = {Association for Computing Machinery},
  address = {New York, NY, USA},
  booktitle = {Proceedings of the 2025 ACM Symposium on Cloud Computing (SoCC 2025)},
  location = {Virtual},
}
```

Lastly, if you have any questions, comments, or concerns, or if you would like to share tools for working with the traces, please contact us at azurepublicdataset@service.microsoft.com

### Unzipping

Dataset is located at: `data/AzureLMMInferenceTrace_multimodal.csv.gz`

You can unzip the file with `gunzip -k AzureLMMInferenceTrace_multimodal.csv.gz`.

### Schema

|Field|Description |
|--|--|
| TIMESTAMP | Request invocation time |
| NumImages | Number of images in the request |
| ContextTokens | Number of context tokens |
| GeneratedTokens | Number of generated tokens |

### Prompt content

Due to customer privacy requirements (e.g., GDPR), we do not have visibility into the content of the prompts.
We instead use the production traces to guide the input and output sizes, where we send the input prompt with the required number of tokens and images, and force the model to generate the corresponding number of output tokens for each request.
Note that the text of the inputs prompts does not impact the performance metrics that we benchmark, since they depend only on the input and output sizes.
For image content, we use ShareGPT-4o image dataset.

### Validation

This data is the sample data used in the SoCC paper mentioned above.
