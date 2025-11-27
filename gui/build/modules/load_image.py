# load_image.py
from tkinter import filedialog
from PIL import Image, ImageTk, UnidentifiedImageError
from modules.resize_image import *
from pathlib import Path
import numpy as np
import os
from modules.change_status import *
from modules.clear import remove_items_from_canvas

def load_image(canvas, x, y, text_x, text_y):
    """
    Ask the user to pick an image, display a 200x200 grayscale preview
    on the canvas, show the filename near the image, and store useful
    metadata on `canvas`.

    - Stores original grayscale PIL image in canvas.original_img
    - Displays a 200x200 resized preview (not aspect preserved)
    """
    change_status_to_waiting(canvas)

    file_path = filedialog.askopenfilename(
        title="Select an image",
        filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff")]
    )
    if not file_path:
        change_status_to_ready(canvas)
        return None  # user cancelled

    path = Path(file_path)
    try:
        # Load original grayscale image (keep full resolution)
        original_img = Image.open(path).convert("L")
    except (UnidentifiedImageError, OSError) as e:
        print(f"Failed to load image: {e}")
        change_status_to_ready(canvas)
        return None

    # Store the full-resolution grayscale image
    canvas.original_img = np.array(original_img)
    canvas.original_img = canvas.original_img.astype(np.int16).astype(np.float64)
    orig_w, orig_h = original_img.size

    # Create a 200x200 resized version for display
    preview = resize_image(original_img)
    img_tk = ImageTk.PhotoImage(preview)

    # Remove previous preview/text if present
    remove_items_from_canvas(canvas, ["original_img_id", "filename_text_id"])

    # Draw the preview and filename on the canvas
    img_id = canvas.create_image(x, y, image=img_tk)
    text_id = canvas.create_text(
        text_x,
        text_y,
        text=path.name,
        fill="#333333",
        font=("Roboto", -13),
        anchor="w",
    )

    # Keep references so Tk doesn't garbage-collect the image
    if not hasattr(canvas, "_image_refs"):
        canvas._image_refs = []
    canvas._image_refs.append(img_tk)

    # Store metadata similar to MATLAB version
    canvas.filePath = str(path)
    canvas.FileLabelName = path.stem.replace("_", "")
    canvas.lastPath = str(path.parent)
    canvas.fullImSizePix = (orig_h, orig_w)   # match MATLAB HxW style
    canvas.FAZ_ctr = (orig_h / 2.0, orig_w / 2.0)

    # # Create a per-image save folder if base dir provided
    # base_save_dir = getattr(canvas, "save_dir", None)
    # if base_save_dir:
    #     canvas.SaveFolder = os.path.join(base_save_dir, canvas.FileLabelName)
    #     os.makedirs(canvas.SaveFolder, exist_ok=True)
    # else:
    #     canvas.SaveFolder = None

    # Remember last drawn items
    canvas.original_img_id = img_id
    canvas.filename_text_id = text_id

    change_status_to_ready(canvas)

    return {
        "path": path,
        "filename": path.name,
        "size": (orig_w, orig_h),
        "img_id": img_id,
        "text_id": text_id,
    }