from tkinter import Canvas, Toplevel
from theme import *
import customtkinter as ctk
from dotenv import load_dotenv
load_dotenv()


def close(window):
  window.destroy()
  window.update()


def open_subscribe_window(canvas: Canvas):
  subwindow = Toplevel()
  subwindow.title("Feedback")
  subwindow.geometry("700x520")
  subwindow.configure(bg = bg_colour)

  subcanvas = Canvas(
      subwindow,
      bg = bg_colour,
      width = 700,
      height = 520,
      bd = 0,
      highlightthickness = 0,
      relief = "ridge"
  )

  subcanvas.place(x = 0, y = 0)

  #contact email address
  subcanvas.create_text(
      50.0,
      30.0,
      anchor="nw",
      text="Please enter your contact email address:",
      fill="#10203F",
      font=("Roboto", 16),
      width=600,
      justify="left"
  )

  # input box
  address_box = ctk.CTkTextbox(subwindow,
                                width=600,
                                height=40,
                                font=("Roboto", 14),
                                fg_color=button_blue_colour,
                                text_color=text_colour,
                                border_width=1,
                                border_color=text_colour,
                                corner_radius=10)
  address_box.place(x=50, y=60)


  #close
  button_close = ctk.CTkButton(subwindow, text="Cancel",
                          command=lambda: close(subwindow),
                          width=150,height=45,
                          font=("Roboto", 14 * -1),
                          text_color=text_colour,
                          fg_color=bg_colour,
                          corner_radius=8,border_width=1,
                          hover_color=button_blue_hover,
      border_color=button_border_colour)
  button_close.place(x=330, y=430)


  subwindow.resizable(False, False)
  subwindow.mainloop()
