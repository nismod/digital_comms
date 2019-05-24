"""Decide on interventions
"""
# pylint: disable=C0103
from digital_comms.mobile_network.model import PostcodeSector

import copy
import math

################################################################
# EXAMPLE COST LOOKUP TABLE
# - TODO come back to net present value or total cost
# of ownership for costs
################################################################

# Postcode-sector level individual interventions
INTERVENTIONS = {
    'carrier_800_1800_2600': {
        'name': 'Upgrade site to LTE',
        'description': 'If a site has only 2G/3G',
        'result': '800, 1800 and 2600 bands available',
        'cost': 142446,
        'assets_to_build': [
            {
                # site_ngr to match upgraded
                'site_ngr': None,
                'frequency': '800',
                'technology': 'LTE',
                'type': 'macrocell_site',
                'bandwidth': '2x10MHz',
                'sectors': 3,
                # set build date when deciding
                'build_date': None,
            },
            {
                # site_ngr to match upgraded
                'site_ngr': None,
                'frequency': '1800',
                'technology': 'LTE',
                'type': 'macrocell_site',
                'bandwidth': '2x10MHz',
                'sectors': 3,
                # set build date when deciding
                'build_date': None,
            },
            {
                # site_ngr to match upgraded
                'site_ngr': None,
                'frequency': '2600',
                'technology': 'LTE',
                'type': 'macrocell_site',
                'bandwidth': '2x10MHz',
                'sectors': 3,
                # set build date when deciding
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
                # site_ngr to match upgraded
                'site_ngr': None,
                'frequency': '700',
                'technology': 'LTE',
                'type': 'macrocell_site',
                'bandwidth': '2x10MHz',
                'sectors': 3,
                # set build date when deciding
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
                # site_ngr to match upgraded
                'site_ngr': None,
                'frequency': '3500',
                'technology': 'LTE',
                'type': 'macrocell_site',
                'bandwidth': '2x10MHz',
                'sectors': 3,
                # set build date when deciding
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
                # site_ngr to match upgraded
                'site_ngr': None,
                'frequency': 'x6_sectors',
                'technology': '5G',
                'type': 'macrocell_site',
                'bandwidth': '2x10MHz',
                'sectors': 6,
                # set build date when deciding
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
                # site_ngr not used
                'site_ngr': 'new_macro_site',
                'frequency': ['800', '1800', '2600'],
                'technology': '4G',
                'type': 'macro_site',
                'bandwidth': '2x10MHz',
                'sectors': 3,
                # set build date when deciding
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
                # site_ngr not used
                'site_ngr': 'new_macro_site',
                'frequency': ['700', '800', '1800', '2600', '3500'],
                'technology': '5G',
                'type': 'macro_site',
                'bandwidth': '2x10MHz',
                'sectors': 3,
                # set build date when deciding
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
                # site_ngr not used
                'site_ngr': 'small_cell_sites',
                'frequency': '3700',
                'technology': 'same',
                'type': 'small_cell',
                'bandwidth': '2x25MHz',
                'sectors': 1,
                # set build date when deciding
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
                # site_ngr not used
                'site_ngr': 'extended_height',
                'frequency': 'same',
                'technology': 'same',
                'type': 'extended_height_macro',
                'bandwidth': 'same',
                'sectors': 'same',
                # set build date when deciding
                'build_date': None,
            },
        ]
    },
    'deploy_c_ran': {
        'name': 'Replace D-Ran with C-RAN',
        'description': 'Must be deployed within viable distance \
            from exchange',
        'result': 'Network architecture change to SDN/NFV',
        'cost': 30000,
        'assets_to_build': [
            {
                # site_ngr not used
                'site_ngr': 'c_ran',
                'frequency': 'same',
                'technology': '5G c_ran',
                'type': 'macro_c_ran',
                'bandwidth': 'same',
                'sectors': 'same',
                # set build date when deciding
                'build_date': None,
            },
        ]
    },
}

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
        'carrier_800_1800_2600', 'carrier_700',
        'carrier_3500', 'build_4G_macro_site',
        'build_5G_macro_site'),

    # # Intervention Strategy X
    # # Share new active equipment
    # # The cost of new equipment will effectively reduce.
    # 'neutral_hosting': ('share_activate_equipment'),

    # Intervention Strategy X
    # Deregulate the height of macrocell sites
    # The cost includes raising the height of the
    # existing site mast.
    'deregulation': ('raise_mast_height'),

    # Intervention Strategy X
    # Deregulate the height of macrocell sites
    # The cost includes raising the height of the
    # existing site mast.
    'cloud-ran': ('deploy_c_ran'),

    # Intervention Strategy X
    # Deploy a small cell layer at 3700 MHz
    # The cost will include the small cell unit and
    # the civil works per cell
    'small-cell': ('carrier_800_1800_2600', 'small_cell'),

    # Intervention Strategy X
    # Deploy a small cell layer at 3700 MHz
    # The cost will include the small cell unit and the
    # civil works per cell
    'small-cell-and-spectrum': (
        'carrier_800_1800_2600', 'carrier_700',
        'carrier_3500', 'small_cell'
        ),
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
        service_built, budget = \
            meet_service_obligation(
            budget, available_interventions, timestep,
            service_obligation_capacity,
            system, traffic, market_share, mast_height
            )
    else:
        service_built = []

    # Build to meet demand
    built, budget = meet_demand(
        budget, available_interventions, timestep,
        system, service_obligation_capacity,
        traffic, market_share, mast_height)

    return built + service_built, budget


def meet_service_obligation(budget, available_interventions,
    timestep, service_obligation_capacity,
    system, traffic, market_share, mast_height):

    areas = _suggest_target_postcodes(
        system, service_obligation_capacity
        )

    return _suggest_interventions(
        budget, available_interventions, areas,
        service_obligation_capacity, timestep,
        traffic, market_share, mast_height
        )


def meet_demand(budget, available_interventions, timestep,
    system, service_obligation_capacity,
    traffic, market_share, mast_height):

    areas = _suggest_target_postcodes(system)
    # print([p.capacity_margin for p in areas])
    return _suggest_interventions(budget,
        available_interventions, areas,
        service_obligation_capacity, timestep,
        traffic, market_share, mast_height
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
    traffic, market_share, mast_height):

    built_interventions = []
    spend = []
    for area in areas:

        area_interventions = []

        if budget <= 0:
            break

        if _area_satisfied(area, area_interventions,
            service_obligation_capacity,
            traffic, market_share, mast_height):
            continue

        # group assets by site
        assets_by_site = {}
        for asset in area.assets:

            if asset['site_ngr'] not in assets_by_site:
                assets_by_site[asset['site_ngr']] = [asset]
            else:
                assets_by_site[asset['site_ngr']].append(asset)

        # integrate_800 and integrate_2.6
        if 'carrier_800_1800_2600' in available_interventions:

            build_option = INTERVENTIONS['carrier_800_1800_2600']['assets_to_build']
            cost = INTERVENTIONS['carrier_800_1800_2600']['cost']

            for site_ngr, site_assets in assets_by_site.items():

                if site_ngr == 'small_cell_sites':
                    continue

                current_tech, current_freqs = current_tech_and_freqs(site_assets)

                if 'LTE' not in current_tech:
                    for option in build_option:
                        to_build = copy.copy(option)
                        to_build['site_ngr'] = site_ngr
                        to_build['technology'] = '4G'
                        to_build['frequency'] = ['800', '1800', '2600']
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

                    if budget < 0:
                        break

        if budget < 0:
            break

        # integrate_700
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
                        # set both assets to this site_ngr
                        for option in build_option:
                            to_build = copy.copy(option)
                            to_build['site_ngr'] = site_ngr
                            to_build['technology'] = '5G'
                            to_build['frequency'] = ['700', '800', '1800', '2600']
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
                        if budget < 0:
                            break

        if budget < 0:
            break

        # integrate_3.5
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
                    for option in build_option:
                        to_build = copy.copy(option)
                        to_build['site_ngr'] = site_ngr
                        to_build['technology'] = '5G'
                        to_build['frequency'] = ['700', '800', '1800', '2600', '3500']
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
                    if budget < 0:
                        break

        if budget < 0:
            break

        # x6_sectors
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

                    for option in build_option:
                        to_build = copy.copy(option)
                        to_build['site_ngr'] = site_ngr
                        to_build['technology'] = '5G'
                        to_build['frequency'] = ['700', '800', '1800', '2600', '3500']
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
                    if budget < 0:
                        break

        if budget < 0:
            break

        # raise_mast_height
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

                # set both assets to this site_ngr
                for option in build_option:
                    to_build['site_ngr'] = site_ngr
                    to_build['pcd_sector'] = area.id
                    to_build['build_date'] = timestep
                    to_build['site_ngr'] = option['site_ngr']
                    to_build['technology'] = option['technology']
                    to_build['frequency'] = option['frequency']
                    to_build['sectors'] = option['sectors']
                    to_build['pcd_sector'] = area.id
                    to_build['lad'] = area.lad_id
                    to_build['build_date'] = timestep
                    to_build['item'] = 'raise_mast_height'
                    to_build['cost'] = cost

                    area_interventions.append(to_build)
                    built_interventions.append(to_build)

                    budget -= cost
                    if budget < 0:
                        break

        if budget < 0:
            break

        # build_macro_site
        if 'build_4G_macro_site' in available_interventions and \
            timestep < 2020:
            if _area_satisfied(area, area_interventions,
                service_obligation_capacity, traffic,
                market_share, mast_height):
                continue

            for site_ngr, site_assets in assets_by_site.items():
                if site_ngr == 'small_cell_sites':
                    continue

                current_number = 0
                for asset in assets_by_site:
                    if asset.startswith('site_'):
                        current_number += 1

                build_option = INTERVENTIONS['build_4G_macro_site']['assets_to_build']
                cost = INTERVENTIONS['build_4G_macro_site']['cost']

                while True:
                    to_build = copy.deepcopy(build_option)
                    to_build[0]['site_ngr'] = site_ngr
                    to_build[0]['technology'] = '4G'
                    to_build[0]['frequency'] = ['800', '1800', '2600']
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

                    assets = area.assets + built_interventions

                    #if it had all evailable spectrum break, otherwise
                    #it gets stuck here. 810 is max RAN capacity
                    if calc_capacity(area, assets, service_obligation_capacity,
                        traffic, market_share, mast_height) > 810:
                        break

                    if budget < 0 or \
                        _area_satisfied(area, area_interventions,
                        service_obligation_capacity,traffic,
                        market_share, mast_height):
                        break


        # build_macro_site
        if 'build_5G_macro_site' in available_interventions and \
            timestep >= 2020:
            if _area_satisfied(area, area_interventions,
                service_obligation_capacity, traffic,
                market_share, mast_height):
                continue

            for site_ngr, site_assets in assets_by_site.items():
                if site_ngr == 'small_cell_sites':
                    continue

                current_number = 0
                for asset in assets_by_site:
                    if asset.startswith('site_'):
                        current_number += 1

                build_option = INTERVENTIONS['build_5G_macro_site']['assets_to_build']
                cost = INTERVENTIONS['build_5G_macro_site']['cost']

                while True:
                    to_build = copy.deepcopy(build_option)
                    to_build[0]['site_ngr'] = site_ngr
                    to_build[0]['technology'] = '5G'
                    to_build[0]['frequency'] = ['700', '800', '1800', '2600', '3500']
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

                    assets = area.assets + built_interventions

                    if calc_capacity(area, assets, service_obligation_capacity,
                        traffic, market_share, mast_height) > 810:
                        break

                    if budget < 0 or \
                        _area_satisfied(area, area_interventions,
                        service_obligation_capacity,traffic,
                        market_share, mast_height) :
                        break

        if budget < 0:
            break


        # #deploy Cloud-RAN
        # if 'deploy_c_ran' in available_interventions:
        #     if _area_satisfied(area, area_interventions,
        #         service_obligation_capacity, traffic, market_share):
        #         continue

        #     build_option = INTERVENTIONS['deploy_c_ran']['assets_to_build']
        #     cost = INTERVENTIONS['deploy_c_ran']['cost']
        #     for site_ngr, site_assets in assets_by_site.items():
        #         if site_ngr == 'small_cell_sites':
        #             continue

        #             # set both assets to this site_ngr
        #             for option in build_option:
        #                 to_build = copy.copy(option)
        #                 to_build['site_ngr'] = site_ngr
        #                 to_build['technology'] = '5G_c_ran'
        #                 to_build['pcd_sector'] = area.id
        #                 to_build['build_date'] = timestep
        #                 area_interventions.append(to_build)
        #                 built_interventions.append(to_build)

        #             spend.append((
        #                 area.id, area.lad_id,
        #                 'deploy_c_ran', cost
        #                 ))
        #             budget -= cost
        #             if budget < 0:
        #                 break

        # if budget < 0:
        #     break

        # build small cells to next density
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
                to_build = copy.deepcopy(build_option)
                to_build[0]['build_date'] = timestep
                to_build[0]['pcd_sector'] = area.id

                area_interventions += to_build
                built_interventions += to_build
                spend.append((
                    area.id, area.lad_id,
                    'small_cells', cost
                    ))
                budget -= cost

                if budget < 0 or _area_satisfied(area,
                    area_interventions,
                    service_obligation_capacity,
                    traffic, market_share, mast_height):
                    break

    # assert len(built_interventions) == len(set(built_interventions))
    # return set(built_interventions), budget, set(spend)
    return built_interventions, budget

def _suggest_target_postcodes(system, threshold=None):
    """
    Sort postcodes by population density (descending)
    - if considering threshold, filter out any with capacity above threshold

    """
    postcodes = system.postcode_sectors.values()

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
