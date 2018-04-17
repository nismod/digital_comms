from digital_comms.models import fixed_model
import fiona
import os

def read_shapefile(file):
    with fiona.open(file, 'r') as source:
        return [f['properties'] for f in source]

if __name__ == "__main__":

    print('Read shapefiles')
    premises = read_shapefile(os.path.join('data', 'processed', 'assets_layer5_premises.shp'))
    distributions = read_shapefile(os.path.join('data', 'processed', 'assets_layer4_distributions.shp'))
    cabinets = read_shapefile(os.path.join('data', 'processed', 'assets_layer3_cabinets.shp'))
    exchanges = read_shapefile(os.path.join('data', 'processed', 'assets_layer2_exchanges.shp'))

    links = []
    links.extend(read_shapefile(os.path.join('data', 'processed', 'links_layer5_premises.shp')))
    links.extend(read_shapefile(os.path.join('data', 'processed', 'links_layer4_distributions.shp')))
    links.extend(read_shapefile(os.path.join('data', 'processed', 'links_layer3_cabinets.shp')))
    
    print('Initialise model')
    my_fixed_model = fixed_model.ICTManager(exchanges, cabinets, distributions, premises, links)

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
    print('Number of dist_to_prem links: ' + str(my_fixed_model.number_of_links['dist_to_prem']))
    print('Number of cab_to_dist links: ' + str(my_fixed_model.number_of_links['cab_to_dist']))
    print('Number of ex_to_cab links: ' + str(my_fixed_model.number_of_links['ex_to_cab']))

    print('<properties')
    print('Average length of dist_to_prem links: ' + str(my_fixed_model.avg_link_length['dist_to_prem']))
    print('Average length of cab_to_dist links: ' + str(my_fixed_model.avg_link_length['cab_to_dist']))
    print('Average length of ex_to_cab links: ' + str(my_fixed_model.avg_link_length['ex_to_cab']))