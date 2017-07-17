import csv

with open ('pcd_sectors.csv') as csvfile:
	reader = csv.DictReader(csvfile, delimiter=',')
	
	pcd_sector = {}
	
	for row in reader:
		print (pcd_sector = {row['pcd_sector'], 
			row['name'], 
			row['oslaua'], 
			int(row['population_weight']),
			float(row['area_sq_km']),
			row['oscty'],
			row['gor'],
			float(row['sitefinder.count']),
			row['geotype'],
			float(row['site.density'])})
			
print(row)