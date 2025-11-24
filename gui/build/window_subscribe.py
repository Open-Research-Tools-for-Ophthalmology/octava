import tkinter as tk
from tkinter import Canvas, Toplevel, messagebox
from theme import *
import customtkinter as ctk
from dotenv import load_dotenv
load_dotenv()

import requests
import json

GOOGLE_WEBAPP_URL = "https://script.google.com/macros/s/AKfycbxwGsLwvIOKctimULdzLS6C3bLrS2WSEy3z4UMGcboo47jq0hx9LLiWFSa4FZ24/exec"

def send_email_to_google_sheet(email: str):
    try:
        r = requests.post(GOOGLE_WEBAPP_URL, json={"email": email})
        print("Status Code:", r.status_code)
        print("Response from Google Web App:", r.text)
        return r.status_code == 200
    except Exception as e:
        print("Error:", e)
        return False


def close(window):
  window.destroy()
  window.update()


def open_subscribe_window(canvas: Canvas):
  subwindow = Toplevel()
  subwindow.title("Subscribe for Updates")
  subwindow.geometry("500x250")
  subwindow.configure(bg = bg_colour)

  subcanvas = Canvas(
      subwindow,
      bg = bg_colour,
      width = 500,
      height = 250,
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
      text="We'll notify you when new updates are available. You won't need to subscribe repetitively. Please enter your contact email address:",
      fill="#10203F",
      font=("Roboto", 16),
      width=400,
      justify="left"
  )


  # input box
  address_box = ctk.CTkTextbox(subwindow,
                                width=400,
                                height=40,
                                font=("Roboto", 14),
                                fg_color=button_blue_colour,
                                text_color=text_colour,
                                border_width=1,
                                border_color=text_colour,
                                corner_radius=10)
  address_box.place(x=50, y=100)

  def on_submit():
        email = address_box.get("1.0", tk.END).strip()

        if not email:
            messagebox.showwarning("Empty email address", "Please enter an email address.")
            return

        ok = send_email_to_google_sheet(email)
        if ok:
            messagebox.showinfo("Subscribed!", "Thank you for subscribing.")
            close(subwindow)
        else:
            messagebox.showerror("Error", "Subscription failed.")

  #close
  button_close = ctk.CTkButton(subwindow, text="Cancel",
                          command=lambda: close(subwindow),
                          width=100,height=40,
                          font=("Roboto", 14 * -1),
                          text_color=text_colour,
                          fg_color=bg_colour,
                          corner_radius=8,border_width=1,
                          hover_color=button_blue_hover,
      border_color=button_border_colour)
  button_close.place(x=240, y=160)


  #submit
  button_submit = ctk.CTkButton(
        subwindow, text="Submit",
        command=lambda: on_submit(),
        width=100, height=40,
        font=("Roboto", 14 * -1),
        text_color=text_colour,
        fg_color=button_yellow_colour,
        corner_radius=8, border_width=1,
        hover_color=button_yellow_hover,
        border_color=button_border_colour
  )
  button_submit.place(x=350, y=160)


  subwindow.resizable(False, False)
  subwindow.mainloop()
