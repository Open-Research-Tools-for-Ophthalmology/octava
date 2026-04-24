from pathlib import Path

import pandas as pd


WORKSPACE_DIR = Path("/Users/milameteor/Library/CloudStorage/OneDrive-UWA/M4 Backup/dev/octava")
INPUT_CSV = WORKSPACE_DIR / "code/modules/tests/python_regional_new_tort_metrics.csv"
OUTPUT_XLSX = WORKSPACE_DIR / "code/modules/tests/python_regional_new_tort_metrics_merged.xlsx"
INPUT_XLSX_BY_FILE_LABEL = {
    "5000": WORKSPACE_DIR / "source/5000/5000_.xlsx",
    "5001": WORKSPACE_DIR / "source/5001/5001_.xlsx",
    "5002": WORKSPACE_DIR / "source/5002/5002_.xlsx",
}

REGIONAL_SHEET_MAP = {
    "Square grid": "Regional analysis_Square grid",
    "ETDRS grid": "Regional analysis_ETDRS grid",
    "Extended": "Regional analysis_Extended",
    "Foveal rings": "Regional analysis_Foveal rings",
    "ONH": "Regional analysis_ONH",
}

METRIC_COLUMNS = ["PWAOC_mean", "PWAOC_std", "SOAM_mean", "SOAM_std"]
MATLAB_SUFFIX_COLUMNS = [f"{column}_matlab" for column in METRIC_COLUMNS]


def load_matlab_regional_metrics(file_label_name: str, workbook_path: Path) -> pd.DataFrame:
    """Load the four regional tortuosity metrics from each relevant Excel sheet."""
    rows = []

    for grid_type, sheet_name in REGIONAL_SHEET_MAP.items():
        df = pd.read_excel(workbook_path, sheet_name=sheet_name)
        first_column = df.columns[0]

        required_columns = [first_column, *METRIC_COLUMNS]
        missing_columns = [column for column in required_columns if column not in df.columns]
        if missing_columns:
            raise KeyError(
                f"Sheet '{sheet_name}' is missing required columns: {missing_columns}"
            )

        subset = df[[first_column, *METRIC_COLUMNS]].copy()
        subset = subset.rename(
            columns={
                first_column: "regionLabel",
                "PWAOC_mean": "PWAOC_mean_matlab",
                "PWAOC_std": "PWAOC_std_matlab",
                "SOAM_mean": "SOAM_mean_matlab",
                "SOAM_std": "SOAM_std_matlab",
            }
        )
        subset["fileLabelName"] = file_label_name
        subset["regionGridType"] = grid_type
        rows.append(subset)

    return pd.concat(rows, ignore_index=True)


def load_all_matlab_regional_metrics() -> pd.DataFrame:
    """Load regional tortuosity metrics from all configured MATLAB workbooks."""
    rows = []

    for file_label_name, workbook_path in INPUT_XLSX_BY_FILE_LABEL.items():
        if not workbook_path.exists():
            raise FileNotFoundError(f"Missing workbook for {file_label_name}: {workbook_path}")
        rows.append(load_matlab_regional_metrics(file_label_name, workbook_path))

    return pd.concat(rows, ignore_index=True)


def merge_regional_tort_metrics(csv_path: Path) -> pd.DataFrame:
    """Merge Python regional metrics with MATLAB sheet values on file, grid type, and region label."""
    python_df = pd.read_csv(csv_path)
    matlab_df = load_all_matlab_regional_metrics()
    python_df["fileLabelName"] = python_df["fileLabelName"].astype(str)
    matlab_df["fileLabelName"] = matlab_df["fileLabelName"].astype(str)

    merged = python_df.merge(
        matlab_df,
        on=["fileLabelName", "regionGridType", "regionLabel"],
        how="left",
        validate="many_to_one",
    )

    missing = merged[MATLAB_SUFFIX_COLUMNS].isna().any(axis=1)
    if missing.any():
        missing_rows = merged.loc[missing, ["fileLabelName", "regionGridType", "regionLabel"]]
        raise ValueError(
            "Failed to match some Python regional rows to MATLAB sheet rows:\n"
            + missing_rows.to_string(index=False)
        )

    base_columns = [column for column in python_df.columns if column not in MATLAB_SUFFIX_COLUMNS]
    merged = merged[base_columns + MATLAB_SUFFIX_COLUMNS]

    return merged


def main():
    merged = merge_regional_tort_metrics(INPUT_CSV)
    merged.to_excel(OUTPUT_XLSX, index=False, sheet_name="regional_new_tort_merged")
    print(merged.head().to_string(index=False))
    print(f"Saved merged workbook to: {OUTPUT_XLSX}")


if __name__ == "__main__":
    main()
