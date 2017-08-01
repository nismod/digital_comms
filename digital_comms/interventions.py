"""Decide on interventions
"""
# pylint: disable=C0103

################################################################
# EXAMPLE COST LOOKUP TABLE
# - TODO come back to net present value or total cost of ownership for costs
################################################################
costs = {
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
[
    {
        'name': 'Upgrade site to LTE',
        'description': 'If a site has only 2G/3G',
        'result': '800 and 2600 bands available',
        'cost': ((40900 + 18000) * 1.1),
    },
    {
        'name': 'Replace LTE site',
        'description': 'Available if a site has had LTE decommissioned',
        'result': '800 and 2600 bands available',
        'cost': (1500 * 1.1),
    },
    {
        'name': 'Build 700 MHz carrier',
        'description': 'Available if a site has LTE',
        'result': '700 band available',
        'cost': (1500 * 1.1),
    },
    {
        'name': 'Build 1500 MHz carrier',
        'description': 'Available if a site has LTE',
        'result': '1500 band available',
        'cost': (1500 * 1.1),
    },
    {
        'name': 'Build a small cell',
        'description': 'Must be deployed at preset densities to be modelled',
        'result': '2x25 MHz small cells available at given density',
        'cost': ((2500 + 13300) * 1.1),
    },
]

################################################################
# EXAMPLE UPGRADE PATH FOR INVESTMENT DECISIONS
################################################################

### Intervention 1 ###
### Minimal Intervention ### 'Do Nothing Scenario'
### Build no more additional sites - > will lead to a capacity margin deficit
### The cost will be the replacement of existing units annually based on the decommissioning rate of 10%
### Capacity will be the sum of 800 and 2600 MHz



### Intervention 2 ###
### Integrate 700 and 3500 MHz on to the macrocellular layer
### The cost will be the addtion of another carrier on each basestation ~£15k (providing thre is 4G already)
### If 4G isn't present, the site will need major upgrades.



### Intervention 3 ###
### Deploy a small cell layer at 3700 MHz
### The cost will include the small cell unit and the civil works per cell


# coverage = area_coverage_2016
# if coverage > 0:
#     cost = lte_present * sitengr_count
# else:
#     cost = no_lte * sitengr_count

# while capacity is not met:
#    integrate_800 and integrate_2.6
#    integrate_700
#    integrate_3.5
#    build small cells to next density
#    fail

