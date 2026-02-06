import numpy as np
from skimage.morphology import skeletonize, remove_small_objects
from scipy.ndimage import distance_transform_edt
from modules.change_status import change_status_to_waiting
from modules.Skel2Graph3D import skel2graph3d
from modules.Graph2Skel3D import graph2skel3d
from modules.resize_image import *
import scipy.io as sio
import time
from skimage.morphology import medial_axis
from PIL import Image, ImageTk
from tkinter import Canvas
import io
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg") 
from scipy.ndimage import binary_dilation
import os

def skeletonise(canvas: Canvas, raw_img: np.ndarray, bin_img: np.ndarray, display: bool = True):
  change_status_to_waiting(canvas, status="🔴 Wait...Skeletonising")

  twig_size = canvas.twig_size.get()

  # generate skeletonized iamge
  y, x = bin_img.shape
  L = bin_img.astype(bool)
  # sk2 = skeletonize(L) 
  sk2, distance = medial_axis(L, return_distance=True)

  # removes branches smaller than twig size
  sk2 = remove_small_objects(sk2, twig_size, connectivity=2) 


  # local thickness measurement
  D = distance_transform_edt(L) * 2
  # D is the closest I can get to the local thickness map so far, so
  # saving as such. Factor of 2 since distance transform gives radius

  # network analysis
  # based on code written by Philip Kollmannsberger
  if np.sum(sk2) == 0:
      nodes = []
      links = []

  else:
      start_skel2graph = time.time()
      nodes, links = skel2graph3d(sk2, twig_size)
      end_skel2graph = time.time()
  
  print("Time for skel2graph:", end_skel2graph - start_skel2graph)

  # calculate total length of network
  wl = sum([len(n.links) for n in nodes])

  # iterate to clean up network and get rid of excess nodes
  start_graph2skel = time.time()
  skel2 = graph2skel3d(nodes, links, y, x, 1)  
  end_graph2skel = time.time()

  nodes, links = skel2graph3d(skel2, 0) # passing 304x304x1
  wl_new = sum([len(n.links) for n in nodes])

  print("Time for graph2skel:", end_graph2skel - start_graph2skel)

  # iterate the same steps until network length changed by less than 0.5%
  start_loop = time.time()
  while (wl_new != wl):
    wl = wl_new

    skel2 = graph2skel3d(nodes, links, y, x, 1)
    nodes, links = skel2graph3d(skel2, 0)

    wl_new = sum([len(n.links) for n in nodes])

  end_loop = time.time()

  print("Time in cleaning loop:", end_loop - start_loop)

  #save to canvas
  canvas.skeleton_image = skel2[:, :, 0]
  canvas.skeleton_nodes = nodes
  canvas.skeleton_links = links

  # --- Convert binary skeleton to 0–255 grayscale like matplotlib ---
  # skel_uint8 = (canvas.skeleton_image.astype(np.uint8)) * 255
  if display:
    skel_uint8 = binary_dilation(canvas.skeleton_image, iterations=1).astype(np.uint8) * 255
    # --- Create PIL image ---
    skel_pil = Image.fromarray(skel_uint8, mode="L")

    # Save skeleton image to current save folder
    skel = canvas.skeleton_image
    fig, ax = plt.subplots(figsize=(3,3), dpi=300)
    ax.imshow(skel, cmap='gray')
    ax.axis('off')
    img_path = os.path.join(canvas.current_save_folder, "images", f"{canvas.FileLabelName}_Skeletonised_TwigSize{twig_size}.png")
    plt.savefig(img_path, bbox_inches='tight', pad_inches=0)

    # --- Resize and convert to ImageTk for display on canvas ---
    resized_img = resize_image(skel_pil)     # if resize is needed
    img_tk = ImageTk.PhotoImage(resized_img)   # convert to Tk-compatible image
    canvas.skeleton_img_id = canvas.create_image(1060, 255, image=img_tk)
    canvas._image_refs["skeleton_img"] = img_tk

  return skel2, nodes, links


