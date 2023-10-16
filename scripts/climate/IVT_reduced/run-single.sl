#!/bin/bash 
#SBATCH --qos=regular
#SBATCH -t 01:00:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH -J iar-3
#SBATCH --constraint=cpu
#SBATCH -o /pscratch/sd/a/atrupe/DisCo/results/IVT_alt_red/res3/params.log
#SBATCH -e /pscratch/sd/a/atrupe/DisCo/results/IVT_alt_red/res3/run.err
#SBATCH --mail-user=atrupe@ucdavis.edu
#SBATCH --mail-type=END,FAIL

cp /pscratch/sd/a/atrupe/DisCo/scripts/IVT_reduced/climate-single.py /pscratch/sd/a/atrupe/DisCo/results/IVT_alt_red/res3/ivt_alt_red-3.py

srun -n 1 python /pscratch/sd/a/atrupe/DisCo/scripts/IVT_reduced/climate-single.py 