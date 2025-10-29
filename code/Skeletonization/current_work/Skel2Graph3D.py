from typing import Any
import numpy as np
from scipy.ndimage import label
from pk_functions import pk_get_nh, pk_get_nh_idx, pk_follow_link

class node_cluster:
    def __init__(self, nodes_idx: list[int], ep: int):
        self.nodes_idx = nodes_idx
        self.links = []
        self.conn = [] # list of indices (w respect to the node list) of all endpoint node voxels (connections)
        self.ep = ep
        self.comx = None
        self.comy = None
        self.comz = None
        self.label = None

    def find_center_mass(self, skel_dim: tuple[int, int, int]) -> None:
        x, y, z = np.unravel_index(self.nodes_idx, skel_dim)
        self.comx = np.mean(x)
        self.comy = np.mean(y)
        self.comz = np.mean(z)
    
    def assign_label(self, lm: np.ndarray):
        self.label = lm.ravel()[self.nodes_idx[0]]

    def assign_links(self, l_idx: int) -> None:
        self.links.append(l_idx)

    def assign_conn(self, ep_idx: int) -> None:
        self.conn.append(ep_idx)

class Link:
    def __init__(self, start: int, end: int, path: list[int], label: int) -> None:
        self.start = start
        self.end = end
        self.path = path
        self.label = None
        self.links = None
        self.conn = None


def skel2graph3d(skel, THR):
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
    skel = skel[:, :, np.newaxis]
    skel = np.pad(skel, pad_width=1, mode='constant')

    # label connected components 
    lm, num_components= label(skel, structure=np.ones((3, 3, 3)))

    skel2 = skel.astype(np.uint16) # needed for labeling nodes etc.

    # all foreground (True) voxels, as flat indices
    list_canal = np.flatnonzero(skel)

    # if image contains no skeletonized data, return empty elements
    if len(list_canal) == 0:
        raise ValueError("No skeletonized data: the input 3D mask contains no foreground voxels.")

    # 26-nh of all canal voxels
    nh = pk_get_nh(skel, list_canal)       # shape: (len(list_canal), 27)

    # 26-nh indices of all canal voxels
    nhi = pk_get_nh_idx(skel, list_canal)  # shape: (len(list_canal), 27)

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
        cans = np.column_stack([cans, can_nb])
    else:
        cans = np.empty((0, 3), dtype=int)

    # group clusters of node voxels to nodes
    node, link = [],[]

    # add node metadata
    tmp = np.zeros(skel.shape, dtype=bool)
    tmp.ravel()[nodes] = True
    labelimg, num_clustered_nodes = label(tmp, structure=np.ones((3,3,3))) # number of unique nodes
    cluster_indices = [np.flatnonzero(labelimg == i) for i in range(1, num_clustered_nodes+1)]

    for i in range(num_clustered_nodes):
        l = lm.flatten()[cluster_indices]
        new_node = node_cluster(cluster_indices[i], 0)
        new_node.find_center_mass(skel.shape)
        new_node.assign_label(lm)
        node.append(new_node)

        # assign index to node voxels in skel2
        id = i + 2
        skel2.ravel()[new_node.nodes_idx] = id

    # add endpoint metadata
    tmp = np.zeros(skel.shape, dtype=bool)
    tmp.ravel()[ep] = True
    labelimg, num_clustered_nodes = label(tmp, structure=np.ones((3,3,3))) # number of unique nodes
    cluster_indices = [np.flatnonzero(labelimg == i) for i in range(1, num_clustered_nodes+1)]


    for i in range(num_clustered_nodes):
        l = lm.flatten()[cluster_indices]
        new_node = node_cluster(cluster_indices[i], 0)
        new_node.find_center_mass(skel.shape)
        new_node.assign_label(lm)
        node.append(new_node)

        # assign index to node voxels in skel2
        id = len(node) + 1
        skel2.ravel()[new_node.nodes_idx] = id

    l_idx = 0

    c2n = np.zeros(skel.shape, dtype=int)
    c2n_flat = c2n.ravel()
    c2n_flat[cans[:, 0]] = np.arange(1, cans.shape[0] + 1)
    c2n = c2n_flat

    s2n = np.zeros(skel.shape, dtype=int)
    s2n[nhi[:, 13]] = np.arange(1, nhi.shape[0] + 1)

    for curr_cluster_node_idx in range(len(node)):
        link_indices = s2n[node[curr_cluster_node_idx].nodes_idx] - 1

        for link_idx in range(len(link_indices)):
            link_cands = nhi[link_indices[link_idx], nh[link_indices[link_idx], :] == 1]

            # short branches with 1 endpoint
            ep_cands = np.intersect1d(link_cands, ep)
            link_cands = link_cands[skel2.ravel()[link_cands] == 1]
            link_cands = np.intersect1d(link_cands, cans[:, 0])

        for can_idx in range(len(link_cands)):
            path, end_cluster_node_idx, ept = pk_follow_link(
                skel2, node, curr_cluster_node_idx, link_idx, link_cands[can_idx], cans, c2n
            )
            # mark seen path 
            skel2.ravel()[path[1:-1]] = 0

            # remove threshold branches
            if (ept and len(path) > THR) or (not ept and curr_cluster_node_idx != end_cluster_node_idx):
                
                # create link structure
                new_link = Link(curr_cluster_node_idx, 
                                end_cluster_node_idx, 
                                path, 
                                lm.ravel()[path[1:-1]])
                
                link.append(new_link)

                # udpate linkage in curr_node  
                curr_node = node[curr_cluster_node_idx]
                curr_node.links.append(l_idx)
                curr_node.conn.append(end_cluster_node_idx)

                # update linkage in end_node
                end_node = node[end_cluster_node_idx]
                end_node.links.append(l_idx)
                end_node.conn.append(curr_cluster_node_idx)

                l_idx += 1
        
        # if short branches are allowed
        if THR == 0:
            for ep_cand_idx in range(len(ep_cands)):
                val = skel2.ravel()[ep_cands[ep_cand_idx]].astype(np.int64) # avoid overflow
                ep_idx = val - 2

                if ep_idx and ep_idx != curr_cluster_node_idx:
                    skel2.ravel()[ep_cands[ep_cand_idx]] = 0
                    new_link = Link(curr_cluster_node_idx,
                                    end_cluster_node_idx,
                                    path,
                                    lm.ravel()[ep_cands[ep_cand_idx]])
                    
                    curr_node = node[curr_cluster_node_idx]
                    curr_node.links.append(l_idx)
                    curr_node.conn.append(end_cluster_node_idx)

                    end_node = node[end_cluster_node_idx]
                    end_node.links.append(l_idx)
                    end_node.conn.append(curr_cluster_node_idx)

                    l_idx += 1
                    
        return node, link