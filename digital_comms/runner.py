from digital_comms.fixed_model import fixed_model, fixed_interventions
import fiona
from operator import attrgetter
import os

BASE_YEAR = 2016
END_YEAR = 2030
TIMESTEP_INCREMENT = 1
TIMESTEPS = range(BASE_YEAR, END_YEAR + 1, TIMESTEP_INCREMENT)

MARKET_SHARE = 0.3

# Annual capital budget constraint for the whole industry, GBP * market share
ANNUAL_BUDGET = (2 * 10 ** 9) * MARKET_SHARE

# Target threshold for universal mobile service, in Mbps/user
SERVICE_OBLIGATION_CAPACITY = 10

def read_shapefile(file):
    with fiona.open(file, 'r') as source:
        return [f['properties'] for f in source]

def read_assets():
    assets = {}
    assets['premises'] = read_shapefile(os.path.join('data', 'processed', 'assets_layer5_premises.shp'))
    assets['distributions'] = read_shapefile(os.path.join('data', 'processed', 'assets_layer4_distributions.shp'))
    assets['cabinets'] = read_shapefile(os.path.join('data', 'processed', 'assets_layer3_cabinets.shp'))
    assets['exchanges'] = read_shapefile(os.path.join('data', 'processed', 'assets_layer2_exchanges.shp'))

    return assets
    
def read_links():
    links = []
    links.extend(read_shapefile(os.path.join('data', 'processed', 'links_layer5_premises.shp')))
    links.extend(read_shapefile(os.path.join('data', 'processed', 'links_layer4_distributions.shp')))
    links.extend(read_shapefile(os.path.join('data', 'processed', 'links_layer3_cabinets.shp')))

    return links

def read_parameters():
    return {
        'costs': {
            'links': {
                'fiber_per_meter': 20,
                'copper_per_meter': 10
            },
            'assets': {
                'exchange': {
                    'fttp': 50000,
                    'gfast': 40000,
                    'fttc': 30000,
                    'adsl': 20000
                },
                'cabinet': {
                    'fttp': 5000,
                    'gfast': 4000,
                    'fttc': 3000,
                    'adsl': 2000
                },
                'distribution': {
                    'fttp': 500,
                    'gfast': 400,
                    'fttc': 300,
                    'adsl': 200
                },
                'premise': {
                    'fttp': 50,
                    'gfast': 40,
                    'fttc': 30,
                    'adsl': 20
                }
            }
        },
        'benefits': {
            'assets': {
                'premise': {
                    'fttp': 50,
                    'gfast': 40,
                    'fttc': 30,
                    'adsl': 20
                }
            }
        }
    }

if __name__ == "__main__": # allow the module to be executed directly 

    for intervention_strategy in [
            ('minimal'),
            ('upgrade_to_FTTdp_from_cabinet'),
            ('upgrade_to_FTTP_from_cabinet'),
            ('upgrade_to_FTTP_from_cabinet'),
        ]:

        print("Running:", intervention_strategy)

        assets = read_assets()
        links = read_links()
        parameters = read_parameters()

        for year in TIMESTEPS:
            print("-", year)

            # Decide on new interventions
            budget = ANNUAL_BUDGET
            service_obligation_capacity = SERVICE_OBLIGATION_CAPACITY

            # simulate first
            if year == BASE_YEAR:
                system = fixed_model.ICTManager(assets, links, parameters)

            # decide
            interventions_built, budget, spend = fixed_interventions.decide_interventions(intervention_strategy, budget, service_obligation_capacity, system, year)