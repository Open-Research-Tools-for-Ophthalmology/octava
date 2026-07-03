import numpy as np
import pandas as pd
from tkinter import Canvas
from scipy.ndimage import distance_transform_edt
from scipy.interpolate import make_splprep
from modules.write_excel import *
from scipy.stats import skew, kurtosis

# imports below used for viewing changes to graph at different smoothing s values

# import matplotlib
# matplotlib.use('TkAgg')
# import matplotlib.pyplot as plt
# print(matplotlib.get_backend())
# import os
# from datetime import datetime


class BiomarkerAnalyzer:
    """
    Compute vessel biomarkers from the current canvas state.
    Results are stored in canvas.metrics and shown in the GUI.
    """

    @staticmethod
    def _movmean(arr, window):
        """Compute a centered moving average with preservation of data trend at edge values."""
        arr = np.asarray(arr, dtype=float)
        n = arr.size
        if n == 0 or window <= 1:
            return arr.copy()

        pad_size = window // 2
        padded_arr = np.pad(arr, (pad_size, pad_size), mode='reflect', reflect_type='odd')
        
        csum = np.cumsum(np.insert(padded_arr, 0, 0.0))
        out = (csum[window:] - csum[:-window]) / window
        
        return out[:n]

    @staticmethod
    def _remove_duplicate_xy_points(points):
        """Remove consecutive duplicate points that create zero-length vectors."""
        points = np.asarray(points, dtype=float)
        if points.shape[0] <= 1:
            return points

        keep = np.ones(points.shape[0], dtype=bool)
        keep[1:] = np.linalg.norm(np.diff(points, axis=0), axis=1) > np.finfo(float).eps
        return points[keep]

    @staticmethod
    def _resample_xy_by_arclength(points, spacing):
        """Resample a centerline to approximately even physical spacing."""
        points = BiomarkerAnalyzer._remove_duplicate_xy_points(points)
        if points.shape[0] < 2 or spacing <= 0:
            return points

        segment_lengths = np.linalg.norm(np.diff(points, axis=0), axis=1)
        arc_positions = np.concatenate(([0.0], np.cumsum(segment_lengths)))
        arc_length = arc_positions[-1]
        if arc_length <= 0:
            return points[:0]

        sample_positions = np.arange(0.0, arc_length, spacing)
        if sample_positions.size == 0:
            sample_positions = np.array([0.0])
        if sample_positions[-1] < arc_length:
            sample_positions = np.append(sample_positions, arc_length)

        resampled_x = np.interp(sample_positions, arc_positions, points[:, 0])
        resampled_y = np.interp(sample_positions, arc_positions, points[:, 1])
        return np.column_stack((resampled_x, resampled_y))

    @staticmethod
    def _points_smoothing(points, s):
        """Smooths a centerline using B-spline smoothing."""
        points = BiomarkerAnalyzer._remove_duplicate_xy_points(points)
        points = points.astype(float)
        
        if len(points) < 4:
            return points
            
        try:
            result = make_splprep([points[:, 0], points[:, 1]], s=s)
            bspline = result[0]
            
            u_new = np.linspace(0, 1, len(points) // 2)  # evaluate at half the density 
            smoothed_points = bspline(u_new)

            # code below used for viewing graph at different s values

            # x_smooth, y_smooth = smoothed_points[0], smoothed_points[1]

            # plt.figure(figsize=(8, 4))
            # plt.plot(points[:, 0], points[:, 1], 'ro--', label='jagged')
            # plt.plot(x_smooth, y_smooth, 'b-', linewidth=2, label='smoothed')
            # plt.legend()
            # session_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            # plt.savefig(f"vessel_{session_time}.png")

            return smoothed_points.T
            
        except ValueError:
            return points

    @staticmethod
    def _compute_soam_from_evenly_spaced_xy(points):
        """
        Compute SOAM as summed turning angle per resampled arc length.
        This is the current in-use function to compute SOAM.
        """
        s = len(points)  # change s depending on number of points
        points = BiomarkerAnalyzer._points_smoothing(points, s)  # not sure what to set for s
        
        points = BiomarkerAnalyzer._remove_duplicate_xy_points(points)
        if points.shape[0] < 3:
            return 0.0

        segment_lengths = np.linalg.norm(np.diff(points, axis=0), axis=1)
        arc_length = np.sum(segment_lengths)
        if arc_length <= 0:
            return 0.0

        eps = np.finfo(float).eps
        total_angle = 0.0
        for j in range(1, points.shape[0] - 1):
            v1 = points[j] - points[j - 1]
            v2 = points[j + 1] - points[j]
            denom = np.linalg.norm(v1) * np.linalg.norm(v2)
            if denom <= eps:
                continue

            cos_theta = np.clip(np.dot(v1, v2) / denom, -1, 1)
            total_angle += np.arccos(cos_theta)

        return total_angle / arc_length

    @staticmethod
    def _compute_new_tortuosity_metrics_from_xy(vessel_x, vessel_y, pix2mm):
        """
        Compute PWAOC tortuosity metrics for one vessel centerline.
        This is the current function used to compute PWAOC metrics.
        Previously contained SOAM calculation but was removed due to new requirements.
        """
        vesselX = np.asarray(vessel_x, dtype=float).ravel() * pix2mm
        vesselY = np.asarray(vessel_y, dtype=float).ravel() * pix2mm

        if vesselX.size < 3 or vesselY.size < 3:
            return None

        numPoints = len(vesselX)
        eps = np.finfo(float).eps
        window_size = 10

        ds = np.sqrt(np.diff(vesselX)**2 + np.diff(vesselY)**2)
        arcLength = np.sum(ds)

        if arcLength <= 0:
            return None

        chordLength = np.sqrt(
            (vesselX[-1] - vesselX[0])**2 +
            (vesselY[-1] - vesselY[0])**2
        )

        smoothedX = BiomarkerAnalyzer._movmean(vesselX, window_size)
        smoothedY = BiomarkerAnalyzer._movmean(vesselY, window_size)

        dx = BiomarkerAnalyzer._movmean(np.gradient(smoothedX), window_size)
        dy = BiomarkerAnalyzer._movmean(np.gradient(smoothedY), window_size)

        ddx = BiomarkerAnalyzer._movmean(np.gradient(dx), window_size)
        ddy = BiomarkerAnalyzer._movmean(np.gradient(dy), window_size)

        curvature = (dx * ddy - ddx * dy) / ((dx**2 + dy**2) ** (3 / 2) + eps)
        curvature = BiomarkerAnalyzer._movmean(curvature, window_size)

        signCurv = np.sign(curvature)
        _ = np.where(np.diff(signCurv) != 0)[0] + 1
        x = np.arange(1, numPoints + 1)

        v1 = np.array([vesselY[-1] - vesselY[0], vesselX[-1] - vesselX[0]])
        v2 = np.array([x[-1] - x[0], 0.0])

        angle = np.arccos(
            np.clip(
                np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + eps),
                -1,
                1,
            )
        )

        vessel = np.column_stack((smoothedY, smoothedX))
        vesselSlope = np.sign(v1[1])

        rot = np.array([
            [np.cos(vesselSlope * angle), -np.sin(vesselSlope * angle)],
            [np.sin(vesselSlope * angle), np.cos(vesselSlope * angle)],
        ])

        vessel_rot = (vessel @ rot)[:, 1]

        gradCurv = BiomarkerAnalyzer._movmean(np.gradient(vessel_rot), window_size)
        signGradCurv = np.sign(gradCurv)
        extremaIdx = np.where(np.diff(signGradCurv) != 0)[0] + 1

        testY = np.diff(vesselY[extremaIdx]) if len(extremaIdx) > 1 else np.array([])
        testX = np.diff(vesselX[extremaIdx]) if len(extremaIdx) > 1 else np.array([])

        if len(extremaIdx) >= 1:
            trueExtrema = [extremaIdx[0]]
            thr = 3 * pix2mm

            for kk in range(1, len(extremaIdx)):
                cond1 = abs(testY[kk - 1]) > thr and abs(testX[kk - 1]) > thr
                cond2 = (
                    (abs(testY[kk - 1]) > thr or abs(testX[kk - 1]) > thr)
                    and (extremaIdx[kk] - extremaIdx[kk - 1] > 100)
                )

                if cond1 or cond2:
                    trueExtrema.append(extremaIdx[kk])

            nExtrema = max(len(trueExtrema), 1)
        else:
            nExtrema = 1

        AOC = np.nan if chordLength == 0 else arcLength / chordLength
        PWAOC = AOC * nExtrema if np.isfinite(AOC) else np.nan

        return {
            "PWAOC": PWAOC,
        }

    @staticmethod
    def _compute_new_tortuosity_metrics_from_xy_paper_soam(
        vessel_x,
        vessel_y,
        pix2mm,
        soam_sample_spacing_mm=0.03,
        soam_smoothing_window=10,
    ):
        """Compute PWAOC and a paper-aligned SOAM from one vessel centerline.

        PWAOC is intentionally delegated to the existing implementation. 
        SOAM is recomputed after smoothing and physical arc-length resampling because the
        paper requires evenly spaced points.
        """
        metrics = BiomarkerAnalyzer._compute_new_tortuosity_metrics_from_xy(
            vessel_x,
            vessel_y,
            pix2mm,
        )
        if metrics is None:
            return None

        vesselX = np.asarray(vessel_x, dtype=float).ravel() * pix2mm
        vesselY = np.asarray(vessel_y, dtype=float).ravel() * pix2mm
        if vesselX.size < 3 or vesselY.size < 3:
            return metrics

        smooth_window = max(int(soam_smoothing_window), 1)
        smoothedX = BiomarkerAnalyzer._movmean(vesselX, smooth_window)
        smoothedY = BiomarkerAnalyzer._movmean(vesselY, smooth_window)
        smoothedX[0], smoothedX[-1] = vesselX[0], vesselX[-1]
        smoothedY[0], smoothedY[-1] = vesselY[0], vesselY[-1]

        points = np.column_stack((smoothedX, smoothedY))
        resampled = BiomarkerAnalyzer._resample_xy_by_arclength(
            points,
            soam_sample_spacing_mm,
        )

        metrics = metrics.copy()
        metrics["SOAM"] = BiomarkerAnalyzer._compute_soam_from_evenly_spaced_xy(resampled)
        return metrics

    @staticmethod
    def _summarize_new_tort_metrics(per_link_metrics):
        """Aggregate per-link tortuosity metrics into mean and standard deviation values."""
        if per_link_metrics:
            pwaoc_vals = np.array([m["PWAOC"] for m in per_link_metrics], dtype=float)
            soam_vals = np.array([m["SOAM"] for m in per_link_metrics], dtype=float)
            return {
                "PWAOC_mean": np.nanmean(pwaoc_vals),
                "PWAOC_std": np.nanstd(pwaoc_vals),
                "SOAM_mean": np.nanmean(soam_vals),
                "SOAM_std": np.nanstd(soam_vals),
            }

        return {
            "PWAOC_mean": np.nan,
            "PWAOC_std": np.nan,
            "SOAM_mean": np.nan,
            "SOAM_std": np.nan,
        }

    @staticmethod
    def compute_new_tortuosity_metrics_from_mat_file(mat_path):
        """Load MATLAB link data and return summarized tortuosity metrics."""
        import scipy.io as sio

        mat = sio.loadmat(mat_path, squeeze_me=True, struct_as_record=False)

        if "links" not in mat:
            raise KeyError("MAT file must contain a 'links' variable.")
        if "realImageSizeMm" not in mat:
            raise KeyError("MAT file must contain 'realImageSizeMm'.")
        if "fullImSizePix" not in mat:
            raise KeyError("MAT file must contain 'fullImSizePix'.")

        image_size_mm = float(np.asarray(mat["realImageSizeMm"]).squeeze())
        full_im_size_pix = np.asarray(mat["fullImSizePix"]).astype(float).ravel()
        if full_im_size_pix.size == 0:
            raise ValueError("'fullImSizePix' must contain at least one value.")

        pix2mm = image_size_mm / full_im_size_pix[0] if full_im_size_pix[0] > 0 else 0.0
        mat_links = np.atleast_1d(mat["links"])

        per_link_metrics = []

        for link in mat_links:
            if not hasattr(link, "x") or not hasattr(link, "y"):
                continue

            # metrics = BiomarkerAnalyzer._compute_new_tortuosity_metrics_from_xy(
            metrics = BiomarkerAnalyzer._compute_new_tortuosity_metrics_from_xy_paper_soam(
                link.x,
                link.x,
                link.y,
                pix2mm,
            )
            if metrics is not None:
                per_link_metrics.append(metrics)

        return BiomarkerAnalyzer._summarize_new_tort_metrics(per_link_metrics)

    @staticmethod
    def process(canvas: Canvas) -> None:
        """Compute whole-image vascular biomarkers, update the GUI, and export metrics."""
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

        if Nx > 0:
            pix_size_mm = image_size_mm / Nx
        else:
            pix_size_mm = 0.0

        # Length metrics
        if links is not None and len(links) > 0:
            links_length_pix = [l.pixLength for l in links if l.pixLength is not None]
            links_length_um = np.asarray(links_length_pix) * pix_size_mm * 1000
            links_length_um_flatten = links_length_um.flatten() # Flatten to 1d

            # ensure we have enough data points
            if len(links_length_um_flatten) > 1:
                var_length = np.var(links_length_um_flatten, ddof=1)
                var_length = 0.0 if np.isnan(var_length) else var_length
                skew_length = skew(links_length_um_flatten)
                kurt_length = kurtosis(links_length_um_flatten, fisher=False)
            else:
                var_length = 0.0
                skew_length = 0.0
                kurt_length = 0.0
        else:
            var_length = 0.0
            skew_length = 0.0
            kurt_length = 0.0

        # Diameter metrics (output: μm)
        radius_map = distance_transform_edt(binary > 0)
        diameter_map = radius_map * 2

        # all_sampled_diameters: the original per-pixel diameter maps, per_link_mean_diameters: one mean per link to match Matlab's metrics link.diameter = mean(diameterMeasurements)
        all_sampled_diameters = []   
        per_link_mean_diameters = []
        img_shape = (Nx, Ny)

        for link in links:
            indices = np.asarray(link.path, dtype=int)
            if indices.size == 0:
                continue

            rows, cols = np.unravel_index(indices, img_shape)
            vals = diameter_map[rows, cols]
            all_sampled_diameters.extend(vals)
            if vals.size > 0:
                per_link_mean_diameters.append(float(np.mean(vals)))

        diameters_pix = np.asarray(all_sampled_diameters, dtype=float)
        diameters_um = diameters_pix * pix_size_mm * 1000.0
        canvas.vessel_diameters_um = diameters_um

        # var/skew/kurt computed on per-link mean diameters (one value per vessel, matching MATLAB)
        if per_link_mean_diameters:
            diameters_scaled_um = np.asarray(per_link_mean_diameters) * pix_size_mm * 1000.0
            mean_diameter_um = np.mean(diameters_scaled_um)
            diameters_scaled_um_flatten = diameters_scaled_um.flatten()

            if len(diameters_scaled_um_flatten) > 1:
                var_diameter_um = np.var(diameters_scaled_um_flatten, ddof=1)
                var_diameter_um = 0.0 if np.isnan(var_diameter_um) else var_diameter_um
                skew_diameter_um = skew(diameters_scaled_um_flatten)
                kurt_diameter_um = kurtosis(diameters_scaled_um_flatten, fisher=False)
            else:
                var_diameter_um = 0.0
                skew_diameter_um = 0.0
                kurt_diameter_um = 0.0
        else:
            mean_diameter_um = 0.0
            var_diameter_um = 0.0
            skew_diameter_um = 0.0
            kurt_diameter_um = 0.0

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
        Z_skeleton = (skeleton > 0)
        Z_binary = (binary > 0)

        h, w = Z_skeleton.shape
        Nx = max(h, w)

        if Nx < 2:
            fractal_dim = {
                'skeleton': {4: 0.0},
                'binary': {4: 0.0}
            }
        else:
            import math

            fractal_dim = {
                'skeleton': {4: 0.0},
                'binary': {4: 0.0}
            }

            # 0529 Find the largest box size
            # Take the floor so the largest box size is around half of the image.
            exponent_end = math.floor(math.log2(Nx))
            # check if duplication of the largest box size is way over the original resolution so we dont pad too much (acceptable +- 10%)
            if exponent_end > 0 and 2 ** exponent_end > Nx * 1.1:
                exponent_end -= 1

            width = 2 ** (exponent_end + 1)
            print(f'Fractal Dimension: Original image width={Nx}, After truncation/padding={width}, Largest box size={2 ** exponent_end}')

            Z_pad = {
                'skeleton': np.zeros((width, width), dtype=bool),
                'binary': np.zeros((width, width), dtype=bool)
            }
            Z_pad['skeleton'][:min(Nx, width), :min(Nx, width)] = Z_skeleton
            Z_pad['binary'][:min(Nx, width), :min(Nx, width)] = Z_binary

            counts = {
                'skeleton': {4: []},
                'binary': {4: []}
            }

            r_values = {
                'skeleton': {4: []},
                'binary': {4: []}
            }

            for img_type, img in {
                'skeleton': Z_pad['skeleton'],
                'binary': Z_pad['binary']
            }.items():
                # start 4 [4, 8, ..., 2^exponent] box sizes
                for exponent_start in [2]: # 2^2 = 4 for starting box_size
                    current_img = img
                    for i in range(1, exponent_end + 1):
                        rows, cols = current_img.shape
                        if rows < 2 or cols < 2:
                            break

                        # Reshape to half of current size
                        shrunk_img = current_img.reshape(rows // 2, 2, cols // 2, 2).max(axis=(1, 3))

                        # Shrink image with smaller box_size first but keep it excluded from regression calculation
                        if i < exponent_start:
                            current_img = shrunk_img
                            continue

                        # Get number of boxes needed to cover the shape
                        n_box = np.sum(shrunk_img)
                        
                        # Store counts and box sizes for later regression
                        counts[img_type][2 ** exponent_start].append(n_box)
                        r_values[img_type][2 ** exponent_start].append(2 ** i)

                        print(f'Using {img_type} image, Starting Box size: {2 ** exponent_start}, Current Box size: {2 ** i}, # of valid boxes {n_box}')
                        current_img = shrunk_img

                    valid_indices = [i for i, c in enumerate(counts[img_type][2 ** exponent_start]) if c > 0]

                    if len(valid_indices) >= 2:
                        x = np.log([r_values[img_type][2 ** exponent_start][i] for i in valid_indices])
                        y = -np.log([counts[img_type][2 ** exponent_start][i] for i in valid_indices])

                        coeffs = np.polyfit(x, y, 1)
                        fractal_dim[img_type][2 ** exponent_start] = float(coeffs[0])
                    else:
                        fractal_dim[img_type][2 ** exponent_start] = 0.0

        # Tortuosity metrics
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

        if tortuosity_list:
            mean_tortuosity = np.mean(tortuosity_list)
            tortuosity_arr = np.asarray(tortuosity_list)
            tortuosity_arr_flatten = tortuosity_arr.flatten() # Flatten to 1d

            if len(tortuosity_arr_flatten) > 1:
                var_tortuosity = np.var(tortuosity_arr_flatten, ddof=1)
                var_tortuosity = 0.0 if np.isnan(var_tortuosity) else var_tortuosity
                skew_tortuosity = skew(tortuosity_arr_flatten)
                kurt_tortuosity = kurtosis(tortuosity_arr_flatten, fisher=False)
            else:
                var_tortuosity = 0.0
                skew_tortuosity = 0.0
                kurt_tortuosity = 0.0
        else:
            mean_tortuosity = 0.0
            var_tortuosity = 0.0
            skew_tortuosity = 0.0
            kurt_tortuosity = 0.0

        # Store tortuosity values for histogram display
        canvas.vessel_tortuosity = np.asarray(tortuosity_list, dtype=float)

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
            "fractal_dimension": float(fractal_dim['skeleton'][4]),  # Displaying the box_size=4 skeleton FD by default
            "mean_tortuosity": float(mean_tortuosity),
        })
        micro_stats = {
            "name": canvas.FileLabelName,
            "Vessel area density": float(vad_pct),
            "Vessel length density": float(vessel_length_density),
            "varLengths": int(var_length),
            "skewLengths": round(float(skew_length), 2),
            "kurtLengths": round(float(kurt_length), 2),
            "MeanDiam": float(mean_diameter_um),
            "varDiams": int(var_diameter_um),
            "skewDiams": round(float(skew_diameter_um), 2),
            "kurtDiams": round(float(kurt_diameter_um), 2),
            "Branchpoint density": float(branchpoint_density),
            "Fractal dimension (Skeleton)": float(fractal_dim['skeleton'][4]),
            "Fractal dimension (Binary)": float(fractal_dim['binary'][4]),
            "mTort": float(mean_tortuosity),
            "varTort": round(float(var_tortuosity), 3),
            "skewTort": round(float(skew_tortuosity), 2),
            "kurtTort": int(kurt_tortuosity),
        }

        # Tortuosity metrics (PWAOC, SOAM, etc.)
        canvas.new_tort_metrics = BiomarkerAnalyzer.new_tortuosity_metrics(
            links=links,
            binary_image=canvas.binary_image,
            image_size_var=canvas.image_size_var,
            fullImSizePix=canvas.fullImSizePix,
        )
        micro_stats.update(canvas.new_tort_metrics)

        # Function parameters (Frangi, MedFilt, etc.)
        param_stats = {
            "Frangi_sigma_max": int(canvas.frangi_max.get()) if canvas.frangi_bool.get() else "N/A",
            "Frangi_sigma_min": int(canvas.frangi_min.get()) if canvas.frangi_bool.get() else "N/A",
            "Jerman_sigmas": ",".join(s.strip() for s in canvas.jerman_sigmas.get().split(',')) if canvas.jerman_bool.get() else "N/A",
            "MedFilt_Kernel": int(canvas.kernel_size.get()) if canvas.med_filt_bool.get() else "N/A",
            "Binarization": "Fuzzy means", # We don't have anything else besides FUZZY means yet
            "TwigSize": int(canvas.twig_size.get()),
        }
        micro_stats.update(param_stats)

        write_excel(micro_stats, canvas.lastMetricsPath, sheet_name="Microvascular metrics")

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
            canvas.itemconfig(canvas.fractal_dim_value_id, text=f"{fractal_dim['skeleton'][4]:.3f}")

        if hasattr(canvas, "tortuosity_value_id"):
            canvas.itemconfig(canvas.tortuosity_value_id, text=f"{mean_tortuosity:.3f}")

    @staticmethod
    def new_tortuosity_metrics(links, binary_image, image_size_var, fullImSizePix):
        """Compute summarized tortuosity metrics directly from graph links."""
        binary = binary_image
        if links is None or len(links) == 0:
            return {
                "PWAOC_mean": np.nan,
                "PWAOC_std": np.nan,
                "SOAM_mean": np.nan,
                "SOAM_std": np.nan,
            }

        # Image scale
        image_size_mm = float(image_size_var.get())
        img_height, _ = fullImSizePix
        pix2mm = image_size_mm / img_height if img_height > 0 else 0.0

        image_shape = binary.shape

        per_link_metrics = []

        for link in links:
            indices = np.asarray(link.path, dtype=int)
            if indices.size < 3:
                continue

            rows, cols = np.unravel_index(indices, image_shape)
            metrics = BiomarkerAnalyzer._compute_new_tortuosity_metrics_from_xy_paper_soam(
                cols,
                rows,
                pix2mm,
            )
            if metrics is not None:
                per_link_metrics.append(metrics)

        return BiomarkerAnalyzer._summarize_new_tort_metrics(per_link_metrics)

 
    @staticmethod
    def new_tortuosity_metrics_all(canvas: Canvas) -> None:
        """Compute the legacy full tortuosity metric set for every link on the canvas. Not in use but kept for reference."""
        import numpy as np

        links = canvas.skeleton_links
        binary = canvas.binary_image

        if links is None or len(links) == 0:
            return

        eps = np.finfo(float).eps

        # Image scale
        image_size_mm = float(canvas.image_size_var.get())
        img_height, img_width = canvas.fullImSizePix
        pix2mm = image_size_mm / img_height if img_height > 0 else 0.0

        image_shape = binary.shape

        metric_names = [
            "AOC","TSC","TSCN","tortDensity","DT",
            "PWAOC","ISR","SOAM","tortAngle","VCI1","VCI2"
        ]

        def movmean(arr, window):
            """Compute a centered moving average for the nested legacy metric routine."""
            arr = np.asarray(arr, dtype=float)
            n = arr.size
            if n == 0 or window <= 1:
                return arr.copy()

            half_left = (window - 1) // 2
            half_right = window // 2

            csum = np.cumsum(np.insert(arr, 0, 0.0))
            out = np.empty(n)

            for i in range(n):
                start = max(0, i - half_left)
                end = min(n, i + half_right + 1)
                out[i] = (csum[end] - csum[start]) / (end - start)

            return out

        def trimmean_10(arr):
            """Return the 10% trimmed mean used by the legacy tortuosity export."""
            arr = np.asarray(arr)
            arr = arr[np.isfinite(arr)]
            if arr.size == 0:
                return np.nan
            arr = np.sort(arr)
            trim = int(np.floor(0.1 * arr.size))
            if arr.size - 2 * trim <= 0:
                return np.mean(arr)
            return np.mean(arr[trim:arr.size - trim])

        per_link_metrics = []

        for link in links:

            indices = np.asarray(link.path, dtype=int)
            if indices.size < 3:
                continue

            rows, cols = np.unravel_index(indices, image_shape)

            vesselX = cols.astype(float) * pix2mm
            vesselY = rows.astype(float) * pix2mm
            numPoints = len(vesselX)

            ds = np.sqrt(np.diff(vesselX)**2 + np.diff(vesselY)**2)
            arcLength = np.sum(ds)

            chordLength = np.sqrt(
                (vesselX[-1]-vesselX[0])**2 +
                (vesselY[-1]-vesselY[0])**2
            )

            if arcLength <= 0:
                continue

            windowSize = 10

            smoothedX = movmean(vesselX, windowSize)
            smoothedY = movmean(vesselY, windowSize)

            dx = np.gradient(smoothedX)
            dy = np.gradient(smoothedY)

            dx = movmean(dx, windowSize)
            dy = movmean(dy, windowSize)

            ddx = np.gradient(dx)
            ddy = np.gradient(dy)

            ddx = movmean(ddx, windowSize)
            ddy = movmean(ddy, windowSize)

            curvature = (dx*ddy - ddx*dy) / ((dx**2 + dy**2)**(3/2) + eps)
            curvature = movmean(curvature, windowSize)

            signCurv = np.sign(curvature)
            inflecIdx = np.where(np.diff(signCurv) != 0)[0] + 1
            nSeg = len(inflecIdx) + 1

            x = np.arange(1, numPoints+1)

            v1 = np.array([
                vesselY[-1]-vesselY[0],
                vesselX[-1]-vesselX[0]
            ])

            v2 = np.array([x[-1]-x[0],0])

            angle = np.arccos(
                np.clip(
                    np.dot(v1,v2) /
                    (np.linalg.norm(v1)*np.linalg.norm(v2)+eps),
                    -1,1
                )
            )

            vessel = np.column_stack((smoothedY, smoothedX))
            vesselSlope = np.sign(v1[1])

            rot = np.array([
                [np.cos(vesselSlope*angle),-np.sin(vesselSlope*angle)],
                [np.sin(vesselSlope*angle), np.cos(vesselSlope*angle)]
            ])

            vessel_rot = vessel @ rot
            vessel_rot = vessel_rot[:,1]

            gradCurv = np.gradient(vessel_rot)
            gradCurv = movmean(gradCurv, windowSize)

            signGradCurv = np.sign(gradCurv)
            extremaIdx = np.where(np.diff(signGradCurv)!=0)[0] + 1

            testY = np.diff(vesselY[extremaIdx]) if len(extremaIdx)>1 else []
            testX = np.diff(vesselX[extremaIdx]) if len(extremaIdx)>1 else []

            trueExtrema = []

            if len(extremaIdx) >= 1:

                trueExtrema = [extremaIdx[0]]
                thr = 3*pix2mm

                for kk in range(1,len(extremaIdx)):

                    cond1 = abs(testY[kk-1])>thr and abs(testX[kk-1])>thr

                    cond2 = (
                        (abs(testY[kk-1])>thr or abs(testX[kk-1])>thr)
                        and (extremaIdx[kk]-extremaIdx[kk-1] > 100)
                    )

                    if cond1 or cond2:
                        trueExtrema.append(extremaIdx[kk])

                nExtrema = max(len(trueExtrema),1)

            else:
                nExtrema = 1

            AOC = np.nan if chordLength==0 else arcLength/chordLength

            TSC = np.sum((curvature[1:-1]**2)*ds[1:]) if len(curvature)>=3 else np.nan
            TSCN = np.sum((curvature[1:-1]**2)*ds[1:]/arcLength) if arcLength>0 else np.nan

            segAOCs = []
            segArcs = []

            segStart = 0

            for k in range(nSeg):

                if k < len(inflecIdx):
                    segEnd = inflecIdx[k]
                else:
                    segEnd = len(vesselX)-1

                segArc = np.sum(
                    np.sqrt(
                        np.diff(vesselX[segStart:segEnd+1])**2 +
                        np.diff(vesselY[segStart:segEnd+1])**2
                    )
                )

                segChord = np.sqrt(
                    (vesselX[segEnd]-vesselX[segStart])**2 +
                    (vesselY[segEnd]-vesselY[segStart])**2
                )

                segAOC_val = np.nan if segChord==0 else segArc/segChord

                segAOCs.append(segAOC_val)
                segArcs.append(segArc)

                segStart = segEnd

            segAOCs = np.asarray(segAOCs)
            segArcs = np.asarray(segArcs)

            if nSeg>1 and arcLength>0:
                tortDensity = ((nSeg-1)/nSeg)*(np.sum(segAOCs-1)/arcLength)
            else:
                tortDensity = segAOCs[0] if segAOCs.size>0 else np.nan

            DT = np.nansum(segAOCs*segArcs)/arcLength if arcLength>0 else np.nan

            PWAOC = AOC*nExtrema if np.isfinite(AOC) else np.nan

            ISR = np.sum(np.abs(curvature))/numPoints if numPoints>0 else np.nan

            if numPoints<3:
                SOAM = 0
            else:

                totalWeightedAngle = 0

                for j in range(1,numPoints-1):

                    v1 = np.array([
                        vesselX[j]-vesselX[j-1],
                        vesselY[j]-vesselY[j-1]
                    ])

                    v2 = np.array([
                        vesselX[j+1]-vesselX[j],
                        vesselY[j+1]-vesselY[j]
                    ])

                    cosTheta = np.clip(
                        np.dot(v1,v2) /
                        (np.linalg.norm(v1)*np.linalg.norm(v2)+eps),
                        -1,1
                    )

                    angleRad = np.arccos(cosTheta)
                    totalWeightedAngle += angleRad

                SOAM = totalWeightedAngle/arcLength

            segStart = 0
            angleRads = []

            for k in range(nSeg):

                if k < len(inflecIdx):
                    segEnd = inflecIdx[k]
                else:
                    segEnd = len(vesselX)-1

                midpointIndex = round((segEnd-segStart)/2)+segStart

                v1 = np.array([
                    vesselX[midpointIndex]-vesselX[segStart],
                    vesselY[midpointIndex]-vesselY[segStart]
                ])

                v2 = np.array([
                    vesselX[segEnd]-vesselX[midpointIndex],
                    vesselY[segEnd]-vesselY[midpointIndex]
                ])

                cosTheta = np.clip(
                    np.dot(v1,v2) /
                    (np.linalg.norm(v1)*np.linalg.norm(v2)+eps),
                    -1,1
                )

                angleRads.append(np.arccos(cosTheta))

            angleRads = np.asarray(angleRads)

            tortAngle = np.sum(angleRads*segArcs)/nSeg if nSeg>0 else np.nan

            windowSize = 4

            smoothedX = movmean(vesselX, windowSize)
            smoothedY = movmean(vesselY, windowSize)

            dx = np.diff(smoothedX)
            dy = np.diff(smoothedY)

            ds = np.sqrt(dx**2 + dy**2)

            if len(ds)>1:

                arcLength2 = np.sum(ds)

                theta = np.arctan2(dy,dx)
                dtheta = np.zeros_like(theta)

                for j in range(1,len(theta)-1):
                    dtheta[j] = (theta[j+1]-theta[j-1])/(ds[j]+ds[j-1])

                dtheta[0] = (theta[1]-theta[0])/ds[0]
                dtheta[-1] = (theta[-1]-theta[-2])/ds[-1]

                window = 4
                nPoints = len(smoothedX)

                L_local = np.zeros(nPoints)

                for j in range(nPoints):

                    idxStart = max(0,j-window//2)
                    idxEnd = min(nPoints,j+window//2+1)

                    localCentroidX = np.mean(smoothedX[idxStart:idxEnd])
                    localCentroidY = np.mean(smoothedY[idxStart:idxEnd])

                    r_local = np.sqrt(
                        (smoothedX[j]-localCentroidX)**2 +
                        (smoothedY[j]-localCentroidY)**2
                    )

                    L_local[j] = r_local**2

                dL_local = np.abs(np.diff(L_local))

                robust_dL = trimmean_10(dL_local)
                VCI1 = robust_dL/(arcLength2/len(dL_local))

            else:
                VCI1 = np.nan

            with np.errstate(divide='ignore',invalid='ignore'):
                curv_safe = curvature.copy()
                curv_safe[np.abs(curv_safe) < 1e-6] = np.nan
                inv_curv = 1.0 / curv_safe
                t = np.gradient(inv_curv)

            t[~np.isfinite(t)] = np.nan
            VCI2 = np.nansum(t)/numPoints

            per_link_metrics.append({
                "AOC":AOC,"TSC":TSC,"TSCN":TSCN,
                "tortDensity":tortDensity,"DT":DT,
                "PWAOC":PWAOC,"ISR":ISR,
                "SOAM":SOAM,"tortAngle":tortAngle,
                "VCI1":VCI1,"VCI2":VCI2
            })

        meanMetrics = {}

        for name in metric_names:

            vals = np.array([m[name] for m in per_link_metrics],dtype=float)

            meanMetrics[f"{name}_mean"] = np.nanmean(vals)
            meanMetrics[f"{name}_std"] = np.nanstd(vals)

        if not hasattr(canvas,"new_tort_metrics"):
            canvas.new_tort_metrics = {}

        canvas.new_tort_metrics.update(meanMetrics)

 

