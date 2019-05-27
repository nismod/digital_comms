"""
Test Mobile Network model.py
11th May 2019
Written by Edward J. Oughton

"""
import pytest
from digital_comms.mobile_network.model import (
    NetworkManager, LAD, PostcodeSector,
    lookup_clutter_geotype, lookup_capacity
    )

class TestNetworkManager():

    def test_create(self, setup_lad, setup_pcd_sector, setup_assets,
                    setup_capacity_lookup, setup_clutter_lookup,
                    setup_service_obligation_capacity,
                    setup_traffic, setup_market_share, setup_mast_height):

        Manager = NetworkManager(setup_lad, setup_pcd_sector, setup_assets,
            setup_capacity_lookup, setup_clutter_lookup,
            setup_service_obligation_capacity,
            setup_traffic, setup_market_share, setup_mast_height)

class TestLAD():

    def test_create(self, setup_lad, setup_service_obligation_capacity):

        testLAD = LAD(setup_lad[0], setup_service_obligation_capacity)

        assert testLAD.id == setup_lad[0]['id']
        assert testLAD.name == setup_lad[0]['name']

    def test_property_population(self, setup_lad, setup_pcd_sector,
        setup_assets, setup_capacity_lookup,
        setup_clutter_lookup, setup_service_obligation_capacity,
        setup_traffic, setup_market_share, setup_mast_height):

        testLAD = LAD(setup_lad[0], setup_service_obligation_capacity)

        # No postcode sectors
        testPopulation = testLAD.population
        assert testPopulation == 0

        # Create a PostcodeSector with a population of 500
        testPostcode = PostcodeSector(setup_pcd_sector[0], setup_assets,
            setup_capacity_lookup, setup_clutter_lookup,
            setup_service_obligation_capacity,
            setup_traffic, setup_market_share, setup_mast_height)

        #test pcd_sector capacity
        assert round(testPostcode.capacity,2) == 4

        #test pcd_sector demand
        testDemand = round(testPostcode.demand,2)
        assert testDemand == 1.14

        testLAD.add_pcd_sector(testPostcode)

        testPopulation = testLAD.population
        assert testPopulation == 500

        # Create a PostcodeSector with a population of 700
        testPostcode = PostcodeSector(setup_pcd_sector[1], setup_assets,
            setup_capacity_lookup, setup_clutter_lookup,
            setup_service_obligation_capacity,
            setup_traffic, setup_market_share, setup_mast_height)

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
        #CB11, 800+2600MHz, density of 0.5 sites per km^2
        # Capacity is 1km^2 + 0.83km^2 = 1.83Mbps/km2
        #CB12 is the same, so (1.83+1.83)/2 = 1.83Mbps/km2 average capacity
        assert round(testCapacity,2) == 4

        #test lad demand
        #2.28 = 1.14*2
        #0.92 = 0.46*2
        #0.8 = (2.28+0.92)/(2+2)
        testDemand = round(testLAD.demand(),2)
        assert testDemand == 0.8

        testCoverage = testLAD.coverage()
        assert testCoverage == 1

class TestPostcode():

    def test_capacity(self, setup_lad, setup_pcd_sector,
        setup_six_sectored_assets,
        setup_capacity_lookup, setup_clutter_lookup,
        setup_service_obligation_capacity,
        setup_traffic, setup_market_share, setup_mast_height):

        testLAD = LAD(setup_lad[0], setup_service_obligation_capacity)

        testPostcode = PostcodeSector(setup_pcd_sector[0],
            setup_six_sectored_assets,
            setup_capacity_lookup, setup_clutter_lookup,
            setup_service_obligation_capacity,
            setup_traffic, setup_market_share, setup_mast_height)

        #test pcd_sector capacity
        assert round(testPostcode.capacity, 2) == 8

        testLAD.add_pcd_sector(testPostcode)

        testPostcode = PostcodeSector(setup_pcd_sector[1],
            setup_six_sectored_assets,
            setup_capacity_lookup, setup_clutter_lookup,
            setup_service_obligation_capacity,
            setup_traffic, setup_market_share, setup_mast_height)

        #test pcd_sector capacity
        assert round(testPostcode.capacity, 2) == 8

        testLAD.add_pcd_sector(testPostcode)

        testCapacity = testLAD.capacity()
        print(testCapacity)
        #LAD area = 2km^2
        #cells = 1 x site w/6 cells
        #(effectively classed as 2 sites as 3 sectors are assumed in LUT)
        #density 2 sites per km^2 = 3 cells per km^2
        assert round(testCapacity,2) == 8#8

def test_lookup_clutter_geotype():

    clutter_lookup = [
        (0.0, 'Rural'),
        (782.0, 'Suburban'),
        (7959.0, 'Urban'),
    ]

    population_density = 200

    actual_result = lookup_clutter_geotype(clutter_lookup, population_density)

    assert actual_result == 'Rural'

    population_density = 1000

    actual_result = lookup_clutter_geotype(clutter_lookup, population_density)

    assert actual_result == 'Suburban'

    population_density = 10000

    actual_result = lookup_clutter_geotype(clutter_lookup, population_density)

    assert actual_result == 'Urban'

def test_lookup_capacity(setup_capacity_lookup):

    with pytest.raises(KeyError):
        lookup_capacity(setup_capacity_lookup,
            'rural', '800', '10', '2', '30')
