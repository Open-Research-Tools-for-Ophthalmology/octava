import numpy as np
from scipy import sparse
from scipy.ndimage import label, generate_binary_structure
from skimage.measure import label as skimage_label
from pk_functions import pk_get_nh, pk_get_nh_idx, pk_follow_link

def skel2graph3d(skel, THR, debug = False):
    """
    Calculate the network graph of a 3D voxel skeleton.

    Parameters
    ----------
    skel : ndarray (3D, binary)
        Input 3D binary image representing the skeleton.
    THR : int or float
        Minimum branch length threshold. Branches shorter than this
        will be pruned.

    Returns
    -------
    A : ndarray
        Adjacency matrix of the skeleton graph.
    node : list of dict
        List of node structures describing node properties.
    link : list of dict
        List of link structures describing link properties.

    Notes
    -----
    Based on the MATLAB implementation by Philip Kollmannsberger
    (philipk@gmx.net). Original version available at the MATLAB File
    Exchange:
    http://uk.mathworks.com/matlabcentral/fileexchange/43527-skel2graph-3d
    """
    # pad volume with zeros
    skel = np.pad(skel, pad_width=1, mode='constant')
    
    # label connected components 
    ndim = skel.ndim
    structure = generate_binary_structure(ndim, ndim)
    lm, _ = label(skel, structure=structure)
    
    # get image dimensions
    w, l, h = skel.shape
    skel2 = skel.astype(np.uint16) # needed for labeling nodes etc.
    
    # all foreground (True) voxels, as flat indices -> careful here because of 0-indexing in python
    list_canal = np.flatnonzero(skel)

    # if image contains no skeletonized data, return empty elements
    if len(list_canal) == 0:
        return sparse.csr_matrix((0,0)), [{
            'idx':[], 'links':[], 'conn':[], 'comx':[], 'comy':[], 'comz':[], 'ep':[], 'label':[]
        }], []
    
    # 26-nh of all canal voxels
    nh = pk_get_nh(skel, list_canal)       # shape: (N, 27)

    # 26-nh indices of all canal voxels
    nhi = pk_get_nh_idx(skel, list_canal)  # shape: (N, 27)

    # num of 26-nb of each skel voxel + 1
    sum_nh = np.sum(nh.astype(bool), axis=1)
    
    # node/endpoint/canal assignment
    nodes = list_canal[sum_nh > 3] # all canal voxels with >2 nb are nodes -> branching points
    ep    = list_canal[sum_nh == 2] # all canal voxels with exactly one nb are end nodes -> endpoints
    cans  = list_canal[sum_nh == 3] # all canal voxels with exactly 2 nb -> segments
    
    # Nx3 matrix with the 2 neighbors of each canal voxel
    if cans.size > 0:
        can_nh_idx = pk_get_nh_idx(skel, cans)
        can_nh = pk_get_nh(skel, cans)

        # remove center of 3x3 cube
        can_nh_idx = np.delete(can_nh_idx, 13, axis=1)
        can_nh = np.delete(can_nh, 13, axis=1)

        # keep only the two existing foreground voxels
        can_nb = np.sort(can_nh * can_nh_idx, axis=1)
        can_nb = can_nb[:, -2:]  # keep last two columns

        # add neighbours to canalicular voxel list (this might include nodes)
        cans_all = np.column_stack([cans, can_nb])
    else:
        cans_all = np.empty((0, 3), dtype=int)
    
    # group clusters of node voxels to nodes
    node, link = [], []

    tmp = np.zeros((w, l, h), dtype=bool)
    tmp.ravel()[nodes] = True
    labelimg, num_realnodes = label(tmp, structure=np.ones((3,3,3))) # number of unique nodes

    # create node structure for branching points (node metadata)
    for labelidx in range(1, num_realnodes+1):
        idxs = np.flatnonzero(labelimg == labelidx)
        x, y, z = np.unravel_index(idxs, (w,l,h))
        node.append({
            'idx': idxs.tolist(),
            'links': [], # indices to access each link's metadata (defined below)
            'conn': [],
            'comx': float(np.mean(x)),
            'comy': float(np.mean(y)),
            'comz': float(np.mean(z)),
            'ep': 0,
            'label': int(lm.flat[idxs[0]]),
        })
        skel2.flat[idxs] = len(node)  # assign index to node voxels

    # cluster endpoint voxels ('ep')
    tmp = np.zeros((w, l, h), dtype=bool)
    tmp.ravel()[ep] = True
    labelimg, num_endnodes = label(tmp, structure=np.ones((3,3,3)))
    for idx in range(1, num_endnodes+1):
        idxs = np.flatnonzero(labelimg == idx)
        ni = num_realnodes + idx - 1
        x, y, z = np.unravel_index(idxs, (w, l, h))

        # create node structure for endpoints (node metadata)
        node.append({
            'idx': idxs.tolist(),
            'links': [], # indices to access each link's metadata (defined below)
            'conn': [],
            'comx': float(np.mean(x)),
            'comy': float(np.mean(y)),
            'comz': float(np.mean(z)),
            'ep': 1,
            'label': int(lm.flat[idxs[0]]),
        })
        skel2.flat[idxs] = len(node)
        
    l_idx = 0

    c2n = np.zeros(w*l*h, dtype=int)
    if cans_all.shape[0] > 0:
        c2n[cans_all[:,0]] = np.arange(cans_all.shape[0])
    s2n = np.zeros(w*l*h, dtype=int)
    if nhi.shape[0] > 0:
        s2n[nhi[:,13]] = np.arange(nhi.shape[0])

    # visit all nodes
    for i, n in enumerate(node):

        # find all canal vox connected to curr node
        this_idxs = n['idx']
        link_idx = s2n[this_idxs]

        # visit all voxels of this node
        for j in range(len(link_idx)):

            lli = link_idx[j]
            if lli == 0:
                continue

            # all potential unvisited links emanating from this voxel
            link_cands = nhi[lli, np.where(nh[lli,:])[0]]

            # short branches that only have an endpoint
            ep_cands = np.intersect1d(link_cands, ep)
            cond = (skel2.flat[link_cands] == 1)
            link_cands = link_cands[cond]
            link_cands = np.intersect1d(link_cands, cans_all[:,0]) if cans_all.shape[0] > 0 else []

            for cand in link_cands:
                # if debug:
                #     vox, n_idx, ept = pk_follow_link(skel2, node, i, j, cand, cans_all, c2n, debug = True)
                vox, n_idx, ept = pk_follow_link(skel2, node, i, j, cand, cans_all, c2n)
                skel2.flat[np.array(vox)[1:-1]] = 0

                # create link structure (link metadata) respecting the THR branch size
                if ((ept and len(vox) > THR) or (not ept and i != n_idx)):
                    link.append({
                        'n1': i,
                        'n2': n_idx,
                        'point': vox,
                        'label': int(lm.flat[vox[0]])
                    })
                    n['links'].append(l_idx)
                    n['conn'].append(int(n_idx))
                    node[n_idx]['links'].append(l_idx)
                    node[n_idx]['conn'].append(int(i))
                    l_idx += 1
            # If short branches allowed (2 connected pixels)
            iter = 0 # remove later
            if THR == 0:
                if debug:
                    print("\n\n")
                    print("==== DEBUGGING SKEL2GRAPH3D WHEN THR IS 0 ===")
                    print("Ep_cands: ", ep_cands)
                    print("Len of ep_cands: ", len(ep_cands))
                    print("Type of ep_cands: ", type(ep_cands))
                for ep_cand in ep_cands:
                    if debug:
                        print(f"--- Iter count: {iter} ---: ")
                        print("Current ep_cand: ", ep_cand)
                        print("Type of ep_cand: ", type(ep_cand))
                        print("Current n_idx: ", n_idx)
                        print("current l_idx: ",l_idx)
                    n_idx = skel2.flat[ep_cand]
                    if n_idx and n_idx != i:
                        skel2.flat[ep_cand] = 0
                        link.append({
                            'n1': i,
                            'n2': int(n_idx),
                            'point': [int(ep_cand)],
                            'label': int(lm.flat[ep_cand])
                        })
                        n['links'].append(l_idx)
                        n['conn'].append(int(n_idx))
                        node[int(n_idx)]['links'].append(l_idx)
                        node[int(n_idx)]['conn'].append(int(i))
                        l_idx += 1
                    iter += 1

    # Mark single-link nodes as endpoints
    if node:
        ep_idx = [idx for idx, nd in enumerate(node) if len(nd['links']) == 1]
        for idx in ep_idx:
            node[idx]['ep'] = 1

    # number of nodes
    n_nodes = len(node)

    # initialize matrix
    A = np.zeros((n_nodes, n_nodes), dtype=int)

    # for all nodes, make according entries into matrix for all its links
    for i, nd in enumerate(node):
        idx1 = [jj for jj,jjv in enumerate(nd['conn']) if jjv>0]
        idx2 = [jj for jj,jjv in enumerate(nd['links']) if jjv>=0]
        idx = np.intersect1d(idx1, idx2)
        for j in idx: # for all its links
            link_idx = nd['links'][j]
            if i == link[link_idx]['n1']: # if we are the starting point
                ln = link[link_idx]['n2']
                L = len(link[link_idx]['point'])
                A[i, ln] = L
                A[ln, i] = L
            if i == link[link_idx]['n2']: # if we are the end point
                ln = link[link_idx]['n1']
                L = len(link[link_idx]['point'])
                A[i, ln] = L
                A[ln, i] = L

    # Convert adjacency matrix to sparse
    A = sparse.csr_matrix(A)

    # transform all voxel and position indices back to non-padded coordinates
    if node:
        for nd in node:
            x, y, z = np.unravel_index(nd['idx'], (w, l, h))
            # -1 for the pad
            x, y, z = np.array(x)-1, np.array(y)-1, np.array(z)-1
            nd['idx'] = np.ravel_multi_index((x, y, z), (w-2, l-2, h-2))
            nd['comx'] -= 1
            nd['comy'] -= 1
            nd['comz'] -= 1

    # transform all link voxel indices back to non-padded coordinates
    for lk in link:
        x, y, z = np.unravel_index(lk['point'], (w, l, h))
        # -1 for the pad
        x, y, z = np.array(x)-1, np.array(y)-1, np.array(z)-1
        lk['point'] = np.ravel_multi_index((x, y, z), (w-2, l-2, h-2))
    
    return A, node, link