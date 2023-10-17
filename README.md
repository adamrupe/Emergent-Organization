# Unsupervised Discovery of Extreme Weather Events Using Universal Representations of Emergent Organization

# Overview

This repo provides source code, SLURM run scripts, parameter logs, and Jupyter notebooks displaying results and figures supporting the manuscript *Unsupervised Discovery of Extreme Weather Events Using Universal Representations of Emergent Organization*. The source code used was created previously as part of [Project DisCo](https://arxiv.org/abs/1909.11822)

# Contents

- src  
    Contains DisCo source code for local causal state reconstruction and segmentation, as well as code for visualization. 
- scripts  
    Python and SLURM run scripts used to perform local causal state segmentation on climate, turbulence, and Jupiter data sets, originally ran on the Cori supercomputer at NERSC.
- param-logs  
    A record of reconstruction and segmentation parameters used for various experiments on Cori. 
- notebooks  
    Collection of jupyter notebooks that perform and demonstrate (results are rendered when opened on GitHub) all post-segmentation analyses, as well as creation of Figures used in the manuscript. 
- test-single-node  
    Small turbulence data set and accompanying jupyter notebook and Python script to run and test the full local causal state segmentation pipeline on a single machine. 

# Installation

DisCo is built on the [Intel Distribution for Python](https://www.intel.com/content/www/us/en/developer/articles/technical/get-started-with-intel-distribution-for-python.html), and we recommend managing dependencies using [conda](https://docs.conda.io/projects/conda/en/stable/user-guide/index.html). 

All required dependencies can be installed on Linux, Windows, and MacOS. However, because DisCo utilizes the Intel Distribution for Python and `daal4py`, it will not run on ARM architectures, like the Apple M1 processor. 

A `disco` conda environment with all the required dependencies can be created from `disco-env.yml` file, which contains all package dependencies with specific version information. 

```
conda env create -f disco-env.yml
```

The environment can also be created manually. 

```
conda config --add channels intel 
conda create -n disco intelpython3_core python=3.8 
conda activate disco
```

Once the `disco` environment is activated, use `conda install` to install the following dependencies:

```
numba=0.57
daal4py=2023.2
netcdf4=1.6
jupyterlab=3.5
matplotlib=3.1
scikit-learn=1.3
scikit-learn-intelex=2023.2
scikit-image=0.19
cartopy=0.21
```

Disco also requires 

```
numpy=1.24
scipy=1.10
``` 

but these are automatically installed as part of `intelpython3_core` when creating the `disco` env. See `disco-deps.yml` for the full list of basic dependencies. 

DisCo was originally developed and run on the, now decommisioned, Cori supercomputer at NERSC. Because Cori used Cray MPI libraries, `daal4py` had to be [built from sources](https://github.com/intel/scikit-learn-intelex/blob/master/daal4py/INSTALL.md) with `MPI_LIBNAME` linked to the Cray MPI library in [setup.py](https://github.com/intel/scikit-learn-intelex/blob/master/setup.py).  
The conda environment used on Cori is given in `disco-cori-env.yml`.

# Basic Usage 

Unsupervised segmentation using local causal states is performed using the `DiscoReconstructor` objects defined in `src/pdisco.py`.  

First, initialize a `DiscoReconstructor` object with the basic lightcone parameters of `past_depth`, `future_depth`, and `propagation_speed`, as well as `distributed`, which specifies if reconstruction will occur over multiple nodes (`True`) or a single machine (`False`).  

Next, extract lightcones from the target dataset using `DiscoReconstruct.extract(target_field, boundary_condition='open')`. The `target_field` should be a three-dimensional `ndarray` with time on axis 0. Spatial boundary conditions can be either `'open'` (default) or `'periodic'`.  

With the lightcones extracted, they are then clustered together using `DiscoReconstructor.kmeans_lightcones()`, which utilizes the `daal4py` [implementation of K-Means clustering](https://intelpython.github.io/daal4py/algorithms.html#k-means-clustering). See the example in `test-single-node` for basic usage.

Lightcone distributions are approximated from the resulted clustering using `DiscoReconstructor.reconstruct_morphs()`, and the local causal states are then reconstructed using `DiscoReconstructor.reconstruct_states(chi_squared)`. 

Finally, to perform a local causal state segmentation on the input target field, use `DiscoReconstructor.causal_filter()`, resulting in the `.state_field` attribute for the `DiscoReconstructor` object. 

Details of implementation and HPC performance can be found in the [DisCo manuscript](https://arxiv.org/abs/1909.11822).

Refer to the `test-single-node` directory for example usage. The test code should run on an 8 GB RAM laptop in under 2 minutes.  
The full reconstruction pipeline, as used in `test-single-node` on the `turb_field` dataset is: 

```python
p_depth = 3
f_depth = 1
c = 1
K_past = 3
K_future = 10
decay_type='spacetime'
p_decay = 0.05
f_decay = 0.0

past_params = {'nClusters':K_past, 'maxIterations':200}
future_params = {'nClusters':K_future, 'maxIterations':200}
p_i_params = {'nClusters':K_past, 'method':'randomDense', 'distributed': False}
f_i_params = {'nClusters':K_future, 'method':'randomDense', 'distributed': False}

model = DiscoReconstructor(p_depth, f_depth, c, distributed=False)
model.extract(turb_field, boundary_condition='periodic')
model.kmeans_lightcones(past_params, 
                        future_params, 
                        decay_type=decay_type, 
                        past_decay=p_decay, 
                        future_decay=f_decay, 
                        past_init_params=p_i_params, 
                        future_init_params=f_i_params,)
model.reconstruct_morphs()
model.reconstruct_states(chi_squared)
model.causal_filter()
```