"""Cambridge Communications Assessment Model
"""
from collections import defaultdict
from itertools import tee
from pprint import pprint

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

    @property
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
            'premises':         [link for link in self._links.values() if link.origin.startswith('premise')],
            'distributions':    [link for link in self._links.values() if link.origin.startswith('distribution')],
            'cabinets':         [link for link in self._links.values() if link.origin.startswith('cabinet')],
            'exchanges':        [link for link in self._links.values() if link.origin.startswith('exchange')]
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

class Exchange(object):
    """Exchanges"""

    def __init__(self, data, clients, parameters):
        self.id = data["id"]
        self.fttp = data["FTTP"]
        self.gfast = data["GFast"]
        self.fttc = data["FTTC"]
        self.adsl = data["ADSL"]

        self._clients = clients

        # Upgrade costs
        self.upgrade_costs = {}
        self.upgrade_costs['fttp'] = parameters['costs']['assets']['exchange']['fttp'] if self.fttp == 0 else 0
        self.upgrade_costs['gfast'] = parameters['costs']['assets']['exchange']['gfast'] if self.gfast == 0 else 0
        self.upgrade_costs['fttc'] = parameters['costs']['assets']['exchange']['fttc'] if self.fttc == 0 else 0
        self.upgrade_costs['adsl'] = parameters['costs']['assets']['exchange']['adsl'] if self.adsl == 0 else 0

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
        try:
            self.rollout_bcr['fttp'] = self.rollout_benefits['fttp'] / self.rollout_costs['fttp']
        except ZeroDivisionError:
            self.rollout_bcr['fttp'] = 0
        try:    
            self.rollout_bcr['gfast'] = self.rollout_benefits['gfast'] / self.rollout_costs['gfast']
        except ZeroDivisionError:
            self.rollout_bcr['gfast'] = 0
        try:
            self.rollout_bcr['fttc'] = self.rollout_benefits['fttc'] / self.rollout_costs['fttc']
        except ZeroDivisionError:
            self.rollout_bcr['fttc'] = 0
        try:
            self.rollout_bcr['adsl'] = self.rollout_benefits['adsl'] / self.rollout_costs['adsl']
        except ZeroDivisionError:
            self.rollout_bcr['adsl'] = 0


    def __repr__(self):
        return "<Exchange id:{}>".format(self.id)

class Cabinet(object):
    """Cabinets"""

    def __init__(self, data, clients, link, parameters):

        # Asset parameters
        self.id = data["id"]
        self.connection = data["connection"]
        self.fttp = data["FTTP"]
        self.gfast = data["GFast"]
        self.fttc = data["FTTC"]
        self.adsl = data["ADSL"]

        # Link parameters
        self._clients = clients
        self.link = link

        # Upgrade costs
        self.upgrade_costs = {}
        self.upgrade_costs['fttp'] = (
            (parameters['costs']['assets']['cabinet']['fttp'] if self.fttp == 0 else 0)
            + 
            (self.link.upgrade_costs['fiber'] if self.link != None else 0)
        )
        self.upgrade_costs['gfast'] = (
            (parameters['costs']['assets']['cabinet']['gfast'] if self.gfast == 0 else 0)
            + 
            (self.link.upgrade_costs['fiber'] if self.link != None else 0)
        )
        self.upgrade_costs['fttc'] = (
            (parameters['costs']['assets']['cabinet']['fttc'] if self.fttc == 0 else 0)
            + 
            (self.link.upgrade_costs['fiber'] if self.link != None else 0)
        )
        self.upgrade_costs['adsl'] = (
            (parameters['costs']['assets']['cabinet']['adsl'] if self.adsl == 0 else 0)
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
        try:
            self.rollout_bcr['fttp'] = self.rollout_benefits['fttp'] / self.rollout_costs['fttp']
        except ZeroDivisionError:
            self.rollout_bcr['fttp'] = 0
        try:    
            self.rollout_bcr['gfast'] = self.rollout_benefits['gfast'] / self.rollout_costs['gfast']
        except ZeroDivisionError:
            self.rollout_bcr['gfast'] = 0
        try:
            self.rollout_bcr['fttc'] = self.rollout_benefits['fttc'] / self.rollout_costs['fttc']
        except ZeroDivisionError:
            self.rollout_bcr['fttc'] = 0
        try:
            self.rollout_bcr['adsl'] = self.rollout_benefits['adsl'] / self.rollout_costs['adsl']
        except ZeroDivisionError:
            self.rollout_bcr['adsl'] = 0


    def __repr__(self):
        return "<Cabinet id:{}>".format(self.id)

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

        # Link parameters
        self._clients = clients
        self.link = link

        # Upgrade costs
        self.upgrade_costs = {}
        self.upgrade_costs['fttp'] = (
            (parameters['costs']['assets']['distribution']['fttp'] if self.fttp == 0 else 0)
            + 
            (self.link.upgrade_costs['fiber'] if self.link != None else 0)
        )
        self.upgrade_costs['gfast'] = (
            (parameters['costs']['assets']['distribution']['gfast'] if self.gfast == 0 else 0)
            +
            (self.link.upgrade_costs['fiber'] if self.link != None else 0)
        )
        self.upgrade_costs['fttc'] = (
            (parameters['costs']['assets']['distribution']['fttc'] if self.fttc == 0 else 0)
            +
            (self.link.upgrade_costs['copper'] if self.link != None else 0)
        )
        self.upgrade_costs['adsl'] = (
            (parameters['costs']['assets']['distribution']['adsl'] if self.adsl == 0 else 0)
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
        try:
            self.rollout_bcr['fttp'] = self.rollout_benefits['fttp'] / self.rollout_costs['fttp']
        except ZeroDivisionError:
            self.rollout_bcr['fttp'] = 0
        try:    
            self.rollout_bcr['gfast'] = self.rollout_benefits['gfast'] / self.rollout_costs['gfast']
        except ZeroDivisionError:
            self.rollout_bcr['gfast'] = 0
        try:
            self.rollout_bcr['fttc'] = self.rollout_benefits['fttc'] / self.rollout_costs['fttc']
        except ZeroDivisionError:
            self.rollout_bcr['fttc'] = 0
        try:
            self.rollout_bcr['adsl'] = self.rollout_benefits['adsl'] / self.rollout_costs['adsl']
        except ZeroDivisionError:
            self.rollout_bcr['adsl'] = 0

    def __repr__(self):
        return "<Distribution id:{}>".format(self.id)

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

        # Link parameters
        self.link = link

        # Upgrade costs
        self.upgrade_costs = {}
        self.upgrade_costs['fttp'] = (
            (parameters['costs']['assets']['premise']['fttp'] if self.fttp == 0 else 0)
            + self.link.upgrade_costs['fiber']
        )
        self.upgrade_costs['gfast'] = (
            (parameters['costs']['assets']['premise']['gfast'] if self.gfast == 0 else 0)
            + self.link.upgrade_costs['fiber']
        )
        self.upgrade_costs['fttc'] = (
            (parameters['costs']['assets']['premise']['fttc'] if self.fttc == 0 else 0)
            + self.link.upgrade_costs['copper']
        )
        self.upgrade_costs['adsl'] = (
            (parameters['costs']['assets']['premise']['adsl'] if self.adsl == 0 else 0)
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
        self.rollout_benefits['fttp'] = parameters['benefits']['assets']['premise']['fttp']
        self.rollout_benefits['gfast'] = parameters['benefits']['assets']['premise']['gfast']
        self.rollout_benefits['fttc'] = parameters['benefits']['assets']['premise']['fttc']
        self.rollout_benefits['adsl'] = parameters['benefits']['assets']['premise']['adsl']

        # Benefit-cost ratio
        self.rollout_bcr = {}
        try:
            self.rollout_bcr['fttp'] = self.rollout_benefits['fttp'] / self.rollout_costs['fttp']
        except ZeroDivisionError:
            self.rollout_bcr['fttp'] = 0
        try:    
            self.rollout_bcr['gfast'] = self.rollout_benefits['gfast'] / self.rollout_costs['gfast']
        except ZeroDivisionError:
            self.rollout_bcr['gfast'] = 0
        try:
            self.rollout_bcr['fttc'] = self.rollout_benefits['fttc'] / self.rollout_costs['fttc']
        except ZeroDivisionError:
            self.rollout_bcr['fttc'] = 0
        try:
            self.rollout_bcr['adsl'] = self.rollout_benefits['adsl'] / self.rollout_costs['adsl']
        except ZeroDivisionError:
            self.rollout_bcr['adsl'] = 0

    def __repr__(self):
        return "<Premise id:{}>".format(self.id)

class Link(object):
    """Links"""

    def __init__(self, data, parameters):
        self.origin = data["origin"]
        self.dest = data["dest"]
        self.technology = data["technology"]
        self.length = data["length"]

        # Upgrade costs
        self.upgrade_costs = {}
        self.upgrade_costs['fiber'] = parameters['costs']['links']['fiber_per_meter'] * self.length if self.technology != 'fiber' else 0
        self.upgrade_costs['copper'] = parameters['costs']['links']['copper_per_meter'] * self.length if self.technology != 'copper' else 0

    def __repr__(self):
        return "<Link origin:{} dest:{} length:{}>".format(self.origin, self.dest, self.length)