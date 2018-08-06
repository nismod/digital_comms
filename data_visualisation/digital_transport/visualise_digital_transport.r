library(tidyverse)
library(RColorBrewer)

#set path
path_inputs <- "C:\\Users\\edwar\\Desktop\\GitHub\\digital_comms\\results\\digital_transport"
path_figures <- "C:\\Users\\edwar\\Dropbox\\DfT ITS Project\\figures"

#set working directory
setwd(path_inputs)

# Get the files names
files = list.files(pattern="*.csv")

# First apply read.csv, then rbind
all_scenarios = do.call(rbind, lapply(files, function(x) read.csv(x, stringsAsFactors = FALSE)))

all_scenarios$road_type[all_scenarios$road_function == 'Densest Motorway' & all_scenarios$urban_rural == 'urban'] <- 'Densest Motorway (Urban)'
all_scenarios$road_type[all_scenarios$road_function == 'Densest Motorway' & all_scenarios$urban_rural == 'rural'] <- 'Densest Motorway (Rural)'
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
                                  levels = c("Densest Motorway (Urban)",
                                             "Densest Motorway (Rural)",
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

cost_per_km2_figure <- ggplot(data=cost_per_km2, aes(x=road_type, y=(cost_per_km2))) + 
  geom_bar(stat="identity", aes(fill=metric))  + 
  ylab("Investment Cost (GBP)") + 
  scale_fill_brewer(palette="Spectral", name = expression('Cost Type'), direction=-1) +
  theme(legend.position = "bottom", axis.title.x=element_blank(), axis.text.x = element_text(angle = 45, hjust = 1)) + 
  guides(fill = guide_legend(reverse = FALSE)) + 
  labs(title="Cost per Kilometer by Road Type", subtitle="Results reported by scenario, strategy and cost type") +
  facet_grid(scenario~strategy, labeller = labeller(strategy = strategy_labels, scenario = scenario_labels))

### EXPORT TO FOLDER
setwd(path_figures)
tiff('cost_per_km2.tiff', units="in", width=9, height=9, res=600)
print(cost_per_km2_figure)
dev.off()

#######################
# COST PER KM
#######################
