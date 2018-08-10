library(tidyverse)
library(RColorBrewer)
library(rgeos)
library(maptools)

#set path
path_inputs <- "C:\\Users\\edwar\\Desktop\\GitHub\\digital_comms\\results\\digital_transport"
path_shapes <- "C:\\Users\\edwar\\Desktop\\GitHub\\digital_comms\\data\\digital_comms\\raw\\lad_uk_2016-12"
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
# COST PER KM
#######################

cost_per_km2 <- select(all_scenarios, year, scenario, strategy, road_type, length_km,
                        RAN_cost, small_cell_mounting_cost, fibre_backhaul_cost)

cost_per_km2 <- gather(cost_per_km2, metric, value, RAN_cost, small_cell_mounting_cost, fibre_backhaul_cost)

cost_per_km2$cost_per_km2 <- cost_per_km2$value /cost_per_km2$length

scenario_labels <- c(`high` = "High (10 Mb/s)",
                    `baseline` = "Baseline (4 Mb/s)", 
                    `low` = "Low (1 Mb/s)")

cost_per_km2$scenario <- factor(cost_per_km2$scenario,
                                levels = c("high",
                                           "baseline",
                                           "low"))

strategy_labels <- c(`cellular_V2X` = "Cellular V2X", 
                     `DSRC_full_greenfield` = "Greenfield DSRC", 
                     `DSRC_NRTS_greenfield` = "DSRC with NRTS")

cost_per_km2$metric <- factor(cost_per_km2$metric,
                                  levels = c("RAN_cost",
                                             "small_cell_mounting_cost",
                                             "fibre_backhaul_cost"),
                                  labels = c("Small Cell TCO",
                                             "Small Cell Civil Works",
                                             "Fibre Backhaul TCO"))

cost_per_km2_figure <- ggplot(data=cost_per_km2, aes(x=reorder(road_type, -cost_per_km2), y=(cost_per_km2))) + 
  geom_bar(stat="identity", aes(fill=metric))  + 
  ylab("Investment Cost (GBP)") + 
  scale_y_continuous(expand = c(0, 0)) + 
  scale_fill_brewer(palette="Spectral", name = expression('Cost Type'), direction=-1) +
  theme(legend.position = "bottom", axis.title.x=element_blank(), axis.text.x = element_text(angle = 45, hjust = 1)) + 
  guides(fill = guide_legend(reverse = FALSE)) + 
  labs(title="Cost per Kilometer by Road Type", subtitle="Results reported by scenario, strategy and cost type") +
  facet_grid(scenario~strategy, labeller = labeller(strategy = strategy_labels, scenario = scenario_labels))

### EXPORT TO FOLDER
setwd(path_figures)
tiff('cost_per_km2.tiff', units="in", width=9, height=9, res=300)
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
                  summarise(length_km = sum(length_km),
                            RAN_cost = sum(RAN_cost),
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

strategy_labels <- c(`cellular_V2X` = "Cellular V2X", 
                     `DSRC_full_greenfield` = "Greenfield DSRC", 
                     `DSRC_NRTS_greenfield` = "DSRC with NRTS")

aggregate_cost$metric <- factor(aggregate_cost$metric,
                                levels = c("RAN_cost",
                                           "small_cell_mounting_cost",
                                           "fibre_backhaul_cost"),
                                labels = c("Small Cell TCO",
                                           "Small Cell Civil Works",
                                           "Fibre Backhaul TCO"))

aggregate_cost_figure <- ggplot(data=aggregate_cost, aes(x=reorder(road_type, -value), y=(value/1000000000))) + 
  geom_bar(stat="identity", aes(fill=metric))  + 
  ylab("Investment Cost (Billions GBP)") + 
  scale_y_continuous(expand = c(0, 0)) + 
  scale_fill_brewer(palette="Spectral", name = expression('Cost Type'), direction=-1) +
  theme(legend.position = "bottom", axis.title.x=element_blank(), axis.text.x = element_text(angle = 45, hjust = 1)) + 
  guides(fill = guide_legend(reverse = FALSE)) + 
  labs(title="Aggregate Cost by Road Type", subtitle="Results reported by scenario, strategy and cost type") +
  facet_grid(scenario~strategy, labeller = labeller(strategy = strategy_labels, scenario = scenario_labels))

### EXPORT TO FOLDER
setwd(path_figures)
tiff('aggregate_cost_figure.tiff', units="in", width=9, height=9, res=300)
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
  scale_y_continuous(expand = c(0, 0)) + 
  scale_fill_manual(values = c("green","red"),
                      name = "Type",
                    labels = c("Benefit", "Cost")) +
  theme(legend.position = "bottom", axis.title.x=element_blank(), axis.text.x = element_text(angle = 45, hjust = 1)) + 
  guides(fill = guide_legend(reverse = FALSE)) + 
  labs(title="Aggregate Cost by Road Type", subtitle="Results reported by scenario, strategy and cost type") +
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
  scale_y_continuous(expand = c(0, 0)) + 
  ylab("Investment Cost (Billions GBP)") + 
  scale_fill_manual(values = c("green","red"),
                    name = "Type",
                    labels = c("Benefit", "Cost")) +
  theme(legend.position = "bottom", axis.title.x=element_blank(), axis.text.x = element_text(angle = 45, hjust = 1)) + 
  guides(fill = guide_legend(reverse = FALSE)) + 
  labs(title="Aggregate Cost by Road Type", subtitle="Results reported by scenario, strategy and cost type") +
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
files = list.files(pattern=glob2rx("lad*.csv"))

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

scenario_labels <- c(`high` = "High (10 Mb/s)",
                     `baseline` = "Baseline (4 Mb/s)",
                     `low` = "Low (1 Mb/s)")

aggregate_cost$scenario <- factor(aggregate_cost$scenario,
                                  levels = c("high",
                                             "baseline",
                                             "low"))

strategy_labels <- c(`cellular_V2X` = "Cellular V2X", 
                     `DSRC_full_greenfield` = "Greenfield DSRC", 
                     `DSRC_NRTS_greenfield` = "DSRC with NRTS")

setwd(path_shapes)

all.shp <- readShapeSpatial("lad_uk_2016-12.shp") 

all.shp <- fortify(all.shp, region = "name")

all.shp <- merge(all.shp, aggregate_cost, by.x="id", by.y="lad")

all.shp <- all.shp[order(all.shp$order),]

cost_by_lad <- ggplot() + geom_polygon(data = all.shp, aes(x = long, y = lat, group=group, 
                                       fill = total_tco), color = "grey", size = 0.1) + 
  coord_equal() +
  guides(fill = guide_legend(reverse = FALSE)) + 
  labs(title="Aggregate Cost by LAD", subtitle="Results reported by scenario, strategy and cost ") +
  theme(legend.position="right", axis.text = element_blank(), axis.title=element_blank(), axis.ticks=element_blank()) +
  facet_grid(scenario ~ strategy, labeller = labeller(scenario = scenario_labels, strategy = strategy_labels))

### EXPORT TO FOLDER
setwd(path_figures)
tiff('cost_by_lad.tiff', units="in", width=9, height=9, res=300)
print(cost_by_lad)
dev.off()

