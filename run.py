import itertools
import argparse
import pickle
import os
import subprocess

cwd = os.getcwd()
# Change to the PPCG root directory
ppcg_dir = '/home/khaled/Documents/ppcg'


    #Many of these flags are enabled by default according to ppcg --help

flags = [
            'tile',
            'no-group-chains',                          # enabled by default
            'no-scale-tile-loops',                      # enabled by default
            'openmp',
            'isl-coalesce-preserve-locals',
            'no-isl-schedule-parametric',              # enabled by default
            'no-isl-schedule-outer-coincidence',        # enabled by default
            'no-isl-schedule-maximize-band-depth',      # enabled by default
            'no-isl-schedule-separate-components',      # enabled by default
            'isl-schedule-whole-component',             # enabled by default
            'isl-schedule-algorithm=feautrier',
            'isl-schedule-serialize-sccs',
            'no-isl-tile-scale-tile-loops',             # enabled by default
            'no-isl-tile-shift-point-loops',            # enabled by default
            'no-isl-ast-build-exploit-nested-bounds',   # enabled by default
            'no-isl-ast-build-scale-strides'            # enabled by default
        ]

'''
flags = [
            'tile',
            'openmp',
            'isl-coalesce-preserve-locals',
            'isl-schedule-whole-component',
            'isl-schedule-algorithm=feautrier',
            'isl-schedule-serialize-sccs'
        ]

'''
# function to execute unix commands
def execute_cmd(cmd, directory):
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, cwd=directory)
    out = str(p.stdout.decode('utf-8'))
    err = str(p.stderr.decode('utf-8'))
    return p.returncode, out, err


def generate():

    ncomb = 0

    # map filename to flags used
    # could be useful to find out which flags were applied to a generate a file
    name_to_cmd = {}


    # keep track of them to remove them later
    generated_with_errors = []

    for L in range(1, len(flags)+1):
        for subset in itertools.combinations(flags, L):
            command = f"{ppcg_dir}/ppcg --pet-autodetect=yes --target=c "
            cmd_flags = ''
            for item in subset:
                cmd_flags += '--' + item + ' '

            name_to_cmd[ncomb+1] = cmd_flags

            command += f"{cmd_flags}chemv.c -o output/chemv_{ncomb+1}.c"


            print(f'Generating variant {ncomb+1}...')

            print(command)

            rc, out, err = execute_cmd(command, cwd)

            #save logs of outputs and errors (if needed, uncomment)
            if len(out) > 2:
                with open(f'{cwd}/logs/{ncomb+1}.log','w') as fd:
                    fd.write(f'{command}\n')
                    fd.write(out)
            if len(err) > 2:

                generated_with_errors.append(ncomb+1)
                
                with open(f'{cwd}/errs/{ncomb+1}.err','w') as fd:
                    fd.write(f'{command}\n')
                    fd.write(err)

            print('==========')

            ncomb += 1
    print(ncomb)

    # save file name to command dictionary
    with open('cmdMap.pk', 'wb') as fd:
        pickle.dump(name_to_cmd, fd)


    # delete files generated with errors because they will not be
    # complete
    print('Deleting variants that triggered a ppcg error...')
    for file_num in generated_with_errors:
        delete_err_cmd = f'rm chemv_{file_num}.c'
        delete_err_dir = cwd + '/output'
        rc, out, err = execute_cmd(delete_err_cmd, delete_err_dir)

    # delete duplicate files using fdupes
    # fdupes can be easily installed on ubuntu using:
    #       sudo apt-get install fdupes
    #
    #   fdupes . : finds duplicate files in the current directory
    #         -d : delete duplicate files (keep only one, prompt the
    #              user to choose which one
    #         -N : keep the first one, delete others and don't prompt
    delete_cmd = 'fdupes . -d -N'
    delete_dir = cwd  + '/output'
    print(f'Deleting duplicates from directory: {delete_dir}')
    rc, out, err = execute_cmd(delete_cmd, delete_dir)


# find out the command used to generate an input filename
def analyze(filename):

    # extract number from file name
    number = int(filename.split('/')[-1].split('.')[0].split('_')[1])

    name_to_cmd = {}

    # load saved dictionary
    with open('cmdMap.pk','rb') as fd:
        name_to_cmd = pickle.load(fd)

    cmd = './ppcg --pet-autodetect=yes --target=c ' + name_to_cmd[number] + 'chemv.c -o ' + filename

    print(f'Command used to generate this file was:\n {cmd}')

if __name__=='__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument('--file', type=str,  help='File path to be analyzed for the generating command')
    args = parser.parse_args()

    # if a file name is provided, go to analysis mode
    if (args.file):
        analyze(args.file)
    else:
        # otherwise, generation mode is the default
        generate()
