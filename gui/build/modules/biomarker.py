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
        # Logic: Retina/ONH uses Circular FOV, others use Rectangular
        if img_type in ("Retina", "ONH"):
            # MATLAB logic: Area = pi * (radius)^2
            radius_pix = Nx / 2.0
            img_area_pix = math.pi * (radius_pix ** 2)
        else:
            # MATLAB logic: Area = Nx * Nx (assuming square)
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



        # --- Calculate Vessel Length Density (mm/mm²) ---

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




        # --- Mean / Median Diameter (mm) ---
        from scipy.ndimage import distance_transform_edt

        vessel_mask = (binary > 0)
        if np.any(vessel_mask):
            dist_map = distance_transform_edt(vessel_mask)

            # define skeleton mask here
            skel_mask = (skeleton > 0)

            radii_pix = dist_map[skel_mask]

            if radii_pix.size > 0:
                diameters_mm = 2.0 * radii_pix * pix_size_mm
                mean_diameter_mm = float(np.mean(diameters_mm))
                median_diameter_mm = float(np.median(diameters_mm))
            else:
                mean_diameter_mm = 0.0
                median_diameter_mm = 0.0
        else:
            mean_diameter_mm = 0.0
            median_diameter_mm = 0.0


        # --- Calculate Branchpoint Density (per mm²) ---
        from scipy.ndimage import convolve

        # 8-connected neighbor kernel
        kernel = np.array([[1, 1, 1],
                           [1, 0, 1],
                           [1, 1, 1]], dtype=np.uint8)

        skel_uint = skel_mask.astype(np.uint8)
        neighbor_count = convolve(skel_uint, kernel, mode="constant", cval=0)

        # Branchpoint: skeleton pixel with >= 3 neighbors
        branchpoints = (skel_mask & (neighbor_count >= 3))

        branchpoint_count = int(np.count_nonzero(branchpoints))

        if img_area_mm2 > 0.0:
            branchpoint_density = branchpoint_count / img_area_mm2
        else:
            branchpoint_density = 0.0

        # --- Calculate Fractal Dimension (Box-Counting) ---
        # Convert to boolean mask (vessels = True)
        Z = (binary > 0)

        # Minimal dimension
        p = min(Z.shape)
        if p < 2:
            fractal_dim = 0.0
        else:
            # Box sizes: powers of 2 (1, 2, 4, ..., up to p/2)
            box_sizes = []
            counts = []

            k = 1
            while k <= p // 2:
                box_sizes.append(k)

                # Compute number of non-empty boxes at scale k
                # Trim image so that it's divisible by k
                new_shape = (Z.shape[0] // k * k, Z.shape[1] // k * k)
                Z_trim = Z[:new_shape[0], :new_shape[1]]

                # Reshape into (n_rows, k, n_cols, k) and check any True in each box
                Z_blocks = Z_trim.reshape(
                    new_shape[0] // k, k,
                    new_shape[1] // k, k
                )
                non_empty = np.any(Z_blocks, axis=(1, 3))
                N_k = float(np.count_nonzero(non_empty))

                counts.append(N_k)
                k *= 2

            # Need at least 2 scales to fit a line
            if len(box_sizes) >= 2 and all(c > 0 for c in counts):
                scales = np.array([1.0 / s for s in box_sizes], dtype=float)
                log_scales = np.log(scales)
                log_counts = np.log(np.array(counts, dtype=float))

                # Linear fit: log(N) = D * log(1/box_size) + C
                D, _ = np.polyfit(log_scales, log_counts, 1)
                fractal_dim = float(D)
            else:
                fractal_dim = 0.0

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
            "mean_diameter_mm": float(mean_diameter_mm),
            "median_diameter_mm": float(median_diameter_mm),
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
                              text=f"{mean_diameter_mm:.4f} mm")

        # Median diameter (mm)
        if hasattr(canvas, "median_diameter_value_id"):
            canvas.itemconfig(canvas.median_diameter_value_id,
                              text=f"{median_diameter_mm:.4f} mm")

        # Branchpoint count
        if hasattr(canvas, "branch_count_value_id"):
            canvas.itemconfig(canvas.branch_count_value_id,
                              text=f"{branchpoint_count:d}")

        # Branchpoint density (per mm²)
        if hasattr(canvas, "branch_density_value_id"):
            canvas.itemconfig(canvas.branch_density_value_id,
                              text=f"{branchpoint_density:.2f} /mm²")

        # Fractal dimension
        if hasattr(canvas, "fractal_dim_value_id"):
            canvas.itemconfig(canvas.fractal_dim_value_id,
                              text=f"{fractal_dim:.3f}")

        # Mean tortuosity
        if hasattr(canvas, "tortuosity_value_id"):
            canvas.itemconfig(canvas.tortuosity_value_id,
                              text=f"{mean_tortuosity:.3f}")
