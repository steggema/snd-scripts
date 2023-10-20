## run example
# python -i hit_sandbox.py -mc /eos/experiment/sndlhc/MonteCarlo/Neutrinos/Genie/sndlhc_13TeV_down_volTarget_100fb-1_SNDG18_02a_01_000 -p 137 -t neutrino

## neutrino path: /eos/experiment/sndlhc/MonteCarlo/Neutrinos/Genie/sndlhc_13TeV_down_volTarget_100fb-1_SNDG18_02a_01_000/137/sndLHC.Genie-TGeant4_digCPP.root

## neutron path: /eos/experiment/sndlhc/users/marssnd/PGsim/neutrons/neu_20_30_double/Ntuples/137/sndLHC.PG_2112-TGeant4_digCPP.root

## event metadata format: [Startz, MCTrack[0].GetPdgCode(), MCTrack[1].GetPdgCode()]


import ROOT
import os,sys,subprocess,atexit
import rootUtils as ut
from array import array
import shipunit as u
import SndlhcMuonReco
import json
from rootpyPickler import Unpickler
import time
from XRootD import client

from datetime import datetime
from pathlib import Path
from tqdm import tqdm
import numpy as np
import matplotlib.pyplot as plt
# import matplotlib as mpl


def pyExit():
       "unfortunately need as bypassing an issue related to use xrootd"
       os.system('kill '+str(os.getpid()))
atexit.register(pyExit)

h = {}
from argparse import ArgumentParser
parser = ArgumentParser()
parser.add_argument("-mc", "--inputMCDir", dest="inputMCDir", help="Monte Carlo input directory", required=False, default="/eos/experiment/sndlhc/MonteCarlo/Neutrinos/Genie/sndlhc_13TeV_down_volMuFilter_20fb-1_SNDG18_02a_01_000/")
parser.add_argument("-p", "--partition", dest="part", help="number of starting partition", default=0)
parser.add_argument("-ne", "--nEvents", dest="nEvents", help="number of events to process", default=3000001)
parser.add_argument("-o", "--outPath", dest="outPath", help="output directory", required=False,
                    default="/afs/cern.ch/user/s/steggema/work/snd/data/")
parser.add_argument("-t", "--type", dest="etype", help="event type to select", default='neutrino')

options = parser.parse_args()
import SndlhcGeo

# find geofile in the MC dir
MCDir = os.path.join(options.inputMCDir, str(options.part)) # '/'.join(options.inputMCFile.split('/')[:-1])
geo_path = None
for name in os.listdir(MCDir):
    if 'geofile' in name:
        geo_path = os.path.join(MCDir, name)
if geo_path is None:
    raise RuntimeError("no geofile found in the MC directory")

geo = SndlhcGeo.GeoInterface(geo_path)
lsOfGlobals = ROOT.gROOT.GetListOfGlobals()
lsOfGlobals.Add(geo.modules['Scifi'])
lsOfGlobals.Add(geo.modules['MuFilter'])
Scifi = geo.modules['Scifi']
Mufi = geo.modules['MuFilter']
nav = ROOT.gGeoManager.GetCurrentNavigator()

## Processing the geometry
detSize = {}
si = geo.snd_geo.Scifi
detSize[0] = [si.channel_width, si.channel_width, si.scifimat_z]
mi = geo.snd_geo.MuFilter
detSize[1] =[mi.VetoBarX/2, mi.VetoBarY/2, mi.VetoBarZ/2]
detSize[2] =[mi.UpstreamBarX/2, mi.UpstreamBarY/2, mi.UpstreamBarZ/2]
detSize[3] =[mi.DownstreamBarX_ver/2, mi.DownstreamBarY/2, mi.DownstreamBarZ/2]


print('\n\n-- Getting detector sizes --')
print(detSize)
A, B = ROOT.TVector3(), ROOT.TVector3()
proc_start_time = datetime.now()

## For MonteCarlo INPUT FILE
tchain = ROOT.TChain("cbmsim")

MCFile_path = None
for name in os.listdir(MCDir):
    if name.endswith('digCPP.root'):
        MCFile_path = os.path.join(MCDir, name)
if MCFile_path is None:
    raise RuntimeError("no MC digi file found in the MC directory")

tchain.Add(MCFile_path)  

## OUTPUT FILE
out_path = os.path.join(options.outPath, options.etype, *MCDir.split('/')[-2:])
if not os.path.exists(out_path):
    os.makedirs(out_path)

# nchan = {'scifi':1536, 'us':10, 'ds':60}
# nplane = {'scifi':5, 'us':5, 'ds':4}

N_events = tchain.GetEntries()
print("N events:", N_events)
event_meta = np.zeros((N_events, 3))

# hitmap = {}
# 8 entries: 
# - 0 is vertical (1) or horizontal (0)
# - 1-3 x/y/z positions of one edge of the strip
# - 4-6 x/y/z positions of the other edge of the strip
# - 7 detector type (0: scifi, 1: us, 2: ds)
hitmap = np.zeros((N_events, 8, 1000), dtype=np.float32) # use uint8?

# hitmap['scifi'] = np.zeros((N_events, 2, nplane['scifi'], nchan['scifi']), dtype=bool) # use uint8?
# hitmap['us'] = np.zeros((N_events, 2, nplane['us'], nchan['us']), dtype=bool)
# hitmap['ds'] = np.zeros((N_events, 2, nplane['ds'], nchan['ds']), dtype=bool)

scifi_depth = []
for i_event, event in tqdm(enumerate(tchain), total=N_events):
    event_pdg0 = event.MCTrack[0].GetPdgCode()
    if options.etype=='neutrino':
        if not ((np.abs(event_pdg0)//10)==1 and (np.abs(event_pdg0)%2)==0): continue
        #print('event ', i_event,' track0 type: ', event.MCTrack[0].GetPdgCode())
    if options.etype=='neutron':
        if not (event.MCTrack[0].GetPdgCode()==2112): continue
        #print('event ', i_event,' track0 type: ', event.MCTrack[0].GetPdgCode())
    #digi_hits = []
    #if event.FindBranch("Digi_ScifiHits"): digi_hits.append(event.Digi_ScifiHits)
    #if event.FindBranch("Digi_MuFilterHits"): digi_hits.append(event.Digi_MuFilterHits)
    #if event.FindBranch("Digi_MuFilterHit"): digi_hits.append(event.Digi_MuFilterHit)
    
    event_meta[i_event] = (event.MCTrack[0].GetStartZ(), event.MCTrack[0].GetPdgCode(), event.MCTrack[1].GetPdgCode())
    
    i_hit = 0

    for aHit in event.Digi_ScifiHits: # digi_hits:
        # if not aHit.isValid(): continue
        detID = aHit.GetDetectorID()
        vert = aHit.isVertical()
        # geo.modules['Scifi'].GetSiPMPosition(detID, A, B) # https://github.com/SND-LHC/sndsw/blob/a3ff0d0c4dfd8af5b12dbea31f9fb5b70f3c3ce9/shipLHC/Scifi.cxx#L557
        geo.modules['Scifi'].GetPosition(detID, A, B)
        # Note should also check https://github.com/SND-LHC/sndsw/blob/a3ff0d0c4dfd8af5b12dbea31f9fb5b70f3c3ce9/shipLHC/Scifi.cxx#L494
        scifi_depth = np.append(scifi_depth, A.z())

        hitmap[i_event, 0, i_hit] = vert
        hitmap[i_event, 1, i_hit] = A.x()
        hitmap[i_event, 2, i_hit] = A.y()
        hitmap[i_event, 3, i_hit] = A.z()
        hitmap[i_event, 4, i_hit] = B.x()
        hitmap[i_event, 5, i_hit] = B.y()
        hitmap[i_event, 6, i_hit] = B.z()
        hitmap[i_event, 7, i_hit] = 0

        i_hit += 1
        
    for aHit in event.Digi_MuFilterHits: # digi_hits:
        # if not aHit.isValid(): continue
        detID = aHit.GetDetectorID()
        vert = aHit.isVertical()

        geo.modules['MuFilter'].GetPosition(detID, A, B)

        n_sys = detID // 10000

        hitmap[i_event, 0, i_hit] = vert
        hitmap[i_event, 1, i_hit] = A.x()
        hitmap[i_event, 2, i_hit] = A.y()
        hitmap[i_event, 3, i_hit] = A.z()
        hitmap[i_event, 4, i_hit] = B.x()
        hitmap[i_event, 5, i_hit] = B.y()
        hitmap[i_event, 6, i_hit] = B.z()
        hitmap[i_event, 7, i_hit] = n_sys - 1 # 0: scifi, 1: us, 2: ds

    # print('\n'*3)
    # if i_event>10: break
print(np.unique(np.around(scifi_depth, decimals=0), return_counts=True))

# Scifi coords
detID = 1000000
geo.modules['Scifi'].GetSiPMPosition(detID, A, B)
print('\nScifi 0 horiz:', np.around(A, decimals=0), np.around(B, decimals=0))
geo.modules['Scifi'].GetSiPMPosition(detID, A, B)
print('Scifi 0 horiz end:', np.around(A, decimals=0), np.around(B, decimals=0))

detID = 1023127
geo.modules['Scifi'].GetSiPMPosition(detID, A, B)
print('Scifi 0 horiz end:', np.around(A, decimals=0), np.around(B, decimals=0))
geo.modules['Scifi'].GetPosition(detID, A, B)
print('Scifi 0 horiz end:', np.around(A, decimals=0), np.around(B, decimals=0))

detID = 1100000
geo.modules['Scifi'].GetSiPMPosition(detID, A, B)
print('\nScifi 0 vert:', np.around(A, decimals=0), np.around(B, decimals=0))
geo.modules['Scifi'].GetPosition(detID, A, B)
print('Scifi 0 vert end:', np.around(A, decimals=0), np.around(B, decimals=0))

detID = 1123127
geo.modules['Scifi'].GetSiPMPosition(detID, A, B)
print('Scifi 0 vert end:', np.around(A, decimals=0), np.around(B, decimals=0))
geo.modules['Scifi'].GetPosition(detID, A, B)
print('Scifi 0 vert end:', np.around(A, decimals=0), np.around(B, decimals=0))

detID = 20000
geo.modules['MuFilter'].GetPosition(detID, A, B)
print('\nUpStream 0 horiz:', np.around(A, decimals=0), np.around(B, decimals=0))
detID = 20009
geo.modules['MuFilter'].GetPosition(detID, A, B)
print('UpStream 0 horiz end:', np.around(A, decimals=0), np.around(B, decimals=0))

detID = 30000
geo.modules['MuFilter'].GetPosition(detID, A, B)
print('\nDownStream 0 horiz:', np.around(A, decimals=0), np.around(B, decimals=0))

detID = 30060
geo.modules['MuFilter'].GetPosition(detID, A, B)
print('\nDownStream 0 vert:', np.around(A, decimals=0), np.around(B, decimals=0))




np.save(out_path+name+'.npy', hitmap)
np.save(out_path+'event_metadata.npy', event_meta)

'''
hit_tot = {}
hit_tot['scifi'] = np.sum(hitmap['scifi'], axis=0, dtype=int)
tmp_scifi = np.zeros((2, nplane['scifi'], 12))
for i in range(12):
    tmp_scifi[:, :, i] = hit_tot['scifi'][..., 128*i:128*(i+1)].sum(axis=-1)
hit_tot['scifi'] = tmp_scifi
hit_tot['us'] = np.sum(hitmap['us'], axis=0, dtype=int)
hit_tot['ds'] = np.sum(hitmap['ds'], axis=0, dtype=int)

for name, hitmap in hit_tot.items():
    for vert in range(2):
        plt.imshow(hitmap[vert].T)
        plt.title(name+' '+('vert' if vert else 'horiz'))
        plt.show()
'''
