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

            print(action)
            if asset_id.startswith('distribution'):
                distribution = [distribution for distribution in self._distributions if distribution.id == asset_id][0]
                distribution.upgrade(action)
                #pprint(vars(distribution))
            
            if asset_id.startswith('cabinet'):
                cabinet = [cabinet for cabinet in self._cabinets if cabinet.id == asset_id][0]
                cabinet.upgrade(action)

    def coverage(self):
        """
        define coverage
        """

        # group premises by lads
        premises_per_lad = defaultdict(list)

        for premise in self._premises:
            """
            'Cambridge': [
                premise1,
                premise2
            ]
            """
            premises_per_lad[premise.lad].append(premise)


        # run statistics on each lad
        coverage_results = defaultdict(dict)
        for lad in premises_per_lad.keys():

            # return dict that looks like
            """
            dict of dicts
            'Cambridge' : {
                'premise_with_fttp': int, 
                'premise_with_fttdp': int, 
                'premise_with_fttc': int, 
                'premise_with_adsl': int, 
                'premise_with_cable': int,
            },
            'Oxford' : ..
            """

            #print(lad)
            sum_of_fttp = sum([premise.fttp for premise in premises_per_lad[lad]]) # contain  list of premises objects in the lad
            sum_of_gfast = sum([premise.gfast for premise in premises_per_lad[lad]]) # contain  list of premises objects in the lad
            sum_of_fttc = sum([premise.fttc for premise in premises_per_lad[lad]]) # contain  list of premises objects in the lad
            sum_of_adsl = sum([premise.adsl for premise in premises_per_lad[lad]]) # contain  list of premises objects in the lad
            
            sum_of_premises = len(premises_per_lad[lad]) # contain  list of premises objects in the lad

            coverage_results[lad] = {
                'percentage_of_premises_with_fttp': round(sum_of_fttp / sum_of_premises, 2),
                'percentage_of_premises_with_gfast': round(sum_of_gfast / sum_of_premises, 2),
                'percentage_of_premises_with_fttc': round(sum_of_fttc / sum_of_premises, 2),
                'percentage_of_premises_with_adsl': round(sum_of_adsl / sum_of_premises, 2)
            }

        return coverage_results

    def capacity(self):
        """
        define capacity
        """

        # group premises by lads
        premises_per_lad = defaultdict(list)

        for premise in self._premises:
            #print(premise)
            #pprint(vars(premise))
            """
            'Cambridge': [
                premise1,
                premise2
            ]
            """          
            premises_per_lad[premise.lad].append(premise)

        capacity_results = defaultdict(dict)

        for lad in premises_per_lad.keys():
            #print(lad)
            summed_capacity = sum([premise.connection_capacity for premise in premises_per_lad[lad]])
            number_of_connections = len(premises_per_lad[lad]) # contain  list of premises objects in the lad

            #return results
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
        self.upgrade_costs['fttp'] = self.parameters['costs_assets_exchange_fttp'] if self.fttp == 0 else 0
        self.upgrade_costs['gfast'] = self.parameters['costs_assets_exchange_gfast'] if self.gfast == 0 else 0
        self.upgrade_costs['fttc'] = self.parameters['costs_assets_exchange_fttc'] if self.fttc == 0 else 0
        self.upgrade_costs['adsl'] = self.parameters['costs_assets_exchange_adsl'] if self.adsl == 0 else 0

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
            (self.parameters['costs_assets_cabinet_fttp_32_ports'] * ceil(len(self._clients) / 32)
             if self.fttp == 0 else 0)
            + 
            (self.link.upgrade_costs['fiber'] if self.link != None else 0)
        )
        self.upgrade_costs['gfast'] = (
            (self.parameters['costs_assets_cabinet_gfast'] if self.gfast == 0 else 0)
            + 
            (self.link.upgrade_costs['fiber'] if self.link != None else 0)
        )
        self.upgrade_costs['fttc'] = (
            (self.parameters['costs_assets_cabinet_fttc'] if self.fttc == 0 else 0)
            + 
            (self.link.upgrade_costs['fiber'] if self.link != None else 0)
        )
        self.upgrade_costs['adsl'] = (
            (self.parameters['costs_assets_cabinet_adsl'] if self.adsl == 0 else 0)
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
            (self.parameters['costs_assets_distribution_fttp_32_ports'] * ceil(len(self._clients) / 32) 
             if self.fttp == 0 else 0)
            + 
            (self.link.upgrade_costs['fiber'] if self.link != None else 0)
        )
        self.upgrade_costs['gfast'] = (
            (self.parameters['costs_assets_distribution_gfast_4_ports'] * ceil(len(self._clients) / 4) 
             if self.gfast == 0 else 0)
            +
            (self.link.upgrade_costs['fiber'] if self.link != None else 0)
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
        self.lad = data['lad']

        self.parameters = parameters

        # Link parameters
        self.link = link
        self.compute()

        def best_connection():

            if self.fttp == 1:
                best_connection = 'fttp' 
            elif self.gfast == 1:
                best_connection = 'gfast' 
            elif self.fttc == 1:
                best_connection = 'fttc' 
            else:
                best_connection = 'adsl'  

            return best_connection

        self.best_connection = best_connection()

        def connection_capacity():

            if self.best_connection == 'fttp' :
                connection_capacity =  250
            elif self.best_connection == 'gfast':
                connection_capacity =  100
            elif self.best_connection  == 'fttc':
                connection_capacity =  50
            else:
                connection_capacity =  10  
            
            return connection_capacity

        self.connection_capacity = connection_capacity()

    def compute(self):

        # Upgrade costs
        self.upgrade_costs = {}
        self.upgrade_costs['fttp'] = (
              (self.parameters['costs_assets_premise_fttp_modem'] if self.fttp == 0 else 0)
            + (self.parameters['costs_assets_premise_fttp_optical_network_terminator'] if self.fttp == 0 else 0)
            + self.link.upgrade_costs['fiber']
        )
        self.upgrade_costs['gfast'] = (
              (self.parameters['costs_assets_premise_gfast_modem'] if self.gfast == 0 else 0)
            + self.link.upgrade_costs['fiber']
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
        self.rollout_costs['fttp'] = self.upgrade_costs['fttp']
        self.rollout_costs['gfast'] = self.upgrade_costs['gfast']
        self.rollout_costs['fttc'] = self.upgrade_costs['fttc']
        self.rollout_costs['adsl'] = self.upgrade_costs['adsl']

        # Rollout benefits
        self.rollout_benefits = {}
        self.rollout_benefits['fttp'] = self.parameters['benefits_assets_premise_fttp']
        self.rollout_benefits['gfast'] = self.parameters['benefits_assets_premise_gfast']
        self.rollout_benefits['fttc'] = self.parameters['benefits_assets_premise_fttc']
        self.rollout_benefits['adsl'] = self.parameters['benefits_assets_premise_adsl']

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
        
        if action == 'rollout_fttp':            
            self.gfast = 1
            
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
        self.upgrade_costs['fiber'] = self.parameters['costs_links_fiber_meter'] * self.length if self.technology != 'fiber' else 0
        self.upgrade_costs['copper'] = self.parameters['costs_links_copper_meter'] * self.length if self.technology != 'copper' else 0

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