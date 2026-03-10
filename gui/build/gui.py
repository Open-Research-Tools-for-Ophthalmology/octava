from pathlib import Path
from tkinter import Tk, Canvas, Entry, Text, Button, PhotoImage, Checkbutton, IntVar, Spinbox, StringVar, ttk, DoubleVar
from tkinter.ttk import Combobox
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
from modules.load_image import *
from modules.select_save_folder import *
from modules.start_processing import *
from modules.round_rectangle import *
from modules.change_status import *
from modules.binarise_image import *
from modules.clear import *
from modules.faz_utils import *
from modules.histogram import HistogramPlotter
from test import *

OUTPUT_PATH = Path(__file__).parent

# Global window registry
OPEN_WINDOWS = {}

# If window exists, bring to front, otherwise create
def open_window(key, callback, *args, **kwargs):
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

canvas.frangi_bool = IntVar(value=1)  # Variable for Frangi checkbox, default to true
canvas.frangi_min = IntVar(value=1)  # Variable for Frangi min sigma
canvas.frangi_max = IntVar(value=4)  # Variable for Frangi max sigma
canvas.med_filt_bool = IntVar(value=0)  # Variable for Median Filter checkbox
canvas.twig_size = IntVar(value=8)  # Variable for Twig Size Spinbox
canvas.kernel_size = IntVar(value=3)  # Variable for Kernel Size Spinbox
canvas.prebinary_var = IntVar(value=0)  # Variable for Prebinary checkbox
canvas.bin_size_var = IntVar(value=10)  # Variable for Bin Size Spinbox
canvas.image_size_var = DoubleVar(value=5.00)  # Variable for Image Size Spinbox
canvas.img_type_var = StringVar(value="Retina")  # Variable for Image Type dropdown
# regional analysis settings variables
canvas.eye_var = StringVar(value="Right Eye")
canvas.load_faz_bool = IntVar(value=0)
canvas.square_grid_bool = IntVar(value=0)
canvas.etdrs_grid_bool = IntVar(value=0)
canvas.extended_etdrs_bool = IntVar(value=0)
canvas.foveal_ring_bool = IntVar(value=0)
canvas.optic_nerve_head_bool = IntVar(value=0)
canvas.apply_regional_analysis_bool = IntVar(value=0)
canvas.bp_file_type_var = StringVar(value="tif")  # Variable for File Type dropdown (Batch Processing Settings)
canvas.bp_batch_resize_var = IntVar(value=0)  # Variable for Batch Resize checkbox (Batch Processing Settings)
canvas.bp_batch_resize_value = IntVar(value=1000)  # Variable for Batch Resize value Spinbox (Batch Processing Settings)
canvas.bp_measure_faz_var = IntVar(value=0)  # Variable for Measure FAZ checkbox (Batch Processing Settings)

# Initialize batch processing settings on canvas        
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

button01 = ctk.CTkButton(window, text="Clear",
                        command=lambda: clear_screen(canvas),
                        width=65,height=25,
                        font=("Roboto", 12 * -1),
                        text_color=text_colour,
                        fg_color=button_blue_colour,
                        corner_radius=2,border_width=1,
                        hover_color=button_blue_hover,
                        border_color=button_border_colour)
button01.place(x=155, y=35)

button02 = ctk.CTkButton(window, text="Help",
                        command=lambda: open_window('help', open_help_window, canvas),
                        width=65,height=25,
                        font=("Roboto", 12 * -1),
                        text_color=text_colour,
                        fg_color=button_blue_colour,
                        corner_radius=2,border_width=1,
                        hover_color=button_blue_hover,
    border_color=button_border_colour)
button02.place(x=225, y=35)

button03 = ctk.CTkButton(window, text="Feedback",
                        command=lambda: open_window('feedback', open_feedback_window, canvas),
                        width=65,height=25,
                        font=("Roboto", 12 * -1),
                        text_color=text_colour,
                        fg_color=button_blue_colour,
                        corner_radius=2,border_width=1,
                        hover_color=button_blue_hover,
    border_color=button_border_colour)
button03.place(x=295, y=35)

button04 = ctk.CTkButton(window, text="Subscribe to Updates",
                        command=lambda: open_window('subscribe', open_subscribe_window, canvas),
                        width=65,height=25,
                        font=("Roboto", 12 * -1),
                        text_color=text_colour,
                        fg_color=button_blue_colour,
                        corner_radius=2,border_width=1,
                        hover_color=button_blue_hover,
    border_color=button_border_colour)
button04.place(x=365, y=35)

canvas.status_id = canvas.create_text(
    950.0,
    35.0,
    anchor="nw",
    text="🟢 Ready",
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


button_loadimg = ctk.CTkButton(window, text="Load Image",
                        command=lambda: load_image(canvas, 550, 255, 180, 170),
                        width=120,height=40,
                        font=("Roboto", 14 * -1),
                        text_color=text_colour,
                        fg_color=button_blue_colour,
                        corner_radius=8,border_width=1,
                        hover_color=button_blue_hover,
    border_color=button_border_colour  )
button_loadimg.place(x=30, y=150)
round_rectangle(canvas, 160, 150, 250, 40, radius=8)


button_save_folder = ctk.CTkButton(window, text="Save Folder",
                        command=lambda: select_save_folder(canvas, text_x=180, text_y=230),
                        width=120,height=40,
                        font=("Roboto", 14 * -1),
                        text_color=text_colour,
                        fg_color=button_blue_colour,
                        corner_radius=8,border_width=1,
                        hover_color=button_blue_hover,
    border_color=button_border_colour  )
button_save_folder.place(x=30, y=210)
round_rectangle(canvas, 160, 210, 250, 40, radius=8)


button_advanced_settings = ctk.CTkButton(window, text="Optional Advanced Settings",
                        command=lambda: open_window('advanced_settings', subwindow1, canvas),
                        width=380,height=65,
                        font=("Roboto", 14 * -1),
                        text_color=text_colour,
                        fg_color=button_yellow_colour,
                        corner_radius=8,border_width=1,
                        hover_color=button_yellow_hover,
    border_color=button_border_colour  )
button_advanced_settings.place(x=30, y=270)

button_point_faz = ctk.CTkButton(window, text="Point FAZ",
                                command=lambda: open_window('point_faz', subwindow4, canvas, editable=True),
                                width=80,height=40,
                                font=("Roboto", 12 * -1),
                                text_color=text_colour,
                                fg_color=button_green_colour,
                                corner_radius=8,border_width=1,
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
                                corner_radius=8,border_width=1,
                                hover_color=button_green_hover,
    border_color=button_border_colour  )
button_auto_faz.place(x=125, y=355)

button_measure_faz = ctk.CTkButton(window, text="Measure FAZ",
                        command=lambda: measure_faz(canvas),
                        width=190,height=40,
                        font=("Roboto", 14 * -1),
                        text_color=text_colour,
                        fg_color=button_green_colour,
                        corner_radius=8,border_width=1,
                        hover_color=button_green_hover,
    border_color=button_border_colour  )
button_measure_faz.place(x=220, y=355)

def update_faz_buttons_state(*args):
    if canvas.img_type_var.get()=="Skin":
        button_point_faz.configure(state="disabled")
        button_auto_faz.configure(state="disabled")
        button_measure_faz.configure(state="disabled")
    else:
        button_point_faz.configure(state="normal")
        button_auto_faz.configure(state="normal")
        button_measure_faz.configure(state="normal")

update_faz_buttons_state()

canvas.img_type_var.trace_add("write", update_faz_buttons_state)


button_regional_analysis = ctk.CTkButton(window, text="Optional Regional Analysis Settings",
                        command=lambda: open_window('regional_analysis', subwindow2, canvas),
                        width=380,height=65,
                        font=("Roboto", 14 * -1),
                        text_color=text_colour,
                        fg_color=button_yellow_colour,
                        corner_radius=8,border_width=1,
                        hover_color=button_yellow_hover,
    border_color=button_border_colour  )
button_regional_analysis.place(x=30, y=415)


button_batch_processing = ctk.CTkButton(window, text="Optional Batch Processing Settings",
                        command=lambda: open_window('batch_processing', subwindow3, canvas),
                        width=380,height=65,
                        font=("Roboto", 14 * -1),
                        text_color=text_colour,
                        fg_color=button_yellow_colour,
                        corner_radius=8,border_width=1,
                        hover_color=button_yellow_hover,
    border_color=button_border_colour  )
button_batch_processing.place(x=30, y=500)


button_process = ctk.CTkButton(window, text="Start Processing",
                        command=lambda: start_processing(canvas),
                        width=380,height=80,
                        font=("Roboto", 14 * -1),
                        text_color=text_colour,
                        fg_color=button_blue_colour,
                        corner_radius=8,border_width=1,
                        hover_color=button_blue_hover,
                        border_color=button_border_colour)
button_process.place(x=30, y=585)


round_rectangle(canvas, 430, 100, 240, 275, radius=8)

round_rectangle(canvas, 685, 100, 240, 275, radius=8)

round_rectangle(canvas, 940, 100, 240, 275, radius=8)


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

round_rectangle(canvas, 430, 395, 240, 270, radius=8)
round_rectangle(canvas, 685, 395, 500, 270, radius=8)


canvas.create_text(
    485.0,
    420.0,
    anchor="nw",
    text="FAZ Segmentation",
    fill=theme_blue,
    font=("Roboto", 16 * -1)
)

canvas.create_text(
    910.0,
    410.0,
    anchor="nw",
    text="Results",
    fill=theme_blue,
    font=("Roboto", 16 * -1)
)

canvas.create_text(
    990.0,
    410.0,
    anchor="nw",
    text="Bin size for histogram",
    fill="#0F1F3F",
    font=("Roboto Medium", 12 * -1)
)

hist_frame = ctk.CTkFrame(window, fg_color=bg_colour, width=230, height=180)
hist_frame.place(x=945, y=455)

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
    width=2,
    textvariable=canvas.bin_size_var,
    command=lambda: canvas.hist_plotter.update_plot(canvas.bin_size_var.get()),
    bg=bg_colour,
    fg=text_colour,
    font=("Roboto", 12 * -1),
    bd=0.5,                  # removes the border thickness
    highlightthickness=0  # removes the focus highlight border
)
binsize_spinbox.place(
    x=1121.0,
    y=408.0
)

canvas.create_text(
    710.0,
    435.0,
    anchor="nw",
    text="Microvascular Metrics (whole image)",
    fill=theme_blue,
    font=("Roboto", 14 * -1)
)

canvas.create_text(
    980.0,
    435.0,
    anchor="nw",
    text="Vessel Diameter Distribution",
    fill=theme_blue,
    font=("Roboto", 14 * -1)
)

canvas.create_text(
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

canvas.create_text(
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

canvas.create_text(
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

canvas.create_text(
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

canvas.create_text(
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


canvas.create_text(
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

# Event handlers
def on_prebinary_toggle():
    if canvas.prebinary_var.get() and getattr(canvas, "bp_selected_folder_path", None) is None and getattr(canvas, "original_img", None) is not None:
        canvas.binary_image = canvas.original_img
        canvas.inverted_image = canvas.original_img.copy()
        display_binarised_image(canvas, canvas.original_img)
    else:
        clear_screen(canvas, clear_screen_mode=ClearMode.CLEAR_BEFORE_PROCESSING)

prebinary_checkbox.configure(command=on_prebinary_toggle)

window.resizable(False, False)
window.mainloop()
