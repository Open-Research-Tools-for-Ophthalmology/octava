from pathlib import Path

# from tkinter import *
# Explicit imports to satisfy Flake8
from tkinter import Tk, Canvas, Entry, Text, Button, PhotoImage, Checkbutton, IntVar, Spinbox
from tkinter.ttk import Combobox
from subwindow1 import *
from subwindow2 import *
from subwindow3 import *
from load_image import load_image
import customtkinter as ctk

OUTPUT_PATH = Path(__file__).parent
ASSETS_PATH = OUTPUT_PATH / Path(r"/Users/milameteor/Library/CloudStorage/OneDrive-UWA/M4 Backup/dev/octava/gui2/build/assets/frame0")

def relative_to_assets(path: str) -> Path:
    return ASSETS_PATH / Path(path)

window = Tk()
window.title("OCTAVA")
window.geometry("1200x850")
window.configure(bg = "#F9F9F9")

prebinary_var = IntVar()  # Variable for Prebinary checkbox

bg_colour = "#F9F9F9"
text_colour = "#10203F"
button_green_colour = "#DDF6D4"
button_yellow_colour = "#FEF0BC"
button_yellow_hover = "#FFF4C1"
button_blue_hover = "#DBF2FF"
button_green_hover = "#EAFCE3"
button_blue_colour = "#CDEDFF"
button_border_colour = "#4D4D4D"
theme_blue = "#4483FF"

canvas = Canvas(
    window,
    bg = bg_colour,
    height = 850,
    width = 1200,
    bd = 0,
    highlightthickness = 0,
    relief = "ridge"
)

canvas.place(x = 0, y = 0)
canvas.create_text(
    38.0,
    30.0,
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

image_image_1 = PhotoImage(
    file=relative_to_assets("image_1.png"))
image_1 = canvas.create_image(
    165.0,
    220.0,
    image=image_image_1
)

image_image_2 = PhotoImage(
    file=relative_to_assets("image_2.png"))
image_2 = canvas.create_image(
    455.0,
    220.0,
    image=image_image_2
)

image_image_3 = PhotoImage(
    file=relative_to_assets("image_3.png"))
image_3 = canvas.create_image(
    745.0,
    220.0,
    image=image_image_3
)

image_image_4 = PhotoImage(
    file=relative_to_assets("image_4.png"))
image_4 = canvas.create_image(
    1035.0,
    220.0,
    image=image_image_4
)

image_image_5 = PhotoImage(
    file=relative_to_assets("image_5.png"))
image_5 = canvas.create_image(
    488.0,
    670.0,
    image=image_image_5
)

canvas.create_text(
    135.0,
    94.0,
    anchor="nw",
    text="Original",
    fill=theme_blue,
    font=("Roboto Bold", 16 * -1)
)

canvas.create_text(
    397.0,
    94.0,
    anchor="nw",
    text="Segmented",
    fill=theme_blue,
    font=("Roboto Bold", 16 * -1)
)

canvas.create_text(
    687.0,
    94.0,
    anchor="nw",
    text="Skeletonized",
    fill=theme_blue,
    font=("Roboto Bold", 16 * -1)
)

canvas.create_text(
    953.0,
    94.0,
    anchor="nw",
    text="FAZ Segmentation",
    fill=theme_blue,
    font=("Roboto Bold", 16 * -1)
)

canvas.create_text(
    444.0,
    533.0,
    anchor="nw",
    text="Diameter",
    fill=theme_blue,
    font=("Roboto Bold", 16 * -1)
)

image_image_6 = PhotoImage(
    file=relative_to_assets("image_6.png"))
image_6 = canvas.create_image(
    506.0,
    47.0,
    image=image_image_6
)

canvas.create_text(
    184.0,
    39.0,
    anchor="nw",
    text="Filename",
    fill=theme_blue,
    font=("Roboto Bold", 12 * -1)
)

button1 = ctk.CTkButton(window, text="Load image",
                        command=lambda: load_image(canvas, 165, 230, 300, 45),
                        width=135,height=40,
                        font=("Roboto Bold", 16 * -1),
                        text_color=text_colour,
                        fg_color=button_blue_colour,
                        corner_radius=8,border_width=1,
                        hover_color=button_blue_hover,
    border_color=button_border_colour  )
button1.place(x=33, y=380)

button3 = ctk.CTkButton(window, text="Process",
                        command=lambda: print("Process clicked"),
                        width=135,height=40,
                        font=("Roboto Bold", 16 * -1),
                        text_color=text_colour,
                        fg_color=button_blue_colour,
                        corner_radius=8,border_width=1,
                        hover_color=button_blue_hover,
    border_color=button_border_colour  )
button3.place(x=380, y=380)


button41 = ctk.CTkButton(window, text="Invert",
                        command=lambda: print("Invert clicked"),
                        width=135,height=40,
                        font=("Roboto Bold", 16 * -1),
                        text_color=text_colour,
                        fg_color=button_blue_colour,
                        corner_radius=8,border_width=1,
                        hover_color=button_blue_hover,
    border_color=button_border_colour  )
button41.place(x=550, y=380)


button4 = ctk.CTkButton(window, text="Advanced Settings",
                        command=subwindow1,
                        width=250,height=70,
                        font=("Roboto Bold", 16 * -1),
                        text_color=text_colour,
                        fg_color=button_yellow_colour,
                        corner_radius=8,border_width=1,
                        hover_color=button_yellow_hover,
    border_color=button_border_colour  )
button4.place(x=900, y=500)


button5 = ctk.CTkButton(window, text="Regional Analysis Settings",
                        command=subwindow2,
                        width=250,height=70,
                        font=("Roboto Bold", 16 * -1),
                        text_color=text_colour,
                        fg_color=button_yellow_colour,
                        corner_radius=8,border_width=1,
                        hover_color=button_yellow_hover,
    border_color=button_border_colour  )
button5.place(x=900, y=600)

button5 = ctk.CTkButton(window, text="Batch Processing Settings",
                        command=subwindow3,
                        width=250,height=70,
                        font=("Roboto Bold", 16 * -1),
                        text_color=text_colour,
                        fg_color=button_yellow_colour,
                        corner_radius=8,border_width=1,
                        hover_color=button_yellow_hover,
    border_color=button_border_colour  )
button5.place(x=900, y=700)


button7 = ctk.CTkButton(window, text="Free FAZ",
                        command=lambda: print("Free FAZ clicked"),
                        width=135,height=40,
                        font=("Roboto Bold", 16 * -1),
                        text_color=text_colour,
                        fg_color=button_green_colour,
                        corner_radius=8,border_width=1,
                        hover_color=button_green_hover,
    border_color=button_border_colour  )
button7.place(x=700, y=380)

button8 = ctk.CTkButton(window, text="Measure FAZ",
                        command=lambda: print("Measure FAZ clicked"),
                        width=135,height=40,
                        font=("Roboto Bold", 16 * -1),
                        text_color=text_colour,
                        fg_color=button_green_colour,
                        corner_radius=8,border_width=1,
                        hover_color=button_green_hover,
    border_color=button_border_colour  )
button8.place(x=850, y=380)


button9 = ctk.CTkButton(window, text="Rapid FAZ",
                        command=lambda: print("Rapid FAZ clicked"),
                        width=135,height=40,
                        font=("Roboto Bold", 16 * -1),
                        text_color=text_colour,
                        fg_color=button_green_colour,
                        corner_radius=8,border_width=1,
                        hover_color=button_green_hover,
    border_color=button_border_colour  )
button9.place(x=1000, y=380)

button10 = ctk.CTkButton(window, text="Save folder",
                        command=lambda: print("Save folder clicked"),
                        width=135,height=40,
                        font=("Roboto Bold", 16 * -1),
                        text_color=text_colour,
                        fg_color=button_blue_colour,
                        corner_radius=8,border_width=1,
                        hover_color=button_blue_hover,
    border_color=button_border_colour  )
button10.place(x=200, y=380)


image_image_7 = PhotoImage(
    file=relative_to_assets("image_7.png"))
image_7 = canvas.create_image(
    175.0,
    670.0,
    image=image_image_7
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
    x=185.0,
    y=475.0
)


# image type dropdown
img_type_list = ["Retina", "ONH", "Skin"]
img_type = Combobox(
    values=img_type_list,
    state="readonly"
)
img_type.set("Retina")  # Default value
img_type.place(
    x=37.0,
    y=475.0,
    width=115.0,
    height=30.0
)

canvas.create_text(
    300.0,
    480.0,
    anchor="nw",
    text="Image size (mm)",
    fill=text_colour,
    font=("Roboto", 14 * -1)
)

entry_image_1 = PhotoImage(
    file=relative_to_assets("entry_1.png"))
entry_bg_1 = canvas.create_image(
    480.0,
    480.0,
    image=entry_image_1
)
entry_1 = Entry(
    bd=0,
    bg="#EFEFEF",
    fg="#000716",
    highlightthickness=0,
    justify='center'
)
entry_1.place(
    x=450.0,
    y=470.0,
    width=86.0,
    height=25.0
)

canvas.create_text(
    38.0,
    9.0,
    anchor="nw",
    text="Save",
    fill="#10203F",
    font=("Roboto Bold", 12 * -1)
)

canvas.create_text(
    81.0,
    9.0,
    anchor="nw",
    text="Clear",
    fill="#10203F",
    font=("Roboto Bold", 12 * -1)
)

canvas.create_text(
    125.0,
    9.0,
    anchor="nw",
    text="Help",
    fill="#10203F",
    font=("Roboto Bold", 12 * -1)
)

canvas.create_text(
    168.0,
    9.0,
    anchor="nw",
    text="Feedback",
    fill="#10203F",
    font=("Roboto Bold", 12 * -1)
)

canvas.create_text(
    99.0,
    531.0,
    anchor="nw",
    text="Metrics",
    fill=theme_blue,
    font=("Roboto Bold", 16 * -1)
)

canvas.create_text(
    53.0,
    568.0,
    anchor="nw",
    text="Vessel area density = ",
    fill="#0F1F3F",
    font=("Roboto SemiBold", 14 * -1)
)

canvas.create_text(
    53.0,
    610.0,
    anchor="nw",
    text="Vessel length density = ",
    fill="#0F1F3F",
    font=("Roboto SemiBold", 14 * -1)
)

canvas.create_text(
    407.0,
    791.0,
    anchor="nw",
    text="Bin size for histograms",
    fill="#0F1F3F",
    font=("Roboto Medium", 12 * -1)
)

canvas.create_text(
    53.0,
    652.0,
    anchor="nw",
    text="Mean diameter = ",
    fill="#0F1F3F",
    font=("Roboto SemiBold", 14 * -1)
)

canvas.create_text(
    53.0,
    694.0,
    anchor="nw",
    text="Branchpoint density = ",
    fill="#0F1F3F",
    font=("Roboto SemiBold", 14 * -1)
)

canvas.create_text(
    53.0,
    736.0,
    anchor="nw",
    text="Fractal dimension = ",
    fill="#0F1F3F",
    font=("Roboto SemiBold", 14 * -1)
)

canvas.create_text(
    53.0,
    778.0,
    anchor="nw",
    text="Mean tortuosity = ",
    fill="#0F1F3F",
    font=("Roboto SemiBold", 14 * -1)
)
window.resizable(False, False)
window.mainloop()
