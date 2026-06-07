import os
import sys
import numpy as np
import tifffile as tiff
from scipy.io import savemat
# Add parent directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir  = os.path.abspath(os.path.join(current_dir, os.pardir))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Now we can import hessian_filter from the parent folder
from hessian_filter import hessian_filter

# 1. Set the target directory
target_dir = "/Users/milameteor/Library/CloudStorage/OneDrive-UWA/M4 Backup/dev/octava/code/modules/tests"

# 2. Load the .tif image
img_path = "/Users/milameteor/Library/CloudStorage/OneDrive-UWA/M4 Backup/LEI/to_be_rename/MILA_renamed/test/5000.tif"
Iraw = tiff.imread(img_path)

# 3. Convert to grayscale using ITU-R BT.601 weights [oai_citation:1‡mathworks.com](https://www.mathworks.com/help/matlab/ref/rgb2gray.html#:~:text=,R%2C%20G%2C%20and%20B%20components)
if Iraw.ndim == 3:
    if Iraw.shape[2] == 3:
        R, G, B = Iraw[..., 0], Iraw[..., 1], Iraw[..., 2]
        I = 0.298936021293775 * R + 0.587043074451121 * G + 0.114020904255103 * B
    else:
        I = Iraw[:, :, 0]
else:
    I = Iraw
I = I.astype(np.float64)

# 4. Choose the same sigma values
sigma_values = [1, 3]

# 5. Compute and save Hessian components for each sigma
for sigma in sigma_values:
    Dxx, Dxy, Dyy = hessian_filter(I, sigma)
    filename = os.path.join(target_dir, f"hessian_python_sigma{sigma}.mat")
    savemat(filename, {"Dxx": Dxx, "Dxy": Dxy, "Dyy": Dyy})
    print(f"Saved Python Hessian outputs for sigma={sigma} to {filename}")


# compare_hessian_results.py
import os
import numpy as np
from scipy.io import loadmat
import matplotlib.pyplot as plt

# 1. Set the target directory
target_dir = '/Users/milameteor/Library/CloudStorage/OneDrive-UWA/M4 Backup/dev/octava/code/modules/tests'

# 2. Sigma values to compare
sigma_values = [1, 3]

# 3. Tolerance for floating‑point equality
tol = 1e-5

for sigma in sigma_values:
    # Load MATLAB output
    matlab_data = loadmat(os.path.join(target_dir, f"hessian_matlab_sigma{sigma}.mat"))
    Dxx_mat, Dxy_mat, Dyy_mat = matlab_data["Dxx"], matlab_data["Dxy"], matlab_data["Dyy"]

    # Load Python output
    python_data = loadmat(os.path.join(target_dir, f"hessian_python_sigma{sigma}.mat"))
    Dxx_py, Dxy_py, Dyy_py = python_data["Dxx"], python_data["Dxy"], python_data["Dyy"]

    # Compare shapes
    assert Dxx_mat.shape == Dxx_py.shape, f"Shape mismatch for sigma={sigma}"
    assert Dxy_mat.shape == Dxy_py.shape, f"Shape mismatch for sigma={sigma}"
    assert Dyy_mat.shape == Dyy_py.shape, f"Shape mismatch for sigma={sigma}"

    # Function to print equality metrics
    def compare_and_print(name, A_mat, A_py):
        """Print error statistics and show a mismatch visualization for one Hessian component."""
        strict_equal   = (A_mat == A_py)
        strict_agree   = strict_equal.mean()
        float_close    = np.isclose(A_mat, A_py, atol=tol)
        float_agree    = float_close.mean()
        print(f"\nSigma = {sigma}, Component = {name}")
        print(f"Strict agreement:   {strict_agree:.6f}")
        print(f"Tolerance match:    {float_agree:.6f} (tol={tol})")
        print(f"Max abs difference: {np.abs(A_mat - A_py).max():.3e}")

        # Visualization
        plt.figure(figsize=(8, 3))
        plt.suptitle(f"Sigma {sigma} - {name}")
        plt.subplot(1,3,1); plt.imshow(A_mat, cmap='gray'); plt.title('MATLAB'); plt.axis('off')
        plt.subplot(1,3,2); plt.imshow(A_py, cmap='gray'); plt.title('Python'); plt.axis('off')
        plt.subplot(1,3,3); plt.imshow(~float_close, cmap='hot'); plt.title('Mismatch'); plt.axis('off')
        plt.tight_layout(); plt.show()

    # Compare each derivative component
    compare_and_print('Dxx', Dxx_mat, Dxx_py)
    compare_and_print('Dxy', Dxy_mat, Dxy_py)
    compare_and_print('Dyy', Dyy_mat, Dyy_py)
