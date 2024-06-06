'''Convert SND numpy arrays produced with digi_to_ml.py to awkward arrays.
'''


import os
import glob
import argparse
from typing import Tuple

from tqdm import tqdm
import numpy as np
import awkward as ak

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
    84: 4,
    13: 5,
    -13:5
}

def pdg_id_to_t(pdg_id: int) -> int:
    return pdgid_to_target[pdg_id]

def np_to_ak(arr, target) -> Tuple[ak.Array, ak.Array]:
    '''Convert numpy hits and target arrays to 
    corresponding awkward arrays'''

    arr = np.swapaxes(arr, 1, 2)

    hits = ak.from_numpy(arr)

    hits = ak.from_regular(hits, axis=1)

    # Remove hits where detector type is 0 (no actual hit)
    hits = hits[hits[:,:,7] > 0]

    # - 0 is vertical (1) or horizontal (0)
    # - 1-3 x/y/z positions of one edge of the strip
    # - 4-6 x/y/z positions of the other edge of the strip
    # - 7 detector type (0: none 1: scifi, 2: us, 3: ds)

    hits = ak.zip({
        'vertical':hits[:,:,0], 
        'strip_x':hits[:,:,1],
        'strip_y':hits[:,:,2],
        'strip_z':hits[:,:,3],
        'strip_x_end':hits[:,:,4],
        'strip_y_end':hits[:,:,5],
        'strip_z_end':hits[:,:,6],
        'det':hits[:,:,7]
        })
    
    targets = ak.zip({
        'start_z':ak.from_numpy(np.ascontiguousarray(target[:,0])),
        'pdg':ak.from_numpy(np.vectorize(pdg_id_to_t)(np.ascontiguousarray(target[:,1]))),
        'pz':ak.from_numpy(np.ascontiguousarray(target[:,2]))
    })

    return hits, targets

def np_to_ak_counts(arr, target, counts) -> Tuple[ak.Array, ak.Array]:
    '''Convert numpy hits and target arrays to 
    corresponding awkward arrays'''

    hits = ak.unflatten(arr, counts)

    # - 0 is vertical (1) or horizontal (0)
    # - 1-3 x/y/z positions of one edge of the strip
    # - 4-6 x/y/z positions of the other edge of the strip
    # - 7 detector type (0: none 1: scifi, 2: us, 3: ds)

    hits = ak.zip({
        'vertical':hits[:,:,0], 
        'strip_x':hits[:,:,1],
        'strip_y':hits[:,:,2],
        'strip_z':hits[:,:,3],
        'strip_x_end':hits[:,:,4],
        'strip_y_end':hits[:,:,5],
        'strip_z_end':hits[:,:,6],
        'det':hits[:,:,7]
        })
    
    targets = ak.zip({
        'start_z':ak.from_numpy(np.ascontiguousarray(target[:,0])),
        'pdg':ak.from_numpy(np.vectorize(pdg_id_to_t)(np.ascontiguousarray(target[:,1]))),
        'pz':ak.from_numpy(np.ascontiguousarray(target[:,2]))
    })

    return hits, targets



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert numpy arrays to pytorch geometric data')
    parser.add_argument("-i", "--input_files", dest="input_files", help="Input npz files (with wildcard)", required=False, default='/Users/jan/cernbox/sndml/neutrino_0.npz')
    parser.add_argument('-o', '--output_folder', dest='output_folder', help='Output folder', required=False, default='output/')
    parser.add_argument('-c', '--from_counts', dest='from_counts', help='Whether the array is flat and accompanied by a counts array', required=False, default=True)

    args = parser.parse_args()

    output_folder = args.output_folder
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    in_files = glob.glob(args.input_files)
    print('Input files: ', in_files)
    print('Output folder: ', output_folder)

    for in_file_name in tqdm(in_files, leave=False):
        with np.load(in_file_name) as in_file:
            arr = in_file['hits']
            target = in_file['targets']
            if not args.from_counts:
                hits, targets = np_to_ak(arr, target)
            else:
                counts = in_file['n_hits']
                hits, targets = np_to_ak_counts(arr, target, counts)
            out_file_name = os.path.splitext(os.path.basename(in_file_name))[0]
            ak.to_parquet(hits, os.path.join(output_folder, f'{out_file_name}_hits.pt'))
            ak.to_parquet(targets, os.path.join(output_folder, f'{out_file_name}_targets.pt'))
