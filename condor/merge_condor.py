'''Python script that merges the numpy npz or npy files that come out of the condor pre-processing'''

import numpy as np

import glob

import argparse
parser = argparse.ArgumentParser(description='Merge npz files')
parser.add_argument("-i", "--input_files", dest="input_files", help="Location of input npz files with wildcard", required=False, default='/afs/cern.ch/user/s/steggema/work/snd/data/neutrino/sndlhc_13TeV_down_volTarget_100fb-1_SNDG18_02a_01_000/*/*npz')
parser.add_argument('-o', '--output_file', dest='output_file', help='Output file name', required=False, default='output')
parser.add_argument('-n', '--n_files_merge', dest='n_merge', type=int, help='Number of input files for one output file', required=False, default=20)

args = parser.parse_args()

input_files = glob.glob(args.input_files)
output_file = args.output_file

print('Input files: ', input_files)
print('Output file: ', output_file)

j = 0

# Loop over the rest
for i, input_file in enumerate(input_files):
    if i % args.n_merge == 0:
        data = np.load(input_file)
        hits = data['hits']
        targets = data['targets']
    else:
        with np.load(input_file) as data_in:
            print('Merging ', input_file)
            hits = np.concatenate([data, data_in['hits']])
            targets = np.concatenate([targets, data_in['targets']])

    if (i + 1) % args.n_merge == 0 or i == len(input_files) - 1:
        # Save the output
        out_name = f'{output_file}_{j}.npz'
        print('Saving to ', out_name)
        np.savez_compressed(out_name, hits=hits, targets=targets)
        j += 1


