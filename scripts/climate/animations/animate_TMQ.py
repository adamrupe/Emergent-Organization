'''
author: Adam Rupe
email: atrupe@ucdavis.edu
brief: animate climate segmentation results
dependencies: python3, matplotlib, ffmpeg
'''
import time, os, sys
from netCDF4 import Dataset

#Parent directory which contains the disco repo
module_path = os.path.abspath(os.path.join('/global/common/software/ProjectDisCo/'))
sys.path.append(module_path)

from source.visuals import *

start = time.time()

# run_dir = "/global/project/projectdirs/dasrepo/gmd/input/ALLHIST/run1"
# allfiles = sorted(os.listdir(run_dir))
# filenames = allfiles[7334:]

# halo = 1
# worksize = 1
# observable = 'TMQ'
# result = '3'

# lcsdir = "/global/project/projectdirs/ProjectDisCo/Adam/climate/{}/result-{}/fields/".format(observable,result)
# N_lcs = len(os.listdir(lcsdir))

# data = []
# states = []
# for rank in range(N_lcs):
#     myfiles = filenames[rank*worksize : (rank+1)*worksize + 2*halo]
#     work_files = myfiles[halo : -halo]
#     myfield = np.vstack([Dataset(run_dir+ '/'+f, 'r')[observable][:] for f in work_files])
#     data.append(myfield)
#     load_file = work_files[0][:-3]+'-1.npy'
#     load_field = np.load(lcsdir + load_file)
#     states.append(load_field)
    
# field = np.vstack(data)
# state_field = np.vstack(states)

# ***SINGLE TIME STEP WORKLOAD ***

observable = 'TMQ'
result = '9'
# past_depth = 14
# future_depth = 3

run_dir = "/global/project/projectdirs/dasrepo/gmd/input/ALLHIST/run1/"
obs_fields = []
lcsdir = "/global/project/projectdirs/ProjectDisCo/Adam/climate/{}/result-{}/fields/".format(observable,result)
lcsfiles = sorted(os.listdir(lcsdir))
lcs_fields = []

for i,s in enumerate(lcsfiles):
    s_field = np.load(lcsdir+s)
    lcs_fields.append(s_field)
    index = i%8
    if index == 0:
        obs_name = s[:-6]+'00000.nc'
        obs_load = Dataset(run_dir+obs_name, 'r')[observable][:]
    obs_field = obs_load[index]
    obs_fields.append(obs_field)
    
state_field = np.vstack(lcs_fields)
field = np.stack(obs_fields)

# anim = comparison_animate(field[past_depth:-future_depth], state_field[past_depth:-future_depth], ticks=False, invert_y=False, field_cmap=plt.cm.Blues, state_cmap=plt.cm.Set3)
anim = comparison_animate(field, state_field, xtick_spacing=100, ytick_spacing=50, field_cmap=plt.cm.Blues, state_cmap=plt.cm.Set3)


Writer = animation.writers['ffmpeg']
writer = Writer(fps=20, metadata=dict(artist='Me'))

anim.save("{}-{}.mp4".format(observable,result), writer=writer)

end = time.time()
print('Run time in minutes: {}'.format((end-start)/60))