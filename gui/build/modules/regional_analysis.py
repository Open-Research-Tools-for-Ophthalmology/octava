from tkinter import Canvas
import numpy as np
from skimage.draw import disk, polygon

RIGHT_EYE = "Right Eye"

def run_regional_analysis(canvas):
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
		apply_etdrs_grid(canvas, binary, original, image_size_mm)

	if canvas.extended_etdrs_grid_bool.get():
		apply_extended_etdrs_grid(canvas,binary, original, image_size_mm)

	if canvas.foveal_ring_bool.get():
		apply_foveal_ring(canvas,binary,original, image_size_mm)

	if canvas.optic_nerve_head_bool.get():
		apply_onh(canvas,binary, original, image_size_mm)


def apply_square_grid(canvas, binary, original, pix_to_mm):
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

	# -------- Area calculations --------
	imgArea_pix = h * w
	imgArea_mm = imgArea_pix * (pix_to_mm**2)

	# -------- Region labels --------
	set_square_grid_labels(canvas)


def apply_etdrs_grid(canvas, binary, original, image_size_mm):
	H, W = canvas.fullImSizePix
	rad_1mm = 0.5 * H / image_size_mm
	rad_3mm = 1.5 * H / image_size_mm

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
	binaryReg[0] = binaryReg[0][
		int(max(cy - rad_3mm, 0)):int(min(cy + rad_3mm, H)),
		int(max(cx - rad_3mm, 0)):int(min(cx + rad_3mm, W))
	] #Crops to a bounding box around FAZ (± rad_3mm)

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
	imgReg[0] = imgReg[0][
		int(max(cy - rad_3mm, 0)):int(min(cy + rad_3mm, H)),
		int(max(cx - rad_3mm, 0)):int(min(cx + rad_3mm, W))
	] #Crops to a bounding box around FAZ (± rad_3mm)

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
		np.sum(sector_masks[:, :, 1]) #? was that a typo in original code?
	]


def apply_extended_etdrs_grid(canvas, binary,original,image_size_mm):
	H, W = canvas.fullImSizePix
	rad_1mm = 0.5 * H / image_size_mm
	rad_3mm = 1.5 * H / image_size_mm

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

def apply_onh(canvas, binary, original,image_size_mm):
	H, W = canvas.fullImSizePix
	rad_1mm = 1 * H / image_size_mm
	rad_outer = 2.0 * H / image_size_mm #The outer ring may need to be 2.5, 3, or 4.25 - The user will need to input this 

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

	binaryReg[0] = binary * sector_masks[:, :, 0][:H//2, W//2:]
	binaryReg[1] = binary * sector_masks[:, :, 1][:H//2, W//2:]
	binaryReg[2] = binary * sector_masks[:, :, 2][:H//2, :W//2]
	binaryReg[3] = binary * sector_masks[:, :, 3][:H//2, :W//2]
	binaryReg[4] = binary * sector_masks[:, :, 4][H//2:, :W//2]
	binaryReg[5] = binary * sector_masks[:, :, 5][H//2:, :W//2]
	binaryReg[6] = binary * sector_masks[:, :, 6][H//2:, W//2:]
	binaryReg[7] = binary * sector_masks[:, :, 7][H//2:, W//2:]

	binaryReg[8]  = binary * (sector_masks[:, :, 0] | sector_masks[:, :, 1] |
														sector_masks[:, :, 2] | sector_masks[:, :, 3])[:H//2, :]
	binaryReg[9]  = binary * (sector_masks[:, :, 4] | sector_masks[:, :, 5] |
														sector_masks[:, :, 6] | sector_masks[:, :, 7])[H//2:, :]

	binaryReg[10] = binary * (sector_masks[:, :, 1] | sector_masks[:, :, 2])[:H//2, :]
	binaryReg[11] = binary * (sector_masks[:, :, 5] | sector_masks[:, :, 6])[H//2:, :]
	binaryReg[12] = binary * (sector_masks[:, :, 3] | sector_masks[:, :, 4])[:, :W//2]
	binaryReg[13] = binary * (sector_masks[:, :, 0] | sector_masks[:, :, 7])[:, W//2:]
	binaryReg[14] = binary * PP_mask

	# Image regions (same geometry as binaryReg)
	imgReg = [None] * 15

	imgReg[0] = original * sector_masks[:, :, 0][:H//2, W//2:]
	imgReg[1] = original * sector_masks[:, :, 1][:H//2, W//2:]
	imgReg[2] = original * sector_masks[:, :, 2][:H//2, :W//2]
	imgReg[3] = original * sector_masks[:, :, 3][:H//2, :W//2]
	imgReg[4] = original * sector_masks[:, :, 4][H//2:, :W//2]
	imgReg[5] = original * sector_masks[:, :, 5][H//2:, :W//2]
	imgReg[6] = original * sector_masks[:, :, 6][H//2:, W//2:]
	imgReg[7] = original * sector_masks[:, :, 7][H//2:, W//2:]

	imgReg[8]  = original * (sector_masks[:, :, 0] | sector_masks[:, :, 1] |
											sector_masks[:, :, 2] | sector_masks[:, :, 3])[:H//2, :]
	imgReg[9]  = original * (sector_masks[:, :, 4] | sector_masks[:, :, 5] |
											sector_masks[:, :, 6] | sector_masks[:, :, 7])[H//2:, :]

	imgReg[10] = original * (sector_masks[:, :, 1] | sector_masks[:, :, 2])[:H//2, :]
	imgReg[11] = original * (sector_masks[:, :, 5] | sector_masks[:, :, 6])[H//2:, :]
	imgReg[12] = original * (sector_masks[:, :, 3] | sector_masks[:, :, 4])[:, :W//2]
	imgReg[13] = original * (sector_masks[:, :, 0] | sector_masks[:, :, 7])[:, W//2:]
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

def apply_foveal_ring(canvas, binary, original, image_size_mm):


	pass


def set_square_grid_labels(canvas):
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
