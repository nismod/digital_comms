import csv

with open('E:\ITRC Econ Demo Projections\population_population_regional_breakdown.csv', 'r') as populationFile:
    r = csv.reader(populationFile)
    i = 0
    for line in r:
        print(line)
        i += 1
        if i > 5:
            break
