import tkinter as tk
from tkinter import Toplevel, messagebox
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class ROISelectorDialog:
    def __init__(self, master, img_np):
        self.result = None # This will store the ROI image
        self.roi = None
        self.roi_artist = None
        self.drag_start = None

        # Modal dialog setup
        self.top = Toplevel(master)
        self.top.transient(master)
        self.top.grab_set()
        self.top.title("Select ROI")        

        self.img = img_np.copy() # Operate on a copy!
        self.img_shape = self.img.shape
        self.roi_type = tk.StringVar(value='rectangle')

        # ROI type selection
        roi_frame = tk.Frame(self.top)
        roi_frame.pack()
        tk.Label(roi_frame, text="ROI type:").pack(side=tk.LEFT)
        for typ in ["rectangle", "circle"]:
            tk.Radiobutton(roi_frame, text=typ.capitalize(), variable=self.roi_type, value=typ).pack(side=tk.LEFT)

        # Matplotlib figure for image display
        self.fig = Figure(figsize=(5,4))
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, self.top)
        self.canvas.get_tk_widget().pack()
        self.ax.imshow(self.img, cmap='gray')
        self.ax.axis('off')
        self.fig.tight_layout()
        self.canvas.draw()

        self.canvas.mpl_connect('button_press_event', self.on_mouse_press)
        self.canvas.mpl_connect('button_release_event', self.on_mouse_release)
        self.canvas.mpl_connect('motion_notify_event', self.on_mouse_drag)

        # Control buttons
        btn_frame = tk.Frame(self.top)
        btn_frame.pack(pady=6)
        tk.Button(btn_frame, text="Clear", command=self.clear_roi).pack(side=tk.LEFT)
        tk.Button(btn_frame, text="Done", command=self.on_done).pack(side=tk.LEFT)
        tk.Button(btn_frame, text="Cancel", command=self.on_cancel).pack(side=tk.LEFT)

    ### --- ROI Drawing handlers (same logic as before) ---
    def on_mouse_press(self, event):
        if self.img is None or not event.inaxes: return
        self.drag_start = (event.xdata, event.ydata)

    def on_mouse_drag(self, event):
        if self.drag_start and self.img is not None and event.inaxes:
            x0, y0 = self.drag_start
            x1, y1 = event.xdata, event.ydata
            t = self.roi_type.get()
            if self.roi_artist:
                self.roi_artist.remove()
            if t == "rectangle":
                from matplotlib.patches import Rectangle
                w, h = x1-x0, y1-y0
                self.roi_artist = self.ax.add_patch(Rectangle((x0, y0), w, h, fill=False, color='r'))
            elif t == "circle":
                from matplotlib.patches import Circle
                r = ((x1-x0)**2+(y1-y0)**2)**0.5
                self.roi_artist = self.ax.add_patch(Circle((x0, y0), r, fill=False, color='b'))
            self.canvas.draw()

    def on_mouse_release(self, event):
        if self.drag_start and self.img is not None and event.inaxes:
            x0, y0 = self.drag_start
            x1, y1 = event.xdata, event.ydata
            t = self.roi_type.get()
            if t == "rectangle":
                roi = {"type":"rectangle", "x":int(round(x0)), "y":int(round(y0)),
                       "width":int(round(x1-x0)), "height":int(round(y1-y0))}
            elif t == "circle":
                r = ((x1-x0)**2+(y1-y0)**2)**0.5
                roi = {"type":"circle", "cx":int(round(x0)), "cy":int(round(y0)), "radius":int(round(r))}
            self.roi = roi
        self.drag_start = None

    def clear_roi(self):
        self.roi = None
        if self.roi_artist:
            self.roi_artist.remove()
            self.roi_artist = None
        self.ax.clear()
        self.ax.imshow(self.img, cmap='gray')
        self.ax.axis('off')
        self.canvas.draw()

    ### --- Finish/cancel logic ---

    def on_done(self):
        if not self.roi:
            messagebox.showwarning("No ROI", "Please select/draw an ROI first.", parent=self.top)
            return
        # Crop image based on ROI
        if self.roi["type"] == "rectangle":
            x, y, w, h = self.roi["x"], self.roi["y"], self.roi["width"], self.roi["height"]
            # Handle negative width/height (dragged from bottom-right to top-left)
            if w < 0: x, w = x + w, -w
            if h < 0: y, h = y + h, -h
            # Clamp to bounds
            x, y = max(0, x), max(0, y)
            x2 = min(self.img.shape[1], x + w)
            y2 = min(self.img.shape[0], y + h)
            self.result = self.img[y:y2, x:x2]
        elif self.roi["type"] == "circle":
            cx, cy, r = self.roi["cx"], self.roi["cy"], self.roi["radius"]
            ygrid, xgrid = np.ogrid[:self.img.shape[0], :self.img.shape[1]]
            mask = (xgrid - cx)**2 + (ygrid - cy)**2 <= r**2
            masked_img = self.img.copy()
            masked_img[~mask] = 0
            # Crop tight bounding box
            x1, x2 = max(0, cx-r), min(self.img.shape[1], cx+r)
            y1, y2 = max(0, cy-r), min(self.img.shape[0], cy+r)
            self.result = masked_img[int(y1):int(y2), int(x1):int(x2)]
        self.top.destroy()

    def on_cancel(self):
        self.result = None
        self.top.destroy()

def select_roi_dialog(master, img_np):
    dialog = ROISelectorDialog(master, img_np)
    dialog.top.wait_window()
    return dialog.result