import pandas as pd
import os

def write_excel(data, file_path: str, sheet_name: str=None, replace_sheet: bool=False):
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
        if_sheet_exists = ('replace' if replace_sheet else 'overlay') if mode == 'a' else None
        
        with pd.ExcelWriter(file_path, mode=mode, engine="openpyxl", if_sheet_exists=if_sheet_exists) as writer:
            # if sheet name is not specified, append data to the first sheet
            if sheet_name is None:
                sheet_name = list(writer.sheets.keys())[0]

            data.to_excel(writer, sheet_name=sheet_name, index=False)
        
        print(f"Export data to Excel {file_path}, sheet: {sheet_name}, data: {data}")

    except Exception as e:
        print(f"Error writing to Excel file {file_path}: {e}")


def round_rectangle(canvas, x1, y1, width, height, radius=16, fill="#EFEFEF", outline="#EFEFEF"):
    """
    Draw a rounded rectangle on a Tkinter Canvas.

    (x1, y1) = top-left corner, (x2, y2) = bottom-right corner.
    radius   = corner radius in pixels.

    kwargs are passed to create_ methods (e.g., fill="blue", outline="black").
    """
    x2 = x1 + width
    y2 = y1 + height
    if radius > (x2 - x1) / 2:
        radius = (x2 - x1) / 2
    if radius > (y2 - y1) / 2:
        radius = (y2 - y1) / 2

    item_ids = []

    # Corners
    item_ids.append(canvas.create_arc(x1, y1, x1 + 2*radius, y1 + 2*radius,
                                      start=90, extent=90, style="pieslice", fill=fill, outline=outline))
    item_ids.append(canvas.create_arc(x2 - 2*radius, y1, x2, y1 + 2*radius,
                                      start=0, extent=90, style="pieslice", fill=fill, outline=outline))
    item_ids.append(canvas.create_arc(x2 - 2*radius, y2 - 2*radius, x2, y2,
                                      start=270, extent=90, style="pieslice", fill=fill, outline=outline))
    item_ids.append(canvas.create_arc(x1, y2 - 2*radius, x1 + 2*radius, y2,
                                      start=180, extent=90, style="pieslice", fill=fill, outline=outline))

    # Edges
    item_ids.append(canvas.create_rectangle(x1 + radius, y1, x2 - radius, y2, fill=fill, outline=outline))
    item_ids.append(canvas.create_rectangle(x1, y1 + radius, x2, y2 - radius, fill=fill, outline=outline))

    return item_ids
