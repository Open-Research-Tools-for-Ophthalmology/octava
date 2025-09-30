import matplotlib.pyplot as plt
import tempfile
import os

def copyfig(fig=None):
    """
    Create a copy of a Matplotlib figure without changing the original.
    
    Parameters:
        fig : matplotlib.figure.Figure or None
            The figure to copy. Defaults to current figure.
    
    Returns:
        new_fig : matplotlib.figure.Figure
            The copied figure.
    """
    if fig is None:
        fig = plt.gcf()

    try:
        # Save to a temporary file
        tmp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        tmp_file.close()
        
        # Save the figure as PNG (raster format)
        fig.savefig(tmp_file.name)
        
        # Create a new figure and load the saved image as a background
        new_fig, new_ax = plt.subplots()
        img = plt.imread(tmp_file.name)
        new_ax.imshow(img)
        new_ax.axis('off')  # Hide axes since it's an image copy
        
        # Cleanup temporary file
        os.unlink(tmp_file.name)

        return new_fig

    except Exception as e:
        print(f"Warning: Could not copy figure properly: {e}")
        # Fallback: return original figure
        return fig
