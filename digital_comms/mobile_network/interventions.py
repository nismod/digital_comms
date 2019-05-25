"""Decide on interventions
"""
# pylint: disable=C0103
from digital_comms.mobile_network.model import PostcodeSector

import copy
import math
from itertools import groupby

################################################################
# EXAMPLE COST LOOKUP TABLE
# - TODO come back to net present value or total cost
# of ownership for costs
################################################################


STRATEGIES = {
    # Intervention Strategy X
    # Minimal Intervention 'Do Nothing Scenario'
    # Build no more additional sites -> will lead to a capacity
    # margin deficit. The cost will be the replacement of
    # existing units annually based on the (decommissioning
    # rate of 10%) common asset lifetime of 10 years
    # Capacity will be the sum of 800 and 2600 MHz
    'minimal': (),

    'upgrade-to-lte': ('carrier_800_1800_2600'),

    # Intervention Strategy X
    # Integrate 700 and 3500 MHz on to the macrocellular layer
    # The cost will be the addtion of another carrier on each
    # basestation ~£15k (providing thre is 4G already)
    # If 4G isn't present, the site will need major upgrades.
    'macrocell-700-3500': (
        'carrier_800_1800_2600', 'carrier_700', 'carrier_3500'
        ),

    # Intervention Strategy X
    # Integrate 700
    'macrocell-700': ('carrier_800_1800_2600', 'carrier_700'),

    # Intervention Strategy X
    # Increase sectoration on macrocell sites
    # The cost will include three additional cells,
    # so from x3 to x6.
    'sectorisation': (
        'carrier_800_1800_2600', 'carrier_700',
        'carrier_3500', 'add_3_sectors',
        ),

    # Intervention Strategy X
    # Build more macrocell sites
    # The cost will include three multicarrier cells,
    # mast & civil works.
    'macro-densification': (
        'carrier_800_1800_2600',
        'carrier_700',
        'carrier_3500',
        'build_5G_macro_site',
        ),

    # # Intervention Strategy X
    # # Share new active equipment
    # # The cost of new equipment will effectively reduce.
    # 'neutral_hosting': ('share_activate_equipment'),

    # Intervention Strategy X
    # Deregulate the height of macrocell sites
    # The cost includes raising the height of the
    # existing site mast.
    'deregulation': ('carrier_800_1800_2600', 'carrier_700',
        'carrier_3500', 'raise_mast_height'),

    # Intervention Strategy X
    # Deregulate the height of macrocell sites
    # The cost includes raising the height of the
    # existing site mast.
    'cloud-ran': ('carrier_800_1800_2600', 'carrier_700',
        'carrier_3500', 'macro_5G_c_ran'),

    # Intervention Strategy X
    # Deploy a small cell layer at 3700 MHz
    # The cost will include the small cell unit and the
    # civil works per cell
    'small-cell-and-spectrum': (
        # 'carrier_800_1800_2600', 'carrier_700',
        # 'carrier_3500',
        'small_cell'
        ),
}


# Postcode-sector level individual interventions
INTERVENTIONS = {
    'carrier_800_1800_2600': {
        'name': 'Upgrade site to LTE',
        'description': 'If a site has only 2G/3G',
        'result': '800, 1800 and 2600 bands available',
        'cost': 142446,
        'assets_to_build': [
            {
                'site_ngr': None,
                'frequency': '800',
                'technology': 'LTE',
                'type': 'macrocell_site',
                'bandwidth': '2x10MHz',
                'sectors': 3,
                'mast_height': 30,
                'build_date': None,
            },
            {
                'site_ngr': None,
                'frequency': '1800',
                'technology': 'LTE',
                'type': 'macrocell_site',
                'bandwidth': '2x10MHz',
                'sectors': 3,
                'mast_height': 30,
                'build_date': None,
            },
            {
                'site_ngr': None,
                'frequency': '2600',
                'technology': 'LTE',
                'type': 'macrocell_site',
                'bandwidth': '2x10MHz',
                'sectors': 3,
                'mast_height': 30,
                'build_date': None,
            },
        ]
    },
    'carrier_700': {
        'name': 'Build 700 MHz carrier',
        'description': 'Available if a site has LTE',
        'result': '700 band available',
        'cost': 50917,
        'assets_to_build': [
            {
                'site_ngr': None,
                'frequency': '700',
                'technology': 'LTE',
                'type': 'macrocell_site',
                'bandwidth': '2x10MHz',
                'sectors': 3,
                'mast_height': 30,
                'build_date': None,
            },
        ]
    },
    'carrier_3500': {
        'name': 'Build 3500 MHz carrier',
        'description': 'Available if a site has LTE',
        'result': '3500 band available',
        'cost': 50917,
        'assets_to_build': [
            {
                'site_ngr': None,
                'frequency': '3500',
                'technology': '5G',
                'type': 'macrocell_site',
                'bandwidth': '2x10MHz',
                'sectors': 3,
                'mast_height': 30,
                'build_date': None,
            },
        ]
    },
    'add_3_sectors': {
        'name': 'sectorisation carrier',
        'description': 'Available if a site has LTE',
        'result': '6 sectors are available',
        'cost': 50000, #£10k each, plus £20 installation
        'assets_to_build': [
            {
                'site_ngr': None,
                'frequency': 'x6_sectors',
                'technology': '5G',
                'type': 'macrocell_site',
                'bandwidth': '2x10MHz',
                'sectors': 6,
                'mast_height': 30,
                'build_date': None,
            },
        ]
    },
    'build_4G_macro_site': {
        'name': 'Build a new 4G macro site',
        'description': 'Must be deployed at preset densities \
            to be modelled',
        'result': 'Macrocell sites available at given density',
        'cost': 150000,
        'assets_to_build': [
            {
                'site_ngr': '',
                'frequency': ['800', '1800', '2600'],
                'technology': '4G',
                'type': 'macro_site',
                'bandwidth': '2x10MHz',
                'sectors': 3,
                'mast_height': 30,
                'build_date': None,
            },
        ]
    },
    'build_5G_macro_site': {
        'name': 'Build a new 5G macro site',
        'description': 'Must be deployed at preset densities \
            to be modelled',
        'result': 'Macrocell sites available at given density',
        'cost': 150000,
        'assets_to_build': [
            {
                'site_ngr': '',
                'frequency': ['700', '800', '1800', '2600', '3500'],
                'technology': '5G',
                'type': 'macro_site',
                'bandwidth': '2x10MHz',
                'sectors': 3,
                'mast_height': 30,
                'build_date': None,
            },
        ]
    },
    'small_cell': {
        'name': 'Build a small cell',
        'description': 'Must be deployed at preset densities \
            to be modelled',
        'result': '2x25 MHz small cells available at given density',
        'cost': 40220,
        'assets_to_build': [
            {
                'site_ngr': 'small_cell_sites',
                'frequency': '3700',
                'technology': 'same',
                'type': 'small_cell',
                'bandwidth': '2x25MHz',
                'sectors': 1,
                'build_date': None,
            },
        ]
    },
    'raise_mast_height': {
        'name': 'Raises existing mast height',
        'description': 'Must be deployed at preset densities to \
            be modelled',
        'result': 'Same technology but with new enhanced capacity',
        'cost': 30000,
        'assets_to_build': [
            {
                'site_ngr': 'extended_height',
                'frequency': None,
                'technology': None,
                'type': 'extended_height_macro',
                'bandwidth': None,
                'sectors': None,
                'mast_height': 40,
                'build_date': None,
            },
        ]
    },
    'macro_5G_c_ran': {
        'name': 'Replace D-Ran with C-RAN',
        'description': 'Must be deployed within viable distance \
            from exchange',
        'result': 'Network architecture change to SDN/NFV',
        'cost': 30000,
        'assets_to_build': [
            {
                'site_ngr': None,
                'frequency': None,
                'technology': '5G_c_ran',
                'type': 'macro_5G_c_ran',
                'bandwidth': None,
                'sectors': None,
                'build_date': None,
            },
        ]
    },
}


def decide_interventions(strategy, budget,
    service_obligation_capacity, system, timestep,
    traffic, market_share, mast_height):
    """
    Given strategy parameters and a system return some
    next best intervention.
    Parameters
    ----------
    strategy : str
        See above for full list.
    budget : int
        Annual budget in GBP
    service_obligation_capacity : float
        Threshold for universal mobile service, in Mbps/km^2
    system : NetworkManager
        Gives areas (postcode sectors) with population
        density, demand
    Returns
    -------
    tuple
        0: `obj`:`list` of `obj`:`dict`
            Details of the assets that were built
            Each containing the keys
                site_ngr: str
                    Unique site reference number
                frequency: str
                    Asset frequency ("700", ..)
                technology: str
                    Asset technology ("LTE", ..)
                bandwidth: str
                    Asset bandwith ("2x10MHz", ..)
                build_date: int
                    Timestep when the asset was built
                pcd_sector: int
                    Id of the postcode sector where asset
                    is located
        1: int
            Remaining budget
        2: int
            Total costs of intervention build step

    """
    available_interventions = STRATEGIES[strategy]
    if service_obligation_capacity > 0:
        unique_intervention_ids = []
        service_built, budget, unique_intervention_ids = \
            meet_service_obligation(
            budget, available_interventions, timestep,
            service_obligation_capacity,
            system, traffic, market_share, mast_height,
            unique_intervention_ids
            )

    else:
        service_built = []

    built, budget, unique_intervention_ids = meet_demand(
        budget, available_interventions, timestep,
        system, service_obligation_capacity,
        traffic, market_share, mast_height,
        unique_intervention_ids)

    return service_built + built, budget


def meet_service_obligation(budget, available_interventions,
    timestep, service_obligation_capacity,
    system, traffic, market_share, mast_height,
    unique_intervention_ids):

    areas = _suggest_target_postcodes(
        system, service_obligation_capacity
        )

    return _suggest_interventions(
        budget, available_interventions, areas,
        service_obligation_capacity, timestep,
        traffic, market_share, mast_height,
        unique_intervention_ids
        )


def meet_demand(budget, available_interventions, timestep,
    system, service_obligation_capacity,
    traffic, market_share, mast_height,
    unique_intervention_ids):

    areas = _suggest_target_postcodes(system)

    return _suggest_interventions(budget,
        available_interventions, areas,
        service_obligation_capacity, timestep,
        traffic, market_share, mast_height,
        unique_intervention_ids
        )


def current_tech_and_freqs(site_assets):

    current_tech = []
    current_freqs = []

    for asset in site_assets:
        current_tech.append(asset['technology'])
        for frequency in asset['frequency']:
            current_freqs.append(frequency)

    return current_tech, current_freqs


def _suggest_interventions(budget, available_interventions,
    areas, service_obligation_capacity, timestep,
    traffic, market_share, mast_height,
    unique_intervention_ids):

    built_interventions = []

    for area in areas:

        area_interventions = []

        if budget <= 0:
            break

        if _area_satisfied(area, area_interventions,
            service_obligation_capacity,
            traffic, market_share, mast_height):
            continue

        assets_by_site = {}
        for asset in area.assets:

            if asset['site_ngr'] not in assets_by_site:
                assets_by_site[asset['site_ngr']] = [asset]
            else:
                assets_by_site[asset['site_ngr']].append(asset)

        if 'carrier_800_1800_2600' in available_interventions:

            build_option = INTERVENTIONS['carrier_800_1800_2600']['assets_to_build']
            cost = INTERVENTIONS['carrier_800_1800_2600']['cost']

            for site_ngr, site_assets in assets_by_site.items():

                if site_ngr == 'small_cell_sites':
                    continue

                current_tech, current_freqs = current_tech_and_freqs(site_assets)

                if 'LTE' not in current_tech:
                    for option in build_option:

                        unique_id = (site_ngr + '_' + '4G' + '_' + 'carrier_800_1800_2600')

                        if unique_id not in unique_intervention_ids:

                            unique_intervention_ids.append(unique_id)

                            to_build = copy.copy(option)
                            to_build['site_ngr'] = site_ngr
                            to_build['technology'] = '4G'
                            to_build['frequency'] = ['800', '1800', '2600']
                            to_build['ran_type'] = 'distributed'
                            to_build['sectors'] = 3
                            to_build['pcd_sector'] = area.id
                            to_build['lad'] = area.lad_id
                            to_build['build_date'] = timestep
                            to_build['item'] = 'carrier_800_1800_2600'
                            to_build['cost'] = cost

                            area_interventions.append(to_build)
                            built_interventions.append(to_build)
                            assets_by_site[site_ngr] = [to_build]

                            budget -= cost

                            if budget <= 0:
                                break

        if budget <= 0:
            break

        if 'carrier_700' in available_interventions and \
            timestep >= 2020:

            if _area_satisfied(area, area_interventions,
                service_obligation_capacity, traffic,
                market_share, mast_height):
                continue

            build_option = INTERVENTIONS['carrier_700']['assets_to_build']
            cost = INTERVENTIONS['carrier_700']['cost']

            for site_ngr, site_assets in assets_by_site.items():

                if site_ngr == 'small_cell_sites':
                    continue

                current_tech, current_freqs = current_tech_and_freqs(site_assets)

                if 'LTE' in current_tech and \
                    '700' not in current_freqs:

                    unique_id = (site_ngr + '_' + '5G' + '_' + 'carrier_700')

                    if unique_id not in unique_intervention_ids:
                        unique_intervention_ids.append(unique_id)
                        for option in build_option:
                            to_build = copy.copy(option)
                            to_build['site_ngr'] = site_ngr
                            to_build['technology'] = '5G'
                            to_build['frequency'] = ['700', '800', '1800', '2600']
                            to_build['ran_type'] = 'distributed'
                            to_build['bandwidth'] = 'frequency_dependent'
                            to_build['sectors'] = 3
                            to_build['pcd_sector'] = area.id
                            to_build['lad'] = area.lad_id
                            to_build['build_date'] = timestep
                            to_build['item'] = 'carrier_700'
                            to_build['cost'] = cost

                            area_interventions.append(to_build)
                            built_interventions.append(to_build)
                            assets_by_site[site_ngr] = [to_build]

                            budget -= cost
                            if budget <= 0:
                                break

        if budget <= 0:
            break

        if 'carrier_3500' in available_interventions and \
            timestep >= 2020:

            if _area_satisfied(area, area_interventions,
                service_obligation_capacity, traffic,
                market_share, mast_height):
                continue

            build_option = INTERVENTIONS['carrier_3500']['assets_to_build']
            cost = INTERVENTIONS['carrier_3500']['cost']

            for site_ngr, site_assets in assets_by_site.items():
                if site_ngr == 'small_cell_sites':
                    continue

                current_tech, current_freqs = current_tech_and_freqs(site_assets)
                if '5G' in current_tech and \
                    '3500' not in current_freqs:

                    unique_id = (site_ngr + '_' + '5G' + '_' + 'carrier_3500')

                    if unique_id not in unique_intervention_ids:
                        unique_intervention_ids.append(unique_id)
                        for option in build_option:
                            to_build = copy.copy(option)
                            to_build['site_ngr'] = site_ngr
                            to_build['technology'] = '5G'
                            to_build['frequency'] = ['700', '800', '1800', '2600', '3500']
                            to_build['ran_type'] = 'distributed'
                            to_build['bandwidth'] = 'frequency_dependent'
                            to_build['sectors'] = 3
                            to_build['pcd_sector'] = area.id
                            to_build['lad'] = area.lad_id
                            to_build['build_date'] = timestep
                            to_build['item'] = 'carrier_3500'
                            to_build['cost'] = cost

                            area_interventions.append(to_build)
                            built_interventions.append(to_build)
                            assets_by_site[site_ngr] = [to_build]

                            budget -= cost

                            if budget <= 0:
                                break

        if budget <= 0:
            break

        if 'add_3_sectors' in available_interventions:
            if _area_satisfied(area, area_interventions,
                service_obligation_capacity, traffic,
                market_share, mast_height):
                continue

            build_option = INTERVENTIONS['add_3_sectors']['assets_to_build']
            cost = INTERVENTIONS['add_3_sectors']['cost']

            for site_ngr, site_assets in assets_by_site.items():
                if site_ngr == 'small_cell_sites':
                    continue

                sectors = [site['sectors'] for site in site_assets]

                current_tech, current_freqs = current_tech_and_freqs(site_assets)

                if '5G' in current_tech and \
                    '700' in current_freqs and \
                    '3500' in current_freqs and \
                    6 not in sectors:

                    unique_id = (site_ngr + '_' + '5G' + '_' + 'add_3_sectors')

                    if unique_id not in unique_intervention_ids:
                        unique_intervention_ids.append(unique_id)
                        for option in build_option:
                            to_build = copy.copy(option)
                            to_build['site_ngr'] = site_ngr
                            to_build['technology'] = '5G'
                            to_build['frequency'] = ['700', '800', '1800', '2600', '3500']
                            to_build['ran_type'] = 'distributed'
                            to_build['bandwidth'] = 'frequency_dependent'
                            to_build['sectors'] = 6
                            to_build['pcd_sector'] = area.id
                            to_build['lad'] = area.lad_id
                            to_build['build_date'] = timestep
                            to_build['item'] = 'add_3_sectors'
                            to_build['cost'] = cost

                            area_interventions.append(to_build)
                            built_interventions.append(to_build)
                            assets_by_site[site_ngr] = [to_build]

                            budget -= cost
                            if budget <= 0:
                                break

        if budget <= 0:
            break

        if 'raise_mast_height' in available_interventions:
            if _area_satisfied(area, area_interventions,
                service_obligation_capacity, traffic,
                market_share, mast_height):
                continue

            build_option = INTERVENTIONS['raise_mast_height']['assets_to_build']
            cost = INTERVENTIONS['raise_mast_height']['cost']

            for site_ngr, site_assets in assets_by_site.items():
                if site_ngr == 'small_cell_sites':
                    continue

                unique_id = (site_ngr + '_' + 'raise_mast_height')

                if unique_id not in unique_intervention_ids:
                    unique_intervention_ids.append(unique_id)
                    for option in build_option:
                        to_build = copy.copy(option)
                        to_build['site_ngr'] = site_ngr
                        to_build['pcd_sector'] = area.id
                        to_build['build_date'] = timestep
                        to_build['technology'] = site_assets[0]['technology']
                        to_build['frequency'] = site_assets[0]['frequency']
                        to_build['ran_type'] = 'distributed'
                        to_build['bandwidth'] = 'frequency_dependent'
                        to_build['sectors'] = site_assets[0]['sectors']
                        to_build['pcd_sector'] = area.id
                        to_build['lad'] = area.lad_id
                        to_build['build_date'] = timestep
                        to_build['item'] = 'raise_mast_height'
                        to_build['cost'] = cost

                        area_interventions.append(to_build)
                        built_interventions.append(to_build)

                        budget -= cost
                        if budget <= 0:
                            break

        if budget <= 0:
            break

        if 'build_4G_macro_site' in available_interventions and \
            timestep < 2020:

            if _area_satisfied(area, area_interventions,
                service_obligation_capacity, traffic,
                market_share, mast_height):
                continue
            print('before')
            for site_ngr, site_assets in assets_by_site.items():
                if site_ngr == 'small_cell_sites':
                    continue

                build_option = INTERVENTIONS['build_4G_macro_site']['assets_to_build']
                cost = INTERVENTIONS['build_4G_macro_site']['cost']

                current_number = 0
                if site_ngr.startswith('site_'):
                    current_number += 1

                while True:

                    parts = site_ngr.partition('_')

                    unique_id = (
                        parts[0] + '_' + str(current_number + 1) + '_build_4G_macro_site'
                        )
                    print('before')
                    if unique_id not in unique_intervention_ids:
                        print('here')
                        unique_intervention_ids.append(unique_id)
                        to_build = copy.deepcopy(build_option)
                        to_build[0]['site_ngr'] = 'site_' + str(current_number + 1)
                        to_build[0]['technology'] = '4G'
                        to_build[0]['frequency'] = ['800', '1800', '2600']
                        to_build[0]['ran_type'] = 'distributed'
                        to_build[0]['bandwidth'] = 'frequency_dependent'
                        to_build[0]['sectors'] = 3
                        to_build[0]['pcd_sector'] = area.id
                        to_build[0]['lad'] = area.lad_id
                        to_build[0]['build_date'] = timestep
                        to_build[0]['item'] = 'build_4G_macro_site'
                        to_build[0]['cost'] = cost

                        area_interventions += to_build
                        built_interventions += to_build
                        assets_by_site[site_ngr] = [to_build]

                        budget -= cost
                        current_number += 1

                        if calc_capacity(area, area_interventions,
                            service_obligation_capacity, traffic,
                            market_share, mast_height) >= check_max_capacity(area):
                            break

                        if budget <= 0 or \
                            _area_satisfied(area, area_interventions,
                            service_obligation_capacity, traffic,
                            market_share, mast_height):
                            break

        if budget <= 0:
            break

        if 'build_5G_macro_site' in available_interventions and \
            timestep >= 2020:
            if _area_satisfied(area, area_interventions,
                service_obligation_capacity, traffic,
                market_share, mast_height):
                continue

            for site_ngr, site_assets in assets_by_site.items():
                if site_ngr == 'small_cell_sites':
                    continue

                build_option = INTERVENTIONS['build_5G_macro_site']['assets_to_build']
                cost = INTERVENTIONS['build_5G_macro_site']['cost']

                while True:

                    current_number = 0
                    if site_ngr.startswith('site_'):
                        current_number += 1

                    parts = site_ngr.partition('_')

                    unique_id = (
                        parts[0] + '_' + str(int(parts[2]) + 1) + '_build_5G_macro_site'
                        )

                    current_number += 1
                    if unique_id not in unique_intervention_ids:

                        unique_intervention_ids.append(unique_id)
                        to_build = copy.deepcopy(build_option)
                        to_build[0]['site_ngr'] = 'site_' + str(int(parts[2]) + 1)
                        to_build[0]['technology'] = '5G'
                        to_build[0]['frequency'] = ['700', '800', '1800', '2600', '3500']
                        to_build[0]['ran_type'] = 'distributed'
                        to_build[0]['bandwidth'] = 'frequency_dependent'
                        to_build[0]['sectors'] = 3
                        to_build[0]['pcd_sector'] = area.id
                        to_build[0]['lad'] = area.lad_id
                        to_build[0]['build_date'] = timestep
                        to_build[0]['item'] = 'build_5G_macro_site'
                        to_build[0]['cost'] = cost

                        area_interventions += to_build
                        built_interventions += to_build
                        assets_by_site[site_ngr] = [to_build]

                        budget -= cost

                        if budget <= 0 or \
                            _area_satisfied(area, area_interventions,
                            service_obligation_capacity,traffic,
                            market_share, mast_height) :
                            break

        if budget <= 0:
            break

        #deploy Cloud-RAN
        if 'macro_5G_c_ran' in available_interventions:
            if _area_satisfied(area, area_interventions,
                service_obligation_capacity, traffic,
                market_share, mast_height):
                continue

            build_option = INTERVENTIONS['macro_5G_c_ran']['assets_to_build']
            cost = INTERVENTIONS['macro_5G_c_ran']['cost']

            for site_ngr, site_assets in assets_by_site.items():
                if site_ngr == 'small_cell_sites':
                    continue

                unique_id = (site_ngr + '_' + 'raise_mast_height')

                if unique_id not in unique_intervention_ids:
                    unique_intervention_ids.append(unique_id)

                    for option in build_option:
                        to_build = copy.copy(option)
                        to_build['site_ngr'] = site_ngr
                        to_build['pcd_sector'] = area.id
                        to_build['build_date'] = timestep
                        to_build['technology'] = '5G'
                        to_build['frequency'] = ['700', '800', '1800', '2600', '3500']
                        to_build['ran_type'] = 'distributed'
                        to_build['bandwidth'] = 'frequency_dependent'
                        to_build['sectors'] = 3
                        to_build['pcd_sector'] = area.id
                        to_build['lad'] = area.lad_id
                        to_build['build_date'] = timestep
                        to_build['item'] = 'macro_5G_c_ran'
                        to_build['cost'] = cost

                        area_interventions.append(to_build)
                        built_interventions.append(to_build)

                        budget -= cost
                        if budget <= 0:
                            break

        if budget <= 0:
            break

        if 'small_cell' in available_interventions and timestep >= 2020:
            if _area_satisfied(area, area_interventions,
                service_obligation_capacity, traffic,
                market_share, mast_height):
                continue

            if 'small_cell_sites' in assets_by_site:
                current_number = len(assets_by_site['small_cell_sites'])
            else:
                current_number = 0

            build_option = INTERVENTIONS['small_cell']['assets_to_build']
            cost = INTERVENTIONS['small_cell']['cost']

            while True:

                unique_id = (
                    'small_cell_sites' + '5G' + str(current_number + 1)
                    )

                if unique_id not in unique_intervention_ids:

                    unique_intervention_ids.append(unique_id)

                    to_build = copy.deepcopy(build_option)
                    to_build[0]['site_ngr'] =  'small_cell_sites' + str(current_number + 1)
                    to_build[0]['build_date'] = timestep
                    to_build[0]['pcd_sector'] = area.id

                    area_interventions += to_build
                    built_interventions += to_build
                    assets_by_site[area.id] = [to_build]

                    budget -= cost
                    current_number += 1

                    if budget <= 0 or _area_satisfied(area,
                        area_interventions,
                        service_obligation_capacity,
                        traffic, market_share, mast_height):
                        break

    return built_interventions, budget, unique_intervention_ids

def _suggest_target_postcodes(system, threshold=None):
    """
    Sort postcodes by population density (descending)
    - if considering threshold, filter out any with capacity above threshold

    """
    postcodes = system.postcode_sectors.values()

    if len(postcodes) == 0:
        print('No postcodes found to suggest!')

    if threshold is not None:
        considered_postcodes = [
            pcd for pcd in postcodes if pcd.capacity < threshold
            ]
    else:
        considered_postcodes = [p for p in postcodes]

    return sorted(
        considered_postcodes, key=lambda pcd: pcd.capacity_margin
        )

def _area_satisfied(area, assets, service_obligation_capacity,
    traffic, market_share, mast_height):

    if service_obligation_capacity == 0:
        target_capacity = area.demand

    else:
        target_capacity = service_obligation_capacity

    reached_capacity = calc_capacity(
        area, assets, service_obligation_capacity,
        traffic, market_share, mast_height
        )
    # print(reached_capacity)
    return reached_capacity >= target_capacity

def calc_capacity(area, assets, service_obligation_capacity,
    traffic, market_share, mast_height):

    data = {
        "id": area.id,
        "lad_id": area.lad_id,
        "population": area.population,
        "area": area.area,
        "user_throughput": area.user_throughput,
    }

    test_area = PostcodeSector(
        data,
        assets,
        area._capacity_lookup_table,
        area._clutter_lookup,
        service_obligation_capacity,
        traffic,
        market_share,
        mast_height
    )

    return test_area.capacity

def check_max_capacity(area):

    density = float(area.population) / float(area.area)

    if density < 782:
        #rural sum(800, 1800, 2600)
        return 1.6051
    elif 782 <= density < 7959:
        #suburban sum(800, 1800, 2600)
        return 46.801895
    elif 7959 <= density:
        #urban sum(800, 1800, 2600)
        return 490.7478
