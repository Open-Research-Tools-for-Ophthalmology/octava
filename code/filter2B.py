from im_expand import im_expand
from scipy.signal import correlate2d
import numpy as np

def filter2B(h:np.ndarray, I:np.ndarray)->np.ndarray:
    """
    Two-dimensional digital filter, similar to MATLAB's FILTER2B.
    
    Filters image I with a 2D FIR filter h using correlation,
    and uses symmetric padding to avoid edge artifacts.

    Parameters:
    ----------
    h : np.ndarray
        2D FIR filter kernel (must have odd dimensions).
    I : np.ndarray
        Input 2D image.

    Returns:
    -------
    np.ndarray
        Filtered image with the same size as I.
    """
    (Mx, My) = h.shape
    if Mx%2 == 0 or My%2 == 0:
        raise ValueError("Filter kernel must have odd dimensions.")

    Nx= Mx // 2
    Ny= My//2

    I_expanded = im_expand(I,Nx,Ny)
    I2=correlate2d(I_expanded, h,mode='valid')
    return I2
