###################################
# THIS MUST BE REVISED AND TESTED #
###################################

import numpy as np
from typing import Dict, Any, Tuple, Union

def create_rectangle_roi(x: int, y: int, width: int, height: int) -> Dict[str, Any]:
    """Return a dict representing a rectangle ROI."""
    return {'type': 'rectangle', 'x': x, 'y': y, 'width': width, 'height': height}

def create_circle_roi(cx: int, cy: int, radius: int) -> Dict[str, Any]:
    """Return a dict representing a circular ROI."""
    return {'type': 'circle', 'cx': cx, 'cy': cy, 'radius': radius}

def apply_roi(image: np.ndarray, roi: Dict[str, Any],
              resize_to_roi: bool = False) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Apply ROI (rectangle or circle) to image as in OCTAVA's MATLAB logic.
    If resize_to_roi is True, output is always cropped to minimal bounding box.
    Returns:
        processed_image
        metadata: dict with fields like 'fullImSizePix', 'FAZ_ctr', 'imgShape'
    """
    meta = {}
    if roi['type'] == 'rectangle':
        # Clamp to image bounds
        x = max(0, roi['x'])
        y = max(0, roi['y'])
        x2 = min(image.shape[1], x + roi['width'])
        y2 = min(image.shape[0], y + roi['height'])
        cropped_img = image[y:y2, x:x2]
        meta['imgShape'] = 'rect'
        meta['fullImSizePix'] = roi['width'] if resize_to_roi else None
        meta['FAZ_ctr'] = [roi['width'] / 2, roi['height'] / 2]
        return cropped_img, meta

    elif roi['type'] == 'circle':
        # Create mask
        cx, cy, r = roi['cx'], roi['cy'], roi['radius']
        Y, X = np.ogrid[:image.shape[0], :image.shape[1]]
        mask = ((X - cx) ** 2 + (Y - cy) ** 2) <= r ** 2
        masked_img = image * mask
        # Crop to minimal bounding box around circle
        x1 = max(0, int(cx - r))
        y1 = max(0, int(cy - r))
        x2 = min(image.shape[1], int(cx + r))
        y2 = min(image.shape[0], int(cy + r))
        cropped_img = masked_img[y1:y2, x1:x2]
        meta['imgShape'] = 'circle'
        meta['fullImSizePix'] = 2 * r if resize_to_roi else None
        meta['FAZ_ctr'] = [cx, cy]
        return cropped_img, meta

    else:
        raise ValueError("Unknown ROI type: {}".format(roi['type']))

# Example usage -------------------------------------------------------

if __name__ == '__main__':
    # Example: load a dummy image (replace with image loading code)
    img = np.zeros((500, 400), dtype=np.uint8)
    img[100:400, 50:350] = 255

    # === Example #1: Rectangle ROI defined by user ===
    rect_roi = create_rectangle_roi(x=60, y=120, width=200, height=150)
    img_rect, meta_rect = apply_roi(img, rect_roi, resize_to_roi=True)
    print("Rectangle ROI results:")
    print("  Cropped shape:", img_rect.shape)
    print("  Metadata:", meta_rect)

    # === Example #2: Circle ROI defined by user ===
    circ_roi = create_circle_roi(cx=200, cy=250, radius=80)
    img_circ, meta_circ = apply_roi(img, circ_roi, resize_to_roi=True)
    print("Circle ROI results:")
    print("  Cropped shape:", img_circ.shape)
    print("  Metadata:", meta_circ)

    # You can now pass img_rect or img_circ to downstream analysis
    # For visualization/testing:
    # import matplotlib.pyplot as plt
    # plt.imshow(img_rect, cmap='gray'); plt.show()
    # plt.imshow(img_circ, cmap='gray'); plt.show()