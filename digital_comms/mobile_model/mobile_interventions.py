"""Decide on interventions
"""
# pylint: disable=C0103
from digital_comms.mobile_model.ccam import PostcodeSector

import copy
import math

################################################################
# EXAMPLE COST LOOKUP TABLE
# - TODO come back to net present value or total cost of ownership for costs
################################################################

# Postcode-sector level individual interventions
INTERVENTIONS = {
    'upgrade_to_lte': {
        'name': 'Upgrade site to LTE',
        'description': 'If a site has only 2G/3G',
        'result': '800 and 2600 bands available',
        'cost': 142446,
        'assets_to_build': [
            {
                # site_ngr to match upgraded
                'site_ngr': None,
                'frequency': '800',
                'technology': 'LTE',
                'type': 'macrocell_site',
                'bandwidth': '2x10MHz',
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
                # set build date when deciding
                'build_date': None,
            },
        ]
    },
    'small_cell': {
        'name': 'Build a small cell',
        'description': 'Must be deployed at preset densities to be modelled',
        'result': '2x25 MHz small cells available at given density',
        'cost': 40220,
        'assets_to_build': [
            {
                # site_ngr not used
                'site_ngr': 'small_cell_sites',
                'frequency': '3700',
                'technology': '5G',
                'type': 'small_cell',
                'bandwidth': '2x25MHz',
                # set build date when deciding
                'build_date': None,
            },
        ]
    },
}

AVAILABLE_STRATEGY_INTERVENTIONS = {
    # Intervention Strategy 1
    # Minimal Intervention 'Do Nothing Scenario'
    # Build no more additional sites -> will lead to a capacity margin deficit
    # The cost will be the replacement of existing units annually based on the
    # (decommissioning rate of 10%) common asset lifetime of 10 years
    # Capacity will be the sum of 800 and 2600 MHz
    'minimal': (),

    # Intervention Strategy 2
    # Integrate 700 and 3500 MHz on to the macrocellular layer
    # The cost will be the addtion of another carrier on each basestation ~£15k
    # (providing thre is 4G already)
    # If 4G isn't present, the site will need major upgrades.
    'macrocell': ('upgrade_to_lte', 'carrier_700',
                  'carrier_3500'),
     # Intervention Strategy 2.
     # Integrate 700
    'macrocell_700': ('upgrade_to_lte', 'carrier_700'),

    # Intervention Strategy 3
    # Deploy a small cell layer at 3700 MHz
    # The cost will include the small cell unit and the civil works per cell
    'small_cell': ('upgrade_to_lte', 'small_cell'),

    # Intervention Strategy 4
    # Deploy a small cell layer at 3700 MHz
    # The cost will include the small cell unit and the civil works per cell
    'small_cell_and_spectrum': ('upgrade_to_lte', 'carrier_700',
                   'carrier_3500', 'small_cell'),
}


def decide_interventions(strategy, budget, service_obligation_capacity,
                         system, timestep):
    """Given strategy parameters and a system return some next best intervention

    Parameters
    ----------
    strategy : str
        One of 'minimal', 'macrocell', 'small_cell' intervention strategies
    budget : int
        Annual budget in GBP
    service_obligation_capacity : float
        Threshold for universal mobile service, in Mbps/km^2
    system : ICTManager
        Gives areas (postcode sectors) with population density, demand

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
                    Id of the postcode sector where asset is located
        1: int
            Remaining budget
        2: int
            Total costs of intervention build step
    """
    available_interventions = AVAILABLE_STRATEGY_INTERVENTIONS[strategy]

    if service_obligation_capacity > 0:
        service_built, budget, service_spend = meet_service_obligation(budget,
            available_interventions, timestep, service_obligation_capacity, system)
    else:
        service_built = []
        service_spend = []

    # Build to meet demand
    built, budget, spend = meet_demand(
        budget, available_interventions, timestep, system)

    print("Service", len(service_built))
    print("Demand", len(built))

    return built + service_built, budget, spend + service_spend


def meet_service_obligation(budget, available_interventions, timestep,
                            service_obligation_capacity, system):
    areas = _suggest_target_postcodes(system, service_obligation_capacity)
    return _suggest_interventions(
        budget, available_interventions, areas, timestep, service_obligation_capacity)


def meet_demand(budget, available_interventions, timestep, system):
    areas = _suggest_target_postcodes(system)
    return _suggest_interventions(
        budget, available_interventions, areas, timestep)


def _suggest_interventions(budget, available_interventions, areas, timestep, threshold=None):
    built_interventions = []
    spend = []
    for area in areas:
        area_interventions = []
        if budget < 0:
            break

        if _area_satisfied(area, area_interventions, threshold):
            continue

        # group assets by site
        assets_by_site = {}
        for asset in area.assets:
            if asset['site_ngr'] not in assets_by_site:
                assets_by_site[asset['site_ngr']] = [asset]
            else:
                assets_by_site[asset['site_ngr']].append(asset)

        # integrate_800 and integrate_2.6
        if 'upgrade_to_lte' in available_interventions:
            build_option = INTERVENTIONS['upgrade_to_lte']['assets_to_build']
            cost = INTERVENTIONS['upgrade_to_lte']['cost']
            for site_ngr, site_assets in assets_by_site.items():
                if site_ngr == 'small_cell_sites':
                    continue
                if 'LTE' not in [asset['technology'] for asset in site_assets]:
                    # set both assets to this site_ngr
                    for option in build_option:
                        to_build = copy.copy(option)
                        to_build['site_ngr'] = site_ngr
                        to_build['pcd_sector'] = area.id
                        to_build['build_date'] = timestep
                        area_interventions.append(to_build)
                        built_interventions.append(to_build)

                    budget -= cost
                    spend.append((area.id, area.lad_id, 'upgrade_to_lte', cost))
                    if budget < 0:
                        break

        if budget < 0:
            break

        # integrate_700
        if 'carrier_700' in available_interventions and timestep >= 2020:
            if _area_satisfied(area, area_interventions, threshold):
                continue

            build_option = INTERVENTIONS['carrier_700']['assets_to_build']
            cost = INTERVENTIONS['carrier_700']['cost']
            for site_ngr, site_assets in assets_by_site.items():
                if site_ngr == 'small_cell_sites':
                    continue
                if 'LTE' in [asset['technology'] for asset in site_assets] and \
                        '700' not in [asset['frequency'] for asset in site_assets]:
                    # set both assets to this site_ngr
                    for option in build_option:
                        to_build = copy.copy(option)
                        to_build['site_ngr'] = site_ngr
                        to_build['pcd_sector'] = area.id
                        to_build['build_date'] = timestep
                        area_interventions.append(to_build)
                        built_interventions.append(to_build)

                    spend.append((area.id, area.lad_id, 'carrier_700', cost))
                    budget -= cost
                    if budget < 0:
                        break

        if budget < 0:
            break

        # integrate_3.5
        if 'carrier_3500' in available_interventions and timestep >= 2020:
            if _area_satisfied(area, area_interventions, threshold):
                continue

            build_option = INTERVENTIONS['carrier_3500']['assets_to_build']
            cost = INTERVENTIONS['carrier_3500']['cost']
            for site_ngr, site_assets in assets_by_site.items():
                if site_ngr == 'small_cell_sites':
                    continue
                if 'LTE' in [asset['technology'] for asset in site_assets] and \
                        '3500' not in [asset['frequency'] for asset in site_assets]:
                    # set both assets to this site_ngr
                    for option in build_option:
                        to_build = copy.copy(option)
                        to_build['site_ngr'] = site_ngr
                        to_build['pcd_sector'] = area.id
                        to_build['build_date'] = timestep
                        area_interventions.append(to_build)
                        built_interventions.append(to_build)

                    spend.append((area.id, area.lad_id, 'carrier_3500', cost))
                    budget -= cost
                    if budget < 0:
                        break

        if budget < 0:
            break

        # build small cells to next density
        if 'small_cell' in available_interventions and timestep >= 2020:
            if _area_satisfied(area, area_interventions, threshold):
                continue

            area_sq_km = area.area
            if 'small_cell_sites' in assets_by_site:
                current_number = len(assets_by_site['small_cell_sites'])
            else:
                current_number = 0
            current_density = current_number / area_sq_km
            build_option = INTERVENTIONS['small_cell']['assets_to_build']
            cost = INTERVENTIONS['small_cell']['cost']

            while True:
                to_build = copy.deepcopy(build_option)
                to_build[0]['build_date'] = timestep
                to_build[0]['pcd_sector'] = area.id

                area_interventions += to_build
                built_interventions += to_build
                spend.append((area.id, area.lad_id, 'small_cells', cost))
                budget -= cost

                if budget < 0 or _area_satisfied(area, area_interventions, threshold):
                    break

    return built_interventions, budget, spend

def _suggest_target_postcodes(system, threshold=None):
    """Sort postcodes by population density (descending)
    - if considering threshold, filter out any with capacity above threshold
    """
    postcodes = system.postcode_sectors.values()
    total_postcodes = len(postcodes)
    if threshold is not None:
        considered_postcodes = [pcd for pcd in postcodes if pcd.capacity < threshold]
    else:
        considered_postcodes = [p for p in postcodes]
    # print("Considering {} of {} postcodes".format(len(considered_postcodes), total_postcodes))
    return sorted(considered_postcodes, key=lambda pcd: -pcd.population_density)

def _area_satisfied(area, built_interventions, threshold):
    if threshold is None:
        target_capacity = area.demand
    else:
        target_capacity = threshold

    data = {
        "id": area.id,
        "lad_id": area.lad_id,
        "population": area.population,
        "area": area.area,
        "user_throughput": area.user_throughput,
    }
    assets = area.assets + built_interventions

    test_area = PostcodeSector(
        data,
        assets,
        area._capacity_lookup_table,
        area._clutter_lookup
    )

    reached_capacity = test_area.capacity

    return reached_capacity >= target_capacity
