# modules/onh_biomarker.py

import numpy as np
from tkinter import Canvas
from scipy.ndimage import distance_transform_edt
from modules.write_excel import *


class ONHBiomarkerAnalyzer:
    """
    Compute ONH biomarkers from the current canvas state.

    Important ONH difference:
    - Retina metrics often use the whole image area as the denominator.
    - ONH metrics should use the annulus ROI area, i.e. canvas.onh_mask_arr.
    - The centre optic disc region and outside-mask region should not be counted.

    Expected canvas inputs:
    - canvas.binary_image
    - canvas.skeleton_image
    - canvas.skeleton_nodes
    - canvas.skeleton_links
    - canvas.onh_mask_arr
    - canvas.image_size_var
    - canvas.FileLabelName
    - canvas.lastMetricsPath
    """

    @staticmethod
    def process(canvas: Canvas) -> None:
        # ------------------------------------------------------------
        # 1. Read input data
        # ------------------------------------------------------------
        if not hasattr(canvas, "binary_image"):
            raise ValueError("No binary image found for ONH biomarker calculation.")

        if not hasattr(canvas, "skeleton_image"):
            raise ValueError("No skeleton image found for ONH biomarker calculation.")

        if not hasattr(canvas, "onh_mask_arr"):
            raise ValueError("No ONH annulus mask found for ONH biomarker calculation.")

        binary = canvas.binary_image
        skeleton = canvas.skeleton_image
        nodes = getattr(canvas, "skeleton_nodes", [])
        links = getattr(canvas, "skeleton_links", [])

        roi_mask = canvas.onh_mask_arr.astype(bool)

        if binary.shape != roi_mask.shape:
            raise ValueError("ONH binary image and ONH ROI mask have different sizes.")

        if skeleton.shape != roi_mask.shape:
            raise ValueError("ONH skeleton image and ONH ROI mask have different sizes.")

        # Ensure vessel and skeleton are inside annulus ROI only
        binary_mask = (binary > 0) & roi_mask
        skeleton_mask = (skeleton > 0) & roi_mask

        height, width = binary_mask.shape

        # ------------------------------------------------------------
        # 2. Physical scale
        # ------------------------------------------------------------
        # image_size_var is the scan width in mm, e.g. 4.5 mm for ONH.
        image_size_mm = float(canvas.image_size_var.get())

        if width > 0:
            pixel_size_mm = image_size_mm / float(width)
        else:
            pixel_size_mm = 0.0

        pixel_area_mm2 = pixel_size_mm ** 2

        # ------------------------------------------------------------
        # 3. ONH annulus ROI area
        # ------------------------------------------------------------
        roi_area_pixels = int(np.count_nonzero(roi_mask))
        roi_area_mm2 = float(roi_area_pixels * pixel_area_mm2)

        if roi_area_pixels == 0 or roi_area_mm2 <= 0:
            raise ValueError("ONH ROI area is zero. Please check the ONH mask.")

        # ------------------------------------------------------------
        # 4. Vessel Area Density, VAD
        # ------------------------------------------------------------
        # ONH denominator = annulus ROI area, not full image area.
        vessel_pixels = int(np.count_nonzero(binary_mask))
        vessel_area_mm2 = float(vessel_pixels * pixel_area_mm2)

        vessel_area_density_pct = float(vessel_pixels / roi_area_pixels * 100.0)
        vessel_area_density_pct = round(vessel_area_density_pct, 2)

        # ------------------------------------------------------------
        # 5. Vessel Length Density, VLD
        # ------------------------------------------------------------
        # Prefer link-based length if links are available.
        # This is better than simply counting skeleton pixels because diagonal
        # steps have length sqrt(2), not 1.
        total_length_pixels = 0.0

        if links is not None and len(links) > 0:
            for link in links:
                indices = np.asarray(link.path, dtype=int)

                if indices.size < 2:
                    continue

                rows, cols = np.unravel_index(indices, binary_mask.shape)
                coords = np.column_stack((rows, cols)).astype(float)

                diffs = np.diff(coords, axis=0)
                step_lengths = np.linalg.norm(diffs, axis=1)

                length_pixels = float(step_lengths.sum())

                total_length_pixels += length_pixels
                link.pixLength = length_pixels

        else:
            # Fallback:
            # approximate length by counting skeleton pixels.
            total_length_pixels = float(np.count_nonzero(skeleton_mask))

        total_length_mm = float(total_length_pixels * pixel_size_mm)

        # ONH denominator = annulus ROI area in mm².
        vessel_length_density = float(total_length_mm / roi_area_mm2)

        # ------------------------------------------------------------
        # 6. Mean diameter
        # ------------------------------------------------------------
        # Use distance transform on the ONH binary vessel mask.
        # Diameter at skeleton point = 2 * distance to background.
        radius_map = distance_transform_edt(binary_mask)
        diameter_map_pixels = radius_map * 2.0

        sampled_diameters_pixels = []

        # Prefer link paths for consistency with graph-based metrics.
        if links is not None and len(links) > 0:
            for link in links:
                indices = np.asarray(link.path, dtype=int)

                if indices.size == 0:
                    continue

                rows, cols = np.unravel_index(indices, binary_mask.shape)

                valid = roi_mask[rows, cols]
                rows = rows[valid]
                cols = cols[valid]

                if rows.size == 0:
                    continue

                values = diameter_map_pixels[rows, cols]
                sampled_diameters_pixels.extend(values)

        else:
            values = diameter_map_pixels[skeleton_mask]
            sampled_diameters_pixels.extend(values)

        sampled_diameters_pixels = np.asarray(sampled_diameters_pixels, dtype=float)

        if sampled_diameters_pixels.size > 0:
            diameters_um = sampled_diameters_pixels * pixel_size_mm * 1000.0
            mean_diameter_um = float(np.mean(diameters_um))
        else:
            diameters_um = np.asarray([], dtype=float)
            mean_diameter_um = 0.0

        # For histogram plotter, keep same canvas variable as Retina.
        canvas.vessel_diameters_um = diameters_um

        # ------------------------------------------------------------
        # 7. Branchpoint density
        # ------------------------------------------------------------
        # For ONH, use branchpoints per annulus ROI area.
        # This is more appropriate than using the full image area.
        branchpoint_count = 0

        if nodes is not None:
            for node in nodes:
                # In skel2graph3d:
                # ep == 1 means endpoint
                # ep == 0 means branch/junction node
                if getattr(node, "ep", 0) == 0:
                    branchpoint_count += 1

        branchpoint_density_per_mm2 = float(branchpoint_count / roi_area_mm2)

        # Optional additional measure: branchpoints per vessel length.
        if total_length_mm > 0:
            branchpoint_density_per_mm = float(branchpoint_count / total_length_mm)
        else:
            branchpoint_density_per_mm = 0.0

        # ------------------------------------------------------------
        # 8. Fractal dimension
        # ------------------------------------------------------------
        # Use skeleton inside ONH annulus.
        fractal_dimension = ONHBiomarkerAnalyzer._box_counting_fractal_dimension(
            skeleton_mask
        )

        # ------------------------------------------------------------
        # 9. Mean tortuosity
        # ------------------------------------------------------------
        # Tortuosity = arc length / chord length for each link.
        tortuosity_values = []

        if links is not None:
            for link in links:
                indices = np.asarray(link.path, dtype=int)

                if indices.size < 3:
                    continue

                rows, cols = np.unravel_index(indices, binary_mask.shape)
                coords_pixels = np.column_stack((rows, cols)).astype(float)

                # Keep only points inside ONH ROI
                valid = roi_mask[rows, cols]
                coords_pixels = coords_pixels[valid]

                if coords_pixels.shape[0] < 3:
                    continue

                diffs = np.diff(coords_pixels, axis=0)
                arc_length_pixels = float(np.sum(np.linalg.norm(diffs, axis=1)))

                start_point = coords_pixels[0]
                end_point = coords_pixels[-1]
                chord_length_pixels = float(np.linalg.norm(end_point - start_point))

                # Avoid unstable tortuosity for extremely short links.
                if chord_length_pixels > 1e-6 and arc_length_pixels >= 3:
                    tortuosity = arc_length_pixels / chord_length_pixels

                    # Basic sanity filter.
                    # Tortuosity should be >= 1.
                    # Very high values often come from tiny/noisy links.
                    if np.isfinite(tortuosity) and 1.0 <= tortuosity <= 20.0:
                        tortuosity_values.append(tortuosity)
                        link.tortuosity = tortuosity

        if len(tortuosity_values) > 0:
            mean_tortuosity = float(np.mean(tortuosity_values))
        else:
            mean_tortuosity = 0.0

        # ------------------------------------------------------------
        # 10. Store metrics on canvas
        # ------------------------------------------------------------
        if not hasattr(canvas, "metrics"):
            canvas.metrics = {}

        canvas.metrics.update({
            "onh_vessel_area_density_pct": float(vessel_area_density_pct),
            "onh_vessel_area_mm2": float(vessel_area_mm2),
            "onh_roi_area_mm2": float(roi_area_mm2),
            "onh_roi_area_pixels": int(roi_area_pixels),
            "onh_vessel_length_mm": float(total_length_mm),
            "onh_vessel_length_density_mm_per_mm2": float(vessel_length_density),
            "onh_mean_diameter_um": float(mean_diameter_um),
            "onh_branchpoint_count": int(branchpoint_count),
            "onh_branchpoint_density_per_mm2": float(branchpoint_density_per_mm2),
            "onh_branchpoint_density_per_mm": float(branchpoint_density_per_mm),
            "onh_fractal_dimension": float(fractal_dimension),
            "onh_mean_tortuosity": float(mean_tortuosity),
        })

        # Also update generic keys if you want GUI/old code compatibility.
        canvas.metrics.update({
            "vessel_area_density_pct": float(vessel_area_density_pct),
            "vessel_area_mm2": float(vessel_area_mm2),
            "image_area_mm2": float(roi_area_mm2),
            "vessel_length_density_mm_per_mm2": float(vessel_length_density),
            "mean_diameter_um": float(mean_diameter_um),
            "branchpoint_count": int(branchpoint_count),
            "branchpoint_density_per_mm2": float(branchpoint_density_per_mm2),
            "fractal_dimension": float(fractal_dimension),
            "mean_tortuosity": float(mean_tortuosity),
        })

        # ------------------------------------------------------------
        # 11. Write Excel
        # ------------------------------------------------------------
        onh_stats = {
            "Vessel area density": float(vessel_area_density_pct),
            "Vessel length density": float(vessel_length_density),
            "Mean diameter": float(mean_diameter_um),
            "Branchpoint density": float(branchpoint_density_per_mm2),
            "Fractal dimension": float(fractal_dimension),
            "Mean tortuosity": float(mean_tortuosity),
            "Vessel area mm2": float(vessel_area_mm2),
            "ONH ROI area mm2": float(roi_area_mm2),
            "Vessel length mm": float(total_length_mm),
            "Branchpoint count": int(branchpoint_count),
            "Branchpoint density per mm": float(branchpoint_density_per_mm),
            "name": canvas.FileLabelName,
        }

        write_excel(
            onh_stats,
            canvas.lastMetricsPath,
            sheet_name="ONH microvascular metrics"
        )

        # ------------------------------------------------------------
        # 12. Update GUI display
        # ------------------------------------------------------------
        ONHBiomarkerAnalyzer._update_gui(
            canvas,
            vessel_area_density_pct,
            vessel_length_density,
            mean_diameter_um,
            branchpoint_count,
            branchpoint_density_per_mm2,
            fractal_dimension,
            mean_tortuosity
        )

        print("ONH biomarker analysis completed.")
        print("ONH VAD (%):", vessel_area_density_pct)
        print("ONH VLD (mm/mm²):", vessel_length_density)
        print("ONH mean diameter (µm):", mean_diameter_um)
        print("ONH branchpoint count:", branchpoint_count)
        print("ONH branchpoint density (/mm²):", branchpoint_density_per_mm2)
        print("ONH fractal dimension:", fractal_dimension)
        print("ONH mean tortuosity:", mean_tortuosity)

    @staticmethod
    def _box_counting_fractal_dimension(Z: np.ndarray) -> float:
        """
        Estimate fractal dimension using box-counting.

        Input:
        - Z: boolean image, True where vessel/skeleton exists.

        Output:
        - fractal dimension as float.
        """

        Z = Z.astype(bool)

        h, w = Z.shape
        max_dim = max(h, w)

        if max_dim < 2 or np.count_nonzero(Z) == 0:
            return 0.0

        import math

        exponent = math.ceil(math.log2(max_dim))
        padded_size = 2 ** exponent

        Z_pad = np.zeros((padded_size, padded_size), dtype=bool)
        Z_pad[:h, :w] = Z

        counts = []
        box_sizes = []

        current_img = Z_pad

        # Start with box size = 1
        counts.append(np.count_nonzero(current_img))
        box_sizes.append(1)

        for i in range(1, exponent + 1):
            rows, cols = current_img.shape

            if rows < 2 or cols < 2:
                break

            # Downsample by 2 using max pooling.
            current_img = current_img.reshape(
                rows // 2, 2,
                cols // 2, 2
            ).max(axis=(1, 3))

            counts.append(np.count_nonzero(current_img))
            box_sizes.append(2 ** i)

        valid = [
            i for i, c in enumerate(counts)
            if c > 0 and box_sizes[i] > 0
        ]

        if len(valid) < 2:
            return 0.0

        x = np.log([box_sizes[i] for i in valid])
        y = -np.log([counts[i] for i in valid])

        coeffs = np.polyfit(x, y, 1)
        fractal_dim = float(coeffs[0])

        return fractal_dim

    @staticmethod
    def _update_gui(
        canvas: Canvas,
        vessel_area_density_pct: float,
        vessel_length_density: float,
        mean_diameter_um: float,
        branchpoint_count: int,
        branchpoint_density_per_mm2: float,
        fractal_dimension: float,
        mean_tortuosity: float
    ) -> None:
        """
        Update existing GUI metric labels.

        Uses the same GUI IDs as Retina, so the ONH metrics can be displayed
        in the current metric panel.
        """

        if hasattr(canvas, "vad_value_id"):
            canvas.itemconfig(
                canvas.vad_value_id,
                text=f"{vessel_area_density_pct:.2f} %"
            )

        if hasattr(canvas, "length_density_value_id"):
            canvas.itemconfig(
                canvas.length_density_value_id,
                text=f"{vessel_length_density:.2f}"
            )

        if hasattr(canvas, "mean_diameter_value_id"):
            canvas.itemconfig(
                canvas.mean_diameter_value_id,
                text=f"{mean_diameter_um:.2f} µm"
            )

        if hasattr(canvas, "branch_count_value_id"):
            canvas.itemconfig(
                canvas.branch_count_value_id,
                text=f"{branchpoint_count:d}"
            )

        if hasattr(canvas, "branch_density_value_id"):
            canvas.itemconfig(
                canvas.branch_density_value_id,
                text=f"{branchpoint_density_per_mm2:.2f} /mm²"
            )

        if hasattr(canvas, "fractal_dim_value_id"):
            canvas.itemconfig(
                canvas.fractal_dim_value_id,
                text=f"{fractal_dimension:.3f}"
            )

        if hasattr(canvas, "tortuosity_value_id"):
            canvas.itemconfig(
                canvas.tortuosity_value_id,
                text=f"{mean_tortuosity:.3f}"
            )