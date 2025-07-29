import numpy as np
from scipy import sparse
from scipy.ndimage import label
from skimage.measure import label as skimage_label
from pk_functions import pk_get_nh, pk_get_nh_idx

def skel2graph3d(skel, THR):
    # 1. Pad volume with zeros
    skel = np.pad(skel, pad_width=1, mode='constant')
    
    # 2. Label connected components (for 'label' attribute etc)
    lm = skimage_label(skel)   # or use scipy.ndimage.label, skimage has more flexible input
    
    w, l, h = skel.shape
    skel2 = skel.astype(np.uint16)
    
    # 3. All foreground (True) voxels, as flat indices
    list_canal = np.flatnonzero(skel)
    if len(list_canal) == 0:
        return sparse.csr_matrix((0,0)), [{
            'idx':[], 'links':[], 'conn':[], 'comx':[], 'comy':[], 'comz':[], 'ep':[], 'label':[]
        }], []
    
    # 4. 26-neighborhoods
    nh = pk_get_nh(skel, list_canal)       # shape: (N, 27)
    nhi = pk_get_nh_idx(skel, list_canal)  # shape: (N, 27)
    sum_nh = np.sum(nh, axis=1)
    
    # 5. Node/endpoint/canal assignment
    nodes = list_canal[sum_nh > 3]
    ep    = list_canal[sum_nh == 2]
    cans  = list_canal[sum_nh == 3]
    
    # 6. Find canal neighbors
    if cans.size > 0:
        can_nh_idx = pk_get_nh_idx(skel, cans)
        can_nh = pk_get_nh(skel, cans)
        # Remove the center voxel (14th: Python 13)
        can_nh_idx = np.delete(can_nh_idx, 13, axis=1)
        can_nh = np.delete(can_nh, 13, axis=1)
        can_nb = np.sort((can_nh * can_nh_idx), axis=1)
        can_nb = can_nb[:, -2:]  # keep last two columns
        cans_all = np.column_stack([cans, can_nb])
    else:
        cans_all = np.empty((0,3), dtype=int)
    
    # 7. Cluster 'nodes' voxels into unique nodes (connected regions)
    node, link = [], []
    tmp = np.zeros((w, l, h), dtype=bool)
    tmp.ravel()[nodes] = True
    labelimg, num_realnodes = label(tmp, structure=np.ones((3,3,3)))
    for labelidx in range(1, num_realnodes+1):
        idxs = np.flatnonzero(labelimg == labelidx)
        x, y, z = np.unravel_index(idxs, (w,l,h))
        node.append({
            'idx': idxs.tolist(),
            'links': [],
            'conn': [],
            'comx': float(np.mean(x)),
            'comy': float(np.mean(y)),
            'comz': float(np.mean(z)),
            'ep': 0,
            'label': int(lm.flat[idxs[0]]),
        })
        skel2.flat[idxs] = labelidx + 1  # so first node is at (labelidx+1)

    # 8. Cluster endpoint voxels ('ep')
    tmp = np.zeros((w, l, h), dtype=bool)
    tmp.ravel()[ep] = True
    labelimg, num_endnodes = label(tmp, structure=np.ones((3,3,3)))
    for idx in range(1, num_endnodes+1):
        idxs = np.flatnonzero(labelimg == idx)
        ni = num_realnodes + idx - 1
        x, y, z = np.unravel_index(idxs, (w, l, h))
        node.append({
            'idx': idxs.tolist(),
            'links': [],
            'conn': [],
            'comx': float(np.mean(x)),
            'comy': float(np.mean(y)),
            'comz': float(np.mean(z)),
            'ep': 1,
            'label': int(lm.flat[idxs[0]]),
        })
        skel2.flat[idxs] = ni + 2
        
    l_idx = 0 # Next link index (Python: 0-based)
    c2n = np.zeros(w*l*h, dtype=int)
    if cans_all.shape[0] > 0:
        c2n[cans_all[:,0]] = np.arange(cans_all.shape[0])
    s2n = np.zeros(w*l*h, dtype=int)
    if nhi.shape[0] > 0:
        s2n[nhi[:,13]] = np.arange(nhi.shape[0])

    # 9. Visit all nodes and follow links
    for i, n in enumerate(node):
        this_idxs = n['idx']
        link_idx = s2n[this_idxs]
        for j in range(len(link_idx)):
            lli = link_idx[j]
            if lli == 0:
                continue
            # all link candidates from this voxel
            link_cands = nhi[lli, np.where(nh[lli,:])[0]]
            ep_cands = np.intersect1d(link_cands, ep)
            # short branches that only have an endpoint
            cond = (skel2.flat[link_cands] == 1)
            link_cands = link_cands[cond]
            link_cands = np.intersect1d(link_cands, cans_all[:,0]) if cans_all.shape[0] > 0 else []
            for cand in link_cands:
                vox, n_idx, ept = pk_follow_link(skel2, node, i, j, cand, cans_all, c2n)
                skel2.flat[np.array(vox)[1:-1]] = 0
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
            # If short branches allowed
            if THR == 0:
                for ep_cand in ep_cands:
                    n_idx = skel2.flat[ep_cand]-1
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

    # Mark single-link nodes as endpoints
    if node:
        ep_idx = [idx for idx, nd in enumerate(node) if len(nd['links']) == 1]
        for idx in ep_idx:
            node[idx]['ep'] = 1

    n_nodes = len(node)
    A = np.zeros((n_nodes, n_nodes), dtype=int)
    for i, nd in enumerate(node):
        idx1 = [jj for jj,jjv in enumerate(nd['conn']) if jjv>0]
        idx2 = [jj for jj,jjv in enumerate(nd['links']) if jjv>=0]
        idx = np.intersect1d(idx1, idx2)
        for j in idx:
            link_idx = nd['links'][j]
            if i == link[link_idx]['n1']:
                ln = link[link_idx]['n2']
                L = len(link[link_idx]['point'])
                A[i, ln] = L
                A[ln, i] = L
            if i == link[link_idx]['n2']:
                ln = link[link_idx]['n1']
                L = len(link[link_idx]['point'])
                A[i, ln] = L
                A[ln, i] = L

    # Convert adjacency matrix to sparse
    A = sparse.csr_matrix(A)

    # 10. Convert all indices back to non-padded coordinates!
    if node:
        for nd in node:
            x, y, z = np.unravel_index(nd['idx'], (w, l, h))
            # -1 for the pad
            x, y, z = np.array(x)-1, np.array(y)-1, np.array(z)-1
            nd['idx'] = np.ravel_multi_index((x, y, z), (w-2, l-2, h-2))
            nd['comx'] -= 1
            nd['comy'] -= 1
            nd['comz'] -= 1
    for lk in link:
        x, y, z = np.unravel_index(lk['point'], (w, l, h))
        # -1 for the pad
        x, y, z = np.array(x)-1, np.array(y)-1, np.array(z)-1
        lk['point'] = np.ravel_multi_index((x, y, z), (w-2, l-2, h-2))
    
    return A, node, link