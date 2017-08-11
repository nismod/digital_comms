"""Decide on interventions
"""
# pylint: disable=C0103
from digital_comms.ccam import Asset, PostcodeSector

import copy
import math

################################################################
# EXAMPLE COST LOOKUP TABLE
# - TODO come back to net present value or total cost of ownership for costs
################################################################
COST_STRUCTURE = {
    'lte_present': [
        {'new_carrier': 1500}
    ],
    'no_lte': [
        {'multi_bs': 40900, 'civils': 18000}
    ],
    'small_cells': [
        {'small_cell': 2500, 'civils': 13300}
    ],
    'core_upgrade': [
        {'core_upgrade': 1.1}
    ]
}

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
        'cost': 111451,
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

    # Intervention Strategy 3
    # Deploy a small cell layer at 3700 MHz
    # The cost will include the small cell unit and the civil works per cell
    'small_cell': ('upgrade_to_lte', 'carrier_700',
                   'carrier_3500', 'small_cell'),
}


def decide_interventions(strategy, budget, service_obligation_capacity,
                         system, timestep):
    """Given strategy parameters and a system return some next best intervention

    Params
    ======
    strategy : str
        One of 'minimal', 'macrocell', 'small_cell' intervention strategies
    budget : int
        Annual budget in GBP
    service_obligation_capacity : float
        Threshold for universal mobile service, in Mbps/km^2
    system : ICTManager
        Gives areas (postcode sectors) with population density, demand
    """
    available_interventions = AVAILABLE_STRATEGY_INTERVENTIONS[strategy]

    obligation = []
    if budget > 0:
        # Build to meet service obligation (up to threshold,
        # set to zero to disable)
        obligation, budget, obligation_spend = meet_service_obligation(
            budget, available_interventions, timestep,
            service_obligation_capacity, system)
    print("obligation", len(obligation))

    demand = []
    if budget > 0:
        # Build to meet demand
        demand, budget, demand_spend = meet_demand(
            budget, available_interventions, timestep, system)
    print("demand", len(demand))

    built = obligation + demand
    spend = obligation_spend + demand_spend
    return built, budget, spend


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
        if _area_satisfied(area, built_interventions, threshold):
            continue

        # group assets by site
        assets_by_site = {}
        for asset in area.assets:
            if asset.site_ngr not in assets_by_site:
                assets_by_site[asset.site_ngr] = [asset]
            else:
                assets_by_site[asset.site_ngr].append(asset)

        # integrate_800 and integrate_2.6
        if 'upgrade_to_lte' in available_interventions:
            build_option = copy.deepcopy(INTERVENTIONS['upgrade_to_lte']['assets_to_build'])
            cost = INTERVENTIONS['upgrade_to_lte']['cost']
            for site_ngr, site_assets in assets_by_site.items():
                if site_ngr == 'small_cell_sites':
                    continue
                if 'LTE' not in [asset.technology for asset in site_assets]:
                    # set both assets to this site_ngr
                    to_build = copy.deepcopy(build_option)
                    to_build[0]['site_ngr'] = site_ngr
                    to_build[0]['pcd_sector'] = area.id
                    to_build[0]['build_date'] = timestep
                    to_build[1]['site_ngr'] = site_ngr
                    to_build[1]['pcd_sector'] = area.id
                    to_build[1]['build_date'] = timestep

                    built_interventions += to_build
                    budget -= cost
                    spend.append((area.id, area.lad_id, 'upgrade_to_lte', cost))
                    if budget < 0:
                        break

        if budget < 0:
            break

        if _area_satisfied(area, built_interventions, threshold):
            continue

        # integrate_700
        if 'carrier_700' in available_interventions:
            build_option = INTERVENTIONS['carrier_700']['assets_to_build']
            cost = INTERVENTIONS['carrier_700']['cost']
            for site_ngr, site_assets in assets_by_site.items():
                if site_ngr == 'small_cell_sites':
                    continue
                if 'LTE' in [asset.technology for asset in site_assets] and \
                        '700' not in [asset.frequency for asset in site_assets]:
                    # set both assets to this site_ngr
                    to_build = copy.deepcopy(build_option)
                    to_build[0]['site_ngr'] = site_ngr
                    to_build[0]['pcd_sector'] = area.id
                    to_build[0]['build_date'] = timestep

                    built_interventions += to_build
                    spend.append((area.id, area.lad_id, 'carrier_700', cost))
                    budget -= cost
                    if budget < 0:
                        break

        if budget < 0:
            break

        if _area_satisfied(area, built_interventions, threshold):
            continue

        # integrate_3.5
        if 'carrier_3500' in available_interventions:
            build_option = INTERVENTIONS['carrier_3500']['assets_to_build']
            cost = INTERVENTIONS['carrier_3500']['cost']
            for site_ngr, site_assets in assets_by_site.items():
                if site_ngr == 'small_cell_sites':
                    continue
                if 'LTE' in [asset.technology for asset in site_assets] and \
                        '3500' not in [asset.frequency for asset in site_assets]:
                    # set both assets to this site_ngr
                    to_build = copy.deepcopy(build_option)
                    to_build[0]['site_ngr'] = site_ngr
                    to_build[0]['pcd_sector'] = area.id
                    to_build[0]['build_date'] = timestep

                    built_interventions += to_build
                    spend.append((area.id, area.lad_id, 'carrier_3500', cost))
                    budget -= cost
                    if budget < 0:
                        break

        if budget < 0:
            break

        if _area_satisfied(area, built_interventions, threshold):
            continue

        # build small cells to next density
        if 'small_cell' in available_interventions:
            while True:
                area_sq_km = area.area
                if 'small_cell_sites' in assets_by_site:
                    current_number = len(assets_by_site['small_cell_sites'])
                else:
                    current_number = 0
                current_density = current_number / area_sq_km
                build_option = INTERVENTIONS['small_cell']['assets_to_build']
                cost = INTERVENTIONS['small_cell']['cost']

                target_densities = [
                    3.98,
                    7.07,
                    10.19,
                    17.63,
                    22.03,
                    28.29,
                    37.67,
                    52.61,
                    78.6,
                    129.92,
                    254.65,
                ]
                target_density = next_larger_value(current_density, target_densities)

                if target_density > current_density:
                    target_number = math.ceil(area_sq_km * target_density)
                    aim_to_build_number = target_number - current_number
                    budgetable_number = math.floor(budget / cost)
                    number_to_build = min(aim_to_build_number, budgetable_number)

                    if number_to_build <= 0:
                        break

                    to_build = copy.deepcopy(build_option)
                    to_build[0]['build_date'] = timestep
                    to_build[0]['pcd_sector'] = area.id
                    to_build = to_build * number_to_build

                    built_interventions += to_build
                    spend.append((area.id, area.lad_id, 'small_cells', number_to_build * cost))
                    budget -= number_to_build * cost

                    if budget <= 0 or _area_satisfied(area, built_interventions, threshold):
                        break
                else:
                    break

    return built_interventions, budget, spend

def next_larger_value(x, vals):
    for val in vals:
        if val > x:
            return val
    else:
        return vals[-1]


def _suggest_target_postcodes(system, threshold=None):
    """Sort postcodes by population density (descending)
    - if considering threshold, filter out any with capacity above threshold
    """
    postcodes = system.postcode_sectors
    total_postcodes = len(postcodes)
    if threshold is not None:
        considered_postcodes = [pcd for pcd in postcodes if pcd.capacity < threshold]
    else:
        considered_postcodes = postcodes[:]
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
    test_area = PostcodeSector(
        data,
        area._capacity_lookup_table,
        area._clutter_lookup
    )
    for asset in area.assets:
        test_area.add_asset(asset)

    for intervention in built_interventions:
        asset = Asset(intervention)
        test_area.add_asset(asset)
    reached_capacity = test_area.capacity

    return reached_capacity >= target_capacity
