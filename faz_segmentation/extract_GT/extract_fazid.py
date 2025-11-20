import cv2
import numpy as np
import matplotlib.pyplot as plt

def extract_faz_gt_mask(img):
    """
    Returns uint8 mask (0/255) where FAZ = 255.
    Used for the FAZID dataset where in GT, FAZ is marked yellow/green-ish
    on a greyscale OCTA image.
    """
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # "yellow" range in OpenCV HSV (H:0–179, S/V:0–255).
    # can tweak for different GT colours
    lower = np.array([15, 60, 60], dtype=np.uint8)   # ~yellow
    upper = np.array([45, 255, 255], dtype=np.uint8)

    mask = cv2.inRange(hsv, lower, upper)  # 255 inside colored FAZ

    return mask
