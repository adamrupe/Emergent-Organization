'''
author: Adam Rupe
email: atrupe@ucdavis.edu
brief: animate climate segmentation results
dependencies: python3, matplotlib, ffmpeg
'''
import os, sys
from netCDF4 import Dataset

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.animation as animation

#Parent directory which contains the disco repo
module_path = os.path.abspath(os.path.join('/global/common/software/ProjectDisCo/'))
sys.path.append(module_path)

from source.visuals import *

observable = 'TMQ' # need to change run_dir for IVT
state = 'IVT_alt'
result = '12'

# load obs
run_dir = "/global/project/projectdirs/dasrepo/gmd/input/ALLHIST/run1/"
obs_fields = []
lcsdir = "/global/project/projectdirs/ProjectDisCo/Adam/climate/{}/result-{}/fields/".format(state,result)
lcsfiles = sorted(os.listdir(lcsdir))

for i,s in enumerate(lcsfiles):
    index = i%8
    if index == 0:
        obs_name = s[:-6]+'00000.nc'
        obs_load = Dataset(run_dir+obs_name, 'r')[observable][:]
    obs_field = obs_load[index]
    obs_fields.append(obs_field)
    
field = np.stack(obs_fields)

# load states
lcsdir = "/global/project/projectdirs/ProjectDisCo/Adam/climate/{}/result-{}/fields/".format(state,result)
lcsfiles = sorted(os.listdir(lcsdir))
lcs_fields = []

for i,s in enumerate(lcsfiles):
    s_field = np.load(lcsdir+s)
    lcs_fields.append(s_field)
    
state_field = np.vstack(lcs_fields)

# special mask to highlight particular states
maskedIVT = np.zeros(np.shape(state_field), dtype=int)
maskedIVT[state_field==1] = 1
maskedIVT[state_field==3] = 1
maskedIVT[state_field==4] = 1
maskedIVT[state_field==5] = 1
maskedIVT[state_field==7] = 1
maskedIVT[state_field==8] = 1


# plots and animation
T,H,W = np.shape(field)
size = 24
fig, ax = plt.subplots(figsize = (size, (H/W)*size))
im1 = ax.imshow(field[0], cmap=plt.cm.Blues)
im2 = ax.imshow(maskedIVT[0], cmap=plt.cm.Greys, alpha=0.5)
ax.invert_yaxis()
ax.tick_params(axis='both',
                        which='both',
                        bottom=False,
                        top=False,
                        left=False,
                        right=False,
                        labelleft=False,
                        labelbottom=False)

plt.close() # prevents initial figure from being displayed in jupyter notebook

# def animate(i):
#     im1.set_array(field[i].flatten())
#     im2.set_array(maskedIVT[i].flatten())

def animate(i):
    im1.set_array(field[i])
    im2.set_array(maskedIVT[i])

frames = T
anim = animation.FuncAnimation(fig, animate, frames=frames)


Writer = animation.writers['ffmpeg']
writer = Writer(fps=20, metadata=dict(artist='Me'))

anim.save("IVT_alt_mask-12.mp4", writer=writer)
