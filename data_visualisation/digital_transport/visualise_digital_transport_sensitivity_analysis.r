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
files = list.files(pattern=glob2rx("sensitivity_isd_spend_*.csv"))

# First apply read.csv, then rbind
all_scenarios = do.call(rbind, lapply(files, function(x) read.csv(x, stringsAsFactors = FALSE)))

cut_down_data <- select(all_scenarios, scenario, strategy, wtp_scenario, isd, 
                         RAN_units, small_cell_mounting_points, fibre_backhaul_m, length_m, total_tco)

cut_down_data <- cut_down_data %>%
  group_by(scenario, strategy, wtp_scenario, isd) %>%
  summarise(RAN_units = sum(RAN_units),
            small_cell_mounting_points = sum(small_cell_mounting_points),
            fibre_backhaul= sum(fibre_backhaul_m),
            length_m = sum(length_m),
            total_tco = round(sum(total_tco),1))

strategy_labels <- c(`cellular_V2X_full_greenfield` = "Greenfield Cellular V2X", 
                     `cellular_V2X_NRTS` = "Cellular V2X with NRTS", 
                     `DSRC_full_greenfield` = "Greenfield DSRC", 
                     `DSRC_NRTS` = "DSRC with NRTS")

scenario_labels <- c(`high` = "High (10 Mb/s, £20 ARPU)",
                     `baseline` = "Baseline (4 Mb/s, £4 ARPU)",
                     `low` = "Low (1 Mb/s, £2 ARPU)")

aggregate_cost <- cut_down_data %>%
  group_by(scenario, strategy, wtp_scenario, isd) %>%
  mutate(RAN_per_m = round(RAN_units / length_m, 5),
         ISD = round(length_m / RAN_units, 5),
            mounting_points_per_m = round(small_cell_mounting_points / length_m, ),
            fibre_backhaul_m = fibre_backhaul/ length_m,
            length_m = length_m,
            cost_per_m = round(total_tco / length_m, 6),
            total_tco = round(sum(total_tco), 3))  %>%
  select(scenario, strategy, wtp_scenario, isd, RAN_per_m, ISD, mounting_points_per_m, cost_per_m, total_tco)

aggregate_cost <- aggregate_cost[(aggregate_cost$ISD < 5000),]

aggregate_cost$scenario <- factor(aggregate_cost$scenario,
                           levels = c("high",
                                      "baseline",
                                      "low"))

ISD <- ggplot(aggregate_cost, aes(x=ISD, y=total_tco/1000000000, group=1)) + geom_line() +
  scale_y_continuous(expand = c(0, 0), limits=c(0,21)) + 
  scale_x_continuous(expand = c(0, 0), limits=c(0,4999)) +
  xlab("Mean Inter-Site Distance (ISD) (m)") + 
  ylab("Investment Cost (Billions GBP)") + 
  labs(title="Sensitivity of Total Cost to Mean Inter-Site Distance (ISD)", subtitle="Results reported by scenario and strategy as mean ISD increases") +
  facet_grid(scenario~strategy, labeller = labeller(strategy = strategy_labels, scenario = scenario_labels))

### EXPORT TO FOLDER
setwd(path_figures)
tiff('ISD.tiff', units="in", width=8, height=9, res=300)
print(ISD)
dev.off()

mean_cost <- aggregate_cost %>%
              group_by(scenario, strategy, wtp_scenario) %>%
              summarise(cost = round(mean(total_tco)/1000000000,2))

rm(aggregate_cost, all_scenarios, cut_down_data, ISD, mean_cost, files)

###############################
# PENETRATION
###############################

#set working directory
setwd(path_inputs)

# Get the files names
files = list.files(pattern=glob2rx("sensitivity_penetration_spend_*.csv"))

# First apply read.csv, then rbind
all_scenarios = do.call(rbind, lapply(files, function(x) read.csv(x, stringsAsFactors = FALSE)))

cut_down_data <- select(all_scenarios, scenario, strategy, wtp_scenario, inflection_year, 
                        annual_CAV_take_up, CAV_revenue)

aggregate_cost <- cut_down_data %>%
  group_by(scenario, strategy, wtp_scenario, inflection_year) %>%
  summarise(annual_CAV_take_up = sum(annual_CAV_take_up),
                   CAV_revenue = sum(CAV_revenue)/1000000000)

strategy_labels <- c(`cellular_V2X_full_greenfield` = "Greenfield Cellular V2X", 
                     `cellular_V2X_NRTS` = "Cellular V2X with NRTS", 
                     `DSRC_full_greenfield` = "Greenfield DSRC", 
                     `DSRC_NRTS` = "DSRC with NRTS")

scenario_labels <- c(`high` = "High (10 Mb/s, £20 ARPU)",
                     `baseline` = "Baseline (4 Mb/s, £4 ARPU)",
                     `low` = "Low (1 Mb/s, £2 ARPU)")

# aggregate_cost <- cut_down_data %>%
#   group_by(scenario, strategy, wtp_scenario, inflection_year) %>%
#   mutate(annual_CAV_take_up = sum(annual_CAV_take_up),
#          CAV_revenue = sum(CAV_revenue))  %>%
#   select(scenario, strategy, wtp_scenario, inflection_year, annual_CAV_take_up, CAV_revenue)

#aggregate_cost <- aggregate_cost[(aggregate_cost$ISD < 5000),]

aggregate_cost$scenario <- factor(aggregate_cost$scenario,
                                  levels = c("high",
                                             "baseline",
                                             "low"))

aggregate_cost$inflection_year <- round(aggregate_cost$inflection_year + 2019,0) 

aggregate_cost$inflection_year <- as.factor(aggregate_cost$inflection_year)
  
penetration_senstivity <- ggplot(aggregate_cost, aes(x=inflection_year, y=CAV_revenue, group=1)) + geom_line() +
  scale_y_continuous(expand = c(0, 0), limits=c(0,0.45)) + 
  scale_x_discrete(expand = c(0, 0)) + 
  xlab("Adoption Rate Inflection year") + 
  ylab("Revenue (Billions GBP)") + 
  theme(legend.position = "bottom", axis.text.x = element_text(angle = 45, hjust = 1)) + 
  labs(title="Sensitivity of Revenue to Subscription Adoption Rate", 
       subtitle="Results reported by scenario and strategy as adoption rate inflection year varies",
       xlab="Adoption Rate Inflection year") +
  facet_grid(scenario~strategy, labeller = labeller(strategy = strategy_labels, scenario = scenario_labels))

### EXPORT TO FOLDER
setwd(path_figures)
tiff('penetration_senstivity.tiff', units="in", width=8, height=9, res=300)
print(penetration_senstivity)
dev.off()

