import csv

#set DictReader with file name
reader = csv.DictReader(open('pcd_sectors.csv'))

#create empty dictionary
result = []

#populate dictionary
for row in reader:
    result.append(row)
#print (result)

#sum area in list of dictionaries by convertint to float
area = sum(float(item['area_sq_km']) for item in result)

print (area)
