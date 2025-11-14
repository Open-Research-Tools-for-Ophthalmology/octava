import os 
import tifffile as tiff
import numpy as np
from fuzzy_thresholding import fuzzy_thresholding
from scipy.io import loadmat
import matplotlib.pyplot as plt

current_dir = os.getcwd()
target_dir = os.path.join(current_dir, 'gui', 'build')
Xraw = tiff.imread('/Users/milameteor/Library/CloudStorage/OneDrive-UWA/M4 Backup/LEI/to_be_rename/MILA_renamed/test/5000.tif')  # this might be 2D or 3D

# Match the MATLAB preprocessing:
if Xraw.ndim == 2:
    X = Xraw
elif Xraw.ndim == 3:
    if Xraw.shape[2] == 3:
        # RGB -> grayscale; approximate rgb2gray, or use exact weights if you care
        X = Xraw.mean(axis=2)
    else:
        # multi-slice -> take first slice
        X = Xraw[:, :, 0]
else:
    raise ValueError(f"Unsupported image shape: {Xraw.shape}")

X = X.astype(np.float64)
Y_py = fuzzy_thresholding(X, nth=2, w=3)
np.save(os.path.join(target_dir, 'fuzzy_python_result.npy'), Y_py)

# ---------------------------------------------------------------------
# 1. Load MATLAB and Python outputs
# ---------------------------------------------------------------------

mat = loadmat(os.path.join(target_dir, 'fuzzy_matlab_result.mat'))   # MATLAB saved: save('fuzzy_matlab_result.mat', 'Y_mat', ...)
Y_mat = mat['Y_mat']

Y_py = np.load(os.path.join(target_dir, 'fuzzy_python_result.npy'))  # Python saved via np.save(...)

print("MATLAB shape:", Y_mat.shape)
print("Python shape:", Y_py.shape)

if Y_mat.shape != Y_py.shape:
    print("ERROR: Shapes DO NOT match — comparison invalid.")
    exit()

# ---------------------------------------------------------------------
# 2. STRICT pixelwise equality
# ---------------------------------------------------------------------

strict_equal = (Y_mat == Y_py)
strict_agreement = strict_equal.mean()

print("\n=== Strict Equality ===")
print(f"Pixelwise agreement: {strict_agreement:.6f}")
print(f"Different pixels:    {np.sum(~strict_equal)}")

# ---------------------------------------------------------------------
# 3. Tolerance-based comparison for floating-point arrays
#    (Use this for debugging intermediate outputs like gX, Xtrap3, etc.)
# ---------------------------------------------------------------------

tol = 1e-5  # tolerance for "equal" labels (if floats occur)

float_close = np.isclose(Y_mat, Y_py, rtol=0.0, atol=tol)
float_agreement = float_close.mean()

print("\n=== Tolerance-Based Equality (|Δ| <= {:.1e}) ===".format(tol))
print(f"Agreement:           {float_agreement:.6f}")
print(f"Different pixels:    {np.sum(~float_close)}")

# ---------------------------------------------------------------------
# 4. Allow labels to differ by ±k (label tolerance)
# ---------------------------------------------------------------------

k = 1  # allow labels to be off by up to ±1
label_close = np.abs(Y_mat - Y_py) <= k
label_agreement = label_close.mean()

print(f"\n=== Label Off-by-k Comparison (k = {k}) ===")
print(f"Agreement:           {label_agreement:.6f}")
print(f"Different pixels:    {np.sum(~label_close)}")

# ---------------------------------------------------------------------
# 5. Visualization of differences
# ---------------------------------------------------------------------

plt.figure(figsize=(12,4))

plt.subplot(1,3,1)
plt.imshow(Y_mat, cmap='nipy_spectral')
plt.title('MATLAB result')
plt.axis('off')

plt.subplot(1,3,2)
plt.imshow(Y_py, cmap='nipy_spectral')
plt.title('Python result')
plt.axis('off')

plt.subplot(1,3,3)
plt.imshow(~strict_equal, cmap='gray')
plt.title('Strict diff (white = mismatch)')
plt.axis('off')

plt.tight_layout()
plt.show()
