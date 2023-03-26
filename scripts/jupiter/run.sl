#!/bin/bash -l

#SBATCH -p regular
#SBATCH -t 0:20:00
#SBATCH --nodes=103
#SBATCH --tasks-per-node=2
#SBATCH --cpus-per-task=32
#SBATCH -C haswell
#SBATCH -J jup-9
#SBATCH -o /global/project/projectdirs/ProjectDisCo/Adam/jupiter/results/result-9/params.log
#SBATCH -e /global/project/projectdirs/ProjectDisCo/Adam/jupiter/results/result-9/run.err
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

srun -n 206 python -m tbb -p 32 --ipc /global/common/software/ProjectDisCo/Adam/jupiter/jupiter.py 
