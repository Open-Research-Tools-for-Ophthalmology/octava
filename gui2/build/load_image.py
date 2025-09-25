# # image_loader.py
# from tkinter import filedialog
# from PIL import Image, ImageTk
# import os

# def load_image(canvas, x, y, text_x, text_y):
#     """
#     Ask the user to pick an image, display it on the given canvas,
#     and show the filename above the given position.
#     """
#     file_path = filedialog.askopenfilename(
#         title="Select an image",
#         filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.tiff")]
#     )

#     if not file_path:
#         return None  # user cancelled

#     # Load and resize image
#     img = Image.open(file_path).resize((200, 200))
#     img_tk = ImageTk.PhotoImage(img)

#     # Add the image to the canvas
#     img_id = canvas.create_image(x, y, image=img_tk)

#     # Show filename
#     filename = os.path.basename(file_path)
#     text_id = canvas.create_text(
#         text_x, text_y,
#         text=filename,
#         fill="#333333",
#         font=("Roboto", 12 * -1),
#     )

#     # Keep references so image don’t vanish
#     canvas.image_ref = img_tk



# load_image.py
from tkinter import filedialog
from PIL import Image, ImageTk, UnidentifiedImageError
from pathlib import Path
import os

def load_image(canvas, x, y, text_x, text_y):
    """
    Ask the user to pick an image, display a 200x200 grayscale preview
    on the canvas, show the filename near the image, and store useful
    metadata on `canvas`.

    - Stores original grayscale PIL image in canvas.original_img
    - Displays a 200x200 resized preview (not aspect preserved)
    """

    file_path = filedialog.askopenfilename(
        title="Select an image",
        filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff")]
    )
    if not file_path:
        return None  # user cancelled

    path = Path(file_path)
    try:
        # Load original grayscale image (keep full resolution)
        original_img = Image.open(path).convert("L")
    except (UnidentifiedImageError, OSError) as e:
        print(f"Failed to load image: {e}")
        return None

    # Store the full-resolution grayscale image
    canvas.original_img = original_img
    orig_w, orig_h = original_img.size

    # Create a 200x200 resized version for display
    preview = original_img.resize((200, 200), Image.LANCZOS)
    img_tk = ImageTk.PhotoImage(preview)

    # Remove previous preview/text if present
    for attr in ("last_img_id", "last_text_id"):
        prev_id = getattr(canvas, attr, None)
        if prev_id:
            try:
                canvas.delete(prev_id)
            except Exception:
                pass

    # Draw the preview and filename on the canvas
    img_id = canvas.create_image(x, y, image=img_tk)
    text_id = canvas.create_text(
        text_x,
        text_y,
        text=path.name,
        fill="#333333",
        font=("Roboto", -12),
        anchor="w",
    )

    # Keep references so Tk doesn't garbage-collect the image
    if not hasattr(canvas, "_image_refs"):
        canvas._image_refs = []
    canvas._image_refs.append(img_tk)

    # Store metadata similar to MATLAB version
    canvas.image_ref = img_tk
    canvas.FileLabelName = path.stem.replace("_", "")
    canvas.lastPath = str(path.parent)
    canvas.fullImSizePix = (orig_h, orig_w)   # match MATLAB HxW style
    canvas.imgShape = "rect"
    canvas.imgOriginal = original_img.copy()
    canvas.FAZ_ctr = (orig_h / 2.0, orig_w / 2.0)

    # # Create a per-image save folder if base dir provided
    # base_save_dir = getattr(canvas, "save_dir", None)
    # if base_save_dir:
    #     canvas.SaveFolder = os.path.join(base_save_dir, canvas.FileLabelName)
    #     os.makedirs(canvas.SaveFolder, exist_ok=True)
    # else:
    #     canvas.SaveFolder = None

    # Remember last drawn items
    canvas.last_img_id = img_id
    canvas.last_text_id = text_id

    return {
        "path": path,
        "filename": path.name,
        "size": (orig_w, orig_h),
        "img_id": img_id,
        "text_id": text_id,
    }