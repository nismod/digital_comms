import os
from itertools import chain
from pprint import pprint

import pytest

from digital_comms.fixed_model.fixed_model import ICTManager


class TestICTManager():

    @pytest.mark.skip(reason="ICTManager has required arguments (pcd_sectors etc.)")
    def test_init(self):
        """Verify if ICTManager initialises"""
        Manager = ICTManager()

        assert Manager.number_of_nodes == 0
        assert Manager.number_of_edges == 0

    @pytest.mark.skip(reason="ICTManager requires data, not file path")
    def test_init_shapefiles(self):
        """Verify if ICTManager initialises with shapefiles"""
        Manager = ICTManager(os.path.join('tests', 'fixed_model', 'fixtures', 'initial_system'))

        assert Manager.number_of_nodes > 0
        assert Manager.number_of_edges > 0

    @pytest.mark.skip(reason="ICTManager has required arguments (pcd_sectors etc.)")
    def test_build_infrastructure(self, setup_fixed_model_pcp, setup_fixed_model_exchanges, setup_fixed_model_links):
        """Verify that infrastructure can be built"""
        Manager = ICTManager()

        # Build nodes
        for geom, props in setup_fixed_model_pcp:
            Manager.build_infrastructure(geom, props)
        assert Manager.number_of_nodes == len(setup_fixed_model_pcp)

        for geom, props in setup_fixed_model_exchanges:
            Manager.build_infrastructure(geom, props)
        assert Manager.number_of_nodes == (len(setup_fixed_model_pcp) + len(setup_fixed_model_exchanges))

        # Build edges
        for geom, props in setup_fixed_model_links:
            Manager.build_infrastructure(geom, props)
        assert Manager.number_of_edges == len(setup_fixed_model_links)

    @pytest.mark.skip(reason="ICTManager has required arguments (pcd_sectors etc.)")
    def test_save(self, tmpdir, setup_fixed_model_pcp, setup_fixed_model_exchanges, setup_fixed_model_links):
        """Verify that shapefiles are correctly saved"""
        Manager = ICTManager()

        for geom, props in chain(setup_fixed_model_pcp, setup_fixed_model_exchanges, setup_fixed_model_links):
            Manager.build_infrastructure(geom, props)

        print(Manager.number_of_nodes)
        print(Manager.number_of_edges)

        Manager.save(tmpdir)
        Manager2 = ICTManager(tmpdir)

        pprint(sorted(Manager._network.edges()))
        pprint(sorted(Manager2._network.edges()))

        assert sorted(Manager._network.nodes()) == sorted(Manager2._network.nodes())
        assert sorted(Manager._network.edges()) == sorted(Manager2._network.edges())


# class TestNode():

#     def test_create(self):

#         node_name = "Node name"
#         node_geometry = Point(0.123, 0.456)

#         myNode = Pcp((node_name, node_geometry))

#         assert myNode.name == node_name
#         assert myNode.geom == node_geometry

#     def test_calc_pcps_served(self, setup_fixed_network):
#         manager = setup_fixed_network

#         assert manager.calc_pcps_served('EAARR') == 2

# class TestLink():

#     def test_create(self):

#         link_name = "Link name"
#         link_geometry = LineString([(0.123, 0.456), (0.789, 0.1011)])

#         link_node_a_name = "Node_a name"
#         link_node_a_geom = Point((0.123, 0.456))
#         link_node_a = Pcp((link_node_a_name, link_node_a_geom))

#         link_node_b_name = "Node_b name"
#         link_node_b_geom = Point((0.789, 0.101))
#         link_node_b = Pcp((link_node_b_name, link_node_b_geom))

#         myLink = Link(link_geometry, link_node_a, link_node_b)

#         assert myLink.geom == link_geometry
#         assert myLink._node_a == link_node_a
#         assert myLink._node_b == link_node_b
