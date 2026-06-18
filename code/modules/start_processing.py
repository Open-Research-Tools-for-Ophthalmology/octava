from tkinter import Canvas
from tkinter import messagebox
from modules.change_status import *
from modules.binarise_image import *
from modules.onh_binarise_image import *
from modules.biomarker import *
from modules.skeletonise import *
from modules.faz_utils import *
from modules.load_image import *
from modules.clear import *
from modules.regional_analysis import *
from modules.onh_vessel_separation import *
from modules.onh_skeletonise import *
from modules.onh_biomarker import *
import numpy as np
import threading
import os
import datetime
from natsort import natsorted
from theme import *

skipped_images = []  # List to track images that failed to load during batch processing

def is_batch_processing_enabled(canvas: Canvas) -> bool:
    """Return whether a batch input folder has been selected."""
    return hasattr(canvas, "bp_selected_folder_path") and canvas.bp_selected_folder_path is not None

def is_regional_analysis_enabled(canvas:Canvas) ->bool:
    """Return whether any regional-analysis mode is enabled for the current run."""
    if is_batch_processing_enabled(canvas):
        return hasattr(canvas, "bp_regional_analysis_var") and canvas.bp_regional_analysis_var.get() == 1
    return canvas.square_grid_bool.get()|canvas.etdrs_grid_bool.get()|canvas.extended_etdrs_bool.get()|canvas.foveal_ring_bool.get()|canvas.optic_nerve_head_bool.get()

def is_onh_quadrant_analysis_enabled(canvas: Canvas) -> bool:
    return (
        hasattr(canvas, "onh_quadrant_analysis_bool")
        and canvas.onh_quadrant_analysis_bool.get() == 1
    )

def is_onh_octant_analysis_enabled(canvas: Canvas) -> bool:
    return (
        hasattr(canvas, "onh_octant_analysis_bool")
        and canvas.onh_octant_analysis_bool.get() == 1
    )

def is_prebinary_enabled(canvas:Canvas) ->bool:
    """Return whether the loaded image should be treated as pre-binarized input."""
    return hasattr(canvas, "prebinary_var") and canvas.prebinary_var.get() == 1

def get_image_type(canvas: Canvas) -> str:
    return canvas.img_type_var.get()

def toggle_processing_and_continue(canvas: Canvas):
    print("toggle_processing_and_continue called. Current process_flag:", getattr(canvas, 'process_flag', False), "abort_flag:", getattr(canvas, 'abort_flag', False))
    if not getattr(canvas, 'process_flag', False):
        print("If not processing, start processing and swap button to abort")
        # If not processing, start processing and swap button to abort
        canvas.abort_flag = False
        canvas.process_flag = True
        canvas.after(0, lambda:canvas.process_button.configure(
            text="Abort (Stop after the current checkpoint)",
            fg_color=button_yellow_colour,
            hover_color=button_yellow_hover,
        ))
        return True
    elif getattr(canvas, 'process_flag', False) and not getattr(canvas, 'abort_flag', False):
        print("If is processing and not aborting, request abort")
        # If is processing and not aborting, request abort
        canvas.abort_flag = True
        canvas.after(0, lambda: canvas.process_button.configure(
            text="Start Processing",
            fg_color=button_blue_colour,
            hover_color=button_blue_hover,
        ))
        canvas.after(1, lambda: change_status_to_waiting(canvas, "● Aborting..."))
        return False
    elif getattr(canvas, 'abort_flag', False):
        print("If is currently aborting, skip action")
        # If is currently aborting, skip action
        return False

def abort_if_requested(canvas: Canvas):
    if getattr(canvas, 'abort_flag', False):
        print("Processing aborted by user after binarisation.")
        canvas.after(0, lambda: change_status_to_ready(canvas))
        return True
    return False

def reset_processing_on_error(canvas: Canvas):
    canvas.after(0, lambda: canvas.process_button.configure(
        text="Start Processing",
        fg_color=button_blue_colour,
        hover_color=button_blue_hover,
    ))

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
        reset_processing_on_error(canvas)
        return

    if is_batch_processing_enabled(canvas) and get_image_type(canvas) != "Retina":
        messagebox.showinfo(
            "Batch Processing Unavailable",
            "Batch processing is currently available for Retina images only."
        )
        reset_processing_on_error(canvas)
        return

    # Toggle process button to either process or abort
    continue_flag = toggle_processing_and_continue(canvas)
    if not continue_flag:
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
    """Create the per-image output folder structure and metrics workbook path."""
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

# Single image processing
def start_processing_threaded(canvas: Canvas, batch: bool = False):
    """Dispatch processing to the pipeline selected for the current image type."""
    img_type = get_image_type(canvas)

    print(f"Image type selected: {img_type}")

    if img_type == "Retina":
        start_retina_processing_threaded(canvas, batch)
    elif img_type == "ONH":
        start_onh_processing_threaded(canvas, batch)
    elif img_type == "Skin":
        start_skin_processing_threaded(canvas, batch)
    else:
        raise ValueError(f"Unsupported image type: {img_type}")


# @param {batch} bool = True for batch processing (will additionally process FAZ)
def start_retina_processing_threaded(canvas: Canvas, batch: bool = False):
    print("Starting Retina processing...")
    if not is_prebinary_enabled(canvas):
        print("Starting Retina binarising...")
        binarise_image(canvas)  # long-running
        print("Binarisation completed. Starting skeletonisation...")
        if abort_if_requested(canvas): return

    # display = not batch  # only display skeleton in single image mode
    display = True
    skeletonise(canvas, canvas.original_img, canvas.binary_image, display=display)
    print("Skeletonisation completed.")
    if abort_if_requested(canvas): return

    BiomarkerAnalyzer.process(canvas)

    # Refresh histogram on main thread
    def refresh_histogram_ui():
        """Refresh and persist the vessel-diameter histogram from the latest measurements."""
        if hasattr(canvas, "hist_plotter"):
            # Always update both datasets; display whichever mode is active
            diameters   = getattr(canvas, "vessel_diameters_um", [])
            tortuosity  = getattr(canvas, "vessel_tortuosity", [])
            hist_mode   = getattr(canvas, "_hist_mode", "diameter")
            tort_bin    = float(getattr(canvas, "tort_bin_size_var", type("_", (), {"get": lambda s: 0.1})()).get())
            diam_bin    = int(canvas.bin_size_var.get())

            if hist_mode == "tortuosity":
                canvas.hist_plotter.set_data(tortuosity)
                canvas.hist_plotter.update_plot(tort_bin)
            else:
                canvas.hist_plotter.set_data(diameters)
                canvas.hist_plotter.update_plot(diam_bin)

            images_dir = os.path.join(canvas.current_save_folder, "images")
            os.makedirs(images_dir, exist_ok=True)

            # Save diameter histogram
            canvas.hist_plotter.set_data(diameters)
            canvas.hist_plotter.update_plot(diam_bin)
            hist_path = os.path.join(images_dir, f"{canvas.FileLabelName}_VDD_Bin{diam_bin}.png")
            canvas.hist_plotter.save_to_file(hist_path)

            # Save tortuosity histogram
            canvas.hist_plotter.set_data(tortuosity)
            canvas.hist_plotter.update_plot(tort_bin)
            tort_path = os.path.join(images_dir, f"{canvas.FileLabelName}_Tortuosity_Hist.png")
            canvas.hist_plotter.save_to_file(tort_path)

            # Restore to active mode
            if hist_mode == "tortuosity":
                canvas.hist_plotter.set_data(tortuosity)
                canvas.hist_plotter.update_plot(tort_bin)
            else:
                canvas.hist_plotter.set_data(diameters)
                canvas.hist_plotter.update_plot(diam_bin)

    canvas.after(0, refresh_histogram_ui)

    print("Biomarker analyzer processing completed.")
    if abort_if_requested(canvas): return

    # Additional processing if batch mode is on
    if batch:
        if canvas.bp_segment_faz_var.get() == 1:
            generate_faz_mask(canvas, batch=True)
            display_faz_image(canvas)
            measure_faz(canvas)
            print("FAZ generation and metrics measurement completed.")
            if abort_if_requested(canvas): return

    if is_regional_analysis_enabled(canvas):
        print("Running regional analysis...")
        run_regional_analysis(canvas)
        print("Regional analysis completed.")

    # Switch back to READY (must be done on main thread)
    canvas.after(0, lambda: change_status_to_ready(canvas))

def start_onh_processing_threaded(canvas: Canvas, batch: bool = False):
    print("Starting ONH processing...")

    if batch:
        canvas.after(0, lambda: messagebox.showinfo(
            "ONH Batch Processing",
            "ONH batch processing is not enabled yet because each image needs a confirmed ONH ring mask."
        ))
        reset_processing_on_error(canvas)
        canvas.after(0, lambda: change_status_to_ready(canvas))
        return

    if not hasattr(canvas, "onh_mask_img") or not hasattr(canvas, "onh_mask_arr"):
        canvas.after(0, lambda: messagebox.showwarning(
            "ONH Mask Missing",
            "Please open ONH Mask and confirm the ring mask before processing."
        ))
        reset_processing_on_error(canvas)
        canvas.after(0, lambda: change_status_to_ready(canvas))
        return

    try:
        # 1. ONH-specific overall binarisation
        if is_prebinary_enabled(canvas):
            print("ONH prebinary selected. Using loaded image as ONH overall binary mask.")
            prepare_onh_prebinary_overall(canvas)
            if abort_if_requested(canvas): return
        else:
            print("Starting ONH-specific binarisation...")
            binarise_onh_image(canvas, display=False)
            if abort_if_requested(canvas): return
            print("ONH-specific binarisation completed.")

        # 2. ONH large/small vessel separation
        print("Starting ONH large/small vessel separation...")
        separate_onh_vessels(canvas, canvas.onh_binary_overall, display=False)
        print("ONH large/small vessel separation completed.")
        if abort_if_requested(canvas): return

        # 3. ONH-specific skeletonisation for each vessel class
        print("Starting ONH skeletonisation for overall, large, and small vessels...")
        skeletonise_onh(
            canvas,
            canvas.onh_binary_overall,
            display=False,
            label="overall",
            set_active=True,
        )
        if abort_if_requested(canvas): return
        skeletonise_onh(
            canvas,
            canvas.onh_binary_large,
            display=False,
            label="large",
            set_active=False,
        )
        if abort_if_requested(canvas): return
        skeletonise_onh(
            canvas,
            canvas.onh_binary_small,
            display=False,
            label="small",
            set_active=False,
        )
        if abort_if_requested(canvas): return
        print("ONH skeletonisation completed for all vessel classes.")

        # 4. ONH metrics for all vessel classes
        ONHBiomarkerAnalyzer.process(canvas)
        if abort_if_requested(canvas): return

        if is_onh_quadrant_analysis_enabled(canvas):
            print("Running ONH quadrant analysis...")
            ONHBiomarkerAnalyzer.process_subregions(canvas, divider="quadrant")
            print("ONH quadrant analysis completed.")
            if abort_if_requested(canvas): return

        if is_onh_octant_analysis_enabled(canvas):
            print("Running ONH octant analysis...")
            ONHBiomarkerAnalyzer.process_subregions(canvas, divider="octant")
            print("ONH octant analysis completed.")
            if abort_if_requested(canvas): return

        selected_view = "Overall"
        if hasattr(canvas, "onh_segmentation_view_var"):
            selected_view = canvas.onh_segmentation_view_var.get()

        canvas.after(
            0,
            lambda view=selected_view: update_onh_segmentation_dropdown_display(canvas, view)
        )

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
                    f"{canvas.FileLabelName}_ONH_VDD_{selected_view.replace(' ', '_')}_Bin{bin_size}.png"
                )
                canvas.hist_plotter.save_to_file(hist_path)

        canvas.after(0, refresh_histogram_ui)
        canvas.after(0, lambda: change_status_to_ready(canvas))
        return

    except Exception as e:
        err_msg = str(e)
        print(f"ONH processing failed: {err_msg}")
        canvas.after(0, lambda msg=err_msg: messagebox.showerror("ONH Processing Error", msg))
        reset_processing_on_error(canvas)


def prepare_onh_prebinary_overall(canvas: Canvas):
    if hasattr(canvas, "binary_image"):
        source = canvas.binary_image
    elif hasattr(canvas, "original_img"):
        source = canvas.original_img
    else:
        raise ValueError("No loaded image found for ONH prebinary processing.")

    roi_mask = canvas.onh_mask_arr.astype(bool)

    if source.shape != roi_mask.shape:
        raise ValueError("ONH prebinary image and ONH mask have different sizes.")

    binary = ((source > 0) & roi_mask).astype(np.uint8) * 255

    canvas.onh_binary_overall = binary
    canvas.onh_overall_vessel_img = binary
    canvas.binary_image = binary
    canvas.inverted_image = binary.copy()

    save_onh_binary_image(canvas, binary)

# Skin pipeline not implemented yet
def start_skin_processing_threaded(canvas: Canvas, batch: bool = False):
    print("Starting Skin processing...")
    print("Skin processing pipeline is not implemented in the current project scope.")

    canvas.after(0, lambda: messagebox.showinfo(
        "Skin Processing",
        "Skin processing pipeline is not implemented in the current project scope."
    ))
    reset_processing_on_error(canvas)
    canvas.after(0, lambda: change_status_to_ready(canvas))

# batch processing
def start_batch_processing_threaded(canvas: Canvas):
    """Iterate through the selected batch folder and process each supported image."""
    print("Starting batch image processing...")
    
    # Get images of selected file type from directory
    image_files = [
        f for f in os.listdir(canvas.bp_selected_folder_path)
        if f.lower().endswith(f".{canvas.bp_file_type_var.get().lower()}")
    ]

    # Natural sort the image files for sequential processing
    image_files = natsorted(image_files)

    if len(image_files) == 0:
        print("No images found in the selected folder.")
        messagebox.showwarning(
            "No Images Found",
            "No images found in the selected folder."
        )
        print("Processing aborted due to no images found.")
        reset_processing_on_error(canvas)
        return change_status_to_ready(canvas)

    # Process each image
    for (index, image_file) in enumerate(image_files, start=1):
        # Check for abort request before starting next image
        if getattr(canvas, 'abort_flag', False):
            print("Batch processing aborted by user.")
            canvas.after(0, lambda: change_status_to_ready(canvas))
            canvas.after(0, lambda: change_queue_status(canvas, status=""))
            return

        #todo: limit this to only images
        image_path = os.path.join(canvas.bp_selected_folder_path, image_file)
        print(f"Processing image: {image_path}")
        canvas.after(0, lambda: change_queue_status(canvas, status=f"Processing {index} of {len(image_files)}", fill=theme_red))

        # Load image
        skipped_images = []
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
    
    # Process only successfully loaded images
    processed_images = [img for img in image_files if img not in skipped_images]
    
    # Natural sort the image files for sequential aggregation
    processed_images = natsorted(processed_images)

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
            """Parse the timestamp embedded in an exported metrics workbook filename."""
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
            if "Regional analysis_" in sheet_name:
                # Special case: split each regional row within the ROI into its own sheet.  
                image_name = os.path.splitext(image_file)[0]
                for row_idx, row in sheet_df.iterrows():
                    row_df = row.to_frame().transpose().copy()
                    region_name = str(row_df.iloc[0].get("Region", f"Region{row_idx + 1}"))
                    row_df.drop(columns=["Region"], inplace=True)
                    row_df["name"] = image_name
                    if region_name not in all_metrics_df:
                        all_metrics_df[region_name] = []
                    all_metrics_df[region_name].append(row_df)
            else:
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

