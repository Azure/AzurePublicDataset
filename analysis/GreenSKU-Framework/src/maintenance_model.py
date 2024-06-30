from typing import Dict, Any
from helpers import *
from carbon_model import ServerCarbon

class ServerMaintenance:
    def __init__(self, config_file: str, data_source: str, carbon_data_dir: str='../data/carbon_data/', overwrite_params: Dict[str, Any]={}):
        self.maintenance_data = read_yaml(data_source)
        self.server_carbon = ServerCarbon(config_file, carbon_data_dir, print_out=False, overwrite_params=overwrite_params)
        self.num_components = self.server_carbon.get_num_components()

    def get_component_num(self, component: str, reuse: bool) -> int:
        if component == "DRAM":
            if reuse:
                return self.num_components["cxl"] if "cxl" in self.num_components else 0
            return self.num_components["memory"]
        elif component == "CPU":
            if reuse:
                raise ValueError("CPU reuse not implemented")
            return self.num_components["CPU"]
        elif component == "SSD":
            if reuse:
                return self.num_components["ssd_reuse"] if "ssd_reuse" in self.num_components else 0
            return self.num_components["ssd"]
        elif component == "NIC":
            if reuse:
                raise ValueError("NIC reuse not implemented")
            return self.num_components["nic"]
        elif component == "Rest":
            return 1
        else:
            raise ValueError(f"Component {component} not found")
        

    def get_AFRs(self) -> float:
        '''
        Returns the AFR for the server configuration
        '''
        total_afr = 0
        for component in self.maintenance_data:
            fip_rate = 1
            if 'FIP_rate' in self.maintenance_data[component]:
                fip_rate = 1 - self.maintenance_data[component]['FIP_rate']
            if 'AFR' in self.maintenance_data[component]:
                component_number = self.get_component_num(component, False)
                total_afr += self.maintenance_data[component]['AFR'] * component_number * fip_rate
            if 'reuse_AFR' in self.maintenance_data[component]:
                component_number = self.get_component_num(component, True)
                total_afr += self.maintenance_data[component]['reuse_AFR'] * component_number * fip_rate
        return total_afr / 100