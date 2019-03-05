"""Generate model runs
"""
import os

def main():
    base_path = os.path.join(
        os.path.dirname(__file__),
        '..',
        'config',
        'sos_model_runs'
    )
    template = """\

decision_module: ''
description: ''
name: {name}
narratives:
  technology_strategy:
  - {strategy}
scenarios:
  adoption: {scenario}
sos_model: digital_comms_only
stamp: '2018-05-01T12:36:34.374Z'
strategies: []
timesteps:
- 2019
- 2020
# - 2021
# - 2022
# - 2023
# - 2024
# - 2025
# - 2026
# - 2027
# - 2028
# - 2029
# - 2030
"""

    # scenarios = [
    #     ('base', 'baseline_adoption'),
    #     ('high', 'high_adoption'),
    #     ('low', 'low_adoption'),
    # ]
    
    # strategies = [
    #     ('fttp_s1', 'fttp_s1_market_based_roll_out'),    
    #     ('fttp_s2', 'fttp_s2_rural_based_subsidy'),   
    #     ('fttp_s3', 'fttp_s3_outside_in_subsidy'),    
    #     ('fttdp_s1', 'fttdp_s1_market_based_roll_out'), 
    #     ('fttdp_s2', 'fttdp_s2_rural_based_subsidy'), 
    #     ('fttdp_s3', 'fttdp_s3_outside_in_subsidy'),   
    # ]

    strategies = [
        ('fttp_s1', 'fttp_s1_market_based_roll_out'),
        ('fttp_s2', 'fttp_s2_rural_based_subsidy'),
        ('fttp_s3', 'fttp_s3_outside_in_subsidy'),   
    ]
    
    scenarios = [
        ('base', 'baseline_adoption'),
    ]

    batchfile = open(os.path.join(base_path, 'batchfile'), 'w')

    for scenario_abbr, scenario in scenarios:
        for strategy_abbr, strategy in strategies:
            name = "digital_comms_{}_{}".format(scenario_abbr, strategy_abbr)
            fname = os.path.join(base_path, name + ".yml")
            technology = strategy_abbr[:-2] 
            with open(fname, 'w') as fh:
                fh.write(
                    template.format(strategy=strategy, scenario=scenario, name=name, technology=technology)
                )
            batchfile.write(name + "\n")

    batchfile.close()

if __name__ == '__main__':
    main()
