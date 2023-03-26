#!/bin/bash -l

#SBATCH -p regular
#SBATCH -t 0:20:00
#SBATCH --nodes=1
#SBATCH --tasks-per-node=2
#SBATCH --cpus-per-task=32
#SBATCH -C haswell
#SBATCH -J count-15
#SBATCH -o /global/project/projectdirs/ProjectDisCo/Adam/turb/analysis/slurm_logs/%j_hsl.log
#SBATCH -e /global/project/projectdirs/ProjectDisCo/Adam/turb/analysis/slurm_logs/%j_hsl.err
#SBATCH --mail-user=atrupe@ucdavis.edu
#SBATCH --mail-type=END,FAIL

module load python/3.6-anaconda-4.4
module unload darshan

export MKL_NUM_THREADS=16
export NUMBA_THREADING_LAYER=TBB
export KMP_BLOCKTIME=10
export HDF5_USE_FILE_LOCKING=FALSE

#source activate animate

#parallel
# n = total no. of processes
# tasks-per-node = mpi processes per node

srun -n 1 python /global/project/projectdirs/ProjectDisCo/Adam/turb/analysis/vort_count.py

# for interactive -- check jupypter notebook to calc -N and -n from desired lightcone params and work size:
# salloc -N 1 -C haswell -q interactive -t 0:30:00
# srun -n 1 python ./animate_TMQ.py 