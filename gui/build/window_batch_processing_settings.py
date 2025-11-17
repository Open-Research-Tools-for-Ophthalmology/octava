from pathlib import Path
from tkinter import Tk, Canvas, Entry, Text, Button, PhotoImage, Toplevel, Checkbutton, IntVar, StringVar, Spinbox
from tkinter.ttk import Combobox
import customtkinter as ctk
from theme import *
from modules.round_rectangle import *
from modules.select_folder import *


def close(subwindow):
  subwindow.destroy()
  subwindow.update()

def subwindow3():
  ASSETS_PATH = Path(r"/Users/milameteor/Library/CloudStorage/OneDrive-UWA/M4 Backup/dev/octava/gui/subwindow3/build/assets/frame0")


  def relative_to_assets(path: str) -> Path:
      return ASSETS_PATH / path


  subwindow = Toplevel()
  subwindow.title("Batch Processing Settings")
  subwindow.geometry("350x450")
  subwindow.configure(bg = "#FBE3D6")

  file_type_var = StringVar(value="tif")
  batch_resize_var = IntVar(value=0) # true or false
  batch_resize_value = IntVar()
  variable_image_size_var = IntVar(value=0)
  apply_advanced_settings_var = IntVar(value=0)
  apply_regional_analysis_settings_var = IntVar(value=0)

  subcanvas3 = Canvas(
      subwindow,
      bg = "#FBE3D6",
      height = 353,
      width = 349,
      bd = 0,
      highlightthickness = 0,
      relief = "ridge"
  )

  subcanvas3.place(x = 0, y = 0)

  button1 = ctk.CTkButton(subwindow, text="Select Raw Data Folder",
                          command=lambda: select_folder(subcanvas3, 60, 100),
                          width=260,height=40,
                          font=("Roboto", 14 * -1),
                          text_color=text_colour,
                          fg_color=button_yellow_colour,
                          corner_radius=8,border_width=1,
                          hover_color=button_yellow_hover,
      border_color=button_border_colour  )
  button1.place(x=45, y=30)
  round_rectangle(subcanvas3, 45, 80, 260, 40, radius=8, fill=bg_colour, outline=bg_colour)
  
  subcanvas3.create_text(
      45.0,
      135.0,
      anchor="nw",
      text="File type",
      fill="#0F1F3F",
      font=("Roboto SemiBold", 14 * -1)
  )

  # file type dropdown
  file_type_list = ["tif", "png", "jpg", "bmp", "mat"]
  file_type = Combobox(
      subwindow,
      textvariable=file_type_var,
      values=file_type_list,
      state="readonly"
  )
  file_type.place(
      x=110.0,
      y=130.0,
      width=100.0,
      height=30.0
  )  

  # batch resize checkbox
  batch_resize_checkbox = Checkbutton(
      subwindow,
      text="Batch resize",
      variable=batch_resize_var,
      bg=subwindow_bg_colour,
      fg=text_colour,
      font=("Roboto", 14 * -1)
  )
  batch_resize_checkbox.place(
      x=40.0,
      y=185.0
  )
  twig_size_spinbox = Spinbox(
      subwindow,
      from_=1,
      to=10,
      width=3,
      textvariable=batch_resize_value,
      bg=subwindow_bg_colour,
      fg=text_colour,
      font=("Roboto", 14 * -1),
      bd=0.5,                # removes the border thickness
      highlightthickness=0,  # removes the focus highlight border
  )
  twig_size_spinbox.place(
      x=160.0,
      y=187.0
  )

  # variable image size checkbox
  variable_image_size_checkbox = Checkbutton(
      subwindow,
      text="Variable image size",
      variable=variable_image_size_var,
      bg=subwindow_bg_colour,
      fg=text_colour,
      font=("Roboto", 14 * -1)
  )
  variable_image_size_checkbox.place(
      x=40.0,
      y=223.0
  )

  subcanvas3.create_text(
      66.0,
      250.0,
      anchor="nw",
      text="No - Process from folder\nYes - Process from list",
      fill="#0F1F3F",
      font=("Roboto SemiBold", 14 * -1)
  )

  # apply advanced settings checkbox
  apply_advanced_settings_checkbox = Checkbutton(
      subwindow,
      text="Apply advanced settings",
      variable=apply_advanced_settings_var,
      bg=subwindow_bg_colour,
      fg=text_colour,
      font=("Roboto", 14 * -1)
  )
  apply_advanced_settings_checkbox.place(
      x=40.0,
      y=300.0
  )

  # apply regional analysis settings checkbox
  apply_regional_analysis_settings_checkbox = Checkbutton(
      subwindow,
      text="Apply regional analysis settings",
      variable=apply_regional_analysis_settings_var,
      bg=subwindow_bg_colour,
      fg=text_colour,
      font=("Roboto", 14 * -1)
  )
  apply_regional_analysis_settings_checkbox.place(
      x=40.0,
      y=330.0
  )


  #close
  button_close = ctk.CTkButton(subwindow, text="Close",
                          command=lambda: close(subwindow),
                          width=130,height=45,
                          font=("Roboto", 14 * -1),
                          text_color=text_colour,
                          fg_color=button_blue_colour,
                          corner_radius=8,border_width=1,
                          hover_color=button_blue_hover,
      border_color=button_border_colour  )
  button_close.place(x=110, y=380)

  subwindow.resizable(False, False)
  subwindow.mainloop()
