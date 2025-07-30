from skimage.io import imread, imshow
from backend_ROI import ROIProcessor
import matplotlib.pyplot as plt


img_path = "./assets/MIPs/10301.bmp" 
img_np = imread(img_path) # 304x304 px

# example using a rectangular ROI
# roi = {
#     'x': 100,
#     'y': 50,
#     'width': 150,
#     'height': 150
# }

# example using a round ROI
roi = {
    'cx': 304//2,
    'cy': 304//2,
    'r': 100
}

# cropping a rectangle out of the original image
roi_proc = ROIProcessor(img_np, 'round', circle=roi)
roi_result = roi_proc.crop_roi(resize=True)
img_result = roi_result['cropped_image']

# plotting images side by side
fig, ax = plt.subplots(1, 2, figsize=(10, 10))
ax[0].imshow(img_np, cmap='gray')
ax[0].set_title("Original")
ax[1].imshow(img_result, cmap='gray')
ax[1].set_title("Cropped ROI")
plt.tight_layout()
plt.show()