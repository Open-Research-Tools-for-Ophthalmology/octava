import os
import tempfile
import time
import numpy as np
from PIL import Image
from matplotlib import pyplot as plt

def print2array(fig=None, res=1, renderer='agg', gs_options=None):
    """
    Export a matplotlib figure to an RGB image array.

    Parameters
    ----------
    fig : matplotlib.figure.Figure, optional
        Figure handle to export. Defaults to current figure.
    res : float, optional
        Resolution scaling factor. Default is 1 (native size).
    renderer : str, optional
        Renderer for saving figure. Default: 'agg' (matplotlib's raster renderer).
    gs_options : str or list, optional
        Ghostscript options (used if EPS->TIF conversion required).

    Returns
    -------
    A : np.ndarray
        MxNx3 uint8 RGB image.
    bcol : np.ndarray
        1x3 uint8 background RGB color.
    alpha : np.ndarray
        MxN uint8 alpha channel (0=transparent, 255=opaque).
    """

    if fig is None:
        fig = plt.gcf()

    # Force a draw to ensure accurate snapshot
    fig.canvas.draw()
    time.sleep(0.05)  # short pause to avoid cropping issues

    # Get figure size in pixels
    w, h = fig.canvas.get_width_height()

    # Background color
    facecolor = fig.get_facecolor()
    bcol = np.array([int(255*facecolor[0]), int(255*facecolor[1]), int(255*facecolor[2])], dtype=np.uint8)

    try:
        # Fast capture via canvas
        if res == 1:
            A = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8)
            A = A.reshape((h, w, 3))
            alpha = 255 * np.ones((h, w), dtype=np.uint8)
        else:
            # Slow path: save to temp TIFF and read
            tmp_path = tempfile.mktemp(suffix=".tif")
            fig.savefig(tmp_path, dpi=plt.rcParams['figure.dpi']*res, format='tiff', facecolor=facecolor, bbox_inches='tight')
            A = np.array(Image.open(tmp_path))
            alpha = 255 * np.ones(A.shape[:2], dtype=np.uint8)
            os.remove(tmp_path)
    except Exception as e:
        # Fallback: save EPS and convert to TIFF using Ghostscript
        tmp_eps = tempfile.mktemp(suffix=".eps")
        tmp_tif = tempfile.mktemp(suffix=".tif")
        fig.savefig(tmp_eps, dpi=plt.rcParams['figure.dpi']*res, format='eps', facecolor=facecolor, bbox_inches='tight')

        # Construct Ghostscript command
        gs_opts = ''
        if gs_options:
            if isinstance(gs_options, list):
                gs_opts = ' '.join(gs_options)
            else:
                gs_opts = str(gs_options)

        cmd = f"-dEPSCrop -q -dNOPAUSE -dBATCH -r{int(plt.rcParams['figure.dpi']*res)} -sDEVICE=tiff24nc -sOutputFile={tmp_tif} {tmp_eps} {gs_opts}"
        ghostscript(cmd)
        A = np.array(Image.open(tmp_tif))
        alpha = 255 * np.ones(A.shape[:2], dtype=np.uint8)
        os.remove(tmp_eps)
        os.remove(tmp_tif)

    return A, bcol, alpha
