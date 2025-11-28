from tkinter import messagebox
import numpy as np
from scipy.ndimage import median_filter
from modules.resize_image import *
from modules.fuzzy_thresholding import *
from modules.frangi_2Dfilter import *
from PIL import Image, ImageTk
from modules.change_status import *


def binarise_image(canvas):
    """
    binarise canvas.original_img using fuzzy thresholding.
    - Ensures vessels are white (255) and background black (0).
    - Optionally applies median filter.
    - Optionally applies Frangi filter (stub).
    Stores result in canvas.binary_image.
    """
    #todo4: (Done!) test basic binarisation (excluding median filter) 
    # --- Locate brightest vessel pixel ---
    y = canvas.original_img.max(axis=0)
    cc = int(y.argmax())
    rr = int(canvas.original_img[:, cc].argmax())

    # --- Apply median filter if selected ---
    #todo5: apply the same medianfilter (leave for advanced processing)
    if canvas.med_filt_bool.get():
        print("Median filter selected.")
        ksize = canvas.kernel_size.get()  # assuming scalar
        img = median_filter(canvas.original_img, size=(ksize, ksize),
                                    mode='constant', cval=0.0)
    else:
        print("Median filter not selected.")
        img = canvas.original_img

    # --- Apply Frangi filter (default to true)---
    if canvas.frangi_bool.get():
        opts = {
            'sigmarange' : (canvas.frangi_min.get(), canvas.frangi_max.get()),
            'sigmastepsize': 2,
            'correctionconst1': 0.8,
            'correctionconst2': 15
        }
        #todo3: implement frangi function (done)
        img = frangi_2Dfilter(img, opts)

    # --- Always use Fuzzy Means ---
    nth = 2
    #todo1: check fuzzy thresholding function (done)
    binary_image = fuzzy_thresholding(img, nth, 3)-1

    # --- Convert to 255 (white vessels) and 0 (black background) ---
    ref_value = binary_image[rr, cc]
    binary_image = np.where(binary_image == ref_value, 255, 0).astype(np.uint8)

    # --- Store result back to canvas ---
    canvas.binary_image = binary_image

    #todo2: display the binarised image on the canvas (done)
    display_binarised_image(canvas, binary_image)


def display_binarised_image(canvas: Canvas, image: np.ndarray):
    # Convert NumPy → PIL → ImageTk
    binary_pil = Image.fromarray(image)  # now a grayscale PIL image
    resized_img = resize_image(binary_pil)     # if resize is needed
    img_tk = ImageTk.PhotoImage(resized_img)   # convert to Tk-compatible image

    # Draw on canvas
    canvas.binary_img_id = canvas.create_image(805, 255, image=img_tk)
    # Prevent garbage collection. Without this, the image will not display.
    if not hasattr(canvas, "_image_refs"):
        canvas._image_refs = []
    canvas._image_refs.append(img_tk)


def invert_binarised_image(canvas: Canvas):
    if not hasattr(canvas, "binary_image"):
      messagebox.showwarning(
          "No Binarised Image", 
          "Please load another image and try to process it again."
      )
      return

    change_status_to_waiting(canvas)

    print ("Inverting binarised image...")

    # Invert binary image
    canvas.binary_image = 255 - canvas.binary_image

    # Update display of binarised image
    display_binarised_image(canvas, canvas.binary_image)

    print ("Inverted binarised image.")

    change_status_to_ready(canvas)
