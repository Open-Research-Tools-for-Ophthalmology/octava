from pathlib import Path

import numpy as np
import pandas as pd


WORKSPACE_DIR = Path("/Users/milameteor/Library/CloudStorage/OneDrive-UWA/M4 Backup/dev/octava")
OUTPUT_XLSX = (
    WORKSPACE_DIR
    / "code/modules/tests/merged_regional_microvascular_metrics.xlsx"
)

PYTHON_WORKBOOKS = {
    "5000": WORKSPACE_DIR / "test_images/5000/5000_24-Apr-2026 132653.xlsx",
    "5001": WORKSPACE_DIR / "test_images/5001/5001_24-Apr-2026 132543.xlsx",
    "5002": WORKSPACE_DIR / "test_images/5002/5002_24-Apr-2026 132442.xlsx",
}

MATLAB_WORKBOOKS = {
    "5000": WORKSPACE_DIR / "source/5000/5000_.xlsx",
    "5001": WORKSPACE_DIR / "source/5001/5001_.xlsx",
    "5002": WORKSPACE_DIR / "source/5002/5002_.xlsx",
}


def regional_sheet_names(workbook_path: Path) -> list[str]:
    """Return only the regional analysis sheet names from a workbook."""
    excel_file = pd.ExcelFile(workbook_path)
    return [name for name in excel_file.sheet_names if name.startswith("Regional analysis_")]


def build_merged_regional_sheet(python_df: pd.DataFrame, matlab_df: pd.DataFrame) -> pd.DataFrame:
    """Append MATLAB regional rows below Python regional rows using the union of columns."""
    all_columns = list(dict.fromkeys(list(python_df.columns) + list(matlab_df.columns)))
    python_aligned = python_df.reindex(columns=all_columns)
    matlab_aligned = matlab_df.reindex(columns=all_columns)
    return pd.concat([python_aligned, matlab_aligned], ignore_index=True)


def build_rmse_table(python_df: pd.DataFrame, matlab_df: pd.DataFrame) -> pd.DataFrame:
    """Compute per-region RMSE for shared numeric columns."""
    if "Region" not in python_df.columns or "Region" not in matlab_df.columns:
        raise KeyError("Both Python and MATLAB regional sheets must contain a 'Region' column.")

    def normalize_region_key(series: pd.Series) -> pd.Series:
        return (
            series.astype(str)
            .str.strip()
            .str.replace(r"\s+", " ", regex=True)
            .str.casefold()
        )

    python_work = python_df.copy()
    matlab_work = matlab_df.copy()
    python_work["Region"] = python_work["Region"].astype(str).str.strip()
    matlab_work["Region"] = matlab_work["Region"].astype(str).str.strip()
    python_work["_region_key"] = normalize_region_key(python_work["Region"])
    matlab_work["_region_key"] = normalize_region_key(matlab_work["Region"])

    python_indexed = python_work.set_index("_region_key")
    matlab_indexed = matlab_work.set_index("_region_key")

    if set(python_indexed.index) != set(matlab_indexed.index):
        raise ValueError("Python and MATLAB region sets do not match for RMSE computation.")

    matlab_indexed = matlab_indexed.reindex(python_indexed.index)
    python_regions = python_indexed["Region"]

    shared_columns = [column for column in python_df.columns if column in matlab_df.columns and column != "Region"]
    numeric_columns = [
        column
        for column in shared_columns
        if pd.api.types.is_numeric_dtype(python_df[column]) and pd.api.types.is_numeric_dtype(matlab_df[column])
    ]

    rmse_df = pd.DataFrame(index=python_indexed.index)
    for column in numeric_columns:
        diff = python_indexed[column].astype(float) - matlab_indexed[column].astype(float)
        rmse_df[column] = np.sqrt(np.square(diff))

    rmse_df.insert(0, "Region", python_regions.values)
    rmse_df = rmse_df.reset_index(drop=True)

    overall_row = {"Region": "OVERALL_RMSE"}
    for column in numeric_columns:
        diff = python_indexed[column].astype(float) - matlab_indexed[column].astype(float)
        overall_row[column] = float(np.sqrt(np.mean(np.square(diff))))

    return pd.concat([rmse_df, pd.DataFrame([overall_row])], ignore_index=True)


def short_output_sheet_name(file_label: str, regional_sheet_name: str) -> str:
    """Create an Excel-safe sheet name that identifies both file and region grid."""
    short_name = regional_sheet_name.replace("Regional analysis_", "")
    if short_name == "Square grid":
        short_name = "Square"
    elif short_name == "ETDRS grid":
        short_name = "ETDRS"
    elif short_name == "Foveal rings":
        short_name = "Foveal"
    return f"{file_label}_{short_name}"[:31]


def merge_all_regional_workbooks(output_path: Path) -> None:
    """Merge Python and MATLAB regional sheets for all configured files into one workbook."""
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        for file_label, python_workbook in PYTHON_WORKBOOKS.items():
            matlab_workbook = MATLAB_WORKBOOKS[file_label]

            if not python_workbook.exists():
                raise FileNotFoundError(f"Missing Python workbook for {file_label}: {python_workbook}")
            if not matlab_workbook.exists():
                raise FileNotFoundError(f"Missing MATLAB workbook for {file_label}: {matlab_workbook}")

            python_sheets = regional_sheet_names(python_workbook)
            matlab_sheets = set(regional_sheet_names(matlab_workbook))

            for sheet_name in python_sheets:
                if sheet_name not in matlab_sheets:
                    raise KeyError(
                        f"MATLAB workbook {matlab_workbook} is missing sheet '{sheet_name}'"
                    )

                python_df = pd.read_excel(python_workbook, sheet_name=sheet_name)
                matlab_df = pd.read_excel(matlab_workbook, sheet_name=sheet_name)
                merged_df = build_merged_regional_sheet(python_df, matlab_df)
                rmse_df = build_rmse_table(python_df, matlab_df)
                output_sheet_name = short_output_sheet_name(file_label, sheet_name)

                merged_df.to_excel(
                    writer,
                    sheet_name=output_sheet_name,
                    index=False,
                )

                title_row = pd.DataFrame([{"Region": "RMSE_BY_REGION"}])
                startrow = len(merged_df) + 3
                title_row.to_excel(
                    writer,
                    sheet_name=output_sheet_name,
                    index=False,
                    header=False,
                    startrow=startrow,
                )
                rmse_df.to_excel(
                    writer,
                    sheet_name=output_sheet_name,
                    index=False,
                    startrow=startrow + 1,
                )


def main():
    merge_all_regional_workbooks(OUTPUT_XLSX)
    print(f"Saved merged regional workbook to: {OUTPUT_XLSX}")


if __name__ == "__main__":
    main()
