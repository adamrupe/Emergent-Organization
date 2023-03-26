'''
author: Adam Rupe
modified: Nalini Kumar
email: atrupe@ucdavis.edu
brief: Test run on Jupiter grayscale data
usage: python jupiter.py
dependencies: python3, numpy, numba, mpi4py, daal4py
'''

# OPT: import only parts of os and sys that we need?
import time, os, sys
from math import ceil

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
    start = time.time()
    
result = '9'

# Initialize parameters for pipeline
p_depth = 12
f_depth = 2
c = 1
K_past = 10
K_future = 25
decay_type='spacetime'
p_decay = 0.25
f_decay = 0.0

past_params = {'nClusters':K_past, 'maxIterations':200}
future_params = {'nClusters':K_future, 'maxIterations':200}
p_i_params = {'nClusters':K_past, 'method':'plusPlusDense', 'distributed': True}
f_i_params = {'nClusters':K_future, 'method':'plusPlusDense', 'distributed': True}

# Load data with appropriate halos
work = 1

# Load data with appropriate halos
data_dir = '/global/project/projectdirs/ProjectDisCo/Jupiter/gs_arrays/'
allfiles = sorted(os.listdir(data_dir))
total = len(allfiles)
n_procs = ceil((total - (p_depth+f_depth))/work) 
last = n_procs - 1
if rank == last:
    myfiles = allfiles[rank*work : total]
else:
    myfiles = allfiles[rank*work : (rank+1)*work + (p_depth+f_depth)]
myfield = np.stack([np.load(os.path.join(data_dir, f)) for f in myfiles])
myfield = myfield[:, 400:-400, :2200].astype(np.float32)


# Initialize DiscoReconstructor object with past and future lightcone depths
recon = DiscoReconstructor(p_depth, f_depth, c)

# Extract lightcones from my subset of files
recon.extract(myfield, boundary_condition='periodic')
del myfield

comm.Barrier()

d4p.daalinit()
recon.kmeans_lightcones(past_params, future_params, decay_type=decay_type, past_decay=p_decay, future_decay=f_decay, past_init_params=p_i_params, future_init_params=f_i_params,)
recon.reconstruct_morphs()
comm.Barrier()
comm.Allreduce(recon.local_joint_dist, recon.global_joint_dist, op=MPI.SUM ) 
recon.reconstruct_states(chi_squared)
recon.causal_filter()

save_dir = '/global/project/projectdirs/ProjectDisCo/Adam/jupiter/results/result-{}/fields/'.format(result)
save_name = 'jup_states_{:03d}'.format(rank)
np.save(save_dir+save_name, recon.state_field)

comm.Barrier()

if rank == 0:
    end = time.time()
    print('Minutes to Solution: {}'.format((end-start)/60))
    print('past depth: {}, \nfuture depth: {}, \nc: {}, \npast K: {}, \nfuture K: {}, \npast decay: {}, \nfuture decay: {}, \ndecay type: {}'.format(p_depth, f_depth, c, K_past, K_future, p_decay, f_decay, decay_type))

d4p.daalfini()