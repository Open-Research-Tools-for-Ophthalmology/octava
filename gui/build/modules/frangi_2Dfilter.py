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



def eig2im(Dxx: np.ndarray, Dxy: np.ndarray, Dyy: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Compute eigenvalues and eigenvectors of the 2D Hessian matrix at each pixel.

    Parameters
    ----------
    Dxx, Dxy, Dyy : np.ndarray
        Second‑order derivatives of the image.

    Returns
    -------
    X, Y : np.ndarray
        Components of the eigenvector associated with the major eigenvalue.
    m2, m1 : np.ndarray
        Eigenvalues sorted by magnitude (m2 = major, m1 = minor).
    """
    tmp = np.sqrt((Dxx - Dyy)**2 + 4 * Dxy**2)

    eig1 = 0.5 * (Dxx + Dyy + tmp)
    eig2 = 0.5 * (Dxx + Dyy - tmp)

    aeig1 = np.abs(eig1)
    aeig2 = np.abs(eig2)

    # m1: minor eigenvalue, m2: major eigenvalue by absolute value
    m1 = np.where(aeig1 > aeig2, eig2, eig1)
    m2 = np.where(aeig1 > aeig2, eig1, eig2)

    # v2 is the eigenvector corresponding to m2 (dominant direction)
    v2x = 2 * Dxy
    v2y = Dyy - Dxx + tmp

    norm = np.sqrt(v2x**2 + v2y**2)
    # Avoid division by zero by setting zeros to 1 before division
    norm[norm == 0] = 1
    v2x /= norm
    v2y /= norm

    v1x = -v2y
    v1y = v2x

    # Choose v2 or v1 based on which eigenvalue is larger in magnitude
    X = np.where(aeig1 > aeig2, v2x, v1x)
    Y = np.where(aeig1 > aeig2, v2y, v1y)

    return X, Y, m2, m1


def frangi_2Dfilter(X: np.ndarray, opts: dict) -> np.ndarray:
    """
    Apply the Frangi vesselness filter to a 2D grayscale image across multiple scales.
    This version mirrors the MATLAB implementation of frangi_2Dfilter.m exactly.

    Parameters
    ----------
    X : np.ndarray
        2D grayscale input image (float64).
    opts : dict
        Parameters:
        - 'sigmarange': (start, end) inclusive
        - 'sigmastepsize': step size for sigma
        - 'correctionconst1': float (beta parameter)
        - 'correctionconst2': float (c parameter)

    Returns
    -------
    np.ndarray
        Vesselness response image with the same shape as X.
    """
    # Generate sigma values exactly as in MATLAB: opts.sigmarange(1):opts.sigmastepsize:opts.sigmarange(2)
    sigmas = np.arange(opts['sigmarange'][0],
                       opts['sigmarange'][1] + opts['sigmastepsize'],
                       opts['sigmastepsize'])
    sigmas = np.sort(sigmas)

    # Precompute constants
    beta = 2.0 * (opts['correctionconst1'] ** 2)
    c    = 2.0 * (opts['correctionconst2'] ** 2)

    h, w = X.shape
    filtX_persigma = np.zeros((h, w, len(sigmas)))
    angles_persigma = np.zeros((h, w, len(sigmas)))

    # Loop over each sigma
    for i, sigma in enumerate(sigmas):
        # 1. Compute Hessian derivatives
        Dxx, Dxy, Dyy = hessian_filter(X, sigma)

        # 2. Scale-space normalization by sigma^2
        var = sigma**2
        Dxx *= var
        Dxy *= var
        Dyy *= var

        # 3. Compute eigenvalues and eigenvectors of the Hessian
        Xi, Yi, m2, m1 = eig2im(Dxx, Dxy, Dyy)

        # 4. Angle of the minor eigenvector (for completeness; not used in final result)
        angles = np.arctan2(Xi, Yi)

        # 5. Compute vesselness measure
        #    Guard against division by zero
        m1[m1 == 0] = np.finfo(np.float64).eps
        mratio = (m2 / m1)**2

        #    Vesselness formula: exp( -mratio/beta ) * (1 - exp( -(m1**2 + m2**2)/c ))
        Xfiltered = np.exp(-mratio / beta) * (1.0 - np.exp(-(m1**2 + m2**2) / c))

        #    Suppress responses where the minor eigenvalue is positive (bright ridges)
        Xfiltered[m1 > 0] = 0.0

        # 6. Store results
        filtX_persigma[:, :, i] = Xfiltered
        angles_persigma[:, :, i] = angles

    # 7. Take maximum response across scales (same size as X)
    Y = np.max(filtX_persigma, axis=2)
    return Y