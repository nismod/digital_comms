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
codepoint.rename(columns={'POSTCODE':'pcd', 'tp':'all_premises', 'rp':'domestic', 'bp':'non_domestic', 'pd':'PO_box', 'ls':'pcd_type'}, inplace=True)

#remove whitespace
codepoint['pcd'].replace(regex=True,inplace=True,to_replace=r' ',value=r'')

#remove whitespace
codepoint['pcd_type'].replace(regex=True,inplace=True,to_replace=r' ',value=r'')

#subset columns
codepoint = codepoint[['pcd','GOR', 'all_premises', 'domestic', 'non_domestic', 'PO_box', 'pcd_type']]

#subset = small user delivery points
codepoint = codepoint.loc[codepoint['pcd_type'] == 'S']

####IMPORT ACTUAL AND INTERPOLATED DISTANCE DATA FOR PCD 2 EXCHANGE#####
#import distance data
a_distance = r'C:\Users\EJO31\Dropbox\Fixed Broadband Model\Data\exchanges.output.csv'
a_distance = pd.read_csv(a_distance)

#rename columns
a_distance.rename(columns={'pcd':'actual_pcd'}, inplace=True)

#rename columns
a_distance.rename(columns={'distances':'actual_distance'}, inplace=True)

#subset columns      
a_distance = a_distance[['actual_pcd','actual_distance']]

a_distance.loc[:,'actual_distance'] *= 1000
#test = pd.merge(v_distance, a_distance, on=['pcd'], how='inner')

#import distance data
v_distance = r'C:\Users\EJO31\Dropbox\Fixed Broadband Model\Data\distance.matrix.csv'
v_distance = pd.read_csv(v_distance)

#remove whitespace
v_distance['InputID'].replace(regex=True,inplace=True,to_replace=r' ',value=r'')

del v_distance['TargetID']

#rename columns
v_distance.rename(columns={'InputID':'interpol_pcd'}, inplace=True)

#rename columns
v_distance.rename(columns={'Distance':'interpol_distance'}, inplace=True)

df_merge = a_distance.merge(v_distance, left_on="actual_pcd", right_on="interpol_pcd", how="right", indicator=True)
df_merge["interpol_distance"] = df_merge["interpol_distance"].where(df_merge["_merge"] != "both", df_merge["actual_distance"]) 
all_distances = df_merge.drop(["actual_pcd", "actual_distance", "_merge"], axis=1).sort_values("interpol_pcd")

counts = df_merge._merge.value_counts()

del a_distance
del v_distance

#rename columns
all_distances.rename(columns={'interpol_pcd':'pcd'}, inplace=True)

#rename columns
all_distances.rename(columns={'interpol_distance':'distance'}, inplace=True)

####IMPORT POSTCODE DIRECTORY####
#import city geotype info
pcd_2_exchanges = r'C:\Users\EJO31\Dropbox\Fixed Broadband Model\Data\pcd2exchanges.csv'
pcd_2_exchanges = pd.read_csv(pcd_2_exchanges)

#rename columns
pcd_2_exchanges.rename(columns={'POSTCODE':'pcd', 'Postcode_1':'exchange_pcd'}, inplace=True)

#remove whitespace
pcd_2_exchanges['pcd'].replace(regex=True,inplace=True,to_replace=r' ',value=r'')

#subset columns
pcd_2_exchanges = pcd_2_exchanges[['pcd','exchange_pcd']]

#merge all distance information with pcd_2_echange list
df_merge = pd.merge(all_distances, pcd_2_exchanges, on='pcd', how='inner')

del pcd_2_exchanges

#create new line_length column
df_merge["line_length"] = "under_2k"

#change line_length to over 2k
df_merge.loc[ (df_merge['distance'] >= 2000), 'line_length'] = 'over_2k'

data = pd.merge(codepoint, df_merge, on='pcd', how='inner')             
    
#sum all_premises to obtain 
exchange_size = data.groupby(by=['exchange_pcd'])['all_premises'].sum()

#rename columns
#exchange_size = exchange_size.rename(columns={'all_premises':'exchange_premises'}, inplace=True)

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

#remove whitespace
kitz_exchanges['Postcode'].replace(regex=True,inplace=True,to_replace=r' ',value=r'')

#rename columns
kitz_exchanges.rename(columns={'Postcode':'pcd'}, inplace=True)

#merge based on kitz_exchanges
exchanges = pd.merge(kitz_exchanges, pcd_directory, on='pcd', how='inner')

exchanges = exchanges[['ID', 'pcd','oslaua', 'OLO', 'Name']]

#merge based on kitz_exchanges
data = pd.merge(data, exchanges, on='pcd', how='outer')  

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
subset = exchanges.loc[exchanges['geotype'] == 'Large City']

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

large_cities = subset.sort(['Rank'])

large_cities = subset.loc[subset['Rank'] < 205]

large_cities.all_premises_y.values.sum()

large_cities["geotype"] = "Large City"

#subset = exchanges.loc[(exchanges.geotype == 'Large City') | (exchanges.geotype == 'Small City'),:]
subset = exchanges.loc[exchanges['geotype'] == 'Small City']

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

small_cities = subset.sort(['Rank'])

small_cities = subset.loc[subset['Rank'] < 181]

small_cities.all_premises_y.values.sum()

small_cities["geotype"] = "Small City"

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

counts = exchanges.geotype.value_counts()

counts = exchanges.groupby(by=['geotype'])['all_premises_y'].sum()












































        





