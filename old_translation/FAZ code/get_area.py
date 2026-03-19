import numpy as np

def get_area(x:np.ndarray,y:np.ndarray)->float:
    """
    Computes the signed area of a polygon using the shoelace formula.

    Parameters:
    - x: 1D array of x-coordinates of the contour points
    - y: 1D array of y-coordinates of the contour points

    Returns:
    - A: Signed area of the polygon (float)
    """
    if len(x) != len(y):
        raise ValueError("Input arrays must have the same length")

    n=len(x)
    sum=0
    for i in range(n-1):
        sum+=x[i]*y[i+1]-x[i+1]*y[i] #! this is converted from the matlab code but it's only correct if the polygon is already closed

    return 0.5*sum

if __name__ == "__main__":
    # Example usage
    print(get_area(np.array([0, 1, 1, 0]), np.array([0, 0, 1, 1])))
    