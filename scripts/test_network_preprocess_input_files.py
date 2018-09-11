from pytest import fixture
import osmnx as ox
import numpy as np

from .network_preprocess_input_files import *

@fixture
def street_graph():
    point = (52.180918, 0.093319)  # center  lat,lng
    return ox.graph_from_point(point, distance=500, network_type='all')


def test_snap_point_to_graph(street_graph):
    x, y = (0.094239, 52.182635)
    expected_x, expected_y = (0.094062, 52.182691)
    actual_x, actual_y = snap_point_to_graph(x, y, street_graph)

    actual = np.array([actual_x, actual_y])
    expected = np.array([expected_x, expected_y])
    print("Actual:", actual)
    print("Expected:", expected)
    np.testing.assert_allclose(actual, expected, rtol=1e-04)
