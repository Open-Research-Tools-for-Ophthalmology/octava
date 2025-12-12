from tkinter import Canvas
from tkinter import messagebox
from modules.change_status import *
from modules.binarise_image import *
from modules.skeletonise import *
from modules.clear import *
import threading
import os

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
    
    # Clear previous results from the canvas
    clear_screen(canvas, clear_screen_mode=ClearMode.CLEAR_BEFORE_PROCESSING)
    
    # Create a per-original-image save folder
    base_save_dir = getattr(canvas, "save_dir", None)
    if base_save_dir:
        canvas.current_save_folder = os.path.join(base_save_dir, canvas.FileLabelName)
    else:
        canvas.current_save_folder = os.path.join(canvas.lastPath, canvas.FileLabelName)
    os.makedirs(canvas.current_save_folder, exist_ok=True)

    # Indicate that processing is starting
    change_status_to_waiting(canvas)

    thread = threading.Thread(target=lambda: start_processing_threaded(canvas))
    thread.start()


def start_processing_threaded(canvas: Canvas):
    print("Starting image processing...")

    binarise_image(canvas)  # long-running

    print("Binarisation completed. Starting skeletonisation...")

    skeletonise(canvas, canvas.binary_image, canvas.twig_size.get())

    print("Skeletonisation completed.")

    # Switch back to READY (must be done on main thread)
    canvas.after(0, lambda: change_status_to_ready(canvas))
