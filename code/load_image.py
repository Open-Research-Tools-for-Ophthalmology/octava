'''
This funtion allows the user to load a single OCT MIP into the app
'''
import os
from tkinter import Label,filedialog, messagebox
from PIL import Image, ImageTk
import tkinter as tk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class ImageApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Testing MIP Loader")
        self.root.geometry("800x600")
        
        # Label to show filename
        self.file_label = tk.Label(root, text="No file selected", font=('Arial', 14))
        self.file_label.pack(pady=10)

        # Button to load image
        self.load_button = tk.Button(root, text="Select Image File", command=self.select_file)
        self.load_button.pack(pady=10)

        # Frame for the image plot
        self.plot_frame = tk.Frame(root)
        self.plot_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = None
        self.input_image = None

    def select_file(self):
        file_path = filedialog.askopenfilename(title="Select MIP", filetypes=[("Image files", "*.*")])
        if not file_path:
            messagebox.showwarning("No file", "You did not choose an image file")
            return

        # Update file label
        file_name = os.path.basename(file_path) # Get the file name without path
        name_without_ext = os.path.splitext(file_name)[0] # Remove the file extension
        self.file_label.config(text=name_without_ext) # Update the label with the file name

        # Load the image and extract first channel
        try:
            image = Image.open(file_path)
            image_np = np.array(image)

            if image_np.ndim == 3:
                first_channel = image_np[:, :, 0]
            else:
                first_channel = image_np  # grayscale

            self.input_image = first_channel.astype(np.float64)

            self.display_image()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {e}")

    def display_image(self):
        # Remove previous canvas if exists
        for widget in self.plot_frame.winfo_children():
            widget.destroy()

        fig, ax = plt.subplots() # Create a new figure and axis
        ax.imshow(self.input_image, cmap='gray')
        ax.axis('off')

        self.canvas = FigureCanvasTkAgg(fig, master=self.plot_frame) # Create a new canvas
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True) # Pack the canvas into the frame

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageApp(root)
    root.mainloop()