"""
Test Mobile Network model.py
11th May 2019
Written by Edward J. Oughton

"""
from digital_comms.mobile_network.model import (
    NetworkManager, LAD, PostcodeSector
    )

class TestNetworkManager():

    def test_create(self, setup_lad, setup_pcd_sector, setup_assets,
                    setup_capacity_lookup, setup_clutter_lookup,
                    setup_service_obligation_capacity,
                    setup_traffic, setup_market_share):

        Manager = NetworkManager(setup_lad, setup_pcd_sector, setup_assets,
            setup_capacity_lookup, setup_clutter_lookup,
            setup_service_obligation_capacity,
            setup_traffic, setup_market_share)

class TestLAD():

    def test_create(self, setup_lad, setup_service_obligation_capacity):

        testLAD = LAD(setup_lad[0], setup_service_obligation_capacity)

        assert testLAD.id == setup_lad[0]['id']
        assert testLAD.name == setup_lad[0]['name']

    def test_property_population(self, setup_lad, setup_pcd_sector,
        setup_assets, setup_capacity_lookup, setup_clutter_lookup,
        setup_service_obligation_capacity, setup_traffic,
        setup_market_share):

        testLAD = LAD(setup_lad[0], setup_service_obligation_capacity)

        # No postcode sectors
        testPopulation = testLAD.population
        assert testPopulation == 0

        # Create a PostcodeSector with a population of 500
        testPostcode = PostcodeSector(setup_pcd_sector[0], setup_assets,
            setup_capacity_lookup, setup_clutter_lookup,
            setup_service_obligation_capacity,
            setup_traffic, setup_market_share)

        #test pcd_sector capacity
        assert round(testPostcode.capacity,2) == 1.83

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
            setup_traffic, setup_market_share)

        assert round(testPostcode.capacity,2) == 1.83

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
        assert round(testCapacity,2) == 1.83

        #test lad demand
        #2.28 = 1.14*2
        #0.92 = 0.46*2
        #0.8 = (2.28+0.92)/(2+2)
        testDemand = round(testLAD.demand(),2)
        assert testDemand == 0.8

        testCoverage = testLAD.coverage()
        assert testCoverage == 0



# MANAGER = NetworkManager(LADS, PCD_SECTORS, ASSETS, CAPACITY_LOOKUP,
#     CLUTTER_LOOKUP, SERVICE_OBLIGATION_CAPACITY, TRAFFIC, MARKET_SHARE)

# for lad in MANAGER.lads.values():
#     pprint(lad)
#     for pcd in lad._pcd_sectors.values():
#         print(" ", pcd, "capacity:{:.2f} demand:{:.2f}".format(
#             pcd.capacity, pcd.demand
#             ))
