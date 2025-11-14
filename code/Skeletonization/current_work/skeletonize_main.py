import numpy as np
from skimage.io import imread
from skimage.filters import frangi
import matplotlib.pyplot as plt
from skimage.morphology import skeletonize, remove_small_objects
from scipy.ndimage import distance_transform_edt
from Skel2Graph3D import skel2graph3d
from Graph2Skel3D import graph2skel3d

import sys
sys.path.append("/Users/mutrera/Documents/Uchicago College/Uchicago 2024 - 2025/Summer/Octava/octava/code")
from frangi_2dfilter import frangi_2Dfilter
from fuzzy_thresholding import fuzzy_thresholding
from adaptive_thresholding import adaptive_thresholding




# HELPERS 

def BinarizeImage(Im:np.ndarray, frangi_sigma = 8, frangi_enabled = True, method = "Fuzzy Means") -> np.ndarray:
    """
    Binarizes an image using the selected method and options from the GUI app.

    Parameters:
    - app: GUI application object containing UI state (e.g., checkboxes, dropdowns)
    - Im: Input image as a 2D NumPy array (grayscale)

    Returns:
    - Binarized image as a 2D NumPy array (dtype=float)
    """
    # Find the brightest pixel in the image
    col_max_vals = np.max(Im, axis=0) # the maximum of each column
    cc = np.argmax(col_max_vals) #  gets the index of the column where the brightest value occurred
    rr = np.argmax(Im[:, cc]) # captures the row index of that max value

    #	•	rr: row of the brightest pixel
	#   •	cc: column of the brightest pixel
    #   •	So (rr, cc) is the coordinate of the brightest pixel in the whole image.

    # Apply Frangi filter if selected
    if frangi_enabled:
        opts = {
            'sigmarange': [1, frangi_sigma],
            'sigmastepsize': 2,
            'correctionconst1': 0.8,
            'correctionconst2': 15
        }
        Im = frangi_2Dfilter(Im, opts)

    # Apply the selected binarization method
    if method == 'Fuzzy Means':
        nth = 2
        Im = fuzzy_thresholding(Im, nth, 3) - 1

    elif method == 'Adaptive Thresholding':
        Im = adaptive_thresholding(Im, 70).astype(float)

    else:
        raise ValueError("Incorrect Segmentation Method")

    # Ensure vessels are white, background is black, turning the image into black and white
    vessel_value = Im[rr, cc]
    Im[Im == vessel_value] = 255
    Im[Im != 255] = 0

    return Im



def skeletonize_main(bin: np.ndarray, THR: int = 0):
    # generate skeletonized iamge
    y, x = bin.shape
    L = bin.astype(bool)
    sk2 = skeletonize(L)

    # removes branches smaller than twig size
    sk2 = remove_small_objects(sk2, THR)

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

    return nodes, links


if __name__ == "__main__":
    octa = imread("/Users/mutrera/Documents/Uchicago College/Uchicago 2024 - 2025/Summer/Octava/octava/assets/MIPs/10301.bmp")

    # Frangi vessel enhancement
    start_bin = time.time()
    vessels = frangi(
        octa,
        scale_range=(0.5, 4),
        scale_step=0.5,
        alpha=0.5,
        beta=0.5,
        gamma=4,
        black_ridges=False
    )

    adpt_mask = BinarizeImage(
        vessels,
        frangi_sigma=8,
        frangi_enabled=False,
        method="Adaptive Thresholding"
    )
    end_bin = time.time()

    start_skel = time.time()
    nodes, links = skeletonize_main(adpt_mask, 1)
    end_skel = time.time()

    print("Num nodes:", len(nodes))
    print("Num links:", len(links))
    print("Time for binarization:", end_bin - start_bin)
    print("Time for skeletonization:", end_skel - start_skel)