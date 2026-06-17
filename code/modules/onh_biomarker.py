from __future__ import annotations

import numpy as np
import pandas as pd

from tkinter import Canvas
from scipy.ndimage import distance_transform_edt
from modules.write_excel import write_excel


ONH_METRIC_TYPES = [
    ("overall", "Overall", "ONH Overall"),
    ("large", "Large Vessels", "ONH Large Vessels"),
    ("small", "Small Vessels", "ONH Small Vessels"),
]

ONH_VIEW_TO_KEY = {
    "Overall": "overall",
    "Large Vessels": "large",
    "Small Vessels": "small",
}

RIGHT_EYE = "Right Eye"
ONH_BRANCHPOINT_MIN_LINK_LENGTH_PX = 15.0
ONH_TORTUOSITY_MIN_LINK_LENGTH_PX = 15.0


class ONHBiomarkerAnalyzer:
    """
    Compute ONH biomarkers for overall, large-vessel, and small-vessel masks.

    ONH metrics use the annulus ROI area from canvas.onh_mask_arr as the
    denominator. Retina's BiomarkerAnalyzer is intentionally untouched.
    """

    @staticmethod
    def process(canvas: Canvas) -> None:
        if not hasattr(canvas, "onh_mask_arr"):
            raise ValueError("No ONH annulus mask found for ONH biomarker calculation.")

        metrics_by_type = {}
        diameters_by_type = {}
        summary_rows = []

        for key, label, sheet_name in ONH_METRIC_TYPES:
            binary = getattr(canvas, f"onh_binary_{key}", None)
            skeleton = getattr(canvas, f"onh_skeleton_{key}", None)
            nodes = getattr(canvas, f"onh_skeleton_nodes_{key}", [])
            links = getattr(canvas, f"onh_skeleton_links_{key}", [])

            if binary is None and key == "overall" and hasattr(canvas, "binary_image"):
                binary = canvas.binary_image

            if skeleton is None and key == "overall" and hasattr(canvas, "skeleton_image"):
                skeleton = canvas.skeleton_image
                nodes = getattr(canvas, "skeleton_nodes", [])
                links = getattr(canvas, "skeleton_links", [])

            if binary is None or skeleton is None:
                print(f"Skipping ONH {label} metrics: missing binary or skeleton image.")
                continue

            metrics, diameters_um = ONHBiomarkerAnalyzer.compute_metrics(
                canvas,
                binary=binary,
                skeleton=skeleton,
                nodes=nodes,
                links=links,
                vessel_type=label,
            )

            metrics_by_type[key] = metrics
            diameters_by_type[key] = diameters_um

            write_excel(
                ONHBiomarkerAnalyzer._excel_row(metrics),
                canvas.lastMetricsPath,
                sheet_name=sheet_name,
                replace_sheet=True,
            )

            summary_rows.append(ONHBiomarkerAnalyzer._summary_row(metrics))

        if summary_rows:
            write_excel(
                pd.DataFrame(summary_rows),
                canvas.lastMetricsPath,
                sheet_name="ONH Summary",
                replace_sheet=True,
            )

        canvas.onh_metrics_by_type = metrics_by_type
        canvas.onh_diameters_by_type = diameters_by_type

        selected_view = "Overall"
        if hasattr(canvas, "onh_segmentation_view_var"):
            selected_view = canvas.onh_segmentation_view_var.get()
        selected_key = ONH_VIEW_TO_KEY.get(selected_view, "overall")

        selected_metrics = metrics_by_type.get(selected_key) or metrics_by_type.get("overall")
        if selected_metrics:
            ONHBiomarkerAnalyzer._update_canvas_metrics(canvas, selected_metrics)
            ONHBiomarkerAnalyzer._update_gui(canvas, selected_metrics)

        selected_diameters = diameters_by_type.get(selected_key)
        if selected_diameters is None:
            selected_diameters = diameters_by_type.get("overall", np.asarray([], dtype=float))
        canvas.vessel_diameters_um = selected_diameters

        print("ONH biomarker analysis completed for:", list(metrics_by_type.keys()))

    @staticmethod
    def process_subregions(canvas: Canvas, divider: str = "quadrant") -> None:
        if not hasattr(canvas, "onh_mask_arr"):
            raise ValueError(f"No ONH annulus mask found for ONH {divider} analysis.")

        if not hasattr(canvas, "onh_center"):
            raise ValueError(f"No ONH center found for ONH {divider} analysis.")

        QUADRANT_NAMES = ("TEMP", "SUP", "NASAL", "INF")
        OCTANT_NAMES = ("ST", "SN", "NS", "NI", "IN", "IT", "TI", "TS")
        
        if divider == "quadrant":
            region_masks = ONHBiomarkerAnalyzer.make_quadrant_masks(canvas)
            REGION_NAMES = QUADRANT_NAMES
        else:
            region_masks = ONHBiomarkerAnalyzer.make_octant_masks(canvas)
            REGION_NAMES = OCTANT_NAMES
        
        center_x, center_y = canvas.onh_center
        eye = canvas.eye_var.get() if hasattr(canvas, "eye_var") else RIGHT_EYE
        eye_code = "OD" if eye == RIGHT_EYE else "OS"
        regional_rows = []

        for region_name in REGION_NAMES:
            region_mask = region_masks[region_name]

            for key, label, _sheet_name in ONH_METRIC_TYPES:
                binary = getattr(canvas, f"onh_binary_{key}", None)
                skeleton = getattr(canvas, f"onh_skeleton_{key}", None)
                nodes = getattr(canvas, f"onh_skeleton_nodes_{key}", [])
                links = getattr(canvas, f"onh_skeleton_links_{key}", [])

                if binary is None or skeleton is None:
                    print(
                        f"Skipping ONH {region_name} {label} metrics: "
                        "missing binary or skeleton image."
                    )
                    continue

                metrics, _diameters_um = ONHBiomarkerAnalyzer.compute_metrics(
                    canvas,
                    binary=binary,
                    skeleton=skeleton,
                    nodes=nodes,
                    links=links,
                    vessel_type=label,
                    roi_mask=region_mask,
                    region_name=region_name,
                    eye=eye,
                    eye_code=eye_code,
                    onh_center=(center_x, center_y),
                )
                regional_rows.append(ONHBiomarkerAnalyzer._regional_excel_row(metrics))

        if regional_rows:
            write_excel(
                pd.DataFrame(regional_rows),
                canvas.lastMetricsPath,
                sheet_name=f"ONH regional_{divider}",
                replace_sheet=True,
            )
            canvas.onh_regional_metrics = regional_rows

        print(f"ONH {divider} analysis completed.")

    @staticmethod
    def make_quadrant_masks(canvas: Canvas) -> dict[str, np.ndarray]:
        annulus_mask = canvas.onh_mask_arr.astype(bool)
        height, width = annulus_mask.shape
        center_x, center_y = canvas.onh_center

        rows, cols = np.indices((height, width))
        angles = np.degrees(np.arctan2(-(rows - center_y), cols - center_x))

        eye = canvas.eye_var.get() if hasattr(canvas, "eye_var") else RIGHT_EYE
        if eye == RIGHT_EYE:
            region_centers = {
                "TEMP": 180.0,
                "SUP": 90.0,
                "NASAL": 0.0,
                "INF": -90.0,
            }
        else:
            region_centers = {
                "TEMP": 0.0,
                "SUP": 90.0,
                "NASAL": 180.0,
                "INF": -90.0,
            }

        region_names = ("TEMP", "SUP", "NASAL", "INF")
        distances = []
        for region_name in region_names:
            center_angle = region_centers[region_name]
            dist = np.abs((angles - center_angle + 180.0) % 360.0 - 180.0)
            distances.append(dist)

        nearest_region = np.argmin(np.stack(distances, axis=0), axis=0)

        return {
            region_name: annulus_mask & (nearest_region == idx)
            for idx, region_name in enumerate(region_names)
        }

    @staticmethod
    def make_octant_masks(canvas: Canvas) -> dict[str, np.ndarray]:
        annulus_mask = canvas.onh_mask_arr.astype(bool)
        height, width = annulus_mask.shape
        center_x, center_y = canvas.onh_center

        rows, cols = np.indices((height, width))
        angles = np.degrees(np.arctan2(-(rows - center_y), cols - center_x))

        eye = canvas.eye_var.get() if hasattr(canvas, "eye_var") else RIGHT_EYE
        if eye == RIGHT_EYE:
            region_centers = {
                "ST": 112.5,
                "SN": 67.5,
                "NS": 22.5,
                "NI": -22.5,
                "IN": -67.5,
                "IT": -112.5,
                "TI": -157.5,
                "TS": 157.5,
            }
        else:
            region_centers = {
                "ST": 67.5,
                "SN": 112.5,
                "NS": 157.5,
                "NI": -157.5,
                "IN": -112.5,
                "IT": -67.5,
                "TI": -22.5,
                "TS": 22.5,
            }

        region_names = ("ST", "SN", "NS", "NI", "IN", "IT", "TI", "TS")
        distances = []
        for region_name in region_names:
            center_angle = region_centers[region_name]
            dist = np.abs((angles - center_angle + 180.0) % 360.0 - 180.0)
            distances.append(dist)

        nearest_region = np.argmin(np.stack(distances, axis=0), axis=0)

        return {
            region_name: annulus_mask & (nearest_region == idx)
            for idx, region_name in enumerate(region_names)
        }
    
    @staticmethod
    def compute_metrics(
        canvas: Canvas,
        binary: np.ndarray,
        skeleton: np.ndarray,
        nodes,
        links,
        vessel_type: str,
        roi_mask: np.ndarray | None = None,
        region_name: str | None = None,
        eye: str | None = None,
        eye_code: str | None = None,
        onh_center: tuple[float, float] | None = None,
    ) -> tuple[dict, np.ndarray]:
        if roi_mask is None:
            roi_mask = canvas.onh_mask_arr.astype(bool)
        else:
            roi_mask = roi_mask.astype(bool)

        if binary.shape != roi_mask.shape:
            raise ValueError(f"ONH {vessel_type} binary image and ROI mask have different sizes.")

        if skeleton.shape != roi_mask.shape:
            raise ValueError(f"ONH {vessel_type} skeleton image and ROI mask have different sizes.")

        binary_mask = (binary > 0) & roi_mask
        skeleton_mask = (skeleton > 0) & roi_mask
        full_onh_mask = canvas.onh_mask_arr.astype(bool)
        diameter_binary_mask = (binary > 0) & full_onh_mask

        height, width = binary_mask.shape
        image_size_mm = float(canvas.image_size_var.get())
        pixel_size_mm = image_size_mm / float(width) if width > 0 else 0.0
        pixel_area_mm2 = pixel_size_mm ** 2

        roi_area_pixels = int(np.count_nonzero(roi_mask))
        roi_area_mm2 = float(roi_area_pixels * pixel_area_mm2)

        if roi_area_pixels == 0 or roi_area_mm2 <= 0:
            raise ValueError("ONH ROI area is zero. Please check the ONH mask.")

        vessel_pixels = int(np.count_nonzero(binary_mask))
        vessel_area_mm2 = float(vessel_pixels * pixel_area_mm2)
        vessel_area_density_pct = float(vessel_pixels / roi_area_pixels * 100.0)

        total_length_pixels = ONHBiomarkerAnalyzer._link_length_pixels(
            links,
            binary_mask.shape,
            skeleton_mask,
            update_links=region_name is None,
        )
        total_length_mm = float(total_length_pixels * pixel_size_mm)
        vessel_length_density = float(total_length_mm / roi_area_mm2)

        diameters_um = ONHBiomarkerAnalyzer._sample_diameters_um(
            diameter_binary_mask,
            skeleton_mask,
            links,
            pixel_size_mm,
            roi_mask,
        )
        mean_diameter_um = float(np.mean(diameters_um)) if diameters_um.size > 0 else 0.0

        # Branchpoint density and fractal dimension were tested during ONH
        # development, but they are not calculated in the final ONH output
        # because the annulus ROI can cut vessels at the inner and outer
        # boundaries, making these metrics less interpretable.
        #
        # valid_branch_link_indices = ONHBiomarkerAnalyzer._valid_link_indices(
        #     links,
        #     binary_mask.shape,
        #     roi_mask,
        #     min_link_length_px=ONH_BRANCHPOINT_MIN_LINK_LENGTH_PX,
        # )
        #
        # branchpoint_count = ONHBiomarkerAnalyzer._branchpoint_count(
        #     nodes,
        #     binary_mask.shape,
        #     roi_mask,
        #     valid_link_indices=valid_branch_link_indices,
        # )
        # branchpoint_density_per_mm2 = float(branchpoint_count / roi_area_mm2)
        # branchpoint_density_per_mm = (
        #     float(branchpoint_count / total_length_mm) if total_length_mm > 0 else 0.0
        # )
        #
        # fractal_dimension = ONHBiomarkerAnalyzer._box_counting_fractal_dimension(
        #     skeleton_mask
        # )

        mean_tortuosity, valid_tortuosity_link_count = ONHBiomarkerAnalyzer._mean_tortuosity(
            links,
            binary_mask.shape,
            roi_mask,
            min_link_length_px=ONH_TORTUOSITY_MIN_LINK_LENGTH_PX,
            update_links=region_name is None,
        )

        metrics = {
            "name": canvas.FileLabelName,
            "eye": eye,
            "eye_code": eye_code,
            "region_name": region_name,
            "vessel_type": vessel_type,
            "vessel_area_density_pct": round(vessel_area_density_pct, 2),
            "vessel_area_mm2": float(vessel_area_mm2),
            "onh_roi_area_mm2": float(roi_area_mm2),
            "onh_roi_area_pixels": int(roi_area_pixels),
            "vessel_length_mm": float(total_length_mm),
            "vessel_length_density_mm_per_mm2": float(vessel_length_density),
            "mean_diameter_um": float(mean_diameter_um),
            "mean_tortuosity": float(mean_tortuosity),
            "tortuosity_min_link_length_px": float(ONH_TORTUOSITY_MIN_LINK_LENGTH_PX),
            "raw_link_count": int(len(links)) if links is not None else 0,
            "valid_tortuosity_link_count": int(valid_tortuosity_link_count),
        }

        if onh_center is not None:
            metrics["onh_center_x_pos"] = float(onh_center[0])
            metrics["onh_center_y_pos"] = float(onh_center[1])

        return metrics, diameters_um

    @staticmethod
    def _link_length_pixels(
        links,
        image_shape,
        skeleton_mask: np.ndarray,
        update_links: bool = True,
    ) -> float:
        total_length_pixels = 0.0

        if links is not None and len(links) > 0:
            for link in links:
                indices = np.asarray(link.path, dtype=int)

                if indices.size < 2:
                    continue

                rows, cols = np.unravel_index(indices, image_shape)
                coords = np.column_stack((rows, cols)).astype(float)
                valid = skeleton_mask[rows, cols]
                diffs = np.diff(coords, axis=0)
                step_lengths = np.linalg.norm(diffs, axis=1)
                valid_steps = valid[:-1] & valid[1:]
                length_pixels = float(step_lengths[valid_steps].sum())

                total_length_pixels += length_pixels
                if update_links:
                    link.pixLength = length_pixels
        else:
            total_length_pixels = float(np.count_nonzero(skeleton_mask))

        return total_length_pixels

    @staticmethod
    def _link_length_pixels_in_roi(
        link,
        image_shape,
        roi_mask: np.ndarray,
    ) -> float:
        indices = np.asarray(getattr(link, "path", []), dtype=int)

        if indices.size < 2:
            return 0.0

        rows, cols = np.unravel_index(indices, image_shape)
        coords = np.column_stack((rows, cols)).astype(float)
        valid = roi_mask[rows, cols]
        diffs = np.diff(coords, axis=0)
        step_lengths = np.linalg.norm(diffs, axis=1)
        valid_steps = valid[:-1] & valid[1:]

        return float(step_lengths[valid_steps].sum())

    @staticmethod
    def _valid_link_indices(
        links,
        image_shape,
        roi_mask: np.ndarray,
        min_link_length_px: float,
    ) -> set[int]:
        valid_indices = set()

        if links is None:
            return valid_indices

        for link_idx, link in enumerate(links):
            length_pixels = ONHBiomarkerAnalyzer._link_length_pixels_in_roi(
                link,
                image_shape,
                roi_mask,
            )

            if length_pixels >= min_link_length_px:
                valid_indices.add(link_idx)

        return valid_indices

    @staticmethod
    def _sample_diameters_um(
        binary_mask: np.ndarray,
        skeleton_mask: np.ndarray,
        links,
        pixel_size_mm: float,
        roi_mask: np.ndarray,
    ) -> np.ndarray:
        radius_map = distance_transform_edt(binary_mask)
        diameter_map_pixels = radius_map * 2.0

        sampled_diameters_pixels = []

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

                sampled_diameters_pixels.extend(diameter_map_pixels[rows, cols])
        else:
            sampled_diameters_pixels.extend(diameter_map_pixels[skeleton_mask])

        sampled = np.asarray(sampled_diameters_pixels, dtype=float)
        return sampled * pixel_size_mm * 1000.0

    @staticmethod
    def _branchpoint_count(
        nodes,
        image_shape,
        roi_mask: np.ndarray,
        valid_link_indices: set[int] | None = None,
    ) -> int:
        if nodes is None:
            return 0

        branchpoint_count = 0

        for node in nodes:
            if getattr(node, "ep", 0) != 0:
                continue

            indices = np.asarray(getattr(node, "nodes_idx", []), dtype=int)
            if indices.size == 0:
                continue

            rows, cols = np.unravel_index(indices, image_shape)
            if not np.any(roi_mask[rows, cols]):
                continue

            if valid_link_indices is not None:
                connected_valid_links = [
                    link_idx for link_idx in getattr(node, "links", [])
                    if int(link_idx) in valid_link_indices
                ]

                if len(connected_valid_links) < 2:
                    continue

            branchpoint_count += 1

        return branchpoint_count

    @staticmethod
    def _mean_tortuosity(
        links,
        image_shape,
        roi_mask: np.ndarray,
        min_link_length_px: float = 0.0,
        update_links: bool = True,
    ) -> tuple[float, int]:
        tortuosity_values = []
        valid_link_count = 0

        if links is None:
            return 0.0, 0

        for link in links:
            indices = np.asarray(link.path, dtype=int)

            if indices.size < 3:
                continue

            length_pixels = ONHBiomarkerAnalyzer._link_length_pixels_in_roi(
                link,
                image_shape,
                roi_mask,
            )

            if length_pixels < min_link_length_px:
                continue

            rows, cols = np.unravel_index(indices, image_shape)
            valid = roi_mask[rows, cols]

            valid_runs = ONHBiomarkerAnalyzer._valid_coord_runs(rows, cols, valid)
            link_tortuosities = []

            for run_rows, run_cols in valid_runs:
                if run_rows.size < 3:
                    continue

                coords_pixels = np.column_stack((run_rows, run_cols)).astype(float)
                diffs = np.diff(coords_pixels, axis=0)
                arc_length_pixels = float(np.sum(np.linalg.norm(diffs, axis=1)))
                chord_length_pixels = float(np.linalg.norm(coords_pixels[-1] - coords_pixels[0]))

                if chord_length_pixels > 1e-6 and arc_length_pixels >= 3:
                    tortuosity = arc_length_pixels / chord_length_pixels
                    if np.isfinite(tortuosity) and 1.0 <= tortuosity <= 20.0:
                        tortuosity_values.append(tortuosity)
                        link_tortuosities.append(tortuosity)

            if update_links and link_tortuosities:
                link.tortuosity = float(np.mean(link_tortuosities))

            if link_tortuosities:
                valid_link_count += 1

        mean_tortuosity = float(np.mean(tortuosity_values)) if tortuosity_values else 0.0
        return mean_tortuosity, valid_link_count

    @staticmethod
    def _valid_coord_runs(rows: np.ndarray, cols: np.ndarray, valid: np.ndarray):
        runs = []
        start = None

        for idx, is_valid in enumerate(valid):
            if is_valid and start is None:
                start = idx
            elif not is_valid and start is not None:
                runs.append((rows[start:idx], cols[start:idx]))
                start = None

        if start is not None:
            runs.append((rows[start:], cols[start:]))

        return runs

    @staticmethod
    def _box_counting_fractal_dimension(Z: np.ndarray) -> float:
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

        counts.append(np.count_nonzero(current_img))
        box_sizes.append(1)

        for i in range(1, exponent + 1):
            rows, cols = current_img.shape

            if rows < 2 or cols < 2:
                break

            current_img = current_img.reshape(
                rows // 2,
                2,
                cols // 2,
                2,
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
        return float(coeffs[0])

    @staticmethod
    def _excel_row(metrics: dict) -> dict:
        return {
            "name": metrics["name"],
            "Vessel type": metrics["vessel_type"],
            "Vessel area density": metrics["vessel_area_density_pct"],
            "Vessel length density": metrics["vessel_length_density_mm_per_mm2"],
            "Mean diameter": metrics["mean_diameter_um"],
            "Mean tortuosity": metrics["mean_tortuosity"],
            "Vessel area mm2": metrics["vessel_area_mm2"],
            "ONH ROI area mm2": metrics["onh_roi_area_mm2"],
            "Vessel length mm": metrics["vessel_length_mm"],
            "Tortuosity min link length px": metrics["tortuosity_min_link_length_px"],
            "Raw link count": metrics["raw_link_count"],
            "Valid tortuosity link count": metrics["valid_tortuosity_link_count"],
        }

    @staticmethod
    def _summary_row(metrics: dict) -> dict:
        row = ONHBiomarkerAnalyzer._excel_row(metrics)
        row.pop("Vessel type", None)
        row["vessel_type"] = metrics["vessel_type"]
        return row

    @staticmethod
    def _regional_excel_row(metrics: dict) -> dict:
        row = {
            "name": metrics["name"],
            "Eye": metrics.get("eye"),
            "Eye code": metrics.get("eye_code"),
            "ONH center x [pos]": metrics.get("onh_center_x_pos"),
            "ONH center y [pos]": metrics.get("onh_center_y_pos"),
            "region_name": metrics.get("region_name"),
            "vessel_type": metrics["vessel_type"],
        }
        metric_row = ONHBiomarkerAnalyzer._excel_row(metrics)
        metric_row.pop("name", None)
        metric_row.pop("Vessel type", None)
        row.update(metric_row)
        return row

    @staticmethod
    def _update_canvas_metrics(canvas: Canvas, metrics: dict) -> None:
        if not hasattr(canvas, "metrics"):
            canvas.metrics = {}

        canvas.metrics.update({
            "vessel_type": metrics["vessel_type"],
            "vessel_area_density_pct": metrics["vessel_area_density_pct"],
            "vessel_area_mm2": metrics["vessel_area_mm2"],
            "image_area_mm2": metrics["onh_roi_area_mm2"],
            "vessel_length_density_mm_per_mm2": metrics["vessel_length_density_mm_per_mm2"],
            "mean_diameter_um": metrics["mean_diameter_um"],
            "mean_tortuosity": metrics["mean_tortuosity"],
        })

    @staticmethod
    def _update_gui(canvas: Canvas, metrics: dict) -> None:
        if hasattr(canvas, "vad_value_id"):
            canvas.itemconfig(
                canvas.vad_value_id,
                text=f"{metrics['vessel_area_density_pct']:.2f} %",
            )

        if hasattr(canvas, "length_density_value_id"):
            canvas.itemconfig(
                canvas.length_density_value_id,
                text=f"{metrics['vessel_length_density_mm_per_mm2']:.2f}",
            )

        if hasattr(canvas, "mean_diameter_value_id"):
            canvas.itemconfig(
                canvas.mean_diameter_value_id,
                text=f"{metrics['mean_diameter_um']:.2f} um",
            )

        # Branchpoint density and fractal dimension are not displayed for the
        # final ONH output. The original canvas labels remain for the Retina
        # workflow.

        if hasattr(canvas, "tortuosity_value_id"):
            canvas.itemconfig(
                canvas.tortuosity_value_id,
                text=f"{metrics['mean_tortuosity']:.3f}",
            )
