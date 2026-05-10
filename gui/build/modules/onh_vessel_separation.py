import os
import numpy as np
import cv2

from PIL import Image, ImageTk
from tkinter import Canvas
from scipy.ndimage import distance_transform_edt, binary_dilation
from skimage.morphology import remove_small_objects

from modules.resize_image import resize_image


ONH_VIEW_TO_KEY = {
    "Overall": "overall",
    "Large Vessels": "large",
    "Small Vessels": "small",
}


def get_onh_large_vessel_threshold_um(canvas: Canvas) -> float:
    """Return the ONH-only large-vessel diameter threshold in microns."""

    if hasattr(canvas, "onh_large_vessel_threshold_um"):
        try:
            return float(canvas.onh_large_vessel_threshold_um.get())
        except Exception:
            pass

    return 40.0


def separate_onh_vessels(
    canvas: Canvas,
    binary_overall: np.ndarray = None,
    display: bool = False,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Split the ONH overall binary mask into large-vessel and small-vessel masks.

    Large vessels are estimated from the local vessel diameter map. Pixels whose
    distance-transform diameter exceeds the ONH large-vessel threshold seed the
    large-vessel mask; the seed is dilated back into the overall vessel mask so
    large vessels are represented as full-width regions instead of thin cores.
    """

    if binary_overall is None:
        if hasattr(canvas, "onh_binary_overall"):
            binary_overall = canvas.onh_binary_overall
        elif hasattr(canvas, "binary_image"):
            binary_overall = canvas.binary_image
        else:
            raise ValueError("No ONH overall binary image found for vessel separation.")

    overall_mask = binary_overall > 0

    if hasattr(canvas, "onh_mask_arr"):
        roi_mask = canvas.onh_mask_arr.astype(bool)
        if roi_mask.shape != overall_mask.shape:
            raise ValueError("ONH mask and binary image have different sizes.")
        overall_mask = overall_mask & roi_mask
    else:
        roi_mask = np.ones_like(overall_mask, dtype=bool)

    height, width = overall_mask.shape
    image_size_mm = float(canvas.image_size_var.get())
    pixel_size_mm = image_size_mm / float(width) if width > 0 else 0.0

    threshold_um = get_onh_large_vessel_threshold_um(canvas)
    threshold_mm = threshold_um / 1000.0

    radius_map_pixels = distance_transform_edt(overall_mask)
    diameter_map_um = radius_map_pixels * 2.0 * pixel_size_mm * 1000.0

    large_seed = overall_mask & (diameter_map_um >= threshold_um)

    if pixel_size_mm > 0:
        large_radius_pixels = max(1, int(round((threshold_mm / pixel_size_mm) / 2.0)))
    else:
        large_radius_pixels = 1

    large_mask = binary_dilation(
        large_seed,
        iterations=large_radius_pixels,
    ) & overall_mask

    min_large_area = max(20, int(np.pi * (large_radius_pixels ** 2) * 0.5))
    large_mask = remove_small_objects(
        large_mask.astype(bool),
        min_size=min_large_area,
        connectivity=2,
    )
    large_mask = large_mask & overall_mask & roi_mask

    small_mask = overall_mask & (~large_mask) & roi_mask

    binary_overall_uint8 = (overall_mask.astype(np.uint8) * 255)
    binary_large_uint8 = (large_mask.astype(np.uint8) * 255)
    binary_small_uint8 = (small_mask.astype(np.uint8) * 255)

    canvas.onh_binary_overall = binary_overall_uint8
    canvas.onh_binary_large = binary_large_uint8
    canvas.onh_binary_small = binary_small_uint8

    # Existing GUI code probes these names, so keep them as display aliases.
    canvas.onh_overall_vessel_img = binary_overall_uint8
    canvas.onh_large_vessel_img = binary_large_uint8
    canvas.onh_small_vessel_img = binary_small_uint8

    canvas.onh_diameter_map_um = diameter_map_um
    canvas.onh_large_vessel_threshold_um_used = threshold_um
    canvas.onh_large_seed_debug = large_seed

    save_onh_vessel_separation_images(canvas)

    if display:
        update_onh_segmentation_dropdown_display(
            canvas,
            getattr(canvas.onh_segmentation_view_var, "get", lambda: "Overall")(),
        )

    return binary_large_uint8, binary_small_uint8


def _display_image_on_canvas(
    canvas: Canvas,
    image: np.ndarray,
    item_attr: str,
    ref_key: str,
    position: tuple,
    dilate: bool = False,
) -> None:
    image_to_show = image > 0

    if dilate:
        image_to_show = binary_dilation(image_to_show, iterations=1)

    image_uint8 = image_to_show.astype(np.uint8) * 255
    pil_image = Image.fromarray(image_uint8, mode="L")
    resized_img = resize_image(pil_image)
    img_tk = ImageTk.PhotoImage(resized_img)

    old_id = getattr(canvas, item_attr, None)
    if old_id:
        try:
            canvas.delete(old_id)
        except Exception:
            pass

    new_id = canvas.create_image(position[0], position[1], image=img_tk)
    setattr(canvas, item_attr, new_id)

    if not hasattr(canvas, "_image_refs"):
        canvas._image_refs = {}
    canvas._image_refs[ref_key] = img_tk


def update_onh_segmentation_dropdown_display(canvas: Canvas, selected_view: str) -> None:
    """
    Display the already-computed ONH binary/skeleton pair selected by the dropdown.
    No computation is triggered here; the dropdown is only a viewer.
    """

    key = ONH_VIEW_TO_KEY.get(selected_view, "overall")

    binary = getattr(canvas, f"onh_binary_{key}", None)
    skeleton = getattr(canvas, f"onh_skeleton_{key}", None)

    if binary is not None:
        _display_image_on_canvas(
            canvas,
            binary,
            item_attr="binary_img_id",
            ref_key="binary_img",
            position=(805, 255),
            dilate=False,
        )
        canvas.binary_image = binary

    if skeleton is not None:
        _display_image_on_canvas(
            canvas,
            skeleton,
            item_attr="skeleton_img_id",
            ref_key="skeleton_img",
            position=(1060, 255),
            dilate=True,
        )
        canvas.skeleton_image = skeleton

    metrics_by_type = getattr(canvas, "onh_metrics_by_type", {})
    metrics = metrics_by_type.get(key)
    if metrics:
        _update_onh_metric_labels(canvas, metrics)

    diameters_by_type = getattr(canvas, "onh_diameters_by_type", {})
    diameters = diameters_by_type.get(key)
    if diameters is not None:
        canvas.vessel_diameters_um = diameters

        if hasattr(canvas, "hist_plotter"):
            canvas.hist_plotter.set_data(diameters)
            canvas.hist_plotter.update_plot(canvas.bin_size_var.get())


def _update_onh_metric_labels(canvas: Canvas, metrics: dict) -> None:
    if hasattr(canvas, "vad_value_id"):
        canvas.itemconfig(
            canvas.vad_value_id,
            text=f"{metrics.get('vessel_area_density_pct', 0.0):.2f} %",
        )

    if hasattr(canvas, "length_density_value_id"):
        canvas.itemconfig(
            canvas.length_density_value_id,
            text=f"{metrics.get('vessel_length_density_mm_per_mm2', 0.0):.2f}",
        )

    if hasattr(canvas, "mean_diameter_value_id"):
        canvas.itemconfig(
            canvas.mean_diameter_value_id,
            text=f"{metrics.get('mean_diameter_um', 0.0):.2f} um",
        )

    if hasattr(canvas, "branch_density_value_id"):
        canvas.itemconfig(
            canvas.branch_density_value_id,
            text=f"{metrics.get('branchpoint_density_per_mm2', 0.0):.2f} /mm^2",
        )

    if hasattr(canvas, "fractal_dim_value_id"):
        canvas.itemconfig(
            canvas.fractal_dim_value_id,
            text=f"{metrics.get('fractal_dimension', 0.0):.3f}",
        )

    if hasattr(canvas, "tortuosity_value_id"):
        canvas.itemconfig(
            canvas.tortuosity_value_id,
            text=f"{metrics.get('mean_tortuosity', 0.0):.3f}",
        )


def save_onh_vessel_separation_images(canvas: Canvas) -> None:
    if not hasattr(canvas, "current_save_folder"):
        return

    images_dir = os.path.join(canvas.current_save_folder, "images")
    os.makedirs(images_dir, exist_ok=True)

    file_label = getattr(canvas, "FileLabelName", "ONH_Image")
    threshold_um = getattr(canvas, "onh_large_vessel_threshold_um_used", 40.0)

    outputs = {
        "ONH_Binary_Overall": getattr(canvas, "onh_binary_overall", None),
        f"ONH_Binary_Large_Threshold{threshold_um:g}um": getattr(canvas, "onh_binary_large", None),
        f"ONH_Binary_Small_Threshold{threshold_um:g}um": getattr(canvas, "onh_binary_small", None),
    }

    for name, image in outputs.items():
        if image is None:
            continue

        path = os.path.join(images_dir, f"{file_label}_{name}.png")
        cv2.imwrite(path, image)
