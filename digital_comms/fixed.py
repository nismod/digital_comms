"""Given a capital constraint, allocate budget to infrastructure upgrades

"""
import pandas as pd
import numpy as np
import os

def tech_roll_out():

    available_budget_each_year = [
        1500000000,
        1500000000,
        1500000000,
        1500000000,
        1500000000,
        1500000000,
        1500000000,
    ]

    exchanges = r'../data/exchanges.csv'
    exchanges = pd.read_csv(exchanges, low_memory=False)

    #sort exchanges based on geotype and then premises numbers
    exchanges = exchanges.sort_values(by=['geotype_number','all_premises'], ascending=[True,False])
    ###############################################################################
    ###### SET UP COPY FOR GFAST COSTINGS ######
    ex_Gfast = exchanges.copy(deep=True)

    # set cost per premises for G.fast
    ex_Gfast.loc[ (ex_Gfast['geotype_number'] == 1), 'prem_cost'] = 200
    ex_Gfast.loc[ (ex_Gfast['geotype_number'] == 2), 'prem_cost'] = 300
    ex_Gfast.loc[ (ex_Gfast['geotype_number'] == 3), 'prem_cost'] = 400
    ex_Gfast.loc[ (ex_Gfast['geotype_number'] == 4), 'prem_cost'] = 500
    ex_Gfast.loc[ (ex_Gfast['geotype_number'] == 5), 'prem_cost'] = 600
    ex_Gfast.loc[ (ex_Gfast['geotype_number'] == 6), 'prem_cost'] = 700
    ex_Gfast.loc[ (ex_Gfast['geotype_number'] == 7), 'prem_cost'] = 800
    ex_Gfast.loc[ (ex_Gfast['geotype_number'] == 8), 'prem_cost'] = 900
    ex_Gfast.loc[ (ex_Gfast['geotype_number'] == 9), 'prem_cost'] = 1000
    ex_Gfast.loc[ (ex_Gfast['geotype_number'] == 10), 'prem_cost'] = 1100
    ex_Gfast.loc[ (ex_Gfast['geotype_number'] == 11), 'prem_cost'] = 1200
    ex_Gfast.loc[ (ex_Gfast['geotype_number'] == 12), 'prem_cost'] = 1300
    ex_Gfast.loc[ (ex_Gfast['geotype_number'] == 13), 'prem_cost'] = 1400

    ex_Gfast['cost'] = ex_Gfast.prem_cost*ex_Gfast.all_premises             

    ex_Gfast['Rank'] = ex_Gfast.groupby(['geotype_number'])['all_premises'].rank(ascending=False)

    # set up zero total amounts budgeted (to be calculated)
    ex_Gfast["total_budgeted"] = np.zeros(len(ex_Gfast))

    # set up NaN year completed (to be filled in)
    nans = np.empty(len(ex_Gfast))
    nans[:] = np.NaN
    ex_Gfast["year_completed"] = nans


    # for each year and budget amount
    for year, budget in enumerate(available_budget_each_year):
        # set up a budget column for this year
        budget_colname = "budget_y{}".format(year)
        ex_Gfast[budget_colname] = np.zeros(len(ex_Gfast))

        # for each row (each exchange),
        # (!) assuming they are in ranked order
        for row in ex_Gfast.itertuples():
            # calculate outstanding cost
            outstanding_cost = row.cost - row.total_budgeted
            # if any,
            if outstanding_cost > 0:
                # if there is sufficient budget
                if budget >= outstanding_cost:
                    # assign the total outstanding cost to the amount budgeted for
                    # this exchange in this year
                    ex_Gfast.set_value(row.Index, budget_colname, outstanding_cost)
                    # add that amount to the total amount budgeted for this exchange
                    ex_Gfast.set_value(row.Index, "total_budgeted", outstanding_cost + row.total_budgeted)
                    # set the year this exchange completed to this year
                    ex_Gfast.set_value(row.Index, "year_completed", year)
                    # decrement the remaing budget available this year
                    budget -= outstanding_cost

                # if there is not enough budget
                else:
                    # assign all remaining budget to this exchange
                    ex_Gfast.set_value(row.Index, budget_colname, budget)
                    # add that amount to the total amount budgeted for this exchange
                    ex_Gfast.set_value(row.Index, "total_budgeted", budget + row.total_budgeted)
                    # set remaining budget for this year to zero
                    budget = 0

        # spare budget?
        if budget > 0:
            print("{} budget unspent in year {}".format(budget, year)) 

    ex_Gfast.loc[:,'year_completed'] += 2017     
        
    ###############################################################################
    ###### SET UP COPY FOR COSTINGS ######
    ex_FTTdp = exchanges.copy(deep=True)

    # DON'T PUT NUMBERS IN '' AS IT MAKES THEM STRINGS!
    ex_FTTdp.loc[ (ex_FTTdp['geotype_number'] == 1), 'prem_cost'] = 400
    ex_FTTdp.loc[ (ex_FTTdp['geotype_number'] == 2), 'prem_cost'] = 441
    ex_FTTdp.loc[ (ex_FTTdp['geotype_number'] == 3), 'prem_cost'] = 432
    ex_FTTdp.loc[ (ex_FTTdp['geotype_number'] == 4), 'prem_cost'] = 401
    ex_FTTdp.loc[ (ex_FTTdp['geotype_number'] == 5), 'prem_cost'] = 710
    ex_FTTdp.loc[ (ex_FTTdp['geotype_number'] == 6), 'prem_cost'] = 377
    ex_FTTdp.loc[ (ex_FTTdp['geotype_number'] == 7), 'prem_cost'] = 538
    ex_FTTdp.loc[ (ex_FTTdp['geotype_number'] == 8), 'prem_cost'] = 463
    ex_FTTdp.loc[ (ex_FTTdp['geotype_number'] == 9), 'prem_cost'] = 1078
    ex_FTTdp.loc[ (ex_FTTdp['geotype_number'] == 10), 'prem_cost'] = 407
    ex_FTTdp.loc[ (ex_FTTdp['geotype_number'] == 11), 'prem_cost'] = 689
    ex_FTTdp.loc[ (ex_FTTdp['geotype_number'] == 12), 'prem_cost'] = 1200
    ex_FTTdp.loc[ (ex_FTTdp['geotype_number'] == 13), 'prem_cost'] = 3500     

    ex_FTTdp['cost'] = ex_FTTdp.prem_cost*ex_FTTdp.all_premises             

    ex_FTTdp['Rank'] = ex_FTTdp.groupby(['geotype_number'])['all_premises'].rank(ascending=False)
    
    # set up zero total amounts budgeted (to be calculated)
    ex_FTTdp["total_budgeted"] = np.zeros(len(ex_FTTdp))

    # set up NaN year completed (to be filled in)
    nans = np.empty(len(ex_FTTdp))
    nans[:] = np.NaN
    ex_FTTdp["year_completed"] = nans

    # for each year and budget amount
    for year, budget in enumerate(available_budget_each_year):
        # set up a budget column for this year
        budget_colname = "budget_y{}".format(year)
        ex_FTTdp[budget_colname] = np.zeros(len(ex_FTTdp))

        # for each row (each exchange),
        # (!) assuming they are in ranked order
        for row in ex_FTTdp.itertuples():
            # calculate outstanding cost
            outstanding_cost = row.cost - row.total_budgeted
            # if any,
            if outstanding_cost > 0:
                # if there is sufficient budget
                if budget >= outstanding_cost:
                    # assign the total outstanding cost to the amount budgeted for
                    # this exchange in this year
                    ex_FTTdp.set_value(row.Index, budget_colname, outstanding_cost)
                    # add that amount to the total amount budgeted for this exchange
                    ex_FTTdp.set_value(row.Index, "total_budgeted", outstanding_cost + row.total_budgeted)
                    # set the year this exchange completed to this year
                    ex_FTTdp.set_value(row.Index, "year_completed", year)
                    # decrement the remaing budget available this year
                    budget -= outstanding_cost

                # if there is not enough budget
                else:
                    # assign all remaining budget to this exchange
                    ex_FTTdp.set_value(row.Index, budget_colname, budget)
                    # add that amount to the total amount budgeted for this exchange
                    ex_FTTdp.set_value(row.Index, "total_budgeted", budget + row.total_budgeted)
                    # set remaining budget for this year to zero
                    budget = 0

        # spare budget?
        if budget > 0:
            print("{} budget unspent in year {}".format(budget, year)) 

    ex_FTTdp.loc[:,'year_completed'] += 2017     

    ###############################################################################
    ###### SET UP COPY FOR COSTINGS ######
    ex_FTTH = exchanges.copy(deep=True)
                
    # DON'T PUT NUMBERS IN '' AS IT MAKES THEM STRINGS!
    ex_FTTH.loc[ (ex_FTTH['geotype_number'] == 1), 'prem_cost'] = 1300
    ex_FTTH.loc[ (ex_FTTH['geotype_number'] == 2), 'prem_cost'] = 1800
    ex_FTTH.loc[ (ex_FTTH['geotype_number'] == 3), 'prem_cost'] = 2000
    ex_FTTH.loc[ (ex_FTTH['geotype_number'] == 4), 'prem_cost'] = 1700
    ex_FTTH.loc[ (ex_FTTH['geotype_number'] == 5), 'prem_cost'] = 3300
    ex_FTTH.loc[ (ex_FTTH['geotype_number'] == 6), 'prem_cost'] = 1900
    ex_FTTH.loc[ (ex_FTTH['geotype_number'] == 7), 'prem_cost'] = 4300
    ex_FTTH.loc[ (ex_FTTH['geotype_number'] == 8), 'prem_cost'] = 1500
    ex_FTTH.loc[ (ex_FTTH['geotype_number'] == 9), 'prem_cost'] = 4000
    ex_FTTH.loc[ (ex_FTTH['geotype_number'] == 10), 'prem_cost'] = 2200
    ex_FTTH.loc[ (ex_FTTH['geotype_number'] == 11), 'prem_cost'] = 6700
    ex_FTTH.loc[ (ex_FTTH['geotype_number'] == 12), 'prem_cost'] = 9000
    ex_FTTH.loc[ (ex_FTTH['geotype_number'] == 13), 'prem_cost'] = 12000
            
    ex_FTTH['cost'] = ex_FTTH.prem_cost*ex_FTTH.all_premises                 

    ex_FTTH['Rank'] = ex_FTTH.groupby(['geotype_number'])['all_premises'].rank(ascending=False)

    # set up zero total amounts budgeted (to be calculated)
    ex_FTTH["total_budgeted"] = np.zeros(len(ex_FTTH))

    # set up NaN year completed (to be filled in)
    nans = np.empty(len(ex_FTTH))
    nans[:] = np.NaN
    ex_FTTH["year_completed"] = nans

    # for each year and budget amount
    for year, budget in enumerate(available_budget_each_year):
        # set up a budget column for this year
        budget_colname = "budget_y{}".format(year)
        ex_FTTH[budget_colname] = np.zeros(len(ex_FTTH))

        # for each row (each exchange),
        # (!) assuming they are in ranked order
        for row in ex_FTTH.itertuples():
            # calculate outstanding cost
            outstanding_cost = row.cost - row.total_budgeted
            # if any,
            if outstanding_cost > 0:
                # if there is sufficient budget
                if budget >= outstanding_cost:
                    # assign the total outstanding cost to the amount budgeted for
                    # this exchange in this year
                    ex_FTTH.set_value(row.Index, budget_colname, outstanding_cost)
                    # add that amount to the total amount budgeted for this exchange
                    ex_FTTH.set_value(row.Index, "total_budgeted", outstanding_cost + row.total_budgeted)
                    # set the year this exchange completed to this year
                    ex_FTTH.set_value(row.Index, "year_completed", year)
                    # decrement the remaing budget available this year
                    budget -= outstanding_cost

                # if there is not enough budget
                else:
                    # assign all remaining budget to this exchange
                    ex_FTTH.set_value(row.Index, budget_colname, budget)
                    # add that amount to the total amount budgeted for this exchange
                    ex_FTTH.set_value(row.Index, "total_budgeted", budget + row.total_budgeted)
                    # set remaining budget for this year to zero
                    budget = 0

        # spare budget?
        if budget > 0:
            print("{} budget unspent in year {}".format(budget, year))       
    
    ex_FTTH.loc[:,'year_completed'] += 2017        
            
    del budget
    del budget_colname
    del nans
    del outstanding_cost
    del row
    del year
    del available_budget_each_year   

    return {'ex_Gfast': ex_Gfast,
            'ex_FTTdp': ex_FTTdp,
            'ex_FTTH': ex_FTTH}

def write_results_to_csv(dataframe, path, name):
    """
    """
    dataframe.to_csv(path, name)

def run_simulation():

    results = tech_roll_out()

    results['total_cost'] = 0
    results['average_speed'] = 0
    results['premises_passed'] = 0
    results['energy_demand'] = 0

    return results

if __name__ == '__main__':

    results = tech_roll_out()
    path=r'../outputs'
    results['ex_Gfast'].to_csv(os.path.join(path,r'ex_Gfast.csv'))
    results['ex_FTTdp'].to_csv(os.path.join(path,r'ex_FTTdp.csv'))
    results['ex_FTTH'].to_csv(os.path.join(path,r'ex_FTTH.csv'))