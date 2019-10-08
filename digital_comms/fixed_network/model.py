"""Cambridge Communications Assessment Model
"""
from collections import defaultdict
from math import ceil
from abc import abstractmethod, abstractproperty, ABCMeta
from typing import Dict

#####################
# MODEL
#####################


class NetworkManager():
    """Model controller class.

    Parameters
    ----------
    assets : dict
        Contains keys for Premises, Distribution Points, Cabinets and Exchanges,
        with each value constituting a list of respective assets.
    links : list_of_dicts
        Contains all links between Premises, Distribution Points, Cabinets and Exchanges.
    parameters : dict
        Contains all parameters from 'digital_comms.yml'.

    Attributes
    ----------
    assets
    links
    number_of_assets
    number_of_links
    total_link_length
    avg_link_length
    lads

    Methods
    -------
    update_adoption_desirability
        Takes exogenously defined annual demand and updates premises adoption desirability.
    coverage
        Allocates premises-level technology technologies to a dict of coverage_results by
        Local Authority District.
    aggregate_coverage
        Calculates the sum and percentage coverage of premises-level technology by Local
        Authority District.
    capacity
        Calculates the average premises connection.

    """
    def __init__(self, exchanges, simulation_parameters):

        self._exchanges = []
        for exchange in exchanges:

            exchange = Exchange(
                exchange,
                simulation_parameters
            )
            self._exchanges.append(exchange)


    def upgrade(self, interventions):
        """

        Upgrades the system with a list of ``interventions``

        Arguments
        ---------
        interventions: list of tuple
            A list of intervention tuples containing asset id and technology

        """
        for intervention in interventions:

            asset_id = intervention[0]
            technology = intervention[1]

            exchange = [exchange for exchange in self._exchanges if exchange.id == asset_id][0]
            exchange.upgrade(technology)


    def coverage(self):
        """
        define coverage
        """
        # run statistics on each lad
        coverage_results = []

        for exchange in self._exchanges:

            coverage_results.append({
                'id': exchange.id,
                'fttp': exchange.fttp,
                'fttdp': exchange.fttdp,
                'fttc': exchange.fttc,
                # 'docsis3': exchange.docsis3,
                'adsl': exchange.adsl,
                'premises': exchange.total_prems,
            })

        output = []

        for item in coverage_results:
            output.append({
                'id': item['id'],
                'percentage_of_premises_with_fttp': _calculate_percentage(item['fttp'], item['premises']),
                'percentage_of_premises_with_fttdp': _calculate_percentage(item['fttdp'], item['premises']),
                'percentage_of_premises_with_fttc': _calculate_percentage(item['fttc'], item['premises']),
                # 'percentage_of_premises_with_docsis3': _calculate_percentage(aggregate_fttp, aggregate_premises)
                'percentage_of_premises_with_adsl': _calculate_percentage(item['adsl'], item['premises']),
                'sum_of_premises': item['premises']
            })

        return output


    def capacity(self):
        """

        Define capacity

        """
        capacity_results = []

        for asset in self._exchanges:

            capacity_by_technology = []

            fttp_availability = getattr(asset, 'fttp')
            fttdp_availability = getattr(asset, 'fttdp') - getattr(asset, 'fttp')
            fttc_availability = getattr(asset, 'fttc') - getattr(asset, 'fttdp')

            total_prems = getattr(asset, 'total_prems')

            prems_with_fttp = _get_prems_with_tech(fttp_availability, total_prems)
            cumulative_premises = prems_with_fttp

            if cumulative_premises <= total_prems:
                capacity_by_technology.append(
                    prems_with_fttp *
                    _generic_connection_capacity('fttp')
                )

            prems_with_fttdp = _get_prems_with_tech(fttdp_availability, total_prems)
            cumulative_premises += prems_with_fttdp

            if cumulative_premises <= total_prems:
                capacity_by_technology.append(
                    prems_with_fttdp *
                    _generic_connection_capacity('fttdp')
                )

            prems_with_fttc = _get_prems_with_tech(fttc_availability, total_prems)
            cumulative_premises += prems_with_fttc

            if cumulative_premises <= total_prems:
                capacity_by_technology.append(
                    prems_with_fttc *
                    _generic_connection_capacity('fttc')
                )
                capacity_by_technology.append(
                    (total_prems - cumulative_premises) *
                    _generic_connection_capacity('adsl')
                )

            summed_capacity = sum(capacity_by_technology)

            if summed_capacity > 0 or total_prems > 0:
                average_capacity = round(summed_capacity / total_prems)
            else:
                average_capacity = 0

            capacity_results.append({
                'id': asset.id,
                'average_capacity': average_capacity,
            })

        return capacity_results


class Exchange():
    """

    Exchange object

    Arguments
    ---------
    data : dict
        Contains asset data including, id, name, postcode, region, county and available
        technologies.
    dwellings : list_of_objects
        Contains all assets (Cabinets) served by an Exchange.
    parameters : dict
        Contains all parameters from 'digital_comms.yml'.

    self.fttp = raw number of unserved premises
    self.fttdp = raw number of unserved premises
    self.fttc = raw number of unserved premises
    self.adsl = raw number of unserved premises

    self.fttp_unserved = number of unserved premises per km^2
    self.fttdp_unserved = number of unserved premises per km^2
    self.fttc_unserved = number of unserved premises per km^2

    """
    def __init__(self, data, simulation_parameters):
        self.id = data["exchange_id"]
        self.lad = data["lad_id"]
        self.area = data['area']

        self.fttp = _determine_technology(data, 'fttp')
        self.fttdp = _determine_technology(data, 'fttdp')
        self.fttc = _determine_technology(data, 'fttc')
        self.adsl = _determine_technology(data, 'adsl')

        self.total_prems = int(data['exchange_dwellings'])

        self.fttp_unserved = (100 - self.fttp) / self.area
        self.fttdp_unserved = (100 - self.fttdp) / self.area
        self.fttc_unserved = (100 - self.fttc) / self.area

        self.rollout_costs = self._calculate_roll_out_costs()


    def _calculate_roll_out_costs(self):

        costs = {
            'fttp': 100000,
            'fttdp': 50000,
            'fttc': 25000,
        }

        return costs

    def upgrade(self, action):
        """

        Upgrade the asset's clients with an ``action``
        If a leaf asset (e.g. an Asset with no clients), upgrade
        self.
        Arguments
        ---------
        action : str
        Notes
        -----
        Could check whether self is an instance of Distribution instead

        """
        if action in ('fttp'):
            self.fttp = self.total_prems
            self.fttdp = 100
            self.fttc = 100
            # self._docsis3 = 0
            self.adsl = 100

        elif action in ('fttdp'):
            self.fttp = self.fttp
            self.fttdp = self.total_prems
            self.fttc = 100
            # self._docsis3 = 0
            self.adsl = 100


def _determine_technology(data, tech):

    if tech == 'fttp':
        quantity = (int(data['fttp_availability']) / 100) * int(data['exchange_dwellings'])
    if tech == 'fttdp':
        quantity = (int(data['fttdp_availability']) / 100) * int(data['exchange_dwellings'])
    if tech == 'fttc':
        quantity = (int(data['fttc_availability']) / 100) * int(data['exchange_dwellings'])
    if tech == 'adsl':
        quantity = (int(data['adsl_availability']) / 100) * int(data['exchange_dwellings'])
    if quantity < 0:
        quantity = 0

    return quantity


def _get_prems_with_tech(tech_availability_percentage, total_prems):

    if tech_availability_percentage > 0:
        result = (tech_availability_percentage / 100) * total_prems
    else:
        result = 0

    return result


def _calculate_percentage(numerator, denominator):

    if numerator == 0 or denominator == 0:
        result = 0
    else:
        result = round(numerator / denominator * 100)

    return result


def _generic_connection_capacity(technology):

    # determine connection_capacity
    if technology == 'fttp':
        connection_capacity = 1000
    elif technology == 'fttdp':
        connection_capacity = 300
    elif technology == 'fttc':
        connection_capacity = 80
    # elif technology == 'docsis3':
    #     connection_capacity = 150
    elif technology == 'adsl':
        connection_capacity = 24

    return connection_capacity
