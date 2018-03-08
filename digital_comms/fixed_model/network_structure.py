import networkx as nx
import fiona
import os
import itertools

from shapely.geometry import LineString, Point, mapping
from collections import OrderedDict

class ICTManager():

    """
    Attributes
    ----------
    length : num
        Total length of links in the network
    """
    def __init__(self, shapefiles=None):
        """Build the initial network using shapefiles as input

        Parameters
        ----------
        shapefiles: str (optional)
            Path to directory containing shapefiles
        """
        self._network = nx.Graph()

        if shapefiles != None:
            self.load_shapefiles(shapefiles)

    def load_shapefiles(self, shapefiles_dir):
        """Build infrastructure defined in shapefiles

        Parameters
        ----------
        shapefiles_dir: 
            Path to directory containing shapefiles
        """
        for filename in os.listdir(shapefiles_dir):
            if filename.endswith(".shp"): 
                with fiona.open(os.path.join(shapefiles_dir, filename), 'r') as source:
                    for c in source:
                        self.build_infrastructure(c['geometry']['coordinates'], dict(c['properties']))    
    @property
    def number_of_nodes(self):
        return nx.number_of_nodes(self._network)

    @property
    def number_of_edges(self):
        return nx.number_of_edges(self._network)

    @property
    def length(self):
        total_length = 0
        for (origin, dest, edge) in list(self._network.edges.data('object')):
            total_length += edge.length
        return total_length

    def build_infrastructure(self, geom, props):
        """Build infrastructure in the network

        Parameters
        ----------
        geom: tuple, array of tuple
            The geometric representation of the infrastructure
        props: dict
            The properties that belong to this infrastructure type

        Raises
        ------
        NotImplementedError
            When the infrastructure types does not exist
        """
        if props['Type'] == 'premise':
            self._network.add_node(props['Name'], object=PremiseNode(geom, props))
        elif props['Type'] == 'dps':
            self._network.add_node(props['Name'], object=DpsNode(geom, props))
        elif props['Type'] == 'pcp':
            self._network.add_node(props['Name'], object=PcpNode(geom, props))
        elif props['Type'] == 'exchange':
            self._network.add_node(props['Name'], object=ExchangeNode(geom, props))
        elif props['Type'] == 'core':
            self._network.add_node(props['Name'], object=CoreNode(geom, props))
        elif props['Type'] == 'link':
            self._network.add_edge(props['Origin'], props['Dest'], object=Link(geom, props))
        else:
            raise NotImplementedError('Node or Link Type ' + c['properties']['Type'] + ' does not exist')

    def save(self, directory):
        """Save the current state of the network in a set of shapefile

        Parameters
        ----------
        directory: str 
            Path to directory where shapefiles are saved
        """
        sink_driver = 'ESRI Shapefile'
        sink_crs = {'no_defs': True, 'ellps': 'WGS84', 'datum': 'WGS84', 'proj': 'longlat'}

        # Create lists of geometry elemtents by node type
        geom_list = {}

        for node_id, node in list(self._network.nodes('object')):
            if node != None:
                geom_list.setdefault(str(type(node)),[]).append(node)

        for origin, dest in list(self._network.edges()):
            link_obj = self._network[origin][dest]['object']
            geom_list.setdefault(str(type(link_obj)),[]).append(link_obj)
        
        # Write nodes to output
        for key in geom_list.keys():

            # Translate props to Fiona sink schema
            prop_schema = []
            for name, value in geom_list[key][0].props.items():
                fiona_prop_type = next((fiona_type for fiona_type, python_type in fiona.FIELD_TYPES_MAP.items() if python_type == type(value)), None)
                prop_schema.append((name, fiona_prop_type))

            sink_schema = {
                'geometry': geom_list[key][0].geom.type,
                'properties': OrderedDict(prop_schema)
            }

            # Write all elements to output file
            with fiona.open(os.path.join(directory, key[8:-2] + '.shp'), 'w', driver=sink_driver, crs=sink_crs, schema=sink_schema) as sink:
                for node in geom_list[key]:
                    sink.write({
                        'geometry': mapping(node.geom),
                        'properties': OrderedDict(node.props)
                    })

class Node():

    def __init__(self, geom, props):
        self.name = props['Name']
        self.geom = Point(geom)
        self.props = props

    def calc_pcps_served(self):
        #print('hello')

        for link in self._links:
            print(type(link))

class PremiseNode(Node):

    @property
    def node_type():
        return 'premise'

class DpsNode(Node):

    @property
    def node_type():
        return 'dps'

class PcpNode(Node):

    @property
    def node_type():
        return 'pcp'

class ExchangeNode(Node):

    @property
    def node_type():
        return 'exchange'

class CoreNode(Node):
    
    @property
    def node_type():
        return 'core'

class Link():

    def __init__(self, geom, props):
        self.id = id
        self.geom = LineString(geom)
        self.props = props

    @property
    def length(self):
        return LineString(self.geom).length
