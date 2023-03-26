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

run_dir = "/global/project/projectdirs/dasrepo/gmd/input/ALLHIST/run3"
allfiles = sorted(os.listdir(run_dir))
filenames = allfiles[7144:]

halo = 1
worksize = 1
observable = 'PSL'
result = '2'

lcsdir = "/global/project/projectdirs/ProjectDisCo/Adam/climate/{}/result-{}/fields/".format(observable,result)
N_lcs = len(os.listdir(lcsdir))

data = []
states = []
for rank in range(N_lcs):
    myfiles = filenames[rank*worksize : (rank+1)*worksize + 2*halo]
    work_files = myfiles[halo : -halo]
    myfield = np.vstack([Dataset(run_dir+ '/'+f, 'r')[observable][:] for f in work_files])
    data.append(myfield)
    load_file = work_files[0][:-3]+'-1.npy'
    load_field = np.load(lcsdir + load_file)
    states.append(load_field)
    
field = np.vstack(data)
state_field = np.vstack(states)

anim = comparison_animate(field[8:-3], state_field[8:-3], ticks=False, invert_y=False, field_cmap=plt.cm.Greys)

Writer = animation.writers['ffmpeg']
writer = Writer(fps=25, metadata=dict(artist='Me'), bitrate=1800)

anim.save("{}-{}.mp4".format(observable,result), writer=writer)
# anim.save("TS_1.mp4", writer='ffmpeg', fps=30)

end = time.time()
print('Run time in minutes: {}'.format((end-start)/60))