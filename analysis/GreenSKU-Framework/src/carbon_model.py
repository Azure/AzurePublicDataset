from typing import Dict, Any, List, Callable, Union, Tuple
from derate_curve import fit_cubic
from math import ceil, floor
import pandas as pd
from helpers import *

def get_opex(power: float, spec: int=100, derate_curve: Callable=None, number: int=1, 
                  opex_rate: float=205.0, monthly_lifetime: int=72, 
                  factor: float=1.0) -> float:
    """Calculate the monthly opex cost of something that consumes power.

    Args:
        power: The power consumption of the server in Watts.
        spec: The SPECint rating of the server.
        derates: A list of derating factors for the server.
        opex_rate: The rate (per kW-Month) that opex is being generated.
        monthly_lifetime: The monthly lifetime of the server.

    Returns:
        The monthly opex cost of the server.
    """
    if not derate_curve:
        derate_curve = lambda x: 1
    # Calculate the monthly opex cost of the server
    return (power/1000) * opex_rate * derate_curve(spec) * monthly_lifetime * number * factor

def get_opex_from_dict(component: Dict[str, Any], spec: int=100, derate_curve: Callable=None,
                            opex_rate: float=205.0, monthly_lifetime: int=72, factor: float=1.0) -> float:
    """Calculate the monthly opex cost of something that consumes power.

    Args:
        component: A dictionary containing the component's power consumption, SPECint rating, and derating curve.
        opex_rate: The rate (per kW-Month) that opex is being generated.
        monthly_lifetime: The monthly lifetime of the server.

    Returns:
        The monthly opex cost of the server.
    """
    # if no number is specified, assume there is only one
    if 'number' not in component:
        component['number'] = 1
    return get_opex(component['power'], 
                         spec, 
                         derate_curve, 
                         component['number'], 
                         opex_rate, 
                         monthly_lifetime,
                         factor=factor)

def get_dict_opex(components: Dict[str, Any], spec: int=100, derate_curve: Callable=None,
                  opex_rate: float=205.0, monthly_lifetime: int=72, factor: float=1.0) -> float:
    """Calculate the monthly opex cost of a component.

    Args:
        components: A dictionary containing the components' power consumption, SPECint rating, and derating curve.
        opex_rate: The rate (per kW-Month) that opex is being generated.
        monthly_lifetime: The monthly lifetime of the server.

    Returns:
        The monthly opex cost of the server.
    """
    total_opex = 0
    for key, component in components.items():
        total_opex += get_opex_from_dict(component, 
                                              spec, 
                                              derate_curve, 
                                              opex_rate, 
                                              monthly_lifetime,
                                              factor=factor)
    return total_opex

def get_power_from_dict(component: Dict[str, Any], derate_curve: Callable, 
                        spec: int=100, factor: float=1.0) -> float:
    """Calculate the power consumption of a component.

    Args:
        components: A dictionary containing the components' power consumption, SPECint rating, and derating curve.

    Returns:
        The power consumption of the server.
    """
    if 'number' not in component:
        component['number'] = 1
    if not derate_curve:
        derate_curve = lambda x: 1
    return component['power'] * component['number'] * derate_curve(spec) * factor

def get_dict_power(components: Dict[str, Any], derate_curve: Callable=None, 
                   spec: int=100, factor: float=1.0, key_factors: Dict[str, float]={}) -> float:
    """Calculate the total power consumption of a component.

    Args:
        components: A dictionary containing the components' power consumption and number.

    Returns:
        The total power consumption of the server.
    """
    total_power = 0
    for key, component in components.items():
        curr_factor = factor
        if 'number' not in component:
            component['number'] = 1
        if key in key_factors:
            curr_factor *= key_factors[key]
        total_power += get_power_from_dict(component, 
                                           derate_curve, 
                                           spec,
                                           factor=curr_factor)
    return total_power

def get_capex_from_dict(component: Dict[str, Any], cost='carbon', factor: float=1.0, 
                        server_lifetime: float=-1) -> float:
    lifetime_factor = 1.0
    if 'number' not in component:
        component['number'] = 1.0
    if 'lifetime' in component and server_lifetime > 0:
        lifetime_factor = server_lifetime / component['lifetime']
    return component[cost] * component['number'] * lifetime_factor * factor

def get_dict_capex(components: Dict[str, Any], cost='carbon', factor: float=1.0, 
                   server_lifetime: float=-1) -> float:
    """Calculate the capex cost of a component.

    Args:
        components: A dictionary containing the components' cost and number.

    Returns:
        The capex cost of the server.
    """
    total_capex = 0
    for key, component in components.items():
        total_capex += get_capex_from_dict(component,
                                           cost=cost,
                                           factor=factor,
                                           server_lifetime=server_lifetime)
    return total_capex

def get_list_capex(components: List[Dict[str, Any]]) -> float:
    """Calculate the capex cost of a list of components.

    Args:
        components: A list of components.

    Returns:
        The capex cost of the server.
    """
    # Calculate the capex cost of the server
    total_capex = 0
    for component in components:
        # if no number is specified, assume there is only one
        if 'number' not in component:
            component['number'] = 1
        total_capex += component['cost'] * component['number']
    return total_capex

def index_cpu_data(vendor: str, cpu_type: str, core_count: int, data_source: str="data_sources") -> Dict[str, Any]:
    """Index the CPU data for a given vendor, CPU type, and core count.
    
    Args:
        vendor: The CPU vendor.
        cpu_type: The CPU type.
        core_count: The number of cores in the CPU.
        data_source: The directory containing the CPU data.

    Returns:
        A dictionary containing the CPU data.
    """
    cpu_data = read_yaml(join_path(data_source, 'CPU.yaml'))
    
    data = None
    spec_derates = None
    for cpu_vendor in cpu_data:
        if cpu_vendor['vendor'] != vendor:
            continue
        spec_derates = cpu_vendor['spec_derates']
        for cpu_type_data in cpu_vendor['types']:
            if cpu_type_data['type'] != cpu_type:
                continue
            for core_count_data in cpu_type_data['core_counts']:
                if core_count_data['count'] != core_count:
                    continue
                data = core_count_data
                data['spec_derates'] = spec_derates
                if 'carbon' not in data:
                    data['carbon'] = 0.0
                if 'threads' not in data:
                    data['threads'] = 2
                return data
    raise ValueError(f'Could not find CPU data for {vendor} {cpu_type} with {core_count} cores.')

def index_memory_data(memory_type: str, memory_frequency: Union[int, str],  memory_size: int,
                      data_source: str="data_sources") -> Dict[str, Any]:
    """Index the memory data for a given memory type, frequency, and size.

    Args:
        memory_type: The memory type.
        memory_frequency: The memory frequency.
        memory_size: The memory size.
        data_source: The directory containing the memory data.

    Returns:
        A dictionary containing the memory data.
    """
    memory_data = read_yaml(join_path(data_source, 'DRAM.yaml'))
    if isinstance(memory_frequency, int):
        memory_frequency = str(memory_frequency)
        memory_frequency = memory_frequency + 'MHz'
    data = None
    if memory_type in memory_data:
        memory_type_data = memory_data[memory_type]
        for freq_item in memory_type_data['frequencies']:
            if freq_item['frequency'] != memory_frequency:
                continue
            sizes = freq_item['sizes']
            for size_item in sizes:
                if size_item['size'] != memory_size:
                    continue
                data = size_item
                data['spec_derates'] = memory_type_data['spec_derates']
                if 'carbon' not in data:
                    data['carbon'] = 0.0
                return data
    raise ValueError(f'Memory data not found for {memory_type} {memory_frequency} {memory_size}')

def index_ssd_data(ssd_type: str, ssd_size: int, data_source: str="data_sources", reuse: bool=False) -> Dict[str, Any]:
    yaml_file = 'SSD.yaml'
    if reuse:
        yaml_file = 'SSD_reuse.yaml'
    ssd_data = read_yaml(join_path(data_source, yaml_file))
    data = None
    for ssd_type_data in ssd_data:
        if ssd_type_data['type'] != ssd_type:
            continue
        for ssd_size_data in ssd_type_data['sizes']:
            if ssd_size_data['size'] != ssd_size:
                continue
            data = ssd_size_data
            # add any dict keys from ssd_type_data - except 'sizes'
            for key in ssd_type_data:
                if key != 'sizes':
                    data[key] = ssd_type_data[key]
            if 'carbon' not in data:
                data['carbon'] = 0.0
            return data
    raise ValueError(f'SSD data not found for {ssd_type} {ssd_size}')

def index_nic_data(nic_bandwidth: str, data_source: str="data_sources") -> Dict[str, Any]:
    nic_data = read_yaml(join_path(data_source, 'NIC.yaml'))
    data = None
    for nic_bandwidth_data in nic_data['bandwidths']:
        if nic_bandwidth_data['bandwidth'] != nic_bandwidth:
            continue
        data = nic_bandwidth_data
        data['spec_derates'] = nic_data['spec_derates']
        if 'carbon' not in data:
            data['carbon'] = 0.0
        return data
    raise ValueError(f'NIC data not found for {nic_bandwidth}')

def index_dc_data(dc_type: str, data_source: str="data_sources") -> Dict[str, Any]:
    dc_data = read_yaml(join_path(data_source, 'data_center.yaml'))
    data = None
    for dc_type_data in dc_data:
        if dc_type_data['type'] != dc_type:
            continue
        data = dc_type_data['items']
        config_data = {key: dc_type_data[key] for key in dc_type_data if key != 'items'}
        return data, config_data
    raise ValueError(f'Data center data not found for {dc_type}')

def index_rack_data(rack_type: str, data_source: str="data_sources") -> Dict[str, Any]:
    rack_data = read_yaml(join_path(data_source, 'rack.yaml'))
    data = None
    for rack_type_data in rack_data:
        if rack_type_data['type'] != rack_type:
            continue
        data = rack_type_data['items']
        return data
    raise ValueError(f'Rack data not found for {rack_type}')

def index_server_data(server_type: str, data_source: str="data_sources") -> Dict[str, Any]:
    server_data = read_yaml(join_path(data_source, 'server.yaml'))
    data = None
    for server_type_data in server_data:
        if server_type_data['type'] != server_type:
            continue
        data = server_type_data['items']
        return data
    raise ValueError(f'Server data not found for {server_type}')

def index_cxl_controller_data(cxl_controller_type: str, data_source: str="data_sources") -> Dict[str, Any]:
    cxl_controller_data = read_yaml(join_path(data_source, 'CXL_controller.yaml'))
    data = None
    if cxl_controller_type in cxl_controller_data['types']:
        data = cxl_controller_data['types'][cxl_controller_type]
        data['spec_derates'] = cxl_controller_data['spec_derates']
        if 'carbon' not in data:
            data['carbon'] = 0.0
        return data

    raise ValueError(f'CXL controller data not found for {cxl_controller_type}')

def convert_units(data: Dict[str, Any]) -> Dict[str, Any]:
    for key in data:
        if not isinstance(data[key], str):
            continue
        if key == 'power':
            data[key] = strip_power(data[key])
        elif key == 'size':
            if data[key].endswith('GB'):
                data[key] = float(data[key].replace('GB', ''))
            elif data[key].endswith('TB'):
                data[key] = float(data[key].replace('TB', ''))*1000
    return data

def strip_power(s):
    s = str(s)
    if s.endswith('kW'):
        s = float(s.replace('kW', ''))*1000
    elif s.endswith('MW'):
        s = float(s.replace('MW', ''))*1000000
    elif s.endswith('GW'):
        s = float(s.replace('GW', ''))*1000000000
    elif s.endswith('W'):
        s = float(s.replace('W', ''))
    return float(s)

def strip_U(s):
    if isinstance(s, str):
        return float(s.strip('U'))
    return float(s)
    
def convert_percent(s):
    if isinstance(s, str):
        return float(s.strip('%'))/100
    return s
    
def get_fan_power(base_server, base_fan, server_power, fan_slope):
    power_diff = server_power - base_server
    return base_fan + fan_slope * power_diff
        
class ServerCarbon:
    per_socket = ['cpu', 'memory', 'ssd', 'cxl', 'cxl_controller', 'ssd_reuse']
    def __init__(self, config_file: str, data_source_dir: str="../data/carbon_data",
                 overwrite_params=None, print_out=True) -> None:
        """Initialize the  class.

        Args:
            config_file: The YAML file containing the server configuration.
            params_file: The YAML file containing the server parameters.
        """
        if data_source_dir is None:
            data_source_dir = "../data/carbon_data"
        self.print_out = print_out
        self.config = read_yaml(config_file)['server']
        params_file = join_path(data_source_dir, 'params.yaml')
        self.params = read_yaml(params_file)
        
        if 'cpu_efficiency' not in self.params:
            self.params['cpu_efficiency'] = 1.0
        if 'power_factor' not in self.params:
            self.params['power_factor'] = 1.0

        if 'fan_slope' not in self.params:
            self.params['fan_slope'] = -1.0
        else:
            if '2U_server_base' not in self.params or '1U_server_base' not in self.params:
                raise ValueError('Fan slope specified but no base server power specified')
            self.params['2U_server_base'] = strip_power(self.params['2U_server_base'])
            self.params['1U_server_base'] = strip_power(self.params['1U_server_base'])

        if self.print_out:
            print(f"Calculating SKU carbon for {self.config['name']}...")

        if overwrite_params is not None:
            for key, value in overwrite_params.items():
                if key in self.params:
                    self.params[key] = value
                else:
                    raise ValueError(f'Parameter {key} not found in params.yaml')
        
        if 'emissions_factor' in self.params:
            # convert from kgCO2e/kWh to kgCO2e/kWMonth
            self.params['emissions_factor'] = self.params['emissions_factor']*24*30

        # set the number of sockets based on number of CPUs
        self._set_socket_count()

        # pull the data for the components
        self.data = {}
        self.data['cpu'] = index_cpu_data(self.config['cpu']['vendor'], 
                                          self.config['cpu']['type'], 
                                          self.config['cpu']['core_count'],
                                          data_source=data_source_dir)
        self.data['cpu']['number'] = self.config['cpu']['number']

        self.data['memory'] = index_memory_data(self.config['memory']['type'], 
                                                self.config['memory']['frequency'], 
                                                self.config['memory']['size'],
                                                data_source=data_source_dir)
        self.data['memory']['number'] = self.config['memory']['number']

        self.data['cxl'] = index_memory_data(self.config['cxl']['type'], 
                                             self.config['cxl']['frequency'], 
                                             self.config['cxl']['size'],
                                             data_source=data_source_dir)
        self.data['cxl']['number'] = self.config['cxl']['number']

        if self.data['cxl']['number'] > 0:
            self.data['cxl_controller'] = index_cxl_controller_data(self.config['cxl']['controller'],
                                                                    data_source=data_source_dir)
            controller_dimm_capacity = self.data['cxl_controller']['channels'] * self.data['cxl_controller']['dimms_per_channel']
            self.data['cxl_controller']['number'] = ceil(self.config['cxl']['number'] / controller_dimm_capacity)
        else:
            self.data['cxl_controller'] = {'number': 0, 'power': 0, 'size': 0, 'carbon': 0}

        self.data['ssd'] = index_ssd_data(self.config['ssd']['type'], 
                                          self.config['ssd']['size'],
                                          data_source=data_source_dir)
        self.data['ssd']['number'] = self.config['ssd']['number']

        if 'ssd_reuse' in self.config:
            self.data['ssd_reuse'] = index_ssd_data(self.config['ssd_reuse']['type'], 
                                                    self.config['ssd_reuse']['size'],
                                                    data_source=data_source_dir,
                                                    reuse=True)
            self.data['ssd_reuse']['number'] = self.config['ssd_reuse']['number']

        self.data['nic'] = index_nic_data(self.config['nic']['bandwidth'],
                                          data_source=data_source_dir)
        self.data['nic']['number'] = self.config['nic']['number']

        for key in self.data:
            self.data[key] = convert_units(self.data[key])

        # pull data for server and rack - these will both be lists of dicts
        self.data['dc'], dc_config = index_dc_data(self.config['dc']['type'],
                                                   data_source=data_source_dir)
        self.data['rack'] = index_rack_data(self.config['rack']['type'],
                                            data_source=data_source_dir)
        self.data['server'] = index_server_data(self.config['type'],
                                                data_source=data_source_dir)
        
        # set dc config
        for key, value in dc_config.items():
            self.config['dc'][key] = value
        self.config['dc']['power_capacity'] = strip_power(self.config['dc']['power_capacity'])
        self.config['dc']['rack_capacity'] = float(self.config['dc']['rack_capacity'])

        for comp in self.data['server']:
            if 'carbon' not in self.data['server'][comp]:
                self.data['server'][comp]['carbon'] = 0.0
            self.data['server'][comp] = convert_units(self.data['server'][comp])
        for comp in self.data['rack']:
            if 'carbon' not in self.data['rack'][comp]:
                self.data['rack'][comp]['carbon'] = 0.0
            self.data['rack'][comp] = convert_units(self.data['rack'][comp])
        self.config['rack'] = convert_units(self.config['rack'])
        for comp in self.data['dc']:
            if 'carbon' not in self.data['dc'][comp]:
                self.data['dc'][comp]['carbon'] = 0.0
            self.data['dc'][comp] = convert_units(self.data['dc'][comp])

        # dicts with component keys, values are derate curves
        self.component_derate_curves = {}
        self._set_derate_curves()

        # set resource capacities
        self.capacities = {}
        self._set_capacities()

        # set the components per server
        self.num_components = {}
        self._set_num_components()

        # per component power
        self.allocated_component_power = {}
        self.provisioned_component_power = {}
        self._set_component_power()

        # set fan power for the server
        self.server_power_no_fan = None
        self._set_fan_power()
        # reset since fan power has changed
        self._set_component_power()

        # per component operational and embodied emissions
        self.component_operational = {}
        self.component_embodied = {}
        self.component_carbon = {}
        self._set_component_carbon()

        # get per-server operational and embodied emissions
        self.component_server_operational = {}
        self.component_server_embodied = {}
        self.component_server_carbon = {}
        self.server_carbon = 0
        self.server_embodied = 0
        self.server_operational = 0
        self._set_server_carbon()

        # set the number of servers
        self.server_count = 0
        self.power_limited = False
        self._set_server_count()

        # set the per-rack operational and embodied carbon
        self.component_rack_operational = {}
        self.component_rack_embodied = {}
        self.component_rack_carbon = {}
        self.rack_carbon = 0
        self.rack_embodied = 0
        self.rack_operational = 0
        self._set_rack_carbon()

        # set the number of racks
        self.rack_count = 0
        self.dc_power_limited = False
        self._set_rack_count()

        # set the per-dc operational and embodied carbon
        self.component_dc_operational = {}
        self.component_dc_embodied = {}
        self.component_dc_carbon = {}
        self.dc_carbon = 0
        self.dc_embodied = 0
        self.dc_operational = 0
        self._set_dc_carbon()

        # set the sellable cores
        self.sellable_cores = self.vCores = 0
        self._set_sellable_cores()
        if print_out:
            self.print_summary()
    
    def print_summary(self) -> None:
        print(f'Sellable cores: {self.sellable_cores:.2f}')

        # format with commas
        print(f'Server operational: {self.get_server_operational():,.2f}, Server embodied: {self.get_server_embodied():,.2f}, Server carbon: {self.get_server_carbon():,.2f} kgCO2e')
        print(f'Rack operational: {self.get_rack_operational():,.2f} kgCO2e ({100 - self.get_rack_perc_embodied()}%), Rack embodied: {self.get_rack_embodied():,.2f} kgCO2e ({self.get_rack_perc_embodied()}%), Rack carbon: {self.get_rack_carbon():,.2f} kgCO2e')
        print(f'DC operational: {self.get_dc_operational():,.2f} kgCO2e ({100 - self.get_dc_perc_embodied()}%), DC embodied: {self.get_dc_embodied():,.2f} kgCO2e ({self.get_dc_perc_embodied()}%), DC carbon: {self.get_dc_carbon():,.2f} kgCO2e')
        print(f'Carbon per sellable core: {self.get_carbon_per_sellable_core():,.2f} kgCO2e\n')

    def _set_derate_curves(self) -> None:
        """Set the derate curves for the server."""
        self.allocated_spec = self.config['spec']
        if 'spec_allocation' in self.config['rack']:
            self.provisioned_spec = self.config['rack']['spec_allocation']
        else:
            self.provisioned_spec = self.allocated_spec

        for key, value in self.data.items():
            if 'spec_derates' not in value:
                self.component_derate_curves[key] = lambda x: 1
                continue
            self.component_derate_curves[key] = fit_cubic(value['spec_derates'])

        for key, value in self.data['server'].items():
            if 'spec_derates' not in value:
                self.component_derate_curves[key] = lambda x: 1
                continue
            self.component_derate_curves[key] = fit_cubic(value['spec_derates'])

        for key, value in self.data['rack'].items():
            if 'spec_derates' not in value:
                self.component_derate_curves[key] = lambda x: 1
                continue
            self.component_derate_curves[key] = fit_cubic(value['spec_derates'])
        
        for key, value in self.data['dc'].items():
            if 'spec_derates' not in value:
                self.component_derate_curves[key] = lambda x: 1
                continue
            self.component_derate_curves[key] = fit_cubic(value['spec_derates'])

    def get_num_cxl_controllers(self) -> int:
        """Get the number of CXL controllers in the server."""
        return self.data['cxl_controller']['number']

    def get_derates(self) -> Dict[str, float]:
        """Get the derates for the server components based on the derate curves and spec rate."""
        derates = {}
        for key, value in self.component_derate_curves.items():
            derates[key] = value(self.allocated_spec)
        return derates
    
    def get_rack_capacity(self, empty: bool=True) -> float:
        """Get the space capacity (# servers) of the rack."""
        rack_capacity = self.config['rack']['capacity']
        rack_capacity = strip_U(rack_capacity)
        if not empty:
            return rack_capacity

        rack_capacity_used = 0
        for component in self.data['rack']:
            rack_capacity_used += strip_U(self.data['rack'][component]['capacity']) * self.data['rack'][component]['number']
        return rack_capacity - rack_capacity_used
    
    def get_dc_capacity(self) -> float:
        """Get the space capacity (# racks) of the data center."""
        return float(self.config['dc']['rack_capacity'])
    
    def get_dc_power_capacity(self) -> float:
        """Get the power capacity of the data center."""
        return float(self.config['dc']['power_capacity'])
    
    def _set_rack_count(self) -> None:
        """Set the number of racks in the data center."""
        rack_provisioned, rack_allocated = self.get_rack_power()
        power_rack_count = floor(self.get_dc_power_capacity() / rack_provisioned)
        capacity_rack_count = self.get_dc_capacity()
        if power_rack_count < capacity_rack_count:
            self.rack_count = power_rack_count
            self.power_limited = True
            if self.print_out:
                print(f"DC is power limited to: {self.rack_count} racks (rather than space limited to {capacity_rack_count})")
        else:
            self.rack_count = capacity_rack_count
            self.power_limited = False
            if self.print_out:
                print(f"DC is space limited to: {self.rack_count} racks (rather than power limited to {power_rack_count})")
    
    def get_server_form(self) -> str:
        """Get the form factor of the server (e.g. 2U)."""
        return strip_U(self.config['form'])

    def _set_server_count(self) -> None:
        """Set the number of servers in the server. Based on rack power and provisioned spec."""
        # num_servers overrides rack power calculation
        if 'num_servers' in self.config['rack'] and self.config['rack']['num_servers'] > 0 and self.config['rack']['num_servers'] is not None:
            self.server_count = self.config['rack']['num_servers']
        else:
            rack_set_power = self.config['rack']['power']
            rack_power = self.provisioned_component_power['rack']
            rack_set_power -= rack_power
            provisioned_power, allocated_power, _ = self.get_server_power()
            if self.print_out:
                print(f"Provisioned power: {provisioned_power:,.2f}, Allocated power: {allocated_power:,.2f}")
                print(f"Rack set power: {rack_set_power:,.2f}")
            power_server_count = floor(rack_set_power / provisioned_power)

            rack_capacity = self.get_rack_capacity()
            capacity_server_count = floor(rack_capacity / self.get_server_form())

            if power_server_count < capacity_server_count:
                self.power_limited = True
                self.server_count = power_server_count
                if self.print_out:
                    print(f"Rack is power limited to: {self.server_count} servers")
            else:
                self.power_limited = False
                self.server_count = capacity_server_count
                if self.print_out:
                    print(f"Rack is space limited to: {self.server_count} servers")
        if self.print_out:
            print(f"Server count: {self.server_count}")

    def get_socket_count(self) -> int:
        """Get the number of sockets in the server."""
        return self.socket_count
    
    def get_server_count(self) -> int:
        """Get the number of servers in the rack."""
        return self.server_count
    
    def get_rack_count(self) -> int:
        """Get the number of racks in the data center."""
        return self.rack_count
    
    def _set_fan_power(self) -> None:
        """Set the fan power for the server."""
        if self.params['fan_slope'] <= 0:
            return

        fan_slope = self.params['fan_slope']
        base_power = self.params['2U_server_base']
        if self.config['form'] == '1U':
            base_power = self.params['1U_server_base']
        
        self.get_server_power_no_fan()
        self.data['server']['fan']['power'] = get_fan_power(base_power,
                                                            self.data['server']['fan']['power'],
                                                            self.server_power_no_fan,
                                                            fan_slope)
        
    def get_server_power_no_fan(self) -> float:
        """Get the power of the server without the fan."""
        if self.server_power_no_fan is not None:
            return self.server_power_no_fan
        
        provisioned_power, allocated_power, used_power = self.get_server_power()
        derated_fan_power = get_power_from_dict(self.data['server']['fan'],
                                                self.component_derate_curves['fan'],
                                                self.allocated_spec)

        used_fan_power = derated_fan_power * self.params['power_factor']
        self.server_power_no_fan = used_power - used_fan_power
        return self.server_power_no_fan

    def _set_component_carbon(self) -> None:
        """Set the emissions for the various components."""
        amortized_components = ['server', 'rack', 'dc']
        for key, value in self.data.items():
            factor = self.params['PUE']
            factor *= self.params['power_factor']
            capex_factor = 1.0
            if key in amortized_components:
                total_opex = 0
                for _key, component in value.items():
                    if 'number' not in component:
                        component['number'] = 1
                    total_opex +=  get_opex(component['power'], 
                                            self.allocated_spec,
                                            self.component_derate_curves[_key],
                                            component['number'],
                                            self.params['emissions_factor'], 
                                            self.params['lifetime'],
                                            factor=factor)
                self.component_operational[key] = total_opex
                self.component_embodied[key] = get_dict_capex(value,
                                                              cost='carbon',
                                                              server_lifetime=self.params['lifetime'])
                continue
            if key == 'cpu':
                factor *= self.params['voltage_regulator_overhead']
                factor *= self.params['cpu_efficiency']
            self.component_operational[key] = get_opex(value['power'],
                                                       self.allocated_spec,
                                                       self.component_derate_curves[key],
                                                       value['number'],
                                                       self.params['emissions_factor'],
                                                       self.params['lifetime'],
                                                       factor=factor)
            self.component_embodied[key] = get_capex_from_dict(value,
                                                               cost='carbon',
                                                               factor=factor,
                                                               server_lifetime=self.params['lifetime'])
        for key, value in self.component_operational.items():
            self.component_carbon[key] = value + self.component_embodied[key]
            
    def _set_component_power(self) -> None:
        """Set the power for the server components."""
        amortized_components = ['server', 'rack', 'dc']
        for key, value in self.data.items():
            factor = 1.0
            if key in amortized_components:
                self.allocated_component_power[key] = get_dict_power(value,
                                                                     self.component_derate_curves[key],
                                                                     self.allocated_spec,
                                                                     factor=factor)
                self.provisioned_component_power[key] = get_dict_power(value,
                                                                       self.component_derate_curves[key],
                                                                       self.provisioned_spec,
                                                                       factor=factor)
                continue
            if key == 'cpu':
                factor *= self.params['voltage_regulator_overhead']
                factor *= self.params['cpu_efficiency']
            self.allocated_component_power[key] = get_power_from_dict(value,
                                                                      self.component_derate_curves[key],
                                                                      self.allocated_spec,
                                                                      factor=factor)
            self.provisioned_component_power[key] = get_power_from_dict(value,
                                                                        self.component_derate_curves[key],
                                                                        self.provisioned_spec,
                                                                        factor=factor)

    def _set_capacities(self) -> None:
        """Set the capacities per socket for the per-socket components."""
        self.capacities = {}
        for key, value in self.data.items():
            if key in self.per_socket:
                if key == 'cpu':
                    self.capacities[key] = value['count'] * value['number']
                elif key == 'memory':
                    self.capacities[key] = value['size'] * value['number']
                elif key == 'cxl':
                    self.capacities[key] = value['size'] * value['number']
                elif key == 'ssd':
                    self.capacities[key] = value['size']  * value['number'] / 1000.0 # convert to TB
                elif key == 'cxl_controller':
                    self.capacities[key] = value['number']
                elif key == 'ssd_reuse':
                    self.capacities[key] = value['size']  * value['number'] / 1000.0 # convert to TB
        
        self.capacities['total_memory'] = self.capacities['memory'] + self.capacities['cxl']
    
    def get_capacities(self) -> Dict[str, float]:
        """Get the capacities for the server components (per-socket)."""
        return self.capacities
    
    def _set_num_components(self) -> None:
        """Set the number of components per server (limiting to per-socket components)."""
        self.num_components = {}
        for key, value in self.data.items():
            if key in self.per_socket:
                self.num_components[key] = value['number'] * self.socket_count
    
    def get_num_components(self) -> Dict[str, int]:
        """Get the dict that contains the number for each component."""
        return self.num_components

    def get_resource_physical_core_ratios(self) -> Dict[str, float]:
        """Get the physical core to resource ratio for each resource."""
        ratios = {}
        for key, value in self.capacities.items():
            ratios[key] = value / self.capacities['cpu']
        return ratios
    
    def get_rack_carbon(self) -> float:
        """Get the carbon for the rack."""
        return self.rack_carbon
    
    def get_rack_embodied(self) -> float:
        """Get the embodied for the rack."""
        return self.rack_embodied
    
    def get_rack_operational(self) -> float:
        """Get the operational for the rack."""
        return self.rack_operational
    
    def get_dc_carbon(self) -> float:
        """Get the carbon for the data center."""
        return self.dc_carbon
    
    def get_dc_embodied(self) -> float:
        """Get the embodied for the data center."""
        return self.dc_embodied
    
    def get_dc_operational(self) -> float:
        """Get the operational for the data center."""
        return self.dc_operational
    
    def get_server_sellable_cores(self) -> float:
        """Get the sellable cores for the server."""
        return self.get_sellable_cores() * self.get_socket_count()
    
    def get_rack_sellable_cores(self) -> float:
        """Get the sellable cores for the rack."""
        return self.get_server_sellable_cores() * self.get_server_count()
    
    def get_dc_sellable_cores(self) -> float:
        """Get the sellable cores for the data center."""
        return self.get_rack_sellable_cores() * self.get_rack_count()

    def get_carbon_per_sellable_core(self) -> float:
        """Get the carbon per sellable core."""
        return round(self.get_rack_carbon() / self.get_rack_sellable_cores(), 2)
    
    def get_operational_per_sellable_core(self) -> float:
        """Get the operational per sellable core."""
        return round(self.get_rack_operational() / self.get_rack_sellable_cores(), 2)
    
    def get_embodied_per_sellable_core(self) -> float:
        """Get the embodied per sellable core."""
        return round(self.get_rack_embodied() / self.get_rack_sellable_cores(), 2)
    
    def get_carbon_per_sellable_core_dc(self) -> float:
        """Get the carbon per sellable core in the data center."""
        return round(self.get_dc_carbon() / self.get_dc_sellable_cores(), 2)
    
    def get_operational_per_sellable_core_dc(self) -> float:
        """Get the operational per sellable core in the data center."""
        return round(self.get_dc_operational() / self.get_dc_sellable_cores(), 2)
    
    def get_embodied_per_sellable_core_dc(self) -> float:
        """Get the embodied per sellable core in the data center."""
        return round(self.get_dc_embodied() / self.get_dc_sellable_cores(), 2)

    def _set_sellable_cores(self) -> None:
        """Set the number of sellable cores in the server."""
        self.vCores = self.capacities['cpu'] * self.data['cpu']['threads']
        vCore_with_overhead = self.vCores
        core_overhead = 0.0
        # if overhead is specified as a percentage (if some cores dedicated to non-VM tasks)
        if 'overhead' in self.config['cpu']:
            core_overhead = self.config['cpu']['overhead']
        # if percentage then take the percentage of the vCores
        if isinstance(core_overhead, str):
            core_overhead = float(core_overhead.strip('%')) / 100.0
            vCore_with_overhead *= 1 - core_overhead
            if self.print_out:
                print(f"core overhead: {core_overhead}")
                print(f"vCores: {vCore_with_overhead}")
                print(f"vCores with overhead: {vCore_with_overhead}")
        # otherwise treat as a number of cores as overhead
        else:
            vCore_with_overhead -= core_overhead
        if 'oversubscription' not in self.config:
            self.sellable_cores = self.vCores * (1 - core_overhead)
            return
        x = 0.0
        y = 0.0
        if self.config['oversubscription']['only_oversubscribable']:
            x = 1.0
        else:
            x = self.config['oversubscription']['cpu_oversubscription']['oversubscribable']
        y = self.config['oversubscription']['cpu_oversubscription']['rate']

        sCores_per_vCore = (1 - x) + x / (1 - y)
        self.sellable_cores = self.vCores * (1 - core_overhead) * sCores_per_vCore

    def get_sellable_cores(self) -> int:
        """Get the number of sellable cores in the server."""
        return self.sellable_cores
    
    def get_vcores(self) -> int:
        """Get the number of vcores in the server."""
        return self.vCores
    
    def get_physical_cores(self) -> int:
        """Get the number of physical cores in the server."""
        return self.capacities['cpu']
    
    def get_server_power(self) -> float:
        """Get the power of the server. Rack stuff is NOT amortized."""
        provisioned_power = 0
        allocated_power = 0
        for key, value in self.data.items():
            if key == 'rack':
                continue
            if key in self.per_socket:
                provisioned_power += self.provisioned_component_power[key] * self.socket_count
                allocated_power += self.allocated_component_power[key] * self.socket_count
                continue
            provisioned_power += self.provisioned_component_power[key]
            allocated_power += self.allocated_component_power[key]
        provisioned_power *= 1.0 + (1.0 - self.params['PSU_efficiency'])
        allocated_power *= 1.0 + (1.0 - self.params['PSU_efficiency'])
        used_power = allocated_power * self.params['power_factor']

        return provisioned_power, allocated_power, used_power
    
    def get_per_month_carbon(self) -> float:
        """Get the carbon per month of the server."""
        return self.get_carbon_per_sellable_core() / self.params['lifetime']
    
    def get_rack_power(self) -> Tuple[float, float]:
        """Get the power of the rack."""
        provisioned_power = 0
        allocated_power = 0
        for key, value in self.data.items():
            if key in self.per_socket:
                provisioned_power += self.provisioned_component_power[key] * self.socket_count
                allocated_power += self.allocated_component_power[key] * self.socket_count
                continue
            provisioned_power += self.provisioned_component_power[key]
            allocated_power += self.allocated_component_power[key]
        provisioned_power *= 1.0 + (1.0 - self.params['PSU_efficiency'])
        allocated_power *= 1.0 + (1.0 - self.params['PSU_efficiency'])

        return provisioned_power, allocated_power
    
    def get_server_operational(self) -> float:
        """Get the operational of the server."""
        return self.server_operational
    
    def get_server_embodied(self) -> float:
        """Get the embodied of the server."""
        return self.server_embodied
    
    def get_server_carbon(self) -> float:
        """Get the carbon of the server."""
        return self.server_carbon
    
    def get_per_server_operational(self) -> float:
        """Get the per-server operational of the server."""
        return self.rack_operational / self.server_count
    
    def get_per_server_embodied(self) -> float:
        """Get the per-server embodied of the server."""
        return self.rack_embodied / self.server_count
    
    def get_per_server_carbon(self) -> float:
        """Get the per-server carbon of the server."""
        return self.rack_carbon / self.server_count
    
    def get_dc_per_server_operational(self) -> float:
        """Get the per-server operational of the data center."""
        return self.dc_operational / self.server_count
    
    def get_dc_per_server_embodied(self) -> float:
        """Get the per-server embodied of the data center."""
        return self.dc_embodied / self.server_count
    
    def get_dc_per_server_carbon(self) -> float:
        """Get the per-server carbon of the data center."""
        return self.dc_carbon / self.server_count
    
    def get_component_power(self) -> Dict[str, float]:
        return self.allocated_component_power
    
    def get_server_cores(self) -> int:
        return self.capacities['cpu']
    
    def get_server_memory(self) -> int:
        return self.capacities['memory']

    def _set_server_carbon(self) -> None:
        """Set the carbon emissions for the server. NOT amortized. (i.e., rack/DC stuff is not included)"""
        self.server_operational = 0
        self.server_embodied = 0
        self.component_server_operational = {}
        self.component_server_embodied = {}
        self.component_server_carbon = {}
        for key in self.component_carbon:
            if key == 'rack' or key == 'dc':
                continue
            component_operational = self.component_operational[key]
            component_embodied = self.component_embodied[key]
            # multiply by the number of sockets if the component is per-socket
            if key in self.per_socket:
                component_operational *= self.socket_count
                component_embodied *= self.socket_count
            self.server_operational += component_operational
            self.server_embodied += component_embodied
            self.component_server_operational[key] = component_operational
            self.component_server_embodied[key] = component_embodied
            self.component_server_carbon[key] = component_operational + component_embodied
        self.server_carbon = self.server_operational + self.server_embodied

    def _set_rack_carbon(self) -> None:
        """Set the carbon emissions for the rack. NOT amortized. (i.e., DC stuff is not included)"""
        # set the per-rack carbon emissions for the components in the rack
        for key in self.component_server_carbon:
            if key == 'rack' or key == 'dc':
                continue
            self.component_rack_operational[key] = self.component_server_operational[key] * self.server_count
            self.component_rack_embodied[key] = self.component_server_embodied[key] * self.server_count
            self.component_rack_carbon[key] = self.component_rack_operational[key] + self.component_rack_embodied[key]
        self.component_rack_operational['rack'] = self.component_operational['rack']
        self.component_rack_embodied['rack'] = self.component_embodied['rack']
        self.component_rack_carbon['rack'] = self.component_rack_operational['rack'] + self.component_rack_embodied['rack']

        # set the total carbon emissions for the rack - by adding on the rack carbon to servers' carbon
        self.rack_operational = self.component_operational['rack'] + self.server_operational * self.server_count
        self.rack_embodied = self.component_embodied['rack'] + self.server_embodied * self.server_count
        self.rack_carbon = self.rack_operational + self.rack_embodied

    def _set_dc_carbon(self) -> None:
        """Set the carbon emissions for the data center."""
        # set the per-dc carbon emissions for the components in the data center
        for key in self.component_rack_carbon:
            if key == 'dc':
                continue
            self.component_dc_operational[key] = self.component_rack_operational[key] * self.rack_count
            self.component_dc_embodied[key] = self.component_rack_embodied[key] * self.rack_count
            self.component_dc_carbon[key] = self.component_dc_operational[key] + self.component_dc_embodied[key]
        self.component_dc_operational['dc'] = self.component_operational['dc']
        self.component_dc_embodied['dc'] = self.component_embodied['dc']
        self.component_dc_carbon['dc'] = self.component_dc_operational['dc'] + self.component_dc_embodied['dc']

        # set the total carbon emissions for the data center - by adding on the dc carbon to racks' carbon
        self.dc_operational = self.component_operational['dc'] + self.rack_operational * self.rack_count
        self.dc_embodied = self.component_embodied['dc'] + self.rack_embodied * self.rack_count
        self.dc_carbon = self.dc_operational + self.dc_embodied

    def _set_socket_count(self) -> None:
        """Set the number of sockets in the server."""
        # if not specified, assume 1 socket
        if 'sockets' not in self.config:
            self.socket_count = 1
            return
        self.socket_count = self.config['sockets']

    def get_server_carbon_df(self) -> pd.DataFrame:
        """Get the operational and embodied carbon for the server as a dataframe."""
        operational = pd.DataFrame.from_dict(self.component_server_operational, orient='index', columns=['operational'])
        embodied = pd.DataFrame.from_dict(self.component_server_embodied, orient='index', columns=['embodied'])
        carbon = pd.DataFrame.from_dict(self.component_server_carbon, orient='index', columns=['carbon'])
        # add totals
        operational.loc['total'] = operational.sum()
        embodied.loc['total'] = embodied.sum()
        carbon.loc['total'] = carbon.sum()
        # calculate percentages of total
        operational['perc of operational'] = operational['operational'] * 100 / operational.loc['total', 'operational']
        embodied['perc of embodied'] = embodied['embodied'] * 100 / embodied.loc['total', 'embodied']
        carbon['perc of carbon'] = carbon * 100 / carbon.loc['total', 'carbon']
        # round to 2 decimal places
        operational = operational.round(2)
        embodied = embodied.round(2)
        carbon = carbon.round(2)
        # concat them as columns
        return pd.concat([operational, embodied, carbon], axis=1)
    
    def get_rack_carbon_df(self) -> pd.DataFrame:
        """Get the operational and embodied carbon for the rack as a dataframe."""
        operational = pd.DataFrame.from_dict(self.component_rack_operational, orient='index', columns=['operational'])
        embodied = pd.DataFrame.from_dict(self.component_rack_embodied, orient='index', columns=['embodied'])
        carbon = pd.DataFrame.from_dict(self.component_rack_carbon, orient='index', columns=['carbon'])
        # add totals
        operational.loc['total'] = operational.sum()
        embodied.loc['total'] = embodied.sum()
        carbon.loc['total'] = carbon.sum()
        # calculate percentages of total
        operational['perc of operational'] = operational['operational'] * 100 / operational.loc['total', 'operational']
        embodied['perc of embodied'] = embodied['embodied'] * 100 / embodied.loc['total', 'embodied']
        carbon['perc of carbon'] = carbon * 100 / carbon.loc['total', 'carbon']
        # round to 2 decimal places
        operational = operational.round(2)
        embodied = embodied.round(2)
        carbon = carbon.round(2)
        # concat them as columns
        return pd.concat([operational, embodied, carbon], axis=1)
    
    def get_dc_carbon_df(self) -> pd.DataFrame:
        """Get the operational and embodied carbon for the data center as a dataframe."""
        operational = pd.DataFrame.from_dict(self.component_dc_operational, orient='index', columns=['operational'])
        embodied = pd.DataFrame.from_dict(self.component_dc_embodied, orient='index', columns=['embodied'])
        carbon = pd.DataFrame.from_dict(self.component_dc_carbon, orient='index', columns=['carbon'])
        # add totals
        operational.loc['total'] = operational.sum()
        embodied.loc['total'] = embodied.sum()
        carbon.loc['total'] = carbon.sum()
        # calculate percentages of total
        operational['perc of operational'] = operational['operational'] * 100 / operational.loc['total', 'operational']
        embodied['perc of embodied'] = embodied['embodied'] * 100 / embodied.loc['total', 'embodied']
        carbon['perc of carbon'] = carbon * 100 / carbon.loc['total', 'carbon']
        # round to 2 decimal places
        operational = operational.round(2)
        embodied = embodied.round(2)
        carbon = carbon.round(2)
        # concat them as columns
        return pd.concat([operational, embodied, carbon], axis=1)
    
    def get_info_dict(self) -> Dict[str, Any]:
        """Get the information about the server as a dictionary."""
        info = {}

        # add per-socket capacities
        for component in self.capacities:
            info[f'{component}_capacity'] = self.capacities[component]

        info['socket_count'] = self.socket_count
        info['server_count'] = self.server_count
        info['sellable_core_count'] = self.sellable_cores
        info['constrained_by'] = "power" if self.power_limited else "space"

        provisioned, allocated = self.get_server_power()
        info['server_design_power'] = provisioned
        info['server_allocated_power'] = allocated
        
        # add rack-level component operational, embodied, and carbon
        for component in self.component_rack_operational:
            info[f'{component}_operational'] = self.component_rack_operational[component]
            info[f'{component}_embodied'] = self.component_rack_embodied[component]
            info[f'{component}_carbon'] = self.component_rack_carbon[component]

            info[f'{component}_operational_perc'] = self.component_rack_operational[component] * 100 / self.rack_operational
            info[f'{component}_embodied_perc'] = self.component_rack_embodied[component] * 100 / self.rack_embodied
            info[f'{component}_carbon_perc'] = self.component_rack_carbon[component] * 100 / self.rack_carbon

        # add rack total operational and embodied carbon
        info['total_rack_operational'] = self.rack_operational
        info['total_rack_embodied'] = self.rack_embodied
        info['total_rack_carbon'] = self.rack_carbon

        # add per-sellable rack-level carbon
        info['carbon_per_sellable_core'] = self.get_carbon_per_sellable_core()

        # round all floats to 2 decimal places
        for key in info:
            if isinstance(info[key], float):
                info[key] = round(info[key], 2)
        
        return info
    
    def get_info_dict_small(self) -> Dict[str, Any]:
        """Get a small subset of the information about the server as a dictionary."""
        info = {}
        info['server_count'] = self.server_count
        info['sellable_core_count'] = self.sellable_cores
        info['rack_embodied_perc'] = self.rack_embodied * 100 / self.rack_carbon
        info['rack_carbon'] = self.rack_carbon
        info['carbon_per_sellable_core'] = self.get_carbon_per_sellable_core()

        for key in info:
            if isinstance(info[key], float):
                info[key] = round(info[key], 2)
        
        return info
    
    def get_breakdown_df(self) -> pd.DataFrame:
        '''Get the breakdown of the carbon for each component in the yaml file.'''
        # get component breakdown
        # each will be a df - each row is a component, columns for percentage of carbon for each component
        rack_carbon_breakdown = self.get_rack_carbon_df()
        # only take columns starting with "perc"
        rack_carbon_breakdown = rack_carbon_breakdown.filter(regex='perc')
        # remove "perc of " from column names
        rack_carbon_breakdown.columns = rack_carbon_breakdown.columns.str.replace('perc of ', '')
        # transpose and then concat them
        rack_carbon_breakdown = rack_carbon_breakdown.T
        # remove "total" column
        rack_carbon_breakdown = rack_carbon_breakdown.drop(columns=['total'])
        return rack_carbon_breakdown
    
    def get_power_per_vcore(self):
        """Get the power per core for the server."""
        return self.get_server_power()[1] / self.sellable_cores
    
    def get_rack_perc_embodied(self):
        """Get the percentage of embodied carbon for the rack."""
        return round(self.rack_embodied * 100 / self.rack_carbon, 2)
    
    def get_rack_perc_operational(self):
        """Get the percentage of operational carbon for the rack."""
        return round(self.rack_operational * 100 / self.rack_carbon, 2)
    
    def get_dc_perc_embodied(self):
        """Get the percentage of embodied carbon for the data center."""
        return round(self.dc_embodied * 100 / self.dc_carbon, 2)
    
    def get_dc_perc_operational(self):
        """Get the percentage of operational carbon for the data center."""
        return round(self.dc_operational * 100 / self.dc_carbon, 2)