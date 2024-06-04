'''Checks output from a condor batch job and creates a resubmission file for failed jobs.
'''
import os
import argparse

parser = argparse.ArgumentParser(description='Check condor output and create resubmission file')
parser.add_argument("-c", "--config", dest="config", help="configuration file", required=False, default='/afs/cern.ch/user/s/steggema/work/snd_lx9/snd-scripts/condor/paramlist_data_2023.txt')
parser.add_argument('-d', '--dir', dest='dir', help='Location of job output files', required=False, default='/afs/cern.ch/user/s/steggema/work/snd_lx9/data/neutrino/2023_reprocess/')
parser.add_argument('-o', '--out', dest='out', help='Name of resubmission file', required=False, default='resubmit.txt')
args = parser.parse_args()

with open(args.config) as f:
    lines = f.readlines()

    # Get second column of each line
    job_ids = [line.split()[1] for line in lines]

    files = [f[-8:-4] for f in os.listdir(args.dir) if f.endswith('.npz')]
    missing = []
    missing = [job_id for job_id in job_ids if job_id not in files]
    print('Missing files:', missing)

    with open(args.out, 'w') as out_file:
        lines = [line for line in lines if line.split()[1] in missing]
        for line in lines:
            out_file.write(line)
        print('Resubmission file created: resubmit.txt')
