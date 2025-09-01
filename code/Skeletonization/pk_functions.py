import numpy as np

import numpy as np

def pk_get_nh(img, indices):
    """
    Compute the 3x3x3 neighborhood for each voxel in indices.
    
    Parameters
    ----------
    img : ndarray
        3D binary image (bool or 0/1)
    indices : 1D array-like
        Flattened voxel indices (0-based) into img
    
    Returns
    -------
    nhood : ndarray
        Boolean array of shape (len(indices), 27)
        Each row corresponds to the 3x3x3 neighborhood of a voxel
    """
    img = np.asarray(img)
    indices = np.asarray(indices)
    
    width, height, depth = img.shape  # MATLAB: size(img,1), size(img,2), size(img,3)
    
    # Convert linear indices to 3D coordinates
    x, y, z = np.unravel_index(indices, img.shape)  # 0-based
    
    nvox = len(indices)
    nhood = np.zeros((nvox, 27), dtype=bool)
    
    # Iterate over 3x3x3 neighborhood
    w_idx = 0
    for xx in range(3):
        for yy in range(3):
            for zz in range(3):
                # Compute neighbor coordinates
                nx = x + xx - 1  # MATLAB: x + xx - 2 (MATLAB is 1-based)
                ny = y + yy - 1
                nz = z + zz - 1
                
                # Handle out-of-bounds by clipping
                nx = np.clip(nx, 0, width-1)
                ny = np.clip(ny, 0, height-1)
                nz = np.clip(nz, 0, depth-1)
                
                # Convert back to linear indices
                neighbor_idx = np.ravel_multi_index((nx, ny, nz), img.shape)
                
                # Fill neighborhood
                nhood[:, w_idx] = img.flat[neighbor_idx]
                
                w_idx += 1
    
    return nhood


def pk_get_nh_idx(img, indices):
    """
    Compute the 3x3x3 neighborhood indices for each voxel in `indices`.

    Parameters
    ----------
    img : ndarray
        3D image (used only to get shape)
    indices : array-like
        1D flattened voxel indices (0-based)

    Returns
    -------
    nhood : ndarray
        Array of shape (len(indices), 27)
        Each row contains the flattened indices of the 3x3x3 neighborhood
    """
    img = np.asarray(img)
    indices = np.asarray(indices)

    width, height, depth = img.shape

    # Convert linear indices to 3D coordinates
    x, y, z = np.unravel_index(indices, img.shape)  # 0-based

    nvox = len(indices)
    nhood = np.zeros((nvox, 27), dtype=int)

    w_idx = 0
    for xx in range(3):
        for yy in range(3):
            for zz in range(3):
                # Neighbor coordinates (Python 0-based)
                nx = x + xx - 1  # MATLAB: x + xx - 2
                ny = y + yy - 1
                nz = z + zz - 1

                # Optional: clip to stay in bounds
                nx = np.clip(nx, 0, width-1)
                ny = np.clip(ny, 0, height-1)
                nz = np.clip(nz, 0, depth-1)

                # Convert back to linear index
                neighbor_idx = np.ravel_multi_index((nx, ny, nz), img.shape)

                nhood[:, w_idx] = neighbor_idx
                w_idx += 1

    return nhood
