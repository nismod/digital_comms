"""Decide on interventions
"""
# pylint: disable=C0103
import copy

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
        'cost': ((40900 + 18000) * 1.1),
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
    'lte_replacement': {
        'name': 'Replace LTE site',
        'description': 'Available if a site has had LTE decommissioned',
        'result': '800 and 2600 bands available',
        'cost': (1500 * 1.1),
        'assets_to_build': [
            {
                # site_ngr to match replaced
                'site_ngr': None,
                'frequency': '800',
                'technology': 'LTE',
                'type': 'macrocell_site',
                'bandwidth': '2x10MHz',
                # set build date when deciding
                'build_date': None,
            },
            {
                # site_ngr to match replaced
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
        'cost': (1500 * 1.1),
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
        'cost': (1500 * 1.1),
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
        'cost': ((2500 + 13300) * 1.1),
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
    'minimal': ('lte_replacement'),

    # Intervention Strategy 2
    # Integrate 700 and 3500 MHz on to the macrocellular layer
    # The cost will be the addtion of another carrier on each basestation ~£15k
    # (providing thre is 4G already)
    # If 4G isn't present, the site will need major upgrades.
    'macrocell': ('upgrade_to_lte', 'lte_replacement', 'carrier_700',
                  'carrier_3500'),

    # Intervention Strategy 3
    # Deploy a small cell layer at 3700 MHz
    # The cost will include the small cell unit and the civil works per cell
    'small_cell': ('upgrade_to_lte', 'lte_replacement', 'carrier_700',
                   'carrier_3500', 'small_cell'),
}


def decide_interventions(strategy, budget, service_obligation_capacity,
                         decommissioned, system, timestep):
    """Given strategy parameters and a system return some next best intervention

    Params
    ======
    strategy : str
        One of 'minimal', 'macrocell', 'small_cell' intervention strategies
    budget : int
        Annual budget in GBP
    service_obligation_capacity : float
        Threshold for universal mobile service, in Mbps/km^2
    decommissioned : list of dict
        Assets decommissioned at the beginning of this timestep (no longer available)
    system : ICTManager
        Gives areas (postcode sectors) with population density, demand
    """
    available_interventions = AVAILABLE_STRATEGY_INTERVENTIONS[strategy]

    # Replace decommissioned
    replace, budget = replace_decommissioned(
        budget, decommissioned, available_interventions, timestep)

    obligation = []
    if not replace and budget > 0:
        # Build to meet service obligation (up to threshold,
        # set to zero to disable)
        obligation, budget = meet_service_obligation(
            budget, available_interventions, timestep, service_obligation_capacity, system)

    demand = []
    if not replace and not obligation and budget > 0:
        # Build to meet demand
        demand, budget = meet_demand(budget, available_interventions, timestep, system)

    built = replace + obligation + demand
    print("replaced", len(replace))
    print("obligation", len(obligation))
    print("demand", len(demand))
    return built, budget


def replace_decommissioned(budget, decommissioned, available_interventions, timestep):
    assets_replaced = []
    for asset in decommissioned:
        if asset['type'] == 'macrocell_site' and asset['technology'] == 'LTE':
            if 'lte_replacement' in available_interventions:
                asset['build_date'] = timestep
                assets_replaced.append(asset)
                budget -= INTERVENTIONS['lte_replacement']['cost']
        elif asset['type'] == 'small_cell':
            if 'small_cell' in available_interventions:
                asset['build_date'] = timestep
                assets_replaced.append(asset)
                budget -= INTERVENTIONS['small_cell']['cost']
        else:
            # not replacing non-LTE
            pass

        if budget < 0:
            break
    return assets_replaced, budget


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
    for area in areas:
        print(area.id, area.population_density)
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
                    if budget < 0:
                        break

        if budget < 0:
            break

        # integrate_700
        if 'carrier_700' in available_interventions:
            build_option = INTERVENTIONS['carrier_700']['assets_to_build']
            cost = INTERVENTIONS['carrier_700']['cost']
            for site_ngr, site_assets in assets_by_site.items():
                if 'LTE' in [asset.technology for asset in site_assets] and \
                        '700' not in [asset.frequency for asset in site_assets]:
                    # set both assets to this site_ngr
                    to_build = copy.deepcopy(build_option)
                    to_build[0]['site_ngr'] = site_ngr
                    to_build[0]['pcd_sector'] = area.id
                    to_build[0]['build_date'] = timestep

                    built_interventions += to_build
                    budget -= cost
                    if budget < 0:
                        break

        if budget < 0:
            break

        # integrate_3.5
        if 'carrier_3500' in available_interventions:
            build_option = INTERVENTIONS['carrier_3500']['assets_to_build']
            cost = INTERVENTIONS['carrier_3500']['cost']
            for site_ngr, site_assets in assets_by_site.items():
                if 'LTE' in [asset.technology for asset in site_assets] and \
                        '3500' not in [asset.frequency for asset in site_assets]:
                    # set both assets to this site_ngr
                    to_build = copy.deepcopy(build_option)
                    to_build[0]['site_ngr'] = site_ngr
                    to_build[0]['pcd_sector'] = area.id
                    to_build[0]['build_date'] = timestep

                    built_interventions += to_build
                    budget -= cost
                    if budget < 0:
                        break

        if budget < 0:
            break

        # build small cells to next density
        if 'small_cell' in available_interventions:
            pass

    for intervention in built_interventions:
        print(intervention)
    return built_interventions, budget


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
    print("Considering {} of {} postcodes".format(len(considered_postcodes), total_postcodes))
    return sorted(considered_postcodes, key=lambda pcd: -pcd.population_density)
