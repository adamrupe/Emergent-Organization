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

run_dir = "/global/project/projectdirs/dasrepo/gmd/input/ALLHIST/run1"
allfiles = sorted(os.listdir(run_dir))
#filenames = allfiles[7552:]
filenames = allfiles[7522:]

IVT_dir = "/global/cscratch1/sd/mwehner/machine_learning_climate_data/All-Hist/CAM5-1-0.25degree_All-Hist_est1_v3_run1/IVT"
IVTfiles = sorted(os.listdir(IVT_dir))
#IVTnames = IVTfiles[7200:]
IVTnames = IVTfiles[7170:]

halo = 1
worksize = 1
obs_1 = 'TMQ'
obs_2 = 'IVT'
result = '4'

N = 64

data_1 = []
data_2 = []
for rank in range(N):
    myfiles = filenames[rank*worksize : (rank+1)*worksize + 2*halo]
    work_files = myfiles[halo : -halo]
    myfield = np.vstack([Dataset(run_dir+ '/'+f, 'r')[obs_1][:] for f in work_files])
    data_1.append(myfield)
    
    IVTs = IVTnames[rank*worksize : (rank+1)*worksize + 2*halo]
    IVTwork = IVTs[halo: -halo]
    IVTfield = np.vstack([Dataset(IVT_dir+ '/'+f, 'r')[obs_2][:] for f in IVTwork])
    data_2.append(IVTfield)

    
field_1 = np.vstack(data_1)
field_2 = np.vstack(data_2).astype(np.float32)

anim = comparison_animate(field_1, field_2, ticks=False, invert_y=False, field_cmap=plt.cm.Blues, state_cmap=plt.cm.Blues)

Writer = animation.writers['ffmpeg']
writer = Writer(fps=25, metadata=dict(artist='Me'))

anim.save("{}-{}.mp4".format('OBS',result), writer=writer)

end = time.time()
print('Run time in minutes: {}'.format((end-start)/60))