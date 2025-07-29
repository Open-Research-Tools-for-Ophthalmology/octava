import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from Graph2Skel3D import skel2graph3d, graph2skel3d

# ---- 1. Load your binary skeleton image ----
# You must load your own data, e.g.:
# skel = np.load('skel.npy')  # Should be a 3D binary numpy array
# Or, if you have a MATLAB .mat file, use:
# from scipy.io import loadmat
# mat = loadmat('skel.mat')
# skel = mat['skel']

# For demonstration purposes, let's suppose 'skel' is defined:
# skel = ...

w, l, h = skel.shape

# ---- 2. Initial skeleton-to-graph conversion (condensation) ----
_, node, link = skel2graph3d(skel, 0)

# ---- 3. Compute total network length ----
wl = sum([len(n['links']) for n in node])

# ---- 4. Convert back to voxel skeleton ----
skel2 = graph2skel3d(node, link, w, l, h)
_, node2, link2 = skel2graph3d(skel2, 0)

# Compute new total network length
wl_new = sum([len(n['links']) for n in node2])

# ---- 5. Iterate until network length changes < 0.5% ----
while wl_new != wl:
    wl = wl_new
    skel2 = graph2skel3d(node2, link2, w, l, h)
    _, node2, link2 = skel2graph3d(skel2, 0)
    wl_new = sum([len(n['links']) for n in node2])

# ---- 6. Visualization: plot the graph in 3D using matplotlib ----
fig = plt.figure(figsize=(14, 10))
ax = fig.add_subplot(111, projection='3d')
ax.set_aspect('auto')
ax.set_axis_off()

for n in node2:
    x1, y1, z1 = n['comx'], n['comy'], n['comz']
    ncol = 'cyan' if n['ep'] == 1 else 'yellow'
    for j, link_idx in enumerate(n['links']):
        other_ep = node2[n['conn'][j]]['ep']
        # Branches: black, links: red
        col = 'k' if n['ep'] == 1 or other_ep == 1 else 'r'
        lnk = link2[link_idx]
        points = lnk['point']
        if len(points) > 1:
            # Draw as line segments through all link points
            idxs = np.unravel_index(points, (w, l, h))
            for k in range(len(points) - 1):
                x3, y3, z3 = idxs[0][k], idxs[1][k], idxs[2][k]
                x2, y2, z2 = idxs[0][k + 1], idxs[1][k + 1], idxs[2][k + 1]
                ax.plot([y3, y2], [x3, x2], [z3, z2], color=col, linewidth=2)
    # Draw nodes as circles
    ax.scatter(y1, x1, z1, s=32, c=ncol, edgecolors='k')

# Set proper axes and view similar to MATLAB
ax.set_box_aspect([l, w, h])
ax.view_init(elev=46, azim=-17)
plt.gca().invert_yaxis()  # Similar to set(gca, 'YDir','reverse')
plt.show()