import numpy as np
import cv2
from matplotlib import pyplot as plt


def apply_clahe(img, clipLimit=1.0, tileGridSize=(8, 8), invert=False):

    clahe = cv2.createCLAHE(clipLimit=clipLimit,tileGridSize=tuple(tileGridSize))
    clahe_img = clahe.apply(img)
    if invert:
        clahe_img = 255 - clahe_img

    return clahe_img


def apply_gaussian_blur(img, kernel_size=(3, 3)):
    return cv2.GaussianBlur(img, tuple(kernel_size), 0)


def display_and_save(original_img, processed, step=None, msg=None):
    """
    drop in function to quickly display images without using Display
    """
    step_str = f"step {str(step)}: "

    plt.subplot(121), plt.imshow(original_img, cmap='gray')
    plt.title('Input Image'), plt.xticks([]), plt.yticks([])

    plt.subplot(122), plt.imshow(processed, cmap='gray')
    plt.title('Previous Step'), plt.xticks([]), plt.yticks([])

    plt.tight_layout()
    if step is not None:
        plt.figtext(0.5, 0.95, step_str + msg,
                horizontalalignment='center', verticalalignment='top')
    else:
        plt.figtext(0.5, 0.95, "Final Processed",
                horizontalalignment='center', verticalalignment='top')
    plt.show()


def threshold(img, percentile):
    """
    Binarise the image using the percentile provided
    """
    thr = int(np.percentile(img, percentile))
    _, veins = cv2.threshold(img, thr, 255, cv2.THRESH_BINARY)

    return veins


def keep_largest(mask, connectivity=8):
    """
    keep largest connected white component, fill any black specks in white area

    connectivity can be 4 or 8
        4 = diagonals are considered not connected
        8 = diagonals are connected
    """
    # Normalize to 0/1
    m01 = (mask > 0).astype(np.uint8)

    num, labels, stats, _ = cv2.connectedComponentsWithStats(m01, connectivity)

    if num <= 1:
        # No foreground
        return (m01 * 255).astype(np.uint8)

    # stats[:, cv2.CC_STAT_AREA] gives areas; index 0 is background
    areas = stats[1:, cv2.CC_STAT_AREA]
    best_label = 1 + np.argmax(areas)

    largest = (labels == best_label).astype(np.uint8) * 255
    return largest


def keep_brightest_pixels(img, percentile=10):
    """
    Set the brightest X% pixels in the image to 255 (white).
    Expects 0 < percentile < 100
    """
    cutoff = 100 - percentile
    thresh = np.percentile(img, cutoff)

    out = img.copy()
    out[img >= thresh] = 255
    return out



def keep_darkest_pixels(img, percentile=10):
    """
    Set the darkest X% pixels in the image to 0 (black).
    Expects  0 < percentile < 100
    """
    thresh = np.percentile(img, percentile)

    out = img.copy()
    out[img <= thresh] = 0
    return out


def flood_fill(img):
    """
    Checks each corner pixel of the image. If it is white, flood fills
    every connected white pixel to black
    """
    h, w = img.shape
    # opencv floodfill requires the mask h, w to be +2 pixels larger than the image
    mask = np.zeros((h+2, w+2), np.uint8)
    # try all four corners
    for sx, sy in [(1,1),(w-2,1),(1,h-2),(w-2,h-2)]:
        if img[sy, sx] > 0:
            cv2.floodFill(img, mask, (sx, sy), 0)
    return img


def remove_protusions(mask, rad=2):
    """
    Remove narrow protrusions/'prongs' that stick out of FAZ centroid
    rad: erosion radius
    how “wide” a protrusion must be to survive
    larger values remove thicker spikes
    """
    m = (mask > 0).astype(np.uint8) * 255
    if rad <= 0:
        return m

    se = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2*rad+1, 2*rad+1))
    marker = cv2.erode(m, se, iterations=1)
    return marker


def expand_and_round(mask, grow_px=2, smooth_ks=3):
    """
    Expand the FAZ slightly and round edges.
    kernels need to be odd values
    """
    m = (mask > 0).astype(np.uint8) * 255

    if grow_px and grow_px > 0:
        K_grow = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2*grow_px+1, 2*grow_px+1))
        m = cv2.dilate(m, K_grow, iterations=1)

    # closing fills tiny holes
    # opening removes tiny nubs leading to a smoother boundary
    if smooth_ks and smooth_ks > 1:
        K_s = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (smooth_ks, smooth_ks))
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, K_s, iterations=1)
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN,  K_s, iterations=1)

    return m


def fill_holes_and_smooth(faz):
    """
    Fill any black holes in the FAZ centroid by using flood fill from the
    borders (black -> white)
    Performs some light boundary smoothing after
    """
    h, w = faz.shape
    mask2 = np.zeros((h+2, w+2), np.uint8)
    ff2 = faz.copy()
    # flood fill stops at FAZ, so any holes (black pixels) inside FAZ centroid is untouched 
    # by flood fill and remains black
    cv2.floodFill(ff2, mask2, (0, 0), 255)
    # inverting the flood filled mask results a mask containing only the holes
    holes = cv2.bitwise_not(ff2)
    # A bitwise_or on the original faz with the hole mask fills in these holes to white 
    faz_out = cv2.bitwise_or(faz, holes)
    faz_out = cv2.morphologyEx(
        faz_out, cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)), 1
    )
    return faz_out
