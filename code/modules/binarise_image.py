from tkinter import messagebox
import numpy as np
from scipy.ndimage import median_filter
from modules.resize_image import *
from modules.fuzzy_thresholding import *
from modules.frangi_2Dfilter import *
from PIL import Image, ImageTk
from modules.change_status import *
import cv2
import os
import matlab
from modules.mat_eng import mat_eng
from skimage.filters import sato

def binarise_image(canvas: Canvas, display:bool=True):
    """
    binarise canvas.original_img using fuzzy thresholding.
    - Ensures vessels are white (255) and background black (0).
    - Optionally applies median filter.
    - Optionally applies Frangi filter (stub).
    Stores result in canvas.binary_image.
    """
    change_status_to_waiting(canvas, status="● Wait...Binarising")

    # --- Apply median filter if selected ---
    # FIXME denoising
    if canvas.med_filt_bool.get() or True:
        # FIXME Median
        print("Median filter selected.")
        ksize = canvas.kernel_size.get()  # assuming scalar
        img = median_filter(canvas.original_img, size=(ksize, ksize),
                                    mode='constant', cval=0.0)
        
        # FIXME bilateral
        img = cv2.bilateralFilter(img, d=ksize, sigmaColor=75, sigmaSpace=75)
        
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

        # FIXME jerman vesselness2D(I, 1:5, [1;1], 1, false)
        # jerman_opts = {
        #     'sigmas': [1, 2, 3, 4, 5],
        #     'spacing': [[1], [1]],
        #     'tau': 0.5
        # }
        # img_mat = mat_eng.vessel_jerman(matlab.single(img.tolist()), matlab.double(jerman_opts['sigmas']), matlab.double(jerman_opts['spacing']), jerman_opts['tau'], True, nargout=1)
        # img = np.array(img_mat) # cast to numpy again (MATLAB functions return matlab.double objects)

        # FIXME sato from skimage
        # sato_opts = {
        #     'start': 1,
        #     'stop': 5,
        #     'step': 1,
        # }
        # img = sato(img, np.arange(sato_opts['start'], sato_opts['stop'], sato_opts['step']), black_ridges=False)

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

    # FIXME jerman
    # img_path = os.path.join(canvas.current_save_folder, "images", f"{canvas.FileLabelName}_jerman_sigmas={jerman_opts['sigmas']}_sp={jerman_opts['spacing'][0][0]}_tau={jerman_opts['tau']}.png")
    
    # FIXME sato
    img_path = os.path.join(canvas.current_save_folder, "images", f"{canvas.FileLabelName}_sato_range({sato_opts['start']}-{sato_opts['stop']}-{sato_opts['step']}).png")
    
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


def invert_binarised_image(canvas: Canvas):
    """Invert the currently displayed binary mask and refresh the preview."""
    if not hasattr(canvas, "binary_image"):
      messagebox.showwarning(
          "No Binarised Image", 
          'Please load an image and click "Start Processing" first.'
      )
      return

    change_status_to_waiting(canvas, status="● Wait...Inverting Binarised Image")

    print ("Inverting binarised image...")

    # Invert binary image
    canvas.inverted_image = 255 - canvas.inverted_image

    # Update display of binarised image
    display_binarised_image(canvas, canvas.inverted_image)

    print ("Inverted binarised image.")

    change_status_to_ready(canvas)
