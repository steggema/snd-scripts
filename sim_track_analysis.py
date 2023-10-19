import uproot
import pandas as pd
import numpy as np
from ROOT import TDatabasePDG
from awkward import Array, flatten, num


def read_branches(tree, b_names, entry_start, entry_stop):
    '''reading branches from entry_start to entry_stop'''
    if (entry_stop < entry_start):
        entry_stop = tree.num_entries

    #reading the branches
    branches = tree.arrays(b_names, entry_start=entry_start, entry_stop=entry_stop)
    #returning the produced array
    return branches

def read_track_branches(tree, prefix="MCTrack.f", entry_start=0, entry_stop=-1):
    '''reading MCTracks from entry_start to entry_stop'''

    suffixes = ["MotherId", "PdgCode", "StartX", "StartY", "StartZ", "Px", "Py", "Pz"]
    b_names = [prefix + suff for suff in suffixes]
    print(b_names)
    return read_branches(tree, b_names, entry_start, entry_stop)

def read_mcpoint_branches(tree, prefix="ScifiPoint.f", entry_start=0, entry_stop=-1):
    '''reading MCTracks from entry_start to last_entry'''
    if (entry_stop < entry_start):
        entry_stop = tree.num_entries  

    suffixes = ["PdgCode", "TrackID", "X", "Y", "Z", "Px", "Py", "Pz"]
    b_names = [prefix + suff for suff in suffixes]
    print(b_names)
    return read_branches(tree, b_names, entry_start, entry_stop)
    # #reading the branches
    # mcpoints = tree.arrays(b_names, entry_start = entry_start, entry_stop = last_entry)
    # #adding float interpretation manually
    # floatinterpretation = tree["MCTrack.fStartX"].interpretation
    # for name in b_names[2:]:
    #     mcpoints[name] = tree[name].array(floatinterpretation)
    # #returning the produced array
    # return mcpoints

pdg_db = TDatabasePDG.Instance()
def get_charge(pdg_id):
    particle = pdg_db.GetParticle(int(pdg_id))
    if particle: # not all particles are known
        return particle.Charge()
    return 0

f = uproot.open('/Users/jan/cernbox/ship.conical.Genie-TGeant4.root')
tree = f['cbmsim']
tracks = read_track_branches(tree, entry_stop=100)
sci_fi_points = read_mcpoint_branches(tree, entry_stop=100)

# Make a dictionary with all pdg ID -> charge translations
unique_pdgs = np.unique(flatten(tracks["MCTrack.fPdgCode"]).to_list())
pdg_charges = {pdg: get_charge(pdg) for pdg in unique_pdgs}

tracks["MCTrack.fCharge"] = [[pdg_charges[p] for p in sub_list] for sub_list in tracks["MCTrack.fPdgCode"].to_list()]

neutrino_daughters = tracks[np.logical_and(tracks["MCTrack.fMotherId"]==0, np.abs(tracks["MCTrack.fCharge"]) > 0)]
neutrino_daughters['MCTrack.fP'] = np.sqrt(neutrino_daughters['MCTrack.fPx']**2 + neutrino_daughters['MCTrack.fPy']**2 + neutrino_daughters['MCTrack.fPz']**2)

print(num(neutrino_daughters["MCTrack.fPdgCode"], axis=1))

# make a plot of the number of daughters per neutrino with matplotlib
import matplotlib.pyplot as plt
plt.hist(num(neutrino_daughters["MCTrack.fPdgCode"], axis=1), bins=10)
plt.show()

plt.hist(flatten(neutrino_daughters['MCTrack.fP'], axis=None), bins=50)
plt.show()

# Loop over events and make some event displays
for i in range(10):
    tr = tracks[i]

