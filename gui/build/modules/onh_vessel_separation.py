import os
import numpy as np
import cv2

from PIL import Image, ImageTk
from tkinter import Canvas
from scipy.ndimage import distance_transform_edt, binary_dilation, binary_propagation
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
            return max(60.0, float(canvas.onh_large_vessel_threshold_um.get()))
        except Exception:
            pass

    return 60.0


def _dilate_bool(mask: np.ndarray, radius_pixels: int) -> np.ndarray:
    radius_pixels = max(0, int(radius_pixels))

    if radius_pixels == 0:
        return mask.astype(bool)

    kernel_size = radius_pixels * 2 + 1
    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE,
        (kernel_size, kernel_size),
    )

    return cv2.dilate(mask.astype(np.uint8), kernel, iterations=1).astype(bool)


def _morphology_bool(
    mask: np.ndarray,
    operation: int,
    radius_pixels: int,
) -> np.ndarray:
    radius_pixels = max(0, int(radius_pixels))

    if radius_pixels == 0:
        return mask.astype(bool)

    kernel_size = radius_pixels * 2 + 1
    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE,
        (kernel_size, kernel_size),
    )

    return cv2.morphologyEx(
        mask.astype(np.uint8),
        operation,
        kernel,
        iterations=1,
    ).astype(bool)


def _opening_by_reconstruction(
    mask: np.ndarray,
    radius_pixels: int,
) -> np.ndarray:
    radius_pixels = max(0, int(radius_pixels))

    if radius_pixels == 0 or not np.any(mask):
        return mask.astype(bool)

    kernel_size = radius_pixels * 2 + 1
    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE,
        (kernel_size, kernel_size),
    )

    eroded = cv2.erode(
        mask.astype(np.uint8),
        kernel,
        iterations=1,
    ).astype(bool)

    return binary_propagation(
        eroded,
        mask=mask.astype(bool),
    ).astype(bool)


def _close_with_line_kernels(
    mask: np.ndarray,
    line_length_pixels: int,
    angle_step_degrees: int = 15,
) -> np.ndarray:
    line_length_pixels = max(3, int(line_length_pixels))
    if line_length_pixels % 2 == 0:
        line_length_pixels += 1

    mask_uint8 = mask.astype(np.uint8)
    closed_union = mask_uint8.copy()
    center = line_length_pixels // 2

    for angle_degrees in range(0, 180, max(1, int(angle_step_degrees))):
        angle_radians = np.deg2rad(angle_degrees)
        half_length = line_length_pixels // 2
        dx = int(round(np.cos(angle_radians) * half_length))
        dy = int(round(np.sin(angle_radians) * half_length))

        kernel = np.zeros(
            (line_length_pixels, line_length_pixels),
            dtype=np.uint8,
        )
        cv2.line(
            kernel,
            (center - dx, center - dy),
            (center + dx, center + dy),
            color=1,
            thickness=1,
        )

        closed = cv2.morphologyEx(
            mask_uint8,
            cv2.MORPH_CLOSE,
            kernel,
            iterations=1,
        )
        closed_union = np.maximum(closed_union, closed)

    return closed_union.astype(bool)


def _filter_large_vessel_components(
    large_mask: np.ndarray,
    min_component_area_pixels: int,
    min_component_span_pixels: int,
) -> tuple[np.ndarray, np.ndarray, int, int]:
    """
    Keep large-vessel components that are large and elongated enough.

    Diameter thresholding alone can classify round bright blobs as large
    vessels because their local diameter is high enough. An area threshold is
    not sufficient for those blobs, so this pass also requires each connected
    component to span a minimum distance in either x or y.
    """

    min_component_area_pixels = max(1, int(min_component_area_pixels))
    min_component_span_pixels = max(1, int(min_component_span_pixels))

    if not np.any(large_mask):
        empty = large_mask.astype(bool)
        return empty, empty.copy(), 0, 0

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
        large_mask.astype(np.uint8),
        connectivity=8,
    )

    filtered = np.zeros_like(large_mask, dtype=bool)
    rejected = np.zeros_like(large_mask, dtype=bool)
    kept_count = 0

    for label_idx in range(1, num_labels):
        area = stats[label_idx, cv2.CC_STAT_AREA]
        width = stats[label_idx, cv2.CC_STAT_WIDTH]
        height = stats[label_idx, cv2.CC_STAT_HEIGHT]
        component_span = max(width, height)
        bounding_box_area = max(1, width * height)
        fill_ratio = area / bounding_box_area
        is_compact_blob = (
            fill_ratio >= 0.55
            and area < min_component_area_pixels * 4
            and component_span < min_component_span_pixels * 2
        )
        component_mask = labels == label_idx

        if (
            area >= min_component_area_pixels
            and component_span >= min_component_span_pixels
            and not is_compact_blob
        ):
            filtered[component_mask] = True
            kept_count += 1
        else:
            rejected[component_mask] = True

    return filtered, rejected, num_labels - 1, kept_count


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

    high_diameter_seed = overall_mask & (diameter_map_um >= threshold_um)
    low_support_threshold_um = max(threshold_um * 0.68, threshold_um - 14.0)
    large_support = overall_mask & (diameter_map_um >= low_support_threshold_um)

    if pixel_size_mm > 0:
        large_radius_pixels = max(1, int(round((threshold_mm / pixel_size_mm) / 2.0)))
    else:
        large_radius_pixels = 1

    min_large_seed_area = max(3, int(np.pi * (large_radius_pixels ** 2) * 0.05))
    large_seed = remove_small_objects(
        high_diameter_seed.astype(bool),
        min_size=min_large_seed_area,
        connectivity=2,
    )

    seed_bridge_radius = max(1, int(round(large_radius_pixels * 0.45)))
    large_seed = _morphology_bool(
        large_seed,
        cv2.MORPH_CLOSE,
        seed_bridge_radius,
    ) & roi_mask

    support_bridge_radius = max(1, int(round(large_radius_pixels * 0.40)))
    large_support = _morphology_bool(
        large_support,
        cv2.MORPH_CLOSE,
        support_bridge_radius,
    ) & roi_mask

    large_core = binary_propagation(
        large_seed,
        mask=large_support,
    ).astype(bool)

    reconstruction_radius = max(1, int(round(large_radius_pixels * 0.95)))
    shape_candidate = _dilate_bool(
        large_core,
        reconstruction_radius,
    ) & overall_mask & roi_mask

    opening_radius = max(1, int(round(large_radius_pixels * 0.30)))
    large_mask = _opening_by_reconstruction(
        shape_candidate,
        opening_radius,
    ) & roi_mask

    line_bridge_length = max(7, int(round(large_radius_pixels * 2.4)))
    line_bridge_support = _dilate_bool(
        shape_candidate,
        max(1, int(round(large_radius_pixels * 0.30))),
    ) & roi_mask
    large_mask = _close_with_line_kernels(
        large_mask,
        line_length_pixels=line_bridge_length,
        angle_step_degrees=15,
    ) & line_bridge_support

    large_mask = _opening_by_reconstruction(
        large_mask,
        opening_radius,
    ) & roi_mask

    bridge_radius = 0
    smooth_radius = opening_radius

    min_large_area = max(20, int(np.pi * (large_radius_pixels ** 2) * 0.5))
    large_mask = remove_small_objects(
        large_mask.astype(bool),
        min_size=min_large_area,
        connectivity=2,
    )

    min_large_component_area = max(350, int(np.pi * (large_radius_pixels ** 2) * 2.5))
    min_large_component_span = max(35, int(round(large_radius_pixels * 6.0)))
    (
        large_mask,
        rejected_large_noise,
        large_component_count,
        large_component_kept_count,
    ) = _filter_large_vessel_components(
        large_mask,
        min_component_area_pixels=min_large_component_area,
        min_component_span_pixels=min_large_component_span,
    )
    large_mask = large_mask & roi_mask

    small_mask = overall_mask & (~large_mask) & (~rejected_large_noise) & roi_mask

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
    canvas.onh_large_support_threshold_um_debug = low_support_threshold_um
    canvas.onh_large_seed_debug = large_seed
    canvas.onh_large_core_debug = large_core
    canvas.onh_large_support_debug = large_support
    canvas.onh_large_shape_candidate_debug = shape_candidate
    canvas.onh_large_seed_min_area_debug = min_large_seed_area
    canvas.onh_large_seed_bridge_radius_debug = seed_bridge_radius
    canvas.onh_large_support_bridge_radius_debug = support_bridge_radius
    canvas.onh_large_reconstruction_radius_debug = reconstruction_radius
    canvas.onh_large_opening_radius_debug = opening_radius
    canvas.onh_large_bridge_radius_debug = bridge_radius
    canvas.onh_large_line_bridge_length_debug = line_bridge_length
    canvas.onh_large_smooth_radius_debug = smooth_radius
    canvas.onh_large_component_min_area_debug = min_large_component_area
    canvas.onh_large_component_min_span_debug = min_large_component_span
    canvas.onh_large_component_count_debug = large_component_count
    canvas.onh_large_component_kept_count_debug = large_component_kept_count
    canvas.onh_large_rejected_noise_debug = rejected_large_noise

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

    # Branchpoint density and fractal dimension are not part of the final ONH
    # metric display because their interpretation is weaker in annulus ROI
    # analysis. The original labels are still used by the Retina workflow.

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
