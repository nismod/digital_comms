###VISUALISE MODEL OUTPUTS###
library(tidyverse)
library(maptools)
library(ggmap)
library(scales)
library(RColorBrewer)
library(ggpubr)       

path <- "C:\\Users\\edwar\\Desktop\\GitHub\\digital_comms\\results\\digital_comms_test\\digital_comms\\decision_0"
path_figures <- "C:\\Users\\edwar\\Desktop\\GitHub\\digital_comms\\data_visualisation\\digital_comms_test"

#################################
# desire to adopt
#################################

setwd(path)

files <- list.files(pattern=glob2rx("output_premises_adoption_desirability*.csv"))

# First apply read.csv, then rbind
all_scenarios = do.call(rbind, lapply(files, function(x) read.csv(x, stringsAsFactors = FALSE)))

all_scenarios$timestep <- as.factor(all_scenarios$timestep)

adoption_desireability <- ggplot(data=all_scenarios, aes(x=timestep, y=value, group = 1)) + geom_line() +
                          labs(y = "Number of households", x = "Year", title = "Total Adoption Desirability")

### EXPORT TO FOLDER
setwd(path_figures)
tiff('adoption_desireability.tiff', units="in", width=9, height=9, res=300)
print(adoption_desireability)
dev.off()

#################################
# % of premises with ftttp
#################################

setwd(path)

files <- list.files(pattern=glob2rx("output_premises_with_fttp*.csv"))

# First apply read.csv, then rbind
all_scenarios = do.call(rbind, lapply(files, function(x) read.csv(x, stringsAsFactors = FALSE)))

# all_scenarios <- all_scenarios %>%
#   ungroup() %>%
#   mutate(value = cumsum(value))


all_scenarios$timestep <- as.factor(all_scenarios$timestep)

premises_with_fttp <- ggplot(data=all_scenarios, aes(x=timestep, y=value, group = 1)) + geom_line() +
                      labs(y = "Number of households", x = "Year", title = "Premises with FTTP")

### EXPORT TO FOLDER
setwd(path_figures)
tiff('premises_with_fttp.tiff', units="in", width=9, height=9, res=300)
print(premises_with_fttp)
dev.off()

#################################
# % of premises with fttdp
#################################

# setwd(path)
# 
# files <- list.files(pattern=glob2rx("output_percentage_of_premises_with_fttdp*.csv"))
# 
# # First apply read.csv, then rbind
# all_scenarios = do.call(rbind, lapply(files, function(x) read.csv(x, stringsAsFactors = FALSE)))
# 
# # all_scenarios <- all_scenarios %>%
# #   ungroup() %>%
# #   mutate(value = cumsum(value))
# 
# all_scenarios$timestep <- as.factor(all_scenarios$timestep)
# 
# premises_with_fttdp <- ggplot(data=all_scenarios, aes(x=timestep, y=value, group = 1)) + geom_line() +
#   labs(y = "Number of households", x = "Year", title = "Premises with FTTdp")
# 
# ### EXPORT TO FOLDER
# setwd(path_figures)
# tiff('premises_with_fttdp.tiff', units="in", width=9, height=9, res=300)
# print(premises_with_fttdp)
# dev.off()

#################################
# cost of distribution upgrades
#################################

setwd(path)

files <- list.files(pattern=glob2rx("output_distribution_upgrade_costs_fttp*.csv"))

# First apply read.csv, then rbind
all_scenarios = do.call(rbind, lapply(files, function(x) read.csv(x, stringsAsFactors = FALSE)))

all_scenarios <- all_scenarios %>%
  group_by(timestep) %>%
  summarise(value = sum(value))

all_scenarios <- select(all_scenarios, timestep, value)

all_scenarios <- all_scenarios %>%
  ungroup() %>%
  mutate(value = cumsum(value))

all_scenarios$timestep <- as.factor(all_scenarios$timestep)

distribution_upgrade_costs <- ggplot(data=all_scenarios, aes(x=timestep, y=(value/1000000), group = 1)) + geom_line() +
                              labs(y = "Upgrade costs (£ Millions)", x = "Year", title = "FTTP Upgrade Costs")

### EXPORT TO FOLDER
setwd(path_figures)
tiff('distribution_upgrade_costs.tiff', units="in", width=9, height=9, res=300)
print(distribution_upgrade_costs)
dev.off()

#################################
# arrange outputs
#################################

multiplot <- ggarrange(adoption_desireability, premises_with_fttp, distribution_upgrade_costs, 
                       labels = c("A", "B", "C"),
                       ncol = 2, nrow = 2)

### EXPORT TO FOLDER
setwd(path_figures)
tiff('multiplot.tiff', units="in", width=9, height=9, res=300)
print(multiplot)
dev.off()

