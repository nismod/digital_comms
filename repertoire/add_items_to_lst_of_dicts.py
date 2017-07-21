import pprint

l1 = [{'pcd_sector': 'ABDC', 'area_coverage_2014': '100'},
	   {'pcd_sector': 'DEFG', 'area_coverage_2014': '0'}]
	   
l2 = [{'pcd_sector': 'ABDC', 'asset': '3G', 'random': '2gs'},
	   {'pcd_sector': 'DEFG', 'asset': '3G', 'random': '3je'},
	   {'pcd_sector': 'CDEF', 'asset': '3G', 'random': '4jd'},
	   {'pcd_sector': 'BCDE', 'asset': '3G', 'random': '5js'}]

grouped = {}
for d in l1 + l2:
	grouped.setdefault(d['pcd_sector'], {'asset':0, 'area_coverage_2014':0}).update(d)

result = [d for d in grouped.values()]
pprint.pprint(result)	