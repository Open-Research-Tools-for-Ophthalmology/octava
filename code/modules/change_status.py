from tkinter import Canvas, messagebox
from theme import *

def check_if_busy(canvas: Canvas):
    # Check if currently processing an image
    status_text = canvas.itemcget(canvas.status_id, "text") 
    queue_text = canvas.itemcget(canvas.queue_id, "text") 
    if (status_text and status_text != "● Ready") or (queue_text and queue_text != "" and queue_text != "Processed" and queue_text != "Aborted by User"):
        return True
    return False

def disable_click_if_busy(canvas: Canvas):
  # Prevent clicking if currently processing an image
  if check_if_busy(canvas):
    print("Currently processing an image. Please wait...")
    messagebox.showinfo("Please Wait", "Currently processing an image. Please wait...")
    return True
  return False

def clear_status_and_queue_status(canvas: Canvas):
    """Reset the main status and queue status labels to their default states."""
    change_status(canvas, status="", colour=theme_blue)
    change_queue_status(canvas, status="", fill=theme_blue)

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
