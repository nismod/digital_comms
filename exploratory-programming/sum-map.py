assets = [
	{
		"type": "site",
		"pcd_sector_id": 1,
		"cells": 3,
		"technology": "LTE"
	},
	{
		"type": "site",
		"pcd_sector_id": 2,
		"cells": 5,
		"technology": "LTE-Advanced"
	},
	{
		"type": "site",
		"pcd_sector_id": 3,
		"cells": 3,
		"technology": "LTE"
	}
	]
	
print({k:sum(map(int, v)) for k, v in assets.items()})