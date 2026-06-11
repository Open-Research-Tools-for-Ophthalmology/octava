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

def directional_median_filter(img: np.ndarray, length: int = 13, num_angles: int = 6) -> np.ndarray:
    """
    Vessel-aware directional median filter for OCTA en-face images.

    For each pixel, a 1-D median is applied along `num_angles` evenly-spaced
    orientations covering 0–180°.  The result from whichever orientation
    deviates least from the original pixel value is kept.  That criterion
    identifies the along-vessel axis (where intensity is smooth) vs the
    across-vessel axis (where intensity jumps at the vessel edge), so
    noise is suppressed parallel to vessels while vessel edges are kept sharp.

    Parameters
    ----------
    img        : uint8 grayscale array (H × W)
    length     : line length in pixels.  Should comfortably span the widest
                 vessel (~10 px); 13 px is a good default for 1000 px images.
    num_angles : orientations sampled over 0–180°.  6 → every 30°, which is
                 sufficient for most retinal vessel curvatures.

    Returns
    -------
    uint8 filtered array, same shape as `img`.
    """
    from scipy.ndimage import rotate as _nd_rotate
    from scipy.ndimage import median_filter as _sp_median

    img_f = img.astype(np.float32)
    best_result = np.zeros_like(img_f)
    best_dev    = np.full_like(img_f, np.inf)

    for i in range(num_angles):
        angle = i * 180.0 / num_angles          # 0°, 30°, 60°, 90°, 120°, 150°
        # Rotate image so this vessel orientation aligns with the vertical axis
        rotated      = _nd_rotate(img_f, angle,  reshape=False, mode='reflect')
        # Apply 1-D median along the (now-vertical) vessel axis only
        filtered     = _sp_median(rotated, size=(length, 1), mode='reflect')
        # Rotate the result back to the original frame
        filtered_bk  = _nd_rotate(filtered, -angle, reshape=False, mode='reflect')
        # Accept this orientation where it agrees best with the original
        # (smallest absolute deviation ↔ smoothing was applied along the vessel)
        dev  = np.abs(filtered_bk - img_f)
        mask = dev < best_dev
        best_result[mask] = filtered_bk[mask]
        best_dev[mask]    = dev[mask]

    return np.clip(best_result, 0, 255).astype(np.uint8)


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
        # Median filter: ksize=3 removes isolated noise without erasing 1-pixel capillaries
        print("Median filter selected.")
        # Normalise to uint8 once — bilateral and CLAHE both require 8-bit
        img = np.clip(canvas.original_img, 0, 255).astype(np.uint8)

        # ksize = canvas.kernel_size.get()  # assuming scalar
        # ksize = 3
        # img = median_filter(img, size=(ksize, ksize), mode='constant', cval=0.0)

        # Bilateral filter: edge-preserving smooth, decoupled from ksize
        # d=5: small diameter to preserve fine capillaries
        # sigmaColor=25: tight intensity tolerance, preserves vessel/background contrast
        # sigmaSpace=5: small spatial range, prevents smearing of fine structures

        # d = 5
        # sigmaColor = 25
        # sigmaSpace = 5
        # img = cv2.bilateralFilter(img, d=d, sigmaColor=sigmaColor, sigmaSpace=sigmaSpace)

        # CLAHE: local contrast enhancement
        # clipLimit=1.0: conservative — halves amplification vs 2.0, avoids lifting noise above threshold
        # tileGridSize=(8,8): 64 larger ~125px tiles (vs 256 ~63px tiles at 16,16)
        #   → gentler, more global correction; (16,16) was inflating vessel density ~30%→50%
        # clipLimit = 1.0
        # tileGridSize = 8
        # clahe = cv2.createCLAHE(clipLimit=clipLimit, tileGridSize=(tileGridSize, tileGridSize))
        # img = clahe.apply(img)

        # FIXME
        # img_path = os.path.join(canvas.current_save_folder, "images", f"{canvas.FileLabelName}_med={ksize}.png")
        # img_path = os.path.join(canvas.current_save_folder, "images", f"{canvas.FileLabelName}_bilateral_d={d}_sigmaColor={sigmaColor}_sigmaSpace={sigmaSpace}.png")
        # img_path = os.path.join(canvas.current_save_folder, "images", f"{canvas.FileLabelName}_med={ksize}_clahe_clipLimit={clipLimit}_gridSize={tileGridSize}.png")
        # img_path = os.path.join(canvas.current_save_folder, "images", f"{canvas.FileLabelName}_bilateral_d={d}_sigmaColor={sigmaColor}_sigmaSpace={sigmaSpace}.png")

        # cv2.imwrite(img_path, img)

        # Vessel-aware directional median filter
        # Applied after CLAHE so that local contrast is already enhanced before
        # the orientation-selection step.  Suppresses speckle and cross-vessel
        # noise while keeping 1-px capillary edges intact.
        # length=13: spans widest expected vessel (~10 px) with a small margin
        # num_angles=6: 30° steps — sufficient for all retinal vessel directions
        length = 13
        num_angles = 6
        img = directional_median_filter(img, length=length, num_angles=num_angles)

        # img_path = os.path.join(canvas.current_save_folder, "images", f"{canvas.FileLabelName}_med={ksize}_clahe_clipLimit={clipLimit}_gridSize={tileGridSize}_directional_med_length={length}_num_angles={num_angles}.png")
        # img_path = os.path.join(canvas.current_save_folder, "images", f"{canvas.FileLabelName}_bilateral_d={d}_sigmaColor={sigmaColor}_sigmaSpace={sigmaSpace}_directional_med_length={length}_num_angles={num_angles}.png")
        img_path = os.path.join(canvas.current_save_folder, "images", f"{canvas.FileLabelName}_directional_med_length={length}_num_angles={num_angles}.png")
        cv2.imwrite(img_path, img)



    else:
        print("Median filter not selected.")
        img = canvas.original_img

    # --- Apply Frangi filter (default to true)---
    if canvas.frangi_bool.get():
        # opts = {
        #     'sigmarange' : (canvas.frangi_min.get(), canvas.frangi_max.get()),
        #     'sigmastepsize': 2,
        #     'correctionconst1': 0.8,
        #     'correctionconst2': 15
        # }
        # img = frangi_2Dfilter(img, opts)

        # FIXME jerman vesselness2D(I, 1:5, [1;1], 1, false)
        jerman_opts = {
            'sigmas': [1, 2, 3, 4, 5],
            'spacing': [[1], [1]],
            'tau': 1
        }
        img_mat = mat_eng.vessel_jerman(matlab.single(img.tolist()), matlab.double(jerman_opts['sigmas']), matlab.double(jerman_opts['spacing']), jerman_opts['tau'], True, nargout=1)
        img = np.array(img_mat) # cast to numpy again (MATLAB functions return matlab.double objects)

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
    img_path = os.path.join(canvas.current_save_folder, "images", f"{canvas.FileLabelName}_jerman_sigmas={jerman_opts['sigmas']}_sp={jerman_opts['spacing'][0][0]}_tau={jerman_opts['tau']}.png")
    
    # FIXME sato
    # img_path = os.path.join(canvas.current_save_folder, "images", f"{canvas.FileLabelName}_sato_range({sato_opts['start']}-{sato_opts['stop']}-{sato_opts['step']}).png")
    
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
