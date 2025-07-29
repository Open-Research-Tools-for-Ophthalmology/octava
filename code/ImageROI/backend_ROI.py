# backend_ROI.py
"""
Backend logic for GUI-based ROI cropping and management.
This module implements the Python equivalent logic for the `doneButtonPushed` MATLAB callback,
cropping an image based on user-selected ROI properties.
"""

import numpy as np
from typing import Tuple, Dict, Any, Optional

class ROIProcessor:
    """
    Class handling ROI cropping and metadata extraction logic.
    """

    def __init__(
        self, 
        image: np.ndarray,  # might need to adjust image format, but I'd say this is fine if we use skimage.io.imread
        roi_shape: str = 'rect',
        rect: Optional[Dict[str, int]] = None, 
        circle: Optional[Dict[str, int]] = None
    ):
        """
        Initialize ROIProcessor.
        
        Args:
            image (np.ndarray): The full image to crop from (2D, grayscale).
            roi_shape (str): Type of ROI shape, 'rect' or 'round'.
            rect (dict, optional): {'x': x0, 'y': y0, 'width': w, 'height': h} if shape is rectangle.
            circle (dict, optional): {'cx': xc, 'cy': yc, 'r': radius} if shape is round.
        """
        assert image is not None, "Image not provided or not available"
        self.original_image = image
        self.input_image = image.copy()
        self.roi_shape = roi_shape
        self.rect = rect
        self.circle = circle

        # Outputs set after crop_roi()
        self.cropped_image: Optional[np.ndarray] = None
        self.fullImSizePix: Optional[int] = None
        self.FAZ_ctr: Optional[Tuple[float, float]] = None
        self.imgShape: str = roi_shape

    def crop_roi(self, resize: bool = True) -> Dict[str, Any]:
        """
        Apply crop or mask to image based on ROI.
        
        Args:
            resize (bool): Whether to update fullImSizePix with ROI width (rect) or diameter (circle).
        
        Returns:
            Dict with keys:
                'cropped_image': np.ndarray of ROI sub-image
                'fullImSizePix': int (width or diameter in px, if resize True)
                'FAZ_ctr': ROI centroid (tuple, in px)
                'imgShape': 'rect' or 'round'
        """
        if self.roi_shape == 'rect':
            # Expect self.rect to be non-None and properly filled
            assert self.rect is not None, "rect info must be provided for rectangle ROI."

            # handling coordinates as int pixels
            x, y, w, h = (
                int(self.rect["x"]), int(self.rect["y"]), 
                int(self.rect["width"]), int(self.rect["height"])
            )
            
            # Clamp bounds to image
            y_end = min(y + h, self.input_image.shape[0])
            x_end = min(x + w, self.input_image.shape[1])
            y = max(0, y)
            x = max(0, x)
            cropped = self.input_image[y:y_end, x:x_end]
            ctr = (w / 2, h / 2)
            full_size = w if resize else None

        elif self.roi_shape == 'round':
            assert self.circle is not None, "circle info must be provided for round ROI."
            cx, cy, r = int(self.circle["cx"]), int(self.circle["cy"]), int(self.circle["r"])

            # Build circular mask and crop
            mask = np.zeros_like(self.input_image, dtype=bool)
            Y, X = np.ogrid[:self.input_image.shape[0], :self.input_image.shape[1]]
            dist_from_ctr = (X - cx) ** 2 + (Y - cy) ** 2
            mask[dist_from_ctr <= r ** 2] = True

            # Crop to bounding box of circle
            y0 = max(0, cy - r)
            y1 = min(self.input_image.shape[0], cy + r)
            x0 = max(0, cx - r)
            x1 = min(self.input_image.shape[1], cx + r)
            cropped = (self.input_image * mask.astype(self.input_image.dtype))[y0:y1, x0:x1]
            ctr = (cx, cy)
            full_size = r * 2 if resize else None
        else:
            raise ValueError("roi_shape must be 'rect' or 'round'.")

        self.cropped_image = cropped
        self.fullImSizePix = full_size
        self.FAZ_ctr = ctr

        return {
            "cropped_image": cropped,
            "fullImSizePix": full_size,
            "FAZ_ctr": ctr,
            "imgShape": self.roi_shape
        }

    def get_current_roi_size(self) -> Dict[str, Any]:
        """
        Returns ROI size parameters (for display).
        Returns:
            Dict of ROI size (x/y or radius), shape, and center.
        """
        if self.roi_shape == "rect" and self.rect:
            return {
                "x": self.rect["width"],
                "y": self.rect["height"],
                "shape": "rect",
                "center": (self.rect["x"] + self.rect["width"] / 2, self.rect["y"] + self.rect["height"] / 2)
            }
        elif self.roi_shape == "round" and self.circle:
            return {
                "r": self.circle["r"],
                "shape": "round",
                "center": (self.circle["cx"], self.circle["cy"])
            }
        else:
            return {}

    # If you later want to add pixel<->mm conversion, you can add method(s) here.