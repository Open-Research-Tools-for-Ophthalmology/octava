from tkinter import Canvas
from modules.change_status import change_status_to_waiting
import numpy as np
from PIL import Image, ImageTk
from modules.resize_image import * 

# Initialize default ring positions to center of the image
# @return sq_start and sq_end coordinates for the square bounding box
def get_default_ring_positions(canvas: Canvas):
    orig_height, orig_width = canvas.original_img.shape
    center_x = orig_width // 2
    center_y = orig_height // 2
    image_size_mm = float(canvas.image_size_var.get())
    default_radius = (2.0 / image_size_mm) * orig_width

    sq_start = (center_x - default_radius, center_y - default_radius)
    sq_end = (center_x + default_radius, center_y + default_radius)
    print("Initializing default ring positions at the center x, y:", sq_start, sq_end)
    return sq_start, sq_end

# This is only available for batch processing, where center of ONH is assumed
# Generate ONH mask from image and treat physical center of the image as the center of ONH by default
def generate_onh_mask(canvas: Canvas):
    change_status_to_waiting(canvas, status="● Wait...Generating ONH mask")

    orig_height, orig_width = canvas.original_img.shape
    sq_start, sq_end = get_default_ring_positions(canvas)
    x1, y1 = sq_start
    x2, y2 = sq_end

    # Calculate center in display coordinates
    center_x = (x1 + x2) / 2
    center_y = (y1 + y2) / 2
    
    # Scale rel. original image coordinates
    center_x_orig = int(center_x)
    center_y_orig = int(center_y)
    radius_outer_orig = int((x2 - x1) / 2)
    radius_inner_orig = int((x2 - x1) / 2) / 2

    # Store ring parameters and create mask for @author Joshua's future use
    canvas.onh_center = (center_x_orig, center_y_orig)
    canvas.onh_radius_outer = radius_outer_orig
    canvas.onh_radius_inner = radius_inner_orig
    
    # Create intersection mask between inner and outer ring
    y_coords, x_coords = np.ogrid[:orig_height, :orig_width]
    dist_from_center = np.sqrt((x_coords - center_x_orig)**2 + (y_coords - center_y_orig)**2)
    inter_mask = (dist_from_center > radius_inner_orig) & (dist_from_center <= radius_outer_orig)
    
    # Store intersection for @author Joshua's future use   
    masked_img = np.where(inter_mask, canvas.original_img, 0).astype(np.uint8)
    canvas.onh_mask_arr = inter_mask
    canvas.onh_mask_img = masked_img


    masked_preview = resize_image(
        Image.fromarray(masked_img, mode="L"),
        (200, 200)
    )
    masked_preview_tk = ImageTk.PhotoImage(masked_preview)
    if hasattr(canvas, "original_img_id"):
        canvas.itemconfigure(canvas.original_img_id, image=masked_preview_tk)
    else:
        canvas.original_img_id = canvas.create_image(550, 255, image=masked_preview_tk)
    if not hasattr(canvas, "_image_refs"):
        canvas._image_refs = {}
    canvas._image_refs["original_img"] = masked_preview_tk

    print(f"ONH mask saved. Center: ({center_x_orig}, {center_y_orig}), Inner radius: {radius_inner_orig}, Outer radius: {radius_outer_orig}")
