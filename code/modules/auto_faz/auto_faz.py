import cv2
import os

from .util_image import *
from .faz import process_image
from .context import Context
from .config import config
from scipy.interpolate import make_splprep

def load_config():
    """
    Load config file
    """
    # This won't work when bundled to single file executable with no access to config.yml
    # module_dir = os.path.dirname(os.path.abspath(__file__))
    # path = os.path.join(module_dir, 'config.yml')
    
    # with open(path, 'r') as f:
    #     return yaml.safe_load(f)
    return config

def load_dataset_file(filepath, crop_bottom):
    """
    Load image for processing the single image defined in config file
    """
    img_path = filepath
    print(f"Loading image: {img_path}")
    if not os.path.isfile(img_path):
        print(f"Image does not exist: {img_path}")
        return
    return load_image(img_path, crop_bottom)

def load_batch(ctx):
    """
    Load a batch of images and GT masks from image_folder and gt_folder
    Returns an array of paired image and gt mask
    Hardcoded that GT masks must be named: <filename_from_image_folder>_FAZ_mask_0.png

    Accepts file types: png, jpg, jpeg, tif, tiff
    """
    image_folder = ctx.config['dataset']['image_folder']
    crop_bottom_px = ctx.config['dataset']['crop_bottom']

    image_folder = os.path.join(image_folder)

    pairs = []
    allowed_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff'}
    # Collect only valid images
    image_files = sorted([
        f for f in os.listdir(image_folder)
        if os.path.splitext(f)[1].lower() in allowed_extensions
    ])

    for img_file in image_files:
        base_id = os.path.splitext(img_file)[0]  # e.g. "foo" from "foo.tif"

        img_path = os.path.join(image_folder, img_file)

        img = load_image(img_path, crop_bottom_px)

        if img is None:
            print(f"Failed to load {img_file}")
            continue

        pairs.append((img, base_id))

    return pairs

def process_batch(pairs, ctx):
    """
    Takes pairs of images to segment and their FAZ mask and
    runs a batch job of images to segment
    Saves the metric results in filepath `batch_out_csv`
    Saves the summary metric results to filepath `batch_summary_txt`
    """
    if len(pairs) == 0:
        return
    out_dir = os.path.join("batch")
    try:
        os.makedirs(out_dir, exist_ok=False) 
    except:
        exit("A batch output with that job name already exists.")

    for idx, (img, image_id) in enumerate(pairs):
        new_ctx = Context(ctx.config, None, filename=image_id, steps=ctx.steps, candidate=ctx.candidate, batch=True)
        pred = process_image(img, new_ctx)

        # save results
        cv2.imwrite(os.path.join(out_dir, f"{image_id}_pred.png"), pred)

# Auto segment FAZ and save results
# @param {Np.array} image - image for single segmentation
def auto_faz(image=None):
    """
    FAZ segmentation tool
    Read image from memory and automatically segment FAZ
    """
    global config, original_img, display_hist, canny_test

    config = load_config()

    # Load parameters
    print(config.items())

    img = image.astype(np.uint8) # Downcase to uint8 to enable processings like CLAHE
    original_img = img.copy()

    ctx = Context(config)

    # return raw binary array
    binary_mask = process_image(img, ctx)

    # save mask
    if binary_mask is not None:

        contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

        # Teh-Chin approximation
        contours_CHAIN_APPROX_TC89_L1, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_TC89_L1)
        contours_CHAIN_APPROX_TC89_KCOS, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_TC89_KCOS)

        # Contours to single contour
        contour = max(contours, key=cv2.contourArea).reshape(-1, 2)
        # Reduced to every i-th points
        contour_reduced_5 = np.ascontiguousarray(contour[::5])   # Reduce to keep only every 5th contour points
        contour_reduced_10 = np.ascontiguousarray(contour[::10]) # Reduce to keep only every 10th contour points
        contour_reduced_20 = np.ascontiguousarray(contour[::20]) # Reduce to keep only every 20th contour points

        contour_CHAIN_APPROX_TC89_L1 = max(contours_CHAIN_APPROX_TC89_L1, key=cv2.contourArea).reshape(-1, 2)
        contour_CHAIN_APPROX_TC89_KCOS = max(contours_CHAIN_APPROX_TC89_KCOS, key=cv2.contourArea).reshape(-1, 2)

        # Douglas–Peucker approximation (epilon = how much set off can new curve be from original structure, closed = If start is connected with trail)
        contour_CHAIN_APPROX_DP_0001 = cv2.approxPolyDP(contour, 0.001 * cv2.arcLength(contour, True), closed=True)
        contour_CHAIN_APPROX_DP_0005 = cv2.approxPolyDP(contour, 0.005 * cv2.arcLength(contour, True), closed=True)
        contour_CHAIN_APPROX_DP_001 = cv2.approxPolyDP(contour, 0.01 * cv2.arcLength(contour, True), closed=True)

        # B-spline smoothing
        x, y = contour[:, 0].astype(float), contour[:, 1].astype(float)
        result_s_len = make_splprep([x, y], s=len(contour))
        result_s_len_half = make_splprep([x, y], s=int(len(contour)/2))
        result_s_len_quarter = make_splprep([x, y], s=int(len(contour)/4))

        # This returns a bspline() instance where spl(x) = y
        bspline_s_len = result_s_len[0]
        bspline_s_len_half = result_s_len_half[0]
        bspline_s_len_quarter = result_s_len_quarter[0]

        # Get coords that are mapped to a normalised 0-1 range, do not space the points otherwise will look like a continuous vertical sheets instead of polygon
        u_new_s_len = np.linspace(0, 1, len(contour))
        u_new_s_len_half = np.linspace(0, 1, int(len(contour)/2))
        u_new_s_len_quarter = np.linspace(0, 1, int(len(contour)/4))
        smoothed_points_s_len = bspline_s_len(u_new_s_len)
        smoothed_points_s_len_half = bspline_s_len_half(u_new_s_len_half)
        smoothed_points_s_len_quarter = bspline_s_len_quarter(u_new_s_len_quarter)
        contour_B_SPLINE_FULL = np.round(smoothed_points_s_len.T).astype(np.int32) # Tranpose from Numpy's [y,x] to cv2's [x,y]
        contour_B_SPLINE_HALF = np.round(smoothed_points_s_len_half.T).astype(np.int32) # Tranpose from Numpy's [y,x] to cv2's [x,y]
        contour_B_SPLINE_QUARTER = np.round(smoothed_points_s_len_quarter.T).astype(np.int32) # Tranpose from Numpy's [y,x] to cv2's [x,y]


        # 2-d array to polygon
        inner_mask = np.zeros_like(binary_mask)
        image_original = cv2.fillPoly(inner_mask.copy(), [contour], 255)
        image_reduced_5 = cv2.fillPoly(inner_mask.copy(), [contour_reduced_5], 255)
        image_reduced_10 = cv2.fillPoly(inner_mask.copy(), [contour_reduced_10], 255)
        image_reduced_20 = cv2.fillPoly(inner_mask.copy(), [contour_reduced_20], 255)
        image_CHAIN_APPROX_TC89_L1 = cv2.fillPoly(inner_mask.copy(), [contour_CHAIN_APPROX_TC89_L1], 255)
        image_CHAIN_APPROX_TC89_KCOS = cv2.fillPoly(inner_mask.copy(), [contour_CHAIN_APPROX_TC89_KCOS], 255)
        image_CHAIN_APPROX_DP_0001 = cv2.fillPoly(inner_mask.copy(), [contour_CHAIN_APPROX_DP_0001], 255)
        image_CHAIN_APPROX_DP_0005 = cv2.fillPoly(inner_mask.copy(), [contour_CHAIN_APPROX_DP_0005], 255)
        image_CHAIN_APPROX_DP_001 = cv2.fillPoly(inner_mask.copy(), [contour_CHAIN_APPROX_DP_001], 255)
        image_B_SPLINE_FULL = cv2.fillPoly(inner_mask.copy(), [contour_B_SPLINE_FULL], 255)
        image_B_SPLINE_HALF = cv2.fillPoly(inner_mask.copy(), [contour_B_SPLINE_HALF], 255)
        image_B_SPLINE_QUARTER = cv2.fillPoly(inner_mask.copy(), [contour_B_SPLINE_QUARTER], 255)

        # Gaussian smoothing
        image_blurred_5 = cv2.GaussianBlur(image_original.copy(), (5, 5), 0)
        image_blurred_11 = cv2.GaussianBlur(image_original.copy(), (11, 11), 0)
        image_blurred_21 = cv2.GaussianBlur(image_original.copy(), (21, 21), 0)
        _, image_SMOOTH_GAUSSIAN_5 = cv2.threshold(image_blurred_5, 127, 255, cv2.THRESH_BINARY)
        _, image_SMOOTH_GAUSSIAN_11 = cv2.threshold(image_blurred_11, 127, 255, cv2.THRESH_BINARY)
        _, image_SMOOTH_GAUSSIAN_21 = cv2.threshold(image_blurred_21, 127, 255, cv2.THRESH_BINARY)

        cv2.imwrite("mask_original.png", binary_mask)
        cv2.imwrite("mask_reduced_5.png", image_reduced_5)
        cv2.imwrite("mask_reduced_10.png", image_reduced_10)
        cv2.imwrite("mask_reduced_20.png", image_reduced_20)
        cv2.imwrite("mask_CHAIN_APPROX_TC89_L1.png", image_CHAIN_APPROX_TC89_L1)
        cv2.imwrite("mask_CHAIN_APPROX_TC89_KCOS.png", image_CHAIN_APPROX_TC89_KCOS)
        cv2.imwrite("mask_CHAIN_APPROX_DP_0001.png", image_CHAIN_APPROX_DP_0001)
        cv2.imwrite("mask_CHAIN_APPROX_DP_0005.png", image_CHAIN_APPROX_DP_0005)
        cv2.imwrite("mask_CHAIN_APPROX_DP_001.png", image_CHAIN_APPROX_DP_001)
        cv2.imwrite("mask_SMOOTH_GAUSSIAN_5.png", image_SMOOTH_GAUSSIAN_5)
        cv2.imwrite("mask_SMOOTH_GAUSSIAN_11.png", image_SMOOTH_GAUSSIAN_11)
        cv2.imwrite("mask_SMOOTH_GAUSSIAN_21.png", image_SMOOTH_GAUSSIAN_21)
        cv2.imwrite("mask_B_SPLINE_FULL.png", image_B_SPLINE_FULL)
        cv2.imwrite("mask_B_SPLINE_HALF.png", image_B_SPLINE_HALF)
        cv2.imwrite("mask_B_SPLINE_QUARTER.png", image_B_SPLINE_QUARTER)

        print("Saved masks to disk")