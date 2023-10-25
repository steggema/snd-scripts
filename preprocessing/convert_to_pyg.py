import os
import glob
import argparse
import gzip
from tqdm import tqdm
import numpy as np

import torch
from torch_geometric.data import Data

def np_to_pyg(arr, target, out):
    '''Convert numpy array to pytorch geometric data'''
    # - 0 is vertical (1) or horizontal (0)
    # - 1-3 x/y/z positions of one edge of the strip
    # - 4-6 x/y/z positions of the other edge of the strip
    # - 7 detector type (0: none 1: scifi, 2: us, 3: ds)

    vertical = torch.tensor(arr[:, 0, :], dtype=torch.float)
    strip_x = torch.tensor(arr[:, 1, :], dtype=torch.float)
    strip_y = torch.tensor(arr[:, 2, :], dtype=torch.float)
    strip_z = torch.tensor(arr[:, 3, :], dtype=torch.float)
    strip_x_end = torch.tensor(arr[:, 4, :], dtype=torch.float)
    strip_y_end = torch.tensor(arr[:, 5, :], dtype=torch.float)
    strip_z_end = torch.tensor(arr[:, 6, :], dtype=torch.float)
    det = torch.tensor(arr[:, 7, :], dtype=torch.float)

    target = torch.tensor(target, dtype=torch.float)

    data = Data(y=target, vertical=vertical, strip_x=strip_x, strip_y=strip_y, strip_z=strip_z, strip_x_end=strip_x_end, strip_y_end=strip_y_end, strip_z_end=strip_z_end, det=det)

    # Save the data object
    with gzip.open(out, 'wb') as f:
        torch.save(data, f)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert numpy arrays to pytorch geometric data')
    parser.add_argument("-i", "--input_dir", dest="input_dir", help="Location of input npz files", required=False, default='/Users/jan/cernbox/sndml/')
    parser.add_argument("-n", "--n_files", dest="n_files", type=int, help="Number of files to process", required=False, default=20)
    parser.add_argument('-o', '--output_dir', dest='output_dir', help='Output directory', required=False, default='output')

    args = parser.parse_args()

    output_dir = args.output_dir

    print('Input directory: ', args.input_dir)
    print('Output directory: ', output_dir)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for i in tqdm(range(args.n_files)):
        in_file_name = os.path.join(args.input_dir, f'output_{i}.npz')
        in_target_name = os.path.join(args.input_dir, f'targets_{i}.npz')
        with np.load(in_file_name) as in_file, np.load(in_target_name) as in_target:
            arr = in_file['arr_0']
            target = in_target['arr_0']
            np_to_pyg(arr, target, f'{output_dir}/output_{i}.pt.gz')

