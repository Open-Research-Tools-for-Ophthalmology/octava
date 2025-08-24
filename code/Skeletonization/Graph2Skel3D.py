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
    skel = np.zeros((w, l, h), dtype=bool)
    
    for node in nodes:
        if node['links']:  # node has links
            skel[node['idx']] = True  # set node voxels
            
            # collect all edge voxels connected to this node
            a = []
            for link_idx in node['links']:
                if link_idx >= 0:
                    a.extend(links[link_idx]['point'])
            if a:
                skel[a] = True  # set edge voxels
    
    return skel
