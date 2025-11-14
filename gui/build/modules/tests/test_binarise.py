# frangi_test_python.py
import os
import sys
import numpy as np
import tifffile as tiff
from scipy.io import savemat

# Make sure we can import frangi_2Dfilter, hessian_filter, eig2im from parent directory
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir  = os.path.abspath(os.path.join(current_dir, os.pardir))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from basic_binarise import *

# 1. Set the output directory
target_dir = "/Users/milameteor/Library/CloudStorage/OneDrive-UWA/M4 Backup/dev/octava/gui/build/modules/tests"
os.makedirs(target_dir, exist_ok=True)

# 2. Load and convert the image to grayscale using ITU-R BT.601 weights [oai_citation:1‡mathworks.com](https://www.mathworks.com/help/matlab/ref/rgb2gray.html#:~:text=,R%2C%20G%2C%20and%20B%20components)
img_path = "/Users/milameteor/Library/CloudStorage/OneDrive-UWA/M4 Backup/LEI/to_be_rename/MILA_renamed/test/5000.tif"
Iraw = tiff.imread(img_path)
if Iraw.ndim == 3:
    if Iraw.shape[2] == 3:
        R, G, B = Iraw[..., 0], Iraw[..., 1], Iraw[..., 2]
        I = 0.298936021293775 * R + 0.587043074451121 * G + 0.114020904255103 * B
    else:
        I = Iraw[:, :, 0]
else:
    I = Iraw
I = I.astype(np.float64)

# 4. Run 
np.random.seed(0)
Y_py = basic_binarise(I)

# 5. Save output
savemat(os.path.join(target_dir, 'binarise_python_result.mat'), {'Y_py': Y_py})
np.save(os.path.join(target_dir, 'binarise_python_result.npy'), Y_py)
print(f"Saved Python Binarise output to {target_dir}")

# compare_frangi_results.py
import os
import numpy as np
from scipy.io import loadmat
import matplotlib.pyplot as plt

# Directory where test results are saved
target_dir = '/Users/milameteor/Library/CloudStorage/OneDrive-UWA/M4 Backup/dev/octava/gui/build/modules/tests'

# Load MATLAB result
Y_mat = loadmat(os.path.join(target_dir, 'binarise_matlab_result.mat'))['Y_mat']
Y_py = loadmat(os.path.join(target_dir, 'binarise_python_result.mat'))['Y_py']
# Load Python result
# Y_py = np.load(os.path.join(target_dir, 'binarise_python_result.npy'))

print("MATLAB shape:", Y_mat.shape)
print("Python shape:", Y_py.shape)
if Y_mat.shape != Y_py.shape:
    raise ValueError("ERROR: Output shapes do not match.")

# 1. Strict equality
strict_equal = (Y_mat == Y_py)
strict_agreement = strict_equal.mean()
print("\n=== Strict Equality ===")
print(f"Pixelwise agreement: {strict_agreement:.6f}")
print(f"Different pixels:    {np.sum(~strict_equal)}")

# 2. Tolerance‑based equality
tol = 1e-5
float_close = np.isclose(Y_mat, Y_py, atol=tol)
float_agreement = float_close.mean()
print(f"\n=== Float Tolerance |Δ| <= {tol:.1e} ===")
print(f"Agreement:           {float_agreement:.6f}")
print(f"Different pixels:    {np.sum(~float_close)}")

# 3. Visualize the outputs and differences
plt.figure(figsize=(12, 4))
plt.subplot(1, 3, 1)
plt.imshow(Y_mat, cmap='gray')
plt.title('MATLAB output')
plt.axis('off')

plt.subplot(1, 3, 2)
plt.imshow(Y_py, cmap='gray')
plt.title('Python output')
plt.axis('off')

plt.subplot(1, 3, 3)
plt.imshow(~float_close, cmap='hot')
plt.title('Difference mask')
plt.axis('off')

plt.tight_layout()
plt.savefig(os.path.join(target_dir, 'binarise_comparison.png'))
plt.show()