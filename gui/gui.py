from pathlib import Path

# from tkinter import *
# Explicit imports to satisfy Flake8
from tkinter import Tk, Canvas, Entry, Text, Button, PhotoImage, Checkbutton, IntVar, Spinbox
from tkinter.ttk import Combobox
from tkinter import filedialog
from PIL import Image, ImageTk
import os


OUTPUT_PATH = Path(__file__).parent
ASSETS_PATH = OUTPUT_PATH / Path(r"/Users/milameteor/Library/CloudStorage/OneDrive-UWA/M4 Backup/dev/octava/build/assets/frame0")


def relative_to_assets(path: str) -> Path:
    return ASSETS_PATH / Path(path)

loaded_image_tk = None  # Keep reference to prevent garbage collection
loaded_image_id = None  # Canvas object ID of the loaded image
filename_text_id = None  # Canvas text object for showing filename

def load_image():
    global loaded_image_tk, loaded_image_id, filename_text_id

    file_path = filedialog.askopenfilename(
        title="Select an image",
        filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.tiff")]
    )
    if file_path:
        # Load and resize image to fit inside image_1.png's frame
        img = Image.open(file_path).resize((140, 140))  # Adjust as needed
        loaded_image_tk = ImageTk.PhotoImage(img)

        # If an image was already added, remove it
        if loaded_image_id is not None:
            canvas.delete(loaded_image_id)

        # Add the new image on top of the background frame
        loaded_image_id = canvas.create_image(
            110.70831298828125,  # same as image_1 X
            151.0+5,               # same as image_1 Y
            image=loaded_image_tk
        )

        # 👇 Display filename above image_6.png
        filename = os.path.basename(file_path)

        if filename_text_id is not None:
            canvas.delete(filename_text_id)

        # image_6 is at x=338.0, y=33.0 → place text near it
        filename_text_id = canvas.create_text(
            338.0,
            33.0,  # slight offset above image_6
            text=filename,
            fill="#333333",
            font=("Roboto", 10 * -1),
        )


window = Tk()

window.geometry("1000x600")
window.configure(bg = "#FFFFFF")


med_filt_on = IntVar()  # True or false for Med Filt checkbox
med_filt_var = IntVar()  # Value for Med Filt Spinbox
display_overlay_var = IntVar()  # Variable for Display Overlay checkbox
prebinary_var = IntVar()  # Variable for Prebinary checkbox
frangi_var = IntVar()  # Variable for Frangi checkbox


canvas = Canvas(
    window,
    bg = "#FFFFFF",
    height = 600,
    width = 1000,
    bd = 0,
    highlightthickness = 0,
    relief = "ridge"
)

canvas.place(x = 0, y = 0)
canvas.create_text(
    28.0,
    17.0,
    anchor="nw",
    text="OCTAVA",
    fill="#5E95FF",
    font=("Roboto Bold", 26 * -1)
)

canvas.create_text(
    525.0,
    18.0,
    anchor="nw",
    text="🟢 Ready",
    fill="#5E95FF",
    font=("Roboto Bold", 20 * -1)
)

image_image_1 = PhotoImage(
    file=relative_to_assets("image_1.png"))
image_1 = canvas.create_image(
    110.70831298828125,
    151.0,
    image=image_image_1
)

image_image_2 = PhotoImage(
    file=relative_to_assets("image_2.png"))
image_2 = canvas.create_image(
    398.0,
    483.0,
    image=image_image_2
)

image_image_3 = PhotoImage(
    file=relative_to_assets("image_3.png"))
image_3 = canvas.create_image(
    910.0,
    321.0,
    image=image_image_3
)

image_image_4 = PhotoImage(
    file=relative_to_assets("image_4.png"))
image_4 = canvas.create_image(
    313.83331298828125,
    151.0,
    image=image_image_4
)

canvas.create_text(
    79.16668701171875,
    67.0,
    anchor="nw",
    text="Original",
    fill="#5E95FF",
    font=("Roboto Bold", 12 * -1)
)

image_image_5 = PhotoImage(
    file=relative_to_assets("image_5.png"))
image_5 = canvas.create_image(
    516.9583740234375,
    151.0,
    image=image_image_5
)

canvas.create_text(
    367.0,
    392.0,
    anchor="nw",
    text="Diameter",
    fill="#5E95FF",
    font=("Roboto Bold", 12 * -1)
)

image_image_6 = PhotoImage(
    file=relative_to_assets("image_6.png"))
image_6 = canvas.create_image(
    338.0,
    33.0,
    image=image_image_6
)

canvas.create_text(
    176.041748046875,
    19.0,
    anchor="nw",
    text="Filename",
    fill="#5E95FF",
    font=("Roboto Bold", 9 * -1)
)

canvas.create_text(
    269.7916259765625,
    67.0,
    anchor="nw",
    text="Segmented",
    fill="#5E95FF",
    font=("Roboto", 12 * -1)
)

canvas.create_text(
    468.75,
    67.0,
    anchor="nw",
    text="Skeletonized",
    fill="#5E95FF",
    font=("Roboto", 12 * -1)
)

button_image_1 = PhotoImage(
    file=relative_to_assets("button_1.png"))
button_1 = Button(
    image=button_image_1,
    borderwidth=0,
    highlightthickness=0,
    command=load_image,
    relief="flat"
)
button_1.place(
    x=18.0,
    y=251.0,
    width=92.0,
    height=37.0
)

button_image_2 = PhotoImage(
    file=relative_to_assets("button_2.png"))
button_2 = Button(
    image=button_image_2,
    borderwidth=0,
    highlightthickness=0,
    command=lambda: print("button_2 clicked"),
    relief="flat"
)
button_2.place(
    x=18.0,
    y=293.0,
    width=91.77166748046875,
    height=37.0
)

button_image_3 = PhotoImage(
    file=relative_to_assets("button_3.png"))
button_3 = Button(
    image=button_image_3,
    borderwidth=0,
    highlightthickness=0,
    command=lambda: print("button_3 clicked"),
    relief="flat"
)
button_3.place(
    x=18.0,
    y=335.0,
    width=90.71929931640625,
    height=37.0
)

button_image_4 = PhotoImage(
    file=relative_to_assets("button_4.png"))
button_4 = Button(
    image=button_image_4,
    borderwidth=0,
    highlightthickness=0,
    command=lambda: print("button_4 clicked"),
    relief="flat"
)
button_4.place(
    x=203.0,
    y=250.0,
    width=100.0,
    height=37.0
)

button_image_5 = PhotoImage(
    file=relative_to_assets("button_5.png"))
button_5 = Button(
    image=button_image_5,
    borderwidth=0,
    highlightthickness=0,
    command=lambda: print("button_5 clicked"),
    relief="flat"
)
button_5.place(
    x=311.0,
    y=250.0,
    width=100.0,
    height=37.0
)

button_image_6 = PhotoImage(
    file=relative_to_assets("button_6.png"))
button_6 = Button(
    image=button_image_6,
    borderwidth=0,
    highlightthickness=0,
    command=lambda: print("button_6 clicked"),
    relief="flat"
)
button_6.place(
    x=501.0,
    y=250.0,
    width=100.0,
    height=37.0
)

button_image_7 = PhotoImage(
    file=relative_to_assets("button_7.png"))
button_7 = Button(
    image=button_image_7,
    borderwidth=0,
    highlightthickness=0,
    command=lambda: print("button_7 clicked"),
    relief="flat"
)
button_7.place(
    x=841.0,
    y=252.0,
    width=139.0,
    height=37.0
)

# image_image_7 = PhotoImage(
#     file=relative_to_assets("image_7.png"))
# image_7 = canvas.create_image(
#     156.0,
#     269.0,
#     image=image_image_7
# )

# image_image_8 = PhotoImage(
#     file=relative_to_assets("image_8.png"))
# image_8 = canvas.create_image(
#     455.0,
#     269.0,
#     image=image_image_8
# )

# image_image_9 = PhotoImage(
#     file=relative_to_assets("image_9.png"))
# image_9 = canvas.create_image(
#     659.0,
#     269.0,
#     image=image_image_9
# )

# image_image_10 = PhotoImage(
#     file=relative_to_assets("image_10.png"))
# image_10 = canvas.create_image(
#     775.0,
#     269.0,
#     image=image_image_10
# )

entry_image_1 = PhotoImage(
    file=relative_to_assets("entry_1.png"))
entry_bg_1 = canvas.create_image(
    775.0,
    321.0,
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
    x=732.0,
    y=315.0,
    width=86.0,
    height=25.0
)

image_image_11 = PhotoImage(
    file=relative_to_assets("image_11.png"))
image_11 = canvas.create_image(
    805.0,
    128.0,
    image=image_image_11
)

image_image_12 = PhotoImage(
    file=relative_to_assets("image_12.png"))
image_12 = canvas.create_image(
    865.0,
    471.0,
    image=image_image_12
)

image_image_13 = PhotoImage(
    file=relative_to_assets("image_13.png"))
image_13 = canvas.create_image(
    154.0,
    483.0,
    image=image_image_13
)

image_image_14 = PhotoImage(
    file=relative_to_assets("image_14.png"))
image_14 = canvas.create_image(
    200.0,
    312.0,
    image=image_image_14
)

image_image_15 = PhotoImage(
    file=relative_to_assets("image_15.png"))
image_15 = canvas.create_image(
    394.0,
    312.0,
    image=image_image_15
)

image_image_16 = PhotoImage(
    file=relative_to_assets("image_16.png"))
image_16 = canvas.create_image(
    609.0,
    312.0,
    image=image_image_16
)

# med filt
med_filt_checkbox = Checkbutton(
    text="Med filt",
    variable=med_filt_on,
    bg="#FFFFFF",
    fg="#5E95FF",
    font=("Roboto", 11 * -1)
)
med_filt_checkbox.place(
    x=110.0,
    y=258.0
)

med_spinbox = Spinbox(
    from_=1,
    to=10,
    width=2,
    textvariable=med_filt_var,
    bg="#FFFFFF",
    fg="#5E95FF",
    font=("Roboto", 12 * -1),
    bd=0.5,                  # removes the border thickness
    highlightthickness=0  # removes the focus highlight border
)
med_spinbox.place(
    x=170.0,
    y=260.0
)

# prebinary
prebinary_checkbox = Checkbutton(
    text="Prebinary",
    variable=prebinary_var,
    bg="#FFFFFF",
    fg="#5E95FF",
    font=("Roboto", 11 * -1)
)
prebinary_checkbox.place(
    x=420.0,
    y=260.0
)

# file type dropdown
file_type_list = ["tif", "png", "jpg", "bmp", "mat"]
file_type = Combobox(
    values=file_type_list,
)
file_type.set("tif")  # Default value
file_type.place(
    x=700.0,
    y=80.0,
    width=107.0,
    height=20.0
)

button_image_8 = PhotoImage(
    file=relative_to_assets("button_8.png"))
button_8 = Button(
    image=button_image_8,
    borderwidth=0,
    highlightthickness=0,
    command=lambda: print("button_8 clicked"),
    relief="flat"
)
button_8.place(
    x=645.0,
    y=42.0,
    width=107.0,
    height=29.0
)

button_image_9 = PhotoImage(
    file=relative_to_assets("button_9.png"))
button_9 = Button(
    image=button_image_9,
    borderwidth=0,
    highlightthickness=0,
    command=lambda: print("button_9 clicked"),
    relief="flat"
)
button_9.place(
    x=774.0,
    y=511.0,
    width=185.0,
    height=29.0
)

button_image_10 = PhotoImage(
    file=relative_to_assets("button_10.png"))
button_10 = Button(
    image=button_image_10,
    borderwidth=0,
    highlightthickness=0,
    command=lambda: print("button_10 clicked"),
    relief="flat"
)
button_10.place(
    x=774.0,
    y=413.0,
    width=63.0,
    height=24.0
)

button_image_11 = PhotoImage(
    file=relative_to_assets("button_11.png"))
button_11 = Button(
    image=button_image_11,
    borderwidth=0,
    highlightthickness=0,
    command=lambda: print("button_11 clicked"),
    relief="flat"
)
button_11.place(
    x=774.0,
    y=447.0,
    width=63.0,
    height=24.0
)

button_image_12 = PhotoImage(
    file=relative_to_assets("button_12.png"))
button_12 = Button(
    image=button_image_12,
    borderwidth=0,
    highlightthickness=0,
    command=lambda: print("button_12 clicked"),
    relief="flat"
)
button_12.place(
    x=774.0,
    y=479.0,
    width=63.0,
    height=24.0
)

button_image_13 = PhotoImage(
    file=relative_to_assets("button_13.png"))
button_13 = Button(
    image=button_image_13,
    borderwidth=0,
    highlightthickness=0,
    command=lambda: print("button_13 clicked"),
    relief="flat"
)
button_13.place(
    x=774.0,
    y=545.0,
    width=185.0,
    height=29.0
)

button_image_14 = PhotoImage(
    file=relative_to_assets("button_14.png"))
button_14 = Button(
    image=button_image_14,
    borderwidth=0,
    highlightthickness=0,
    command=lambda: print("button_14 clicked"),
    relief="flat"
)
button_14.place(
    x=762.0,
    y=97.0,
    width=107.0,
    height=17.0
)

button_image_15 = PhotoImage(
    file=relative_to_assets("button_15.png"))
button_15 = Button(
    image=button_image_15,
    borderwidth=0,
    highlightthickness=0,
    command=lambda: print("button_15 clicked"),
    relief="flat"
)
button_15.place(
    x=645.0,
    y=203.0,
    width=317.6715087890625,
    height=28.0
)

canvas.create_text(
    622.0,
    260.0,
    anchor="nw",
    text="Twig size",
    fill="#5E95FF",
    font=("Roboto", 9 * -1)
)

canvas.create_text(
    729.0,
    256.0,
    anchor="nw",
    text="Display overlay",
    fill="#5E95FF",
    font=("Roboto", 9 * -1)
)

canvas.create_text(
    729.0,
    300.0,
    anchor="nw",
    text="Image size (mm)",
    fill="#5E95FF",
    font=("Roboto", 11 * -1)
)

canvas.create_text(
    652.0,
    105.0,
    anchor="nw",
    text="Save binary",
    fill="#5E95FF",
    font=("Roboto", 9 * -1)
)

canvas.create_text(
    652.0,
    81.0,
    anchor="nw",
    text="File type",
    fill="#5E95FF",
    font=("Roboto", 9 * -1)
)

canvas.create_text(
    789.0,
    391.0,
    anchor="nw",
    text="Right Eye",
    fill="#5E95FF",
    font=("Roboto", 9 * -1)
)

canvas.create_text(
    844.0,
    487.0,
    anchor="nw",
    text="True FAZ segmentation",
    fill="#5E95FF",
    font=("Roboto", 9 * -1)
)

canvas.create_text(
    844.0,
    413.0,
    anchor="nw",
    text="Rapid FAZ stringency factor",
    fill="#5E95FF",
    font=("Roboto", 9 * -1)
)

canvas.create_text(
    844.0,
    453.0,
    anchor="nw",
    text="Lax Strict",
    fill="#5E95FF",
    font=("Roboto", 9 * -1)
)

canvas.create_text(
    652.0,
    122.0,
    anchor="nw",
    text="Batch resize",
    fill="#5E95FF",
    font=("Roboto", 9 * -1)
)

canvas.create_text(
    652.0,
    139.0,
    anchor="nw",
    text="Region analysis",
    fill="#5E95FF",
    font=("Roboto", 9 * -1)
)

canvas.create_text(
    766.0,
    146.0,
    anchor="nw",
    text="Variable img size",
    fill="#5E95FF",
    font=("Roboto", 9 * -1)
)

canvas.create_text(
    652.0,
    156.0,
    anchor="nw",
    text="Segment FAZ",
    fill="#5E95FF",
    font=("Roboto", 9 * -1)
)

canvas.create_text(
    652.0,
    175.0,
    anchor="nw",
    text="Process from folder",
    fill="#5E95FF",
    font=("Roboto", 9 * -1)
)

canvas.create_text(
    134.0,
    304.0,
    anchor="nw",
    text="Frangi",
    fill="#5E95FF",
    font=("Roboto", 9 * -1)
)

canvas.create_text(
    302.0,
    304.0,
    anchor="nw",
    text="Segmentation Method",
    fill="#5E95FF",
    font=("Roboto", 9 * -1)
)

canvas.create_text(
    523.0,
    304.0,
    anchor="nw",
    text="AT kernel size",
    fill="#5E95FF",
    font=("Roboto", 9 * -1)
)

canvas.create_text(
    716.0,
    21.0,
    anchor="nw",
    text="Batch Processing",
    fill="#5E95FF",
    font=("Roboto", 12 * -1)
)

canvas.create_text(
    775.0,
    365.0,
    anchor="nw",
    text="Retinal Analysis",
    fill="#5E95FF",
    font=("Roboto Bold", 12 * -1)
)

canvas.create_text(
    84.0,
    390.0,
    anchor="nw",
    text="Metrics",
    fill="#5E95FF",
    font=("Roboto Bold", 12 * -1)
)

canvas.create_text(
    38.0,
    416.0,
    anchor="nw",
    text="Vessel area density",
    fill="#5E95FF",
    font=("Roboto", 10 * -1)
)

canvas.create_text(
    38.0,
    439.0,
    anchor="nw",
    text="Vessel length density",
    fill="#5E95FF",
    font=("Roboto", 10 * -1)
)

canvas.create_text(
    38.0,
    462.0,
    anchor="nw",
    text="Total vessel length",
    fill="#5E95FF",
    font=("Roboto", 10 * -1)
)

canvas.create_text(
    38.0,
    485.0,
    anchor="nw",
    text="Mean diameter",
    fill="#5E95FF",
    font=("Roboto", 10 * -1)
)

canvas.create_text(
    38.0,
    508.0,
    anchor="nw",
    text="Median diameter",
    fill="#5E95FF",
    font=("Roboto", 10 * -1)
)

canvas.create_text(
    38.0,
    531.0,
    anchor="nw",
    text="Branchpoint density",
    fill="#5E95FF",
    font=("Roboto", 10 * -1)
)

canvas.create_text(
    38.0,
    554.0,
    anchor="nw",
    text="Fractal dimension",
    fill="#5E95FF",
    font=("Roboto", 10 * -1)
)

entry_image_2 = PhotoImage(
    file=relative_to_assets("entry_2.png"))
entry_bg_2 = canvas.create_image(
    865.0,
    56.0,
    image=entry_image_2
)
entry_2 = Entry(
    bd=0,
    bg="#FFFFFF",
    fg="#000716",
    highlightthickness=0
)
entry_2.place(
    x=772.0,
    y=41.0,
    width=186.0,
    height=28.0
)

button_image_16 = PhotoImage(
    file=relative_to_assets("button_16.png"))
button_16 = Button(
    image=button_image_16,
    borderwidth=0,
    highlightthickness=0,
    command=lambda: print("button_16 clicked"),
    relief="flat"
)
button_16.place(
    x=768.0,
    y=50.0,
    width=13.090909957885742,
    height=12.0
)

entry_image_3 = PhotoImage(
    file=relative_to_assets("entry_3.png"))
entry_bg_3 = canvas.create_image(
    815.5,
    129.0,
    image=entry_image_3
)
entry_3 = Entry(
    bd=0,
    bg="#FFFFFF",
    fg="#000716",
    highlightthickness=0
)
entry_3.place(
    x=772.0,
    y=119.0,
    width=87.0,
    height=18.0
)
window.resizable(False, False)
window.mainloop()
