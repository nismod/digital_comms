"""Cambridge Communications Assessment Model Test
"""

from digital_comms.mobile_model.mobile_model import ICTManager, LAD, PostcodeSector

class TestICTManager():

    def test_create(self, setup_lad, setup_pcd_sector, setup_assets,
                    setup_capacity_lookup, setup_clutter_lookup):

        Manager = ICTManager(setup_lad, setup_pcd_sector, setup_assets,
                             setup_capacity_lookup, setup_clutter_lookup)

class TestLAD():

    def test_create(self, setup_lad):

        testLAD = LAD(setup_lad[0])

        assert testLAD.id == setup_lad[0]['id']
        assert testLAD.name == setup_lad[0]['name']

    def test_property_population(self, setup_lad, setup_pcd_sector, setup_assets, setup_capacity_lookup, setup_clutter_lookup):

        testLAD = LAD(setup_lad[0])

        # No postcode sectors
        testPopulation = testLAD.population
        assert testPopulation == 0

        # Create a PostcodeSector with a population of 500
        testPostcode = PostcodeSector(setup_pcd_sector[0], setup_assets, setup_capacity_lookup, setup_clutter_lookup)
        testLAD.add_pcd_sector(testPostcode)

        testPopulation = testLAD.population
        assert testPopulation == 500

        # Create a PostcodeSector with a population of 700
        testPostcode = PostcodeSector(setup_pcd_sector[1], setup_assets, setup_capacity_lookup, setup_clutter_lookup)
        testLAD.add_pcd_sector(testPostcode)

        testPopulation = testLAD.population
        assert testPopulation == 700



