import csv

def read_in_exchange(file_path):
    """

    {'CLBER': {'prem_under_1km': 4576, 
               'prem_1_3km': 13728,
               'prem_over_3km': 4576},
               },
               {'location': {'oslaua':,
                             'oscty':,	
                             'gor':	,
                             'code': }}

    """
    exchange = {}

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

    return exchange


class Exchange(object):
    """

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

    def average_speed_per_exchange(self):
        """
        """

        total_premises = 0
        total_speed = 0

        total_premises = sum([band.premises for band in self.bands])

        proportions = [band.premises / total_premises for band in self.bands] 

        proportions = []
        for band in self.bands:
            proportions.append(band.premises / total_premises)

        average_speed = sum([weight * band.speed for (weight, band) in zip(proportions, self.bands)])

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
        self.bands[band_id - 1].set_technology(technology)


class Band(object):

    def __init__(self, premises, current_speed):
        self.technology = 'current'
        self.premises = int(premises)
        self.speed = current_speed
    
    def set_technology(self, technology):
        self.technology = technology
        if self.technology == 'fttp':
            self.speed = 2000
        elif self.technology == 'gfast':
            self.speed = 300


def apply_interventions_to_exchanges(decisions, exchanges):

    for decision in decisions:
        # Find the matching exchanges with the same geotype
        technology, geotype, band = decision['name'].split("_")
        for id, exchange in exchanges.items():
            if exchange.location['geotype_number'] == geotype:
                exchange.update_band_technology(int(band), technology)
    
def calculate_speed(exchanges):
    """For each OFCOM geography (code), calculate the average speed

    """
    results = []
    for id, exchange in exchanges.items():
        results.append({'speed': exchange.average_speed_per_exchange(),
                        'code': exchange.location['code']})
    return results

def aggregate_by_region(results, region_heading='code'):
    """Calculated running mean 

    Returns
    -------
    dict
        Returns a dictionary aggregated `results` by `region_heading` e.g. {'00London': 50}

    """
    calc_spd = {}

    counts = {}
    totals = {}

    for row in results:
        if row[region_heading] not in totals:
            totals[row[region_heading]] = 0
        if row[region_heading] not in counts:
            counts[row[region_heading]] = 0
        counts[row[region_heading]] += 1
        totals[row[region_heading]] += row['speed']
        calc_spd[row[region_heading]] = totals[row[region_heading]] / counts[row[region_heading]]
    return calc_spd

def run(decisions, file_path='data/exchanges.csv'):
    """

    Notes
    -----

    data['average_speed']['00London']['1'] = 340
    data['premises_passed']['00London']['1'] = 29983
    data['energy_demand']['00London']['1'] = 239

    """
    results = {}


    exchanges = read_in_exchange(file_path)
    apply_interventions_to_exchanges(decisions, exchanges)

    speed = calculate_speed(exchanges)

    results['average_speed'] = aggregate_by_region(speed)
    # energy_demand = calculate_energy_demand(exchanges)
    # premises_passed_by_tech = calculate_premises_passed(exchanges)

    return results
