from pathlib import Path
import webbrowser

import tkinter as tk
# Explicit imports to satisfy Flake8
from tkinter import Tk, Canvas, Entry, Text, Button, PhotoImage, Toplevel, Checkbutton, IntVar, Spinbox
from resource_path import ASSETS_PATH
from theme import *
import customtkinter as ctk


def close(window):
  window.destroy()
  window.update()


def open_help_window(canvas):
  subwindow = Toplevel()
  subwindow.title("Help")
  subwindow.iconphoto(False, tk.PhotoImage(file=str(ASSETS_PATH / "favicon.png")))
  subwindow.geometry("800x600")
  subwindow.configure(bg = bg_colour)

  subcanvas = Canvas(
      subwindow,
      bg = bg_colour,
      width = 800,
      height = 600,
      bd = 0,
      highlightthickness = 0,
      relief = "ridge"
  )

  subcanvas.place(x = 0, y = 0)

  subcanvas.create_text(
      100.0,
      50.0,
      anchor="nw",
      text="Instructions",
      fill="#10203F",
      font=("Roboto", 16, "bold")
  )

  subcanvas.create_text(
      100.0,
      100.0,
      anchor="nw",
      text=
        "1. Select the region of interest from 'Retina', 'ONH' or 'Skin'. Change 'Prebinary' or 'Image size (mm)' settings if needed.\n"
        "2. Load an image using the 'Load Image' button. Supported formats include PNG, JPG/JPEG, BMP, and TIF/TIFF.\n"
        "3. Select a folder to save results using the 'Save Folder' button.\n"
        "4. Adjust any optional settings if needed by clicking the 'Advanced Settings', 'Regional Analysis Settings', and 'Batch Processing Settings' buttons.\n"
        "5. Click 'Start Processing' to start the analysis.\n"
        "6. Process optional FAZ segmentation with provided 'Auto FAZ' function or label manually using 'Point FAZ'. Click 'Measure FAZ' to save images and metrics.\n"
        "7. Once processing is complete, check the selected save folder for output files.",
      fill="#10203F",
      font=("Roboto", 16),
      width=600,
      justify="left"
  )

  # lead to github issues page to collect feedback
  button_issues = ctk.CTkButton(subwindow, text="Github Issues",
                          command=lambda: webbrowser.open("https://github.com/milanaveed/octava/issues"),
                          width=400,height=45,
                          font=("Roboto", 14 * -1),
                          text_color=text_colour,
                          fg_color=button_blue_colour,
                          corner_radius=8,border_width=1,
                          hover_color=button_blue_hover,
      border_color=button_border_colour  )
  button_issues.place(x=200, y=500)

  subwindow.resizable(False, False)
  return subwindow
