###VISUALISE MODEL OUTPUTS###
library(tidyverse)
library(maptools)
library(rgeos)
library(Cairo)
library(rgdal)
library(ggmap)
library(scales)
library(RColorBrewer)
library(ggpubr)       

set.seed(8000)

base_directory <- "D:\\Github\\digital_comms\\data"
data_directory <- "D:\\Github\\digital_comms\\results\\mobile_outputs"
shapes_directory <- "D:\\Github\\digital_comms\\data\\raw\\d_shapes"
output_directory <- "D:\\Github\\digital_comms\\data_visualisation\\tprc_2019"

############################


postcode_data <- read.csv(file.path(base_directory, 'processed', 'final_processed_sites.csv'))

postcode_data <- unique(postcode_data)

test <- postcode_data %>%
        group_by(lad) %>%
        summarise (mean(target))



setwd(file.path(shapes_directory, 'datashare_pcd_sectors'))

all.shp <- readOGR(dsn=file.path(shapes_directory, 'datashare_pcd_sectors'), "PostalSector") 
all.shp <- fortify(all.shp, region = "RMSect")

print(head(all.shp))
names(postcode_data)[names(postcode_data) == 'postcode'] <- 'id'
all.shp<-merge(all.shp, postcode_data, by="id")
all.shp <- all.shp[order(all.shp$order),]

ggplot() + geom_polygon(data = all.shp, aes(x = long, y = lat, group=group, fill = lte)) + coord_equal() +
  scale_fill_manual( values=c("red","blue"))
  theme(axis.text = element_blank(), axis.ticks = element_blank(), axis.title = element_blank(), legend.position = "bottom") +
  labs(title = 'Demand Growth by Scenario')




facet_grid(scenario ~ year, labeller = labeller(scenario = scenario_names, year = year_labels))

### EXPORT TO FOLDER 
setwd(output_directory)
tiff('demand.tiff', units="in", width=12, height=10, res=400)
print(demand)
dev.off()









############################################################
#### VISUALISE DATA - POPULATION PER SUBSTATION
############################################################

substation_results$Population <- round(substation_results$Population/1000000, 2)

substation_results$Population <-  cut(substation_results$Population, 
                                      breaks = c(0, 0.15, 0.3, 0.45, 0.6, 0.75, 0.9, 1.05),
                                      labels = c("<0.15", "0.15-0.3", "0.3-0.45", "0.45-0.6",
                                                 "0.6-0.75", "0.75-0.9",">0.9"))

substation_results_population <- unique(substation_results[c("Site.Code", "Population", "Easting", "Northing")])

substation_results_population <- na.omit(substation_results_population)

setwd("C:/users/edwar/Dropbox/UK Space Weather Analysis/LADs.2012/Simplified")
all.shp <- readShapeSpatial("simplified_LADS_no_shetland.shp") 

all.shp <- fortify(all.shp, region = "LAD12CD")

all.shp <- all.shp[order(all.shp$order),]

population_per_substation <- ggplot() + geom_polygon(data = all.shp, aes(x = long, y = lat, group=group), 
                                                     color = "grey", size = 0.3,fill = NA) +
  geom_point(data=substation_results_population, aes(x=Easting, y=Northing, size=factor(Population), 
                                                     colour=factor(Population), fill = NA), alpha=0.5) +
  coord_equal() + 
  scale_fill_brewer(palette="Spectral", name = expression('Voltage\nInstability\nZones')) +
  theme(axis.text = element_blank(), axis.ticks = element_blank(), axis.title = element_blank(), 
        legend.position = "right",legend.direction="vertical") +
  guides(fill = guide_legend(ncol=1,nrow=4,reverse = FALSE)) + 
  labs(title = "(A) Population Served\nPer Substation") +
  scale_colour_manual(name = "Population\nPer Node\n(Million)",
                      labels = c("<0.15", "0.15-0.3", "0.3-0.45", "0.45-0.6",
                                 "0.6-0.75", "0.75-0.9",">0.9"),
                      values = c("skyblue4", "blue", "green", "yellow", "orange", "red", "brown")) +   
  scale_size_manual(name = "Population\nPer Node\n(Million)",
                    labels = c("<0.15", "0.15-0.3", "0.3-0.45", "0.45-0.6",
                               "0.6-0.75", "0.75-0.9",">0.9"),
                    values = c(1, 2, 3, 4, 5, 6, 7))

### EXPORT TO FOLDER
setwd("C:/users/edwar/Dropbox/UK Space Weather Analysis/Figures")
tiff('population_per_substation.tiff', units="in", width=6, height=6, res=500)
print(population_per_substation)
dev.off()

rm(all.shp)

############################################################
#### VISUALISE GRID
############################################################

setwd("C:/users/edwar/Dropbox/UK Space Weather Analysis/LADs.2012/Simplified")
all.shp <- readShapeSpatial("simplified_LADS_no_shetland.shp") 

all.shp <- fortify(all.shp, region = "LAD12CD")

all.shp <- all.shp[order(all.shp$order),]

#import 275 kv network
setwd("C:/users/edwar/Dropbox/UK Space Weather Analysis/Grid/BGS Grid Model")
network <- readShapeSpatial("final_uk_grid.shp", IDvar = "id") 
network <- fortify(network, region = "id")
network$id <- as.numeric(network$id) 

data <- read.csv("final_uk_grid.csv")
data$id <- as.numeric(data$id) 
network <- merge(network, data, by=c('id'='id'), all.x=TRUE)

network <- network[order(network$order),]

grid_structure <- ggplot() + geom_polygon(data = all.shp, aes(x = long, y = lat, group=group), 
                                          color = "grey", size = 0.3,fill = NA) +
  geom_line(data = network, aes(x = long, y = lat, group=id, colour=factor(voltage)), size = 0.5) +
  coord_equal() + 
  scale_fill_brewer(palette="Spectral", name = expression('Voltage\nInstability\nZones')) +
  theme(axis.text = element_blank(), axis.ticks = element_blank(), axis.title = element_blank(), 
        legend.position = "right",legend.direction="vertical") +
  guides(fill = guide_legend(ncol=1,nrow=4,reverse = FALSE)) + 
  labs(title = "(B) UK High Voltage\nNetwork") +
  scale_colour_manual(name = "Line\nVoltage\n(kV)", values = c("blue", "Red")) 

### EXPORT TO FOLDER
setwd("C:/users/edwar/Dropbox/UK Space Weather Analysis/Figures")
tiff('grid_structure.tiff', units="in", width=6, height=6, res=500)
print(grid_structure)
dev.off()

############################################################
#### VISUALISE DATA - GIC PER SUBSTATION
############################################################

substation_coordinates <- select(substation_results, Site.Code, Easting, Northing)

substation_coordinates <- unique(substation_coordinates)

GIC_per_substation <- merge(GIC_per_substation, substation_coordinates, by='Site.Code')

setwd("C:/users/edwar/Dropbox/UK Space Weather Analysis/LADs.2012/Simplified")
all.shp <- readShapeSpatial("simplified_LADS_no_shetland.shp")

all.shp <- fortify(all.shp, region = "LAD12CD")

all.shp <- all.shp[order(all.shp$order),]

GIC_per_substation <- unique(GIC_per_substation)

GIC_per_substation$scenario = factor(GIC_per_substation$scenario, 
                                     levels=c("one_in_10", 
                                              "one_in_30",
                                              "one_in_100_x1.4",
                                              "one_in_500_x2.4",
                                              "one_in_1000_x3.1",
                                              "one_in_10000_x4.2"),
                                     labels=c( "1-in-10",
                                               "1-in-30",
                                               "1-in-100",
                                               "1-in-500",
                                               "1-in-1,000",                                                    
                                               "1-in-10,000"))

GIC_per_substation$current <-  cut(GIC_per_substation$current, 
                                   breaks = c(0, 25, 50, 75, 100, 125, 150, 175, Inf),
                                   labels = c("0-25", "25-50", "50-75", "75-100",
                                              "100-125", "125-150","150-175",">175"))

GIC_per_substation <- na.omit(GIC_per_substation)

GIC_per_substation_graphic <- ggplot() + geom_polygon(data = all.shp, aes(x = long, y = lat, group=group), 
                                                      color = "grey", size = 0.3,fill = NA) +
  geom_point(data=GIC_per_substation, aes(x=Easting, y=Northing, size=factor(current), 
                                          colour=factor(current), fill = NA), alpha=0.5) +
  coord_equal() + 
  scale_fill_brewer(palette="Spectral", name = expression('Voltage\nInstability\nZones')) +
  theme(axis.text = element_blank(), axis.ticks = element_blank(), axis.title = element_blank(), 
        legend.position = "right") +
  guides(fill = guide_legend(reverse = FALSE)) + 
  labs(title = "(B) Total GIC Per Substation (for all EHV transformers)") +
  scale_colour_manual(name = "Total GIC Per\nSubstation\n(Amperes)",
                      labels = c("0-25", "25-50", "50-75", "75-100",
                                 "100-125", "125-150","150-175",">175"),
                      values = c("skyblue4", "blue", "green", "yellow", "orange", "red", "brown", "black")) +   
  scale_size_manual(name = "Total GIC Per\nSubstation\n(Amperes)",
                    labels = c("0-25", "25-50", "50-75", "75-100",
                               "100-125", "125-150","150-175",">175"),
                    values = c(1, 2, 3, 4, 5, 6, 7, 8, 9)) +
  facet_wrap(~scenario, nrow=2)

### EXPORT TO FOLDER
setwd("C:/users/edwar/Dropbox/UK Space Weather Analysis/Figures")
tiff('GIC_per_substation_graphic.tiff', units="in", width=6, height=6, res=500)
print(GIC_per_substation_graphic)
dev.off()

#rm(all.shp, substation_coordinates)

############################################################
#### VISUALISE DATA - MAX GIC PER TRANSFORMER
############################################################

setwd("C:/users/edwar/Dropbox/UK Space Weather Analysis/LADs.2012/Simplified")
all.shp <- readShapeSpatial("simplified_LADS_no_shetland.shp") 

all.shp <- fortify(all.shp, region = "LAD12CD")

all.shp <- all.shp[order(all.shp$order),]

site_coordinates <- select(substation_results, Site.Code, Easting, Northing)

site_coordinates <- unique(site_coordinates)

max_GIC_per_transformer <- merge(max_GIC_per_transformer, site_coordinates, by='Site.Code')

max_GIC_per_transformer$scenario = factor(max_GIC_per_transformer$scenario, 
                                          levels=c("one_in_10", 
                                                   "one_in_30",
                                                   "one_in_100_x1.4",
                                                   "one_in_500_x2.4",
                                                   "one_in_1000_x3.1",
                                                   "one_in_10000_x4.2"),
                                          labels=c( "1-in-10",
                                                    "1-in-30",
                                                    "1-in-100",
                                                    "1-in-500",
                                                    "1-in-1,000",                                                    
                                                    "1-in-10,000"))

max_GIC_per_transformer$current <-  cut(max_GIC_per_transformer$current, 
                                        breaks = c(0, 20, 40, 60, 80, 100, 120, 140, Inf),
                                        labels = c("0-20", "20-40", "40-60", "60-80",
                                                   "80-100", "100-120","120-140",">140"))

max_GIC_per_transformer <- na.omit(max_GIC_per_transformer)

max_GIC_per_transformer <- ggplot() + geom_polygon(data = all.shp, aes(x = long, y = lat, group=group), 
                                                   color = "grey", size = 0.3,fill = NA) +
  geom_point(data=max_GIC_per_transformer, aes(x=Easting, y=Northing, size=factor(current), 
                                               colour=factor(current), fill = NA), alpha=0.5) +
  coord_equal() + 
  scale_fill_brewer(palette="Spectral", name = expression('Voltage\nInstability\nZones')) +
  theme(axis.text = element_blank(), axis.ticks = element_blank(), axis.title = element_blank(), 
        legend.position = "right") +
  guides(fill = guide_legend(reverse = FALSE)) + 
  labs(title = "(A) Max GIC Per EHV Transformer Phase") +
  scale_colour_manual(name = "Max GIC Per\nTransformer\nPhase\n(Amperes)",
                      labels = c("0-20", "20-40", "40-60", "60-80",
                                 "80-100", "100-120","120-140",">140"),
                      values = c("skyblue4", "blue", "green", "yellow", "orange", "red", "brown", "black")) +   
  scale_size_manual(name = "Max GIC Per\nTransformer\nPhase\n(Amperes)",
                    labels = c("0-20", "20-40", "40-60", "60-80",
                               "80-100", "100-120","120-140",">140"),
                    values = c(1, 2, 3, 4, 5, 6, 7, 8)) +
  facet_wrap(~scenario, nrow=2)

### EXPORT TO FOLDER
setwd("C:/users/edwar/Dropbox/UK Space Weather Analysis/Figures")
tiff('max_GIC_per_transformer.tiff', units="in", width=6, height=6, res=500)
print(max_GIC_per_transformer)
dev.off()

rm(all.shp)

############################################################
#### GGARRANGE OUTPUTS
############################################################

pop_and_transformer_plot <- ggarrange(population_per_substation, 
                                      grid_structure,
                                      transformer_count_per_substation,
                                      EHV_transformer_count_per_substation,
                                      align = c("hv"), nrow = 2, ncol = 2)

### EXPORT TO FOLDER
setwd("C:/users/edwar/Dropbox/UK Space Weather Analysis/Figures")
tiff('pop_and_transformer_plot.tiff', units="in", width=7, height=8, res=500)
print(pop_and_transformer_plot)
dev.off()

GIC_plot <- ggarrange(max_GIC_per_transformer,
                      GIC_per_substation_graphic,
                      align = c("v"), 
                      nrow=2, ncol=1)

### EXPORT TO FOLDER
setwd("C:/users/edwar/Dropbox/UK Space Weather Analysis/Figures")
tiff('GIC_plot.tiff', units="in", width=8, height=12, res=500)
print(GIC_plot)
dev.off()










############################

































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

all_scenarios$aggregate_demand <- (all_scenarios$demand * all_scenarios$area) #in Mbps still
all_scenarios$aggregate_capacity <-  (all_scenarios$capacity * all_scenarios$area) #in Mbps still
all_scenarios$aggregate_capacity_deficit <- (all_scenarios$capacity_deficit * all_scenarios$area) #in Mbps still

all_scenarios <- all_scenarios %>% separate(file, c("file_type", "scenario", "throughput", "strategy"), "_", remove = FALSE)