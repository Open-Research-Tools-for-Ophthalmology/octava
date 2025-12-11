from hessian2d import hessian_filter
import numpy as np

def eig2im(Dxx:np.ndarray, Dxy:np.ndarray, Dyy:np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Compute the eigenvalues and eigenvectors of the Hessian matrix at each pixel.

    Parameters:
    - Dxx: Second-order derivative in the x direction
    - Dxy: Second-order mixed derivative
    - Dyy: Second-order derivative in the y direction

    Returns:
    - X: x-component of the dominant eigenvector
    - Y: y-component of the dominant eigenvector
    - m2: Eigenvalue of the dominant direction (larger absolute value)
    - m1: Eigenvalue of the orthogonal direction (smaller absolute value)
    """
    tmp = np.sqrt((Dxx - Dyy)**2 + 4 * Dxy**2)

    eig1 = 0.5 * (Dxx + Dyy + tmp)
    eig2 = 0.5 * (Dxx + Dyy - tmp)

    aeig1 = np.abs(eig1)
    aeig2 = np.abs(eig2)

    m1 = np.where(aeig1 > aeig2, eig2, eig1)
    m2 = np.where(aeig1 > aeig2, eig1, eig2)

    v2x = 2 * Dxy
    v2y = Dyy - Dxx + tmp

    norm = np.sqrt(v2x**2 + v2y**2)
    v2x[norm != 0] /= norm[norm != 0]
    v2y[norm != 0] /= norm[norm != 0]

    v1x = -v2y
    v1y = v2x

    X = np.where(aeig1 > aeig2, v2x, v1x)
    Y = np.where(aeig1 > aeig2, v2y, v1y)

    return X, Y, m2, m1


def frangi_2Dfilter(X:np.ndarray, opts:dict) -> np.ndarray:
    """
    Apply Frangi vesselness filter to a 2D grayscale image across multiple scales.

    This function enhances tubular or vessel-like structures in the input image
    by computing the Hessian matrix at multiple Gaussian scales and evaluating
    a vesselness measure based on eigenvalue analysis.

    Parameters:
    - X (np.ndarray): 2D grayscale input image
    - opts (dict): Dictionary of options with keys:
        - 'sigmarange': tuple(float, float), range of sigma values
        - 'sigmastepsize': float, step size for sigma
        - 'correctionconst1': float, Frangi filter parameter (beta)
        - 'correctionconst2': float, Frangi filter parameter (c)

    Returns:
    - Y (np.ndarray): 2D image with vesselness response (same shape as X)
    """
    # Generate array of sigma values (scales) for multi-scale filtering
    sigmas = np.arange(opts['sigmarange'][0],
                       opts['sigmarange'][1] + opts['sigmastepsize'],
                       opts['sigmastepsize'])
    sigmas = np.sort(sigmas) # Ensure ascending order

    # Constants used in the Frangi vesselness formula
    beta = 2 * opts['correctionconst1'] ** 2
    c = 2 * opts['correctionconst2'] ** 2

    # Preallocate arrays to store results for each scale
    h, w = X.shape
    filtX_persigma = np.zeros((h, w, len(sigmas)))
    angles_persigma = np.zeros((h, w, len(sigmas)))

    # Process image at each scale
    for i, sigma in enumerate(sigmas):
        # Compute second-order derivatives of image at current scale
        Dxx, Dxy, Dyy = hessian_filter(X, sigma)
        # Normalize derivative responses by sigma^2 (scale-space theory)
        var= sigma**2
        Dxx *= var
        Dxy *= var
        Dyy *= var

        # Compute eigenvalues and eigenvectors of the Hessian matrix
        Xi, Yi, m2, m1 = eig2im(Dxx, Dxy, Dyy)

        # Calculate vessel orientation (angle of minor eigenvector)
        angles = np.arctan2(Xi, Yi)

        # Avoid division by zero in later steps
        m1[m1 == 0] = np.finfo(np.float64).eps # set the 0s to a small value
        mratio = (m2 / m1)**2

        # Compute the output image
        Xfiltered = np.exp(-mratio / beta) * (1 - np.exp(-(m1**2 + m2**2) / c))
        Xfiltered[m1 > 0] = 0
        filtX_persigma[:, :, i] = Xfiltered
        angles_persigma[:, :, i] = angles

    Y = np.max(filtX_persigma, axis=2)
    return Y


def main():
    # Testing:
    from skimage import io, img_as_float
    import matplotlib.pyplot as plt

    image = img_as_float(io.imread("/Users/milameteor/Library/CloudStorage/OneDrive-UWA/M4 Backup/LEI/to_be_rename/MILA_renamed/test/5000.tif", as_gray=True))

    opts = {
        'sigmarange': (1, 3),
        'sigmastepsize': 1,
        'correctionconst1': 0.8,
        'correctionconst2': 15
    }

    vessel_image = frangi_2Dfilter(image, opts)

    plt.imshow(vessel_image, cmap='gray')
    plt.title("Frangi Vesselness")
    plt.axis('off')
    plt.show()

if __name__ == "__main__":
    main()