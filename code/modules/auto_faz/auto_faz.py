import cv2
import os

from .util_image import *
from .faz import process_image
from .context import Context
from .config import config

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
        # cv2.imwrite("mask.png", processed_img)
        # print("Saved mask to mask.png")
        return binary_mask