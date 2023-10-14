import numpy as np
import os
from netCDF4 import Dataset
from skimage.measure import block_reduce

import os, sys
module_path = os.path.abspath(os.path.join('../src/'))
sys.path.append(module_path)
from pdisco import *

turb_field = np.load("./turb_small.npy")

'''
first try running the code as is with the line below commented out, 
if memory runs out you can try running with the line uncommented;
if there is still not enough memory available, try setting block_size=(1,4,4) for further data size reduction
'''
# turb_field = block_reduce(turb_field, block_size=(1,2,2), func=np.mean) # do a 2x2 mean pooling reduction

# Initialize parameters for pipeline
p_depth = 3
f_depth = 1
c = 1
K_past = 3
K_future = 10
decay_type='spacetime'
p_decay = 0.05
f_decay = 0.0

past_params = {'nClusters':K_past, 'maxIterations':200}
future_params = {'nClusters':K_future, 'maxIterations':200}
p_i_params = {'nClusters':K_past, 'method':'randomDense', 'distributed': False}
f_i_params = {'nClusters':K_future, 'method':'randomDense', 'distributed': False}

model = DiscoReconstructor(p_depth, f_depth, c, distributed=False)
model.extract(turb_field, boundary_condition='periodic')
model.kmeans_lightcones(past_params, 
                        future_params, 
                        decay_type=decay_type, 
                        past_decay=p_decay, 
                        future_decay=f_decay, 
                        past_init_params=p_i_params, 
                        future_init_params=f_i_params,)
model.reconstruct_morphs()
model.reconstruct_states(chi_squared)
model.causal_filter()

np.save("./turb-test-states.npy", model.state_field)