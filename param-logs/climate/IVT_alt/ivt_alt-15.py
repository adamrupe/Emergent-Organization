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
past_depth = 10
future_depth = 3
c = 1
past_K = 16
future_K = 20
decay = 0.1
past_params = {'nClusters':past_K, 'maxIterations':200}
future_params = {'nClusters':future_K, 'maxIterations':200}

# A = 0.25

observable = 'IVT_alt'
result = '15'

d4p.daalinit()

# Load netcdf files for my proc
run_dir = "/global/project/projectdirs/dasrepo/gmd/input/ALLHIST/run1"
allfiles = sorted(os.listdir(run_dir))
filenames = allfiles[7522:]
assert past_depth >= future_depth, 'assuming past_depth >= future_depth'
p = past_depth - 1 
halo = int((p - p%8) / 8) + 1
index = rank % 8
file = int((rank - index) / 8)
myfiles = filenames[file : (file+1) + 2*halo]

# Load TMQ data for one time-step per process
myfield = np.vstack([Dataset(run_dir+ '/'+f, 'r')['TMQ'][:] for f in myfiles])
pmargin = 8*halo - past_depth + index
fmargin = 8*halo - future_depth + (7-index)
TMQfield = myfield[pmargin: -fmargin]

# Load U850 data for one time-step per process
myfield = np.vstack([Dataset(run_dir+ '/'+f, 'r')['U850'][:] for f in myfiles])
pmargin = 8*halo - past_depth + index
fmargin = 8*halo - future_depth + (7-index)
Ufield = myfield[pmargin: -fmargin]

# Load V850 data for one time-step per process
myfield = np.vstack([Dataset(run_dir+ '/'+f, 'r')['V850'][:] for f in myfiles])
pmargin = 8*halo - past_depth + index
fmargin = 8*halo - future_depth + (7-index)
Vfield = myfield[pmargin: -fmargin]

# extract from TMQ first    
reconQ = DiscoReconstructor(past_depth, future_depth, c)
reconQ.extract(TMQfield)
del TMQfield

# now extract from U850
reconU = DiscoReconstructor(past_depth, future_depth, c)
reconU.extract(Ufield)
del Ufield

# now extract from V850
reconV = DiscoReconstructor(past_depth, future_depth, c)
reconV.extract(Vfield)
del Vfield

# recon = DiscoReconstructor(past_depth, future_depth, c)

# concatenate U and V lightcones onto TMQ lightcones
plcs_1 = (reconU.plcs*reconQ.plcs)*(reconU.plcs*reconQ.plcs)
plcs_2 = (reconV.plcs*reconQ.plcs)*(reconV.plcs*reconQ.plcs)
reconQ.plcs = np.concatenate((plcs_1, plcs_2), axis=1)
flcs_1 = (reconU.flcs*reconQ.flcs)*(reconU.flcs*reconQ.flcs)
flcs_2 = (reconV.flcs*reconQ.flcs)*(reconV.flcs*reconQ.flcs)
reconQ.flcs = np.concatenate((flcs_1, flcs_2), axis=1)

plc_decays = np.concatenate(( past_spacetime_decay(past_depth, c, decay), past_spacetime_decay(past_depth, c, decay) ))
reconQ.plcs *= np.sqrt(plc_decays)
comm.Barrier()
reconQ.kmeans_lightcones(past_params, future_params, decay_type='none', past_decay=0, future_decay=0)
reconQ.reconstruct_morphs()
comm.Barrier() 
comm.Allreduce(reconQ.local_joint_dist, reconQ.global_joint_dist, op=MPI.SUM ) 
reconQ.reconstruct_states(chi_squared)
reconQ.causal_filter()

save_dir = '/global/project/projectdirs/ProjectDisCo/Adam/climate/{}/result-{}/fields/'.format(observable, result)
workfile = myfiles[halo]
save_file = workfile[:-8]+'{:02}'.format(3*index) # add hour of the day for the given time-step
np.save(save_dir+save_file, reconQ.state_field)

run_details = "past_depth: {} \nfuture_depth: {} \nc :{} \
               \npast_K: {} \nfuture_K: {} \nlc decay: {} ".format(past_depth, 
                                                                    future_depth, 
                                                                    c, 
                                                                    past_K, 
                                                                    future_K, 
                                                                    decay)

if rank == 0:
    full_end = time.time()
    print("Multivariate analysis with lightcone metric to replicate IVT---(U850*TMQ)^2 concat (V850*TMQ)^2 lightcones---spacetime decays applied appropriately.")
    print(run_details, flush=True)
#     print("Note, hopefully fixed MPI issue with the environment for this one.")
    print('Time to solution: {}'.format(full_end-full_start))

d4p.daalfini()
