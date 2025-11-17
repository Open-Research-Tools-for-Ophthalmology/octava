from PIL import Image, ImageTk, UnidentifiedImageError

def resize_image(image):
  return image.resize((200, 200), Image.LANCZOS)
