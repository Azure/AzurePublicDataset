# Carbon Model Source Code

The source code for the carbon model is located here in the `src` directory. The model is implemented as a Python package, and can be run on any machine with Python installed. We outline the structure of the source code below - explaining each Python module and its purpose.

## `carbon_model`
The main model logic is implemented in `carbon_model.py`, which contains a Class definition `ServerCarbon` that can be instantiated with a certain server configuration and source data in order to model the carbon emissions of a server SKU over its lifetime.

The model aggregates components hierarchically based on three levels, in order of lower to higher in the data center hierarchy: (1) the individual server level, (2) the rack level, and (3) cluster/data-center level.

## `derate_curve`

The `derate_curve.py` module contains the logic for calculating the derate curve for the power of a server component. The derate curve is a function that maps the utilization ([SPECrate](https://www.spec.org/cpu2017/)) of a server component to its power consumption relative to its peak power consumption, aka its Thermal Design Power ([TDP](https://en.wikipedia.org/wiki/Thermal_design_power)).

## `helpers`

The `helpers.py` module contains helper functions that are used in the main model logic. These functions are used to load data, calculate carbon intensity, and perform other tasks.

## `maintenance_model`

The `maintenance_model.py` module contains the logic for modeling the maintenance overhead of a server SKU. We specifically calculate the Annualized Failure Rate ([AFR](https://en.wikipedia.org/wiki/Annualized_failure_rate)) of a server SKU based on its constituent components' AFRs. This value provides information on how many additional servers (and thus how much additional carbon) are required to maintain a cluster of server SKUs over its lifetime.
