import numpy as np
from skimage.morphology import remove_small_objects
from scipy.ndimage import distance_transform_edt
from modules.change_status import change_status_to_waiting
from modules.skel_Skel2Graph3D import skel2graph3d
from modules.skel_Graph2Skel3D import graph2skel3d
from modules.resize_image import *
import time
from skimage.morphology import medial_axis
from PIL import Image, ImageTk
from tkinter import Canvas
import matplotlib
matplotlib.use("Agg")
from scipy.ndimage import binary_dilation
import os
import cv2

def skeletonise(canvas: Canvas, raw_img: np.ndarray, bin_img: np.ndarray, display: bool = True, notify: bool=True):
  """Skeletonize a binary vessel mask, build its graph, and optionally render the result."""
  if notify:
    change_status_to_waiting(canvas, status="● Wait...Skeletonising")

  twig_size = canvas.twig_size.get()

  # generate skeletonized image
  y, x = bin_img.shape
  L = bin_img.astype(bool)
  sk2, distance = medial_axis(L, return_distance=True, rng=0)

  # removes branches smaller than twig size
  sk2 = remove_small_objects(sk2, twig_size, connectivity=2)

  # local thickness measurement
  D = distance_transform_edt(L) * 2

  # network analysis
  if np.sum(sk2) == 0:
      nodes = []
      links = []
      skel = sk2[:, :, None].astype(bool)  # keep shape consistent downstream
  else:
      start_skel2graph = time.time()
      nodes, links = skel2graph3d(sk2, twig_size)
      end_skel2graph = time.time()
      print("Time for skel2graph:", end_skel2graph - start_skel2graph)

      # calculate total length of network
      wl = sum([len(n.links) for n in nodes])

      # iterate to clean up network and get rid of excess nodes
      start_graph2skel = time.time()
      skel = graph2skel3d(nodes, links, y, x, 1)
      end_graph2skel = time.time()
      print("Time for graph2skel:", end_graph2skel - start_graph2skel)

      # one rebuild to get initial wl_new
      nodes, links = skel2graph3d(skel, 0)
      wl_new = sum([len(n.links) for n in nodes])

      # iterate until stable (throttle expensive skel2graph rebuild)
      start_loop = time.time()

      rebuild_every = 4   # only rebuild graph every N iterations
      max_iters = 30      # safety guard

      iter_i = 0
      prev_pixels = np.count_nonzero(skel)

      while (wl_new != wl) and (iter_i < max_iters):
        wl = wl_new
        iter_i += 1

        skel = graph2skel3d(nodes, links, y, x, 1)

        # cheap convergence check to avoid rebuilding graph too often
        curr_pixels = np.count_nonzero(skel)
        if curr_pixels == prev_pixels:
          break
        prev_pixels = curr_pixels

        # rebuild graph only occasionally
        if (iter_i % rebuild_every) == 0:
          nodes, links = skel2graph3d(skel, 0)
          wl_new = sum([len(n.links) for n in nodes])

      # final rebuild to keep nodes/links consistent with final skeleton
      nodes, links = skel2graph3d(skel, 0)
      wl_new = sum([len(n.links) for n in nodes])

      end_loop = time.time()
      print("Time in cleaning loop:", end_loop - start_loop)

  # save to canvas
  canvas.skeleton_image = skel[:, :, 0]
  canvas.skeleton_nodes = nodes
  canvas.skeleton_links = links

  if display:
    skel_uint8 = binary_dilation(canvas.skeleton_image, iterations=1).astype(np.uint8) * 255
    skel_pil = Image.fromarray(skel_uint8, mode="L")

    # Save files in original shape
    print("Skeleton image shape:", canvas.skeleton_image.shape)
    image_identifier = canvas.FileLabelName + '_' + canvas.img_type_var.get()
    curr_idx = len([f for f in os.listdir(os.path.join(canvas.current_save_folder, "images")) if f'{image_identifier}_Skeletonised_TwigSize' in f])
    img_path = os.path.join(canvas.current_save_folder, "images", f"{image_identifier}_Skeletonised_TwigSize{twig_size}_{curr_idx}.png")
    cv2.imwrite(img_path, canvas.skeleton_image * 255)

    resized_img = resize_image(skel_pil)
    img_tk = ImageTk.PhotoImage(resized_img)
    canvas.skeleton_img_id = canvas.create_image(1060, 255, image=img_tk)
    canvas._image_refs["skeleton_img"] = img_tk

    # Reset zoom/pan for skeletonised thumbnail
    if hasattr(canvas, 'thumbnail_state') and 'skeletonised' in canvas.thumbnail_state:
        canvas.thumbnail_state['skeletonised'].update({"zoom": 1.0, "pan_x": 0.0, "pan_y": 0.0})

  return skel, nodes, links
