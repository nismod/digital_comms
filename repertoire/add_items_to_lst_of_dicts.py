import pprint

lst = [{'pcd_sector': 'ABDC', 'area_coverage_2014': '100'},
       {'pcd_sector': 'DEFG', 'area_coverage_2014': '0'},
	   {'pcd_sector': 'DEFG', 'area_coverage_2014': 'NA'}]

for sub in lst:
	for key in ['area_coverage_2014']: # list of keys to convert
		try:
			sub[key] = float(sub[key]) if key !='NA' else None
		except ValueError as e:
			pass
	   
for d in lst:
	try:
		coverage = float(d['area_coverage_2014'])
		if coverage > 0:
			d['new_key'] = True
		else:
			d['new_key'] = False
	except ValueError as e:
		d['new_key'] = False
		
pprint.pprint (lst)









