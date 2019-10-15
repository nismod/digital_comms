"""Cambridge Communications Assessment Model
"""
from collections import defaultdict
from itertools import tee
from pprint import pprint

class NetworkManager(object):
    """
    Model controller class.

    Represents postcode sectors nested in local area districts,
    with all affiliated assets, capacities and clutter types.

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
        * area: :obj:`float`
            Areas size in square kilometers (km^2)
        * user_throughput: :obj:`int`
            Per user monthly data demand in gigabytes (GB)
    assets: :obj:`list` of :obj:`dict`
        List of assets
        * pcd_sector: :obj:`str`
            Code of the postcode sector
        * site_ngr: :obj:`int`
            Unique site reference number
        * technology: :obj:`str`
            Abbreviation of the asset technology (LTE, 5G etc.)
        * frequency: :obj:`str`
            Spectral frequency(s) the asset operates at (800, 2600, ..)
        * bandwidth: :obj:`str`
            Downlink bandwith of the asset (10MHz, ..)
        * build_date: :obj:`int`
            Build year of the asset
    capacity_lookup_table: dict
        Dictionary that represents the clutter/asset type, spectrum
        frequency and channel bandwidth, and the consequential
        cellular capacity provided for different asset densities.
        * key: :obj:`tuple`
            * 0: :obj:`str`
                Area type ('urban', 'suburban' or 'rural') or asset
                type ('small_cells')
            * 1: :obj:`str`
                Frequency of the asset configuration (800, 2600, ..)
            * 2: :obj:`str`
                Bandwith of the asset configuration (10, 40, ..)
        * value: :obj:`list` of :obj:`tuple`
            * 0: :obj:`int`
                Cellular asset density per square kilometer (sites per km^2)
            * 1: :obj:`int`
                Average Radio Access Network capacity in Mbps per square
                kilometer (Mbps/km^2)
    clutter_lookup: list of tuples
        Each element represents the settlement definitions for
        urban, suburban and rural by population density in square
        kilometers (persons per km^2)
        * 0: :obj:`int`
            Population density in persons per km^2.
        * 1: :obj:`string`
            Settlement type (rban, suburban and rural)
    simulation_parameters: dict
        Contains all simulation parameters, set in the run script.
        * market_share: :obj: 'int'
            Percentage market share of the modelled hypothetical operator.
        * annual_budget: :obj: 'int'
            Annual budget to spend.
        * service_obligation_capacity: :obj: 'int'
            Required service obligation.
        * busy_hour_traffic_percentage: :obj: 'int'
            Percentage of daily traffic taking place in the busy hour.
        * coverage_threshold: :obj: 'int'
            The threshold we wish to measure the served population against.
        * penetration: :obj: 'int'
            The penetration of users with smartphone and data access.

    """
    def __init__(self, lads, pcd_sectors, assets, capacity_lookup_table,
        clutter_lookup, simulation_parameters):

        self.lads = {}

        self.postcode_sectors = {}

        for lad_data in lads:
            lad_id = lad_data["id"]
            self.lads[lad_id] = LAD(lad_data, simulation_parameters)

        assets_by_pcd = defaultdict(list)
        for asset in assets:
            assets_by_pcd[asset['pcd_sector']].append(asset)

        for pcd_sector_data in pcd_sectors:

            try:
                lad_id = pcd_sector_data["lad_id"]
                pcd_sector_id = pcd_sector_data["id"]
                assets = assets_by_pcd[pcd_sector_id]
                pcd_sector = PostcodeSector(pcd_sector_data, assets,
                capacity_lookup_table, clutter_lookup, simulation_parameters, 0)
                self.postcode_sectors[pcd_sector_id] = pcd_sector

                lad_containing_pcd_sector = self.lads[lad_id]
                lad_containing_pcd_sector.add_pcd_sector(pcd_sector)
            except:
                print('could not create object for {}'.format(pcd_sector_data["id"]))
                print(pcd_sector_data)
                pass


class LAD(object):
    """
    Local area district.

    Represents an area to be modelled. Contains data for demand
    characterisation and assets for supply assessment.

    Arguments
    ---------
    data: dict
        Metadata and info for the LAD
        * id: :obj:`int`
            Unique ID
        * name: :obj:`str`
            Name of the LAD
    simulation_parameters: dict
        Contains all simulation parameters, set in the run script.
        * market_share: :obj: 'int'
            Percentage market share of the modelled hypothetical operator.
        * annual_budget: :obj: 'int'
            Annual budget to spend.
        * service_obligation_capacity: :obj: 'int'
            Required service obligation.
        * busy_hour_traffic_percentage: :obj: 'int'
            Percentage of daily traffic taking place in the busy hour.
        * coverage_threshold: :obj: 'int'
            The threshold we wish to measure the served population against.
        * penetration: :obj: 'int'
            The penetration of users with smartphone and data access.

    """
    def __init__(self, data, simulation_parameters):
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
    def area(self):
        return sum([
            pcd_sector.area
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

        summed_demand = sum(
            pcd_sector.demand * pcd_sector.area
            for pcd_sector in self._pcd_sectors.values()
        )
        summed_area = sum(
            pcd_sector.area
            for pcd_sector in self._pcd_sectors.values()
        )

        return summed_demand / summed_area


    def coverage(self, simulation_parameters):
        """Return proportion of population with capacity coverage over a threshold
        """
        if not self._pcd_sectors:
            return 0

        threshold = simulation_parameters['coverage_threshold']

        population_with_coverage = sum([
            pcd_sector.population
            for pcd_sector in self._pcd_sectors.values()
            if pcd_sector.capacity >= threshold])

        total_pop = sum([
            pcd_sector.population
            for pcd_sector in self._pcd_sectors.values()])

        return float(population_with_coverage) / total_pop


class PostcodeSector(object):
    """Represents a pcd_sector to be modelled
    """
    def __init__(self, data, assets, capacity_lookup_table,
        clutter_lookup, simulation_parameters, testing):

        self.id = data["id"]
        self.lad_id = data["lad_id"]
        self.population = data["population"]
        self.area = data["area_km2"]
        self.user_throughput = data["user_throughput"]
        self.penetration = simulation_parameters['penetration']
        self.busy_hour_traffic = simulation_parameters['busy_hour_traffic_percentage']

        self.market_share = simulation_parameters['market_share']
        self.user_demand = self._calculate_user_demand(
            self.user_throughput, simulation_parameters)

        self.demand_density = self.demand / self.area

        self._capacity_lookup_table = capacity_lookup_table
        self._clutter_lookup = clutter_lookup
        self.clutter_environment = lookup_clutter_geotype(
            self._clutter_lookup,
            self.population_density
        )

        self.assets = assets

        self.site_density_macrocells = self._calculate_site_density_macrocells()
        self.site_density_small_cells = self._calculate_site_density_small_cells()

        self.capacity = (
            self._macrocell_site_capacity(simulation_parameters, testing) +
            self.small_cell_capacity(simulation_parameters, testing)
        )


    def __repr__(self):
        return "<PostcodeSector id:{}>".format(self.id)

    def _calculate_site_density_macrocells(self):

        unique_sites = set()
        for asset in self.assets:
            if asset['type'] == 'macrocell_site':
                unique_sites.add(asset['site_ngr'])

        site_density = float(len(unique_sites)) / self.area

        return site_density


    def _calculate_site_density_small_cells(self):

        small_cells = []
        for asset in self.assets:
            if asset['type'] == 'small_cell':
                small_cells.append(asset)

        site_density = float(len(small_cells)) / self.area

        return site_density


    def _calculate_user_demand(self, user_throughput, simulation_parameters):
        """Calculate Mb/second from GB/month supplied as throughput scenario

        E.g.
            2 GB per month
                * 1024 to find MB
                * 8 to covert bytes to bits
                * busy_hour_traffic = daily traffic taking place
                  in the busy hour
                * 1/30 assuming 30 days per month
                * 1/3600 converting hours to seconds,
            = ~0.01 Mbps required per user
        """
        busy_hour_traffic = simulation_parameters['busy_hour_traffic_percentage'] / 100

        demand = user_throughput * 1024 * 8 * busy_hour_traffic / 30 / 3600

        return demand


    @property
    def demand(self):
        """
        Estimate total demand based on population and penetration.

        E.g.
            0.02 Mbps per user during busy hours
                * 100 population
                * 0.8 penetration
                / 10 km^2 area
            = ~0.16 Mbps/km^2 area capacity demand

        """
        users = self.population * (self.penetration / 100) * self.market_share

        user_throughput = users * self.user_demand

        capacity_per_kmsq = user_throughput / self.area

        return capacity_per_kmsq


    @property
    def population_density(self):
        """
        Calculate population density for a specific population and area.

        """
        return self.population / self.area


    def _macrocell_site_capacity(self, simulation_parameters, testing):
        """
        Find the macrocellular Radio Access Network capacity given the
        area assets and deployed frequency bands.

        """
        capacity = 0

        for frequency in ['700', '800', '1800', '2600', '3500', '26000']:
            unique_sites = set()
            for asset in self.assets:
                for asset_frequency in asset['frequency']:

                    if asset_frequency == frequency:
                        unique_sites.add(asset['site_ngr'])

            site_density = float(len(unique_sites)) / self.area

            bandwidth = find_frequency_bandwidth(frequency,
                simulation_parameters)

            if frequency == '700' or frequency == '3500' or frequency == '26000':
                generation = '5G'
            else:
                generation = '4G'

            tech_capacity = lookup_capacity(
                self._capacity_lookup_table,
                self.clutter_environment,
                frequency,
                bandwidth,
                generation,
                site_density,
                0)

            capacity += tech_capacity

        return capacity


    def small_cell_capacity(self, simulation_parameters, testing):
        """
        Find the small cell Radio Access Network capacity given the
        area assets and deployed frequency bands.

        """
        num_small_cells = len([
            asset
            for asset in self.assets
            if asset['type'] == "small_cell"
        ])

        site_density = float(num_small_cells) / self.area

        capacity = lookup_capacity(
            self._capacity_lookup_table,
            "small_cells",
            "3700",
            "25",
            "5G",
            site_density,
            testing)

        return capacity


def find_frequency_bandwidth(frequency, simulation_parameters):
    """
    Finds the correct bandwidth for a specific frequency from the
    simulation parameters.

    """
    simulation_parameter = 'channel_bandwidth_{}'.format(frequency)

    if simulation_parameter not in simulation_parameters.keys():
        KeyError('{} not specified in simulation_parameters'.format(frequency))

    bandwidth = simulation_parameters[simulation_parameter]

    return bandwidth


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
    highest_popd, highest_geotype = clutter_lookup[2]
    middle_popd, middle_geotype = clutter_lookup[1]
    lowest_popd, lowest_geotype = clutter_lookup[0]

    if population_density < middle_popd:
        return lowest_geotype

    elif population_density > highest_popd:
        return highest_geotype

    else:
        return middle_geotype


def lookup_capacity(lookup_table, clutter_environment, frequency, bandwidth, generation, site_density, testing):
    """
    Use lookup table to find capacity by clutter environment geotype,
    frequency, bandwidth and site density.

    """
    if (clutter_environment, frequency, bandwidth, generation) not in lookup_table:
        raise KeyError("Combination %s not found in lookup table",
                       (clutter_environment, frequency, bandwidth, generation))
    density_capacities = lookup_table[(clutter_environment, frequency, bandwidth, generation)]

    lowest_density, lowest_capacity = density_capacities[0]
    if site_density < lowest_density:
        return 0

    for a, b in pairwise(density_capacities):
        lower_density, lower_capacity = a
        upper_density, upper_capacity = b
        if lower_density <= site_density and site_density < upper_density:
            return interpolate(lower_density, lower_capacity, upper_density, upper_capacity, site_density)

    # If not caught between bounds return highest capacity
    highest_density, highest_capacity = density_capacities[-1]

    return highest_capacity


def interpolate(x0, y0, x1, y1, x):
    """
    Linear interpolation between two values.

    """
    y = (y0 * (x1 - x) + y1 * (x - x0)) / (x1 - x0)
    return y
