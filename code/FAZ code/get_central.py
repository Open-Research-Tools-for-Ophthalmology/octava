import numpy as np
from get_area import get_area

def get_central(x,y):
    '''
    Computes the central point of a polygon defined by its contour points.'''
    if len(x) != len(y):
        raise ValueError("Input arrays must have the same length")

    if (x[0] != x[-1]) or (y[0] != y[-1]):
        x = np.append(x, x[0])
        y = np.append(y, y[0])

    area = get_area(x, y)
    if area == 0:
        raise ValueError("Polygon area is zero; centroid is undefined.")
    
    cross = x[:-1] * y[1:] - x[1:] * y[:-1]

    sum_x = np.sum(cross * (x[:-1] + x[1:]))
    sum_y = np.sum(cross * (y[:-1] + y[1:]))

    Cx = sum_x / (6 * area)
    Cy = sum_y / (6 * area)

    return Cx, Cy


