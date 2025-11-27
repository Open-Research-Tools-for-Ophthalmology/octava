import tkinter as tk
from skimage.io import imread
from skimage.transform import resize

class ImageResizeAPP:
    def __init__(self, root, image=None):
        self.root = root
        self.root.title("New Image Size")
        self.img = image
        self.img_y = image.shape[0]  # rows (height)
        self.img_x = image.shape[1]  # columns (width)
        # Output variable
        self.resized_img = None
        self.setup_controls()
        
    def setup_controls(self):
        control_frame = tk.Frame(self.root)
        control_frame.pack(fill='y', padx=10, pady=10)
        
        tk.Label(control_frame, text="Width (pixels):").pack(anchor='w')
        self.new_w = tk.Entry(control_frame)
        self.new_w.insert(0, str(self.img_x))
        self.new_w.pack(fill='x', pady=2)
        
        tk.Label(control_frame, text="Height (pixels):").pack(anchor='w')
        self.new_h = tk.Entry(control_frame)
        self.new_h.insert(0, str(self.img_y))
        self.new_h.pack(fill='x', pady=2)

        button_frame = tk.Frame(control_frame)
        button_frame.pack(pady=5)

        tk.Button(button_frame, text="OK", command=self.resize_image, width=8).pack(side='left', padx=5)
        tk.Button(button_frame, text="Cancel", command=self.exit, width=8).pack(side='left', padx=5)

    def resize_image(self):
        try:
            x = int(self.new_w.get())
            y = int(self.new_h.get())
            self.resized_img = resize(
                self.img, (y, x), order=0,
                preserve_range=True, anti_aliasing=False
            ).astype(self.img.dtype)
            print("Image resized to:", self.resized_img.shape)
            self.exit()
        except Exception as e:
            print("Error resizing image:", e)

    def exit(self):
        self.root.destroy()
        # Optionally return self.resized_img if integrating elsewhere

if __name__ == '__main__':
    root = tk.Tk()
    sample_path = "./assets/MIPs/10301.bmp"
    sample_img = imread(sample_path)
    app = ImageResizeAPP(root, sample_img)
    root.mainloop()
    # The resized image is stored in app.resized_img after resizing