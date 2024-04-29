# GreenSKU Carbon Model

[![DOI](https://zenodo.org/badge/779488355.svg)](https://zenodo.org/doi/10.5281/zenodo.10896254)

This repository contains a public version of the GreenSKU Carbon Model, a tool for estimating the carbon emissions of a compute server Stock Keeping Unit (SKU) over its lifetime. This carbon model is part of the GreenSKU framework described in the ISCA 2024 paper 'Designing Cloud Servers for Lower Carbon'.

# Overview

The source code and data of the GreenSKU model is contained in the [GreenSKU-Framework subfolder](analysis/GreenSKU-Framework). Subsequent pathnames are relative to this folder.

The main model logic is implemented in `src/carbon_model.py`. The model is used to estimate the carbon emissions of a server SKU over its lifetime, given server design inputs which are defined based on server configuration files. Such configuration files that are used in the paper are located in the `server_configs/` directory. The input data used to calculate the carbon emissions, such as per-component power and embodied emissions, are located in the `data/` directory. We provide open-sourced estimations of the required data for each component in the `data/carbon_data` directory; however, this data can be replaced with more accurate/specific data if available. For more information, see the paper.

For more detailed information on the model, see the [README](analysis/GreenSKU-Framework/src/README.md) in the `src` directory. For more detailed information on the server configuration files, see the [README](analysis/GreenSKU-Framework/server_configs/README.md) in the `server_configs` directory.

The rest of this README provides instructions on how to set up the environment to run the model, and how to reproduce the figures in the paper.

## Getting Started Instructions

In this section, we describe how to set up the environment. 

### Requirements

The carbon model is implemented as a Python package, and can thus run on any machine with Python installed. The model has been tested to run on Python 3.9. We strongly recommend running the model scripts in a virtual environment. We recommend using an Anaconda installation (see [Miniconda installation here](https://docs.anaconda.com/free/miniconda/#quick-command-line-install)) to create a virtual environment. (Note: This requires ~400MB of disk space). Make sure [Git is installed](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) on your machine.

Once Anaconda is installed, to set up a virtual environment using Anaconda, run the following command in a bash terminal:

```
conda create --name carbon_model python=3.9
```

where `carbon_model` is the name of the virtual environment. To activate the virtual environment, run the following command:

```
conda activate carbon_model
```
You can re-activate the virtual environment by running the same command. (And you can deactivate the virtual environment by running `conda deactivate` - however please run all artifact commands in the virtual environment).

Once the virtual environment is activated, install the required packages by running the following command (only needs to be performed once for the virtual environment):

```
git clone https://github.com/Azure/AzurePublicDataset.git
cd analysis\GreenSKU-Framework
pip install -r requirements.txt
conda install jupyterlab
```


## Setting Up the Notebook Environment

Jupyter notebooks are located in the `notebooks` directory. Only one notebook is provided/necessary for evaluation. You can run the notebook in your preferred Jupyter environment (VSCode, Jupyter Notebook, Jupyter Lab, etc.). We provide instructions using Jupyter Lab (which is included in the `requirements.txt` file). We also provide instructions for running the notebook both on a local machine ([Local Setup](#local-setup)) and remote machine accessed through ssh ([Remote Setup](#remote-setup)).

### Local Setup
(Skip this section if you are running the notebook remotely).
To run the notebook locally, first navigate to the repository directory in your terminal and activate the virtual environment. Then, run the following command:

```
jupyter lab
```
which will automatically open a Jupyter Lab interface in your browser. From there, you can navigate to the `notebooks` directory and open the notebook. (See the next [section](#running-the-notebooks--reproducing-results) for more details on running and reproducing results). If for some reason the Jupyter Lab interface does not open automatically, you can copy and paste the URL provided in the terminal output into your browser.


### Remote Setup
(Skip this section if you are running the notebook locally).
If you are running the notebook on a remote server, you will need to set up port forwarding to access the Jupyter Lab interface. To do this step, instead of running `jupyter lab`, run the following command in a terminal on your remote machine:

```
jupyter lab --no-browser --port=8888
```

Then, run the following command on your local machine:

```
ssh -N -f -L localhost:8888:localhost:8888 username@remote_host
```
where `username` is your username on the remote server and `remote_host` is the address of the remote server. The command should immediately return with no output. Then, navigate on your local machine within a browser to the URL provided by the terminal output of the `jupyter lab` command on the remote machine. Specifically, there should be an output to the terminal towards the bottom on the remote machine that looks like:

```
    To access the server, open this file in a browser:
        file:///path/to/jupyter/runtime/jpserver-<some_number>-open.html
    Or copy and paste one of these URLs:
        http://localhost:8888/lab?token=<some_token>
```
Use the second URL in your local browser specified after "Or copy and paste one of these URLs" to access the Jupyter Lab interface.

## Running the Notebook + Reproducing Results

Once the above setup is performed, relevant results and figures can be reproduced in the [`carbon_savings.ipynb`](analysis/GreenSKU-Framework/notebooks/carbon_savings.ipynb) notebook located in the `notebooks/` directory.

Here is a table with figures/results to reproduce and the expected run time to produce each one:

| Result in paper to reproduce | Run time | Output file(s) | 
| --- | --- | --- |
| [Last three columns of Table V](analysis/GreenSKU-Framework/figures/paper_figures_original/Table_V.csv) | < 1 minute | [`figures/generated_figures/Table_V.csv`](analysis/GreenSKU-Framework/figures/generated_figures/Table_V.csv) |
| Appendix A-D claim: "We re-calculate the average cluster-level savings to find an average of **15%**..." | < 1 minute | [`figures/generated_figures/cluster_savings.txt`](analysis/GreenSKU-Framework/figures/generated_figures/cluster_savings.txt) (and `carbon_savings.ipynb` cell print output) |
| Appendix A-D claim: "... leading to an overall data center-level savings of **8\%**." | < 1 minute | [`figures/generated_figures/dc_savings.txt`](analysis/GreenSKU-Framework/figures/generated_figures/dc_savings.txt) (and `carbon_savings.ipynb` cell print output) |
| [Figure 12](analysis/GreenSKU-Framework/figures/paper_figures_original/Figure_12.png) | 1 minute | [`figures/generated_figures/Figure_12.png`](analysis/GreenSKU-Framework/figures/generated_figures/Table_V.csv) |

Note: First column links to copies of the Table and Figure from the paper. The links in last column will work only when figures are generated from the notebook.
