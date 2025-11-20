from tkinter import Canvas

'''
When calling print(canvas.__dict__.keys()), we get:
dict_keys(['widgetName', 'master', 'tk', '_name', '_w', 'children', '_tclCommands', 'frangi_bool', 'frangi_min', 'frangi_max', 'med_filt_bool', 'twig_size', 'kernel_size', 'prebinary_var', 'bin_size_var', 'image_size_var', 'img_type_var', 'faz_type_var', 'status_id', 'original_img', '_image_refs', 'FileLabelName', 'lastPath', 'fullImSizePix', 'FAZ_ctr', 'last_original_img_id', 'last_filename_text_id', 'binary_image'])
'''

def remove_items_from_canvas(canvas: Canvas, item_ids: list):
  # Remove specified items from the canvas
  for item_id in item_ids:
    id = getattr(canvas, item_id, None)
    if id:
      try:
        canvas.delete(id)
      except Exception:
        pass


def clear_screen(canvas: Canvas):

  item_ids_to_remove = ["original_img_id", "filename_text_id", "save_folder_text_id", "binary_img_id"]

  remove_items_from_canvas(canvas, item_ids_to_remove)

  # Clear all visual images on the canvas
  if hasattr(canvas, "_image_refs"):
    canvas._image_refs.clear()
