# from typing import Any
# import numpy as np
# from scipy import sparse
# from scipy.ndimage import label
# from pk_functions import pk_get_nh, pk_get_nh_idx, pk_follow_link
# import math

# class node_cluster:
#     def __init__(self, nodes_idx: list[int], ep: int):
#         self.nodes_idx = nodes_idx
#         self.links = []
#         self.conn = [] # list of indices (w respect to the node list) of all endpoint node voxels (connections)
#         self.ep = ep
#         self.comx = None
#         self.comy = None
#         self.comz = None
#         self.label = None

#     def find_center_mass(self, skel_dim: tuple[int, int, int]) -> None:
#         x, y, z = np.unravel_index(self.nodes_idx, skel_dim)
#         self.comx = np.mean(x)
#         self.comy = np.mean(y)
#         self.comz = np.mean(z)
    
#     def assign_label(self, lm: np.ndarray):
#         self.label = lm.ravel()[self.nodes_idx[0]]

#     def assign_links(self, l_idx: int) -> None:
#         self.links.append(l_idx)

#     def assign_conn(self, ep_idx: int) -> None:
#         self.conn.append(ep_idx)

#     def __str__(self):
#         return (
#             f"node_cluster(\n"
#             f"  nodes_idx: {self.nodes_idx}\n"
#             f"  links: {self.links}\n"
#             f"  conn: {self.conn}\n"
#             f"  ep: {self.ep}\n"
#             f"  comx: {self.comx}\n"
#             f"  comy: {self.comy}\n"
#             f"  comz: {self.comz}\n"
#             f"  label: {self.label}\n"
#             f")"
#         )

# class Link:
#     def __init__(self, start: int, end: int, path: list[int], label: int) -> None:
#         self.start = start
#         self.end = end
#         self.path = path
#         self.label = label

#         # geometry along skeleton
#         self.x = None               
#         self.y = None               
#         self.dir_vectors = None
            
#         # lengths
#         self.pixlength = None       
#         self.end2end_length = None

#         # measurements
#         self.tortuosity = None
#         self.diameter_measurements = None
#         self.diameter = None

#     def compute_dir_vectors(self, img_y: list[int], img_x: list[int]) -> None:
#         ''' 
#         Assign x and y coordinates for each point in the link
#         '''
#         x, y = np.unravel_index(self.path, (img_y, img_x))
#         self.x = x
#         self.y = y

#         coords = np.vstack((y, x))  # (2, N)
#         d = np.diff(coords, axis=1).T  # (N-1, 2) → [dy, dx]
#         self.dir_vectors = d

#     def compute_pixlength(self):
#         # Length of branch in pixels
#         pixLength = np.linalg.norm(self.dir_vectors, axis=1).sum()
#         self.pixlength = pixLength
    
#     def compute_end2endlength(self):
#         self.end2end_length = np.sqrt(
#             (self.x[-1] - self.x[0])**2 + (self.y[-1] - self.y[0])**2
#         )
    
#     def compute_tortuosity(self):
#         if self.end2end_length == 0:
#             self.tortuosity = np.inf  # same behavior as MATLAB
#         else:
#             self.tortuosity = self.pixlength / self.end2end_length

#     def compute_diameter_measurements(self, D: np.ndarray):
#         self.diameter_measurements = D.flat[self.path]

#     def compute_diameter(self):
#         self.diameter = float(np.mean(self.diameter_measurements))

#     def __str__(self):
#         return (
#             f"Link(\n"
#             f"  start: {self.start}\n"
#             f"  end: {self.end}\n"
#             f"  path: {self.path}\n"
#             f"  label: {self.label}\n"
#             f")"
#         )


# #############################
# ##### Helper functions  #####
# #############################

# def unpad_indices(indices, padded_shape):
#     ''' 
#     Convert linear indices defined with respect to a padded 3D skeletonized image 
#     into equivalent indices for the original unpadded 2D skeletonized image.

#     This function is useful when the skeleton was padded (e.g., by 1 voxel on all sides)
#     during processing — such as when using `skel2graph3d` — and you need to map voxel 
#     indices back to the original unpadded image coordinates.

#     Inputs
#     indices : array_like of int
#         Linear indices corresponding to voxels in the padded 3D skeleton array.
#     padded_shape : tuple of int
#         Shape of the padded 3D skeleton array (e.g., `(w, l, h)`).

#     Returns
#     np.ndarray of int
#         Linear indices corresponding to the same voxels, but expressed with respect 
#         to the unpadded skeleton array (i.e., with 1 voxel border removed along each axis).
#     '''
#     unpadded_shape = (padded_shape[0] - 2, padded_shape[1] - 2, padded_shape[2] - 2)
#     x, y, z = np.unravel_index(indices, padded_shape) # get all x, y, z coordinates of all linear indices that are wrt 3D skel
#     x, y, z = x - 1, y - 1, z - 1
#     valid = (
#         (x >= 0) & (x < unpadded_shape[0]) &
#         (y >= 0) & (y < unpadded_shape[1]) &
#         (z >= 0) & (z < unpadded_shape[2])
#     )

#     # check if any of the linear indices that are wrt to the 3D space are for some reason 
#     # out of bound for when moved to the 2D space (they shouldn't because 3D is just padding, no info should be lost!)
#     if not np.all(valid):
#         invalid_coords = np.column_stack([x[~valid], y[~valid], z[~valid]])
#         raise ValueError(
#             f"Some coordinates are out of bounds after unpadding:\n"
#             f"{invalid_coords[:10]}...\n"
#             f"Unpadded shape: {unpadded_shape}\n"
#             f"Total invalid: {np.sum(~valid)}"
#         )

#     x, y, z = x[valid], y[valid], z[valid]
#     return np.ravel_multi_index((x, y, z), unpadded_shape)


# def compute_link_metrics(links, D, skel_shape):
#     """
#     Replicates the MATLAB code:

#         [x, y, ~] = ind2sub([Nx,Nx,1], point)
#         d = diff([y', x'])
#         pixLength = sum(sqrt(sum(d.*d,2)))
#         end2endLength = sqrt((x(end)-x(1))^2 + (y(end)-y(1))^2)
#         tortuosity = pixLength / end2endLength
#         diameterMeasurements = D(point)
#         diameter = mean(diameterMeasurements)

#     Parameters
#     ----------
#     links : list of Link objects
#     D : ndarray
#         Diameter / distance transform image (same size as skeleton).
#     skel_shape : tuple
#         Shape of the skeleton (e.g. (Nx, Ny, Nz) or (Nx, Ny)).
#     """

#     for link in links:

#         # -----------------------------------------
#         # 1. Convert linear indices → (x, y) coords
#         # -----------------------------------------
#         coords = np.unravel_index(link.path, skel_shape)  
#         # coords = (x, y) or (x, y, z)
#         x = coords[0]
#         y = coords[1]

#         link.x = x
#         link.y = y

#         # -----------------------------------------
#         # 2. Compute pixel-by-pixel differences
#         # MATLAB: d = diff([y', x'])
#         # -----------------------------------------
#         # Stack as rows then diff down the columns:
#         #   [y0, y1, y2 ...]
#         #   [x0, x1, x2 ...]
#         mat = np.vstack((y, x))            # shape = (2, N)
#         d = np.diff(mat, axis=1).T         # shape = (N-1, 2), rows = [dy dx]

#         # -----------------------------------------
#         # 3. Pixel length (sum of Euclidean distances)
#         # -----------------------------------------
#         link.pixLength = np.linalg.norm(d, axis=1).sum()

#         # -----------------------------------------
#         # 4. End-to-end ("arc") length
#         # -----------------------------------------
#         dx = x[-1] - x[0]
#         dy = y[-1] - y[0]
#         link.end2endLength = np.sqrt(dx * dx + dy * dy)

#         # -----------------------------------------
#         # 5. Tortuosity
#         # -----------------------------------------
#         if link.end2endLength == 0:
#             link.tortuosity = np.inf  # avoid divide-by-zero
#         else:
#             link.tortuosity = link.pixLength / link.end2endLength

#         # -----------------------------------------
#         # 6. Diameter measurements at each voxel
#         # MATLAB: D(link(i).point)
#         # -----------------------------------------
#         link.diameterMeasurements = D.ravel()[link.path]
#         link.diameter = float(np.mean(link.diameterMeasurements))



# def skel2graph3d(skel, thr = 0):
#     """
#     Converts a 2D or 3D binary skeletonized image into a graph representation, 
#     where nodes correspond to branch points or endpoints, and links correspond 
#     to canal (segment) connections between them.

#     Inputs:
#         - skel [np.ndarray]: 2D or 3D binary array representing a skeletonized structure.
#         Nonzero voxels represent the skeleton. The input will be automatically padded 
#         and expanded to 3D if 2D.
#         - thr [int, optional]: minimum link length threshold (in voxels). 
#         Links shorter than `thr` are removed unless they connect two distinct nodes.
#         Default is 0 (keeps all links, including short terminal branches).

#     Process overview:
#         1. Labels connected components in the skeletonized image.
#         2. Identifies voxels as:
#             - nodes: branch points (more than 2 neighbors)
#             - endpoints: terminal points (1 neighbor)
#             - canals: segment voxels (2 neighbors)
#         3. Groups adjacent node voxels into node clusters and computes each cluster's
#         center of mass and component label.
#         4. Follows canal voxels to build link connections between node clusters.
#         5. Constructs `node_cluster` and `Link` objects for the full graph representation.

#     Returns:
#         - node [list[node_cluster]]: list of node clusters, each representing a unique 
#         branching point or endpoint in the skeleton. Each node_cluster includes:
#             - .nodes_idx: linear indices of voxels in that node cluster
#             - .center: center-of-mass coordinates
#             - .ep: 1 if endpoint, 0 otherwise
#             - .conn: indices of connected nodes
#             - .links: indices of connecting links
#         - link [list[Link]]: list of Link objects connecting nodes. Each link contains:
#             - .n1, .n2: indices of the connected nodes
#             - .path: linear voxel indices forming the link
#             - .label: label of the connected component from the input skeleton

#     Raises:
#         - ValueError: if the input skeleton contains no foreground voxels.
#     """
#     # Add third dimension if missing and pad array
#     if skel.ndim == 2:
#         skel = skel[:, :, np.newaxis]
    
#     skel = np.pad(skel, pad_width=1, mode='constant')
#     # label connected components 
#     lm, num_components= label(skel, structure=np.ones((3, 3, 3)))

#     skel2 = skel.astype(np.uint16) # needed for labeling nodes etc.

#     # all foreground (True) voxels, as flat indices
#     list_canal = np.flatnonzero(skel)

#     # if image contains no skeletonized data, return empty elements
#     if len(list_canal) == 0:
#         raise ValueError("No skeletonized data: the input 3D mask contains no foreground voxels.")

#     # 26-nh of all canal voxels
#     nh = pk_get_nh(skel, list_canal)       # shape: (len(list_canal), 27)

#     # 26-nh indices of all canal voxels
#     nhi = pk_get_nh_idx(skel, list_canal)  # shape: (len(list_canal), 27)

#     # num of 26-nb of each skel voxel + 1
#     sum_nh = np.sum(nh.astype(bool), axis=1)

#     # node/endpoint/canal assignment
#     nodes = list_canal[sum_nh > 3] # all canal voxels with >2 nb are nodes -> branching points
#     ep    = list_canal[sum_nh == 2] # all canal voxels with exactly one nb are end nodes -> endpoints
#     cans  = list_canal[sum_nh == 3] # all canal voxels with exactly 2 nb -> segments

#     # Nx3 matrix with the 2 neighbors of each canal voxel
#     if cans.size > 0:
#         can_nh_idx = pk_get_nh_idx(skel, cans)
#         can_nh = pk_get_nh(skel, cans)

#         # remove center of 3x3 cube
#         can_nh_idx = np.delete(can_nh_idx, 13, axis=1)
#         can_nh = np.delete(can_nh, 13, axis=1)

#         # keep only the two existing foreground voxels
#         can_nb = np.sort(can_nh * can_nh_idx, axis=1)
#         can_nb = can_nb[:, -2:]  # keep last two columns

#         # add neighbours to canalicular voxel list (this might include nodes)
#         cans = np.column_stack([cans, can_nb])
#     else:
#         cans = np.empty((0, 3), dtype=int)


#     # group clusters of node voxels to nodes
#     node, link = [],[]

#     # add node metadata
#     tmp = np.zeros(skel.shape, dtype=bool)
#     tmp.ravel()[nodes] = True
#     labelimg, num_clustered_nodes = label(tmp, structure=np.ones((3,3,3))) # number of unique nodes
#     cluster_indices = [np.flatnonzero(labelimg == i) for i in range(1, num_clustered_nodes+1)]

#     # create cluster nodes 
#     for i in range(num_clustered_nodes):
#         l = lm.flatten()[cluster_indices[i]] # I want to know the lin_idx of the voxels that constitute this cluster node!
#         new_node = node_cluster(cluster_indices[i], 0)
#         new_node.find_center_mass(skel.shape)
#         new_node.assign_label(lm)
#         node.append(new_node)

#         # assign index to node voxels in skel2
#         id = i + 2
#         skel2.ravel()[new_node.nodes_idx] = id

#     # add endpoint metadata
#     tmp = np.zeros(skel.shape, dtype=bool)
#     tmp.ravel()[ep] = True
#     labelimg, num_endpoints = label(tmp, structure=np.ones((3,3,3))) # number of unique nodes
#     cluster_indices = [np.flatnonzero(labelimg == i) for i in range(1, num_endpoints+1)]


#     for i in range(num_endpoints):
#         l = lm.flatten()[cluster_indices[i]]
#         new_node = node_cluster(cluster_indices[i], 1)
#         new_node.find_center_mass(skel.shape)
#         new_node.assign_label(lm)
#         node.append(new_node)

#         # assign index to node voxels in skel2
#         id = len(node) + 1
#         skel2.ravel()[new_node.nodes_idx] = id

#     l_idx = 0

#     c2n = np.zeros(skel.shape, dtype=int)
#     c2n_flat = c2n.ravel()
#     c2n_flat[cans[:, 0]] = np.arange(1, cans.shape[0] + 1)
#     c2n = c2n_flat

#     s2n = np.zeros(skel.shape, dtype=int)
#     s2n_flat = s2n.ravel()
#     s2n_flat[nhi[:, 13]] = np.arange(1, nhi.shape[0] + 1)
#     s2n = s2n_flat

#     for curr_cluster_node_idx in range(len(node)):
#         link_indices = s2n[node[curr_cluster_node_idx].nodes_idx] - 1

#         for link_idx in range(len(link_indices)):
#             link_cands = nhi[link_indices[link_idx], nh[link_indices[link_idx], :] == 1]

#             # short branches with 1 endpoint
#             ep_cands = np.intersect1d(link_cands, ep)
#             link_cands = link_cands[skel2.ravel()[link_cands] == 1]
#             link_cands = np.intersect1d(link_cands, cans[:, 0])

#             for can_idx in range(len(link_cands)):
#                 path, end_cluster_node_idx, ept = pk_follow_link(
#                     skel2, node, curr_cluster_node_idx, link_idx, link_cands[can_idx], cans, c2n
#                 )
#                 # mark seen path 
#                 skel2.ravel()[path[1:-1]] = 0

#                 # remove threshold branches
#                 if (ept and len(path) > thr) or (not ept and curr_cluster_node_idx != end_cluster_node_idx):
#                     # create link structure
#                     assert isinstance(path, list), (
#                         f"Start node: {node[curr_cluster_node_idx]} \n"
#                         f"End node: {node[end_cluster_node_idx]} \n"
#                         f"Normal loop"
#                     )
#                     new_link = Link(curr_cluster_node_idx, 
#                                 end_cluster_node_idx, 
#                                 path, 
#                                 lm.ravel()[path[0]])
                    
#                     link.append(new_link)

#                     # udpate linkage in curr_node  
#                     curr_node = node[curr_cluster_node_idx]
#                     curr_node.links.append(l_idx)
#                     curr_node.conn.append(end_cluster_node_idx)

#                     # update linkage in end_node
#                     end_node = node[end_cluster_node_idx]
#                     end_node.links.append(l_idx)
#                     end_node.conn.append(curr_cluster_node_idx)

#                     l_idx += 1
            
#             # if short branches are allowed
#             if thr == 0:
#                 for ep_cand_idx in range(len(ep_cands)):
#                     val = skel2.ravel()[ep_cands[ep_cand_idx]].astype(np.int64) # avoid overflow
#                     ep_idx = val - 2
#                     ep_idx = max(ep_idx, 0)

#                     if ep_idx and ep_idx != curr_cluster_node_idx:
#                         skel2.ravel()[ep_cands[ep_cand_idx]] = 0
#                         path = [ep_cands[ep_cand_idx]]
#                         assert isinstance(path, list), (
#                             f"Start node: {node[curr_cluster_node_idx]} \n"
#                             f"End node: {node[ep_idx]} \n"
#                             f"THR == 0 loop"
#                         )
#                         new_link = Link(
#                             curr_cluster_node_idx,
#                             ep_idx,
#                             path,
#                             np.asarray(lm.ravel()[ep_cands[ep_cand_idx]]).item()
#                         )
#                         link.append(new_link)
                                        
#                         curr_node = node[curr_cluster_node_idx]
#                         curr_node.links.append(l_idx)
#                         curr_node.conn.append(ep_idx)

#                         end_node = node[ep_idx]
#                         end_node.links.append(l_idx)
#                         end_node.conn.append(curr_cluster_node_idx)

#                         l_idx += 1

#     if len(node) > 0:
#         # indices of nodes that have exactly one link
#         ep_idx = [i for i, n in enumerate(node) if len(n.links) == 1]

#         # mark them as endpoints
#         for i in ep_idx:
#             node[i].ep = 1

        
#     # transform linear indices s.t they are represented wrt the 2D skeletonized image as 
#     # opposed to the 3D skeletonized padded image
#     for n in node:
#         n.nodes_idx = unpad_indices(np.array(n.nodes_idx), skel.shape)

#     for lnk in link:
#         lnk.path = unpad_indices(np.array(lnk.path), skel.shape)

#     return node, link

import numpy as np
from scipy.ndimage import label
from pk_functions import pk_get_nh, pk_get_nh_idx, pk_follow_link


##############################################
# node_cluster and Link classes unchanged
##############################################

class node_cluster:
    def __init__(self, nodes_idx: list[int], ep: int):
        self.nodes_idx = nodes_idx
        self.links = []
        self.conn = []
        self.ep = ep
        self.comx = None
        self.comy = None
        self.comz = None
        self.label = None

    def find_center_mass(self, skel_dim):
        x, y, z = np.unravel_index(self.nodes_idx, skel_dim)
        self.comx = np.mean(x)
        self.comy = np.mean(y)
        self.comz = np.mean(z)

    def assign_label(self, lm):
        self.label = lm.ravel()[self.nodes_idx[0]]

    def __str__(self):
        return f"node_cluster(nodes={self.nodes_idx}, links={self.links}, conn={self.conn}, ep={self.ep})"


class Link:
    def __init__(self, start, end, path, label):
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
            ep_cands = candidates[np.isin(candidates, ep)]

            # only voxels still marked 1 in skel2 and in canal list
            cand_mask = (skel2_flat[candidates] == 1)
            candidates = candidates[cand_mask]
            if candidates.size == 0:
                continue

            candidates = candidates[np.isin(candidates, cans[:, 0])]

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