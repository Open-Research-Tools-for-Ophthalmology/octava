import numpy as np

def im_expand(I:np.ndarray, Nx:int, Ny:int)->np.ndarray:
    """
    Symmetric (DCT-like) expansion of a 2D image by mirroring its edges and corners.

    This function expands the input image `I` by `Nx` rows (top and bottom)
    and `Ny` columns (left and right) using mirrored padding. This is useful
    for avoiding edge effects in image filtering or convolution operations.

    Parameters:
    ----------
    I : np.ndarray
        2D input image (grayscale).
    Nx : int
        Number of rows to mirror at the top and bottom.
    Ny : int
        Number of columns to mirror at the left and right.

    Returns:
    -------
    I_out : np.ndarray
        Expanded image with shape (H + 2*Nx, W + 2*Ny),
        where H and W are the height and width of the original image.
    """
    I_v = np.flipud(I)
    I_top = I_v[-Nx:, :]
    I_bottom=I_v[:Nx, :]

    I_h=np.fliplr(I)
    I_right = I_h[:, :Ny]
    I_left =I_h[:, -Ny:]

    I_c=np.flipud(I_h)
    I_top_right=I_c[-Nx:, :Ny]
    I_top_left=I_c[-Nx:, -Ny:]
    I_bottom_right=I_c[:Nx, :Ny]
    I_bottom_left=I_c[:Nx, -Ny:]

    # Concatenate blocks
    top = np.hstack((I_top_left, I_top, I_top_right))
    middle = np.hstack((I_left, I, I_right))
    bottom = np.hstack((I_bottom_left, I_bottom, I_bottom_right))
    I_out = np.vstack((top, middle, bottom))

    return I_out