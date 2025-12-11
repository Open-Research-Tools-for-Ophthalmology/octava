"""
Python translation of MATLAB skeletonization code.
Translates the Skel2Graph3D network analysis pipeline.

Author: Translated from MATLAB code by Philip Kollmannsberger
"""

import numpy as np
from scipy import ndimage, sparse
from scipy.ndimage import distance_transform_edt
from skimage.morphology import skeletonize
from skimage.io import imread
from skimage.filters import frangi

import sys
sys.path.append("/home/mutrera/OCTAVA/octava/code/")
from frangi_2dfilter import frangi_2Dfilter
from fuzzy_thresholding import fuzzy_thresholding
from adaptive_thresholding import adaptive_thresholding


# ============================================================================
# Helper Functions for main
# ============================================================================
def center_crop(img, dim):
    """
    Center crop an image (2D NumPy array).

    Parameters:
        img (np.ndarray): Input image (H x W).
        dim (tuple): Desired output size (h, w).

    Returns:
        np.ndarray: Cropped image of size (h, w).
    """
    h, w = img.shape[:2]
    new_h, new_w = dim

    if new_h > h or new_w > w:
        raise ValueError("Crop size must be smaller than the image size")

    top = (h - new_h) // 2
    left = (w - new_w) // 2

    return img[top: top + new_h, left: left + new_w]

def BinarizeImage(Im:np.ndarray, frangi_sigma = 8, frangi_enabled = True, method = "Fuzzy Means") -> np.ndarray:
    """
    Binarizes an image using the selected method and options from the GUI app.

    Parameters:
    - app: GUI application object containing UI state (e.g., checkboxes, dropdowns)
    - Im: Input image as a 2D NumPy array (grayscale)

    Returns:
    - Binarized image as a 2D NumPy array (dtype=float)
    """
    # Find the brightest pixel in the image
    col_max_vals = np.max(Im, axis=0) # the maximum of each column
    cc = np.argmax(col_max_vals) #  gets the index of the column where the brightest value occurred
    rr = np.argmax(Im[:, cc]) # captures the row index of that max value

    #	•	rr: row of the brightest pixel
	#   •	cc: column of the brightest pixel
    #   •	So (rr, cc) is the coordinate of the brightest pixel in the whole image.

    # Apply Frangi filter if selected
    if frangi_enabled:
        opts = {
            'sigmarange': [1, frangi_sigma],
            'sigmastepsize': 2,
            'correctionconst1': 0.8,
            'correctionconst2': 15
        }
        Im = frangi_2Dfilter(Im, opts)

    # Apply the selected binarization method
    if method == 'Fuzzy Means':
        nth = 2
        Im = fuzzy_thresholding(Im, nth, 3) - 1

    elif method == 'Adaptive Thresholding':
        Im = adaptive_thresholding(Im, 70).astype(float)

    else:
        raise ValueError("Incorrect Segmentation Method")

    # Ensure vessels are white, background is black, turning the image into black and white
    vessel_value = Im[rr, cc]
    Im[Im == vessel_value] = 255
    Im[Im != 255] = 0

    return Im

# ============================================================================
# Helper Functions (pk_*)
# ============================================================================

def pk_get_nh_idx(img, i):
    """
    Get 27-neighborhood indices for given voxel positions.
    
    MATLAB equivalent: pk_get_nh_idx.m
    
    Parameters
    ----------
    img : ndarray
        3D binary image
    i : ndarray
        Flat indices of voxels (1D array)
        
    Returns
    -------
    nhood : ndarray
        (N, 27) array of flat neighbor indices for each input voxel
    """
    width, height, depth = img.shape
    
    # Convert flat indices to subscripts (MATLAB's ind2sub)
    # Note: MATLAB is column-major (Fortran order), so we use 'F' order
    x, y, z = np.unravel_index(i, (width, height, depth), order='F')
    
    nhood = np.zeros((len(i), 27), dtype=np.int64)
    
    # Iterate through 3x3x3 neighborhood
    w_idx = 0
    for xx in range(3):
        for yy in range(3):
            for zz in range(3):
                # Offset from center (-1, 0, +1 for each dimension)
                x_offset = x + xx - 1
                y_offset = y + yy - 1
                z_offset = z + zz - 1
                
                # Convert back to flat indices (MATLAB's sub2ind)
                # Use mode='clip' to handle edge cases where offsets go out of bounds
                nhood[:, w_idx] = np.ravel_multi_index(
                    (x_offset, y_offset, z_offset),
                    (width, height, depth),
                    order='F',
                    mode='clip'
                )
                w_idx += 1
    
    return nhood


def pk_get_nh(img, i):
    """
    Get 27-neighborhood values for given voxel positions.
    
    MATLAB equivalent: pk_get_nh.m
    
    Parameters
    ----------
    img : ndarray
        3D binary image
    i : ndarray
        Flat indices of voxels (1D array)
        
    Returns
    -------
    nhood : ndarray
        (N, 27) boolean array of neighbor values for each input voxel
    """
    width, height, depth = img.shape
    
    # Convert flat indices to subscripts
    x, y, z = np.unravel_index(i, (width, height, depth), order='F')
    
    nhood = np.zeros((len(i), 27), dtype=bool)
    
    # Iterate through 3x3x3 neighborhood
    w_idx = 0
    for xx in range(3):
        for yy in range(3):
            for zz in range(3):
                # Offset from center
                x_offset = x + xx - 1
                y_offset = y + yy - 1
                z_offset = z + zz - 1
                
                # Get flat indices for this neighborhood position
                # Use mode='clip' to handle edge cases where offsets go out of bounds
                idx = np.ravel_multi_index(
                    (x_offset, y_offset, z_offset),
                    (width, height, depth),
                    order='F',
                    mode='clip'
                )
                
                # Get values from image using flat indexing
                nhood[:, w_idx] = img.flat[idx]
                w_idx += 1
    
    return nhood


def pk_follow_link(skel, node, k, j, idx, cans, c2n):
    """
    Follow a link from one node to another along canal voxels.
    
    MATLAB equivalent: pk_follow_link.m
    
    Parameters
    ----------
    skel : ndarray
        Labeled skeleton where nodes have values > 1
    node : list of dict
        List of node structures
    k : int
        Starting node index (0-based)
    j : int
        Index of voxel within starting node
    idx : int
        Starting canal voxel flat index
    cans : ndarray
        (N, 3) array: [canal_voxel, neighbor1, neighbor2]
    c2n : ndarray
        Lookup array mapping canal flat index to row in cans
        
    Returns
    -------
    vox : list
        List of flat indices along the link
    n_idx : int
        Destination node index (0-based), or None
    ep : bool
        Whether destination is an endpoint
    """
    vox = []
    n_idx = None
    ep = False
    
    # Start with the node voxel
    vox.append(node[k]['idx'][j])
    
    i = 0
    isdone = False
    
    while not isdone:
        i += 1
        next_cand = c2n[idx]
        
        # Get the candidate next voxel (one of the two neighbors)
        cand = cans[next_cand, 1]  # Index 1 corresponds to column 2 in MATLAB
        
        if cand == vox[i-1]:  # Switch direction if we'd go backwards
            cand = cans[next_cand, 2]  # Index 2 corresponds to column 3 in MATLAB
        
        if skel.flat[cand] > 1:  # Node found (labeled with node_idx + 1)
            vox.append(idx)
            vox.append(cand)
            n_idx = int(skel.flat[cand] - 1)  # Convert back to 0-based index
            
            if node[n_idx]['ep']:
                ep = True
            
            isdone = True
        else:  # Continue to next voxel
            vox.append(idx)
            idx = cand
    
    return vox, n_idx, ep


# ============================================================================
# Core Graph Functions
# ============================================================================

def Graph2Skel3D(node, link, w, l, h):
    """
    Convert graph representation back to binary skeleton image.
    
    MATLAB equivalent: Graph2Skel3D.m
    
    Parameters
    ----------
    node : list of dict
        List of node structures with 'idx' and 'links' keys
    link : list of dict
        List of link structures with 'point' key
    w, l, h : int
        Dimensions of output image
        
    Returns
    -------
    skel : ndarray
        Binary 3D skeleton image
    """
    # Create binary image
    skel = np.zeros((w, l, h), dtype=bool)
    
    # For all nodes
    for i in range(len(node)):
        if node[i]['links'] is not None and len(node[i]['links']) > 0:
            # Set node voxels
            skel.flat[node[i]['idx']] = True
            
            # Get all link indices for this node (only positive links)
            valid_links = [lnk for lnk in node[i]['links'] if lnk > 0]
            
            # Set edge voxels
            if valid_links:
                for link_idx in valid_links:
                    if link[link_idx]['point'] is not None:
                        skel.flat[link[link_idx]['point']] = True
    
    return skel


def Skel2Graph3D(skel, THR):
    """
    Calculate the network graph of a 3D voxel skeleton.
    
    MATLAB equivalent: Skel2Graph3D.m
    Based on code by Philip Kollmannsberger
    
    Parameters
    ----------
    skel : ndarray
        3D binary skeleton image
    THR : int
        Threshold for minimum length of branches
        
    Returns
    -------
    A : sparse matrix
        Adjacency matrix
    node : list of dict
        Node structures containing position, connections, and properties
    link : list of dict
        Link structures containing endpoints and voxel positions
    """
    # Pad volume with zeros (adds 1-pixel border on all sides)
    skel = np.pad(skel, pad_width=1, mode='constant', constant_values=0)
    
    # Create label matrix for different skeletons (connected components)
    labeled_skel, num_components = ndimage.label(skel, structure=np.ones((3, 3, 3)))
    lm = labeled_skel
    
    # Image dimensions
    w, l, h = skel.shape
    
    # Need this for labeling nodes etc.
    skel2 = skel.astype(np.uint16)
    
    # All foreground voxels (MATLAB's find)
    list_canal = np.flatnonzero(skel)
    
    # 26-nh of all canal voxels
    nh = pk_get_nh(skel, list_canal).astype(bool)
    
    # 26-nh indices of all canal voxels
    nhi = pk_get_nh_idx(skel, list_canal)
    
    # Number of neighbors of each skel voxel (MATLAB: sum + 1 for center)
    sum_nh = np.sum(nh, axis=1)
    
    # All canal voxels with >2 neighbors are nodes
    nodes = list_canal[sum_nh > 3]
    
    # All canal voxels with exactly one neighbor are end nodes
    ep = list_canal[sum_nh == 2]
    
    # All canal voxels with exactly 2 neighbors are canal voxels
    cans = list_canal[sum_nh == 3]
    
    # Get neighborhood info for canal voxels
    can_nh_idx = pk_get_nh_idx(skel, cans)
    can_nh = pk_get_nh(skel, cans)
    
    # Remove center of 3x3x3 cube (index 13 in 0-based, 14 in 1-based MATLAB)
    can_nh_idx = np.delete(can_nh_idx, 13, axis=1)
    can_nh = np.delete(can_nh, 13, axis=1)
    
    # Keep only the two existing foreground voxels
    # Sort so that True values (neighbors) come last
    can_nb = np.sort(can_nh.astype(bool) * can_nh_idx, axis=1)
    
    # Keep only last 2 columns (the two neighbors)
    can_nb = can_nb[:, -2:]
    
    # Add neighbors to canalicular voxel list
    cans = np.column_stack([cans, can_nb])
    
    # Group clusters of node voxels to nodes
    node = []
    link = []
    
    # Label node voxels
    tmp = np.zeros((w, l, h), dtype=bool)
    tmp.flat[nodes] = True
    labeled_nodes, num_realnodes = ndimage.label(tmp, structure=np.ones((3, 3, 3)))
    
    # Create node structures for junction nodes
    for i in range(num_realnodes):
        node_idx = np.flatnonzero(labeled_nodes == (i + 1))
        x, y, z = np.unravel_index(node_idx, (w, l, h), order='F')
        
        node.append({
            'idx': node_idx,
            'links': [],
            'conn': [],
            'comx': np.mean(x),
            'comy': np.mean(y),
            'comz': np.mean(z),
            'ep': 0,
            'label': lm.flat[node_idx[0]]
        })
        
        # Assign index to node voxels (1-based for compatibility with pk_follow_link)
        skel2.flat[node_idx] = i + 2  # +2 because 0=background, 1=unlabeled skeleton
    
    # Label endpoint voxels
    tmp = np.zeros((w, l, h), dtype=bool)
    tmp.flat[ep] = True
    labeled_ep, num_ep = ndimage.label(tmp, structure=np.ones((3, 3, 3)))
    
    # Create node structures for endpoints
    for i in range(num_ep):
        ni = num_realnodes + i
        ep_idx = np.flatnonzero(labeled_ep == (i + 1))
        x, y, z = np.unravel_index(ep_idx, (w, l, h), order='F')
        
        node.append({
            'idx': ep_idx,
            'links': [],
            'conn': [],
            'comx': np.mean(x),
            'comy': np.mean(y),
            'comz': np.mean(z),
            'ep': 1,
            'label': lm.flat[ep_idx[0]]
        })
        
        # Assign index to node voxels
        skel2.flat[ep_idx] = ni + 2
    
    l_idx = 0  # Link counter
    
    # Create lookup arrays
    c2n = np.zeros(w * l * h, dtype=np.int64)
    if len(cans) > 0:
        c2n[cans[:, 0]] = np.arange(len(cans))
    
    s2n = np.zeros(w * l * h, dtype=np.int64)
    s2n[nhi[:, 13]] = np.arange(len(nhi))  # Center voxel is at index 13
    
    # Visit all nodes
    for i in range(len(node)):
        # Find all canal voxels in neighborhood of all node voxels
        link_idx = s2n[node[i]['idx']]
        
        for j in range(len(link_idx)):
            # Visit all voxels of this node
            
            # All potential unvisited links emanating from this voxel
            neighbors_mask = nh[link_idx[j], :] == 1
            link_cands = nhi[link_idx[j], neighbors_mask]
            
            # Short branches that only have an endpoint
            ep_cands = np.intersect1d(link_cands, ep)
            
            # Filter for unvisited canal voxels
            link_cands = link_cands[skel2.flat[link_cands] == 1]
            link_cands = np.intersect1d(link_cands, cans[:, 0])
            
            for k in range(len(link_cands)):
                vox, n_idx, ept = pk_follow_link(skel2, node, i, j, link_cands[k], cans, c2n)
                
                # Mark visited voxels (except endpoints)
                if len(vox) > 2:
                    skel2.flat[vox[1:-1]] = 0
                
                # Add link if it meets criteria
                if (ept and len(vox) > THR) or (not ept and i != n_idx):
                    link.append({
                        'n1': i,
                        'n2': n_idx,
                        'point': np.array(vox),
                        'label': lm.flat[vox[0]]
                    })
                    
                    node[i]['links'].append(l_idx)
                    node[i]['conn'].append(n_idx)
                    node[n_idx]['links'].append(l_idx)
                    node[n_idx]['conn'].append(i)
                    l_idx += 1
            
            # Handle short endpoint branches if THR == 0
            if THR == 0:
                for k in range(len(ep_cands)):
                    n_idx_val = skel2.flat[ep_cands[k]] - 1
                    if n_idx_val > 0 and n_idx_val - 1 != i:
                        n_idx = int(n_idx_val - 1)
                        skel2.flat[ep_cands[k]] = 0
                        
                        link.append({
                            'n1': i,
                            'n2': n_idx,
                            'point': np.array([ep_cands[k]]),
                            'label': lm.flat[ep_cands[k]]
                        })
                        
                        node[i]['links'].append(l_idx)
                        node[i]['conn'].append(n_idx)
                        node[n_idx]['links'].append(l_idx)
                        node[n_idx]['conn'].append(i)
                        l_idx += 1
    
    # Mark all 1-nodes as end points
    if len(node) > 0:
        for i in range(len(node)):
            if len(node[i]['links']) == 1:
                node[i]['ep'] = 1
    
    # Number of nodes
    n_nodes = len(node)
    
    # Initialize adjacency matrix
    A = np.zeros((n_nodes, n_nodes))
    
    # Build adjacency matrix
    for i in range(n_nodes):
        for j in range(len(node[i]['links'])):
            link_idx = node[i]['links'][j]
            if link_idx >= 0 and link_idx < len(link):
                link_len = len(link[link_idx]['point'])
                
                if i == link[link_idx]['n1']:
                    n2 = link[link_idx]['n2']
                    A[i, n2] = link_len
                    A[n2, i] = link_len
                    
                if i == link[link_idx]['n2']:
                    n1 = link[link_idx]['n1']
                    A[i, n1] = link_len
                    A[n1, i] = link_len
    
    # Convert to sparse matrix
    A = sparse.csr_matrix(A)
    
    # Transform all voxel indices back to non-padded coordinates
    for i in range(len(node)):
        x, y, z = np.unravel_index(node[i]['idx'], (w, l, h), order='F')
        node[i]['idx'] = np.ravel_multi_index((x - 1, y - 1, z - 1), (w - 2, l - 2, h - 2), order='F')
        node[i]['comx'] -= 1
        node[i]['comy'] -= 1
        node[i]['comz'] -= 1
    
    # Transform all link voxel indices back to non-padded coordinates
    for i in range(len(link)):
        x, y, z = np.unravel_index(link[i]['point'], (w, l, h), order='F')
        link[i]['point'] = np.ravel_multi_index((x - 1, y - 1, z - 1), (w - 2, l - 2, h - 2), order='F')
    
    # Handle empty case
    if len(node) == 0:
        node = [{
            'idx': np.array([]),
            'links': [],
            'conn': [],
            'comx': np.array([]),
            'comy': np.array([]),
            'comz': np.array([]),
            'ep': np.array([]),
            'label': np.array([])
        }]
    
    return A, node, link


# ============================================================================
# Main Skeletonization Function
# ============================================================================

def prune_skeleton_branches(skel, min_branch_length):
    """
    Remove branches shorter than min_branch_length from skeleton.
    
    This mimics MATLAB's bwskel with MinBranchLength parameter.
    
    Parameters
    ----------
    skel : ndarray
        Binary skeleton image
    min_branch_length : int
        Minimum length for branches to keep
        
    Returns
    -------
    pruned_skel : ndarray
        Skeleton with short branches removed
    """
    if min_branch_length == 0:
        return skel
    
    # Convert to graph to identify branches
    _, nodes, links = Skel2Graph3D(skel, 0)  # THR=0 to get all branches
    
    if len(nodes) == 0 or len(links) == 0:
        return skel
    
    # Identify branches to keep (longer than threshold)
    valid_links = []
    for i, link in enumerate(links):
        if len(link['point']) >= min_branch_length:
            valid_links.append(i)
    
    # If no valid links, return empty skeleton
    if len(valid_links) == 0:
        return np.zeros_like(skel, dtype=bool)
    
    # Filter links and update node connections
    new_links = [links[i] for i in valid_links]
    
    # Update node structures to only reference valid links
    link_mapping = {old_idx: new_idx for new_idx, old_idx in enumerate(valid_links)}
    
    for node in nodes:
        new_node_links = []
        new_node_conn = []
        for j, link_idx in enumerate(node['links']):
            if link_idx in link_mapping:
                new_node_links.append(link_mapping[link_idx])
                new_node_conn.append(node['conn'][j])
        node['links'] = new_node_links
        node['conn'] = new_node_conn
    
    # Reconstruct skeleton from filtered graph
    w, l, h = skel.shape
    pruned_skel = Graph2Skel3D(nodes, new_links, w, l, h)
    
    return pruned_skel


def skeletonize_main(input_image, bin_img, twig_size):
    """
    Main skeletonization pipeline with network analysis.
    
    MATLAB equivalent: skeletonize() method in main app
    
    Parameters
    ----------
    input_image : ndarray
        Grayscale input image (2D)
    bin_img : ndarray
        Binary image to skeletonize (2D)
    twig_size : int
        Minimum branch length threshold
        
    Returns
    -------
    sk2 : ndarray
        Skeletonized binary image (2D)
    nodes : list of dict
        Node structures from graph analysis
    links : list of dict
        Link structures with computed metrics
    distance_map : ndarray
        Local thickness map (2D)
    """
    # Get image dimensions
    Nx, Ny = bin_img.shape
    
    # Convert to logical/boolean
    L = bin_img.astype(bool)
    
    # Initial skeletonization using scikit-image
    # Note: Need to handle 3D by adding singleton dimension
    L_3d = L[:, :, np.newaxis]
    sk2_3d = skeletonize(L_3d)
    sk2 = sk2_3d[:, :, 0]
    
    # Remove branches smaller than twig size
    sk2_3d = sk2[:, :, np.newaxis]
    sk2_3d = prune_skeleton_branches(sk2_3d, twig_size)
    sk2 = sk2_3d[:, :, 0]
    
    img_skel = sk2.copy()
    
    # Local thickness measurement
    # Distance transform gives Euclidean distance to nearest background pixel
    # Multiply by 2 since distance transform gives radius, not diameter
    D = distance_transform_edt(L) * 2
    
    # Network analysis
    # Convert 2D skeleton to 3D for Skel2Graph3D (add singleton z dimension)
    skel_3d = img_skel[:, :, np.newaxis]
    
    if np.sum(img_skel) == 0:
        nodes = []
        links = []
    else:
        _, nodes, links = Skel2Graph3D(skel_3d, twig_size)
        
        # Calculate total length of network
        if len(nodes) > 0:
            wl = sum(len(node['links']) for node in nodes)
            
            # Iterate to clean up network and get rid of excess nodes
            skel2_3d = Graph2Skel3D(nodes, links, Nx, Ny, 1)
            _, nodes, links = Skel2Graph3D(skel2_3d, 0)
            wl_new = sum(len(node['links']) for node in nodes)
            
            # Iterate the same steps until network length changed by less than 0.5%
            while wl_new != wl:
                wl = wl_new
                
                skel2_3d = Graph2Skel3D(nodes, links, Nx, Ny, 1)
                _, nodes, links = Skel2Graph3D(skel2_3d, 0)
                
                wl_new = sum(len(node['links']) for node in nodes)
    
    # Add parameters to links structure for calculating metrics
    for i in range(len(links)):
        # Convert flat indices to 2D coordinates
        # Note: indices are in 3D space (Nx, Ny, 1), need to convert to 2D
        x_3d, y_3d, z_3d = np.unravel_index(links[i]['point'], (Nx, Ny, 1), order='F')
        
        links[i]['x'] = x_3d
        links[i]['y'] = y_3d
        
        # Calculate pixel length (path length along the branch)
        if len(links[i]['x']) > 1:
            d = np.diff(np.column_stack([links[i]['y'], links[i]['x']]), axis=0)
            links[i]['pixLength'] = np.sum(np.sqrt(np.sum(d * d, axis=1)))
        else:
            links[i]['pixLength'] = 0
        
        # Calculate end-to-end length (straight-line distance)
        if len(links[i]['x']) > 0:
            links[i]['end2endLength'] = np.sqrt(
                (links[i]['x'][-1] - links[i]['x'][0])**2 + 
                (links[i]['y'][-1] - links[i]['y'][0])**2
            )
        else:
            links[i]['end2endLength'] = 0
        
        # Calculate tortuosity (ratio of path length to straight distance)
        if links[i]['end2endLength'] > 0:
            links[i]['tortuosity'] = links[i]['pixLength'] / links[i]['end2endLength']
        else:
            links[i]['tortuosity'] = 1.0
        
        # Get diameter measurements at each point within the link
        # Convert 3D indices back to 2D for diameter lookup
        idx_2d = np.ravel_multi_index((x_3d, y_3d), (Nx, Ny), order='F')
        links[i]['diameterMeasurements'] = D.flat[idx_2d]
        
        # Mean diameter for the link
        links[i]['diameter'] = np.mean(links[i]['diameterMeasurements'])
    
    return sk2, nodes, links, D


if __name__ == "__main__":
    # Load image
    octa_path = "octava/assets/MIPs/10301.bmp"
    img = imread(octa_path, as_gray=True).astype(np.float32)

    # Frangi vessel enhancement
    vessels = frangi(
        img,
        scale_range=(0.5, 4),
        scale_step=0.5,
        alpha=0.5,
        beta=0.5,
        gamma=4,
        black_ridges=False
    )

    # Binarize
    adpt_mask = BinarizeImage(vessels, frangi_sigma=8, frangi_enabled=False,
                              method="Adaptive Thresholding")

    # Crop
    adpt_mask_cropped = center_crop(adpt_mask, dim=(200, 200))

    # Skeletonize
    nodes, links = skeletonize_main(img, adpt_mask, twig_size=0)


