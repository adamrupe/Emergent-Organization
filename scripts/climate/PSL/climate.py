'''
author: Adam Rupe
email: atrupe@ucdavis.edu
brief: Test run on climate data
dependencies: python3, numpy, numba, mpi4py, daal4py
'''

# OPT: import only parts of os and sys that we need?
import time, os, sys
from netCDF4 import Dataset

#Parent directory which contains the disco repo
module_path = os.path.abspath(os.path.join('/global/common/software/ProjectDisCo/'))
sys.path.append(module_path)

from source.pdisco import *

#Initialize MPI variables
from mpi4py import MPI
comm = MPI.COMM_WORLD
size = comm.Get_size()
rank = comm.Get_rank()

if rank == 0:
    full_start = time.time()

# Initialize parameters for pipeline
past_depth = 16
future_depth = 3
c = 1
past_K = 24
future_K = 50
decay = 1.0
decay_type = 'time'
past_params = {'nClusters':past_K, 'maxIterations':200}
future_params = {'nClusters':future_K, 'maxIterations':200}

observable = 'PSL'
result = '3'

# Load data for one time-step per process
run_dir = "/global/project/projectdirs/dasrepo/gmd/input/ALLHIST/run1"
allfiles = sorted(os.listdir(run_dir))
# filenames = allfiles[7334:]
filenames = allfiles[7522:]
assert past_depth >= future_depth, 'assuming past_depth >= future_depth'
p = past_depth - 1 
halo = int((p - p%8) / 8) + 1
index = rank % 8
file = int((rank - index) / 8)
myfiles = filenames[file : (file+1) + 2*halo]
myfield = np.vstack([Dataset(run_dir+ '/'+f, 'r')[observable][:] for f in myfiles])
pmargin = 8*halo - past_depth + index
fmargin = 8*halo - future_depth + (7-index)
myfield = myfield[pmargin: -fmargin]

    
recon = DiscoReconstructor(past_depth, future_depth, c)
recon.extract(myfield)
del myfield
comm.Barrier()
d4p.daalinit()
recon.kmeans_lightcones(past_params, future_params, decay_type=decay_type, past_decay=decay, future_decay=decay)
recon.reconstruct_morphs()
comm.Barrier() 
comm.Allreduce(recon.local_joint_dist, recon.global_joint_dist, op=MPI.SUM ) 
recon.reconstruct_states(chi_squared)
recon.causal_filter()

save_dir = '/global/project/projectdirs/ProjectDisCo/Adam/climate/{}/result-{}/fields/'.format(observable, result)
workfile = myfiles[halo]
save_file = workfile[:-8]+'{:02}'.format(3*index) # add hour of the day for the given time-step
np.save(save_dir+save_file, recon.state_field)

run_details = "past_depth: {} \nfuture_depth: {} \nc :{} \
               \npast_K: {} \nfuture_K: {} \nlc decay: {} \ndecay type: {} ".format(past_depth, 
                                                                    future_depth, 
                                                                    c, 
                                                                    past_K, 
                                                                    future_K, 
                                                                    decay, 
                                                                    decay_type)

if rank == 0:
    full_end = time.time()
    print(run_details, flush=True)
    print('Time to solution: {}'.format(full_end-full_start))

d4p.daalfini()
