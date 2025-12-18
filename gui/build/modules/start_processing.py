from tkinter import Canvas
from tkinter import messagebox
from modules.change_status import *
from modules.binarise_image import *
from modules.skeletonise import *
from modules.faz_utils import *
from modules.change_status import *
from modules.load_image import *
import threading
import os

def is_batch_processing_enabled(canvas: Canvas) -> bool:
    return hasattr(canvas, "bp_selected_folder_path") and canvas.bp_selected_folder_path is not None

def start_processing(canvas: Canvas):
    """
    Start the image processing pipeline on the loaded image in the canvas.
    This includes binarisation and any other processing steps.
    """

    # Preliminary checks for image loaded
    if not hasattr(canvas, "original_img") and not is_batch_processing_enabled(canvas):
        messagebox.showwarning(
            "No Image Loaded", 
            "Please load an image before processing."
        )
        return

    if not is_batch_processing_enabled(canvas):
        # Preliminary image saving folder setup
        make_save_folder(canvas)
        # Indicate that processing is starting
        change_status_to_waiting(canvas)
        thread = threading.Thread(target=lambda: start_processing_threaded(canvas, False))
        thread.start()
    else:
        # TODO batch processing
        start_batch_processing_threaded(canvas)

# Create save folder for current image
# variables such as canvas.FileLabelName and canvas.lastPath are set after load_image
def make_save_folder(canvas: Canvas):
    base_save_dir = getattr(canvas, "save_dir", None)
    if base_save_dir:
        canvas.current_save_folder = os.path.join(base_save_dir, canvas.FileLabelName)
    else:
        canvas.current_save_folder = os.path.join(canvas.lastPath, canvas.FileLabelName)
    os.makedirs(canvas.current_save_folder, exist_ok=True)
    os.makedirs(os.path.join(canvas.current_save_folder, "images"), exist_ok=True)

# Single image processing
# @param {batch} bool = True for batch processing (will additionally process FAZ)
def start_processing_threaded(canvas: Canvas, batch: bool = False):
    print("Starting image processing...")

    binarise_image(canvas)  # long-running

    print("Binarisation completed. Starting skeletonisation...")

    skeletonise(canvas, canvas.binary_image, canvas.twig_size.get())

    print("Skeletonisation completed.")

    # Additional processing if batch mode is on
    if batch:
        if canvas.bp_segment_faz_var.get() == 1:
            generate_faz_mask(canvas)
            measure_faz(canvas)
            print("FAZ generation and metrics measurement completed.")
        # TODO
        # if regional_analysis xxx

    # Switch back to READY (must be done on main thread)
    canvas.after(0, lambda: change_status_to_ready(canvas))

# TODO batch processing
def start_batch_processing_threaded(canvas: Canvas):
    print("Starting batch image processing...")

    # Get images of selected file type from directory
    image_files = [
        f for f in os.listdir(canvas.bp_selected_folder_path)
        if f.lower().endswith(f".{canvas.bp_file_type_var.get().lower()}")
    ]

    if len(image_files) == 0:
        print("No images found in the selected folder.")
        messagebox.showwarning(
            "No Images Found",
            "No images found in the selected folder."
        )
        return change_status_to_ready(canvas)

    # Process each image
    for image_file in image_files:
        image_path = os.path.join(canvas.bp_selected_folder_path, image_file)
        print(f"Processing image: {image_path}")

        # Load image
        try:
            load_image(canvas, 550, 255, 180, 170, silent=True, filePath=image_path)

            # Resize (optional)
            if canvas.bp_batch_resize_bool_var.get() == 1:
                # Convert float64 back to uint8 for PIL, then resize
                image = Image.fromarray(canvas.original_img.astype(np.uint8), mode='L')
                target_size = canvas.bp_batch_resize_value_var.get()
                image_resized = resize_image(image, (target_size, target_size))
                canvas.original_img = np.array(image_resized).astype(np.float64)
                # Update canvas size metadata to match resized image
                canvas.fullImSizePix = (target_size, target_size)
                canvas.FAZ_ctr = (target_size / 2.0, target_size / 2.0)

            # Variable image size (optional)
            if canvas.bp_variable_image_size_bool_var.get() == 1:
                df = canvas.bp_variable_image_size_df[canvas.bp_variable_image_size_df['name'] == image_file]
                if df.empty:
                    canvas.image_size_var.set(int(image_df['size']) if image_df is not None else 1) # Default kernel image size is 1
                else:
                    image_df = df.iloc[0]
                    canvas.image_size_var.set(int(image_df['size']))

            # Create save folders per image
            make_save_folder(canvas)

            # Start processing pipeline
            start_processing_threaded(canvas, batch=True)

        except Exception as e:
            print(f"Failed to load image {image_file}: {e}")
            messagebox.showerror(
                "Image Load Error",
                f"Failed to load image {image_file}."
            )
            continue  # Skip to next image

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
