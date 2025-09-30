import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

def cartoonifyPatch(patch, ax):
    # Bail out if patch is invisible
    if not patch.get_visible():
        return False

    # Save original data for undo (as attributes on patch)
    patch._xkcd_backup = {
        'verts': np.array(patch.get_xy()),
        'facecolor': patch.get_facecolor(),
        'edgecolor': patch.get_edgecolor(),
        'linewidth': patch.get_linewidth(),
        'face_vertex_cdata': getattr(patch, '_face_vertex_cdata', None),
        'vertex_normals': getattr(patch, '_vertex_normals', None),
    }

    # The original vertices
    verts = patch.get_xy()
    nOld = verts.shape[0]

    # Parameters for jittering
    nPixOffset = 6
    pixPerX, pixPerY = getPixelsPerUnit(ax)
    xJitter = nPixOffset / pixPerX
    yJitter = nPixOffset / pixPerY

    # Upsample and jitter vertices
    xPts = verts[:, 0]
    yPts = verts[:, 1]
    xNew, yNew = upSampleAndJitter(xPts, yPts, xJitter, yJitter)

    # Ensure first and last vertex stay the same for closed polygon
    xNew[0], yNew[0] = xPts[0], yPts[0]
    xNew[-1], yNew[-1] = xPts[-1], yPts[-1]

    newVerts = np.column_stack([xNew, yNew])

    # Set new vertices to patch
    patch.set_xy(newVerts)

    # Optionally modify face color or edge color if you want
    # For simplicity, just keep them as is.

    # Store face vertex color data and vertex normals on patch for undo
    # (You can add these as custom attributes)
    patch._face_vertex_cdata = patch._xkcd_backup['face_vertex_cdata']  # no change here
    patch._vertex_normals = patch._xkcd_backup['vertex_normals']        # no change here

    # Add a translucent background mask (simple shadow)
    addBackgroundMask(newVerts, ax)

    return True

def undoCartoonifyPatch(patch):
    if hasattr(patch, '_xkcd_backup'):
        backup = patch._xkcd_backup
        patch.set_xy(backup['verts'])
        patch.set_facecolor(backup['facecolor'])
        patch.set_edgecolor(backup['edgecolor'])
        patch.set_linewidth(backup['linewidth'])
        # Restore saved custom properties
        patch._face_vertex_cdata = backup.get('face_vertex_cdata', None)
        patch._vertex_normals = backup.get('vertex_normals', None)
        patch.figure.canvas.draw_idle()  # Redraw the figure
        return True
    return False

def getPixelsPerUnit(ax):
    # Calculate pixels per data unit in x and y directions
    fig = ax.figure
    bbox = ax.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
    width_inch, height_inch = bbox.width, bbox.height
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    pixPerX = fig.dpi * width_inch / abs(xlim[1] - xlim[0])
    pixPerY = fig.dpi * height_inch / abs(ylim[1] - ylim[0])
    return pixPerX, pixPerY

def upSampleAndJitter(x, y, xJitter, yJitter, jitter=True):
    # Simple upsampling: linearly interpolate between points to double resolution
    n = len(x)
    new_n = 2 * n - 1
    x_new = np.empty(new_n)
    y_new = np.empty(new_n)

    x_new[0::2] = x
    y_new[0::2] = y
    x_new[1::2] = (x[:-1] + x[1:]) / 2
    y_new[1::2] = (y[:-1] + y[1:]) / 2

    if jitter:
        # Add jitter to midpoints only
        jitter_x = (np.random.rand(n - 1) - 0.5) * 2 * xJitter
        jitter_y = (np.random.rand(n - 1) - 0.5) * 2 * yJitter
        x_new[1::2] += jitter_x
        y_new[1::2] += jitter_y

    return x_new, y_new

def addBackgroundMask(verts, ax):
    # Simple translucent shadow behind patch
    shadow_offset = 0.02
    shadow_verts = verts + shadow_offset

    shadow_patch = Polygon(shadow_verts, closed=True, facecolor='gray', alpha=0.2, zorder=patch.get_zorder()-1)
    ax.add_patch(shadow_patch)
    ax.figure.canvas.draw_idle()