"""Cambridge Communications Assessment Model
"""
from collections import defaultdict
from itertools import tee
from pprint import pprint
from math import ceil

#####################
# MODEL
#####################

class NetworkManager(object):
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
    upgrade
        Takes intervention decisions and builds them.
    update_adoption_desirability
        Takes exogenously defined annual demand and updates premises adoption desirability.
    coverage
        Allocates premises-level technology technologies to a dict of coverage_results by Local Authority District.
    aggregate_coverage
        Calculates the sum and percentage coverage of premises-level technology by Local Authority District.
    capacity
        Calculates the average premises connection.

    """

    def __init__(self, assets, links, parameters):
        self._links = {
        }

        self._links_from_premises = []
        self._links_from_distributions = []
        self._links_from_cabinets = []
        self._links_from_exchanges = []
        for link_dict in links:
            link = Link(link_dict, parameters)
            origin = link.origin
            self._links[origin] = link
            if origin.startswith('premise'):
                self._links_from_premises.append(link)
            elif origin.startswith('distribution'):
                self._links_from_distributions.append(link)
            elif origin.startswith('cabinet'):
                self._links_from_cabinets.append(link)
            elif origin.startswith('exchange'):
                self._links_from_exchanges.append(link)

        self._premises = []
        self._premises_by_id = {}
        self._premises_by_lad = defaultdict(list)
        self._premises_by_dist = defaultdict(list)
        for premise in assets['premises']:
            premise = Premise(
                premise,
                self._links.get(premise['id'], None),
                parameters
            )
            self._premises.append(premise)
            self._premises_by_id[premise.id] = premise
            self._premises_by_lad[premise.lad].append(premise)
            self._premises_by_dist[premise.connection].append(premise)

        self._distributions = []
        self._distributions_by_cab = defaultdict(list)
        for distribution in assets['distributions']:
            distribution = Distribution(
                distribution,
                self._premises_by_dist[distribution['id']],
                self._links.get(distribution['id'], None),
                parameters
            )
            self._distributions.append(distribution)
            self._distributions_by_cab[distribution.connection].append(distribution)

        self._cabinets = []
        self._cabinets_by_exchange = defaultdict(list)
        for cabinet in assets['cabinets']:
            cabinet = Cabinet(
                cabinet,
                self._distributions_by_cab[cabinet['id']],
                self._links.get(cabinet['id'], None),
                parameters
            )
            self._cabinets.append(cabinet)
            self._cabinets_by_exchange[cabinet.connection].append(cabinet)

        self._exchanges = []
        for exchange in assets['exchanges']:
            exchange = Exchange(
                exchange,
                self._cabinets_by_exchange[exchange['id']],
                parameters
            )
            self._exchanges.append(exchange)

    def upgrade(self, interventions):

        for asset_id, technology, policy, delivery_type, cost in interventions:

            if asset_id.startswith('distribution'):
                distribution = [distribution for distribution in self._distributions if distribution.id == asset_id][0]
                distribution.upgrade(technology)

            if asset_id.startswith('cabinet'):
                cabinet = [cabinet for cabinet in self._cabinets if cabinet.id == asset_id][0]
                cabinet.upgrade(technology)

    def update_adoption_desirability(self, adoption_desirability):

        for premises_id, desirability_to_adopt in adoption_desirability:
            premises = self._premises_by_id[premises_id]
            premises.uprade_desirability_to_adopt(desirability_to_adopt)

    def coverage(self):
        """
        define coverage
        """
        premises_per_lad = self._premises_by_lad

        # run statistics on each lad
        coverage_results = {}

        for lad in premises_per_lad:
            sum_of_fttp = sum(premise.fttp for premise in premises_per_lad[lad]) # contain  list of premises objects in the lad
            sum_of_fttdp = sum(premise.fttdp for premise in premises_per_lad[lad]) # contain  list of premises objects in the lad
            sum_of_fttc = sum(premise.fttc for premise in premises_per_lad[lad]) # contain  list of premises objects in the lad
            sum_of_adsl = sum(premise.adsl for premise in premises_per_lad[lad]) # contain  list of premises objects in the lad

            num_premises = len(premises_per_lad[lad])

            coverage_results[lad] = {
                'num_premises': num_premises,
                'num_fttp': sum_of_fttp,
                'num_fttdp': sum_of_fttdp,
                'num_fttc': sum_of_fttc,
                'num_adsl': sum_of_adsl
            }

        return coverage_results

    def aggregate_coverage(self):
        """
        define aggregate coverage
        """
        premises_per_lad = self._premises_by_lad

        coverage_results = []
        for lad in premises_per_lad.keys():
            sum_of_fttp = sum(premise.fttp for premise in premises_per_lad[lad])
            sum_of_fttdp = sum(premise.fttdp for premise in premises_per_lad[lad])
            sum_of_fttc = sum(premise.fttc for premise in premises_per_lad[lad])
            sum_of_adsl = sum(premise.adsl for premise in premises_per_lad[lad])
            sum_of_premises = len(premises_per_lad[lad])

            coverage_results.append({
                'sum_of_fttp': sum_of_fttp,
                'sum_of_fttdp': sum_of_fttdp,
                'sum_of_fttc': sum_of_fttc,
                'sum_of_adsl': sum_of_adsl,
                'sum_of_premises': sum_of_premises
            })

        output = []

        for item in coverage_results:
            aggregate_fttp = sum(item['sum_of_fttp'] for item in coverage_results)
            aggregate_fttdp = sum(item['sum_of_fttdp'] for item in coverage_results)
            aggregate_fttc = sum(item['sum_of_fttc'] for item in coverage_results)
            aggregate_adsl = sum(item['sum_of_adsl'] for item in coverage_results)
            aggregate_premises = sum(item['sum_of_premises'] for item in coverage_results)

            output.append({
                'percentage_of_premises_with_fttp': aggregate_fttp,
                'percentage_of_premises_with_fttdp': aggregate_fttdp,
                'percentage_of_premises_with_fttc': aggregate_fttc,
                'percentage_of_premises_with_adsl': aggregate_adsl,
                'sum_of_premises': aggregate_premises
            })

        return output

    def capacity(self):
        """
        define capacity
        """

        # group premises by lads
        premises_per_lad = self._premises_by_lad

        capacity_results = defaultdict(dict)

        for lad in premises_per_lad.keys():
            summed_capacity = sum(premise.connection_capacity for premise in premises_per_lad[lad])
            number_of_connections = len(premises_per_lad[lad])

            capacity_results[lad] = {
                'average_capacity': round(summed_capacity / number_of_connections, 2),
            }

        return capacity_results


    @property # shortcut for creating a read-only property
    def assets(self):
        """Returns a certain subset of links"""
        return {
            'premises':         self._premises,
            'distributions':    self._distributions,
            'cabinets':         self._cabinets,
            'exchanges':        self._exchanges
        }

    @property
    def links(self):
        """Returns a certain subset of links"""
        return {
            'premises':         self._links_from_premises,
            'distributions':    self._links_from_distributions,
            'cabinets':         self._links_from_cabinets,
            'exchanges':        self._links_from_exchanges
        }

    @property
    def number_of_assets(self):
        """obj: Number of assets in the model
        """
        return {
            'premises':         len(self.assets['premises']),
            'distributions':    len(self.assets['distributions']),
            'cabinets':         len(self.assets['cabinets']),
            'exchanges':        len(self.assets['exchanges']),
        }

    @property
    def number_of_links(self):
        """obj: Number of links in the model
        """
        return {
            'premises':         len(self.links['premises']),
            'distributions':    len(self.links['distributions']),
            'cabinets':         len(self.links['cabinets']),
            'exchanges':        len(self.links['exchanges']),
        }

    @property
    def total_link_length(self):
        """obj: Total link length in the model
        """
        return {
            'premises':         sum(link.length for link in self.links['premises']),
            'distributions':    sum(link.length for link in self.links['distributions']),
            'cabinets':         sum(link.length for link in self.links['cabinets'])
        }

    @property
    def avg_link_length(self):
        return {
            'premises':         self.total_link_length['premises'] / self.number_of_links['premises'],
            'distributions':    self.total_link_length['distributions'] / self.number_of_links['distributions'],
            'cabinets':         self.total_link_length['cabinets'] / self.number_of_links['cabinets']
        }

    @property
    def lads(self):
        """Returns a list of lads which have premises
        """
        return list(self._premises_by_lad.keys())

class Exchange(object):
    """Exchange object

    Parameters
    ----------
    data : dict
        Contains asset data including, id, name, postcode, region, county and available technologies.
    clients : list_of_objects
        Contains all assets (Cabinets) served by an Exchange.
    parameters : dict
        Contains all parameters from 'digital_comms.yml'.

    Attributes
    ----------
    id
    fttp
    fttdp
    fttc
    adsl
    parameters
    compute()

    Methods
    -------
    compute
        Calculates upgrade costs and benefits.

    """

    def __init__(self, data, clients, parameters):
        self.id = data["id"]
        self.fttp = data["FTTP"]
        self.fttdp = data["GFast"]
        self.fttc = data["FTTC"]
        self.adsl = data["ADSL"]

        self.parameters = parameters
        self._clients = clients

        self.compute()

    def compute(self):
        # Upgrade costs
        self.upgrade_costs = {}
        self.upgrade_costs['fttp'] = self.parameters['costs_assets_exchange_fttp'] if self.fttp == 0 else 0
        self.upgrade_costs['fttdp'] = self.parameters['costs_assets_exchange_fttdp'] if self.fttdp == 0 else 0
        self.upgrade_costs['fttc'] = self.parameters['costs_assets_exchange_fttc'] if self.fttc == 0 else 0
        self.upgrade_costs['adsl'] = self.parameters['costs_assets_exchange_adsl'] if self.adsl == 0 else 0

        # Rollout costs
        self.rollout_costs = {}
        self.rollout_costs['fttp'] = self.upgrade_costs['fttp'] + sum(client.rollout_costs['fttp'] for client in self._clients)
        self.rollout_costs['fttdp'] = self.upgrade_costs['fttdp'] + sum(client.rollout_costs['fttdp'] for client in self._clients)
        self.rollout_costs['fttc'] = self.upgrade_costs['fttc'] + sum(client.rollout_costs['fttc'] for client in self._clients)
        self.rollout_costs['adsl'] = self.upgrade_costs['adsl'] + sum(client.rollout_costs['adsl'] for client in self._clients)

        # Rollout benefits
        self.rollout_benefits = {}
        self.rollout_benefits['fttp'] = sum(client.rollout_benefits['fttp'] for client in self._clients)
        self.rollout_benefits['fttdp'] = sum(client.rollout_benefits['fttdp'] for client in self._clients)
        self.rollout_benefits['fttc'] = sum(client.rollout_benefits['fttc'] for client in self._clients)
        self.rollout_benefits['adsl'] = sum(client.rollout_benefits['adsl'] for client in self._clients)

        # Benefit-cost ratio
        self.rollout_bcr = {}
        self.rollout_bcr['fttp'] = _calculate_benefit_cost_ratio(self.rollout_benefits['fttp'], self.rollout_costs['fttp'])
        self.rollout_bcr['fttdp'] = _calculate_benefit_cost_ratio(self.rollout_benefits['fttdp'], self.rollout_costs['fttdp'])
        self.rollout_bcr['fttc'] = _calculate_benefit_cost_ratio(self.rollout_benefits['fttc'], self.rollout_costs['fttc'])
        self.rollout_bcr['adsl'] = _calculate_benefit_cost_ratio(self.rollout_benefits['adsl'], self.rollout_costs['adsl'])

    def __repr__(self):
        return "<Exchange id:{}>".format(self.id)


class Cabinet(object):
    """Cabinet object

    Parameters
    ----------
    data : dict
        Contains asset data including, id, name, connection and available technologies.
    clients : list_of_objects
        Contains all assets served.
    link : TODO
        TODO
    parameters : dict
        Contains all parameters from 'digital_comms.yml'.

    Attributes
    ----------
    id
    connection
    fttp
    fttdp
    fttc
    adsl
    parameters
    link
    compute()

    Methods
    -------
    compute
        Calculates upgrade costs and benefits.

    """
    def __repr__(self):
        return "<Cabinet id:{}>".format(self.id)

    def __init__(self, data, clients, link, parameters):

        # Asset parameters
        self.id = data["id"]
        self.connection = data["connection"]
        self.fttp = data["FTTP"]
        self.fttdp = data["GFast"]
        self.fttc = data["FTTC"]
        self.adsl = data["ADSL"]
        self.parameters = parameters

        # Link parameters
        self._clients = clients
        self.link = link

        self.compute()

    def compute(self):

        # Upgrade costs
        self.upgrade_costs = {}
        self.upgrade_costs['fttp'] = (
            (self.parameters['costs_assets_upgrade_cabinet_fttp'] * ceil(len(self._clients) / 32)
             if self.fttp == 0 else 0)
            +
            (self.link.upgrade_costs['fibre'] if self.link != None else 0)
        )
        self.upgrade_costs['fttdp'] = (
            (self.parameters['costs_assets_cabinet_fttdp'] if self.fttdp == 0 else 0)
            +
            (self.link.upgrade_costs['fibre'] if self.link != None else 0)
        )
        self.upgrade_costs['fttc'] = (
            (self.parameters['costs_assets_cabinet_fttc'] if self.fttc == 0 else 0)
            +
            (self.link.upgrade_costs['fibre'] if self.link != None else 0)
        )
        self.upgrade_costs['adsl'] = (
            (self.parameters['costs_assets_cabinet_adsl'] if self.adsl == 0 else 0)
            +
            (self.link.upgrade_costs['copper'] if self.link != None else 0)
        )

        # Rollout costs
        self.rollout_costs = {}
        self.rollout_costs['fttp'] = self.upgrade_costs['fttp'] + sum(client.rollout_costs['fttp'] for client in self._clients)
        self.rollout_costs['fttdp'] = self.upgrade_costs['fttdp'] + sum(client.rollout_costs['fttdp'] for client in self._clients)
        self.rollout_costs['fttc'] = self.upgrade_costs['fttc'] + sum(client.rollout_costs['fttc'] for client in self._clients)
        self.rollout_costs['adsl'] = self.upgrade_costs['adsl'] + sum(client.rollout_costs['adsl'] for client in self._clients)

        # Rollout benefits
        self.rollout_benefits = {}
        self.rollout_benefits['fttp'] = sum(client.rollout_benefits['fttp'] for client in self._clients)
        self.rollout_benefits['fttdp'] = sum(client.rollout_benefits['fttdp'] for client in self._clients)
        self.rollout_benefits['fttc'] = sum(client.rollout_benefits['fttc'] for client in self._clients)
        self.rollout_benefits['adsl'] = sum(client.rollout_benefits['adsl'] for client in self._clients)

        # Benefit-cost ratio
        self.rollout_bcr = {}
        self.rollout_bcr['fttp'] = _calculate_benefit_cost_ratio(self.rollout_benefits['fttp'], self.rollout_costs['fttp'])
        self.rollout_bcr['fttdp'] = _calculate_benefit_cost_ratio(self.rollout_benefits['fttdp'], self.rollout_costs['fttdp'])
        self.rollout_bcr['fttc'] = _calculate_benefit_cost_ratio(self.rollout_benefits['fttc'], self.rollout_costs['fttc'])
        self.rollout_bcr['adsl'] = _calculate_benefit_cost_ratio(self.rollout_benefits['adsl'], self.rollout_costs['adsl'])

    def upgrade(self, action):

        if action == 'rollout_fttp':
            self.fttp = 1
            if self.link != None:
                self.link.upgrade('fibre')
            for client in self._clients:
                client.upgrade(action)

        if action == 'rollout_fttdp':
            self.fttp = 1
            if self.link != None:
                self.link.upgrade('fibre')
            for client in self._clients:
                client.upgrade(action)

        self.compute()


class Distribution(object):
    """Distribution object

    Parameters
    ----------
    data : dict
        Contains asset data including, id, name, connection and available technologies.
    clients : list_of_objects
        Contains all assets served.
    link : TODO
        TODO
    parameters : dict
        Contains all parameters from 'digital_comms.yml'.

    Attributes
    ----------
    id
    connection
    fttp
    fttdp
    fttc
    adsl
    parameters
    link
    compute()

    Methods
    -------
    compute
        Calculates upgrade costs and benefits.
    upgrade
        Upgrades any links with new technology.

    """

    def __init__(self, data, clients, link, parameters):

        # Asset parameters
        self.id = data["id"]
        self.connection = data["connection"]
        self.fttp = data["FTTP"]
        self.fttdp = data["GFast"]
        self.fttc = data["FTTC"]
        self.adsl = data["ADSL"]
        self.parameters = parameters

        # Link parameters
        self._clients = clients
        self.link = link

        self.compute()

    def compute(self):

        # Upgrade costs
        self.upgrade_costs = {}
        self.upgrade_costs['fttp'] = (
            (self.parameters['costs_assets_premise_fttp_optical_connection_point'] * ceil(len(self._clients) / 32)
             if self.fttp == 0 else 0)
            +
            (self.link.upgrade_costs['fibre'] if self.link != None else 0)
        )
        self.upgrade_costs['fttdp'] = (
            (self.parameters['costs_assets_distribution_fttdp_8_ports'] * ceil(len(self._clients) / 8)
             if self.fttdp == 0 else 0)
            +
            (self.link.upgrade_costs['fibre'] if self.link != None else 0)
        )
        self.upgrade_costs['fttc'] = (
            (self.parameters['costs_assets_distribution_fttc'] if self.fttc == 0 else 0)
            +
            (self.link.upgrade_costs['copper'] if self.link != None else 0)
        )
        self.upgrade_costs['adsl'] = (
            (self.parameters['costs_assets_distribution_adsl'] if self.adsl == 0 else 0)
            +
            (self.link.upgrade_costs['copper'] if self.link != None else 0)
        )

        # Rollout costs
        self.rollout_costs = {}
        self.rollout_costs['fttp'] = self.upgrade_costs['fttp'] + sum(client.rollout_costs['fttp'] for client in self._clients)
        self.rollout_costs['fttdp'] = self.upgrade_costs['fttdp'] + sum(client.rollout_costs['fttdp'] for client in self._clients)
        self.rollout_costs['fttc'] = self.upgrade_costs['fttc'] + sum(client.rollout_costs['fttc'] for client in self._clients)
        self.rollout_costs['adsl'] = self.upgrade_costs['adsl'] + sum(client.rollout_costs['adsl'] for client in self._clients)

        # Rollout benefits
        self.rollout_benefits = {}
        self.rollout_benefits['fttp'] = sum(client.rollout_benefits['fttp'] for client in self._clients)
        self.rollout_benefits['fttdp'] = sum(client.rollout_benefits['fttdp'] for client in self._clients)
        self.rollout_benefits['fttc'] = sum(client.rollout_benefits['fttc'] for client in self._clients)
        self.rollout_benefits['adsl'] = sum(client.rollout_benefits['adsl'] for client in self._clients)

        # Benefit-cost ratio
        self.rollout_bcr = {}
        self.rollout_bcr['fttp'] = _calculate_benefit_cost_ratio(self.rollout_benefits['fttp'], self.rollout_costs['fttp'])
        self.rollout_bcr['fttdp'] = _calculate_benefit_cost_ratio(self.rollout_benefits['fttdp'], self.rollout_costs['fttdp'])
        self.rollout_bcr['fttc'] = _calculate_benefit_cost_ratio(self.rollout_benefits['fttc'], self.rollout_costs['fttc'])
        self.rollout_bcr['adsl'] = _calculate_benefit_cost_ratio(self.rollout_benefits['adsl'], self.rollout_costs['adsl'])

    def __repr__(self):
        return "<Distribution id:{}>".format(self.id)

    def upgrade(self, action):

        if action in ('fttp', 'fttp'):
            action = 'fttp'
            self.fttp = 1
            if self.link != None:
                self.link.upgrade('fibre')
            for client in self._clients:
                client.upgrade(action)

        if action in ('fttdp', 'fttdp'):
            action = 'fttdp'
            self.fttdp = 1
            if self.link != None:
                self.link.upgrade('fibre')
            for client in self._clients:
                client.upgrade(action)

        self.compute()

class Premise(object):
    """Premise object

    Parameters
    ----------
    data : dict
        Contains asset data including, id, name, connection and available technologies.
    link : TODO
        TODO
    parameters : dict
        Contains all parameters from 'digital_comms.yml'.

    Attributes
    ----------
    id
    connection
    fttp
    fttdp
    fttc
    adsl
    wta
    wtp
    adoption_desirability
    parameters
    link
    compute()

    Methods
    -------
    compute
        Calculates upgrade costs and benefits.
    upgrade
        Upgrades any links with new technology.
    update_desirability_to_adopt
        Update premises desirability to adopt.

    """

    def __init__(self, data, link, parameters):

        # Parameters
        self.id = data['id']
        self.connection = data['connection']
        self.fttp = 0 #data['FTTP']
        self.fttdp = 0 #data['FTTdp'] # FTTdp indicator is incorrect. Probably counting DOCSIS. Using FTTP for now.
        self.fttc = data['FTTC']
        self.adsl = data['ADSL']
        self.lad = data['lad']
        self.wta = data['wta']
        self.wtp = data['wtp']
        self.adoption_desirability = False

        self.parameters = parameters

        # Link parameters
        self.link = link
        self.compute()

    def compute(self):

        # Upgrade costs
        self.upgrade_costs = {}
        self.upgrade_costs['fttp'] = (
              (self.parameters['costs_assets_premise_fttp_modem'] if self.fttp == 0 else 0)
            + (self.parameters['costs_assets_premise_fttp_optical_network_terminator'] if self.fttp == 0 else 0)
            + (self.parameters['planning_administration_cost'] if self.fttp == 0 else 0)
            + self.link.upgrade_costs['fibre']
        )
        self.upgrade_costs['fttdp'] = (
              (self.parameters['costs_assets_premise_fttdp_modem'] if self.fttdp == 0 else 0)
            + self.link.upgrade_costs['copper']
        )
        self.upgrade_costs['fttc'] = (
              (self.parameters['costs_assets_premise_fttc_modem'] if self.fttc == 0 else 0)
            + self.link.upgrade_costs['copper']
        )
        self.upgrade_costs['adsl'] = (
              (self.parameters['costs_assets_premise_adsl_modem'] if self.adsl == 0 else 0)
            + self.link.upgrade_costs['copper']
        )
        # Rollout costs
        self.rollout_costs = {}
        self.rollout_costs['fttp'] = int(round(self.upgrade_costs['fttp'],0))
        self.rollout_costs['fttdp'] = int(round(self.upgrade_costs['fttdp'],0))
        self.rollout_costs['fttc'] = self.upgrade_costs['fttc']
        self.rollout_costs['adsl'] = self.upgrade_costs['adsl']

        # Rollout benefits
        self.rollout_benefits = {}
        self.rollout_benefits['fttp'] = (int(self.wtp) * self.parameters['months_per_year'] * self.parameters['payback_period'] * ((100-self.parameters['profit_margin'])/100)) if self.adoption_desirability else 0
        self.rollout_benefits['fttdp'] = (int(self.wtp) * self.parameters['months_per_year'] * self.parameters['payback_period'] * ((100-self.parameters['profit_margin'])/100)) if self.adoption_desirability else 0
        self.rollout_benefits['fttc'] = (int(self.wtp) * self.parameters['months_per_year'] * self.parameters['payback_period'] * ((100-self.parameters['profit_margin'])/100)) if self.adoption_desirability else 0
        self.rollout_benefits['adsl'] = (int(self.wtp) * self.parameters['months_per_year'] * self.parameters['payback_period'] * ((100-self.parameters['profit_margin'])/100)) if self.adoption_desirability else 0

        # Benefit-cost ratio
        self.rollout_bcr = {}
        self.rollout_bcr['fttp'] = int(_calculate_benefit_cost_ratio(self.rollout_benefits['fttp'], self.rollout_costs['fttp']))
        self.rollout_bcr['fttdp'] = int(_calculate_benefit_cost_ratio(self.rollout_benefits['fttdp'], self.rollout_costs['fttdp']))
        self.rollout_bcr['fttc'] = _calculate_benefit_cost_ratio(self.rollout_benefits['fttc'], self.rollout_costs['fttc'])
        self.rollout_bcr['adsl'] = _calculate_benefit_cost_ratio(self.rollout_benefits['adsl'], self.rollout_costs['adsl'])

        #determine best_connection:
        if self.fttp == 1:
            self.best_connection = 'fttp'
        elif self.fttdp == 1:
            self.best_connection = 'fttdp'
        elif self.fttc == 1:
            self.best_connection = 'fttc'
        else:
            self.best_connection = 'adsl'

        #determine connection_capacity
        if self.best_connection == 'fttp' :
            self.connection_capacity = 250
        elif self.best_connection == 'fttdp':
            self.connection_capacity = 100
        elif self.best_connection == 'fttc':
            self.connection_capacity = 50
        else:
            self.connection_capacity = 10

    def __repr__(self):
        return "<Premise id:{}>".format(self.id)

    def upgrade(self, action):
        if action in ('rollout_fttp', 'subsidised_fttp'):
            action = 'rollout_fttp'
            self.fttp = 1
            self.link.upgrade('fibre')
        if action in ('rollout_fttdp', 'subsidised_fttdp'):
            action = 'rollout_fttdp'
            self.fttdp = 1

        self.compute()

    def update_desirability_to_adopt(self, desirability_to_adopt):

        self.adoption_desirability = True

class Link(object):
    """Link object

    Parameters
    ----------
    data : list_of_dicts
        TODO
    parameters : dict
        Contains all parameters from 'digital_comms.yml'.

    Attributes
    ----------
    origin
    dest
    technology
    length
    parameters
    compute()

    Methods
    -------
    compute
        Calculates upgrade costs and benefits.
    upgrade
        Upgrades any links with new technology.

    """

    def __init__(self, data, parameters):
        self.origin = data["origin"]
        self.dest = data["dest"]
        self.technology = data["technology"]
        self.length = data["length"]

        self.parameters = parameters
        self.compute()

    def compute(self):

        # Upgrade costs
        self.upgrade_costs = {}
        self.upgrade_costs['fibre'] = self.parameters['costs_links_fibre_meter'] * float(self.length) if self.technology != 'fibre' else 0
        self.upgrade_costs['copper'] = self.parameters['costs_links_copper_meter'] * float(self.length) if self.technology != 'copper' else 0

    def __repr__(self):
        return "<Link origin:{} dest:{} length:{}>".format(self.origin, self.dest, self.length)

    def upgrade(self, technology):
        if technology == 'fibre':
            self.technology = 'fibre'

        self.compute()

def _calculate_benefit_cost_ratio(benefits, costs):
    try:
        return benefits / costs
    except ZeroDivisionError:
        return 0
