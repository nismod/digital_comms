from pprint import pprint

class Exchange(object):
    """ Defines a generic exchange.
    Arguments
    ---------
    data: dict
    """
    def __init__(self, data, cabinets, dist_points, buildings):
        self.id = data["id"]
        self.exchange_type = data["exchange_type"]
        self.cabinets_per_exchange = data["cabinets_per_exchange"]
        self.lines_per_exchange = data["lines_per_exchange"]
        self.cable_type = data["cable_type"]
        self.cable_length = data["cable_length"]
        self.cable_count = data["cable_count"]

        self.cabinets = {}

        for cabinet in cabinets:
            cabinet_id = cabinet["id"]
            self.cabinets[cabinet["id"]] = Cabinet(cabinet, dist_points, buildings)

    def __repr__(self):
        return "<cabinets:{}>".format(self.cabinets)

    def population(self):

        if not self.cabinets:
            return 0

        summed_occupants = sum(
            self.cabinets[cabinet].population()
            for cabinet in self.cabinets
        )

        return summed_occupants

class Cabinet(object):
    """ Defines a generic street cabinet.
    Arguments
    ---------
    data: dict
    """
    def __init__ (self, data, dist_points, buildings):
        self.id = data["id"]
        self.cabinet_type = data["cabinet_type"]
        self.lines_per_cabinet = data["lines_per_cabinet"]
        self.cable_type = data["cable_type"]
        self.cable_length = data["cable_length"]
        self.cable_count = data["cable_count"]

        self.dist_points = {}

        for dist_point in dist_points:
            dist_point_id = dist_point["id"]
            self.dist_points[dist_point["id"]] = DistributionPoint(dist_point, buildings) # don't understand singular vs plural here

    def __repr__(self):
        return "<dist_points:{}>".format(self.dist_points)

    def population(self):

        if not self.dist_points:
            return 0

        summed_occupants = sum(
            self.dist_points[dist_point].population()
            for dist_point in self.dist_points
        )

        return summed_occupants

class DistributionPoint(object):
    """Represents a Distribution Point to be modelled
    Arguments
    ---------
    data: dict
    """
    def __init__(self, data, buildings):
        self.id = data["id"]
        self.cabinet = data["cabinet"]
        self.dist_point_type = data["dist_point_type"]
        self.dist_point_location = data["dist_point_location"]
        self.cable_type = data["cable_type"]
        self.cable_length = data["cable_length"]
        self.cable_count = data["cable_count"]

        self.buildings = {}

        for building in buildings:
            if building["dist_point"] == self.id:
                building_id = building["id"]
                self.buildings[building["id"]] = Building(building)

    def population(self):
        """Calculate population as the sum of occupantsfrom all buildings
        Returns
        -------
        obj
            population of the buildings served by the distribution point
        Notes
        -----
        Function returns `0` when no buildings are served.
        """
        if not self.buildings:
            return 0

        summed_occupants = sum(
            self.buildings[building].occupants
            for building in self.buildings
        )

        print(summed_occupants)
        return summed_occupants

class Building(object):
    """ Represents a Building to be modelled
    Arguments
    ---------
    data: dict
    """
    def __init__(self, data):
        self.id = data["id"]
        self.oa = data["oa"]
        self.dist_point = data["dist_point"]
        self.cable_type = data["cable_type"]
        self.cable_length = data["cable_length"]
        self.cable_count = data["cable_count"]
        self.residential_buildings = data["residential address count"]
        self.non_residential_buildings = data["non-residential address count"]
        self.occupants = data["occupants"]

    def __repr__(self):
        return "<Premised id:{} oa_id:{} occupants:{}>".format(self.id, self.oa, self.occupants)

# __name__ == '__main__' means that the module is bring run in standalone by the user
if __name__ == '__main__':

    EXCHANGES = [
        {
            "id": 1,
            "exchange_type": "Tier 1",
            "cabinets_per_exchange": 50,
            "lines_per_exchange": 128,
            "cable_type": "fibre",
            "cable_length": 5000,
            "cable_count": 2,
        },
        {
            "id": 2,
            "exchange_type": "Tier 2",
            "cabinets_per_exchange": 80,
            "lines_per_exchange": 128,
            "cable_type": "fibre",
            "cable_length": 12000,
            "cable_count": 2,
        }
    ]

    CABINETS = [
        {
            "id": 1,
            "cabinet_type": "VDSL",
            "lines_per_cabinet": 128,
            "cable_type": "fibre",
            "cable_length": 800,
            "cable_count": 1,
        },
        {
            "id": 2,
            "cabinet_type": "VDSL",
            "lines_per_cabinet": 256,
            "cable_type": "fibre",
            "cable_length": 900,
            "cable_count": 1,
        }
    ]

    DISTRIBUTION_POINTS = [
        {
            "id": 1,
            "cabinet": 1,
            "dist_point_type": "legacy",
            "dist_point_location": "aerial",
            "cable_type": "legacy",
            "cable_length": 40,
            "cable_count": 1,
        },
        {
            "id": 2,
            "cabinet": 1,
            "dist_point_type": "legacy",
            "dist_point_location": "footway_box",
            "cable_type": "legacy",
            "cable_length": 80,
            "cable_count": 1,
        },
        {
            "id": 3,
            "cabinet": 2,
            "dist_point_type": "legacy",
            "dist_point_location": "aerial",
            "cable_type": "legacy",
            "cable_length": 60,
            "cable_count": 1,
        }
    ]

    BUILDINGS = [
        {
            "id": 1,
            "oa": "E00090610",
            "dist_point": 1,
            "cable_type": 'legacy',
            "cable_length": 12,
            "cable_count": 1,
            "residential address count": 1,
            "non-residential address count": 0,
            "occupants": 2,
        },
        {
            "id": 2,
            "oa": "E00090610",
            "dist_point": 1,
            "cable_type": 'legacy',
            "cable_length": 11,
            "cable_count": 1,
            "residential address count": 1,
            "non-residential address count": 1,
            "occupants": 8,
        },
        {
            "id": 3,
            "oa": "E00090611",
            "dist_point": 2,
            "cable_type": 'legacy',
            "cable_length": 16,
            "cable_count": 1,
            "residential address count": 2,
            "non-residential address count": 0,
            "occupants": 3,
        },
        {
            "id": 4,
            "oa": "E00090611",
            "dist_point": 2,
            "cable_type": 'legacy',
            "cable_length": 9,
            "cable_count": 1,
            "residential address count": 1,
            "non-residential address count": 0,
            "occupants": 7,
        },
        {
            "id": 5,
            "oa": "E00090612",
            "dist_point": 3,
            "cable_type": 'legacy',
            "cable_length": 19,
            "cable_count": 1,
            "residential address count": 3,
            "non-residential address count": 0,
            "occupants": 6,
        },
        {
            "id": 6,
            "oa": "E00090612",
            "dist_point": 3,
            "cable_type": 'legacy',
            "cable_length": 21,
            "cable_count": 1,
            "residential address count": 1,
            "non-residential address count": 1,
            "occupants": 4,
        },
    ]

    OurExchange = Exchange(EXCHANGES[0], CABINETS, DISTRIBUTION_POINTS, BUILDINGS)

    for building in OurExchange.cabinets.values():
        pprint(building)

    print(OurExchange.population())
