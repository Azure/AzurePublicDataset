# Azure Functions Invocation Trace 2021
-- revision 1, 2021-11-30

## Introduction
This is a trace of function invocations  in [Microsoft's Azure Functions](https://docs.microsoft.com/en-us/azure/azure-functions/functions-overview) for two weeks starting on 2021-01-31. This trace has been used in the SOSP 2021 paper [**Faster and Cheaper Serverless Computing on Harvested Resources**](https://www.microsoft.com/en-us/research/publication/faster-and-cheaper-serverless-computing-on-harvested-resources/).


## Using the Data

### License
The data is made available and licensed under a [CC-BY Attribution License](https://github.com/Azure/AzurePublicDataset/blob/master/LICENSE). By downloading it or using them, you agree to the terms of this license.

### Attribution
If you use this data for a publication or project, please cite the accompanying paper:

> Yanqi Zhang, Íñigo Goiri, Gohar Irfan Chaudhry, Rodrigo Fonseca, Sameh Elnikety, Christina Delimitrou,  Ricardo Bianchini. "[**Faster and Cheaper Serverless Computing on Harvested Resources**](https://www.microsoft.com/en-us/research/publication/faster-and-cheaper-serverless-computing-on-harvested-resources/)", in Proceedings of the ACM International Symposium on Operating Systems Principles (SOSP), October 2021.

If you have any questions, comments, or concerns, or if you would like to share tools for working with the traces, please contact us at azurepublicdataset@service.microsoft.com 

### Downloading
You can download the dataset here:  [**AzureFunctionsInvocationTraceForTwoWeeksJan2021.rar**](https://github.com/Azure/AzurePublicDataset/raw/master/data/AzureFunctionsInvocationTraceForTwoWeeksJan2021.rar).

## Schema and Description

### Schema

- app: application id (encrypted)
- func: function id (encrypted), and unique only within an application 
- end_timestamp: function invocation end timestamp (in seconds)
- duration: duration of function invocation (in seconds)

### Remarks 

In Azure Functions, the unit of deployment is called an application, and an application has one or more functions. For example, an application could be a binary file with one or more entry points.  A function invocation specifies both the app id and the func id withen the app. 

Invocation timestamps have been modified from those in the actual production trace.

#### Sample

|app|func|end_timestamp|duration|
|--|--|--|--|
|734272c01926d19690e5ec308bab64ef97950b75b1c7582283e0783fce1751d8|313c03f53a0d31f70aec25f62efb33e7dd779725ca4af579018452d1204beaad|5160.142570018768|0.134|
|17c37a0fdd5d1932b755c0e6447137bc08fd524f455e14fdac414f584de08dc5|c9f8e30e36d1aef62c10b3cfca6e289a93848a148d876dd514753040314f4817|5161.280997037888|0.013|
|7fa05b607ae861b85ec53cea12d3efaed8be0f9a92f5d6e8067244161d491e96|9bc86d6cd1ee254aaa313492f0fd88be8bd7b92d50d4237ff52d7685440c0906|5241.567729949951|42.356|
|c8c43e1a911f29e5506460a2fbef61ff39723d672f3b3b67d12d4c236c6872f7|653cdbc309bc359f3289d3b4df21c4a8e478d22946b35cbfdab05377dcacd3e0|5253.883348941803|42.372|
|db6be4a997f386b37c6246aaeecf81ab81562db84cf4c0d44907d9df2d0ab9fc|9040b71f8a0325ba418c85bcefa3b19c02c781bed6284af487d3f111f369534a|5219.518173933029|0.108|
|f7bfe5bc8d2a37a5c15986fbfc2c477a746e866adcb9663f9df7535b61c3eb9b|34f4775366e51728635af48df1a96d332cf1565eee069a0030f12966ae760274|5220.1072909832|0.093|
