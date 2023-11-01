import os
import glob
import argparse
import gzip
from random import shuffle
from tqdm import tqdm
import numpy as np

import torch
from torch_geometric.data import Data

def np_to_pyg(events, arr, target, i_out, n_out):
    '''Convert numpy array to pytorch geometric data'''
    # - 0 is vertical (1) or horizontal (0)
    # - 1-3 x/y/z positions of one edge of the strip
    # - 4-6 x/y/z positions of the other edge of the strip
    # - 7 detector type (0: none 1: scifi, 2: us, 3: ds)
    for i in range(i_out, len(arr), n_out):
        row = arr[i]
        vertical = torch.tensor(row[:, 0], dtype=torch.float)
        strip_x = torch.tensor(row[:, 1], dtype=torch.float)
        strip_y = torch.tensor(row[:, 2], dtype=torch.float)
        strip_z = torch.tensor(row[:, 3], dtype=torch.float)
        strip_x_end = torch.tensor(row[:, 4], dtype=torch.float)
        strip_y_end = torch.tensor(row[:, 5], dtype=torch.float)
        strip_z_end = torch.tensor(row[:, 6], dtype=torch.float)
        det = torch.tensor(row[:, 7], dtype=torch.float)

        all_vals = torch.stack([vertical, strip_x, strip_y, strip_z, strip_x_end, strip_y_end, strip_z_end, det], dim=1)
        all_vals = all_vals[det != 0]

        # 0: z value where object is created, 1: PDG ID, 2: pZ (longitudinal momentum)
        t = torch.tensor(target[i], dtype=torch.float)

        data = Data(y=t[1], start_z=t[0], pz=t[2], vertical=all_vals[:, 0], strip_x=all_vals[:, 1], strip_y=all_vals[:, 2], strip_z=all_vals[:, 3], strip_x_end=all_vals[:, 4], strip_y_end=all_vals[:, 5], strip_z_end=all_vals[:, 6], det=all_vals[:, 7])
        events.append(data)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert numpy arrays to pytorch geometric data')
    parser.add_argument("-i", "--input_files", dest="input_files", help="Input npz files (with wildcard)", required=False, default='/Users/jan/cernbox/sndml/*npz')
    parser.add_argument('-o', '--output_dir', dest='output_dir', help='Output directory', required=False, default='output')
    parser.add_argument('-n', '--n_files', dest='n_files', help='Number of output files to be created', required=False, default=30)

    args = parser.parse_args()

    output_dir = args.output_dir
    in_files = glob.glob(args.input_files)
    print('Input files: ', in_files)
    print('Output directory: ', output_dir)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for i_out in tqdm(range(args.n_files)):

        events = []
        for i, in_file_name in enumerate(tqdm(in_files)):
            with np.load(in_file_name) as in_file:
                arr = in_file['hits']
                target = in_file['targets']
                
                np_to_pyg(events, arr, target, i_out, args.n_files)

        with gzip.open(f'{output_dir}/output_{i_out}.pt.gz', 'wb') as f:
            shuffle(events)
            torch.save(events, f)

