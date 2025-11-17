from tkinter import Canvas

def change_status(canvas: Canvas, status: str):
  canvas.itemconfigure(canvas.status_id, text=status)
  canvas.update_idletasks()  # immediately refresh the UI


def change_status_to_waiting(canvas):
  print("Changing status to waiting...")
  change_status(canvas, status="🟡 Waiting...")


def change_status_to_ready(canvas):
  change_status(canvas, status="🟢 Ready")