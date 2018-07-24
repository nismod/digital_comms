"""Digital demand dummy model
"""
import os
import fiona
import configparser
import numpy as np
np.set_printoptions(threshold=np.nan)

from digital_comms.fixed_network.model import ICTManager
from digital_comms.fixed_network.interventions import decide_interventions

from smif.model.sector_model import SectorModel

class DigitalCommsWrapper(SectorModel):
    """Digital model
    """
    def __init__(self, name):
        super().__init__(name)

        self.user_data = {}

    def initialise(self, initial_conditions):
        print('initialise')

    def before_model_run(self, data_handle):
        print('before model run')
        """Implement this method to conduct pre-model run tasks

        Arguments
        ---------
        data_handle: smif.data_layer.DataHandle
            Access parameter values (before any model is run, no dependency
            input data or state is guaranteed to be available)
        """

        # Get wrapper configuration
        path_main = os.path.dirname(os.path.abspath(__file__))
        config = configparser.ConfigParser()
        config.read(os.path.join(path_main, 'wrapperconfig.ini'))
        data_path = config['PATHS']['path_local_data']

        # Get modelrun configuration
        parameters = data_handle.get_parameters()
        
        # Load assets
        assets = {}
        assets['premises'] = read_shapefile(os.path.join(data_path, 'assets_layer5_premises.shp'))
        assets['distributions'] = read_shapefile(os.path.join(data_path, 'assets_layer4_distributions.shp'))
        assets['cabinets'] = read_shapefile(os.path.join(data_path, 'assets_layer3_cabinets.shp'))
        assets['exchanges'] = read_shapefile(os.path.join(data_path, 'assets_layer2_exchanges.shp'))
        
        # Load links
        links = []
        links.extend(read_shapefile(os.path.join(data_path, 'links_layer5_premises.shp')))
        links.extend(read_shapefile(os.path.join(data_path, 'links_layer4_distributions.shp')))
        links.extend(read_shapefile(os.path.join(data_path, 'links_layer3_cabinets.shp')))

        self.logger.info("DigitalCommsWrapper - Intitialise system")
        self.system = ICTManager(assets, links, parameters)

    def simulate(self, data_handle):
        
        # -----
        # Start
        # -----
        now = data_handle.current_timestep
        self.logger.info("DigitalCommsWrapper received inputs in %s",
                         now)

        # -----------------------
        # Run fixed network model
        # -----------------------
        self.logger.info("DigitalCommsWrapper - Decide interventions")
        interventions, budget, spend = decide_interventions('rollout_fttp_per_distribution', data_handle.get_parameter('annual_budget'), data_handle.get_parameter('service_obligation_capacity'), self.system, now)

        self.logger.info("DigitalCommsWrapper - Upgrading system")
        self.system.upgrade(interventions)

        # -------------
        # Write outputs
        # -------------
        interventions_lut = {intervention[0]:intervention for intervention in interventions}
        
        distribution_upgrades = np.empty((self.system.number_of_assets['distributions'],1))
        for idx, distribution in enumerate(data_handle.get_region_names('broadband_distributions')):
            distribution_upgrades[idx, 0] = interventions_lut[distribution][2] if distribution in interventions_lut else 0
        data_handle.set_results('distribution_upgrades', distribution_upgrades)

        distribution_upgrade_costs_fttp = np.empty((self.system.number_of_assets['distributions'],1))
        for idx, distribution in enumerate(self.system.assets['distributions']):
            distribution_upgrade_costs_fttp[idx, 0] = distribution.upgrade_costs['fttp']
        data_handle.set_results('distribution_upgrade_costs_fttp', distribution_upgrade_costs_fttp)

        # ----
        # Exit
        # ----
        self.logger.info("DigitalCommsWrapper produced outputs in %s",
                         now)
    
    def extract_obj(self, results):
        return 0

def read_shapefile(file):
    with fiona.open(file, 'r') as source:
        return [f['properties'] for f in source]