from tkinter import Canvas
from tkinter import messagebox
from modules.change_status import *
from modules.binarise_image import *
from modules.biomarker import *
from modules.skeletonise import *
from modules.faz_utils import *
from modules.load_image import *
from modules.clear import *
import threading
import os
import datetime

def is_batch_processing_enabled(canvas: Canvas) -> bool:
    return hasattr(canvas, "bp_selected_folder_path") and canvas.bp_selected_folder_path is not None

def start_processing(canvas: Canvas):
    """
    Start the image processing pipeline on the loaded image in the canvas.
    This includes binarisation and any other processing steps.
    """

    # Check if single image loaded or the mode sets to batch processing
    if not hasattr(canvas, "original_img") and not is_batch_processing_enabled(canvas):
        messagebox.showwarning(
            "No Image Loaded", 
            "Please load an image before processing."
        )
        return

    # Clear previous results from the canvas
    clear_screen(canvas, clear_screen_mode=ClearMode.CLEAR_BEFORE_PROCESSING)
    
    if not is_batch_processing_enabled(canvas):
        # Preliminary image saving folder setup
        make_save_folder(canvas)
        # Indicate that processing is starting
        change_status_to_waiting(canvas)
        thread = threading.Thread(target=lambda: start_processing_threaded(canvas, False))
        thread.start()
    else:
        # Batch processing - also run in separate thread to keep UI responsive
        change_status_to_waiting(canvas)
        thread = threading.Thread(target=lambda: start_batch_processing_threaded(canvas))
        thread.start()

# Create save folder for current image
# variables such as canvas.FileLabelName and canvas.lastPath are set after load_image
def make_save_folder(canvas: Canvas):
    # Create a per-original-image save folder
    base_save_dir = getattr(canvas, "save_dir", None)
    if base_save_dir:
        canvas.current_save_folder = os.path.join(base_save_dir, canvas.FileLabelName)
    else:
        canvas.current_save_folder = os.path.join(canvas.lastPath, canvas.FileLabelName)
    os.makedirs(canvas.current_save_folder, exist_ok=True)
    os.makedirs(os.path.join(canvas.current_save_folder, "images"), exist_ok=True)
    # create per-original image metrics files
    canvas.lastMetricsPath = os.path.join(canvas.current_save_folder, canvas.FileLabelName + '_' + datetime.datetime.now().strftime("%d-%b-%Y %H%M%S") + '.xlsx')


    # if not is_batch_processing_enabled(canvas):
    #     # Preliminary image saving folder setup
    #     make_save_folder(canvas)
    #     # Indicate that processing is starting
    #     change_status_to_waiting(canvas)
    #     thread = threading.Thread(target=lambda: start_processing_threaded(canvas, False))
    #     thread.start()
    # else:
    #     # TODO batch processing
    #     start_batch_processing_threaded(canvas)

# Create save folder for current image
# variables such as canvas.FileLabelName and canvas.lastPath are set after load_image
# def make_save_folder(canvas: Canvas):
#     base_save_dir = getattr(canvas, "save_dir", None)
#     if base_save_dir:
#         canvas.current_save_folder = os.path.join(base_save_dir, canvas.FileLabelName)
#     else:
#         canvas.current_save_folder = os.path.join(canvas.lastPath, canvas.FileLabelName)
#     os.makedirs(canvas.current_save_folder, exist_ok=True)
#     os.makedirs(os.path.join(canvas.current_save_folder, "images"), exist_ok=True)

# Single image processing
# @param {batch} bool = True for batch processing (will additionally process FAZ)
def start_processing_threaded(canvas: Canvas, batch: bool = False):
    print("Starting image processing...")

    binarise_image(canvas)  # long-running

    print("Binarisation completed. Starting skeletonisation...")

    display = not batch  # only display skeleton in single image mode
    skeletonise(canvas, canvas.original_img, canvas.binary_image, display=display)

    print("Skeletonisation completed.")

    BiomarkerAnalyzer.process(canvas)

    # Refresh histogram on main thread
    def refresh_histogram_ui():
        if hasattr(canvas, "hist_plotter"):
            diameters = getattr(canvas, "vessel_diameters_um", [])
            canvas.hist_plotter.set_data(diameters)
            canvas.hist_plotter.update_plot(canvas.bin_size_var.get())
            images_dir = os.path.join(canvas.current_save_folder, "images")
            os.makedirs(images_dir, exist_ok=True)

            bin_size = int(canvas.bin_size_var.get())
            hist_path = os.path.join(
                images_dir,
                f"{canvas.FileLabelName}_VDD_Bin{bin_size}.png"
            )
            canvas.hist_plotter.save_to_file(hist_path)

    canvas.after(0, refresh_histogram_ui)

    print("Biomarker analyzer processing completed.")
    
    # Additional processing if batch mode is on
    if batch:
        if canvas.bp_segment_faz_var.get() == 1:
            generate_faz_mask(canvas, batch=True)
            display_faz_image(canvas)
            measure_faz(canvas)
            print("FAZ generation and metrics measurement completed.")
        # TODO
        # if regional_analysis xxx

    # Switch back to READY (must be done on main thread)
    canvas.after(0, lambda: change_status_to_ready(canvas))

# batch processing
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
        #todo: limit this to only images
        image_path = os.path.join(canvas.bp_selected_folder_path, image_file)
        print(f"Processing image: {image_path}")
        canvas.after(0, lambda: change_queue_status(canvas, status=f"Processing {index} of {len(image_files)}", fill=theme_red))

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
            skipped_images.append(image_file)
            continue  # Skip to next image

    # TODO Generate overall metrics spreadsheet for all images
    
    # Process only successfully loaded images
    processed_images = [img for img in image_files if img not in skipped_images]
    
    # Dictionary to hold DataFrames by sheet name
    all_metrics_df = {}
    
    for (index, image_file) in enumerate(processed_images, start=1):
        image_folder_path = os.path.join(canvas.bp_selected_folder_path, os.path.splitext(image_file)[0])
        
        # 1. Read the latest generated spreadsheets from this folder
        spreadsheets = [
            f for f in os.listdir(image_folder_path)
            if f.lower().endswith('.xlsx')
        ]
        
        # Sort by datetime in filename (same strptime %d-%b-%Y %H%M%S")
        def get_file_datetime(file_name):
            try:
                file_exts = file_name.split('_', 1)
                datetime_str = file_exts[1].replace('.xlsx', '')
                return datetime.datetime.strptime(datetime_str, "%d-%b-%Y %H%M%S")
            except:
                pass
            return datetime.datetime.min
        
        # Sort spreadsheets by datetime and get the latest
        spreadsheets.sort(key=get_file_datetime, reverse=True)
        print(f"Latest spreadsheet for {image_file}: {spreadsheets[0]}")
        
        # Read all sheets from the Excel file
        excel_data = pd.read_excel(os.path.join(image_folder_path, spreadsheets[0]), sheet_name=None, index_col=None)
        
        # Group dfs by sheet name
        for sheet_name, sheet_df in excel_data.items():
            if sheet_name not in all_metrics_df:
                all_metrics_df[sheet_name] = []
            all_metrics_df[sheet_name].append(sheet_df)

    # 2. Concat df for each sheet and save the overall metrics spreadsheet
    results_file_path = os.path.join(canvas.bp_selected_folder_path, f"OCTAVA Results {datetime.datetime.now().strftime('%d-%b-%Y %H%M%S')}.xlsx")
    
    with pd.ExcelWriter(results_file_path, engine='openpyxl') as writer:
        for sheet_name, df_list in all_metrics_df.items():
            df_concat = pd.concat(df_list, ignore_index=True)
            df_concat.to_excel(writer, sheet_name=sheet_name, index=False)
    
    print(f"Overall metrics saved to: {results_file_path}")
    print("Batch image processing completed.")

    # Switch back to READY
    change_status_to_ready(canvas)

    # Reset queue status
    change_queue_status(canvas, status="Processed", fill=theme_blue)
