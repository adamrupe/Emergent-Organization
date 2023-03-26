#!/bin/bash -l

#SBATCH -p regular
#SBATCH -t 01:00:00
#SBATCH --nodes=183
#SBATCH --tasks-per-node=2
#SBATCH --cpus-per-task=32
#SBATCH -C haswell
#SBATCH -J turb-18
#SBATCH -o /global/project/projectdirs/ProjectDisCo/Adam/turb/results/result-18/params.log
#SBATCH -e /global/project/projectdirs/ProjectDisCo/Adam/turb/results/result-18/run.err
#SBATCH --mail-user=atrupe@ucdavis.edu
#SBATCH --mail-type=END

module load python/3.6-anaconda-4.4
module unload darshan

export MKL_NUM_THREADS=16
export NUMBA_THREADING_LAYER=TBB
export KMP_BLOCKTIME=10
export HDF5_USE_FILE_LOCKING=FALSE

source /global/common/software/ProjectDisCo/pyenv/kmeans_hsw/bin/activate

#parallel
# n = total no. of processes
# tasks-per-node = mpi processes per node

srun -n 366 python -m tbb -p 32 --ipc /global/common/software/ProjectDisCo/Adam/turb/turb.py 

# for interactive -- check jupypter notebook to calc -N and -n from desired lightcone params and work size:
# salloc -N 59 -C haswell -q interactive -t 01:00:00
# srun -n 118 --tasks-per-node=2 --cpus-per-task=32 python -m tbb -p 32 --ipc ./turb.py >> $SCRATCH/results/turbulence/SC19/result-21/params.txt