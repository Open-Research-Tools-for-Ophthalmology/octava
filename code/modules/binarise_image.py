from tkinter import messagebox
import numpy as np
from scipy.ndimage import median_filter
from modules.resize_image import *
from modules.fuzzy_thresholding import *
from modules.frangi_2Dfilter import *
from modules.jerman_2Dfilter import *
from PIL import Image, ImageTk
from modules.change_status import *
import cv2
import os

def binarise_image(canvas: Canvas, display:bool=True):
    """
    binarise canvas.original_img using fuzzy thresholding.
    - Ensures vessels are white (255) and background black (0).
    - Optionally applies median filter.
    - Optionally applies Frangi filter (stub).
    - Optionally applies Jerman filter(stub).
    Stores result in canvas.binary_image.
    """
    change_status_to_waiting(canvas, status="● Wait...Binarising")

    # --- Apply median filter if selected ---
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
        img = frangi_2Dfilter(img, opts)

    if canvas.jerman_bool.get():
        sigmas_str = canvas.jerman_sigmas.get()
        sigmas_arr = [float(s.strip()) for s in sigmas_str.split(',')]
        img = jerman_2Dfilter(img, sigmas=np.array(sigmas_arr), tau=canvas.jerman_tau.get())

    # --- Always use Fuzzy Means ---
    nth = 2
    binary_image = fuzzy_thresholding(img, nth, 3)-1

    # --- Convert to 255 (white vessels) and 0 (black background) ---
    # labels = np.unique(binary_image)
    # bright_label = max(labels, key=lambda label: img[binary_image == label].mean())
    bright_label = 1  # Since we are using nth=2, we expect labels to be [0, 1] where 1 is the brighter cluster.
    binary_image = np.where(binary_image == bright_label, 255, 0).astype(np.uint8)

    # --- Store result back to canvas ---
    canvas.binary_image = binary_image
    canvas.inverted_image = binary_image.copy()

    # --- Display binarised image ---
    display_binarised_image(canvas, binary_image)

    # --- Save binary image to local ---
    curr_idx = len([f for f in os.listdir(os.path.join(canvas.current_save_folder, "images")) if 'Binarymask' in f])
    img_path = os.path.join(canvas.current_save_folder, "images", f"{canvas.FileLabelName}_Binarymask_{curr_idx}.png")
    cv2.imwrite(img_path, binary_image)

def display_binarised_image(canvas: Canvas, image: np.ndarray):
    """Render a binarized image preview onto the GUI canvas."""
    # Convert NumPy → PIL → ImageTk
    binary_pil = Image.fromarray(image)  # now a grayscale PIL image
    resized_img = resize_image(binary_pil)     # if resize is needed
    img_tk = ImageTk.PhotoImage(resized_img)   # convert to Tk-compatible image

    # Draw on canvas
    canvas.binary_img_id = canvas.create_image(805, 255, image=img_tk)
    # Prevent garbage collection. Without this, the image will not display.
    canvas._image_refs["binary_img"] = img_tk

    # Reset zoom/pan for binarised thumbnail
    if hasattr(canvas, 'thumbnail_state') and 'binarised' in canvas.thumbnail_state:
        canvas.thumbnail_state['binarised'].update({"zoom": 1.0, "pan_x": 0.0, "pan_y": 0.0})


def invert_binarised_image(canvas: Canvas):
    """Invert the currently displayed binary mask and refresh the preview."""
    if not hasattr(canvas, "binary_image"):
      messagebox.showwarning(
          "No Binarised Image", 
          'Please load an image and click "Start Processing" first.'
      )
      return

    # change_status_to_waiting(canvas, status="● Wait...Inverting Binarised Image")

    print ("Inverting binarised image...")

    # Invert binary image
    canvas.inverted_image = 255 - canvas.inverted_image

    # Update display of binarised image
    display_binarised_image(canvas, canvas.inverted_image)

    print ("Inverted binarised image.")

    # change_status_to_ready(canvas)
