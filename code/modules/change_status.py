from tkinter import Canvas, messagebox
from theme import *

def disable_click_if_busy(canvas: Canvas):
  # Prevent clicking if currently processing an image
  status_text = canvas.itemcget(canvas.status_id, "text") 
  queue_text = canvas.itemcget(canvas.queue_id, "text") 
  if (status_text and status_text != "● Ready") or (queue_text and queue_text != ""):
    print("Currently processing an image. Please wait...")
    messagebox.showinfo("Please Wait", "Currently processing an image. Please wait...")
    return True
  return False
    
def change_status(canvas: Canvas, status: str, colour: str = theme_blue):
  """Update the main status label and flush the Tk event queue."""
  canvas.itemconfigure(canvas.status_id, text=status, fill=colour)
  canvas.update_idletasks()  # immediately refresh the UI

def change_status_to_waiting(canvas:Canvas, status:str="● Wait"):
  """Set the main status label to a waiting state."""
  change_status(canvas, status=status, colour=theme_red)

def change_status_to_ready(canvas:Canvas):
  """Set the main status label to the ready state."""
  print("change_status_to_ready: Changing status to ready.")
  change_status(canvas, status="● Ready", colour=theme_blue)
  canvas.abort_flag = False
  canvas.process_flag = False

def change_queue_status(canvas:Canvas, status:str="Processed", fill:str=theme_blue):
  """Update the batch-processing queue status label."""
  canvas.itemconfigure(canvas.queue_id, text=status, fill=fill)
  canvas.update_idletasks()  # immediately refresh the UI
