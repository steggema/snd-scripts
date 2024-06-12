'''Creates file lists for condor jobs. 
The MC and data are not saved in a very systematic way in SND, so need targeted code for diferent datasets.
'''


import os
from glob import glob

def write_paramlist(out_file, sample_dir, partitions_to_merge):
    partitions = [int(i) for i in os.listdir(sample_dir)]
    min_partition, max_partition =  min(partitions), max(partitions)
    start, end = min_partition, partitions_to_merge + min_partition
    while start <= max_partition:
        out_file.write(f"neutron {start} {sample_dir} {min(end-1, max_partition)}\n")
        start += partitions_to_merge
        end += partitions_to_merge

def write_nh_paramlist(out_file_name, base_dir, partitions_to_merge):
    ''' Writes the list for neutral hadron samples.'''
    with open(out_file_name, 'w') as out_file:
        for sample in os.listdir(base_dir):
            # For particle gun, only consider target area files
            if 'PGsim' in base_dir and not 'tgtarea' in sample:
                continue
            sample_dir = os.path.join(base_dir, sample, 'Ntuples')
            write_paramlist(out_file, sample_dir, partitions_to_merge)
            

# Neutrons and kaons
# base_dir = '/eos/experiment/sndlhc/users/marssnd/PGsim/neutrons/'
write_nh_paramlist('paramlist_neutronMC.txt', '/eos/experiment/sndlhc/MonteCarlo/NeutralHadrons/FTFP_BERT/neutrons/', 100)
write_nh_paramlist('paramlist_kaonMC.txt', '/eos/experiment/sndlhc/MonteCarlo/NeutralHadrons/FTFP_BERT/kaons/', 100)

# Neutrinos
partitions_to_merge = 1
with open('paramlist_neutrinoMC.txt', 'w') as out_file:
    sample_dir = os.path.join('/eos/experiment/sndlhc/MonteCarlo/Neutrinos/Genie/sndlhc_13TeV_down_volTarget_100fb-1_SNDG18_02a_01_000')
    write_paramlist(out_file, sample_dir, partitions_to_merge)

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
