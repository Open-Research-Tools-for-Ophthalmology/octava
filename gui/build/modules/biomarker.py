# modules/biomarker.py

import numpy as np
import math
from tkinter import Canvas


class BiomarkerAnalyzer:
    """
    Calculates Vessel Area Density (VAD) mirroring MATLAB logic.
    Updates canvas.metrics and GUI display directly.
    """

    @staticmethod
    def process(canvas: Canvas) -> None:
        # --- Input Data ---

        binary = canvas.binary_image
        skeleton = canvas.skeleton_image
        nodes = canvas.skeleton_nodes
        links = canvas.skeleton_links
        Nx, Ny = binary.shape
        image_size_mm = float(canvas.image_size_var.get())

        # --- Retrieve Image Parameters ---

        # Determine Image Type (Retina/ONH vs Skin/Other)
        img_type = canvas.img_type_var.get() if hasattr(canvas, "img_type_var") else None

        # --- Determine Effective Area (Pixels) ---

        img_area_pix = float(Nx * Nx)


        # --- Calculate VAD (%) ---
        # Normalize sum of white pixels (255 -> 1)
        vessel_sum = float(np.sum(binary))
        vessel_pixels = vessel_sum / 255.0

        vad_pct = round(vessel_pixels / img_area_pix * 100.0, 2)

        # --- Calculate Physical Metrics (mm²) ---
        if Nx > 0:
            pix_size_mm = image_size_mm / Nx
        else:
            pix_size_mm = 0.0


        img_area_mm2 = img_area_pix * (pix_size_mm ** 2)
        vessel_area_mm2 = vessel_pixels * (pix_size_mm ** 2)

        skel_mask = (skeleton > 0)


        # --- Calculate Vessel Length Density ---

        total_length_pix = 0.0

        for link in links:
            # 1D indices into the binary image
            indices = np.asarray(link.path, dtype=int)
            if indices.size < 2:
                continue

            # Convert flat indices to (row, col)
            rows, cols = np.unravel_index(indices, binary.shape)
            coords = np.column_stack((rows, cols)).astype(float)

            # Euclidean length along the path (in pixels)
            diffs = np.diff(coords, axis=0)
            step_lengths = np.linalg.norm(diffs, axis=1)
            length_pix = float(step_lengths.sum())

            total_length_pix += length_pix

            # Optional: store per-link length in pixels
            link.pixLength = length_pix

        # Pixels -> mm
        total_length_mm = total_length_pix * pix_size_mm

        # Length density (mm per mm²), using image_size_mm²
        length_area_mm2 = image_size_mm ** 2
        vessel_length_density = total_length_mm / length_area_mm2



        # --- Mean Diameter ---
        from scipy.ndimage import distance_transform_edt

        # Binary vessel mask
        vessel_mask = (binary > 0)

        if np.any(vessel_mask):
            # Local thickness map in pixels (like D = bwdist(~L) * 2)
            thickness_map = distance_transform_edt(vessel_mask) * 2.0  # pixels
            thickness_flat = thickness_map.ravel()

            diameters_um = []

            for link in links:
                # link.path is a 1D index array into the image (MATLAB: Glinks(i).point)
                indices = np.asarray(link.path, dtype=int)
                if indices.size == 0:
                    continue

                # Diameter values along this link (pixels)
                diam_vals_pix = thickness_flat[indices]
                if diam_vals_pix.size == 0:
                    continue

                # Mean diameter for this link (pixels)
                link_diam_pix = float(diam_vals_pix.mean())

                # Optional: store back on the link (like MATLAB)
                link.diameterMeasurements = diam_vals_pix
                link.diameter = link_diam_pix

                # Convert to microns (pix -> mm -> µm)
                link_diam_um = link_diam_pix * pix_size_mm * 1000.0
                diameters_um.append(link_diam_um)

            if diameters_um:
                mean_diameter_um = float(round(np.mean(diameters_um), 2))
            else:
                mean_diameter_um = 0.0
        else:
            mean_diameter_um = 0.0

        # --- Calculate Branchpoint Density (Exact MATLAB Logic) ---


        
        branchpoint_count = 0
        if nodes is not None:
            for node in nodes:

                if node.ep == 0:
                    branchpoint_count += 1

        
        if total_length_mm > 0.0:
            branchpoint_density = branchpoint_count / total_length_mm
        else:
            branchpoint_density = 0.0




        # --- Calculate Mean Tortuosity ---
        mean_tortuosity = 0.0

        tortuosities = []

        if links is not None:
            for link in links:
                try:
                    # 这里假设 link 有 coords 属性 / 字段，是 N x 2 (row, col)
                    coords = np.asarray(getattr(link, "coords", None), dtype=float)

                    if coords is None or coords.shape[0] < 2:
                        continue

                    # Path length in pixels
                    diffs = np.diff(coords, axis=0)
                    step_lengths = np.linalg.norm(diffs, axis=1)
                    path_len_pix = float(np.sum(step_lengths))

                    # Chord length in pixels (first to last point)
                    chord_len_pix = float(np.linalg.norm(coords[-1] - coords[0]))

                    if chord_len_pix > 0.0 and path_len_pix > 0.0:
                        tort = path_len_pix / chord_len_pix
                        tortuosities.append(tort)
                except Exception:
                    # 如果这个 link 结构不符合预期，就跳过它
                    continue

        if len(tortuosities) > 0:
            mean_tortuosity = float(np.mean(tortuosities))
        else:
            mean_tortuosity = 0.0



        # --- Store Metrics in Canvas ---
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

        # --- Update GUI Display ---
        # VAD
        if hasattr(canvas, "vad_value_id"):
            canvas.itemconfig(canvas.vad_value_id, text=f"{vad_pct:.2f} %")

        # Vessel length density (mm/mm²)
        if hasattr(canvas, "length_density_value_id"):
            canvas.itemconfig(canvas.length_density_value_id,
                              text=f"{vessel_length_density:.2f} %")

        # Mean diameter (mm)
        if hasattr(canvas, "mean_diameter_value_id"):
            canvas.itemconfig(canvas.mean_diameter_value_id,
                              text=f"{mean_diameter_um:.2f} µm")

        # Branchpoint count
        if hasattr(canvas, "branch_count_value_id"):
            canvas.itemconfig(canvas.branch_count_value_id,
                              text=f"{branchpoint_count:d}")

        # Branchpoint density (per mm²)
        if hasattr(canvas, "branch_density_value_id"):
            canvas.itemconfig(canvas.branch_density_value_id,
                              text=f"{branchpoint_density:.2f} (1/mm)")

        # Fractal dimension
        if hasattr(canvas, "fractal_dim_value_id"):
            canvas.itemconfig(canvas.fractal_dim_value_id,
                              text=f"{fractal_dim:.3f}")

        # Mean tortuosity
        if hasattr(canvas, "tortuosity_value_id"):
            canvas.itemconfig(canvas.tortuosity_value_id,
                              text=f"{mean_tortuosity:.3f}")
