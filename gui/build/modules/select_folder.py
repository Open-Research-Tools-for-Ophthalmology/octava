# # folder_loader.py
# from tkinter import filedialog
# import os

# def _shorten_path(path: str, max_chars: int = 140) -> str:
#     """
#     Shorten long paths for display while keeping the start and end.
#     e.g. /Users/alex/.../my_project/assets
#     """
#     if len(path) <= max_chars:
#         return path
#     head = path[: max_chars // 2 - 3]
#     tail = path[-max_chars // 2 :]
#     return f"{head}...{tail}"

# def select_folder(canvas, text_x, text_y, text_width=200):
#     """
#     Ask the user to pick a folder, draw a simple folder icon on the given canvas,
#     and show the full folder path near the given position.

#     Returns the selected folder path (str) or None if cancelled.
#     """
#     dir_path = filedialog.askdirectory(
#         title="Select a folder",
#         mustexist=True,
#     )
#     if not dir_path:
#         return None  # user cancelled

#     # --- show the folder path (shortened for display, full path in a tooltip-ish title) ---
#     display_text = _shorten_path(dir_path, max_chars=int(text_width * 0.9 // 7))  # rough char/px
#     text_id = canvas.create_text(
#         text_x, text_y,
#         text=display_text,
#         fill="#333333",
#         font=("Roboto", 12 * -1),
#         anchor="w",          # align left edge at (text_x, text_y)
#         width=text_width,    # enable wrapping if desired
#     )

#     # Store references/ids on the canvas so callers can manage them later.
#     canvas.selected_folder_path = dir_path  # keep the real path handy

#     return dir_path

# folder_loader.py
import os
import tkinter as tk
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

def select_folder(canvas: tk.Canvas, text_x: int, text_y: int, text_width: int = 220):
    """
    Ask the user to pick a folder and draw the (fitted) folder path on the canvas
    at (text_x, text_y). `text_width` is the max pixel width allowed for the text.

    Returns the selected folder path (str) or None if cancelled.
    """
    dir_path = filedialog.askdirectory(
        title="Select a folder",
        mustexist=True,
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

    # Draw a single-line, left-anchored label (no wrapping needed because we fit it)
    text_id = canvas.create_text(
        text_x, text_y,
        text=display_text,
        fill="#333333",
        font=font_spec,
        anchor="w",
    )

    #todo: Keep the real path handy for later use
    # canvas.selected_folder_path = dir_path

    return dir_path