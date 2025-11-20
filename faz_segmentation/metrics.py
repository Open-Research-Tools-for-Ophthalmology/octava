import numpy as np
import cv2

def bin01(x):
    """
    Convert masks to 0/1 binary format
    """
    return (x > 0).astype(np.uint8)

def largest_contour(mask01):
    """Return the largest external contour (by area)."""
    m255 = (mask01 * 255).astype(np.uint8)
    cnts, _ = cv2.findContours(m255, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return None
    return max(cnts, key=cv2.contourArea)


def pixel_to_physical(area_px, perim_px, ctx, h):
    """Convert FAZ area and perimeter from px into mm^2 and mm."""
    scan_mm = ctx.config['scaling']['scan_size']
    res_px = h

    px_size_mm = scan_mm / res_px
    area_mm2 = area_px * (px_size_mm ** 2)
    perim_mm = perim_px * px_size_mm

    return area_mm2, perim_mm


def shape_metrics(mask):
    """
    Compute area (px), perimeter (px), acircularity, circularity
    for the largest connected component of mask
    Returns zeros if no foreground
    """
    cnt = largest_contour(mask)
    if cnt is None:
        return 0, 0.0, 0.0, 0.0

    area = float(cv2.contourArea(cnt))
    perim = float(cv2.arcLength(cnt, True))

    if area <= 0.0 or perim <= 0.0:
        return 0, 0.0, 0.0, 0.0

    # acircularity (1 = perfect circle, expect >1)
    acirc = perim / (2.0 * np.sqrt(np.pi * area))

    # circularity (1 = perfect circle, expect <1)
    circ = (4.0 * np.pi * area) / (perim * perim)

    return int(round(area)), perim, acirc, circ


def mask_metrics(gt_mask, pred_mask, ctx):
    """
    Calculates metrics: Dice, IoU, Precision, Recall, and Absolute area error (pixels).
    returns the metrics in a dict of floats.
    """
    gt = bin01(gt_mask)
    pr = bin01(pred_mask)
    inter = (gt & pr).sum()
    gt_sum = gt.sum()
    pr_sum = pr.sum()

    dice = (2*inter) / (gt_sum + pr_sum + 1e-9)
    iou  = inter / (gt_sum + pr_sum - inter + 1e-9)
    prec = inter / (pr_sum + 1e-9)
    rec  = inter / (gt_sum + 1e-9)

    pr_area_px, pr_perim_px, pr_acirc, pr_circ = shape_metrics(pr)
    gt_area_px, gt_perim_px, gt_acirc, gt_circ = shape_metrics(gt)

    pr_area_mm2, pr_perim_mm2 = pixel_to_physical(pr_area_px, pr_perim_px, ctx, pred_mask.shape[0])
    gt_area_mm2, gt_perim_mm2 = pixel_to_physical(gt_area_px, gt_perim_px, ctx, pred_mask.shape[0])
    
    # incorrect segmentation
    # values are nan - does not contribute to final stat summaries
    if dice < 0.05 or iou < 0.025:
        dice = np.nan
        iou = dice = np.nan
        prec = np.nan
        rec = np.nan
        area_diff_pct = np.nan
        pr_area_px = np.nan
        pr_perim_px = np.nan
        pr_area_mm2 = np.nan
        pr_perim_mm2 = np.nan
        pr_acirc = np.nan
        pr_circ = np.nan

    else:
        area_diff_pct = abs(pr_area_mm2 - gt_area_mm2) / (gt_area_mm2 + 1e-9) * 100.0

    return {
        "dice": float(dice),
        "iou": float(iou),
        "precision": float(prec),
        "recall": float(rec),
        "area_difference_pct": float(area_diff_pct),
        "pred_faz_area_px2": float(pr_area_px),
        "pred_faz_perim_px": float(pr_perim_px),
        "pred_faz_area_mm2": float(pr_area_mm2),
        "pred_faz_perimeter_mm": float(pr_perim_mm2),
        "pred_faz_acircularity": float(pr_acirc),
        "pred_faz_circularity": float(pr_circ),
    }
