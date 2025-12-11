import numpy as np

def get_lines(c:np.ndarray):
    """
    Parses a contour matrix in MATLAB-style format (2 x N) and returns:
    - s: list of dicts with keys 'v', 'x', 'y' for each contour line
    - index: index of the contour line with the most points

    Parameters:
    - c: 2D NumPy array of shape (2, N), where contour lines are encoded
         as: [value, x1, x2, ..., xn; n_points, y1, y2, ..., yn]

    Returns:
    - s: list of dicts, one for each contour line
    - index: index of the longest contour line
    """
    sz = c.shape[1]
    ii = 0
    jj = 0
    maxi = 0
    index = 0
    s = []

    while ii < sz:
        n = int(c[1, ii])  # number of points in this contour
        value = c[0, ii]
        x = c[0, ii + 1 : ii + 1 + n]
        y = c[1, ii + 1 : ii + 1 + n]

        s.append({'v': value, 'x': x, 'y': y})

        if n > maxi:
            maxi = n
            index = jj

        ii += n + 1  # move to the next contour block
        jj += 1

    return s, index

