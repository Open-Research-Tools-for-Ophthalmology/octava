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
    Exact Python translation of frangi_2Dfilter.m.
    """
    # Generate sigmas inclusive of the upper bound, like MATLAB's a:b:c
    sigmas = np.arange(opts['sigmarange'][0],
                       opts['sigmarange'][1] + 1,
                       opts['sigmastepsize'])
    sigmas = np.sort(sigmas)

    beta = 2.0 * (opts['correctionconst1'] ** 2)
    c    = 2.0 * (opts['correctionconst2'] ** 2)

    h, w = X.shape
    filtX_persigma = np.zeros((h, w, len(sigmas)))
    angles_persigma = np.zeros((h, w, len(sigmas)))

    for i, sigma in enumerate(sigmas):
        # 1. Hessian derivatives
        Dxx, Dxy, Dyy = hessian_filter(X, sigma)

        # 2. Normalize by sigma^2
        var = sigma**2
        Dxx *= var
        Dxy *= var
        Dyy *= var

        # 3. Eigen decomposition
        # eig2im returns (Xdir, Ydir, m2, m1) where m2=major, m1=minor
        Xi, Yi, m_major, m_minor = eig2im(Dxx, Dxy, Dyy)

        # Swap names to match MATLAB's usage: m1=major, m2=minor
        m1 = m_major
        m2 = m_minor

        # 4. Direction of the minor eigenvector (stored but unused)
        angles = np.arctan2(Xi, Yi)

        # 5. Vesselness measure
        m1[m1 == 0] = np.finfo(np.float64).eps
        mratio = (m2 / m1)**2  # minor / major as in MATLAB

        Xfiltered = np.exp(-mratio / beta) * (1.0 - np.exp(-(m1**2 + m2**2) / c))

        # Suppress bright ridges: zero response where major eigenvalue > 0
        Xfiltered[m1 > 0] = 0.0

        filtX_persigma[:, :, i] = Xfiltered
        angles_persigma[:, :, i] = angles

    Y = np.max(filtX_persigma, axis=2)
    return Y

# Adapted from:
# https://github.com/timjerman/JermanEnhancementFilter/blob/master/vesselness2D.m
# https://github.com/mcgarrysd/vessel_metrics/blob/main/final_scripts/vessel_metrics.py
# https://github.com/scikit-image/scikit-image/pull/8074/changes#diff-c4d9acd2360fa044a07e7b15990290c46ede15951b42a712e301bb0a53a20097
# Only difference is we use self-contained hessian_filter functions
def jerman(
    im,
    sigmas: np.ndarray = np.arange(1, 6, 1), # by default 1:5
    tau=0.75,
    brightondark=True,
):
    im = np.asarray(im, dtype=np.float64)
    vesselness = np.zeros_like(im, dtype=np.float64)

    for i, sigma in enumerate(sigmas):
        # 1. Hessian derivatives
        Dxx, Dxy, Dyy = hessian_filter(im, sigma)

        # 2. Normalize by sigma^2
        var = sigma ** 2
        Dxx *= var
        Dxy *= var
        Dyy *= var

        # reduce computation by computing vesselness only where needed
        # S.-F. Yang and C.-H. Cheng, “Fast computation of Hessian-based
        # enhancement filters for medical images,” Comput. Meth. Prog. Bio., vol.
        # 116, no. 3, pp. 215–225, 2014.
        # Trace = B1, Det(erminant) = B2 (line 84 / vesselness2D)
        trace = Dxx + Dyy
        det = Dxx * Dyy - Dxy ** 2
        degenerate = (trace == 0) & (det == 0)
        # Mask = indeces = find(T==1) = ~T
        if brightondark:
            mask = (trace <= 0) & ~degenerate
        else:
            mask = (trace >= 0) & ~degenerate

        # m_major, m_minor = Lambda1i,Lambda2i (line 114 / vesselness2D)
        # TODO check if we need to Dxx = Dxx(mask) to match vesselness2D? (line 105 / vesselness2D) or is this just for efficiency?
        _, _, m_major, m_minor = eig2im(Dxx, Dxy, Dyy)
        m_major = np.where(mask, m_major, 0)
        m_minor = np.where(mask, m_minor, 0)

        # some noise removal (line 120 / vesselness2D)
        m_major[np.abs(m_major) < 1e-4] = 0
        m_minor[np.abs(m_minor) < 1e-4] = 0

        # Negate at brightondark to make lambda positive values, Line 43 / vesselness2D
        Lambda2 = -m_major if brightondark else m_major

        # 2D adaptation: Lambda3 = Lambda2, only two eigenvalues exist in 2D; (line 47 / vesselness2D)
        Lambda3 = Lambda2.copy()

        # Lambda_rho regularisation (line 50 / vesselness2D).
        Lambda_rho = Lambda3.copy()
        Lambda3_max = float(np.max(Lambda3))
        low_indeces = (Lambda3 > 0) & (Lambda3 <= tau * Lambda3_max)
        Lambda_rho[low_indeces] = tau * Lambda3_max
        Lambda_rho[Lambda3 <= 0] = 0

        # Vesselness response (line 53 / vesselness2D).
        with np.errstate(invalid='ignore', divide='ignore'): # NaN case handled in normalisation step
            response = (Lambda2 ** 2 * (Lambda_rho - Lambda2) * 27 / ((Lambda2 + Lambda_rho) ** 3))

        # 0,1 Normlisation (line 55 / vesselness2D).
        response[(Lambda2 >= Lambda_rho / 2) & (Lambda_rho > 0)] = 1
        response[(Lambda2 <= 0) | (Lambda_rho <= 0)] = 0
        response[~np.isfinite(response)] = 0

        # max response over multiple scales (line 59 / vesselness2D).
        if sigma == 1:
            vesselness = response
        else:
            vesselness = np.maximum(vesselness, response)

    # should not be really needed as already normlised, but keep consistent as (line 69 / vesselness2D)... 
    vesselness = vesselness / float(np.max(vesselness))
    vesselness[vesselness < 1e-2] = 0

    return vesselness