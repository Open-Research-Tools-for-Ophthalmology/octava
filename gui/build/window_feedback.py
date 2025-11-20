from pathlib import Path
import tkinter as tk
# Explicit imports to satisfy Flake8
from tkinter import Tk, Canvas, Entry, Text, Button, PhotoImage, Toplevel, Checkbutton, IntVar, Spinbox, messagebox
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from theme import *
import customtkinter as ctk


def close(window):
  window.destroy()
  window.update()


def send_email(feedback_text: str):
    """
    Send the feedback text to Mila's email using Gmail SMTP.

    IMPORTANT:
    - Replace SENDER_EMAIL with your Gmail address.
    - Replace APP_PASSWORD with your Gmail app password
      (generate this in your Google Account > Security > App passwords).
    """
    SENDER_EMAIL = "your_gmail_address@gmail.com"          # <- change this
    APP_PASSWORD = "YOUR_APP_PASSWORD_HERE"                # <- change this
    RECEIVER_EMAIL = "mila.zhang2019@gmail.com"

    # Build the email
    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL
    msg["Subject"] = "OCTAVA Feedback"
    msg.attach(MIMEText(feedback_text, "plain"))

    # Send via Gmail SMTP
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.send_message(msg)


def open_feedback_window(canvas):
  subwindow = Toplevel()
  subwindow.title("Feedback")
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
      70.0,
      anchor="nw",
      text="Send us your feedback:",
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
  feedback_box.place(x=100, y=110)

  def on_submit():
      feedback_text = feedback_box.get("1.0", tk.END).strip()
      if not feedback_text:
          messagebox.showwarning("Empty feedback",
                                  "Please enter some feedback before sending.")
          return
      try:
          send_email(feedback_text)
          messagebox.showinfo("Thank you!", "Your feedback has been sent.")
          feedback_box.delete("1.0", tk.END)
          close(subwindow)
      except Exception as e:
          messagebox.showerror("Error", f"Failed to send feedback:\n{e}")

  #close
  button_close = ctk.CTkButton(subwindow, text="Cancel",
                          command=lambda: close(subwindow),
                          width=150,height=45,
                          font=("Roboto", 14 * -1),
                          text_color=text_colour,
                          fg_color=button_blue_colour,
                          corner_radius=8,border_width=1,
                          hover_color=button_blue_hover,
      border_color=button_border_colour  )
  button_close.place(x=200, y=450)

  #close
  button_submit = ctk.CTkButton(
        subwindow, text="Send Feedback",
        command=on_submit,
        width=150, height=45,
        font=("Roboto", 14 * -1),
        text_color=text_colour,
        fg_color=button_blue_colour,
        corner_radius=8, border_width=1,
        hover_color=button_blue_hover,
        border_color=button_border_colour
    )
  button_submit.place(x=400, y=450)

  subwindow.resizable(False, False)
  subwindow.mainloop()
