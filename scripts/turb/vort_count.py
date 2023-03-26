'''
author: Adam Rupe
email: atrupe@ucdavis.edu
brief: animate climate segmentation results
dependencies: python3, matplotlib, ffmpeg
'''
import os, sys
from skimage.measure import label

#Parent directory which contains the disco repo
module_path = os.path.abspath(os.path.join('/global/common/software/ProjectDisCo/'))
sys.path.append(module_path)

from source.visuals import *

result = '18'
vortex_states = [7]

# file = "/global/project/projectdirs/ProjectDisCo/Adam/turb/data/abs_vort_kmeans_K-03.npy"
# state_field = np.load(file)

lcsdir = "/global/project/projectdirs/ProjectDisCo/Adam/turb/results/result-{}/fields/".format(result)
lcsfiles = sorted(os.listdir(lcsdir))
lcs_fields = []

for file in lcsfiles:
    lcs_field = np.load(lcsdir + file)
    lcs_fields.append(lcs_field)

state_field = np.vstack(lcs_fields)

vortex_counts = []

for lcs_field in state_field:
    filtered_field = np.zeros(np.shape(lcs_field), dtype=int)
    for state in vortex_states:
        filtered_field[lcs_field == state] = 1
    labels = label(filtered_field)
    num_vortices = np.max(labels)
    vortex_counts.append(num_vortices)

    
save_dir = '/global/project/projectdirs/ProjectDisCo/Adam/turb/analysis/counts/'.format(result)
save_name = 'vortex_counts-{}'.format(result)
np.save(save_dir+save_name, np.array(vortex_counts))