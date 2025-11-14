import tkinter as tk
from tkinter import messagebox
from modules.binarise_image import *

def start_processing(canvas):
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

    print("\nStarting image processing...")

    # Binarise the image using fuzzy thresholding
    binarise_image(canvas)

    print("Image processing completed.")