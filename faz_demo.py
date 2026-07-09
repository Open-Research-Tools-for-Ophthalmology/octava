import numpy as np
import os
import tkinter as tk
from tkinter import DoubleVar, Canvas, StringVar, filedialog, messagebox, ttk, Spinbox, Button, IntVar, Entry
import cv2
import PIL.Image as Image
import pandas as pd

class FAZHelper:
    # From FAZ_code/get_area.py
    @staticmethod
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

    # From FAZ_code/get_central.py
    @staticmethod
    def get_central(x,y):
        '''
        Computes the central point of a polygon defined by its contour points.'''
        if len(x) != len(y):
            raise ValueError("Input arrays must have the same length")

        if (x[0] != x[-1]) or (y[0] != y[-1]):
            x = np.append(x, x[0])
            y = np.append(y, y[0])

        area = FAZHelper.get_area(x, y)
        if area == 0:
            raise ValueError("Polygon area is zero; centroid is undefined.")
        
        cross = x[:-1] * y[1:] - x[1:] * y[:-1]

        sum_x = np.sum(cross * (x[:-1] + x[1:]))
        sum_y = np.sum(cross * (y[:-1] + y[1:]))

        Cx = sum_x / (6 * area)
        Cy = sum_y / (6 * area)

        return Cx, Cy

class FAZAnalyzer:
    def __init__(self, root):
        self.root = root
        self.root.title("FAZ Analysis")
        self.root.geometry("800x600")  # Larger window
        self.root.minsize(800, 600)  # Set minimum size
        self.root.configure(bg='#f0f0f0')  # Light gray background
        self.root.canvas = Canvas(
            self.root,
            bg = '#f0f0f0',
            width = 1210,
            height = 750,
            bd = 0,
            highlightthickness = 0,
            relief = "ridge"
        )
        self.root.canvas.place(x = 0, y = 0)

        # Pack the UIs: image size selector, folder selector
        self.root.image_size_var = DoubleVar(value=3.00)  # Variable for Image Size Spinbox
        self.root.image_res_var = IntVar(value=1000)  # Variable for image resolution (0: 3x3mm, 1: 6x6mm, etc.)
        self.root.folder_faz_var = StringVar(value="")  # Variable for FAZ folder path
        self.root.folder_bin_var = StringVar(value="")  # Variable for binary folder path
        
        # Image size selector
        self.root.canvas.create_text(
            200.0,
            50.0,
            anchor="nw",
            text="Image Size (mm/px):",
            font=("Roboto", 14 * -1)
        )
        image_size_spinbox = Spinbox(
            from_=0.50,
            to=10.00,
            increment=0.50,
            width=4,
            textvariable=self.root.image_size_var,
            font=("Roboto", 14 * -1),
            bd=0.5,                  # removes the border thickness
            highlightthickness=0,  # removes the focus highlight border
        )
        image_size_spinbox.place(
            x=400.0,
            y=50.0
        )

        image_res_input = Entry(
            textvariable=self.root.image_res_var,
            font=("Roboto", 12 * -1),
            bd=0.5,
            highlightthickness=0,
            width=10
        )
        image_res_input.place(
            x=500.0,
            y=50.0
        )

        # Load FAZ folder button
        load_btn_faz = Button(self.root, text="Select FAZ Folder", 
                            command=lambda: self.select_folder_path(y=200, name="folder_faz_var"), font=('Arial', 12, 'bold'),
                            bg='#3498db', fg='white', relief='raised', bd=2,
                            padx=25, pady=10)
        load_btn_faz.place(x=300.0, y=100.0)

        # Load start button
        start_btn = Button(self.root, text="Start",
                            command=lambda: self.start_faz(self.root.canvas), font=('Arial', 12, 'bold'),
                            bg='#2ecc71', fg='white', relief='raised', bd=2,
                            padx=25, pady=10)
        start_btn.place(x=350.0, y=300.0)

    def select_folder_path(self, y: int, name: str):
        folder_path = filedialog.askdirectory()
        if not folder_path:
            return
        getattr(self.root, name).set(folder_path)
        return self.root.canvas.create_text(
            200, y,
            text=f"Selected folder: {folder_path}",
            fill="#333333",
            font=("Roboto", 14 * -1),
            anchor="w",
        )

    def start_faz(self, canvas: Canvas):
        faz_data = []
        for filename in os.listdir(self.root.folder_faz_var.get()):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.tif', '.bmp')):
                img_path = os.path.join(self.root.folder_faz_var.get(), filename)
                # Load image and process
                img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
                faz_stats = measure_faz(self, img, filename)
                faz_data.append(faz_stats)

        # Save images/excel to local
        faz_df = pd.DataFrame(faz_data)
        file_path = os.path.join(self.root.folder_faz_var.get(), "FAZ summary.xlsx")
        with pd.ExcelWriter(file_path, mode='w', engine="openpyxl") as writer:
            faz_df.to_excel(writer, sheet_name="FAZ Metrics", index=False)
        
        messagebox.showinfo("FAZ Analysis Complete", f"FAZ metrics have been saved to {file_path}.")

# measure 1. contour in red 2. contour with 300 micron expansion in yellow 3. binary mask 4. double contours
def measure_faz(self, img, filename):
    """Measure FAZ morphology and FD_300, then export the metrics and validation images."""
    print("Measuring FAZ metrics...")

    # Get image size from canvas
    image_size_mm = self.root.image_size_var.get()
    
    # Get image dimensions
    img_height = self.root.image_res_var.get()
    pix_to_mm = image_size_mm / img_height
    
    # Get faz mask
    grayscale_arr = img.copy()
    
    # Calculate FD_300 (FAZ with 300 microns expanded)
    # 1. Get contour points
    # replacement of matlab's bwboundaries
    # https://docs.opencv.org/4.x/d9/d8b/tutorial_py_contours_hierarchy.html
    # RETR_EXTERNAL: only capture outer-most, parent, non-nested contours
    # CHAIN_APPROX_NONE all possible contour points, if we want to have drag adjustment, may consider CHAIN_APPROX_SIMPLE for lesser points
    contours, _ = cv2.findContours(grayscale_arr, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    print("contours found:", len(contours))

    if len(contours) == 0:
        return messagebox.showwarning("No FAZ contours found", "Failed to find any FAZ contours.")
    
    # 1. Inner contour: Get the largest contour
    cnt = max(contours, key=cv2.contourArea)
    cnt = cnt.reshape(-1, 2)  # Shape: (N, 2)
    print("largest contour points:", len(cnt))

    # 2. Centroid: Calculate centroid
    Cx, Cy = FAZHelper.get_central(cnt[:, 0], cnt[:, 1])
    FAZ_ctr = np.array([Cy, Cx])

    # 3. Convert contour to polar coordinates relative to centroid
    cnt_x = cnt[:, 0] - Cx
    cnt_y = cnt[:, 1] - Cy
    cnt_theta = np.arctan2(cnt_y, cnt_x)
    cnt_rho = np.sqrt(cnt_x**2 + cnt_y**2)
    
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
    return {
        'name': filename,
        'Area': round(area_mm2, 3),
        'Centroid_1': round(Cx * pix_to_mm, 3),  # X coordinate in mm
        'Centroid_2': round(Cy * pix_to_mm, 3),  # Y coordinate in mm
        'MajorAxisLength': round(major_axis_mm, 3),
        'MinorAxisLength': round(minor_axis_mm, 3),
        'Eccentricity': round(eccentricity, 2),
        'Circularity': round(circularity, 2),
        'Perimeter': round(perimeter_mm, 3),
        'acircularity_index': round(acircularity_index, 2),
        'axis_ratio': round(axis_ratio, 2)
    }

if __name__ == "__main__":
    root = tk.Tk()
    app = FAZAnalyzer(root)
    root.mainloop()