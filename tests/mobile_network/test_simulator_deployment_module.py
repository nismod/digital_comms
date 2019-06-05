import pytest
import os
import numpy as np
from shapely.geometry import shape, Point

from digital_comms.mobile_network.system_simulator_deployment_module import (
    find_and_deploy_new_site,
    )

def test_find_and_deploy_new_site(setup_transmitters, setup_interfering_sites,
    setup_postcode_sector, setup_simulation_parameters):

    new_transmitter, site_area = find_and_deploy_new_site(
        setup_transmitters, 1, setup_interfering_sites,
        setup_postcode_sector, setup_simulation_parameters
        )

    assert len(new_transmitter) == 5
    assert new_transmitter[0]['properties']['sitengr'] == '{new}{GEN4}'

    new_transmitter, site_area = find_and_deploy_new_site(
        setup_transmitters, 4, setup_interfering_sites,
        setup_postcode_sector, setup_simulation_parameters
        )

    assert len(new_transmitter) == 8
    assert new_transmitter[3]['properties']['sitengr'] == '{new}{GEN7}'

    new_transmitter, site_area = find_and_deploy_new_site(
        setup_transmitters, 20, setup_interfering_sites,
        setup_postcode_sector, setup_simulation_parameters
        )

    assert len(new_transmitter) == 24
    assert new_transmitter[19]['properties']['sitengr'] == '{new}{GEN23}'
