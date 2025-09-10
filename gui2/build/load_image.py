# image_loader.py
from tkinter import filedialog
from PIL import Image, ImageTk
import os

def load_image(canvas, x, y, text_x, text_y):
    """
    Ask the user to pick an image, display it on the given canvas,
    and show the filename above the given position.
    """
    file_path = filedialog.askopenfilename(
        title="Select an image",
        filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.tiff")]
    )

    if not file_path:
        return None  # user cancelled

    # Load and resize image
    img = Image.open(file_path).resize((200, 200))
    img_tk = ImageTk.PhotoImage(img)

    # Add the image to the canvas
    img_id = canvas.create_image(x, y, image=img_tk)

    # Show filename
    filename = os.path.basename(file_path)
    text_id = canvas.create_text(
        text_x, text_y,
        text=filename,
        fill="#333333",
        font=("Roboto", 12 * -1),
    )

    # Keep references so image/text don’t vanish
    canvas.image_ref = img_tk
    canvas.image_id = img_id
    canvas.filename_text_id = text_id

    return file_path