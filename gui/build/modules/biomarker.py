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
        # --- Validate Input Data ---
        if not hasattr(canvas, "binary_image"):
            return

        binary = canvas.binary_image

        # Ensure binary is a valid 2D numpy array
        if not isinstance(binary, np.ndarray):
            try:
                binary = np.asarray(binary)
            except Exception:
                return
        
        if binary.ndim != 2:
            return

        # Ensure correct type (uint8)
        if binary.dtype != np.uint8:
            binary = binary.astype(np.uint8)

        Nx, Ny = binary.shape

        # --- Retrieve Image Parameters ---
        # Get physical size (mm), default to 1.0 if missing
        if hasattr(canvas, "image_size_var"):
            image_size_mm = float(canvas.image_size_var.get())
        else:
            image_size_mm = 1.0

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

        # --- Store Metrics in Canvas ---
        if not hasattr(canvas, "metrics"):
            canvas.metrics = {}

        canvas.metrics.update({
            "vessel_area_density_pct": vad_pct,
            "vessel_area_mm2": float(vessel_area_mm2),
            "image_area_mm2": float(img_area_mm2)
        })

        # --- Update GUI Display ---
        if hasattr(canvas, "vad_value_id"):
            canvas.itemconfig(canvas.vad_value_id, text=f"{vad_pct} %")