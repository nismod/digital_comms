import pprint

l1 = [{'pcd_sector': 'ABDC', 'area_coverage_2014': '100'},
	   {'pcd_sector': 'DEFG', 'area_coverage_2014': '0'}]
	   
l2 = [{'pcd_sector': 'ABDC', 'asset': '3G', 'asset_id': '2gs'},
	  {'pcd_sector': 'ABDC', 'asset': '4G', 'asset_id': '7jd'},
	  {'pcd_sector': 'DEFG', 'asset': '3G', 'asset_id': '3je'},
	  {'pcd_sector': 'DEFG', 'asset': '4G', 'asset_id': '8js'},
	  {'pcd_sector': 'CDEF', 'asset': '3G', 'asset_id': '4jd'}]

d1 = {d['pcd_sector']:d for d in l1}
result = [dict(d, **d1.get(d['pcd_sector'], {})) for d in l2]	
	
pprint.pprint(result)




