###VISUALISE MODEL OUTPUTS###
#library(ggplot2)
#library(dplyr)
library(tidyverse)
#install.packages("maptools")
library(maptools)
#install.packages("rgeos")
library(rgeos)
#install.packages("Cairo")
library(Cairo)
#install.packages("ggmap")
library(ggmap)
library(scales)
library(RColorBrewer)
#library(ineq)
#install.packages("ggpubr")
library(ggpubr)       

set.seed(8000)

path <- "C:\\Users\\edwar\\Desktop\\GitHub\\digital_comms\\results\\digital_comms_test\\digital_comms\\decision_0"

setwd(path)
metric_files <- list.files(path, pattern = c("(national)"))

#initialised empty dataframe
empty_df <- data.frame(timestep=numeric(),
                       region=character(), 
                       interval=numeric(), 
                       value=numeric()) 

import_function = lapply(metric_files, function(x) {
  DF <- read.csv(x, header = T, sep = ",")
  DF_Merge <- merge(empty_df, DF, all = T)
  DF_Merge$file <- as.factor(x)
  return(DF_Merge)})

all_scenarios <- do.call(rbind, import_function)

ggplot(data=all_scenarios, aes(x=timestep, y=value)) +
  geom_line()


