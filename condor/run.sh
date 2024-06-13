#!/bin/bash
SNDLHC_mymaster=/afs/cern.ch/user/s/steggema/work/snd_lx9/
OUTPUTDIR=/afs/cern.ch/user/s/steggema/work/snd/data/

etype=$1
partition=$2
MC_PATH=$3
endpartition=$4
tag=$5
isdata=$6
(
    export ALIBUILD_WORK_DIR=$SNDLHC_mymaster/sw #for alienv

    source /cvmfs/sndlhc.cern.ch/SNDLHC-2023/Aug30/setUp.sh
    echo $SNDSW_ROOT
    echo 'loading alienv'
    eval `alienv load --no-refresh sndsw/latest`
    echo $SNDSW_ROOT

    /cvmfs/sndlhc.cern.ch/SNDLHC-2023/Aug30/bin/python $SNDLHC_mymaster/snd-scripts/digi_to_ml.py -mc $MC_PATH -t $etype -p $partition -o $OUTPUTDIR/$tag -e $endpartition $isdata
)
# Now convert to awkward
(
    source /afs/cern.ch/user/s/steggema/miniconda3/etc/profile.d/conda.sh
    conda activate ak
    python $SNDLHC_mymaster/snd-scripts/preprocessing/convert_to_awkward.py -i $OUTPUTDIR/$tag/hits_$partition.npz -o $OUTPUTDIR/$tag $isdata
    rm $OUTPUTDIR/$tag/hits_$partition.npz
)