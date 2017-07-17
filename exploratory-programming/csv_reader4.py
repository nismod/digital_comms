import csv

#set DictReader with file name
reader = csv.DictReader(open('pcd_sectors.csv'))

#create empty dictionary
result = {}

#populate dictionary
for row in reader:
    key = row.pop('pcd_sector')
    if key in result:
        # implement your duplicate row handling here
        pass
    result[key] = row
print (result)

#print just the keys in the outer dictionary, so pcd_sectors
#for i in result:
#	print(i)
	
#myDictionary[] takes us into the inner dictionary
#for i in result:
#	for j in result[i]:	
#		print(result[i][j])
