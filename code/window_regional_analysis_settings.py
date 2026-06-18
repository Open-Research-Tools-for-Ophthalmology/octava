from pathlib import Path
from tkinter import Tk, Canvas, Entry, Text, Button, PhotoImage, Toplevel, Checkbutton, IntVar, StringVar
from theme import *
from tkinter.ttk import Combobox
import customtkinter as ctk


def init_regional_analysis_settings(canvas: Canvas):
  """Initialize canvas variables used by the regional analysis UI and pipeline."""
  canvas.eye_var = StringVar(value="Right Eye")
  canvas.load_faz_bool = IntVar(value=0)
  canvas.square_grid_bool = IntVar(value=0)
  canvas.etdrs_grid_bool = IntVar(value=0)
  canvas.extended_etdrs_bool = IntVar(value=0)
  canvas.foveal_ring_bool = IntVar(value=0)
  canvas.optic_nerve_head_bool = IntVar(value=0)
  canvas.onh_quadrant_analysis_bool = IntVar(value=0)
  canvas.onh_octant_analysis_bool = IntVar(value=0)
  canvas.apply_regional_analysis_bool = IntVar(value=0)
  canvas.RAlabels = []


def close(subwindow):
  subwindow.destroy()
  subwindow.update()

def subwindow2(canvas):
  subwindow = Toplevel()
  subwindow.title("Regional Analysis Settings")
  subwindow.geometry("300x350")
  subwindow.configure(bg = "#FBE3D6")

  subcanvas2 = Canvas(
      subwindow,
      bg = subwindow_bg_colour,
      height = 350,
      width = 300,
      bd = 0,
      highlightthickness = 0,
      relief = "ridge"
  )
  subcanvas2.place(x = 0, y = 0)

  # eye type dropdown
  subcanvas2.create_text(
      45.0,
      50.0,
      anchor="nw",
      text="Eye",
      fill=text_colour,
      font=("Roboto", 14 * -1)
  )
  eye_list = ["Left Eye", "Right Eye"]
  eye_combobox = Combobox(
      subwindow,
      textvariable=canvas.eye_var,
      values=eye_list,
      state="readonly"
  )
  eye_combobox.place(
      x=80.0,
      y=45.0,
      width=150.0,
      height=30.0
  )

  is_onh_mode = (
      hasattr(canvas, "img_type_var")
      and canvas.img_type_var.get() == "ONH"
  )

  if is_onh_mode:
      onh_quadrant_checkbox = Checkbutton(
          subwindow,
          text="ONH quadrant analysis",
          variable=canvas.onh_quadrant_analysis_bool,
          bg=subwindow_bg_colour,
          fg=text_colour,
          font=("Roboto", 14 * -1)
      )
      onh_quadrant_checkbox.place(
          x=40.0,
          y=110.0
      )

      onh_octant_checkbox = Checkbutton(
          subwindow,
          text="ONH octant analysis",
          variable=canvas.onh_octant_analysis_bool,
          bg=subwindow_bg_colour,
          fg=text_colour,
          font=("Roboto", 14 * -1)
      )
      onh_octant_checkbox.place(
          x=40.0,
          y=140.0
      )
  else:
      # square grid checkbox
      square_grid_checkbox = Checkbutton(
          subwindow,
          text="Square grid",
          variable=canvas.square_grid_bool,
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
          variable=canvas.etdrs_grid_bool,
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
          variable=canvas.extended_etdrs_bool,
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
          variable=canvas.foveal_ring_bool,
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
          variable=canvas.optic_nerve_head_bool,
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
  button_close.place(x=80, y=270)


  subwindow.resizable(False, False)
  return subwindow
