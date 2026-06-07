from PIL import Image, ImageTk, UnidentifiedImageError

MINIMUM_IMAGE_PIXELS = 1000

# Resize image to specified size, by default 200x200
def resize_image(image, size = (200, 200)):
  """Resize a PIL image to the requested pixel dimensions using Lanczos resampling."""
  return image.resize(size, Image.LANCZOS)

# Update: 20260504, image > 3mm will be 2000px and <= 3mm will be 1000px
def size_to_pixels(size_value: float) -> int:
  """
  Convert the image size to pixels

  Mappings: 
  <= 3.0mm  -> 1000
  > 3.0mm   -> 2000

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
  
  if size_value <= 3.0:
    pixels = 1000
  else:
    pixels = 2000
  
  return round(pixels)
