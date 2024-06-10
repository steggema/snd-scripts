''' Script to create npy files as input for ML training.
Adapted from https://github.com/golovart/Napoli_emulsion/blob/main/SND/neutrino_ml/data_process/hit_sandbox.py
'''


## run example
## neutrino path: /eos/experiment/sndlhc/MonteCarlo/Neutrinos/Genie/sndlhc_13TeV_down_volTarget_100fb-1_SNDG18_02a_01_000/

## neutron path: /eos/experiment/sndlhc/users/marssnd/PGsim/neutrons/neu_*double/

import os #, atexit
from datetime import datetime
from tqdm import tqdm
import numpy as np
import ROOT


from argparse import ArgumentParser
parser = ArgumentParser()
parser.add_argument("-mc", "--inputmc_dir", dest="inputmc_dir", help="Monte Carlo input directory", required=False, default="/eos/experiment/sndlhc/MonteCarlo/Neutrinos/Genie/sndlhc_13TeV_down_volMuFilter_20fb-1_SNDG18_02a_01_000/")
parser.add_argument("-p", "--partition", dest="part", type=int, help="number of starting partition (or run number for data)", default=0)
parser.add_argument("-e", "--end_partition", dest="end_part", type=int, help="number of ending partition (or run number) - note this is inclusive", default=-1)
parser.add_argument("-d", "--is_data", dest="is_data", type=bool, help="is real data?", default=False)
parser.add_argument("-o", "--outPath", dest="outPath", help="output directory", required=False,
                    default="/afs/cern.ch/user/s/steggema/work/snd/data/")
parser.add_argument("-t", "--type", dest="etype", help="event type to select", default='neutrino')
parser.add_argument("-nh", "--nhits", dest="nhits", type=int, help="minimum number of scifi hits", default=75)

options = parser.parse_args()
is_data = options.is_data
n_hits_min = options.nhits

p_start = options.part
p_end = options.part if options.end_part < options.part else options.end_part

import SndlhcGeo # import takes some time so putting it after the arg parser

# For MC, there's one geo file in every subdirectory; for data, there is one in the main directory
mc_dir = os.path.join(options.inputmc_dir, str(options.part))
if is_data:
    mc_dir = options.inputmc_dir
geo_path = None
for name in os.listdir(mc_dir):
    if 'geofile' in name:
        geo_path = os.path.join(mc_dir, name)
if geo_path is None:
    raise RuntimeError(f"no geofile found in the input directory {mc_dir}")
if is_data:
    mc_dir = os.path.join(options.inputmc_dir, f'run_00{options.part}')

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

for part in range(p_start, p_end + 1):
    add_dir = os.path.join(options.inputmc_dir,  f'run_00{part}' if is_data else str(part))
    if not os.path.exists(add_dir):
        print('Partition', part, 'does not exist', 'in dir', add_dir)
        continue
    files = [f for f in os.listdir(add_dir) if f.endswith('TGeant4_digCPP.root') or (f.startswith('sndsw_raw') and f.endswith('.root'))]
    if len(files) == 0:
        print('No digi file found for partition', part, 'in dir', add_dir)

    for name in files:
        tchain.Add(os.path.join(add_dir, name))
        print("add file to TChain:", os.path.join(add_dir, name))
            

## OUTPUT FILE
out_path = os.path.join(options.outPath, options.etype, *mc_dir.split('/')[-2:-1] if options.etype=='neutrino' else mc_dir.split('/')[-3:-1])
if not os.path.exists(out_path):
    print('Creating output directory:', out_path)
    os.makedirs(out_path)

# nchan = {'scifi':1536, 'us':10, 'ds':60}
# nplane = {'scifi':5, 'us':5, 'ds':4}

N_events = tchain.GetEntries(f"@Digi_ScifiHits.size()>={n_hits_min}")
print(f"N events with at least {n_hits_min} SciFi hits:", N_events)

# Event metadata with 7 entries/event:
# - 0: z position of the neutrino interaction
# - 1: pdg code of the neutrino
# - 2: pz of the neutrino
# - 3: event_id, partition + event_i
# - 4-6: x,y,z on first interaction point
event_meta = np.zeros((N_events, 7))

n_hits_arr = np.zeros((N_events), dtype=np.int32)

# Loop 1: Count hits
i_ev_sel = 0
for i_event, event in tqdm(enumerate(tchain), total=tchain.GetEntries()):
    n_hits = 0
    if len(event.Digi_ScifiHits) < n_hits_min:
        continue

    for hit in event.Digi_ScifiHits:
        if hit.isValid():
            n_hits += 1
    
    for hit in event.Digi_MuFilterHits:
        if hit.isValid():
            n_hits += 1
    
    n_hits_arr[i_ev_sel] = n_hits
    i_ev_sel += 1

n_hits_total = np.sum(n_hits_arr)
print('Saving a total number of', n_hits_total, 'hits')

# Hitmap with 8 entries/hit: 
# - 0 is vertical (1) or horizontal (0)
# - 1-3 x/y/z positions of one edge of the strip
# - 4-6 x/y/z positions of the other edge of the strip
# - 7 detector type (0: none 1: scifi, 2: us, 3: ds)
hitmap = np.zeros((n_hits_total, 8), dtype=np.float16) 

i_ev_sel = 0
i_hit = 0
for i_event, event in tqdm(enumerate(tchain), total=tchain.GetEntries()):
    if len(event.Digi_ScifiHits) < n_hits_min:
        continue

    if not is_data:
        event_pdg0 = event.MCTrack[0].GetPdgCode()
        event_pdg1 = event.MCTrack[1].GetPdgCode()
        x1 = event.MCTrack[1].GetStartX()
        y1 = event.MCTrack[1].GetStartY()
        z1 = event.MCTrack[1].GetStartZ()
        if options.etype=='neutrino':
            if not ((np.abs(event_pdg0)//10)==1 and (np.abs(event_pdg0)%2)==0): continue
            #print('event ', i_event,' track0 type: ', event.MCTrack[0].GetPdgCode())
        if options.etype=='neutron':
            if not (event.MCTrack[0].GetPdgCode()==2112): continue
            #print('event ', i_event,' track0 type: ', event.MCTrack[0].GetPdgCode())
        if options.etype=='muon':
            if not abs(event.MCTrack[0].GetPdgCode())==13: continue
            #print('event ', i_event,' track0 type: ', event.MCTrack[0].GetPdgCode())
        
        #set event_id
        event_id = (int(options.part)+1)*100000 + i_event

        # Add 100 for neutral-current interactions
        event_meta[i_ev_sel] = (event.MCTrack[0].GetStartZ(), event.MCTrack[0].GetPdgCode() + 100 *(event_pdg0==event_pdg1), event.MCTrack[0].GetPz(), event_id, x1, y1, z1)    
    else:
        # Note should save event number for data
        event_meta[i_ev_sel] = (event.EventHeader.GetRunId(), event.EventHeader.GetFillNumber(), event.EventHeader.GetEventNumber(), 0., 0., 0., 0.)

    for hit in event.Digi_ScifiHits: # digi_hits:
        if not hit.isValid(): 
            continue

        detID = hit.GetDetectorID()
        vert = hit.isVertical()
        geo.modules['Scifi'].GetSiPMPosition(detID, A, B) # https://github.com/SND-LHC/sndsw/blob/a3ff0d0c4dfd8af5b12dbea31f9fb5b70f3c3ce9/shipLHC/Scifi.cxx#L557

        hitmap[i_hit, 0] = vert
        hitmap[i_hit, 1] = A.x()
        hitmap[i_hit, 2] = A.y()
        hitmap[i_hit, 3] = A.z()
        hitmap[i_hit, 4] = B.x()
        hitmap[i_hit, 5] = B.y()
        hitmap[i_hit, 6] = B.z()
        hitmap[i_hit, 7] = 4

        i_hit += 1
        
    for hit in event.Digi_MuFilterHits: # digi_hits:
        if not hit.isValid(): 
            continue

        detID = hit.GetDetectorID()
        vert = hit.isVertical()

        geo.modules['MuFilter'].GetPosition(detID, A, B)

        # The following gives the subsystem number (1:veto, 2: us, 3: ds)
        n_sys = detID // 10000

        hitmap[i_hit, 0] = vert
        hitmap[i_hit, 1] = A.x()
        hitmap[i_hit, 2] = A.y()
        hitmap[i_hit, 3] = A.z()
        hitmap[i_hit, 4] = B.x()
        hitmap[i_hit, 5] = B.y()
        hitmap[i_hit, 6] = B.z()
        hitmap[i_hit, 7] = n_sys # 1: veto, 2: us, 3: ds

        i_hit += 1
    
    i_ev_sel += 1

print('Filled', i_ev_sel, 'events with', i_hit, 'hits out of total', n_hits_total, 'hits')

debug = False
if debug:
    for det_id in [1000000, 1100000, 1023127, 1123127, 20009, 30060, 20000, 30000]:
        det = 'Scifi' if det_id > 1000000 else 'MuFilter'
        geo.modules[det].GetSiPMPosition(detID, A, B)
        print(f'\n{det} {detID} SiPM:', np.around(A, decimals=0), np.around(B, decimals=0))
        if det == 'Scifi':
            geo.modules[det].GetPosition(detID, A, B)
            print(f'{det} {detID} horiz pos:', np.around(A, decimals=0), np.around(B, decimals=0))


np.savez_compressed(os.path.join(out_path, 'hits_{}.npz'.format(*mc_dir.split('/')[-1:] if options.etype=='neutrino' else mc_dir.split('/')[-1:])), hits=hitmap, targets=event_meta, n_hits=n_hits_arr)
