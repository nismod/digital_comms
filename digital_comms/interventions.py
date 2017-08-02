"""Decide on interventions
"""
# pylint: disable=C0103

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
    'carrier_1500': {
        'name': 'Build 1500 MHz carrier',
        'description': 'Available if a site has LTE',
        'result': '1500 band available',
        'cost': (1500 * 1.1),
        'assets_to_build': [
            {
                # site_ngr to match upgraded
                'site_ngr': None,
                'frequency': '1500',
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
                'site_ngr': None,
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
    ### Intervention Strategy 1 ###
    ### Minimal Intervention ### 'Do Nothing Scenario'
    ### Build no more additional sites -> will lead to a capacity margin deficit
    ### The cost will be the replacement of existing units annually based on the decommissioning rate of 10%
    ### Capacity will be the sum of 800 and 2600 MHz
    'minimal': ('lte_replacement'),

    ### Intervention Strategy 2 ###
    ### Integrate 700 and 3500 MHz on to the macrocellular layer
    ### The cost will be the addtion of another carrier on each basestation ~£15k (providing thre is 4G already)
    ### If 4G isn't present, the site will need major upgrades.
    'macrocell': ('upgrade_to_lte', 'lte_replacement', 'carrier_700', 'carrier_1500'),

    ### Intervention Strategy 3 ###
    ### Deploy a small cell layer at 3700 MHz
    ### The cost will include the small cell unit and the civil works per cell
    'small_cell': ('upgrade_to_lte', 'lte_replacement', 'carrier_700', 'carrier_1500', 'small_cell'),
}

def decide_interventions(strategy, budget, service_obligation_capacity, decommissioned, system):
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
    replace, budget = replace_decommissioned(budget, decommissioned)
    # Build to meet service obligation (up to threshold, set to zero to disable)
    obligation, budget = meet_service_obligation(budget, available_interventions, service_obligation_capacity, system)
    # Build to meet demand
    demand, budget = meet_demand(budget, available_interventions, system)

    built = replace + obligation + demand

    return built, budget

def replace_decommissioned(budget, decommissioned):
    assets_replaced = []
    for asset in decommissioned:
        pass
    return assets_replaced, budget

def meet_service_obligation(budget, available_interventions, service_obligation_capacity, system):
    interventions_built = []
    for area in system.postcode_sectors:
        built, budget = meet_area_capacity(budget, available_interventions, area.assets, service_obligation_capacity)
        interventions_built += built

    return interventions_built, budget

def meet_demand(budget, available_interventions, system):
    interventions_built = []
    for area in system.postcode_sectors:
        built, budget = meet_area_capacity(budget, available_interventions, area.assets, area.demand)
        interventions_built += built

    return interventions_built, budget

def meet_area_capacity(budget, available_interventions, existing_assets, capacity_threshold):
    # while capacity is not met:
    #    integrate_800 and integrate_2.6
    #    integrate_700
    #    integrate_3.5
    #    build small cells to next density
    #    fail
    return [], budget

