"""Cambridge Communications Assessment Model
"""

import itertools
#from operator import itemgetter

class ICTManager(object):
	"""Model controller class
	"""
	def __init__(self, lads, pcd_sectors, assets):
		"""Create an instance of the model

		Parameters
		----------
		areas: list of dicts
			Each area is an LAD, expect the dictionary to have values for
			- ID
			- name
			- population
			- area (km^2)
			- penetration
			- user demand
		"""
		# Area ID (integer?) => Area
		self.lads = {}

		# pcd_sector id =? LAD id
		lad_id_by_pcd_sector = {}

		for lad_data in lads:
			id = lad_data["id"]
			self.lads[id] = LAD(lad_data)

		for pcd_sector_data in pcd_sectors:
			lad_id = pcd_sector_data["lad_id"]
			pcd_sector_id = pcd_sector_data["id"]
			# add PostcodeSector to LAD
			self.lads[lad_id].add_pcd_sector(PostcodeSector(pcd_sector_data))
			# add LAD id to lookup by pcd_sector_id
			lad_id_by_pcd_sector[pcd_sector_id] = lad_id
			
		for asset_data in assets:
			asset = Asset(asset_data)
			lad_id = lad_id_by_pcd_sector[asset.pcd_sector_id]
			area_for_asset = self.lads[lad_id]
			area_for_asset.add_asset(asset)
		
	def apply_interventions(self, interventions):
		pass

	def results(self):
		return {
			"system": {area.name: area.system() for area in self.lads.values()},
			"capacity": {area.name: area.capacity() for area in self.lads.values()},
			"coverage": {area.name: area.coverage() for area in self.lads.values()},
			"demand": {area.name: area.demand() for area in self.lads.values()},
			"cost": {area.name: area.cost() for area in self.lads.values()},
			"energy_demand": {area.name: area.energy_demand() for area in self.lads.values()}
		}


class LAD(object):
	"""Represents an area to be modelled, contains
	data for demand characterisation and assets for
	supply assessment
	"""
	def __init__(self, data):
		self.id = data["id"]
		self.name = data["name"]
		self.population = data["population"]
		self.area = data["area"]
		self.user_demand = data["user_demand"]
		self._pcd_sectors = {} 

	def add_pcd_sector(self, pcd_sector):
		self._pcd_sectors[pcd_sector.id] = pcd_sector

	def add_asset(self, asset):
		pcd_sector_id = asset.pcd_sector_id
		self._pcd_sectors[pcd_sector_id].add_asset(asset)

	def system(self):
		for asset in assets:
			area_id = self._pcd_sectors['lad_id']
			tech = self._pcd_sectors['technology']
			cells = self._pcd_sectors['cells']
			# check area is in system
			if area_id not in system:
				system[area_id] = {}
			# check tech is in area
			if tech not in system[area_id]:
				system[area_id][tech] = 0
				# add number of cells to tech in area
				system[area_id][tech] += cells
		return system

	def capacity(self):
		"""returning the value from the method in pcd_sector object"""
		return sum([pcd_sector.capacity() for pcd_sector in self._pcd_sectors.values()])

	def demand(self):
		"""returning the value from the method in pcd_sector object"""
		return sum([pcd_sector.demand() for pcd_sector in self._pcd_sectors.values()]) / len(self._pcd_sectors)

	def coverage(self):
		threshold = 2
		population_with_coverage = sum([pcd_sector.population for pcd_sector in self._pcd_sectors.values() if pcd_sector.capacity() >= threshold])
		total_pop = self.population  # or sum of PostcodeSector populations
		return float(population_with_coverage) / total_pop

	def cost(self):
		'''returning the value from the method in pcd_sector object'''
		return sum([pcd_sector.cost() for pcd_sector in self._pcd_sectors.values()])
	
	def energy_demand(self):
		'''returning the value from the method in pcd_sector object'''
		return sum([pcd_sector.energy_demand() for pcd_sector in self._pcd_sectors.values()])

		
class PostcodeSector(object):
	"""Represents a pcd_sector to be modelled
	"""
	def __init__(self, data):
		self.id = data["id"]
		self.lad_id = ["lad_id"]
		self.name = data["name"]
		self.population = data["population"]
		self.area = data["area"]
		# TODO: replace hard-coded parameters
		self.user_demand = 2
		self.penetration = 0.8
		self._assets = []
		#I've turned assets from a list of dictionaries, to an explicit list per asset type
		
	def add_asset(self, asset):
		self._assets.append(asset)

	def demand(self):
		users = self.population * self.penetration
		user_throughput = users * self.user_demand
		capacity_per_kmsq = user_throughput / self.area
		return capacity_per_kmsq
	
	def system(self):
		for asset in assets:
			area_id = asset['pcd_sector_id']
			tech = asset['technology']
			cells = asset['cells']
			# check area is in system
			if area_id not in system:
				system[area_id] = {}
			# check tech is in area
			if tech not in system[area_id]:
				system[area_id][tech] = 0
				# add number of cells to tech in area
				system[area_id][tech] += cells
		return system

	def capacity(self):
		# sites : count how many assets are sites
		sites = len(list(filter(lambda asset: asset.type == "site", self._assets)))
		# sites/km^2 : divide num_sites/area
		site_density = float(sites) / self.area
		# for a given site density and spectrum band, look up capacity
		capacity = lookup_capacity(site_density)
		return capacity
	
	def cost(self):
		# sites : count how many assets are sites
		sites = len(list(filter(lambda asset: asset.type == "site", self._assets)))
		# for a given number of sites, what is the total cost?	
		cost = (sites * 10)
		return cost
		
	def energy_demand(self):
		# cells : count how many cells there are in the assets database
		cells = sum(map(lambda asset : asset.cells, self._assets))
		# for a given number of cells, what is the total cost?	
		energy_demand = (cells * 5)
		return energy_demand


class Asset(object):
	"""Element of the communication infrastructure system,
	e.g. base station or distribution-point unit.
	"""
	def __init__(self, data):
		self.type = data["type"]
		self.pcd_sector_id = data["pcd_sector_id"]
		self.cells = data["cells"]
		self.technology = data["technology"]

def lookup_capacity(site_density):
	"""Use lookup table to find capacity by site density
	TODO:
	- extend to include spectrum band
	- load from data source?
	- handle any density - round/bin
	"""
	lookup_table = {
		5:70,
		3:24,
		2:12,
		1:6,
		0.5: 3,
		0.25: 2,
		0.2: 1,
		0.1: 0.5,
		0: 0
	}
	return lookup_table[site_density]

if __name__ == '__main__':
	lads = [
		{
			"id": 1,
			"name": "Cambridge",
			"population": 250000,
			"area": 10,
			"user_demand": 1,
			"spectrum_available": {
				"700": False,
				"800": True
			}
		},		
		{
			"id": 2,
			"name": "Oxford",
			"population": 220000,
			"area": 10,
			"user_demand": 1,
			"spectrum_available": {
				"700": False,
				"800": True
			}
		}
	]
	pcd_sectors = [
		{
			"id": 1,
			"lad_id": 1,
			"name": "CB1G",
			"population": 50000,
			"area": 2, 
		},
		{
			"id": 2,
			"lad_id": 1,
			"name": "CB1H",
			"population": 50000,
			"area": 2, 
		},
		{			
			"id": 3,
			"lad_id": 2,
			"name": "OX1A",
			"population": 50000,
			"area": 4, 
		},
		{
			"id": 4,
			"lad_id": 2,
			"name": "OX1B",
			"population": 50000,
			"area": 4
		}
	]
	assets = [
		{
			"type": "site",
			"pcd_sector_id": 1,
			"cells": 3,
			"technology": "LTE"
		},
		{
			"type": "site",
			"pcd_sector_id": 1,
			"cells": 5,
			"technology": "LTE-Advanced"
		},
		{
			"type": "site",
			"pcd_sector_id": 2,
			"cells": 3,
			"technology": "LTE"
		},
		{
			"type": "site",
			"pcd_sector_id": 2,
			"cells": 6,
			"technology": "LTE-Advanced"
		},
		{
			"type": "site",
			"pcd_sector_id": 3,
			"cells": 3,
			"technology": "LTE"
		},
		{
			"type": "site",
			"pcd_sector_id": 3,
			"cells": 2,
			"technology": "LTE-Advanced"
		},	
		{
			"type": "site",
			"pcd_sector_id": 4,
			"cells": 1,
			"technology": "LTE"
		},
		{
			"type": "site",
			"pcd_sector_id": 4,
			"cells": 3,
			"technology": "LTE-Advanced"
		}	
]
	manager = ICTManager(lads, pcd_sectors, assets)
	print(manager.results())