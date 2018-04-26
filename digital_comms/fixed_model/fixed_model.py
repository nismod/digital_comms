"""Cambridge Communications Assessment Model
"""
from collections import defaultdict
from itertools import tee
from pprint import pprint
from math import ceil

class ICTManager(object):
    """Model controller class."""

    def __init__(self, assets, links, parameters):
        self._links = {link['origin']:Link(link, parameters) for link in links}

        self._premises = [Premise(premise, self._links.get(premise['id'], None), parameters) for premise in assets['premises']]
        premises = defaultdict(list)
        for premise in self._premises:
            premises[premise.connection].append(premise)

        self._distributions = [Distribution(distribution, premises[distribution['id']], self._links.get(distribution['id'], None), parameters) for distribution in assets['distributions']]
        distributions = defaultdict(list)
        for distribution in self._distributions:
            distributions[distribution.connection].append(distribution)

        self._cabinets = [Cabinet(cabinet, distributions[cabinet['id']], self._links.get(cabinet['id'], None), parameters) for cabinet in assets['cabinets']]
        cabinets = defaultdict(list)
        for cabinet in self._cabinets:
            cabinets[cabinet.connection].append(cabinet)

        self._exchanges = [Exchange(exchange, cabinets[exchange['id']], parameters) for exchange in assets['exchanges']]

    def upgrade(self, interventions):

        for asset_id, action, costs in interventions:

            if asset_id.startswith('distribution'):
                print(asset_id)
                distribution = [distribution for distribution in self._distributions if distribution.id == asset_id][0]
                distribution.upgrade(action)
            
            if asset_id.startswith('cabinet'):
                print(asset_id)
                cabinet = [cabinet for cabinet in self._cabinets if cabinet.id == asset_id][0]
                cabinet.upgrade(action)


    @property # shortcut for creating a read-only property
    def assets(self):
        """Returns a certain subset of links"""
        return {
            'premises':         self._premises,
            'distributions':    self._distributions,
            'cabinets':         self._cabinets,
            'exchanges':        self._exchanges
        }

    @property # shortcut for creating a read-only property
    def links(self):
        """Returns a certain subset of links"""
        return {
            'premises':         [link for link in self._links.values() if link.origin.startswith('premise')],
            'distributions':    [link for link in self._links.values() if link.origin.startswith('distribution')],
            'cabinets':         [link for link in self._links.values() if link.origin.startswith('cabinet')],
            'exchanges':        [link for link in self._links.values() if link.origin.startswith('exchange')]
        }

    @property # shortcut for creating a read-only property
    def number_of_assets(self):
        """obj: Number of assets in the model
        """
        return {
            'premises':         len(self.assets['premises']),
            'distributions':    len(self.assets['distributions']),
            'cabinets':         len(self.assets['cabinets']),
            'exchanges':        len(self.assets['exchanges']),
        }

    @property # shortcut for creating a read-only property
    def number_of_links(self):
        """obj: Number of links in the model
        """
        return {
            'premises':         len(self.links['premises']),
            'distributions':    len(self.links['distributions']),
            'cabinets':         len(self.links['cabinets']),
            'exchanges':        len(self.links['exchanges']),
        }

    @property # shortcut for creating a read-only property
    def total_link_length(self):
        """obj: Total link length in the model
        """
        return {
            'premises':         sum(link.length for link in self.links['premises']),
            'distributions':    sum(link.length for link in self.links['distributions']),
            'cabinets':         sum(link.length for link in self.links['cabinets'])
        }

    @property # shortcut for creating a read-only property
    def avg_link_length(self):
        return {
            'premises':         self.total_link_length['premises'] / self.number_of_links['premises'],
            'distributions':    self.total_link_length['distributions'] / self.number_of_links['distributions'],
            'cabinets':         self.total_link_length['cabinets'] / self.number_of_links['cabinets']
        }


class Exchange(object):
    """Exchanges"""

    def __init__(self, data, clients, parameters):
        self.id = data["id"]
        self.fttp = data["FTTP"]
        self.gfast = data["GFast"]
        self.fttc = data["FTTC"]
        self.adsl = data["ADSL"]

        self.parameters = parameters
        self._clients = clients

        self.compute()

    def compute(self):
        # Upgrade costs
        self.upgrade_costs = {}
        self.upgrade_costs['fttp'] = self.parameters['costs']['assets']['exchange']['fttp'] if self.fttp == 0 else 0
        self.upgrade_costs['gfast'] = self.parameters['costs']['assets']['exchange']['gfast'] if self.gfast == 0 else 0
        self.upgrade_costs['fttc'] = self.parameters['costs']['assets']['exchange']['fttc'] if self.fttc == 0 else 0
        self.upgrade_costs['adsl'] = self.parameters['costs']['assets']['exchange']['adsl'] if self.adsl == 0 else 0

        # Rollout costs
        self.rollout_costs = {}
        self.rollout_costs['fttp'] = self.upgrade_costs['fttp'] + sum(client.rollout_costs['fttp'] for client in self._clients)
        self.rollout_costs['gfast'] = self.upgrade_costs['gfast'] + sum(client.rollout_costs['gfast'] for client in self._clients)
        self.rollout_costs['fttc'] = self.upgrade_costs['fttc'] + sum(client.rollout_costs['fttc'] for client in self._clients)
        self.rollout_costs['adsl'] = self.upgrade_costs['adsl'] + sum(client.rollout_costs['adsl'] for client in self._clients)

        # Rollout benefits
        self.rollout_benefits = {}
        self.rollout_benefits['fttp'] = sum(client.rollout_benefits['fttp'] for client in self._clients)
        self.rollout_benefits['gfast'] = sum(client.rollout_benefits['gfast'] for client in self._clients)
        self.rollout_benefits['fttc'] = sum(client.rollout_benefits['fttc'] for client in self._clients)
        self.rollout_benefits['adsl'] = sum(client.rollout_benefits['adsl'] for client in self._clients)

        # Benefit-cost ratio
        self.rollout_bcr = {}
        self.rollout_bcr['fttp'] = _calculate_benefit_cost_ratio(self.rollout_benefits['fttp'], self.rollout_costs['fttp'])
        self.rollout_bcr['gfast'] = _calculate_benefit_cost_ratio(self.rollout_benefits['gfast'], self.rollout_costs['gfast'])
        self.rollout_bcr['fttc'] = _calculate_benefit_cost_ratio(self.rollout_benefits['fttc'], self.rollout_costs['fttc'])
        self.rollout_bcr['adsl'] = _calculate_benefit_cost_ratio(self.rollout_benefits['adsl'], self.rollout_costs['adsl'])

    def __repr__(self):
        return "<Exchange id:{}>".format(self.id)


class Cabinet(object):
    """Cabinets"""
    def __repr__(self):
        return "<Cabinet id:{}>".format(self.id)

    def __init__(self, data, clients, link, parameters):

        # Asset parameters
        self.id = data["id"]
        self.connection = data["connection"]
        self.fttp = data["FTTP"]
        self.gfast = data["GFast"]
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
            (self.parameters['costs']['assets']['cabinet']['fttp']['32_ports'] * ceil(len(self._clients) / 32)
             if self.fttp == 0 else 0)
            + 
            (self.link.upgrade_costs['fiber'] if self.link != None else 0)
        )
        self.upgrade_costs['gfast'] = (
            (self.parameters['costs']['assets']['cabinet']['gfast'] if self.gfast == 0 else 0)
            + 
            (self.link.upgrade_costs['fiber'] if self.link != None else 0)
        )
        self.upgrade_costs['fttc'] = (
            (self.parameters['costs']['assets']['cabinet']['fttc'] if self.fttc == 0 else 0)
            + 
            (self.link.upgrade_costs['fiber'] if self.link != None else 0)
        )
        self.upgrade_costs['adsl'] = (
            (self.parameters['costs']['assets']['cabinet']['adsl'] if self.adsl == 0 else 0)
            +
            (self.link.upgrade_costs['copper'] if self.link != None else 0)
        )

        # Rollout costs
        self.rollout_costs = {}
        self.rollout_costs['fttp'] = self.upgrade_costs['fttp'] + sum(client.rollout_costs['fttp'] for client in self._clients)
        self.rollout_costs['gfast'] = self.upgrade_costs['gfast'] + sum(client.rollout_costs['gfast'] for client in self._clients)
        self.rollout_costs['fttc'] = self.upgrade_costs['fttc'] + sum(client.rollout_costs['fttc'] for client in self._clients)
        self.rollout_costs['adsl'] = self.upgrade_costs['adsl'] + sum(client.rollout_costs['adsl'] for client in self._clients)

        # Rollout benefits
        self.rollout_benefits = {}
        self.rollout_benefits['fttp'] = sum(client.rollout_benefits['fttp'] for client in self._clients)
        self.rollout_benefits['gfast'] = sum(client.rollout_benefits['gfast'] for client in self._clients)
        self.rollout_benefits['fttc'] = sum(client.rollout_benefits['fttc'] for client in self._clients)
        self.rollout_benefits['adsl'] = sum(client.rollout_benefits['adsl'] for client in self._clients)

        # Benefit-cost ratio
        self.rollout_bcr = {}
        self.rollout_bcr['fttp'] = _calculate_benefit_cost_ratio(self.rollout_benefits['fttp'], self.rollout_costs['fttp'])
        self.rollout_bcr['gfast'] = _calculate_benefit_cost_ratio(self.rollout_benefits['gfast'], self.rollout_costs['gfast'])
        self.rollout_bcr['fttc'] = _calculate_benefit_cost_ratio(self.rollout_benefits['fttc'], self.rollout_costs['fttc'])
        self.rollout_bcr['adsl'] = _calculate_benefit_cost_ratio(self.rollout_benefits['adsl'], self.rollout_costs['adsl'])

    def upgrade(self, action):

        if action == 'rollout_fttp':
            self.fttp = 1
            if self.link != None:
                self.link.upgrade('fiber')
            for client in self._clients:
                client.upgrade(action)

        self.compute()


class Distribution(object):
    """Distribution"""

    def __init__(self, data, clients, link, parameters):

        # Asset parameters
        self.id = data["id"]
        self.connection = data["connection"]
        self.fttp = data["FTTP"]
        self.gfast = data["GFast"]
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
            (self.parameters['costs']['assets']['distribution']['fttp']['32_ports'] * ceil(len(self._clients) / 32) 
             if self.fttp == 0 else 0)
            + 
            (self.link.upgrade_costs['fiber'] if self.link != None else 0)
        )
        self.upgrade_costs['gfast'] = (
            (self.parameters['costs']['assets']['distribution']['gfast']['4_ports'] * ceil(len(self._clients) / 4) 
             if self.gfast == 0 else 0)
            +
            (self.link.upgrade_costs['fiber'] if self.link != None else 0)
        )
        self.upgrade_costs['fttc'] = (
            (self.parameters['costs']['assets']['distribution']['fttc'] if self.fttc == 0 else 0)
            +
            (self.link.upgrade_costs['copper'] if self.link != None else 0)
        )
        self.upgrade_costs['adsl'] = (
            (self.parameters['costs']['assets']['distribution']['adsl'] if self.adsl == 0 else 0)
            +
            (self.link.upgrade_costs['copper'] if self.link != None else 0)
        )

        # Rollout costs
        self.rollout_costs = {}
        self.rollout_costs['fttp'] = self.upgrade_costs['fttp'] + sum(client.rollout_costs['fttp'] for client in self._clients)
        self.rollout_costs['gfast'] = self.upgrade_costs['gfast'] + sum(client.rollout_costs['gfast'] for client in self._clients)
        self.rollout_costs['fttc'] = self.upgrade_costs['fttc'] + sum(client.rollout_costs['fttc'] for client in self._clients)
        self.rollout_costs['adsl'] = self.upgrade_costs['adsl'] + sum(client.rollout_costs['adsl'] for client in self._clients)

        # Rollout benefits
        self.rollout_benefits = {}
        self.rollout_benefits['fttp'] = sum(client.rollout_benefits['fttp'] for client in self._clients)
        self.rollout_benefits['gfast'] = sum(client.rollout_benefits['gfast'] for client in self._clients)
        self.rollout_benefits['fttc'] = sum(client.rollout_benefits['fttc'] for client in self._clients)
        self.rollout_benefits['adsl'] = sum(client.rollout_benefits['adsl'] for client in self._clients)

        # Benefit-cost ratio
        self.rollout_bcr = {}
        self.rollout_bcr['fttp'] = _calculate_benefit_cost_ratio(self.rollout_benefits['fttp'], self.rollout_costs['fttp'])
        self.rollout_bcr['gfast'] = _calculate_benefit_cost_ratio(self.rollout_benefits['gfast'], self.rollout_costs['gfast'])
        self.rollout_bcr['fttc'] = _calculate_benefit_cost_ratio(self.rollout_benefits['fttc'], self.rollout_costs['fttc'])
        self.rollout_bcr['adsl'] = _calculate_benefit_cost_ratio(self.rollout_benefits['adsl'], self.rollout_costs['adsl'])

    def __repr__(self):
        return "<Distribution id:{}>".format(self.id)

    def upgrade(self, action):

        if action == 'rollout_fttp':
            self.fttp = 1
            if self.link != None:
                self.link.upgrade('fiber')
            for client in self._clients:
                client.upgrade(action)

        self.compute()


class Premise(object):
    """Premise"""

    def __init__(self, data, link, parameters):

        # Parameters
        self.id = data['id']
        self.connection = data['connection']
        self.fttp = data['FTTP']
        self.gfast = data['GFast']
        self.fttc = data['FTTC']
        self.adsl = data['ADSL']
        self.parameters = parameters

        # Link parameters
        self.link = link
        self.compute()

    def compute(self):

        # Upgrade costs
        self.upgrade_costs = {}
        self.upgrade_costs['fttp'] = (
              (self.parameters['costs']['assets']['premise']['fttp']['modem'] if self.fttp == 0 else 0)
            + (self.parameters['costs']['assets']['premise']['fttp']['optical_network_terminator'] if self.fttp == 0 else 0)
            + self.link.upgrade_costs['fiber']
        )
        self.upgrade_costs['gfast'] = (
              (self.parameters['costs']['assets']['premise']['gfast']['modem'] if self.gfast == 0 else 0)
            + self.link.upgrade_costs['fiber']
        )
        self.upgrade_costs['fttc'] = (
              (self.parameters['costs']['assets']['premise']['fttc']['modem'] if self.fttc == 0 else 0)
            + self.link.upgrade_costs['copper']
        )
        self.upgrade_costs['adsl'] = (
              (self.parameters['costs']['assets']['premise']['adsl']['modem'] if self.adsl == 0 else 0)
            + self.link.upgrade_costs['copper']
        )

        # Rollout costs
        self.rollout_costs = {}
        self.rollout_costs['fttp'] = self.upgrade_costs['fttp']
        self.rollout_costs['gfast'] = self.upgrade_costs['gfast']
        self.rollout_costs['fttc'] = self.upgrade_costs['fttc']
        self.rollout_costs['adsl'] = self.upgrade_costs['adsl']

        # Rollout benefits
        self.rollout_benefits = {}
        self.rollout_benefits['fttp'] = self.parameters['benefits']['assets']['premise']['fttp']
        self.rollout_benefits['gfast'] = self.parameters['benefits']['assets']['premise']['gfast']
        self.rollout_benefits['fttc'] = self.parameters['benefits']['assets']['premise']['fttc']
        self.rollout_benefits['adsl'] = self.parameters['benefits']['assets']['premise']['adsl']

        # Benefit-cost ratio
        self.rollout_bcr = {}
        self.rollout_bcr['fttp'] = _calculate_benefit_cost_ratio(self.rollout_benefits['fttp'], self.rollout_costs['fttp'])
        self.rollout_bcr['gfast'] = _calculate_benefit_cost_ratio(self.rollout_benefits['gfast'], self.rollout_costs['gfast'])
        self.rollout_bcr['fttc'] = _calculate_benefit_cost_ratio(self.rollout_benefits['fttc'], self.rollout_costs['fttc'])
        self.rollout_bcr['adsl'] = _calculate_benefit_cost_ratio(self.rollout_benefits['adsl'], self.rollout_costs['adsl'])

    def __repr__(self):
        return "<Premise id:{}>".format(self.id)

    def upgrade(self, action):

        if action == 'rollout_fttp':
            self.fttp = 1
            self.link.upgrade('fiber')

        self.compute()


class Link(object):
    """Links"""

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
        self.upgrade_costs['fiber'] = self.parameters['costs']['links']['fiber']['meter'] * self.length if self.technology != 'fiber' else 0
        self.upgrade_costs['copper'] = self.parameters['costs']['links']['copper']['meter'] * self.length if self.technology != 'copper' else 0

    def __repr__(self):
        return "<Link origin:{} dest:{} length:{}>".format(self.origin, self.dest, self.length)

    def upgrade(self, technology):
        if technology == 'fiber':
            self.technology = 'fiber'
        
        self.compute()


def _calculate_benefit_cost_ratio(benefits, costs):
    try:
        return benefits / costs
    except ZeroDivisionError:
        return 0