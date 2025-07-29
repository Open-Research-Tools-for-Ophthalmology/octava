import numpy as np

def pk_follow_link(skel, node, k, j, idx, cans, c2n):
    """
    Follows a canal (link) from a node until it reaches the next node.
    skel: 3D array (int), with >1 at nodes
    node: list of dicts, node structure
    k: int, current node index
    j: int, node voxel index in node[k]['idx'] array
    idx: int, current canal voxel (flat index)
    cans: 2D array, each row: [canal voxel, neighbor1, neighbor2]
    c2n: 1D array, mapping of canal voxel flat index to row in cans
    Returns:
        vox: list of voxel indices traversed (flat indices)
        n_idx: index of next node reached
        ep: is the endpoint? (1 or 0)
    """
    vox = []
    n_idx = None
    ep = 0

    # assign start node to first voxel
    vox.append(node[k]['idx'][j])

    i = 1
    isdone = False
    while not isdone:
        i += 1
        next_cand = c2n[idx]
        # Fetch neighbor candidates from cans structure
        cand = cans[next_cand, 1]  # 2nd col: neighbor 1
        if cand == vox[i - 2]:     # If neighbor is previous voxel, switch to other
            cand = cans[next_cand, 2]  # 3rd col: neighbor 2
        if skel.flat[cand] > 1:    # Node found (skel value >1)
            vox.append(idx)        # add current canal voxel
            vox.append(cand)       # add the node voxel reached
            n_idx = int(skel.flat[cand]) - 1  # node index (Python 0-based)
            if node[n_idx]['ep']:
                ep = 1
            isdone = True
        else:
            vox.append(idx)
            idx = cand  # Move to next voxel
    return vox, n_idx, ep

def pk_get_nh(img, i):
    """
    Get the 3x3x3 neighborhood (as a 27-element vector) for each flat index in img.
    img : 3D np.ndarray (binary or integer)
    i   : 1D array of flat indices (numpy compliant)
    Returns: nhood  (len(i), 27) bool array
    """
    width, height, depth = img.shape
    x, y, z = np.unravel_index(i, img.shape)  # Arrays of shape (len(i),)

    nhood = np.zeros((len(i), 27), dtype=bool)
    w = 0
    for xx in range(3):
        for yy in range(3):
            for zz in range(3):
                # Neighbor coordinate offset: -1,0,1
                nx = x + xx - 1
                ny = y + yy - 1
                nz = z + zz - 1
                # Out-of-bounds mask
                mask = (
                    (nx >= 0) & (nx < width) &
                    (ny >= 0) & (ny < height) &
                    (nz >= 0) & (nz < depth)
                )
                idx = np.zeros_like(nx)
                idx[mask] = np.ravel_multi_index(
                    (nx[mask], ny[mask], nz[mask]),
                    img.shape
                )
                nh_vals = np.zeros_like(nx, dtype=bool)
                nh_vals[mask] = img.flat[idx[mask]]
                nhood[:, w] = nh_vals
                w += 1
    return nhood

def pk_get_nh_idx(img, i):
    """
    Return a (len(i),27) array of flat indices of the 3x3x3 neighborhood centers for each position in `i`.
    img: 3D ndarray
    i  : list or ndarray of flat indices
    Returns nhood: (len(i), 27) integer array
    """
    width, height, depth = img.shape
    x, y, z = np.unravel_index(i, img.shape)  # Arrays of shape (len(i),)

    nhood = np.zeros((len(i), 27), dtype=int)
    w = 0
    for xx in range(3):
        for yy in range(3):
            for zz in range(3):
                # Python is 0-based, so -1, 0, +1 offsets
                nx = x + xx - 1
                ny = y + yy - 1
                nz = z + zz - 1
                # This will result in invalid indices if out-of-bounds,
                # just like MATLAB's sub2ind would.
                # You may want to mask/check them later as needed.
                nh_idx = np.ravel_multi_index(
                    (nx, ny, nz), (width, height, depth),
                    mode='clip'
                )
                nhood[:, w] = nh_idx
                w += 1
    return nhood