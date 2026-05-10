from tkinter import messagebox
import numpy as np
import cv2
import os
from PIL import Image, ImageTk
from scipy.ndimage import median_filter

from modules.resize_image import *
from modules.change_status import *
from modules.frangi_2Dfilter import *


def binarise_onh_image(canvas, display: bool = True):
    """
    ONH-specific binarisation pipeline.

    This function is designed for optic nerve head OCTA images.

    Current strategy:
    - Use ROI-based normalisation to avoid the black background dominating contrast.
    - Use CLAHE to enhance local vessel contrast.
    - Use gentle background correction to avoid hollow large vessels.
    - Use a bright-vessel seed mask to preserve large bright vessels.
    - Use Frangi vesselness to detect fine line-like vessels.
    - Combine both masks into one overall binary vessel mask.

    Expected outputs:
    - canvas.binary_image: 0/255 binary vessel mask
        - vessel = 255 white
        - background = 0 black
    - canvas.inverted_image: copy of binary_image
    """

    change_status_to_waiting(canvas, status="● Wait...Binarising ONH")

    # ------------------------------------------------------------
    # 1. Choose input image
    # ------------------------------------------------------------
    if hasattr(canvas, "onh_mask_img"):
        img = canvas.onh_mask_img.astype(np.float64)
        print("Using canvas.onh_mask_img for ONH binarisation.")
    elif hasattr(canvas, "original_img"):
        img = canvas.original_img.astype(np.float64)
        print("Using canvas.original_img for ONH binarisation.")
    else:
        messagebox.showwarning(
            "No Image",
            "No image found for ONH binarisation."
        )
        return

    # ------------------------------------------------------------
    # 2. Get ONH ROI mask
    # ------------------------------------------------------------
    if hasattr(canvas, "onh_mask_arr"):
        roi_mask = canvas.onh_mask_arr.astype(bool)
        print("Using canvas.onh_mask_arr as ONH ROI mask.")
    else:
        roi_mask = np.ones_like(img, dtype=bool)
        print("No ONH ROI mask found. Using full image.")

    if img.shape != roi_mask.shape:
        messagebox.showwarning(
            "Mask Size Mismatch",
            "ONH image and ONH mask have different sizes."
        )
        return

    roi_pixels = img[roi_mask]

    if roi_pixels.size == 0:
        messagebox.showwarning(
            "Invalid ONH Mask",
            "The ONH mask contains no valid pixels."
        )
        return

    image_size = img.shape[0]

    # ------------------------------------------------------------
    # Optional median filtering, controlled by the shared Advanced
    # Settings control. This is only read here for ONH; Retina code is
    # not changed.
    # ------------------------------------------------------------
    if hasattr(canvas, "med_filt_bool") and canvas.med_filt_bool.get():
        ksize = int(canvas.kernel_size.get()) if hasattr(canvas, "kernel_size") else 3
        ksize = max(1, ksize)
        img = median_filter(
            img,
            size=(ksize, ksize),
            mode="constant",
            cval=0.0,
        )
        img = np.where(roi_mask, img, 0).astype(np.float64)
        roi_pixels = img[roi_mask]
        print("ONH median filter selected. Kernel size:", ksize)

    # ------------------------------------------------------------
    # 3. Normalise image using ROI pixels only
    # ------------------------------------------------------------
    p_low, p_high = np.percentile(roi_pixels, (1, 99))

    if p_high <= p_low:
        p_low = roi_pixels.min()
        p_high = roi_pixels.max()

    img_norm = (img - p_low) / (p_high - p_low + 1e-8)
    img_norm = np.clip(img_norm, 0, 1)
    img_uint8 = (img_norm * 255).astype(np.uint8)

    # Force outside ROI to black.
    img_uint8 = np.where(roi_mask, img_uint8, 0).astype(np.uint8)

    # ------------------------------------------------------------
    # 4. Local contrast enhancement with CLAHE
    # ------------------------------------------------------------
    # If too noisy, reduce clipLimit to 1.5.
    # If fine vessels are still weak, try 2.5.
    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8)
    )

    img_enhanced = clahe.apply(img_uint8)
    img_enhanced = np.where(roi_mask, img_enhanced, 0).astype(np.uint8)

    # ------------------------------------------------------------
    # 5. Gentle background correction
    # ------------------------------------------------------------
    # Do not fully subtract the background.
    # Full subtraction can make vessels hollow or fragmented.
    bg_kernel = max(15, int(image_size * 0.035))
    if bg_kernel % 2 == 0:
        bg_kernel += 1

    background = cv2.GaussianBlur(
        img_enhanced,
        (bg_kernel, bg_kernel),
        0
    )

    img_corrected = cv2.addWeighted(
        img_enhanced,
        1.0,
        background,
        -0.5,
        0
    )

    img_corrected = cv2.normalize(
        img_corrected,
        None,
        0,
        255,
        cv2.NORM_MINMAX
    ).astype(np.uint8)

    img_corrected = np.where(roi_mask, img_corrected, 0).astype(np.uint8)

    # Very light smoothing before Frangi.
    # Gaussian is gentler than median blur for thin vessels.
    img_smooth = cv2.GaussianBlur(img_corrected, (3, 3), 0)

    # ------------------------------------------------------------
    # 6. Bright vessel seed mask
    # ------------------------------------------------------------
    # This preserves large/bright vessels so they remain solid.
    roi_enhanced_pixels = img_enhanced[roi_mask]

    # If large vessels are incomplete, reduce to 80.
    # If too much bright background is included, increase to 88 or 90.
    bright_seed_threshold = np.percentile(roi_enhanced_pixels, 85)

    bright_vessel_seed_mask = np.zeros_like(img_enhanced, dtype=np.uint8)
    bright_vessel_seed_mask[
        (img_enhanced >= bright_seed_threshold) & roi_mask
    ] = 255

    seed_kernel_size = max(5, int(image_size * 0.008))
    if seed_kernel_size % 2 == 0:
        seed_kernel_size += 1

    seed_kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE,
        (seed_kernel_size, seed_kernel_size)
    )

    bright_vessel_seed_mask = cv2.morphologyEx(
        bright_vessel_seed_mask,
        cv2.MORPH_CLOSE,
        seed_kernel
    )

    bright_vessel_seed_mask = np.where(
        roi_mask,
        bright_vessel_seed_mask,
        0
    ).astype(np.uint8)

    # ------------------------------------------------------------
    # 7. Fine vessel candidate mask using Frangi vesselness
    # ------------------------------------------------------------
    # Adaptive thresholding was too sensitive to OCTA speckle noise.
    # Frangi is used here because it enhances line-like / vessel-like structures.

    use_frangi = True
    if hasattr(canvas, "frangi_bool"):
        use_frangi = bool(canvas.frangi_bool.get())

    if use_frangi:
        frangi_min = int(canvas.frangi_min.get()) if hasattr(canvas, "frangi_min") else 1
        frangi_max = int(canvas.frangi_max.get()) if hasattr(canvas, "frangi_max") else 4
        if frangi_max < frangi_min:
            frangi_min, frangi_max = frangi_max, frangi_min

        frangi_opts = {
            "sigmarange": (frangi_min, frangi_max),
            "sigmastepsize": 1,
            "correctionconst1": 0.8,
            "correctionconst2": 15,
        }

        frangi_response = frangi_2Dfilter(
            img_smooth.astype(np.float64),
            frangi_opts
        )

        frangi_response = cv2.normalize(
            frangi_response,
            None,
            0,
            255,
            cv2.NORM_MINMAX
        ).astype(np.uint8)

        frangi_response = np.where(
            roi_mask,
            frangi_response,
            0
        ).astype(np.uint8)

        roi_frangi_pixels = frangi_response[roi_mask]

        # Lower percentile = more fine vessels, more noise.
        # Higher percentile = cleaner, but fewer fine vessels.
        fine_threshold = np.percentile(roi_frangi_pixels, 70)

        fine_vessel_candidate_mask = np.zeros_like(frangi_response, dtype=np.uint8)
        fine_vessel_candidate_mask[
            (frangi_response >= fine_threshold) & roi_mask
        ] = 255

        # Connect fragmented fine vessels gently.
        fine_kernel_size = max(3, int(image_size * 0.004))
        if fine_kernel_size % 2 == 0:
            fine_kernel_size += 1

        fine_kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE,
            (fine_kernel_size, fine_kernel_size)
        )

        fine_vessel_candidate_mask = cv2.morphologyEx(
            fine_vessel_candidate_mask,
            cv2.MORPH_CLOSE,
            fine_kernel
        )

        fine_vessel_candidate_mask = np.where(
            roi_mask,
            fine_vessel_candidate_mask,
            0
        ).astype(np.uint8)
    else:
        frangi_response = np.zeros_like(img_corrected, dtype=np.uint8)
        fine_vessel_candidate_mask = np.zeros_like(img_corrected, dtype=np.uint8)
        print("ONH Frangi filter disabled. Using bright-vessel seed only.")

    # ------------------------------------------------------------
    # 8. Combine bright-vessel seed and fine-vessel candidate masks
    # ------------------------------------------------------------
    binary_image = cv2.bitwise_or(
        bright_vessel_seed_mask,
        fine_vessel_candidate_mask
    )

    binary_image = np.where(roi_mask, binary_image, 0).astype(np.uint8)

    # ------------------------------------------------------------
    # 9. Gentle final connection
    # ------------------------------------------------------------
    # Only close small gaps. Do not perform strong opening here,
    # because opening can remove fine ONH vessels.
    cleanup_kernel_size = max(3, int(image_size * 0.003))
    if cleanup_kernel_size % 2 == 0:
        cleanup_kernel_size += 1

    cleanup_kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE,
        (cleanup_kernel_size, cleanup_kernel_size)
    )

    binary_image = cv2.morphologyEx(
        binary_image,
        cv2.MORPH_CLOSE,
        cleanup_kernel
    )

    binary_image = np.where(roi_mask, binary_image, 0).astype(np.uint8)

    # ------------------------------------------------------------
    # 10. Optional very light component removal
    # ------------------------------------------------------------
    # Keep this disabled for now while tuning.
    # If the result is too noisy later, re-enable with a very small threshold.
    #
    # num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
    #     binary_image,
    #     connectivity=8
    # )
    #
    # min_area = max(5, int(image_size * image_size * 0.000005))
    # cleaned = np.zeros_like(binary_image, dtype=np.uint8)
    #
    # for label in range(1, num_labels):
    #     area = stats[label, cv2.CC_STAT_AREA]
    #     if area >= min_area:
    #         cleaned[labels == label] = 255
    #
    # binary_image = cleaned
    # binary_image = np.where(roi_mask, binary_image, 0).astype(np.uint8)

    # ------------------------------------------------------------
    # 11. Store result on canvas
    # ------------------------------------------------------------
    canvas.onh_binary_overall = binary_image
    canvas.onh_overall_vessel_img = binary_image
    canvas.binary_image = binary_image
    canvas.inverted_image = binary_image.copy()

    # Debug outputs for later inspection.
    canvas.onh_bright_vessel_seed_mask_debug = bright_vessel_seed_mask
    canvas.onh_fine_vessel_candidate_mask_debug = fine_vessel_candidate_mask
    canvas.onh_enhanced_debug = img_enhanced
    canvas.onh_corrected_debug = img_corrected
    canvas.onh_frangi_response_debug = frangi_response

    # ------------------------------------------------------------
    # 12. Display result
    # ------------------------------------------------------------
    if display:
        display_onh_binarised_image(canvas, binary_image)

    # ------------------------------------------------------------
    # 13. Save result
    # ------------------------------------------------------------
    save_onh_binary_image(canvas, binary_image)

    print("ONH binarisation completed.")


def display_onh_binarised_image(canvas, image: np.ndarray):
    """
    Display ONH binary image on the GUI.
    """

    binary_pil = Image.fromarray(image)
    resized_img = resize_image(binary_pil)
    img_tk = ImageTk.PhotoImage(resized_img)

    canvas.binary_img_id = canvas.create_image(805, 255, image=img_tk)

    if not hasattr(canvas, "_image_refs"):
        canvas._image_refs = {}

    canvas._image_refs["binary_img"] = img_tk


def save_onh_binary_image(canvas, binary_image: np.ndarray):
    """
    Save ONH binary mask and useful debug images to the current output folder.
    """

    if not hasattr(canvas, "current_save_folder"):
        print("No current_save_folder found. ONH binary image not saved.")
        return

    images_dir = os.path.join(canvas.current_save_folder, "images")
    os.makedirs(images_dir, exist_ok=True)

    file_label = getattr(canvas, "FileLabelName", "ONH_Image")

    curr_idx = len([
        f for f in os.listdir(images_dir)
        if "ONH_Binarymask" in f
    ])

    # Save final binary image
    img_path = os.path.join(
        images_dir,
        f"{file_label}_ONH_Binarymask_{curr_idx}.png"
    )

    cv2.imwrite(img_path, binary_image)
    print(f"ONH binary image saved to: {img_path}")

    # Save debug images if available
    debug_items = {
        "ONH_Enhanced": getattr(canvas, "onh_enhanced_debug", None),
        "ONH_Corrected": getattr(canvas, "onh_corrected_debug", None),
        "ONH_FrangiResponse": getattr(canvas, "onh_frangi_response_debug", None),
        "ONH_BrightSeedMask": getattr(canvas, "onh_bright_vessel_seed_mask_debug", None),
        "ONH_FineCandidateMask": getattr(canvas, "onh_fine_vessel_candidate_mask_debug", None),
    }

    for name, debug_img in debug_items.items():
        if debug_img is None:
            continue

        debug_path = os.path.join(
            images_dir,
            f"{file_label}_{name}_{curr_idx}.png"
        )

        cv2.imwrite(debug_path, debug_img)
        print(f"Debug image saved to: {debug_path}")
