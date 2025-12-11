'''
Checked and tested
'''
import numpy as np

def curvature(I: np.ndarray) -> np.ndarray:
    """
    Computes the mean curvature of a 2D grayscale image using finite differences.

    Parameters:
    -----------
    I : np.ndarray
        2D input image (grayscale) as a NumPy array. Should be of shape (m, n).
        The image will be internally converted to float64 for precision.

    Returns:
    --------
    K : np.ndarray
        2D array of the same shape as `I`, representing the normalized curvature
        values at each pixel location. The values are scaled to the range [-1, 1].

    Description:
    ------------
    This function approximates the mean curvature of an image intensity surface φ(x, y)
    using first and second order partial derivatives:
        - ∂φ/∂x and ∂φ/∂y (first derivatives)
        - ∂²φ/∂x², ∂²φ/∂y², and ∂²φ/∂x∂y (second derivatives)
    These are computed using central differences for the interior and one-sided
    differences at the borders.

    The curvature is calculated via the formula:
        K = (φ_xx * φ_y² - 2 * φ_x * φ_y * φ_xy + φ_yy * φ_x²) / (φ_x² + φ_y² + ε)^(3/2)

    The result is normalized by the maximum absolute curvature value to stabilize
    the output for further processing or visualization.
    """
    I = I.astype(np.float64)  # Ensure the image is in float format for precision
    m, n = I.shape  # Get image dimensions

    # First derivatives ∂φ/∂x and ∂φ/∂y
    phix = np.zeros_like(I)
    phiy = np.zeros_like(I)

    # ∂φ/∂x using forward, backward, and central difference
    phix[:, 0] = I[:, 1] - I[:, 0]  # first column: forward difference at left border
    phix[:, -1] = I[:, -1] - I[:, -2]  # last column: backward difference at right border
    phix[:, 1:-1] = 0.5 * (I[:, 2:] - I[:, :-2])  # second column to second last columns: central difference

    # ∂φ/∂y using forward, backward, and central difference
    phiy[0, :] = I[1, :] - I[0, :]  # first row: forward difference at top border
    phiy[-1, :] = I[-1, :] - I[-2, :]  # last row: backward difference at bottom border
    phiy[1:-1, :] = 0.5 * (I[2:, :] - I[:-2, :])  # second to second last rows: central difference

    # Second derivatives ∂²φ/∂x² and ∂²φ/∂y²
    phixx = np.zeros_like(I)
    phiyy = np.zeros_like(I)

    # ∂²φ/∂x²
    phixx[:, 0] = I[:, 2] - 2 * I[:, 1] + I[:, 0]  # left edge
    phixx[:, -1] = I[:, -1] - 2 * I[:, -2] + I[:, -3]  # right edge
    phixx[:, 1:-1] = I[:, :-2] - 2 * I[:, 1:-1] + I[:, 2:]  # central difference

    # ∂²φ/∂y²
    phiyy[0, :] = I[2, :] - 2 * I[1, :] + I[0, :]  # top edge
    phiyy[-1, :] = I[-1, :] - 2 * I[-2, :] + I[-3, :]  # bottom edge
    phiyy[1:-1, :] = I[:-2, :] - 2 * I[1:-1, :] + I[2:, :]  # central difference

    # Mixed partial derivative ∂²φ/∂x∂y (phixy)
    phixy = np.zeros_like(I)

    # Corners
    phixy[0, 0] = I[1, 1] - I[1, 0] - I[0, 1] + I[0, 0]  # upper left
    phixy[0, -1] = I[1, -1] - I[0, -1] - I[1, -2] + I[0, -2]  # upper right
    phixy[-1, 0] = I[-1, 1] - I[-2, 1] - I[-1, 0] + I[-2, 0]  # lower left
    phixy[-1, -1] = I[-1, -1] - I[-2, -1] - I[-1, -2] + I[-2, -2]  # lower right

    # Top row (excluding corners) xyu
    phixy[0, 1:-1] = (I[1, 2:] - I[0, 2:] - I[1, :-2] + I[0, :-2]) / 2

    # Bottom row (excluding corners) xyb
    phixy[-1, 1:-1] = (I[-1, 2:] - I[-2, 2:] - I[-1, :-2] + I[-2, :-2]) / 2

    # Left column (excluding corners) xyl
    phixy[1:-1, 0] = (I[2:, 1] - I[:-2, 1] - I[2:, 0] + I[:-2, 0]) / 2

    # Right column (excluding corners) xyr
    phixy[1:-1, -1] = (I[2:, -1] - I[:-2, -1] - I[2:, -2] + I[:-2, -2]) / 2

    # Center region (chatgpt made a mistake here, it's corrected now)
    phixy[1:-1, 1:-1] = (I[1:-1, 1:-1] - I[:-2, 2:] - I[2:, :-2] - I[:-2, :-2]) / 4

    # Compute curvature using the geometric formula
    numerator = (phixx * phiy**2 - 2 * phix * phiy * phixy + phiyy * phix**2)
    denominator = (phix**2 + phiy**2 + np.finfo(float).eps) ** 1.5
    K = numerator / denominator

    # Normalize curvature to range [-1, 1]
    K /= np.max(np.abs(K))

    return K



if __name__ == "__main__":
    image_path = "/Users/milameteor/Library/CloudStorage/OneDrive-UWA/M4 Backup/LEI/to_be_rename/MILA_renamed/test/5000.tif"

    import cv2
    import numpy as np

    # Load image and convert to grayscale
    I = cv2.imread(image_path)

    if I is None:
        raise ValueError("Image not found!")

    if len(I.shape) == 3:
        I = cv2.cvtColor(I, cv2.COLOR_BGR2GRAY)

    I = I.astype(np.float64)  # Convert to float to match MATLAB
    K_python = curvature(I)

    from scipy.io import loadmat
    from numpy import corrcoef

    data = loadmat('K_matlab.mat')
    K_matlab = data['K_matlab']

    # Ensure same shape
    assert K_matlab.shape == K_python.shape

    cv2.imwrite('K_python.png', ((K_python - K_python.min()) / (K_python.max() - K_python.min()) * 255).astype(np.uint8))

    # Compare difference
    diff = np.abs(K_matlab - K_python)
    print("Max difference:", np.max(diff))
    print("Mean difference:", np.mean(diff))

    # Correlation check
    corr = corrcoef(K_matlab.flatten(), K_python.flatten())[0, 1]
    print("Correlation:", corr)