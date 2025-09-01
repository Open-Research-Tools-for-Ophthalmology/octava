from pathlib import Path
from tkinter import Tk, Canvas, Entry, Text, Button, PhotoImage, Toplevel, Checkbutton, IntVar, StringVar
from tkinter.ttk import Combobox
import customtkinter as ctk
from theme import *

def close(subwindow):
  subwindow.destroy()
  subwindow.update()

def subwindow3():
  ASSETS_PATH = Path(r"/Users/milameteor/Library/CloudStorage/OneDrive-UWA/M4 Backup/dev/octava/gui2/subwindow3/build/assets/frame0")


  def relative_to_assets(path: str) -> Path:
      return ASSETS_PATH / path


  subwindow = Toplevel()
  subwindow.title("Batch Processing Settings")
  subwindow.geometry("349x353")
  subwindow.configure(bg = "#FBE3D6")

  file_type_var = StringVar(value="tif")

  canvas = Canvas(
      subwindow,
      bg = "#FBE3D6",
      height = 353,
      width = 349,
      bd = 0,
      highlightthickness = 0,
      relief = "ridge"
  )

  canvas.place(x = 0, y = 0)

  canvas.create_text(
      40.0,
      100.0,
      anchor="nw",
      text="File type",
      fill="#0F1F3F",
      font=("Roboto SemiBold", 14 * -1)
  )

  button1 = ctk.CTkButton(subwindow, text="Select Raw Data Folder",
                          command=lambda: print("button clicked"),
                          width=260,height=40,
                          font=("Roboto", 14 * -1),
                          text_color=text_colour,
                          fg_color=button_yellow_colour,
                          corner_radius=8,border_width=1,
                          hover_color=button_yellow_hover,
      border_color=button_border_colour  )
  button1.place(x=40, y=30)
  
  # file type dropdown
  file_type_list = ["tif", "png", "jpg", "bmp", "mat"]
  file_type = Combobox(
      subwindow,
      textvariable=file_type_var,
      values=file_type_list,
      state="readonly"
  )
  file_type.place(
      x=105.0,
      y=95.0,
      width=100.0,
      height=30.0
  )  

  canvas.create_text(
      48.0,
      154.0,
      anchor="nw",
      text="Batch resize",
      fill="#0F1F3F",
      font=("Roboto SemiBold", 14 * -1)
  )

  canvas.create_text(
      48.0,
      188.0,
      anchor="nw",
      text="Variable image size",
      fill="#0F1F3F",
      font=("Roboto SemiBold", 14 * -1)
  )

  canvas.create_text(
      70.0,
      220.0,
      anchor="nw",
      text="No - Process from folder\nYes - Process from list",
      fill="#0F1F3F",
      font=("Roboto SemiBold", 14 * -1)
  )

  button_image_1 = PhotoImage(
      file=relative_to_assets("button_1.png"))
  button_1 = Button(
      subwindow,
      image=button_image_1,
      borderwidth=0,
      highlightthickness=0,
      command=lambda: close(subwindow),
      relief="flat"
  )
  button_1.place(
      x=114.0,
      y=286.0,
      width=121.0,
      height=37.0
  )



  entry_image_1 = PhotoImage(
      file=relative_to_assets("entry_1.png"))
  entry_bg_1 = canvas.create_image(
      254.0,
      162.0,
      image=entry_image_1
  )
  entry_1 = Entry(
      subwindow,
      bd=0,
      bg="#FEEFBB",
      fg="#000716",
      highlightthickness=0,
      justify='center'
  )
  entry_1.place(
      x=211.0,
      y=149.0,
      width=86.0,
      height=26.0
  )
  subwindow.resizable(False, False)
  subwindow.mainloop()
