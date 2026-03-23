from pathlib import Path
from tkinter import (
    Tk,
    Canvas,
    Entry,
    Text,
    Button,
    PhotoImage,
    Toplevel,
    Checkbutton,
    IntVar,
    StringVar,
    Spinbox,
)
from tkinter.ttk import Combobox
import customtkinter as ctk
from theme import *
from modules.round_rectangle import *
from modules.select_folder import *
from window_regional_analysis_settings import *

def init_batch_processing_settings(canvas: Canvas):
    canvas.bp_selected_folder_path = None
    canvas.bp_file_type_var = StringVar(value="tif")
    canvas.bp_batch_resize_bool_var = IntVar(value=0)
    canvas.bp_batch_resize_value_var = IntVar(value=1000)
    canvas.bp_variable_image_size_bool_var = IntVar(value=0)
    canvas.bp_variable_image_size_df = None
    canvas.bp_segment_faz_var = IntVar(value=0)
    canvas.bp_regional_analysis_var = IntVar(value=0)

def close(subwindow):
    subwindow.destroy()
    subwindow.update()

def subwindow3(canvas, open_window_fn=None):
    subwindow = Toplevel()
    subwindow.title("Batch Processing Settings")
    subwindow.geometry("350x455")
    subwindow.configure(bg="#FBE3D6")
    
    # Trace checkbox to enable/disable batch resize entry
    trace_id = None

    subcanvas3 = Canvas(
        subwindow,
        bg="#FBE3D6",
        height=455,
        width=350,
        bd=0,
        highlightthickness=0,
        relief="ridge",
    )

    subcanvas3.place(x=0, y=0)

    button1 = ctk.CTkButton(
        subwindow,
        text="Select Raw Data Folder",
        command=lambda: select_folder(subcanvas3, canvas, 60, 100),
        width=260,
        height=40,
        font=("Roboto", 14 * -1),
        text_color=text_colour,
        fg_color=button_yellow_colour,
        corner_radius=8,
        border_width=1,
        hover_color=button_yellow_hover,
        border_color=button_border_colour,
    )
    button1.place(x=45, y=30)
    round_rectangle(
        subcanvas3, 45, 80, 260, 40, radius=8, fill=bg_colour, outline=bg_colour
    )

    subcanvas3.create_text(
        45.0,
        135.0,
        anchor="nw",
        text="File type",
        fill="#0F1F3F",
        font=("Roboto SemiBold", 14 * -1),
    )

    # file type dropdown
    file_type_list = ["tif", "png", "jpg", "bmp", "mat"]
    file_type = Combobox(
        subwindow, textvariable=canvas.bp_file_type_var, values=file_type_list, state="readonly"
    )
    file_type.place(x=110.0, y=130.0, width=165.0, height=30.0)

    # batch resize checkbox
    batch_resize_checkbox = Checkbutton(
        subwindow,
        text="Batch resize",
        variable=canvas.bp_batch_resize_bool_var,
        bg=subwindow_bg_colour,
        fg=text_colour,
        font=("Roboto", 14 * -1),
    )
    batch_resize_checkbox.place(x=40.0, y=185.0)

    batch_resize_text = Entry(
        subwindow,
        textvariable=canvas.bp_batch_resize_value_var,
        bg=bg_colour,
        fg=text_colour,
        font=("Roboto", 14 * -1),
        state="normal" if canvas.bp_batch_resize_bool_var.get() == 1 else "disabled",
        width=12,
        bd=0.5,
        highlightthickness=0,
    )

    # Disable text entry if checkbox not selected
    def update_batch_resize_state(*args): # .args to dump unused args
        if batch_resize_text.winfo_exists():  # Check if widget still exists
            if canvas.bp_batch_resize_bool_var.get() == 1:
                batch_resize_text.config(state="normal")
            else:
                batch_resize_text.config(state="disabled")

    trace_id = canvas.bp_batch_resize_bool_var.trace("w", update_batch_resize_state)

    batch_resize_text.place(x=160.0, y=188.0)

    # variable image size checkbox
    variable_image_size_checkbox = Checkbutton(
        subwindow,
        text="Variable image size",
        variable=canvas.bp_variable_image_size_bool_var,
        command=lambda: select_file(subcanvas3, canvas) if canvas.bp_variable_image_size_bool_var.get() == 1 else None,
        bg=subwindow_bg_colour,
        fg=text_colour,
        font=("Roboto", 14 * -1),
    )
    variable_image_size_checkbox.place(x=40.0, y=223.0)

    subcanvas3.create_text(
        66.0,
        250.0,
        anchor="nw",
        text="No - Process from folder\nYes - Process from list",
        fill="#0F1F3F",
        font=("Roboto SemiBold", 14 * -1),
    )

    # measure faz checkbox
    measure_faz_checkbox = Checkbutton(
        subwindow,
        text="Segment FAZ",
        variable=canvas.bp_segment_faz_var,
        bg=subwindow_bg_colour,
        fg=text_colour,
        font=("Roboto", 14 * -1),
    )
    measure_faz_checkbox.place(x=40.0, y=286.0)

    # regional analysis checkbox
    regional_analysis_checkbox = Checkbutton(
        subwindow,
        text="Run Regional Analysis",
        variable=canvas.bp_regional_analysis_var,
        command=lambda: (open_window_fn("regional_analysis", subwindow2, canvas)) if canvas.bp_regional_analysis_var.get() == 1 else None,
        bg=subwindow_bg_colour,
        fg=text_colour,
        font=("Roboto", 14 * -1),
    )
    regional_analysis_checkbox.place(x=40.0, y=321.0)

    # close
    button_close = ctk.CTkButton(
        subwindow,
        text="Close",
        command=lambda: (
            canvas.bp_batch_resize_bool_var.trace_vdelete("w", trace_id),
            close(subwindow)
        ),
        width=130,
        height=45,
        font=("Roboto", 14 * -1),
        text_color=text_colour,
        fg_color=button_blue_colour,
        corner_radius=8,
        border_width=1,
        hover_color=button_blue_hover,
        border_color=button_border_colour,
    )
    button_close.place(x=110, y=370)

    # Populate selected folder path if already set
    print("Current selected folder path:", canvas.bp_selected_folder_path)
    if canvas.bp_selected_folder_path is not None:
        display_text = fit_path_to_canvas(canvas.bp_selected_folder_path, subcanvas3, ("Roboto", 12 * -1), 220)
        display_text_to_canvas(
            subcanvas3,
            60, 
            100,
            display_text,
            ("Roboto", 12 * -1),
        )

    subwindow.resizable(False, False)
    return subwindow
