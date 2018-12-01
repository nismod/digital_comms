#!/bin/bash
#exchanges=`python scripts/network_cluster_input_files.py`

exchanges = [
            'WEWPRI', # Primrose Hill (Inner London)
            'MYCHA', # Chapeltown (Major City)
            'STBNMTH', # Bournemouth (Minor City)
            'EACAM', # Cambridge (>20,000)
            'NEILB', # Ingleby Barwick(>10,000)
            'STWINCH', #Winchester (>3,000)
            'WWTORQ', #Torquay (>,1000)
            'EACOM' #Comberton (<1000)
            ]

#seq 1 $count | parallel -n1 --no-notice ./plot_stations.py {}
parallel --sshloginfile nodeslist -n1 --no-notice --progress `pwd`/scripts/network_preprocess_input_files.sh ::: $exchanges