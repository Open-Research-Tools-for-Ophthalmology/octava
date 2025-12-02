import numpy as np

def pk_get_nh_idx(img, indices):
    """
    Python translation of MATLAB pk_get_nh_idx.
    - img: 3D numpy array (shape (W,H,D)). Should be padded externally (like MATLAB padarray).
    - indices: 1D array-like of linear indices (numpy 0-based indices into img.ravel()).
    Returns:
      nhood: (N,27) int64 array. Each row contains 27 0-based linear indices for that voxel's 3x3x3 neighborhood.
    """
    indices = np.asarray(indices, dtype=np.int64)
    if indices.ndim != 1:
        indices = indices.ravel()

    w, h, d = img.shape
    # unravel to coordinates (0-based)
    x, y, z = np.unravel_index(indices, (w, h, d))
    # prepare output
    n = len(indices)
    nhood = np.empty((n, 27), dtype=np.int64)

    col = 0
    # MATLAB loops xx=1:3,yy=1:3,zz=1:3 and uses x+xx-2 etc.
    # We loop offsets (-1,0,+1) which corresponds to xx-2 in MATLAB.
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                # neighbor coordinates
                nx = x + dx
                ny = y + dy
                nz = z + dz
                # convert to linear index (0-based)
                nhood[:, col] = np.ravel_multi_index((nx, ny, nz), (w, h, d))
                col += 1

    return nhood

def pk_get_nh(img, indices):
    """
    Python translation of MATLAB pk_get_nh.
    - img: 3D numpy array (dtype can be bool or int). Should be padded externally.
    - indices: 1D array-like of linear indices (0-based).
    Returns:
      nhood: (N,27) boolean numpy array; True if voxel is foreground/non-zero.
    """
    indices = np.asarray(indices, dtype=np.int64).ravel()
    w, h, d = img.shape
    x, y, z = np.unravel_index(indices, (w, h, d))

    n = len(indices)
    nhood = np.empty((n, 27), dtype=bool)

    col = 0
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                nx = x + dx
                ny = y + dy
                nz = z + dz
                linear_idx = np.ravel_multi_index((nx, ny, nz), (w, h, d))
                # pick values from img by flat indexing
                nhood[:, col] = img.ravel()[linear_idx].astype(bool)
                col += 1

    return nhood

def pk_follow_link(skel2, nodes, curr_node_cluster_idx, curr_node_idx, can_idx, cans, c2n):
    """
    Returns the path from the current node and its current canal voxel neighbor to another node
    (endpoint or not).

    Inputs: 
        - skel2 [np.ndarray]: skeletonized image with identified node clusters (clusters have unique id [2, inf],
          all 1s are canal voxels, and all 0s are background voxels)
        - nodes [list[node_cluster]]: list of all node_clusters in the network
        - curr_node_cluster_idx [int]: index of the current node cluster
        - curr_node_idx [int]: index of the current voxel in the current node cluster
        - can_idx [int]: current canal voxel index
        - cans [np.ndarray or list]: canal voxel connections
        - c2n [np.ndarray or list]: mapping from canal voxel index to neighbor canal index
    """
    path = []
    ep = 0

    # ensure int
    path.append(int(nodes[curr_node_cluster_idx].nodes_idx[curr_node_idx]))

    done = False
    while not done:
        next_cand = int(c2n[can_idx] - 1)
        cand = int(cans[next_cand][1])

        # switch to other canal voxel neighbor
        if cand == path[-1]:
            cand = int(cans[next_cand][2])

        if skel2.flat[cand] > 1:
            path.append(int(can_idx))
            path.append(int(cand))
            n_idx = int(skel2.flat[cand] - 2)

            ep = int(nodes[n_idx].ep)
            done = True

        else:
            path.append(int(can_idx))
            can_idx = int(cand)

    return (path, n_idx, ep)