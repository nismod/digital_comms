"""
Test Mobile Network model.py
11th May 2019
Written by Edward J. Oughton

"""
import pytest

from digital_comms.mobile_network.model import (
    NetworkManager, LAD, PostcodeSector,
    lookup_clutter_geotype, lookup_capacity,
    interpolate, find_frequency_bandwidth
    )


class TestNetworkManager():

    def test_create(self, setup_lad, setup_pcd_sector, setup_assets,
                    setup_capacity_lookup, setup_clutter_lookup,
                    setup_simulation_parameters):

        Manager = NetworkManager(setup_lad, setup_pcd_sector, setup_assets,
            setup_capacity_lookup, setup_clutter_lookup,
            setup_simulation_parameters)


class TestLAD():

    def test_create(self, setup_lad, setup_simulation_parameters):

        testLAD = LAD(setup_lad[0],
            setup_simulation_parameters
        )

        assert testLAD.id == setup_lad[0]['id']
        assert testLAD.name == setup_lad[0]['name']

    def test_property_population(self, setup_lad, setup_pcd_sector,
        setup_assets, setup_capacity_lookup,
        setup_clutter_lookup, setup_simulation_parameters):

        testLAD = LAD(setup_lad[0],
            setup_simulation_parameters
        )

        # No postcode sectors
        testPopulation = testLAD.population
        assert testPopulation == 0

        # Create a PostcodeSector with a population of 500
        testPostcode = PostcodeSector(setup_pcd_sector[0], setup_assets,
            setup_capacity_lookup, setup_clutter_lookup,
            setup_simulation_parameters)

        #test pcd_sector capacity
        assert round(testPostcode.capacity, 2) == 4

        #test pcd_sector demand
        testDemand = round(testPostcode.demand,2)
        assert round(testDemand, 2) == 1.14

        testLAD.add_pcd_sector(testPostcode)

        testPopulation = testLAD.population
        assert testPopulation == 500

        # Create a PostcodeSector with a population of 700
        testPostcode = PostcodeSector(setup_pcd_sector[1], setup_assets,
            setup_capacity_lookup, setup_clutter_lookup,
            setup_simulation_parameters)

        assert round(testPostcode.capacity,2) == 4

        #test pcd_sector demand
        testDemand = round(testPostcode.demand,2)
        assert testDemand == 0.46

        testLAD.add_pcd_sector(testPostcode)

        testPopulation = testLAD.population
        assert testPopulation == 700

        testPopDensity = testLAD.population_density
        assert testPopDensity == 175

        testCapacity = testLAD.capacity()
        assert round(testCapacity,2) == 4

        #test lad demand
        testDemand = round(testLAD.demand(),2)
        assert testDemand == 0.8

        testCoverage = testLAD.coverage(setup_simulation_parameters)
        assert testCoverage == 1


class TestPostcode():

    def test_capacity(self, setup_lad, setup_pcd_sector,
        setup_assets,setup_capacity_lookup, setup_clutter_lookup,
        setup_simulation_parameters):

        testLAD = LAD(setup_lad[0], setup_simulation_parameters)

        testPostcode = PostcodeSector(setup_pcd_sector[0], setup_assets,
            setup_capacity_lookup, setup_clutter_lookup,
            setup_simulation_parameters)

        #test pcd_sector capacity
        assert round(testPostcode.capacity, 2) == 4

        testLAD.add_pcd_sector(testPostcode)

        testPostcode = PostcodeSector(setup_pcd_sector[1], setup_assets,
            setup_capacity_lookup, setup_clutter_lookup,
            setup_simulation_parameters)

        #test pcd_sector capacity
        assert round(testPostcode.capacity, 2) == 4

        testLAD.add_pcd_sector(testPostcode)

        testCapacity = testLAD.capacity()

        assert round(testCapacity,2) == 4


def test_lookup_clutter_geotype():

    clutter_lookup = [
        (0.0, 'rural'),
        (782.0, 'suburban'),
        (7959.0, 'urban'),
    ]

    population_density = 200

    actual_result = lookup_clutter_geotype(clutter_lookup, population_density)

    assert actual_result == 'rural'

    population_density = 1000

    actual_result = lookup_clutter_geotype(clutter_lookup, population_density)

    assert actual_result == 'suburban'

    population_density = 10000

    actual_result = lookup_clutter_geotype(clutter_lookup, population_density)

    assert actual_result == 'urban'


def test_lookup_capacity(setup_capacity_lookup):

    with pytest.raises(KeyError):
        lookup_capacity(setup_capacity_lookup,
            'rural', '100', '50', '2')


def test_interpolate():

    x0 = 10
    y0 = 20
    x1 = 20
    y1 = 40
    x = 15

    answer = interpolate(x0, y0, x1, y1, x)

    assert answer == 30

    answer = interpolate(x0, y0, x1, y1, 30)

    assert answer == 60

def test_find_frequency_bandwidth(setup_simulation_parameters):

    with pytest.raises(KeyError, match='channel_bandwidth_1000'):
        find_frequency_bandwidth(1000, setup_simulation_parameters)
