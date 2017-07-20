import csv
import os
import pprint

BASE_DIR = os.path.dirname(__file__)
CONFIG_DIR = os.path.join(BASE_DIR, '..', 'Data')
DATA_FILE = os.path.join(CONFIG_DIR, 'reprex_pcd_sector_data.csv')

#set DictReader with file name
reader = csv.DictReader(open(DATA_FILE))

#create empty dictionary
data = []

#populate dictionary
for row in reader:
    data.append(row)

pprint.pprint(data)

for index in range(len(data)):
	for key in data[


#class pcd_sector(object):
#	'''represents a postcode sector to be modelled'''
#	def __init__(self, data):
#		self.id = int(data["id"])
#		self.population = int(data["population"])
#		self.area = int(data["area"])
#	
#	def pop_density(self):
#		for i in range(len(self.id)):
#			density[i] = self.population[i] / self.area[i]
#			density.append(i)
#		return density		

#pcds = pcd_sector(data)
#pcds.pop_density()
	

list_of_dicts = [{'id': 'a', 'population': '20', 'area': '10'},
				{'id': 'a', 'population': '20', 'area': '10'}]
				
class pcd_sector(object):
	'''represents a postcode sector to be modelled'''
	def __init__(self, data):
		self.id = int(data["id"])
		self.population = int(data["population"])
		self.area = int(data["area"])
	
	def pop_density(self):
		for i in range(len(self.id)):
			density[i] = self.population[i] / self.area[i]
			density.append(i)
		return density					
				
				
def pop_density(self):
	for i in range(len(self.id)):
		density[i] = self.population[i] / self.area[i]
		density.append(i)
		return density	
				
				
results = [{'id': 'a', 'population': '20', 'area': '10', 'pop_density': 2},
		   {'id': 'a', 'population': '30', 'area': '5', 'pop_density': 6}]
