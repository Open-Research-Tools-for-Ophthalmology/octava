import tkinter as tk
import typing
from typing import Optional, Any
from tkinter import filedialog, messagebox, ttk, StringVar, DoubleVar
from PIL import Image, ImageTk
import numpy as np
import matplotlib
matplotlib.use('TkAgg')

from matplotlib.figure import Figure
from backend_ROI import ROIProcessor
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.widgets import RectangleSelector, EllipseSelector

# ------------- Tkinter/Matplotlib GUI -------------
class ROISelectorApp:
    def __init__(self, root, img = None): # CHANGE: img left as default (none) till final implementation, when we pull the OCTAVA image
        self.root = root
        self.root.title("ROI Selector")
        self.img = img
        self.ax = None
        self.rect_selector = None
        self.ellipse_selector = None
        self.use_mm = tk.BooleanVar()
        self.img_width_mm = DoubleVar(value=5.0)
        self.roi_shape = StringVar(value='Rectangle')
        self.label_roi_size = None

        # Keep references for cropping
        self.rect_info = None
        self.circle_info = None

        # --- UI Setup ---
        self.setup_controls()
        self.setup_canvas()

    def setup_controls(self):
        '''
        Creates a left pannel with the buttons
        Defines the buttons and assigns their respective functions
        Adds text labels
        '''
        control_frame = tk.Frame(self.root)
        control_frame.pack(side='left', fill='y')

        tk.Button(control_frame, text="Open Image", command=self.open_image).pack(fill='x', pady=2) # will remove later
        tk.Label(control_frame, text="ROI shape:").pack(anchor='w')
        ttk.Radiobutton(control_frame, text='Rectangle', variable=self.roi_shape, value='Rectangle', command=self.change_roi_shape).pack(anchor='w')
        ttk.Radiobutton(control_frame, text='Round', variable=self.roi_shape, value='Round', command=self.change_roi_shape).pack(anchor='w')
        tk.Button(control_frame, text="Start ROI", command=self.start_roi).pack(fill='x', pady=2)
        tk.Button(control_frame, text="Clear ROI", command=self.clear_roi).pack(fill='x', pady=2)
        tk.Button(control_frame, text="Done", command=self.done).pack(fill='x', pady=2)
        tk.Button(control_frame, text="Cancel", command=self.root.quit).pack(fill='x', pady=2)
        tk.Label(control_frame, text="ROI Size:").pack(anchor='w')

        self.label_roi_size = tk.Label(control_frame, text="N/A", bg='white')
        self.label_roi_size.pack(fill='x', pady=5)

        ttk.Checkbutton(control_frame, text="Show size in mm", variable=self.use_mm, command=self.update_roi_label).pack(anchor='w')

        tk.Label(control_frame, text="Img width (mm):").pack(anchor='w')
        tk.Entry(control_frame, textvariable=self.img_width_mm).pack(fill='x', pady=2)

    def setup_canvas(self):
        '''
        Creates the matplotlib canvas to work on the image's ROI
        Sets it at the right portion of the screen
        '''
        self.fig = Figure(figsize=(4, 4))
        self.ax = self.fig.add_subplot(111)
        self.ax.axis('off')

        # create matplotlib canvas in root
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        # set matplotlib canvas on right portion of screen
        self.canvas.get_tk_widget().pack(side='right', fill='both', expand=True)

        # CHANGE: uncomment this portion to allow automatic image loading
        # self.show_image()
        # self.clear_roi()

    # CHANGE: delete
    def open_image(self):
        filepath = filedialog.askopenfilename()
        if not filepath:
            return
        self.img_pil = Image.open(filepath).convert('L')
        self.img = np.array(self.img_pil)
        self.show_image()
        self.clear_roi()


    def show_image(self):
        ''' 
        Display OCTA image in the matplotlib canvas (RHS of screen)
        '''
        self.ax.clear()
        self.ax.imshow(self.img, cmap='gray')
        self.ax.axis('off')
        self.canvas.draw()

    def change_roi_shape(self):
        ''' 
        Swtich the type of ROI being drawn
        '''
        self.clear_roi()

    def start_roi(self):
        '''
        Allows user to draw ROI based on the current ROI selection (drawn from self.roi_shape)
        Sets the 
        '''
        self.clear_roi()
        if self.img is None:
            messagebox.showwarning("No image", "Please open an image first.")
            return

        # rectangle ROI
        if self.roi_shape.get() == 'Rectangle':
            self.rect_selector = RectangleSelector(
                self.ax, self.on_select_rect,
                useblit=True, button=[1],
                interactive=True
            )
            self.ellipse_selector = None

        # round ROI
        else:  
            self.ellipse_selector = EllipseSelector(
                self.ax, self.on_select_ellipse,
                useblit=True, button=[1],
                interactive=True
            )
            self.rect_selector = None
        self.canvas.draw()

    def clear_roi(self):
        '''
        Sets currently active matplotlib's figure selector off
        Cleans the previous ROI coordinates
        '''
        if self.rect_selector:
            self.rect_selector.set_active(False)
            self.rect_selector = None
        if self.ellipse_selector:
            self.ellipse_selector.set_active(False)
            self.ellipse_selector = None
        self.rect_info = None
        self.circle_info = None
        self.label_roi_size.config(text="N/A")
        self.canvas.draw()

    def on_select_rect(self, eclick, erelease):
        '''
        Handles rectangle selection event.

        Updates the rectangle info (x, y, width, height) from the 
        current RectangleSelector and refreshes the ROI label.

        Just updates info for LABEL, doesn't draw new rectangles
        '''
        # Won't draw anything here: selector itself is interactive
        if self.rect_selector:
            x1, x2, y1, y2 = map(int, self.rect_selector.extents)
            self.rect_info = {
                "x": min(x1, x2),
                "y": min(y1, y2),
                "width": abs(x2 - x1),
                "height": abs(y2 - y1)
            }
            self.update_roi_label()
            self.canvas.draw()

    def on_select_ellipse(self, eclick, erelease):
        '''
        Handles circle selection event.

        Updates the rectangle info (cx, cy, r) from the 
        current EllipseSelector and refreshes the ROI label.

        Just updates info for LABEL, doesn't draw new circles
        '''
        if self.ellipse_selector:
            xc, yc = self.ellipse_selector.center
            w, h = self.ellipse_selector.width, self.ellipse_selector.height
            r = int(round((w + h) / 4))
            self.circle_info = {
                "cx": int(xc),
                "cy": int(yc),
                "r": r
            }
            self.update_roi_label()
            self.canvas.draw()

    def update_roi_label(self):
        ''' 
        Reflects the ROI dimensions for every new selection
        '''
        if self.roi_shape.get() == 'Rectangle':
            info = self.rect_info
            if not info:
                self.label_roi_size.config(text="N/A")
                return
            width, height = info["width"], info["height"]
            if self.use_mm.get() and self.img is not None and self.img_width_mm.get() != 0:
                px_per_mm = self.img.shape[1] / self.img_width_mm.get()
                width_mm = width / px_per_mm
                height_mm = height / px_per_mm
                text = f"x = {width_mm:.2f} mm\ny = {height_mm:.2f} mm"
            else:
                text = f"x = {width} px\ny = {height} px"
        else:
            info = self.circle_info
            if not info:
                self.label_roi_size.config(text="N/A")
                return
            r = info["r"]
            if self.use_mm.get() and self.img is not None and self.img_width_mm.get() != 0:
                px_per_mm = self.img.shape[1] / self.img_width_mm.get()
                r_mm = r / px_per_mm
                text = f"r = {r_mm:.2f} mm"
            else:
                text = f"r = {r} px"
        self.label_roi_size.config(text=text)

    def done(self) -> Optional[dict[str, Any]]:
        '''
        Extracts the final coordinaets of the ROI
        Crops original image to reflect new ROI
        CHANGE: Returns the ROIProcessor dictionary containing the following 
            - 'cropped_image': np.ndarray of ROI sub-image
            - 'fullImSizePix': int (width or diameter in px, if resize True)
            - 'FAZ_ctr': ROI centroid (tuple, in px)
            - 'imgShape': 'rect' or 'round'
        '''
        if self.img is None:
            messagebox.showwarning("Incomplete", "No image loaded.")
            return

        roi_shape = 'rect' if self.roi_shape.get() == 'Rectangle' else 'round'

        # Rectangle
        if roi_shape == 'rect' and self.rect_selector:
            x1, x2, y1, y2 = map(int, self.rect_selector.extents)
            rect = {
                "x": min(x1, x2),
                "y": min(y1, y2),
                "width": abs(x2 - x1),
                "height": abs(y2 - y1)
            }
            self.rect_info = rect

        # Elipse
        elif roi_shape == 'round' and self.ellipse_selector:
            xc, yc = self.ellipse_selector.center
            w, h = self.ellipse_selector.width, self.ellipse_selector.height
            r = int(round((w + h) / 4))
            circle = {
                "cx": int(xc),
                "cy": int(yc),
                "r": r
            }
            self.circle_info = circle

        rect = self.rect_info if roi_shape == 'rect' else None
        circle = self.circle_info if roi_shape == 'round' else None

        if (roi_shape == 'rect' and not rect) or (roi_shape == 'round' and not circle):
            messagebox.showwarning("Incomplete", "No ROI selected.")
            return

        processor = ROIProcessor(self.img, roi_shape, rect, circle)
        result = processor.crop_roi(resize=True)
        # return result?
        cropped_image = result['cropped_image']
        # return cropped_image?
        # depends on what things from the result dictinary we'd like to keep. Not sure yet


        # CHANGE: delete this bc we don't want to show, we just return the result of the cropped image
        # Unless we do want to display a preview and then add a button that says cancel or save changes 
        # to confirm selection

        # Show the cropped ROI
        new_win = tk.Toplevel(self.root)
        tk.Label(new_win, text="Selected ROI:").pack()
        # Avoid showing empty images
        disp_img = cropped_image
        if disp_img is None or disp_img.size == 0:
            tk.Label(new_win, text="Empty ROI!").pack()
        else:
            out_img = Image.fromarray(disp_img)
            out_img = out_img.convert('L')
            imgtk = ImageTk.PhotoImage(out_img.resize((200, 200)))
            tk.Label(new_win, image=imgtk).pack()
            new_win.imgtk = imgtk  # avoid GC

if __name__ == '__main__':
    root = tk.Tk()
    app = ROISelectorApp(root)
    root.mainloop()