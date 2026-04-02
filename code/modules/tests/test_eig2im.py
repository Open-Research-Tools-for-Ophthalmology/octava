# eig2im_test_python.py
import os
import sys
import numpy as np
from scipy.io import loadmat, savemat

# Adjust sys.path to import eig2im from the parent folder
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir  = os.path.abspath(os.path.join(current_dir, os.pardir))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Now import the Python eig2im implementation
from eig2im import eig2im

# 1. Set the target directory (must match MATLAB)
target_dir = "/Users/milameteor/Library/CloudStorage/OneDrive-UWA/M4 Backup/dev/octava/code/modules/tests"
os.makedirs(target_dir, exist_ok=True)

# 2. Sigma values to test
sigma_values = [1, 3]

# 3. Load Hessian components from the MATLAB test and run eig2im
for sigma in sigma_values:
    hfile = os.path.join(target_dir, f"hessian_matlab_sigma{sigma}.mat")
    data  = loadmat(hfile)
    Dxx, Dxy, Dyy = data["Dxx"], data["Dxy"], data["Dyy"]
    
    # Compute eigenvectors and eigenvalues (Python version)
    X, Y, m2, m1 = eig2im(Dxx, Dxy, Dyy)
    
    outfile = os.path.join(target_dir, f"eig2im_python_sigma{sigma}.mat")
    savemat(outfile, {"X": X, "Y": Y, "m1": m1, "m2": m2})
    print(f"Saved Python eig2im outputs for sigma={sigma} to {outfile}")


# compare_eig2im_results.py
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
    # Load MATLAB eig2im results
    matlab_data = loadmat(os.path.join(target_dir, f"eig2im_matlab_sigma{sigma}.mat"))
    X_mat, Y_mat = matlab_data["X"], matlab_data["Y"]
    m1_mat, m2_mat = matlab_data["m1"], matlab_data["m2"]
    
    # Load Python eig2im results
    python_data = loadmat(os.path.join(target_dir, f"eig2im_python_sigma{sigma}.mat"))
    X_py, Y_py = python_data["X"], python_data["Y"]
    m1_py, m2_py = python_data["m1"], python_data["m2"]
    
    # Check shapes
    assert X_mat.shape == X_py.shape, f"X shape mismatch for sigma={sigma}"
    assert Y_mat.shape == Y_py.shape, f"Y shape mismatch for sigma={sigma}"
    assert m1_mat.shape == m1_py.shape, f"m1 shape mismatch for sigma={sigma}"
    assert m2_mat.shape == m2_py.shape, f"m2 shape mismatch for sigma={sigma}"
    
    # Function to compare arrays
    def compare_component(name, A_mat, A_py):
        strict_eq   = (A_mat == A_py)
        strict_agree = strict_eq.mean()
        float_close  = np.isclose(A_mat, A_py, atol=tol)
        float_agree  = float_close.mean()
        print(f"\nSigma = {sigma}, Component = {name}:")
        print(f"  Strict match:   {strict_agree:.6f}")
        print(f"  Tol match:      {float_agree:.6f} (tol={tol})")
        print(f"  Max abs diff:   {np.max(np.abs(A_mat - A_py)):.3e}")
        
        # Optional visualization
        plt.figure(figsize=(8, 3))
        plt.suptitle(f"Sigma {sigma} - {name}")
        plt.subplot(1,3,1); plt.imshow(A_mat, cmap='gray'); plt.title('MATLAB'); plt.axis('off')
        plt.subplot(1,3,2); plt.imshow(A_py, cmap='gray'); plt.title('Python'); plt.axis('off')
        plt.subplot(1,3,3); plt.imshow(~float_close, cmap='hot'); plt.title('Mismatch'); plt.axis('off')
        plt.tight_layout(); plt.show()
    
    # Compare all outputs
    compare_component('X', X_mat, X_py)
    compare_component('Y', Y_mat, Y_py)
    compare_component('m1', m1_mat, m1_py)
    compare_component('m2', m2_mat, m2_py)
