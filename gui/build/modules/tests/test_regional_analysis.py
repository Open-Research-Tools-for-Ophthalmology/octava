import os
import sys
import numpy as np
import tifffile as tiff
import scipy.io as sio
import matplotlib.pyplot as plt

target_py_dir = "/Users/milameteor/Library/CloudStorage/OneDrive-UWA/M4 Backup/dev/octava/individual image/first-image/5000/regional_validation"

target_matlab_dir = "/Users/milameteor/Library/CloudStorage/OneDrive-UWA/M4 Backup/dev/octava/source/5000/regional_validation"

current_dir = os.getcwd()  # current working directory
comparison_results_path = os.path.join(current_dir, "regional_analysis_comparison_results")

os.makedirs(comparison_results_path, exist_ok=True)

square_grid_list_py = [f for f in sorted(os.listdir(target_py_dir)) if "Square grid" in f]
square_grid_pngs_py = [f for f in square_grid_list_py if f.endswith(".png")]
square_grid_nps = [f for f in square_grid_list_py if f.endswith(".npz")]


square_grid_list_m = [f for f in sorted(os.listdir(target_matlab_dir)) if "Square grid" in f]
square_grid_pngs_m = [f for f in square_grid_list_m if f.endswith(".png")]
square_grid_mats = [f for f in square_grid_list_m if f.endswith(".mat")]
print("square_grid_mats:", square_grid_mats)

# print("Square grid PNGs:", square_grid_pngs)
# print("Square grid NPZs:", square_grid_nps)

# for file in square_grid_pngs:

TYPES_OF_DATA = ["imgRegion", "binaryRegion", "skelRegion"]

def load_data_from_npz(npz_path: str, data_type: str) -> np.ndarray:
    d = np.load(npz_path)
    if data_type not in d:
        raise KeyError(f"'{data_type}' not found in {npz_path}. Keys: {list(d.keys())}")
    arr = d[data_type]
    return arr


def load_data_from_mat(mat_path: str, data_type: str) -> np.ndarray:
    d = sio.loadmat(mat_path)
    if data_type not in d:
        keys = [k for k in d.keys() if not k.startswith("__")]
        raise KeyError(f"'{data_type}' not found in {mat_path}. Keys: {keys}")
    arr = d[data_type]
    return arr


def squeeze_to_2d(a: np.ndarray) -> np.ndarray:
    """
    Make arrays comparable:
    - drop singleton dims
    - if accidentally loaded as HxWx1 or 1xHxW etc, squeeze fixes it
    """
    a = np.asarray(a)
    a = np.squeeze(a)
    if a.ndim != 2:
        raise ValueError(f"Expected 2D image after squeeze, got shape {a.shape}")
    return a


def compare_and_plot(Y_mat: np.ndarray, Y_py: np.ndarray, title: str, atol=0, rtol=0):
    """
    If images are uint8 and should match exactly, keep atol=rtol=0.
    If you expect slight float differences, set e.g. atol=1 or rtol=1e-6.
    """
    # Convert to common dtype for comparison
    # (If both are uint8, equality is exact; if float, isclose is better.)
    if np.issubdtype(Y_mat.dtype, np.integer) and np.issubdtype(Y_py.dtype, np.integer) and atol == 0 and rtol == 0:
        mismatch = (Y_mat != Y_py)
    else:
        mismatch = ~np.isclose(Y_mat.astype(np.float32), Y_py.astype(np.float32), atol=atol, rtol=rtol)

    plt.figure(figsize=(12, 6))
    plt.suptitle(title, y=0.90, fontsize=16)

    plt.subplot(1, 3, 1)
    plt.imshow(Y_mat, cmap='gray')
    plt.title('MATLAB output')
    plt.axis('off')

    plt.subplot(1, 3, 2)
    plt.imshow(Y_py, cmap='gray')
    plt.title('Python output')
    plt.axis('off')

    plt.subplot(1, 3, 3)
    # mismatch is True where different; show True as bright
    plt.imshow(mismatch, cmap='hot')
    plt.title(f'Difference mask (mismatches: {mismatch.sum()})')
    plt.axis('off')

    plt.tight_layout(rect=[0, 0, 1, 1])
    plt.savefig(os.path.join(comparison_results_path, f"{title}.png"), dpi=300)
    plt.show()

    # Optional: print quick stats
    total = mismatch.size
    print(f"{title}: mismatches={mismatch.sum()}/{total} ({100*mismatch.mean():.3f}%)")


# --- Traverse both lists in lockstep ---
for npz_name, mat_name in zip(square_grid_nps, square_grid_mats):
    npz_path = os.path.join(target_py_dir, npz_name)
    mat_path = os.path.join(target_matlab_dir, mat_name)
    region_name = npz_name.replace("_data.npz", "") # Extract region name from filename

    for type in TYPES_OF_DATA:

      # Load arrays
      Y_py = load_data_from_npz(npz_path, type)
      Y_mat = load_data_from_mat(mat_path, type)

      # Make sure they are 2D
      Y_py = squeeze_to_2d(Y_py)
      Y_mat = squeeze_to_2d(Y_mat)

      # If one is float 0..1 and the other uint8 0..255, normalize here.
      # Comment this block out if both are already comparable.
      if Y_py.dtype != np.uint8 and np.nanmax(Y_py) <= 1.0:
          Y_py = (np.clip(Y_py, 0, 1) * 255).astype(np.uint8)
      if Y_mat.dtype != np.uint8 and np.nanmax(Y_mat) <= 1.0:
          Y_mat = (np.clip(Y_mat, 0, 1) * 255).astype(np.uint8)

      # If shapes mismatch, you’ll need to debug your cropping rules.
      if Y_py.shape != Y_mat.shape:
          print(f"SHAPE MISMATCH for {npz_name} vs {mat_name}: py={Y_py.shape}, mat={Y_mat.shape}")
          continue

      compare_and_plot(Y_mat, Y_py, title=f"{region_name}-{type} Comparison", atol=0, rtol=0)