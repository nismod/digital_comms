"""Cambridge Communications Assessment Model
"""
from collections import defaultdict
from math import ceil

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
    upgrade
        Takes intervention decisions and builds them.
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
                parameters
            )
            self._exchanges.append(exchange)

    def upgrade(self, interventions, asset_type):

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

            if asset_id.startswith('cabinet'):
                cabinet = [cabinet for cabinet in self._cabinets if cabinet.id == asset_id][0]
                cabinet.upgrade(technology)

            if asset_id.startswith('exchange'):
                exchange = [exchange for exchange in self._exchanges if exchange.id == asset_id][0]
                exchange.upgrade(technology)

    def update_adoption_desirability(self, adoption_desirability):

        for distribution_id, desirability_to_adopt in adoption_desirability:
            for distribution in self._distributions:
                if distribution_id == distribution.id:
                    distribution.update_desirability_to_adopt(desirability_to_adopt)

    def get_total_upgrade_costs_by_distribution_point(self, tech):
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

    def coverage(self):
        """
        define coverage
        """
        distributions_per_lad = self._distributions_by_lad

        # run statistics on each lad
        coverage_results = {}

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

            coverage_results[lad] = {
                'num_premises': num_premises,
                'num_fttp': sum_of_fttp,
                'num_fttdp': sum_of_fttdp,
                'num_fttc': sum_of_fttc,
                'num_docsis3': sum_of_docsis3,
                'num_adsl': sum_of_adsl
            }

        return coverage_results

    def aggregate_coverage(self):
        """
        define aggregate coverage
        """
        distributions_per_lad = self._distributions_by_lad

        coverage_results = []
        for lad in distributions_per_lad.keys():
            sum_of_fttp = sum(distribution.fttp for distribution in distributions_per_lad[lad])
            sum_of_fttdp = sum(distribution.fttdp for distribution in distributions_per_lad[lad])
            sum_of_fttc = sum(distribution.fttc for distribution in distributions_per_lad[lad])
            sum_of_docsis3 = sum(distribution.docsis3 for distribution in distributions_per_lad[lad])
            sum_of_adsl = sum(distribution.adsl for distribution in distributions_per_lad[lad])
            sum_of_premises = sum(distribution.total_prems for distribution in distributions_per_lad[lad])

            coverage_results.append({
                'sum_of_fttp': sum_of_fttp,
                'sum_of_fttdp': sum_of_fttdp,
                'sum_of_fttc': sum_of_fttc,
                'sum_of_docsis3': sum_of_docsis3,
                'sum_of_adsl': sum_of_adsl,
                'sum_of_premises': sum_of_premises
            })

        output = []

        for item in coverage_results:
            aggregate_fttp = sum(item['sum_of_fttp'] for item in coverage_results)
            aggregate_fttdp = sum(item['sum_of_fttdp'] for item in coverage_results)
            aggregate_fttc = sum(item['sum_of_fttc'] for item in coverage_results)
            aggregate_docsis3 = sum(item['sum_of_docsis3'] for item in coverage_results)
            aggregate_adsl = sum(item['sum_of_adsl'] for item in coverage_results)
            aggregate_premises = sum(item['sum_of_premises'] for item in coverage_results)

            output.append({
                'percentage_of_premises_with_fttp': aggregate_fttp / aggregate_premises * 100,
                'percentage_of_premises_with_fttdp': aggregate_fttdp / aggregate_premises * 100,
                'percentage_of_premises_with_fttc': aggregate_fttc / aggregate_premises * 100,
                'percentage_of_premises_with_docsis3': aggregate_docsis3 / aggregate_premises * 100,
                'percentage_of_premises_with_adsl': aggregate_adsl / aggregate_premises * 100,
                'sum_of_premises': aggregate_premises
            })

        return output

    def capacity(self):
        """
        define capacity
        """

        # group premises by lads
        distributions_by_lad = self._distributions_by_lad

        capacity_results = defaultdict(dict)

        technologies = ['fttp', 'fttdp', 'fttc', 'docsis3', 'adsl']

        for lad in distributions_by_lad.keys():

            capacity_by_technology = []

            for distribution_point in distributions_by_lad[lad]:
                for technology in technologies:
                    number_of_premises_with_technology = getattr(
                        distribution_point, technology)
                    if technology == 'adsl':

                        fttp = getattr(distribution_point, 'fttp')
                        fttdp = getattr(distribution_point, 'fttdp')
                        fttc = getattr(distribution_point, 'fttc')
                        docsis3 = getattr(distribution_point, 'docsis3')
                        total_prems = getattr(distribution_point, 'total_prems')

                        number_of_premises_with_technology = total_prems - (
                            fttp + fttdp + fttc + docsis3
                        )

                    technology_capacity = distribution_point.connection_capacity(technology)
                    capacity = technology_capacity * number_of_premises_with_technology
                    capacity_by_technology.append(capacity)

            summed_capacity = sum(capacity_by_technology)

            number_of_connections = sum([dist.total_prems for dist in distributions_by_lad[lad]])

            capacity_results[lad] = {
                'average_capacity': round(summed_capacity / number_of_connections, 2),
            }

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

class Exchange():
    """Exchange object

    Parameters
    ----------
    data : dict
        Contains asset data including, id, name, postcode, region, county and available
        technologies.
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
        self.fttp = data["fttp"]
        self.fttdp = data["fttdp"]
        self.fttc = data["fttc"]
        self.adsl = data["adsl"]

        self.parameters = parameters
        self._clients = clients

        self.compute()

    def compute(self):
        # Upgrade costs
        self.upgrade_costs = {}
        self.upgrade_costs['fttp'] = \
            self.parameters['costs_assets_exchange_fttp'] if self.fttp == 0 else 0
        self.upgrade_costs['fttdp'] = \
            self.parameters['costs_assets_exchange_fttdp'] if self.fttdp == 0 else 0
        self.upgrade_costs['fttc'] = \
            self.parameters['costs_assets_exchange_fttc'] if self.fttc == 0 else 0
        self.upgrade_costs['adsl'] = \
            self.parameters['costs_assets_exchange_adsl'] if self.adsl == 0 else 0

        # Rollout costs
        self.rollout_costs = {}
        self.rollout_costs['fttp'] = self.upgrade_costs['fttp'] + \
            sum(client.rollout_costs['fttp'] for client in self._clients)
        self.rollout_costs['fttdp'] = self.upgrade_costs['fttdp'] + \
            sum(client.rollout_costs['fttdp'] for client in self._clients)
        self.rollout_costs['fttc'] = self.upgrade_costs['fttc'] + \
            sum(client.rollout_costs['fttc'] for client in self._clients)
        self.rollout_costs['adsl'] = self.upgrade_costs['adsl'] + \
            sum(client.rollout_costs['adsl'] for client in self._clients)

        # Rollout benefits
        self.rollout_benefits = {}
        self.rollout_benefits['fttp'] = sum(
            client.rollout_benefits['fttp'] for client in self._clients)
        self.rollout_benefits['fttdp'] = sum(
            client.rollout_benefits['fttdp'] for client in self._clients)
        self.rollout_benefits['fttc'] = sum(
            client.rollout_benefits['fttc'] for client in self._clients)
        self.rollout_benefits['adsl'] = sum(
            client.rollout_benefits['adsl'] for client in self._clients)

        # Benefit-cost ratio
        self.rollout_bcr = {}
        self.rollout_bcr['fttp'] = _calculate_benefit_cost_ratio(
            self.rollout_benefits['fttp'], self.rollout_costs['fttp'])
        self.rollout_bcr['fttdp'] = _calculate_benefit_cost_ratio(
            self.rollout_benefits['fttdp'], self.rollout_costs['fttdp'])
        self.rollout_bcr['fttc'] = _calculate_benefit_cost_ratio(
            self.rollout_benefits['fttc'], self.rollout_costs['fttc'])
        self.rollout_bcr['adsl'] = _calculate_benefit_cost_ratio(
            self.rollout_benefits['adsl'], self.rollout_costs['adsl'])

    def __repr__(self):
        return "<Exchange id:{}>".format(self.id)


class Cabinet():
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

    def __init__(self, data, clients, link, parameters):

        # Asset parameters
        self.id = data["id"]
        self.connection = data["connection"]
        self.fttp = data["fttp"]
        self.fttdp = data["fttdp"]
        self.fttc = data["fttc"]
        self.adsl = data["adsl"]
        self.parameters = parameters

        # Link parameters
        self._clients = clients

        self.link = link

        self.compute()

    def __repr__(self):
        return "<Cabinet id:{}>".format(self.id)

    def compute(self):

        # Upgrade costs
        self.upgrade_costs = {}
        self.upgrade_costs['fttp'] = (
            (
                self.parameters['costs_assets_upgrade_cabinet_fttp'] \
                * ceil(len(self._clients) / 32) \
                if self.fttp == 0 else 0
            )
            +
            (self.link.upgrade_costs['fibre'] if self.link is not None else 0)
        )
        self.upgrade_costs['fttdp'] = (
            (self.parameters['costs_assets_cabinet_fttdp'] if self.fttdp == 0 else 0)
            +
            (self.link.upgrade_costs['fibre'] if self.link is not None else 0)
        )
        self.upgrade_costs['fttc'] = (
            (self.parameters['costs_assets_cabinet_fttc'] if self.fttc == 0 else 0)
            +
            (self.link.upgrade_costs['fibre'] if self.link is not None else 0)
        )
        self.upgrade_costs['adsl'] = (
            (self.parameters['costs_assets_cabinet_adsl'] if self.adsl == 0 else 0)
            +
            (self.link.upgrade_costs['copper'] if self.link is not None else 0)
        )

        # Rollout costs
        self.rollout_costs = {}
        self.rollout_costs['fttp'] = self.upgrade_costs['fttp'] + \
            sum(client.rollout_costs['fttp'] for client in self._clients)
        self.rollout_costs['fttdp'] = self.upgrade_costs['fttdp'] + \
            sum(client.rollout_costs['fttdp'] for client in self._clients)
        self.rollout_costs['fttc'] = self.upgrade_costs['fttc'] + \
            sum(client.rollout_costs['fttc'] for client in self._clients)
        self.rollout_costs['adsl'] = self.upgrade_costs['adsl'] + \
            sum(client.rollout_costs['adsl'] for client in self._clients)

        # Rollout benefits
        self.rollout_benefits = {}
        self.rollout_benefits['fttp'] = sum(
            client.rollout_benefits['fttp'] for client in self._clients)
        self.rollout_benefits['fttdp'] = sum(
            client.rollout_benefits['fttdp'] for client in self._clients)
        self.rollout_benefits['fttc'] = sum(
            client.rollout_benefits['fttc'] for client in self._clients)
        self.rollout_benefits['adsl'] = sum(
            client.rollout_benefits['adsl'] for client in self._clients)

        # Benefit-cost ratio
        self.rollout_bcr = {}
        self.rollout_bcr['fttp'] = _calculate_benefit_cost_ratio(
            self.rollout_benefits['fttp'], self.rollout_costs['fttp'])
        self.rollout_bcr['fttdp'] = _calculate_benefit_cost_ratio(
            self.rollout_benefits['fttdp'], self.rollout_costs['fttdp'])
        self.rollout_bcr['fttc'] = _calculate_benefit_cost_ratio(
            self.rollout_benefits['fttc'], self.rollout_costs['fttc'])
        self.rollout_bcr['adsl'] = _calculate_benefit_cost_ratio(
            self.rollout_benefits['adsl'], self.rollout_costs['adsl'])

    def upgrade(self, action):

        if action == 'rollout_fttp':
            self.fttp = 1
            if self.link is not None:
                self.link.upgrade('fibre')
            for client in self._clients:
                client.upgrade(action)

        if action == 'rollout_fttdp':
            self.fttp = 1
            if self.link is not None:
                self.link.upgrade('fibre')
            for client in self._clients:
                client.upgrade(action)

        self.compute()


class Distribution():
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

    """
    def __init__(self, data, link, parameters):

        # Asset parameters
        self.id = data["id"]
        self.lad = data["lad"]
        self.connection = data["connection"]
        self.fttp = int(data["fttp"])
        self.fttdp = int(data["fttdp"])
        self.fttc = int(data["fttc"])
        self.docsis3 = int(data["docsis3"])
        self.adsl = int(data["adsl"])
        self.total_prems = int(data['total_prems'])
        self.wta = float(data["wta"])
        self.wtp = int(data["wtp"])
        self.adoption_desirability = False

        self.parameters = parameters

        # Link parameters
        self.link = link

        self.compute()

    def compute(self):

        # Upgrade costs
        self.upgrade_costs = {}
        self.upgrade_costs['fttp'] = (
            (self.parameters['costs_assets_premise_fttp_modem'] * self.total_prems) +
            (self.parameters['costs_assets_premise_fttp_optical_network_terminator'] \
                * self.total_prems if self.fttp == 0 else 0) +
            (self.parameters['planning_administration_cost'] * self.total_prems \
                if self.fttp == 0 else 0) +
            (self.parameters['costs_assets_premise_fttp_optical_connection_point'] \
                * (-(-self.total_prems // 32)) if self.fttp == 0 else 0) +
            (self.link.upgrade_costs['fibre'] if self.link is not None else 0)
        )
        self.upgrade_costs['fttdp'] = (
            (self.parameters['costs_assets_distribution_fttdp_8_ports'] \
                * (-(-self.total_prems // 8)) if self.fttdp == 0 else 0) +
            (self.parameters['costs_assets_premise_fttdp_modem'] * self.total_prems \
                if self.fttdp == 0 else 0)
        )
        self.upgrade_costs['fttc'] = (
            (self.parameters['costs_assets_distribution_fttc'] if self.fttc == 0 else 0) +
            (self.parameters['costs_assets_premise_fttc_modem'] if self.fttc == 0 else 0) +
            (self.link.upgrade_costs['copper'] if self.link is not None else 0)
        )
        self.upgrade_costs['adsl'] = (
            (self.parameters['costs_assets_distribution_adsl'] if self.adsl == 0 else 0) +
            (self.parameters['costs_assets_premise_adsl_modem'] if self.adsl == 0 else 0) +
            (self.link.upgrade_costs['copper'] if self.link is not None else 0)
        )

        # Rollout costs
        self.rollout_costs = {}
        self.rollout_costs['fttp'] = int(round(self.upgrade_costs['fttp'], 0))
        self.rollout_costs['fttdp'] = int(round(self.upgrade_costs['fttdp'], 0))
        self.rollout_costs['fttc'] = self.upgrade_costs['fttc']
        self.rollout_costs['adsl'] = self.upgrade_costs['adsl']

        # Rollout benefits
        self.rollout_benefits = {}
        if self.adoption_desirability:
            # Problem: wtp is now aggregated to the distribution point
            # But households will adopt at different times
            # scenario adoption should really be done before the aggregation
            # or a logic developed which relies on the overall attractiveness
            # of the distribution point.
            self.rollout_benefits['fttp'] = (
                int(self.wtp) \
                * self.parameters['months_per_year'] \
                * self.parameters['payback_period'] \
                * (100 - self.parameters['profit_margin']) / 100
            )
            self.rollout_benefits['fttdp'] = (
                int(self.wtp) \
                * self.parameters['months_per_year'] \
                * self.parameters['payback_period'] \
                * (100 - self.parameters['profit_margin']) / 100
            )
            self.rollout_benefits['fttc'] = (
                int(self.wtp) \
                * self.parameters['months_per_year'] \
                * self.parameters['payback_period'] \
                * (100 - self.parameters['profit_margin']) / 100
            )
            self.rollout_benefits['adsl'] = (
                int(self.wtp) \
                * self.parameters['months_per_year'] \
                * self.parameters['payback_period'] \
                * (100 - self.parameters['profit_margin']) / 100
            )
        else:
            self.rollout_benefits['fttp'] = 0
            self.rollout_benefits['fttdp'] = 0
            self.rollout_benefits['fttc'] = 0
            self.rollout_benefits['adsl'] = 0

        # Benefit-cost ratio
        self.rollout_bcr = {}
        self.rollout_bcr['fttp'] = int(_calculate_benefit_cost_ratio(
            self.rollout_benefits['fttp'], self.rollout_costs['fttp']))
        self.rollout_bcr['fttdp'] = int(_calculate_benefit_cost_ratio(
            self.rollout_benefits['fttdp'], self.rollout_costs['fttdp']))
        self.rollout_bcr['fttc'] = _calculate_benefit_cost_ratio(
            self.rollout_benefits['fttc'], self.rollout_costs['fttc'])
        self.rollout_bcr['adsl'] = _calculate_benefit_cost_ratio(
            self.rollout_benefits['adsl'], self.rollout_costs['adsl'])

    def connection_capacity(self, technology):

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

    def __repr__(self):
        return "<Distribution id:{}>".format(self.id)

    def upgrade(self, action):

        if action in ('fttp'):
            action = 'fttp'
            self.fttp = self.total_prems
            self.link.upgrade('fibre')
        if action in ('fttdp'):
            action = 'fttdp'
            self.fttdp = self.total_prems

        self.compute()

    def update_desirability_to_adopt(self, desirability_to_adopt):
        self.adoption_desirability = desirability_to_adopt

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
