lst = [{'pcd_sector': 'ABDC', 'area_coverage_2014': '100'},
	   {'pcd_sector': 'DEFG', 'area_coverage_2014': '0'}]

for d in lst:
	if d['area_coverage_2014'] > 0:
		d['new_key'] = 'True'
	   

