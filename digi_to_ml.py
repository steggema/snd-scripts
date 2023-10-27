''' Script to create npy files as input for ML training.
Adapted from https://github.com/golovart/Napoli_emulsion/blob/main/SND/neutrino_ml/data_process/hit_sandbox.py
'''


## run example
# python -i hit_sandbox.py -mc /eos/experiment/sndlhc/MonteCarlo/Neutrinos/Genie/sndlhc_13TeV_down_volTarget_100fb-1_SNDG18_02a_01_000 -p 137 -t neutrino

## neutrino path: /eos/experiment/sndlhc/MonteCarlo/Neutrinos/Genie/sndlhc_13TeV_down_volTarget_100fb-1_SNDG18_02a_01_000/137/sndLHC.Genie-TGeant4_digCPP.root

## neutron path: /eos/experiment/sndlhc/users/marssnd/PGsim/neutrons/neu_20_30_double/Ntuples/137/sndLHC.PG_2112-TGeant4_digCPP.root

## event metadata format: [Startz, MCTrack[0].GetPdgCode(), MCTrack[1].GetPdgCode()]


import os #, atexit
from datetime import datetime
from tqdm import tqdm
import numpy as np
import ROOT


from argparse import ArgumentParser
parser = ArgumentParser()
parser.add_argument("-mc", "--inputmc_dir", dest="inputmc_dir", help="Monte Carlo input directory", required=False, default="/eos/experiment/sndlhc/MonteCarlo/Neutrinos/Genie/sndlhc_13TeV_down_volMuFilter_20fb-1_SNDG18_02a_01_000/")
parser.add_argument("-p", "--partition", dest="part", help="number of starting partition", default=0)
parser.add_argument("-e", "--end_partition", dest="end_part", type=int, help="number of ending partition", default=-1)
parser.add_argument("-o", "--outPath", dest="outPath", help="output directory", required=False,
                    default="/afs/cern.ch/user/s/steggema/work/snd/data/")
parser.add_argument("-t", "--type", dest="etype", help="event type to select", default='neutrino')
parser.add_argument("-n", "--nhitsmax", dest="nhitsmax", help="Maximum number of hits to save", default=4000)

options = parser.parse_args()
n_hits_max = int(options.nhitsmax)

import SndlhcGeo # import takes some time so putting it after the arg parser

# find geofile in the MC dir
mc_dir = os.path.join(options.inputmc_dir, str(options.part))
geo_path = None
for name in os.listdir(mc_dir):
    if 'geofile' in name:
        geo_path = os.path.join(mc_dir, name)
if geo_path is None:
    raise RuntimeError("no geofile found in the MC directory")

geo = SndlhcGeo.GeoInterface(geo_path)
lsOfGlobals = ROOT.gROOT.GetListOfGlobals()
lsOfGlobals.Add(geo.modules['Scifi'])
lsOfGlobals.Add(geo.modules['MuFilter'])
Scifi = geo.modules['Scifi']
Mufi = geo.modules['MuFilter']
nav = ROOT.gGeoManager.GetCurrentNavigator()

A, B = ROOT.TVector3(), ROOT.TVector3()
proc_start_time = datetime.now()

tchain = ROOT.TChain("cbmsim")

mc_file_path = None
for name in os.listdir(mc_dir):
    if name.endswith('digCPP.root'):
        mc_file_path = os.path.join(mc_dir, name)
if mc_file_path is None:
    raise RuntimeError("no MC digi file found in the MC directory")

tchain.Add(mc_file_path)  

if options.end_part > options.part:
    for part in range(int(options.part)+1, options.end_part+1):
        add_dir = os.path.join(options.inputmc_dir, str(part))
        for name in os.listdir(add_dir):
            if name.endswith('digCPP.root'):
                tchain.Add(os.path.join(add_dir, name))
                break
        else: 
            print('No digi file found for partition', part, 'in dir', add_dir)

## OUTPUT FILE
out_path = os.path.join(options.outPath, options.etype, *mc_dir.split('/')[-2:])
if not os.path.exists(out_path):
    print('Creating output directory:', out_path)
    os.makedirs(out_path)

# nchan = {'scifi':1536, 'us':10, 'ds':60}
# nplane = {'scifi':5, 'us':5, 'ds':4}

N_events = tchain.GetEntries()
print("N events:", N_events)

# Event metadata with 3 entries/event:
# - 0: z position of the neutrino interaction
# - 1: pdg code of the neutrino
# - 2: pz of the neutrino
event_meta = np.zeros((N_events, 3))

# Hitmap with 8 entries/hit: 
# - 0 is vertical (1) or horizontal (0)
# - 1-3 x/y/z positions of one edge of the strip
# - 4-6 x/y/z positions of the other edge of the strip
# - 7 detector type (0: none 1: scifi, 2: us, 3: ds)
hitmap = np.zeros((N_events, 8, n_hits_max), dtype=np.float32) # use uint8?

n_total = []
n_scifi = []

for i_event, event in tqdm(enumerate(tchain), total=N_events):
    event_pdg0 = event.MCTrack[0].GetPdgCode()
    if options.etype=='neutrino':
        if not ((np.abs(event_pdg0)//10)==1 and (np.abs(event_pdg0)%2)==0): continue
        #print('event ', i_event,' track0 type: ', event.MCTrack[0].GetPdgCode())
    if options.etype=='neutron':
        if not (event.MCTrack[0].GetPdgCode()==2112): continue
        #print('event ', i_event,' track0 type: ', event.MCTrack[0].GetPdgCode())
    
    event_meta[i_event] = (event.MCTrack[0].GetStartZ(), event.MCTrack[0].GetPdgCode(), event.MCTrack[0].GetPz())
    
    i_hit = 0

    for aHit in event.Digi_ScifiHits: # digi_hits:
        if i_hit >= n_hits_max:
            print('WARNING: More than', n_hits_max, 'sci fit hits')
            break

        # if not aHit.isValid(): continue
        detID = aHit.GetDetectorID()
        vert = aHit.isVertical()
        geo.modules['Scifi'].GetSiPMPosition(detID, A, B) # https://github.com/SND-LHC/sndsw/blob/a3ff0d0c4dfd8af5b12dbea31f9fb5b70f3c3ce9/shipLHC/Scifi.cxx#L557
        # geo.modules['Scifi'].GetPosition(detID, A, B) # https://github.com/SND-LHC/sndsw/blob/a3ff0d0c4dfd8af5b12dbea31f9fb5b70f3c3ce9/shipLHC/Scifi.cxx#L494
        # the second gives errors of type 
        # Error in <TGeoNavigator::cd>: Path /cave_1/Detector_0/volTarget_1/ScifiVolume1_1000000/ScifiHorPlaneVol1_1000000/HorMatVolume_1000000/FiberVolume_1010000 not valid
        # so we go with the first (which are also fibre positions so probably fine!)

        hitmap[i_event, 0, i_hit] = vert
        hitmap[i_event, 1, i_hit] = A.x()
        hitmap[i_event, 2, i_hit] = A.y()
        hitmap[i_event, 3, i_hit] = A.z()
        hitmap[i_event, 4, i_hit] = B.x()
        hitmap[i_event, 5, i_hit] = B.y()
        hitmap[i_event, 6, i_hit] = B.z()
        hitmap[i_event, 7, i_hit] = 1

        i_hit += 1

    n_scifi.append(i_hit)
        
    for aHit in event.Digi_MuFilterHits: # digi_hits:
        if i_hit >= n_hits_max:
            print('WARNING: More than', n_hits_max, 'sci fit + muon hits')
            break
        # if not aHit.isValid(): continue
        detID = aHit.GetDetectorID()
        vert = aHit.isVertical()

        geo.modules['MuFilter'].GetPosition(detID, A, B)

        # The following gives the subsystem number (2: us, 3: ds)
        n_sys = detID // 10000

        hitmap[i_event, 0, i_hit] = vert
        hitmap[i_event, 1, i_hit] = A.x()
        hitmap[i_event, 2, i_hit] = A.y()
        hitmap[i_event, 3, i_hit] = A.z()
        hitmap[i_event, 4, i_hit] = B.x()
        hitmap[i_event, 5, i_hit] = B.y()
        hitmap[i_event, 6, i_hit] = B.z()
        hitmap[i_event, 7, i_hit] = n_sys # 1: scifi, 2: us, 3: ds

        i_hit += 1
    
    n_total.append(i_hit)

print('Total number of hits:', np.sum(n_total))
print('Total number of scifi hits:', np.sum(n_scifi))
print('Max number of hits in an event:', np.max(n_total))
print('Max number of scifi hits in an event:', np.max(n_scifi))

debug = False
if debug:
    for det_id in [1000000, 1100000, 1023127, 1123127, 20009, 30060, 20000, 30000]:
        det = 'Scifi' if det_id > 1000000 else 'MuFilter'
        geo.modules[det].GetSiPMPosition(detID, A, B)
        print(f'\n{det} {detID} SiPM:', np.around(A, decimals=0), np.around(B, decimals=0))
        if det == 'Scifi':
            geo.modules[det].GetPosition(detID, A, B)
            print(f'{det} {detID} horiz pos:', np.around(A, decimals=0), np.around(B, decimals=0))


np.savez_compressed(os.path.join(out_path, 'hits.npz'), hits=hitmap, targets=event_meta)
