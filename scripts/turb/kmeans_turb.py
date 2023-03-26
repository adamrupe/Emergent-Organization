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
from netCDF4 import Dataset

#Parent directory which contains the disco repo
module_path = os.path.abspath(os.path.join('/global/common/software/ProjectDisCo/'))
sys.path.append(module_path)

from source.pdisco import *

K = 3

# Load data with appropriate halos
data_file = "/global/project/projectdirs/ProjectDisCo/Adam/turb/data/twodimturb_03_his.nc"
data = Dataset(data_file)
myfield = data['vorticity'][:]
myfield = np.absolute(myfield)
myshape = np.shape(myfield)

field = myfield.flatten().reshape(-1,1)

params = {'nClusters':K, 'maxIterations':200}
init_params = {'nClusters':K, 'method':'plusPlusDense', 'distributed': False}

d4p.daalinit()
initial = d4p.kmeans_init(**init_params)
init_centroids = initial.compute(field).centroids
cluster = d4p.kmeans(**params).compute(field, init_centroids)
centroids = cluster.centroids
assignments = d4p.kmeans(nClusters=K, distributed=False, assignFlag=True, maxIterations=0).compute(field, centroids).assignments.flatten()

assign_field = assignments.reshape(myshape)

save_dir = '/global/project/projectdirs/ProjectDisCo/Adam/turb/data/'
save_name = 'abs_vort_kmeans_K-{:02d}'.format(K)
np.save(save_dir+save_name, assign_field)

d4p.daalfini()