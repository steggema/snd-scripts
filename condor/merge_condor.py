'''Python script that merges the numpy npz files that come out of the condor pre-processing'''

import numpy as np

import glob

import argparse
parser = argparse.ArgumentParser(description='Merge npz files')
parser.add_argument("-mc", "--input_files", dest="input_files", help="Location of input npz files with wildcard", required=False, default='/afs/cern.ch/user/s/steggema/work/snd/data/neutrino/sndlhc_13TeV_down_volTarget_100fb-1_SNDG18_02a_01_000/*/*npz')
parser.add_argument('-o', '--output_file', dest='output_file', help='Output file name', required=False, default='output.npz')

args = parser.parse_args()

input_files = glob.glob(args.input_files)
output_file = args.output_file

print('Input files: ', input_files)
print('Output file: ', output_file)

# Load the first file
data = np.load(input_files[0])['arr_0']
# Loop over the rest
for input_file in input_files[1:]:
    with np.load(input_file) as data_in:
        print('Merging ', input_file)
        data = np.concatenate(data, data_in['arr_0'])

# Save the output
print('Saving to ', output_file)
np.savez_compressed(output_file, data)
