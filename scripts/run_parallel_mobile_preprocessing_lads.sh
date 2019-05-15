#!/bin/bash

#seq 1 $count | parallel -n1 --no-notice ./plot_stations.py {}
#parallel --sshloginfile nodeslist -n1 --no-notice --progress `pwd`/digital_comms/mobile_network/transmitter_module.sh ::: $exchanges

echo Pre-processing $1

python scripts/mobile_cluster_lad_input_files.py $1 | \
    parallel python `pwd`/scripts/mobile_preprocess_lookup_tables.py {}
