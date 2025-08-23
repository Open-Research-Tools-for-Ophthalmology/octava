# I WILL COMPILE ALL THE FUNCTIONALITY RELATED TO SKELETONIZATION HERE
import glob
import os
from tkinter import messagebox

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from matplotlib import cm
from scipy.ndimage import distance_transform_edt
from skan import Skeleton, csr
from skimage import img_as_ubyte
from skimage.io import imread, imsave
from skimage.morphology import (
    dilation,
    remove_small_objects,
    skeletonize,
    skeletonize_3d,
    square,
)

# Local imports (if any) would go here
from Skel2Graph3D import skel2graph3d


def skeletonize_button_pushed(app, event=None):
    ''' 
    Skeletonization main function
    '''
    # 1. Initial checks
    if not app.skelReady:
        if app.inputImage is None:
            messagebox.showwarning("Warning", "You did not choose an image file")
        else:
            messagebox.showwarning("Warning", "Binary mask required for skeletonization")
    else:
        app.ReadyLabel.text = 'Wait'   # sets wait label
        app.ReadyLamp.color = (1, 0, 0) # RGB for red
        plt.pause(0.01)

        # 2. Setup output folder
        fol = os.path.join(app.SaveFolder, 'images')
        if not os.path.exists(fol):
            os.makedirs(fol)

        # 3. Skeletonize
        sk2, ovrlyFileName = skeletonize_py(app, app.BinaryImage, fol, 1)
        
        # 4. Display skeleton overlay on original image
        ax = app.SkelImageAxes
        ax.clear()
        base_img = app.inputImage * 3 / 4 + 10
        ax.imshow(base_img.astype('uint8'), cmap=app.bin_overlay)
        ax.imshow(img_as_ubyte(sk2), cmap='gray', alpha=0.5)
        ax.figure.canvas.draw_idle()

        # 5. Load saved overlay image and display
        ovrly = imread(ovrlyFileName)
        app.OverlayImageAxes.clear()
        app.OverlayImageAxes.imshow(ovrly)
        app.OverlayImageAxes.figure.canvas.draw_idle()

        # 6. Update labels and state
        app.ReadyLabel.text = 'Ready'
        app.ReadyLamp.color = (0, 1, 0) # RGB for green
        plt.pause(0.01)
        app.skelReady = 3


def skeletonize_py(app, bin_img, fol, disp):
    ''' 
    Skeletonization main function
    '''
    # Find number of already saved skeleton files
    skeleton_files = glob.glob(os.path.join(fol, '*_Skeleton*.tif'))
    imgnum = len(skeleton_files)

    # Generate skeletonized image
    Nx = app.inputImage.shape[0]
    L = bin_img.astype(bool)
    sk2 = skeletonize(L)

    # Removes "branches" smaller than twig size (note: component-based, not true branches)
    sk2 = remove_small_objects(sk2, min_size=int(app.TwigsizeSpinner.value))
    app.imgSkel = sk2

    TifFileName = None

    if disp == 1:
        # Prepare display and save skeleton image
        sk2_vis = dilation(sk2, square(3))  # thicken
        fig, ax = plt.subplots(figsize=(10, 10))
        base_img = app.inputImage * 3 / 4 + 10
        ax.imshow(base_img.astype('uint8'), cmap=app.bin_overlay)
        ax.imshow(sk2_vis * 255, cmap='gray', alpha=0.5)
        ax.set_axis_off()
        ax.invert_yaxis()
        fig.tight_layout()
        TifFileName = os.path.join(fol, f"{app.FileLabelName}_Skeleton_{imgnum}.tif")
        fig.savefig(TifFileName, dpi=150, bbox_inches='tight', pad_inches=0)
        plt.close(fig)

    # Local thickness measurement
    D = distance_transform_edt(L) * 2  # Similar to MATLAB's bwdist(~L)*2
    if disp == 1:
        D_output = (D / D.max()) * 255
        pngFileName = os.path.join(fol, f"{app.FileLabelName}_Local_thickness_{imgnum}.png")
        imsave(pngFileName, D_output.astype(np.uint8), cmap=cm.hot)

    # Network analysis
    if np.sum(app.imgSkel) == 0:
        nodes = []
        links = []
    else:
        _, nodes, links = skel2graph3d(app.imgSkel, int(app.TwigsizeSpinner.value))

        # Calculate total length of network
        wl = sum([len(link) for link in nodes['links']])

        # Iterate to clean up network and get rid of excess nodes
        skel2 = Graph2Skel3D(nodes, links, Nx, Nx, 1)
        _, nodes, links = skel2graph3d(skel2, 0)
        wl_new = sum([len(link) for link in nodes['links']])

        # Iterate until network length changes by less than 0.5%
        while wl_new != wl:
            wl = wl_new
            skel2 = Graph2Skel3D(nodes, links, Nx, Nx, 1)
            _, nodes, links = skel2graph3d(skel2, 0)
            wl_new = sum([len(link) for link in nodes['links']])

    app.Gnodes = nodes
    app.Glinks = links

    # Add parameters to links
    for i in range(len(app.Glinks)):
        # x, y, z coords for each point on link
        x, y, z = np.unravel_index(app.Glinks[i]['point'], (Nx, Nx, 1))
        app.Glinks[i]['x'] = x
        app.Glinks[i]['y'] = y

        d = np.diff(np.vstack((app.Glinks[i]['y'], app.Glinks[i]['x'])).T, axis=0)
        app.Glinks[i]['pixLength'] = np.sum(np.sqrt(np.sum(d * d, axis=1)))
        app.Glinks[i]['end2endLength'] = np.sqrt((app.Glinks[i]['x'][-1] - app.Glinks[i]['x'][0])**2 +
                                                 (app.Glinks[i]['y'][-1] - app.Glinks[i]['y'][0])**2)
        app.Glinks[i]['tortuosity'] = app.Glinks[i]['pixLength'] / app.Glinks[i]['end2endLength']
        app.Glinks[i]['diameterMeasurements'] = D.take(app.Glinks[i]['point'])
        app.Glinks[i]['diameter'] = np.mean(app.Glinks[i]['diameterMeasurements'])

    if disp == 1:
        # Display result - full graph structure in its own window
        fig, ax = plt.subplots(figsize=(10, 10))
        ax.imshow(app.inputImage.astype('uint8'), cmap='gray')
        ax.set_axis_off()
        ax.invert_yaxis()
        fig.tight_layout()

        for i in range(len(nodes)):
            x1 = nodes[i]['comx']
            y1 = nodes[i]['comy']
            z1 = nodes[i]['comz']

            for j in range(len(nodes[i]['links'])):
                # Color selection logic
                col = 'black'
                if nodes[nodes[i]['conn'][j]]['ep'] == 1:
                    col = 'green'
                else:
                    col = 'yellow'
                if nodes[i]['ep'] == 1:
                    col = 'green'
                if nodes[nodes[i]['conn'][j]]['ep'] == 1 and nodes[i]['ep'] == 1:
                    col = 'blue'
                # Draw edges
                ax.plot(app.Glinks[nodes[i]['links'][j]]['y'],
                        app.Glinks[nodes[i]['links'][j]]['x'],
                        color=col, linewidth=2)

            if nodes[i]['ep'] == 1:
                ncol = 'cyan'
            else:
                ncol = 'magenta'

            ax.plot(y1, x1, 'o', markersize=4, markerfacecolor=ncol, color='k')

        ax.axis('image')
        ax.axis('off')
        fig.canvas.draw()
        fig.set_size_inches(fig.get_size_inches()[0] * 5,
                            fig.get_size_inches()[1] * 5)
        # Save as tif
        TifFileName = os.path.join(fol, f"{app.FileLabelName}_Overlay_{imgnum}.tif")
        fig.savefig(TifFileName, dpi=150, bbox_inches='tight', pad_inches=0)
        plt.close(fig)

    return sk2, TifFileName