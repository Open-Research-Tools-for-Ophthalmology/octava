import numpy as np
from scipy.ndimage import label, generate_binary_structure
from scipy.sparse import csr_matrix
from pk_functions import pk_follow_link, pk_get_nh, pk_get_nh_idx

def pad_volume(vol, pad=1):
    return np.pad(vol, pad_width=pad, mode='constant')

def bwconncomp(binary_img):
    struct = generate_binary_structure(3, 3)
    labeled, num = label(binary_img, structure=struct)
    # Create list of pixel indices for each component
    obj_pixel_list = [(labeled == i+1).nonzero() for i in range(num)]
    flat_pix_lists = [np.ravel_multi_index(indices, binary_img.shape) for indices in obj_pixel_list]
    return {'NumObjects': num, 'PixelIdxList': flat_pix_lists, 'labeled': labeled}

def skel2graph3d(skel, THR):
    skel = pad_volume(skel, pad=1)
    # Connected components (each skeleton, label matrix)
    cc_skel = bwconncomp(skel)
    lm = cc_skel['labeled']
    w, l, h = skel.shape
    skel2 = skel.astype(np.uint16)
    list_canal = np.flatnonzero(skel)
    
    # These must be implemented for correct 26-neighbor retrievals:
    nh = pk_get_nh(skel, list_canal)  # (N, 27) (including self)
    nhi = pk_get_nh_idx(skel, list_canal)  # (N, 27)
    sum_nh = np.sum(nh, axis=1)

    # "node" voxels: >2 neighbors, "end node": exactly one neighbor, "canal": exactly 2 neighbors
    nodes = list_canal[sum_nh > 3]
    ep = list_canal[sum_nh == 2]
    cans = list_canal[sum_nh == 3]
    
    # Build can_nb, add neighbors, remove self
    can_nh_idx = pk_get_nh_idx(skel, cans)  # (e.g., [num_cans, 27])
    can_nh = pk_get_nh(skel, cans)          # (ditto)
    can_nh_idx = np.delete(can_nh_idx, 13, axis=1)  # 14-th col (central) index for MATLAB 1-based
    can_nh = np.delete(can_nh, 13, axis=1)
    can_nb = np.sort((can_nh * can_nh_idx), axis=1)  # Remove zeros
    can_nb = can_nb[:, -2:]  # Only keep last two columns (neighbor indices)
    cans = np.concatenate([cans[:, None], can_nb], axis=1).flatten()
    
    # Cluster of node voxels into nodes
    node, link = [], []
    tmp = np.zeros((w, l, h), dtype=bool)
    tmp.flat[nodes] = 1
    cc2 = bwconncomp(tmp)
    num_realnodes = cc2['NumObjects']

    # Node structure creation
    skel2_flat = skel2.ravel()
    for i in range(num_realnodes):
        idxs = cc2['PixelIdxList'][i]
        x, y, z = np.unravel_index(idxs, (w, l, h))
        # Create node dict
        node.append({
            'idx': idxs,
            'links': [],
            'conn': [],
            'comx': x.mean(),
            'comy': y.mean(),
            'comz': z.mean(),
            'ep': 0,
            'label': lm.flat[idxs[0]]
        })
        # Assign index to node voxels in skel2
        skel2_flat[idxs] = i + 2  # MATLAB i+1, Python i+2 due to padding+index

    # Repeat for endpoints ("ep")
    tmp = np.zeros((w, l, h), dtype=bool)
    tmp.flat[ep] = 1
    cc3 = bwconncomp(tmp)
    for i in range(cc3['NumObjects']):
        ni = num_realnodes + i
        idxs = cc3['PixelIdxList'][i]
        x, y, z = np.unravel_index(idxs, (w, l, h))
        node.append({
            'idx': idxs,
            'links': [],
            'conn': [],
            'comx': x.mean(),
            'comy': y.mean(),
            'comz': z.mean(),
            'ep': 1,
            'label': lm.flat[idxs[0]]
        })
        skel2_flat[idxs] = ni + 2

    l_idx = 0
    c2n = np.zeros(w*l*h, dtype=int)
    c2n[cans] = np.arange(1, len(cans)+1)

    s2n = np.zeros(w*l*h, dtype=int)
    s2n[nhi[:,13]] = np.arange(1, nhi.shape[0]+1)
    
    # Node-link creation (requires `pk_follow_link`)
    for i, nd in enumerate(node):
        link_idx = s2n[nd['idx']]
        for j in range(len(link_idx)):
            # ... implement neighbor search; call pk_follow_link as in MATLAB
            pass  # To be implemented

    # Mark end points, make adjacency matrix as in MATLAB ...
    n_nodes = len(node)
    A = np.zeros((n_nodes, n_nodes), dtype=int)
    # For each node, make adjacency etc...
    # (MATLAB code loop here, see above, translate as loop)

    A = csr_matrix(A)
    # De-pad indices to original coordinates
    for nd in node:
        x, y, z = np.unravel_index(nd['idx'], (w, l, h))
        nd['idx'] = np.ravel_multi_index((x-1, y-1, z-1), (w-2, l-2, h-2))

    for lk in link:
        x, y, z = np.unravel_index(lk['point'], (w, l, h))
        lk['point'] = np.ravel_multi_index((x-1, y-1, z-1), (w-2, l-2, h-2))
    
    if not node:
        node = [{'idx':[], 'links':[], 'conn':[], 'comx':[], 'comy':[], 'comz':[], 'ep':[], 'label':[]}]

    return A, node, link