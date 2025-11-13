import numpy as np

def graph2skel3d(nodes, links, w, l, h):
    """
    Create a 3D binary skeleton from node and link structures. Similar to the original
    skeletonized image, but now network is clean

    Inputs
        node [list[dict[Any, Any]]]: list of node structures containing 'idx' and 'links'.
        link [list[dict[Any, Any]]]: list of link structures containing 'point'.
        w, l, h [int]: dimensions of the 3D skeletonized image

    Return [np.ndarray]: 3D boolean array representing the reconstructed skeleton.
    """
    # I will create the 3D skel exaclty as we do in skel2graph
    # I will create the 2D np.ndarray, then add the additional dimension, then pad
    skel = np.zeros((w, l), dtype=bool)
    skel = skel[:, :, np.newaxis]
    skel = np.pad(skel, pad_width=1, mode='constant')

    # for all nodes
    for n in nodes:
        if n.links:  # if node has links
            skel.flat[n.nodes_idx] = True  # node voxels
            # collect all points from its links
            pts = []
            for li in n.links:
                if li >= 0:
                    pts.extend(links[li].path)
            if pts:
                skel.flat[np.array(pts)] = True  # edge voxels
                # how do we know that the points are going to be set in the z = 1 dimension though?

    return skel
