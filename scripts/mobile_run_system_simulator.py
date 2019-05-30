from scripts.mobile_cluster_input_files import segments_for_simulator
from scripts.mobile_simulator_run import run_simulator

SIMULATION_PARAMETERS = {
    'iterations': 100,
    'seed_value': None,
    'tx_baseline_height': 30,
    'tx_upper_height': 40,
    'tx_power': 40,
    'tx_gain': 16,
    'tx_losses': 1,
    'rx_gain': 4,
    'rx_losses': 4,
    'rx_misc_losses': 4,
    'rx_height': 1.5,
    'network_load': 50,
    'percentile': 5,
    'desired_transmitter_density': 10,
    'sectorisation': 3,
}

# sectors = segments_for_simulator()

sectors = [
    # ('LS1 3', 'urban'),
    # ('LS6 2', 'suburban'),
    ('LS17 9', 'rural'),
]

for sector, environment in sectors:

    print('--running {}'.format(sector))

    run_simulator(sector, environment, 'synthetic', SIMULATION_PARAMETERS)
