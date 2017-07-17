import csv

#set DictReader with file name
reader = csv.DictReader(open('pcd_sectors.csv'))

#create empty dictionary
result = {}

#populate dictionary
with open ('pcd_sectors.csv') as f:
	reader = 


for row in reader:
    key = row.pop('pcd_sector')
    if key in result:
        # implement your duplicate row handling here
        pass
    result[key] = row
print (result)

#area = {result.pcd_sector: result.area_sq_km() for result in result.values()},

#print(area)