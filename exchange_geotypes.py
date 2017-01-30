# -*- coding: utf-8 -*-
"""
Created on Sun Jan 15 21:14:16 2017

@author: oughtone
"""

#%%
import os
#print (os.getcwd())
#set working directory
os.chdir('C:\\Users\\oughtone\\Dropbox\\Fixed Broadband Model\\UK Data')

#import pandas as pd
import pandas as pd #this is how I usually import pandas
import numpy as np

####IMPORT CODEPOINT DATA#####
#import codepoint
codepoint = r'C:\Users\oughtone\Dropbox\Fixed Broadband Model\Data\codepoint.csv'
codepoint = pd.read_csv(codepoint, low_memory=False)

#rename columns
codepoint.rename(columns={'POSTCODE':'pcd', 'tp':'all_premises', 'rp':'domestic', 'bp':'non_domestic', 'pd':'PO_box', 'ls':'pcd_type', 'dc':'oslaua'}, inplace=True)

#remove whitespace in pcd column
codepoint['pcd'].replace(regex=True,inplace=True,to_replace=r' ',value=r'')

#remove whitespace in pcd_type column (so small or large delivery point column)
codepoint['pcd_type'].replace(regex=True,inplace=True,to_replace=r' ',value=r'')

#subset columns
codepoint = codepoint[['pcd','oslaua', 'GOR', 'all_premises', 'domestic', 'non_domestic', 'PO_box', 'pcd_type']]

#subset = small user delivery points
codepoint = codepoint.loc[codepoint['pcd_type'] == 'S']

####IMPORT ACTUAL AND INTERPOLATED DISTANCE DATA FOR PCD 2 EXCHANGE#####   This data uses the ONSP_August_2012_UK_O.csv lookup
#import actual distance data
a_distance = r'C:\Users\oughtone\Dropbox\Fixed Broadband Model\Data\exchanges.output.csv'
a_distance = pd.read_csv(a_distance)
#counts = a_distance.mdf.value_counts()

#rename columns
a_distance.rename(columns={'pcd':'actual_pcd', 'distances':'actual_distance'}, inplace=True)

#subset columns      
a_distance = a_distance[['actual_pcd','actual_distance']]

#covert from kms to meters 
a_distance.loc[:,'actual_distance'] *= 1000
#test = pd.merge(v_distance, a_distance, on=['pcd'], how='inner')

#import interpolated distance data
v_distance = r'C:\Users\oughtone\Dropbox\Fixed Broadband Model\Data\distance.matrix.csv'
v_distance = pd.read_csv(v_distance)

#remove whitespace
v_distance['InputID'].replace(regex=True,inplace=True,to_replace=r' ',value=r'')

#delete unwanted variable
del v_distance['TargetID']

#rename columns
v_distance.rename(columns={'InputID':'interpol_pcd', 'Distance':'interpol_distance'}, inplace=True)

df_merge = a_distance.merge(v_distance, left_on="actual_pcd", right_on="interpol_pcd", how="right", indicator=True)
df_merge["interpol_distance"] = df_merge["interpol_distance"].where(df_merge["_merge"] != "both", df_merge["actual_distance"]) 
all_distances = df_merge.drop(["actual_pcd", "actual_distance", "_merge"], axis=1).sort_values("interpol_pcd")

#remove unwanted dfs
del a_distance
del v_distance

#rename columns
all_distances.rename(columns={'interpol_pcd':'pcd', 'interpol_distance':'distance'}, inplace=True)

####IMPORT POSTCODE to EXCHANGE DATA####  
#pcd to exchange data - 5381 exchanges
pcd_2_exchanges = r'C:\Users\oughtone\Dropbox\Fixed Broadband Model\Data\pcd2exchanges.csv'
pcd_2_exchanges = pd.read_csv(pcd_2_exchanges)
#counts = pcd_2_exchanges.Postcode_1.value_counts()

#rename columns
pcd_2_exchanges.rename(columns={'POSTCODE':'pcd', 'Postcode_1':'exchange_pcd'}, inplace=True)

#remove whitespace
pcd_2_exchanges['pcd'].replace(regex=True,inplace=True,to_replace=r' ',value=r'')

#subset columns
pcd_2_exchanges = pcd_2_exchanges[['pcd','exchange_pcd']]

#merge all distance information with pcd_2_echange list
df_merge = pd.merge(all_distances, pcd_2_exchanges, on='pcd', how='inner')

#counts = df_merge.exchange_pcd.value_counts()

#remove unwanted df
del pcd_2_exchanges

#create new line_length column
df_merge["line_length"] = "under_2k"

#change line_length to over 2k
df_merge.loc[ (df_merge['distance'] >= 2000), 'line_length'] = 'over_2k'

#merge dfs
data = pd.merge(codepoint, df_merge, on='pcd', how='inner')             
counts = data.exchange_pcd.value_counts()

#sum all_premises to obtain 
exchange_size = data.groupby(by=['exchange_pcd'])['all_premises'].sum()

#merge a pandas.core.series with a pandas core.frame.dataframe
data = data.merge(exchange_size.to_frame(), left_on='exchange_pcd', right_on='Index', right_index=True)

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

counts = data.exchange_pcd.value_counts()
         
####IMPORT POSTCODE DIRECTORY####
#set location and read in as df
Location = r'C:\Users\oughtone\Dropbox\Fixed Broadband Model\Data\ONSPD_AUG_2012_UK_O.csv'
onsp = pd.read_csv(Location, header=None, low_memory=False)

#rename columns
onsp.rename(columns={0:'pcd', 6:'oslaua', 9:'easting', 10:'northing', 13:'country', 15:'region'}, inplace=True)

#remove whitespace from pcd columns
onsp['pcd'].replace(regex=True,inplace=True,to_replace=r' ',value=r'')

#subset columns  ##   pcd_directory = onsp[['pcd','oslaua', 'region', 'easting', 'northing', 'country']]
pcd_directory = onsp[['pcd','oslaua']]

#remove unwated data
del onsp

###IMPORT kitz exchange list
#set location and read in as df
Location = r'C:\Users\oughtone\Dropbox\Fixed Broadband Model\Data\exchange.data.kitz.csv'
kitz_exchanges = pd.read_csv(Location)

kitz_exchanges = kitz_exchanges[kitz_exchanges.Region != 'Northern Ireland']
   
#remove whitespace
kitz_exchanges['Postcode'].replace(regex=True,inplace=True,to_replace=r' ',value=r'')

#rename columns
kitz_exchanges.rename(columns={'Postcode':'pcd'}, inplace=True)

#merge based on kitz_exchanges
exchanges = pd.merge(kitz_exchanges, pcd_directory, on='pcd', how='inner')

exchanges = exchanges[['ID', 'pcd','oslaua', 'OLO', 'Name']]

del data['oslaua']

#merge based on exchange data
data = pd.merge(data, exchanges, on='pcd', how='outer', indicator=True)  

#This is where you need to find the non matching exchange pcds
#subset = test.loc[test['_merge'] == 'left_only']
#test = (subset.drop_duplicates(['exchange_pcd']))
#exchanges.to_csv('kitz.exchanges.w.geo.csv')

#subset columns      
subset = data[['OLO','pcd', 'oslaua', 'all_premises_y']]
#subset = exchanges[['pcd','oslaua']]

subset = (subset.drop_duplicates(['OLO']))
#remove unwated data
del kitz_exchanges
 
#import city geotype info
geotypes1 = r'C:\Users\oughtone\Dropbox\Fixed Broadband Model\Data\geotypes.csv'
geotypes1 = pd.read_csv(geotypes1)

#merge 
merge = pd.merge(subset, geotypes1, on='oslaua', how='outer')

del geotypes1
del merge['oslaua']
del merge['pcd']

exchanges = exchanges.drop_duplicates('OLO')

merge = merge.drop_duplicates('OLO')

#exchanges["geotype"] = ""

#exchanges.geotype.update(exchanges.OLO.map(merge.set_index('OLO').geotype))

#merge 
exchanges = pd.merge(exchanges, merge, on='OLO', how='outer')

counts = exchanges.geotype.value_counts()
  
exchanges['Rank'] = exchanges.groupby(['geotype'])['all_premises_y'].rank(ascending=False)
     
#subset = exchanges.loc[(exchanges.geotype == 'Large City') | (exchanges.geotype == 'Small City'),:]
subset = exchanges.loc[exchanges['geotype'] == 'Large City']

large_cities = subset.copy(deep=True)

#subset = exchanges.loc[:,exchanges.loc['geotype'] == 'Large City']

# <1000 lines
#subset.loc[subset['TotalLines'] < 1000, 'geotype'] = '<1,000'
# >1000 lines but <3000
#subset.loc[ (subset['TotalLines'] >= 1000) & (subset['TotalLines'] < 3000), 'geotype'] = '>1,000'
# >3000 lines but <10000
#subset.loc[ (subset['TotalLines'] >= 3000) & (subset['TotalLines'] < 10000), 'geotype'] = '>3,000'
# >10000 lines but <20000
#subset.loc[ (subset['TotalLines'] >= 10000) & (subset['TotalLines'] < 20000), 'geotype'] = '>10,000'
# >20000
#subset.loc[ (subset['TotalLines'] >= 20000), 'geotype'] = '>20,000'

large_cities = large_cities.sort_values(by='Rank')

large_cities = large_cities.loc[large_cities['Rank'] < 205]

large_cities.all_premises_y.values.sum()

large_cities["geotype"] = "Large City"

#subset = exchanges.loc[(exchanges.geotype == 'Large City') | (exchanges.geotype == 'Small City'),:]
subset = exchanges.loc[exchanges['geotype'] == 'Small City']

small_cities = subset.copy(deep=True)

# <1000 lines
#subset.loc[ (subset.loc['TotalLines'] < 1000), 'geotype'] = '<1,000'
# >1000 lines but <3000
#subset.loc[ (subset['TotalLines'] >= 1000) & (subset['TotalLines'] < 3000), 'geotype'] = '>1,000'
# >3000 lines but <10000
#subset.loc[ (subset['TotalLines'] >= 3000) & (subset['TotalLines'] < 10000), 'geotype'] = '>3,000'
# >10000 lines but <20000
#subset.loc[ (subset['TotalLines'] >= 10000) & (subset['TotalLines'] < 20000), 'geotype'] = '>10,000'
# >20000
#subset.loc[ (subset['TotalLines'] >= 20000), 'geotype'] = '>20,000'

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
subset = exchanges[['OLO','ID','oslaua']]
#subset = exchanges[['pcd','oslaua']]

#import city geotype info
geotypes2 = r'C:\Users\oughtone\Dropbox\Fixed Broadband Model\Data\geotypes2.csv'
geotypes2 = pd.read_csv(geotypes2)

#merge 
merge = pd.merge(subset, geotypes2, on='oslaua', how='outer')

del geotypes2
del merge['oslaua']

exchanges = exchanges.drop_duplicates('OLO')

merge = merge.drop_duplicates('OLO')

exchanges.geotype.update(exchanges.OLO.map(merge.set_index('OLO').geotype))

exchanges.geotype.update(exchanges.OLO.map(large_cities.set_index('OLO').geotype))

exchanges.geotype.update(exchanges.OLO.map(small_cities.set_index('OLO').geotype))

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
subset = exchanges[['pcd','geotype']]

subset = subset.copy(deep=True)

#rename columns
subset.rename(columns={'pcd':'exchange_pcd'}, inplace=True)

#subset = subset[(subset['geotype'] =='Inner London') | (subset['geotype'] =='Large City') | (subset['geotype'] =='Small City')]

del data['geotype']
# merge 
data = pd.merge(data, subset, on='exchange_pcd', how='outer')

counts = data.geotype_name.value_counts()

data['geotype_name'] = data['geotype'].combine_first(data['geotype_name'])

#not_matched = data[data.OLO ==""]
#test = data[data.geotype_name !=""]

exchanges = data.groupby(['geotype_name','OLO', 'Name', 'exchange_pcd', 'oslaua'], as_index=False).sum()

counts = exchanges.geotype_name.value_counts()

del exchanges['all_premises_x']
del exchanges['domestic']
del exchanges['non_domestic']
del exchanges['PO_box']
del exchanges['distance']
del exchanges['ID']

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
Location = r'C:\Users\oughtone\Dropbox\Fixed Broadband Model\Data\ONSPD_AUG_2012_UK_O.csv'
onsp = pd.read_csv(Location, header=None, low_memory=False)

#rename columns
onsp.rename(columns={0:'pcd', 6:'oslaua', 9:'easting', 10:'northing', 13:'country', 15:'region'}, inplace=True)

#remove whitespace from pcd columns
onsp['pcd'].replace(regex=True,inplace=True,to_replace=r' ',value=r'')

pcd_directory = onsp[['pcd', 'region', 'easting', 'northing', 'country']]

#subset columns  ##   pcd_directory = onsp[['pcd','oslaua', 'region', 'easting', 'northing', 'country']]
#pcd_directory = onsp[['pcd','oslaua']]
exchanges = pd.merge(exchanges, pcd_directory, left_on = 'exchange_pcd', right_on = 'pcd', how='inner')
 
###### LOTS OF LOST DATA!!!!!!!!!########
counts = exchanges.geotype_name.value_counts()

del all_distances             
del codepoint
del data
del merge
del pcd_directory
del subset
del counts               
del Location
del onsp

available_budget_each_year = [
    1500000000,
    1500000000,
    1500000000,
    1500000000,
]
    
#sort exchanges based on geotype and then premises numbers
exchanges = exchanges.sort_values(by=['geotype_number','all_premises_y'], ascending=[True,False])
###############################################################################
###### SET UP COPY FOR GFAST COSTINGS ######
ex_Gfast = exchanges.copy(deep=True)

# DON'T PUT NUMBERS IN '' AS IT MAKES THEM STRINGS!
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

ex_Gfast['cost'] = ex_Gfast.prem_cost*ex_Gfast.all_premises_y             

ex_Gfast['Rank'] = ex_Gfast.groupby(['geotype_number'])['all_premises_y'].rank(ascending=False)
   
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
###### SET UP COPY FOR GFAST COSTINGS ######
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

ex_FTTdp['cost'] = ex_FTTdp.prem_cost*ex_FTTdp.all_premises_y             

ex_FTTdp['Rank'] = ex_FTTdp.groupby(['geotype_number'])['all_premises_y'].rank(ascending=False)
   
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
###### SET UP COPY FOR GFAST COSTINGS ######
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
         
ex_FTTH['cost'] = ex_FTTH.prem_cost*ex_FTTH.all_premises_y                 

ex_FTTH['Rank'] = ex_FTTH.groupby(['geotype_number'])['all_premises_y'].rank(ascending=False)

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

path=r'C:\Users\oughtone\Dropbox\Fixed Broadband Model\R_model'
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

#%%

df = (ex_Gfast.drop_duplicates(['exchange_pcd', 'year_completed']))
#rename columns
df.rename(columns={'exchange_pcd':'A', 'year_completed':'B'}, inplace=True)

cols = list('AB')
mux = pd.MultiIndex.from_product([df.A.unique(), df.B.unique()], names=cols)
test = df.set_index(cols).reindex(mux, fill_value=0).reset_index()



test = test.set_value('E148EZ', 'OLO', 10)





#sum all_premises to obtain 
test = ex_Gfast.groupby(by=['region', 'year_completed'])['all_premises_y'].sum()

test = ex_Gfast.pivot(index='year_completed', columns='oslaua', values='all_premises_y')


df = pd.DataFrame(np.random.rand(10, 4), columns=['a', 'b', 'c', 'd'])
df.iplot(kind='area', fill=True, filename='cufflinks/stacked-area')








df.iplot(subplots=True, shape=(4, 1), filename='pandas/cufflinks-subplot rows')






N = 40
x = np.linspace(0, 1, N)
y = np.random.randn(N)
df = pd.DataFrame({'x': x, 'y': y})
df.head()

data = [
    go.Bar(
        x=ex_Gfast['geotype_name'], # assign x as the dataframe column 'x'
        y=ex_Gfast['total_budgeted']
    )
]

url = py.plot(data, filename='pandas-bar-chart')



# Learn about API authentication here: https://plot.ly/pandas/getting-started
# Find your api_key here: https://plot.ly/settings/api
import plotly.plotly as py
import plotly.graph_objs as go

import pandas as pd
import numpy as np

N = 20
x = np.linspace(1, 10, N)
y = np.random.randn(N)+3
y2 = np.random.randn(N)+6
y3 = np.random.randn(N)+9
y4 = np.random.randn(N)+12
df = pd.DataFrame({'x': x, 'y': y, 'y2':y2, 'y3':y3, 'y4':y4})
df.head()

data = [
    go.Bar(
        x=df['x'], # assign x as the dataframe column 'x'
        y=df['y']
    ),
    go.Bar(
        x=df['x'],
        y=df['y2']
    ),
    go.Bar(
        x=df['x'],
        y=df['y3']
    ),
    go.Bar(
        x=df['x'],
        y=df['y4']
    )

]

layout = go.Layout(
    barmode='stack',
    title='Stacked Bar with Pandas'
)

fig = go.Figure(data=data, layout=layout)

# IPython notebook
# py.iplot(fig, filename='pandas-bar-chart-layout')

url = py.plot(data, filename='pandas-bar-chart-layout')














