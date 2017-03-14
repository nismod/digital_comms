# -*- coding: utf-8 -*-
"""
Created on Sun Jan  1 12:22:37 2017

@author: EJO31
"""
#%%
import os
#print (os.getcwd())
#set working directory
os.chdir('E:\\NNA Submission\\Modelling\\Fixed\Exchanges')

#import pandas as pd
import pandas as pd #this is how I usually import pandas

###IMPORT POSTCODE DIRECTORY
#set location and read in as df
Location = r'E:\\NNA Submission\\Modelling\\Fixed\Exchanges\\ONSPD_AUG_2012_UK_O.csv'
onsp = pd.read_csv(Location, header=None, low_memory=False)

#rename columns
onsp.rename(columns={0:'pcd', 6:'oslaua', 9:'easting', 10:'northing', 13:'country', 15:'region'}, inplace=True)

#remove whitespace from pcd columns
onsp['pcd'].replace(regex=True,inplace=True,to_replace=r' ',value=r'')

#subset columns
pcd_directory = onsp[['pcd','oslaua', 'region', 'easting', 'northing', 'country']]

#remove unwated data
del onsp

###IMPORT kitz exchange list
#set location and read in as df
Location = r'E:\Fixed Broadband Model\Data\SamKnows_Exchanges_All_Stats.csv'
samknows = pd.read_csv(Location)

samknows = samknows[['OLO', 'Name', 'Postcode']]

#remove whitespace
samknows['Postcode'].replace(regex=True,inplace=True,to_replace=r' ',value=r'')

#rename columns
samknows.rename(columns={'Postcode':'pcd'}, inplace=True)

#merge based on kitz_exchanges
exchanges = pd.merge(samknows, pcd_directory, on='pcd', how='inner')

exchanges = exchanges.loc[exchanges['country'] != 'N99999999']

exchanges.to_csv('exchanges.w.geo.csv')

#remove unwated data
del samknows

###IMPORT EXCHANGE DATA###
# 1913 unique exchanges, XXXX unique cabinets, XXXX unique postcodes
#set location and read in as df1
Location = r'E:\NNA Submission\Modelling\Fixed\Exchanges\pcd.to.ex1.csv'
pcd1 = pd.read_csv(Location)
#set location and read in as df2
Location = r'E:\NNA Submission\Modelling\Fixed\Exchanges\pcd.to.ex2.csv'
pcd2 = pd.read_csv(Location)

#concatenate vertically
pcd_all = pd.concat([pcd1, pcd2], axis=0)

#select columns 1:6
pcd_all = pcd_all[pcd_all.columns[0:6]]

#rename columns
pcd_all.rename(columns={'SAU_ID':'exchange'}, inplace=True)

#remove unwated data
del pcd1 
del pcd2

###IMPORT EXCHANGE DATA from Tomasso Valletti###
# 3389 unique exchanges, XXXX unique postcodes
#set location and read in as df1
Location = r'E:\NNA Submission\Modelling\Fixed\Exchanges\exch_name_pcde.csv'
pcd_all2  = pd.read_csv(Location)

#rename columns
pcd_all2.rename(columns={'Q42010':'exchange', '20110131':'pcd'}, inplace=True)

#remove whitespace from pcd columns
pcd_all2['pcd'].replace(regex=True,inplace=True,to_replace=r' ',value=r'')
pcd_all2['exchange'].replace(regex=True,inplace=True,to_replace=r' ',value=r'')

###IMPORT EXCHANGE DATA from Openreach rollout###
# 1451 unique exchanges, XXXX unique postcodes
#set location and read in as df1
Location = r'E:\NNA Submission\Modelling\Fixed\Exchanges\pcp.to.pcd.dec.11.one.csv'
pcd3  = pd.read_csv(Location)
#read in df2
Location = r'E:\NNA Submission\Modelling\Fixed\Exchanges\pcp.to.pcd.dec.11.two.csv'
pcd4  = pd.read_csv(Location)

#concatenate vertically
pcd_all3 = pd.concat([pcd3, pcd4], axis=0)

#select columns 1:6
pcd_all3 = pcd_all[pcd_all.columns[0:6]]

del pcd3 
del pcd4 

#### 1913 unique exchanges, 77041 unique cabinets, unique 1,260,555
#concatenate vertically
all_data = pd.concat([pcd_all, pcd_all3], axis=0)

#remove whitespace from pcd columns
all_data['pcd'].replace(regex=True,inplace=True,to_replace=r' ',value=r'')
all_data['exchange'].replace(regex=True,inplace=True,to_replace=r' ',value=r'')

exchanges = (list(set(all_data.exchange)))
cabinets = list(set(all_data.SAU_NODE_ID))
pcds = list(set(all_data.pcd))

#get only unique combinations of exchanges, cabinets and pcds
#unique = 1,586,985
all_data = all_data.drop_duplicates(subset=['exchange', 'SAU_NODE_ID', 'pcd'])

all_data = all_data[['exchange', 'pcd', 'SAU_NODE_ID']]

#merge with inner join
output = pd.merge(all_data, pcd_directory, on='pcd', how='inner')

output = output.loc[output['country'] != 'N99999999']

del output['oslaua']
del output['region']
del output['country']

#rename columns
output.rename(columns={'exchange':'OLO'}, inplace=True)  

output = output[output.easting.notnull()]
output = output[output.northing.notnull()]
                                
os.chdir('E:\\Fixed Broadband Model\pcd_2_cab_2_exchange_data')

output.to_csv('pcd_2_cab_2_exchange_data.csv', index=False)

#cambridge = output[(output.oslaua == 'E07000008')]

#cambridge.to_excel('cambridge.xlsx', index=False)







