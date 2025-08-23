import numpy as np

def graph2skel3d(node, link, w, l, h):
    """
    Create a 3D binary skeleton from node and link structures. Similar to the original
    skeletonized image, but now network is clean

    Inputs
        node [list[dict[Any, Any]]]: list of node structures containing 'idx' and 'links'.
        link [list[dict[Any, Any]]]: list of link structures containing 'point'.
        w, l, h [int]: dimensions of the 3D skeletonized image

    Return [np.ndarray]: 3D boolean array representing the reconstructed skeleton.
    """
    # create binary image
    skel = np.zeros((w, l, h), dtype=bool)

    # for all nodes
    for n in node:
        if n['links']:  # if node has links
            skel.flat[n['idx']] = True  # node voxels
            # collect all points from its links
            pts = []
            for li in n['links']:
                print("\n\n\n")
                print("Type of li: ", type(li))
                print("Type of link: ", type(link)) # list of dictionaries
                print("This is link: ", link)
                print("Type of link[li]: ", type(link[li])) # should be a dictionary
                print("This is link[li]: ", link[li])
                print("type of link[li]['point']: ", type(link[li]['point']))
                if li >= 0:
                    pts.extend(link[li]['point'])
            if pts:
                skel.flat[np.array(pts)] = True  # edge voxels

    return skel