import os
import numpy as np
import cv2 as cv
from skimage.io import imread
from skimage.filters import frangi
import matplotlib.pyplot as plt
from skimage.morphology import skeletonize, remove_small_objects
from scipy.ndimage import distance_transform_edt

from Skel2Graph3D import skel2graph3d
from Graph2Skel3D import graph2skel3d

# libraries to test
import sys
sys.path.append("/home/mutrera/OCTAVA/octava/code/")
from frangi_2dfilter import frangi_2Dfilter
from fuzzy_thresholding import fuzzy_thresholding
from adaptive_thresholding import adaptive_thresholding


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

def center_crop(img, dim):
    """
    Center crop an image (2D NumPy array).

    Parameters:
        img (np.ndarray): Input image (H x W).
        dim (tuple): Desired output size (h, w).

    Returns:
        np.ndarray: Cropped image of size (h, w).
    """
    h, w = img.shape[:2]
    new_h, new_w = dim

    if new_h > h or new_w > w:
        raise ValueError("Crop size must be smaller than the image size")

    top = (h - new_h) // 2
    left = (w - new_w) // 2

    return img[top: top + new_h, left: left + new_w]

def skeletonize_py(input_img, binary_img, twig_size):
    # generate skeletonized image
    h, w = input_img.shape
    boolean_binarized = binary_img.astype(bool)
    sk2 = skeletonize(boolean_binarized, method = "zhang") # meant for 2D

    # remove branches smaller than twig_size
    sk2 = remove_small_objects(sk2, min_size=twig_size)

    # local thickness measurement
    D = distance_transform_edt(sk2) * 2

    # network analysis
    if sum(sum(sk2)) == 0:
        nodes = []
        links = []
    else:
        _, nodes, links = skel2graph3d(np.expand_dims(sk2, axis=-1), twig_size)

        # # calculate the total length of the network
        # wl = sum(len(node['links']) for node in nodes)

        # # iterate to clean up network and get rid of excess nodes
        # skel2 = graph2skel3d(nodes, links, h, w, 1)

        # _, nodes, links = skel2graph3d(skel2, 0)
        # wl_new = sum(len(node['links']) for node in nodes)

        # num_iters = 1

        # while(wl_new != wl):
        #     print(f"This is iteration number {num_iters}")
        #     wl = wl_new
            
        #     skel2 = graph2skel3d(nodes, links, h, w, 1)
        #     _, nodes, links = skel2graph3d(skel2, 0)

        #     wl_new = sum(len(node['links']) for node in nodes)
        #     num_iters += 1
        
    return nodes, links





if __name__ == "__main__":
    # Load image
    octa_path = "/home/mutrera/OCTAVA/octava/assets/MIPs/10301.bmp"
    img = imread(octa_path, as_gray=True).astype(np.float32)

    # Frangi vessel enhancement
    vessels = frangi(
        img,
        scale_range=(0.5, 4),
        scale_step=0.5,
        alpha=0.5,
        beta=0.5,
        gamma=4,
        black_ridges=False
    )

    # Binarize
    adpt_mask = BinarizeImage(vessels, frangi_sigma=8, frangi_enabled=False,
                              method="Adaptive Thresholding")

    # Crop
    adpt_mask_cropped = center_crop(adpt_mask, dim=(200, 200))

    # Skeletonize
    nodes, links = skeletonize_py(img, adpt_mask, twig_size=0)