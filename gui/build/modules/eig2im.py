import numpy as np

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