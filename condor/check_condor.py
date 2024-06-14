'''Checks output from a condor batch job and creates a resubmission file for failed jobs.
'''
import os
import argparse

parser = argparse.ArgumentParser(description='Check condor output and create resubmission file')
parser.add_argument("-c", "--config", dest="config", help="configuration file", required=False, default='/afs/cern.ch/user/s/steggema/work/snd_lx9/snd-scripts/condor/paramlist_data_2023.txt')
parser.add_argument('-d', '--dir', dest='dir', help='Location of job output files', required=False, default='/afs/cern.ch/user/s/steggema/work/snd_lx9/data/')
parser.add_argument('-o', '--out', dest='out', help='Name of resubmission file', required=False, default='resubmit.txt')
args = parser.parse_args()

with open(args.config) as f:
    out_lines = []
    lines = f.readlines()
    for line in lines:
        # Get second column of each line
        job_id = line.split()[1]
        out_dir = line.split()[4]

        files = [f.split('_')[1] for f in os.listdir(os.path.join(args.dir, out_dir)) if f.endswith('hits.pt')]

        if job_id not in files:
            print('Missing files:', job_id, out_dir)
            out_lines.append(line)    

    with open(args.out, 'w') as out_file:
        for line in out_lines:
            out_file.write(line)
        print(f'Resubmission file created: {args.out}')
