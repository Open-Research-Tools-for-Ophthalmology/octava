import numpy as np
from scipy.ndimage import label
from modules.pk_functions import pk_get_nh, pk_get_nh_idx, pk_follow_link

class node_cluster:
    def __init__(self, nodes_idx: list[int], ep: int):
        """Initialize a node cluster with its voxel indices and endpoint flag."""
        self.nodes_idx = nodes_idx
        self.links = []
        self.conn = []
        self.ep = ep
        self.comx = None
        self.comy = None
        self.comz = None
        self.label = None

    def find_center_mass(self, skel_dim):
        """Compute the cluster center of mass in skeleton coordinates."""
        x, y, z = np.unravel_index(self.nodes_idx, skel_dim)
        self.comx = np.mean(x)
        self.comy = np.mean(y)
        self.comz = np.mean(z)

    def assign_label(self, lm):
        """Assign the connected-component label for this node cluster."""
        self.label = lm.ravel()[self.nodes_idx[0]]

    def __str__(self):
        """Return a debug-friendly string representation of the node cluster."""
        return f"node_cluster(nodes={self.nodes_idx}, links={self.links}, conn={self.conn}, ep={self.ep})"


class Link:
    def __init__(self, start, end, path, label):
        """Initialize a graph link between two nodes and its voxel path."""
        self.start = start
        self.end = end
        self.path = path
        self.label = label
        self.x = None
        self.y = None
        self.dir_vectors = None
        self.pixLength = None
        self.end2endLength = None
        self.tortuosity = None
        self.diameterMeasurements = None
        self.diameter = None


##############################################
# Helper: unpadding
##############################################

def unpad_indices(indices, padded_shape):
    """Map indices from a 1-pixel padded volume back to the original volume."""
    px, py, pz = padded_shape
    ux, uy, uz = px - 2, py - 2, pz - 2

    x, y, z = np.unravel_index(indices, padded_shape)
    x -= 1
    y -= 1
    z -= 1

    good = (
        (x >= 0) & (x < ux) &
        (y >= 0) & (y < uy) &
        (z >= 0) & (z < uz)
    )

    x = x[good]
    y = y[good]
    z = z[good]

    return np.ravel_multi_index((x, y, z), (ux, uy, uz))


##############################################
# FAST, EXACT skel2graph3d
##############################################

def skel2graph3d(skel, thr=0):
    """Convert a padded 2D/3D skeleton mask into node and link graph structures."""

    # -----------------------------
    # 1. Guarantee 3D + pad
    # -----------------------------
    original_2d = (skel.ndim == 2)
    if original_2d:
        skel = skel[:, :, None]

    skel = np.pad(skel, 1, mode="constant")
    w, h, d = skel.shape

    # label components
    lm, _ = label(skel, structure=np.ones((3, 3, 3)))
    lm_flat = lm.ravel()

    skel_flat = skel.ravel()
    skel2 = skel.astype(np.uint16)
    skel2_flat = skel2.ravel()

    # foreground voxels
    list_canal = np.flatnonzero(skel_flat)
    if list_canal.size == 0:
        return [], []

    # full neighborhood
    nh = pk_get_nh(skel, list_canal)         # bool matrix (N,27)
    nhi = pk_get_nh_idx(skel, list_canal)    # int matrix (N,27)

    # degree (#neighbors - 1)
    deg = nh.sum(axis=1)

    # classify
    nodes = list_canal[deg > 3]
    ep = list_canal[deg == 2]
    cans = list_canal[deg == 3]

    # -----------------------------------------
    # Compute canal neighbors (same as original)
    # -----------------------------------------
    if cans.size > 0:
        cnh = pk_get_nh(skel, cans)
        cnh_idx = pk_get_nh_idx(skel, cans)

        # remove center
        cnh = np.delete(cnh, 13, axis=1)
        cnh_idx = np.delete(cnh_idx, 13, axis=1)

        # keep only neighbors where cnh == True
        cand_nb = np.sort(cnh * cnh_idx, axis=1)
        cand_nb = cand_nb[:, -2:]
        cans = np.column_stack([cans, cand_nb])
    else:
        cans = np.empty((0, 3), dtype=int)

    ##########################################################
    # Group node clusters (branch points) exactly as original
    ##########################################################
    node_list = []
    skel2_tmp = np.zeros_like(skel2_flat, dtype=bool)
    skel2_tmp[nodes] = True

    labelimg, n_clusters = label(
        skel2_tmp.reshape(skel.shape),
        structure=np.ones((3,3,3))
    )
    labelimg_flat = labelimg.ravel()

    cluster_indices = [
        np.flatnonzero(labelimg_flat == (i + 1))
        for i in range(n_clusters)
    ]

    # build node_cluster objects
    for i, idxs in enumerate(cluster_indices):
        nc = node_cluster(idxs, 0)
        nc.find_center_mass(skel.shape)
        nc.assign_label(lm)
        node_list.append(nc)
        skel2_flat[idxs] = i + 2   # mark node index in skel2

    # -----------------------------------------
    # Endpoints as separate clusters
    # -----------------------------------------
    skel2_tmp[:] = False
    skel2_tmp[ep] = True
    labelimg, n_end = label(
        skel2_tmp.reshape(skel.shape),
        structure=np.ones((3,3,3))
    )
    labelimg_flat = labelimg.ravel()

    epi_clusters = [
        np.flatnonzero(labelimg_flat == (i + 1))
        for i in range(n_end)
    ]

    for idxs in epi_clusters:
        nc = node_cluster(idxs, 1)
        nc.find_center_mass(skel.shape)
        nc.assign_label(lm)
        node_list.append(nc)
        skel2_flat[idxs] = len(node_list) + 1

    ##########################################################
    # Build c2n and s2n lookup maps
    ##########################################################

    # map each canal voxel → its row index in cans
    c2n = np.zeros_like(skel2_flat, dtype=int)
    if cans.size > 0:
        c2n[cans[:,0]] = np.arange(1, cans.shape[0] + 1)

    # map skeleton voxel → its index in nhi/nh tables
    s2n = np.zeros_like(skel2_flat, dtype=int)
    s2n[nhi[:, 13]] = np.arange(1, nhi.shape[0] + 1)

    ##########################################################
    # LINK BUILDING — FAST, EXACT, SAFE
    ##########################################################

    link_list = []
    l_idx = 0
    # --- O(1) membership masks ---
    is_canal_voxel = np.zeros_like(skel2_flat, dtype=bool)
    if cans.size > 0:
        is_canal_voxel[cans[:, 0]] = True

    is_ep_voxel = np.zeros_like(skel2_flat, dtype=bool)
    is_ep_voxel[ep] = True

    for curr_node_idx_cluster, node_obj in enumerate(node_list):

        node_vox = node_obj.nodes_idx
        link_indices = s2n[node_vox] - 1   # preserves 1:1 positional mapping

        for curr_node_local_idx, li in enumerate(link_indices):

            if li < 0:
                continue

            # neighborhood where nh is True
            nh_row = nh[li]
            candidates = nhi[li][nh_row]

            # endpoint neighbors
            ep_cands = candidates[is_ep_voxel[candidates]]

            # only voxels still marked 1 in skel2 and in canal list
            cand_mask = (skel2_flat[candidates] == 1)
            candidates = candidates[cand_mask]
            candidates = candidates[is_canal_voxel[candidates]]
            if candidates.size == 0:
                continue


            # follow each canal candidate
            for c in candidates:

                path, end_node, ept = pk_follow_link(
                    skel2, node_list,
                    curr_node_idx_cluster,
                    curr_node_local_idx,      # IMPORTANT: preserve index!
                    int(c),
                    cans,
                    c2n
                )

                if len(path) > 2:
                    skel2_flat[path[1:-1]] = 0

                # threshold rule identical to MATLAB
                if (ept and len(path) <= thr) or \
                   (not ept and curr_node_idx_cluster == end_node):
                    continue

                # create Link
                new_link = Link(
                    curr_node_idx_cluster,
                    end_node,
                    path,
                    int(lm_flat[path[0]])
                )
                link_list.append(new_link)

                # update node connections
                node_obj.links.append(l_idx)
                node_obj.conn.append(end_node)

                node_list[end_node].links.append(l_idx)
                node_list[end_node].conn.append(curr_node_idx_cluster)

                l_idx += 1

            # THR == 0: add trivial endpoint links
            if thr == 0 and ep_cands.size:
                for ep_vox in ep_cands:

                    val = int(skel2_flat[ep_vox])
                    ep_idx = max(val - 2, 0)

                    if ep_idx and ep_idx != curr_node_idx_cluster:
                        skel2_flat[ep_vox] = 0
                        path = [int(ep_vox)]

                        new_link = Link(
                            curr_node_idx_cluster,
                            ep_idx,
                            path,
                            int(lm_flat[ep_vox])
                        )

                        link_list.append(new_link)

                        node_obj.links.append(l_idx)
                        node_obj.conn.append(ep_idx)

                        node_list[ep_idx].links.append(l_idx)
                        node_list[ep_idx].conn.append(curr_node_idx_cluster)

                        l_idx += 1

    ##########################################################
    # Mark nodes with exactly 1 link as endpoints
    ##########################################################
    for i, nd in enumerate(node_list):
        if len(nd.links) == 1:
            nd.ep = 1

    ##########################################################
    # Unpad final node + link paths back to original 2D
    ##########################################################
    padded_shape = skel.shape

    for nd in node_list:
        nd.nodes_idx = unpad_indices(nd.nodes_idx, padded_shape)

    for lk in link_list:
        lk.path = unpad_indices(lk.path, padded_shape)

    ##########################################################
    # return results
    ##########################################################
    return node_list, link_list
