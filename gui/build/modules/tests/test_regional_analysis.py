import os
import sys
import numpy as np
from scipy import stats
import tifffile as tiff
import scipy.io as sio
import matplotlib.pyplot as plt
import pandas as pd
from enum import Enum

class GridType(Enum):
	SQUARE_GRID = "Square grid"
	ETDRS_GRID = "ETDRS grid"
	EXTENDED_ETDRS_GRID = "Extended"
	ONH = "ONH"
	FOVEAL_RING = "Foveal rings"

results=[]

target_py_dir = "/Users/milameteor/Library/CloudStorage/OneDrive-UWA/M4 Backup/dev/octava/individual image/first-image/5000/regional_validation"

target_matlab_dir = "/Users/milameteor/Library/CloudStorage/OneDrive-UWA/M4 Backup/dev/octava/source/5000/regional_validation"

current_dir = "/Users/milameteor/Library/CloudStorage/OneDrive-UWA/M4 Backup/dev/octava/gui/build/modules/tests"  # current working directory
comparison_results_path = os.path.join(current_dir, "regional_analysis_comparison_results")

os.makedirs(comparison_results_path, exist_ok=True)

# square_grid_list_py = [f for f in sorted(os.listdir(target_py_dir)) if "Square grid" in f]
# square_grid_pngs_py = [f for f in square_grid_list_py if f.endswith(".png")]
# square_grid_nps = [f for f in square_grid_list_py if f.endswith(".npz")]


# square_grid_list_m = [f for f in sorted(os.listdir(target_matlab_dir)) if "Square grid" in f]
# square_grid_pngs_m = [f for f in square_grid_list_m if f.endswith(".png")]
# square_grid_mats = [f for f in square_grid_list_m if f.endswith(".mat")]


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

def compare_and_plot(
    Y_mat: np.ndarray,
    Y_py: np.ndarray,
    title: str,
    show: bool = True,
    tol: float = 1e-5,
):
    """
    Compares MATLAB vs Python images with:
      1) strict equality (==)
      2) tolerance-based equality (isclose with atol=tol)

    Saves a 1x3 figure (MATLAB, Python, mismatch mask) with agreement stats.
    Returns a dict of stats + the mismatch mask (tolerance-based).
    """

    # Ensure arrays are comparable shapes
    # if Y_mat.shape != Y_py.shape:
    #     raise ValueError(f"Shape mismatch: MATLAB {Y_mat.shape} vs Python {Y_py.shape}")


    if Y_mat.shape != Y_py.shape:
        mismatch = np.ones((max(Y_mat.shape[0], Y_py.shape[0]), max(Y_mat.shape[1], Y_py.shape[1])), dtype=bool)
        print(f"For {title}, shape mismatch: MATLAB {Y_mat.shape} vs Python {Y_py.shape}")
        strict_agreement = 0.0
    else:
        # --- 1) Strict equality ---
        strict_equal = (Y_mat == Y_py)
        strict_agreement = float(strict_equal.mean())
        strict_diff = int(np.sum(~strict_equal))

        # --- 2) Tolerance-based equality ---
        # Use float32 for stable numeric comparison
        float_close = np.isclose(
            Y_mat.astype(np.float32),
            Y_py.astype(np.float32),
            atol=tol,
            rtol=0.0
        )
        float_agreement = float(float_close.mean())
        float_diff = int(np.sum(~float_close))

        # Mismatch mask for plotting (True = mismatch)
        mismatch = ~float_close

    try:
        # --- Plot ---
        plt.figure(figsize=(12, 6))
        plt.suptitle(title, y=0.95, fontsize=16)

        plt.subplot(1, 3, 1)
        plt.imshow(Y_mat, cmap="gray")
        plt.title("MATLAB output")
        plt.axis("off")

        plt.subplot(1, 3, 2)
        plt.imshow(Y_py, cmap="gray")
        plt.title("Python output")
        plt.axis("off")

        plt.subplot(1, 3, 3)
        plt.imshow(mismatch, cmap="hot")
        plt.title("Difference mask (mismatches in white)")
        plt.axis("off")

        plt.tight_layout(rect=[0, 0.12, 1, 1])  # leave space at bottom for stats text

        if Y_mat.shape == Y_py.shape:
            accuracy_text = (
                f"Strict equality agreement: {strict_agreement:.6f}  |  Diff pixels: {strict_diff}\n"
                f"Tolerance |Δ| <= {tol:.1e} agreement: {float_agreement:.6f}  |  Diff pixels: {float_diff}"
            )

            plt.figtext(
                0.5, 0.04,
                accuracy_text,
                ha="center",
                va="bottom",
                fontsize=11
            )

            print("\n=== Strict Equality ===")
            print(f"Pixelwise agreement: {strict_agreement:.6f}")
            print(f"Different pixels:    {strict_diff}")

            print(f"\n=== Float Tolerance |Δ| <= {tol:.1e} ===")
            print(f"Agreement:           {float_agreement:.6f}")
            print(f"Different pixels:    {float_diff}") 

        # out_name = safe_filename(title) + ".png"
        out_path = os.path.join(comparison_results_path, title+".png")
        plt.savefig(out_path, dpi=300, bbox_inches="tight", pad_inches=0.05)

        if show:
            plt.show()
        else:
            plt.close()
    except Exception as e:
        print(f"Error during plotting/saving for {title}: {e}")
      
    return {
        "strict_agreement": strict_agreement,
        "saved_path": out_path
    }


for grid_type in GridType:
    current_grid_list_py = [f for f in sorted(os.listdir(target_py_dir)) if grid_type.value in f]
    current_grid_pngs_py = [f for f in current_grid_list_py if f.endswith(".png")]
    current_grid_nps = [f for f in current_grid_list_py if f.endswith(".npz")]


    current_grid_list_m = [f for f in sorted(os.listdir(target_matlab_dir)) if grid_type.value in f]
    current_grid_pngs_m = [f for f in current_grid_list_m if f.endswith(".png")]
    current_grid_mats = [f for f in current_grid_list_m if f.endswith(".mat")]

    # --- Traverse both lists in lockstep ---
    for npz_name, mat_name in zip(current_grid_nps, current_grid_mats):
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

          # # If shapes mismatch, you’ll need to debug your cropping rules.
          # if Y_py.shape != Y_mat.shape:
          #     print(f"SHAPE MISMATCH for {npz_name} vs {mat_name}: py={Y_py.shape}, mat={Y_mat.shape}")
          #     continue

          result=compare_and_plot(Y_mat, Y_py, title=f"{region_name}_{type}_Comparison", show=False)

          results.append({
              "region_name": region_name,
              "type": type,
              "strict_agreement": result["strict_agreement"],
              # "saved_path": result["saved_path"]
              })
          
    df = pd.DataFrame(results)
    df.to_csv(
        os.path.join(comparison_results_path, "regional_analysis_comparison.csv"),
        index=False
    )
