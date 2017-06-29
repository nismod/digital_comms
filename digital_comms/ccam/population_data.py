import csv

populationFile = open('E:\ITRC Econ Demo Projections\population_population_regional_breakdown.csv')
populationReader = csv.reader(populationFile)
populationData = list(populationReader)

print(populationData[0:3])

