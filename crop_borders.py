import numpy as np

def crop_borders(A, bcol=None, padding=0, crop_amounts=None):
    """
    Crop the borders of an image or stack of images.

    Parameters
    ----------
    A : ndarray
        H x W x C x N stack of images.
    bcol : array-like or scalar
        Background colour vector of length C. If None, use transparent case.
    padding : float, optional
        Padding relative to cropped image size (0 <= padding <= 1). Default: 0
    crop_amounts : list/tuple of 4 floats, optional
        [top, right, bottom, left]:
        - NaN/Inf -> auto-cropping
        - 0       -> no cropping
        - other   -> crop that many pixels

    Returns
    -------
    A : ndarray
        Cropped (and possibly padded) stack of images.
    vA : list
        Coordinates in A that contain the cropped image.
    vB : list
        Coordinates in B where the cropped version of A is placed.
    bb_rel : list
        Relative bounding box (for EPS cropping).
    """
    h, w, c, n = A.shape

    if crop_amounts is None:
        crop_amounts = [np.nan, np.nan, np.nan, np.nan]
    crop_amounts = list(crop_amounts) + [np.nan] * (4 - len(crop_amounts))

    if bcol is None or (isinstance(bcol, (list, np.ndarray)) and len(bcol) == 0):
        # transparent bgcolor case
        bcol = A[h // 2, 0, :, 0]
    bcol = np.array(bcol)
    if np.isscalar(bcol):
        bcol = np.full((c,), bcol)

    # --- Crop margins ---

    # left
    if not np.isfinite(crop_amounts[3]):
        l = 0
        for l in range(w):
            bail = False
            for a in range(c):
                if not np.all(A[:, l, a, :].ravel() == bcol[a]):
                    bail = True
                    break
            if bail:
                break
    else:
        l = abs(int(crop_amounts[3]))

    # right
    if not np.isfinite(crop_amounts[1]):
        r = w - 1
        for r in range(w - 1, l - 1, -1):
            bail = False
            for a in range(c):
                if not np.all(A[:, r, a, :].ravel() == bcol[a]):
                    bail = True
                    break
            if bail:
                break
    else:
        r = w - abs(int(crop_amounts[1])) - 1

    # top
    if not np.isfinite(crop_amounts[0]):
        t = 0
        for t in range(h):
            bail = False
            for a in range(c):
                if not np.all(A[t, :, a, :].ravel() == bcol[a]):
                    bail = True
                    break
            if bail:
                break
    else:
        t = abs(int(crop_amounts[0]))

    # bottom
    if not np.isfinite(crop_amounts[2]):
        b = h - 1
        for b in range(h - 1, t - 1, -1):
            bail = False
            for a in range(c):
                if not np.all(A[b, :, a, :].ravel() == bcol[a]):
                    bail = True
                    break
            if bail:
                break
    else:
        b = h - abs(int(crop_amounts[2])) - 1

    # --- Padding logic ---
    if padding == 0:
        pass
    elif abs(padding) < 1:
        padding = int(np.sign(padding) *
                      round(np.mean([(b - t), (r - l)]) * abs(padding)))
    else:
        padding = int(round(padding))

    if padding > 0:
        # Create padded background
        new_h = (b - t + 1) + padding * 2
        new_w = (r - l + 1) + padding * 2
        B = np.tile(bcol, (new_h, new_w, 1, n))

        vA = [t, b, l, r]
        vB = [padding, padding + (b - t), padding, padding + (r - l)]

        B[vB[0]:vB[1] + 1, vB[2]:vB[3] + 1, :, :] = A[t:b + 1, l:r + 1, :, :]
        A = B
    else:
        vA = [t - padding, b + padding, l - padding, r + padding]
        A = A[vA[0]:vA[1] + 1, vA[2]:vA[3] + 1, :, :]
        vB = [np.nan, np.nan, np.nan, np.nan]

    # --- EPS bounding box ---
    bb_pixels = np.array([l, h - b - 1, r + 1, h - t])
    bb_pixels = np.clip(bb_pixels, 0, [w, h, w, h])
    bb_rel = bb_pixels / np.array([w, h, w, h], dtype=float)

    return A, vA, vB, bb_rel
