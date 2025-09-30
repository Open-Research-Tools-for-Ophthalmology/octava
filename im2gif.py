import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from PIL import Image, ImageSequence, ImageChops
import numpy as np
import os

def crop_borders(im):
    # Crop border pixels that match the corner pixel color
    bg = im.getpixel((0, 0))
    bg_layer = Image.new(im.mode, im.size, bg)
    diff = ImageChops.difference(im, bg_layer)
    bbox = diff.getbbox()
    return im.crop(bbox) if bbox else im

def im2gif(infile, outfile=None, nocrop=False, nodither=False, ncolors=256, loops=65535, delay=1/15):
    if not outfile:
        base, _ = os.path.splitext(infile)
        outfile = base + '.gif'

    # Open image and extract frames
    im = Image.open(infile)
    frames = []
    for frame in ImageSequence.Iterator(im):
        frame = frame.convert("RGBA")
        if not nocrop:
            frame = crop_borders(frame)
        frames.append(frame)

    # Quantize frames
    # Use dithering based on option
    dither = Image.FLOYDSTEINBERG if not nodither else Image.NONE
    quantized_frames = []
    for f in frames:
        qf = f.quantize(colors=ncolors, method=Image.MEDIANCUT, dither=dither)
        quantized_frames.append(qf)

    # Convert delay from seconds to hundredths of seconds (GIF standard)
    duration = int(delay * 1000)  # PIL expects milliseconds

    # Save frames as GIF
    quantized_frames[0].save(
        outfile,
        save_all=True,
        append_images=quantized_frames[1:],
        loop=loops,
        duration=duration,
        disposal=2
    )

    messagebox.showinfo("Success", f"Animated GIF saved:\n{outfile}")

def ask_options():
    options = {}

    nocrop = messagebox.askyesno("Crop Borders", "Do you want to crop borders?\nClick 'No' to disable cropping.")
    options['nocrop'] = not nocrop

    nodither = messagebox.askyesno("Dithering", "Do you want to disable dithering?")
    options['nodither'] = nodither

    ncolors = simpledialog.askinteger("Colors", "Max number of colors (1-256):", initialvalue=256, minvalue=1, maxvalue=256)
    options['ncolors'] = ncolors if ncolors else 256

    loops = simpledialog.askinteger("Loops", "Number of animation loops (0 = infinite):", initialvalue=65535, minvalue=0)
    options['loops'] = loops if loops is not None else 65535

    delay = simpledialog.askfloat("Delay", "Delay between frames in seconds:", initialvalue=1/15, minvalue=0)
    options['delay'] = delay if delay else 1/15

    return options

def select_files_and_convert():
    infile = filedialog.askopenfilename(
        title="Select multi-frame image (e.g. TIFF)",
        filetypes=[("Image files", "*.tif *.tiff *.gif *.png *.bmp")]
    )
    if not infile:
        return

    outfile = filedialog.asksaveasfilename(
        title="Save Animated GIF as",
        defaultextension=".gif",
        filetypes=[("GIF files", "*.gif")]
    )
    if not outfile:
        return

    opts = ask_options()

    im2gif(
        infile,
        outfile,
        nocrop=opts['nocrop'],
        nodither=opts['nodither'],
        ncolors=opts['ncolors'],
        loops=opts['loops'],
        delay=opts['delay']
    )

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Multi-frame Image to Animated GIF")
    root.geometry("350x120")
    root.resizable(False, False)

    btn = tk.Button(root, text="Select Image and Convert to GIF", command=select_files_and_convert)
    btn.pack(expand=True, pady=30)

    root.mainloop()