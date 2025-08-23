''' 
This is a script to test the skeletonization once I have a sample binarized image
This is using a GUI just so I can upload the image, skeletonize and observe all in the
same place
However, I might only use ipynbs to test and call it a day!
'''


import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from skimage.morphology import skeletonize, dilation, square

class SkeletonGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Skeletonization Tester")
        self.img = None
        self.skel_img = None

        self.setup_controls()
        self.setup_canvas()

    def setup_controls(self):
        control_frame = tk.Frame(self.root)
        control_frame.pack(side='left', fill='y')

        tk.Button(control_frame, text="Open Image", command=self.open_image).pack(fill='x', pady=2)
        tk.Button(control_frame, text="Skeletonize", command=self.run_skeletonize).pack(fill='x', pady=2)
        tk.Button(control_frame, text="Quit", command=self.root.quit).pack(fill='x', pady=(10, 2))

    def setup_canvas(self):
        self.fig = Figure(figsize=(4, 4))
        self.ax = self.fig.add_subplot(111)
        self.ax.axis('off')
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack(side='right', fill='both', expand=True)

    def open_image(self):
        filepath = filedialog.askopenfilename()
        if not filepath:
            return
        img_pil = Image.open(filepath).convert('L')
        self.img = np.array(img_pil)
        self.skel_img = None
        self.show_image()

    def show_image(self):
        self.ax.clear()
        if self.img is not None:
            self.ax.imshow(self.img, cmap='gray')
            self.ax.axis('off')
        self.canvas.draw()

    def run_skeletonize(self):
        if self.img is None:
            messagebox.showwarning("No image", "Please open an image first.")
            return
        # Ensure binary image for skeletonization
        img_bin = self.img > np.mean(self.img)
        skel = skeletonize(img_bin)
        skel = dilation(skel, square(3))  # thicken to make visible
        self.ax.clear()
        self.ax.imshow(self.img, cmap='gray')
        self.ax.imshow(skel, cmap='hot', alpha=0.6)
        self.ax.axis('off')
        self.canvas.draw()

if __name__ == '__main__':
    root = tk.Tk()
    app = SkeletonGUI(root)
    root.mainloop()