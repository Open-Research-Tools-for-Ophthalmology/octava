from tkinter import Canvas
from tkinter import messagebox
from modules.change_status import *
from modules.binarise_image import *
import threading

def start_processing(canvas: Canvas):
    """
    Start the image processing pipeline on the loaded image in the canvas.
    This includes binarisation and any other processing steps.
    """
    if not hasattr(canvas, "original_img"):
        messagebox.showwarning(
            "No Image Loaded", 
            "Please load an image before processing."
        )
        return


    # Indicate that processing is starting
    change_status_to_waiting(canvas)

    thread = threading.Thread(target=lambda: start_processing_threaded(canvas))
    thread.start()


def start_processing_threaded(canvas: Canvas):
    print("Starting image processing...")

    binarise_image(canvas)  # long-running

    print("Image processing completed.")

    # Switch back to READY (must be done on main thread)
    canvas.after(0, lambda: change_status_to_ready(canvas))
