from digital_comms.fixed_model import fixed_model
import fiona
from operator import attrgetter
import os

def read_shapefile(file):
    with fiona.open(file, 'r') as source:
        return [f['properties'] for f in source]

if __name__ == "__main__":

    print('Read shapefiles')
    assets = {}
    assets['premises'] = read_shapefile(os.path.join('data', 'processed', 'assets_layer5_premises.shp'))
    assets['distributions'] = read_shapefile(os.path.join('data', 'processed', 'assets_layer4_distributions.shp'))
    assets['cabinets'] = read_shapefile(os.path.join('data', 'processed', 'assets_layer3_cabinets.shp'))
    assets['exchanges'] = read_shapefile(os.path.join('data', 'processed', 'assets_layer2_exchanges.shp'))
    
    links = []
    links.extend(read_shapefile(os.path.join('data', 'processed', 'links_layer5_premises.shp')))
    links.extend(read_shapefile(os.path.join('data', 'processed', 'links_layer4_distributions.shp')))
    links.extend(read_shapefile(os.path.join('data', 'processed', 'links_layer3_cabinets.shp')))

    # Initialise parameter
    parameters = {
        'costs_links_fiber_meter': 5,
        'costs_links_copper_meter': 3,
        'costs_assets_exchange_fttp': 50000,
        'costs_assets_exchange_gfast': 40000,
        'costs_assets_exchange_fttc': 30000,
        'costs_assets_exchange_adsl': 20000,
        'costs_assets_cabinet_fttp_32_ports': 10,
        'costs_assets_cabinet_gfast': 4000,
        'costs_assets_cabinet_fttc': 3000,
        'costs_assets_cabinet_adsl': 2000,
        'costs_assets_distribution_fttp_32_ports': 10,
        'costs_assets_distribution_gfast_4_ports': 1500,
        'costs_assets_distribution_fttc': 300,
        'costs_assets_distribution_adsl': 200,
        'costs_assets_premise_fttp_modem': 20,
        'costs_assets_premise_fttp_optical_network_terminator': 10,
        'costs_assets_premise_gfast_modem': 20,
        'costs_assets_premise_fttc_modem': 15,
        'costs_assets_premise_adsl_modem': 10,
        'benefits_assets_premise_fttp': 50,
        'benefits_assets_premise_gfast': 40,
        'benefits_assets_premise_fttc': 30,
        'benefits_assets_premise_adsl': 20,
    }

    print('Initialise model')
    my_fixed_model = fixed_model.ICTManager(assets, links, parameters)

    print('--Statistics--')
    print('<assets>')
    print('Number of premises: ' + str(my_fixed_model.number_of_assets['premises']))
    print('Number of distributions: ' + str(my_fixed_model.number_of_assets['distributions']))
    print('Number of cabinets: ' + str(my_fixed_model.number_of_assets['cabinets']))
    print('Number of exchanges: ' + str(my_fixed_model.number_of_assets['exchanges']))

    print('<links>')
    print('Number of premises links: ' + str(my_fixed_model.number_of_links['premises']))
    print('Number of distributions links: ' + str(my_fixed_model.number_of_links['distributions']))
    print('Number of cabinets links: ' + str(my_fixed_model.number_of_links['cabinets']))
    print('Number of exchanges links: ' + str(my_fixed_model.number_of_links['exchanges']))

    print('--Analysis example--')
    print('<costs>')
    max_exchange_rollout_costs_fttp = max(my_fixed_model.assets['exchanges'], key=lambda x:x.rollout_costs['fttp'])
    print('Most expensive exchange for FTTP rollout: ' + max_exchange_rollout_costs_fttp.id)
    max_cabinet_rollout_costs_fttp = max(my_fixed_model.assets['cabinets'], key=lambda x:x.rollout_costs['fttp'])
    print('Most expensive cabinet for FTTP rollout: ' + max_cabinet_rollout_costs_fttp.id)
    max_distribution_rollout_costs_fttp = max(my_fixed_model.assets['distributions'], key=lambda x:x.rollout_costs['fttp'])
    print('Most expensive distribution for FTTP rollout: ' + max_distribution_rollout_costs_fttp.id)
    max_premise_rollout_costs_fttp = max(my_fixed_model.assets['premises'], key=lambda x:x.rollout_costs['fttp'])
    print('Most expensive premise for FTTP rollout: ' + max_premise_rollout_costs_fttp.id)

    print('<benefits>')
    max_exchange_rollout_benefits_fttp = max(my_fixed_model.assets['exchanges'], key=lambda x:x.rollout_benefits['fttp'])
    print('Most benefitial exchange for FTTP rollout: ' + max_exchange_rollout_benefits_fttp.id)
    max_cabinet_rollout_benefits_fttp = max(my_fixed_model.assets['cabinets'], key=lambda x:x.rollout_benefits['fttp'])
    print('Most benefitial cabinet for FTTP rollout: ' + max_cabinet_rollout_benefits_fttp.id)
    max_distribution_rollout_benefits_fttp = max(my_fixed_model.assets['distributions'], key=lambda x:x.rollout_benefits['fttp'])
    print('Most benefitial distribution for FTTP rollout: ' + max_distribution_rollout_benefits_fttp.id)
    max_premise_rollout_benefits_fttp = max(my_fixed_model.assets['premises'], key=lambda x:x.rollout_benefits['fttp'])
    print('Most benefitial premise for FTTP rollout: ' + max_premise_rollout_benefits_fttp.id)

    print('<benefit-costs-ratio>')
    max_exchange_rollout_bcr_fttp = max(my_fixed_model.assets['exchanges'], key=lambda x:x.rollout_bcr['fttp'])
    print('Best benefit-costs-ratio exchange for FTTP rollout: ' + max_exchange_rollout_bcr_fttp.id)
    max_cabinet_rollout_bcr_fttp = max(my_fixed_model.assets['cabinets'], key=lambda x:x.rollout_bcr['fttp'])
    print('Best benefit-costs-ratio cabinet for FTTP rollout: ' + max_cabinet_rollout_bcr_fttp.id)
    max_distribution_rollout_bcr_fttp = max(my_fixed_model.assets['distributions'], key=lambda x:x.rollout_bcr['fttp'])
    print('Best benefit-costs-ratio distribution for FTTP rollout: ' + max_distribution_rollout_bcr_fttp.id)
    max_premise_rollout_bcr_fttp = max(my_fixed_model.assets['premises'], key=lambda x:x.rollout_bcr['fttp'])
    print('Best benefit-costs-ratio premise for FTTP rollout: ' + max_premise_rollout_bcr_fttp.id)