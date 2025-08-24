from typing import Any
import numpy as np
from skimage.measure import label

from pk_functions import pk_get_nh

def skel2graph3d(skel: np.ndarray, THR: int) -> tuple[Any, Any, Any]:
    ''' 
    Given a 3D voxel skeleton, creates a the vessel network graph with the nodes 
    and links of the branches in the skeletonized image. Prunes the network so 
    that branches shorter than THR are not considered in the network

    Inputs:
        - skel: skeletonized image
        - THR: minimum branch size 
    
    Returns: a tuple with the following values:
        - Adjacency matrix
        - list of node structures
        - list of link structures

    Philip Kollmannsberger (philipk@gmx.net)

    For more information, see <a
    href="matlab:web('http://uk.mathworks.com/matlabcentral/fileexchange/43527-skel2graph-3d')">Skel2Graph3D</a> at the MATLAB File Exchange.
    '''
    # pad volume with zeros
    skel = np.pad(skel, pad_width=1, mode = 'constant', constant_values=0)

    # create label matrix for different skeletons
    labeled_matrix = label(skel, connectivity=3)

    # image dimensions
    h, w, l = skel.shape

    # need this for labeling nodes etc.
    skel2 = skel.astype(np.uint16)

    # all foreground voxels
    list_canal = np.flatnonzero(skel) # flat list of foreground indices 

    nh = pk_get_nh(skel, list_canal).astype(np.bool)