import cv2
import numpy as np
import matplotlib.pyplot as plt
import yaml
import os
import argparse
import csv
import sys

from util_image import *
from metrics import mask_metrics
from faz import process_image
from display import Display
from context import Context


def load_config(path='config.yml'):
    """
    Load config file
    """
    with open(path, 'r') as f:
        return yaml.safe_load(f)


def load_dataset_file(filepath, crop_bottom):
    """
    Load image for processing the single image defined in config file
    """
    data_root = './datasets'
    img_path = os.path.join(data_root, filepath)

    if not os.path.isfile(img_path):
        print(f"Image does not exist: {img_path}")
        return
    return load_image(img_path, crop_bottom)


def sanity_check(gt, pr):
    """
    Quickly check GT and predicted FAZ mask are the same size
    Show FAZ overlay comparison
    """
    print(f"GT shape:{gt.shape}, data type:{gt.dtype}, unique values:{np.unique(gt)}")
    print(f"PR shape:{pr.shape}, data type:{pr.dtype}, unique values:{np.unique(pr)}")

    if pr.shape != gt.shape:
        pr = cv2.resize(pr, (gt.shape[1], gt.shape[0]), interpolation=cv2.INTER_NEAREST)
        print("Resized PR ->", pr.shape)

    # areas (in pixels)
    gt_area = (gt>0).sum()
    pr_area = (pr>0).sum()
    print(f"GT area:{gt_area}, PR area:{pr_area}")

    plt.figure(figsize=(9,3))
    plt.subplot(1,3,1); plt.imshow(gt, cmap='gray'); plt.title("GT"); plt.axis('off')
    plt.subplot(1,3,2); plt.imshow(pr, cmap='gray'); plt.title("Pred"); plt.axis('off')
    plt.subplot(1,3,3); 
    plt.imshow(gt, cmap='gray'); 
    plt.imshow(pr, cmap='jet', alpha=0.4); 
    plt.title("Overlay"); plt.axis('off')
    plt.tight_layout(); plt.show()

    return gt, pr


def _summ(vals):
    """
    Return mean, sd, median of vals
    """
    vals = np.asarray(vals, dtype=float)
    vals = vals[np.isfinite(vals)]  # drop NaN and inf

    mean = float(vals.mean()) if vals.size else 0.0
    sd   = float(vals.std(ddof=1)) if vals.size > 1 else 0.0
    med  = float(np.median(vals)) if vals.size else 0.0
    return mean, sd, med


def load_batch(ctx):
    """
    Load a batch of images and GT masks from image_folder and gt_folder
    Returns an array of paired image and gt mask
    Hardcoded that GT masks must be named: <filename_from_image_folder>_FAZ_mask_0.png

    Accepts file types: png, jpg, jpeg, tif, tiff
    """
    image_folder = ctx.config['dataset']['image_folder']
    gt_folder = ctx.config['dataset']['gt_folder']
    gt_suffix = ctx.config['dataset']['gt_suffix']
    crop_bottom_px = ctx.config['dataset']['crop_bottom']

    data_root = './datasets'
    image_folder = os.path.join(data_root, image_folder)
    gt_folder = os.path.join(data_root, gt_folder)

    pairs = []
    allowed_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff'}
    # Collect only valid images
    image_files = sorted([
        f for f in os.listdir(image_folder)
        if os.path.splitext(f)[1].lower() in allowed_extensions
    ])

    for img_file in image_files:
        base_id = os.path.splitext(img_file)[0]  # e.g. "foo" from "foo.tif"
        mask_file = base_id + gt_suffix

        img_path = os.path.join(image_folder, img_file)
        mask_path = os.path.join(gt_folder, mask_file)

        if not os.path.exists(mask_path):
            print(f"No GT mask for {img_file}, expected {mask_file}")
            continue

        img = load_image(img_path, crop_bottom_px)
        gt_mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)

        if img is None or gt_mask is None:
            print(f"Failed to load {img_file} or {mask_file}")
            continue

        pairs.append((img, gt_mask, base_id))

    return pairs


def process_batch(pairs, job_name, ctx):
    """
    Takes pairs of images to segment and their FAZ mask and
    runs a batch job of images to segment
    Saves the metric results in filepath `batch_out_csv`
    Saves the summary metric results to filepath `batch_summary_txt`
    """
    if len(pairs) == 0:
        return
    out_dir = os.path.join("batch", job_name)
    try:
        os.makedirs(out_dir, exist_ok=False) 
    except:
        exit("A batch output with that job name already exists.")
    csv_path = os.path.join(out_dir, "out.csv")
    summary_path = os.path.join(out_dir, "summary.txt")

    rows = []
    skipped = 0
    for idx, (img, gt, image_id) in enumerate(pairs):
        display = Display(img)
        new_ctx = Context(ctx.config, display, filename=image_id, steps=False, candidate=False)
        pred = process_image(img, new_ctx)
        pred_resized = cv2.resize(pred, (gt.shape[1], gt.shape[0]),
                        interpolation=cv2.INTER_NEAREST)
        # ensure masks are uint8 binary (0/255)
        gt_bin   = (gt > 0).astype(np.uint8) * 255
        pred_bin = (pred_resized > 0).astype(np.uint8) * 255

        m = mask_metrics(gt_bin, pred_bin, new_ctx)

        if np.isnan(m["area_difference_pct"]):
            skipped += 1

        # attach ID to rows
        m["image_id"] = image_id
        rows.append(m)

    # dp precision for outputs
    precision_map = {
    "dice": 4, "iou": 4, "precision": 4, "recall": 4,
    "acircularity": 4, "circularity": 4,
    "area": 1, "perimeter": 1,
}

    # write output to `batch/job_name/out.csv`
    fieldnames = ["image_id"] + [k for k in rows[0].keys() if k != "image_id"]
    with open(csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") 
            for k in fieldnames})

    # write output to `batch/job_name/summary.txt`
    summary_lines = ["=== Summary (mean ± sd) [median] ===\n"]
    
    print(summary_lines[0], end="")
    for k in fieldnames:
        if k == "image_id":
            continue
        vals = [row[k] for row in rows]
        mean, sd, med = _summ(vals)
        prec = next((v for key, v in precision_map.items() if key in k.lower()), 3)
        line = f"{k:28s}: {mean:.{prec}f} ± {sd:.{prec}f}  [{med:.{prec}f}]"
        print(line)
        summary_lines.append(line + '\n')

    with open(summary_path, "w") as f:
        f.writelines(summary_lines)
        f.writelines(f"\nImages with failed segmentation: {skipped} / {len(rows)}")

    print(f"\nImages with failed segmentation: {skipped} / {len(rows)}")

def main():
    """
    FAZ segmentation tool

    Use --help to view argument details

    Running the script without --batch arg segments a single image, this requires values for
    `filepath`, `gt_filepath`, `crop_bottom` in the config file.

    Running in batch mode requires the config values `image_folder`, `gt_folder`, and `crop_bottom`
    """
    global config, original_img, display_hist, canny_test

    config = load_config()

    parser = argparse.ArgumentParser(description="FAZ segmentation tool")
    parser.add_argument(
        "--batch",
        help="run the tool in batch mode, requires the job name to be specified with --output arg",
        action='store_true')
    parser.add_argument(
        "--output",
        help="specify name of the batch job. E.g. --output [job_name] saves batch job output results to" \
        "`batch/[job_name]/out.csv`, summary results saves to `batch/[job_name]/summary.txt`",
        type=str)
    parser.add_argument(
        "--steps",
        help="display results of each step in the tool side by side with the input image, also enables " \
        "--candidate opt",
        action='store_true')
    parser.add_argument(
        "--candidate",
        help="show candidate FAZ considered during segmentation, enabled if 'steps' opt is also provided",
        action='store_true')
    args = parser.parse_args()


    if (args.batch):
        if (args.output):
            ctx = Context(config)
            pairs = load_batch(ctx)
            process_batch(pairs, args.output, ctx)
        else:
            sys.exit("Error: --output should be provided along with --batch")
    else:
        img = load_dataset_file(config['dataset']['filepath'], config['dataset']['crop_bottom'])
        original_img = img.copy()

        step_displayer = Display(original_img)
        ctx = Context(config, display=step_displayer, steps=args.steps, candidate=args.candidate)

        # expects FAZ mask to be binary with 0 background, 255 FAZ
        # if GT is not already binarised, can use/adapt `extract_faz_gt_mask` or batch version
        # to create binary masks
        gt_mask = extract_faz_gt_mask(config['dataset']['gt_filepath'])

        # process image
        processed_img = process_image(img, ctx)

        ctx.show(processed_img, final=True)

        if processed_img is not None:
            plt.imshow(gt_mask)
            plt.title('GT Mask')
            plt.show()
            sanity_check(gt_mask, processed_img)
            # ensure pred and gt mask the same size so metrics can be calculated
            processed_img = cv2.resize(processed_img, (gt_mask.shape[1], gt_mask.shape[0]), interpolation=cv2.INTER_NEAREST)
            print(mask_metrics(gt_mask, processed_img, ctx))

if __name__ == '__main__':
    main()
