import matplotlib.pyplot as plt
import copy

def isolate_axes(axes, vis=False):
    """
    Isolate the specified axes in a new figure, along with legends/colorbars.

    Parameters
    ----------
    axes : list of matplotlib.axes.Axes
        Axes to isolate. Must all come from the same figure.
    vis : bool, optional
        Whether the new figure should be visible. Default False.

    Returns
    -------
    fig : matplotlib.figure.Figure
        New figure containing only the specified axes.
    """
    if not isinstance(axes, (list, tuple)):
        axes = [axes]

    # Ensure all axes are from the same figure
    parent_figs = {ax.figure for ax in axes}
    if len(parent_figs) != 1:
        raise ValueError("All axes must come from the same figure.")
    src_fig = parent_figs.pop()

    # Create new figure
    fig = plt.figure()
    if not vis:
        plt.close(fig)  # hide if vis=False, keep handle alive

    new_axes = []
    for ax in axes:
        # Copy position and create new axes
        pos = ax.get_position()
        new_ax = fig.add_axes(pos)
        
        # Copy contents of the original axes
        for line in ax.get_lines():
            new_ax._add_line(copy.copy(line))
        for im in ax.get_images():
            new_ax.imshow(im.get_array(),
                          cmap=im.get_cmap(),
                          norm=im.norm,
                          extent=im.get_extent(),
                          origin=im.origin,
                          aspect=im.get_aspect())
        for coll in ax.collections:
            new_ax.add_collection(copy.copy(coll))
        for patch in ax.patches:
            new_ax.add_patch(copy.copy(patch))
        for text in ax.texts:
            new_ax.text(text.get_position()[0], text.get_position()[1],
                        text.get_text(), transform=new_ax.transData)

        # Copy labels, title, limits, scale
        new_ax.set_title(ax.get_title())
        new_ax.set_xlabel(ax.get_xlabel())
        new_ax.set_ylabel(ax.get_ylabel())
        new_ax.set_xlim(ax.get_xlim())
        new_ax.set_ylim(ax.get_ylim())
        new_ax.set_xscale(ax.get_xscale())
        new_ax.set_yscale(ax.get_yscale())

        # Copy legend if present
        leg = ax.get_legend()
        if leg is not None:
            handles, labels = ax.get_legend_handles_labels()
            new_ax.legend(handles, labels, loc=leg._loc)

        new_axes.append(new_ax)

    return fig
