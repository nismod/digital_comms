#!/bin/bash
. /etc/profile.d/profile.sh
echo Pre-processing $1: Running on `hostname`

source activate digital_comms
cd /ouce-home/projects/mistral/nismod/digital_comms2/

cd /soge-home/projects/mistral/nismod/digital_comms/data/digital_comms/intermediate
mkdir -p $1
touch $1/log.txt

python `pwd`/scripts/network_preprocess_input_files.py $1 &> data/processed_cluster/$1/log.txt
