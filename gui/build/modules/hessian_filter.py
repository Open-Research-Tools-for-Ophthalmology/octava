import numpy as np
from scipy.ndimage import correlate

def hessian_filter(I: np.ndarray, sigma: float = 1) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Compute the second‑order derivatives (Hessian) of an image using correlation
    with zero padding to match MATLAB’s imfilter behavior (which rotates the
    filter for convolution on symmetric kernels).

    Parameters
    ----------
    I : np.ndarray
        2D grayscale image.
    sigma : float
        Standard deviation of the Gaussian.

    Returns
    -------
    Dxx, Dxy, Dyy : np.ndarray
        Second‑order derivative components of the Hessian.
    """
    size = int(np.round(3 * sigma))
    # Use indexing='ij' so that X(i,j)=x_i and Y(i,j)=y_j, matching MATLAB’s ndgrid.
    x = np.arange(-size, size + 1)
    y = np.arange(-size, size + 1)
    X, Y = np.meshgrid(x, y, indexing='ij')

    normalization = 1 / (2 * np.pi * sigma**4)
    DGaussxx = normalization * ((X**2 / sigma**2) - 1) * np.exp(-(X**2 + Y**2) / (2 * sigma**2))
    DGaussxy = (1 / (2 * np.pi * sigma**6)) * (X * Y) * np.exp(-(X**2 + Y**2) / (2 * sigma**2))
    # Define DGaussyy explicitly using Y**2 so it matches MATLAB's DGaussxx' logic.
    DGaussyy = normalization * ((Y**2 / sigma**2) - 1) * np.exp(-(X**2 + Y**2) / (2 * sigma**2))

    # Correlate with zero padding (mode='constant', cval=0) to emulate MATLAB's imfilter(...,'conv')
    Dxx = correlate(I, DGaussxx, mode='constant', cval=0.0)
    Dxy = correlate(I, DGaussxy, mode='constant', cval=0.0)
    Dyy = correlate(I, DGaussyy, mode='constant', cval=0.0)

    return Dxx, Dxy, Dyy