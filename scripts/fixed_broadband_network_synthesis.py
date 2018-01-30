from digital_comms.fixed_model.network_structure import ICTManager
import os

from networkx import nx, drawing

from shapely.geometry import Point, LineString, mapping
import matplotlib.pyplot as plt

# Config
input_shapefiles_dir = 'input_shapefiles'
output_shapefiles_dir = 'output_shapefiles'

# Synthesize network
Manager = ICTManager(input_shapefiles_dir)

# Analyse network
nx.draw(Manager._network, with_labels=True, font_weight='bold')
plt.show()

print('Total length of the network: ', Manager.length)

# Intervention
Manager.build_infrastructure((-1.844580, 52.692175), {'Name': 'cab8', 'Type': 'pcp'})
Manager.build_infrastructure(([( -1.844580, 52.692175), (0, 52), ( 0.802002, 51.154586)]), {'Origin': 'CoreNode', 'Dest': 'cab8', 'Type': 'link','Physical': 'fiberglass'})

# Analyse network
nx.draw(Manager._network, with_labels=True, font_weight='bold')
plt.show()

print('Total length of the network: ', Manager.length)

# Write shapefile
Manager.save(output_shapefiles_dir)