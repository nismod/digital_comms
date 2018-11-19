#!/bin/bash
. /etc/profile.d/profile.sh
echo Pre-processing $1: Running on `hostname`

source activate digital_comms
cd projects/digital_comms

cd /soge-home/projects/mistral/nismod/digital_comms
mkdir -p data/digital_comms/intermediate/$1
touch data/digital_comms/intermediate/$1/log.txt

python `pwd`/scripts/network_preprocess_input_files.py $1 &> data/processed_cluster/$1/log.txt