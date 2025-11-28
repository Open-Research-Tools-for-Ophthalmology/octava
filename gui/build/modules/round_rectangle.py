
def round_rectangle(canvas, x1, y1, width, height, radius=16, fill="#EFEFEF", outline="#EFEFEF"):
    """
    Draw a rounded rectangle on a Tkinter Canvas.

    (x1, y1) = top-left corner, (x2, y2) = bottom-right corner.
    radius   = corner radius in pixels.

    kwargs are passed to create_ methods (e.g., fill="blue", outline="black").
    """
    x2 = x1 + width
    y2 = y1 + height
    if radius > (x2 - x1) / 2:
        radius = (x2 - x1) / 2
    if radius > (y2 - y1) / 2:
        radius = (y2 - y1) / 2

    # Corners
    canvas.create_arc(x1, y1, x1 + 2*radius, y1 + 2*radius,
                      start=90, extent=90, style="pieslice", fill=fill, outline=outline)
    canvas.create_arc(x2 - 2*radius, y1, x2, y1 + 2*radius,
                      start=0, extent=90, style="pieslice", fill=fill, outline=outline)
    canvas.create_arc(x2 - 2*radius, y2 - 2*radius, x2, y2,
                      start=270, extent=90, style="pieslice", fill=fill, outline=outline)
    canvas.create_arc(x1, y2 - 2*radius, x1 + 2*radius, y2,
                      start=180, extent=90, style="pieslice", fill=fill, outline=outline)

    # Edges
    canvas.create_rectangle(x1 + radius, y1, x2 - radius, y2, fill=fill, outline=outline)
    canvas.create_rectangle(x1, y1 + radius, x2, y2 - radius, fill=fill, outline=outline)