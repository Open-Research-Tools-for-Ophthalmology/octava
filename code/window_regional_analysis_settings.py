from pathlib import Path
from resource_path import ASSETS_PATH
from tkinter import Tk, Canvas, Entry, Text, Button, PhotoImage, Toplevel, Checkbutton, IntVar, StringVar, Spinbox
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
  canvas.wide_field_ring_bool = IntVar(value=0)
  canvas.wide_field_ring_width_var = IntVar(value=1)
  canvas.onh_quadrant_analysis_bool = IntVar(value=0)
  canvas.onh_octant_analysis_bool = IntVar(value=0)
  canvas.apply_regional_analysis_bool = IntVar(value=0)
  canvas.RAlabels = []


def close(subwindow):
  subwindow.destroy()
  subwindow.update()

def subwindow2(canvas):
  is_onh_mode = (
      hasattr(canvas, "img_type_var")
      and canvas.img_type_var.get() == "ONH"
  )
  is_retina_mode = (
      hasattr(canvas, "img_type_var")
      and canvas.img_type_var.get() == "Retina"
  )
  is_skin_mode = (
      hasattr(canvas, "img_type_var")
      and canvas.img_type_var.get() == "Skin"
  )
  
  subwindow = Toplevel()
  subwindow.title("Regional Analysis Settings")
  subwindow.iconphoto(False, PhotoImage(file=str(ASSETS_PATH / "favicon.png")))
  subwindow.configure(bg = "#FBE3D6")
  view_height = 350 if is_retina_mode else 300 if is_onh_mode else 250
  subwindow.geometry(f"300x{view_height}")
  subcanvas2 = Canvas(
      subwindow,
      bg = subwindow_bg_colour,
      height = view_height,
      width = 300,
      bd = 0,
      highlightthickness = 0,
      relief = "ridge"
  )
  subcanvas2.place(x = 0, y = 0)

  if (not is_skin_mode):
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

  # Display masks for different image types
  if is_skin_mode: # [Square, Wide-field]
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
        y=60.0
    )

    # Wide-field retina settings with customized spinbox for ring width
    wide_field_checkbox = Checkbutton(
      subwindow,
      text="Wide Field rings",
      variable=canvas.wide_field_ring_bool,
      bg=subwindow_bg_colour,
      fg=text_colour,
      font=("Roboto", 14 * -1)
    )
    wide_field_checkbox.place(
      x=40.0,
      y=90.0
    )
    wide_field_ring_width_spinbox = Spinbox(
      subwindow,
      from_=1,
      to=10.00,
      increment=1,
      width=4,
      textvariable=canvas.wide_field_ring_width_var,
      bg=bg_colour,
      fg=text_colour,
      font=("Roboto", 14 * -1),
      bd=0.5,                  # removes the border thickness
      highlightthickness=0,  # removes the focus highlight border
    )
    wide_field_ring_width_spinbox.place(
      x=180.0,
      y=92.0
    )
  elif is_onh_mode:  # [ONH quadrant, ONH octant]
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
  else: # [square, etdrs, extended etdrs, foveal rings, wide-field]
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

      # Wide-field retina settings with customized spinbox for ring width
      wide_field_checkbox = Checkbutton(
        subwindow,
        text="Wide Field rings",
        variable=canvas.wide_field_ring_bool,
        bg=subwindow_bg_colour,
        fg=text_colour,
        font=("Roboto", 14 * -1)
      )
      wide_field_checkbox.place(
        x=40.0,
        y=220.0
      )
      wide_field_ring_width_spinbox = Spinbox(
        subwindow,
        from_=1,
        to=10.00,
        increment=1,
        width=4,
        textvariable=canvas.wide_field_ring_width_var,
        bg=bg_colour,
        fg=text_colour,
        font=("Roboto", 14 * -1),
        bd=0.5,                  # removes the border thickness
        highlightthickness=0,  # removes the focus highlight border
      )
      wide_field_ring_width_spinbox.place(
        x=180.0,
        y=222.0
      )

  # close
  button_close = ctk.CTkButton(subwindow, text="Close",
    command=lambda: close(subwindow),
    width=130,height=45,
    font=("Roboto", 14 * -1),
    text_color=text_colour,
    fg_color=button_blue_colour,
    corner_radius=8,border_width=1,
    hover_color=button_blue_hover,
    border_color=button_border_colour
  )
  button_close.place(x=80, y=view_height - 80)

  subwindow.resizable(False, False)
  return subwindow
