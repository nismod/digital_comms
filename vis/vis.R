###VISUALISE MODEL OUTPUTS###
#install.packages("tidyverse")
library(tidyverse)
# library(dplyr)
#install.packages("maptools")
library(maptools)
#install.packages("rgeos")
library(rgeos)
# install.packages("maps")
library(maps)
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
# install.packages("arules")
library(arules)
# install.packages("ggpolypath")
library(ggpolypath)

data_input_directory <- "D:\\Github\\digital_comms\\data\\raw\\b_mobile_model"
data_directory <- "D:\\Github\\digital_comms\\results\\mobile_outputs"
shapes_directory <- "D:\\Github\\digital_comms\\data\\raw\\d_shapes\\lad_uk_2016-12"
output_directory <- "D:\\Github\\digital_comms\\vis\\figures"

setwd(data_directory)

metric_files <- list.files(data_directory, pattern="*.csv")

#subset those metric files
metric_files <- metric_files[grep("^metrics.*", metric_files)]

#initialised empty dataframe
empty_df <- data.frame(year=numeric(),
                       area_id=character(), 
                       area_name=character(), 
                       area=numeric(),
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

all_scenarios <- all_scenarios[which(
  all_scenarios$area_id== 'E06000031' |
    all_scenarios$area_id== 'E07000005' |
    all_scenarios$area_id== 'E07000006' |
    all_scenarios$area_id== 'E07000007' |
    all_scenarios$area_id== 'E06000032' |
    all_scenarios$area_id== 'E06000042' |
    all_scenarios$area_id== 'E06000055' |
    all_scenarios$area_id== 'E06000056' |
    all_scenarios$area_id== 'E07000004' |
    all_scenarios$area_id== 'E07000008' |
    all_scenarios$area_id== 'E07000009' |
    all_scenarios$area_id== 'E07000010' |
    all_scenarios$area_id== 'E07000011' |
    all_scenarios$area_id== 'E07000012' |
    all_scenarios$area_id== 'E07000150' |
    all_scenarios$area_id== 'E07000151' |
    all_scenarios$area_id== 'E07000152' |
    all_scenarios$area_id== 'E07000153' |
    all_scenarios$area_id== 'E07000154' |
    all_scenarios$area_id== 'E07000155' |
    all_scenarios$area_id== 'E07000156' |
    all_scenarios$area_id== 'E07000177' |
    all_scenarios$area_id== 'E07000178' |
    all_scenarios$area_id== 'E07000179' |
    all_scenarios$area_id== 'E07000180' |
    all_scenarios$area_id== 'E07000181' 
),]

all_scenarios <- all_scenarios %>% separate(file, c("file_type", "scenario", "data_scenario", "strategy"), "_", remove = FALSE)
all_scenarios$aggregate_demand <- (all_scenarios$demand * all_scenarios$area) #in Mbps still
all_scenarios$aggregate_capacity <-  (all_scenarios$capacity * all_scenarios$area) #in Mbps still
all_scenarios$aggregate_capacity_deficit <- (all_scenarios$capacity_deficit * all_scenarios$area) #in Mbps still


all_scenarios$scenario = factor(all_scenarios$scenario, levels=c("base",
                                                                 "0-unplanned",
                                                                 "1-new-cities-from-dwellings",
                                                                 "2-expansion",
                                                                 "3-new-cities23-from-dwellings",
                                                                 "4-expansion23"),
                                labels=c("Baseline",
                                         "Unplanned",
                                         "New Cities",
                                         "Expansion",
                                         "New Cities 23k",
                                         "Expansion 23k"))

all_scenarios$data_scenario = factor(all_scenarios$data_scenario, levels=c("low",
                                                                           "base",
                                                                           "high"),
                                     labels=c("Low",
                                              "Baseline",
                                              "High"))

all_scenarios$strategy = factor(all_scenarios$strategy, levels=c("minimal.csv",
                                                                 "macrocell.csv",
                                                                 "small-cell-and-spectrum.csv",
                                                                 "small-cell.csv"),
                                labels=c("No Investment",
                                         "Spectrum Integration",
                                         "Small Cells",
                                         "Spectrum and Small Cells"))

just_scenarios <- all_scenarios[which(all_scenarios$data_scenario == 'Baseline'),]


# test <-  data.frame(
#   area_id=c(rep(c("London","New York"),each=1)),
#   year=c(rep(c("2020","2021"),each=2)),
#   strategy=c(rep(c("A","B"),each=4)),
#   scenario=c(rep(c("baseline","s1", "s2"),each=8)),
#   metric=(rep(c(1, 2, 3),each=8))
# )
# 

results = (
  just_scenarios %>% 
    group_by(area_id, year, strategy) %>% 
    mutate(
      demand_baseline = demand[scenario=='Baseline'], demand_difference = demand - demand_baseline,
      capacity_baseline = capacity[scenario=='Baseline'], capacity_difference = capacity - capacity_baseline,
      capacity_deficit_baseline = capacity_deficit[scenario=='Baseline'], capacity_deficit_difference = capacity_deficit - capacity_deficit_baseline,
      cost_baseline = cost[scenario=='Baseline'], cost_difference = cost - cost_baseline,
    )
)

#################################
### Aggregate Metrics
#################################


aggregate_metrics_func <- function(mydata)
{
  mydata %>% 
    
    group_by(scenario, data_scenario, strategy, year) %>% 
    
    summarise(cost_m = round(sum(cost, na.rm = TRUE)/1000000,1),
              aggregate_demand_gbps = round(sum(aggregate_demand, na.rm = TRUE)/1000,1), 
              # capacity = sum(capacity, na.rm = TRUE),
              aggregate_capacity_gbps = round(sum(aggregate_capacity, na.rm = TRUE)/1000,1), 
              #capacity_deficit = sum(capacity_deficit, na.rm = TRUE),
              aggregate_capacity_deficit_gbps = round(sum(aggregate_capacity_deficit, na.rm = TRUE)/1000,1),
              population = sum(population, na.rm = TRUE),
              area = sum(area, na.rm = TRUE)) %>%
    
    mutate(pop_density_km2 = population / area, 
           demand_density_mbps_km2 = round((aggregate_demand_gbps*1000) / area,1),
           capacity_density_mbps_km2 = round((aggregate_capacity_gbps*1000) / area,1),
           capacity_margin_density_mbps_km2 = round((aggregate_capacity_deficit_gbps*1000) / area,1),
           
           mean_capacity_per_person_market_share_25 = round(
             (aggregate_capacity_gbps*1000) / ((pop_density_km2*area) * 0.25 / 50),1)
    ) %>%
    
    select(scenario, data_scenario, strategy, year, cost_m, aggregate_demand_gbps, aggregate_capacity_gbps,
           aggregate_capacity_deficit_gbps, population, area, 
           pop_density_km2, demand_density_mbps_km2, capacity_density_mbps_km2, capacity_margin_density_mbps_km2,
           mean_capacity_per_person_market_share_25)
}

aggregate_scenario_metrics <- aggregate_metrics_func(all_scenarios)

aggregate_scenario_metrics <- aggregate_scenario_metrics[which(aggregate_scenario_metrics$data_scenario== 'Baseline'), ]

results <- (
  aggregate_scenario_metrics %>% 
    group_by(year, strategy) %>% 
    mutate(
      # demand_baseline = demand[scenario=='Baseline'], demand_difference = demand - demand_baseline,
      # capacity_baseline = capacity[scenario=='Baseline'], capacity_difference = capacity - capacity_baseline,
      # capacity_deficit_baseline = capacity_deficit[scenario=='Baseline'], capacity_deficit_difference = capacity_deficit - capacity_deficit_baseline,
      mean_capacity_per_person_baseline = mean_capacity_per_person_market_share_25[scenario=='Baseline'], mean_capacity_per_person_difference = mean_capacity_per_person_market_share_25 - mean_capacity_per_person_baseline,
      cost_baseline = cost_m[scenario=='Baseline'], cost_difference = cost_m - cost_baseline,
    )
)

results <- results[
  with(results, order(scenario, data_scenario, strategy, year)),
  ]

results$mean_capacity_per_person_difference[results$mean_capacity_per_person_difference > 0] <- 0
results$cost_difference[results$cost_difference < 0] <- 0

results <- results %>%
  group_by(scenario, data_scenario, strategy) %>%
  mutate(
    cost_baseline_cumsum = cumsum(cost_baseline),
    cost_difference_cumsum = cumsum(cost_difference))

baseline_data <- results[which(results$scenario== 'Baseline'), ]


cols <- c("Baseline" = "#999999", "Unplanned" = "#E69F00", "New Cities" = "#56B4E9", 
          "Expansion" = "#009E73", "New Cities 23k" = "#F0E442", "Expansion 23k" = "#0072B2")

linetypes <- c("Baseline" = "solid",
               "Unplanned" = "longdash",
               "New Cities" = "dotdash",
               "Expansion" = "dotted",
               "New Cities 23k" = "dashed",
               "Expansion 23k" = "twodash")

baseline_user_capacity <- ggplot(baseline_data, aes(x=as.factor(year), y=mean_capacity_per_person_baseline, 
                                                    group=scenario, colour=scenario, linetype=scenario)) + expand_limits(y = 0) + 
  geom_line(size=0.8) + facet_grid(cols = vars(strategy)) +
  scale_color_manual(values = cols, drop = FALSE) +
  scale_linetype_manual(values=linetypes, drop = FALSE) +
  theme(legend.title = element_blank(),
        legend.text = element_text(size = 9),
        legend.position = "bottom",
        plot.title = element_text(size=9),
        axis.title.x=element_blank(),
        axis.text.x = element_text(angle = 45, hjust = 1, size = 7),
        axis.text=element_text(size=9),
        axis.title=element_text(size=9),
        strip.text = element_text(size = 9)) +
  labs(y = "Mean Cell Edge\nUser Capacity (Mbps)", x = "Year", 
       title = "Baseline Mean Cell Edge User Capacity (90% reliability)") +
  guides(colour=guide_legend(ncol=6)) 

baseline_cost <- (ggplot(baseline_data, aes(x=as.factor(year), y=cost_baseline_cumsum, 
                                            group=scenario, colour=scenario, linetype = scenario)) + expand_limits(y = 0) + 
                    geom_line(size=0.8) + facet_grid(cols = vars(strategy)) +
                    scale_color_manual(values = cols, drop = FALSE) +
                    scale_linetype_manual(values=linetypes, drop = FALSE) +
                    theme(legend.title = element_blank(),
                          legend.text = element_text(size = 9),
                          legend.position = "bottom",
                          plot.title = element_text(size=9),
                          axis.title.x=element_blank(),
                          axis.text.x = element_text(angle = 45, hjust = 1, size = 7),
                          axis.text=element_text(size=9),
                          axis.title=element_text(size=9),
                          strip.text = element_text(size = 9)) +
                    labs(y = "Cost (£ Millions)", x = "Year", 
                         title = "Baseline Investment Costs") +
                    guides(colour=guide_legend(ncol=6)) 
)


# to get mean capacity per person the calculation needs to be:
# take capacity (Mbps per km2) * area (km2) / 
# ((population_density (persons per km2) * area (km2)) * market share factor / OBF)
mean_user_capacity <- (ggplot(results, aes(x=as.factor(year), y=mean_capacity_per_person_difference, 
                                           group=scenario, colour=scenario, linetype = scenario)) + 
                         geom_line(size=0.8) + facet_grid(cols = vars(strategy)) +
                         scale_color_manual(values = cols, drop = FALSE) +
                         scale_linetype_manual(values=linetypes, drop = FALSE) +
                         theme(legend.title = element_blank(),
                               legend.text = element_text(size = 9),
                               legend.position = "bottom",
                               plot.title = element_text(size=9),
                               axis.title.x=element_blank(),
                               axis.text.x = element_text(angle = 45, hjust = 1, size = 7),
                               axis.text=element_text(size=9),
                               axis.title=element_text(size=9),
                               strip.text = element_text(size = 9)) +
                         labs(y = "Mean Cell Edge\nUser Capacity (Mbps)", x = "Year", 
                              title = "Difference from Baseline Mean Cell Edge User Capacity (90% reliability)")  +
                         guides(colour=guide_legend(ncol=6)) 
)

# to get mean capacity per person the calculation needs to be:
# take capacity (Mbps per km2) * area (km2) / 
# ((population_density (persons per km2) * area (km2)) * market share factor / OBF)
sum_of_cost <- (ggplot(results, aes(x=as.factor(year), y=cost_difference_cumsum, 
                                    group=scenario, colour=scenario, linetype = scenario)) + 
                  geom_line(size=0.8) + facet_grid(cols = vars(strategy)) +
                  scale_color_manual(values = cols, drop = FALSE) +
                  scale_linetype_manual(values=linetypes, drop = FALSE) +
                  theme(legend.title = element_blank(),
                        legend.text = element_text(size = 9),
                        legend.position = "bottom",
                        plot.title = element_text(size=9),
                        axis.title.x=element_blank(),
                        axis.text.x = element_text(angle = 45, hjust = 1, size = 7),
                        axis.text=element_text(size=9),
                        axis.title=element_text(size=9),
                        strip.text = element_text(size = 9)) +
                  labs(y = "Cost (£ Millions)", x = "Year", 
                       title = "Difference from Baseline Investment Costs")  +
                  guides(colour=guide_legend(ncol=6)) 
)

user_capacity <- ggarrange(baseline_user_capacity,
                           mean_user_capacity,
                           baseline_cost,
                           sum_of_cost,
                           labels = NULL,
                           ncol=1,
                           nrow=4,
                           widths = c(1, 1.5),
                           align = "v",
                           legend = "bottom", 
                           common.legend = TRUE)

### EXPORT TO FOLDER
setwd(output_directory)
tiff('user_capacity.tiff', units="in", width=8.5, height=8.5, res=500)
print(user_capacity)
dev.off()

#################################
### Data Demand
#################################

setwd(data_input_directory)

user_data_demand <- read.csv('monthly_data_growth_scenarios.csv')

user_data_demand <- gather(user_data_demand, Scenario, Data_Demand, Low:High, factor_key=TRUE)

per_user_data_demand <- ggplot(user_data_demand, aes(x=Year, y=Data_Demand, group=Scenario, colour=Scenario, linetype = Scenario)) + 
  geom_line(size=0.8) +
  scale_x_continuous(expand = c(0, 0)) + scale_y_continuous(expand = c(0, 0)) +
  geom_vline(xintercept=c(2016), linetype="dotted") + 
  geom_vline(xintercept=c(2020), linetype="dotted") +
  annotate("text", x=2014, y=20, label= "Historical\nData", angle = 90, size=3) +
  annotate("text", x=2018, y=20, label= "Cisco VNI\n Forecast", angle = 90, size=3) +
  annotate("text", x=2022, y=20, label= "Scenario\nForecast", angle = 90, size=3) +
  annotate("text", x=2029, y=25, label= "High", size=3) +
  annotate("text", x=2029, y=17, label= "Base", size=3) +
  annotate("text", x=2029, y=12, label= "Low", size=3) +
  scale_color_manual(values = c("black", "black", "black"))+
  scale_linetype_manual(values = c("dashed", "solid", "dotted")) +
  theme(legend.title = element_blank(),
        legend.text = element_text(size = 8),
        legend.position = "none",
        plot.title = element_text(size=10),
        axis.title.x=element_blank(),
        axis.text.x = element_text(size = 8, angle = 45, hjust = 1),
        axis.title=element_text(size=10),
        strip.text = element_text(size = 10)) +
  labs(y = "Gigabytes (GB/Month)",  
       title = "A. Monthly Per User Data Consumption")  

demand_scenarios <- all_scenarios[which(all_scenarios$strategy == 'No Investment'),]

demand_scenarios <- demand_scenarios %>% 
  group_by(scenario, data_scenario, year) %>% 
  summarise(cost = sum(cost, na.rm = TRUE),
            aggregate_demand = sum(aggregate_demand, na.rm = TRUE),
            capacity = sum(capacity, na.rm = TRUE),
            aggregate_capacity = sum(aggregate_capacity, na.rm = TRUE),
            capacity_deficit = sum(capacity_deficit, na.rm = TRUE),
            aggregate_capacity_deficit = sum(aggregate_capacity_deficit, na.rm = TRUE),
            population = sum(population, na.rm = TRUE),
            area = sum(area, na.rm = TRUE)) %>%
  mutate(pop_density = population / area, 
         demand_density = aggregate_demand / area) %>%
  select(scenario, data_scenario, year, cost, aggregate_demand, capacity, aggregate_capacity,
         capacity_deficit, aggregate_capacity_deficit, population, 
         area, pop_density, demand_density)

colours <- c("Baseline" = "black",
             "Unplanned" = "orange",
             "New Cities" = "green",
             "Expansion" = "red",
             "New Cities 23k" = "yellow",
             "Expansion 23k" = "blue")

linetypes <- c("Baseline" = "solid",
               "Unplanned" = "longdash",
               "New Cities" = "dotdash",
               "Expansion" = "dotted",
               "New Cities 23k" = "dashed",
               "Expansion 23k" = "twodash")

population <- ggplot(demand_scenarios, aes(x=factor(year), y=(population/1000000), colour = scenario, group=scenario)) +
  geom_line(aes(linetype = scenario, colour = scenario, group=scenario),size=0.7) + 
  scale_y_continuous(expand = c(0,0)) + 
  scale_x_discrete(expand = c(0,0.1)) +
  scale_color_manual(values = c("#999999", "#E69F00", "#56B4E9", "#009E73",
                                "#F0E442", "#0072B2", "#D55E00", "#CC79A7"))+
  scale_linetype_manual(values=linetypes) +
  theme(legend.title = element_blank(),
        legend.text = element_text(size = 8),
        legend.position = "bottom",
        plot.title = element_text(size=10),
        axis.title.x=element_blank(),
        axis.title=element_text(size=10),
        axis.text.x = element_text(size = 8, angle = 45, hjust = 1)) +
  labs(y = "Population (Millions)", x = "Year", 
       title = "B. Population Growth by Scenario") +
  guides(colour=guide_legend(ncol=3) 
  )

aggregate_demand <- ggplot(demand_scenarios, aes(x=factor(year), y=(aggregate_demand/1000000), colour = scenario, group=scenario)) + #Mbps to Tbps
  geom_line(aes(linetype = scenario, colour = scenario, group=scenario), size=0.7) + 
  facet_grid(cols = vars(data_scenario)) +
  scale_y_continuous(expand = c(0,0)) +
  scale_x_discrete(expand = c(0,0.1), limits=c("2020","2025","2030")) +
  scale_color_manual(values = c("#999999", "#E69F00", "#56B4E9", "#009E73",
                                "#F0E442", "#0072B2", "#D55E00", "#CC79A7"))+
  scale_linetype_manual(values=linetypes) +
  theme(legend.title = element_blank(),
        legend.text = element_text(size = 8),
        legend.position = "none",
        plot.title = element_text(size=10),
        axis.title=element_text(size=10),
        axis.title.x=element_blank(),
        axis.text.x = element_text(size = 8, angle = 45, hjust = 1)) +
  labs(y = "Data Demand (Tbps)", x = "Year",
       title = "C. Total Busy Hour Demand by Scenario") +
  guides(colour=guide_legend(ncol=3)) 


# ## EXPORT TO FOLDER
# setwd(output_directory)
# tiff('demand_plot.tiff', units="in", width=10, height=10, res=300)
# print(demand_plot)
# dev.off()

###################################################################################
#### DEMAND VISUALISATION
###################################################################################

year_labels <- c(
  `2020` = "2020",
  `2025` = "2025",
  `2030` = "2030")

scenario_names <- c('Baseline' = "Baseline",
                    'Unplanned' = "Unplanned",
                    'New Cities' = "New Cities",
                    'Expansion' = "Expansion",
                    'New Cities 23k' = "New Cities 23k",
                    'Expansion 23k' = "Expansion 23k")

subset <- all_scenarios[which(all_scenarios$data_scenario == 'Baseline' & all_scenarios$strategy == 'No Investment'),]

myvars <- c("year", "area_id", "demand", "scenario")
subset <- subset[myvars]

subset <- subset[which(subset$year== 2020 |
                         subset$year== 2025 |
                         subset$year== 2030), ]

expansion <- subset[which(subset$area_id== 'E06000042' |
                         subset$area_id== 'E07000178' |
                         subset$area_id== 'E06000055' |
                         subset$area_id== 'E07000008'), ]

expansion <- expansion[which(expansion$scenario == 'Baseline' |
                               expansion$scenario == 'Expansion'), ]

subset$demand <- cut(subset$demand, breaks=c(0,10,15,20,25,30,35,45,100,120,800))    #-Inf,10,30,60,90,120,150,800

names(subset)[names(subset) == "area_id"] <- "id"
subset$id <- as.character(subset$id)

setwd(shapes_directory)
all.shp <- readOGR(".", "lad_uk_2016-12")
all.shp <- fortify(all.shp, region = "name")

all.shp$rank <- NA
all.shp$rank <- 1:nrow(all.shp)
all.shp <- merge(subset, all.shp, by = "id")
all.shp <- all.shp[order(all.shp$rank), ]

all.shp$demand_density_baseline = ordered(
  all.shp$demand,
  levels=c(
    "(0,10]",
    "(10,15]",
    "(15,20]",
    "(20,25]",
    "(25,30]",
    "(30,35]",
    "(35,45]",
    "(45,100]",
    "(100,120]",
    "(120,800]",
  )
)

original_demand_graphic <- ggplot() +
    geom_polypath(
      data = all.shp,
      aes(
        x = long,
        y = lat,
        group = group,
        fill = demand
      ),
      colour = "grey",
      size = 0.2
    ) +
    coord_equal() +
    scale_fill_brewer(
      palette = "Spectral",
      name = expression("Mbps" ~ km ^ 2),
      direction = -1,
      drop = FALSE
    ) +
    theme(
      legend.text = element_text(size = 8),
      legend.position = "bottom",
      legend.title = element_text(size = 9),
      plot.title = element_text(size = 10),
      axis.text = element_blank(),
      axis.ticks = element_blank(),
      axis.title = element_blank(),
      axis.title.x = element_blank()
    ) +
    guides(fill = guide_legend(reverse = FALSE, nrow = 2)) +
    labs(title = 'D. Demand Growth by Scenario (Baseline Data Consumption)') +
    facet_grid(scenario ~ year)


### EXPORT TO FOLDER
setwd(output_directory)
tiff('original_demand_graphic.tiff', units="in", width=8, height=8.5, res=900)
print(original_demand_graphic)
dev.off()

################################################################################
####### GGARRANGE #########
################################################################################

demand_graphic <- ggarrange(
  ggarrange(
    per_user_data_demand,
    population,
    aggregate_demand,
    nrow = 3,
    ncol = 1,
    labels = NULL,
    heights = c(1, 1),
    align = "v"),
  original_demand_graphic,
  labels = NULL,
  ncol = 2,
  widths = c(1, 1.5),
  align = "v")

### EXPORT TO FOLDER
setwd(output_directory)
tiff('demand_graphic.tiff', units="in", width=8, height=8.5, res=700)
print(demand_graphic)
dev.off()

################################################################################
####### POSTCODE ANALYSIS #########
################################################################################

setwd(data_directory)

metric_files <- list.files(data_directory, pattern="*.csv")

#subset those metric files
metric_files <- metric_files[grep("^pcd_metrics.*", metric_files)]

#initialised empty dataframe
empty_df <- data.frame(year=numeric(),
                       postcode=character(), 
                       lad_id=character(),
                       area=numeric(),
                       cost=numeric(),
                       demand=numeric(),
                       demand_density=numeric(),
                       user_demand=numeric(),
                       site_density_macrocells=numeric(),
                       site_density_small_cells=numeric(),
                       capacity=numeric(),
                       capacity_deficit=numeric(),
                       population=numeric(),
                       pop_density= numeric(), 
                       clutter_env=character())

import_function = lapply(metric_files, function(x) {
  DF <- read.csv(x, header = T, sep = ",")
  DF_Merge <- merge(empty_df, DF, all = T)
  DF_Merge$file <- as.factor(x)
  return(DF_Merge)})

all_scenarios <- do.call(rbind, import_function)

all_scenarios <- all_scenarios[which(
  all_scenarios$lad_id== 'E06000031' |
    all_scenarios$lad_id== 'E07000005' |
    all_scenarios$lad_id== 'E07000006' |
    all_scenarios$lad_id== 'E07000007' |
    all_scenarios$lad_id== 'E06000032' |
    all_scenarios$lad_id== 'E06000042' |
    all_scenarios$lad_id== 'E06000055' |
    all_scenarios$lad_id== 'E06000056' |
    all_scenarios$lad_id== 'E07000004' |
    all_scenarios$lad_id== 'E07000008' |
    all_scenarios$lad_id== 'E07000009' |
    all_scenarios$lad_id== 'E07000010' |
    all_scenarios$lad_id== 'E07000011' |
    all_scenarios$lad_id== 'E07000012' |
    all_scenarios$lad_id== 'E07000150' |
    all_scenarios$lad_id== 'E07000151' |
    all_scenarios$lad_id== 'E07000152' |
    all_scenarios$lad_id== 'E07000153' |
    all_scenarios$lad_id== 'E07000154' |
    all_scenarios$lad_id== 'E07000155' |
    all_scenarios$lad_id== 'E07000156' |
    all_scenarios$lad_id== 'E07000177' |
    all_scenarios$lad_id== 'E07000178' |
    all_scenarios$lad_id== 'E07000179' |
    all_scenarios$lad_id== 'E07000180' |
    all_scenarios$lad_id== 'E07000181' 
),]

all_scenarios <- all_scenarios %>% separate(file, c("unit","file_type", "scenario", "data_scenario", "strategy"), "_", remove = FALSE)
all_scenarios$aggregate_demand <- (all_scenarios$demand * all_scenarios$area) #in Mbps still
all_scenarios$aggregate_capacity <-  (all_scenarios$capacity * all_scenarios$area) #in Mbps still
all_scenarios$aggregate_capacity_deficit <- (all_scenarios$capacity_deficit * all_scenarios$area) #in Mbps still

all_scenarios$geotype[all_scenarios$pop_density >= 7959] = 'Urban'
all_scenarios$geotype[all_scenarios$pop_density >= 3119 & all_scenarios$pop_density < 7959] = 'Suburban 1'
all_scenarios$geotype[all_scenarios$pop_density >= 782 & all_scenarios$pop_density < 3119] = 'Suburban 2'
all_scenarios$geotype[all_scenarios$pop_density >= 112 & all_scenarios$pop_density < 782] = 'Rural 1'
all_scenarios$geotype[all_scenarios$pop_density >= 47 & all_scenarios$pop_density < 112] = 'Rural 2'
all_scenarios$geotype[all_scenarios$pop_density < 47] = 'Rural 3'
# all_scenarios$geotype[all_scenarios$pop_density >= 0 & all_scenarios$pop_density < 25] = 'Rural 4'


all_scenarios$scenario = factor(all_scenarios$scenario, levels=c("base",
                                                                 "0-unplanned",
                                                                 "1-new-cities-from-dwellings",
                                                                 "2-expansion",
                                                                 "3-new-cities23-from-dwellings",
                                                                 "4-expansion23"),
                                labels=c("Baseline",
                                         "Unplanned",
                                         "New Cities",
                                         "Expansion",
                                         "New Cities 23k",
                                         "Expansion 23k"))

all_scenarios$data_scenario = factor(all_scenarios$data_scenario, levels=c("low",
                                                                           "base",
                                                                           "high"),
                                     labels=c("Low",
                                              "Baseline",
                                              "High"))

all_scenarios$geotype = factor(all_scenarios$geotype, levels=c("Urban",
                                                               "Suburban 1",
                                                               "Suburban 2",
                                                               "Rural 1",
                                                               "Rural 2",
                                                               "Rural 3"))

pcd_demand <- ggplot(all_scenarios, aes(x=as.factor(year), y=(demand), group=year)) + 
  facet_grid(scenario ~ data_scenario) + 
  geom_point(position=position_jitterdodge(jitter.width=2, dodge.width = 0), 
             pch=21, aes(fill=geotype, shape=geotype), size = 1.5) +
  theme(legend.title = element_blank(),
        legend.text = element_text(size = 10),
        legend.position = "right",
        plot.title = element_text(size=12),
        axis.title.x=element_blank(),
        axis.text.x = element_text(angle = 45, hjust = 1)) +
  labs(y = "Data Demand (Mbps km^2)", x = "Year", title = "Busy Hour Data Demand by Scenario") 


### EXPORT TO FOLDER
setwd(output_directory)
tiff('pcd_demand.tiff', units="in", width=8.5, height=8.5, res=500)
print(pcd_demand)
dev.off()

#################################
### Plot Strategies 
#################################

all_scenarios$strategy = factor(all_scenarios$strategy, levels=c("minimal.csv",
                                                                 "macrocell.csv",
                                                                 "small-cell-and-spectrum.csv",
                                                                 "small-cell.csv"),
                                labels=c("No Investment",
                                         "Spectrum Integration",
                                         "Small Cells",
                                         "Spectrum and Small Cells"))

capacity_margin <- ggplot(all_scenarios, aes(x=as.factor(year), y=(capacity_deficit), group=year)) + 
  facet_grid(scenario ~ strategy) + 
  geom_point(position=position_jitterdodge(jitter.width=2, dodge.width = 0), 
             pch=21, aes(fill=geotype, shape=geotype), size = 1) +
  theme(legend.title = element_blank(),
        legend.text = element_text(size = 10),
        legend.position = "bottom",
        plot.title = element_text(size=12),
        axis.title.x=element_blank(),
        axis.text.x = element_text(angle = 45, hjust = 1)) +
  labs(y = "Capacity Margin (Mbps km^2)", x = "Year", title = "")

### EXPORT TO FOLDER
setwd(output_directory)
tiff('capacity_margin.tiff', units="in", width=8.5, height=8.5, res=500)
print(capacity_margin)
dev.off()

cost <- ggplot(all_scenarios, aes(x=as.factor(year), y=(cost/1e6), group=year)) + 
  facet_grid(scenario ~ strategy) + 
  geom_point(position=position_jitterdodge(jitter.width=2, dodge.width = 0), 
             pch=21, aes(fill=geotype, shape=geotype), size = 1) +
  theme(legend.title = element_blank(),
        legend.text = element_text(size = 10),
        legend.position = "bottom",
        plot.title = element_text(size=12),
        axis.title.x=element_blank(),
        axis.text.x = element_text(angle = 45, hjust = 1)) +
  labs(y = "Cost (£ Millions)", x = "Year", title = "")

### EXPORT TO FOLDER
setwd(output_directory)
tiff('cost.tiff', units="in", width=8.5, height=8.5, res=500)
print(cost)
dev.off()


#################################
### single area plots
#################################

subset <- all_scenarios[which(all_scenarios$year== 2020 &
                                all_scenarios$scenario== 'Baseline' &
                                all_scenarios$data_scenario== 'Baseline' &
                                all_scenarios$strategy == 'No Investment'), ]

remove(all_scenarios, empty_df, import_function)

plot1 <- ggplot(subset,aes(x=population, y=area, color=geotype, shape=geotype)) +
  scale_shape_manual(values=(0:7)) +
  labs(title = "Population and Area by Geotype", x="Population", y="Area (km^2)") +
  geom_point(size=1.5) + scale_color_brewer(palette="Dark2") +
  theme(legend.title = element_blank(),legend.text = element_text(size = 8),legend.position = "right",text = element_text(size=8),
        plot.title = element_text(size=10), axis.text.x = element_text(angle = 45, hjust = 1)) +
  guides(colour=guide_legend(ncol=7))

plot2 <- ggplot(subset,aes(x=pop_density, y=area, color=geotype, shape=geotype)) +
  scale_shape_manual(values=(0:7)) +
  labs(title = "Population Density and Area by Geotype", x="Population Density (Persons per km^2)", y="Area (km^2)") +
  geom_point(size=1.5) + scale_color_brewer(palette="Dark2") +
  theme(legend.title = element_blank(),legend.text = element_text(size = 8),legend.position = "right",text = element_text(size=8),
        plot.title = element_text(size=10), axis.text.x = element_text(angle = 45, hjust = 1)) 

plot3 <- ggplot(subset,aes(x=pop_density, y=population, color=geotype, shape=geotype)) +
  scale_shape_manual(values=(0:7)) +
  labs(title = "Population Density and Population by Geotype", x="Population Density (Persons per km^2)", y="Population") +
  geom_point(size=1.5) + scale_color_brewer(palette="Dark2") +
  theme(legend.title = element_blank(),legend.text = element_text(size = 8),legend.position = "right",text = element_text(size=8),
        plot.title = element_text(size=10), axis.text.x = element_text(angle = 45, hjust = 1)) 

plot4 <- ggplot(subset,aes(x=pop_density, y=capacity, color=geotype, shape=geotype)) +
  scale_shape_manual(values=(0:7)) +
  labs(title = "Population Density and Capacity by Geotype", x="Population Density (Persons per km^2)", y="Capacity (Mbps km^2)") +
  geom_point(size=1.5) + scale_color_brewer(palette="Dark2") +
  theme(legend.title = element_blank(),legend.text = element_text(size = 8),legend.position = "right",text = element_text(size=8),
        plot.title = element_text(size=10), axis.text.x = element_text(angle = 45, hjust = 1)) 

plot5 <- ggplot(subset,aes(x=pop_density, y=demand, color=geotype, shape=geotype)) +
  scale_shape_manual(values=(0:7)) +
  labs(title = "Population Density and Demand by Geotype", x="Population Density (Persons per km^2)", y="Demand (Mbps km^2)") +
  geom_point(size=1.5) + scale_color_brewer(palette="Dark2") +
  theme(legend.title = element_blank(),legend.text = element_text(size = 8),legend.position = "right",text = element_text(size=8),
        plot.title = element_text(size=10), axis.text.x = element_text(angle = 45, hjust = 1)) 

plot6 <- ggplot(subset,aes(x=pop_density, y=capacity_deficit, color=geotype, shape=geotype)) +
  scale_shape_manual(values=(0:7)) +
  labs(title = "Population Density and Capacity Margin by Geotype", x="Population Density (Persons per km^2)", y="Capacity Margin (Mbps km^2)") +
  geom_point(size=1.5) + scale_color_brewer(palette="Dark2") +
  theme(legend.title = element_blank(),legend.text = element_text(size = 8),legend.position = "right",text = element_text(size=8),
        plot.title = element_text(size=10), axis.text.x = element_text(angle = 45, hjust = 1)) 

composition <- ggarrange(plot1, plot2, plot3, plot4, plot5, plot6, ncol=2, nrow=3, common.legend = TRUE, legend="right", align = "hv")

### EXPORT TO FOLDER
setwd(output_directory)
tiff('pcd_sector_analytics.tiff', units="in", width=8.5, height=8.5, res=500)
print(composition)
dev.off()
