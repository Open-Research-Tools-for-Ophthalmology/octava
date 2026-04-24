import re
from tkinter import Canvas
import numpy as np
from skimage.draw import disk, polygon
import pandas as pd
from modules.skeletonise import *
from modules.change_status import *
from modules.write_excel import *
from modules.biomarker import BiomarkerAnalyzer
from enum import Enum
import math
from scipy.ndimage import distance_transform_edt
import os
from openpyxl import Workbook
import cv2

RIGHT_EYE = "Right Eye"

class GridType(Enum):
	'''Enum for different types of regional analysis grids.'''
	SQUARE_GRID = "Square grid"
	ETDRS_GRID = "ETDRS grid"
	EXTENDED_ETDRS_GRID = "Extended"
	ONH = "ONH"
	FOVEAL_RING = "Foveal rings"

def run_regional_analysis(canvas):
	"""Run all enabled regional analysis modes for the current canvas state.

	Args:
		canvas: Tk canvas-like object holding the loaded image, masks, scale,
			and region-analysis configuration flags.

	Returns:
		None. Results are written back onto ``canvas`` and exported to Excel.
	"""
	change_status_to_waiting(canvas, status="● Regional analysis...")

	# Get image size from canvas
	image_size_mm = canvas.image_size_var.get()
	# Get image dimensions
	img_height, img_width = canvas.fullImSizePix
	pix_to_mm = image_size_mm / img_height

	binary = canvas.binary_image
	original = canvas.original_img
	
	if canvas.square_grid_bool.get():
		apply_square_grid(canvas, binary, original, pix_to_mm)

	if canvas.etdrs_grid_bool.get():
		apply_etdrs_grid(canvas, binary, original, pix_to_mm, image_size_mm)

	if canvas.extended_etdrs_bool.get():
		apply_extended_etdrs_grid(canvas,binary, original, pix_to_mm, image_size_mm)

	if canvas.foveal_ring_bool.get():
		apply_foveal_ring(canvas,binary,original, pix_to_mm, image_size_mm)

	if canvas.optic_nerve_head_bool.get():
		apply_onh(canvas,binary, original, pix_to_mm, image_size_mm)


def apply_square_grid(canvas, binary, original, pix_to_mm):
	"""Split the image into a 3x3 square grid and analyze each region.

	Args:
		canvas: Tk canvas-like object that stores shared app state.
		binary: Binary vessel mask for the full image.
		original: Grayscale source image for the full image.
		pix_to_mm: Physical scale conversion from pixels to millimeters.

	Returns:
		None. Regional results are delegated to ``run_analysis_on_regions``.
	"""
	# Divide image into 3x3 grid
	regionsize = np.floor(np.array(canvas.fullImSizePix) / 3).astype(int)
	h, w = regionsize

	binaryReg = []
	imgReg = []

	# -------- Binary regions --------
	binaryReg.append(binary[0:h, 0:w])
	binaryReg.append(binary[0:h, w : 2 * w])
	binaryReg.append(binary[0:h, 2 * w : 3 * w])

	binaryReg.append(binary[h : 2 * h, 0:w])
	binaryReg.append(binary[h : 2 * h, w : 2 * w])
	binaryReg.append(binary[h : 2 * h, 2 * w : 3 * w])

	binaryReg.append(binary[2 * h : 3 * h, 0:w])
	binaryReg.append(binary[2 * h : 3 * h, w : 2 * w])
	binaryReg.append(binary[2 * h : 3 * h, 2 * w : 3 * w])

	# -------- Original Image regions --------
	imgReg.append(original[0:h, 0:w])
	imgReg.append(original[0:h, w : 2 * w])
	imgReg.append(original[0:h, 2 * w : 3 * w])

	imgReg.append(original[h : 2 * h, 0:w])
	imgReg.append(original[h : 2 * h, w : 2 * w])
	imgReg.append(original[h : 2 * h, 2 * w : 3 * w])

	imgReg.append(original[2 * h : 3 * h, 0:w])
	imgReg.append(original[2 * h : 3 * h, w : 2 * w])
	imgReg.append(original[2 * h : 3 * h, 2 * w : 3 * w])

	# -------- Region labels --------
	if canvas.eye_var.get() == RIGHT_EYE:
		canvas.RAlabels = [
			"Supero-temporal",
			"Superior",
			"Supero-nasal",
			"Temporal",
			"Central",
			"Nasal",
			"Infero-temporal",
			"Inferior",
			"Infero-nasal",
		]
	else:
		canvas.RAlabels = [
			"Supero-nasal",
			"Superior",
			"Supero-temporal",
			"Nasal",
			"Central",
			"Temporal",
			"Infero-nasal",
			"Inferior",
			"Infero-temporal",
		]

	run_analysis_on_regions(canvas, binaryReg, imgReg, imgArea_pix_vec=None, pix_to_mm=pix_to_mm, grid_type=GridType.SQUARE_GRID)

def apply_etdrs_grid(canvas, binary, original, pix_to_mm, image_size_mm):
	"""Construct an ETDRS parafoveal grid and analyze its regions.

	Args:
		canvas: Tk canvas-like object that stores shared app state.
		binary: Binary vessel mask for the full image.
		original: Grayscale source image for the full image.
		pix_to_mm: Physical scale conversion from pixels to millimeters.
		image_size_mm: Real image width in millimeters.

	Returns:
		None. Regional results are delegated to ``run_analysis_on_regions``.
	"""
	H, W = canvas.fullImSizePix
	rad_1mm = 0.5 * H / image_size_mm
	rad_3mm = 1.5 * H / image_size_mm

	if getattr(canvas, "FAZ_ctr", None) is None:
		canvas.FAZ_ctr = np.array([H // 2, W // 2])
	cy, cx = canvas.FAZ_ctr

	# foveal and parafoveal masks
	foveal_mask = np.zeros((H, W), dtype=bool)
	rr, cc = disk((cy, cx), rad_1mm, shape=(H, W))
	foveal_mask[rr, cc] = True

	outer_mask = np.zeros((H, W), dtype=bool)
	rr, cc = disk((cy, cx), rad_3mm, shape=(H, W))
	outer_mask[rr, cc] = True

	parafoveal_mask = outer_mask & (~foveal_mask)

	# sector masks
	sector_masks = np.zeros((H, W, 6), dtype=bool)

	for ii in range(6):
		theta = np.linspace(0, -60, 1000) - 60 * ii
		x = rad_3mm * np.cos(np.deg2rad(theta)) + cx
		y = rad_3mm * np.sin(np.deg2rad(theta)) + cy

		poly_x = np.concatenate([[cx], x, [cx]])
		poly_y = np.concatenate([[cy], y, [cy]])

		rr, cc = polygon(poly_y, poly_x, shape=(H, W))
		mask = np.zeros((H, W), dtype=bool)
		mask[rr, cc] = True

		sector_masks[:, :, ii] = mask & (~foveal_mask)

	#binary image
	binaryReg = [None] * 8
	
	binaryReg[0] = binary * foveal_mask #foveal circle
	y1 = int(round(max(cy - rad_3mm, 0)))
	y2 = int(round(min(cy + rad_3mm, H)))
	x1 = int(round(max(cx - rad_3mm, 0)))
	x2 = int(round(min(cx + rad_3mm, W)))
	#Crops to a bounding box around FAZ (± rad_3mm)
	binaryReg[0]=binaryReg[0][y1:y2, x1:x2]

	binaryReg[1] = binary * parafoveal_mask #parafoveal ring

	binaryReg[2] = binary * (sector_masks[:, :, 0] | sector_masks[:, :, 1] | sector_masks[:, :, 2]) #superior hemi-parafoveal rim
	binaryReg[2] = binaryReg[2][:H//2, :]

	binaryReg[3] = binary * (sector_masks[:, :, 3] | sector_masks[:, :, 4] | sector_masks[:, :, 5])#inferior hemi-parafoveal rim
	binaryReg[3] = binaryReg[3][H//2:, :]

	binaryReg[4] = binary * (sector_masks[:, :, 0] | sector_masks[:, :, 5])
	binaryReg[4] = binaryReg[4][:, W//2:]#temporal/nasal parafoveal rim

	binaryReg[5] = binary * (sector_masks[:, :, 2] | sector_masks[:, :, 3])
	binaryReg[5] = binaryReg[5][:, :W//2]#temporal/nasal parafoveal rim

	binaryReg[6] = binary * sector_masks[:, :, 1] #superior-parafoveal rim
	binaryReg[6] = binaryReg[6][:H//2, :]

	binaryReg[7] = binary * sector_masks[:, :, 4]#inferior-parafoveal rim
	binaryReg[7] = binaryReg[7][H//2:, :]
	
	# original image
	imgReg = [None] * 8

	imgReg[0] = original * foveal_mask #foveal circle
	imgReg[0]    = imgReg[0][y1:y2, x1:x2] #Crops to a bounding box around FAZ (± rad_3mm)

	imgReg[1] = original * parafoveal_mask #parafoveal rim

	imgReg[2] = original * (sector_masks[:, :, 0] | sector_masks[:, :, 1] | sector_masks[:, :, 2])#superior hemi-parafoveal rim
	imgReg[2] = imgReg[2][:H//2, :]

	imgReg[3] = original * (sector_masks[:, :, 3] | sector_masks[:, :, 4] | sector_masks[:, :, 5])#inferior hemi-parafoveal rim
	imgReg[3] = imgReg[3][H//2:, :]

	imgReg[4] = original * (sector_masks[:, :, 0] | sector_masks[:, :, 5])
	imgReg[4] = imgReg[4][:, W//2:] #tempo/nasal parafoveal rim

	imgReg[5] = original * (sector_masks[:, :, 2] | sector_masks[:, :, 3])
	imgReg[5] = imgReg[5][:, :W//2]#tempo/nasal parafoveal rim

	imgReg[6] = original * sector_masks[:, :, 1]#superior-parafoveal rim
	imgReg[6] = imgReg[6][:H//2, :]

	imgReg[7] = original * sector_masks[:, :, 4]#inferior-parafoveal rim
	imgReg[7] = imgReg[7][H//2:, :]

	#set region labels
	if canvas.eye_var.get() == RIGHT_EYE:
		canvas.RAlabels = [
			"Foveal circle",
			"Parafoveal rim",
			"Superior hemi-parafoveal rim",
			"Inferior hemi-parafoveal rim",
			"Nasal parafoveal rim",
			"Tempo parafoveal rim",
			"Superior parafoveal rim",
			"Inferior parafoveal rim"
		]
	else:
		canvas.RAlabels = [
			"Foveal circle",
			"Parafoveal rim",
			"Superior hemi-parafoveal rim",
			"Inferior hemi-parafoveal rim",
			"Tempo parafoveal rim",
			"Nasal parafoveal rim",
			"Superior parafoveal rim",
			"Inferior parafoveal rim"
		]

	#area vectors
	imgArea_pix_vec = [
		np.sum(foveal_mask),
		np.sum(parafoveal_mask),
		np.sum(sector_masks[:, :, 0] | sector_masks[:, :, 1] | sector_masks[:, :, 2]),
		np.sum(sector_masks[:, :, 3] | sector_masks[:, :, 4] | sector_masks[:, :, 5]),
		np.sum(sector_masks[:, :, 0] | sector_masks[:, :, 5]),
		np.sum(sector_masks[:, :, 2] | sector_masks[:, :, 3]),
		np.sum(sector_masks[:, :, 1]),
		np.sum(sector_masks[:, :, 1]) #? was np.sum(sector_masks[:, :, 1]) a typo in original code? should be np.sum(sector_masks[:, :, 4])?
	]
	
	run_analysis_on_regions(
		canvas,
		binaryReg=binaryReg,
		imgReg=imgReg,
		imgArea_pix_vec=imgArea_pix_vec,
		pix_to_mm=pix_to_mm,
		grid_type=GridType.ETDRS_GRID,   # change per function
	)

def apply_extended_etdrs_grid(canvas, binary,original,pix_to_mm,image_size_mm):
	"""Construct an extended ETDRS grid and analyze its regions.

	Args:
		canvas: Tk canvas-like object that stores shared app state.
		binary: Binary vessel mask for the full image.
		original: Grayscale source image for the full image.
		pix_to_mm: Physical scale conversion from pixels to millimeters.
		image_size_mm: Real image width in millimeters.

	Returns:
		None. Regional results are delegated to ``run_analysis_on_regions``.
	"""
	H, W = canvas.fullImSizePix
	rad_1mm = 0.5 * H / image_size_mm
	rad_3mm = 1.5 * H / image_size_mm

	if getattr(canvas, "FAZ_ctr", None) is None:
		canvas.FAZ_ctr = np.array([H // 2, W // 2])
	cy, cx = canvas.FAZ_ctr

	# Foveal & parafoveal masks
	foveal_mask = np.zeros((H, W), dtype=bool)
	rr, cc = disk((cy, cx), rad_1mm, shape=(H, W))
	foveal_mask[rr, cc] = True

	outer_mask = np.zeros((H, W), dtype=bool)
	rr, cc = disk((cy, cx), rad_3mm, shape=(H, W))
	outer_mask[rr, cc] = True

	parafoveal_mask = outer_mask & (~foveal_mask)

	# Sector masks (8 × 45°)
	sector_masks = np.zeros((H, W, 8), dtype=bool)

	for ii in range(8):
		theta = np.linspace(0, -45, 1000) - 45 * ii
		x = rad_3mm * np.cos(np.deg2rad(theta)) + cx
		y = rad_3mm * np.sin(np.deg2rad(theta)) + cy

		poly_x = np.concatenate([[cx], x, [cx]])
		poly_y = np.concatenate([[cy], y, [cy]])

		rr, cc = polygon(poly_y, poly_x, shape=(H, W))
		mask = np.zeros((H, W), dtype=bool)
		mask[rr, cc] = True

		sector_masks[:, :, ii] = mask & (~foveal_mask)

	# binary image
	binaryReg = [None] * 10

	binaryReg[0] = binary * sector_masks[:, :, 0]
	binaryReg[0] = binaryReg[0][:H//2, W//2:]

	binaryReg[1] = binary * sector_masks[:, :, 1]
	binaryReg[1] = binaryReg[1][:H//2, W//2:]

	binaryReg[2] = binary * sector_masks[:, :, 2]
	binaryReg[2] = binaryReg[2][:H//2, :W//2]

	binaryReg[3] = binary * sector_masks[:, :, 3]
	binaryReg[3] = binaryReg[3][:H//2, :W//2]

	binaryReg[4] = binary * sector_masks[:, :, 4]
	binaryReg[4] = binaryReg[4][H//2:, :W//2]

	binaryReg[5] = binary * sector_masks[:, :, 5]
	binaryReg[5] = binaryReg[5][H//2:, :W//2]

	binaryReg[6] = binary * sector_masks[:, :, 6]
	binaryReg[6] = binaryReg[6][H//2:, W//2:]

	binaryReg[7] = binary * sector_masks[:, :, 7]
	binaryReg[7] = binaryReg[7][H//2:, W//2:]

	binaryReg[8] = binary * (sector_masks[:, :, 0] | sector_masks[:, :, 7])
	binaryReg[8] = binaryReg[8][:, W//2:]

	binaryReg[9] = binary * (sector_masks[:, :, 3] | sector_masks[:, :, 4])
	binaryReg[9] = binaryReg[9][:, :W//2]


	#original image
	imgReg = [None] * 10

	imgReg[0] = original * sector_masks[:, :, 0]
	imgReg[0] = imgReg[0][:H//2, W//2:]

	imgReg[1] = original * sector_masks[:, :, 1]
	imgReg[1] = imgReg[1][:H//2, W//2:]

	imgReg[2] = original * sector_masks[:, :, 2]
	imgReg[2] = imgReg[2][:H//2, :W//2]

	imgReg[3] = original * sector_masks[:, :, 3]
	imgReg[3] = imgReg[3][:H//2, :W//2]

	imgReg[4] = original * sector_masks[:, :, 4]
	imgReg[4] = imgReg[4][H//2:, :W//2]

	imgReg[5] = original * sector_masks[:, :, 5]
	imgReg[5] = imgReg[5][H//2:, :W//2]

	imgReg[6] = original * sector_masks[:, :, 6]
	imgReg[6] = imgReg[6][H//2:, W//2:]

	imgReg[7] = original * sector_masks[:, :, 7]
	imgReg[7] = imgReg[7][H//2:, W//2:]

	imgReg[8] = original * (sector_masks[:, :, 0] | sector_masks[:, :, 7])
	imgReg[8] = imgReg[8][:, W//2:]

	imgReg[9] = original * (sector_masks[:, :, 3] | sector_masks[:, :, 4])
	imgReg[9] = imgReg[9][:, :W//2]

	#set region labels
	if canvas.eye_var.get() == RIGHT_EYE:
		canvas.RAlabels = ["Super nasal", "Nasal superior", "Temporal superior", "Super temporal", "Inferio temporal", "Temporal inferior", "Nasal inferior", "Inferio nasal", "Nasal wedge", "Temporal wedge"]
	else:
		canvas.RAlabels =["Super temporal", "Temporal superior", "Nasal superior", "Super nasal", "Inferio nasal", "Nasal inferior", "Temporal inferior", "Inferio temporal", "Temporal wedge", "Nasal wedge"]

	# Area (pixels)
	imgArea_pix_vec = [
		np.sum(sector_masks[:, :, 0]),
		np.sum(sector_masks[:, :, 1]),
		np.sum(sector_masks[:, :, 2]),
		np.sum(sector_masks[:, :, 3]),
		np.sum(sector_masks[:, :, 4]),
		np.sum(sector_masks[:, :, 5]),
		np.sum(sector_masks[:, :, 6]),
		np.sum(sector_masks[:, :, 7]),
		np.sum(sector_masks[:, :, 0] | sector_masks[:, :, 7]),
		np.sum(sector_masks[:, :, 3] | sector_masks[:, :, 4]),
	]
	
	run_analysis_on_regions(
		canvas,
		binaryReg=binaryReg,
		imgReg=imgReg,
		imgArea_pix_vec=imgArea_pix_vec,
		pix_to_mm=pix_to_mm,
		grid_type=GridType.EXTENDED_ETDRS_GRID,   # change per function
	) 


def apply_onh(canvas, binary, original,pix_to_mm,image_size_mm):
	"""Construct an ONH/peripapillary grid and analyze its regions.

	Args:
		canvas: Tk canvas-like object that stores shared app state.
		binary: Binary vessel mask for the full image.
		original: Grayscale source image for the full image.
		pix_to_mm: Physical scale conversion from pixels to millimeters.
		image_size_mm: Real image width in millimeters.

	Returns:
		None. Regional results are delegated to ``run_analysis_on_regions``.
	"""
	H, W = canvas.fullImSizePix
	rad_1mm = 1 * H / image_size_mm
	rad_outer = 2.0 * H / image_size_mm #The outer ring may need to be 2.5, 3, or 4.25 - The user will need to input this 

	if getattr(canvas, "FAZ_ctr", None) is None:
		canvas.FAZ_ctr = np.array([H // 2, W // 2])
	cy, cx = canvas.FAZ_ctr
	
	# Inner + outer masks
	ONH_mask_inner = np.zeros((H, W), dtype=bool)
	rr, cc = disk((cy, cx), rad_1mm, shape=(H, W))
	ONH_mask_inner[rr, cc] = True

	outer_mask = np.zeros((H, W), dtype=bool)
	rr, cc = disk((cy, cx), rad_outer, shape=(H, W))
	outer_mask[rr, cc] = True

	PP_mask = outer_mask & (~ONH_mask_inner)   # peripapillary ring

	# Sector masks (8 × 45° wedges)
	sector_masks = np.zeros((H, W, 8), dtype=bool)

	for ii in range(8):
		theta = np.linspace(0, -45, 1000) - 45 * ii
		x = rad_outer * np.cos(np.deg2rad(theta)) + cx
		y = rad_outer * np.sin(np.deg2rad(theta)) + cy

		poly_x = np.concatenate([[cx], x, [cx]])
		poly_y = np.concatenate([[cy], y, [cy]])

		rr, cc = polygon(poly_y, poly_x, shape=(H, W))
		mask = np.zeros((H, W), dtype=bool)
		mask[rr, cc] = True

		sector_masks[:, :, ii] = mask & (~ONH_mask_inner)

	# Binary regions (15 total)
	binaryReg = [None] * 15

	binaryReg[0] = (binary * sector_masks[:, :, 0])[:H//2, W//2:]
	binaryReg[1] = (binary * sector_masks[:, :, 1])[:H//2, W//2:]
	binaryReg[2] = (binary * sector_masks[:, :, 2])[:H//2, :W//2]
	binaryReg[3] = (binary * sector_masks[:, :, 3])[:H//2, :W//2]
	binaryReg[4] = (binary * sector_masks[:, :, 4])[H//2:, :W//2]
	binaryReg[5] = (binary * sector_masks[:, :, 5])[H//2:, :W//2]
	binaryReg[6] = (binary * sector_masks[:, :, 6])[H//2:, W//2:]
	binaryReg[7] = (binary * sector_masks[:, :, 7])[H//2:, W//2:]

	binaryReg[8]  = (binary * (sector_masks[:, :, 0] | sector_masks[:, :, 1] |
														sector_masks[:, :, 2] | sector_masks[:, :, 3]))[:H//2, :]
	binaryReg[9]  = (binary * (sector_masks[:, :, 4] | sector_masks[:, :, 5] |
														sector_masks[:, :, 6] | sector_masks[:, :, 7]))[H//2:, :]

	binaryReg[10] = (binary * (sector_masks[:, :, 1] | sector_masks[:, :, 2]))[:H//2, :]
	binaryReg[11] = (binary * (sector_masks[:, :, 5] | sector_masks[:, :, 6]))[H//2:, :]
	binaryReg[12] = (binary * (sector_masks[:, :, 3] | sector_masks[:, :, 4]))[:, :W//2]
	binaryReg[13] = (binary * (sector_masks[:, :, 0] | sector_masks[:, :, 7]))[:, W//2:]
	binaryReg[14] = binary * PP_mask

	# Image regions (same geometry as binaryReg)
	imgReg = [None] * 15

	imgReg[0] = (original * sector_masks[:, :, 0])[:H//2, W//2:]
	imgReg[1] = (original * sector_masks[:, :, 1])[:H//2, W//2:]
	imgReg[2] = (original * sector_masks[:, :, 2])[:H//2, :W//2]
	imgReg[3] = (original * sector_masks[:, :, 3])[:H//2, :W//2]
	imgReg[4] = (original * sector_masks[:, :, 4])[H//2:, :W//2]
	imgReg[5] = (original * sector_masks[:, :, 5])[H//2:, :W//2]
	imgReg[6] = (original * sector_masks[:, :, 6])[H//2:, W//2:]
	imgReg[7] = (original * sector_masks[:, :, 7])[H//2:, W//2:]

	imgReg[8]  = (original * (sector_masks[:, :, 0] | sector_masks[:, :, 1] |
											sector_masks[:, :, 2] | sector_masks[:, :, 3]))[:H//2, :]
	imgReg[9]  = (original * (sector_masks[:, :, 4] | sector_masks[:, :, 5] |
											sector_masks[:, :, 6] | sector_masks[:, :, 7]))[H//2:, :]

	imgReg[10] = (original * (sector_masks[:, :, 1] | sector_masks[:, :, 2]))[:H//2, :]
	imgReg[11] = (original * (sector_masks[:, :, 5] | sector_masks[:, :, 6]))[H//2:, :]
	imgReg[12] = (original * (sector_masks[:, :, 3] | sector_masks[:, :, 4]))[:, :W//2]
	imgReg[13] = (original * (sector_masks[:, :, 0] | sector_masks[:, :, 7]))[:, W//2:]
	imgReg[14] = original * PP_mask


	#set labels
	if canvas.eye_var.get() == RIGHT_EYE:
		canvas.RAlabels = ["NS","SN","ST","TS","TI","IT","IN","NI",
								"S_hemi","I_hemi","S","I","T","N","PP"]
	else:
		canvas.RAlabels =["TS","ST","SN","NS","NI","IN","IT","TI",
								"S_hemi","I_hemi","S","I","N","T","PP"]


	# Area (pixel counts)
	imgArea_pix_vec = [
			np.sum(sector_masks[:, :, i]) for i in range(8)
	] + [
			np.sum(sector_masks[:, :, 0] | sector_masks[:, :, 1] |
						sector_masks[:, :, 2] | sector_masks[:, :, 3]),
			np.sum(sector_masks[:, :, 4] | sector_masks[:, :, 5] |
						sector_masks[:, :, 6] | sector_masks[:, :, 7]),
			np.sum(sector_masks[:, :, 1] | sector_masks[:, :, 2]),
			np.sum(sector_masks[:, :, 5] | sector_masks[:, :, 6]),
			np.sum(sector_masks[:, :, 3] | sector_masks[:, :, 4]),
			np.sum(sector_masks[:, :, 0] | sector_masks[:, :, 7]),
			np.sum(PP_mask),
	]

	run_analysis_on_regions(
		canvas,
		binaryReg=binaryReg,
		imgReg=imgReg,
		imgArea_pix_vec=imgArea_pix_vec,
		pix_to_mm=pix_to_mm,
		grid_type=GridType.ONH,   # change per function
	)



def apply_foveal_ring(canvas, binary, original,pix_to_mm, image_size_mm):
	"""Construct a concentric foveal ring grid and analyze its regions.

	Args:
		canvas: Tk canvas-like object that stores shared app state.
		binary: Binary vessel mask for the full image.
		original: Grayscale source image for the full image.
		pix_to_mm: Physical scale conversion from pixels to millimeters.
		image_size_mm: Real image width in millimeters.

	Returns:
		None. Regional results are delegated to ``run_analysis_on_regions``.
	"""
	H, W = canvas.fullImSizePix
	rad_1mm = 0.5 * H / image_size_mm
	rad_2mm = 1.0 * H / image_size_mm
	rad_3mm = 1.5 * H / image_size_mm

	if getattr(canvas, "FAZ_ctr", None) is None:
		canvas.FAZ_ctr = np.array([H // 2, W // 2])
	cy, cx = canvas.FAZ_ctr

	# Create circular ROI masks
	foveal_mask = np.zeros((H, W), dtype=bool)
	rr, cc = disk((cy, cx), rad_1mm, shape=(H, W))
	foveal_mask[rr, cc] = True

	pf500_outer = np.zeros((H, W), dtype=bool)
	rr, cc = disk((cy, cx), rad_2mm, shape=(H, W))
	pf500_outer[rr, cc] = True
	pf500_mask = pf500_outer & (~foveal_mask)

	pfouter_outer = np.zeros((H, W), dtype=bool)
	rr, cc = disk((cy, cx), rad_3mm, shape=(H, W))
	pfouter_outer[rr, cc] = True
	pfouter_mask = pfouter_outer & (~pf500_outer)

	# Binary regions
	binaryReg = [None] * 3

	#Crops each region to a tight square around the FAZ (± 3 mm) to reduce image size and speed later analysis 
	y1 = int(round(max(cy - rad_3mm, 0)))
	y2 = int(round(min(cy + rad_3mm, H)))
	x1 = int(round(max(cx - rad_3mm, 0))) 
	x2 = int(round(min(cx + rad_3mm, W)))

	binaryReg[0] = (binary * foveal_mask)[y1:y2, x1:x2]
	binaryReg[1] = (binary * pf500_mask)[y1:y2, x1:x2]
	binaryReg[2] = binary * pfouter_mask

	# Image regions
	imgReg = [None] * 3

	imgReg[0] = (original * foveal_mask)[y1:y2, x1:x2]
	imgReg[1] = (original * pf500_mask)[y1:y2, x1:x2]
	imgReg[2] = original * pfouter_mask

	# Region labels
	canvas.RAlabels = [
			"FAZ circle",
			"Inner 0.5mm ring around FAZ",
			"Outer 0.5mm ring",
	]

	# Area (pixel counts)
	imgArea_pix_vec = [
			np.sum(foveal_mask),
			np.sum(pf500_mask),
			np.sum(pfouter_mask),
	]

	run_analysis_on_regions(
		canvas,
		binaryReg=binaryReg,
		imgReg=imgReg,
		imgArea_pix_vec=imgArea_pix_vec,
		pix_to_mm=pix_to_mm,
		grid_type=GridType.FOVEAL_RING,
	)


def run_analysis_on_regions(
		canvas,
		binaryReg,
		imgReg,
		imgArea_pix_vec,
		pix_to_mm,
		grid_type,
):
		"""Perform skeletonization and metric extraction for each region.

		Args:
			canvas: Tk canvas-like object holding graph state, labels, and
				output paths.
			binaryReg: List of binary vessel masks, one per region.
			imgReg: List of grayscale image crops, one per region.
			imgArea_pix_vec: Region areas in pixels for non-square grids.
			pix_to_mm: Physical scale conversion from pixels to millimeters.
			grid_type: ``GridType`` enum describing the regional layout.

		Returns:
			pandas.DataFrame: Table of per-region vascular metrics.
		"""
		canvas.regional_metrics = [{} for _ in range(len(binaryReg))]

		# Create validation folder
		validation_folder = os.path.join(canvas.current_save_folder, 		"regional_validation")
		os.makedirs(validation_folder, exist_ok=True)

		for i in range(len(binaryReg)):

				# Skeletonize this region
				skeletonise(
						canvas,
						imgReg[i],
						binaryReg[i],
						display=False,
						notify=False,
				)
				
				change_status_to_waiting(canvas, status="● Regional analysis...")

				region_name = re.sub(r'\s+', '_', str(canvas.RAlabels[i]).strip("_"))
				file_prefix = f"{canvas.FileLabelName}_{grid_type.value}_R{i+1:02d}_{region_name}"

				cv2.imwrite(
					os.path.join(validation_folder, f"{file_prefix}_img.png"),
					imgReg[i].astype(np.uint8),
				)

				cv2.imwrite(
						os.path.join(validation_folder, f"{file_prefix}_binary.png"),
						binaryReg[i].astype(np.uint8),
				)

				cv2.imwrite(
						os.path.join(validation_folder, f"{file_prefix}_skel.png"),
						(canvas.skeleton_image.astype(np.uint8) * 255),
				)

				np.savez(
						os.path.join(validation_folder, f"{file_prefix}_data.npz"),
						imgRegion=imgReg[i],
						binaryRegion=binaryReg[i],
						skelRegion=(canvas.skeleton_image.astype(np.uint8) * 255),
				)

				# Image area
				if grid_type != GridType.SQUARE_GRID:
						imgArea_pix = imgArea_pix_vec[i]
						imgArea_mm = imgArea_pix * (pix_to_mm ** 2)
				else:
						regionsize = np.floor(np.array(canvas.fullImSizePix) / 3).astype(int)
						h, w = regionsize
						imgArea_pix = h * w
						imgArea_mm = imgArea_pix * (pix_to_mm**2)

				canvas.regional_metrics[i]["Region"] = canvas.RAlabels[i]

				# If skeleton graph exists
				links = getattr(canvas, "skeleton_links", None)
				nodes = getattr(canvas, "skeleton_nodes", None)

				if links is not None and len(links) > 0:
						# sum(~[app.Gnodes.ep])
						canvas.regional_metrics[i]["nodes"] = count_branchpoints(nodes)

						# sum(sum(binaryReg{i})) / 255 / imgArea_pix
						vessel_pixels = np.sum(binaryReg[i]) / 255.0
						canvas.regional_metrics[i]["VAD"] = round(vessel_pixels / imgArea_pix, 4) * 100

						# Vessel length density
						total_length_mm = compute_length(links, binaryReg[i], pix_to_mm)
						canvas.regional_metrics[i]["totalLength"] = round(total_length_mm, 2)

						# VLD %
						canvas.regional_metrics[i]["VLD_pct"] = round(
								(total_length_mm * pix_to_mm) / imgArea_mm, 4
						) * 100 #? is that a bug in the original code? (pix_to_mm should not be there?)

						# VLD 1/mm
						canvas.regional_metrics[i]["VLD_mminv"] = round(
								total_length_mm / imgArea_mm, 4
						)

						# Mean / Median length (µm)
						links_length_pix = [l.pixLength for l in links if l.pixLength is not None]
						canvas.regional_metrics[i]["MeanLength"] = round(np.mean(links_length_pix)*pix_to_mm*1000)
						canvas.regional_metrics[i]["MedianLength"] = round(np.median(links_length_pix)*pix_to_mm*1000)

						# Mean / Median diameter (µm)
						mean_diam_um, median_diam_um = compute_diameter(links, binaryReg[i], pix_to_mm)
						canvas.regional_metrics[i]["MeanDiam"] = round(mean_diam_um)
						canvas.regional_metrics[i]["MedianDiam"] = round(median_diam_um)

						# Branch density
						canvas.regional_metrics[i]["BD"] = round(
								canvas.regional_metrics[i]["nodes"] / canvas.regional_metrics[i]["totalLength"], 2
						)

						# fractalDimension(app)
						slope = compute_fractal_dimension(canvas)
						canvas.regional_metrics[i]["FD"] = round(slope, 4)

						# mean tortuosity
						canvas.regional_metrics[i]["mTort"] = compute_mean_tortuosity(links, binaryReg[i])

				# If no skeleton graph
				else:
						canvas.regional_metrics[i]["nodes"] = 0
						vessel_pixels = np.sum(binaryReg[i]) / 255.0
						canvas.regional_metrics[i]["VAD"] = round(vessel_pixels / imgArea_pix, 4) * 100
						canvas.regional_metrics[i]["totalLength"] = 0
						canvas.regional_metrics[i]["VLD_pct"] = 0
						canvas.regional_metrics[i]["VLD_mminv"] = 0
						canvas.regional_metrics[i]["MeanLength"] = 0
						canvas.regional_metrics[i]["MedianLength"] = 0
						canvas.regional_metrics[i]["MeanDiam"] = 0
						canvas.regional_metrics[i]["MedianDiam"] = 0
						canvas.regional_metrics[i]["BD"] = 0
						slope = compute_fractal_dimension(canvas)
						canvas.regional_metrics[i]["FD"] = round(slope, 4)
						canvas.regional_metrics[i]["mTort"] = 0

				new_tort_metrics = BiomarkerAnalyzer.new_tortuosity_metrics(
						links=canvas.skeleton_links,
						binary_image=binaryReg[i],
						image_size_var=canvas.image_size_var,
						fullImSizePix=canvas.fullImSizePix,
				)
				canvas.regional_metrics[i].update(
						normalize_regional_tortuosity_metrics(new_tort_metrics)
				)

		# Save Excel to local
		df = pd.DataFrame(canvas.regional_metrics)
		sheet_name = f"Regional analysis_{grid_type.value}"
		sheet_name = re.sub(r'[:\\/?*\[\]]', '_', sheet_name)[:31]
		write_excel(df, canvas.lastMetricsPath, sheet_name)

		return df


def normalize_regional_tortuosity_metrics(metrics):
		"""Convert undefined regional tortuosity outputs into stable numeric values."""
		normalized = {}

		for key in ("PWAOC_mean", "PWAOC_std", "SOAM_mean", "SOAM_std"):
				value = metrics.get(key, np.nan)
				normalized[key] = float(value) if np.isfinite(value) else 0.0

		return normalized


def compute_length(links, binary, pix_to_mm):
	"""Compute the total vessel-link length for a region.

	Args:
		links: List of vessel link objects with ``path`` attributes.
		binary: Binary vessel mask whose shape defines index decoding.
		pix_to_mm: Physical scale conversion from pixels to millimeters.

	Returns:
		float: Total vessel length in millimeters.
	"""
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

	total_length_mm = total_length_pix * pix_to_mm
	return total_length_mm


def compute_diameter(links, binary, pix_to_mm):
	"""Compute mean and median vessel diameter for a region.

	Args:
		links: List of vessel link objects with ``path`` attributes.
		binary: Binary vessel mask used to build a distance transform.
		pix_to_mm: Physical scale conversion from pixels to millimeters.

	Returns:
		tuple[float, float]: Mean and median diameters in micrometers.
	"""
	radius_map = distance_transform_edt(binary > 0)
	diameter_map = radius_map * 2

	all_sampled_diameters = []
	img_shape = binary.shape

	for link in links:
			indices = np.asarray(link.path, dtype=int)
			if indices.size == 0:
					continue

			rows, cols = np.unravel_index(indices, img_shape)
			vals = diameter_map[rows, cols]
			all_sampled_diameters.extend(vals)

	total_points = len(all_sampled_diameters)

	if total_points > 0:
			mean_diameter_pix = np.mean(all_sampled_diameters)
			mean_diameter_mm = mean_diameter_pix * pix_to_mm #pix_size_mm -> pix_to_mm
			mean_diameter_um = mean_diameter_mm * 1000.0
			median_diameter_pix = np.median(all_sampled_diameters)
			median_diameter_mm = median_diameter_pix*pix_to_mm
			median_diameter_um = median_diameter_mm * 1000.0
	else:
			mean_diameter_um = 0.0
			median_diameter_um = 0.0

	return mean_diameter_um, median_diameter_um


def count_branchpoints(nodes):
	"""Count branchpoints in a skeleton graph.

	Args:
		nodes: Iterable of node objects with an ``ep`` endpoint flag.

	Returns:
		int: Number of non-endpoint nodes.
	"""
	branchpoint_count = 0
	if nodes is not None:
			for node in nodes:
					if node.ep == 0:
							branchpoint_count += 1
	return branchpoint_count


def compute_branch_point_density(branchpoint_count, total_length_mm):
	"""Compute branchpoint density in units of 1/mm.

	Args:
		branchpoint_count: Number of branchpoints in the region.
		total_length_mm: Total vessel length in millimeters.

	Returns:
		float: Branchpoint density in inverse millimeters.
	"""
	if total_length_mm > 0.0:
			branchpoint_density = branchpoint_count / total_length_mm
	else:
			branchpoint_density = 0.0
	return branchpoint_density


def compute_fractal_dimension(canvas):
		"""Estimate fractal dimension from the current skeleton image.

		Args:
			canvas: Tk canvas-like object with ``skeleton_image`` populated.

		Returns:
			float: Box-counting fractal dimension estimate.
		"""
		img = canvas.skeleton_image.astype(bool)

		h, w = img.shape
		Nx = max(h, w)
		if Nx < 2:
				return 0.0

		numIterations = int(math.ceil(math.log(Nx, 2)))  # ceil(log2(Nx))
		width = 2 ** numIterations

		Z = np.zeros((width, width), dtype=bool)
		Z[:h, :w] = img

		# MATLAB: n_r(numIterations+1) = sum(sum(img));
		n_r = [int(Z.sum())]

		current = Z
		for _ in range(numIterations):
				rows, cols = current.shape
				if rows < 2 or cols < 2:
						break
				# MATLAB's effect is repeated 2×2 OR pooling
				current = current.reshape(rows // 2, 2, cols // 2, 2).max(axis=(1, 3))
				n_r.append(int(current.sum()))

		# MATLAB does: n_r = n_r(end:-1:1); r = 2.^(0:numIterations);
		# But their final polyfit uses matching r with n_r ordered from r=1,2,4,...
		r = 2 ** np.arange(len(n_r), dtype=float)          # [1,2,4,...]
		n_r = np.array(n_r, dtype=float)

		# MATLAB: P = polyfit(log(r), -log(n_r), 1); slope = P(1);
		P = np.polyfit(np.log(r), -np.log(n_r), 1)
		return float(P[0])


def compute_mean_tortuosity(links, binary):
	"""Compute mean arc-over-chord tortuosity across vessel links.

	Args:
		links: List of vessel link objects with ``path`` attributes.
		binary: Binary vessel mask whose shape defines index decoding.

	Returns:
		float: Mean tortuosity across valid links.
	"""
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
			mean_tortuosity = round(np.mean(tortuosity_list),4)
	else:
			mean_tortuosity = 0.0
	return mean_tortuosity
