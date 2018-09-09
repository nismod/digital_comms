###VISUALISE MODEL OUTPUTS###
library(tidyverse)
library(maptools)
library(ggmap)
library(scales)
library(RColorBrewer)
library(ggpubr)       

path_figures <- "C:\\Users\\edwar\\Desktop\\GitHub\\digital_comms\\data_visualisation\\digital_comms_test"
path_shapes <- "C:\\Users\\edwar\\Desktop\\GitHub\\digital_comms\\data\\digital_comms\\raw\\lad_uk_2016-12"

read_in_data <- function(file_pattern) {

  path <- "C:\\Users\\edwar\\Desktop\\GitHub\\digital_comms\\results"

  myfiles <- list.files(path = path, pattern = glob2rx(file_pattern), recursive = TRUE)
  files <- myfiles[!grepl("digital_transport", myfiles)]
  
  setwd(path)
  
  #initialised empty dataframe
  empty_df <- data.frame(timestep=numeric(),
                         region=character(), 
                         interval=numeric(), 
                         value=numeric())
  
  import_function = lapply(files, function(x) {
    DF <- read.csv(x, header = T, sep = ",")
    DF_Merge <- merge(empty_df, DF, all = T)
    DF_Merge$scenario <- as.factor(substring(x, 15,15))
    DF_Merge$strategy <- as.factor(substring(x, 22,23))
    DF_Merge$tech <- as.factor(substring(x, 17,21))
    return(DF_Merge)})
  
  all_scenarios <- do.call(rbind, import_function)
  
  all_scenarios <- select(all_scenarios, timestep, value, scenario, strategy, tech, region)
  
  rm(empty_df, files, myfiles)
  
  all_scenarios$scenario <- factor(all_scenarios$scenario,
                                   levels = c("h",
                                              "b",
                                              "l"),
                                   labels = c("High Take-up",
                                              "Baseline Take-up",
                                              "Low Take-up"))
  
  all_scenarios$strategy <- gsub(".*r.*", "Market Rollout", all_scenarios$strategy)
  all_scenarios$strategy <- gsub(".*s.*", "Targeted Subsidy", all_scenarios$strategy)
  
  all_scenarios$strategy <- factor(all_scenarios$strategy,
                                   levels = c("Market Rollout",
                                              "Targeted Subsidy"),
                                   labels = c("Market Rollout",
                                              "Targeted Subsidy"))
  
  all_scenarios$tech <- gsub(".*fttdp.*", "FTTdp", all_scenarios$tech)
  all_scenarios$tech <- gsub(".*fttp.*", "FTTP", all_scenarios$tech)
  
  all_scenarios$tech <- factor(all_scenarios$tech,
                               levels = c("FTTdp",
                                          "FTTP"),
                               labels = c("FTTdp",
                                          "FTTP"))
  
  all_scenarios$timestep <- as.factor(all_scenarios$timestep)
  
  return(all_scenarios)
}

all_scenarios <- read_in_data("output_premises_with*.csv")

all_scenarios <- all_scenarios[complete.cases(all_scenarios),]

scenario_results <- ggplot(data=all_scenarios, aes(x=timestep, y=(value), group = tech, colour = tech)) + geom_line() +
                    labs(y = "Premises Connected (%)", x = "Year", colour = "Technology", 
                    title = "Technology Rollout by Scenario and Strategy", subtitle = "Expected Return Period: 4 Years") +
                    scale_y_continuous(expand = c(0, 0), limits=c(0,70)) +  
                    scale_x_discrete(expand = c(0, 0.15)) +
                    theme(axis.text.x = element_text(angle = 45, hjust = 1), legend.position = "bottom") +
                    facet_grid(scenario~strategy)
        
### EXPORT TO FOLDER
setwd(path_figures)
tiff('scenario_results.tiff', units="in", width=8, height=9, res=300)
print(scenario_results)
dev.off()

#################################
# Total cost 
#################################

all_scenarios <- read_in_data("output_distribution_upgrade_costs_*.csv")

all_scenarios <- all_scenarios[which(all_scenarios$timestep==2019),] 

all_scenarios <- all_scenarios[which(all_scenarios$scenario=='Baseline Take-up'),] 

premises_by_dp <- read_in_data("output_premises_by_distribution_*.csv")

premises_by_dp <- premises_by_dp[which(premises_by_dp$timestep==2019),] 

premises_by_dp <- premises_by_dp[which(premises_by_dp$scenario=='Baseline Take-up'),] 

premises_by_dp$premises <- premises_by_dp$value

premises_by_dp <- select(premises_by_dp, region, premises)

all_scenarios <- merge(all_scenarios, premises_by_dp, by.x="region", by.y="region")

all_scenarios$cost_per_premises <- round(all_scenarios$value / all_scenarios$premises,0)

total_cost_results_dp <- ggplot(data=all_scenarios, aes(all_scenarios$value)) + 
                      geom_histogram(aes(y =..density..), 
                                     breaks=seq(0, 30000, by = 1000), 
                                     col="red", 
                                     fill="green", 
                                     alpha = .2) + 
                      geom_density(col=3) + 
                      labs(title="Density Plot of Cost Per Distribution Point") +
                      labs(x="Technology Upgrade Cost per Distribution Point", y="Count") +
                      facet_grid(~tech) +
                      scale_y_continuous(expand = c(0, 0)) + 
                      scale_x_continuous(expand = c(0, 0), limits=c(0,60000)) 

### EXPORT TO FOLDER
setwd(path_figures)
tiff('total_cost_results_dp.tiff', units="in", width=8, height=9, res=300)
print(total_cost_results_dp)
dev.off()

all_scenarios <- select(all_scenarios, region, tech, cost_per_premises)

all_scenarios <- unique(all_scenarios)

all_scenarios <- all_scenarios[which(all_scenarios$cost_per_premises>0),] 

all_scenarios <- all_scenarios[!(all_scenarios$cost_per_premises== Inf),] 

total_cost_results_prem <- ggplot(data=all_scenarios, aes(all_scenarios$cost_per_premises)) + 
  geom_histogram(aes(y =..density..), 
                 breaks=seq(0, 10000, by = 100), 
                 col="red", 
                 fill="green", 
                 alpha = .2) + 
  geom_density(col=3) + 
  labs(title="Density Plot of Cost Per Premises") +
  labs(x="Technology Upgrade Cost per Distribution Point", y="Density") +
  facet_grid(~tech) +
  scale_y_continuous(expand = c(0, 0)) + 
  scale_x_continuous(expand = c(0, 0), limits=c(0,4750)) 

### EXPORT TO FOLDER
setwd(path_figures)
tiff('total_cost_results_prem.tiff', units="in", width=8, height=9, res=300)
print(total_cost_results_prem)
dev.off()

#################################
# Mean cost per premises connected
#################################

all_scenarios <- read_in_data("output_premises_upgrade_costs*.csv")

mean_cost_per_premises <- all_scenarios %>%
  group_by(timestep, scenario, strategy, tech) %>%
  summarise(value=mean(value))

prem_cost_results <- ggplot(data=mean_cost_per_premises, 
                            aes(x=timestep, y=value, group = tech, colour = tech)) + geom_line() +
  labs(y = "Mean cost per premises connected", x = "Year", colour = "Technology", 
       title = "Technology Rollout by Scenario and Strategy") +
  scale_y_continuous(expand = c(0, 0)) + 
  scale_x_discrete(expand = c(0, 0)) +
  theme(axis.text.x = element_text(angle = 45, hjust = 1), legend.position = "bottom") +
  facet_grid(scenario~strategy)

### EXPORT TO FOLDER
setwd(path_figures)
tiff('prem_cost_results.tiff', units="in", width=8, height=9, res=300)
print(prem_cost_results)
dev.off()

#################################
# Premises connected geographically
#################################

all_scenarios <- read_in_data("*regions_lad2016_intervals_annual.csv")

all_scenarios <- all_scenarios[which(all_scenarios$scenario=='Baseline Take-up'),] 

all_scenarios <- all_scenarios[which(all_scenarios$timestep== 2020 |
                                      all_scenarios$timestep== 2022 |
                                      all_scenarios$timestep== 2024 |
                                      all_scenarios$timestep== 2026 |
                                      all_scenarios$timestep== 2028 |
                                      all_scenarios$timestep== 2030),] 

all_scenarios <-all_scenarios[(all_scenarios$value > 0),]

all_scenarios$value <- cut(all_scenarios$value, 10)

setwd(path_shapes)

all.shp <- readShapeSpatial("simplified_LADS_WGS84") 

all.shp <- fortify(all.shp, region = "LAD12CD")

all.shp <- merge(all.shp, all_scenarios, by.x="id", by.y="region", all.y = TRUE)

all.shp <- all.shp[order(all.shp$order),]

spatial_rollout <- ggplot() + geom_polygon(data = all.shp, aes(x = long, y = lat, group=group, 
                                                               fill = value), color = NA) + 
  coord_equal() +
  scale_fill_brewer(palette="Spectral", name = expression('Technology Rollout'),
                    labels = comma, direction=-1, drop = TRUE) +
  theme(axis.text = element_blank(), axis.ticks = element_blank(), axis.title = element_blank(), 
        legend.position = "bottom") +
  guides(fill = guide_legend(reverse = TRUE)) + 
  facet_grid(strategy~timestep)

### EXPORT TO FOLDER
setwd(path_figures)
tiff('spatial_rollout.tiff', units="in", width=12, height=5, res=300)
print(spatial_rollout)
dev.off()


