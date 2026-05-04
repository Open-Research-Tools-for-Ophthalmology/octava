from PIL import Image, ImageTk, UnidentifiedImageError

MINIMUM_IMAGE_PIXELS = 1000

# Resize image to specified size, by default 200x200
def resize_image(image, size = (200, 200)):
  """Resize a PIL image to the requested pixel dimensions using Lanczos resampling."""
  return image.resize(size, Image.LANCZOS)

def size_to_pixels(size_value: float) -> int:
  """
  Convert the image size to pixels

  Mappings: 
  3.0 -> 1000
  5.5 -> 1833
  6.0 -> 2000
  8.0 -> 2667

  All other values scale proportionally according to:
  3.0 -> 1000

  Returns:
  int: pixel size (rounded)

  """

  canonical_map = {
    3.0: 1000,
    6.0: 2000,
    8.0: 2667,
    5.5: 1833,
  }

  # if bad input
  if size_value is None:
    return MINIMUM_IMAGE_PIXELS
  
  try: 
    size_value = float(size_value)
  except (TypeError, ValueError):
    return MINIMUM_IMAGE_PIXELS
  
  # use canonical mapping for specific values
  if size_value in canonical_map:
    return canonical_map[size_value]
  
  # proportional scaling
  pixels = (size_value / 3.0) * 1000
  
  # No less than 1000 pix
  # pixels = MINIMUM_IMAGE_PIXELS if pixels < MINIMUM_IMAGE_PIXELS else pixels
  
  return round(pixels)
