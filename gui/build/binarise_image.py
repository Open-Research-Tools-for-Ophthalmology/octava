import numpy as np
from scipy.ndimage import median_filter

# Placeholder fuzzy thresholding
def fuzzy_thresholding(image: np.ndarray, nth: int = 2, param: int = 3) -> np.ndarray:
    """
    Example fuzzy thresholding placeholder.
    Replace with your actual fuzzy thresholding implementation.
    """
    # Simple stand-in using mean intensity as threshold
    thresh = image.mean()
    binary = (image > thresh).astype(np.uint8)
    return binary

def binarize_image(canvas):
    """
    Binarize canvas.img_original using fuzzy thresholding.
    - Ensures vessels are white (255) and background black (0).
    - Optionally applies median filter.
    - Optionally applies Frangi filter (stub).
    Stores result in canvas.BinaryImage.
    """

    # --- Locate brightest vessel pixel ---
    y = canvas.img_original[1:, 1:].max(axis=0)
    cc = y.argmax()
    rr = canvas.img_original[1:, cc].argmax()

    cc += 1
    rr += 1

    # --- Apply median filter if selected ---
    if getattr(canvas, "MedfiltCheckBox", False) and canvas.MedfiltCheckBox:
        ksize = int(canvas.kernelSize)  # assuming scalar
        Im = median_filter(canvas.img_original, size=(ksize, ksize))
    else:
        Im = canvas.img_original

    # --- Apply Frangi filter if selected (stub) ---
    if getattr(canvas, "frangi_bool", False) and canvas.frangi_bool:
        print("Frangi filter selected — not yet implemented, using input image.")
        opts = {
            'sigmamin': 1,
            'sigmamax': int(canvas.sigma_max),
            'sigmastepsize': 2,
            'correctionconst1': 0.8,
            'correctionconst2': 15
        }
        #todo: Im = frangi_2Dfilter(Im, opts)

    # --- Always use Fuzzy Means ---
    nth = 2
    BinaryImage = fuzzy_thresholding(Im, nth, 3)

    # --- Convert to 255 (white vessels) and 0 (black background) ---
    ref_value = BinaryImage[rr, cc]
    BinaryImage = np.where(BinaryImage == ref_value, 255, 0).astype(np.uint8)

    # --- Store result back to canvas ---
    canvas.BinaryImage = BinaryImage

    #todo: display the binarized image on the canvas