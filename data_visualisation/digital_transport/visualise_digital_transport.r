library(tidyverse)
library(RColorBrewer)
library(rgeos)
library(maptools)
library(scales)

#set path
path_inputs <- "C:\\Users\\edwar\\Desktop\\GitHub\\digital_comms\\results\\digital_transport"
path_shapes <- "C:\\Users\\edwar\\Desktop\\GitHub\\digital_comms\\data\\digital_comms\\raw\\simplified_LADs"
path_figures <- "C:\\Users\\edwar\\Dropbox\\DfT ITS Project\\figures"

#set working directory
setwd(path_inputs)

# Get the files names
files = list.files(pattern=glob2rx("spend*.csv"))

# First apply read.csv, then rbind
all_scenarios = do.call(rbind, lapply(files, function(x) read.csv(x, stringsAsFactors = FALSE)))

all_scenarios$road_type[all_scenarios$road_function == 'Dense Motorway' & all_scenarios$urban_rural == 'urban'] <- 'Dense Motorway (Urban)'
all_scenarios$road_type[all_scenarios$road_function == 'Dense Motorway' & all_scenarios$urban_rural == 'rural'] <- 'Dense Motorway (Rural)'
all_scenarios$road_type[all_scenarios$road_function == 'Motorway' & all_scenarios$urban_rural == 'urban'] <- 'Motorway (Urban)'
all_scenarios$road_type[all_scenarios$road_function == 'Motorway' & all_scenarios$urban_rural == 'rural'] <- 'Motorway (Rural)'
all_scenarios$road_type[all_scenarios$road_function == 'A Road' & all_scenarios$urban_rural == 'urban'] <- 'A Road (Urban)'
all_scenarios$road_type[all_scenarios$road_function == 'A Road' & all_scenarios$urban_rural == 'rural'] <- 'A Road (Rural)'
all_scenarios$road_type[all_scenarios$road_function == 'B Road' & all_scenarios$urban_rural == 'urban'] <- 'B Road (Urban)'
all_scenarios$road_type[all_scenarios$road_function == 'B Road' & all_scenarios$urban_rural == 'rural'] <- 'B Road (Rural)'
all_scenarios$road_type[all_scenarios$road_function == 'Minor Road' & all_scenarios$urban_rural == 'urban'] <- 'Minor Road (Urban)'
all_scenarios$road_type[all_scenarios$road_function == 'Minor Road' & all_scenarios$urban_rural == 'rural'] <- 'Minor Road (Rural)'
all_scenarios$road_type[all_scenarios$road_function == 'Local Road' & all_scenarios$urban_rural == 'urban'] <- 'Local Road (Urban)'
all_scenarios$road_type[all_scenarios$road_function == 'Local Road' & all_scenarios$urban_rural == 'rural'] <- 'Local Road (Rural)'

all_scenarios$road_type <- factor(all_scenarios$road_type,
                                  levels = c("Dense Motorway (Urban)",
                                             "Dense Motorway (Rural)",
                                             "Motorway (Urban)",
                                             "Motorway (Rural)",
                                             "A Road (Urban)",
                                             "A Road (Rural)",
                                             "B Road (Urban)",
                                             "B Road (Rural)",
                                             "Minor Road (Urban)",
                                             "Minor Road (Rural)",
                                             "Local Road (Urban)",
                                             "Local Road (Rural)"))

all_scenarios$year <- as.factor(all_scenarios$year) 

#######################
# Vehicle Rollout and Subscription Take-up
#######################

vehicle_rollout_and_take_up <- all_scenarios[(all_scenarios$scenario == 'baseline' |
                                                all_scenarios$strategy == 'cellular_V2X_full_greenfield'),]

vehicle_rollout_and_take_up <- select(all_scenarios, year, total_cars, annual_CAV_capability, annual_CAV_take_up)

vehicle_rollout_and_take_up <- vehicle_rollout_and_take_up %>%
  group_by(year) %>%
  summarise(total_cars = sum(total_cars),
            annual_CAV_capability = sum(annual_CAV_capability),
            annual_CAV_take_up = sum(annual_CAV_take_up))

vehicle_rollout_and_take_up <- gather(vehicle_rollout_and_take_up, metric, value, total_cars, annual_CAV_capability, annual_CAV_take_up)

CAV_rollout_figure <- ggplot(data=vehicle_rollout_and_take_up, aes(x=year, y=(value/1000000), fill=metric)) + 
  geom_bar(position="dodge", stat="identity")  + 
  scale_y_continuous(expand = c(0, 0), limits=c(0,45)) + 
  ylab("Vehicles (Millions)") + 
  scale_fill_manual(values = c("orange2","green4", "light blue"),
                    name = "Type",
                    labels = c("Enabled CAVs", "Subscribers", "Total Registered Vehicles")) +
  theme(legend.position = "bottom", axis.title.x=element_blank(), axis.text.x = element_text(angle = 45, hjust = 1)) + 
  guides(fill = guide_legend(reverse = FALSE)) + 
  labs(title="Enabled CAVs and Subscription Take-up ", subtitle="Vehicle registration annual growth rate: 0.09%") 

### EXPORT TO FOLDER
setwd(path_figures)
tiff('CAV_rollout_figure.tiff', units="in", width=7, height=5, res=300)
print(CAV_rollout_figure)
dev.off()

rm(vehicle_rollout_and_take_up, CAV_rollout_figure)

#######################
# CAV road density
#######################

CAV_density <- all_scenarios[(all_scenarios$scenario == 'baseline' |
                                all_scenarios$scenario == 'low' |
                                all_scenarios$scenario == 'high'),]

CAV_density <- CAV_density[(CAV_density$strategy == 'cellular_V2X_full_greenfield'),]

CAV_density <- select(CAV_density, year, scenario, road_function, length_km, 
                      total_cars, annual_CAV_capability, annual_CAV_take_up)

CAV_density$road_function <- factor(CAV_density$road_function,
                                    levels = c("Dense Motorway",
                                               "Motorway",
                                               "A Road",
                                               "B Road",
                                               "Minor Road",
                                               "Local Road"))

scenario_labels <- c(`high` = "High",
                     `baseline` = "Baseline", 
                     `low` = "Low")

CAV_density$scenario <- factor(CAV_density$scenario,
                               levels = c("low",
                                          "baseline",
                                          "high"))

road_function_labels <- c('Dense Motorway' = "Dense Motorway", 
                          `Motorway` = "Motorway", 
                          `A Road` = "A Road",
                          `B Road` = "B Road",
                          `Minor Road` = "Minor Road",
                          `Local Road` = "Local Road")

CAV_density <- CAV_density %>%
  group_by(year, scenario, road_function) %>%
  mutate(total_car_density_km2 = round(total_cars/round(length_km,0),2),
         CAV_enabled_density_km2 = round(annual_CAV_capability/round(length_km,0),2),
         CAV_take_up_density_km2 = round(annual_CAV_take_up/round(length_km,0),2))

CAV_density <- select(CAV_density, year, scenario, road_function, 
                      total_car_density_km2, CAV_enabled_density_km2, CAV_take_up_density_km2)

CAV_density <- gather(CAV_density, metric, value, total_car_density_km2, CAV_enabled_density_km2, CAV_take_up_density_km2)

CAV_density_figure <- ggplot(data=CAV_density, aes(x=year, y=value, fill=metric)) +
  geom_bar(position="dodge", stat="identity")  +
  scale_y_continuous(expand = c(0, 0), limits=c(0,225)) + 
  scale_fill_manual(values = c("orange2","green4", "light blue"),
                    name = "Type",
                    labels = c("Enabled CAVs", "Subscribers", "Total Registered Vehicles")) +
  ylab("Average Vehicle Density (Km)") + 
  theme(legend.position = "bottom", axis.title.x=element_blank(), axis.text.x = element_text(angle = 45, hjust = 1)) + 
  guides(fill = guide_legend(reverse = FALSE)) + 
  labs(title="Average Density of Enabled CAVs and Subscribers", subtitle="Results reported by scenario, road type and metric type") +
  facet_grid(road_function~scenario, labeller = labeller(scenario = scenario_labels, road_function = road_function_labels))

### EXPORT TO FOLDER
setwd(path_figures)
tiff('CAV_density_figure.tiff', units="in", width=8, height=11, res=300)
print(CAV_density_figure)
dev.off()

rm(CAV_density, CAV_density_figure)

#######################
# COST PER KM
#######################

cost_per_km2 <- all_scenarios[(all_scenarios$scenario == 'baseline' |
                                 all_scenarios$scenario == 'low' |
                                 all_scenarios$scenario == 'high'),]

cost_per_km2 <- cost_per_km2[(cost_per_km2$year == '2020'),]

cost_per_km2 <- select(cost_per_km2, scenario, strategy, road_type, length_km,
                       RAN_cost, small_cell_mounting_cost, fibre_backhaul_cost)

cost_per_km2 <- gather(cost_per_km2, metric, value, RAN_cost, small_cell_mounting_cost, fibre_backhaul_cost)

cost_per_km2$value_per_km <- round(cost_per_km2$value*4,0)

cost_per_km2$value_per_km <- round(cost_per_km2$value/cost_per_km2$length_km,0)

cost_per_km2$metric <- factor(cost_per_km2$metric,
                              levels = c("RAN_cost",
                                         "small_cell_mounting_cost",
                                         "fibre_backhaul_cost"),
                              labels = c("Small Cell TCO",
                                         "Small Cell Civil Works",
                                         "Fibre Backhaul TCO"))

cost_per_km2$scenario <- factor(cost_per_km2$scenario,
                                   levels = c("high",
                                              "baseline",
                                              "low"))

scenario_labels <- c(`high` = "High (10 Mb/s)",
                     `baseline` = "Baseline (4 Mb/s)",
                     `low` = "Low (1 Mb/s)")

strategy_labels <- c(`cellular_V2X_full_greenfield` = "Greenfield Cellular V2X", 
                     `cellular_V2X_NRTS` = "Cellular V2X with NRTS", 
                     `DSRC_full_greenfield` = "Greenfield DSRC", 
                     `DSRC_NRTS` = "DSRC with NRTS")

cost_per_km2_figure <- ggplot(data=cost_per_km2, aes(x=reorder(road_type, value_per_km), y=value_per_km)) + geom_bar(stat="identity", aes(fill=metric)) +
  facet_grid(scenario~strategy, labeller = labeller(strategy = strategy_labels, scenario = scenario_labels)) +
  ylab("Investment Cost Per Kilometer (GBP)") +
  scale_y_continuous(expand = c(0, 0), labels = comma, limits=c(0,55000)) +
  scale_fill_brewer(palette="Spectral", name = expression('Cost Type'), direction=-1) +
  theme(legend.position = "bottom", axis.title.x=element_blank(), axis.text.x = element_text(angle = 60, hjust = 1)) +
  guides(fill = guide_legend(reverse = FALSE)) +
  labs(title="Cost per Kilometer by Road Type", subtitle="Results reported by scenario, strategy and cost type") 

### EXPORT TO FOLDER
setwd(path_figures)
tiff('cost_per_km2.tiff', units="in", width=8, height=10, res=300)
print(cost_per_km2_figure)
dev.off()

rm(cost_per_km2, cost_per_km2_figure)

#######################
# AGGREGATE COST 
#######################

aggregate_cost <- select(all_scenarios, year, scenario, strategy, road_type, length_km,
                         RAN_cost, small_cell_mounting_cost, fibre_backhaul_cost)

aggregate_cost <- aggregate_cost %>%
  group_by(scenario, strategy, road_type) %>%
  summarise(RAN_cost = sum(RAN_cost),
            small_cell_mounting_cost = sum(small_cell_mounting_cost), 
            fibre_backhaul_cost = sum(as.numeric(fibre_backhaul_cost)))

aggregate_cost <- gather(aggregate_cost, metric, value, RAN_cost, small_cell_mounting_cost, fibre_backhaul_cost)

scenario_labels <- c(`high` = "High (10 Mb/s)",
                     `baseline` = "Baseline (4 Mb/s)",
                     `low` = "Low (1 Mb/s)")

aggregate_cost$scenario <- factor(aggregate_cost$scenario,
                                  levels = c("high",
                                             "baseline",
                                             "low"))

strategy_labels <- c(`cellular_V2X_full_greenfield` = "Greenfield Cellular V2X", 
                     `cellular_V2X_NRTS` = "Cellular V2X with NRTS", 
                     `DSRC_full_greenfield` = "Greenfield DSRC", 
                     `DSRC_NRTS` = "DSRC with NRTS")

aggregate_cost$metric <- factor(aggregate_cost$metric,
                                levels = c("RAN_cost",
                                           "small_cell_mounting_cost",
                                           "fibre_backhaul_cost"),
                                labels = c("Small Cell TCO",
                                           "Small Cell Civil Works",
                                           "Fibre Backhaul TCO"))

aggregate_cost_figure <- ggplot(data=aggregate_cost, aes(x=reorder(road_type, value), y=(value/1000000000))) + 
  geom_bar(stat="identity", aes(fill=metric))  + 
  ylab("Investment Cost (Billions GBP)") + 
  scale_y_continuous(expand = c(0, 0), limits=c(0,5.5)) + 
  scale_fill_brewer(palette="Spectral", name = expression('Cost Type'), direction=-1) +
  theme(legend.position = "bottom", axis.title.x=element_blank(), axis.text.x = element_text(angle = 70, hjust = 1)) + 
  guides(fill = guide_legend(reverse = FALSE)) + 
  labs(title="Aggregate Cost by Road Type", subtitle="Results reported by scenario, strategy and cost type") +
  facet_grid(scenario~strategy, labeller = labeller(strategy = strategy_labels, scenario = scenario_labels))

### EXPORT TO FOLDER
setwd(path_figures)
tiff('aggregate_cost_figure.tiff', units="in", width=8, height=10, res=300)
print(aggregate_cost_figure)
dev.off()

rm(aggregate_cost, aggregate_cost_figure)

#######################
# COST BENEFIT METRICS 
#######################

total_CBA <- select(all_scenarios, year, scenario, strategy, CAV_revenue, total_tco)

total_CBA <- total_CBA %>%
  group_by(year, scenario, strategy) %>%
  summarise(CAV_revenue = sum(as.numeric(CAV_revenue)),
            total_tco = sum(as.numeric(total_tco)))

total_CBA$scenario <- factor(total_CBA$scenario,
                             levels = c("high",
                                        "baseline",
                                        "low"))

total_CBA <- gather(total_CBA, metric, value, CAV_revenue, total_tco)

total_CBA_figure <- ggplot(data=total_CBA, aes(x=year, y=(value/1000000000), fill=metric)) + 
  geom_bar(position="dodge", stat="identity")  + 
  ylab("Investment Cost (Billions GBP)") + 
  scale_y_continuous(expand = c(0, 0), limits=c(0, 4.5)) + 
  scale_fill_manual(values = c("green4","orange2"),
                    name = "Type",
                    labels = c("Benefit", "Cost")) +
  theme(legend.position = "bottom", axis.title.x=element_blank(), axis.text.x = element_text(angle = 45, hjust = 1)) + 
  guides(fill = guide_legend(reverse = FALSE)) + 
  labs(title="Strategy Performance by Scenario: All Roads", subtitle="Results reported by scenario, strategy and performance metric") +
  facet_grid(scenario~strategy, labeller = labeller(strategy = strategy_labels, scenario = scenario_labels))

### EXPORT TO FOLDER
setwd(path_figures)
tiff('total_CBA_figure.tiff', units="in", width=9, height=9, res=300)
print(total_CBA_figure)
dev.off()

##########################################
# COST BENEFIT METRICS MOTORWAYS & A Roads
##########################################

SRN_CBA <- all_scenarios[which(all_scenarios$road_function == 'Dense Motorway' |
                                 all_scenarios$road_function == 'Motorway' |
                                 all_scenarios$road_function == 'A Road'),]

SRN_CBA <- select(SRN_CBA, year, scenario, strategy, CAV_revenue, total_tco)

SRN_CBA <- SRN_CBA %>%
  group_by(year, scenario, strategy) %>%
  summarise(CAV_revenue = sum(as.numeric(CAV_revenue)),
            total_tco = sum(as.numeric(total_tco)))

SRN_CBA$scenario <- factor(SRN_CBA$scenario,
                           levels = c("high",
                                      "baseline",
                                      "low"))

SRN_CBA <- gather(SRN_CBA, metric, value, CAV_revenue, total_tco)

SRN_CBA_figure <- ggplot(data=SRN_CBA, aes(x=year, y=(value/1000000000), fill=metric)) + 
  geom_bar(position="dodge", stat="identity")  + 
  scale_y_continuous(expand = c(0, 0), limits=c(0,0.6)) + 
  ylab("Investment Cost (Billions GBP)") + 
  scale_fill_manual(values = c("green4","orange2"),
                    name = "Type",
                    labels = c("Benefit", "Cost")) +
  theme(legend.position = "bottom", axis.title.x=element_blank(), axis.text.x = element_text(angle = 45, hjust = 1)) + 
  guides(fill = guide_legend(reverse = FALSE)) + 
  labs(title="Strategy Performance by Scenario: Strategic Road Network", subtitle="Results reported by scenario, strategy and performance metric") +
  facet_grid(scenario~strategy, labeller = labeller(strategy = strategy_labels, scenario = scenario_labels))

### EXPORT TO FOLDER
setwd(path_figures)
tiff('SRN_CBA_figure.tiff', units="in", width=9, height=9, res=300)
print(SRN_CBA_figure)
dev.off()

rm(SRN_CBA, SRN_CBA_figure, total_CBA, total_CBA_figure)

#######################
# IMPORT COST PER LAD
#######################

#set working directory
setwd(path_inputs)

# Get the files names
files = list.files(pattern=glob2rx("lad_*.csv"))

# First apply read.csv, then rbind
all_scenarios = do.call(rbind, lapply(files, function(x) read.csv(x, stringsAsFactors = FALSE)))

all_scenarios$road_type[all_scenarios$road_function == 'Dense Motorway' & all_scenarios$urban_rural == 'urban'] <- 'Dense Motorway (Urban)'
all_scenarios$road_type[all_scenarios$road_function == 'Dense Motorway' & all_scenarios$urban_rural == 'rural'] <- 'Dense Motorway (Rural)'
all_scenarios$road_type[all_scenarios$road_function == 'Motorway' & all_scenarios$urban_rural == 'urban'] <- 'Motorway (Urban)'
all_scenarios$road_type[all_scenarios$road_function == 'Motorway' & all_scenarios$urban_rural == 'rural'] <- 'Motorway (Rural)'
all_scenarios$road_type[all_scenarios$road_function == 'A Road' & all_scenarios$urban_rural == 'urban'] <- 'A Road (Urban)'
all_scenarios$road_type[all_scenarios$road_function == 'A Road' & all_scenarios$urban_rural == 'rural'] <- 'A Road (Rural)'
all_scenarios$road_type[all_scenarios$road_function == 'B Road' & all_scenarios$urban_rural == 'urban'] <- 'B Road (Urban)'
all_scenarios$road_type[all_scenarios$road_function == 'B Road' & all_scenarios$urban_rural == 'rural'] <- 'B Road (Rural)'
all_scenarios$road_type[all_scenarios$road_function == 'Minor Road' & all_scenarios$urban_rural == 'urban'] <- 'Minor Road (Urban)'
all_scenarios$road_type[all_scenarios$road_function == 'Minor Road' & all_scenarios$urban_rural == 'rural'] <- 'Minor Road (Rural)'
all_scenarios$road_type[all_scenarios$road_function == 'Local Road' & all_scenarios$urban_rural == 'urban'] <- 'Local Road (Urban)'
all_scenarios$road_type[all_scenarios$road_function == 'Local Road' & all_scenarios$urban_rural == 'rural'] <- 'Local Road (Rural)'

all_scenarios$road_type <- factor(all_scenarios$road_type,
                                  levels = c("Dense Motorway (Urban)",
                                             "Dense Motorway (Rural)",
                                             "Motorway (Urban)",
                                             "Motorway (Rural)",
                                             "A Road (Urban)",
                                             "A Road (Rural)",
                                             "B Road (Urban)",
                                             "B Road (Rural)",
                                             "Minor Road (Urban)",
                                             "Minor Road (Rural)",
                                             "Local Road (Urban)",
                                             "Local Road (Rural)"))

all_scenarios$year <- as.factor(all_scenarios$year) 

#######################
# COST PER LAD
#######################

aggregate_cost <- select(all_scenarios, lad, scenario, strategy, total_tco)

aggregate_cost <- aggregate_cost %>%
  group_by(lad, scenario, strategy) %>%
  summarise(total_tco = sum(total_tco))

aggregate_cost$total_tco <- aggregate_cost$total_tco/1000000

breaks <- c(0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 350)
aggregate_cost$total_tco_binned <- cut(aggregate_cost$total_tco, breaks)

aggregate_cost$total_tco_binned = factor(aggregate_cost$total_tco_binned,
                                         levels=c("(0,5]",
                                                  "(5,10]",
                                                  "(10,15]",
                                                  "(15,20]",
                                                  "(20,25]",
                                                  "(25,30]",
                                                  "(30,35]",
                                                  "(35,40]",
                                                  "(40,45]",
                                                  "(45,50]",
                                                  "(50,350]"),
                                         labels=c('(0-5)',
                                                  '(5-10)',
                                                  '(10-15)',
                                                  '(15-20)',
                                                  '(20-25)',
                                                  '(25-30)',
                                                  '(30-35)',
                                                  '(35-40)',
                                                  '(40-45)',
                                                  '(45-50)',
                                                  '(>50)'))

aggregate_cost$total_tco_binned = forcats::fct_rev(factor(aggregate_cost$total_tco_binned))

scenario_labels <- c(`high` = "High (10 Mb/s)",
                     `baseline` = "Baseline (4 Mb/s)",
                     `low` = "Low (1 Mb/s)")

aggregate_cost$scenario <- factor(aggregate_cost$scenario,
                                  levels = c("high",
                                             "baseline",
                                             "low"))

strategy_labels <- c(`cellular_V2X_full_greenfield` = "Greenfield Cellular V2X", 
                     `cellular_V2X_NRTS` = "Cellular V2X with NRTS", 
                     `DSRC_full_greenfield` = "Greenfield DSRC", 
                     `DSRC_NRTS` = "DSRC with NRTS")
setwd(path_shapes)

all.shp <- readShapeSpatial("simplified_LADS_WGS84") 

all.shp <- fortify(all.shp, region = "LAD12CD")

all.shp <- merge(all.shp, aggregate_cost, by.x="id", by.y="lad", all.y = TRUE)

all.shp <- all.shp[order(all.shp$order),]

cost_by_lad <- ggplot() + geom_polygon(data = all.shp, aes(x = long, y = lat, group=group, 
                                                           fill = total_tco_binned)) + 
  coord_equal() +
  guides(fill = guide_legend(reverse = FALSE)) + 
  scale_fill_brewer(palette=("Spectral"), name = expression('Cost\n(Millions)', direction=1)) +
  labs(title="Total Road Network Aggregate Cost by LAD", subtitle="Results reported by scenario, strategy and cost ") +
  theme(legend.position="right", axis.text = element_blank(), axis.title=element_blank(), axis.ticks=element_blank()) +
  facet_grid(scenario ~ strategy, labeller = labeller(scenario = scenario_labels, strategy = strategy_labels))

### EXPORT TO FOLDER
setwd(path_figures)
tiff('cost_by_lad.tiff', units="in", width=8, height=9, res=300)
print(cost_by_lad)
dev.off()

#######################
# COST PER LAD for SRN
#######################

aggregate_cost_SRN <- all_scenarios[which(all_scenarios$road_function == 'Dense Motorway' |
                                            all_scenarios$road_function == 'Motorway' |
                                            all_scenarios$road_function == 'A Road'),]

aggregate_cost_SRN <- select(aggregate_cost_SRN, lad, scenario, strategy, total_tco)

aggregate_cost_SRN <- aggregate_cost_SRN %>%
  group_by(lad, scenario, strategy) %>%
  summarise(total_tco = sum(total_tco))

aggregate_cost_SRN$total_tco <- aggregate_cost_SRN$total_tco/1000000

breaks <- c(0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 200)
aggregate_cost_SRN$total_tco_binned <- cut(aggregate_cost_SRN$total_tco, breaks)

aggregate_cost_SRN$total_tco_binned = factor(aggregate_cost_SRN$total_tco_binned,
                                         levels=c("(0,1]",
                                                  "(1,2]",
                                                  "(2,3]",
                                                  "(3,4]",
                                                  "(4,5]",
                                                  "(5,6]",
                                                  "(6,7]",
                                                  "(7,8]",
                                                  "(8,9]",
                                                  "(9,10]",
                                                  "(10,200]"),
                                         labels=c('(0-1)',
                                                  '(1-2)',
                                                  '(2-3)',
                                                  '(3-4)',
                                                  '(4-5)',
                                                  '(5-6)',
                                                  '(6-7)',
                                                  '(7-8)',
                                                  '(8-9)',
                                                  '(9-10)',
                                                  '(>10)'))

aggregate_cost_SRN$total_tco_binned = forcats::fct_rev(factor(aggregate_cost_SRN$total_tco_binned))

scenario_labels <- c(`high` = "High (10 Mb/s)",
                     `baseline` = "Baseline (4 Mb/s)",
                     `low` = "Low (1 Mb/s)")

aggregate_cost_SRN$scenario <- factor(aggregate_cost_SRN$scenario,
                                      levels = c("high",
                                                 "baseline",
                                                 "low"))

strategy_labels <- c(`cellular_V2X_full_greenfield` = "Greenfield Cellular V2X", 
                     `cellular_V2X_NRTS` = "Cellular V2X with NRTS", 
                     `DSRC_full_greenfield` = "Greenfield DSRC", 
                     `DSRC_NRTS` = "DSRC with NRTS")

setwd(path_shapes)

all.shp <- readShapeSpatial("simplified_LADS_WGS84") 

all.shp <- fortify(all.shp, region = "LAD12CD")

all.shp <- merge(all.shp, aggregate_cost_SRN, by.x="id", by.y="lad", all.y = TRUE)

all.shp <- all.shp[order(all.shp$order),]

SRN_cost_by_lad <- ggplot() + geom_polygon(data = all.shp, aes(x = long, y = lat, group=group, 
                                                               fill = total_tco_binned)) + 
  coord_equal() +
  guides(fill = guide_legend(reverse = FALSE)) + 
  scale_fill_brewer(palette="Spectral", name = expression('Cost\n(Millions)')) +
  labs(title="SRN Aggregate Cost by LAD", subtitle="Results reported by scenario, strategy and cost ") +
  theme(legend.position="right", axis.text = element_blank(), axis.title=element_blank(), axis.ticks=element_blank()) +
  facet_grid(scenario ~ strategy, labeller = labeller(scenario = scenario_labels, strategy = strategy_labels))

### EXPORT TO FOLDER
setwd(path_figures)
tiff('SRN_cost_by_lad.tiff', units="in", width=9, height=9, res=300)
print(SRN_cost_by_lad)
dev.off()

##################################
# TOTAL COST OUTPUT METRICS
##################################

total_cost <- select(all_scenarios, scenario, strategy, total_tco)

total_cost %>%
  group_by(scenario, strategy) %>%
  summarise(total_tco = round(sum(as.numeric(total_tco)/1000000000),2))

##################################
# TOTAL COST OUTPUT METRICS
##################################

aggregate_cost_by_road_type <- select(all_scenarios, scenario, strategy, road_type, total_tco)

aggregate_cost_by_road_type <- aggregate_cost_by_road_type %>%
  group_by(scenario, strategy, road_type) %>%
  summarise(total_tco = sum(as.numeric(total_tco)/1000000000))

##################################
# AVERAGE COST OUTPUT METRICS
##################################

# average_cost_per_km2 <- all_scenarios[(all_scenarios$year == '2020'),]
# 
# average_cost_per_km2$value_per_km <- round(average_cost_per_km2$total_tco*4,0)
# 
# average_cost_per_km2 <- select(all_scenarios, scenario, strategy, length_km, total_tco)
# 
# average_cost_per_km2 <- average_cost_per_km2 %>%
#   group_by(scenario, strategy) %>%
#   summarise(total_tco = sum(as.numeric(total_tco)),
#             length_km = sum(as.numeric(length_km)))



