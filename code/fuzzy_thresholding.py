import numpy as np
from scipy.ndimage import median_filter, convolve
from skfuzzy.cluster import cmeans


def fuzzy_thresholding(X, nth, w):
    X = X.astype(np.float64)

    # Normalize the image using mean ± 2*std range
    sigmaX = np.std(X)
    muX = np.mean(X)
    mask = (X > (muX - 2 * sigmaX)) & (X < (muX + 2 * sigmaX))
    norma = np.max(X[mask])
    X = X / norma

    # Apply Gaussian smoothing
    h = gaussian_kernel(11, 1.5)
    gX = smooth_function(h, X)

    # Fuzzy C-means clustering
    data = gX.flatten()[np.newaxis, :]
    cntr, u, _, _, _, _, _ = cmeans(data, nth, 2, error=1e-5, maxiter=100)
    Xfcm = np.sort(cntr.flatten())

    max_gX = np.max(gX)
    min_gX = np.min(gX)

    Xtrap3 = np.zeros((X.shape[0], X.shape[1], nth))

    for imax in range(nth):
        if imax == 0: # first cluster
            a1 = a2 = min_gX
            a3 = Xfcm[0]
            a4 = Xfcm[1]
        elif imax == nth - 1: # last cluster
            a1 = Xfcm[-2]
            a2 = a3 = a4 = max_gX
        else:
            a1 = Xfcm[imax - 1]
            a2 = a3 = Xfcm[imax]
            a4 = Xfcm[imax + 1]

        Xtrap = trapezoid_fuzzy_membership(X, a1, a2, a3, a4)
        Xtrap3[:, :, imax] = Xtrap

    medXtrap3 = np.zeros_like(Xtrap3)
    for ii in range(nth):
        medXtrap3[:, :, ii] = median_filter(Xtrap3[:, :, ii], size=(w, w))

    Y = np.argmax(medXtrap3, axis=2) + 1 #! Axis 2 is the third dimension; +1 to match the index as in Matlab. May need to change the +1 based on the context
    Y = Y * (Y > 0) + (Y == 0)

    return Y


def gaussian_kernel(size, sigma):
    # Create a 1D array of evenly spaced values from -size//2 to size//2
    ax = np.linspace(-(size // 2), size // 2, size)
    # Create 2D coordinate grids from the 1D array (meshgrid of x and y)
    xx, yy = np.meshgrid(ax, ax)
    # Compute the 2D Gaussian function on the grid
    kernel = np.exp(-(xx ** 2 + yy ** 2) / (2.0 * sigma ** 2))
    # Normalize the kernel so that the sum of all elements equals 1
    return kernel / np.sum(kernel)


def smooth_function(h, X):
    Mx, My = h.shape
    nx = (Mx - 1) // 2
    ny = (My - 1) // 2
    Xe = iexpansion(X, nx, ny)
    fXe = convolve(Xe, h, mode='constant', cval=0.0)
    return fXe[nx:-nx, ny:-ny]


def iexpansion(X, nx, ny):
    Xn = np.flipud(X)[-nx:, :]
    Xs = np.flipud(X)[:nx, :]
    Xe = np.fliplr(X)[:, :ny]
    Xw = np.fliplr(X)[:, -ny:]
    Xr = np.flipud(np.fliplr(X))                # flip both axes once
    Xne = Xr[-nx:, :ny]                         # top-right corner
    Xno = Xr[-nx:, -ny:]                        # top-left corner
    Xse = Xr[:nx, :ny]                          # bottom-right corner
    Xso = Xr[:nx, -ny:]                         # bottom-left corner


    top = np.hstack((Xno, Xn, Xne))
    mid = np.hstack((Xw, X, Xe))
    bot = np.hstack((Xso, Xs, Xse))

    return np.vstack((top, mid, bot))


def trapezoid_fuzzy_membership(x, a, b, c, d):
    x = x.astype(np.float64)
    y = np.zeros_like(x)

    if (b < a) or (c < b) or (d < c):
        raise ValueError('Bad params')

    if a == b:
        y = ((x - c) * (-1) / (d - c) + 1) * ((x > c) & (x < d)) + (x <= c)
    elif b == c:
        y = ((x - a) / (b - a)) * ((x > a) & (x <= b)) + ((x - c) * (-1) / (d - c) + 1) * ((x > c) & (x < d))
    elif c == d:
        y = ((x - a) / (b - a)) * ((x > a) & (x < b)) + (x >= b)
    else:
        y = ((x - a) / (b - a)) * ((x > a) & (x < b)) + ((x >= b) & (x <= c)) + ((x - c) * (-1) / (d - c) + 1) * (
            (x > c) & (x < d))

    return y
