'''Creates file lists for condor jobs. 
The MC and data are not saved in a very systematic way in SND, so need targeted code for diferent datasets.
'''


import os
from glob import glob

# Neutrons
base_dir = '/eos/experiment/sndlhc/users/marssnd/PGsim/neutrons/'
partitions_to_merge = 150
with open('paramlist_neutronMC.txt', 'w') as out_file:
    for sample in os.listdir(base_dir):
        if 'tgtarea' in sample:
            sample_dir = os.path.join('/eos/experiment/sndlhc/users/marssnd/PGsim/neutrons/', sample, 'Ntuples')
            partitions = os.listdir(sample_dir)
            partitions = [int(i) for i in partitions]
            max_partition = max(partitions)
            min_partition = min(partitions)
            start, end = min_partition, partitions_to_merge + min_partition
            while start <= max_partition:
                out_file.write(f"neutron {start} {sample_dir} {end-1}\n")
                start += partitions_to_merge
                end += partitions_to_merge
                break # only first file

# Neutrinos
partitions_to_merge = 1
with open('paramlist_neutrinoMC.txt', 'w') as out_file:
    sample_dir = os.path.join('/eos/experiment/sndlhc/MonteCarlo/Neutrinos/Genie/sndlhc_13TeV_down_volTarget_100fb-1_SNDG18_02a_01_000')
    partitions = os.listdir(sample_dir)
    partitions = [int(i) for i in partitions]
    max_partition = max(partitions)
    min_partition = min(partitions)
    start, end = min_partition, partitions_to_merge + min_partition
    while start <= max_partition:
        out_file.write(f"neutrino {start} {sample_dir} {end-1}\n")
        start += partitions_to_merge
        end += partitions_to_merge

# 2023 data
files_to_merge = 20
with open('paramlist_data_2023.txt', 'w') as out_file:
    sample_dir = os.path.join('/eos/experiment/sndlhc/convertedData/physics/2023_reprocess/')
    files = glob(sample_dir+'*/*.root')
    partitions = sorted([int(i[-24:-20]) for i in files if 'run_' in i])
    starts = partitions[::files_to_merge]
    ends = partitions[files_to_merge-1::files_to_merge]
    if len(starts) > len(ends):
        ends.append(partitions[-1])
    prev_start, prev_end = -1, -1
    for start, end in zip(starts, ends):
        if start == prev_end:
            start += 1
            if start > end:
                continue
        out_file.write(f"neutrino {start} {sample_dir} {end} -d\n")
        prev_start, prev_end = start, end
