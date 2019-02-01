#!/bin/bash
pcd_sectors=`python scripts/mobile_cluster_input_files.py $1`

#seq 1 $count | parallel -n1 --no-notice ./plot_stations.py {}
#parallel --sshloginfile nodeslist -n1 --no-notice --progress `pwd`/digital_comms/mobile_network/transmitter_module.sh ::: $exchanges

echo pcd_sectors

python `pwd`/digital_comms/mobile_network/transmitter_module.py ::: $pcd_sectors