'''
author: Adam Rupe
email: atrupe@ucdavis.edu
brief: Test run on climate data
dependencies: python3, numpy, numba, mpi4py, daal4py

Quick and dirty code to get results for 4x4 downsampled low-res climate data
'''

# OPT: import only parts of os and sys that we need?
import time, os, sys

#Parent directory which contains the disco repo
module_path = os.path.abspath(os.path.join('/pscratch/sd/a/atrupe/DisCo/'))
sys.path.append(module_path)

from src.pdisco import *

full_start = time.time()

# Initialize parameters for pipeline
past_depth = 6
future_depth = 3
c = 1
past_K = 14
future_K = 20
decay = 0.5
past_params = {'nClusters':past_K, 'maxIterations':200}
future_params = {'nClusters':future_K, 'maxIterations':200}

# A = 0.25

observable = 'IVT_alt'
result = '3'

d4p.daalinit()

# Load TMQ data for one time-step per process
tmq_dir = "/pscratch/sd/a/atrupe/DisCo/data/reduced_npy_data/TMQ/"
tmq_files = sorted(os.listdir(tmq_dir))
TMQfield = np.vstack([np.load(tmq_dir+f) for f in tmq_files])

# extract from TMQ first    
reconQ = DiscoReconstructor(past_depth, future_depth, c)
reconQ.extract(TMQfield)
del TMQfield

# Load U850 data for one time-step per process
u850_dir = "/pscratch/sd/a/atrupe/DisCo/data/reduced_npy_data/U850/"
u850_files = sorted(os.listdir(u850_dir))
Ufield = np.vstack([np.load(u850_dir+f) for f in u850_files])

# now extract from U850
reconU = DiscoReconstructor(past_depth, future_depth, c)
reconU.extract(Ufield)
del Ufield

# Load V850 data for one time-step per process
v850_dir = "/pscratch/sd/a/atrupe/DisCo/data/reduced_npy_data/V850/"
v850_files = sorted(os.listdir(v850_dir))
Vfield = np.vstack([np.load(v850_dir+f) for f in v850_files])

# now extract from V850
reconV = DiscoReconstructor(past_depth, future_depth, c)
reconV.extract(Vfield)
del Vfield

# combine U and V lightcones onto TMQ lightcones
plcs_1 = (reconU.plcs*reconQ.plcs)*(reconU.plcs*reconQ.plcs)
plcs_2 = (reconV.plcs*reconQ.plcs)*(reconV.plcs*reconQ.plcs)
reconQ.plcs = np.concatenate((plcs_1, plcs_2), axis=1)
flcs_1 = (reconU.flcs*reconQ.flcs)*(reconU.flcs*reconQ.flcs)
flcs_2 = (reconV.flcs*reconQ.flcs)*(reconV.flcs*reconQ.flcs)
reconQ.flcs = np.concatenate((flcs_1, flcs_2), axis=1)

plc_decays = np.concatenate(( past_spacetime_decay(past_depth, c, decay), past_spacetime_decay(past_depth, c, decay) ))
reconQ.plcs *= np.sqrt(plc_decays)
reconQ.kmeans_lightcones(past_params, future_params, decay_type='none', past_decay=0, future_decay=0)
# reconQ.reconstruct_morphs()
# comm.Barrier() 
# comm.Allreduce(reconQ.local_joint_dist, reconQ.global_joint_dist, op=MPI.SUM ) 
# reconQ.reconstruct_states(chi_squared)
# reconQ.causal_filter()
state_field = reconQ.pasts.reshape(*reconQ._adjusted_shape)
spatial_pad = reconQ._padding
margin_padding = (
                            (past_depth, future_depth), # do temporal margin for single-node
                            (spatial_pad, spatial_pad),
                            (spatial_pad, spatial_pad)
                        )
state_field = np.pad(state_field, margin_padding, 'constant')

save_dir = '/pscratch/sd/a/atrupe/DisCo/results/IVT_alt_red/res{}/fields/'.format(result)
np.save(save_dir+"LCS_1deg_reduced-full", state_field)

run_details = "past_depth: {} \nfuture_depth: {} \nc :{} \
               \npast_K: {} \nfuture_K: {} \nlc decay: {} ".format(past_depth, 
                                                                    future_depth, 
                                                                    c, 
                                                                    past_K, 
                                                                    future_K, 
                                                                    decay)

full_end = time.time()
print("Multivariate analysis with lightcone metric to replicate IVT---(U850*TMQ)^2 concat (V850*TMQ)^2 lightcones---spacetime decays applied appropriately.")
print(run_details)
print('Time to solution: {}'.format(full_end-full_start))

d4p.daalfini()