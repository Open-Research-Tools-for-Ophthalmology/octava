import os
import sys

import pandas as pd


current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from biomarker import BiomarkerAnalyzer


MAT_FILES = [
    "/Users/milameteor/Library/CloudStorage/OneDrive-UWA/M4 Backup/dev/octava/source/5000/images/5000_tort_validation.mat",
    "/Users/milameteor/Library/CloudStorage/OneDrive-UWA/M4 Backup/dev/octava/source/5001/images/5001_tort_validation.mat",
    "/Users/milameteor/Library/CloudStorage/OneDrive-UWA/M4 Backup/dev/octava/source/5002/images/5002_tort_validation.mat",
]

OUTPUT_XLSX = (
    "/Users/milameteor/Library/CloudStorage/OneDrive-UWA/M4 Backup/dev/octava/"
    "code/modules/tests/matlab_link_tortuosity_validation.xlsx"
)


def main():
    """Run the MATLAB-link tortuosity validation workflow and export the summary workbook."""
    rows = []
    missing_files = []

    for mat_path in MAT_FILES:
        if not os.path.exists(mat_path):
            missing_files.append(mat_path)
            continue

        metrics = BiomarkerAnalyzer.compute_new_tortuosity_metrics_from_mat_file(mat_path)
        row = {"name": os.path.basename(mat_path).replace("_tort_validation.mat", "")}
        row.update(metrics)
        rows.append(row)

    df = pd.DataFrame(rows, columns=[
        "name",
        "PWAOC_mean",
        "PWAOC_std",
        "SOAM_mean",
        "SOAM_std",
    ])
    df.to_excel(OUTPUT_XLSX, index=False, sheet_name="MATLAB link validation")

    print(df)
    print(f"Saved Excel file to: {OUTPUT_XLSX}")
    if missing_files:
        print("Skipped missing files:")
        for path in missing_files:
            print(path)


if __name__ == "__main__":
    main()
