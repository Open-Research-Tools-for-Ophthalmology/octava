from pathlib import Path
from tkinter import Tk, Canvas, Entry, Text, Button, PhotoImage, Toplevel, Checkbutton, IntVar, StringVar
from theme import *
from tkinter.ttk import Combobox
import customtkinter as ctk


def close(subwindow):
  subwindow.destroy()
  subwindow.update()

def subwindow2():
  REGIONAL_ANALYSIS_ASSETS_PATH = Path("/Users/milameteor/Library/CloudStorage/OneDrive-UWA/M4 Backup/dev/octava/gui2/subwindow2/build/assets/frame0")
   

  def relative_to_assets(path: str) -> Path:
      return REGIONAL_ANALYSIS_ASSETS_PATH / path


  subwindow = Toplevel()
  subwindow.title("Regional Analysis Settings")
  subwindow.geometry("349x380")
  subwindow.configure(bg = "#FBE3D6")

  eye_var = StringVar()
  load_faz_var = IntVar(value=0)
  square_grid_var = IntVar(value=0)
  etdrs_grid_var = IntVar(value=0)
  extended_etdrs_var = IntVar(value=0)
  foveal_rings_var = IntVar(value=0)
  optic_nerve_head_var = IntVar(value=0)


  canvas = Canvas(
      subwindow,
      bg = subwindow_bg_colour,
      height = 380,
      width = 349,
      bd = 0,
      highlightthickness = 0,
      relief = "ridge"
  )

  canvas.place(x = 0, y = 0)

  # eye type dropdown
  eye_list = ["Left Eye", "Right Eye"]
  eye_combobox = Combobox(
      subwindow,
      textvariable=eye_var,
      values=eye_list,
      state="readonly"
  )
  eye_combobox.place(
      x=40.0,
      y=30.0,
      width=140.0,
      height=30.0
  )

  # def show_selection(event=None):
  #     print("Selected:", eye_var.get())

  # eye_combobox.bind("<<ComboboxSelected>>", show_selection)


  # load faz checkbox
  load_faz_checkbox = Checkbutton(
      subwindow,
      text="Load FAZ masks",
      variable=load_faz_var,
      bg=subwindow_bg_colour,
      fg=text_colour,
      font=("Roboto", 14 * -1)
  )
  load_faz_checkbox.place(
      x=40.0,
      y=70.0
  )

  # square grid checkbox
  square_grid_checkbox = Checkbutton(
      subwindow,
      text="Square grid",
      variable=square_grid_var,
      bg=subwindow_bg_colour,
      fg=text_colour,
      font=("Roboto", 14 * -1)
  )
  square_grid_checkbox.place(
      x=40.0,
      y=100.0
  )


  # etdrs grid checkbox
  etdrs_grid_checkbox = Checkbutton(
      subwindow,
      text="ETDRS grid",
      variable=etdrs_grid_var,
      bg=subwindow_bg_colour,
      fg=text_colour,
      font=("Roboto", 14 * -1)
  )
  etdrs_grid_checkbox.place(
      x=40.0,
      y=130.0
  )

  # extended etdrs grid checkbox
  extended_etdrs_checkbox = Checkbutton(
      subwindow,
      text="Extended ETDRS grid",
      variable=extended_etdrs_var,
      bg=subwindow_bg_colour,
      fg=text_colour,
      font=("Roboto", 14 * -1)
  )
  extended_etdrs_checkbox.place(
      x=40.0,
      y=160.0
  )

  # foveal rings checkbox
  foveal_rings_checkbox = Checkbutton(
      subwindow,
      text="Foveal rings",
      variable=foveal_rings_var,
      bg=subwindow_bg_colour,
      fg=text_colour,
      font=("Roboto", 14 * -1)
  )
  foveal_rings_checkbox.place(
      x=40.0,
      y=190.0
  )

  # optic nerve head checkbox
  optic_nerve_head_checkbox = Checkbutton(
      subwindow,
      text="Optic nerve head",
      variable=optic_nerve_head_var,
      bg=subwindow_bg_colour,
      fg=text_colour,
      font=("Roboto", 14 * -1)
  )
  optic_nerve_head_checkbox.place(
      x=40.0,
      y=220.0
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
  button_close.place(x=100, y=300)


  subwindow.resizable(False, False)
  subwindow.mainloop()
