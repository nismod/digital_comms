#!/bin/bash
exchanges=`python scripts/network_cluster_input_files.py $1`

#echo $exchanges

# #seq 1 $count | parallel -n1 --no-notice ./plot_stations.py {}
parallel --sshloginfile nodeslist -n1 --no-notice --progress `pwd`/scripts/network_preprocess_input_files.sh ::: $exchanges

echo 'parallel processing complete'