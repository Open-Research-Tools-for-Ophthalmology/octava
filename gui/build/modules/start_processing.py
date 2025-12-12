from tkinter import Canvas
from tkinter import messagebox
from modules.change_status import *
from modules.binarise_image import *
from modules.skeletonise import *
from modules.faz_utils import *
from modules.change_status import *
from modules.clear import *
import threading
import os

def start_processing(canvas: Canvas):
    """
    Start the image processing pipeline on the loaded image in the canvas.
    This includes binarisation and any other processing steps.
    """
    if not hasattr(canvas, "original_img") and not hasattr(canvas, "selected_folder_path"):
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
    else:
        start_batch_processing_threaded(canvas)

def start_processing_threaded(canvas: Canvas):
    print("Starting image processing...")

    binarise_image(canvas)  # long-running

    print("Binarisation completed. Starting skeletonisation...")

    skeletonise(canvas, canvas.binary_image, canvas.twig_size.get())

    print("Skeletonisation completed.")

    # Switch back to READY (must be done on main thread)
    canvas.after(0, lambda: change_status_to_ready(canvas))

# TODO batch processing
def start_batch_processing_threaded(canvas: Canvas):
    print("Starting batch image processing...")

    # Read options
    dir_path = canvas.selected_folder_path
    file_type = canvas.bp_file_type_var.get()
    batch_resize = canvas.bp_batch_resize_var.get()
    batch_resize_value = canvas.bp_batch_resize_value.get()
    measure_faz = canvas.bp_measure_faz_var.get()

    # Get images from directory
    image_files = [
        f for f in os.listdir(dir_path)
        if f.lower().endswith(f".{file_type.lower()}")
    ]

    # Batch resize
    if batch_resize == 1:
        change_status_to_waiting(canvas, status="🔴 Wait...Batch Resizing")
        print(f"Batch resizing images to {batch_resize_value} pixels...")

        for image_file in image_files:
            image_path = os.path.join(dir_path, image_file)
            image = Image.open(image_path).convert("L")
            image_resized = resize_image(image, (batch_resize_value, batch_resize_value))
            image_resized.save(os.path.join(dir_path, image_file.strip(file_type).strip(".") + "_resized." + file_type))
        print("Batch resizing completed.")
        change_status_to_ready(canvas)

    # Task to be multi-threaded
    tasks = [
        # binarise_image,
        # skeletonise,
        # generate_faz_mask,
        # TODO generate metrics
    ]
    threads = []

    # TODO We can multi-thread image processing and saving
    # Append tasks
    for task in tasks:
        thread = threading.Thread(target=task, args=(canvas,))
        threads.append(thread)

    # Start each thread
    for thread in threads:
        thread.start()

    # Wait for all threads to finish
    for thread in threads:
        thread.join()

    # TODO For metrics calculation, do it in main thread
    print("Batch image processing completed.")
    # measure_faz(canvas)

    # Switch back to READY (must be done on main thread)
    canvas.after(0, lambda: change_status_to_ready(canvas))
