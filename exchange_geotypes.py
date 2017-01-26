# -*- coding: utf-8 -*-
"""
Created on Sun Jan 15 21:14:16 2017

@author: EJO31
"""

#%%
import os
#print (os.getcwd())
#set working directory
os.chdir('C:\\Users\\EJO31\\Dropbox\\Fixed Broadband Model\\UK Data')

#import pandas as pd
import pandas as pd #this is how I usually import pandas

####IMPORT CODEPOINT DATA#####
#import codepoint
codepoint = r'C:\Users\EJO31\Dropbox\Fixed Broadband Model\Data\codepoint.csv'
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
a_distance = r'C:\Users\EJO31\Dropbox\Fixed Broadband Model\Data\exchanges.output.csv'
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
v_distance = r'C:\Users\EJO31\Dropbox\Fixed Broadband Model\Data\distance.matrix.csv'
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
pcd_2_exchanges = r'C:\Users\EJO31\Dropbox\Fixed Broadband Model\Data\pcd2exchanges.csv'
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
data.loc[ (data['geotype'] == '<1,000') & (data['distance'] > 1000), 'geotype_name'] = 'm Below 1,000 (b)'
# <=1000 lines, 1km
data.loc[ (data['geotype'] == '<1,000') & (data['distance'] <= 1000), 'geotype_name'] = 'l Below 1,000 (a)'

# >1000 lines but <3000, 1km
data.loc[ (data['geotype'] == '>1,000') & (data['distance'] > 1000), 'geotype_name'] = 'k Above 1,000 (b)'
# >1000 lines but <3000, 1km
data.loc[ (data['geotype'] == '>1,000') & (data['distance'] <= 1000), 'geotype_name'] = 'j Above 1,000 (a)'

# >3000 lines but <10000, 1km
data.loc[ (data['geotype'] == '>3,000') & (data['distance'] > 1000), 'geotype_name'] = 'i Above 3,000 (b)'
# >3000 lines but <10000, 1km
data.loc[ (data['geotype'] == '>3,000') & (data['distance'] <= 1000), 'geotype_name'] = 'h Above 3,000 (a)'

# >10000 lines but <20000, 2km
data.loc[ (data['geotype'] == '>10,000') & (data['distance'] > 2000), 'geotype_name'] = 'g Above 10,000 (b)'
# >10000 lines but <20000, 2km
data.loc[ (data['geotype'] == '>10,000') & (data['distance'] <= 2000), 'geotype_name'] = 'f Above 10,000 (a)'

# >20000 lines, 2km
data.loc[ (data['geotype'] == '>20,000') & (data['distance'] > 2000), 'geotype_name'] = 'e Above 20,000 (b)'
# >20000 lines, 2km
data.loc[ (data['geotype'] == '>20,000') & (data['distance'] <= 2000), 'geotype_name'] = 'd Above 20,000 (a)'        

counts = data.exchange_pcd.value_counts()
         
####IMPORT POSTCODE DIRECTORY####
#set location and read in as df
Location = r'C:\Users\EJO31\Dropbox\Fixed Broadband Model\Data\ONSPD_AUG_2012_UK_O.csv'
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
Location = r'C:\Users\EJO31\Dropbox\Fixed Broadband Model\Data\exchange.data.kitz.csv'
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
geotypes1 = r'C:\Users\EJO31\Dropbox\Fixed Broadband Model\Data\geotypes.csv'
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
subset = exchanges.loc[exchanges['geotype'] == 'b Large City']

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

large_cities["geotype"] = "b Large City"

#subset = exchanges.loc[(exchanges.geotype == 'Large City') | (exchanges.geotype == 'Small City'),:]
subset = exchanges.loc[exchanges['geotype'] == 'c Small City']

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

small_cities["geotype"] = "c Small City"

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
geotypes2 = r'C:\Users\EJO31\Dropbox\Fixed Broadband Model\Data\geotypes2.csv'
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

counts = exchanges.groupby(by=['geotype'])['all_premises_y'].sum()

del data['geotype']
del large_cities
del small_cities

#subset columns      
subset = exchanges[['OLO','geotype']]

#merge 
test = pd.merge(data, subset, on='OLO', how='outer')
#test2 = test.groupby(['OLO'])[["prem_under_2k", "prem_over_2k", "prem_under_1k", "prem_over_1k"]].sum()


#make data into dataframe shape

#1 turn geotype into number

#%%













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






















        





