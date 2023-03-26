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


observable = 'IVT_alt'
result = '17'

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
        obs_load = Dataset(run_dir+obs_name, 'r')["TMQ"][:]
#         obs_load = Dataset(run_dir+obs_name, 'r')[observable][:]
    obs_field = obs_load[index]
    obs_fields.append(obs_field)
    
state_field = np.vstack(lcs_fields)

# filt_field = np.empty(np.shape(state_field), dtype=int)
# for ind, field in enumerate(state_field):
#     filt = filt_field[ind]
#     counts = np.unique(field, return_counts=True)[1]
#     for sind, state in enumerate(counts.argsort()):
#         filt[field==state] = sind
    
obs = np.stack(obs_fields)

# anim = comparison_animate(field[past_depth:-future_depth], state_field[past_depth:-future_depth], ticks=False, invert_y=False, field_cmap=plt.cm.Blues, state_cmap=plt.cm.Set3)
anim = comparison_animate(obs, state_field, xtick_spacing=100, ytick_spacing=50, invert_y=False, field_cmap=plt.cm.Blues, state_cmap=plt.cm.tab20)


Writer = animation.writers['ffmpeg']
writer = Writer(fps=18, metadata=dict(artist='Me'))

anim.save("{}-{}.mp4".format(observable,result), writer=writer)

end = time.time()
print('Run time in minutes: {}'.format((end-start)/60))
