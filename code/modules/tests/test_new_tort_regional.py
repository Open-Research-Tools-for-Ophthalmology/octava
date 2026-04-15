import glob
import os
import sys
import unittest
from types import SimpleNamespace

import numpy as np
import pandas as pd
import scipy.io as sio


current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from biomarker import BiomarkerAnalyzer


SOURCE_ROOT = "/Users/milameteor/Library/CloudStorage/OneDrive-UWA/M4 Backup/dev/octava/source"
MAT_GLOB = os.path.join(SOURCE_ROOT, "**", "regional_validation", "*_tort_validation.mat")
OUTPUT_XLSX = os.path.join(current_dir, "regional_tortuosity_comparison.xlsx")
TOL = 1e-1


class DummyVar:
    def __init__(self, value):
        self._value = value

    def get(self):
        return self._value


class DummyCanvas(SimpleNamespace):
    pass


def _mat_struct_array(value):
    if value is None:
        return []
    arr = np.atleast_1d(value)
    return [item for item in arr.flat]


def _mat_links_to_python_links(mat_links, shape):
    links = []
    for link in _mat_struct_array(mat_links):
        if hasattr(link, "point"):
            path = np.asarray(link.point).astype(np.int64).ravel() - 1
        elif hasattr(link, "path"):
            path = np.asarray(link.path).astype(np.int64).ravel() - 1
        elif hasattr(link, "x") and hasattr(link, "y"):
            rows = np.asarray(link.x).astype(int).ravel() - 1
            cols = np.asarray(link.y).astype(int).ravel() - 1

            valid = (
                (rows >= 0)
                & (cols >= 0)
                & (rows < shape[0])
                & (cols < shape[1])
            )
            rows = rows[valid]
            cols = cols[valid]

            if rows.size < 3:
                continue

            path = np.ravel_multi_index((rows, cols), shape)
        else:
            continue

        valid = (path >= 0) & (path < shape[0] * shape[1])
        path = path[valid]
        if path.size < 3:
            continue

        links.append(SimpleNamespace(path=path))

    return links


def _expected_metrics_map(mean_metrics):
    return {
        "AOC_mean": float(mean_metrics.AOCmean),
        "AOC_std": float(mean_metrics.AOCstd),
        "TSC_mean": float(mean_metrics.TSCmean),
        "TSC_std": float(mean_metrics.TSCstd),
        "TSCN_mean": float(mean_metrics.TSCNmean),
        "TSCN_std": float(mean_metrics.TSCNstd),
        "tortDensity_mean": float(mean_metrics.tortDensitymean),
        "tortDensity_std": float(mean_metrics.tortDensitystd),
        "DT_mean": float(mean_metrics.DTmean),
        "DT_std": float(mean_metrics.DTstd),
        "PWAOC_mean": float(mean_metrics.PWAOCmean),
        "PWAOC_std": float(mean_metrics.PWAOCstd),
        "ISR_mean": float(mean_metrics.ISRmean),
        "ISR_std": float(mean_metrics.ISRstd),
        "SOAM_mean": float(mean_metrics.SOAMmean),
        "SOAM_std": float(mean_metrics.SOAMstd),
        "tortAngle_mean": float(mean_metrics.tortAnglemean),
        "tortAngle_std": float(mean_metrics.tortAnglestd),
        "VCI1_mean": float(mean_metrics.VCI1mean),
        "VCI1_std": float(mean_metrics.VCI1std),
        "VCI2_mean": float(mean_metrics.VCI2mean),
        "VCI2_std": float(mean_metrics.VCI2std),
    }


class TestNewTortuosityRegional(unittest.TestCase):
    def test_regional_new_tortuosity_matches_matlab(self):
        mat_files = sorted(glob.glob(MAT_GLOB, recursive=True))
        if not mat_files:
            self.skipTest("No regional validation MAT files found.")

        rows = []
        failures = []
        os.makedirs(os.path.dirname(OUTPUT_XLSX), exist_ok=True)

        try:
            for mat_path in mat_files:
                data = sio.loadmat(mat_path, squeeze_me=True, struct_as_record=False)

                if "links" not in data:
                    failures.append(f"Missing links in {mat_path}")
                    continue
                if "binaryRegion" not in data:
                    failures.append(f"Missing binaryRegion in {mat_path}")
                    continue
                if "fullImSizePix" not in data:
                    failures.append(f"Missing fullImSizePix in {mat_path}")
                    continue
                if "realImageSizeMm" not in data:
                    failures.append(f"Missing realImageSizeMm in {mat_path}")
                    continue
                if "meanMetrics" not in data:
                    failures.append(f"Missing meanMetrics in {mat_path}")
                    continue

                binary_region = np.asarray(data["binaryRegion"])
                full_im_size_pix = np.asarray(data["fullImSizePix"]).astype(int).ravel()
                real_image_size_mm = float(np.asarray(data["realImageSizeMm"]).squeeze())
                expected = data["meanMetrics"]

                canvas = DummyCanvas()
                canvas.binary_image = binary_region
                canvas.skeleton_links = _mat_links_to_python_links(
                    data["links"],
                    binary_region.shape,
                )
                canvas.image_size_var = DummyVar(real_image_size_mm)
                canvas.fullImSizePix = tuple(full_im_size_pix[:2])
                canvas.new_tort_metrics = {}

                BiomarkerAnalyzer.new_tortuosity_metrics_all(canvas)

                actual = canvas.new_tort_metrics
                expected_map = _expected_metrics_map(expected)

                row = {
                    "mat_path": mat_path,
                    "file_name": os.path.basename(mat_path),
                    "n_links": len(canvas.skeleton_links),
                    "realImageSizeMm": real_image_size_mm,
                    "image_height": int(full_im_size_pix[0]) if full_im_size_pix.size > 0 else np.nan,
                    "image_width": int(full_im_size_pix[1]) if full_im_size_pix.size > 1 else np.nan,
                }

                for key, expected_value in expected_map.items():
                    if key not in actual:
                        failures.append(f"{key} missing from Python metrics for {mat_path}")
                        row[f"{key}_python"] = np.nan
                        row[f"{key}_matlab"] = expected_value
                        row[f"{key}_abs_diff"] = np.nan
                        continue

                    actual_value = float(actual[key])
                    row[f"{key}_python"] = actual_value
                    row[f"{key}_matlab"] = expected_value
                    row[f"{key}_abs_diff"] = abs(actual_value - expected_value)

                    if not np.isclose(actual_value, expected_value, atol=TOL, rtol=0.0, equal_nan=True):
                        failures.append(
                            f"Mismatch for {key} in {mat_path}: "
                            f"python={actual_value}, matlab={expected_value}"
                        )

                rows.append(row)
        finally:
            if rows:
                df = pd.DataFrame(rows)
                with pd.ExcelWriter(OUTPUT_XLSX, engine="openpyxl") as writer:
                    df.to_excel(writer, index=False, sheet_name="regional_tortuosity")

        if failures:
            self.fail("\n".join(failures[:50]))


if __name__ == "__main__":
    unittest.main()
