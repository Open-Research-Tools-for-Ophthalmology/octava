import numpy as np

def pk_follow_link(skel, node, k, j, idx, cans, c2n, max_iter=10000, debug=False):
    vox = []
    n_idx = None
    ep = 0

    # assign start node to first voxel
    vox.append(node[k]['idx'][j])

    i = 0
    isdone = False
    while not isdone:
        i += 1

        if i > max_iter:  # safety guard
            print("⚠️ Max iterations reached, possible infinite loop!")
            break

        next_cand = c2n[idx]  # row index into cans
        cand = cans[next_cand, 1]  # candidate neighbor (col 2)
        if cand == vox[i - 1]:
            cand = cans[next_cand, 2]  # switch to other neighbor

        if debug:
            print(f"\nIteration {i}")
            print(f"  Current idx: {idx}")
            print(f"  Candidate row (next_cand): {next_cand}")
            print(f"  cand: {cand}")
            print(f"  skel[cand]: {skel.flat[cand]}")
            print(f"  vox so far: {vox[-5:]}")  # last 5 voxels

        if skel.flat[cand] > 1:  # node found
            vox.append(idx)
            vox.append(cand)
            n_idx = int(skel.flat[cand]) - 1
            if node[n_idx]['ep']:
                ep = 1
            isdone = True
        else:  # keep walking
            vox.append(idx)
            idx = cand

    return vox, n_idx, ep



def pk_get_nh(img, i):
    """
    Get the 3x3x3 neighborhood (as a 2D boolean array) for each skeleton voxel 
    in the 3D image. Each column corresponds to one position in the 3x3x3 neighborhood 
    (including the voxel itself).

    Args:
        img (np.ndarray): 3D skeletonized image (binary or integer)
        i (np.ndarray): 1D array of all foreground (True) voxels

    Returns:
        np.ndarray: neighborhood matrix of shape (len(i), 27), dtype=bool
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
                    (nx[mask], ny[mask], nz[mask]), img.shape
                )
                nh_vals = np.zeros_like(nx, dtype=bool)
                nh_vals[mask] = img.flat[idx[mask]]
                nhood[:, w] = nh_vals
                w += 1
    return nhood


def pk_get_nh_idx(img, i):
    """
    Get the flat indices of the 3x3x3 neighborhood for each skeleton voxel in a 3D image.

    Args:
        img (np.ndarray): 3D skeletonized image (binary or integer)
        i (np.ndarray): 1D array of flat indices of foreground (skeleton) voxels

    Returns:
        np.ndarray: neighborhood (len(i), 27) integer array of flat indices

    Raises:
        IndexError: if any neighbor is out of bounds
    """
    width, height, depth = img.shape
    x, y, z = np.unravel_index(i, img.shape)

    nhood = np.zeros((len(i), 27), dtype=int)
    w = 0
    for xx in range(3):
        for yy in range(3):
            for zz in range(3):
                nx = x + xx - 1
                ny = y + yy - 1
                nz = z + zz - 1

                # Check bounds
                if (
                    np.any(nx < 0) or np.any(nx >= width) or
                    np.any(ny < 0) or np.any(ny >= height) or
                    np.any(nz < 0) or np.any(nz >= depth)
                ):
                    raise IndexError("Neighbor index out of bounds")

                nh_idx = np.ravel_multi_index((nx, ny, nz), (width, height, depth))
                nhood[:, w] = nh_idx
                w += 1

    return nhood
