"""Cambridge Communications Assessment Model
"""
from itertools import tee
from pprint import pprint

class ICTManager(object):
    """Model controller class
    """
    def __init__(self, lads, pcd_sectors, assets, capacity_lookup_table, clutter_lookup):
        """Create an instance of the model

        Parameters
        ----------
        lads: list of dicts
            Each LAD must have values for:
            - id
            - name
        pcd_sectors: list of dicts
            Each postcode sector must have values for:
            - id
            - lad_id
            - population
            - area
            - user_throughput
        assets: list of dicts
            Each asset must have values for:
            - pcd_sector
            - site_ngr
            - technology
            - frequency
            - bandwidth
        """
        # Area ID (integer?) => Area
        self.lads = {}

        # List of all postcode sectors
        self.postcode_sectors = []

        # pcd_sector id =? LAD id
        lad_id_by_pcd_sector = {}
        # {
        # 	"pcd_sector_1": "lad_0",
        # 	"pcd_sector_2": "lad_0"
        # }

        for lad_data in lads:  # lad_data in lads <-'lads' is the list of dicts of lad data
            lad_id = lad_data["id"]  # find ID out of lads list of dicts
            self.lads[lad_id] = LAD(lad_data)  # create LAD object using lad_data and put in self.lads dict

        for pcd_sector_data in pcd_sectors:
            lad_id = pcd_sector_data["lad_id"]
            pcd_sector_id = pcd_sector_data["id"]
            pcd_sector = PostcodeSector(pcd_sector_data, capacity_lookup_table, clutter_lookup)

            # add PostcodeSector to simple list
            self.postcode_sectors.append(pcd_sector)

            # add PostcodeSector to LAD
            lad_containing_pcd_sector = self.lads[lad_id]
            lad_containing_pcd_sector.add_pcd_sector(pcd_sector)

            # add LAD id to lookup by pcd_sector_id
            lad_id_by_pcd_sector[pcd_sector_id] = lad_id

        for asset_data in assets:
            asset = Asset(asset_data)
            lad_id = lad_id_by_pcd_sector[asset.pcd_sector]
            area_for_asset = self.lads[lad_id]
            area_for_asset.add_asset(asset)

    def results(self):
        return {
            "capacity": {area.name: area.capacity() for area in self.lads.values()},
            "coverage": {area.name: area.coverage() for area in self.lads.values()},
            "demand": {area.name: area.demand() for area in self.lads.values()},
            "cost": {area.name: area.cost() for area in self.lads.values()},
            "energy_demand": {area.name: area.energy_demand() for area in self.lads.values()}
        }

class LAD(object):
    """Represents an area to be modelled, contains
    data for demand characterisation and assets for
    supply assessment
    """
    def __init__(self, data):
        self.id = data["id"]
        self.name = data["name"]
        self._pcd_sectors = {}

    def __repr__(self):
        return "<LAD id:{} name:{}>".format(self.id, self.name)

    @property
    def population(self):
        return sum([
            pcd_sector.population
            for pcd_sector in self._pcd_sectors.values()])

    @property
    def population_density(self):
        total_area = sum([
            pcd_sector.area
            for pcd_sector in self._pcd_sectors.values()])
        if total_area == 0:
            return 0
        else:
            return self.population / total_area

    def add_pcd_sector(self, pcd_sector):
        self._pcd_sectors[pcd_sector.id] = pcd_sector

    def add_asset(self, asset):
        pcd_sector_id = asset.pcd_sector
        self._pcd_sectors[pcd_sector_id].add_asset(asset)

    def system(self):
        system = {}
        for pcd_sector in self._pcd_sectors.values():
            pcd_system = pcd_sector.system()
            for tech, cells in pcd_system.items():
                # check tech is in system
                if tech not in system:
                    system[tech] = 0
                # add number of cells to tech in area
                system[tech] += cells
        return system

    def capacity(self):
        """Return the mean capacity from all nested postcode sectors
        """
        if not self._pcd_sectors:
            return 0

        summed_capacity = sum([
            pcd_sector.capacity
            for pcd_sector in self._pcd_sectors.values()])
        return summed_capacity / len(self._pcd_sectors)

    def demand(self):
        """Return the mean capacity demand from all nested postcode sectors
        """
        if not self._pcd_sectors:
            return 0

        summed_demand = sum([
            pcd_sector.demand
            for pcd_sector in self._pcd_sectors.values()])
        return summed_demand / len(self._pcd_sectors)

    def coverage(self):
        """Return proportion of population with capacity coverage over a threshold
        """
        if not self._pcd_sectors:
            return 0

        # TODO replace hardcoded threshold value
        threshold = 2

        population_with_coverage = sum([
            pcd_sector.population
            for pcd_sector in self._pcd_sectors.values()
            if pcd_sector.capacity >= threshold])
        total_pop = sum([
            pcd_sector.population
            for pcd_sector in self._pcd_sectors.values()])
        return float(population_with_coverage) / total_pop

    def cost(self):
        """Return the sum of costs from all nested postcode sectors
        """
        return sum([pcd_sector.cost for pcd_sector in self._pcd_sectors.values()])

    def energy_demand(self):
        """Return the sum of energy demand from all nested postcode sectors
        """
        return sum([pcd_sector.energy_demand for pcd_sector in self._pcd_sectors.values()])


class PostcodeSector(object):
    """Represents a pcd_sector to be modelled
    """
    def __init__(self, data, capacity_lookup_table, clutter_lookup):
        self.id = data["id"]
        self.population = data["population"]
        self.area = data["area"]

        self.user_throughput = data["user_throughput"]
        self.user_demand = self._calculate_user_demand(self.user_throughput)

        self._capacity_lookup_table = capacity_lookup_table
        self._clutter_lookup = clutter_lookup

        # TODO: replace hard-coded parameter
        self.penetration = 0.8

        # Keep list of assets
        self.assets = []

    def __repr__(self):
        return "<PostcodeSector id:{}>".format(self.id)

    def _calculate_user_demand(self, user_throughput):
        """Calculate Mb/second from GB/month supplied as throughput scenario

        E.g.
            2 GB per month
                * 1024 to find MB
                * 8 to covert bytes to bits
                * 1/9 assuming 9 busy hours per day
                * 1/30 assuming 30 days per month
                * 1/3600 converting hours to seconds,
            = ~0.02 Mbps required per user
        """
        return user_throughput * 1024 * 8 / 9 / 30 / 3600

    def add_asset(self, asset):
        """Add an instance of an Asset object to this area's assets
        """
        self.assets.append(asset)

    @property
    def demand(self):
        """Estimate total demand based on population and penetration

        E.g.
            0.02 Mbps per user during busy hours
                * 100 population
                * 0.8 penetration
                / 10 km^2 area
            = ~0.16 Mbps/km^2 area capacity demand
        """
        users = self.population * self.penetration
        user_throughput = users * self.user_demand
        capacity_per_kmsq = user_throughput / self.area
        return capacity_per_kmsq

    @property
    def population_density(self):
        """Calculate population density
        """
        return self.population / self.area

    @property
    def clutter_environment(self):
        """Estimate clutter_environment geotype based on population density
        """
        return lookup_clutter_geotype(
            self._clutter_lookup,
            self.population_density
        )

    @property
    def capacity(self):
        """Calculate capacity as sum of capacity based principally on the site
        density of each frequency/bandwidth combination.
        """
        return self._macrocell_site_capacity() + self._small_cell_capacity()

    def _macrocell_site_capacity(self):
        # Find unique frequency/bandwidth combinations
        technology_combinations = set([
            (asset.frequency, asset.bandwidth)
            for asset in self.assets
            # TODO check list of assessable technology - i.e. excluding 2G/3G
            if asset.technology in ("LTE")
            and asset.type == "macrocell_site"
        ])

        capacity = 0

        for frequency, bandwidth in technology_combinations:
            # count sites with this frequency/bandwidth combination
            num_sites = len(set([
                asset.site_ngr
                for asset in self.assets
                if asset.frequency == frequency and
                asset.bandwidth == bandwidth
            ]))
            # sites/km^2 : divide num_sites/area
            site_density = float(num_sites) / self.area

            # for a given site density and spectrum band, look up capacity
            tech_capacity = lookup_capacity(
                self._capacity_lookup_table,
                self.clutter_environment,
                frequency,
                bandwidth,
                site_density)
            capacity += tech_capacity

        return capacity

    def _small_cell_capacity(self):
        # Find unique frequency/bandwidth combinations for small cells
        technology_combinations = set([
            (asset.frequency, asset.bandwidth)
            for asset in self.assets
            if asset.type == "small_cell"
        ])

        capacity = 0

        for frequency, bandwidth in technology_combinations:
            # count all small_cells with this frequency/bandwidth combination
            num_small_cells = len([
                asset
                for asset in self.assets
                if asset.frequency == frequency and
                asset.bandwidth == bandwidth
            ])
            # sites/km^2 : divide num_small_cells/area
            site_density = float(num_small_cells) / self.area

            # for a given site density and spectrum band, look up capacity
            capacity += lookup_capacity(
                self._capacity_lookup_table,
                "Small cells",  # Override clutter environment for small cells
                frequency,
                bandwidth,
                site_density)

        return capacity

    @property
    def capacity_margin(self):
        capacity_margin = self.capacity - self.demand
        return capacity_margin

    @property
    def cost(self):
        # sites : count how many assets are sites
        sites = len(set([asset.site_ngr for asset in self.assets]))
        # for a given number of sites, what is the total cost?
        # TODO replace hardcoded value
        cost = (sites * 10)
        return cost

    @property
    def energy_demand(self):
        # cells : count how many cells there are in the assets database
        cells = sum([asset.cells for asset in self.assets])
        # for a given number of cells, what is the total cost?
        # TODO replace hardcoded value
        energy_demand = (cells * 5)
        return energy_demand


class Asset(object):
    """Element of the communication infrastructure system,
    e.g. base station or distribution-point unit.
    """
    def __init__(self, data):
        self.pcd_sector = data["pcd_sector"]
        self.site_ngr = data["site_ngr"]
        self.type = data["type"]
        self.technology = data["technology"]
        self.frequency = data["frequency"]
        self.bandwidth = data["bandwidth"]
        # Assume any mobile asset has 3 cells
        self.cells = 3

    def __repr__(self):
        fmt = r'Asset(\{"pcd_sector": {}, "site_ngr": {}, "technology": {},' + \
            r' "frequency": {}, "bandwidth": {}\})'
        return fmt.format(self.pcd_sector, self.site_ngr, self.technology,
                          self.frequency, self.bandwidth)


def pairwise(iterable):
    """Return iterable of 2-tuples in a sliding window

        >>> list(pairwise([1,2,3,4]))
        [(1,2),(2,3),(3,4)]
    """
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


def lookup_clutter_geotype(clutter_lookup, population_density):
    """Return geotype based on population density

    Params:
    ======
    clutter_lookup : list of (population_density_upper_bound, geotype) tuples
        sorted by population_density_upper_bound ascending
    """
    lowest_popd, lowest_geotype = clutter_lookup[0]
    if population_density < lowest_popd:
        # Never fail, simply return least dense geotype
        return lowest_geotype

    for (lower_popd, lower_geotype), (upper_popd, upper_geotype) in pairwise(clutter_lookup):
        if lower_popd < population_density and population_density <= upper_popd:
            # Be pessimistic about clutter, return upper bound
            return upper_geotype

    # If not caught between bounds, return highest geotype
    highest_popd, highest_geotype = clutter_lookup[-1]
    return highest_geotype


def lookup_capacity(lookup_table, clutter_environment, frequency, bandwidth, site_density):
    """Use lookup table to find capacity by clutter environment geotype,
    frequency, bandwidth and site density

    TODO:
    - neat handling of loaded lookup_table
    """
    if (clutter_environment, frequency, bandwidth) not in lookup_table:
        raise KeyError("Combination %s not found in lookup table",
                       (clutter_environment, frequency, bandwidth))

    density_capacities = lookup_table[(clutter_environment, frequency, bandwidth)]

    lowest_density, lowest_capacity = density_capacities[0]
    if site_density < lowest_density:
        # Never fail, return zero capacity if site density is below range
        return 0

    for a, b in pairwise(density_capacities):
        lower_density, lower_capacity = a
        upper_density, upper_capacity = b
        if lower_density <= site_density and site_density < upper_density:
            # Interpolate between values
            return interpolate(lower_density, lower_capacity, upper_density, upper_capacity, site_density)

    # If not caught between bounds return highest capacity
    highest_density, highest_capacity = density_capacities[-1]
    return highest_capacity

def interpolate(x0, y0, x1, y1, x):
    """Linear interpolation between two values
    """
    y = (y0 * (x1 - x) + y1 * (x - x0)) / (x1 - x0)
    return y

# __name__ == '__main__' means that the module is bring run in standalone by the user
if __name__ == '__main__':
    LADS = [
        {
            "id": 1,
            "name": "Cambridge",
        }
    ]
    PCD_SECTORS = [
        {
            "id": "CB11",
            "lad_id": 1,
            "population": 500,
            "area": 2,
            "user_throughput": 2
        },
        {
            "id": "CB12",
            "lad_id": 1,
            "population": 200,
            "area": 2,
            "user_throughput": 2
        }
    ]
    ASSETS = [
        {
            "pcd_sector": "CB11",
            "site_ngr": 100,
            "technology": "LTE",
            "frequency": "800",
            "bandwidth": "2x10MHz",
            "build_date": 2017
        },
        {
            "pcd_sector": "CB12",
            "site_ngr": 200,
            "technology": "LTE",
            "frequency": "2600",
            "bandwidth": "2x10MHz",
            "build_date": 2017
        }
    ]

    CAPACITY_LOOKUP = {
        ("Urban", "800", "2x10MHz"): [
            (0, 1),
            (1, 2),
        ],
        ("Urban", "2600", "2x10MHz"): [
            (0, 3),
            (3, 5),
        ]
    }

    CLUTTER_LOOKUP = [
        (5, "Urban")
    ]

    MANAGER = ICTManager(LADS, PCD_SECTORS, ASSETS, CAPACITY_LOOKUP, CLUTTER_LOOKUP)
    pprint(MANAGER.results())

    for lad in MANAGER.lads.values():
        pprint(lad)
        for pcd in lad._pcd_sectors.values():
            print(" ", pcd, "capacity:{:.2f} demand:{:.2f}".format(pcd.capacity, pcd.demand))
