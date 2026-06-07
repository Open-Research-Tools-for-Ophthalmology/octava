'''compare regional tortuosity metrics computed by Python vs MATLAB for the same skeletonised results saved from matlab.'''

import json
import os
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.io as sio


current_dir = os.path.dirname(os.path.abspath(__file__))
code_dir = os.path.abspath(os.path.join(current_dir, os.pardir, os.pardir))
if code_dir not in sys.path:
    sys.path.insert(0, code_dir)

from modules.biomarker import BiomarkerAnalyzer
from modules.regional_analysis import normalize_regional_tortuosity_metrics


WORKSPACE_DIR = Path(code_dir).parent
DEFAULT_OUTPUT_CSV = Path(current_dir) / "python_regional_new_tort_metrics.csv"
DEFAULT_OUTPUT_JSON = Path(current_dir) / "python_regional_new_tort_metrics.json"


def discover_validation_files(root_dir: Path) -> list[Path]:
    """Find MATLAB regional tortuosity validation files only under regional_tort_validation folders."""
    return sorted(root_dir.rglob("regional_tort_validation/*_tort_validation.mat"))


def _to_scalar(value):
    """Convert MATLAB-loaded scalars/char arrays into plain Python values."""
    if isinstance(value, str):
        return value

    arr = np.asarray(value)
    if arr.ndim == 0:
        return arr.item()
    if arr.size == 1:
        return arr.reshape(-1)[0].item()
    return value


def compute_regional_new_tort_metrics_from_mat_file(mat_path: Path) -> dict:
    """Load one MATLAB regional validation file and compute Python tortuosity metrics."""
    mat = sio.loadmat(mat_path, squeeze_me=True, struct_as_record=False)

    if "links" not in mat:
        raise KeyError(f"{mat_path} is missing 'links'.")
    if "realImageSizeMm" not in mat:
        raise KeyError(f"{mat_path} is missing 'realImageSizeMm'.")
    if "fullImSizePix" not in mat:
        raise KeyError(f"{mat_path} is missing 'fullImSizePix'.")

    image_size_mm = float(np.asarray(mat["realImageSizeMm"]).squeeze())
    full_im_size_pix = np.asarray(mat["fullImSizePix"]).astype(float).ravel()
    if full_im_size_pix.size == 0:
        raise ValueError(f"{mat_path} has empty 'fullImSizePix'.")

    # Match the MATLAB/Python whole-image scale convention used by tort_metrics_new().
    pix2mm = image_size_mm / full_im_size_pix[0] if full_im_size_pix[0] > 0 else 0.0

    mat_links = np.atleast_1d(mat["links"])
    per_link_metrics = []

    for link in mat_links:
        if not hasattr(link, "x") or not hasattr(link, "y"):
            continue

        metrics = BiomarkerAnalyzer._compute_new_tortuosity_metrics_from_xy(
            link.x,
            link.y,
            pix2mm,
        )
        if metrics is not None:
            per_link_metrics.append(metrics)

    summarized = BiomarkerAnalyzer._summarize_new_tort_metrics(per_link_metrics)
    normalized = normalize_regional_tortuosity_metrics(summarized)

    return {
        "mat_path": str(mat_path),
        "fileLabelName": _to_scalar(mat.get("fileLabelName", "")),
        "regionGridType": _to_scalar(mat.get("regionGridType", "")),
        "regionIndex": int(_to_scalar(mat.get("regionIndex", 0)) or 0),
        "regionLabel": _to_scalar(mat.get("regionLabel", "")),
        "num_links": int(len(mat_links)),
        "num_valid_links": int(len(per_link_metrics)),
        **normalized,
    }


def collect_regional_new_tort_metrics(validation_dir: Path) -> pd.DataFrame:
    """Compute Python regional new tortuosity metrics for every saved MATLAB region file."""
    mat_files = discover_validation_files(validation_dir)
    if not mat_files:
        raise FileNotFoundError(
            f"No regional tort validation MAT files found under {validation_dir}"
        )

    rows = [compute_regional_new_tort_metrics_from_mat_file(path) for path in mat_files]
    df = pd.DataFrame(rows)

    sort_columns = [col for col in ("fileLabelName", "regionGridType", "regionIndex") if col in df.columns]
    if sort_columns:
        df = df.sort_values(sort_columns).reset_index(drop=True)

    return df


class TestCompareRegionalNewTort(unittest.TestCase):
    def test_collect_regional_new_tort_metrics(self):
        validation_root = Path(
            os.environ.get("OCTAVA_REGIONAL_TORT_VALIDATION_DIR", str(WORKSPACE_DIR))
        )
        mat_files = discover_validation_files(validation_root)

        if not mat_files:
            self.skipTest(
                "No regional tort validation MAT files found. "
                "Set OCTAVA_REGIONAL_TORT_VALIDATION_DIR to the folder containing them."
            )

        df = collect_regional_new_tort_metrics(validation_root)

        self.assertFalse(df.empty)
        self.assertTrue(
            {"PWAOC_mean", "PWAOC_std", "SOAM_mean", "SOAM_std"}.issubset(df.columns)
        )
        self.assertTrue(np.isfinite(df[["PWAOC_mean", "PWAOC_std", "SOAM_mean", "SOAM_std"]]).all().all())


if __name__ == "__main__":
    validation_root = Path(
        os.environ.get("OCTAVA_REGIONAL_TORT_VALIDATION_DIR", str(WORKSPACE_DIR))
    )
    df = collect_regional_new_tort_metrics(validation_root)

    df.to_csv(DEFAULT_OUTPUT_CSV, index=False)
    with open(DEFAULT_OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(df.to_dict(orient="records"), f, indent=2)

    print(df)
    print(f"Saved CSV to: {DEFAULT_OUTPUT_CSV}")
    print(f"Saved JSON to: {DEFAULT_OUTPUT_JSON}")
