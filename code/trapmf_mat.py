'''
Same code as trapezoid_fuzzy_membership() in fuzzy_thresholding.py
'''
import numpy as np



def trapmf_mat(x:np.ndarray, a:float, b:float, c:float, d:float) -> np.ndarray:
    """
    Compute the trapezoidal fuzzy membership values for input x.

    Parameters:
    - x: Input NumPy array
    - a, b, c, d: Float parameters defining the shape of the trapezoid.
      The membership function is:
        - 0 for x <= a or x >= d
        - Linearly increases from 0 to 1 between a and b
        - 1 between b and c
        - Linearly decreases from 1 to 0 between c and d

    Returns:
    - y: NumPy array of membership values in [0, 1], same shape as x
    """
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
