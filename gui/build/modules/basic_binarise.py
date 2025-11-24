# This was created for testing purposes only.

import numpy as np
from scipy.ndimage import median_filter
from fuzzy_thresholding import *
from frangi_2Dfilter import *
from PIL import Image, ImageTk

def basic_binarise(X: np.ndarray) -> np.ndarray:
    """
    Perform basic binarisation identical to the MATLAB basic_binarise.m.

    Steps:
    1. Find the brightest pixel in the whole image (row rr, column cc).
    2. Run the Frangi vesselness filter with the same options.
    3. Apply fuzzy thresholding with two clusters and window size 3.
    4. Convert the chosen cluster (label at rr,cc) to 255 and the others to 0.

    Parameters
    ----------
    X : 2D NumPy array of dtype float
        The input grayscale image.

    Returns
    -------
    np.ndarray
        A binarised image of dtype uint8 with values 0 or 255.
    """
    # 1. Locate the brightest pixel (global maximum) in X
    # y contains the maximum of each column
    y = X.max(axis=0)
    cc = int(y.argmax())         # column index of global max
    rr = int(X[:, cc].argmax())  # row index of that max

    ksize = 3  # assuming scalar
    X = median_filter(X, size=(ksize, ksize),
                                    mode='constant', cval=0.0)

    # 2. Apply the Frangi filter (using the same options)
    opts = {
        'sigmarange': (1, 4),     # matches [1 4] in MATLAB
        'sigmastepsize': 2,       # step size 2 -> {1, 3}
        'correctionconst1': 0.8,
        'correctionconst2': 15
    }
    vesselness = frangi_2Dfilter(X, opts)

    # 3. Fuzzy thresholding with two clusters, window size 3, then subtract 1
    nth = 2
    labels = fuzzy_thresholding(vesselness, nth, 3) - 1

    # 4. Convert to binary mask: label matching (rr, cc) → 255, others → 0
    ref_value = labels[rr, cc]
    binary = np.where(labels == ref_value, 255, 0).astype(np.uint8)

    return binary