from scripts.mobile_cluster_input_files import segments_for_simulator
from scripts.mobile_simulator_run import run_simulator

SIMULATION_PARAMETERS = {
    'iterations': 1,
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
    'percentile': 10,
    'desired_transmitter_density': 10,
    'sectorisation': 3,
    'interfering_sites': 20,
    'overbooking_factor': 50,
}

SPECTRUM_PORTFOLIO = [
    ('generic', 'FDD DL', 0.7, 10, '5G'),
    ('generic', 'FDD DL', 0.8, 10, '4G'),
    ('generic', 'FDD DL', 1.8, 10, '4G'),
    ('generic', 'FDD DL', 2.6, 10, '4G'),
    ('generic', 'FDD DL', 3.5, 80, '5G'),
]

MAST_HEIGHT = [
    (30),
    (40)
]

MODULATION_AND_CODING_LUT =[
    # CQI Index	Modulation	Coding rate
    # Spectral efficiency (bps/Hz) SINR estimate (dB)
    ('4G', 1, 'QPSK',	0.0762,	0.1523, -6.7),
    ('4G', 2, 'QPSK',	0.1172,	0.2344, -4.7),
    ('4G', 3, 'QPSK',	0.1885,	0.377, -2.3),
    ('4G', 4, 'QPSK',	0.3008,	0.6016, 0.2),
    ('4G', 5, 'QPSK',	0.4385,	0.877, 2.4),
    ('4G', 6, 'QPSK',	0.5879,	1.1758,	4.3),
    ('4G', 7, '16QAM', 0.3691, 1.4766, 5.9),
    ('4G', 8, '16QAM', 0.4785, 1.9141, 8.1),
    ('4G', 9, '16QAM', 0.6016, 2.4063, 10.3),
    ('4G', 10, '64QAM', 0.4551, 2.7305, 11.7),
    ('4G', 11, '64QAM', 0.5537, 3.3223, 14.1),
    ('4G', 12, '64QAM', 0.6504, 3.9023, 16.3),
    ('4G', 13, '64QAM', 0.7539, 4.5234, 18.7),
    ('4G', 14, '64QAM', 0.8525, 5.1152, 21),
    ('4G', 15, '64QAM', 0.9258, 5.5547, 22.7),
    ('5G', 1, 'QPSK', 78, 0.1523, -6.7),
    ('5G', 2, 'QPSK', 193, 0.377, -4.7),
    ('5G', 3, 'QPSK', 449, 0.877, -2.3),
    ('5G', 4, '16QAM', 378, 1.4766, 0.2),
    ('5G', 5, '16QAM', 490, 1.9141, 2.4),
    ('5G', 6, '16QAM', 616, 2.4063, 4.3),
    ('5G', 7, '64QAM', 466, 2.7305, 5.9),
    ('5G', 8, '64QAM', 567, 3.3223, 8.1),
    ('5G', 9, '64QAM', 666, 3.9023, 10.3),
    ('5G', 10, '64QAM', 772, 4.5234, 11.7),
    ('5G', 11, '64QAM', 873, 5.1152, 14.1),
    ('5G', 12, '256QAM', 711, 5.5547, 16.3),
    ('5G', 13, '256QAM', 797, 6.2266, 18.7),
    ('5G', 14, '256QAM', 885, 6.9141, 21),
    ('5G', 15, '256QAM', 948, 7.4063, 22.7),
]

SITE_DENSITIES = {
    'urban': [
        7.22, 3.21, 1.8, 1.15, 0.8, #0.59,
        0.45, #0.36, 0.29, 0.24, 0.2, 0.17,
        0.15, #0.13, 0.11, 0.1, 0.09, 0.08,
        0.07, #0.05, 0.03, 0.02
    ],
    'suburban': [
        0.59, #0.45, 0.36,
        0.29, #0.24, 0.2,
        #0.17,
        0.15, #0.13, 0.09, 0.07,
        0.06,
        #0.05, 0.03,
        0.0236, #0.018, 0.0143,
        #0.0115, 0.0095,
        0.008,
    ],
    'rural': [
        0.0500, 0.0115, 0.0080, #0.0051,
        0.0040,
        #0.0029, 0.0024,
        0.0018, 0.0016, 0.0013,
        # 0.0009, #0.0007,
        # 0.0006,
    ]
}

# sectors = segments_for_simulator()

SECTORS = [
    # ('LS1 3', 'urban'),
    # ('LS6 2', 'suburban'),
    # ('LS17 9', 'rural'),
    ('ML12 6', 'rural'),
]

for sector, environment in SECTORS:

    print('--running {}'.format(sector))

    run_simulator(sector,
        'synthetic',
        SIMULATION_PARAMETERS,
        SPECTRUM_PORTFOLIO,
        MAST_HEIGHT,
        SITE_DENSITIES,
        MODULATION_AND_CODING_LUT
        )
