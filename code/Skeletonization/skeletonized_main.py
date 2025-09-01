import os
import numpy as np
from skimage.morphology import skeletonize, thin
from skimage.morphology import remove_small_objects
from skimage.io import imread, imsave
from scipy.ndimage import distance_transform_edt
import matplotlib.pyplot as plt

def skeletonize_image(app, bin_img, folder, disp=True):
    # Find existing skeleton files
    list_files = [f for f in os.listdir(folder) if '_Skeleton' in f and f.endswith('.tif')]
    imgnum = len(list_files)

    Nx = app.inputImage.shape[0]
    
    # Skeletonize
    L = bin_img.astype(bool)
    sk2 = skeletonize(L)  # basic 2D skeletonization
    
    # Remove small branches (approximation of bwskel 'MinBranchLength')
    sk2 = remove_small_objects(sk2, min_size=app.TwigsizeSpinner.Value)
    app.imgSkel = sk2

    TifFileName = None
    if disp:
        # Prepare display
        sk2_disp = thin(sk2)  # thicken approximation
        fig, ax = plt.subplots()
        ax.imshow(app.inputImage * 0.75 + 10, cmap='gray')
        ax.imshow(sk2_disp * 255, alpha=0.5, cmap='hot')
        ax.axis('off')
        TifFileName = os.path.join(folder, f"{app.FileLabelName}_Skeleton_{imgnum}.tif")
        plt.savefig(TifFileName, bbox_inches='tight')
        plt.close(fig)

    # Local thickness (approximate with distance transform)
    D = distance_transform_edt(L) * 2
    if disp:
        pngFileName = os.path.join(folder, f"{app.FileLabelName}_Local_thickness_{imgnum}.png")
        D_output = (D / D.max() * 255).astype(np.uint8)
        imsave(pngFileName, D_output)

    # Network analysis
    if sk2.sum() == 0:
        nodes = []
        links = []
    else:
        # These functions need to be implemented in Python
        _, nodes, links = Skel2Graph3D(sk2, app.TwigsizeSpinner.Value)
        wl = sum(len(n['links']) for n in nodes)
        
        skel2 = Graph2Skel3D(nodes, links, Nx, Nx, 1)
        _, nodes, links = Skel2Graph3D(skel2, 0)
        wl_new = sum(len(n['links']) for n in nodes)
        
        while wl_new != wl:
            wl = wl_new
            skel2 = Graph2Skel3D(nodes, links, Nx, Nx, 1)
            _, nodes, links = Skel2Graph3D(skel2, 0)
            wl_new = sum(len(n['links']) for n in nodes)
    
    app.Gnodes = nodes
    app.Glinks = links

    # Add parameters to links
    for link in app.Glinks:
        y, x = np.unravel_index(link['point'], (Nx, Nx))
        link['x'] = x
        link['y'] = y
        d = np.diff(np.column_stack([y, x]), axis=0)
        link['pixLength'] = np.sum(np.sqrt(np.sum(d**2, axis=1)))
        link['end2endLength'] = np.sqrt((x[-1]-x[0])**2 + (y[-1]-y[0])**2)
        link['tortuosity'] = link['pixLength'] / link['end2endLength']
        link['diameterMeasurements'] = D[link['point']]
        link['diameter'] = np.mean(link['diameterMeasurements'])

    if disp:
        # Visualization
        fig, ax = plt.subplots()
        ax.imshow(app.inputImage, cmap='gray')
        for i, node in enumerate(nodes):
            x1, y1 = node['comx'], node['comy']
            for j, link_idx in enumerate(node['links']):
                link = app.Glinks[link_idx]
                ax.plot(link['y'], link['x'], 'y', linewidth=2)
            ax.plot(y1, x1, 'mo', markersize=4)
        ax.axis('off')
        overlay_file = os.path.join(folder, f"{app.FileLabelName}_Overlay_{imgnum}.tif")
        plt.savefig(overlay_file, bbox_inches='tight')
        plt.close(fig)
    
    return sk2, TifFileName
