import cv2
import numpy as np
import matplotlib.pyplot as plt

from .util import *


def process_image(img, ctx):
    """Segment a FAZ mask from a grayscale or pre-binarized OCTA image."""
    # check if input images are already pre-binarized 0/255 uint8
    binarised = img
    unique_vals = np.unique(img)
    is_binarized = np.isin(unique_vals, [0, 255]).all()

    h, w = img.shape
    brightness = int(img.mean())
    if (ctx.steps):
        print("Image mean brightness", brightness)
        print(f"Image dimensions: height: {h}", f"width: {w}")

    # If en-face image, binarise. Else skip binarisation
    if not is_binarized:
        # keep initial darkest 30% and brightest 30% pixels in image
        img = keep_darkest_pixels(img, percentile=30)
        img = keep_brightest_pixels(img, percentile=30)
        if (ctx.steps): ctx.show(img, "keep darkest and lightest")

        if h <= 500:
            tileGridSize = (10, 10)
        if h > 500:
            tileGridSize = (60, 60)

        # very bright   
        if brightness > 140:
            img = apply_clahe(img, clipLimit=1.5, tileGridSize=tileGridSize)
            if (ctx.steps): ctx.show(img, "clahe")
        elif brightness > 100:
            img = apply_clahe(img, clipLimit= 1.5, tileGridSize=tileGridSize)
            if (ctx.steps): ctx.show(img, "clahe")
        elif brightness > 60:
            img = apply_clahe(img, clipLimit=3.0, tileGridSize=tileGridSize)
            if (ctx.steps): ctx.show(img, "clahe")
        else:
        # very dark
            img = apply_clahe(img, clipLimit=4.0, tileGridSize=tileGridSize)
            if (ctx.steps): ctx.show(img, "clahe")


        if h <= 500:
            img = apply_gaussian_blur(img, kernel_size=(3, 3))
        if h > 500:
            img = apply_gaussian_blur(img, kernel_size=(5, 5))
        if (ctx.steps): ctx.show(img, "gaussian blur")


        # apply CLAHE for better contrast
        img = apply_clahe(img, clipLimit=2.0, tileGridSize=(3, 3))
        if (ctx.steps): ctx.show(img, "clahe")


        # percentile thresholding for binarisation
        binarised = threshold(img, 40)

        # visual check
        # if not is_binarized:
        #     plt.imsave("auto_faz_binarised.png", binarised, cmap='gray')
        if (ctx.steps): ctx.show(img, "binarise threshold")


    if h <= 500:
        faz = faz_from_binarised(binarised, ctx, dilate_ks=6, close_ks=3)
    if h > 500:
        faz = faz_from_binarised(binarised, ctx, dilate_ks=7, close_ks=5)
    return faz


def pick_faz_component(lab, stats, faz, ctx,
                       min_area_frac=0.0007,       # min % area of faz relative to image size
                       max_circularity = 0.75):
    """
    Uses scoring system to choose FAZ from candidates
    score considers shape, area, aspect ratio, circularity

    Returns a uint8 mask 0/255 for chosen FAZ, zeros if none (black image).
    """
    H, W = lab.shape
    total_px = float(H * W)
    min_area_px = total_px * float(min_area_frac)
    best_lbl, best_score = 0, -1.0

    for lbl in range(1, stats.shape[0]):  # skip background
        area_px = int(stats[lbl, cv2.CC_STAT_AREA])
        if area_px < min_area_px:
            continue

        comp_mask = (lab == lbl).astype(np.uint8) * 255

        # if candidate touches image border, skip
        x, y, w, h, _ = stats[lbl]
        if x <= 0 or y <= 0 or (x + w) >= W or (y + h) >= H:
            # touches image border — skip this candidate
            continue

        # contour-based shape metrics
        cnts, _ = cv2.findContours(comp_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not cnts:
            continue
        c = max(cnts, key=cv2.contourArea)
        A = cv2.contourArea(c)
        P = cv2.arcLength(c, True)
        if P == 0 or A <= 0:
            continue

        # 1 is a perfect circle
        circularity = float(4.0 * np.pi * A / (P * P))

        # hull is the smallest contour that encloses all points in the candidate boundary
        hull = cv2.convexHull(c)
        A_hull = cv2.contourArea(hull)
        # solidity is how filled in is the hull
        solidity = float(A / (A_hull + 1e-6))

        # shape score: geometric mean of solidity & circularity
        shape = np.sqrt(max(1e-6, solidity) * max(1e-6, circularity))

        area_frac = A / float(H*W)
        # weight of area in score reduced
        area_term = np.sqrt(area_frac)

        # penalty for aspect ratio of major and minor axis
        # 1:1 ratio is circle
        if len(c) >= 5:
            (_, _), (MA, ma), _ = cv2.fitEllipse(c)
            if MA < ma: MA, ma = ma, MA
            aspect = (MA / ma) if ma > 0 else 1.0
        else:
            aspect = 1.0
        aspect_pen = 1.0 / max(1.0, aspect)
        aspect_pen = max(0.5, aspect_pen)

        # cap candidates if too much like a perfect circle
        circ_cap_pen = 1.0 if circularity < max_circularity else 0.3

        # scoring
        score = shape * area_term * aspect_pen * circ_cap_pen

        if (ctx.steps or ctx.candidate):
            overlay = cv2.cvtColor(faz, cv2.COLOR_GRAY2BGR)
            cv2.drawContours(overlay, [c], -1, (0,255,0), 1)
            plt.imshow(overlay)
            plt.title(
                f"lbl={lbl} area={A:.0f} area_term={area_term:.2f} circ={circularity:.2f} "
                f"sol={solidity:.2f} aspect={aspect:.2f} shape={shape:.2f}\n"
                f"aspect_pen={aspect_pen:.2f} circ_cap_pen={circ_cap_pen:.2f} score={score:.4e}"
            )
            plt.axis('off'); plt.show()
        
        if score > best_score:
            best_score, best_lbl = score, lbl
            if ctx.steps or ctx.candidate:
                print(f"new best lbl:{best_lbl}, score:{best_score}")

    if best_lbl == 0:
        print(f"{ctx.filename}: No candidates passed filters. Consider changing parameters/penalties.")
        return np.zeros((H, W), dtype=np.uint8)

    return (lab == best_lbl).astype(np.uint8) * 255


def faz_from_binarised(binarised, ctx, dilate_ks=7, close_ks=7):
    """Convert a binarized vessel map into a cleaned FAZ candidate mask."""

    Kd = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (dilate_ks, dilate_ks))
    walls = cv2.dilate(binarised, Kd, 1)
    if (ctx.steps): ctx.show(walls, "dilate vessel walls")

    if close_ks:
        Kc = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (close_ks, close_ks))
        walls = cv2.morphologyEx(walls, cv2.MORPH_CLOSE, Kc, 1)
    if (ctx.steps): ctx.show(walls, "close vessel walls")
    
    # make non-vessel spaces white
    inv = cv2.bitwise_not(walls)
    if (ctx.steps): ctx.show(inv, "binary inversion")

    # flood fill from the image corners
    # eliminates any white regions that are connected to the corners, this reduces no. of FAZ candidates for later
    # (we assume these are not FAZ as image would be very off centred)
    # rare chance that FAZ is still unbounded and is filled in to black
    # this also overcomes some artifacts (large completely black areas in the image)
    ff = inv.copy()
    h, w = ff.shape
    ff = flood_fill(ff)
    if (ctx.steps): ctx.show(ff, "flood fill")

    # enclose any white regions left (candidate FAZ)
    num, lab, stats, _ = cv2.connectedComponentsWithStats((ff>0).astype(np.uint8), 8)
    if num <= 1: # no region found
        return np.zeros_like(binarised)

    # score candidates and pick 'best' FAZ
    if h <= 500:
        faz = pick_faz_component(lab, stats, ff, ctx, min_area_frac=0.002, max_circularity=0.75)
    if h > 500:
        faz = pick_faz_component(lab, stats, ff, ctx, min_area_frac=0.0007, max_circularity=0.75)
    if (ctx.steps): ctx.show(faz, "pick faz from candidates")

    # fill holes inside + light smooth
    faz = fill_holes_and_smooth(faz)
    if (ctx.steps): ctx.show(faz, "fill specks, lightly smooth edge boundary")

    # take away any protusions coming out from main blob
    # protrusions must be > rad to survive pruning
    faz = remove_protusions(faz, rad=2)
    if (ctx.steps): ctx.show(faz, "remove protrusions")

    # light morphological dilation and closing again to smoothen edge
    faz = expand_and_round(faz, grow_px=1, smooth_ks=1)
    if (ctx.steps): ctx.show(faz, "light dilation and closing")

    # to counter dilation and closing that may split the FAZ the multiple white blobs,
    # keep largest white region
    faz = keep_largest(faz)
    if (ctx.steps): ctx.show(faz, "keep largest white region")
    
    return faz
