from digital_comms.fixed_model.network_structure import ICTManager, Pcp, Exchange, Link
from shapely.geometry import Point, LineString

class TestICTManager():

    def test_create(self, setup_fixed_model_pcp, setup_fixed_model_exchanges, setup_fixed_model_links):

        empty_data = {}

        Manager = ICTManager(empty_data, empty_data, setup_fixed_model_pcp,
                             setup_fixed_model_exchanges, empty_data,
                             setup_fixed_model_links)

class TestNode():

    def test_create(self):

        node_name = "Node name"
        node_geometry = Point(0.123, 0.456)

        myNode = Pcp((node_name, node_geometry))

        assert myNode.name == node_name
        assert myNode.geom == node_geometry

    def test_calc_pcps_served(self, setup_fixed_network):
        manager = setup_fixed_network

        assert manager.calc_pcps_served('EAARR') == 2

class TestLink():

    def test_create(self):

        link_name = "Link name"
        link_geometry = LineString([(0.123, 0.456), (0.789, 0.1011)])

        link_node_a_name = "Node_a name"
        link_node_a_geom = Point((0.123, 0.456))
        link_node_a = Pcp((link_node_a_name, link_node_a_geom))

        link_node_b_name = "Node_b name"
        link_node_b_geom = Point((0.789, 0.101))
        link_node_b = Pcp((link_node_b_name, link_node_b_geom))

        myLink = Link(link_geometry, link_node_a, link_node_b)

        assert myLink.geom == link_geometry
        assert myLink._node_a == link_node_a
        assert myLink._node_b == link_node_b








