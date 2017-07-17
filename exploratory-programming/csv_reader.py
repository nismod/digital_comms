import csv

def import_data (file_path):

	with  open(file_path) as csvfle:
		input_file = csv.DictReader(csvfile)
		for row in input_file:
			pcd_sector = row['pcd_sector'],
			name = row['name'],
			oslaua = row['oslaua'],
			pop_weight = row['population.weight'],
			area_sq_km = row['area_sq_km'],
			gor = row['gor'],
			sitefinder_count = row['sitefinder.count'],
			geotype = row['geotype'],
			site_density = row['site.density']
	return 