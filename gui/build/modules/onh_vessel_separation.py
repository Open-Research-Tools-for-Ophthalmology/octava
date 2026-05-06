import os
import time
import numpy as np
import cv2

from PIL import Image, ImageTk
from tkinter import Canvas

from skimage.morphology import medial_axis, remove_small_objects
from scipy.ndimage import binary_dilation, distance_transform_edt, convolve

from modules.change_status import change_status_to_waiting
from modules.resize_image import resize_image
from modules.Skel2Graph3D import skel2graph3d


def prune_short_spurs(
    skeleton: np.ndarray,
    min_branch_length: int = 12,
    max_iterations: int = 10
):
    """
    Remove short endpoint branches from a 2D skeleton.

    This is different from remove_small_objects().
    remove_small_objects() can only remove small isolated connected components.
    This function can remove short branches that are attached to a larger vessel network.

    Parameters
    ----------
    skeleton:
        Boolean 2D skeleton image.

    min_branch_length:
        Endpoint-originating branches shorter than or equal to this value
        are removed.

    max_iterations:
        Number of pruning passes.

    Returns
    -------
    pruned:
        Boolean 2D skeleton image after short-spur pruning.
    """

    skel = skeleton.astype(bool).copy()

    # 8-neighbourhood kernel, excluding centre pixel.
    kernel = np.array(
        [
            [1, 1, 1],
            [1, 0, 1],
            [1, 1, 1]
        ],
        dtype=np.uint8
    )

    for _ in range(max_iterations):
        neighbour_count = convolve(
            skel.astype(np.uint8),
            kernel,
            mode="constant",
            cval=0
        )

        endpoints = np.argwhere(skel & (neighbour_count == 1))

        if len(endpoints) == 0:
            break

        pixels_to_remove = []

        for endpoint in endpoints:
            path = []
            current = tuple(endpoint)
            previous = None

            for _step in range(min_branch_length + 1):
                path.append(current)

                y, x = current
                neighbours = []

                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        if dy == 0 and dx == 0:
                            continue

                        ny, nx = y + dy, x + dx

                        if (
                            0 <= ny < skel.shape[0]
                            and 0 <= nx < skel.shape[1]
                            and skel[ny, nx]
                        ):
                            if previous is None or (ny, nx) != previous:
                                neighbours.append((ny, nx))

                # No further skeleton pixel.
                if len(neighbours) == 0:
                    break

                # Reached a branchpoint / junction.
                # If the endpoint branch is short, remove it.
                if len(neighbours) >= 2:
                    if len(path) <= min_branch_length:
                        # Keep the junction pixel itself.
                        pixels_to_remove.extend(path[:-1])
                    break

                # Continue along a simple path.
                previous = current
                current = neighbours[0]

        if not pixels_to_remove:
            break

        for y, x in pixels_to_remove:
            skel[y, x] = False

    return skel


def skeletonise_onh(canvas: Canvas, bin_img: np.ndarray = None, display: bool = True):
    """
    ONH-specific skeletonisation v2.2.

    This version:
    - generates a skeleton from the ONH binary image
    - applies ONH ROI mask
    - performs conservative binary pre-cleaning
    - performs skeleton component pruning
    - performs endpoint short-spur pruning
    - extracts graph nodes and links using skel2graph3d
    - stores skeleton, distance map, nodes, and links on canvas

    It intentionally does NOT run graph2skel3d iterative cleaning yet.

    Expected outputs:
    - canvas.skeleton_image
    - canvas.skeleton_nodes
    - canvas.skeleton_links
    - canvas.distance_map

    ONH-specific aliases:
    - canvas.onh_skeleton_image
    - canvas.onh_skeleton_nodes
    - canvas.onh_skeleton_links
    - canvas.onh_distance_map
    """

    change_status_to_waiting(canvas, status="● Wait...Skeletonising ONH")

    # ------------------------------------------------------------
    # 1. Choose binary input
    # ------------------------------------------------------------
    if bin_img is None:
        if hasattr(canvas, "binary_image"):
            bin_img = canvas.binary_image
        else:
            raise ValueError("No binary image found for ONH skeletonisation.")

    vessel_mask = bin_img > 0

    # ------------------------------------------------------------
    # 2. Apply ONH ROI mask
    # ------------------------------------------------------------
    if hasattr(canvas, "onh_mask_arr"):
        roi_mask = canvas.onh_mask_arr.astype(bool)

        if roi_mask.shape != vessel_mask.shape:
            raise ValueError("ONH mask and binary image have different sizes.")

        vessel_mask = vessel_mask & roi_mask
    else:
        roi_mask = np.ones_like(vessel_mask, dtype=bool)

    image_size = vessel_mask.shape[0]

    # ------------------------------------------------------------
    # 3. Pre-cleaning before skeletonisation
    # ------------------------------------------------------------
    # Removes tiny isolated binary components before skeletonisation.
    # For 1500x1500 images:
    # image_size * image_size * 0.00001 = 22.5 pixels
    pre_min_area = max(20, int(image_size * image_size * 0.00001))

    vessel_mask_clean = remove_small_objects(
        vessel_mask.astype(bool),
        min_size=pre_min_area,
        connectivity=2
    )

    vessel_mask_clean = vessel_mask_clean & roi_mask

    # ------------------------------------------------------------
    # 4. Skeletonise
    # ------------------------------------------------------------
    # medial_axis gives both skeleton and distance map.
    # The distance map is useful for diameter calculation later.
    skeleton_bool, medial_distance = medial_axis(
        vessel_mask_clean,
        return_distance=True
    )

    skeleton_bool = skeleton_bool & roi_mask

    # Full distance transform from cleaned binary vessel mask.
    # This is usually more stable for diameter calculation.
    distance_map = distance_transform_edt(vessel_mask_clean)

    # ------------------------------------------------------------
    # 5. Skeleton component pruning
    # ------------------------------------------------------------
    if hasattr(canvas, "twig_size"):
        retina_twig_size = int(canvas.twig_size.get())
    else:
        retina_twig_size = 10

    # v2.2 default:
    # Start with a stronger pruning than v2.
    #
    # If true fine vessels disappear too much:
    #   onh_twig_size = max(5, int(retina_twig_size * 0.8))
    #
    # If graph is still too complex:
    #   onh_twig_size = max(10, int(retina_twig_size))
    onh_twig_size = max(8, int(retina_twig_size))

    skeleton_clean = remove_small_objects(
        skeleton_bool.astype(bool),
        min_size=onh_twig_size,
        connectivity=2
    )

    skeleton_clean = skeleton_clean & roi_mask

    # ------------------------------------------------------------
    # 6. Short-spur pruning
    # ------------------------------------------------------------
    # Removes short endpoint branches attached to larger networks.
    # This should reduce endpoints, branch nodes, and short noisy links.
    spur_prune_length = max(10, int(onh_twig_size * 1.5))

    before_spur_pixels = np.count_nonzero(skeleton_clean)

    skeleton_clean = prune_short_spurs(
        skeleton_clean,
        min_branch_length=spur_prune_length,
        max_iterations=10
    )

    skeleton_clean = skeleton_clean & roi_mask

    after_spur_pixels = np.count_nonzero(skeleton_clean)

    print("ONH skeleton pixels before spur pruning:", before_spur_pixels)
    print("ONH skeleton pixels after spur pruning:", after_spur_pixels)
    print("ONH spur prune length:", spur_prune_length)

    # ------------------------------------------------------------
    # 7. Extract graph nodes and links using skel2graph3d
    # ------------------------------------------------------------
    # We only extract nodes/links here.
    # We do NOT run graph2skel3d cleaning yet.
    if np.count_nonzero(skeleton_clean) == 0:
        print("ONH skeleton is empty. No graph extracted.")
        nodes = []
        links = []
    else:
        start_graph = time.time()

        nodes, links = skel2graph3d(
            skeleton_clean.astype(bool),
            onh_twig_size
        )

        end_graph = time.time()

        print("ONH skel2graph3d completed.")
        print("Time for ONH skel2graph3d:", end_graph - start_graph)
        print("ONH graph nodes:", len(nodes))
        print("ONH graph links:", len(links))

        endpoint_count = sum(
            1 for n in nodes
            if getattr(n, "ep", 0) == 1
        )

        branch_count = len(nodes) - endpoint_count

        link_lengths = [
            len(l.path) for l in links
            if hasattr(l, "path") and l.path is not None
        ]

        mean_link_len = np.mean(link_lengths) if link_lengths else 0
        median_link_len = np.median(link_lengths) if link_lengths else 0

        print("ONH endpoints:", endpoint_count)
        print("ONH branch nodes:", branch_count)
        print("ONH mean link length:", mean_link_len)
        print("ONH median link length:", median_link_len)

    # ------------------------------------------------------------
    # 8. Store outputs on canvas
    # ------------------------------------------------------------
    canvas.skeleton_image = skeleton_clean
    canvas.skeleton_nodes = nodes
    canvas.skeleton_links = links
    canvas.distance_map = distance_map

    canvas.onh_skeleton_image = skeleton_clean
    canvas.onh_skeleton_nodes = nodes
    canvas.onh_skeleton_links = links
    canvas.onh_distance_map = distance_map

    # Useful tuning/debug information.
    canvas.onh_vessel_mask_clean_debug = vessel_mask_clean
    canvas.onh_skeleton_twig_size = onh_twig_size
    canvas.onh_pre_min_area = pre_min_area
    canvas.onh_spur_prune_length = spur_prune_length

    # ------------------------------------------------------------
    # 9. Display and save
    # ------------------------------------------------------------
    if display:
        display_onh_skeleton(canvas, skeleton_clean)

    save_onh_skeleton_image(canvas, skeleton_clean, onh_twig_size)

    print("ONH skeletonisation v2.2 completed.")

    return skeleton_clean, nodes, links


def display_onh_skeleton(canvas: Canvas, skeleton_image: np.ndarray):
    """
    Display ONH skeleton image on the GUI.

    The skeleton is dilated only for display visibility.
    The original one-pixel skeleton is still stored on canvas.skeleton_image.
    """

    skel_uint8 = binary_dilation(
        skeleton_image,
        iterations=1
    ).astype(np.uint8) * 255

    skel_pil = Image.fromarray(skel_uint8, mode="L")
    resized_img = resize_image(skel_pil)
    img_tk = ImageTk.PhotoImage(resized_img)

    canvas.skeleton_img_id = canvas.create_image(1060, 255, image=img_tk)

    if not hasattr(canvas, "_image_refs"):
        canvas._image_refs = {}

    canvas._image_refs["skeleton_img"] = img_tk


def save_onh_skeleton_image(canvas: Canvas, skeleton_image: np.ndarray, twig_size: int):
    """
    Save ONH skeleton image and optional debug masks.
    """

    if not hasattr(canvas, "current_save_folder"):
        print("No current_save_folder found. ONH skeleton image not saved.")
        return

    images_dir = os.path.join(canvas.current_save_folder, "images")
    os.makedirs(images_dir, exist_ok=True)

    file_label = getattr(canvas, "FileLabelName", "ONH_Image")

    curr_idx = len([
        f for f in os.listdir(images_dir)
        if "ONH_Skeletonised" in f
    ])

    # Save original one-pixel skeleton.
    skel_uint8 = skeleton_image.astype(np.uint8) * 255

    img_path = os.path.join(
        images_dir,
        f"{file_label}_ONH_Skeletonised_TwigSize{twig_size}_{curr_idx}.png"
    )

    cv2.imwrite(img_path, skel_uint8)
    print(f"ONH skeleton image saved to: {img_path}")

    # Save display version as well, easier to inspect visually.
    skel_display_uint8 = binary_dilation(
        skeleton_image,
        iterations=1
    ).astype(np.uint8) * 255

    display_path = os.path.join(
        images_dir,
        f"{file_label}_ONH_Skeletonised_Display_TwigSize{twig_size}_{curr_idx}.png"
    )

    cv2.imwrite(display_path, skel_display_uint8)
    print(f"ONH display skeleton image saved to: {display_path}")

    # Save pre-cleaned vessel mask if available.
    vessel_mask_clean = getattr(canvas, "onh_vessel_mask_clean_debug", None)

    if vessel_mask_clean is not None:
        vessel_mask_path = os.path.join(
            images_dir,
            f"{file_label}_ONH_VesselMaskClean_{curr_idx}.png"
        )

        cv2.imwrite(
            vessel_mask_path,
            vessel_mask_clean.astype(np.uint8) * 255
        )

        print(f"ONH cleaned vessel mask saved to: {vessel_mask_path}")