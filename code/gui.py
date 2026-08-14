from email.mime import image
from pathlib import Path
from tkinter import Tk, Canvas, Entry, Text, Button, PhotoImage, Checkbutton, IntVar, Spinbox, StringVar, ttk, DoubleVar
from tkinter.ttk import Combobox
from window_onh_editor import *
from window_advanced_settings import *
from window_regional_analysis_settings import *
from window_batch_processing_settings import *
from window_help import *
from window_feedback import *
from window_faz_viewer import *
from window_subscribe import *
from window_faz_viewer import *
import customtkinter as ctk
from theme import *
from gui_config_manager import manager
from modules.load_image import *
from modules.select_save_folder import *
from modules.start_processing import *
from modules.general_utils import *
from modules.change_status import *
from modules.binarise_image import *
from modules.clear import *
from modules.faz_utils import *
from modules.onh_vessel_separation import *
from modules.histogram import HistogramPlotter
from modules.preview_thumbnail import init_thumbnail_zoom_pan
from test import *
from resource_path import ICONS_PATH

# command for bundling on mac with pyinstaller: 
# pyinstaller --noconsole --windowed --add-data "./code/assets:assets" --hidden-import='PIL._tkinter_finder' ./code/gui.py

# Global window registry
OPEN_WINDOWS = {}

# If window exists, bring to front, otherwise create
def open_window(key, callback, *args, **kwargs):
    if disable_click_if_busy(canvas): return # Disable clicking if currently busy

    global OPEN_WINDOWS
    
    # Check if window already exists
    if key in OPEN_WINDOWS:
        try:
            if OPEN_WINDOWS[key].winfo_exists():
                OPEN_WINDOWS[key].lift()
                OPEN_WINDOWS[key].focus()
                return OPEN_WINDOWS[key]
        except:
            # Delete from dict if window no longer exists (either normal closure or programmatically handled closure e.g. FAZ editor)
            del OPEN_WINDOWS[key]
    
    # Spawn new window
    new_window = callback(*args, **kwargs)
    
    if new_window is not None:
        OPEN_WINDOWS[key] = new_window    
    return new_window

# Close all registered sub-windows if exists
def close_windows():
    global OPEN_WINDOWS
    for key in list(OPEN_WINDOWS.keys()):
        try:
            window = OPEN_WINDOWS.pop(key, None)
            if window is not None and window.winfo_exists():
                window.destroy()
        except:
            pass
        print(f"Closed window: {key}")

def on_closing():
    """Save img_type_var to cache when closing the window"""
    manager.config.img_type = canvas.img_type_var.get()
    manager.config.image_size = canvas.image_size_var.get()
    manager.save()
    window.destroy()

window = Tk()
window.title("OCTAVA")
window.geometry("1210x750")
window.configure(bg = bg_colour)

canvas = Canvas(
    window,
    bg = bg_colour,
    width = 1210,
    height = 750,
    bd = 0,
    highlightthickness = 0,
    relief = "ridge"
)

canvas.bin_size_var = IntVar(value=10)  # Variable for Bin Size Spinbox (diameter mode)
canvas.tort_bin_size_var = DoubleVar(value=0.1)  # Variable for Bin Size Spinbox (tortuosity mode)
canvas.image_size_var = DoubleVar(value=manager.config.image_size)  # Variable for Image Size Spinbox
canvas.img_type_var = StringVar(value=manager.config.img_type) # Variable for Image Type dropdown

IMAGE_SIZE_DEFAULTS_MM = {
    "Retina": 3.0,
    "ONH": 4.5,
    "Skin": 3.0,
}
FRANGI_MIN_DEFAULTS_MM = {
    "Retina": 1,
    "ONH": 1,
    "Skin": 1,
}
FRANGI_MAX_DEFAULTS_MM = {
    "Retina": 4,
    "ONH": 4,
    "Skin": 8,
}

init_advanced_settings(canvas)
init_regional_analysis_settings(canvas)      
init_batch_processing_settings(canvas)

canvas.place(x = 0, y = 0)
canvas.create_text(
    30.0,
    30.0,
    anchor="nw",
    text="OCTAVA",
    fill=theme_blue,
    font=("Roboto", 26 * -1)
)

def default_settings():
    manager.load_default()
    if hasattr(canvas, "img_type_var"):
        canvas.img_type_var.set(manager.config.img_type)
        img_type.set(manager.config.img_type)
    
    is_onh_mode = (
      hasattr(canvas, "img_type_var")
      and canvas.img_type_var.get() == "ONH"
    )
    
    params = [
        "frangi_bool", "frangi_min", "frangi_max", 
        "jerman_bool", "jerman_sigmas", "jerman_tau",
        "med_filt_bool", "twig_size", "kernel_size", "prebinary_var"
    ]
    
    for p in params:
        canvas_attr = f"onh_{p}" if (is_onh_mode and p in ["frangi_bool", "frangi_min", "frangi_max", "jerman_bool", "jerman_sigmas", "jerman_tau"]) else p        
        var_object = getattr(canvas, canvas_attr, getattr(canvas, f"{canvas_attr}_var", None))
        
        if var_object and hasattr(var_object, "set"):
            default_value = getattr(manager.config, canvas_attr, getattr(manager.config, p, None))
            
            if default_value is not None:
                var_object.set(default_value)
                
                global_widget = globals().get(canvas_attr) or globals().get(f"{canvas_attr}_var") or globals().get(p)
                if global_widget and hasattr(global_widget, "set"):
                    global_widget.set(default_value)
    

button01 = ctk.CTkButton(window, text="Clear",
                        command=lambda: (clear_screen(canvas), default_settings()),
                        width=65,height=25,
                        font=("Roboto", 12 * -1),
                        text_color=text_colour,
                        fg_color=button_blue_colour,
                        corner_radius=2,border_width=1,
                        hover_color=button_blue_hover,
                        border_color=button_border_colour)
button01.place(x=190, y=35)

button02 = ctk.CTkButton(window, text="Help",
                        command=lambda: open_window('help', open_help_window, canvas),
                        width=65,height=25,
                        font=("Roboto", 12 * -1),
                        text_color=text_colour,
                        fg_color=button_blue_colour,
                        corner_radius=2,border_width=1,
                        hover_color=button_blue_hover,
    border_color=button_border_colour)
button02.place(x=260, y=35)

button03 = ctk.CTkButton(window, text="Feedback",
                        command=lambda: open_window('feedback', open_feedback_window, canvas),
                        width=65,height=25,
                        font=("Roboto", 12 * -1),
                        text_color=text_colour,
                        fg_color=button_blue_colour,
                        corner_radius=2,border_width=1,
                        hover_color=button_blue_hover,
    border_color=button_border_colour)
button03.place(x=330, y=35)

button04 = ctk.CTkButton(window, text="Subscribe to Updates",
                        command=lambda: open_window('subscribe', open_subscribe_window, canvas),
                        width=65,height=25,
                        font=("Roboto", 12 * -1),
                        text_color=text_colour,
                        fg_color=button_blue_colour,
                        corner_radius=2,border_width=1,
                        hover_color=button_blue_hover,
    border_color=button_border_colour)
button04.place(x=400, y=35)


canvas.status_id = canvas.create_text(
    950.0,
    35.0,
    anchor="nw",
    text="● Ready",
    fill=theme_blue,
    font=("Roboto", 20 * -1)
)

canvas.queue_id = canvas.create_text(
    975.0,
    65.0,
    anchor="nw",
    text="",
    fill=theme_blue,
    font=("Roboto", 16 * -1)
)


# image type dropdown
img_type_list = ["Retina", "ONH", "Skin"]
img_type = Combobox(
    textvariable=canvas.img_type_var,
    values=img_type_list,
    state="readonly"
)
img_type.place(
    x=30.0,
    y=105.0,
    width=90.0,
    height=30.0
)


# prebinary
prebinary_checkbox = Checkbutton(
    text="Prebinary",
    variable=canvas.prebinary_var,
    bg=bg_colour,
    fg="#10203F",
    font=("Roboto", 14 * -1)
)
prebinary_checkbox.place(
    x=140.0,
    y=105.0
)

#image size
canvas.create_text(
    250.0,
    109.0,
    anchor="nw",
    text="Image size (mm)",
    fill=text_colour,
    font=("Roboto", 14 * -1)
)
# image size Spinbox
image_size_spinbox = Spinbox(
    from_=0.50,
    to=10.00,
    increment=0.50,
    width=4,
    textvariable=canvas.image_size_var,
    bg=bg_colour,
    fg=text_colour,
    font=("Roboto", 14 * -1),
    bd=0.5,                  # removes the border thickness
    highlightthickness=0,  # removes the focus highlight border
)
image_size_spinbox.place(
    x=365.0,
    y=108.0
)

def is_batch_processing_enabled(canvas: Canvas) -> bool:
    """Return whether a batch input folder has been selected."""
    return hasattr(canvas, "bp_selected_folder_path") and canvas.bp_selected_folder_path is not None

def toggle_start_processing():
    """Enable or disable the Start Processing button based on whether an image is loaded"""
    has_image = hasattr(canvas, "original_img")
    has_folder = is_batch_processing_enabled(canvas)

    if has_image or has_folder:
        button_process.configure(state="normal")
    else:
        button_process.configure(state="disabled")
    
    window.after(10, toggle_start_processing)  # keep checking whether image/folder has loaded

button_loadimg = ctk.CTkButton(window, text="Load Image",
                        command=lambda: load_image(canvas, 550, 255, 180, 170),
                        width=120,height=40,
                        font=("Roboto", 14 * -1),
                        text_color=text_colour,
                        fg_color=button_blue_colour,
                        corner_radius=6,border_width=1,
                        hover_color=button_blue_hover,
    border_color=button_border_colour  )
button_loadimg.place(x=30, y=150)
round_rectangle(canvas, 160, 150, 250, 40, radius=6)


button_save_folder = ctk.CTkButton(window, text="Save Folder",
                        command=lambda: select_save_folder(canvas, text_x=180, text_y=230),
                        width=120,height=40,
                        font=("Roboto", 14 * -1),
                        text_color=text_colour,
                        fg_color=button_blue_colour,
                        corner_radius=6,border_width=1,
                        hover_color=button_blue_hover,
    border_color=button_border_colour  )
button_save_folder.place(x=30, y=210)
round_rectangle(canvas, 160, 210, 250, 40, radius=6)


button_advanced_settings = ctk.CTkButton(window, text="Optional Advanced Settings",
                        command=lambda: open_window('advanced_settings', subwindow1, canvas),
                        width=380,height=65,
                        font=("Roboto", 14 * -1),
                        text_color=text_colour,
                        fg_color=button_yellow_colour,
                        corner_radius=6,border_width=1,
                        hover_color=button_yellow_hover,
    border_color=button_border_colour  )
button_advanced_settings.place(x=30, y=270)

button_point_faz = ctk.CTkButton(window, text="Point FAZ",
                                command=lambda: open_window('point_faz', subwindow4, canvas, editable=True),
                                width=80,height=40,
                                font=("Roboto", 12 * -1),
                                text_color=text_colour,
                                fg_color=button_green_colour,
                                corner_radius=6,border_width=1,
                                hover_color=button_green_hover,
                                border_color=button_border_colour,
                                # state="disabled" if canvas.img_type_var.get()=="Skin" else "normal"
                                )
button_point_faz.place(x=30, y=355)

button_auto_faz = ctk.CTkButton(window, text="Auto FAZ",command=lambda: open_window('auto_faz', subwindow4, canvas, editable=False),
                                width=80,height=40,
                                font=("Roboto", 12 * -1),
                                text_color=text_colour,
                                fg_color=button_green_colour,
                                corner_radius=6,border_width=1,
                                hover_color=button_green_hover,
    border_color=button_border_colour  )
button_auto_faz.place(x=125, y=355)

button_measure_faz = ctk.CTkButton(window, text="Measure FAZ",
                        command=lambda: measure_faz(canvas),
                        width=190,height=40,
                        font=("Roboto", 14 * -1),
                        text_color=text_colour,
                        fg_color=button_green_colour,
                        corner_radius=6,border_width=1,
                        hover_color=button_green_hover,
    border_color=button_border_colour  )
button_measure_faz.place(x=220, y=355)

button_onh_mask = ctk.CTkButton(window, text="ONH Mask",
                        command=lambda: open_window('onh_mask', window_onh_editor, canvas),
                        width=380,height=40,
                        font=("Roboto", 14 * -1),
                        text_color=text_colour,
                        fg_color=button_green_colour,
                        corner_radius=6,border_width=1,
                        hover_color=button_green_hover,
    border_color=button_border_colour  )

# Swap back to default settings for the selected image type
# Image size: Retina/Skin = 3, ONH = 4.5
# Frangi Min-Max: Retina/ONH = 1-4, Skin = 1-8
def update_default_settings_for_type(img_type):
    previous_img_type = getattr(canvas, "_previous_img_type", None)
    target_default = IMAGE_SIZE_DEFAULTS_MM.get(img_type)

    # Assign previous values to default if not set
    if previous_img_type is None or target_default is None:
        canvas._previous_img_type = img_type
        canvas._previous_image_size = IMAGE_SIZE_DEFAULTS_MM.get(img_type, 3.0)
        return

    image_size_default = IMAGE_SIZE_DEFAULTS_MM.get(img_type)
    frangi_min_default = FRANGI_MIN_DEFAULTS_MM.get(img_type)
    frangi_max_default = FRANGI_MAX_DEFAULTS_MM.get(img_type)

    # Resetting mode-specific defaults
    canvas.image_size_var.set(image_size_default)
    canvas.frangi_min.set(frangi_min_default) if img_type != "ONH" else canvas.onh_frangi_min.set(frangi_min_default)
    canvas.frangi_max.set(frangi_max_default) if img_type != "ONH" else canvas.onh_frangi_max.set(frangi_max_default)

    canvas._previous_img_type = img_type
    canvas._previous_image_size = image_size_default
    print(f"Updating _previous_img_type to {img_type}, resetting image_size={image_size_default}, frangi_min={frangi_min_default}, frangi_max={frangi_max_default}")

def update_optional_buttons_state(*args):
    img_type = canvas.img_type_var.get()

    # Change back if current process is busy
    if disable_click_if_busy(canvas):
        return canvas.after(0, canvas.img_type_var.set(canvas._previous_img_type))

    # Update mode-specific settings
    update_default_settings_for_type(img_type)
    # Clear entire screen after changing image type
    clear_screen(canvas, clear_screen_mode=ClearMode.CLEAR_ENTIRE_SCREEN)

    # ONH mode
    if img_type == "ONH":
        canvas.coords(canvas.status_id, 875.0, 35.0)
        button_onh_mask.place(x=30, y=355)

        button_point_faz.place_forget()
        button_auto_faz.place_forget()
        button_measure_faz.place_forget()

        canvas.onh_segmentation_dropdown.place(
            x=460.0,
            y=407.0,
            width=150.0,
            height=24.0
        )

        update_onh_results_layout()

        if hasattr(canvas, "onh_overall_vessel_img"):
            update_onh_segmentation_dropdown_display(
                canvas,
                canvas.onh_segmentation_view_var.get()
            )
        
        # ONH shows diameter histogram
        if canvas._hist_mode != "diameter":
            toggle_hist_mode()
        # Hide swap button
        hist_toggle_btn.place_forget()

    # Retina/Skin mode
    else:
        canvas.coords(canvas.status_id, 950.0, 35.0)
        button_onh_mask.place_forget()

        button_point_faz.place(x=30, y=355)
        button_auto_faz.place(x=125, y=355)
        button_measure_faz.place(x=220, y=355)

        canvas.onh_segmentation_dropdown.place_forget()

        canvas.itemconfig(canvas.segmentation_title_id, text="FAZ Segmentation")
        update_default_results_layout()

    # Disable FAZ only for Skin
    if img_type == "Skin":
        button_point_faz.configure(state="disabled")
        button_auto_faz.configure(state="disabled")
        button_measure_faz.configure(state="disabled")
    else:
        button_point_faz.configure(state="normal")
        button_auto_faz.configure(state="normal")
        button_measure_faz.configure(state="normal")

    # Add swap button only for Retina/Skin
    if img_type == "Retina" or img_type == "Skin":
        hist_toggle_btn.place(x=1128, y=406.0)
    else:
        # Swap back to diameter
        if canvas._hist_mode != "diameter":
            toggle_hist_mode()
        # Hide swap button
        hist_toggle_btn.place_forget()


def set_canvas_items_state(item_ids, state):
    for item_id in item_ids:
        canvas.itemconfigure(item_id, state=state)


def update_onh_results_layout():
    set_canvas_items_state(canvas.segmentation_panel_ids, "hidden")
    set_canvas_items_state(canvas.results_panel_ids, "hidden")
    set_canvas_items_state(canvas.onh_results_panel_ids, "normal")
    canvas.itemconfigure(canvas.segmentation_title_id, state="hidden")

    canvas.coords(canvas.results_title_id, 760.0, 410.0)
    canvas.coords(canvas.bin_size_label_id, 990.0, 410.0)
    binsize_spinbox.place(x=1121.0, y=408.0)

    canvas.coords(canvas.micro_metrics_title_id, 460.0, 435.0)
    canvas.itemconfig(canvas.micro_metrics_title_id, text="ONH Microvascular Metrics")
    canvas.coords(canvas.hist_title_id, 880.0, 435.0)
    hist_frame.place(x=890, y=455)

    canvas.coords(canvas.vad_label_id, 460.0, 470.0)
    canvas.coords(canvas.vad_value_id, 603.0, 470.0)
    canvas.coords(canvas.length_density_label_id, 460.0, 525.0)
    canvas.coords(canvas.length_density_value_id, 616.0, 525.0)
    canvas.coords(canvas.mean_diameter_label_id, 460.0, 580.0)
    canvas.coords(canvas.mean_diameter_value_id, 575.0, 580.0)
    set_canvas_items_state([
        canvas.branch_density_label_id,
        canvas.branch_density_value_id,
        canvas.fractal_dim_label_id,
        canvas.fractal_dim_value_id,
    ], "hidden")
    canvas.coords(canvas.tortuosity_label_id, 460.0, 635.0)
    canvas.coords(canvas.tortuosity_value_id, 580.0, 635.0)


def update_default_results_layout():
    set_canvas_items_state(canvas.segmentation_panel_ids, "normal")
    set_canvas_items_state(canvas.results_panel_ids, "normal")
    set_canvas_items_state(canvas.onh_results_panel_ids, "hidden")
    canvas.itemconfigure(canvas.segmentation_title_id, state="normal")

    canvas.coords(canvas.results_title_id, 880.0, 410.0)
    canvas.coords(canvas.bin_size_label_id, 960.0, 410.0)
    binsize_spinbox.place(x=1082.0, y=408.0)

    canvas.coords(canvas.micro_metrics_title_id, 710.0, 435.0)
    canvas.itemconfig(canvas.micro_metrics_title_id, text="Microvascular Metrics (whole image)")
    canvas.coords(canvas.hist_title_id, 980.0, 435.0)
    hist_frame.place(x=945, y=455)

    canvas.coords(canvas.vad_label_id, 710.0, 470.0)
    canvas.coords(canvas.vad_value_id, 853.0, 470.0)
    canvas.coords(canvas.length_density_label_id, 710.0, 500.0)
    canvas.coords(canvas.length_density_value_id, 866.0, 500.0)
    canvas.coords(canvas.mean_diameter_label_id, 710.0, 530.0)
    canvas.coords(canvas.mean_diameter_value_id, 825.0, 530.0)
    set_canvas_items_state([
        canvas.branch_density_label_id,
        canvas.branch_density_value_id,
        canvas.fractal_dim_label_id,
        canvas.fractal_dim_value_id,
    ], "normal")
    canvas.coords(canvas.branch_density_label_id, 710.0, 560.0)
    canvas.coords(canvas.branch_density_value_id, 857.0, 560.0)
    canvas.coords(canvas.fractal_dim_label_id, 710.0, 590.0)
    canvas.coords(canvas.fractal_dim_value_id, 843.0, 590.0)
    canvas.coords(canvas.tortuosity_label_id, 710.0, 620.0)
    canvas.coords(canvas.tortuosity_value_id, 830.0, 620.0)




button_regional_analysis = ctk.CTkButton(window, text="Optional Regional Analysis Settings",
                        command=lambda: open_window('regional_analysis', subwindow2, canvas),
                        width=380,height=65,
                        font=("Roboto", 14 * -1),
                        text_color=text_colour,
                        fg_color=button_yellow_colour,
                        corner_radius=6,border_width=1,
                        hover_color=button_yellow_hover,
    border_color=button_border_colour  )
button_regional_analysis.place(x=30, y=415)


button_batch_processing = ctk.CTkButton(window, text="Optional Batch Processing Settings",
                        command=lambda: open_window('batch_processing', subwindow3, canvas, open_window_fn=open_window),
                        width=380,height=65,
                        font=("Roboto", 14 * -1),
                        text_color=text_colour,
                        fg_color=button_yellow_colour,
                        corner_radius=6,border_width=1,
                        hover_color=button_yellow_hover,
    border_color=button_border_colour  )
button_batch_processing.place(x=30, y=500)


button_process = ctk.CTkButton(window, text="Start Processing",
                        command=lambda: (start_processing(canvas), close_windows()),
                        state="disabled",
                        width=380,height=80,
                        font=("Roboto", 14 * -1),
                        text_color=text_colour,
                        fg_color=button_blue_colour,
                        corner_radius=6,border_width=1,
                        hover_color=button_blue_hover,
                        border_color=button_border_colour)
button_process.place(x=30, y=585)

canvas.process_button = button_process  # store ref so start_processing can toggle it

box_original = round_rectangle(canvas, 430, 100, 240, 275, radius=8)

box_binarised = round_rectangle(canvas, 685, 100, 240, 275, radius=8)

box_skeletonised = round_rectangle(canvas, 940, 100, 240, 275, radius=8)


canvas.create_text(
    525.0,
    120.0,
    anchor="nw",
    text="Original",
    fill=theme_blue,
    font=("Roboto", 16 * -1)
)

canvas.create_text(
    770.0,
    120.0,
    anchor="nw",
    text="Binarised",
    fill=theme_blue,
    font=("Roboto", 16 * -1)
)

button41 = ctk.CTkButton(window, text="Invert",
                        command=lambda: invert_binarised_image(canvas),
                        width=60,height=25,
                        font=("Roboto", 12 * -1),
                        text_color=text_colour,
                        fg_color=button_blue_colour,
                        corner_radius=4,border_width=1,
                        hover_color=button_blue_hover,
    border_color=button_border_colour  )
button41.place(x=856, y=117)

canvas.create_text(
    1015.0,
    120.0,
    anchor="nw",
    text="Skeletonised",
    fill=theme_blue,
    font=("Roboto", 16 * -1)
)

canvas.segmentation_panel_ids = round_rectangle(canvas, 430, 395, 240, 270, radius=8)
canvas.results_panel_ids = round_rectangle(canvas, 685, 395, 500, 270, radius=8)
canvas.onh_results_panel_ids = round_rectangle(canvas, 430, 395, 755, 270, radius=8)
for panel_item_id in canvas.onh_results_panel_ids:
    canvas.itemconfigure(panel_item_id, state="hidden")

canvas.segmentation_title_id = canvas.create_text(
    485.0,
    420.0,
    anchor="nw",
    text="FAZ Segmentation",
    fill=theme_blue,
    font=("Roboto", 16 * -1)
)

canvas.onh_segmentation_view_var = StringVar(value="Overall")

canvas.onh_segmentation_dropdown = Combobox(
    window,
    textvariable=canvas.onh_segmentation_view_var,
    values=["Overall", "Large Vessels", "Small Vessels"],
    state="readonly"
)
canvas.onh_segmentation_dropdown.place(
    x=550.0,
    y=400.0,
    width=110.0,
    height=20.0
)

canvas.onh_segmentation_dropdown.place_forget()

def on_onh_segmentation_dropdown_change(event=None):
    update_onh_segmentation_dropdown_display(
        canvas,
        canvas.onh_segmentation_view_var.get()
    )

canvas.onh_segmentation_dropdown.bind(
    "<<ComboboxSelected>>",
    on_onh_segmentation_dropdown_change
)

# Thumbnail zoom / pan editor
thumbnail_config = {
    "original": dict(
        cx=550,
        cy=255,
        img_id_attr="original_img_id",
        base_attr="original_img"
    ),
    "binarised": dict(
        cx=805,
        cy=255,
        img_id_attr="binary_img_id",
        base_attr="binary_image",
    ),
    "skeletonised": dict(
        cx=1060,
        cy=255,
        img_id_attr="skeleton_img_id",
        base_attr="skeleton_image",
    ),
    "faz": dict(
        cx=550,
        cy=550,
        img_id_attr="faz_img_id",
        base_attr="faz_grayscale_img",
    ),
}

thumbnail_boxes = {
    "original":     (430, 100, 670, 375),
    "binarised":    (685, 100, 925, 375),
    "skeletonised": (940, 100, 1180, 375),
    "faz":          (430, 395, 670, 665),
}

init_thumbnail_zoom_pan(canvas, thumbnail_config, thumbnail_boxes)

canvas.results_title_id = canvas.create_text(
    880.0,
    410.0,
    anchor="nw",
    text="Results",
    fill=theme_blue,
    font=("Roboto", 16 * -1)
)

canvas.bin_size_label_id = canvas.create_text(
    960.0,
    410.0,
    anchor="nw",
    text="Bin size for histogram",
    fill="#0F1F3F",
    font=("Roboto Medium", 12 * -1)
)

hist_frame = ctk.CTkFrame(window, fg_color=bg_colour, width=230, height=180)
hist_frame.place(x=945, y=450)

canvas.hist_plotter = HistogramPlotter(
    master_frame=hist_frame,
    bg_color=theme_grey,
    bar_color=theme_blue,
    axis_color=text_colour
)


# bin size Spinbox
binsize_spinbox = Spinbox(
    from_=1,
    to=10,
    width=4,
    textvariable=canvas.bin_size_var,
    command=lambda: canvas.hist_plotter.update_plot(
        canvas.tort_bin_size_var.get() if canvas._hist_mode == "tortuosity" else canvas.bin_size_var.get()
    ),
    bg=bg_colour,
    fg=text_colour,
    font=("Roboto", 12 * -1),
    bd=0.5,
    highlightthickness=0
)
binsize_spinbox.place(
    x=1082.0,
    y=408.0
)

canvas.micro_metrics_title_id = canvas.create_text(
    710.0,
    435.0,
    anchor="nw",
    text="Microvascular Metrics (whole image)",
    fill=theme_blue,
    font=("Roboto", 14 * -1)
)

# Histogram mode toggle (Diameter ↔ Tortuosity)
canvas._hist_mode = "diameter"   # "diameter" or "tortuosity"

def toggle_hist_mode():
    if canvas._hist_mode == "diameter":
        canvas._hist_mode = "tortuosity"
        canvas.hist_title_id and canvas.itemconfig(canvas.hist_title_id, text="Tortuosity Distribution")
        data     = getattr(canvas, "vessel_tortuosity", [])
        bin_size = canvas.tort_bin_size_var.get()
        binsize_spinbox.configure(from_=0.05, to=2.0, increment=0.05,
                                  textvariable=canvas.tort_bin_size_var)
    else:
        canvas._hist_mode = "diameter"
        canvas.hist_title_id and canvas.itemconfig(canvas.hist_title_id, text="Vessel Diameter Distribution")
        data     = getattr(canvas, "vessel_diameters_um", [])
        bin_size = canvas.bin_size_var.get()
        binsize_spinbox.configure(from_=1, to=10, increment=1,
                                  textvariable=canvas.bin_size_var)
    canvas.hist_plotter.set_data(data)
    canvas.hist_plotter.update_plot(bin_size)

hist_toggle_btn = ctk.CTkButton(
    window, text="Swap",
    command=toggle_hist_mode,
    width=50, height=22,
    font=("Roboto", 11 * -1),
    text_color=text_colour,
    fg_color=button_blue_colour,
    corner_radius=4, border_width=1,
    hover_color=button_blue_hover,
    border_color=button_border_colour
)
hist_toggle_btn.place(x=1128, y=406.0)

canvas.hist_title_id = canvas.create_text(
    980.0, 435.0, anchor="nw", text="Vessel Diameter Distribution",
    fill=theme_blue, font=("Roboto", 14 * -1)
)

canvas.vad_label_id = canvas.create_text(
    710.0,
    470.0,
    anchor="nw",
    text="Vessel area density = ",
    fill="#0F1F3F",
    font=("Roboto", 14 * -1)
)

canvas.vad_value_id = canvas.create_text(
    853.0, 
    470.0,
    anchor="nw",
    text="",
    fill="#0F1F3F",
    font=("Roboto", 14 * -1)
)

canvas.length_density_label_id = canvas.create_text(
    710.0,
    500.0,
    anchor="nw",
    text="Vessel length density = ",
    fill="#0F1F3F",
    font=("Roboto", 14 * -1)
)

canvas.length_density_value_id = canvas.create_text(
    866.0,
    500.0,
    anchor="nw",
    text="",
    fill="#0F1F3F",
    font=("Roboto", 14 * -1)
)

canvas.mean_diameter_label_id = canvas.create_text(
    710.0,
    530.0,
    anchor="nw",
    text="Mean diameter = ",
    fill="#0F1F3F",
    font=("Roboto", 14 * -1)
)

canvas.mean_diameter_value_id = canvas.create_text(
    825.0,
    530.0,
    anchor="nw",
    text="",
    fill="#0F1F3F",
    font=("Roboto", 14 * -1)
)

canvas.branch_density_label_id = canvas.create_text(
    710.0,
    560.0,
    anchor="nw",
    text="Branchpoint density = ",
    fill="#0F1F3F",
    font=("Roboto", 14 * -1)
)

canvas.branch_density_value_id = canvas.create_text(
    857.0,
    560.0,
    anchor="nw",
    text="",
    fill="#0F1F3F",
    font=("Roboto", 14 * -1)
)

canvas.fractal_dim_label_id = canvas.create_text(
    710.0,
    590.0,
    anchor="nw",
    text="Fractal dimension = ",
    fill="#0F1F3F",
    font=("Roboto", 14 * -1)
)

canvas.fractal_dim_value_id = canvas.create_text(
    843.0,
    590.0,
    anchor="nw",
    text="",
    fill="#0F1F3F",
    font=("Roboto", 14 * -1)
)


canvas.tortuosity_label_id = canvas.create_text(
    710.0,
    620.0,
    anchor="nw",
    text="Mean tortuosity = ",
    fill="#0F1F3F",
    font=("Roboto", 14 * -1)
)

canvas.tortuosity_value_id = canvas.create_text(
    830.0,
    620.0,
    anchor="nw",
    text="",
    fill="#0F1F3F",
    font=("Roboto", 14 * -1)
)

update_optional_buttons_state()
canvas.img_type_var.trace_add("write", lambda *args: (update_optional_buttons_state(), close_windows()))

# Event handlers
def on_prebinary_toggle():
    if disable_click_if_busy(canvas):
        prebinary_checkbox.deselect() # Revert toggle
        return

    print("Prebinary checkbox toggled, display? ", canvas.prebinary_var.get() and getattr(canvas, "bp_selected_folder_path", None) is None and getattr(canvas, "original_img", None) is not None)
    if canvas.prebinary_var.get() and getattr(canvas, "bp_selected_folder_path", None) is None and getattr(canvas, "original_img", None) is not None:
        # ONH space case:
        img_type = canvas.img_type_var.get()
        prebinary_image = canvas.original_img
        if img_type == "ONH" and hasattr(canvas, "onh_mask_img"):
            prebinary_image = canvas.onh_mask_img
        canvas.binary_image = prebinary_image
        canvas.inverted_image = prebinary_image.copy()
        display_binarised_image(canvas, prebinary_image)
    else:
        clear_screen(canvas, clear_screen_mode=ClearMode.CLEAR_BEFORE_PROCESSING)

prebinary_checkbox.configure(command=on_prebinary_toggle)

def update_image_size_spinbox_state(*args):
    if hasattr(canvas, "bp_variable_image_size_bool_var") and canvas.bp_variable_image_size_bool_var.get() == 1:
        image_size_spinbox.config(state="disabled")
    else:
        image_size_spinbox.config(state="normal")

canvas.bp_variable_image_size_bool_var.trace_add("write", update_image_size_spinbox_state)


window.resizable(False, False)
window.protocol("WM_DELETE_WINDOW", on_closing)
window.after(10, toggle_start_processing)  # toggle the 'start processing' button initially
window.mainloop()
