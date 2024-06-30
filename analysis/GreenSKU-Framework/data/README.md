# Data sources

This directory contains the data sources used as inputs for the GreenSKU Carbon Model. The data sources are organized as follows:

- `carbon_data/`: This directory contains the open-sourced data sources used in the carbon model. The data sources include the carbon intensity of the electricity grid, the embodied emissions of server components, and the power consumption of server components. The data sources are provided in yaml format.

- `AFR_data/`: This directory contains the data sources used to calculate the Annual Failure Rate (AFR) of server components by the maintenance model. The data sources include the AFR of server components and the failure rate of server components. The data sources are provided in yaml format.

- `other_data/`: This directory contains other data sources that we use to calculate carbon saving such as cluster data, fan power data, and data center carbon intensity data.

Here we include a table of the carbon data values to be easier to read:

| Component | TDP (W) | Embodied Carbon (kg CO2e) |
| --- | --- | --- |
| CPU Genoa | 290 | 30.7 |
| CPU Bergamo | 400 | 28.3 |
| DDR4 DIMM (reused), per GB | 11.85 | 0 |
| DDR5 DIMM, per GB | 11.85 | 1.65 |
| SSD, per TB | 22.4 | 17.3 |
| NIC | 19 | 58.1 |
| CXL Controller | 5.8 | 2.5 |
| Server Fan (1U) | 75 | 1.6 |
| Server Fan (2U) | 112.5 | 1.6 |
| Misc. Server Components (1U) | 35 | 350 |
| Misc. Server Components (2U) | 35 | 375 |
| Misc. Rack Components | 500 | 500 |


## Data sourcing explanations

Here we describe the open-source data we provide. For each value, we provide a short descriptor of the public data source we use and how we arrived at the final value we provide.

### Component numbers
We first address each server and rack component that require TDP and embodied carbon values. We outline derived values for components used in the Baseline and GreenSKU-Full designs, which constitute all the components necessary to produce carbon estimations for our server SKU configurations.

#### CPU
We have two CPU types: AMD Genoa and Bergamo. For power, we use public reports of Genoa and Bergamo having TDPs of [290W](https://www.tomshardware.com/reviews/amd-4th-gen-epyc-genoa-9654-9554-and-9374f-review-96-cores-zen-4-and-5nm-disrupt-the-data-center) and [400W](https://www.phoronix.com/review/amd-epyc-9754-bergamo), respectively.

In terms of embodied emissions for Genoa, we use public die area estimations from teardowns to estimate the die area of both the Core Complex Dice (CCDs) chiplets, which each have 10 cores, and the I/O Die (IOD), of which there is one per CPU ([source](https://wccftech.com/amd-epyc-genoa-zen-4-cpu-pictured-in-all-its-glory-12-ccds-featuring-up-to-96-cores-massive-iod/)). Given our baseline server uses an 80-core Genoa, this means the CPU contains 8 CCDs. We use this to estimate the total area and feed that as input to [ACT](https://github.com/facebookresearch/ACT), using a 5nm node. This gives us a final estimation of 30.7 kg CO2e for the Genoa CPU's embodied carbon.

We perform a similar estimation and calculation for the Bergamo CPU, using die area estimations from teardowns for its 8 CCDs ([source](https://wccftech.com/amd-epyc-genoa-zen-4-cpu-pictured-in-all-its-glory-12-ccds-featuring-up-to-96-cores-massive-iod/)).
We use the same area for the IOD, as it's reported that Genoa and Bergamo share the same IOD ([source](https://www.xda-developers.com/amd-128-core-bergame-genoa-epyc-cpu/)).
We use ACT's 5nm and the estimated die area as inputs to ACT to estimate 28.3 kg CO2e for the Bergamo CPU's embodied carbon.

#### DRAM
We have two DRAM types, DDR4 and DDR5.
In terms of TDP, we use measured power consumption for DDR4 DIMMs, which reports about [2.96W per 8GB of DRAM](https://www.tomshardware.com/reviews/intel-core-i7-5960x-haswell-e-cpu,3918.html).
We scale this to generate TDP values for our 32GB DDR4 DIMM (i.e., 11.85W).
We use the same linear scaling for our 64 and 96GB DDR5 DIMMs, as [public data](https://exittechnologies.com/blog/memory/ddr4-vs-ddr5/) has shown DDR4 and DDR5 to have similar power consumption.

For DRAM's embodied carbon, we only use reused DDR4 DIMMs, which contribute zero embodied carbon.
For the DDR5 DIMMs, we use the reported kg CO2e-per-GB value used in the [Dell LCA](https://corporate.delltechnologies.com/content/dam/digitalassets/active/en/unauth/data-sheets/products/servers/lca_poweredge_r740.pdf) and ACT's DRAM carbon model, which provides a value of 1.65.

#### SSD
For the TDP of our SSDs, we use [data reported from a Seagate LCA report](https://www.seagate.com/esg/planet/product-sustainability/nytro-3530-sustainability-report/) for their 4TB enterprise SSD, which reports an average 5.6W per TB power consumption.
We scale this factor for each TB in our SSDs.

For embodied carbon, we use the same Seagate LCA report, which reports 17.3 kg CO2e per TB.
We use this to generate embodied carbon numbers for our SSD sizes.

#### NIC
We model our NIC after the data center SmartNICs designed in [previous work](https://www.usenix.org/conference/nsdi18/presentation/firestone), which measures an average power consumption of 19W for their design.

For embodied carbon, given the SmartNIC design largely consists of an FPGA, we take [published estimations](https://arxiv.org/abs/2311.12396) of the embodied carbon of standard FPGA devices, specifically the Stratix 10, which is estimated to have an embodied carbon of 58.1 kg CO2e.
We use this value as the embodied carbon of our NIC.

#### CXL Controller
There is relatively little published data on the power consumption of CXL controllers.
We make a rough estimation that a CXL controller consumes roughly as much power as a PCIe switch, which is [reported to consume 5.8W](https://www.broadcom.com/products/pcie-switches-retimers/pcie-switches/pex8732).

For embodied carbon, we use the [specification for the Microchip CXL controller](https://www.microchip.com/en-us/products/memory/smart-memory-controllers), which gives the size of the die package, which is 19 by 19 mm.
We use a [rough die to package ratio of 1:1](https://ieeexplore.ieee.org/document/7412319/) to estimate the area of the controller chip.
We then use the area estimate as an input to ACT, using a 28nm node due to controller components often being fabricated with larger nodes.
This results in an embodied carbon estimation of 2.5 kg CO2e.

#### Server Fan
For the servers' fans, we first use the [specifications](https://www.dell.com/en-us/shop/productdetailstxn/poweredge-r250) of standard 1U servers which contain 4 fans, relative to 6 fans for 2U designs.
Given this, we take [public data](https://www.techtarget.com/searchdatacenter/tip/Optimizing-server-energy-efficiency) of 1U designs requiring up to 75W of fan power.
We use this value for our 1U server designs, and then scale this power up by 50% (i.e., 4 to 6 fans) to account for the extra fans in a 2U design.

For the embodied carbon of the fans, we use the [Dell LCA](https://corporate.delltechnologies.com/content/dam/digitalassets/active/en/unauth/data-sheets/products/servers/lca_poweredge_r740.pdf), which uses a 2U design and reports a total embodied carbon for its fans, per server, as 1.6 kg CO2e.
We scale this value down by a third (6 to 4 fans for the 1U design) to estimate the embodied carbon for our 1U designs.

#### Misc. Server Components
For the miscellaneous components such as cabling, mechanicals, and the chassis, we provide a lump sum estimate of both the combined power and embodied carbon, which we estimate at 35W and 350/375 kg CO2e for a 1U and 2U server, respectively.

#### Misc. Rack Components
Similarly to the various server components, we provide a lump sum estimate for rack components (e.g., the rack itself, management boards, etc.), which results in 500W and 500 kg CO2e.

#### Data Center Building
We provide a lump sum estimate for the embodied carbon of the data center building, which we estimate at 9000000 kg CO2e (using an estimate of the [per-ft2 embodied carbon](https://carbonleadershipforum.org/how-microsoft-is-reducing-embodied-carbon/)).

### Misc. Parameters
Beyond component numbers that directly serve as inputs to the carbon accounting, there are other parameters and factors that we derive and provide that impact the resulting carbon emissions.
We detail them here.

#### Carbon Intensity
We use [public data](https://www.microsoft.com/en-us/corporate-responsibility/sustainability/report) reported by Azure of the portion of a data center region's energy that comes from renewable sources.
We take [published data](https://www.nrel.gov/docs/fy13osti/57187.pdf) on the average carbon intensity of renewable energy sources, which is 27.7 gCO2e per kWh, to determine the carbon intensity of such renewable energy.
We then match each data center region with the regions average annual carbon intensity as [reported by public grid data](https://www.electricitymaps.com/).
We then calculate the average carbon intensity of the data center as the renewable energy fraction multiplied by the renewable carbon intensity, added with the fraction of grid energy (non-renewable) multiplied by the grid carbon intensity.

We take some of Azure's largest regions and take the average calculated carbon intensity to produce carbon saving values (as in Table VIII).

#### Power Derating Curves
In order to properly account for the power of components as a function of their utilization, we use [prior work](https://dl.acm.org/doi/abs/10.1145/3185768.3185775)'s measured values for CPU power as a function of SPEC utilization rates.
Given this, we are able to discount the power of components by tracing the power utilization value for certain SPEC rates along the curve. 
To simplify, we use the same derating curve for all components that consume power (except for the miscellaneous server and rack components). 

We use reasonable estimates for SPEC rates seen in practice.
To determine how many servers we can fit into a rack given a rack's power budget, we discount the component power by using the power utilization at a conservative SPEC rate of 50%, to avoid power capping.
To discount the power used by the components that contribute to their operational emissions, we take a slightly smaller number, 40%.

#### Server Lifetime
We use 6 years (72 months) as the standard lifetime of our servers.
This is what is standard in production.

#### Data Center Lifetime
We use 20 years (240 months) as the standard lifetime of our data centers.
We find this is reasonable in production.

#### Voltage Regulator Overhead
A CPU's voltage regulator has a small power overhead in addition to the power consumed by the CPU.
We use [reported voltage regulator modules' efficiency](https://www.digikey.com/en/articles/understanding-the-advantages-and-disadvantages-of-linear-regulators) of 95%, adding an additional 5% power overhead to the CPU power. 

#### Fan vs. Server Power
Fan power will increase as a server design's power increases, as additional server power necessitates additional fan cooling.
We model this increase by taking [reported curves](https://www.servethehome.com/deep-dive-into-lowering-server-power-consumption-intel-inspur-hpe-dell-emc/) of fan power vs. server power and fitting a linear model, as the increase is linear.
The linear model provides us with a "fan slope" that estimates by how many watts does fan power increase for every watt that a server design increases. 
We use our baseline design, in both 1U and 2U configurations, to establish the baseline fan power for a server design.
For other designed SKUs, we take the increase or decrease in server power relative to the baseline and then apply the fan slope factor to the baseline fan power to determine the new fan power.

#### PSU Efficiency
A server's PSU is not 100% efficient in terms of power delivery, so we add an additional factor to the server's power (so excluding rack power) to account for the inefficiency.
We use [publicly reported PSU efficiency](https://help.corsair.com/hc/en-us/articles/14641912717453-PSU-Efficiency-Ratings-Explained) value of around 95%, adding an additional 5% overhead to server power.

#### Data Center PUE
The PUE of a data center is an additional overhead, on top of all IT power, that accounts for things like traditional HVAC cooling that is necessary for compute servers to function.
We use a PUE value of 1.12, which is what [Azure reports](https://azure.microsoft.com/en-us/blog/how-microsoft-measures-datacenter-water-and-energy-use-to-improve-azure-cloud-sustainability/) as the PUE of their newest generation of data centers.

#### Rack Power and Space Capacity
Data center racks have power and space capacities, which influence how many servers can fit in one rack.
We use [commonly reported](https://www.vertiv.com/en-emea/about/news-and-insights/articles/educational-articles/server-rack-sizes-matter-get-these-3-critical-rack-server-dimensions-right/) space capacity for a normal data center rack of having 42U of space.
For power constraints, we use [reported power capacities](https://www.sdxcentral.com/articles/analysis/data-center-rack-density-how-high-can-it-go/2023/09/), which is used by hyperscalers like Azure, of 15kW racks.

#### Rack Power Utilization
[Recent work](https://www.microsoft.com/en-us/research/publication/smartoclock-workload-and-risk-aware-overclocking-in-the-cloud/) has shown that the power utilization of racks falls well below the power that they are allocated, even with derating.
We use an additional power discounting factor of 0.66, which [is shown](https://www.microsoft.com/en-us/research/publication/smartoclock-workload-and-risk-aware-overclocking-in-the-cloud/) to be the median power utilization at rack scale within Azure clusters.

#### Data Center Power and Space Capacity
We use rough estimates from Azure that data centers can have a space capacity of about 2500 racks and a power capacity of about 50MW.

#### Growth Buffer Overhead
For the growth buffer overhead, while we can't disclose the exact calculations used in Azure, we provide an average overhead estimation of 10%, meaning that an additional 10% of cores are needed to service the growth buffer.
We account for this overhead by taking the total number of cores in a cluster (i.e., the number of servers in the cluster multiplied by the number of cores per server), and add enough additional baseline servers to increase the cluster's core count by 10%. 