# load_image.py
from tkinter import filedialog
from PIL import Image, ImageTk, UnidentifiedImageError
from modules.resize_image import *
from pathlib import Path
import numpy as np
import os
from modules.change_status import *
from modules.clear import *
from modules.binarise_image import *

# Load an image for processing
# @param {Boolean} silent = True for automated batch processing/image subset
# @param {String} filePath = path to load image from (for automated batch processing)
# @param {np.ndarray} imgArr = image array to replace to (for image subset)
def load_image(canvas, x, y, text_x, text_y, silent=False, filePath=None, imgArr=None):
    """
    Ask the user to pick an image, display a 200x200 grayscale preview
    on the canvas, show the filename near the image, and store useful
    metadata on `canvas`.

    - Stores original grayscale PIL image in canvas.original_img
    - Displays a 200x200 resized preview (not aspect preserved)
    """
    change_status_to_waiting(canvas)

    # Method 1: Load from given path
    if imgArr is None:
        # Method 1.1 Load image from file browser prompt
        if not silent:
            file_path = filedialog.askopenfilename(
                title="Select an image",
                filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff")]
            )
            if not file_path:
                change_status_to_ready(canvas)
                return None  # user cancelled
        else:
            # Method 1.2 Load image from given path (image batch processing)
            file_path = filePath
        
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
    else:
        # Method 2: Load from given image array (image subset)
        canvas.original_img = imgArr
        original_img = Image.fromarray(imgArr.astype(np.uint8))
        path = Path(canvas.filePath)  # Keep original path info

    canvas.original_img = canvas.original_img.astype(np.int16).astype(np.float64)
    orig_w, orig_h = original_img.size

    # Create a 200x200 resized version for display
    preview = resize_image(original_img)
    img_tk = ImageTk.PhotoImage(preview)

    # Remove previous preview/text if present
    clear_screen(canvas, clear_screen_mode=ClearMode.CLEAR_BEFORE_LOADING_NEW_IMG)

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
        canvas._image_refs = {}
    canvas._image_refs["original_img"] = img_tk

    # Prebinary, load original image as binarized if prebinary is toggled on
    if canvas.prebinary_var.get():    # --- Store result back to canvas ---
        canvas.binary_image = canvas.original_img.copy()
        canvas.inverted_image = canvas.binary_image.copy()

        # --- Display binarised image ---
        display_binarised_image(canvas, canvas.binary_image)

    # Store metadata similar to MATLAB version
    canvas.filePath = str(path)
    canvas.FileLabelName = path.stem.replace("_", "")
    canvas.lastPath = str(path.parent)
    canvas.fullImSizePix = (orig_h, orig_w)   # match MATLAB HxW style
    canvas.FAZ_ctr = np.array([orig_h // 2, orig_w // 2])

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