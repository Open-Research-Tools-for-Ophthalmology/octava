import tkinter as tk
from tkinter import Canvas, Toplevel, messagebox
from urllib import response
from theme import *
import customtkinter as ctk
from dotenv import load_dotenv
import os
import requests
import asyncio

load_dotenv()

def close(window):
  window.destroy()
  window.update()

async def send_email(name: str, address: str, feedback_text: str):
  """
  Send the feedback text to orto email using cloud function endpoint
  """    

  return requests.post('https://australia-southeast1-orto-blog.cloudfunctions.net/feedback',
    json={
      "name": name,
      "email": address,
      "message": feedback_text,
      "collectionId": "octava_feedback",
      "tag": "OCTAVA"
    }
  )

def open_feedback_window(canvas: Canvas):
  subwindow = Toplevel()
  subwindow.title("Feedback")
  subwindow.geometry("700x620")
  subwindow.configure(bg = bg_colour)

  subcanvas = Canvas(
      subwindow,
      bg = bg_colour,
      width = 700,
      height = 620,
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
      text="Please enter your preferred name:",
      fill="#10203F",
      font=("Roboto", 16),
      width=600,
      justify="left"
  )

  # input box
  name_box = ctk.CTkTextbox(subwindow,
                                width=300,
                                height=40,
                                font=("Roboto", 14),
                                fg_color=button_blue_colour,
                                text_color=text_colour,
                                border_width=1,
                                border_color=text_colour,
                                corner_radius=10)
  name_box.place(x=50, y=60)


  #contact email address
  subcanvas.create_text(
      50.0,
      130.0,
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
  address_box.place(x=50, y=160)


  #Feedback text
  subcanvas.create_text(
      50.0,
      230.0,
      anchor="nw",
      text="Please write down your feedback:",
      fill="#10203F",
      font=("Roboto", 16),
      width=600,
      justify="left"
  )

  # input box
  feedback_box = ctk.CTkTextbox(subwindow,
                                width=600,
                                height=250,
                                font=("Roboto", 14),
                                fg_color=button_blue_colour,
                                text_color=text_colour,
                                border_width=1,
                                border_color=text_colour,
                                corner_radius=10)
  feedback_box.place(x=50, y=260)

  async def on_submit():
      name_text = name_box.get("1.0", tk.END).strip()
      address_text = address_box.get("1.0", tk.END).strip()
      feedback_text = feedback_box.get("1.0", tk.END).strip()

      if not name_text:
          messagebox.showwarning("Empty name",
                                  "Please enter your name before sending.")
          return

      if not address_text:
          messagebox.showwarning("Empty email address",
                                  "Please enter your email address before sending.")
          return
      
      if not feedback_text:
          messagebox.showwarning("Empty feedback",
                                  "Please enter some feedback before sending.")
          return

      try:
        response = await send_email(name=name_text, address=address_text, feedback_text=feedback_text)
        if response.ok: # status_code less than 400
            messagebox.showinfo("Thank you!", "Your feedback has been sent.")
            feedback_box.delete("1.0", tk.END)
            close(subwindow)
        else:
            raise Exception(response.json().get("message", "Unknown error"))
      except Exception as e:
          messagebox.showerror("Error", f"Failed to send feedback:\n{e}")

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
  button_close.place(x=330, y=530)

  #close
  button_submit = ctk.CTkButton(
        subwindow, text="Send Feedback",
        command=lambda: asyncio.run(on_submit()),
        width=150, height=45,
        font=("Roboto", 14 * -1),
        text_color=text_colour,
        fg_color=button_yellow_colour,
        corner_radius=8, border_width=1,
        hover_color=button_yellow_hover,
        border_color=button_border_colour
  )
  button_submit.place(x=500, y=530)

  subwindow.resizable(False, False)
  return subwindow
