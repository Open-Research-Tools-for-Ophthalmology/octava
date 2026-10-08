import os
import cv2
import numpy as np
import pandas as pd
from tkinter import Canvas
from scipy.ndimage import distance_transform_edt
from scipy.interpolate import make_splprep
from modules.general_utils import *
from scipy.stats import skew, kurtosis

# imports below used for viewing changes to graph at different smoothing s values

# import matplotlib
# matplotlib.use('TkAgg')
# import matplotlib.pyplot as plt
# print(matplotlib.get_backend())
# import os
# from datetime import datetime

class Link:
    def __init__(self, path: list[int], rows: list[float], cols: list[float], points: list[tuple[float, float]]):
        """
        Link object represent a vessel segment

        @example path (pix): [1,2,3,1001,2002]
        @example rows (mm): [0,0,0,1,2]
        @example cols (mm): [1,2,3,1,2]
        @example points (mm): [(0,1),(0,2),(0,3),(1,1),(2,2)]
        """
        self.path = path
        self.rows = rows
        self.cols = cols
        self.points = points
        self.pixLength = None
   
class BiomarkerAnalyzer:
    """
    Compute vessel biomarkers from the current canvas state.
    Results are stored in canvas.metrics and shown in the GUI.
    """

    # Smoother functions
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
        """
        Smooths a centerline using B-spline smoothing.
        Currently, all s values are len(points) to avoid over-smoothing.
        Endpoints are re-anchored to the original first/last points since a
        smoothing spline (s>0) is only bounded by total residual and can
        otherwise drift away from the true vessel ends.
        """
        points = BiomarkerAnalyzer._remove_duplicate_xy_points(points)
        points = points.astype(float)
        
        if len(points) < 4:
            return points
         
        try:
            # If the weights represent the inverse of the standard deviation of x
            weights = 1.0 / np.std(points, axis=0)
            # a good s value should be found in the range (m - sqrt(2*m), m + sqrt(2*m)), where m in # of points
            result = make_splprep([points[:, 0], points[:, 1]], s=s, w=weights) 
            bspline = result[0]
            
            u_new = np.linspace(0, 1, len(points) // 2)  # evaluate at half the density 
            smoothed_points = bspline(u_new)

            # commented-out code below used for viewing graph at different s values

            # x_smooth, y_smooth = smoothed_points[0], smoothed_points[1]

            # plt.figure(figsize=(8, 4))
            # plt.plot(points[:, 0], points[:, 1], 'ro--', label='jagged')
            # plt.plot(x_smooth, y_smooth, 'b-', linewidth=2, label='smoothed')
            # plt.legend()
            # session_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            # plt.savefig(f"vessel_{session_time}.png")

            smoothed_points = smoothed_points.T

            # FIXME, compute the residual error at each end and blend it back into the curve linearly across arc length
            # Linearly blend the endpoint residuals back in: a linear correction adds
            # no curvature, so interior smoothing is preserved while the ends land
            # exactly on points[0] / points[-1].
            start_error = points[0] - smoothed_points[0]
            end_error = points[-1] - smoothed_points[-1]
            blend = np.linspace(0.0, 1.0, len(smoothed_points))[:, None]
            smoothed_points = smoothed_points + (1 - blend) * start_error + blend * end_error

            return smoothed_points
            
        except ValueError:
            return points

    @staticmethod
    def _tort_smoothing(links, image_shape=1000, pix2mm=0.003, movmean_window=10, resample_spacing=0.003, bspline_s=1):
        """
        All-in-one smoothing for all possible tortuosity metrics
        1st links from skeletonisation
            -> 2nd movMean
            -> 3rd resampled
            -> 4rd bsplined
        @param links: Links parsed from skeletonisation Link(start: int, end: int, path: list,  label: int), where path consists of flat index of each point
        @param image_shape: Shape of the image used for unraveling indices.
        @param movmean_window: Window size for moving mean smoothing.
        @param resample_spacing: Spacing for resampling the points, recommended to set to same as pix2mm, physical size of 1 pix
        @param bspline_s: Smoothing factor for B-spline smoothing, s = b_spline_s_factor * len(points)
        @return List[Link]
        """

        # Get x and y coords from the links list
        smoothed_links = []
        for link in links:   
            indices = np.asarray(link.path, dtype=int)
            vessel_x, vessel_y = np.unravel_index(indices, image_shape)

            vesselX = np.asarray(vessel_x, dtype=float).ravel() * pix2mm
            vesselY = np.asarray(vessel_y, dtype=float).ravel() * pix2mm

            # Moving mean smoothing
            smoothedX = BiomarkerAnalyzer._movmean(vesselX, movmean_window)
            smoothedY = BiomarkerAnalyzer._movmean(vesselY, movmean_window)
            smoothedX[0], smoothedX[-1] = vesselX[0], vesselX[-1]
            smoothedY[0], smoothedY[-1] = vesselY[0], vesselY[-1]

            # Resample points
            smoothedPoints = np.column_stack((smoothedX, smoothedY))
            resampledPoints = BiomarkerAnalyzer._resample_xy_by_arclength(
                smoothedPoints,
                resample_spacing,
            )

            # B-spline smoothing
            bsplinedPoints = BiomarkerAnalyzer._points_smoothing(resampledPoints, bspline_s * len(resampledPoints))

            # Remove duplicates
            bsplinedPoints = BiomarkerAnalyzer._remove_duplicate_xy_points(bsplinedPoints)

            # Aggregate all links
            bsplinedPoints_pix = (bsplinedPoints / pix2mm).astype(int)
            bsplinedPath = [np.ravel_multi_index(point, image_shape) for point in bsplinedPoints_pix]
            bsplinedRows, bsplinedCols = [arr * pix2mm for arr in np.unravel_index(bsplinedPath, image_shape)]
            smoothed_links.append(Link(
                path=bsplinedPath,
                rows=bsplinedRows,
                cols=bsplinedCols,
                points=bsplinedPoints
            ))

        return smoothed_links

    # Metrics calculation functions
    @staticmethod
    def _compute_soam(points):
        """
        Compute SOAM from evenly-spaced 'x' and 'y' points, 
        as summed turning angle per resampled arc length.
        This is the current in-use function to compute SOAM.
        """
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
    def _compute_pwaoc(vesselX, vesselY, pix2mm):
        """
        Compute PWAOC tortuosity metrics for one vessel centerline.
        This is the current function used to compute PWAOC metrics.
        Previously contained SOAM calculation but was removed due redundancy.
        """
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

        return PWAOC

    def _compute_density(vesselX, vesselY):
        if len(vesselX) < 2:
            return np.nan

        # Preparations
        window_size = 10

        ds = np.sqrt(np.diff(vesselX)**2 + np.diff(vesselY)**2)
        arcLength = np.sum(ds)

        smoothedX = BiomarkerAnalyzer._movmean(vesselX, window_size)
        smoothedY = BiomarkerAnalyzer._movmean(vesselY, window_size)

        dx = np.gradient(smoothedX)
        dy = np.gradient(smoothedY)
        dx = BiomarkerAnalyzer._movmean(dx, window_size)
        dy = BiomarkerAnalyzer._movmean(dy, window_size)

        ddx = np.gradient(dx)
        ddy = np.gradient(dy)
        ddx = BiomarkerAnalyzer._movmean(ddx, window_size)
        ddy = BiomarkerAnalyzer._movmean(ddy, window_size)

        eps = np.finfo(float).eps
        curvature = (dx * ddy - ddx * dy) / ((dx**2 + dy**2)**(3/2) + eps)
        curvature = BiomarkerAnalyzer._movmean(curvature, window_size)

        signCurv = np.sign(curvature)
        inflecIdx = np.where(np.diff(signCurv) != 0)[0] + 1
        nSeg = len(inflecIdx) + 1

        # Tortuosity density
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
                (vesselX[segEnd] - vesselX[segStart])**2 +
                (vesselY[segEnd] - vesselY[segStart])**2
            )

            segAOC_val = np.nan if segChord==0 else segArc / segChord

            segAOCs.append(segAOC_val)
            segArcs.append(segArc)

            segStart = segEnd

        segAOCs = np.asarray(segAOCs)
        segArcs = np.asarray(segArcs)

        if nSeg>1 and arcLength>0:
            tortDensity = ((nSeg-1) / nSeg) * (np.sum(segAOCs-1) / arcLength)
        else:
            tortDensity = segAOCs[0] if segAOCs.size > 0 else np.nan

        return tortDensity

    @staticmethod
    def _compute_new_tortuosity_metrics(
        vessel_x,
        vessel_y,
        points,
        pix2mm,
    ):
        """Compute PWAOC, a paper-aligned SOAM and Density from one vessel centerline.

        As per paper requirements, SOAM is computed in `_compute_soam()` after 
        smoothing and physical arc-length resampling.

        PWAOC is computed using `_compute_pwaoc()`. 
        This function previously contained SOAM computation but was removed due to redundancy
        caused by the new function.

        Density is computed using `_compute_density()` where the preparations steps are the same as Matlab rather than modified in pwaoc
        """

        # PWAOC
        pwaoc_value = BiomarkerAnalyzer._compute_pwaoc(vessel_x, vessel_y, pix2mm)

        # SOAM
        soam_value = BiomarkerAnalyzer._compute_soam(points)

        # Density
        density_value = BiomarkerAnalyzer._compute_density(vessel_x, vessel_y)

        if pwaoc_value is None and soam_value is None and density_value is None:
            return None

        metrics = {}
        metrics["PWAOC"] = pwaoc_value
        metrics["SOAM"] = soam_value
        metrics["tortDensity"] = density_value

        return metrics

    @staticmethod
    def _summarize_new_tort_metrics(per_link_metrics):
        """Aggregate per-link tortuosity metrics into mean and standard deviation values."""
        if per_link_metrics:
            pwaoc_vals = np.array([m["PWAOC"] for m in per_link_metrics], dtype=float)
            soam_vals = np.array([m["SOAM"] for m in per_link_metrics], dtype=float)
            density_vals = np.array([m["tortDensity"] for m in per_link_metrics], dtype=float)
            return {
                "PWAOC_mean": np.nanmean(pwaoc_vals),
                "PWAOC_std": np.nanstd(pwaoc_vals),
                "SOAM_mean": np.nanmean(soam_vals),
                "SOAM_std": np.nanstd(soam_vals),
                "tortDensity_mean": np.nanmean(density_vals),
                "tortDensity_std": np.nanstd(density_vals),
            }

        return {
            "PWAOC_mean": np.nan,
            "PWAOC_std": np.nan,
            "SOAM_mean": np.nan,
            "SOAM_std": np.nan,
            "tortDensity_mean": np.nan,
            "tortDensity_std": np.nan,
        }

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

        # Smoothed links for all tortuosity calculation
        pix2mm=image_size_mm / Nx
        links = BiomarkerAnalyzer._tort_smoothing(links, binary.shape, pix2mm, 5, pix2mm, 1)

        # Read optional image type from GUI
        img_type = canvas.img_type_var.get() if hasattr(canvas, "img_type_var") else None

        # Image area in pixels
        img_area_pix = float(Nx * Nx)

        # Vessel Area Density (VAD %)
        vessel_sum = float(np.sum(binary))
        vessel_pixels = vessel_sum / 255.0
        vad_pct = vessel_pixels / img_area_pix * 100.0

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
        vessel_length_density_mminv = total_length_mm / length_area_mm2
        vessel_length_density_pct = vessel_length_density_mminv * pix_size_mm * 100.0 # mm/mm^2 * mm/px = 1/px * 100 = %/px

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
            median_diameter_um = np.median(diameters_scaled_um)
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
            median_diameter_um = 0.0
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
            Z_pad['skeleton'][:min(Nx, width), :min(Nx, width)] = Z_skeleton[:min(Nx, width), :min(Nx, width)]
            Z_pad['binary'][:min(Nx, width), :min(Nx, width)] = Z_binary[:min(Nx, width), :min(Nx, width)]

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

        # To display
        canvas.metrics.update({
            "vessel_area_density_pct": float(vad_pct),
            "vessel_area_mm2": float(vessel_area_mm2),
            "image_area_mm2": float(img_area_mm2),
            "vessel_length_density_mm_per_mm2": float(vessel_length_density_mminv),
            "mean_diameter_um": float(mean_diameter_um),
            "branchpoint_count": int(branchpoint_count),
            "branchpoint_density_per_mm2": float(branchpoint_density),
            "fractal_dimension": float(fractal_dim['skeleton'][4]),  # Displaying the box_size=4 skeleton FD by default
            "mean_tortuosity": float(mean_tortuosity),
        })

        # To report
        micro_stats = {
            "Name": canvas.FileLabelName,
            "VAD": round(float(vad_pct), 1),
            "VLD_pct": round(float(vessel_length_density_pct), 1),
            "VLD_mminv": round(float(vessel_length_density_mminv), 1),
            "varLengths": int(var_length),
            "skewLengths": round(float(skew_length), 2),
            "kurtLengths": round(float(kurt_length), 2),
            "MeanDiam": round(float(mean_diameter_um), 1),
            "MedianDiam": round(float(median_diameter_um), 1),
            "varDiams": int(var_diameter_um),
            "skewDiams": round(float(skew_diameter_um), 2),
            "kurtDiams": round(float(kurt_diameter_um), 2),
            "BD": round(float(branchpoint_density), 2),
            "Fractal_dimension (Skeleton)": round(float(fractal_dim['skeleton'][4]), 2),
            "Fractal_dimension (Binary)": round(float(fractal_dim['binary'][4]), 2),
            "AOC": round(float(mean_tortuosity), 2),
            "varTort": round(float(var_tortuosity), 2),
            "skewTort": round(float(skew_tortuosity), 2),
            "kurtTort": round(float(kurt_tortuosity), 2),
        }

        # Tortuosity metrics (PWAOC, SOAM, etc.)
        canvas.new_tort_metrics = BiomarkerAnalyzer.new_tortuosity_metrics(
            links=links,
            image_size_var=canvas.image_size_var,
            fullImSizePix=canvas.fullImSizePix,
        )
        canvas.new_tort_metrics = {key: round(float(value), 2) for key, value in canvas.new_tort_metrics.items()}
        micro_stats.update(canvas.new_tort_metrics)

        # Save the smoothed skeleton: this same smoothing now feeds every metric above, not just SOAM
        if hasattr(canvas, "current_save_folder"):
            images_dir = os.path.join(canvas.current_save_folder, "images")
            os.makedirs(images_dir, exist_ok=True)

            image_identifier = canvas.FileLabelName + '_' + canvas.img_type_var.get()
            twig_size = canvas.twig_size.get()
            curr_idx = len([
                f for f in os.listdir(images_dir)
                if f"{image_identifier}_Skeletonised_TwigSize" in f
            ])

            smoothed_skeleton = BiomarkerAnalyzer._rasterize_smoothed_skeleton(links, pix2mm, binary.shape)
            smoothed_path = os.path.join(
                images_dir,
                f"{image_identifier}_Skeletonised_TwigSize{twig_size}_{curr_idx}.png"
            )
            cv2.imwrite(smoothed_path, smoothed_skeleton)
            print(f"Smoothed skeleton image saved to: {smoothed_path}")

        # Function parameters (Frangi, MedFilt, etc.)
        param_stats = {
            "MedFilt_Kernel": int(canvas.kernel_size.get()) if canvas.med_filt_bool.get() else "N/A",
            "Frangi_sigma_min": int(canvas.frangi_min.get()) if canvas.frangi_bool.get() else "N/A",
            "Frangi_sigma_max": int(canvas.frangi_max.get()) if canvas.frangi_bool.get() else "N/A",
            "Jerman_sigmas": ",".join(s.strip() for s in canvas.jerman_sigmas.get().split(',')) if canvas.jerman_bool.get() else "N/A",
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
                text=f"{vessel_length_density_mminv:.2f} (1/mm)",
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
    def _rasterize_smoothed_skeleton(links, pix2mm, image_shape):
        """Rasterize smoothed link centerlines (mm space) into a single 0/255 skeleton image."""
        skeleton_img = np.zeros(image_shape, dtype=np.uint8)
        if not links or pix2mm <= 0:
            return skeleton_img

        height, width = image_shape
        for link in links:
            points = np.asarray(link.points, dtype=float)
            if points.shape[0] == 0:
                continue

            pixel_points = np.rint(points / pix2mm).astype(int)
            rows = np.clip(pixel_points[:, 0], 0, height - 1)
            cols = np.clip(pixel_points[:, 1], 0, width - 1)

            if len(rows) == 1:
                cv2.circle(skeleton_img, (int(cols[0]), int(rows[0])), 0, 255, -1)
                continue

            for j in range(len(rows) - 1):
                cv2.line(skeleton_img, (int(cols[j]), int(rows[j])), (int(cols[j + 1]), int(rows[j + 1])), 255, 1)

        return skeleton_img

    @staticmethod
    #! This is the one being used by BiomarkerAnalyzer.process() and in regional analysis
    def new_tortuosity_metrics(links, image_size_var, fullImSizePix):
        """Compute summarized tortuosity metrics directly from graph links."""
        if links is None or len(links) == 0:
            return {
                "PWAOC_mean": np.nan,
                "PWAOC_std": np.nan,
                "SOAM_mean": np.nan,
                "SOAM_std": np.nan,
                "tortDensity_mean": np.nan,
                "tortDensity_std": np.nan,
            }

        # Image scale
        image_size_mm = float(image_size_var.get())
        img_height, _ = fullImSizePix
        pix2mm = image_size_mm / img_height if img_height > 0 else 0.0

        per_link_metrics = []

        for link in links:
            #! Use Janelle's smoothing
            metrics = BiomarkerAnalyzer._compute_new_tortuosity_metrics(
                link.cols,
                link.rows,
                link.points,
                pix2mm,
            )
            if metrics is not None:
                per_link_metrics.append(metrics)

        return BiomarkerAnalyzer._summarize_new_tort_metrics(per_link_metrics)