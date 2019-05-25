###VISUALISE MODEL OUTPUTS###
#library(ggplot2)
#library(dplyr)
#install.packages("tidyverse")
library(tidyverse)
#install.packages("maptools")
library(maptools)
#install.packages("rgeos")
library(rgeos)
#install.packages("Cairo")
library(Cairo)
# install.packages('rgdal')
library(rgdal)
#install.packages("ggmap")
library(ggmap)
library(scales)
library(RColorBrewer)
#library(ineq)
#install.packages("ggpubr")
library(ggpubr)       

set.seed(8000)

data_directory <- "D:\\Github\\digital_comms\\results\\mobile_outputs"
shapes_directory <- "D:\\Github\\digital_comms\\data\\raw\\d_shapes\\lad_uk_2016-12"
output_directory <- "D:\\Github\\digital_comms\\data_visualisation\\arc_5G"

setwd(data_directory)

metric_files <- list.files(data_directory, pattern="*.csv")

#subset those metric files
metric_files <- metric_files[grep("^metrics.*", metric_files)]

#initialised empty dataframe
empty_df <- data.frame(year=numeric(),
                       area_id=character(), 
                       area_name=character(), 
                       cost=numeric(),
                       demand=numeric(),
                       capacity=numeric(),
                       capacity_deficit=numeric(),
                       population=numeric(),
                       area=numeric(),
                       pop_density= numeric()) 

import_function = lapply(metric_files, function(x) {
  DF <- read.csv(x, header = T, sep = ",")
  DF_Merge <- merge(empty_df, DF, all = T)
  DF_Merge$file <- as.factor(x)
  return(DF_Merge)})

all_scenarios <- do.call(rbind, import_function)

all_scenarios <- all_scenarios[which(all_scenarios$area_id== 'E07000008' |
                                     all_scenarios$area_id== 'E07000177' |
                                     all_scenarios$area_id== 'E07000099' |
                                     all_scenarios$area_id== 'E06000055' |
                                     all_scenarios$area_id== 'E06000056' |
                                     all_scenarios$area_id== 'E07000012' |
                                      all_scenarios$area_id== 'E06000032' |
                                      all_scenarios$area_id== 'E07000179' |
                                      all_scenarios$area_id== 'E07000004' |
                                      all_scenarios$area_id== 'E07000180' |
                                      all_scenarios$area_id== 'E07000181' |
                                      all_scenarios$area_id== 'E07000155' |
                                      all_scenarios$area_id== 'E06000042' |
                                      all_scenarios$area_id== 'E07000178' |
                                      all_scenarios$area_id== 'E06000030' |
                                      all_scenarios$area_id== 'E07000151' |
                                      all_scenarios$area_id== 'E07000154' |
                                      all_scenarios$area_id== 'E07000156' |
                                      all_scenarios$area_id== 'E07000009' |
                                      all_scenarios$area_id== 'E07000242' |
                                      all_scenarios$area_id== 'E07000011' |
                                      all_scenarios$area_id== 'E07000243'
                                      ),]

all_scenarios$aggregate_demand <- (all_scenarios$demand * all_scenarios$area) #in Mbps still
all_scenarios$aggregate_capacity <-  (all_scenarios$capacity * all_scenarios$area) #in Mbps still
all_scenarios$aggregate_capacity_deficit <- (all_scenarios$capacity_deficit * all_scenarios$area) #in Mbps still

all_scenarios <- all_scenarios %>% separate(file, c("file_type", "scenario", "throughput", "strategy"), "_", remove = FALSE)

aggregate_metrics_func <- function(mydata)
{
  mydata %>% 
    group_by(year, scenario, strategy) %>% 
    summarise(cost_m = round(sum(cost, na.rm = TRUE)/1000000,1),
              aggregate_demand_gbps = round(sum(aggregate_demand, na.rm = TRUE)/1000,1), 
              # = sum(capacity, na.rm = TRUE),
              aggregate_capacity_gbps = round(sum(aggregate_capacity, na.rm = TRUE)/1000,1), 
              #capacity_deficit = sum(capacity_deficit, na.rm = TRUE),
              aggregate_capacity_deficit_gbps = round(sum(aggregate_capacity_deficit, na.rm = TRUE)/1000,1),
              population = sum(population, na.rm = TRUE),
              area = sum(area, na.rm = TRUE)) %>%
    mutate(pop_density_km2 = population / area, 
           demand_density_mbps_km2 = round((aggregate_demand_gbps*1000) / area,1),
           ) %>%
    select(year, cost_m, aggregate_demand_gbps, aggregate_capacity_gbps,
           aggregate_capacity_deficit_gbps, population, area, 
           pop_density_km2, demand_density_mbps_km2, scenario, strategy)
}

aggregate_scenario_metrics <- aggregate_metrics_func(all_scenarios)

### EXPORT TO FOLDER
setwd(output_directory)
write.csv(aggregate_scenario_metrics, "aggregate_scenario_metrics.csv")

aggregate_scenario_metrics$strategy = factor(aggregate_scenario_metrics$strategy, levels=c('strategy-minimal.csv',
                                                   'strategy-macrocell-700-3500.csv', 
                                                   'strategy-sectorisation.csv',
                                                   'strategy-macro-densification.csv', 
                                                   "strategy-small-cell.csv",
                                                   'strategy-small-cell-and-spectrum.csv'))

aggregate_scenario_metrics$scenario = factor(aggregate_scenario_metrics$scenario, levels=c('pop-base',
                                                                                           'pop-0-unplanned',
                                                                                           'pop-1-new-cities',
                                                                                           'pop-2-expansion'))
scenario_names <- c('pop-base' = 'Baseline',
                    'pop-0-unplanned' = 'Unplanned',
                    'pop-1-new-cities' = 'New Cities',
                    'pop-2-expansion' = 'Expansion') 

strategy_names <- c('strategy-minimal.csv' = 'No investment',
                    'strategy-macrocell-700-3500.csv' = "Spectrum integration", 
                    'strategy-sectorisation.csv' = 'Sectorisation',
                    'strategy-macro-densification.csv' = "Macro densification", 
                    'strategy-small-cell.csv' = "Small cells",
                    'strategy-small-cell-and-spectrum.csv' = 'Spectrum + small cells') 

ggplot(data=aggregate_scenario_metrics, aes(x=year, y=cost_m)) +
  geom_line()+ geom_point() + facet_grid(strategy ~ scenario, labeller = labeller(scenario = scenario_names, strategy = strategy_names))


aggregate_metrics_long <-  aggregate_scenario_metrics %>% 
                            select(year, scenario, strategy, pop_density_km2, 
                                   aggregate_demand_gbps, aggregate_capacity_gbps,
                                   aggregate_capacity_deficit_gbps)

aggregate_metrics_long <- aggregate_metrics_long %>% gather(metric, value, pop_density_km2, 
                                                            aggregate_demand_gbps, aggregate_capacity_gbps,
                                                            aggregate_capacity_deficit_gbps)

aggregate_metrics_long$metric = factor(aggregate_metrics_long$metric, levels=c('pop_density_km2',
                                                                               'aggregate_demand_gbps',
                                                                               'aggregate_capacity_gbps', 
                                                                               'aggregate_capacity_deficit_gbps'))

aggregate_metrics_long$strategy <- factor(aggregate_metrics_long$strategy, 
                                          levels=c('strategy-minimal.csv',
                                                   'strategy-macrocell-700-3500.csv', 
                                                   'strategy-sectorisation.csv',
                                                   'strategy-macro-densification.csv', 
                                                   'strategy-small-cell.csv',
                                                   'strategy-small-cell-and-spectrum.csv'),
                                          labels=c('strategy-minimal.csv' = 'No investment',
                                                  'strategy-macrocell-700-3500.csv' = "Spectrum integration", 
                                                  'strategy-sectorisation.csv' = 'Sectorisation',
                                                  'strategy-macro-densification.csv' = "Macro densification", 
                                                  'strategy-small-cell.csv' = "Small cells",
                                                  'strategy-small-cell-and-spectrum.csv' = 'Spectrum + small cells')) 

metric_names <- c('pop_density_km2' = 'Population density (km^2)',
                  'aggregate_demand_gbps' = 'Aggregate demand (Gbps)',
                  'aggregate_capacity_gbps' = "Aggregate capacity (Gbps)", 
                  'aggregate_capacity_deficit_gbps' = "Capacity margin (Gbps)") 

aggregate_metrics <- ggplot(data=aggregate_metrics_long, aes(x=year, y=value, colour=strategy)) +
  geom_line() + geom_point() + labs(colour="Strategy") +
  theme(legend.position = "bottom", axis.title.x=element_blank(),axis.title.y=element_blank()) +   
  facet_grid(metric ~ scenario, labeller = labeller(scenario = scenario_names, metric = metric_names))

### EXPORT TO FOLDER 
setwd(output_directory)
tiff('aggregate_metrics.tiff', units="in", width=12, height=10, res=400)
print(aggregate_metrics)
dev.off()


###################################################################################
#### DEMAND VISUALISATION
###################################################################################

all_scenarios <- all_scenarios %>% separate(file, c("file_type", "scenario", "throughput", "strategy"), "_", remove = FALSE)


data_demand_func <- function(mydata)
{
  mydata %>% 
    group_by(year, area_id, scenario, strategy, file) %>% 
    summarise(cost = sum(cost, na.rm = TRUE),
              aggregate_demand = sum(aggregate_demand, na.rm = TRUE), # how much do we need nationally
              #average_demand = mean(demand, na.rm = TRUE),
              capacity = sum(capacity, na.rm = TRUE),
              aggregate_capacity = sum(aggregate_capacity, na.rm = TRUE), # what is the national requirement
              capacity_deficit = sum(capacity_deficit, na.rm = TRUE),
              aggregate_capacity_deficit = sum(aggregate_capacity_deficit, na.rm = TRUE),
              population = sum(population, na.rm = TRUE),
              area = sum(area, na.rm = TRUE)) %>%
    mutate(pop_density = population / area, 
           demand_density = aggregate_demand / area) %>%
    select(year, scenario, strategy, area_id, cost, aggregate_demand, capacity, aggregate_capacity,
           capacity_deficit, aggregate_capacity_deficit, population, area, pop_density, demand_density, file)
}

all_scenarios <- data_demand_func(all_scenarios)

remove(empty_df, import_function, data_demand_func, metric_files)

###################################################################################
#### DEMAND VISUALISATION
###################################################################################

myvars <- c("year", "area_id", "demand_density", "scenario") 
subset <- all_scenarios[myvars]

names(subset)[names(subset) == 'area_id'] <- 'id'

subset <- subset[which(subset$scenario=="pop-base" | 
                         subset$scenario=="pop-0-unplanned" |
                         subset$scenario=="pop-1-new-cities" |
                         subset$scenario=="pop-2-expansion" ),]

subset <- subset[duplicated(subset),]

subset$scenario = factor(subset$scenario, levels=c("pop-base",
                                                   "pop-0-unplanned",
                                                   "pop-1-new-cities",
                                                   "pop-2-expansion"))

subset$demand_density <- round(subset$demand_density, 0)
subset$demand_density <- cut_number(subset$demand_density, 10)

subset <- subset[
  order( subset$year, subset$scenario ),
  ]

scenario_names <- c('pop-base' = 'Baseline',
                    'pop-0-unplanned' = 'Unplanned',
                    'pop-1-new-cities' = 'New Cities',
                    'pop-2-expansion' = 'Expansion') 

year_labels <- c(
  `2015` = "2015",
  `2020` = "2020", 
  `2030` = "2030", 
  `2050` = "2050")

setwd(shapes_directory)
all.shp <- readShapeSpatial("lad_uk_2016-12.shp") 
all.shp <- fortify(all.shp, region = "name")

print(head(all.shp))
names(subset)[names(subset) == 'area_id'] <- 'id'
all.shp<-merge(all.shp, subset, by="id")
all.shp <- all.shp[order(all.shp$order),]

demand <- ggplot() + geom_polygon(data = all.shp, aes(x = long, y = lat, group=group, fill = demand_density)) + coord_equal() +
  scale_fill_brewer(palette="Spectral", name = expression('Demand\nDensity\n(Mbps km'^2*')'),direction=-1, drop = FALSE) + 
  theme(axis.text = element_blank(), axis.ticks = element_blank(), axis.title = element_blank(), legend.position = "bottom") +
  guides(fill = guide_legend(reverse = FALSE)) + labs(title = 'Demand Growth by Scenario') + 
  facet_grid(scenario ~ year, labeller = labeller(scenario = scenario_names, year = year_labels))

### EXPORT TO FOLDER 
setwd(output_directory)
tiff('demand.tiff', units="in", width=12, height=10, res=400)
print(demand)
dev.off()

###################################################################################
#### INTERVENTION VISUALISATION
###################################################################################

capacity_func <- function (data, 
                           scenario_1, scenario_1_name,  
                           scenario_2, scenario_2_name,  
                           scenario_3, scenario_3_name,
                           scenario_4, scenario_4_name,
                           figure_title)  {
  
  myvars <- c("year", "area_id", "capacity_deficit", "file")
  subset <- all_scenarios[myvars]
  
  names(subset)[names(subset) == 'area_id'] <- 'id'
  
  subset <- subset[which(subset$file== scenario_1 |
                           subset$file== scenario_2 |
                           subset$file== scenario_3 |
                           subset$file== scenario_4),]

  subset$scenario = factor(subset$file, levels=c(scenario_1, scenario_2, scenario_3, scenario_4))
  
  subset$capacity_deficit <- round(subset$capacity_deficit, 0)
  #subset$capacity_deficit <- cut_number(subset$capacity_deficit, n=10, dig.lab=10)
  
  breaks <- c(-Inf, -200, -150, -100, -50, 0, 50, 100, 150, 200, Inf)
  
  subset$capacity_deficit <- cut(subset$capacity_deficit, breaks, dig.lab=10)
  
  setwd(shapes_directory)
  all.shp <- readShapeSpatial("lad_uk_2016-12.shp") 
  all.shp <- fortify(all.shp, region = "name")
  
  names(subset)[names(subset) == 'area_id'] <- 'id'
  all.shp<-merge(all.shp, subset, by="id")
  all.shp <- all.shp[order(all.shp$order),]

  ggplot() + geom_polygon(data = all.shp, aes(x = long, y = lat, group=group, fill = capacity_deficit), color = "black", size = 0.1) + 
    coord_equal() + 
    scale_fill_brewer(palette="Spectral", name = expression('\nCapacity\nMargin\n(Mbps km'^2*')'), drop = FALSE) +
    theme(axis.text = element_blank(), axis.ticks = element_blank(), axis.title = element_blank(), legend.position = "right") +
    guides(fill = guide_legend(reverse = TRUE)) + labs(title = figure_title) +
    facet_grid(scenario ~ year, labeller = labeller(scenario = scenario_names, year = year_labels)) 
}

scenario_names <- c("metrics_pop-base_throughput-base_strategy-macro-densification.csv" = 'Baseline',
                    "metrics_pop-0-unplanned_throughput-base_strategy-macro-densification.csv" = 'Unplanned',
                    "metrics_pop-1-new-cities_throughput-base_strategy-macro-densification.csv" = 'New Cities',
                    "metrics_pop-2-expansion_throughput-base_strategy-macro-densification.csv" = 'Expansion') 

year_labels <- c(
  `2015` = "2015",
  `2020` = "2020", 
  `2030` = "2030", 
  `2050` = "2050")

densification <- capacity_func(all_scenarios, 
                                         "metrics_pop-base_throughput-base_strategy-macro-densification.csv", "Baseline",
                                         "metrics_pop-0-unplanned_throughput-base_strategy-macro-densification.csv", "Unplanned",                                         
                                         "metrics_pop-1-new-cities_throughput-base_strategy-macro-densification.csv", "New Cities",
                                         "metrics_pop-2-expansion_throughput-base_strategy-macro-densification.csv", "Expansion",
                                         "Macrocell Densification")
### EXPORT TO FOLDER 
setwd(output_directory)
tiff('densification.tiff', units="in", width=12, height=10, res=400)
print(densification)
dev.off()


scenario_names <- c("metrics_pop-base_throughput-base_strategy-sectorisation.csv" = 'Baseline',
                    "metrics_pop-0-unplanned_throughput-base_strategy-sectorisation.csv" = 'Unplanned',
                    "metrics_pop-1-new-cities_throughput-base_strategy-sectorisation.csv" = 'New Cities',
                    "metrics_pop-2-expansion_throughput-base_strategy-sectorisation.csv" = 'Expansion') 

year_labels <- c(
  `2015` = "2015",
  `2020` = "2020", 
  `2030` = "2030", 
  `2050` = "2050")

sectorisation <- capacity_func(all_scenarios, 
                               "metrics_pop-base_throughput-base_strategy-sectorisation.csv", "Baseline",
                               "metrics_pop-0-unplanned_throughput-base_strategy-sectorisation.csv", "Unplanned",                                         
                               "metrics_pop-1-new-cities_throughput-base_strategy-sectorisation.csv", "New Cities",
                               "metrics_pop-2-expansion_throughput-base_strategy-sectorisation.csv", "Expansion",
                               "Increased Sectorisation")
### EXPORT TO FOLDER 
setwd(output_directory)
tiff('sectorisation.tiff', units="in", width=12, height=10, res=400)
print(sectorisation)
dev.off()



#### Spectrum Intervention 700 3500 ###
scenario_names <- c("metrics_pop_high_throughput_high_strategy_macrocell.csv" = "High demand",
                    "metrics_pop_base_throughput_base_strategy_macrocell.csv" = "Baseline demand",
                    "metrics_pop_low_throughput_low_strategy_macrocell.csv" = "Low demand")

spectrum_integration_capacity_margin <- capacity_func(all_scenarios, 
                                                      "metrics_pop_high_throughput_high_strategy_macrocell.csv", "High demand",
                                                      "metrics_pop_base_throughput_base_strategy_macrocell.csv", "Baseline demand",
                                                      "metrics_pop_low_throughput_low_strategy_macrocell.csv", "Low demand",
                                                      "Spectrum Integration Strategy")

### EXPORT TO FOLDER
#setwd("~/Dropbox/Digital Comms - Cambridge data/visualisation/figures")
#tiff('700_3500_spectrum_capacity_margin_15pc.tiff', units="in", width=10, height=10, res=300)
#print(spectrum_integration_capacity_margin)
#dev.off()

#### Spectrum Intervention 700 ###
#scenario_names <- c("metrics_pop_high_throughput_high_strategy_macrocell_700.csv" = "High demand",
#                    "metrics_pop_base_throughput_base_strategy_macrocell_700.csv" = "Baseline demand",
#                    "metrics_pop_low_throughput_low_strategy_macrocell_700.csv" = "Low demand")

#macrocell_700_capacity_margin <- capacity_func(all_scenarios, 
#                                           "metrics_pop_high_throughput_high_strategy_macrocell_700.csv", "High demand",
#                                           "metrics_pop_base_throughput_base_strategy_macrocell_700.csv", "Baseline demand",
#                                           "metrics_pop_low_throughput_low_strategy_macrocell_700.csv", "Low demand",
#                                           "700 MHz Spectrum Integration")

### EXPORT TO FOLDER
#setwd("~/Dropbox/Digital Comms - Cambridge data/visualisation/figures")
#tiff('700_capacity_margin_15pc.tiff', units="in", width=10, height=10, res=300)
#print(macrocell_700_capacity_margin)
#dev.off()

#### Small Cell Deployment ####
scenario_names <- c("metrics_pop_high_throughput_high_strategy_small_cell.csv" = "High demand",
                    "metrics_pop_base_throughput_base_strategy_small_cell.csv" = "Baseline demand",
                    "metrics_pop_low_throughput_low_strategy_small_cell.csv" = "Low demand")

small_cell_capacity_margin <- capacity_func(all_scenarios, 
                                            "metrics_pop_high_throughput_high_strategy_small_cell.csv", "High demand",
                                            "metrics_pop_base_throughput_base_strategy_small_cell.csv", "Baseline demand",
                                            "metrics_pop_low_throughput_low_strategy_small_cell.csv", "Low demand",
                                            "Small Cell Deployment")

### EXPORT TO FOLDER
#setwd("~/Dropbox/Digital Comms - Cambridge data/visualisation/figures")
#tiff('small_cell_capacity_margin_15pc.tiff', units="in", width=10, height=10, res=300)
#print(small_cell_capacity_margin)
#dev.off()

####  Hybrid Deployment Strategy ####
scenario_names <- c("metrics_pop_high_throughput_high_strategy_small_cell_and_spectrum.csv" = "High demand",
                    "metrics_pop_base_throughput_base_strategy_small_cell_and_spectrum.csv" = "Baseline demand",
                    "metrics_pop_low_throughput_low_strategy_small_cell_and_spectrum.csv" = "Low demand")

hybrid_capacity_margin <- capacity_func(all_scenarios, 
                                        "metrics_pop_high_throughput_high_strategy_small_cell_and_spectrum.csv", "High demand",
                                        "metrics_pop_base_throughput_base_strategy_small_cell_and_spectrum.csv", "Baseline demand",
                                        "metrics_pop_low_throughput_low_strategy_small_cell_and_spectrum.csv", "Low demand",
                                        "Hybrid Deployment Strategy")

### EXPORT TO FOLDER
#setwd("~/Dropbox/Digital Comms - Cambridge data/visualisation/figures")
#tiff('hybrid_capacity_margin_15pc.tiff', units="in", width=10, height=10, res=300)
#print(hybrid_capacity_margin)
#dev.off()

###IMPORT DATA###
setwd("~/Dropbox/Digital Comms - Mobile/outputs")

#get list of all filenames for metric files
metric_files_A <- list.files("~/Dropbox/Digital Comms - Mobile/outputs", pattern = c("(low|base|high).+\\1"))
metric_files_B <- list.files("~/Dropbox/Digital Comms - Mobile/outputs", pattern = c("(static2017.*base)"))

metric_files <- append(metric_files_A, metric_files_B)
rm(metric_files_A, metric_files_B)

#subset those metric files
metric_files <- metric_files[grep("^pcd_metrics.*", metric_files)]

#initialised empty dataframe
empty_df <- data.frame(year=numeric(),
                       postcode=character(), 
                       cost=numeric(),
                       demand=numeric(),
                       capacity=numeric(),
                       capacity_deficit=numeric(),
                       population=numeric(),
                       pop_density= numeric()) 

import_function = lapply(metric_files, function(x) {
  DF <- read.csv(x, header = T, sep = ",")
  DF_Merge <- merge(empty_df, DF, all = T)
  DF_Merge$file <- as.factor(x)
  return(DF_Merge)})

all_scenarios <- do.call(rbind, import_function)

all_scenarios$area <-  all_scenarios$population / all_scenarios$pop_density #in persons per km^2
all_scenarios$aggregate_demand <- (all_scenarios$demand * all_scenarios$area) #in Mbps still
all_scenarios$aggregate_capacity <-  (all_scenarios$capacity * all_scenarios$area) #in Mbps still
all_scenarios$aggregate_capacity_deficit <- (all_scenarios$capacity_deficit * all_scenarios$area) #in Mbps still

# Urban
all_scenarios$geotype [all_scenarios$pop_density >= 7959 ] <- "Urban"
# Suburban 1
all_scenarios$geotype [all_scenarios$pop_density >= 3119 & all_scenarios$pop_density < 7959 ] <- "Suburban 1"
# Suburban 2
all_scenarios$geotype [all_scenarios$pop_density >= 782 & all_scenarios$pop_density < 3119 ] <- "Suburban 2"
# Rural 1
all_scenarios$geotype [all_scenarios$pop_density >= 112 & all_scenarios$pop_density < 782 ] <- "Rural 1"
# Rural 2
all_scenarios$geotype [all_scenarios$pop_density >= 47 & all_scenarios$pop_density < 112 ] <- "Rural 2"
# Rural 3
all_scenarios$geotype [all_scenarios$pop_density >= 25 & all_scenarios$pop_density < 47 ] <- "Rural 3"
# Rural 4
all_scenarios$geotype [all_scenarios$pop_density >= 0.001 & all_scenarios$pop_density < 25 ] <- "Rural 4"

spending <- aggregate (. ~ file + year + geotype, FUN=sum, data=all_scenarios)

spending$postcode <- NULL
spending$pop_density <- NULL

spending <- spending[!grepl('static', spending$file),]
spending <- spending[!grepl('700', spending$file),]

spending$file = factor(spending$file, levels=c("pcd_metrics_pop_high_throughput_high_strategy_minimal.csv",
                                               "pcd_metrics_pop_high_throughput_high_strategy_macrocell.csv",
                                               "pcd_metrics_pop_high_throughput_high_strategy_small_cell.csv",
                                               "pcd_metrics_pop_high_throughput_high_strategy_small_cell_and_spectrum.csv",
                                               "pcd_metrics_pop_base_throughput_base_strategy_minimal.csv",
                                               "pcd_metrics_pop_base_throughput_base_strategy_macrocell.csv",
                                               "pcd_metrics_pop_base_throughput_base_strategy_small_cell.csv",
                                               "pcd_metrics_pop_base_throughput_base_strategy_small_cell_and_spectrum.csv",
                                               "pcd_metrics_pop_low_throughput_low_strategy_minimal.csv",
                                               "pcd_metrics_pop_low_throughput_low_strategy_macrocell.csv",
                                               "pcd_metrics_pop_low_throughput_low_strategy_small_cell.csv",
                                               "pcd_metrics_pop_low_throughput_low_strategy_small_cell_and_spectrum.csv"))


#### scenario names  ###
scenario_names <- c("pcd_metrics_pop_high_throughput_high_strategy_minimal.csv" = "High, Minimum Intervention",
                    "pcd_metrics_pop_high_throughput_high_strategy_macrocell.csv" = "High, Spectrum Strategy",          
                    "pcd_metrics_pop_high_throughput_high_strategy_small_cell.csv" = "High, Small Cell Strategy",
                    "pcd_metrics_pop_high_throughput_high_strategy_small_cell_and_spectrum.csv" = "High, Hybrid Strategy",
                    "pcd_metrics_pop_base_throughput_base_strategy_minimal.csv" = "Baseline, Minimum Intervention",
                    "pcd_metrics_pop_base_throughput_base_strategy_macrocell.csv" = "Baseline, Spectrum Strategy",          
                    "pcd_metrics_pop_base_throughput_base_strategy_small_cell.csv" = "Baseline, Small Cell Strategy",
                    "pcd_metrics_pop_base_throughput_base_strategy_small_cell_and_spectrum.csv" = "Baseline, Hybrid Strategy",
                    "pcd_metrics_pop_low_throughput_low_strategy_minimal.csv" = "Low, Minimum Intervention",
                    "pcd_metrics_pop_low_throughput_low_strategy_macrocell.csv" = "Low, Spectrum Strategy",          
                    "pcd_metrics_pop_low_throughput_low_strategy_small_cell.csv" = "Low, Small Cell Strategy",
                    "pcd_metrics_pop_low_throughput_low_strategy_small_cell_and_spectrum.csv" = "Low, Hybrid Strategy")

spending$geotype = factor(spending$geotype, levels=c("Urban" = "Urban",
                                                     "Suburban 1" = "Suburban 1",          
                                                     "Suburban 2" = "Suburban 2",
                                                     "Rural 1" = "Rural 1",
                                                     "Rural 2" = "Rural 2",
                                                     "Rural 3" = "Rural 3",          
                                                     "Rural 4" = "Rural 4"))

spending_by_scenario <- ggplot(data=spending, aes(x=year, y=(cost/1000000000))) + 
  geom_bar(stat="identity", aes(fill=geotype)) + 
  scale_y_continuous(expand = c(0, 0), breaks=seq(0, 0.6, 0.2))  +
  scale_fill_brewer(palette="Spectral", name = expression('Geotype'), direction=-1, drop = FALSE) +                      
  ylab("Spending (Billions GBP)") + scale_x_continuous(expand = c(0, 0)) + 
  theme(legend.position = "bottom",
        axis.title.x=element_blank()) + 
  guides(fill = guide_legend(reverse = FALSE, nrow=1), colour = guide_legend(nrow = 1)) +
  facet_wrap(~file, nrow=3, labeller = labeller(file = scenario_names)) 


#spending$geotype <-  gsub("Suburban 1", "Suburban", spending$geotype)
#spending$geotype <-  gsub("Suburban 2", "Suburban", spending$geotype)
#spending$geotype <-  gsub("Rural 1", "Rural", spending$geotype)
#spending$geotype <-  gsub("Rural 2", "Rural", spending$geotype)
#spending$geotype <-  gsub("Rural 3", "Rural", spending$geotype)
#spending$geotype <-  gsub("Rural 4", "Rural", spending$geotype)

spending <- aggregate (. ~ file + year + geotype, FUN=sum, data=spending)

spending$file = factor(spending$file, levels=c("pcd_metrics_pop_high_throughput_high_strategy_minimal.csv",
                                               "pcd_metrics_pop_high_throughput_high_strategy_macrocell.csv",
                                               "pcd_metrics_pop_high_throughput_high_strategy_small_cell.csv",
                                               "pcd_metrics_pop_high_throughput_high_strategy_small_cell_and_spectrum.csv",
                                               "pcd_metrics_pop_base_throughput_base_strategy_minimal.csv",
                                               "pcd_metrics_pop_base_throughput_base_strategy_macrocell.csv",
                                               "pcd_metrics_pop_base_throughput_base_strategy_small_cell.csv",
                                               "pcd_metrics_pop_base_throughput_base_strategy_small_cell_and_spectrum.csv",
                                               "pcd_metrics_pop_low_throughput_low_strategy_minimal.csv",
                                               "pcd_metrics_pop_low_throughput_low_strategy_macrocell.csv",
                                               "pcd_metrics_pop_low_throughput_low_strategy_small_cell.csv",
                                               "pcd_metrics_pop_low_throughput_low_strategy_small_cell_and_spectrum.csv"))


capacity_margin_by_geotype <- ggplot(spending, aes(x=year, y=(aggregate_capacity_deficit/1000000))) + #convert Mbps to Tbps - double check units
  geom_bar(position="dodge", stat="identity", aes(fill=geotype)) + 
  coord_cartesian(ylim = c(-2.5, 6.75)) + scale_x_continuous(expand = c(0, 0)) + 
  scale_fill_brewer(palette="Spectral", name = expression('Geotype'), direction=-1) +
  facet_wrap(~ file, ncol = 4, labeller = labeller(file = scenario_names)) +
  labs(y = "Data Demand (Tbps)") + #title = "Capacity Margin for Urban, Suburban and Rural Areas by Scenario") 
  theme(legend.position = "bottom",
        axis.title.x=element_blank()) + 
  guides(fill = guide_legend(reverse = FALSE, nrow=1))

### EXPORT TO FOLDER
setwd("~/Dropbox/Digital Comms - Mobile/visualisation/figures")
tiff('capacity_margin_by_geotype.tiff', units="in", width=8.5, height=6, res=600)
print(capacity_margin_by_geotype)
dev.off()

write.csv(spending, "spending.csv")

#################################
### PER USER SPEED CALCULATIONS 
#################################

#divide total capacity by number of users (80%) and market share (30%), then multiply by the OBF of 20
all_scenarios$per_user_speed <- (all_scenarios$aggregate_capacity/((all_scenarios$population*0.8)*0.3))*20

all_scenarios <- all_scenarios[!grepl('static', all_scenarios$file),]
all_scenarios <- all_scenarios[!grepl('700', all_scenarios$file),]

aggregate_metrics_func <- function(mydata)
{
  mydata %>% 
    group_by(geotype, year, file) %>% 
    summarise(cost = sum(cost, na.rm = TRUE),
              aggregate_demand = sum(aggregate_demand, na.rm=TRUE),
              aggregate_capacity = sum(aggregate_capacity, na.rm = TRUE), # what is the national requirement
              aggregate_capacity_deficit = sum(aggregate_capacity_deficit, na.rm = TRUE),
              median_per_user_speed = median(per_user_speed, na.rm = TRUE),
              average_per_user_speed = mean(per_user_speed, na.rm = TRUE),
              population = sum(population, na.rm = TRUE),
              area = sum(area, na.rm = TRUE)) %>%
    mutate(pop_density = population / area, 
           demand_density = aggregate_demand / area,
           scenario = file) %>%
    select(year, geotype, cost, aggregate_demand, aggregate_capacity,
           aggregate_capacity_deficit, median_per_user_speed, average_per_user_speed, 
           population, area, pop_density, demand_density, scenario)
}

aggregate_scenario_metrics <- aggregate_metrics_func(all_scenarios)

aggregate_scenario_metrics <- select(aggregate_scenario_metrics, year, geotype, median_per_user_speed, scenario) 

aggregate_scenario_metrics$scenario = factor(aggregate_scenario_metrics$scenario, 
                                             levels=c("pcd_metrics_pop_high_throughput_high_strategy_minimal.csv",
                                                      "pcd_metrics_pop_high_throughput_high_strategy_macrocell.csv",
                                                      "pcd_metrics_pop_high_throughput_high_strategy_small_cell.csv",
                                                      "pcd_metrics_pop_high_throughput_high_strategy_small_cell_and_spectrum.csv",
                                                      "pcd_metrics_pop_base_throughput_base_strategy_minimal.csv",
                                                      "pcd_metrics_pop_base_throughput_base_strategy_macrocell.csv",
                                                      "pcd_metrics_pop_base_throughput_base_strategy_small_cell.csv",
                                                      "pcd_metrics_pop_base_throughput_base_strategy_small_cell_and_spectrum.csv",
                                                      "pcd_metrics_pop_low_throughput_low_strategy_minimal.csv",
                                                      "pcd_metrics_pop_low_throughput_low_strategy_macrocell.csv",
                                                      "pcd_metrics_pop_low_throughput_low_strategy_small_cell.csv",
                                                      "pcd_metrics_pop_low_throughput_low_strategy_small_cell_and_spectrum.csv"),
                                             labels=c('High, Minimum Intervention',
                                                      'High, Spectrum Strategy',
                                                      'High, Small Cell Strategy',
                                                      'High, Hybrid Strategy',
                                                      'Baseline, Minimum Intervention',
                                                      'Baseline, Spectrum Strategy',
                                                      'Baseline, Small Cell Strategy',
                                                      'Baseline, Hybrid Strategy',
                                                      'Low, Minimal Strategy',
                                                      'Low, Spectrum Strategy',
                                                      'Low, Small Cell Strategy',
                                                      'Low, Hybrid Strategy'))

aggregate_scenario_metrics$geotype = factor(aggregate_scenario_metrics$geotype, levels=c("Urban" = "Urban",
                                                                                         "Suburban 1" = "Suburban 1",          
                                                                                         "Suburban 2" = "Suburban 2",
                                                                                         "Rural 1" = "Rural 1",
                                                                                         "Rural 2" = "Rural 2",
                                                                                         "Rural 3" = "Rural 3",          
                                                                                         "Rural 4" = "Rural 4"))

median_per_user_speed <-  ggplot(aggregate_scenario_metrics, aes(x=year, y=median_per_user_speed, colour=geotype, group=geotype)) + 
  geom_line() +
  theme(legend.position = "bottom",
        axis.title.x=element_blank()) + 
  facet_wrap(~scenario) + 
  labs(title = "Change in Median Per User Speed by Strategy", colour = "Geotype", 
       y="Median Per User Speed (Mbps)", x="") +
  guides(fill = guide_legend(reverse = FALSE, nrow=1), colour = guide_legend(nrow = 1)) +
  scale_fill_brewer(palette="Spectral", name = expression('Geotype'), direction=-1, drop = FALSE) +
  facet_wrap(~scenario, nrow=3) 

### EXPORT TO FOLDER
setwd("~/Dropbox/Digital Comms - Mobile/visualisation/figures")
tiff('median_per_user_speed.tiff', units="in", width=8.5, height=6, res=600)
print(median_per_user_speed)
dev.off()

#################################
### IMPORT TECHNOLOGY COSTS
#################################

###IMPORT DATA###
setwd("~/Dropbox/Digital Comms - Mobile/outputs")
#setwd("C:/Users/oughtone/Dropbox/Digital Comms - Cambridge data/outputs")
#metric_files_A <- list.files("C:/Users/oughtone/Dropbox/Digital Comms - Cambridge data/outputs", pattern = c("(low|base|high).+\\1"))
#metric_files_B <- list.files("C:/Users/oughtone/Dropbox/Digital Comms - Cambridge data/outputs", pattern = c("(static2017.*base)"))

#get list of all filenames for metric files
metric_files_A <- list.files("~/Dropbox/Digital Comms - Mobile/outputs", pattern = c("(low|base|high).+\\1"))
metric_files_B <- list.files("~/Dropbox/Digital Comms - Mobile/outputs", pattern = c("(static2017.*base)"))

metric_files <- append(metric_files_A, metric_files_B)

rm(metric_files_A, metric_files_B)

#subset those metric files
metric_files <- metric_files[grep("^spend*", metric_files)]

#remove minimal files
metric_files <- metric_files[-grep("\\minimal.csv$", metric_files)]

#initialised empty dataframe
empty_df <- data.frame(year=numeric(),
                       pcd_sector=character(), 
                       lad=character(), 
                       item=character(),
                       cost=numeric()) 

import_function = lapply(metric_files, function(x) {
  DF <- read.csv(x, header = T, sep = ",")
  DF_Merge <- merge(empty_df, DF, all = T)
  DF_Merge$file <- as.factor(x)
  return(DF_Merge)})

all_scenarios <- do.call(rbind, import_function)

high_minimal <- read.csv('blank_spend_for_minimal_intervention.csv', header=TRUE, stringsAsFactors=FALSE)
high_minimal$file <- "spend_pop_high_throughput_high_strategy_minimal.csv"  
base_minimal <- read.csv('blank_spend_for_minimal_intervention.csv', stringsAsFactors=FALSE)
base_minimal$file <- "spend_pop_base_throughput_base_strategy_minimal.csv" 
low_minimal <- read.csv('blank_spend_for_minimal_intervention.csv', stringsAsFactors=FALSE)
low_minimal$file <- "spend_pop_low_throughput_low_strategy_minimal.csv" 

all_scenarios <- rbind(all_scenarios, high_minimal)
all_scenarios <- rbind(all_scenarios, base_minimal)
all_scenarios <- rbind(all_scenarios, low_minimal)

data_demand_func <- function(mydata)
{
  output_name <- mydata %>% 
    group_by(item, year, file) %>% 
    summarise(cost = sum(cost, na.rm = TRUE))%>%
    mutate(scenario = file) %>%
    select(cost, item, year, scenario)
}

all_scenarios <- data_demand_func(all_scenarios)

all_scenarios <- all_scenarios[!grepl('700', all_scenarios$scenario),]
all_scenarios <- all_scenarios[!grepl('static2017', all_scenarios$scenario),]

all_scenarios$scenario = factor(all_scenarios$scenario,  
                                levels=c('spend_pop_high_throughput_high_strategy_minimal.csv',
                                         'spend_pop_high_throughput_high_strategy_macrocell.csv',
                                         'spend_pop_high_throughput_high_strategy_small_cell.csv',
                                         'spend_pop_high_throughput_high_strategy_small_cell_and_spectrum.csv',
                                         'spend_pop_base_throughput_base_strategy_minimal.csv',
                                         'spend_pop_base_throughput_base_strategy_macrocell.csv',
                                         'spend_pop_base_throughput_base_strategy_small_cell.csv',
                                         'spend_pop_base_throughput_base_strategy_small_cell_and_spectrum.csv',
                                         'spend_pop_low_throughput_low_strategy_minimal.csv',                                           
                                         'spend_pop_low_throughput_low_strategy_macrocell.csv',
                                         'spend_pop_low_throughput_low_strategy_small_cell.csv',
                                         'spend_pop_low_throughput_low_strategy_small_cell_and_spectrum.csv'),
                                labels=c('High, Minimum Intervention',
                                         'High, Spectrum Strategy',
                                         'High, Small Cell Strategy',
                                         'High, Hybrid Strategy',
                                         'Baseline, Minimum Intervention',
                                         'Baseline, Spectrum Strategy',
                                         'Baseline, Small Cell Strategy',
                                         'Baseline, Hybrid Strategy',
                                         'Low, Minimal Strategy',
                                         'Low, Spectrum Strategy',
                                         'Low, Small Cell Strategy',
                                         'Low, Hybrid Strategy'))

all_scenarios$item = factor(all_scenarios$item, levels=c("upgrade_to_lte",
                                                         "carrier_700",          
                                                         "carrier_3500",
                                                         "small_cells"),
                            labels = c("Upgrade to LTE",
                                       "Integrate 700 MHz",          
                                       "Integrate 3500 MHz",
                                       "Small Cell Deployment"))

spending_by_tech <- ggplot(data=all_scenarios, aes(x=year, y=(cost/1000000000))) + 
  geom_bar(stat="identity", aes(fill=item))  + 
  scale_fill_brewer(palette="Spectral", name = expression('Technology'), direction=-1, drop = FALSE,
                    breaks=c("Upgrade to LTE", "Integrate 700 MHz", "Integrate 3500 MHz", "Small Cell Deployment")) +                      
  ylab("Spending (Billions GBP)") + scale_x_continuous(expand = c(0, 0)) + 
  scale_y_continuous(expand = c(0, 0), breaks=seq(0, 0.6, 0.2)) +
  theme(legend.position = "bottom", axis.title.x=element_blank()) + guides(fill = guide_legend(reverse = FALSE)) +
  facet_wrap(~scenario, nrow=3) 

### EXPORT TO FOLDER
# setwd("~/Dropbox/Digital Comms - Mobile/visualisation/figures")
# tiff('spending_by_tech.tiff', units="in", width=10, height=10, res=300)
# print(spending_by_tech)
# dev.off()

################################################################################
####### GGARRANGE #########
################################################################################

demand_graphic <- ggarrange(ggarrange(population,
                                      aggregate_demand,nrow=2, 
                                      labels=NULL, 
                                      heights = c(1,1), align = "v"), demand,
                            labels =NULL, 
                            ncol=2, 
                            widths = c(1,1.5), 
                            align = "v")

### EXPORT TO FOLDER
setwd("~/Dropbox/Digital Comms - Mobile/visualisation/figures")
tiff('demand_graphic.tiff', units="in", width=8.5, height=8.5, res=500)
print(demand_graphic)
dev.off()

#ggarrange(population, aggregate_demand, Gini_time_series + rremove("x.text"), 
#          labels = c("A", "B", "C"),
#          ncol = 2, nrow = 2)

capacity_margin_panal_plot <- ggarrange(minimal_capacity_margin, 
                                        spectrum_integration_capacity_margin,
                                        small_cell_capacity_margin,
                                        hybrid_capacity_margin + 
                                          rremove("x.text"), common.legend = TRUE, 
                                        ncol = 2, nrow = 2,
                                        legend = "bottom")

### EXPORT TO FOLDER
setwd("~/Dropbox/Digital Comms - Mobile/visualisation/figures")
tiff('capacity_margin_panal_plot.tiff', units="in", width=8.5, height=12, res=400)
print(capacity_margin_panal_plot)
dev.off()

annual_spending <- ggarrange(spending_by_scenario, 
                             spending_by_tech, 
                             labels="AUTO",
                             ncol = 1, nrow = 2)

### EXPORT TO FOLDER
setwd("~/Dropbox/Digital Comms - Mobile/visualisation/figures")
tiff('annual_spending.tiff', units="in", width=8.5, height=12, res=500)
print(annual_spending)
dev.off()


