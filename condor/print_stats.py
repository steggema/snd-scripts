'''Prints total evnt numbers for each MC sample.
Given MC samples are not saved in systematic way in SND, need dedicated code for each sample.
'''


import os
from glob import glob
import ROOT

def print_info(sample_dir, silent=True):
    files = [f for f in glob(sample_dir+'/*/*TGeant4_digCPP.root')]
    n_events = 0
    for name in files:
        tchain = ROOT.TChain("cbmsim")
        tchain.Add(os.path.join(sample_dir, name))
        n_events += tchain.GetEntries()
        if not silent:
            print('N(events) in', name, ':', tchain.GetEntries())
    print('Total N(events):', n_events, 'for sample', sample_dir)
    return n_events


def print_info_nh(base_dir):
    ''' Writes the list for neutral hadron samples.'''
    n_events = 0
    for sample in os.listdir(base_dir):
        # For particle gun, only consider target area files
        if 'PGsim' in base_dir and not 'tgtarea' in sample:
            continue
        sample_dir = os.path.join(base_dir, sample, 'Ntuples')
        n_events += print_info(sample_dir)
    print('Total N(events) NH:', n_events)
            

# Neutrons and kaons
print_info_nh('/eos/experiment/sndlhc/MonteCarlo/NeutralHadrons/FTFP_BERT/neutrons/')
print_info_nh('/eos/experiment/sndlhc/MonteCarlo/NeutralHadrons/FTFP_BERT/kaons/')

# Neutrinos
sample_dir = os.path.join('/eos/experiment/sndlhc/MonteCarlo/Neutrinos/Genie/sndlhc_13TeV_down_volTarget_100fb-1_SNDG18_02a_01_000')
print_info(sample_dir)
