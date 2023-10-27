#!/bin/bash
SNDLHC_mymaster=/afs/cern.ch/user/s/steggema/work/snd/
export ALIBUILD_WORK_DIR=$SNDLHC_mymaster/sw #for alienv

source /cvmfs/sndlhc.cern.ch/SNDLHC-2023/Aug30/setUp.sh
echo $SNDSW_ROOT
echo 'loading alienv'
eval `alienv load --no-refresh sndsw/latest`
echo $SNDSW_ROOT

MC_PATH="/eos/experiment/sndlhc/MonteCarlo/Neutrinos/Genie/sndlhc_13TeV_down_volTarget_100fb-1_SNDG18_02a_01_000" # This is the neutrino MC from here https://twiki.cern.ch/twiki/bin/view/SndLHC/NeutrinoMC
etype=$1
partition=$2
MC_PATH=$3
endpartition=$4

#4705 4654 4661 4713 4778 5113
OUTPUTDIR=/afs/cern.ch/user/s/steggema/work/snd/data/

# File=$OUTPUTDIR/ds_detid_time_p${partition}_${runN}.npy # sndsw_raw-${partition}_${runN}_muonReco.root
# echo $File
# checks
#if [ $(stat -c%s "$File") -gt 0 ]
#then
#   return
#else
/cvmfs/sndlhc.cern.ch/SNDLHC-2023/Aug30/sw/slc7_x86-64/Python/v3.8.12-local1/bin/python $SNDLHC_mymaster/snd-scripts/digi_to_ml.py -mc $MC_PATH -t $etype -p $partition -o $OUTPUTDIR -e $endpartition
#fi

