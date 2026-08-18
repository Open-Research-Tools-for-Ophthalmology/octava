from PIL import Image, ImageTk, UnidentifiedImageError

MINIMUM_IMAGE_PIXELS = 0

# Resize image to specified size, by default 200x200
def resize_image(image, size = (200, 200)):
  """Resize a PIL image to the requested pixel dimensions using Lanczos resampling."""
  return image.resize(size, Image.LANCZOS)

# Update: 20260504, image > 3mm will be 2000px and <= 3mm will be 1000px
# Update: 20260818, image is always scaled proportionally to 3mm/1000px
def size_to_pixels(size_value: float) -> int:
  """
  Convert the image size to pixels

  Mappings: 
  size_value * (1000/3) = pixels

  Returns:
  int: pixel size

  """

  # if bad input
  if size_value is None:
    return MINIMUM_IMAGE_PIXELS
  
  try: 
    size_value = float(size_value)
  except (TypeError, ValueError):
    return MINIMUM_IMAGE_PIXELS
  
  pixels = size_value * (1000 / 3)

  return round(pixels)
