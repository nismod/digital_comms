import csv

test_file = 'pcd_sectors.csv'
csv_file = csv.DictReader(open(test_file, 'rb'), delimiter=',')

for row in csv_file:
	print(csv_file)


