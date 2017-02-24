"""The fixed broadband model

"""

import csv

class Exchange(object):
    """An asset which serves fixed broadband premises

    An Exchange is associated with a `geotype`, an area `code`.

    The areas served by an Exchange are disaggregated into Bands, each of
    which uses a technology. Average connection speed at the premises is a
    function of the technology.

    Arguments
    ---------
    location: dict
        Contains 'oslaua', 'oscty', 'gor', 'code', 'geotype_name', 'geotype_number'
    """

    def __init__(self, premises, speeds, location):

        self.bands = []

        for premise, speed in zip(premises, speeds):
            self.bands.append(Band(premise, speed))

        self.location = location

    def weighted_premises(self):
        """Calculates the proportion of premises per band for the exchange

        Returns
        -------
        list
            A list, of length ``len(self.bands)`` containing the proportion of
            premises held in each band
        """
        total_premises = sum([band.premises for band in self.bands])

        weights = [band.premises / total_premises for band in self.bands]

        return weights

    def average_speed_per_exchange(self):
        """Computes weighted average of speeds at the premesis per Exchange

        Returns
        -------
        float
        """
        average_speed = sum([weight * band.speed \
            for (weight, band) in zip(self.weighted_premises(), self.bands)])

        return average_speed

    def update_band_technology(self, band_id, technology):
        """Update the technology in a band

        Arguments
        ---------
        band_id: int
            The number of the band to update (1 to 3)
        technology: str
            The name of a valid technology ('fttp' or 'gfast')
        """
        self.bands[band_id - 1].technology = technology


class Band(object):
    """A `Band` is an area surrounding an exchange

    A `Band` collects premises of similar connection speeds
    around an `Exchange`

    Parameters
    ----------
    premises: int
        The number of premises served in the `Band`
    current_speed: float
        The existing average connection speed of the premises in the `Band`

    Attributes
    ----------
    speed: float
        The connection speed available to premises in this `Band`
    """

    def __init__(self, premises, current_speed):
        self._technology = 'current'
        self.premises = int(premises)
        self.speed = current_speed

    @property
    def technology(self):
        """The technology type currently available in the `Band`
 
        Changing the technology affects the average connection speed.
        """
        return self._technology

    @technology.setter
    def technology(self, technology):
        self._technology = technology
        if self._technology == 'fttp':
            self.speed = 2000
        elif self._technology == 'gfast':
            self.speed = 300



def read_in_exchange(file_path):
    """Reads in the exchanges and regions from the exchange data file

    Parameters
    ----------
    file_path: str
        The file path of the csv file containing the exchange data

    Returns
    -------
    exchange : dict
        A dictionary of :class:`Exchange` objects
    code : dict
        Maps exchanges to codes
    geotype : dict
        Maps exchanges to geotypes.  For examples::

            geotypes = {1: ['CLBER', 'CLBIS', 'CLCAN']}

    """
    exchange = {}
    code = {}
    geotype = {}

    with open(file_path) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:

            prem_1 = int(row['prem_under_1km'])
            prem_2 = int(row['prem_1_3km'])
            prem_3 = int(row['prem_over_3km'])

            premises = [prem_1, prem_2, prem_3]

            speed = int(row['av_spd_per_prem'])
            speeds = [speed, speed, speed]

            locations = {'oslaua': row['oslaua'],
                         'oscty': row['oscty'],
                         'gor': row['gor'],
                         'code': row['code'],
                         'geotype_number': row['geotype_number']}

            exchange[row['exchange']] = Exchange(premises,
                                                 speeds,
                                                 locations)

            if row['code'] not in code:
                code[row['code']] = []
            else:
                code[row['code']].append(row['exchange'])

            if row['geotype_number'] not in geotype:
                geotype[row['geotype_number']] = []
            else:
                geotype[row['geotype_number']].append(row['exchange'])

    return exchange, code, geotype





def apply_interventions_to_exchanges(decisions, exchanges, geotypes):
    """

    Arguments
    ---------
    decisions: list
        A list of intervention dicts
    exchanges: dict
        The dictionary of exchanges
    geotypes: dict
        The dictionary of exchanges mapped to geotypes
    """

    for decision in decisions:
        # Find the matching exchanges with the same geotype
        technology, geotype, band = decision['name'].split("_")

        for exchange_id in geotypes[geotype]:

        # for id, exchange in exchanges.items():
        #     if exchange.location['geotype_number'] == geotype:
            exchanges[exchange_id].update_band_technology(int(band), technology)

def calculate_speed(exchanges):
    """For each OFCOM geography (code), calculate the average speed

    Returns
    -------
    dict
        Returns a dictionary, where the exchange id is the key, and the
        average speed is the value
    """
    results = {}
    for key, exchange in exchanges.items():
        results[key] = exchange.average_speed_per_exchange()
    return results

def aggregate_by_region(results, aggregation):
    """Calculates average over an aggregated set of exchanges

    Arguments
    ---------
    results : dict
        A dictionary with exchange id as keys and values as values
    aggregation: dict
        A dict with aggregation heading as key, and list of exchange ids as values

    Returns
    -------
    dict
        Returns a dictionary aggregated `results` by `aggregation` e.g. {'00London': 50}

    """
    aggregated_results = {}

    for heading, exchanges in aggregation.items():
        total = sum([results[exchange] for exchange in exchanges])
        count = len(exchanges)
        aggregated_results[heading] = total / count

    return aggregated_results

def run(decisions, file_path='data/exchanges.csv'):
    """

    Notes
    -----

    data['average_speed']['00London']['1'] = 340
    data['premises_passed']['00London']['1'] = 29983
    data['energy_demand']['00London']['1'] = 239

    """
    results = {}

    exchanges, codes, geotypes = read_in_exchange(file_path)

    apply_interventions_to_exchanges(decisions, exchanges, geotypes)

    speed = calculate_speed(exchanges)

    results['average_speed'] = aggregate_by_region(speed, codes)
    # energy_demand = calculate_energy_demand(exchanges)
    # premises_passed_by_tech = calculate_premises_passed(exchanges)

    return results
