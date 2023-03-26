'''
author: Adam Rupe
email: atrupe@ucdavis.edu
brief: Test run on climate data
dependencies: python3, numpy, numba, mpi4py, daal4py
'''

# OPT: import only parts of os and sys that we need?
import time, os, sys
from netCDF4 import Dataset
from sklearn.preprocessing import StandardScaler

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
past_depth = 12
future_depth = 3
c = 1
past_K = 24
future_K = 20
decay = 1.2
past_params = {'nClusters':past_K, 'maxIterations':200}
future_params = {'nClusters':future_K, 'maxIterations':200}

W = 0.8 # ratio to weigh PSL lightcones, compared to TMQ

observable = 'TMQ_PSL'
result = '12'

# Load TMQ data for one time-step per process
run_dir = "/global/project/projectdirs/dasrepo/gmd/input/ALLHIST/run1"
allfiles = sorted(os.listdir(run_dir))
filenames = allfiles[7522:]
assert past_depth >= future_depth, 'assuming past_depth >= future_depth'
p = past_depth - 1 
halo = int((p - p%8) / 8) + 1
index = rank % 8
file = int((rank - index) / 8)
myfiles = filenames[file : (file+1) + 2*halo]
myfield = np.vstack([Dataset(run_dir+ '/'+f, 'r')['TMQ'][:] for f in myfiles])
pmargin = 8*halo - past_depth + index
fmargin = 8*halo - future_depth + (7-index)
TMQfield = myfield[pmargin: -fmargin]

# Load PSL data for one time-step per process
myfield = np.vstack([Dataset(run_dir+ '/'+f, 'r')['PSL'][:] for f in myfiles])
pmargin = 8*halo - past_depth + index
fmargin = 8*halo - future_depth + (7-index)
PSLfield = myfield[pmargin: -fmargin]

# extract from TMQ first    
recon = DiscoReconstructor(past_depth, future_depth, c)
recon.extract(TMQfield)
recon.plcs *= np.sqrt(past_spacetime_decay(past_depth, c, decay))
del TMQfield

# recon.plcs = StandardScaler().fit_transform(recon.plcs)
# recon.flcs = StandardScaler().fit_transform(recon.flcs)

# now extract from PSL
recon2 = DiscoReconstructor(past_depth, future_depth, c)
recon2.extract(PSLfield/5000)
shrink = 0.000001
recon2.plcs *= np.sqrt(shrink * past_spacetime_decay(past_depth, c, decay)) # strongly reduce PSL plcs to see if it reproduces TMQ-only analysis
del PSLfield

# recon2.plcs = StandardScaler().fit_transform(recon2.plcs)
# recon2.flcs = StandardScaler().fit_transform(recon2.flcs)

# concatenate PSL lightcones onto TMQ lightcones
recon.plcs = np.concatenate((recon.plcs, recon2.plcs), axis=1)
recon.flcs = np.concatenate((recon.flcs, recon2.flcs), axis=1)

# plc_decays = np.concatenate((past_spacetime_decay(past_depth, c, decay), (A**2)*past_spacetime_decay(past_depth, c, decay)))
# plc_decays = np.concatenate((past_spacetime_decay(past_depth, c, decay), past_spacetime_decay(past_depth, c, decay)))
# recon.plcs *= np.sqrt(plc_decays)

comm.Barrier()
d4p.daalinit()
recon.kmeans_lightcones(past_params, future_params, decay_type='none', past_decay=0, future_decay=0)
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
               \npast_K: {} \nfuture_K: {} \nlc decay: {} ".format(past_depth, 
                                                                    future_depth, 
                                                                    c, 
                                                                    past_K, 
                                                                    future_K, 
                                                                    decay)

if rank == 0:
    full_end = time.time()
    print("Multivariate analysis, with PSL lightcones concatenated to TMQ lightcones, with spacetime decays applied appropriately.\
           Ratio of PSL to TMQ for weighing contribution to lightcone distance: {}".format(shrink))
    print(run_details, flush=True)
    print('Time to solution: {}'.format(full_end-full_start))

d4p.daalfini()
