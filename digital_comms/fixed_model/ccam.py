"""Cambridge Communications Assessment Model
"""
from collections import defaultdict
from itertools import tee
from pprint import pprint

PERCENTAGE_OF_TRAFFIC_IN_BUSY_HOUR = 0.15

SERVICE_OBLIGATION_CAPACITY = 10

class ICTManager(object):
    """Model controller class.

    Represents local area districts and postcode sectors with their assets, capacities and clutters.
    
    Parameters
    ----------
    lads: :obj:`list` of :obj:`dict`
        List of local area districts

        * id: :obj:`int`
            Unique ID
        * name: :obj:`str`
            Name of the LAD

    pcd_sectors: :obj:`list` of :obj:`dict`
        List of postcode sectors (pcd)

        * id: :obj:`str`
            Postcode name
        * lad_id: :obj:`int`
            Unique ID
        * population: :obj:`int`
            Number of inhabitants
        * area: :obj:`int`
            Size in TODO
        * user_throughput: :obj:`int`
            TODO

    assets: :obj:`list` of :obj:`dict`
        List of assets

        * pcd_sector: :obj:`str`
            Code of the postcode sector
        * site_ngr: :obj:`int`
            Unique site reference number
        * technology: :obj:`str`
            Abbreviation of the asset technology (LTE, 3G, 4G, ..)
        * frequency: :obj:`str`
            Frequency of the asset (800, 2600, ..)
        * bandwidth: :obj:`str`
            Bandwith of the asset (2x10MHz, ..)
        * build_date: :obj:`int`
            Build year of the asset

    capacity_lookup_table: dict
        Dictionary that represents the capacity of an asset configuration as a function of population density, per district type

        * key: :obj:`tuple`
            * 0: :obj:`str`
                Area type ('urban', ..)
            * 1: :obj:`str`
                Frequency of the asset configuration (800, 2600, ..)
            * 2: :obj:`str`
                Bandwith of the asset configuration (2x10MHz, ..)

        * value: :obj:`list` of :obj:`tuple`
            * 0: :obj:`int`
                Population density
            * 1: :obj:`int`
                Capacity

    clutter_lookup: list of tuple
        Each element represents TODO

        * 0: :obj:`int`
            TODO
        * 1: :obj:`int`
            TODO
    """

    def __init__(self, lads, pcd_sectors, assets, capacity_lookup_table, clutter_lookup):
        """ Load the `lads` in local :obj:`dict` attribute `lad`
        Record the assets, capacity and clutter per postcode sector in the :obj:`dict` attribute `postcode_sectors`
        """

        # Area ID (integer?) => Area
        self.lads = {}

        # List of all postcode sectors
        self.postcode_sectors = {}

        # lad_data in lads <-'lads' is the list of dicts of lad data
        for lad_data in lads:
            # find ID out of lads list of dicts
            lad_id = lad_data["id"]
            # create LAD object using lad_data and put in self.lads dict
            self.lads[lad_id] = LAD(lad_data) # <- create lower level LAD object here

        assets_by_pcd = defaultdict(list)
        for asset in assets:
            assets_by_pcd[asset['pcd_sector']].append(asset)

        for pcd_sector_data in pcd_sectors:
            lad_id = pcd_sector_data["lad_id"]
            pcd_sector_id = pcd_sector_data["id"]
            assets = assets_by_pcd[pcd_sector_id]
            pcd_sector = PostcodeSector(
                pcd_sector_data, assets, capacity_lookup_table, clutter_lookup) # <- create lower level PostcodeSector object here

            # add PostcodeSector to simple list
            self.postcode_sectors[pcd_sector_id] = pcd_sector

            # add PostcodeSector to LAD
            lad_containing_pcd_sector = self.lads[lad_id]
            lad_containing_pcd_sector.add_pcd_sector(pcd_sector)

class LAD(object):
    """Local area district. 
    
    Represents an area to be modelled, contains data for demand 
    characterisation and assets for supply assessment.

    Arguments
    ---------
    data: dict
        Metadata and info for the LAD
        
        * id: :obj:`int`
            Unique ID
        * name: :obj:`str`
            Name of the LAD
    """
    def __init__(self, data):
        self.id = data["id"]
        self.name = data["name"]
        self._pcd_sectors = {} #single underscore indicates it's a private variable which cannot be accessed excepted from within the object
        #this means that code can add pcd_sectors and get summary states (capacity, pop_density etc.), while not having direct access

    def __repr__(self):
        return "<LAD id:{} name:{}>".format(self.id, self.name)

    @property
    def population(self):
        """obj: Sum of all postcode sectors populations in the local area district
        """
        return sum([
            pcd_sector.population
            for pcd_sector in self._pcd_sectors.values()])

    @property
    def population_density(self):
        """obj: The population density in the local area district
        """
        total_area = sum([
            pcd_sector.area
            for pcd_sector in self._pcd_sectors.values()])
        if total_area == 0:
            return 0
        else:
            return self.population / total_area

    def add_pcd_sector(self, pcd_sector):
        """Add a postcode sector to the local area district.

        Arguments
        ---------
        pcd_sector: PostcodeSector
            Representation of a postcode sector that needs to be
            added to the local area district
        """
        self._pcd_sectors[pcd_sector.id] = pcd_sector

    def add_asset(self, asset):
        """Add an asset to postcode sector

        Arguments
        ---------
        asset: TODO
            TODO
        """
        pcd_sector_id = asset.pcd_sector
        self._pcd_sectors[pcd_sector_id].add_asset(asset)

    def system(self):
        """Populates a dict with all existing assets
        Which in total represents the system.

        Returns
        -------
        dict
            TODO
        """
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
        """Calculate mean capacity from all nested postcode sectors

        Returns
        -------
        obj
            Mean capacity of the local area district

        Notes
        -----
        Function returns `0` when no postcode sectors are configured to the LAD.
        """
        if not self._pcd_sectors:
            return 0

        summed_capacity = sum([
            pcd_sector.capacity
            for pcd_sector in self._pcd_sectors.values()])
        return summed_capacity / len(self._pcd_sectors)

    def demand(self):
        """Calculate demand per square kilometer (Mbps km^2) from all nested postcode sectors

        Returns
        -------
        obj 
            Demand of the local area district

        Notes
        -----
        Function returns `0` when no postcode sectors are configured to the LAD.
        """
        if not self._pcd_sectors:
            return 0

        summed_demand = sum(
            pcd_sector.demand * pcd_sector.area
            for pcd_sector in self._pcd_sectors.values()
        )
        summed_area = sum(
            pcd_sector.area
            for pcd_sector in self._pcd_sectors.values()
        )
        return summed_demand / summed_area

    def coverage(self):
        """Calculate coverage as the proportion of the population able to obtain the specified capacity threshold

        Returns
        -------
        obj
            Coverage in the local area district

        Notes
        -----
        Function returns `0` when no postcode sectors are configured to the LAD.
        """
        if not self._pcd_sectors:
            return 0

        population_with_coverage = sum([
            pcd_sector.population
            for pcd_sector in self._pcd_sectors.values()
            if pcd_sector.capacity >= SERVICE_OBLIGATION_CAPACITY])
        total_pop = sum([
            pcd_sector.population
            for pcd_sector in self._pcd_sectors.values()])
        return float(population_with_coverage) / total_pop


class PostcodeSector(object):
    """Represents a Postcode sector to be modelled
    """
    def __init__(self, data, assets, capacity_lookup_table, clutter_lookup):
        self.id = data["id"]
        self.lad_id = data["lad_id"]
        self.population = data["population"]
        self.area = data["area"]

        self.user_throughput = data["user_throughput"]
        self.user_demand = self._calculate_user_demand(self.user_throughput)

        self._capacity_lookup_table = capacity_lookup_table
        self._clutter_lookup = clutter_lookup

        self.clutter_environment = lookup_clutter_geotype(
            self._clutter_lookup,
            self.population_density
        )

        # TODO: replace hard-coded parameter
        self.penetration = 0.8

        # Keep list of assets
        self.assets = assets
        self.capacity = self._macrocell_site_capacity() + self._small_cell_capacity()

    def __repr__(self):
        return "<PostcodeSector id:{}>".format(self.id)

    def _calculate_user_demand(self, user_throughput):
        """Calculate Mb/second from GB/month supplied as throughput scenario

        Notes
        -----
        E.g.
            2 GB per month
                * 1024 to find MB
                * 8 to covert bytes to bits
                * 0.075 represents 7.5% of daily traffic taking place in the busy hour
                * 1/30 assuming 30 days per month
                * 1/3600 converting hours to seconds,
            = ~0.01 Mbps required per user
        """
        return user_throughput * 1024 * 8 * PERCENTAGE_OF_TRAFFIC_IN_BUSY_HOUR / 30 / 3600 ### i have removed market share and place in def demand below
        #return user_throughput / 20 # assume we want to give X Mbps per second, with an OBF of  20

    def threshold_demand(self, SERVICE_OBLIGATION_CAPACITY):
        """Calculate capacity required to meet a service obligation.

        Parameters
        ----------
        SERVICE_OBLIGATION_CAPACITY: int
            The required service obligation in Mb/s

        Returns
        -------
        int
            The threshold demand in Mbps/km^2

        Notes
        -----
        Effectively calculating Mb/s/km^2 from Mb/s/user

        E.g.
            100 people in this area
            * 0.8 penetration proportion
            * 0.3 market share
            * 2 Mb/s/person service obligation
            / 10 km^2 area
            = ~4.8 Mbps/km^2
        """
        ### MARKET SHARE? ###
        threshold_demand = self.population * self.penetration * SERVICE_OBLIGATION_CAPACITY / self.area ##Do we not need to put market share in here?
        return threshold_demand

    @property
    def demand(self):
        """obj: The demand in capacity per km^2
        TODO Double check

        Notes
        -----
            0.02 Mbps per user during busy hours
                * 100 population
                * 0.8 penetration
                / 10 km^2 area
            = ~0.16 Mbps/km^2 area capacity demand
        """
        users = self.population * self.penetration * 0.3 #market share
        user_throughput = users * self.user_demand
        capacity_per_kmsq = user_throughput / self.area
        return capacity_per_kmsq

    @property
    def population_density(self):
        """obj: The population density in persons per square kilometer (km^2)
        """
        return self.population / self.area

    def _macrocell_site_capacity(self):
        capacity = 0

        for frequency in ['800', '2600', '700', '3500']:
            # count sites with this frequency/bandwidth combination
            num_sites = 0
            for asset in self.assets:
                if asset['frequency'] == frequency:
                    num_sites += 1

            # sites/km^2 : divide num_sites/area
            site_density = float(num_sites) / self.area

            # for a given site density and spectrum band, look up capacity
            tech_capacity = lookup_capacity(
                self._capacity_lookup_table,
                self.clutter_environment,
                frequency,
                "2x10MHz",
                site_density)
            capacity += tech_capacity

        return capacity

    def _small_cell_capacity(self):
        # count small_cells
        num_small_cells = len([
            asset
            for asset in self.assets
            if asset['type'] == "small_cell"
        ])
        # sites/km^2 : divide num_small_cells/area
        site_density = float(num_small_cells) / self.area

        # for a given site density and spectrum band, look up capacity
        capacity = lookup_capacity(
            self._capacity_lookup_table,
            "Small cells",  # Override clutter environment for small cells
            "3700",
            "2x25MHz",
            site_density)

        return capacity

    @property
    def capacity_margin(self):
        """obj: Capacity margin per postcode sector in Mbps
        """
        capacity_margin = self.capacity - self.demand
        return capacity_margin


def pairwise(iterable):
    """Return iterable of 2-tuples in a sliding window

    Parameters
    ----------
    iterable: list
        Sliding window

    Returns
    -------
    list of tuple
        Iterable of 2-tuples

    Example
    -------
        >>> list(pairwise([1,2,3,4]))
            [(1,2),(2,3),(3,4)]
    """
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


def lookup_clutter_geotype(clutter_lookup, population_density):
    """Return geotype based on population density

    Parameters
    ----------
    clutter_lookup: list of tuple
        Lookup table that represents geographical types and their population density
        sorted by population_density_upper_bound ascending.

        * 0: :obj:`int`
            Population density in persons per square kilometer (p/km^2)
        * 1: :obj:`str`
            Geotype ('Urban', ..)

    population_density: int
        The population density in persons per square kilometer, that needs to be 
        looked up in the clutter lookup table

    Returns
    -------
    str
        Geotype match for `population_density`

    Example
    -------
        >>> clutter_lookup = [
                (5, "Urban")
            ]
        >>> lookup_clutter_geotype(clutter_lookup, 0)
            "Urban"

    Notes
    -----
    Returns lowest boundary if population density is lower than the lowest boundary.
    Returns upper boundary of a region if population density is within a region range.
    Returns upper boundary if population density is higher than the highest boundary.

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

    Parameters
    ----------
    lookup_table: dict
        Capacity lookup table
    clutter_environment: str
        Area type ('urban', ..)
    frequency: str
        Frequency of the asset configuration (800, 2600, ..)
    bandwidth: str
        Bandwith of the asset configuration (2x10MHz, ..)
    site_density: int
        The population density in asset area

    Returns
    -------
    int
        The capacity for the asset in TODO

    Example
    -------
    >>> lookup_table = {
            ("Urban", "800", "2x10MHz"): [
                (0, 1),
                (1, 2),
            ],
            ("Urban", "2600", "2x10MHz"): [
                (0, 3),
                (3, 5),
            ]
        }
    >>> lookup_capacity(lookup_table, "Urban", "2600", "2x10MHz", 3)
        5

    Notes
    -----
    Returns a capacity of 0 when the site density is below the specified range.
    Interpolates between values between the lower and upper bounds.
    Returns the maximum capacity when the site density is higher than the uppper bound.

    Raises
    ------
    KeyError
        If combination is not found in the lookup table.
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

    Parameters
    ----------
    x0: int 
        Lower x-value
    y0: int
        Lower y-value
    x1: int
        Upper x-value
    y1: int
        Upper y-value
    x: int
        Requested x-value

    Returns
    -------
    int, float
        Interpolated y-value
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
