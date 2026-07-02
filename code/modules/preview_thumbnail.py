"""
Adds scroll-to-zoom and drag-to-pan behaviour to to main GUI's four thumbnail image 
"""

from PIL import Image, ImageTk
import numpy as np
from scipy.ndimage import binary_dilation

# Size (px) at which each thumbnail is rendered inside its box
THUMB_DISPLAY_SIZE = 200

ONH_VIEW_TO_KEY = {
    "Overall": "overall",
    "Large Vessels": "large",
    "Small Vessels": "small",
}

def init_thumbnail_zoom_pan(canvas, thumbnail_cfg, thumb_boxes):
    """Wire up cursor, zoom, and pan behaviour for all thumbnail boxes."""

    # Per-thumbnail mutable state
    thumb_state = {
        key: {"zoom": 1.0, "pan_x": 0.0, "pan_y": 0.0, "drag_x": 0, "drag_y": 0}
        for key in thumbnail_cfg
    }
    # Expose on canvas so display modules can reset state on new image load
    canvas.thumbnail_state = thumb_state
    canvas._active_thumb = None

    #  helper functions
    def get_base_pil(key):
        """Return the base PIL image for this thumbnail, or None if not loaded."""
        cfg = thumbnail_cfg[key].copy()

        # Special Prebinary cases
        img_type = canvas.img_type_var.get()
        prebinary_var = canvas.prebinary_var.get()
        if prebinary_var == 1 and key == "binarised":
            cfg["base_attr"] = "original_img"

        # Special ONH cases
        # Original: display raw image if not being masked yet, and display ring mask if available
        if img_type == "ONH" and key == "original" and hasattr(canvas, "onh_mask_img"):
            cfg["base_attr"] = "onh_mask_img"
        # Binarised: display either overall/large/small depending on selection
        if img_type == "ONH" and key == "binarised":
            segmentation_view = canvas.onh_segmentation_view_var.get()
            print(f"ONH binarised thumbnail, checking segmentation view... {segmentation_view}")

            if hasattr(canvas, f"onh_binary_{ONH_VIEW_TO_KEY[segmentation_view]}"): # If have segmentation view: image already processed, use seg view
                cfg["base_attr"] = f"onh_binary_{ONH_VIEW_TO_KEY[segmentation_view]}"
            elif prebinary_var == 1: # If no segmentation view, display onh_mask or original if prebinary is toggled on
                cfg["base_attr"] = "onh_mask_img" if hasattr(canvas, "onh_mask_img") else "original_img"
        # skeletonisation: display either overall/large/small depending on selection
        if img_type == "ONH" and key == "skeletonised":
            segmentation_view = canvas.onh_segmentation_view_var.get()
            print(f"ONH skeletonised thumbnail, checking segmentation view... {segmentation_view}")
            cfg["base_attr"] = f"onh_skeleton_{ONH_VIEW_TO_KEY[segmentation_view]}"

        raw = getattr(canvas, cfg["base_attr"], None)
        if raw is None:
            return None
        img_id = cfg["img_id_attr"]
        if img_id == "original_img_id":
            return Image.fromarray(raw) # already in 8-bit
        elif img_id == "binary_img_id":
            return Image.fromarray(raw.astype("uint8"))
        elif img_id == "skeleton_img_id":
            # Same display logic as skeleonisation to dilate vessels thicker
            skel_uint8 = binary_dilation(raw, iterations=1).astype(np.uint8) * 255
            return Image.fromarray(skel_uint8, mode="L")
            # return Image.fromarray((raw * 255).astype("uint8"), mode="L")
        elif img_id == "faz_img_id":
            return raw
        return None

    def redraw(key):
        """Re-render a thumbnail at its current zoom / pan state."""
        cfg  = thumbnail_cfg[key]
        st   = thumb_state[key]
        base = get_base_pil(key)
        if base is None:
            print(f"No base image for thumbnail {key}, skipping redraw.")
            return

        bw, bh = base.size
        if bw == 0 or bh == 0:
            return

        # Viewport size in base-image pixels
        vw = bw / st["zoom"]
        vh = bh / st["zoom"]

        # Centre of viewport in base-image coordinates
        cx = bw / 2.0 + st["pan_x"]
        cy = bh / 2.0 + st["pan_y"]

        # Clamp so viewport never leaves the image
        cx = max(vw / 2.0, min(bw - vw / 2.0, cx))
        cy = max(vh / 2.0, min(bh - vh / 2.0, cy))
        st["pan_x"] = cx - bw / 2.0
        st["pan_y"] = cy - bh / 2.0

        x1 = max(0, int(cx - vw / 2.0))
        y1 = max(0, int(cy - vh / 2.0))
        x2 = min(bw, int(cx + vw / 2.0))
        y2 = min(bh, int(cy + vh / 2.0))

        cropped = base.crop((x1, y1, x2, y2))
        display  = cropped.resize((THUMB_DISPLAY_SIZE, THUMB_DISPLAY_SIZE), Image.LANCZOS)
        img_tk   = ImageTk.PhotoImage(display)

        img_id_attr = cfg["img_id_attr"]
        if hasattr(canvas, img_id_attr):
            canvas.itemconfigure(getattr(canvas, img_id_attr), image=img_tk)
        if not hasattr(canvas, "_image_refs"):
            canvas._image_refs = {}
        canvas._image_refs[key + "_zoom"] = img_tk   # prevent garbage collection

    # event handlers for a specific thumbnail
    def scroll(key, event):
        st = thumb_state[key]
        zoom_in = (event.num == 4) or (getattr(event, "delta", 0) > 0)
        if zoom_in:
            st["zoom"] = min(st["zoom"] * 1.1, 10.0)
        else:
            st["zoom"] = max(st["zoom"] / 1.1, 1.0)
            if st["zoom"] <= 1.0:
                st["pan_x"] = 0.0
                st["pan_y"] = 0.0
        redraw(key)

    def drag_start(key, event):
        st = thumb_state[key]
        st["drag_x"] = event.x
        st["drag_y"] = event.y

    def drag_move(key, event):
        st   = thumb_state[key]
        base = get_base_pil(key)
        if base is None:
            return
        dx = event.x - st["drag_x"]
        dy = event.y - st["drag_y"]
        st["drag_x"] = event.x
        st["drag_y"] = event.y
        # Convert screen-pixel delta → base-image-pixel delta
        scale = base.size[0] / (st["zoom"] * THUMB_DISPLAY_SIZE)
        st["pan_x"] -= dx * scale
        st["pan_y"] -= dy * scale
        redraw(key)

    # canvas-level event handlers
    def get_thumb_at(x, y):
        for key, (bx1, by1, bx2, by2) in thumb_boxes.items():
            if bx1 <= x <= bx2 and by1 <= y <= by2:
                return key
        return None

    def on_motion(event):
        key = get_thumb_at(event.x, event.y)
        if key is not None:
            canvas.configure(cursor="fleur")
            canvas._active_thumb = key
        else:
            canvas.configure(cursor="")
            canvas._active_thumb = None

    def ondrag_start(event):
        if canvas._active_thumb is not None:
            drag_start(canvas._active_thumb, event)

    def ondrag_move(event):
        if canvas._active_thumb is not None:
            drag_move(canvas._active_thumb, event)

    def on_scroll(event):
        if canvas._active_thumb is not None:
            scroll(canvas._active_thumb, event)

    canvas.bind("<Motion>", on_motion)
    canvas.bind("<ButtonPress-1>", ondrag_start)
    canvas.bind("<B1-Motion>", ondrag_move)
    canvas.bind("<MouseWheel>", on_scroll)
