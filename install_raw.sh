#! /bin/bash

openneuro_derivatives="/home/remi/datalad/datasets.datalad.org/openneuro-derivatives"

raw_datasets=$(find ${openneuro_derivatives} -type d -name raw)

cwd=$(pwd)

for dataset in ${raw_datasets}; do

    echo ${dataset}
    cd ${dataset} || exit
    cd ..

    datalad install raw

    # git reset --hard

    cd ${cwd} || exit

done
