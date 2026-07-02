from tkinter import Canvas
from enum import Enum
'''
When calling print(canvas.__dict__.keys()), we get:
dict_keys(['widgetName', 'master', 'tk', '_name', '_w', 'children', '_tclCommands', 'frangi_bool', 'frangi_min', 'frangi_max', 'med_filt_bool', 'twig_size', 'kernel_size', 'prebinary_var', 'bin_size_var', 'image_size_var', 'img_type_var', 'faz_type_var', 'status_id', 'original_img', '_image_refs', 'FileLabelName', 'lastPath', 'fullImSizePix', 'FAZ_ctr', 'last_original_img_id', 'last_filename_text_id', 'binary_image'])
'''
class ClearMode(Enum):
  CLEAR_ENTIRE_SCREEN = 1
  CLEAR_BEFORE_LOADING_SINGLE_IMG = 2
  CLEAR_BEFORE_PROCESSING = 3
  CLEAR_BEFORE_LOADING_BATCH_IMG = 4


ONH_IMAGE_STATE_ATTRIBUTES = {
  "onh_mask_arr",
  "onh_mask_img",
  "onh_center",
  "onh_radius_outer",
  "onh_radius_inner",
  "onh_overall_vessel_img",
  "onh_large_vessel_img",
  "onh_small_vessel_img",
  "onh_diameter_map_um",
  "onh_large_vessel_threshold_um_used",
  "onh_large_support_threshold_um_debug",
  "onh_large_seed_debug",
  "onh_large_core_debug",
  "onh_large_support_debug",
  "onh_large_shape_candidate_debug",
  "onh_large_seed_min_area_debug",
  "onh_large_seed_bridge_radius_debug",
  "onh_large_support_bridge_radius_debug",
  "onh_large_reconstruction_radius_debug",
  "onh_large_opening_radius_debug",
  "onh_large_bridge_radius_debug",
  "onh_large_line_bridge_length_debug",
  "onh_large_smooth_radius_debug",
  "onh_large_component_min_area_debug",
  "onh_large_component_min_span_debug",
  "onh_large_component_count_debug",
  "onh_large_component_kept_count_debug",
  "onh_large_rejected_noise_debug",
  "onh_bright_vessel_seed_mask_debug",
  "onh_fine_vessel_candidate_mask_debug",
  "onh_enhanced_debug",
  "onh_corrected_debug",
  "onh_vesselness_response_debug",
  "onh_skeleton_image",
  "onh_skeleton_nodes",
  "onh_skeleton_links",
  "onh_distance_map",
  "onh_vessel_mask_clean_debug",
  "onh_skeleton_twig_size",
  "onh_pre_min_area",
  "onh_spur_prune_length",
  "onh_metrics_by_type",
  "onh_diameters_by_type",
  "onh_regional_metrics",
}

ONH_IMAGE_STATE_PREFIXES = (
  "onh_binary_",
  "onh_skeleton_",
  "onh_large_skeleton_",
  "onh_distance_map_",
  "onh_vessel_mask_clean_debug_",
  "onh_pre_min_area_",
  "onh_spur_prune_length_",
)


def clear_onh_image_state(canvas: Canvas):
  """Discard ONH masks and results that belong to the current image geometry."""
  for attribute in list(canvas.__dict__):
    if (
      attribute in ONH_IMAGE_STATE_ATTRIBUTES
      or attribute.startswith(ONH_IMAGE_STATE_PREFIXES)
    ):
      delattr(canvas, attribute)


def remove_items_from_canvas(canvas: Canvas, item_ids: list):
  """Delete the named canvas items if they exist."""
  # Remove specified items from the canvas
  for item_id in item_ids:
    id = getattr(canvas, item_id, None)
    if id is not None:
      try:
        canvas.delete(id) # remove graphical items
        delattr(canvas, item_id) # remove object items
      except Exception:
        pass


def clear_screen(canvas: Canvas, clear_screen_mode: ClearMode=ClearMode.CLEAR_ENTIRE_SCREEN):
  """Clear canvas images, labels, and cached plot state for the requested workflow stage."""
  item_ids_to_remove = set()
  processed_results_ids = {"binary_img_id", "binary_image", "skeleton_img_id", "skeleton_image", "faz_img_id", "faz_grayscale_img"}

  if clear_screen_mode == ClearMode.CLEAR_ENTIRE_SCREEN:
    other_item_ids_to_remove = {"original_img_id", "original_img", "filename_text_id", "bp_selected_folder_path", "save_folder_text_id"}
    clear_onh_image_state(canvas)
  elif clear_screen_mode == ClearMode.CLEAR_BEFORE_LOADING_SINGLE_IMG:
    other_item_ids_to_remove = {"original_img_id","original_img", "filename_text_id", "bp_selected_folder_path"}
    clear_onh_image_state(canvas)
  elif clear_screen_mode == ClearMode.CLEAR_BEFORE_LOADING_BATCH_IMG:
    other_item_ids_to_remove = {"original_img_id","original_img", "filename_text_id"}
    clear_onh_image_state(canvas)
  elif clear_screen_mode == ClearMode.CLEAR_BEFORE_PROCESSING:
    other_item_ids_to_remove = {}
    # Skip clearing binary image if prebinary is toggled on
    if canvas.prebinary_var.get():
      processed_results_ids.remove("binary_img_id") 
      processed_results_ids.remove("binary_image") 
  
  item_ids_to_remove.update(processed_results_ids)
  item_ids_to_remove.update(other_item_ids_to_remove)
  remove_items_from_canvas(canvas, item_ids_to_remove)
  print("value ids:", [k for k in canvas.__dict__.keys() if k.endswith("_value_id")])
  print("has hist_plotter:", hasattr(canvas, "hist_plotter"))


  # Clear all visual images on the canvas
  if hasattr(canvas, "_image_refs"):
    original_img_ref = canvas._image_refs.get("original_img")
    binary_img_ref = canvas._image_refs.get("binary_img")
    
    # Clear image refs case dependent
    # Image to be cleared at all cases
    canvas._image_refs.pop("skeleton_img", None)
    canvas._image_refs.pop("faz_img", None)
    # Don't clear loaded original / prebinary image
    if clear_screen_mode != ClearMode.CLEAR_BEFORE_PROCESSING and original_img_ref:
      if original_img_ref:
        canvas._image_refs.pop("original_img", None)
      if binary_img_ref and not canvas.prebinary_var.get():
        canvas._image_refs.pop("binary_img", None)

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
