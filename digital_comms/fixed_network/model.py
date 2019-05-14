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
    def __init__(self, assets, links, parameters):

        self._links = {}

        self._links_distributions = []
        self._links_cabinets = []
        self._links_exchanges = []

        for link_dict in links:
            link = Link(link_dict, parameters)

            destination = link.dest
            self._links[destination] = link

            if destination.startswith('distribution'):
                self._links_distributions.append(link)
            elif destination.startswith('cabinet'):
                self._links_cabinets.append(link)
            elif destination.startswith('exchange'):
                self._links_exchanges.append(link)

        self._distributions = []
        self._distributions_by_lad = defaultdict(list)
        self._distributions_by_cab = defaultdict(list)
        for distribution in assets['distributions']:
            distribution = Distribution(
                distribution,
                self._links.get(distribution['id'], None),
                parameters,
            )

            self._distributions.append(distribution)
            self._distributions_by_lad[distribution.lad].append(distribution)
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
                self._links.get(exchange['id'], None),
                parameters
            )
            self._exchanges.append(exchange)

    def upgrade(self, interventions):
        """Upgrades the system with a list of ``interventions``

        Arguments
        ---------
        interventions: list of tuple
            A list of intervention tuples containing asset id and technology
        """
        for intervention in interventions:

            asset_id = intervention[0]
            technology = intervention[1]

            if asset_id.startswith('distribution'):
                distribution = [
                    distribution
                    for distribution in self._distributions
                    if distribution.id == asset_id
                ][0]
                distribution.upgrade(technology)
                print('upgrade')

            if asset_id.startswith('cabinet'):
                cabinet = [cabinet for cabinet in self._cabinets if cabinet.id == asset_id][0]
                cabinet.upgrade(technology)

            if asset_id.startswith('exchange'):
                exchange = [exchange for exchange in self._exchanges if exchange.id == asset_id][0]
                exchange.upgrade(technology)

    def update_adoption_desirability(self, adoption_desirability):
        """

        Updates the state of the set of distributions, then computes new statistics
        at the cabinet and exchange levels

        Arguments
        ---------
        adoption_desirability : list of tuple
        """

        for distribution_id, desirability_to_adopt in adoption_desirability:
            for distribution in self._distributions:
                if distribution_id == distribution.id:
                    distribution.update_desirability_to_adopt(desirability_to_adopt)

        for cabinet in self._cabinets:
            cabinet.compute()

        for exchange in self._exchanges:
            exchange.compute()

    def get_total_upgrade_costs(self, tech):
        upgrade_costs = {}

        #find upgrade costs for dist, cab, exchange
        for exchange in self._exchanges:
            exchange_id = exchange.id
            exchange_cost = exchange.upgrade_costs[tech]
            cabs = self._cabinets_by_exchange[exchange_id]
            for cab in cabs:
                cab_id = cab.id
                cab_cost = cab.upgrade_costs[tech]
                dps = self._distributions_by_cab[cab_id]
                for dp in dps:
                    dp_id = dp.id
                    dp_cost = dp.upgrade_costs[tech]
                    upgrade_costs[dp_id] = (dp_cost, cab_cost, exchange_cost)

        return upgrade_costs

    def get_total_benefit(self, tech):
        rollout_benefits = {}

        #find upgrade costs for dist, cab, exchange
        for exchange in self._exchanges:
            exchange_id = exchange.id
            exchange_benefit = exchange.rollout_benefits[tech]
            cabs = self._cabinets_by_exchange[exchange_id]
            for cab in cabs:
                cab_id = cab.id
                cab_benefit = cab.rollout_benefits[tech]
                dps = self._distributions_by_cab[cab_id]
                for dp in dps:
                    dp_id = dp.id
                    dp_benefit = dp.rollout_benefits[tech]
                    rollout_benefits[dp_id] = (dp_benefit, cab_benefit, exchange_benefit)

        return rollout_benefits

    def coverage(self, aggregation_geography):
        """
        define coverage
        """
        # run statistics on each lad
        coverage_results = []

        if aggregation_geography == 'exchange':

            for exchange in self._exchanges:

                coverage_results.append({
                    'id': exchange.id,
                    'fttp': exchange.fttp,
                    'fttdp': exchange.fttdp,
                    'fttc': exchange.fttc,
                    'docsis3': exchange.docsis3,
                    'adsl': exchange.adsl,
                    'premises': exchange.total_prems,
                })

        elif aggregation_geography == 'lad':

            distributions_per_lad = self._distributions_by_lad

            for lad in distributions_per_lad:
                # contain  list of premises objects in the lad
                sum_of_fttp = sum(distribution.fttp for distribution in distributions_per_lad[lad])

                # contain  list of premises objects in the lad
                sum_of_fttdp = sum(distribution.fttdp for distribution in distributions_per_lad[lad])

                # contain  list of premises objects in the lad
                sum_of_fttc = sum(distribution.fttc for distribution in distributions_per_lad[lad])

                # contain  list of premises objects in the lad
                sum_of_docsis3 = sum(distribution.docsis3 for distribution in distributions_per_lad[lad])

                # contain  list of premises objects in the lad
                sum_of_adsl = sum(distribution.adsl for distribution in distributions_per_lad[lad])

                # contain  list of premises objects in the lad
                num_premises = sum(distribution.total_prems for distribution in distributions_per_lad[lad])

                coverage_results.append({
                    'id': lad,
                    'fttp': sum_of_fttp,
                    'fttdp': sum_of_fttdp,
                    'fttc': sum_of_fttc,
                    'docsis3': sum_of_docsis3,
                    'adsl': sum_of_adsl,
                    'premises': num_premises,
                })

        else:
            raise ValueError('Did not recognise aggregation_geography')

        output = []

        for item in coverage_results:

            output.append({
                'id': item['id'],
                'percentage_of_premises_with_fttp': round(item['fttp'] / item['premises'] * 100),
                'percentage_of_premises_with_fttdp': round(item['fttdp'] / item['premises'] * 100),
                'percentage_of_premises_with_fttc': round(item['fttc'] / item['premises'] * 100),
                'percentage_of_premises_with_docsis3': round(item['docsis3'] / item['premises'] * 100),
                'percentage_of_premises_with_adsl': round(item['adsl'] / item['premises'] * 100),
                'sum_of_premises': item['premises']
            })

        return output

    def aggregate_coverage(self, aggregation_geography):
        """
        define aggregate coverage
        """
        coverage_results = []

        if aggregation_geography == 'exchange':

            for exchange in self._exchanges:

                coverage_results.append({
                    'id': exchange.id,
                    'sum_of_fttp': exchange.fttp,
                    'sum_of_fttdp': exchange.fttdp,
                    'sum_of_fttc': exchange.fttc,
                    'sum_of_docsis3': exchange.docsis3,
                    'sum_of_adsl': exchange.adsl,
                    'sum_of_premises': exchange.total_prems,
                })

        elif aggregation_geography == 'lad':

            assets_by_geography = self._distributions_by_lad

            for area in assets_by_geography.keys():
                sum_of_fttp = sum(
                    distribution.fttp for distribution in assets_by_geography[area])
                sum_of_fttdp = sum(
                    distribution.fttdp for distribution in assets_by_geography[area])
                sum_of_fttc = sum(
                    distribution.fttc for distribution in assets_by_geography[area])
                sum_of_docsis3 = sum(
                    distribution.docsis3 for distribution in assets_by_geography[area])
                sum_of_adsl = sum(
                    distribution.adsl for distribution in assets_by_geography[area])
                sum_of_premises = sum(
                    distribution.total_prems for distribution in assets_by_geography[area])

                coverage_results.append({
                    'id': area,
                    'sum_of_fttp': sum_of_fttp,
                    'sum_of_fttdp': sum_of_fttdp,
                    'sum_of_fttc': sum_of_fttc,
                    'sum_of_docsis3': sum_of_docsis3,
                    'sum_of_adsl': sum_of_adsl,
                    'sum_of_premises': sum_of_premises
                })

        else:
            raise ValueError('Did not recognise aggregation_geography')

        output = []

        for item in coverage_results:
            aggregate_fttp = sum(item['sum_of_fttp'] for item in coverage_results)
            aggregate_fttdp = sum(item['sum_of_fttdp'] for item in coverage_results)
            aggregate_fttc = sum(item['sum_of_fttc'] for item in coverage_results)
            aggregate_docsis3 = sum(item['sum_of_docsis3'] for item in coverage_results)
            aggregate_adsl = sum(item['sum_of_adsl'] for item in coverage_results)
            aggregate_premises = sum(item['sum_of_premises'] for item in coverage_results)

            output.append({
                'id': item['id'],
                'percentage_of_premises_with_fttp': round(aggregate_fttp / aggregate_premises * 100),
                'percentage_of_premises_with_fttdp': round(aggregate_fttdp / aggregate_premises * 100),
                'percentage_of_premises_with_fttc': round(aggregate_fttc / aggregate_premises * 100),
                'percentage_of_premises_with_docsis3': round(aggregate_docsis3 / aggregate_premises * 100),
                'percentage_of_premises_with_adsl': round(aggregate_adsl / aggregate_premises * 100),
                'sum_of_premises': aggregate_premises
            })

        return output

    def capacity(self, aggregation_geography):
        """
        define capacity
        """
        technologies = ['fttp', 'fttdp', 'fttc', 'docsis3', 'adsl']

        capacity_results = []

        if aggregation_geography == 'exchange':

            for asset in self._exchanges:
                capacity_by_technology = []
                total_prems = getattr(asset, 'total_prems')

                if asset.fttp == total_prems:
                    #so expect 20 prems at 1000 each = 1000 mean
                    average_capacity = (
                        asset.fttp * asset.connection_capacity('fttp')
                        / asset.total_prems
                    )
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
                            docsis3 = getattr(asset, 'docsis3')

                            number_of_premises_with_technology = total_prems - (
                                fttp + fttdp + fttc + docsis3
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

        elif aggregation_geography == 'lad':

            assets_by_area = self._distributions_by_lad

            for area in assets_by_area.keys():

                capacity_by_technology = []

                for asset in assets_by_area[area]:
                    for technology in technologies:
                        number_of_premises_with_technology = getattr(
                            asset, technology)

                        if technology == 'adsl':

                            fttp = getattr(asset, 'fttp')
                            fttdp = getattr(asset, 'fttdp')
                            fttc = getattr(asset, 'fttc')
                            docsis3 = getattr(asset, 'docsis3')
                            total_prems = getattr(asset, 'total_prems')

                            number_of_premises_with_technology = total_prems - (
                                fttp + fttdp + fttc + docsis3
                            )

                        technology_capacity = asset.connection_capacity(technology)
                        capacity = technology_capacity * number_of_premises_with_technology
                        capacity_by_technology.append(capacity)

                summed_capacity = sum(capacity_by_technology)

                number_of_connections = sum([asset.total_prems for asset in assets_by_area[area]])

                capacity_results.append({
                    'id': area,
                    'average_capacity': round(summed_capacity / number_of_connections),
                })

        else:
            raise ValueError('Did not recognise aggregation_geography')

        return capacity_results

    @property  # shortcut for creating a read-only property
    def assets(self):
        """Returns a certain subset of links"""
        return {
            'distributions':    self._distributions,
            'cabinets':         self._cabinets,
            'exchanges':        self._exchanges
        }

    @property
    def links(self):
        """Returns a certain subset of links"""
        return {
            'distributions':    self._links_distributions,
            'cabinets':         self._links_cabinets,
            'exchanges':        self._links_exchanges,
        }


class Asset(metaclass=ABCMeta):
    """Abstract fixed network node

    An Asset with no ``clients`` is a distribution point

    Arguments
    ---------
    clients : list, optional
        An optional list of digital_comms.fixed_network.model:`Asset`
    """

    def __init__(self, clients=None):
        self.id = None
        if clients:
            self._clients = clients
        else:
            self._clients = []
        self.link = None

    @abstractmethod
    def compute(self):
        raise NotImplementedError

    @abstractproperty
    def upgrade_costs(self):
        return NotImplementedError

    @property
    def fttp(self):
        return sum([client.fttp for client in self._clients])

    @property
    def fttdp(self):
        return sum([client.fttdp for client in self._clients])

    @property
    def fttc(self):
        return sum([client.fttc for client in self._clients])

    @property
    def docsis3(self):
        return sum([client.docsis3 for client in self._clients])

    @property
    def adsl(self):
        return sum([client.adsl for client in self._clients])

    @property
    def total_prems(self):
        return sum([client.total_prems for client in self._clients])

    def upgrade(self, action):
        """Upgrade the asset's clients with an ``action``

        If a leaf asset (e.g. an Asset with no clients), upgrade
        self.

        Arguments
        ---------
        action : str

        Notes
        -----
        Could check whether self is an instance of Distribution instead

        """
        if self._clients:
            if self.link is not None:
                self.link.upgrade('fibre')
            for client in self._clients:
                client.upgrade(action)

        else:
            if action in ('fttp'):
                self._fttp = self.total_prems
                self._fttdp = 0
                self._fttc = 0
                self._docsis3 = 0
                self._adsl = 0
                if self.link is not None:
                    self.link.upgrade('fibre')

            elif action in ('fttdp'):
                self._fttp = 0
                self._fttdp = self.total_prems
                self._fttc = 0
                self._docsis3 = 0
                self._adsl = 0

        self.compute()

    @property
    def rollout_costs(self) -> Dict:
        rollout_costs = {}
        upgrade_costs = self.upgrade_costs
        costs = [client.rollout_costs for client in self._clients]

        for tech in ['fttp', 'fttdp', 'fttc', 'adsl']:
            rollout_costs[tech] = upgrade_costs[tech] + \
                sum(cost[tech] for cost in costs)
        return rollout_costs

    @property
    def rollout_benefits(self) -> Dict:
        rollout_benefits = {}
        benefits = [client.rollout_benefits for client in self._clients]
        for tech in ['fttp', 'fttdp', 'fttc', 'adsl']:
            rollout_benefits[tech] = sum(benefit[tech] for benefit in benefits)
        return rollout_benefits

    @property
    def rollout_bcr(self) -> Dict:
        rollout_bcr = {}
        benefits = self.rollout_benefits
        costs = self.rollout_costs
        for tech in ['fttp', 'fttdp', 'fttc', 'adsl']:
            rollout_bcr[tech] = _calculate_benefit_cost_ratio(
                benefits[tech], costs[tech])
        return rollout_bcr

    @property
    def total_potential_benefit(self) -> Dict:
        total_potential_benefit = {}
        benefits = [client.total_potential_benefit for client in self._clients]
        for tech in ['fttp', 'fttdp', 'fttc', 'adsl']:
            total_potential_benefit[tech] = sum(benefit[tech] for benefit in benefits)
        return total_potential_benefit

    @property
    def total_potential_bcr(self) -> Dict:
        total_potential_bcr = {}
        benefit = self.total_potential_benefit
        cost = self.rollout_costs
        for tech in ['fttp', 'fttdp', 'fttc', 'adsl']:
            total_potential_bcr[tech] = _calculate_benefit_cost_ratio(
                benefit[tech],
                cost[tech]
                )
        return total_potential_bcr


class Exchange(Asset):
    """Exchange object

    Arguments
    ---------
    data : dict
        Contains asset data including, id, name, postcode, region, county and available
        technologies.
    clients : list_of_objects
        Contains all assets (Cabinets) served by an Exchange.
    link
    parameters : dict
        Contains all parameters from 'digital_comms.yml'.

    """

    def __init__(self, data, clients, link, parameters):
        super().__init__(clients)
        self.id = data["id"]
        self.parameters = parameters
        self._clients = clients

        self.link = link

        self.compute()

    @property
    def upgrade_costs(self) -> Dict:
        upgrade_costs = {}
        upgrade_costs['fttp'] = (
            (self.parameters['costs_assets_exchange_fttp'] if self.fttp == 0 else 0)
            +
            (self.link.upgrade_costs['fibre'] if self.link is not None else 0))
        upgrade_costs['fttdp'] = (
            (self.parameters['costs_assets_exchange_fttdp'] if self.fttdp == 0 else 0)
            +
            (self.link.upgrade_costs['fibre'] if self.link is not None else 0))
        upgrade_costs['fttc'] = (
            (self.parameters['costs_assets_exchange_fttc'] if self.fttc == 0 else 0)
            +
            (self.link.upgrade_costs['fibre'] if self.link is not None else 0))
        upgrade_costs['adsl'] = (
            self.parameters['costs_assets_exchange_adsl'] if self.adsl == 0 else 0)
        return upgrade_costs

    def compute(self):
        """Calculate upgrade costs and benefits
        """

        self.list_of_asset_costs = []
        self.list_of_asset_costs.append({
            'id': self.id,
            'costs_assets_exchange_fttp':
                (self.parameters['costs_assets_exchange_fttp'] if self.fttp == 0 else 0),
            'link_upgrade_costs':
                (self.link.upgrade_costs['fibre'] if self.link is not None else 0),
            'total_cost': (
                (self.parameters['costs_assets_exchange_fttp'] if self.fttp == 0 else 0)
                +
                (self.link.upgrade_costs['fibre'] if self.link is not None else 0))
        })

    def __repr__(self):
        return "<Exchange id:{}>".format(self.id)

    def connection_capacity(self, technology):
        capacity = _generic_connection_capacity(technology)
        return capacity


class Cabinet(Asset):
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

    """
    def __init__(self, data, clients, link, parameters):
        super().__init__(clients)
        # Asset parameters
        self.id = data["id"]
        self.connection = data["connection"]
        self.parameters = parameters
        self._clients = clients

        self.link = link

        self.compute()

    def __repr__(self):
        return "<Cabinet id:{}>".format(self.id)

    @property
    def upgrade_costs(self) -> Dict:

        upgrade_costs = {}

        upgrade_costs['fttp'] = (
            (
                self.parameters['costs_assets_cabinet_fttp'] \
                * ceil(len(self._clients) / 32) \
                if self.fttp == 0 else 0
            )
            +
            (self.link.upgrade_costs['fibre'] if self.link is not None else 0)
        )
        upgrade_costs['fttdp'] = (
            (self.parameters['costs_assets_cabinet_fttdp'] if self.fttdp == 0 else 0)
            +
            (self.link.upgrade_costs['fibre'] if self.link is not None else 0)
        )
        upgrade_costs['fttc'] = (
            (self.parameters['costs_assets_cabinet_fttc'] if self.fttc == 0 else 0)
            +
            (self.link.upgrade_costs['fibre'] if self.link is not None else 0)
        )
        upgrade_costs['adsl'] = (
            (self.parameters['costs_assets_cabinet_adsl'] if self.adsl == 0 else 0)
            +
            (self.link.upgrade_costs['copper'] if self.link is not None else 0)
        )

        return upgrade_costs

    def compute(self):
        """Calculates upgrade costs and benefits.
        """

        self.list_of_asset_costs = []
        self.list_of_asset_costs.append({
            'id': self.id,
            'costs_assets_cabinet_fttp': (self.parameters['costs_assets_cabinet_fttp'] \
                * ceil(len(self._clients) / 32) \
                if self.fttp == 0 else 0),
            'link_upgrade_costs': (self.link.upgrade_costs['fibre'] if self.link is not None else 0),
            'total_cost': (
            (
                self.parameters['costs_assets_cabinet_fttp'] \
                * ceil(len(self._clients) / 32) \
                if self.fttp == 0 else 0
            )
            +
            (self.link.upgrade_costs['fibre'] if self.link is not None else 0)
        )
        })


class Distribution(Asset):
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
    """
    def __init__(self, data, link, parameters):
        super().__init__()
        # Asset parameters
        self.id = data["id"]
        self.lad = data["lad"]
        self.connection = data["connection"]
        self._fttp = int(data["fttp"])
        self._fttdp = int(data["fttdp"])
        self._fttc = int(data["fttc"])
        self._docsis3 = int(data["docsis3"])
        self._adsl = int(data["adsl"])
        self._total_prems = int(data['total_prems'])
        self.wta = float(data["wta"])
        self.wtp = int(data["wtp"])
        self.adoption_desirability = False  # type: bool

        self.parameters = parameters

        # Link parameters
        self.link = link

        self.compute()

    @property
    def fttp(self):
        return self._fttp

    @property
    def fttdp(self):
        return self._fttdp

    @property
    def fttc(self):
        return self._fttc

    @property
    def docsis3(self):
        return self._docsis3

    @property
    def adsl(self):
        return self._adsl

    @property
    def total_prems(self):
        return self._total_prems

    def compute(self):

        self.list_of_asset_costs = []
        self.list_of_asset_costs.append({
            'id': self.id ,
            'costs_assets_premise_fttp_modem': (self.parameters['costs_assets_premise_fttp_modem'] * self.total_prems),
            'costs_assets_premise_fttp_optical_network_terminator': (self.parameters['costs_assets_premise_fttp_optical_network_terminator'] * self.total_prems if self.fttp == 0 else 0),
            'planning_administration_cost': (self.parameters['planning_administration_cost'] * self.total_prems if self.fttp == 0 else 0),
            'costs_assets_premise_fttp_optical_connection_point': (self.parameters['costs_assets_premise_fttp_optical_connection_point'] * (-(-self.total_prems // 32)) if self.fttp == 0 else 0),
            'link_upgrade_costs': (self.link.upgrade_costs['fibre'] if self.link is not None else 0),
            'total_cost': (
            (self.parameters['costs_assets_premise_fttp_modem'] * self.total_prems) +
            (self.parameters['costs_assets_premise_fttp_optical_network_terminator'] \
                * self.total_prems if self.fttp == 0 else 0) +
            (self.parameters['planning_administration_cost'] * self.total_prems \
                if self.fttp == 0 else 0) +
            (self.parameters['costs_assets_premise_fttp_optical_connection_point'] \
                * (-(-self.total_prems // 32)) if self.fttp == 0 else 0) +
            (self.link.upgrade_costs['fibre'] if self.link is not None else 0)
        )
        })

    @property
    def upgrade_costs(self):
        # Upgrade costs
        upgrade_costs = {}
        upgrade_costs['fttp'] = (
            (self.parameters['costs_assets_premise_fttp_modem'] * self.total_prems) +
            (self.parameters['costs_assets_premise_fttp_optical_network_terminator']
                * self.total_prems if self.fttp == 0 else 0) +
            (self.parameters['planning_administration_cost'] * self.total_prems
                if self.fttp == 0 else 0) +
            (self.parameters['costs_assets_premise_fttp_optical_connection_point']
                * (-(-self.total_prems // 32))) +
            (self.link.upgrade_costs['fibre'] if self.link is not None else 0)
        )
        upgrade_costs['fttdp'] = (
            (self.parameters['costs_assets_distribution_fttdp_8_ports']
                * (-(-self.total_prems // 8)) if self.fttdp == 0 else 0) +
            (self.parameters['costs_assets_premise_fttdp_modem'] * self.total_prems
                if self.fttdp == 0 else 0)
        )
        upgrade_costs['fttc'] = (
            (self.parameters['costs_assets_distribution_fttc'] if self.fttc == 0 else 0) +
            (self.parameters['costs_assets_premise_fttc_modem'] if self.fttc == 0 else 0) +
            (self.link.upgrade_costs['copper'] if self.link is not None else 0)
        )
        upgrade_costs['adsl'] = (
            (self.parameters['costs_assets_distribution_adsl'] if self.adsl == 0 else 0) +
            (self.parameters['costs_assets_premise_adsl_modem'] if self.adsl == 0 else 0) +
            (self.link.upgrade_costs['copper'] if self.link is not None else 0)
        )
        return upgrade_costs

    @property
    def rollout_benefits(self):
        """Compute the benefit of rolling out the technologies

        Notes
        -----
        Problem: wtp is now aggregated to the distribution point
        But households will adopt at different times
        scenario adoption should really be done before the aggregation
        or a logic developed which relies on the overall attractiveness
        of the distribution point.

        """
        rollout_benefits = {}

        benefit = self._calculate_revenue()

        for tech in ['fttp', 'fttdp', 'fttc', 'adsl']:
            if self.adoption_desirability:
                if getattr(self, tech) == 0:
                    rollout_benefits[tech] = benefit
                else:
                    rollout_benefits[tech] = 0
            else:
                rollout_benefits[tech] = 0
        return rollout_benefits

    @property
    def total_potential_benefit(self):
        total_potential_benefit = {}

        benefit = self._calculate_revenue()

        for tech in ['fttp', 'fttdp', 'fttc', 'adsl']:
            total_potential_benefit[tech] = benefit
        return total_potential_benefit

    def _calculate_revenue(self):
        return _calculate_potential_revenue(
                self.wtp, self.parameters['months_per_year'],
                self.parameters['payback_period'],
                self.parameters['profit_margin'])

    def connection_capacity(self, technology):
        capacity = _generic_connection_capacity(technology)
        return capacity

    def __repr__(self):
        return "<Distribution id:{}>".format(self.id)

    def update_desirability_to_adopt(self, desirability_to_adopt):
        self.adoption_desirability = desirability_to_adopt
        self.compute()


class Link():
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
        self.length = int(round(float(data["length"])))

        self.parameters = parameters
        self.compute()

    def compute(self):

        # Upgrade costs
        self.upgrade_costs = {}
        self.upgrade_costs['fibre'] = self.parameters['costs_links_fibre_meter'] * \
            float(self.length) if self.technology != 'fibre' else 0
        self.upgrade_costs['copper'] = self.parameters['costs_links_copper_meter'] * \
            float(self.length) if self.technology != 'copper' else 0

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


def _calculate_potential_revenue(wtp, months, payback_period, profit_margin):

    try:
        return int(wtp) * months * payback_period \
               * (100 - profit_margin) / 100
    except ZeroDivisionError:
        return 0


def _generic_connection_capacity(technology):

    # determine connection_capacity
    if technology == 'fttp':
        connection_capacity = 1000
    elif technology == 'fttdp':
        connection_capacity = 300
    elif technology == 'fttc':
        connection_capacity = 80
    elif technology == 'docsis3':
        connection_capacity = 150
    else:
        connection_capacity = 24

    return connection_capacity
