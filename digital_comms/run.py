"""Digital demand dummy model
"""
import configparser
import csv
import os

#from memory_profiler import profile
#from pyinstrument import Profiler

import fiona  # type: ignore
import numpy as np  # type: ignore

from digital_comms.fixed_network.model import NetworkManager
from digital_comms.fixed_network.interventions import decide_interventions
from digital_comms.fixed_network.adoption import update_adoption_desirability

from smif.model.sector_model import SectorModel  # type: ignore

# numpy options
np.set_printoptions(threshold=np.nan)

# configure profiling with environment variable
PROFILE = False
if 'PROFILE_DC' in os.environ and os.environ['PROFILE_DC'] == "1":
    PROFILE = True


def memprofile(func):
    """Decorator - profile memory usage if profiling is enabled
    """
    def wrapper(*args, **kwargs):
        if PROFILE:
            profile(func, precision=1)(*args, **kwargs)
        else:
            func(*args, **kwargs)
    return wrapper


def cpuprofile(func):
    """Decorator - profile cpu usage
    """
    def wrapper(*args, **kwargs):
        if PROFILE:
            profiler = Profiler()
            profiler.start()
        func(*args, **kwargs)
        if PROFILE:
            profiler.stop()
            print(profiler.output_text(unicode=False, color=True))
    return wrapper

class DigitalCommsWrapper(SectorModel):
    """Digital model
    """
    def __init__(self, name):
        super().__init__(name)

        self.user_data = {}

    def initialise(self, initial_conditions):
        print('initialise')

    @cpuprofile
    @memprofile
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
        self.system = NetworkManager(assets, links, parameters)

        print('only distribution points with a benefit cost ratio > 1 can be upgraded')
        print('model rollout is constrained by the adoption desirability set by scenario')


    @cpuprofile
    @memprofile
    def simulate(self, data_handle):
        # -----
        # Start
        # -----
        now = data_handle.current_timestep
        self.logger.info("DigitalCommsWrapper received inputs in %s", now)

        # Set global parameters
        STRATEGY = data_handle.get_parameter('technology_strategy')
        TECH = STRATEGY.split("_")[0]

        # -----------------------
        # Get scenario adoption rate
        # -----------------------
        print("-------------------")
        print("Running", TECH, STRATEGY, data_handle.current_timestep)
        print("-------------------")
        annual_adoption_rate = data_handle.get_data('adoption')
        adoption_desirability = [premise for premise in self.system._premises if premise.adoption_desirability is True]
        total_premises = [premise for premise in self.system._premises]
        adoption_desirability_percentage = (len(adoption_desirability) / len(total_premises) * 100)
        percentage_annual_increase = annual_adoption_rate - adoption_desirability_percentage
        percentage_annual_increase = round(float(percentage_annual_increase), 1)
        print("* {} annual_adoption_rate is {} %".format(TECH, percentage_annual_increase))

        # -----------------------
        # Run fixed network model
        # -----------------------
        self.logger.info("DigitalCommsWrapper - Update adoption status on premises")
        self.system.update_adoption_desirability = update_adoption_desirability(self.system, percentage_annual_increase)
        premises_adoption_desirability_ids = self.system.update_adoption_desirability

        MAXIMUM_ADOPTION = len(premises_adoption_desirability_ids) + sum(getattr(premise, TECH) for premise in self.system._premises)
        # print("// length of premises_adoption_desirability_ids is {}".format(len(premises_adoption_desirability_ids)+1))
        # print("// sum of premises by tech {}".format(sum(getattr(premise, TECH) for premise in self.system._premises)))
        # print("// MAXIMUM_ADOPTION is {}".format(MAXIMUM_ADOPTION))

        self.logger.info("DigitalCommsWrapper - Decide interventions")
        interventions, budget, spend, match_funding_spend, subsidised_spend = decide_interventions(
            STRATEGY, data_handle.get_parameter('annual_budget'), data_handle.get_parameter('service_obligation_capacity'),
            self.system, now, MAXIMUM_ADOPTION, data_handle.get_parameter('telco_match_funding'),
            data_handle.get_parameter('subsidy'))

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

        premises_by_distribution = np.empty((self.system.number_of_assets['distributions'],1))
        for idx, distribution in enumerate(self.system.assets['distributions']):
            premises_by_distribution[idx, 0] = len(distribution._clients)
        data_handle.set_results('premises_by_distribution', premises_by_distribution)

        print("* {} premises adoption desirability is {}".format(TECH, (len(premises_adoption_desirability_ids))))
        premises_wanting_to_adopt = np.empty((1,1))
        premises_wanting_to_adopt[0, 0] = len(premises_adoption_desirability_ids)
        data_handle.set_results('premises_adoption_desirability', premises_wanting_to_adopt)

        distribution_upgrade_costs = ('distribution_upgrade_costs_' + str(TECH))
        distribution_upgrade_costs = np.empty((self.system.number_of_assets['distributions'],1))
        for idx, distribution in enumerate(self.system.assets['distributions']):
            distribution_upgrade_costs[idx, 0] = distribution.upgrade_costs[TECH]
        data_handle.set_results(('distribution_upgrade_costs_' + str(TECH)), distribution_upgrade_costs)

        upgrade_cost_per_premises = ('upgrade_cost_per_premises_' + str(TECH))
        upgrade_cost_per_premises = np.empty((self.system.number_of_assets['distributions'],1))
        for idx, distribution in enumerate(self.system.assets['distributions']):
            if len(distribution._clients) > 0:
                upgrade_cost_per_premises[idx, 0] = distribution.upgrade_costs[TECH] / len(distribution._clients)
            else:
                upgrade_cost_per_premises[idx, 0] = 0
        data_handle.set_results(('premises_upgrade_costs_' + str(TECH)), upgrade_cost_per_premises)

        #premises passed
        premises_passed = ('premises_passed_with_' + str(TECH))
        premises_passed = np.empty((1,1))
        premises_passed[0, 0] = sum(getattr(premise, TECH) for premise in self.system._premises)
        print("* {} premises passed {}".format(TECH, premises_passed))
        data_handle.set_results(('premises_passed_with_' + str(TECH)), premises_passed)

        percentage_of_premises_passed = ('percentage_of_premises_passed_with_' + str(TECH))
        percentage_of_premises_passed = np.empty((1,1))
        percentage_of_premises_passed[0, 0] = round((sum(getattr(premise, TECH) for premise in self.system._premises) / len(self.system._premises)*100),2)
        print("* {} percentage of premises passed {}".format(TECH, percentage_of_premises_passed))
        data_handle.set_results(('percentage_of_premises_passed_with_' + str(TECH)), percentage_of_premises_passed)

        #premises connected
        premises_connected = ('premises_connected_with_' + str(TECH))
        premises_connected = np.empty((1,1))
        premises_connected[0, 0] = sum(getattr(premise, TECH) for premise in self.system._premises if premise.adoption_desirability == True)
        print("* {} premises connected {}".format(TECH, premises_connected))
        data_handle.set_results(('premises_connected_with_' + str(TECH)), premises_connected)

        percentage_of_premises_connected = ('percentage_of_premises_connected_with_' + str(TECH))
        percentage_of_premises_connected = np.empty((1,1))
        percentage_of_premises_connected[0, 0] = round((sum(getattr(premise, TECH) for premise in self.system._premises if premise.adoption_desirability == True) / len(self.system._premises)*100),2)
        print("* {} percentage of premises connected {}".format(TECH, percentage_of_premises_connected))
        data_handle.set_results(('percentage_of_premises_connected_with_' + str(TECH)), percentage_of_premises_connected)

        # Regional output
        lad_names = self.get_region_names('lad2016')
        num_lads = len(lad_names)
        num_fttp = np.zeros((num_lads, 1))
        num_fttdp = np.zeros((num_lads, 1))
        num_fttc = np.zeros((num_lads, 1))
        num_adsl = np.zeros((num_lads, 1))

        coverage = self.system.coverage()
        for i, lad in enumerate(lad_names):
            if lad not in coverage:
                continue
            stats = coverage[lad]
            num_fttp[i, 0] = stats['num_fttp']
            num_fttdp[i, 0] = stats['num_fttdp']
            num_fttc[i, 0] = stats['num_fttc']
            num_adsl[i, 0] = stats['num_adsl']

        data_handle.set_results('lad_premises_with_fttp', num_fttp)
        data_handle.set_results('lad_premises_with_fttdp', num_fttdp)

        #get cambridge exchange data
        if STRATEGY == 'fttp_rollout_per_distribution' and TECH == 'fttp':

            path_main = os.path.dirname(os.path.abspath(__file__))
            config = configparser.ConfigParser()
            config.read(os.path.join(path_main, 'wrapperconfig.ini'))
            BASE_PATH = config['PATHS']['path_export_data']

            def csv_writer(data, filename, fieldnames):
                with open(os.path.join(BASE_PATH, filename),'w') as csv_file:
                    writer = csv.DictWriter(csv_file, fieldnames, lineterminator = '\n')
                    writer.writeheader()
                    writer.writerows(data)

            def write_out_upgrades(data):
                export_data = []
                for datum in data:
                    export_data.append({
                        'id': datum.id,
                        'upgrade': datum.fttp,
                        'year': now
                    })
                return export_data

            #get exchanges
            exchange = [exchange for exchange in self.system._exchanges if exchange.id == 'exchange_EACAM'][0]

            #get cabinets
            cabinets = exchange._clients
            cabinet_export_data = write_out_upgrades(cabinets)

            #get distributions
            distributions = []
            [distributions.extend(cabinet._clients) for cabinet in cabinets]
            distribution_export_data = write_out_upgrades(distributions)

            #get premises
            premises = []
            [premises.extend(distribution._clients) for distribution in distributions]

            premises_export_data = []
            for premise in premises:
                premises_export_data.append({
                    'id': premise.id,
                    'adoption_desirability': premise.adoption_desirability,
                    'premises_passed': premise.fttp,
                    'year': now
                })

            #get exchange to cabinet links
            exchange_to_cabinet_links = [link for link in self.system._links_from_cabinets if link.dest == 'exchange_EACAM']

            #get cabinet to dist point links
            cab_to_dist_point_links = exchange_to_cabinet_links.origin

            #get distributions
            cab_to_dist_point_links = []
            [cab_to_dist_point_links.extend(link.origin) for link in cab_to_dist_point_links]
            print(cab_to_dist_point_links)

            #set fieldnames
            generic_fieldnames = ['id','upgrade','year']
            premises_fieldnames = ['id','adoption_desirability','premises_passed','year']

            #write out
            csv_writer(cabinet_export_data, ('cabinet_data{}.csv'.format(now)), generic_fieldnames)
            csv_writer(distribution_export_data, ('distribution_data{}.csv'.format(now)), generic_fieldnames)
            csv_writer(premises_export_data, ('premises_data{}.csv'.format(now)), premises_fieldnames)

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
