from pathlib import Path

# from tkinter import *
# Explicit imports to satisfy Flake8
from tkinter import Tk, Canvas, Entry, Text, Button, PhotoImage, Checkbutton, IntVar, Spinbox, StringVar
from tkinter.ttk import Combobox
from subwindow1 import *
from subwindow2 import *
from subwindow3 import *
from load_image import load_image
import customtkinter as ctk
from theme import *

OUTPUT_PATH = Path(__file__).parent
ASSETS_PATH = OUTPUT_PATH / Path(r"/Users/milameteor/Library/CloudStorage/OneDrive-UWA/M4 Backup/dev/octava/gui2/build/assets/frame0")

def relative_to_assets(path: str) -> Path:
    return ASSETS_PATH / Path(path)

window = Tk()
window.title("OCTAVA")
window.geometry("1170x820")
window.configure(bg = "#F9F9F9")

prebinary_var = IntVar(value=0)  # Variable for Prebinary checkbox
bin_size_var = IntVar()  # Variable for Bin Size Spinbox
image_size_var = IntVar()  # Variable for Image Size Spinbox
img_type_var = StringVar(value="Retina")  # Variable for Image Type dropdown

canvas = Canvas(
    window,
    bg = bg_colour,
    height = 850,
    width = 1200,
    bd = 0,
    highlightthickness = 0,
    relief = "ridge"
)


button01 = ctk.CTkButton(window, text="Save",
                        command=lambda: print("Save clicked"),
                        width=65,height=25,
                        font=("Roboto Bold", 12 * -1),
                        text_color=text_colour,
                        fg_color=button_blue_colour,
                        corner_radius=2,border_width=1,
                        hover_color=button_blue_hover,
    border_color=button_border_colour
    )
button01.place(x=35, y=10)

button02 = ctk.CTkButton(window, text="Clear",
                        command=lambda: print("Clear clicked"),
                        width=65,height=25,
                        font=("Roboto Bold", 12 * -1),
                        text_color=text_colour,
                        fg_color=button_blue_colour,
                        corner_radius=2,border_width=1,
                        hover_color=button_blue_hover,
    border_color=button_border_colour)
button02.place(x=105, y=10)

button03 = ctk.CTkButton(window, text="Help",
                        command=lambda: print("Help clicked"),
                        width=65,height=25,
                        font=("Roboto Bold", 12 * -1),
                        text_color=text_colour,
                        fg_color=button_blue_colour,
                        corner_radius=2,border_width=1,
                        hover_color=button_blue_hover,
    border_color=button_border_colour)
button03.place(x=175, y=10)

button04 = ctk.CTkButton(window, text="Feedback",
                        command=lambda: print("Feedback clicked"),
                        width=65,height=25,
                        font=("Roboto Bold", 12 * -1),
                        text_color=text_colour,
                        fg_color=button_blue_colour,
                        corner_radius=2,border_width=1,
                        hover_color=button_blue_hover,
    border_color=button_border_colour)
button04.place(x=245, y=10)

button04 = ctk.CTkButton(window, text="Update",
                        command=lambda: print("Update clicked"),
                        width=65,height=25,
                        font=("Roboto Bold", 12 * -1),
                        text_color=text_colour,
                        fg_color=button_blue_colour,
                        corner_radius=2,border_width=1,
                        hover_color=button_blue_hover,
    border_color=button_border_colour)
button04.place(x=315, y=10)


canvas.place(x = 0, y = 0)
canvas.create_text(
    38.0,
    50.0,
    anchor="nw",
    text="OCTAVA",
    fill=theme_blue,
    font=("Roboto Bold", 26 * -1)
)

canvas.create_text(
    905.0,
    30.0,
    anchor="nw",
    text="🟢 Ready",
    fill=theme_blue,
    font=("Roboto Bold", 20 * -1)
)


image_image_6 = PhotoImage(
    file=relative_to_assets("image_6.png"))
image_6 = canvas.create_image(
    505.0,
    65.0,
    image=image_image_6
)

canvas.create_text(
    184.0,
    58.0,
    anchor="nw",
    text="Filename",
    fill=theme_blue,
    font=("Roboto Bold", 12 * -1)
)


image_image_1 = PhotoImage(
    file=relative_to_assets("image_1.png"))
image_1 = canvas.create_image(
    165.0,
    240,
    image=image_image_1
)

image_image_2 = PhotoImage(
    file=relative_to_assets("image_2.png"))
image_2 = canvas.create_image(
    445.0,
    240,
    image=image_image_2
)

image_image_3 = PhotoImage(
    file=relative_to_assets("image_3.png"))
image_3 = canvas.create_image(
    725.0,
    240,
    image=image_image_3
)

image_image_4 = PhotoImage(
    file=relative_to_assets("image_4.png"))
image_4 = canvas.create_image(
    1005.0,
    240,
    image=image_image_4
)

canvas.create_text(
    135.0,
    110.0,
    anchor="nw",
    text="Original",
    fill=theme_blue,
    font=("Roboto Bold", 16 * -1)
)

canvas.create_text(
    397.0,
    110.0,
    anchor="nw",
    text="Segmented",
    fill=theme_blue,
    font=("Roboto Bold", 16 * -1)
)

canvas.create_text(
    677.0,
    110.0,
    anchor="nw",
    text="Skeletonized",
    fill=theme_blue,
    font=("Roboto Bold", 16 * -1)
)

canvas.create_text(
    945.0,
    110.0,
    anchor="nw",
    text="FAZ Segmentation",
    fill=theme_blue,
    font=("Roboto Bold", 16 * -1)
)

button1 = ctk.CTkButton(window, text="Load image",
                        command=lambda: load_image(canvas, 165, 250, 280, 65),
                        width=135,height=40,
                        font=("Roboto Bold", 16 * -1),
                        text_color=text_colour,
                        fg_color=button_blue_colour,
                        corner_radius=8,border_width=1,
                        hover_color=button_blue_hover,
    border_color=button_border_colour  )
button1.place(x=56, y=395)

button10 = ctk.CTkButton(window, text="Save folder",
                        command=lambda: print("Save folder clicked"),
                        width=135,height=40,
                        font=("Roboto Bold", 16 * -1),
                        text_color=text_colour,
                        fg_color=button_blue_colour,
                        corner_radius=8,border_width=1,
                        hover_color=button_blue_hover,
    border_color=button_border_colour  )
button10.place(x=211, y=395)

button3 = ctk.CTkButton(window, text="Process",
                        command=lambda: print("Process clicked"),
                        width=135,height=40,
                        font=("Roboto Bold", 16 * -1),
                        text_color=text_colour,
                        fg_color=button_blue_colour,
                        corner_radius=8,border_width=1,
                        hover_color=button_blue_hover,
    border_color=button_border_colour  )
button3.place(x=366, y=395)

button41 = ctk.CTkButton(window, text="Invert",
                        command=lambda: print("Invert clicked"),
                        width=135,height=40,
                        font=("Roboto Bold", 16 * -1),
                        text_color=text_colour,
                        fg_color=button_blue_colour,
                        corner_radius=8,border_width=1,
                        hover_color=button_blue_hover,
    border_color=button_border_colour  )
button41.place(x=521, y=395)

button7 = ctk.CTkButton(window, text="Free FAZ",
                        command=lambda: print("Free FAZ clicked"),
                        width=135,height=40,
                        font=("Roboto Bold", 16 * -1),
                        text_color=text_colour,
                        fg_color=button_green_colour,
                        corner_radius=8,border_width=1,
                        hover_color=button_green_hover,
    border_color=button_border_colour  )
button7.place(x=676, y=395)


button8 = ctk.CTkButton(window, text="Measure FAZ",
                        command=lambda: print("Measure FAZ clicked"),
                        width=135,height=40,
                        font=("Roboto Bold", 16 * -1),
                        text_color=text_colour,
                        fg_color=button_green_colour,
                        corner_radius=8,border_width=1,
                        hover_color=button_green_hover,
    border_color=button_border_colour  )
button8.place(x=831, y=395)


button9 = ctk.CTkButton(window, text="Rapid FAZ",
                        command=lambda: print("Rapid FAZ clicked"),
                        width=135,height=40,
                        font=("Roboto Bold", 16 * -1),
                        text_color=text_colour,
                        fg_color=button_green_colour,
                        corner_radius=8,border_width=1,
                        hover_color=button_green_hover,
    border_color=button_border_colour  )
button9.place(x=986, y=395)


button4 = ctk.CTkButton(window, text="Advanced Settings",
                        command=subwindow1,
                        width=300,height=80,
                        font=("Roboto Bold", 16 * -1),
                        text_color=text_colour,
                        fg_color=button_yellow_colour,
                        corner_radius=8,border_width=1,
                        hover_color=button_yellow_hover,
    border_color=button_border_colour  )
button4.place(x=825, y=490)


button5 = ctk.CTkButton(window, text="Regional Analysis Settings",
                        command=subwindow2,
                        width=300,height=80,
                        font=("Roboto Bold", 16 * -1),
                        text_color=text_colour,
                        fg_color=button_yellow_colour,
                        corner_radius=8,border_width=1,
                        hover_color=button_yellow_hover,
    border_color=button_border_colour  )
button5.place(x=825, y=595)

button5 = ctk.CTkButton(window, text="Batch Processing Settings",
                        command=subwindow3,
                        width=300,height=80,
                        font=("Roboto Bold", 16 * -1),
                        text_color=text_colour,
                        fg_color=button_yellow_colour,
                        corner_radius=8,border_width=1,
                        hover_color=button_yellow_hover,
    border_color=button_border_colour  )
button5.place(x=825, y=700)


# Metrics background
image_image_7 = PhotoImage(
    file=relative_to_assets("image_metrics.png"))
image_7 = canvas.create_image(
    260.0,
    640.0,
    image=image_image_7
)

# diagram background
image_image_5 = PhotoImage(
    file=relative_to_assets("image_5.png"))
image_5 = canvas.create_image(
    650.0,
    640.0,
    image=image_image_5
)

canvas.create_text(
    620.0,
    500.0,
    anchor="nw",
    text="Diameter",
    fill=theme_blue,
    font=("Roboto Bold", 16 * -1)
)

canvas.create_text(
    565.0,
    760.0,
    anchor="nw",
    text="Bin size for histograms",
    fill="#0F1F3F",
    font=("Roboto Medium", 12 * -1)
)

# bin size Spinbox
binsize_spinbox = Spinbox(
    from_=1,
    to=10,
    width=2,
    textvariable=bin_size_var,
    bg=bg_colour,
    fg=text_colour,
    font=("Roboto", 12 * -1),
    bd=0.5,                  # removes the border thickness
    highlightthickness=0  # removes the focus highlight border
)
binsize_spinbox.place(
    x=705.0,
    y=758.0
)


# prebinary
prebinary_checkbox = Checkbutton(
    text="Prebinary",
    variable=prebinary_var,
    bg=bg_colour,
    fg="#10203F",
    font=("Roboto", 14 * -1)
)
prebinary_checkbox.place(
    x=210.0,
    y=450.0
)


# image type dropdown
img_type_list = ["Retina", "ONH", "Skin"]
img_type = Combobox(
    textvariable=img_type_var,
    values=img_type_list,
    state="readonly"
)
img_type.place(
    x=65.0,
    y=450.0,
    width=115.0,
    height=30.0
)

# def show_selection(event=None):
#     print("Selected:", img_type_var.get())

# img_type.bind("<<ComboboxSelected>>", show_selection)

canvas.create_text(
    330.0,
    455.0,
    anchor="nw",
    text="Image size (mm)",
    fill=text_colour,
    font=("Roboto", 14 * -1)
)

# image size Spinbox
image_size_spinbox = Spinbox(
    from_=1,
    to=10,
    width=3,
    textvariable=image_size_var,
    bg=bg_colour,
    fg=text_colour,
    font=("Roboto", 14 * -1),
    bd=0.5,                  # removes the border thickness
    highlightthickness=0,  # removes the focus highlight border
)
image_size_spinbox.place(
    x=450.0,
    y=454.0
)

# entry_image_1 = PhotoImage(
#     file=relative_to_assets("entry_1.png"))
# entry_bg_1 = canvas.create_image(
#     470.0,
#     465.0,
#     image=entry_image_1
# )
# entry_1 = Entry(
#     bd=0,
#     bg="#EFEFEF",
#     fg="#000716",
#     highlightthickness=0,
#     justify='center'
# )
# entry_1.place(
#     x=455.0,
#     y=455.0,
#     width=30.0,
#     height=18.0
# )

canvas.create_text(
    245.0,
    500.0,
    anchor="nw",
    text="Metrics",
    fill=theme_blue,
    font=("Roboto Bold", 16 * -1)
)

canvas.create_text(
    70.0,
    540.0,
    anchor="nw",
    text="Vessel area density = ",
    fill="#0F1F3F",
    font=("Roboto SemiBold", 14 * -1)
)

canvas.create_text(
    70.0,
    580.0,
    anchor="nw",
    text="Vessel length density = ",
    fill="#0F1F3F",
    font=("Roboto SemiBold", 14 * -1)
)

canvas.create_text(
    70.0,
    620.0,
    anchor="nw",
    text="Mean diameter = ",
    fill="#0F1F3F",
    font=("Roboto SemiBold", 14 * -1)
)

canvas.create_text(
    70.0,
    660.0,
    anchor="nw",
    text="Branchpoint density = ",
    fill="#0F1F3F",
    font=("Roboto SemiBold", 14 * -1)
)

canvas.create_text(
    70.0,
    700.0,
    anchor="nw",
    text="Fractal dimension = ",
    fill="#0F1F3F",
    font=("Roboto SemiBold", 14 * -1)
)

canvas.create_text(
    70.0,
    740.0,
    anchor="nw",
    text="Mean tortuosity = ",
    fill="#0F1F3F",
    font=("Roboto SemiBold", 14 * -1)
)



window.resizable(False, False)
window.mainloop()
