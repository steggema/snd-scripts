import os
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
            while end <= max_partition:
                out_file.write(f"neutron {start} {sample_dir} {end}\n")
                start += partitions_to_merge
                end += partitions_to_merge
                break # only first file

partitions_to_merge = 4
with open('paramlist_neutrinoMC.txt', 'w') as out_file:
    sample_dir = os.path.join('/eos/experiment/sndlhc/MonteCarlo/Neutrinos/Genie/sndlhc_13TeV_down_volTarget_100fb-1_SNDG18_02a_01_000')
    partitions = os.listdir(sample_dir)
    partitions = [int(i) for i in partitions]
    max_partition = max(partitions)
    min_partition = min(partitions)
    start, end = min_partition, partitions_to_merge + min_partition
    while end <= max_partition:
        out_file.write(f"neutrino {start} {sample_dir} {end}\n")
        start += partitions_to_merge
        end += partitions_to_merge

