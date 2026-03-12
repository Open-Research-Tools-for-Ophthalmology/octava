from tkinter import Canvas
from theme import *

def change_status(canvas: Canvas, status: str, colour: str = theme_blue):
  canvas.itemconfigure(canvas.status_id, text=status, fill=colour)
  canvas.update_idletasks()  # immediately refresh the UI

def change_status_to_waiting(canvas:Canvas, status:str="🔴 Wait"):
  change_status(canvas, status=status, colour=theme_red)

def change_status_to_ready(canvas:Canvas):
  change_status(canvas, status="● Ready", colour=theme_blue)

def change_queue_status(canvas:Canvas, status:str="Processed", fill:str=theme_blue):
  canvas.itemconfigure(canvas.queue_id, text=status, fill=fill)
  canvas.update_idletasks()  # immediately refresh the UI