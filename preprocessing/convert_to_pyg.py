'''Convert SND numpy arrays produced with digi_to_ml.py to pytorch geometric data.
Takes a list of input files (with wildcard) and produces a specified number of files N.
Combines events from all input files with the following algorithm:
- Take every Nth event from each input file.
- Shuffle the events.
- Remove events with no hits.
Note that this leads to slow runtime since each input file is read multiple times 
(we can't hold of all events in memory at once).
'''


import os
import glob
import argparse
import gzip
from random import shuffle
from tqdm import tqdm
import numpy as np

import torch
from torch_geometric.data import Data

pdgid_to_target = {
    12: 0,
    -12: 0,
    14: 1,
    -14: 1,
    16: 2,
    -16: 2,
    2112: 3,
    2212: 3,
    # NC
    112: 4,
    88: 4,
    114: 4,
    86: 4,
    116: 4,
    84: 4
}

pdgid_to_target_3classes = {
    12: 0, 
    -12: 0,
    14: 1,
    -14: 1,

    # NC
    112: 2,
    88: 2,
    114: 2,
    86: 2,
    116: 2,
    84: 2
}

def np_to_pyg(events, arr, target, n_class):
    '''Convert numpy array to pytorch geometric data'''
    # - 0 is vertical (1) or horizontal (0)
    # - 1-3 x/y/z positions of one edge of the strip
    # - 4-6 x/y/z positions of the other edge of the strip
    # - 7 detector type (0: none 1: scifi, 2: us, 3: ds)
    for i in range(len(arr)):
        row = arr[i]
        vertical = torch.tensor(row[0], dtype=torch.float)
        if len(vertical) == 0:
            continue
        
        strip_x = torch.tensor(row[1], dtype=torch.float)
        strip_y = torch.tensor(row[2], dtype=torch.float)
        strip_z = torch.tensor(row[3], dtype=torch.float)
        strip_x_end = torch.tensor(row[4], dtype=torch.float)
        strip_y_end = torch.tensor(row[5], dtype=torch.float)
        strip_z_end = torch.tensor(row[6], dtype=torch.float)
        det = torch.tensor(row[7], dtype=torch.float)

        all_vals = torch.stack([vertical, strip_x, strip_y, strip_z, strip_x_end, strip_y_end, strip_z_end, det], dim=1)
        all_vals = all_vals[det != 0]

        # 0: z value where object is created, 1: PDG ID, 2: pZ (longitudinal momentum)
        t = torch.tensor(target[i], dtype=torch.float)

        #print("event id {}".format(t[3]))
        if (n_class==3):
            if(int(t[1]) == 16 or int(t[1]) == -16 or int(t[1]) == 2112 or int(t[1]) == 2212):
                #print("dumping ", i, " pdgId: ", int(t[1]) )
                continue
            data = Data(y=torch.tensor(pdgid_to_target_3classes[int(t[1])], dtype=torch.long), start_z=t[0], pz=t[2],event_id=t[3],vertical=all_vals[:, 0], strip_x=all_vals[:, 1], strip_y=all_vals[:, 2], strip_z=all_vals[:, 3], strip_x_end=all_vals[:, 4], strip_y_end=all_vals[:, 5], strip_z_end=all_vals[:, 6], det=all_vals[:, 7])
            events.append(data)
        elif(n_class==5):
            data = Data(y=torch.tensor(pdgid_to_target[int(t[1])], dtype=torch.long), start_z=t[0], pz=t[2], event_id=t[3], vertical=all_vals[:, 0], strip_x=all_vals[:, 1], strip_y=all_vals[:, 2], strip_z=all_vals[:, 3], strip_x_end=all_vals[:, 4], strip_y_end=all_vals[:, 5], strip_z_end=all_vals[:, 6], det=all_vals[:, 7])
            events.append(data)
        else:
            raise RuntimeError("number of classes of particles do not match")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert numpy arrays to pytorch geometric data')
    parser.add_argument("-i", "--input_dir", dest="input_dir", help="Input directory of npz files", required=False, default='/Users/jan/cernbox/sndml/')
    parser.add_argument('-o', '--output_dir', dest='output_dir', help='Output directory', required=False, default='output')
    parser.add_argument('-n', '--n_files', dest='n_files', help='Number of output files to be created',  type =int, required=False, default=5)
    parser.add_argument('-c', '--n_class', dest='n_class', help='Number of classes of particles', required=False, default=5)
    parser.add_argument('-s', '--split_ratio', dest='split_ratio', help='split ratio of train val and test set, e.g [0.8, 0.1, 0.1]', required=False, default=[0.8, 0.1, 0.1])

    args = parser.parse_args()

    output_dir = args.output_dir
    npz_files = [file for file in os.listdir(args.input_dir) if file.endswith(".npz")]

    print("Input directory: ", args.input_dir)
    print('Input files: ', npz_files)
    print('Output directory: ', output_dir)

    #Shuffle the list of files
    shuffle(npz_files)

    # Calculate the number of files for each split
    total_files = len(npz_files)
    num_train = int(args.split_ratio[0] * total_files)
    num_val = int(args.split_ratio[1]* total_files)

    # Split the files
    train_files = npz_files[:num_train]
    val_files = npz_files[num_train:num_train + num_val]
    test_files = npz_files[num_train + num_val:]

    # Create subdirectories in the destination directory
    train_dir = os.path.join(output_dir, 'train')
    val_dir = os.path.join(output_dir, 'val')
    test_dir = os.path.join(output_dir, 'test')

    split_dirs = [train_dir, val_dir, test_dir]
    split_files = [train_files,val_files,test_files]

    for idx, (out_dir, out_files) in enumerate(zip(split_dirs, split_files)):
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
        
        print("processing on {} set".format(out_dir.split('/')[-1]))
        for i, in_file_name in enumerate(tqdm(out_files)):
            events = []
            in_file_name = os.path.join(args.input_dir, in_file_name)
            #print(in_file_name)
            with np.load(in_file_name) as in_file:
                arr = in_file['hits']
                target = in_file['targets']
                np_to_pyg(events, arr, target, args.n_class)

            shuffle(events)
            torch.save(events, f"{out_dir}/{in_file_name.split('_')[-1].split('.')[0]}.pt")