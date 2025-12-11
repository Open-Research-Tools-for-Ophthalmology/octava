import numpy as np
from scipy.ndimage import uniform_filter
from skimage.util import invert
from skimage import img_as_float

def adaptive_thresholding(X:np.ndarray, w:int) -> np.ndarray:
    """
    Adaptive thresholding closely replicating MATLAB's method using:
    - Local mean subtraction
    - Zero threshold
    - Image inversion

    Parameters:
        X (ndarray): Input grayscale image (float or uint8)
        w (int): Window size for local averaging

    Returns:
        ndarray: Binary image (bool), foreground as True
    """
    # Normalize to [0, 1] like mat2gray
    X = img_as_float(X)

    # Apply local averaging (replicates MATLAB's fspecial('average', w))
    local_mean = uniform_filter(X, size=w, mode='nearest')

    # Subtract mean from original image
    diff = local_mean - X

    # Threshold at 0: positive → foreground
    Y = diff > 0

    # Invert so that vessels/objects are white (True), background is black
    Y = invert(Y)

    return Y
