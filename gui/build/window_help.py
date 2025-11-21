from pathlib import Path

import tkinter as tk
# Explicit imports to satisfy Flake8
from tkinter import Tk, Canvas, Entry, Text, Button, PhotoImage, Toplevel, Checkbutton, IntVar, Spinbox
from theme import *
import customtkinter as ctk


def close(window):
  window.destroy()
  window.update()


def open_help_window(canvas):
  subwindow = Toplevel()
  subwindow.title("Help")
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
      100.0,
      anchor="nw",
      text="Instructions",
      fill="#10203F",
      font=("Roboto", 16, "bold")
  )

  subcanvas.create_text(
      100.0,
      140.0,
      anchor="nw",
      text=
        "1. Load an image using the 'Load Image' button. Supported formats include PNG, JPG, BMP, and TIFF.\n"
        "2. Select a folder to save results using the 'Save Folder' button.\n"
        "3. Adjust any optional settings if needed by clicking the 'Advanced Settings', 'Regional Analysis Settings', and 'Batch Processing Settings' buttons.\n"
        "4. Click 'Start Processing' to start the analysis.\n"
        "5. Once processing is complete, check the selected save folder for output files.",
      fill="#10203F",
      font=("Roboto", 16),
      width=600,
      justify="left"
  )

  #close
  button_close = ctk.CTkButton(subwindow, text="Close",
                          command=lambda: close(subwindow),
                          width=400,height=45,
                          font=("Roboto", 14 * -1),
                          text_color=text_colour,
                          fg_color=button_blue_colour,
                          corner_radius=8,border_width=1,
                          hover_color=button_blue_hover,
      border_color=button_border_colour  )
  button_close.place(x=200, y=450)

  subwindow.resizable(False, False)
  subwindow.mainloop()
