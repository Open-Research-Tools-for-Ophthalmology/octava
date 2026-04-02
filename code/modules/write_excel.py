import pandas as pd
import os


def write_excel(data, file_path: str, sheet_name: str=None):
    """
    Write data (dict or DataFrame) to a certain sheet in an Excel file.
    """
    
    if file_path is None:
        print("No file path provided for writing Excel.")
        return
    
    # if data is raw dict, convert to pandas dataframe
    if (type(data) is dict):
        data = pd.DataFrame([data])
    
    # we always append/overlay new data to existing excel file
    try:
        mode = 'a' if os.path.exists(file_path) else 'w'
        if_sheet_exists = 'overlay' if mode == 'a' else None
        
        with pd.ExcelWriter(file_path, mode=mode, engine="openpyxl", if_sheet_exists=if_sheet_exists) as writer:
            # if sheet name is not specified, append data to the first sheet
            if sheet_name is None:
                sheet_name = list(writer.sheets.keys())[0]

            data.to_excel(writer, sheet_name=sheet_name, index=False)
        
        print(f"Export data to Excel {file_path}, sheet: {sheet_name}, data: {data}")

    except Exception as e:
        print(f"Error writing to Excel file {file_path}: {e}")
