from tkinter import Canvas
from enum import Enum
'''
When calling print(canvas.__dict__.keys()), we get:
dict_keys(['widgetName', 'master', 'tk', '_name', '_w', 'children', '_tclCommands', 'frangi_bool', 'frangi_min', 'frangi_max', 'med_filt_bool', 'twig_size', 'kernel_size', 'prebinary_var', 'bin_size_var', 'image_size_var', 'img_type_var', 'faz_type_var', 'status_id', 'original_img', '_image_refs', 'FileLabelName', 'lastPath', 'fullImSizePix', 'FAZ_ctr', 'last_original_img_id', 'last_filename_text_id', 'binary_image'])
'''
class ClearMode(Enum):
  CLEAR_ENTIRE_SCREEN = 1
  CLEAR_BEFORE_LOADING_NEW_IMG = 2
  CLEAR_BEFORE_PROCESSING = 3

def remove_items_from_canvas(canvas: Canvas, item_ids: list):
  """Delete the named canvas items if they exist."""
  # Remove specified items from the canvas
  for item_id in item_ids:
    id = getattr(canvas, item_id, None)
    if id:
      try:
        canvas.delete(id)
      except Exception:
        pass


def clear_screen(canvas: Canvas, clear_screen_mode: ClearMode=ClearMode.CLEAR_ENTIRE_SCREEN):
  """Clear canvas images, labels, and cached plot state for the requested workflow stage."""
  item_ids_to_remove = set()
  processed_results_ids = {"binary_img_id","skeleton_img_id", "faz_img_id"}

  if clear_screen_mode == ClearMode.CLEAR_ENTIRE_SCREEN:
    other_item_ids_to_remove = {"original_img_id","filename_text_id", "save_folder_text_id"}
  elif clear_screen_mode == ClearMode.CLEAR_BEFORE_LOADING_NEW_IMG:
    other_item_ids_to_remove = {"original_img_id","filename_text_id"}
  elif clear_screen_mode == ClearMode.CLEAR_BEFORE_PROCESSING:
    other_item_ids_to_remove = {}
    # Skip clearing binary image if prebinary is toggled on
    if canvas.prebinary_var.get():
      processed_results_ids.remove("binary_img_id") 
  
  item_ids_to_remove.update(processed_results_ids)
  item_ids_to_remove.update(other_item_ids_to_remove)
  remove_items_from_canvas(canvas, item_ids_to_remove)
  print("value ids:", [k for k in canvas.__dict__.keys() if k.endswith("_value_id")])
  print("has hist_plotter:", hasattr(canvas, "hist_plotter"))


  # Clear all visual images on the canvas
  if hasattr(canvas, "_image_refs"):
    original_img_ref = canvas._image_refs.get("original_img")
    binary_img_ref = canvas._image_refs.get("binary_img") if canvas.prebinary_var.get() else None
    canvas._image_refs.clear()
    if clear_screen_mode == ClearMode.CLEAR_BEFORE_PROCESSING and original_img_ref:
      canvas._image_refs["original_img"] = original_img_ref
    if clear_screen_mode == ClearMode.CLEAR_BEFORE_PROCESSING and binary_img_ref:
      canvas._image_refs["binary_img"] = binary_img_ref

  # Reset thumbnail zoom/pan states
  if hasattr(canvas, "thumbnail_state"):
    for st in canvas.thumbnail_state.values():
      st["zoom"] = 1.0
      st["pan_x"] = 0.0
      st["pan_y"] = 0.0

  for key, val in canvas.__dict__.items():
    if key.endswith("_value_id"):
      try:
        canvas.itemconfig(val, text="")
      except Exception:
        pass
  if hasattr(canvas, "hist_plotter"):
    try:
      canvas.hist_plotter.set_data([])
      canvas.hist_plotter.update_plot(canvas.bin_size_var.get())
    except Exception:
      pass


