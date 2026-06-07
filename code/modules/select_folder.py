import os
import tkinter as tk
import pandas as pd
from tkinter import filedialog
from tkinter import font as tkfont

def fit_path_to_canvas(path: str, canvas: tk.Canvas, font: tuple, max_width: int) -> str:
    """
    Return a version of `path` that fits within `max_width` pixels when rendered
    on the given canvas with `font`. Keeps the beginning and end, trimming the middle.
    """
    tk_font = tkfont.Font(canvas, font=font)

    # Already fits
    if tk_font.measure(path) <= max_width:
        return path

    dots = "..."
    dots_w = tk_font.measure(dots)

    # If even "..." is wider than the box, just return "..."
    if dots_w > max_width:
        return dots

    # Binary search the total number of visible characters to maximize info
    lo, hi = 1, max(1, len(path) - len(dots))
    best = dots
    while lo <= hi:
        mid = (lo + hi) // 2
        # Split mid between head and tail
        head_len = mid // 2
        tail_len = mid - head_len
        candidate = path[:head_len] + dots + path[-tail_len:]
        if tk_font.measure(candidate) <= max_width:
            best = candidate
            lo = mid + 1  # try to keep more
        else:
            hi = mid - 1  # keep fewer
    return best

def display_text_to_canvas(canvas: tk.Canvas, text_x: int, text_y: int, display_text: str, font_spec: tuple):
    """Draw a left-anchored text label on the canvas and return its item id."""
    # Draw a single-line, left-anchored label (no wrapping needed because we fit it)
    return canvas.create_text(
        text_x, text_y,
        text=display_text,
        fill="#333333",
        font=font_spec,
        anchor="w",
    )

def select_file(canvas: tk.Canvas, mainCanvas: tk.Canvas):
    """
    Ask the user to pick a xlsx file.
    
    Returns the selected file path (str) or None if cancelled.
    """
    file_path = filedialog.askopenfilename(
        title="Select a xlsx file",
        filetypes=[("Excel files", "*.xlsx"), ('Excel Files', '*.xls')],
        parent=canvas
    )
    if not file_path:
        mainCanvas.bp_variable_image_size_bool_var.set(0)
        return None  # user cancelled
    
    print(f"Selected variable image size file: {file_path}")
    try:
        variable_image_size_df = pd.read_excel(file_path)
        print(f"Loaded variable image size dataframe: {variable_image_size_df}")
        mainCanvas.bp_variable_image_size_df = variable_image_size_df
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        mainCanvas.bp_variable_image_size_bool_var.set(0)
        return None

    return file_path

def select_folder(canvas: tk.Canvas, mainCanvas: tk.Canvas, text_x: int, text_y: int, text_width: int = 220):
    """
    Ask the user to pick a folder and draw the (fitted) folder path on the canvas
    at (text_x, text_y). `text_width` is the max pixel width allowed for the text.

    Returns the selected folder path (str) or None if cancelled.
    """
    dir_path = filedialog.askdirectory(
        title="Select a folder",
        mustexist=True,
        parent=canvas
    )
    if not dir_path:
        return None  # user cancelled

    font_spec = ("Roboto", 12 * -1)

    # Make the path fit the given pixel width
    display_text = fit_path_to_canvas(
        dir_path,
        canvas=canvas,
        font=font_spec,
        max_width=text_width,
    )

    display_text_to_canvas(
        canvas,
        text_x,
        text_y,
        display_text,
        font_spec
    )

    # Keep the real path handy for later use
    mainCanvas.bp_selected_folder_path = dir_path
    print(f"Selected folder: {dir_path}")

    return dir_path
