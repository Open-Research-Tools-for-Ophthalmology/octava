# folder_loader.py
import tkinter as tk
from tkinter import filedialog
from tkinter import font as tkfont

TAG_SAVE_FOLDER_TEXT = "save_folder_text"

def fit_path_to_canvas(path: str, canvas: tk.Canvas, font: tuple, max_width: int) -> str:
    tk_font = tkfont.Font(canvas, font=font)
    if tk_font.measure(path) <= max_width:
        return path
    dots = "..."
    dots_w = tk_font.measure(dots)
    if dots_w > max_width:
        return dots
    lo, hi = 1, max(1, len(path) - len(dots))
    best = dots
    while lo <= hi:
        mid = (lo + hi) // 2
        head_len = mid // 2
        tail_len = mid - head_len
        candidate = path[:head_len] + dots + path[-tail_len:]
        if tk_font.measure(candidate) <= max_width:
            best = candidate
            lo = mid + 1
        else:
            hi = mid - 1
    return best

def select_save_folder(canvas: tk.Canvas, text_x: int, text_y: int, text_width: int = 220):
    dir_path = filedialog.askdirectory(title="Select a folder", mustexist=True)
    if not dir_path:
        return None  # user cancelled

    font_spec = ("Roboto", 12 * -1)
    display_text = fit_path_to_canvas(dir_path, canvas=canvas, font=font_spec, max_width=text_width)

    # Remove any previously drawn label at that spot
    canvas.delete(TAG_SAVE_FOLDER_TEXT)

    # Draw new text and tag it
    text_id = canvas.create_text(
        text_x, text_y,
        text=display_text,
        fill="#333333",
        font=font_spec,
        anchor="w",
        tags=(TAG_SAVE_FOLDER_TEXT,)
    )

    # Keep the real path for later use
    canvas.save_folder_path = dir_path
    # (optional) keep the id if you want
    canvas.save_folder_text_id = text_id

    return dir_path