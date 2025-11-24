import tkinter as tk
from tkinter import Canvas, Toplevel, messagebox
from theme import *
import customtkinter as ctk
import requests
from dotenv import load_dotenv
load_dotenv()

GOOGLE_WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzzJbH4EfyuwmLaxNJkZpT9ghsFlHTpPKH35uoS2E9Y6EZdPiTjwb-y0nI76z61OJw/exec"

def send_email_to_google_sheet(name: str, email: str):
    try:
        r = requests.post(GOOGLE_WEBAPP_URL, json={"name": name, "email": email})
        # print("Response from Google Web App:", r.text)
        return r.text == '{"status":"OK"}'
    except Exception as e:
        print("Error:", e)
        return False


def close(window):
  window.destroy()
  window.update()


def open_subscribe_window(canvas: Canvas):
  subwindow = Toplevel()
  subwindow.title("Subscribe for Updates")
  subwindow.geometry("500x350")
  subwindow.configure(bg = bg_colour)

  subcanvas = Canvas(
      subwindow,
      bg = bg_colour,
      width = 500,
      height = 350,
      bd = 0,
      highlightthickness = 0,
      relief = "ridge"
  )

  subcanvas.place(x = 0, y = 0)

  #preferred name
  subcanvas.create_text(
      50.0,
      30.0,
      anchor="nw",
      text="We'll notify you when new updates are available. You only need to subscribe once. Please enter your contact email address:",
      fill="#10203F",
      font=("Roboto", 16),
      width=400,
      justify="left"
  )

  # input box
  name_box = ctk.CTkTextbox(subwindow,
                                width=400,
                                height=40,
                                font=("Roboto", 14),
                                fg_color=button_blue_colour,
                                text_color=text_colour,
                                border_width=1,
                                border_color=text_colour,
                                corner_radius=10)
  name_box.place(x=50, y=100)


  #contact email address
  subcanvas.create_text(
      50.0,
      170.0,
      anchor="nw",
      text="Please enter your contact email address:",
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
  address_box.place(x=50, y=200)


  def on_submit():
        name = name_box.get("1.0", tk.END).strip()
        email = address_box.get("1.0", tk.END).strip()

        if not name:
            messagebox.showwarning("Empty name", "Please enter a name.")
            return

        if not email:
            messagebox.showwarning("Empty email address", "Please enter an email address.")
            return

        ok = send_email_to_google_sheet(name,email)
        if ok:
            messagebox.showinfo("Subscribed!", f"Thank you for subscribing via {email}.")
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
  button_close.place(x=240, y=270)


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
  button_submit.place(x=350, y=270)


  subwindow.resizable(False, False)
  subwindow.mainloop()
