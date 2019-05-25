#!/bin/bash

# python scripts/mobile_cluster_input_files.py $1 | \
#     parallel python `pwd`/digital_comms/mobile_network/transmitter_module.py {}

sectors=$(python scripts/mobile_cluster_input_files.py $1)

for sector in $(sectors)
  do
    `which python` `pwd`/digital_comms/mobile_network/transmitter_module.py $sector
done
