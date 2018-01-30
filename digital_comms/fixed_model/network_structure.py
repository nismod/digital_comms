import networkx as nx
import fiona
import os
import itertools

from shapely.geometry import LineString, Point, mapping

from collections import OrderedDict

class ICTManager():

    def __init__(self, shapefiles):

        self._network = nx.Graph()

        for filename in os.listdir(shapefiles):
            if filename.endswith(".shp"): 
                with fiona.open(os.path.join(shapefiles, filename), 'r') as source:
                    for c in source:
                        if   (c['properties']['Type'] == 'premise'):
                            self.add_premise(c['geometry']['coordinates'], dict(c['properties']))
                        elif (c['properties']['Type'] == 'dps'):
                            self.add_dps(c['geometry']['coordinates'], dict(c['properties']))
                        elif (c['properties']['Type'] == 'pcp'):
                            self.add_pcp(c['geometry']['coordinates'], dict(c['properties']))
                        elif (c['properties']['Type'] == 'exchange'):
                            self.add_exchange(c['geometry']['coordinates'], dict(c['properties']))
                        elif (c['properties']['Type'] == 'core'):
                            self.add_corenode(c['geometry']['coordinates'], dict(c['properties']))
                        elif (c['properties']['Type'] == 'link'):
                            self.add_link(c['geometry']['coordinates'], dict(c['properties']))
                        else:
                            raise Exception('Node or Link Type ' + c['properties']['Type'] + ' is not defined')

    @property
    def length(self):
        total_length = 0
        for (origin, dest, edge) in list(self._network.edges.data('object')):
            total_length += edge.length
        return total_length

    def add_premise(self, geom, props):
        self._network.add_node(props['Name'], object=PremiseNode(geom, props))

    def add_dps(self, geom, props):
        self._network.add_node(props['Name'], object=DpsNode(geom, props))

    def add_pcp(self, geom, props):
        self._network.add_node(props['Name'], object=PcpNode(geom, props))

    def add_exchange(self, geom, props):
        self._network.add_node(props['Name'], object=ExchangeNode(geom, props))

    def add_corenode(self, geom, props):
        self._network.add_node(props['Name'], object=CoreNode(geom, props))

    def add_link(self, geom, props):
        self._network.add_edge(props['Origin'], props['Dest'], object=Link(geom, props))

    def calc_pcps_served(self, NodeId):
        return self._nodes[NodeId].calc_pcps_served()

    def save(self, directory):

        sink_driver = 'ESRI Shapefile'
        sink_crs = {'no_defs': True, 'ellps': 'WGS84', 'datum': 'WGS84', 'proj': 'longlat'}

        # Create lists of geometry elemtents by node type
        geom_list = {}

        for node_id, node in list(self._network.nodes('object')):
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
