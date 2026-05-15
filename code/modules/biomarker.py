# modules/biomarker.py

import numpy as np
import pandas as pd
from tkinter import Canvas
from scipy.ndimage import distance_transform_edt
from modules.write_excel import *


class BiomarkerAnalyzer:
    """
    Compute vessel biomarkers from the current canvas state.
    Results are stored in canvas.metrics and shown in the GUI.
    """

    @staticmethod
    def _movmean(arr, window):
        """Compute a centered moving average with edge-aware truncation."""
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

    @staticmethod
    def _compute_new_tortuosity_metrics_from_xy(vessel_x, vessel_y, pix2mm):
        """Compute PWAOC and SOAM tortuosity metrics for one vessel centerline."""
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

        if numPoints < 3:
            SOAM = 0.0
        else:
            totalWeightedAngle = 0.0

            for j in range(1, numPoints - 1):
                v1 = np.array([
                    vesselX[j] - vesselX[j - 1],
                    vesselY[j] - vesselY[j - 1],
                ])
                v2 = np.array([
                    vesselX[j + 1] - vesselX[j],
                    vesselY[j + 1] - vesselY[j],
                ])

                cosTheta = np.clip(
                    np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + eps),
                    -1,
                    1,
                )
                totalWeightedAngle += np.arccos(cosTheta)

            SOAM = totalWeightedAngle / arcLength

        return {
            "PWAOC": PWAOC,
            "SOAM": SOAM,
        }

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
    def _matlab_round(value, ndigits=0):
        """Round scalar metrics while preserving NaN for undefined MATLAB-like outputs."""
        if value is None or not np.isfinite(value):
            return np.nan
        rounded = np.round(value, ndigits)
        if ndigits == 0:
            return int(rounded)
        return float(rounded)

    @staticmethod
    def _sample_variance(values):
        """Return MATLAB-style sample variance, with singleton vectors equal to zero."""
        values = np.asarray(values, dtype=float)
        values = values[np.isfinite(values)]
        if values.size == 0:
            return np.nan
        if values.size == 1:
            return 0.0
        return float(np.var(values, ddof=1))

    @staticmethod
    def _skewness(values):
        """Return MATLAB default skewness for finite values."""
        values = np.asarray(values, dtype=float)
        values = values[np.isfinite(values)]
        n = values.size
        if n < 3:
            return np.nan
        centered = values - np.mean(values)
        std = np.sqrt(np.mean(centered ** 2))
        if std == 0:
            return np.nan
        biased_skewness = np.mean(centered ** 3) / (std ** 3)
        return float(np.sqrt(n * (n - 1)) / (n - 2) * biased_skewness)

    @staticmethod
    def _kurtosis(values):
        """Return MATLAB default Pearson kurtosis for finite values."""
        values = np.asarray(values, dtype=float)
        values = values[np.isfinite(values)]
        n = values.size
        if n < 4:
            return np.nan
        centered = values - np.mean(values)
        std = np.sqrt(np.mean(centered ** 2))
        if std == 0:
            return np.nan
        biased_excess = np.mean(centered ** 4) / (std ** 4) - 3.0
        unbiased_excess = ((n - 1) / ((n - 2) * (n - 3))) * ((n + 1) * biased_excess + 6.0)
        return float(unbiased_excess + 3.0)

    @staticmethod
    def _compute_link_measurements(links, binary, diameter_map=None):
        """Populate MATLAB-style per-link length, diameter, and tortuosity fields."""
        if diameter_map is None:
            diameter_map = distance_transform_edt(binary > 0) * 2

        image_shape = binary.shape
        link_lengths_pix = []
        link_diameters_pix = []
        link_tortuosities = []

        for link in links:
            indices = np.asarray(link.path, dtype=int)
            if indices.size == 0:
                continue

            rows, cols = np.unravel_index(indices, image_shape)
            coords = np.column_stack((cols, rows)).astype(float)

            if coords.shape[0] >= 2:
                diffs = np.diff(coords, axis=0)
                length_pix = float(np.sum(np.sqrt(np.sum(diffs * diffs, axis=1))))
                end2end_length = float(np.linalg.norm(coords[-1] - coords[0]))
                tortuosity = length_pix / end2end_length if end2end_length > 0 else np.inf
            else:
                length_pix = 0.0
                end2end_length = 0.0
                tortuosity = np.inf

            diameter_measurements = diameter_map[rows, cols]
            diameter = float(np.mean(diameter_measurements)) if diameter_measurements.size > 0 else np.nan

            link.x = rows
            link.y = cols
            link.pixLength = length_pix
            link.end2endLength = end2end_length
            link.tortuosity = tortuosity
            link.diameterMeasurements = diameter_measurements
            link.diameter = diameter

            link_lengths_pix.append(length_pix)
            if np.isfinite(diameter):
                link_diameters_pix.append(diameter)
            link_tortuosities.append(tortuosity)

        return (
            np.asarray(link_lengths_pix, dtype=float),
            np.asarray(link_diameters_pix, dtype=float),
            np.asarray(link_tortuosities, dtype=float),
        )

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

            metrics = BiomarkerAnalyzer._compute_new_tortuosity_metrics_from_xy(
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
        full_im_size_pix = getattr(canvas, "fullImSizePix", None)
        if full_im_size_pix is None:
            full_im_size_pix = (Nx, Ny)
        full_image_pixels = np.asarray(full_im_size_pix, dtype=float).ravel()
        full_image_height_pix = float(full_image_pixels[0]) if full_image_pixels.size > 0 else float(Nx)

        # Read optional image shape from MATLAB-compatible state. Default OCTA images are rectangular.
        img_shape_name = str(getattr(canvas, "imgShape", "rect")).lower()
        is_circular_roi = img_shape_name in {"circ", "circle", "circular"}

        # Image area in pixels
        if is_circular_roi:
            img_area_pix = float(np.pi * (Nx / 2.0) ** 2)
        else:
            img_area_pix = float(Nx * Nx)

        # Vessel Area Density (VAD %)
        vessel_sum = float(np.sum(binary))
        vessel_pixels = vessel_sum / 255.0
        vad_pct = round(vessel_pixels / img_area_pix * 100.0, 2)

        # Pixel size and physical areas (mm²)
        if full_image_height_pix > 0:
            pix_size_mm = image_size_mm / full_image_height_pix
        else:
            pix_size_mm = 0.0

        img_area_mm2 = img_area_pix * (pix_size_mm ** 2)
        vessel_area_mm2 = vessel_pixels * (pix_size_mm ** 2)

        radius_map = distance_transform_edt(binary > 0)
        diameter_map = radius_map * 2
        link_lengths_pix, link_diameters_pix, tortuosities = BiomarkerAnalyzer._compute_link_measurements(
            links,
            binary,
            diameter_map=diameter_map,
        )

        # Vessel length density (mm per mm²)
        total_length_pix = float(np.sum(link_lengths_pix))
        total_length_mm = total_length_pix * pix_size_mm
        length_area_mm2 = image_size_mm ** 2
        vessel_length_density = total_length_mm / length_area_mm2
        vessel_length_density_pct = (
            round((total_length_mm * pix_size_mm) / img_area_mm2, 4) * 100.0
            if img_area_mm2 > 0
            else 0.0
        )
        vessel_length_density_mminv = (
            round(total_length_mm / img_area_mm2, 4)
            if img_area_mm2 > 0
            else 0.0
        )

        link_lengths_mm = link_lengths_pix * pix_size_mm
        link_lengths_um = link_lengths_mm * 1000.0

        if link_lengths_um.size > 0:
            mean_length_um = round(float(np.mean(link_lengths_um)))
            median_length_um = round(float(np.median(link_lengths_um)))
        else:
            mean_length_um = 0
            median_length_um = 0

        # Mean diameter (output: μm)
        diameters_pix = np.asarray(link_diameters_pix, dtype=float)
        diameters_um = diameters_pix * pix_size_mm * 1000.0
        canvas.vessel_diameters_um = diameters_um

        if diameters_um.size > 0:
            mean_diameter_pix = np.mean(diameters_pix)
            mean_diameter_mm = mean_diameter_pix * pix_size_mm #pix_size_mm -> pix_to_mm
            mean_diameter_um = mean_diameter_mm * 1000.0
            median_diameter_um = float(np.median(diameters_um))
        else:
            mean_diameter_um = 0.0
            median_diameter_um = 0.0

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
        finite_tortuosities = tortuosities[np.isfinite(tortuosities)]
        canvas.vessel_lengths_mm = link_lengths_mm
        canvas.vessel_lengths_um = link_lengths_um
        canvas.vessel_tortuosities = finite_tortuosities

        if finite_tortuosities.size > 0:
            mean_tortuosity = np.mean(finite_tortuosities)
        else:
            mean_tortuosity = 0.0

        total_length_rounded_mm = round(total_length_mm, 2)

        diameter_variance = BiomarkerAnalyzer._matlab_round(
            BiomarkerAnalyzer._sample_variance(diameters_um),
        )
        diameter_skewness = BiomarkerAnalyzer._matlab_round(
            BiomarkerAnalyzer._skewness(diameters_um),
            2,
        )
        diameter_kurtosis = BiomarkerAnalyzer._matlab_round(
            BiomarkerAnalyzer._kurtosis(diameters_um),
            2,
        )

        length_variance = BiomarkerAnalyzer._matlab_round(
            BiomarkerAnalyzer._sample_variance(link_lengths_um),
        )
        length_skewness = BiomarkerAnalyzer._matlab_round(
            BiomarkerAnalyzer._skewness(link_lengths_um),
            2,
        )
        length_kurtosis = BiomarkerAnalyzer._matlab_round(
            BiomarkerAnalyzer._kurtosis(link_lengths_um),
            2,
        )

        tortuosity_variance = BiomarkerAnalyzer._matlab_round(
            BiomarkerAnalyzer._sample_variance(finite_tortuosities),
            3,
        )
        tortuosity_skewness = BiomarkerAnalyzer._matlab_round(
            BiomarkerAnalyzer._skewness(finite_tortuosities),
            2,
        )
        tortuosity_kurtosis = BiomarkerAnalyzer._matlab_round(
            BiomarkerAnalyzer._kurtosis(finite_tortuosities),
        )

        # Store metrics in canvas
        if not hasattr(canvas, "metrics"):
            canvas.metrics = {}

        canvas.metrics.update({
            "vessel_area_density_pct": float(vad_pct),
            "vessel_area_mm2": float(vessel_area_mm2),
            "image_area_mm2": float(img_area_mm2),
            "vessel_length_density_mm_per_mm2": float(vessel_length_density),
            "vessel_length_density_pct": float(vessel_length_density_pct),
            "total_vessel_length_mm": float(total_length_rounded_mm),
            "mean_length_um": float(mean_length_um),
            "median_length_um": float(median_length_um),
            "mean_diameter_um": float(mean_diameter_um),
            "median_diameter_um": float(median_diameter_um),
            "branchpoint_count": int(branchpoint_count),
            "branchpoint_density_per_mm2": float(branchpoint_density),
            "fractal_dimension": float(fractal_dim),
            "mean_tortuosity": float(mean_tortuosity),
            "diameter_variance": diameter_variance,
            "diameter_skewness": diameter_skewness,
            "diameter_kurtosis": diameter_kurtosis,
            "length_variance": length_variance,
            "length_skewness": length_skewness,
            "length_kurtosis": length_kurtosis,
            "tortuosity_variance": tortuosity_variance,
            "tortuosity_skewness": tortuosity_skewness,
            "tortuosity_kurtosis": tortuosity_kurtosis,
        })
        micro_stats = {
            "name": canvas.FileLabelName,
            "Vessel area density": float(vad_pct),
            "Total vessel length": float(total_length_rounded_mm),
            "VLD_pct": float(vessel_length_density_pct),
            "VLD_mminv": float(vessel_length_density_mminv),
            "Mean length": float(mean_length_um),
            "Median length": float(median_length_um),
            "varLengths": length_variance,
            "skewLengths": length_skewness,
            "kurtLengths": length_kurtosis,
            "Mean diameter": float(mean_diameter_um),
            "Median diameter": float(median_diameter_um),
            "varDiams": diameter_variance,
            "skewDiams": diameter_skewness,
            "kurtDiams": diameter_kurtosis,
            "Branchpoint density": float(branchpoint_density),
            "Fractal dimension": float(fractal_dim),
            "Mean tortuosity": float(mean_tortuosity),
            "varTort": tortuosity_variance,
            "skewTort": tortuosity_skewness,
            "kurtTort": tortuosity_kurtosis,
        }

        # Compute new tortuosity metrics and add to micro_stats
        canvas.new_tort_metrics = BiomarkerAnalyzer.new_tortuosity_metrics(
            links=canvas.skeleton_links,
            binary_image=canvas.binary_image,
            image_size_var=canvas.image_size_var,
            fullImSizePix=canvas.fullImSizePix,
        )
        micro_stats.update(canvas.new_tort_metrics)

        parameters = {
            "Frangi Sigma Min": canvas.frangi_min.get(),
            "Frangi Sigma Max": canvas.frangi_max.get(),
            "Median Filter Kernel Size": canvas.kernel_size.get() if canvas.med_filt_bool.get() else 0,
            "Twig Size": canvas.twig_size.get(),
        }
        micro_stats.update(parameters)

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
            canvas.itemconfig(canvas.fractal_dim_value_id, text=f"{fractal_dim:.3f}")

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
            metrics = BiomarkerAnalyzer._compute_new_tortuosity_metrics_from_xy(
                cols,
                rows,
                pix2mm,
            )
            if metrics is not None:
                per_link_metrics.append(metrics)

        return BiomarkerAnalyzer._summarize_new_tort_metrics(per_link_metrics)

 
    @staticmethod
    def new_tortuosity_metrics_all(canvas: Canvas) -> None:
        """Compute the legacy full tortuosity metric set for every link on the canvas."""
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
            trim = int(np.floor(0.05 * arr.size))
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
                # t = np.gradient(1/curvature)
                curv_safe = curvature.copy()
                curv_safe[np.abs(curv_safe) < 1e-6] = np.nan
                inv_curv = 1.0 / curv_safe
                t = np.gradient(inv_curv)
                # t[~np.isfinite(t)] = np.nan
                # VCI2 = np.nanmean(np.abs(t))

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

 
