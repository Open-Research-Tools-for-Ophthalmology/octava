from tkinter import Canvas
from theme import *

def change_status(canvas: Canvas, status: str, colour: str = theme_blue):
  """Update the main status label and flush the Tk event queue."""
  canvas.itemconfigure(canvas.status_id, text=status, fill=colour)
  canvas.update_idletasks()  # immediately refresh the UI

def change_status_to_waiting(canvas:Canvas, status:str="● Wait"):
  """Set the main status label to a waiting state."""
  change_status(canvas, status=status, colour=theme_red)

def change_status_to_ready(canvas:Canvas):
  """Set the main status label to the ready state."""
  change_status(canvas, status="● Ready", colour=theme_blue)

def change_queue_status(canvas:Canvas, status:str="Processed", fill:str=theme_blue):
  """Update the batch-processing queue status label."""
  canvas.itemconfigure(canvas.queue_id, text=status, fill=fill)
  canvas.update_idletasks()  # immediately refresh the UI
