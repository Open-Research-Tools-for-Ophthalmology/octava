import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import tkinter as tk
from tkinter import filedialog, Menu
import os
import re
import shutil
import webbrowser
from pathlib import Path
from PIL import ImageGrab

# Utility functions
def clean_filename(filename):
    return re.sub(r'[*?"<>|:/\\]+', '-', filename)

def open_folder(path):
    if os.name == 'nt':  # Windows
        os.startfile(path)
    else:
        webbrowser.open(path)

def copy_to_clipboard(fig):
    # Grab the figure as image and copy to clipboard (Windows only)
    fig.canvas.draw()
    x0 = fig.bbox.x0
    y0 = fig.bbox.y0
    x1 = fig.bbox.x1
    y1 = fig.bbox.y1
    img = ImageGrab.grab(bbox=(x0, y0, x1, y1))
    img.show()  # Temporary display, since true clipboard copy requires pyperclip or win32clipboard

# Interactive export function
def interactive_export(fig, root):
    default_name = clean_filename(fig.get_label() or 'figure')
    default_folder = os.getcwd()
    formats = ['pdf','eps','svg','png','jpg','tif','gif','bmp']
    formats_clip = ['clipboard:image']

    all_formats = formats + formats_clip

    filetypes = [(f"{fmt.upper()} file", f"*.{fmt}") for fmt in formats]
    filetypes.append(("Clipboard image", "*.*"))

    filename = filedialog.asksaveasfilename(
        title="Save figure export as",
        initialfile=default_name,
        initialdir=default_folder,
        filetypes=filetypes
    )
    if not filename:
        return  # User canceled

    ext = Path(filename).suffix[1:].lower()
    if ext == "" and "clipboard" in filename:
        copy_to_clipboard(fig)
    else:
        fig.savefig(filename)
        folder = str(Path(filename).parent)
        print(f"Figure saved as {filename}")
        open_folder(folder)

# Add toolbar button
def add_toolbar_button(fig, canvas, root):
    toolbar = NavigationToolbar2Tk(canvas, root)
    toolbar.update()
    
    button = tk.Button(root, text="Export Figure", command=lambda: interactive_export(fig, root))
    button.pack(side=tk.TOP, fill=tk.X)

# Add menubar menu
def add_menubar_menu(fig, root):
    menubar = Menu(root)
    file_menu = Menu(menubar, tearoff=0)
    file_menu.add_command(label="Export Figure", command=lambda: interactive_export(fig, root))
    menubar.add_cascade(label="Export", menu=file_menu)
    root.config(menu=menubar)

# Add context menu
def add_context_menu(fig, canvas, root):
    context_menu = Menu(root, tearoff=0)
    context_menu.add_command(label="Export Figure", command=lambda: interactive_export(fig, root))
    
    def show_context_menu(event):
        context_menu.tk_popup(event.x_root, event.y_root)

    canvas.get_tk_widget().bind("<Button-3>", show_context_menu)  # Right-click

# Example usage
def main():
    root = tk.Tk()
    root.title("Exportable Figure Demo")

    fig, ax = plt.subplots()
    ax.plot([1,2,3],[4,5,6])
    fig.set_label("DemoFigure")

    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=1)

    # Add all interactive export functions
    add_toolbar_button(fig, canvas, root)
    add_menubar_menu(fig, root)
    add_context_menu(fig, canvas, root)

    tk.mainloop()

if __name__ == "__main__":
    main()
