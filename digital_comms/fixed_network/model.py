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
        define capacity
        """
        technologies = ['fttp', 'fttdp', 'fttc', 'adsl'] #'docsis3',

        capacity_results = []

        for asset in self._exchanges:
            capacity_by_technology = []
            total_prems = getattr(asset, 'total_prems')

            if asset.fttp == total_prems:
                if asset.fttp > 0:
                #so expect 20 prems at 1000 each = 1000 mean
                    average_capacity = (
                        asset.fttp * asset.connection_capacity('fttp')
                        / asset.total_prems
                    )
                else:
                    average_capacity = 0
            elif asset.fttdp == total_prems:
                #so expect 20 prems at 300 each = 300 mean
                if asset.fttp == 0:
                    average_capacity = (
                        asset.fttdp * asset.connection_capacity('fttdp')
                        / asset.total_prems
                    )
                else:
                #so expect 10 prems at 300 each and 10 at 1000 = 650 mean
                    new_fttdp = asset.fttp - asset.fttdp
                    average_capacity = (
                        ((asset.fttp * asset.connection_capacity('fttp')) +
                        (new_fttdp * asset.connection_capacity('fttdp'))) /
                        asset.total_prems
                    )
            else:
                for technology in technologies:
                    number_of_premises_with_technology = getattr(asset, technology)
                    if technology == 'adsl':
                        fttp = getattr(asset, 'fttp')
                        fttdp = getattr(asset, 'fttdp')
                        fttc = getattr(asset, 'fttc')
                        # docsis3 = getattr(asset, 'docsis3')

                        number_of_premises_with_technology = total_prems - (
                            fttp + fttdp + fttc #+ docsis3
                        )

                        if number_of_premises_with_technology < 0:
                            number_of_premises_with_technology == 0
                        else:
                            pass

                    technology_capacity = asset.connection_capacity(technology)
                    capacity = technology_capacity * number_of_premises_with_technology
                    capacity_by_technology.append(capacity)

                summed_capacity = sum(capacity_by_technology)

                number_of_connections = asset.total_prems

                average_capacity = round(summed_capacity / number_of_connections)

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

    """
    def __init__(self, data, simulation_parameters):

        self.id = data["exchange_id"]
        self.lad = data["lad_id"]
        self.area = data['exchange_area']

        self.fttp = _determine_technology(data, 'fttp')
        self.fttdp = 0
        self.fttc = _determine_technology(data, 'fttc')
        self.adsl = _determine_technology(data, 'adsl')
        self.total_prems = int(data['exchange_dwellings'])

        self.fttp_unserved = self.fttp / self.area
        self.fttdp_unserved = self.fttdp / self.area
        self.fttc_unserved = self.fttc / self.area

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
            self.fttdp = 0
            self.gfast = 0
            self.fttc = 0
            # self._docsis3 = 0
            self.adsl = 0

        elif action in ('fttdp'):
            self.fttdp = self.total_prems - self.fttp
            self.gfast = 0
            self.fttc = 0
            # self._docsis3 = 0
            self.adsl = 0


    def connection_capacity(self, technology):
        capacity = _generic_connection_capacity(technology)
        return capacity


def _determine_technology(data, tech):

    if tech == 'fttp':
        quantity = int(data['fttp_availability'])
    # if tech == 'fttdp':
    #     quantity = data['fttdp_availability'] - data['fttp_availability']
    # if tech == 'gfast':
    #     quantity = data['gfast_availability'] - data['fttp_availability']
    if tech == 'fttc':
        quantity = data['fttc_availability'] - data['fttp_availability']
    if tech == 'adsl':
        quantity = 100 - int(data['fttc_availability']) #+ int(data['fttp_availability'])
    if quantity < 0:
        quantity = 0

    return quantity

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
