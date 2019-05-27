from scripts.mobile_cluster_input_files import segments_for_transmitter_module
from digital_comms.mobile_network.transmitter_module import run_transmitter_module

sectors = segments_for_transmitter_module()

for sector in sectors:

    print('--running {}'.format(sector))

    run_transmitter_module(sector, 'synthetic')
