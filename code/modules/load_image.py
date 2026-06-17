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
from modules.select_folder import *

def resize_from_spinbox(canvas):
    """Resize the full-resolution image based on the current spinbox value and update preview."""
    if not hasattr(canvas, "full_res_img"):
        return

    clear_onh_image_state(canvas)

    mm_value = canvas.image_size_var.get()
    target_pixels = size_to_pixels(mm_value)

    # Resize from the original full-resolution image
    resized_img = resize_image(canvas.full_res_img.copy(), (target_pixels, target_pixels))
    
    canvas.original_img = np.array(resized_img).astype(np.float64)
    canvas.fullImSizePix = (resized_img.height, resized_img.width)
    canvas.FAZ_ctr = np.array([resized_img.height // 2, resized_img.width // 2])

    # Update preview (200x200)
    preview = resize_image(resized_img.copy(), (200, 200))
    img_tk = ImageTk.PhotoImage(preview)

    canvas.itemconfigure(canvas.original_img_id, image=img_tk)
    canvas._image_refs["original_img"] = img_tk

    print(f"[Spinbox Resize] mm={mm_value}, pixels={target_pixels}, resized shape={resized_img.size}")

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

    else:
        # Method 2: Load from given image array (image subset)
        original_img = Image.fromarray(imgArr.astype(np.uint8))
        path = Path(canvas.filePath) if hasattr(canvas, "filePath") else Path("unknown")
    
    # Store full-resolution original
    canvas.full_res_img = original_img.copy()

    # resize image according to spinbox value
    mm_value = canvas.image_size_var.get() # current spinbox value
    print("---- Resize debug info ----")
    print("Spinbox value (mm):", mm_value)

    target_pixels = size_to_pixels(mm_value) # convert from mm to pixels
    print("Target pixel size:", target_pixels)

    resized_img = resize_image(original_img, (target_pixels, target_pixels))
    print("Resized image size (W, H):", resized_img.size)

    canvas.original_img = np.array(resized_img).astype(np.float64)

    # Update metadata
    canvas.fullImSizePix = (resized_img.height, resized_img.width)  # H x W
    canvas.FAZ_ctr = np.array([resized_img.height // 2, resized_img.width // 2])
    print("Stored fullImSizePix:", canvas.fullImSizePix)
    print("Stored FAZ_ctr:", canvas.FAZ_ctr)

    # Create a 200x200 resized version for display
    preview = resize_image(resized_img, (200, 200))
    img_tk = ImageTk.PhotoImage(preview)

    # Remove previous preview/text if present
    clear_screen(canvas, clear_screen_mode=ClearMode.CLEAR_BEFORE_LOADING_NEW_IMG)

    # Draw the preview and filename on the canvas
    img_id = canvas.create_image(x, y, image=img_tk)

    display_text = fit_path_to_canvas(path.name, canvas, ("Roboto", 12 * -1), 220)
    text_id = display_text_to_canvas(
        canvas,
        text_x, 
        text_y,
        display_text,
        ("Roboto", 12 * -1),
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
    canvas.FileLabelName = path.stem # match input/output naming convention
    canvas.lastPath = str(path.parent)

    # Remember last drawn items
    canvas.original_img_id = img_id
    canvas.filename_text_id = text_id

    # Reset zoom/pan for original thumbnail
    if hasattr(canvas, 'thumbnail_state') and 'original' in canvas.thumbnail_state:
        canvas.thumbnail_state['original'].update({"zoom": 1.0, "pan_x": 0.0, "pan_y": 0.0})

    # Attach spinbox trace to dynamically resize
    if hasattr(canvas, "image_size_var"):
        canvas.image_size_var.trace_add("write", lambda *args: resize_from_spinbox(canvas))


    change_status_to_ready(canvas)

    return {
        "path": path,
        "filename": path.name,
        "size": (resized_img.width, resized_img.height),
        "img_id": img_id,
        "text_id": text_id,
    }
