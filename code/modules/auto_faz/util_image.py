"""
Utility functions for loading images
"""

import os
import cv2
import numpy as np
from tifffile import imread as tiff_imread


def load_image(img_path, crop_bottom_px=0):
    """
    Loads a single greyscale image from the specified path.
    Uses cv2 for png/jpg/jpeg, tifffile for tif/tiff.
    Image cropping available to remove instrument annotations/watermarks on the image
    """
    _, ext = os.path.splitext(img_path)
    ext = ext.lower()

    if ext in {'.png', '.jpg', '.jpeg', '.bmp'}:
        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)

    elif ext in {'.tif', '.tiff'}:
        # tifffile handles multi-channel/bit-depth better
        img = tiff_imread(img_path)

        # If multi-channel, pick first channel or convert to greyscale
        if img.ndim == 3:  
            if img.shape[2] > 1:
                # Take mean across channels, or just first channel depending on dataset
                img = np.mean(img, axis=2).astype(np.uint8)
            else:
                img = img[:, :, 0]
        
        # If higher than 8-bit, normalize to 0–255
        if img.dtype != np.uint8:
            img = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

    else:
        print(f"Unsupported file extension for {img_path}")
        return None

    if img is None:
        print(f"Failed to load {img_path}")
        return None

    # crop bottom if requested
    if crop_bottom_px > 0 and crop_bottom_px < img.shape[0]:
        img = img[:-crop_bottom_px, :]

    return img


def extract_faz_gt_mask(gt_img):
    """
    Load a uint8 FAZ mask (0/255) where FAZ = 255,
    Can handle tif/tiff files by loading with original bit depth and then scaling to binary
    """
    data_root = './datasets'
    img_path = os.path.join(data_root, gt_img)

    img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise ValueError(f"Could not read image {img_path}")

    # If multi-channel, convert to greyscale
    if img.ndim == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Invariant: already binary 0/255 uint8
    assert img.dtype == np.uint8, "Expected uint8 mask"
    unique_vals = np.unique(img)
    assert np.all(np.isin(unique_vals, [0, 255])), f"Mask not binary: {unique_vals}"

    return img


def load_colour_gt_mask(img, crop_bottom_px=None):
    """
    Assumes FAZ is coloured on a greyscalae OCTA image
    thus image needs to be opened with cv2.IMREAD_COLOR
    """
    img = cv2.imread(img, cv2.IMREAD_COLOR)
    if img is None:
        exit("File not found")
    
    if crop_bottom_px > 0 and crop_bottom_px < img.shape[0]:
        img = img[:-crop_bottom_px, :]
    
    return img