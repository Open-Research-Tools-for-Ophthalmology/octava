import os
import cv2

from extract_GT.extract_fazid import extract_faz_gt_mask
from util_image import load_colour_gt_mask

gt_folder = '../datasets/FAZID/Diabetic/Marked'
folder_name = '../datasets/FAZID/Diabetic/FAZ_mask'

def batch_extract_gt(gt_folder, folder_name, crop_bottom=0):
    """
    Load a batch of GT images from a folder, extract GT (colored FAZ) masks
    and save to a folder
    GT masks are named 'Diabetic_marked (XX).jpg', this function extracts FAZ
    from coloured to binary image, saves file as 'Diabetic_clear (XX)_FAZ_mask_0.png'
    where XX is the image number from the original file.
    This is done as the pipeline expects FAZ mask file to match image filename + '_FAZ_mask_0.png' prefix
    e.g. <image_filename>_FAZ_mask_0.png
    """
    allowed_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff'}

    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    raw_images = sorted(os.listdir(gt_folder))
    for index, filename in enumerate(raw_images):
        ext = os.path.splitext(filename)[1].lower()
        if ext in allowed_extensions:
            img_path = os.path.join(gt_folder, filename)
            print(img_path)
            img = load_colour_gt_mask(img_path, crop_bottom)
            mask = extract_faz_gt_mask(img)
            if mask is not None:
                save_path = os.path.join(folder_name, f"{os.path.splitext(filename)[0].replace('marked', 'clear')}_FAZ_mask_0.png")
                cv2.imwrite(save_path, mask)
            else:
                print(f"Failed to load image {index}")

if __name__ == "__main__":
    batch_extract_gt(gt_folder, folder_name, crop_bottom=18)