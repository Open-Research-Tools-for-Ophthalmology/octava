import numpy as np
from skimage.io import imread
from skimage.filters import frangi
import matplotlib.pyplot as plt
from skimage.morphology import skeletonize, remove_small_objects
from scipy.ndimage import distance_transform_edt
from Skel2Graph3D import skel2graph3d
from Graph2Skel3D import graph2skel3d
import scipy.io as sio
import time

import numpy as np
import matplotlib.pyplot as plt
# from bwmorph import *
from skimage.morphology import medial_axis

# def bwskel_prune_exact(skel, min_len):
#     if min_len <= 0:
#         return skel

#     vol = skel.astype(bool)[..., np.newaxis]  # convert to 3D with depth 1
#     nodes, links = skel2graph3d(vol, min_len)

#     H, W = skel.shape
#     vol2 = graph2skel3d(nodes, links, H, W, 1)

#     return vol2[..., 0].astype(bool)

# def skeletonize_main(bin: np.ndarray, THR: int = 0):
#     y, x = bin.shape
#     L = bin.astype(bool)

#     # === 1) EXACT MATLAB bwmorph(L,'skel',Inf) ===
#     sk2 = bwmorph_skeleton(L)

#     # === 2) EXACT MATLAB bwskel(...,'MinBranchLength',THR) ===
#     sk2 = bwskel_prune_exact(sk2, THR)

#     # === 3) EXACT MATLAB local thickness ===
#     D = distance_transform_edt(~L) * 2      # IMPORTANT: distance to background!!

#     # === Network analysis (same as your original) ===
#     if np.sum(sk2) == 0:
#         nodes = []
#         links = []
#     else:
#         nodes, links = skel2graph3d(sk2, THR)

#     wl = sum(len(n.links) for n in nodes)

#     skel2 = graph2skel3d(nodes, links, y, x, 1)
#     nodes, links = skel2graph3d(skel2, 0)
#     wl_new = sum(len(n.links) for n in nodes)

#     while wl_new != wl:
#         wl = wl_new
#         skel2 = graph2skel3d(nodes, links, y, x, 1)
#         nodes, links = skel2graph3d(skel2, 0)
#         wl_new = sum(len(n.links) for n in nodes)

#     return skel2, nodes, links


def bwmorph(bin: np.ndarray):
    # generate skeletonized iamge
    y, x = bin.shape
    L = bin.astype(bool)

    skel, distance = medial_axis(L, return_distance=True)
    # # sk2 = skeletonize(L) 

    return skel



def skeletonize_main(bin: np.ndarray, THR: int = 0):
    # generate skeletonized iamge
    y, x = bin.shape
    L = bin.astype(bool)
    # sk2 = skeletonize(L) 
    sk2 = skeletonize(L) 

    # removes branches smaller than twig size
    # sk2 = remove_small_objects(sk2, THR, connectivity=8) 

    # local thickness measurement
    D = distance_transform_edt(L) * 2
    # D is the closest I can get to the local thickness map so far, so
    # saving as such. Factor of 2 since distance transform gives radius

    # network analysis
    # based on code written by Philip Kollmannsberger
    if np.sum(sk2) == 0:
        nodes = []
        links = []

    else:
        start_skel2graph = time.time()
        nodes, links = skel2graph3d(sk2, THR)
        end_skel2graph = time.time()
    
    print("Time for skel2graph:", end_skel2graph - start_skel2graph)

    # calculate total length of network
    wl = sum([len(n.links) for n in nodes])

    # iterate to clean up network and get rid of excess nodes
    start_graph2skel = time.time()
    skel2 = graph2skel3d(nodes, links, y, x, 1)  
    end_graph2skel = time.time()

    nodes, links = skel2graph3d(skel2, 0) # passing 304x304x1
    wl_new = sum([len(n.links) for n in nodes])

    print("Time for graph2skel:", end_graph2skel - start_graph2skel)

    # iterate the same steps until network length changed by less than 0.5%
    start_loop = time.time()
    while (wl_new != wl):
        wl = wl_new

        skel2 = graph2skel3d(nodes, links, y, x, 1)
        nodes, links = skel2graph3d(skel2, 0)

        wl_new = sum([len(n.links) for n in nodes])

    end_loop = time.time()

    print("Time in cleaning loop:", end_loop - start_loop)

    return skel2, nodes, links


if __name__ == "__main__":
    data = sio.loadmat("/Users/mutrera/Documents/Uchicago College/Uchicago 2024 - 2025/Summer/Octava/octava/code/Skeletonization/matlab_skels/binarise_python_result.mat")
    python_bin_img = data['Y_py']

    start_skel = time.time()
    THR = 1
    skel, nodes, links = skeletonize_main(python_bin_img, THR)
    end_skel = time.time()

    print("Num nodes:", len(nodes))
    print("Num links:", len(links))
    print("Dimensions of skel2:", skel.shape)
    print("Time for skeletonization:", end_skel - start_skel)