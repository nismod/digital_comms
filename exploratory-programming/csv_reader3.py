import csv

reader = csv.DictReader(open('pcd_sectors.csv'))

result = {}
for row in reader:
    key = row.pop('pcd_sector')
    if key in result:
        # implement your duplicate row handling here
        pass
    result[key] = row
print (result)