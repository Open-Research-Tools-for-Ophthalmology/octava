from tkinter import Canvas, messagebox
import numpy as np
import cv2
import os
from modules.auto_faz.auto_faz import auto_faz
from modules.resize_image import *
from PIL import Image, ImageTk, ImageDraw
from scipy import ndimage
import pandas as pd
import datetime
from modules.change_status import *

def display_faz_image(canvas: Canvas):
    # TODO Display finished FAZ mask on main window canvas
    # Create a 200x200 resized version for display
    preview = resize_image(canvas.faz_grayscale_img)
    img_tk = ImageTk.PhotoImage(preview)

    img_id = canvas.create_image(550, 550, image=img_tk)

    # Prevent garbage collection. Without this, the image will not display.
    if not hasattr(canvas, "_image_refs"):
        canvas._image_refs = []
    canvas._image_refs.append(img_tk)

# Edit: Load existing FAZ grayscale array into polygon points
def load_faz_grayscale_arr(canvas: Canvas):
    # Get faz mask
    grayscale_arr = canvas.faz_grayscale_arr.copy()
    
    contours, _ = cv2.findContours(grayscale_arr, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE) # Find contours from grayscale mask

    print("contours found:", len(contours))

    if len(contours) == 0:
        return messagebox.showwarning("No FAZ contours found")
    
    cnt = max(contours, key=cv2.contourArea)
    cnt = cnt.reshape(-1, 2)  # Shape: (N, 2)
    print("largest contour points:", len(cnt))

    # TODO may need better reduce machanism
    # Reduce number of points to closely to 20 points for easier editing
    reduce_divisor = max(1, len(cnt) // 20)
    cnt_reduced = cnt[::reduce_divisor]
    print("reduced contour points:", len(cnt_reduced))
    return [(point[0], point[1]) for point in cnt_reduced]

# TODO From FAZ_code/get_area.py
def get_area(x:np.ndarray,y:np.ndarray)->float:
    """
    Computes the signed area of a polygon using the shoelace formula.

    Parameters:
    - x: 1D array of x-coordinates of the contour points
    - y: 1D array of y-coordinates of the contour points

    Returns:
    - A: Signed area of the polygon (float)
    """
    if len(x) != len(y):
        raise ValueError("Input arrays must have the same length")

    n=len(x)
    sum=0
    for i in range(n-1):
        sum+=x[i]*y[i+1]-x[i+1]*y[i] #! this is converted from the matlab code but it's only correct if the polygon is already closed

    return 0.5*sum

# TODO From FAZ_code/get_central.py
def get_central(x,y):
    '''
    Computes the central point of a polygon defined by its contour points.'''
    if len(x) != len(y):
        raise ValueError("Input arrays must have the same length")

    if (x[0] != x[-1]) or (y[0] != y[-1]):
        x = np.append(x, x[0])
        y = np.append(y, y[0])

    area = get_area(x, y)
    if area == 0:
        raise ValueError("Polygon area is zero; centroid is undefined.")
    
    cross = x[:-1] * y[1:] - x[1:] * y[:-1]

    sum_x = np.sum(cross * (x[:-1] + x[1:]))
    sum_y = np.sum(cross * (y[:-1] + y[1:]))

    Cx = sum_x / (6 * area)
    Cy = sum_y / (6 * area)

    return Cx, Cy

# Generate FAZ mask from image using auto_faz module
def generate_faz_mask(canvas: Canvas, batch: bool = False):
    change_status_to_waiting(canvas, status="🔴 Wait...Segmenting FAZ")

    grayscale_arr = auto_faz(filepath=canvas.filePath)

    # grayscale image from array
    grayscale_img = Image.fromarray(grayscale_arr.astype(np.uint8), mode='L')

    print("grayscale_arr type/shape:", type(grayscale_arr), grayscale_arr.shape, "grayscale_img type:", type(grayscale_img))

    # Store to main canvas
    canvas.faz_grayscale_arr = grayscale_arr
    canvas.faz_grayscale_img = grayscale_img

    if not batch:
        change_status_to_ready(canvas)

# TODO measure 1. contour in red 2. contour with 300 micron expansion in yellow 3. binary mask 4. double contours
def measure_faz(canvas: Canvas):
    print("Measuring FAZ metrics...")
    if not hasattr(canvas, 'current_save_folder'):
        return messagebox.showwarning("Empty save folder", "Save folder not specified")
    if not hasattr(canvas, 'faz_grayscale_arr'):
        return messagebox.showwarning("Empty FAZ mask", "FAZ mask required")
    if not hasattr(canvas, 'binary_image'):
        return messagebox.showwarning("No Binarised Image", "Please binarise an image before measuring FAZ.")
    # Get image size from canvas
    image_size_mm = canvas.image_size_var.get()
    
    # Get image dimensions
    img_height, img_width = canvas.fullImSizePix
    pix_to_mm = image_size_mm / img_height
    
    # Get faz mask
    grayscale_arr = canvas.faz_grayscale_arr.copy()
    
    # Calculate FD_300 (FAZ with 300 microns expanded)
    # 1. Get contour points
    # TODO replacement of matlab's bwboundaries
    # https://docs.opencv.org/4.x/d9/d8b/tutorial_py_contours_hierarchy.html
    # RETR_EXTERNAL: only capture outer-most, parent, non-nested contours
    # TODO CHAIN_APPROX_NONE all possible contour points, if we want to have drag adjustment, may consider CHAIN_APPROX_SIMPLE for lesser points
    contours, _ = cv2.findContours(grayscale_arr, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    print("contours found:", len(contours))

    if len(contours) == 0:
        return messagebox.showwarning("No FAZ contours found")
    
    # 1. Inner contour: Get the largest contour
    cnt = max(contours, key=cv2.contourArea)
    cnt = cnt.reshape(-1, 2)  # Shape: (N, 2)
    print("largest contour points:", len(cnt))

    # 2. Centroid: Calculate centroid
    Cx, Cy = get_central(cnt[:, 0], cnt[:, 1])

    # 3. Convert contour to polar coordinates relative to centroid
    cnt_x = cnt[:, 0] - Cx
    cnt_y = cnt[:, 1] - Cy
    cnt_theta = np.arctan2(cnt_y, cnt_x)
    cnt_rho = np.sqrt(cnt_x**2 + cnt_y**2)
    
    # 3. Outer Contour: Expand radius by 300 microns
    rad_size_pix = 0.3 / pix_to_mm 
    cnt_rho_expanded = cnt_rho + rad_size_pix
    
    # 4. Convert back to cartesian
    cnt_x_expanded = cnt_rho_expanded * np.cos(cnt_theta) + Cx
    cnt_y_expanded = cnt_rho_expanded * np.sin(cnt_theta) + Cy
    
    # 5. Inner/Outer Contours -> Inner/Outer Masks
    inner_mask = np.zeros((img_height, img_width), dtype=np.uint8)
    cv2.fillPoly(inner_mask, [cnt], 255)
    
    outer_pts = np.column_stack((cnt_x_expanded, cnt_y_expanded)).astype(np.int32) # x/y coords, int32 for large size
    outer_mask = np.zeros((img_height, img_width), dtype=np.uint8)
    cv2.fillPoly(outer_mask, [outer_pts], 255)
    
    # 6. Create ring mask: outer - inner
    # Both outer/inner masks have 0 and 255 values
    # ring_mask will be 255 in the ring area (outer - inner) and NAN elsewhere
    ring_mask = outer_mask - inner_mask
    ring_mask = ring_mask.astype(np.float32) # Convert to float for NaN assignment
    ring_mask[ring_mask == 0] = np.nan

    # 7. FD_300: Apply ring mask to original binary vessel image
    #! Use the original binary image (vessels), not the FAZ mask
    binary_image = canvas.binary_image.copy()
    mask_bin = (ring_mask / 255.0) * (binary_image / 255.0) # Binary mask within the ring (vessel=1)
    
    print("mask_bin unique values / nansum:", np.unique(mask_bin), np.nansum(mask_bin))
    n_pix = np.nansum(ring_mask) / 255  # Num of pixels within the ring (ring_mask has 255 where ring exists)
    print("n_pix:", n_pix)
    n_mask_bin = np.nansum(mask_bin)
    print("n_mask_bin:", n_mask_bin)
    FD_300 = n_mask_bin / n_pix * 100 if n_pix > 0 else 0
    print("FD_300:", FD_300) # The vessel density within the ring mask

    # Calculate region properties using OpenCV
    # Area
    area_pix = cv2.contourArea(cnt)
    area_mm2 = area_pix * (pix_to_mm ** 2)
    
    # Perimeter
    perimeter_pix = cv2.arcLength(cnt, closed=True)
    perimeter_mm = perimeter_pix * pix_to_mm
    
    # Fit ellipse to get major/minor axes (need at least 5 points)
    if len(cnt) >= 5:
        ellipse = cv2.fitEllipse(cnt)
        (center_x, center_y), (minor_axis, major_axis), angle = ellipse
        # cv2.fitEllipse returns (width, height) which is (minor, major)
        major_axis_mm = max(major_axis, minor_axis) * pix_to_mm
        minor_axis_mm = min(major_axis, minor_axis) * pix_to_mm
        
        # Calculate eccentricity from ellipse
        if major_axis > 0:
            eccentricity = np.sqrt(1 - (minor_axis_mm / major_axis_mm) ** 2)
        else:
            eccentricity = 0
    else:
        major_axis_mm = minor_axis_mm = 0
        eccentricity = 0
    
    # Circularity = 4pi * Area / Perimeter ^2
    circularity = (4 * np.pi * area_pix) / (perimeter_pix ** 2) if perimeter_pix > 0 else 0
    
    # Acircularity index = Perimeter / (2pi * sqrt(Area/pi))
    acircularity_index = perimeter_pix / (2 * np.pi * np.sqrt(area_pix / np.pi)) if area_pix > 0 else 0
    
    # Axis ratio
    axis_ratio = major_axis_mm / minor_axis_mm if minor_axis_mm > 0 else 0
    
    # Create statistics dictionary
    FAZ_stats = {
        'Area': round(area_mm2, 3),
        'Centroid_1': round(Cx * pix_to_mm, 3),  # X coordinate in mm
        'Centroid_2': round(Cy * pix_to_mm, 3),  # Y coordinate in mm
        'MajorAxisLength': round(major_axis_mm, 3),
        'MinorAxisLength': round(minor_axis_mm, 3),
        'Eccentricity': round(eccentricity, 2),
        'Circularity': round(circularity, 2),
        'Perimeter': round(perimeter_mm, 3),
        'acircularity_index': round(acircularity_index, 2),
        'axis_ratio': round(axis_ratio, 2),
        'FD_300': round(FD_300, 1),
        'name': canvas.FileLabelName,
    }
    
    # Save images/excel to local
    save_faz_stats(canvas, FAZ_stats)
    save_faz_images(canvas, cnt, outer_pts, Cx, Cy)

def save_faz_stats(canvas, stats):
    os.makedirs(canvas.current_save_folder, exist_ok=True)
    
    faz_stats_file_path = os.path.join(canvas.current_save_folder, canvas.FileLabelName + '_' + datetime.datetime.now().strftime("%d-%b-%Y %H%M%S") + '.xlsx')
    pd.DataFrame([stats]).to_excel(faz_stats_file_path, 'FAZ metrics', index=False)

    print(f"Saved FAZ stats to {faz_stats_file_path}")

def save_faz_images(canvas, inner_contour, outer_contour, Cx, Cy):
    """Save FAZ visualization images"""
    os.makedirs(os.path.join(canvas.current_save_folder, 'images'), exist_ok=True)

    # save faz images
    print("Saving FAZ images...")
    faz_images_folder_path = os.path.join(canvas.current_save_folder, 'images')
    
    # Count current index of existing images
    curr_idx = len([f for f in os.listdir(faz_images_folder_path) if 'FAZ_Contour' in f])
    
    filename_base = canvas.FileLabelName if hasattr(canvas, 'FileLabelName') else 'image'
    
    # Get original image (image array)
    img_original= cv2.cvtColor(canvas.original_img.copy().astype(np.uint8), cv2.COLOR_GRAY2BGR)  # image array -> colour image
    img_contour_inner = img_original.copy()
    img_contour_outer = img_original.copy()
    img_contour_both = img_original.copy()

    # Get grayscale image (actual image)
    img_grayscale = canvas.faz_grayscale_img.copy()
    
    # 1. Inner contour only (red)
    cv2.drawContours(img_contour_inner, [inner_contour], -1, (0, 0, 255), 2) # contourIdx=-1 draw all contours
    cv2.imwrite(os.path.join(faz_images_folder_path, f'{filename_base}_FAZ_Contour_{curr_idx}.png'), img_contour_inner)
    
    # 2. Outer contour only (yellow)
    cv2.polylines(img_contour_outer, [outer_contour], True, (0, 255, 255), 2) # isClosed=True
    cv2.imwrite(os.path.join(faz_images_folder_path, f'{filename_base}_FAZ300_Contour_{curr_idx}.png'), img_contour_outer)
    
    # 3. Both contours with centroid as a crosshair
    cv2.drawContours(img_contour_both, [inner_contour], -1, (0, 0, 255), 2)
    cv2.polylines(img_contour_both, [outer_contour], True, (0, 255, 255), 2)
    cv2.drawMarker(img_contour_both, (int(Cx), int(Cy)), (0, 0, 255), cv2.MARKER_CROSS, 5)  # Red centroid marker
    cv2.imwrite(os.path.join(faz_images_folder_path, f'{filename_base}_FAZ_Contour_both_{curr_idx}.png'), img_contour_both)
    
    # 4. Binary mask
    img_grayscale.save(os.path.join(faz_images_folder_path, f'{filename_base}_FAZ_mask_{curr_idx}.png'))
    
    print(f"Saved FAZ images to {faz_images_folder_path}")


