import matplotlib.pyplot as plt
import numpy as np
import re
import warnings
import os

def print2eps(filename, fig=None, export_options=None, *print_options):
    """
    Prints figures to EPS with improved line styles, font fixes, and optional cropping/padding.

    Args:
        filename (str): Output EPS file name (extension added automatically if missing)
        fig (matplotlib.figure.Figure, optional): Figure to save. Defaults to current figure.
        export_options (dict or list, optional): Options for padding, cropping, font swapping, etc.
        *print_options: Additional options passed to `savefig` (e.g., dpi, format)
    """

    # Use current figure if none provided
    if fig is None:
        fig = plt.gcf()
    
    # Default options
    bb_padding = 0
    bb_crop = False
    fontswap = True
    preserve_size = False
    font_space = ''
    renderer = 'agg'  # Use non-GUI backend for EPS
    crop_amounts = [np.nan]*4

    # Parse export_options
    if export_options is not None:
        if isinstance(export_options, dict):
            bb_padding = export_options.get('bb_padding', bb_padding)
            bb_crop = export_options.get('crop', bb_crop)
            fontswap = export_options.get('fontswap', fontswap)
            preserve_size = export_options.get('preserve_size', preserve_size)
            font_space = export_options.get('font_space', font_space)
            renderer = export_options.get('rendererStr', renderer)
            crop_amounts = export_options.get('crop_amounts', crop_amounts)
            regexprep = export_options.get('regexprep', None)
        elif isinstance(export_options, (list, tuple)):
            if len(export_options) > 0: bb_padding = export_options[0]
            if len(export_options) > 1: bb_crop = export_options[1]
            if len(export_options) > 2: fontswap = export_options[2]
            if len(export_options) > 3: preserve_size = export_options[3]
        else:
            raise ValueError("export_options must be dict or list/tuple")

    # Ensure filename ends with .eps
    if not filename.lower().endswith('.eps'):
        filename += '.eps'

    # --- Font handling ---
    if fontswap:
        for ax in fig.get_axes():
            for label in ax.get_xticklabels() + ax.get_yticklabels() + [ax.title, ax.xaxis.label, ax.yaxis.label]:
                if label.get_fontname() not in ['Helvetica', 'Times', 'Courier']:
                    fontname = label.get_fontname().replace(' ', font_space)
                    label.set_fontname(fontname)

    # --- Workarounds for line width / color issues ---
    for line in fig.findobj(match=plt.Line2D):
        # Fix white lines slightly off
        if np.all(line.get_color() == [1,1,1]):
            line.set_color([1,1,1-1e-5])
        # Fix thin lines in HG2-style
        if line.get_linewidth() < 0.75:
            line.set_linewidth(1.0)

    # --- Transparency handling ---
    stored_colors = eps_maintainAlpha(fig)

    # --- Render figure to EPS ---
    fig.savefig(filename, format='eps', dpi=300, bbox_inches='tight', **{k:v for k,v in print_options})

    # --- Post-process EPS file ---
    try:
        with open(filename, 'r') as f:
            fstrm = f.read()
    except Exception as e:
        warnings.warn(f"Failed to load EPS file: {e}")
        fstrm = ''

    # Restore transparency
    if stored_colors:
        fstrm = eps_maintainAlpha(fig, fstrm, stored_colors)

    # Apply regex replacement if requested
    if export_options and isinstance(export_options, dict) and 'regexprep' in export_options:
        old_str, new_str = export_options['regexprep']
        fstrm = re.sub(old_str, new_str, fstrm)

    # Write back the EPS
    if fstrm:
        with open(filename, 'w') as f:
            f.write(fstrm)

    # Optional: preserve figure size in EPS (Python's savefig already does tight bbox)
    if preserve_size:
        warnings.warn("Preserve size functionality is limited in Python backend; using tight bbox.")

    # Pause to ensure rendering finishes
    plt.pause(0.01)


# --- Placeholder functions ---
def eps_maintainAlpha(fig, fstrm=None, stored_colors=None):
    """
    Convert transparency to unique RGB colors in figure or restore in EPS string.
    """
    if fstrm is None:
        # Collect transparent colors
        stored_colors = []
        for patch in fig.findobj(match=plt.Patch):
            fc = patch.get_facecolor()
            if len(fc) == 4 and fc[3] < 1.0:
                new_color = (0.4, 0.4, 0.4, 1.0)  # dummy unique color
                stored_colors.append((patch, fc, new_color))
                patch.set_facecolor(new_color)
        return stored_colors
    else:
        # Restore EPS colors
        for patch, orig, newc in stored_colors:
            # Replace RGB in EPS string (simplified)
            old_str = f"{newc[0]} {newc[1]} {newc[2]} RC"
            new_str = f"{orig[0]} {orig[1]} {orig[2]} RC"
            fstrm = fstrm.replace(old_str, new_str)
        return fstrm

