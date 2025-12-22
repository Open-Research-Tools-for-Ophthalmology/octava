from PIL import Image, ImageTk, UnidentifiedImageError

# Resize image to specified size, by default 200x200
def resize_image(image, size = (200, 200)):
  return image.resize(size, Image.LANCZOS)