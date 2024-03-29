import numpy as np
import daal4py as d4p

from numba import njit
from scipy.stats import chisquare
from collections import Counter
from itertools import product


def dist_from_data(X, Y, Nx, Ny):#, row_labels=False, column_labels=False):
    '''
    Creates a conditional distribution P(X,Y) from sample observations of pairs (x,y).
    Joint distribution given as nd array. X and Y assumed to take values from
    [0,1,...,Nx-1] and [0,1,...,Ny-1].

    Parameters
    ----------
    X: array-like
        Sample observations of X. Must take values from [0,1,...,Nx-1],
        where Nx is the number of unique possible outcomes of X.

    Y: array-like
        Sample observations of Y. Must take values from [0,1,...,Ny-1],
        where Ny is the number of unique possible outcomes of Y.

    row_labels: bool, optional (default=False)
        Option to add an extra column, transpose([0,1,...,Nx-1]),
        to the left (i.e. column 0) of the distribution array. This extra
        column serves as labels for X; useful if permutations are performed
        on the distribution array.

    column_labels: bool, optional (default=False)
        Option to add an exra row, [0,1,...,Ny-1], to the top (i.e. row 0)
        of the distribution array. This extra row serves as a labels for Y;
        useful if permutations are performed on the distribution array.

    Returns
    -------
    dist: ndarray
        An ndarray of shape (Nx, Ny) representing the joint distribution of
        X and Y; dist[i,j] = P(X=i, Y=j). Rows and columns are conditional distributions,
        e.g. dist[i] = P(Y | X=i).
    '''
    dist = np.zeros((Nx, Ny), dtype=np.uint64)

    counts = Counter(zip(X,Y))

    for pair, count in counts.items():
        dist[pair] = count

    return dist


class CausalState(object):
    '''
    Class for the local causal state objects. Mostly a data container -- keeps
    the integer label for the state (State.index), the set of pasts in the
    state (State.pasts), and the weighted average morph for the state (State.morph).

    Could just use a namedtuple, but for now keeping it as a class.
    '''

    def __init__(self, state_index, first_past, first_morph):
        '''
        Initializes the CausalState instance with the state label, the first
        past that belongs to the state, and the morph of that first past.

        Parameters
        ----------
        state_index: int
            Integer label for the state.

        first_past: int
            Label for the past lightcone cluster (past) that has first been
            placed in the CausalState instance.

        first_morph: array
            1D array of counts of futures seen with first_past, i.e.
            the (non-normalized) morph of first_past.
        '''
        self.index = state_index
        self.pasts = {first_past}
        self.counts = np.copy(first_morph)
        self.morph = np.copy(first_morph)
        self.entropy = None

    def update(self, past, morph_counts):
        '''
        Adds the new past lightcone into the state and updates the state's morph,
        which is the aggregate count over futures from all pasts in the state.

        Parameters
        ----------
        past: int
            Label for the new past lightcone cluster (past) being added into the
            state.

        morph_counts: array
            1D array of counts of futures seen with the new past being added into
            the state.
        '''
        self.pasts.add(past)
        self.counts += morph_counts
        # average counts over the contributions from each past of the state
        self.morph = np.copy(self.counts)
        self.morph = np.divide(self.morph, len(self.pasts))
        self.entropy = None

    def normalized_morph(self):
        '''
        Returns the normalized morph of the state.
        This is not needed for the chi squared distribution comparison currently
        used, so don't want to do this calculation unless desired. May be needed
        in the future for different distribution comparisons.
        '''
        # OPT: memoize
        morph = self.morph / np.sum(self.morph)
        return morph

    def morph_entropy(self):
        '''
        Returns the Shannon entropy of the state's morph.
        '''
        if self.entropy is None:
            morph = self.normalized_morph()
            non_zero = morph[morph != 0]
            self.entropy = np.sum(-non_zero * np.log2(non_zero))
        return self.entropy


def chi_squared(X, Y, *args, offset=10, **kwargs):
    '''
    Returns the p value for the scipy 1-way chi_squared test.
    In our use, X should be the morph for a past, and Y the
    morph for a past cluster (local causal state).

    As the distributions we encounter will sometimes have zero
    counts, this function adds 10 to all counts as a quick hack
    to circumvent this (the scipy chisquare will return nan if
    it encounters zero counts)

    Parameters
    ----------
    X: array
        Array of counts (histogram) for empirical distribution X.

    Y: array
        Array of counts (histogram) for empirical distribution Y.

    Returns
    -------
    p: float
        The p value of the chi square comparison.
    '''
    adjusted_X = X + offset
    adjusted_Y = Y + offset
    
    try:
        output = chisquare(adjusted_X, adjusted_Y, *args, **kwargs)
        pval = output.pvalue 
    except ValueError:
        pval = 0.0

    return pval


@njit(fastmath=True)
def lightcone_size_2D(depth, c):
    size = 0
    for d in range(depth+1):
        size += (2*c*d + 1)**2
    return size



@njit
def extract_lightcones_2D(padded_data, T, Y, X, past_depth, future_depth, c, base_anchor):
    '''
    Returns arrays of past and future lightcones extracted from the given data.
    If the original data has periodic boundary conditions, it must be pre-padded
    before being given to this function.


    Parameters
    ----------
    padded_data: ndarray
        3D Spacetime array of target data from which lightcones are to be extracted.
        Time should be the 0th axis (vertical) and space Y and X on the following axes.
        If the original spacetime data has periodic boundary conditions, it should
        be pre-padded accordingly.

    T: int
        Size of the temporal dimension of the original (unpadded) spacetime field, minus the margin.

    Y: int
        Size of the vertical spatial dimension of the original (upadded) spacetime field, minus the margin.

    X: int
        Size of the horizontal spatial dimension of the original (unpadded) spacetime field, minus the margin.

    past_depth: int
        Depth of the past lightcones to be extracted.

    future_depth: int
        Depth of the future lightcones to be extracted.

    past_size: int
        Size of the flattened past lightcone arrays.

    future_size: int
        Size of the flattened future lightcone arrays.

    c: int
        Propagation speed of the spacetime field.

    base_anchor: (int, int)
        Spacetime indices that act as reference point for indices that are "moved"
        throughout the spacetime field to extract lightcones at those points.
        Should start in the top left of the spacetime field, accounting for the
        margin and periodic boundary condition padding.

    Returns
    -------
    lightcones: (array, array)
        Returns tuple of arrays, (past_lightcones, future_lightcones), extracted
        from the spacetime field.
    '''
    dtype = padded_data.dtype
    past_size = lightcone_size_2D(past_depth, c)
    future_size = lightcone_size_2D(future_depth, c) - 1
    plcs = np.zeros((T*Y*X, past_size), dtype=dtype)
    flcs = np.zeros((T*Y*X, future_size), dtype=dtype)
    base_t, base_y, base_x = base_anchor # reference starting point for spacetime indices

    i = 0
    for t in range(T):
        for y in range(Y):
            for x in range(X):
                # loops for past lightcone
                p = 0
                for d in range(past_depth + 1):
                    span = np.arange(-d*c, d*c + 1)
                    for a in span:
                        for b in span:
                            plcs[i,p] = padded_data[base_t+t-d, base_y+y+a, base_x+x+b]
                            p += 1

                # loops for future lightcone
                f = 0
                for depth in range(future_depth):
                    d = depth + 1
                    span = np.arange(-d*c, d*c + 1)
                    for a in span:
                        for b in span:
                            flcs[i,f] = padded_data[base_t+t+d, base_y+y+a, base_x+x+b]
                            f += 1
                i += 1

    return (plcs, flcs)


@njit
def past_spatial_decay(depth, c, decay_rate):
    '''
    Returns an array of exponential SPATIAL decays for a given 2+1 D past lightcone shape.
    This is meant to be multiplied to a past lightcone array (or ndarray vertical stack of multiple
    lightcones of the same shape) to apply the spatial decay to the past lightcone array(s).
    ''' 
    size = lightcone_size_2D(depth, c)
    distances = np.ones(size)
    
    i = 0
    for d in range(depth+1):
        span = np.arange(-d*c, d*c + 1)
        for a in span:
            for b in span:
                distances[i] = np.sqrt((a**2) + (b**2))
                i += 1
    decays = np.exp(-distances*decay_rate)
    return decays

@njit
def future_spatial_decay(depth, c, decay_rate):
    '''
    Returns an array of exponential SPATIAL decays for a given 2+1 D future lightcone shape.
    This is meant to be multiplied to a future lightcone array (or ndarray vertical stack of multiple
    lightcones of the same shape) to apply the spatial decay to the future lightcone array(s).
    ''' 
    size = lightcone_size_2D(depth, c) - 1
    distances = np.ones(size)
    
    i = 0
    for d in range(depth):
        d += 1
        span = np.arange(-d*c, d*c + 1)
        for a in span:
            for b in span:
                distances[i] = np.sqrt((a**2) + (b**2))
                i += 1
    decays = np.exp(-distances*decay_rate)
    return decays

@njit
def past_temporal_decay(depth, c, decay_rate):
    '''
    Returns an array of exponential SPATIAL decays for a given 2+1 D past lightcone shape.
    This is meant to be multiplied to a past lightcone array (or ndarray vertical stack of multiple
    lightcones of the same shape) to apply the spatial decay to the past lightcone array(s).
    ''' 
    size = lightcone_size_2D(depth, c)
    distances = np.ones(size)
    
    i = 0
    for d in range(depth+1):
        span = np.arange(-d*c, d*c + 1)
        for a in span:
            for b in span:
                distances[i] = d
                i += 1
    decays = np.exp(-distances*decay_rate)
    return decays

@njit
def future_temporal_decay(depth, c, decay_rate):
    '''
    Returns an array of exponential SPATIAL decays for a given 2+1 D future lightcone shape.
    This is meant to be multiplied to a future lightcone array (or ndarray vertical stack of multiple
    lightcones of the same shape) to apply the spatial decay to the future lightcone array(s).
    ''' 
    size = lightcone_size_2D(depth, c) - 1
    distances = np.ones(size)
    
    i = 0
    for d in range(depth):
        d += 1
        span = np.arange(-d*c, d*c + 1)
        for a in span:
            for b in span:
                distances[i] = d
                i += 1
    decays = np.exp(-distances*decay_rate)
    return decays

@njit
def past_spacetime_decay(depth, c, decay_rate):
    '''
    Returns an array of exponential SPATIAL decays for a given 2+1 D past lightcone shape.
    This is meant to be multiplied to a past lightcone array (or ndarray vertical stack of multiple
    lightcones of the same shape) to apply the spatial decay to the past lightcone array(s).
    ''' 
    size = lightcone_size_2D(depth, c)
    distances = np.ones(size)
    
    i = 0
    for d in range(depth+1):
        span = np.arange(-d*c, d*c + 1)
        for a in span:
            for b in span:
                distances[i] = np.sqrt((a**2) + (b**2) + (d**2))
                i += 1
    decays = np.exp(-distances*decay_rate)
    return decays

@njit
def future_spacetime_decay(depth, c, decay_rate):
    '''
    Returns an array of exponential SPATIAL decays for a given 2+1 D future lightcone shape.
    This is meant to be multiplied to a future lightcone array (or ndarray vertical stack of multiple
    lightcones of the same shape) to apply the spatial decay to the future lightcone array(s).
    ''' 
    size = lightcone_size_2D(depth, c) - 1
    distances = np.ones(size)
    
    i = 0
    for d in range(depth):
        d += 1
        span = np.arange(-d*c, d*c + 1)
        for a in span:
            for b in span:
                distances[i] = np.sqrt((a**2) + (b**2) + (d**2))
                i += 1
    decays = np.exp(-distances*decay_rate)
    return decays

class DiscoReconstructor(object):
    '''
    Class for handling single-node and distributed local causal state 
    reconstruction and segmentation. The basic pipeline is:

    model = DiscoReconstructor()
    model.extract(target_field)
    model.kmeans_lightcones()
    model.reconstruct_morphs()
    model.reconstruct_states()
    model.causal_filter()

    The local causal state segmentation field is then the attribute:
    model.state_field
    '''

    def __init__(self, past_depth, future_depth, propagation_speed, distributed=True):
        '''
        Initialize Reconstructor instance with main inference parameters.
        These define the shape of the lightcone template.
        Lightcone depths are hyperparameters for the reconstruction. The
        propagation speed is either set by the system, or chosen as an inference
        parameter if not known.

        Parameters
        ----------
        past_depth: int
            Depth of the past lightcones.

        future_depth: int
            Depth of the past lightcones.

        propagation_speed: int
            Finite speed of interaction / perturbation propagation used for inference.
            Either explicitly specified by the system (like with cellular automata) or
            chosen as an inference parameter to capture specific physics (e.g. chosing
            advection scale rather than accoustic scale for climate).
        '''
        # inference params
        self.past_depth = past_depth
        self.future_depth = future_depth
        self.c = propagation_speed

        self._distributed = distributed

        # for causal clustering and filtering
        self.states = []
        self.epsilon_map = {}
        self._state_index = 1

        # for lightcone extraction
        max_depth = max(self.past_depth, self.future_depth)
        self._padding = max_depth*self.c

        # initialize some attributes to None for pipeline fidelity
        self.plcs = None
        self.target_pasts = None
        self.joint_dist = None
        self._adjusted_shape = None

    def extract(self, field, boundary_condition='open'):
        '''
        Scans target field that is to be filtered after local causal state reconstruction.
        This is the first method that should be run.

        Parameters
        ----------
        field: ndarray
            2D or 3D array of the target spacetime field. In both cases time should
            be the zero axis.

        boundary_condition: str, optional (default='open')
            Set according to boundary conditions of the target field. Can only be
            either 'open' or 'periodic'. Open leaves a spatial margin where lightcones
            are not collected. Periodic gathers lightcones across the whole spatial
            lattice. Any additional training fields scanned with the .extract_more()
            method will be treated with same boundary conditions specified here.
        '''
        self._base_anchor = (self.past_depth, self._padding, self._padding)

        shape = np.shape(field)
        if len(shape) != 3:
            raise ValueError("Input field must be 3 dimensions")

        T, Y, X = shape
        adjusted_T = T - self.past_depth - self.future_depth # always cut out time margin
        if boundary_condition == 'open':
            adjusted_Y = Y - 2*self._padding # also have spatial margin for open boundaries
            adjusted_X = X - 2*self._padding
            padded_field = field
        elif boundary_condition == 'periodic':
            adjusted_Y = Y # no spatial margin for periodic boundaries
            adjusted_X = X
            padded_field = np.pad(field,
                                  (
                                      (0,0),
                                      (self._padding, self._padding),
                                      (self._padding, self._padding)
                                  ),
                                  'wrap')
        else:
            raise ValueError("boundary_condition must be either 'open' or 'periodic'.")
        self._adjusted_shape = (adjusted_T, adjusted_Y, adjusted_X)
        self._bc = boundary_condition


        self.plcs, self.flcs = extract_lightcones_2D(padded_field, *self._adjusted_shape,
                                                    self.past_depth,
                                                    self.future_depth,
                                                    self.c,
                                                    self._base_anchor)


    def kmeans_lightcones(self, past_params, future_params, decay_type='none',
                            past_decay=0, future_decay=0,
                            past_init_params=None, future_init_params=None):
        '''
        Performs clustering on the global arrays of both past and future lightcones.

        See the daal4py k-means documentation for more details: 
        https://intelpython.github.io/daal4py/algorithms.html#k-means-clustering

        Parameters
        ----------
        past_params: dict,
            Dictionary of keword arguments for past lightcone clustering algorithm.

            If past_cluster == 'kmeans':
                past_params must include values for 'nClusters' and 'maxIterations'
                
        future_params: dict,
            Dictionary of keword arguments for future lightcone clustering algorithm.

            If future_cluster == 'kmeans':
                future_params must include values for 'nClusters' and 'maxIterations'

        past_decay: int, optional (default=0)
            Exponential decay rate for lightcone distance used for past lightcone clustering.

        future_decay: int, optional (default=0)
            Exponential decay rate for lightcone distance used for future lightcone clustering.
        '''
        if self.plcs is None:
            raise RuntimeError("Must call .extract() on a training field(s) before calling .cluster_lightcones().")


        if decay_type not in ['space', 'time', 'spacetime', 'none']:
            raise ValueError("decay_type must be 'none', 'space', 'time', or 'spacetime'")
            
        if decay_type == 'space':
            past_decays = past_spatial_decay(self.past_depth, self.c, past_decay)
            future_decays = future_spatial_decay(self.future_depth, self.c, future_decay)
        elif decay_type == 'time':
            past_decays = past_temporal_decay(self.past_depth, self.c, past_decay)
            future_decays = future_temporal_decay(self.future_depth, self.c, future_decay)
        elif decay_type == 'spacetime':
            past_decays = past_spacetime_decay(self.past_depth, self.c, past_decay)
            future_decays = future_spacetime_decay(self.future_depth, self.c, future_decay)
            
        if decay_type != 'none':
            self.plcs *= np.sqrt(past_decays)
            self.flcs *= np.sqrt(future_decays)
        
        
        self._N_pasts = past_params['nClusters']
        self._N_futures = future_params['nClusters']

        if past_init_params is None: # better way to do this?
            #method = 'randomDense'
            #method = 'parallelPlusDense'
            #method = 'plusPlusDense'
            method = 'defaultDense'
            past_init_params = {'nClusters':self._N_pasts,
                                    #'method':'plusPlusDense',
                                   'method': method,
                                   'distributed': self._distributed}
        initial = d4p.kmeans_init(**past_init_params)
        centroids = initial.compute(self.plcs).centroids
        past_cluster = d4p.kmeans(distributed=self._distributed, **past_params).compute(self.plcs, centroids)
        past_local = d4p.kmeans(nClusters=self._N_pasts, distributed=False, assignFlag=True, maxIterations=0).compute(self.plcs, past_cluster.centroids)
        self.pasts = past_local.assignments.flatten()
     
        del past_cluster 
        del self.plcs 

        if future_init_params is None: # better way to do this?
            #method = 'randomDense'
            #method = 'parallelPlusDense'
            #method = 'plusPlusDense'
            method = 'defaultDense'
            future_init_params = {'nClusters':self._N_futures,
                                  #'method':'plusPlusDense',
                                   'method': method,
                                   'distributed': self._distributed}
        initial = d4p.kmeans_init(**future_init_params)
        centroids = initial.compute(self.flcs).centroids
        future_cluster = d4p.kmeans(distributed=self._distributed, **future_params).compute(self.flcs, centroids)
        future_local = d4p.kmeans(nClusters=self._N_futures, distributed=False, assignFlag=True, maxIterations=0).compute(self.flcs, future_cluster.centroids)
        self.futures = future_local.assignments.flatten()

        del future_cluster
        del self.flcs 


    def reconstruct_morphs(self):
        '''
        Counts lightcone cluster labels to build empirical joint distribution.
        '''
        if self.pasts is None:
            raise RuntimeError("Must call .cluster_lightcones() before calling .reconstruct_morphs()")
        # morphs accessed through this joint distribution over pasts and futures
        self.local_joint_dist = dist_from_data(self.pasts, self.futures, self._N_pasts, self._N_futures)#, row_labels=True)
        if self._distributed:
            self.global_joint_dist = np.zeros((self._N_pasts, self._N_futures), dtype=np.uint64)

        del self.futures


    def reconstruct_states(self, metric, *metric_args, pval_threshold=0.05, **metric_kwargs):
        '''
        Hierarchical agglomerative clustering of lightcone morphs
        from a given joint distribution array (joint over lightcone clusters),
        where the first column is the labels for the plc clusters (pasts).
        This is needed because a random permutation should be done before
        clustering.

        Any noise clusters are ignored. If there is a noise cluster for pasts,
        it is assigned to the NAN state. If there is a noise cluster for futures,
        the counts of this cluster are removed from the morphs of each past.

        Parameters
        ----------
        metric: function
            Python function that does a stastical comparison of two empirical distributions.
            In the current use, this function is expected to return a p value for this
            comparison.

        pval_threshold: float, optional (default=0.05)
            p value threshold for the distribution comparison. If the comparison p
            value is greater than pval_threshold, the two distributions are considered
            equivalent.

        '''
       
        # create past labels to keep track of after random permutation
        rlabels = np.arange(0, self._N_pasts, dtype=np.uint64)[np.newaxis] 
        # self.global_joint_dist = np.hstack((rlabels.T, self.global_joint_dist))
        # morphs = self.global_joint_dist
        if self._distributed:
            morphs = np.hstack((rlabels.T, self.global_joint_dist))
        else:
            morphs = np.hstack((rlabels.T, self.local_joint_dist))

        self.label_map = np.zeros(self._N_pasts, dtype=int) # for vectorized causal_filter

        # hierarchical agglomerative clustering -- clusters pasts into local causal states
        for item in morphs:
            past = item[0]
            morph = item[1:]
            for state in self.states:
                p_value = metric(morph, state.morph, *metric_args, **metric_kwargs)
                if p_value > pval_threshold:
                    state.update(past, morph)
                    self.epsilon_map.update({past : state})
                    self.label_map[past] = state.index
                    break

            else:
                new_state = CausalState(self._state_index, past, morph)
                self.states.append(new_state)
                self._state_index += 1
                self.epsilon_map.update({past : new_state})
                self.label_map[past] = new_state.index

        del self.joint_dist

    def causal_filter(self):
        '''
        Performs causal filtering on target field (input for Reconstructor.extract())
        and creats associated local causal state field (Reconstructor.state_field)

        The margins, spacetime points that don't have a full past or future lightcone,
        are assigned the NAN state with integer label 0.
        '''
        # OPT: comment out for peformance runs
        if len(self.states) == 0:
            raise RuntimeError("Must call .reconstruct_states() first.")

        past_field = self.pasts.reshape(*self._adjusted_shape)
        self.state_field = np.zeros(self._adjusted_shape, dtype=int)

        # use label_map to map past_field to field of local causal state labels
        self.state_field = self.label_map[past_field]

        # Go back and re-pad state field with margin so it is the same shape as the original data
        if self._bc == 'open':
            spatial_pad = self._padding
        elif self._bc == 'periodic':
            spatial_pad = 0

        margin_padding = (
                            (0, 0), # don't re-pad temporal margin; taken care of w/ haloing
                            (spatial_pad, spatial_pad),
                            (spatial_pad, spatial_pad)
                        )
        self.state_field = np.pad(self.state_field, margin_padding, 'constant')
