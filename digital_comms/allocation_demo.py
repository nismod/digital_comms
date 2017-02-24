# -*- coding: utf-8 -*-
"""
Created on Thu Jan 26 21:38:58 2017

@author: EJO31
"""

from __future__ import print_function
import numpy as np
import pandas as pd

# given some data
raw_data = [('a', 0.4, 1),
    ('a', 0.4, 2),
    ('a', 0.4, 3),
    ('b', 1.3, 1),
    ('b', 1.3, 2),
    ('c', 1.3, 3),
    ('d', 3.7, 1),
    ('d', 3.7, 2)]

# set up DataFrame with columns
data = np.zeros((len(raw_data),), dtype=[
    # notes on dtypes: https://docs.scipy.org/doc/numpy/reference/arrays.dtypes.html
    ("exchange", 'a4'),
    ("cost", 'f8'),
    ("rank", 'i8')
])

# assign data to the DataFrame
data[:] = raw_data
df = pd.DataFrame(data)

# set up zero total amounts budgeted (to be calculated)
df["total_budgeted"] = np.zeros(len(raw_data))

# set up NaN year completed (to be filled in)
nans = np.empty(len(raw_data))
nans[:] = np.NaN
df["year_completed"] = nans

# print for sanity check
print(df)



# given a set of yearly budgets
available_budget_each_year = [
    1.5,
    1.5,
    1.5,
    1.5]

# for each year and budget amount
for year, budget in enumerate(available_budget_each_year):
    # set up a budget column for this year
    budget_colname = "budget_y{}".format(year)
    df[budget_colname] = np.zeros(len(raw_data))

    # for each row (each exchange),
    # (!) assuming they are in ranked order
    for row in df.itertuples():
        # calculate outstanding cost
        outstanding_cost = row.cost - row.total_budgeted
        # if any,
        if outstanding_cost > 0:
            # if there is sufficient budget
            if budget >= outstanding_cost:
                # assign the total outstanding cost to the amount budgeted for
                # this exchange in this year
                df.set_value(row.Index, budget_colname, outstanding_cost)
                # add that amount to the total amount budgeted for this exchange
                df.set_value(row.Index, "total_budgeted", outstanding_cost + row.total_budgeted)
                # set the year this exchange completed to this year
                df.set_value(row.Index, "year_completed", year)
                # decrement the remaing budget available this year
                budget -= outstanding_cost

            # if there is not enough budget
            else:
                # assign all remaining budget to this exchange
                df.set_value(row.Index, budget_colname, budget)
                # add that amount to the total amount budgeted for this exchange
                df.set_value(row.Index, "total_budgeted", budget + row.total_budgeted)
                # set remaining budget for this year to zero
                budget = 0

    # spare budget?
    if budget > 0:
        print("{} budget unspent in year {}".format(budget, year))


# print results
print(df)
