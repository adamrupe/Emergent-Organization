#!/bin/bash -l

#SBATCH -p regular
#SBATCH -t 0:40:00
#SBATCH --nodes=250
#SBATCH --tasks-per-node=2
#SBATCH --cpus-per-task=32
#SBATCH -C haswell
#SBATCH -J PSL-seg3
#SBATCH -o /global/project/projectdirs/ProjectDisCo/Adam/climate/PSL/result-3/params.log
#SBATCH -e /global/project/projectdirs/ProjectDisCo/Adam/climate/PSL/result-3/run.err
#SBATCH --mail-user=atrupe@ucdavis.edu
#SBATCH --mail-type=END,FAIL

module load python/3.6-anaconda-4.4
module unload darshan

export MKL_NUM_THREADS=16
export NUMBA_THREADING_LAYER=TBB
export KMP_BLOCKTIME=10

source /global/common/software/ProjectDisCo/pyenv/kmeans_hsw/bin/activate

#parallel
# n = total no. of processes
# tasks-per-node = mpi processes per node


srun -n 500 python -m tbb -p 32 --ipc /global/common/software/ProjectDisCo/Adam/climate/PSL/climate.py 

# for interactive -- check jupypter notebook to calc -N and -n from desired lightcone params and work size:
# salloc -N 20 -C haswell -q interactive -t 01:00:00
# srun -n 40 --tasks-per-node=2 --cpus-per-task=32 python -m tbb -p 32 --ipc ./climate-test.py >> /global/project/projectdirs/ProjectDisCo/Adam/climate/TMQ/result-test2/params.txt