# -*- coding: utf-8 -*-
"""
Created on Sun Jan 15 21:14:16 2017

@author: RDO
"""

#%%
import os
#print (os.getcwd())
#set working directory
os.chdir('F:\Fixed Broadband Model\Data')

#import pandas as pd
import pandas as pd #this is how I usually import pandas
import numpy as np

####IMPORT CODEPOINT DATA#####
#import codepoint
codepoint = r'F:\Fixed Broadband Model\Data\codepoint_centroids.csv'
codepoint = pd.read_csv(codepoint, low_memory=False)

codepoint.rename(columns={'POSTCODE':'pcd'}, inplace=True)

codepoint['pcd'].replace(regex=True,inplace=True,to_replace=r' ',value=r'')

####IMPORT DISTANCE MATRIX#####
distance = r'F:\Fixed Broadband Model\Data\distance_matrix.csv'
distance = pd.read_csv(distance, low_memory=False)

#rename columns
distance.rename(columns={'InputID':'pcd', 'TargetID':'exchange', 'Distance':'distance'}, inplace=True)

distance['pcd'].replace(regex=True,inplace=True,to_replace=r' ',value=r'')

df_merge = pd.merge(codepoint, distance, on='pcd', how='inner')

#subset columns
df_merge = df_merge[['pcd', 'exchange', 'distance']]

codepoint = r'F:\Fixed Broadband Model\Data\all_codepoint.csv'
codepoint = pd.read_csv(codepoint, header=None, low_memory=False)

#subset columns
codepoint = codepoint[[0,3,5,6,7,16,18]]

#rename columns
codepoint.rename(columns={0:'pcd', 3:'all_premises', 5:'domestic', 6:'non_domestic', 7:'PO_box', 16:'oslaua', 18:'pcd_type'}, inplace=True)

codepoint['pcd'].replace(regex=True,inplace=True,to_replace=r' ',value=r'')

#remove whitespace in pcd_type column (so small or large delivery point column)
codepoint['pcd_type'].replace(regex=True,inplace=True,to_replace=r' ',value=r'')

#subset = small user delivery points
codepoint = codepoint.loc[codepoint['pcd_type'] == 'S']

#subset columns
codepoint = codepoint[['pcd', 'all_premises', 'oslaua']]

#counts = codepoint.exchange.value_counts()

df_merge = pd.merge(codepoint, df_merge, on='pcd', how='inner')

#subset columns
df_merge = df_merge[['pcd', 'exchange', 'all_premises', 'distance', 'oslaua']]

df_merge = df_merge.drop_duplicates('pcd')

Vstreets = r'F:\\Fixed Broadband Model\\Codepoint_shapes_Oct_2016\\Vstreet_lookup\\output.csv'
Vstreets = pd.read_csv(Vstreets , low_memory=False)

Vstreets['pcd'].replace(regex=True,inplace=True,to_replace=r' ',value=r'')

Vstreets = Vstreets.drop_duplicates('vertical')

df_merge.pcd.update(df_merge.pcd.map(Vstreets.set_index('vertical').pcd))

#remove unwanted df
del distance
del codepoint
del Vstreets

#create new line_length column
df_merge["line_length"] = "under_2k"

#change line_length to over 2k
df_merge.loc[ (df_merge['distance'] >= 2000), 'line_length'] = 'over_2k'

#sum all_premises to obtain 
exchange_size = df_merge.groupby(by=['exchange'])['all_premises'].sum()

data = df_merge

#merge a pandas.core.series with a pandas core.frame.dataframe
data = data.merge(exchange_size.to_frame(), left_on='exchange', right_on='Index', right_index=True)

#rename columns
#output = data.rename(columns={'all_premises_x':'all_premises'}, inplace=True)

#rename columns
#all = data.rename(columns={'all_premises_y':'exchange_premises'}, inplace=True)

del exchange_size
del df_merge

#create variable                
data["prem_under_2k"] = "0"

#allocate all premises to column if under_2k
data.loc[ (data['distance'] < 2000), 'prem_under_2k'] = data.all_premises_x
         
 #create variable          
data["prem_over_2k"] = "0"

#allocate all premises to column if over_2k
data.loc[ (data['distance'] >= 2000), 'prem_over_2k'] = data.all_premises_x
         
#create variable  
data["prem_under_1k"] = "0"

#allocate all premises to column if under_1k
data.loc[ (data['distance'] < 1000), 'prem_under_1k'] = data.all_premises_x
    
#create variable  
data["prem_over_1k"] = "0"        
          
#allocate all premises to column if over_1k
data.loc[ (data['distance'] >= 1000), 'prem_over_1k'] = data.all_premises_x

#create geotype empty column
data["geotype"] = ""
#segment exchanges by size
# <1000 lines
data.loc[ (data['all_premises_y'] < 1000), 'geotype'] = '<1,000'
# >1000 lines but <3000
data.loc[ (data['all_premises_y'] >= 1000) & (data['all_premises_y'] < 3000), 'geotype'] = '>1,000'
# >3000 lines but <10000
data.loc[ (data['all_premises_y'] >= 3000) & (data['all_premises_y'] < 10000), 'geotype'] = '>3,000'
# >10000 lines but <20000
data.loc[ (data['all_premises_y'] >= 10000) & (data['all_premises_y'] < 20000), 'geotype'] = '>10,000'
# >20000
data.loc[ (data['all_premises_y'] >= 20000), 'geotype'] = '>20,000'

#create geotype_name empty column
data["geotype_name"] = ""
         
# <1000 lines, 1km
data.loc[ (data['geotype'] == '<1,000') & (data['distance'] > 1000), 'geotype_name'] = 'Below 1,000 (b)'
# <=1000 lines, 1km
data.loc[ (data['geotype'] == '<1,000') & (data['distance'] <= 1000), 'geotype_name'] = 'Below 1,000 (a)'

# >1000 lines but <3000, 1km
data.loc[ (data['geotype'] == '>1,000') & (data['distance'] > 1000), 'geotype_name'] = 'Above 1,000 (b)'
# >1000 lines but <3000, 1km
data.loc[ (data['geotype'] == '>1,000') & (data['distance'] <= 1000), 'geotype_name'] = 'Above 1,000 (a)'

# >3000 lines but <10000, 1km
data.loc[ (data['geotype'] == '>3,000') & (data['distance'] > 1000), 'geotype_name'] = 'Above 3,000 (b)'
# >3000 lines but <10000, 1km
data.loc[ (data['geotype'] == '>3,000') & (data['distance'] <= 1000), 'geotype_name'] = 'Above 3,000 (a)'

# >10000 lines but <20000, 2km
data.loc[ (data['geotype'] == '>10,000') & (data['distance'] > 2000), 'geotype_name'] = 'Above 10,000 (b)'
# >10000 lines but <20000, 2km
data.loc[ (data['geotype'] == '>10,000') & (data['distance'] <= 2000), 'geotype_name'] = 'Above 10,000 (a)'

# >20000 lines, 2km
data.loc[ (data['geotype'] == '>20,000') & (data['distance'] > 2000), 'geotype_name'] = 'Above 20,000 (b)'
# >20000 lines, 2km
data.loc[ (data['geotype'] == '>20,000') & (data['distance'] <= 2000), 'geotype_name'] = 'Above 20,000 (a)'        

counts = data.exchange.value_counts()
         
####IMPORT POSTCODE DIRECTORY####
#set location and read in as df
#Location = r'F:\Fixed Broadband Model\Data\onspd_Nov_2016.csv'
#onsp = pd.read_csv(Location, low_memory=False)

#subset columns 
#onsp = onsp[['pcd','oslaua', 'gor', 'ctry', 'msoa11', 'ru11ind']]

#pcd_directory = onsp.copy(deep=True)

#rename columns
#pcd_directory.rename(columns={'ctry':'country', 'gor':'region'}, inplace=True)

#remove whitespace from pcd columns
#pcd_directory['pcd'].replace(regex=True,inplace=True,to_replace=r' ',value=r'')

#remove unwated data
#del onsp

#test = pd.merge(data, pcd_directory, on='pcd', how='inner')

#import codepoint
ofcom_geography = r'F:\Fixed Broadband Model\Data\ofcom_geography.csv'
ofcom_geography = pd.read_csv(ofcom_geography, low_memory=False)

#merge 
data = pd.merge(data, ofcom_geography, on='oslaua', how='outer')

#subset columns      
subset = data[['exchange', 'oslaua']]
#subset = exchanges[['pcd','oslaua']]

subset = (subset.drop_duplicates(['exchange']))
 
#import city geotype info
geotypes1 = r'F:\Fixed Broadband Model\Data\geotypes.csv'
geotypes1 = pd.read_csv(geotypes1)

#merge 
merge = pd.merge(subset, geotypes1, on='oslaua', how='outer')

del geotypes1
del merge['oslaua']

exchanges = data[['exchange', 'oslaua', 'all_premises_y']]

exchanges = exchanges.drop_duplicates('exchange')

merge = merge.drop_duplicates('exchange')

#merge 
exchanges = pd.merge(exchanges, merge, on='exchange', how='outer')

counts = exchanges.geotype.value_counts()
  
exchanges['Rank'] = exchanges.groupby(['geotype'])['all_premises_y'].rank(ascending=False)
     
#subset = exchanges.loc[(exchanges.geotype == 'Large City') | (exchanges.geotype == 'Small City'),:]
subset = exchanges.loc[exchanges['geotype'] == 'Large City']

large_cities = subset.copy(deep=True)

large_cities = large_cities.sort_values(by='Rank')

large_cities = large_cities.loc[large_cities['Rank'] < 205]

large_cities.all_premises_y.values.sum()

large_cities["geotype"] = "Large City"

#subset = exchanges.loc[(exchanges.geotype == 'Large City') | (exchanges.geotype == 'Small City'),:]
subset = exchanges.loc[exchanges['geotype'] == 'Small City']

small_cities = subset.copy(deep=True)

small_cities = small_cities.sort_values(by='Rank')

small_cities = small_cities.loc[small_cities['Rank'] < 181]

small_cities.all_premises_y.values.sum()

small_cities["geotype"] = "Small City"

exchanges["geotype"] = ""
#segment exchanges by size again to eliinate previous large or small city geotypes
# <1000 lines
exchanges.loc[ (exchanges['all_premises_y'] < 1000), 'geotype'] = '<1,000'
# >1000 lines but <3000
exchanges.loc[ (exchanges['all_premises_y'] >= 1000) & (exchanges['all_premises_y'] < 3000), 'geotype'] = '>1,000'
# >3000 lines but <10000
exchanges.loc[ (exchanges['all_premises_y'] >= 3000) & (exchanges['all_premises_y'] < 10000), 'geotype'] = '>3,000'
# >10000 lines but <20000
exchanges.loc[ (exchanges['all_premises_y'] >= 10000) & (exchanges['all_premises_y'] < 20000), 'geotype'] = '>10,000'
# >20000
exchanges.loc[ (exchanges['all_premises_y'] >= 20000), 'geotype'] = '>20,000'

#subset columns      
subset = exchanges[['exchange','oslaua']]
#subset = exchanges[['pcd','oslaua']]

#import city geotype info
geotypes2 = r'C:\Users\ExecEducation\Dropbox\Fixed Broadband Model\Data\geotypes2.csv'
geotypes2 = pd.read_csv(geotypes2)

#merge 
merge = pd.merge(subset, geotypes2, on='oslaua', how='outer')

del geotypes2
del merge['oslaua']

exchanges = exchanges.drop_duplicates('exchange')

merge = merge.drop_duplicates('exchange')

exchanges.geotype.update(exchanges.exchange.map(merge.set_index('exchange').geotype))

exchanges.geotype.update(exchanges.exchange.map(large_cities.set_index('exchange').geotype))

exchanges.geotype.update(exchanges.exchange.map(small_cities.set_index('exchange').geotype))

counts = exchanges.geotype.value_counts()

exchanges = exchanges[(exchanges['geotype'] =='Inner London') | (exchanges['geotype'] =='Large City') | (exchanges['geotype'] =='Small City')]

counts = exchanges.groupby(by=['geotype'])['all_premises_y'].sum()

del large_cities
del small_cities

# <1000 lines, 1km
data.loc[ (data['geotype'] == '<1,000') & (data['distance'] > 1000), 'geotype_name'] = 'Below 1,000 (b)'
# <=1000 lines, 1km
data.loc[ (data['geotype'] == '<1,000') & (data['distance'] <= 1000), 'geotype_name'] = 'Below 1,000 (a)'

# >1000 lines but <3000, 1km
data.loc[ (data['geotype'] == '>1,000') & (data['distance'] > 1000), 'geotype_name'] = 'Above 1,000 (b)'
# >1000 lines but <3000, 1km
data.loc[ (data['geotype'] == '>1,000') & (data['distance'] <= 1000), 'geotype_name'] = 'Above 1,000 (a)'

# >3000 lines but <10000, 1km
data.loc[ (data['geotype'] == '>3,000') & (data['distance'] > 1000), 'geotype_name'] = 'Above 3,000 (b)'
# >3000 lines but <10000, 1km
data.loc[ (data['geotype'] == '>3,000') & (data['distance'] <= 1000), 'geotype_name'] = 'Above 3,000 (a)'

# >10000 lines but <20000, 2km
data.loc[ (data['geotype'] == '>10,000') & (data['distance'] > 2000), 'geotype_name'] = 'Above 10,000 (b)'
# >10000 lines but <20000, 2km
data.loc[ (data['geotype'] == '>10,000') & (data['distance'] <= 2000), 'geotype_name'] = 'Above 10,000 (a)'

# >20000 lines, 2km
data.loc[ (data['geotype'] == '>20,000') & (data['distance'] > 2000), 'geotype_name'] = 'Above 20,000 (b)'
# >20000 lines, 2km
data.loc[ (data['geotype'] == '>20,000') & (data['distance'] <= 2000), 'geotype_name'] = 'Above 20,000 (a)'        

#subset columns      
subset = exchanges[['exchange','geotype']]

subset = subset.copy(deep=True)

del data['geotype']
# merge 
data = pd.merge(data, subset, on='exchange', how='outer')

counts = data.geotype_name.value_counts()

data['geotype_name'] = data['geotype'].combine_first(data['geotype_name'])

del data['geotype']

#subset columns      
subset = data[['exchange', 'oslaua', 'oscty', 'gor', 'code', 'geotype_name']]

#subset =
subset = subset.drop_duplicates('exchange')

#convert all non-numeric variables to numeric for summation
data[["all_premises_x", "prem_under_2k", "prem_over_2k", "prem_under_1k", "prem_over_1k"]] = data[["all_premises_x", "prem_under_2k", "prem_over_2k", "prem_under_1k", "prem_over_1k"]].apply(pd.to_numeric)

exchanges = data.groupby(['exchange'], as_index=False).sum()

del exchanges['all_premises_y']
del exchanges['distance']

#rename columns
exchanges.rename(columns={'all_premises_x':'all_premises'}, inplace=True)

#merge 
exchanges = pd.merge(exchanges, subset, on='exchange', how='inner')

counts = exchanges.geotype_name.value_counts()

exchanges["geotype_number"] = ""

# DON'T PUT NUMBERS IN '' AS IT MAKES THEM STRINGS!
exchanges.loc[ (exchanges['geotype_name'] == 'Inner London'), 'geotype_number'] = 1
exchanges.loc[ (exchanges['geotype_name'] == 'Large City'), 'geotype_number'] = 2
exchanges.loc[ (exchanges['geotype_name'] == 'Small City'), 'geotype_number'] = 3
exchanges.loc[ (exchanges['geotype_name'] == 'Above 20,000 (a)'), 'geotype_number'] = 4
exchanges.loc[ (exchanges['geotype_name'] == 'Above 20,000 (b)'), 'geotype_number'] = 5
exchanges.loc[ (exchanges['geotype_name'] == 'Above 10,000 (a)'), 'geotype_number'] = 6
exchanges.loc[ (exchanges['geotype_name'] == 'Above 10,000 (b)'), 'geotype_number'] = 7
exchanges.loc[ (exchanges['geotype_name'] == 'Above 3,000 (a)'), 'geotype_number'] = 8
exchanges.loc[ (exchanges['geotype_name'] == 'Above 3,000 (b)'), 'geotype_number'] = 9
exchanges.loc[ (exchanges['geotype_name'] == 'Above 1,000 (a)'), 'geotype_number'] = 10
exchanges.loc[ (exchanges['geotype_name'] == 'Above 1,000 (b)'), 'geotype_number'] = 11
exchanges.loc[ (exchanges['geotype_name'] == 'Below 1,000 (a)'), 'geotype_number'] = 12
exchanges.loc[ (exchanges['geotype_name'] == 'Below 1,000 (b)'), 'geotype_number'] = 13

# DON'T PUT NUMBERS IN '' AS IT MAKES THEM STRINGS!
exchanges.loc[ (exchanges['geotype_name'] == 'Inner London'), 'speed'] = 50
exchanges.loc[ (exchanges['geotype_name'] == 'Large City'), 'speed'] = 50
exchanges.loc[ (exchanges['geotype_name'] == 'Small City'), 'speed'] = 50
exchanges.loc[ (exchanges['geotype_name'] == 'Above 20,000 (a)'), 'speed'] = 30
exchanges.loc[ (exchanges['geotype_name'] == 'Above 20,000 (b)'), 'speed'] = 30
exchanges.loc[ (exchanges['geotype_name'] == 'Above 10,000 (a)'), 'speed'] = 30
exchanges.loc[ (exchanges['geotype_name'] == 'Above 10,000 (b)'), 'speed'] = 30
exchanges.loc[ (exchanges['geotype_name'] == 'Above 3,000 (a)'), 'speed'] = 30
exchanges.loc[ (exchanges['geotype_name'] == 'Above 3,000 (b)'), 'speed'] = 10
exchanges.loc[ (exchanges['geotype_name'] == 'Above 1,000 (a)'), 'speed'] = 10
exchanges.loc[ (exchanges['geotype_name'] == 'Above 1,000 (b)'), 'speed'] = 10
exchanges.loc[ (exchanges['geotype_name'] == 'Below 1,000 (a)'), 'speed'] = 10
exchanges.loc[ (exchanges['geotype_name'] == 'Below 1,000 (b)'), 'speed'] = 10
            
####IMPORT POSTCODE DIRECTORY####
#set location and read in as df
#Location = r'C:\Users\RDO\Dropbox\Fixed Broadband Model\Data\ONSPD_AUG_2012_UK_O.csv'
#onsp = pd.read_csv(Location, header=None, low_memory=False)

#rename columns
#onsp.rename(columns={0:'pcd', 6:'oslaua', 9:'easting', 10:'northing', 13:'country', 15:'region'}, inplace=True)

#remove whitespace from pcd columns
#onsp['pcd'].replace(regex=True,inplace=True,to_replace=r' ',value=r'')

#pcd_directory = onsp[['pcd', 'region', 'easting', 'northing', 'country']]

#common = exchanges.merge(pcd_directory,on=['exchange_pcd','pcd'])
#subset columns  ##   pcd_directory = onsp[['pcd','oslaua', 'region', 'easting', 'northing', 'country']]
#pcd_directory = onsp[['pcd','oslaua']]
#exchanges = pd.merge(exchanges, pcd_directory, left_on = 'exchange_pcd', right_on = 'pcd', how='outer')

#right_pcd_directory = test[(test['_merge'] =='right_only')]
#left_exchanges = test[(test['_merge'] =='left_only')]
#########FIND NON MATCHING EXCHANGES#########
#pcd_2_exchanges = r'C:\Users\RDO\Dropbox\Fixed Broadband Model\Data\pcd2exchanges.csv'
#pcd_2_exchanges = pd.read_csv(pcd_2_exchanges)
#total_list = (pcd_2_exchanges.drop_duplicates(['Postcode_1']))
#total_list = total_list[['Postcode_1']]
#total_list.rename(columns={'Postcode_1':'exchange_pcd'}, inplace=True)
#total_list['exchange_pcd'].replace(regex=True,inplace=True,to_replace=r' ',value=r'')
#total_list = total_list.sort_values(by=['exchange_pcd'], ascending=[True])
#total_list = total_list.reset_index(drop=True)

#matching = (exchanges.drop_duplicates(['exchange_pcd','OLO', 'Name']))                       
#matching = matching[['exchange_pcd']]
#matching['exchange_pcd'].replace(regex=True,inplace=True,to_replace=r' ',value=r'')
#matching = matching.sort_values(by=['exchange_pcd'], ascending=[True])
#matching = matching.reset_index(drop=True)

#common = total_list.merge(matching,on=['exchange_pcd','exchange_pcd'])
#print(common)
#non_matching = total_list[(~total_list.exchange_pcd.isin(common.exchange_pcd))&(~total_list.exchange_pcd.isin(common.exchange_pcd))]                      
#non_matching = pd.merge(non_matching, pcd_2_exchanges, left_on = 'exchange_pcd', right_on = 'Postcode_1', how='inner')
#non_matching = (non_matching.drop_duplicates(['exchange_pcd','Postcode_1']))  
#set location and read in as df
#Location = r'C:\Users\RDO\Dropbox\Fixed Broadband Model\Data\exchange.data.kitz.csv'
#kitz_exchanges = pd.read_csv(Location)

#non_matching = pd.merge(non_matching, kitz_exchanges, left_on = 'exchange_pcd', right_on = 'Postcode', how='inner')

#path=r'C:\Users\RDO\Dropbox\Fixed Broadband Model'
#non_matching.to_csv(os.path.join(path,r'non_matching.csv'))
#########FIND NON MATCHING EXCHANGES#########                      
###### LOTS OF LOST DATA!!!!!!!!!########
counts = exchanges.geotype_name.value_counts()
           
del data
del merge
del subset

path=r'C:\Users\ExecEducation\Dropbox\Fixed Broadband Model\model_outputs'
exchanges.to_csv(os.path.join(path,r'exchanges.csv'))

####################################################################
#%%
exchanges = r'C:\Users\ExecEducation\Dropbox\Fixed Broadband Model\model_outputs\exchanges.csv'
exchanges = pd.read_csv(exchanges, low_memory=False)

summary = exchanges.groupby(['geotype_number']).mean()

summary_2 = exchanges.groupby(['geotype_number']).sum()

counts = exchanges.geotype_number.value_counts()

####################################################################

available_budget_each_year = [
    1500000000,
    1500000000,
    1500000000,
    1500000000,
    1500000000,
    1500000000,
    1500000000,
]
    
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

path=r'C:\Users\ExecEducation\Dropbox\Fixed Broadband Model\model_outputs'
ex_Gfast.to_csv(os.path.join(path,r'ex_Gfast.csv'))
ex_FTTdp.to_csv(os.path.join(path,r'ex_FTTdp.csv'))
ex_FTTH.to_csv(os.path.join(path,r'ex_FTTH.csv'))
#%%     
###############################################################################
# standard windows cmd prompt as administrator and typed  pip install ggplot

##WORKING EXAMPLE

# Learn about API authentication here: https://plot.ly/pandas/getting-started
# Find your api_key here: https://plot.ly/settings/api

import plotly.plotly as py
import plotly.graph_objs as go
import pandas as pd
import numpy as np

trace = go.Scatter( x=ex_Gfast['year_completed'], y=ex_Gfast['all_premises_y'] )
data = [trace]
url = py.plot(data, filename='ex_Gfast_time-series')

trace = go.Scatter( x=ex_FTTdp['year_completed'], y=ex_FTTdp['all_premises_y'] )
data = [trace]
url = py.plot(data, filename='ex_FTTdp_time-series')

trace = go.Scatter( x=ex_FTTH['year_completed'], y=ex_FTTH['all_premises_y'] )
data = [trace]
url = py.plot(data, filename='ex_FTTH_time-series')








