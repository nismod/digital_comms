"""
System-level wireless network simulator

Written by Edward Oughton
May 2019

"""
from rtree import index
from shapely.geometry import shape, Point
import numpy as np
from geographiclib.geodesic import Geodesic
from itertools import tee
from pyproj import Proj, transform
from collections import OrderedDict

from digital_comms.mobile_network.path_loss_module import path_loss_calculator

#set numpy seed
np.random.seed(42)

class NetworkManager(object):
    """
    Meta-object for managing all transmitters and receivers in wireless system.

    Parameters
    ----------
    area : geojson
        Polygon of the simulation area boundary
    sites : list of dicts
        Contains a dict for each cellular transmitter site in a list format.
    receivers : list of dicts
        Contains a dict for each user equipment receiver in a list format.
    simulation_parameters : dict
        A dict containing all simulation parameters necessary.

    """
    def __init__(self, area, sites, receivers, simulation_parameters):

        self.area = {}
        self.sites = {}
        self.receivers = {}
        area_id = area['properties']['RMSect'].replace(' ', '')
        self.area[area_id] = Area(area)

        for site in sites:
            site_id = site['properties']["sitengr"]
            site_object = Transmitter(site, simulation_parameters)
            self.sites[site_id] = site_object

            area_containing_sites = self.area[area_id]
            area_containing_sites.add_site(site_object)

        for receiver in receivers:
            receiver_id = receiver['properties']["ue_id"]
            receiver = Receiver(receiver, simulation_parameters)
            self.receivers[receiver_id] = receiver

            area_containing_receivers = self.area[area_id]
            area_containing_receivers.add_receiver(receiver)


    def build_new_assets(self, list_of_new_assets, area_id,
        simulation_parameters):

        for site in list_of_new_assets:
            site_id = site['properties']["sitengr"]
            site_object = Transmitter(site, simulation_parameters)

            self.sites[site_id] = site_object

            for area_containing_sites in self.area.values():
                if area_containing_sites.id == area_id:
                    area_containing_sites.add_site(site_object)


    def estimate_link_budget(self, frequency, bandwidth,
        generation, mast_height, environment, modulation_and_coding_lut,
        simulation_parameters):
        """
        Takes propagation parameters and calculates link budget capacity.

        Parameters
        ----------
        frequency : float
            The carrier frequency for the chosen spectrum band (GHz).
        bandwidth : float
            The width of the spectrum around the carrier frequency (MHz).
        environment : string
            Either urban, suburban or rural.
        modulation_and_coding_lut : list of tuples
            A lookup table containing modulation and coding rates,
            spectral efficiencies and SINR estimates.

        Returns
        -------
        sinr : float
            The signal to noise plut interference ratio (GHz).
        capacity_mbps : float
            The estimated link budget capacity.

        """
        results = []

        seed_value = simulation_parameters['seed_value']

        for receiver in self.receivers.values():

            closest_site, interfering_sites = (
                self.find_closest_available_sites(receiver)
            )

            path_loss = self.calculate_path_loss(
                closest_site, receiver, frequency, mast_height,
                environment, seed_value
            )

            received_power = self.calc_received_power(
                closest_site, receiver, path_loss
            )

            interference = self.calculate_interference(
                interfering_sites, receiver, frequency, environment,
                seed_value)

            noise = self.calculate_noise(
                bandwidth
            )

            sinr = self.calculate_sinr(
                received_power, interference, noise, simulation_parameters
            )

            spectral_efficiency = self.modulation_scheme_and_coding_rate(
                sinr, generation, modulation_and_coding_lut
            )

            estimated_capacity = self.link_budget_capacity(
                bandwidth, spectral_efficiency
            )

            data = {
                'spectral_efficiency': spectral_efficiency,
                'sinr': sinr,
                'capacity_mbps': estimated_capacity
                }

            results.append(data)

            # if spectral_efficiency == None:
            #     print('received_power is {}'.format(received_power))
            #     print('interference is {}'.format(interference))
            #     print('noise is {}'.format(noise))
            #     print('sinr is {}'.format(sinr))
            #     print('spectral_efficiency is {}'.format(spectral_efficiency))
            #     print('estimated_capacity is {}'.format(estimated_capacity))
            #     print('path_loss is {}'.format(path_loss))
            #     print('-----------------------------')

        return results


    def find_closest_available_sites(self, receiver):
        """
        Returns a list of all sites, ranked based on proximity
        to the receiver.

        """
        idx = index.Index()

        for site in self.sites.values():
            idx.insert(0, Point(site.coordinates).bounds, site)

        number_of_sites = len(self.sites.values())

        all_closest_sites =  list(
            idx.nearest(
                Point(receiver.coordinates).bounds,
                number_of_sites, objects='raw')
                )

        closest_site = all_closest_sites[0]

        interfering_sites = all_closest_sites[1:4]

        return closest_site, interfering_sites


    def calculate_path_loss(self, closest_site, receiver,
        frequency, mast_height, environment, seed_value):

        # for area in self.area.values():
        #     local_authority_ids = area.local_authority_ids

        x2_receiver = receiver.coordinates[0]
        y2_receiver = receiver.coordinates[1]

        x1_site, y1_site = transform_coordinates(
            Proj(init='epsg:27700'), Proj(init='epsg:4326'),
            closest_site.coordinates[0],
            closest_site.coordinates[1],
            )

        x2_receiver, y2_receiver = transform_coordinates(
            Proj(init='epsg:27700'), Proj(init='epsg:4326'),
            receiver.coordinates[0],
            receiver.coordinates[1],
            )

        Geo = Geodesic.WGS84

        i_strt_distance = Geo.Inverse(
            y1_site, x1_site,  y2_receiver, x2_receiver
            )

        interference_strt_distance = round(i_strt_distance['s12'],0)

        ant_height = mast_height
        ant_type =  'macro'

        # type_of_sight, building_height, street_width = built_environment_module(
        # site_geom, receiver_geom

        if interference_strt_distance < 250 :
            type_of_sight = 'los'
        else:
            type_of_sight = 'nlos'

        building_height = 20
        street_width = 20
        above_roof = 0
        location = receiver.indoor

        path_loss = path_loss_calculator(
            frequency,
            interference_strt_distance,
            ant_height,
            ant_type,
            building_height,
            street_width,
            environment,
            type_of_sight,
            receiver.ue_height,
            above_roof,
            location,
            seed_value
            )

        # print('path loss for {} to nearest cell {} is {}'.format(
        #     receiver.id, closest_site.id, path_loss)
        #     )

        return path_loss


    def calc_received_power(self, site, receiver, path_loss):
        """
        Calculate received power based on site and receiver
        characteristcs, and path loss.

        Equivalent Isotropically Radiated Power (EIRP) = Power + Gain - Losses

        """
        #calculate Equivalent Isotropically Radiated Power (EIRP)
        eirp = float(site.power) + \
            float(site.gain) - \
            float(site.losses)

        received_power = eirp - \
            path_loss - \
            receiver.misc_losses + \
            receiver.gain - \
            receiver.losses

        return received_power


    def calculate_interference(
        self, closest_sites, receiver, frequency, environment, seed_value):
        """
        Calculate interference from other cells.

        closest_sites contains all sites, ranked based
        on distance, meaning we need to select cells 1-3 (as cell 0
        is the actual cell in use)

        """
        interference = []

        x1_receiver, y1_receiver = transform_coordinates(
            Proj(init='epsg:27700'),
            Proj(init='epsg:4326'),
            receiver.coordinates[0],
            receiver.coordinates[1]
            )

        #calculate interference from other power sources
        for interference_site in closest_sites:

            #get distance
            x2_interference = interference_site.coordinates[0]
            y2_interference = interference_site.coordinates[1]

            x2_interference, y2_interference = transform_coordinates(
                Proj(init='epsg:27700'),
                Proj(init='epsg:4326'),
                interference_site.coordinates[0],
                interference_site.coordinates[1]
                )

            Geo = Geodesic.WGS84

            i_strt_distance = Geo.Inverse(
                y2_interference,
                x2_interference,
                y1_receiver,
                x1_receiver,
                )

            interference_strt_distance = int(
                round(i_strt_distance['s12'], 0)
                )

            if interference_strt_distance < 250 :
                type_of_sight = 'los'
            else:
                type_of_sight = 'nlos'

            ant_height = 20
            ant_type =  'macro'
            building_height = 20
            street_width = 20
            type_of_sight = 'nlos'
            above_roof = 0
            indoor = receiver.indoor

            path_loss = path_loss_calculator(
                frequency,
                interference_strt_distance,
                ant_height,
                ant_type,
                building_height,
                street_width,
                environment,
                type_of_sight,
                receiver.ue_height,
                above_roof,
                indoor,
                seed_value,
                )

            # print('interference path loss for {} to {} is {}'.format(
            #     receiver.id, interference_site.id, path_loss)
            #     )

            #calc interference from other cells
            received_interference = self.calc_received_power(
                interference_site,
                receiver,
                path_loss
                )

            #add cell interference to list
            interference.append(received_interference)

        return interference


    def calculate_noise(self, bandwidth):
        #TODO
        """
        Terminal noise can be calculated as:

        “K (Boltzmann constant) x T (290K) x bandwidth”.

        The bandwidth depends on bit rate, which defines the number of resource blocks.
        We assume 50 resource blocks, equal 9 MHz, transmission for 1 Mbps downlink.

        Required SNR (dB)
        Detection bandwidth (BW) (Hz)
        k = Boltzmann constant
        T = Temperature (kelvins) (290 kelvin = ~16 celcius)
        NF = Receiver noise figure

        NoiseFloor (dBm) = 10log10(k*T*1000)+NF+10log10BW

        NoiseFloor (dBm) = 10log10(1.38x10e-23*290*1x10e3)+1.5+10log10(10x10e6)

        """
        k = 1.38e-23
        t = 290
        BW = bandwidth*1000000

        noise = 10*np.log10(k*t*1000)+1.5+10*np.log10(BW)

        return noise


    def calculate_sinr(self, received_power, interference, noise,
        simulation_parameters):
        """
        Calculate the Signal-to-Interference-plus-Noise-Ration (SINR).

        """
        raw_received_power = 10**received_power

        interference_values = []
        for value in interference:
            output_value = 10**value
            interference_values.append(output_value)

        network_load = simulation_parameters['network_load']

        raw_sum_of_interference = sum(interference_values) * (1+(network_load/100))

        raw_noise = 10**noise

        sinr = np.log10(
            raw_received_power / (raw_sum_of_interference + raw_noise)
            )

        return round(sinr, 2)


    def modulation_scheme_and_coding_rate(self, sinr,
        generation, modulation_and_coding_lut):
        """
        Uses the SINR to allocate a modulation scheme and affliated
        coding rate.

        """
        spectral_efficiency = 0.1
        for lower, upper in pairwise(modulation_and_coding_lut):
            if lower[0] and upper[0] == generation:

                lower_sinr = lower[5]
                upper_sinr = upper[5]

                if sinr >= lower_sinr and sinr < upper_sinr:
                    spectral_efficiency = lower[4]
                    return spectral_efficiency

                highest_value = modulation_and_coding_lut[-1]
                if sinr >= highest_value[5]:

                    spectral_efficiency = highest_value[4]
                    return spectral_efficiency


                lowest_value = modulation_and_coding_lut[0]

                if sinr < lowest_value[5]:

                    spectral_efficiency = lowest_value[4]
                    return spectral_efficiency


    def link_budget_capacity(self, bandwidth, spectral_efficiency):
        """
        Estimate wireless link capacity (Mbps) based on bandwidth and
        receiver signal.

        capacity (Mbps) = bandwidth (MHz) + log2*(1+SINR[dB])

        """
        # if spectral_efficiency == None:
        #     spectral_efficiency = 0.01

        bandwidth_in_hertz = bandwidth*1000000

        link_budget_capacity = bandwidth_in_hertz*spectral_efficiency
        link_budget_capacity_mbps = link_budget_capacity / 1000000

        return link_budget_capacity_mbps


    def find_sites_in_area(self):

        if not self.sites:
            return 0

        area_geometry = ([(d.geometry) for d in self.area.values()][0])

        idx = index.Index()

        for site in self.sites.values():
            idx.insert(0, Point(site.coordinates).bounds, site)

        sites_in_area = []

        for n in idx.intersection(shape(area_geometry).bounds, objects=True):
            point = Point(n.object.coordinates)
            if shape(area_geometry).contains(point):
                sites_in_area.append(n.object)

        return sites_in_area


    def site_density(self):
        """
        Calculate site density per square kilometer (km^2)

        Returns
        -------
        obj
            Sum of sites

        Notes
        -----
        Function returns `0` when no sites are configered to the area.

        """
        if not self.sites:
            return 0

        sites_in_area = self.find_sites_in_area()

        postcode_sector_area = (
            [round(a.area) for a in self.area.values()]
            )[0]

        site_density = (
            len(sites_in_area) / (postcode_sector_area/1000000)
            )

        return site_density


    def receiver_density(self):
        """
        Calculate receiver density per square kilometer (km^2)

        Returns
        -------
        obj
            Sum of receiver

        Notes
        -----
        Function returns `0` when no receivers are configered to the area.
        """
        if not self.receivers:
            return 0

        postcode_sector_area = (
            [round(a.area) for a in self.area.values()]
            )[0]

        receiver_density = (
            len(self.receivers) / (postcode_sector_area/1000000)
            )

        return receiver_density


    def energy_consumption(self, simulation_parameters):
        """
        Gets the energy consumption of the sites in the area.

        Parameters
        ----------
        total_power_dbm : float
            Total dbm for all sites for a single cell.
        watts_for_1_cell_per_site : float
            Total watts for all sites for a single cell.
        total_power_watts : float
            Total watts for all cells in use.

        """
        if not self.area:
            return 0

        cells_per_site = simulation_parameters['sectorisation']

        sites_in_area = self.find_sites_in_area()

        total_power_dbm = [round(a.power) for a in sites_in_area]

        watts_per_area = []
        for value in total_power_dbm:
            watts_for_1_cell_per_site = 10**(value / 10) / 1000
            wattsd_per_site = watts_for_1_cell_per_site * cells_per_site
            watts_per_area.append(wattsd_per_site)

        total_power_watts = sum(watts_per_area)

        return total_power_watts


class Area(object):
    """
    The geographic area which holds all sites and receivers.

    """
    def __init__(self, data):
        #id and geographic info
        self.id = data['properties']['RMSect']
        self.local_authority_ids =  data['properties']['local_authority_ids']
        self.geometry = data['geometry']
        self.coordinates = data['geometry']['coordinates']
        self.area = self._calculate_area(data)

        self._sites = {}
        self._receivers = {}

    def _calculate_area(self, data):
        polygon = shape(data['geometry'])
        area = polygon.area
        return area

    def add_site(self, site):
        self._sites[site.id] = site

    def add_receiver(self, receiver):
        self._receivers[receiver.id] = receiver


class Transmitter(object):
    """
    A site object is specific site.

    """
    def __init__(self, data, simulation_parameters):

        #id and geographic info
        self.id = data['properties']['sitengr']
        self.coordinates = data['geometry']['coordinates']
        self.geometry = data['geometry']

        self.ant_type = 'macro'
        self.ant_height = simulation_parameters['tx_baseline_height']
        self.power = simulation_parameters['tx_power']
        self.gain = simulation_parameters['tx_gain']
        self.losses = simulation_parameters['tx_losses']

    def __repr__(self):
        return "<Transmitter id:{}>".format(self.id)


class Receiver(object):
    """
    A receiver object is a piece of user equipment which can
    connect to a site.

    """
    def __init__(self, data, simulation_parameters):
        self.id = data['properties']['ue_id']
        self.coordinates = data['geometry']["coordinates"]

        self.misc_losses = data['properties']['misc_losses']
        self.gain = data['properties']['gain']
        self.losses = data['properties']['losses']
        self.ue_height = data['properties']['ue_height']
        self.indoor = data['properties']['indoor']

    def __repr__(self):
        return "<Receiver id:{}>".format(self.id)


def transform_coordinates(old_proj, new_proj, x, y):

    new_x, new_y = transform(old_proj, new_proj, x, y)

    return new_x, new_y


def pairwise(iterable):
    """
    Return iterable of 2-tuples in a sliding window

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
