# modules/biomarker.py

import numpy as np
import math
from tkinter import Canvas
from scipy.ndimage import distance_transform_edt
from modules.write_excel import *


class BiomarkerAnalyzer:
    """
    Compute vessel biomarkers from the current canvas state.
    Results are stored in canvas.metrics and shown in the GUI.
    """

    @staticmethod
    def process(canvas: Canvas) -> None:
        # Read input data from canvas
        binary = canvas.binary_image
        skeleton = canvas.skeleton_image
        nodes = canvas.skeleton_nodes
        links = canvas.skeleton_links

        Nx, Ny = binary.shape
        image_size_mm = float(canvas.image_size_var.get())

        # Read optional image type from GUI
        img_type = canvas.img_type_var.get() if hasattr(canvas, "img_type_var") else None

        # Image area in pixels
        img_area_pix = float(Nx * Nx)

        # Vessel Area Density (VAD %)
        vessel_sum = float(np.sum(binary))
        vessel_pixels = vessel_sum / 255.0
        vad_pct = round(vessel_pixels / img_area_pix * 100.0, 2)

        # Pixel size and physical areas (mm²)
        if Nx > 0:
            pix_size_mm = image_size_mm / Nx
        else:
            pix_size_mm = 0.0

        img_area_mm2 = img_area_pix * (pix_size_mm ** 2)
        vessel_area_mm2 = vessel_pixels * (pix_size_mm ** 2)

        skel_mask = (skeleton > 0)

        # Vessel length density (mm per mm²)
        total_length_pix = 0.0

        for link in links:
            indices = np.asarray(link.path, dtype=int)
            if indices.size < 2:
                continue

            rows, cols = np.unravel_index(indices, binary.shape)
            coords = np.column_stack((rows, cols)).astype(float)

            diffs = np.diff(coords, axis=0)
            step_lengths = np.linalg.norm(diffs, axis=1)
            length_pix = float(step_lengths.sum())

            total_length_pix += length_pix
            link.pixLength = length_pix

        total_length_mm = total_length_pix * pix_size_mm
        length_area_mm2 = image_size_mm ** 2
        vessel_length_density = total_length_mm / length_area_mm2

        # Mean diameter (output: μm)
        if Nx > 0:
            pix_size_mm = image_size_mm / Nx
        else:
            pix_size_mm = 0.0

        radius_map = distance_transform_edt(binary > 0)
        diameter_map = radius_map * 2

        all_sampled_diameters = []
        img_shape = (Nx, Ny)

        for link in links:
            indices = np.asarray(link.path, dtype=int)
            if indices.size == 0:
                continue

            rows, cols = np.unravel_index(indices, img_shape)
            vals = diameter_map[rows, cols]
            all_sampled_diameters.extend(vals)

        total_points = len(all_sampled_diameters)

        diameters_pix = np.asarray(all_sampled_diameters, dtype=float)
        diameters_um = diameters_pix * pix_size_mm * 1000.0
        canvas.vessel_diameters_um = diameters_um

        if total_points > 0:
            mean_diameter_pix = np.mean(all_sampled_diameters)
            mean_diameter_mm = mean_diameter_pix * pix_size_mm
            mean_diameter_um = mean_diameter_mm * 1000.0
        else:
            mean_diameter_um = 0.0

        # Branchpoint density
        branchpoint_count = 0
        if nodes is not None:
            for node in nodes:
                if node.ep == 0:
                    branchpoint_count += 1

        if total_length_mm > 0.0:
            branchpoint_density = branchpoint_count / total_length_mm
        else:
            branchpoint_density = 0.0

        # Fractal dimension
        Z = (skeleton > 0)

        h, w = Z.shape
        Nx = max(h, w)

        if Nx < 2:
            fractal_dim = 0.0
        else:
            import math

            exponent = math.ceil(math.log2(Nx))
            width = 2 ** exponent

            Z_pad = np.zeros((width, width), dtype=bool)
            Z_pad[:h, :w] = Z

            counts = []
            r_values = []

            counts.append(np.sum(Z_pad))
            r_values.append(1)

            current_img = Z_pad

            for i in range(1, exponent + 1):
                rows, cols = current_img.shape
                if rows < 2 or cols < 2:
                    break

                shrunk_img = current_img.reshape(rows // 2, 2, cols // 2, 2).max(axis=(1, 3))

                n_box = np.sum(shrunk_img)
                counts.append(n_box)
                r_values.append(2 ** i)

                current_img = shrunk_img

            valid_indices = [i for i, c in enumerate(counts) if c > 0]

            if len(valid_indices) >= 2:
                x = np.log([r_values[i] for i in valid_indices])
                y = -np.log([counts[i] for i in valid_indices])

                coeffs = np.polyfit(x, y, 1)
                fractal_dim = float(coeffs[0])
            else:
                fractal_dim = 0.0

        # Mean tortuosity
        tortuosity_list = []
        image_shape = binary.shape

        for link in links:
            indices = np.asarray(link.path, dtype=int)
            if indices.size < 2:
                continue

            rows, cols = np.unravel_index(indices, image_shape)
            coords = np.column_stack((rows, cols)).astype(float)

            diffs = np.diff(coords, axis=0)
            arc_length = np.sum(np.linalg.norm(diffs, axis=1))

            start_point = coords[0]
            end_point = coords[-1]
            chord_length = np.linalg.norm(start_point - end_point)

            if chord_length > 1e-6:
                tortuosity = arc_length / chord_length
                tortuosity_list.append(tortuosity)

        if len(tortuosity_list) > 0:
            mean_tortuosity = np.mean(tortuosity_list)
        else:
            mean_tortuosity = 0.0

        # Store metrics in canvas
        if not hasattr(canvas, "metrics"):
            canvas.metrics = {}

        canvas.metrics.update({
            "vessel_area_density_pct": float(vad_pct),
            "vessel_area_mm2": float(vessel_area_mm2),
            "image_area_mm2": float(img_area_mm2),
            "vessel_length_density_mm_per_mm2": float(vessel_length_density),
            "mean_diameter_um": float(mean_diameter_um),
            "branchpoint_count": int(branchpoint_count),
            "branchpoint_density_per_mm2": float(branchpoint_density),
            "fractal_dimension": float(fractal_dim),
            "mean_tortuosity": float(mean_tortuosity),
        })
        micro_stats = {
            "name": canvas.FileLabelName,
            "Vessel area density": float(vad_pct),
            "Vessel length density": float(vessel_length_density),
            "Mean vessel diameter": float(mean_diameter_um),
            "Branchpoint density": float(branchpoint_density),
            "Fractal dimension": float(fractal_dim),
            "Mean vessel tortuosity": float(mean_tortuosity),
        }
        
        write_excel(micro_stats, canvas.lastMetricsPath, sheet_name="General metrics")

        # Update GUI display
        if hasattr(canvas, "vad_value_id"):
            canvas.itemconfig(canvas.vad_value_id, text=f"{vad_pct:.2f} %")

        if hasattr(canvas, "length_density_value_id"):
            canvas.itemconfig(
                canvas.length_density_value_id,
                text=f"{vessel_length_density:.2f} %",
            )

        if hasattr(canvas, "mean_diameter_value_id"):
            canvas.itemconfig(
                canvas.mean_diameter_value_id,
                text=f"{mean_diameter_um:.2f} µm",
            )

        if hasattr(canvas, "branch_count_value_id"):
            canvas.itemconfig(canvas.branch_count_value_id, text=f"{branchpoint_count:d}")

        if hasattr(canvas, "branch_density_value_id"):
            canvas.itemconfig(
                canvas.branch_density_value_id,
                text=f"{branchpoint_density:.2f} (1/mm)",
            )

        if hasattr(canvas, "fractal_dim_value_id"):
            canvas.itemconfig(canvas.fractal_dim_value_id, text=f"{fractal_dim:.3f}")

        if hasattr(canvas, "tortuosity_value_id"):
            canvas.itemconfig(canvas.tortuosity_value_id, text=f"{mean_tortuosity:.3f}")
