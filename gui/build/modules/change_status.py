from tkinter import Canvas
from theme import *

def change_status(canvas: Canvas, status: str, colour: str = theme_blue):
  canvas.itemconfigure(canvas.status_id, text=status, fill=colour)
  canvas.update_idletasks()  # immediately refresh the UI


def change_status_to_waiting(canvas):
  change_status(canvas, status="🔴 Wait", colour=theme_red)


def change_status_to_ready(canvas):
  change_status(canvas, status="🟢 Ready")