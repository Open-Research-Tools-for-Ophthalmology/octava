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


        # --- Calculate Fractal Dimension (Exact MATLAB Logic) ---
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

            
            counts = [] # 记录 N(r)
            r_values = [] # 记录 r

            counts.append(np.sum(Z_pad))
            r_values.append(1)
            
            current_img = Z_pad

            for i in range(1, exponent + 1):
                rows, cols = current_img.shape
                
                if rows < 2 or cols < 2:
                    break

                shrunk_img = current_img.reshape(rows//2, 2, cols//2, 2).max(axis=(1, 3))
                

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

        # [DEBUG]
        print(f"DEBUG: Fractal Dimension Inputs: Shape={Z.shape}, Padded={width}x{width}")
        print(f"DEBUG: FD Calculation: {fractal_dim:.4f}")

        # --- Calculate Mean Tortuosity ---
        # 需要: links, image_shape (从 binary.shape 获取)
        
        tortuosity_list = []
        
        # 获取图像尺寸 (高, 宽) - 只要有 binary 或 skeleton 变量就在这
        # 如果你不想传 binary，必须手动指定比如 image_shape = (1024, 1024)
        image_shape = binary.shape 

        for link in links:
            # 1. 获取路径索引
            indices = np.asarray(link.path, dtype=int)
            if indices.size < 2:
                continue

            # 2. 核心步骤：必须用 shape 把索引转回坐标 (Row, Col)
            rows, cols = np.unravel_index(indices, image_shape)
            coords = np.column_stack((rows, cols)).astype(float)

            # 3. 计算实际路径长度 (Arc Length) - 分子
            # 沿路径每一步距离累加
            diffs = np.diff(coords, axis=0)
            arc_length = np.sum(np.linalg.norm(diffs, axis=1))

            # 4. 计算首尾直线距离 (Chord Length) - 分母
            start_point = coords[0]
            end_point = coords[-1]
            chord_length = np.linalg.norm(start_point - end_point)

            # 5. 计算弯曲度 (Tortuosity = Arc / Chord)
            # 过滤掉首尾重合的圆环 (chord_length approx 0)
            if chord_length > 1e-6:
                tortuosity = arc_length / chord_length
                tortuosity_list.append(tortuosity)

        # 6. 计算最终平均值
        if len(tortuosity_list) > 0:
            mean_tortuosity = np.mean(tortuosity_list)
        else:
            mean_tortuosity = 0.0

        # [DEBUG]
        # print(f"DEBUG: Mean Tortuosity: {mean_tortuosity:.4f}")



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
